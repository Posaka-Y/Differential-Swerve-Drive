/* Closed-loop bench test: auto-starts once at boot, holding steer at the boot
 * angle and commanding a wheel rpm step (0 -> TEST_WHEEL_TARGET_RPM). Wheel
 * must be lifted clear of the ground (free-spinning) before running this.
 * Checks mode non-interference (steer should stay near the held angle while
 * the wheel spins) and tunes wheel_accel_rpm_per_s / drive_mode_ki.
 *
 * No rpm-tracking divergence guard: current_limit already hard-clamps every
 * motor command, so a wheel-rpm-error threshold only added false trips on the
 * expected breakaway kick (see 2026-07-06 notes in CONTROL_LOOP_TUNING.md —
 * open-loop test confirmed breakaway happens cleanly around 850raw, current
 * feedback has no glitches). Stops are just B1 press, sensor/C620 feedback
 * timeout, steer angle divergence, or the fixed test duration.
 * No friction feedforward: the mode-PI integral rejects friction on its own,
 * given current_limit has margin over the worst-case measured breakaway. */

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
    CLOSED_LOOP_TEST_ENABLED = 0U, /* Set to 1 only during a supervised test. */
    CONTROL_PERIOD_MS = 1U,
    FEEDBACK_TIMEOUT_MS = 20U,
    REPORT_PERIOD_MS = 250U,
    TEST_MAX_DURATION_MS = 10000U, /* Auto-stop so an unattended wheel can't spin forever. */
};

static const float TEST_WHEEL_TARGET_RPM = 50.0f;

typedef struct {
    c620_feedback_t feedback;
    uint32_t last_rx_ms;
    bool received;
} motor_state_t;

static motor_state_t motors[2];
static unit_controller_t controller;
static unit_control_output_t output;

static int32_t to_milli(float value)
{
    const float scaled = value * 1000.0f;
    return (int32_t)(scaled >= 0.0f ? scaled + 0.5f : scaled - 0.5f);
}

