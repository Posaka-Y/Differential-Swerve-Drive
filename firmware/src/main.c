/* CAN target bench app. The unit boots disabled, accepts SET_TARGET on the
 * central CAN bus, and only drives after UNIT_CTRL enable.
 * Wheel must be lifted clear of the ground (free-spinning) before enabling.
 *
 * No rpm-tracking divergence guard: current_limit already hard-clamps every
 * motor command, so a wheel-rpm-error threshold only added false trips on the
 * expected breakaway kick (see 2026-07-06 notes in CONTROL_LOOP_TUNING.md —
 * open-loop test confirmed breakaway happens cleanly around 850raw, current
 * feedback has no glitches). Stops are just B1 press, sensor/C620 feedback
 * timeout, steer angle divergence, or the fixed test duration.
 * Kinetic-friction feedforward and drive-integral floor exist in the
 * controller but default to 0 (disabled) here; SET_CONFIG (0x140+unitId) can
 * tune them live to address the low-rpm stick-slip limit cycle without a
 * reflash. */

#include <stdbool.h>
#include <stdint.h>

#include "control/unit_controller.h"
#include "platform/amt22.h"
#include "platform/clock.h"
#include "platform/fdcan.h"
#include "platform/gpio.h"
#include "platform/uart.h"
#include "protocol/c620.h"

enum {
    CONTROL_PERIOD_MS = 1U,
    FEEDBACK_TIMEOUT_MS = 20U,
    REPORT_PERIOD_MS = 100U,
    ANGLE_DIVERGENCE_STOP_DEG_MILLI = 120000U,
    MOTOR_TEMPERATURE_LIMIT_C = 80U,
    M3508_INTERNAL_REDUCTION = 19U,
    UNIT_ID = 1U,
    CAN_ID_SET_TARGET_BASE = 0x100U,
    CAN_ID_SET_TARGET = CAN_ID_SET_TARGET_BASE + UNIT_ID,
    CAN_ID_UNIT_CTRL_BASE = 0x120U,
    CAN_ID_UNIT_CTRL = CAN_ID_UNIT_CTRL_BASE + UNIT_ID,
    UNIT_CTRL_SET_ENABLE = 0x01U,
    CAN_ID_SET_CONFIG_BASE = 0x140U,
    CAN_ID_SET_CONFIG = CAN_ID_SET_CONFIG_BASE + UNIT_ID,
    TARGET_TIMEOUT_MS = 1000U,
};

typedef struct {
    c620_feedback_t feedback;
    uint32_t last_rx_ms;
    bool received;
} motor_state_t;

static motor_state_t motors[2];
static unit_controller_t controller;
static unit_control_output_t output;
static bool unit_enabled = false;
static bool target_received = false;
static uint32_t last_target_ms = 0U;
static uint32_t last_target_log_ms = 0U;
static float can_target_wheel_rpm = 0.0f;
static float can_target_steer_deg = 0.0f;

static int32_t to_milli(float value)
{
    const float scaled = value * 1000.0f;
    return (int32_t)(scaled >= 0.0f ? scaled + 0.5f : scaled - 0.5f);
}

static float absf(float value)
{
    return value < 0.0f ? -value : value;
}

static float clampf(float value, float minimum, float maximum)
{
    if (value < minimum) {
        return minimum;
    }
    if (value > maximum) {
        return maximum;
    }
    return value;
}

static int32_t read_i32_le(const uint8_t *data)
{
    const uint32_t raw =
        (uint32_t)data[0] |
        ((uint32_t)data[1] << 8U) |
        ((uint32_t)data[2] << 16U) |
        ((uint32_t)data[3] << 24U);
    return (int32_t)raw;
}

static bool target_is_fresh(uint32_t now_ms)
{
    return target_received &&
           (uint32_t)(now_ms - last_target_ms) < TARGET_TIMEOUT_MS;
}

/* SET_CONFIG (0x140+unitId) param indices; each clamp is the safety range for
 * that field, independent of what the CAN sender asks for. */
