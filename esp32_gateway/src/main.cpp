#include <Arduino.h>
#include <Bluepad32.h>
#include <LittleFS.h>
#include <math.h>

#include "gateway_config.h"

namespace {

constexpr uint8_t kFrameSync0 = 0xa5u;
constexpr uint8_t kFrameSync1 = 0x5au;
constexpr uint8_t kFrameTypeCommand = 0x01u;
constexpr uint8_t kFrameTypeStatus = 0x81u;
constexpr size_t kFrameSize = 14u;
constexpr int32_t kFullTurnMdeg = 360000;
constexpr int32_t kMaxCommandAngleErrorMdeg = 90000;
constexpr char kOfflineLogPath[] = "/radio.csv";
constexpr char kTelemetryCsvHeader[] =
    "ms,bt,armed,enable,unit_active,target_steer_mdeg,actual_steer_mdeg,"
    "steer_error_mdeg,target_wheel_mrpm,actual_wheel_mrpm,wheel_error_mrpm,"
    "rpm_limit,controller_age_ms,unit_age_ms,uart_rx_frames,uart_rx_bad,"
    "uart_rx_gaps,uart_tx_fail\n";

ControllerPtr controller = nullptr;
HardwareSerial unit_uart(2);
bool have_controller_data = false;
bool have_unit_status = false;
bool armed = false;
bool enable_commanded = false;
bool unit_active = false;
bool previous_options = false;
bool previous_capture = false;
bool have_uart_rx_sequence = false;
bool littlefs_ready = false;
bool offline_log_active = false;
bool offline_log_dumping = false;
uint8_t previous_dpad = 0;
uint8_t last_uart_rx_sequence = 0;
uint32_t last_controller_data_ms = 0;
uint32_t last_unit_status_ms = 0;
uint32_t last_uart_ms = 0;
uint32_t uart_tx_failures = 0;
uint32_t uart_rx_frames = 0;
uint32_t uart_rx_bad_frames = 0;
uint32_t uart_rx_sequence_gaps = 0;
uint32_t offline_log_rows = 0;
uint32_t last_offline_log_flush_ms = 0;
uint8_t uart_tx_sequence = 0;
uint8_t uart_rx_buffer[kFrameSize] = {};
size_t uart_rx_count = 0;
int32_t current_steer_mdeg = 0;
int32_t current_wheel_rpm_milli = 0;
int32_t target_steer_mdeg = 0;
int32_t target_wheel_rpm_milli = 0;
float wheel_rpm_limit = DSD_MAX_WHEEL_RPM;
File offline_log_file;

float clampf(float value, float minimum, float maximum)
{
    if (value < minimum) {
        return minimum;
    }
    if (value > maximum) {
        return maximum;
    }
    return value;
}

int32_t wrap_angle_mdeg(int32_t angle)
{
    angle %= kFullTurnMdeg;
    return angle < 0 ? angle + kFullTurnMdeg : angle;
}

int32_t shortest_angle_error_mdeg(int32_t target, int32_t current)
{
    int32_t error = wrap_angle_mdeg(target) - wrap_angle_mdeg(current);
    if (error > kFullTurnMdeg / 2) {
        error -= kFullTurnMdeg;
    } else if (error < -kFullTurnMdeg / 2) {
        error += kFullTurnMdeg;
    }
    return error;
}

float normalize_axis(int32_t raw)
{
    return clampf(static_cast<float>(raw) / 512.0f, -1.0f, 1.0f);
}

float response_curve(float value)
{
    return DSD_STICK_LINEAR_MIX * value +
           (1.0f - DSD_STICK_LINEAR_MIX) * value * value * value;
}

float apply_axis_deadzone(float value)
{
    const float magnitude = fabsf(value);
    if (magnitude <= DSD_STICK_DEADZONE) {
        return 0.0f;
    }
    const float remapped =
        (magnitude - DSD_STICK_DEADZONE) / (1.0f - DSD_STICK_DEADZONE);
    return value < 0.0f ? -remapped : remapped;
}

void write_i32_le(uint8_t *destination, int32_t value)
{
    const uint32_t raw = static_cast<uint32_t>(value);
    destination[0] = static_cast<uint8_t>(raw & 0xffu);
    destination[1] = static_cast<uint8_t>((raw >> 8) & 0xffu);
    destination[2] = static_cast<uint8_t>((raw >> 16) & 0xffu);
    destination[3] = static_cast<uint8_t>((raw >> 24) & 0xffu);
}

int32_t read_i32_le(const uint8_t *source)
{
    const uint32_t raw = static_cast<uint32_t>(source[0]) |
                         (static_cast<uint32_t>(source[1]) << 8) |
                         (static_cast<uint32_t>(source[2]) << 16) |
                         (static_cast<uint32_t>(source[3]) << 24);
    return static_cast<int32_t>(raw);
}

uint8_t crc8(const uint8_t *data, size_t length)
{
    uint8_t crc = 0;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x80u) != 0u
                      ? static_cast<uint8_t>((crc << 1u) ^ 0x07u)
                      : static_cast<uint8_t>(crc << 1u);
        }
    }
    return crc;
}