static float absf(float value)
{
    return value < 0.0f ? -value : value;
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
        .steer_max_rpm = 5.0f, /* stick-slip below ~1rpm; run above re-stick speed */
        .steer_min_rpm = 2.0f,
        .steer_accel_rpm_per_s = 50.0f,
        /* Untested default; tune during this wheel!=0 test. */
        .wheel_accel_rpm_per_s = 200.0f,
        .angle_kp_rpm_per_deg = 0.5f,
        .angle_deadband_deg = 0.5f,
        .steer_mode_kp = 5.0f,
        .steer_mode_ki = 125.0f, /* 150 regressed to Ki=100-level response; 200 caused a
                                   * hard +/-2deg limit cycle (2026-07-05). 125 is best (2026-07-06). */
        .drive_mode_kp = 5.0f,
        .drive_mode_ki = 100.0f,
        /* Above worst-case breakaway (~850-950 raw, 2026-07-05/06 measurements) so the
         * integral can still defeat static friction, below current_limit so a
         * stuck-phase charge cannot release as a full-limit jump. */
        .mode_integral_limit = 1200.0f,
        .mode_rpm_filter_tau_s = 0.02f,
        /* Measured breakaway ranged ~150-950 raw across angle/direction (2026-07-05/06
         * characterization); this gives ~2x margin over the worst case. */
        .current_limit = 2000.0f,
        .steer_motor_sign = 1.0f,
    };

    clock_init();
    board_io_init();
    debug_uart_init(115200U);
    amt22_init();
    unit_controller_init(&controller, &control_config);

    debug_printf("\n=== differential wheel step test (steer held, wheel 0->%drpm) ===\n",
                 (int32_t)TEST_WHEEL_TARGET_RPM);
    debug_printf("WHEEL MUST BE LIFTED CLEAR OF THE GROUND (free-spinning) before starting.\n");
    debug_printf("auto-starts once; press B1 any time to abort (latches stopped)\n");
    debug_printf("limit=%d iLimit=%d wheelAccel=%drpm/s maxDur=%us\n",
                 (int32_t)control_config.current_limit,
                 (int32_t)control_config.mode_integral_limit,
                 (int32_t)control_config.wheel_accel_rpm_per_s,
                 TEST_MAX_DURATION_MS / 1000U);
    debug_printf("bench actuation: %s\n",
                 CLOSED_LOOP_TEST_ENABLED ? "ENABLED" : "DISABLED (safe idle)");
    clock_delay_ms(250U);

    if (!fdcan_init(FDCAN_BUS_C620, FDCAN_MODE_NORMAL)) {
        debug_printf("FDCAN2 init FAILED\n");
        for (;;) {
            status_led_write(((clock_millis() / 100U) & 1U) != 0U);
        }
    }

    send_currents(0, 0);
    debug_printf("ready: wheel target=%drpm, steer target=current angle (held)\n",
                 (int32_t)TEST_WHEEL_TARGET_RPM);

    bool active = false;
    bool test_done = false; /* Latches once stopped; only a board reset re-arms. */
    uint32_t last_control_ms = clock_millis();
    uint32_t last_report_ms = last_control_ms;
    uint32_t test_start_ms = 0U;
    float current_angle_deg = 0.0f;
    float test_target_deg = 0.0f;

    for (;;) {
        const uint32_t now_ms = clock_millis();
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
            test_done = true;
            unit_controller_reset(&controller);
        } else if (!active && !test_done && CLOSED_LOOP_TEST_ENABLED &&
                   amt_ok && feedback_is_fresh(now_ms)) {
            active = true;
            test_start_ms = now_ms;
            test_target_deg = current_angle_deg; /* Hold steer; only the wheel steps. */
            unit_controller_reset(&controller);
            unit_controller_set_target(&controller, TEST_WHEEL_TARGET_RPM, test_target_deg);
            debug_printf("START: angle=%d target=%d wheelTarget=%d\n",
                         to_milli(current_angle_deg),
                         to_milli(test_target_deg),
                         (int32_t)TEST_WHEEL_TARGET_RPM);
        }

        if (active && (!amt_ok || !feedback_is_fresh(now_ms))) {
            debug_printf("STOP: sensor/C620 timeout\n");
            active = false;
            test_done = true;
            unit_controller_reset(&controller);
        }

        if (active && (now_ms - test_start_ms) >= TEST_MAX_DURATION_MS) {
            debug_printf("STOP: max test duration reached\n");
            active = false;
            test_done = true;
            unit_controller_reset(&controller);
        }

        int16_t current1 = 0;
        int16_t current2 = 0;
        if (active) {
            const unit_measurement_t measurement = {
                .steer_deg = current_angle_deg,
                .motor1_rpm = (float)motors[0].feedback.rpm,
                .motor2_rpm = (float)motors[1].feedback.rpm,
            };
            unit_controller_update(&controller, &measurement, dt_s, &output);

            if (absf(output.angle_error_deg) > 12.0f) {
                debug_printf("STOP: angle diverged err=%d\n",
                             to_milli(output.angle_error_deg));
                active = false;
                test_done = true;
                unit_controller_reset(&controller);
            } else {
                current1 = output.motor1_current;
                current2 = output.motor2_current;
            }
        }

        send_currents(current1, current2);
        status_led_write(active);

        if ((uint32_t)(now_ms - last_report_ms) >= REPORT_PERIOD_MS) {
            last_report_ms = now_ms;
            debug_printf("run=%u angle=%d target=%d err=%d steer=%d "
                         "m1=%d/%d i1=%d m2=%d/%d i2=%d "
                         "steerMode=%d/%d iSteer=%d driveMode=%d/%d iDrive=%d "
                         "wheel=%d\n",
                         active ? 1U : 0U, to_milli(current_angle_deg),
                         to_milli(test_target_deg),
                         to_milli(output.angle_error_deg),
                         to_milli(output.steer_rpm_command),
                         (int32_t)motors[0].feedback.rpm,
                         to_milli(output.motor1_target_rpm),
                         (int32_t)current1,
                         (int32_t)motors[1].feedback.rpm,
                         to_milli(output.motor2_target_rpm),
                         (int32_t)current2,
                         to_milli(output.steer_mode_target_rpm),
                         to_milli(output.steer_mode_measured_rpm),
                         to_milli(output.steer_mode_current),
                         to_milli(output.drive_mode_target_rpm),
                         to_milli(output.drive_mode_measured_rpm),
                         to_milli(output.drive_mode_current),
                         to_milli(output.wheel_rpm_command));
        }
    }
}