enum {
    SET_CONFIG_DRIVE_MODE_KP = 1U,
    SET_CONFIG_DRIVE_MODE_KI = 2U,
    SET_CONFIG_STEER_MODE_KP = 3U,
    SET_CONFIG_STEER_MODE_KI = 4U,
    SET_CONFIG_ANGLE_KP_RPM_PER_DEG = 5U,
    SET_CONFIG_ANGLE_DEADBAND_DEG = 6U,
    SET_CONFIG_STEER_MAX_RPM = 7U,
    SET_CONFIG_STEER_MIN_RPM = 8U,
    SET_CONFIG_STEER_ACCEL_RPM_PER_S = 9U,
    SET_CONFIG_WHEEL_ACCEL_RPM_PER_S = 10U,
    SET_CONFIG_MODE_INTEGRAL_LIMIT = 11U,
    SET_CONFIG_CURRENT_LIMIT = 12U,
    SET_CONFIG_MODE_RPM_FILTER_TAU_S = 13U,
    SET_CONFIG_DRIVE_KINETIC_FF_CURRENT = 14U,
    SET_CONFIG_DRIVE_INTEGRAL_FLOOR_CURRENT = 15U,
    SET_CONFIG_DRIVE_MOTION_THRESHOLD_RPM = 16U,
    SET_CONFIG_DRIVE_ONSET_INTEGRAL_CLAMP = 17U,
};

static void apply_set_config(uint8_t idx, int32_t value_milli)
{
    const float value = (float)value_milli * 0.001f;
    float applied;
    switch (idx) {
    case SET_CONFIG_DRIVE_MODE_KP:
        applied = clampf(value, 0.0f, 500.0f);
        controller.config.drive_mode_kp = applied;
        break;
    case SET_CONFIG_DRIVE_MODE_KI:
        applied = clampf(value, 0.0f, 500.0f);
        controller.config.drive_mode_ki = applied;
        break;
    case SET_CONFIG_STEER_MODE_KP:
        applied = clampf(value, 0.0f, 500.0f);
        controller.config.steer_mode_kp = applied;
        break;
    case SET_CONFIG_STEER_MODE_KI:
        applied = clampf(value, 0.0f, 500.0f);
        controller.config.steer_mode_ki = applied;
        break;
    case SET_CONFIG_ANGLE_KP_RPM_PER_DEG:
        applied = clampf(value, 0.0f, 10.0f);
        controller.config.angle_kp_rpm_per_deg = applied;
        break;
    case SET_CONFIG_ANGLE_DEADBAND_DEG:
        applied = clampf(value, 0.0f, 5.0f);
        controller.config.angle_deadband_deg = applied;
        break;
    case SET_CONFIG_STEER_MAX_RPM:
        applied = clampf(value, 0.0f, 10.0f);
        controller.config.steer_max_rpm = applied;
        break;
    case SET_CONFIG_STEER_MIN_RPM:
        applied = clampf(value, 0.0f, 5.0f);
        controller.config.steer_min_rpm = applied;
        break;
    case SET_CONFIG_STEER_ACCEL_RPM_PER_S:
        applied = clampf(value, 0.0f, 200.0f);
        controller.config.steer_accel_rpm_per_s = applied;
        break;
    case SET_CONFIG_WHEEL_ACCEL_RPM_PER_S:
        applied = clampf(value, 0.0f, 2000.0f);
        controller.config.wheel_accel_rpm_per_s = applied;
        break;
    case SET_CONFIG_MODE_INTEGRAL_LIMIT:
        applied = clampf(value, 0.0f, 2000.0f);
        controller.config.mode_integral_limit = applied;
        break;
    case SET_CONFIG_CURRENT_LIMIT:
        /* Upper bound of 2000 is a hard safety ceiling; never raise it. */
        applied = clampf(value, 0.0f, 2000.0f);
        controller.config.current_limit = applied;
        break;
    case SET_CONFIG_MODE_RPM_FILTER_TAU_S:
        applied = clampf(value, 0.0f, 1.0f);
        controller.config.mode_rpm_filter_tau_s = applied;
        break;
    case SET_CONFIG_DRIVE_KINETIC_FF_CURRENT:
        applied = clampf(value, 0.0f, 1000.0f);
        controller.config.drive_kinetic_ff_current = applied;
        break;
    case SET_CONFIG_DRIVE_INTEGRAL_FLOOR_CURRENT:
        applied = clampf(value, 0.0f, 1000.0f);
        controller.config.drive_integral_floor_current = applied;
        break;
    case SET_CONFIG_DRIVE_MOTION_THRESHOLD_RPM:
        applied = clampf(value, 0.0f, 50.0f);
        controller.config.drive_motion_threshold_rpm = applied;
        break;
    case SET_CONFIG_DRIVE_ONSET_INTEGRAL_CLAMP:
        applied = clampf(value, 0.0f, 1200.0f);
        controller.config.drive_onset_integral_clamp_current = applied;
        break;
    default:
        debug_printf("SET_CONFIG BAD idx=%u\n", (uint32_t)idx);
        return;
    }
    debug_printf("SET_CONFIG idx=%u val=%d\n", (uint32_t)idx, to_milli(applied));
}