void send_uart_command(bool enable)
{
    uint8_t frame[kFrameSize] = {
        kFrameSync0, kFrameSync1, kFrameTypeCommand, uart_tx_sequence++,
    };
    write_i32_le(&frame[4], target_steer_mdeg);
    write_i32_le(&frame[8], target_wheel_rpm_milli);
    frame[12] = enable ? 1u : 0u;
    frame[13] = crc8(frame, kFrameSize - 1u);
    if (unit_uart.write(frame, sizeof(frame)) == sizeof(frame)) {
        enable_commanded = enable;
    } else {
        ++uart_tx_failures;
    }
}

void command_safe_stop()
{
    target_wheel_rpm_milli = 0;
    if (enable_commanded) {
        send_uart_command(false);
    }
}

void stop_offline_log(ControllerPtr ctl)
{
    if (!offline_log_active) {
        return;
    }
    offline_log_file.flush();
    offline_log_file.close();
    offline_log_active = false;
    Console.printf("offline-log: stopped rows=%lu path=%s\n",
                   static_cast<unsigned long>(offline_log_rows),
                   kOfflineLogPath);
    if (ctl != nullptr) {
        ctl->playDualRumble(0, 300, 60, 60);
    }
}

void start_offline_log(ControllerPtr ctl, uint32_t now_ms)
{
    if (!littlefs_ready) {
        Console.println("offline-log: LittleFS unavailable");
        if (ctl != nullptr) {
            ctl->playDualRumble(0, 500, 0, 150);
        }
        return;
    }
    LittleFS.remove(kOfflineLogPath);
    offline_log_file = LittleFS.open(kOfflineLogPath, FILE_WRITE);
    if (!offline_log_file) {
        Console.println("offline-log: open failed");
        if (ctl != nullptr) {
            ctl->playDualRumble(0, 500, 0, 150);
        }
        return;
    }
    offline_log_file.print(kTelemetryCsvHeader);
    offline_log_rows = 0;
    last_offline_log_flush_ms = now_ms;
    offline_log_active = true;
    Console.printf("offline-log: started path=%s\n", kOfflineLogPath);
    if (ctl != nullptr) {
        ctl->playDualRumble(0, 120, 40, 40);
    }
}

void dump_offline_log(ControllerPtr ctl)
{
    if (!littlefs_ready || offline_log_active) {
        Console.println("offline-log: dump unavailable while recording");
        return;
    }
    File source = LittleFS.open(kOfflineLogPath, FILE_READ);
    if (!source) {
        Console.println("offline-log: no saved log");
        if (ctl != nullptr) {
            ctl->playDualRumble(0, 500, 0, 150);
        }
        return;
    }
    offline_log_dumping = true;
    Console.println("OFFLINE_LOG_BEGIN");
    while (source.available() > 0) {
        Console.write(static_cast<char>(source.read()));
    }
    Console.println("OFFLINE_LOG_END");
    source.close();
    offline_log_dumping = false;
    if (ctl != nullptr) {
        ctl->playDualRumble(0, 200, 30, 30);
    }
}

void handle_usb_commands()
{
    while (Serial.available() > 0) {
        const char command = static_cast<char>(Serial.read());
        if (command == 'D' || command == 'd') {
            // Download is performed after the run. Closing an accidentally
            // still-open recording here preserves every flushed row and makes
            // recovery independent of controller button mappings.
            stop_offline_log(controller);
            dump_offline_log(controller);
        }
    }
}

void on_controller_connected(ControllerPtr ctl)
{
    if (controller != nullptr || !ctl->isGamepad()) {
        ctl->disconnect();
        return;
    }
    controller = ctl;
    have_controller_data = false;
    armed = false;
    previous_options = false;
    previous_capture = false;
    previous_dpad = 0;
    command_safe_stop();
    const ControllerProperties properties = ctl->getProperties();
    Console.printf("bt: connected model=%s vid=%04x pid=%04x\n",
                   ctl->getModelName().c_str(), properties.vendor_id,
                   properties.product_id);
    ctl->setColorLED(255, 128, 0);
}

void on_controller_disconnected(ControllerPtr ctl)
{
    stop_offline_log(ctl);
    if (controller == ctl) {
        controller = nullptr;
    }
    have_controller_data = false;
    armed = false;
    previous_options = false;
    previous_capture = false;
    previous_dpad = 0;
    command_safe_stop();
    Console.println("bt: controller disconnected; disabled");
}

void update_controller_command(uint32_t now_ms)
{
    if (controller == nullptr || !controller->isConnected() ||
        !controller->isGamepad()) {
        command_safe_stop();
        return;
    }

    if (controller->hasData()) {
        have_controller_data = true;
        last_controller_data_ms = now_ms;

        const uint8_t dpad = controller->dpad();
        const bool rpm_up = (dpad & DPAD_UP) != 0u;
        const bool rpm_down = (dpad & DPAD_DOWN) != 0u;
        const bool previous_rpm_up = (previous_dpad & DPAD_UP) != 0u;
        const bool previous_rpm_down = (previous_dpad & DPAD_DOWN) != 0u;
        if (rpm_up && !previous_rpm_up && !rpm_down) {
            wheel_rpm_limit = clampf(
                wheel_rpm_limit + DSD_WHEEL_RPM_LIMIT_STEP,
                DSD_MIN_WHEEL_RPM_LIMIT, DSD_MAX_WHEEL_RPM_LIMIT);
            controller->playDualRumble(0, 60, 40, 40);
            Console.printf("control: rpm limit=%.0f\n", wheel_rpm_limit);
        } else if (rpm_down && !previous_rpm_down && !rpm_up) {
            wheel_rpm_limit = clampf(
                wheel_rpm_limit - DSD_WHEEL_RPM_LIMIT_STEP,
                DSD_MIN_WHEEL_RPM_LIMIT, DSD_MAX_WHEEL_RPM_LIMIT);
            controller->playDualRumble(0, 60, 20, 20);
            Console.printf("control: rpm limit=%.0f\n", wheel_rpm_limit);
        }
        const bool capture = controller->miscSelect() ||
                             controller->miscCapture();
        const bool record_button = capture || (dpad & DPAD_LEFT) != 0u;
        const bool previous_record_button = previous_capture ||
            (previous_dpad & DPAD_LEFT) != 0u;
        if (record_button && !previous_record_button) {
            if (controller->l1()) {
                dump_offline_log(controller);
            } else if (offline_log_active) {
                stop_offline_log(controller);
            } else {
                start_offline_log(controller, now_ms);
            }
        }
        previous_capture = capture;
        previous_dpad = dpad;

        // Radio-style split controls: left X steers and right Y throttles.
        // A centered steering stick commands the calibrated 0-degree heading.
        const float steer = response_curve(apply_axis_deadzone(
            -normalize_axis(controller->axisX())));
        const float throttle = response_curve(apply_axis_deadzone(
            -normalize_axis(controller->axisRY())));
        const int32_t desired_steer_mdeg = static_cast<int32_t>(
            steer * DSD_MAX_STEER_DEG * 1000.0f);
        if (have_unit_status) {
            const int32_t error = shortest_angle_error_mdeg(
                desired_steer_mdeg, current_steer_mdeg);
            const int32_t limited_error = error > kMaxCommandAngleErrorMdeg
                ? kMaxCommandAngleErrorMdeg
                : (error < -kMaxCommandAngleErrorMdeg
                   ? -kMaxCommandAngleErrorMdeg : error);
            target_steer_mdeg = wrap_angle_mdeg(
                current_steer_mdeg + limited_error);
        } else {
            target_steer_mdeg = wrap_angle_mdeg(desired_steer_mdeg);
        }
        target_wheel_rpm_milli = static_cast<int32_t>(
            throttle * wheel_rpm_limit * 1000.0f);

        const bool options = controller->miscStart();
        if (options && !previous_options && !controller->r1() &&
            target_wheel_rpm_milli == 0 && have_unit_status) {
#if DSD_MOTOR_ENABLE_ALLOWED
            if (!armed) {
                // Bumpless arm: the first enable holds the measured angle and
                // zero wheel speed. Motion starts only after a later stick
                // update while R1 is held.
                target_steer_mdeg = current_steer_mdeg;
                target_wheel_rpm_milli = 0;
                armed = true;
            } else {
                armed = false;
            }
            controller->setColorLED(armed ? 0 : 255, armed ? 255 : 128, 0);
            Console.printf("control: armed=%u\n", armed ? 1u : 0u);
#else
            Console.println("control: arm request ignored; commissioning lock active");
#endif
        }
        previous_options = options;
    }

    const bool controller_fresh =
        have_controller_data && now_ms - last_controller_data_ms <=
                                    DSD_CONTROLLER_TIMEOUT_MS;
    const bool status_fresh =
        have_unit_status && now_ms - last_unit_status_ms <=
                                DSD_UNIT_STATUS_TIMEOUT_MS;
    const bool desired_enable = DSD_MOTOR_ENABLE_ALLOWED && armed &&
                                controller_fresh && status_fresh &&
                                controller->r1();
    if (!controller_fresh) {
        target_wheel_rpm_milli = 0;
    }
    if (desired_enable != enable_commanded) {
        send_uart_command(desired_enable);
    }
}