static void receive_central_can(uint32_t now_ms)
{
    fdcan_frame_t frame;
    while (fdcan_receive(FDCAN_BUS_CENTRAL, &frame)) {
        if (!frame.extended && !frame.remote &&
            frame.id == CAN_ID_SET_TARGET && frame.dlc == 8U) {
            const int32_t target_steer_mdeg = read_i32_le(&frame.data[0]);
            const int32_t target_wheel_rpm_milli = read_i32_le(&frame.data[4]);
            can_target_steer_deg = (float)target_steer_mdeg * 0.001f;
            can_target_wheel_rpm = (float)target_wheel_rpm_milli * 0.001f;
            last_target_ms = now_ms;
            target_received = true;
            if ((uint32_t)(now_ms - last_target_log_ms) >= 500U) {
                last_target_log_ms = now_ms;
                debug_printf("SET_TARGET_RX steer=%d wheel=%d\n",
                             target_steer_mdeg,
                             target_wheel_rpm_milli);
            }
        } else if (!frame.extended && !frame.remote &&
                   frame.id == CAN_ID_UNIT_CTRL && frame.dlc >= 2U &&
                   frame.data[0] == UNIT_CTRL_SET_ENABLE) {
            unit_enabled = frame.data[1] != 0U;
            debug_printf("UNIT_CTRL enable=%u\n", unit_enabled ? 1U : 0U);
        } else if (!frame.extended && !frame.remote &&
                   frame.id == CAN_ID_SET_CONFIG && frame.dlc == 8U) {
            apply_set_config(frame.data[0], read_i32_le(&frame.data[4]));
        } else {
            debug_printf("CENTRAL_RX id=%x dlc=%u data=%x %x %x %x %x %x %x %x\n",
                         frame.id,
                         (uint32_t)frame.dlc,
                         (uint32_t)frame.data[0],
                         (uint32_t)frame.data[1],
                         (uint32_t)frame.data[2],
                         (uint32_t)frame.data[3],
                         (uint32_t)frame.data[4],
                         (uint32_t)frame.data[5],
                         (uint32_t)frame.data[6],
                         (uint32_t)frame.data[7]);
        }
    }
}

static void receive_c620(uint32_t now_ms)
{
    fdcan_frame_t frame;
    while (fdcan_receive(FDCAN_BUS_C620, &frame)) {
        c620_feedback_t feedback;
        if (c620_decode_feedback(&frame, &feedback) &&
            feedback.motor_id >= 1U && feedback.motor_id <= 2U) {
            motor_state_t *motor = &motors[feedback.motor_id - 1U];
            motor->feedback = feedback;
            motor->last_rx_ms = now_ms;
            motor->received = true;
        }
    }
}

static bool feedback_is_fresh(uint32_t now_ms)
{
    return motors[0].received && motors[1].received &&
           (uint32_t)(now_ms - motors[0].last_rx_ms) < FEEDBACK_TIMEOUT_MS &&
           (uint32_t)(now_ms - motors[1].last_rx_ms) < FEEDBACK_TIMEOUT_MS;
}

static void send_currents(int16_t motor1, int16_t motor2)
{
    fdcan_frame_t command;
    c620_make_current_command(&command, motor1, motor2, 0, 0);
    (void)fdcan_send(FDCAN_BUS_C620, &command);
}