void start_unit_uart()
{
    unit_uart.begin(115200, SERIAL_8N1, DSD_UART_RX_GPIO, DSD_UART_TX_GPIO);
    Console.printf("uart: 115200 8N1 TX=GPIO%d RX=GPIO%d unit=%u ready\n",
                   DSD_UART_TX_GPIO, DSD_UART_RX_GPIO, DSD_UNIT_ID);
    send_uart_command(false);
}

void receive_unit_uart(uint32_t now_ms)
{
    while (unit_uart.available() > 0) {
        const uint8_t byte = static_cast<uint8_t>(unit_uart.read());
        if (uart_rx_count == 0) {
            if (byte == kFrameSync0) {
                uart_rx_buffer[uart_rx_count++] = byte;
            }
            continue;
        }
        if (uart_rx_count == 1 && byte != kFrameSync1) {
            uart_rx_count = byte == kFrameSync0 ? 1u : 0u;
            continue;
        }
        uart_rx_buffer[uart_rx_count++] = byte;
        if (uart_rx_count < kFrameSize) {
            continue;
        }
        uart_rx_count = 0;
        if (uart_rx_buffer[2] != kFrameTypeStatus ||
            crc8(uart_rx_buffer, kFrameSize - 1u) !=
                uart_rx_buffer[kFrameSize - 1u]) {
            ++uart_rx_bad_frames;
            continue;
        }

        const uint8_t received_sequence = uart_rx_buffer[3];
        if (have_uart_rx_sequence) {
            const uint8_t sequence_delta = static_cast<uint8_t>(
                received_sequence - last_uart_rx_sequence);
            // A small forward delta means dropped status frames. A large
            // delta is treated as a NUCLEO restart / sequence reset.
            if (sequence_delta > 1u && sequence_delta < 128u) {
                uart_rx_sequence_gaps += sequence_delta - 1u;
            }
        }
        last_uart_rx_sequence = received_sequence;
        have_uart_rx_sequence = true;
        ++uart_rx_frames;
        current_steer_mdeg = read_i32_le(&uart_rx_buffer[4]);
        current_wheel_rpm_milli = read_i32_le(&uart_rx_buffer[8]);
        unit_active = (uart_rx_buffer[12] & 1u) != 0u;
        if (!have_unit_status) {
            target_steer_mdeg = current_steer_mdeg;
            Console.printf("uart: first status steer=%ldmdeg wheel=%ldmrpm\n",
                           static_cast<long>(current_steer_mdeg),
                           static_cast<long>(current_wheel_rpm_milli));
        }
        have_unit_status = true;
        last_unit_status_ms = now_ms;
    }
}