int main(void)
{
    static const unit_controller_config_t control_config = {
        .motor_max_rpm = 469.0f,
        .steer_max_rpm = 5.0f,
        .steer_min_rpm = 0.0f,
        .steer_accel_rpm_per_s = 50.0f,
        /* Untested default; tune during this wheel!=0 test. */
        .wheel_accel_rpm_per_s = 200.0f,
        .angle_kp_rpm_per_deg = 0.5f,
        .angle_deadband_deg = 0.5f,
        .steer_mode_kp = 50.0f,
        .steer_mode_ki = 30.0f,
        /* drive_mode_kp / drive_integral_floor_current / drive_motion_threshold_rpm
         * are 2026-07-07 measured values (kinetic friction ~200 raw). */
        .drive_mode_kp = 10.0f,
        .drive_mode_ki = 20.0f,
        /* Above worst-case breakaway (~850-950 raw, 2026-07-05/06 measurements) so the
         * integral can still defeat static friction, below current_limit so a
         * stuck-phase charge cannot release as a full-limit jump. */
        .mode_integral_limit = 1200.0f,
        .mode_rpm_filter_tau_s = 0.02f,
        /* Measured breakaway ranged ~150-950 raw across angle/direction (2026-07-05/06
         * characterization); this gives ~2x margin over the worst case. */
        .current_limit = 2000.0f,
        .steer_motor_sign = 1.0f,
        /* Kinetic-friction FF stays disabled (0); integral floor and motion
         * threshold are 2026-07-07 measured values (kinetic friction ~200 raw). */
        .drive_kinetic_ff_current = 0.0f,
        .drive_integral_floor_current = 200.0f,
        .drive_motion_threshold_rpm = 5.0f,
        /* 400: rides through local friction snags (breakaway up to ~950 raw)
         * while cutting the 850->200 breakaway kick; 250 re-sticks at snag
         * angles (2026-07-08 bench A/B, 25rpm 3/3 stuck-free). */
        .drive_onset_integral_clamp_current = 400.0f,
    };

    clock_init();
    board_io_init();
    debug_uart_init(115200U);
    amt22_init();
    unit_controller_init(&controller, &control_config);

    debug_printf("\n=== CAN target differential unit test ===\n");
    debug_printf("WHEEL MUST BE LIFTED CLEAR OF THE GROUND before UNIT_CTRL enable.\n");
    debug_printf("boots disabled; press B1 any time to abort and latch disabled\n");
    debug_printf("limit=%d iLimit=%d wheelAccel=%drpm/s targetTimeout=%ums\n",
                 (int32_t)control_config.current_limit,
                 (int32_t)control_config.mode_integral_limit,
                 (int32_t)control_config.wheel_accel_rpm_per_s,
                 TARGET_TIMEOUT_MS);
    clock_delay_ms(250U);

    if (!fdcan_init(FDCAN_BUS_CENTRAL, FDCAN_MODE_NORMAL)) {
        debug_printf("FDCAN1 init FAILED\n");
        for (;;) {
            status_led_write(((clock_millis() / 100U) & 1U) != 0U);
        }
    }

    if (!fdcan_init(FDCAN_BUS_C620, FDCAN_MODE_NORMAL)) {
        debug_printf("FDCAN2 init FAILED\n");
        for (;;) {
            status_led_write(((clock_millis() / 100U) & 1U) != 0U);
        }
    }

    send_currents(0, 0);
    debug_printf("ready: central CAN SET_TARGET + UNIT_CTRL enable, unitId=%u\n",
                 UNIT_ID);

    bool active = false;
    uint32_t last_control_ms = clock_millis();
    uint32_t last_report_ms = last_control_ms;
    float current_angle_deg = 0.0f;
    float test_target_deg = 0.0f;

    for (;;) {
        const uint32_t now_ms = clock_millis();
        receive_central_can(now_ms);
        receive_c620(now_ms);

        const uint32_t elapsed_ms = now_ms - last_control_ms;
        if (elapsed_ms < CONTROL_PERIOD_MS) {
            continue;
        }
        last_control_ms = now_ms;
        float dt_s = (float)elapsed_ms * 0.001f;
        if (dt_s > 0.010f) {
            dt_s = 0.010f;
        }

        amt22_sample_t encoder;
        const bool amt_transfer_ok = amt22_read(&encoder);
        const bool amt_ok = amt_transfer_ok && encoder.check_bits_ok;
        if (amt_ok) {
            current_angle_deg = (float)encoder.position * (360.0f / 4096.0f);
        }

        const bool pressed = user_button_is_pressed();
        if (active && pressed) {
            debug_printf("STOP: B1 abort\n");
            active = false;
            unit_enabled = false;
            unit_controller_reset(&controller);
        } else if (!active && unit_enabled && target_is_fresh(now_ms) &&
                   amt_ok && feedback_is_fresh(now_ms)) {
            active = true;
            test_target_deg = can_target_steer_deg;
            unit_controller_reset(&controller);
            unit_controller_set_target(&controller, can_target_wheel_rpm, test_target_deg);
            debug_printf("START_CAN: angle=%d target=%d wheelTarget=%d\n",
                         to_milli(current_angle_deg),
                         to_milli(test_target_deg),
                         to_milli(can_target_wheel_rpm));
        }

        if (active && !unit_enabled) {
            debug_printf("STOP: disabled\n");
            active = false;
            unit_controller_reset(&controller);
        }

        if (active && !target_is_fresh(now_ms)) {
            debug_printf("STOP: target timeout\n");
            active = false;
            unit_enabled = false;
            unit_controller_reset(&controller);
        }

        if (active && (!amt_ok || !feedback_is_fresh(now_ms))) {
            debug_printf("STOP: sensor/C620 timeout\n");
            active = false;
            unit_enabled = false;
            unit_controller_reset(&controller);
        }

        if (active && (motors[0].feedback.temperature_c >= MOTOR_TEMPERATURE_LIMIT_C ||
                       motors[1].feedback.temperature_c >= MOTOR_TEMPERATURE_LIMIT_C)) {
            debug_printf("STOP: motor temperature m1=%u m2=%u\n",
                         (uint32_t)motors[0].feedback.temperature_c,
                         (uint32_t)motors[1].feedback.temperature_c);
            active = false;
            unit_enabled = false;
            unit_controller_reset(&controller);
        }

        int16_t current1 = 0;
        int16_t current2 = 0;
        if (active) {
            const unit_measurement_t measurement = {
                .steer_deg = current_angle_deg,
                /* C620 speed feedback is motor-rotor rpm; kinematics use the
                 * M3508 gearbox output-shaft rpm (19:1 reduction). */
                .motor1_rpm = (float)motors[0].feedback.rpm /
                              (float)M3508_INTERNAL_REDUCTION,
                .motor2_rpm = (float)motors[1].feedback.rpm /
                              (float)M3508_INTERNAL_REDUCTION,
            };
            test_target_deg = can_target_steer_deg;
            unit_controller_set_target(&controller, can_target_wheel_rpm,
                                       test_target_deg);
            unit_controller_update(&controller, &measurement, dt_s, &output);

            if (absf(output.angle_error_deg) * 1000.0f >
                (float)ANGLE_DIVERGENCE_STOP_DEG_MILLI) {
                debug_printf("STOP: angle diverged err=%d\n",
                             to_milli(output.angle_error_deg));
                active = false;
                unit_enabled = false;
                unit_controller_reset(&controller);
            } else {
                current1 = output.motor1_current;
                current2 = output.motor2_current;
            }
        }

        send_currents(current1, current2);
        status_led_write(active);

        if (active && (uint32_t)(now_ms - last_report_ms) >= REPORT_PERIOD_MS) {
            last_report_ms = now_ms;
            debug_printf("run=%u step=%u angle=%d target=%d err=%d steer=%d "
                         "m1=%d/%d i1=%d t1=%u m2=%d/%d i2=%d t2=%u "
                         "steerMode=%d/%d iSteer=%d driveMode=%d/%d iDrive=%d scale=%u "
                         "wheel=%d\n",
                         active ? 1U : 0U, 0U,
                         to_milli(current_angle_deg),
                         to_milli(test_target_deg),
                         to_milli(output.angle_error_deg),
                         to_milli(output.steer_rpm_command),
                         (int32_t)motors[0].feedback.rpm,
                         to_milli(output.motor1_target_rpm),
                         (int32_t)current1,
                         (uint32_t)motors[0].feedback.temperature_c,
                         (int32_t)motors[1].feedback.rpm,
                         to_milli(output.motor2_target_rpm),
                         (int32_t)current2,
                         (uint32_t)motors[1].feedback.temperature_c,
                         to_milli(output.steer_mode_target_rpm),
                         to_milli(output.steer_mode_measured_rpm),
                         to_milli(output.steer_mode_current),
                         to_milli(output.drive_mode_target_rpm),
                         to_milli(output.drive_mode_measured_rpm),
                         to_milli(output.drive_mode_current),
                         (uint32_t)output.torque_scaling_active,
                         to_milli(output.wheel_rpm_command));
        }
    }
}