void print_telemetry(uint32_t now_ms)
{
    static uint32_t last_telemetry_ms = 0;
    if (now_ms - last_telemetry_ms < DSD_TELEMETRY_PERIOD_MS) {
        return;
    }
    last_telemetry_ms = now_ms;

    const int32_t controller_age_ms = have_controller_data
        ? static_cast<int32_t>(now_ms - last_controller_data_ms) : -1;
    const int32_t unit_age_ms = have_unit_status
        ? static_cast<int32_t>(now_ms - last_unit_status_ms) : -1;
    const int32_t steer_error_mdeg = have_unit_status
        ? shortest_angle_error_mdeg(target_steer_mdeg, current_steer_mdeg) : 0;
    const int32_t wheel_error_rpm_milli = have_unit_status
        ? target_wheel_rpm_milli - current_wheel_rpm_milli : 0;

    char telemetry_line[256];
    const int telemetry_length = snprintf(
        telemetry_line, sizeof(telemetry_line),
        "%lu,%u,%u,%u,%u,%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld,%lu,%lu,%lu,%lu\n",
        static_cast<unsigned long>(now_ms),
        controller != nullptr ? 1u : 0u,
        armed ? 1u : 0u,
        enable_commanded ? 1u : 0u,
        unit_active ? 1u : 0u,
        static_cast<long>(target_steer_mdeg),
        static_cast<long>(current_steer_mdeg),
        static_cast<long>(steer_error_mdeg),
        static_cast<long>(target_wheel_rpm_milli),
        static_cast<long>(current_wheel_rpm_milli),
        static_cast<long>(wheel_error_rpm_milli),
        static_cast<long>(wheel_rpm_limit),
        static_cast<long>(controller_age_ms),
        static_cast<long>(unit_age_ms),
        static_cast<unsigned long>(uart_rx_frames),
        static_cast<unsigned long>(uart_rx_bad_frames),
        static_cast<unsigned long>(uart_rx_sequence_gaps),
        static_cast<unsigned long>(uart_tx_failures));
    if (telemetry_length <= 0 ||
        telemetry_length >= static_cast<int>(sizeof(telemetry_line))) {
        return;
    }

    if (offline_log_active) {
        offline_log_file.write(
            reinterpret_cast<const uint8_t *>(telemetry_line),
            static_cast<size_t>(telemetry_length));
        ++offline_log_rows;
        if (now_ms - last_offline_log_flush_ms >=
                DSD_OFFLINE_LOG_FLUSH_PERIOD_MS) {
            last_offline_log_flush_ms = now_ms;
            offline_log_file.flush();
        }
    } else if (!offline_log_dumping) {
        Console.print("TEL,");
        Console.print(telemetry_line);
    }
}

void print_status(uint32_t now_ms)
{
    static uint32_t last_status_ms = 0;
    if (now_ms - last_status_ms < 1000) {
        return;
    }
    last_status_ms = now_ms;
    const uint32_t controller_age =
        have_controller_data ? now_ms - last_controller_data_ms : UINT32_MAX;
    const uint32_t unit_age = have_unit_status ? now_ms - last_unit_status_ms
                                                : UINT32_MAX;
    Console.printf(
        "status: bt=%u age=%s armed=%u enable=%u unit=%s uartRx=%lu uartFail=%lu "
        "target=%ldmdeg,%ldmrpm rpmLimit=%.0f\n",
        controller != nullptr ? 1u : 0u,
        have_controller_data ? String(controller_age).c_str() : "none",
        armed ? 1u : 0u, enable_commanded ? 1u : 0u,
        have_unit_status ? String(unit_age).c_str() : "none",
        static_cast<unsigned long>(uart_rx_frames),
        static_cast<unsigned long>(uart_tx_failures),
        static_cast<long>(target_steer_mdeg),
        static_cast<long>(target_wheel_rpm_milli), wheel_rpm_limit);
}

}  // namespace

void setup()
{
    // Bluepad32 Console output uses the ESP-IDF UART0 logger directly. Start
    // Arduino Serial as well so the same CH340 link can receive host commands
    // (for example, 'D' to download a LittleFS log).
    Serial.begin(115200);
    Console.println("DSD ESP32 DualSense direct UART receiver v1");
    Console.println(
        "TEL_HEADER,ms,bt,armed,enable,unit_active,target_steer_mdeg,"
        "actual_steer_mdeg,steer_error_mdeg,target_wheel_mrpm,"
        "actual_wheel_mrpm,wheel_error_mrpm,rpm_limit,controller_age_ms,"
        "unit_age_ms,uart_rx_frames,uart_rx_bad,uart_rx_gaps,uart_tx_fail");
    littlefs_ready = LittleFS.begin(true);
    Console.printf("offline-log: LittleFS=%u start/stop=DpadLeft dump=L1+DpadLeft\n",
                   littlefs_ready ? 1u : 0u);
    Console.printf("Bluepad32: %s\n", BP32.firmwareVersion());
    BP32.setup(&on_controller_connected, &on_controller_disconnected);
#if DSD_FORGET_BLUETOOTH_KEYS_ON_BOOT
    BP32.forgetBluetoothKeys();
    Console.println("bt: stored pairing keys cleared for commissioning");
#endif
    BP32.enableVirtualDevice(false);
    BP32.enableBLEService(false);
    start_unit_uart();
}

void loop()
{
    BP32.update();
    handle_usb_commands();
    const uint32_t now_ms = millis();
    receive_unit_uart(now_ms);
    update_controller_command(now_ms);
    if (now_ms - last_uart_ms >= DSD_UART_PERIOD_MS) {
        last_uart_ms = now_ms;
        send_uart_command(enable_commanded);
    }
    print_telemetry(now_ms);
    print_status(now_ms);
    delay(1);
}
