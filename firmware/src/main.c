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
    /* Disabled-state angle report so a UI can seed its steer target from the
     * actual angle before the first enable (run= lines only print while
     * active). */
    IDLE_REPORT_PERIOD_MS = 500U,
    ANGLE_DIVERGENCE_STOP_DEG_MILLI = 120000U,
    MOTOR_TEMPERATURE_LIMIT_C = 80U,
    M3508_INTERNAL_REDUCTION = 19U,
    UNIT_ID = 1U,
    CAN_ID_SET_TARGET_BASE = 0x100U,
    CAN_ID_SET_TARGET = CAN_ID_SET_TARGET_BASE + UNIT_ID,
    CAN_ID_SET_TARGET_FF_BASE = 0x110U,
    CAN_ID_SET_TARGET_FF = CAN_ID_SET_TARGET_FF_BASE + UNIT_ID,
    CAN_ID_UNIT_CTRL_BASE = 0x120U,
    CAN_ID_UNIT_CTRL = CAN_ID_UNIT_CTRL_BASE + UNIT_ID,
    UNIT_CTRL_SET_ENABLE = 0x01U,
    CAN_ID_SET_CONFIG_BASE = 0x140U,
    CAN_ID_SET_CONFIG = CAN_ID_SET_CONFIG_BASE + UNIT_ID,
    CAN_ID_STATUS1_BASE = 0x180U,
    CAN_ID_STATUS1 = CAN_ID_STATUS1_BASE + UNIT_ID,
    CAN_ID_STATUS2_BASE = 0x190U,
    CAN_ID_STATUS2 = CAN_ID_STATUS2_BASE + UNIT_ID,
    CAN_ID_STATUS3_BASE = 0x1A0U,
    CAN_ID_STATUS3 = CAN_ID_STATUS3_BASE + UNIT_ID,
    TARGET_TIMEOUT_MS = 1000U,
    STATUS1_NORMAL_PERIOD_MS = 20U,
    STATUS2_NORMAL_PERIOD_MS = 50U,
    STATUS3_PERIOD_MS = 20U,
    SETTLE_DWELL_MS = 100U,
    /* docs/communication/COMMUNICATION_NAMING_AND_IDS.md "SET_TARGET_FF
     * payload": sender is assumed to publish at >=50Hz; 200ms is the
     * documented staleness bound before the FF must fall back to 0. */
    TARGET_FF_TIMEOUT_MS = 200U,
    /* mdeg/s -> rpm: /1000 (mdeg->deg) then /6 (deg/s->rpm) = /6000. */
    STEER_RATE_FF_MDEG_PER_S_TO_RPM_DIV = 6000,
};

enum {
    STATUS_FLAG_ACTIVE = 1U << 0,
    STATUS_FLAG_TARGET_FRESH = 1U << 1,
    STATUS_FLAG_FEEDBACK_OK = 1U << 2,
    STATUS_FLAG_AMT_OK = 1U << 3,
    STATUS_FLAG_STEER_IN_BAND = 1U << 4,
    STATUS_FLAG_WHEEL_IN_BAND = 1U << 5,
    STATUS_FLAG_MOTION_SETTLED = 1U << 6,
    STATUS_FLAG_LIMITING_ACTIVE = 1U << 7,
};

#define SETTLE_ANGLE_BAND_DEG 0.5f
#define SETTLE_STEER_AXIS_RPM 1.0f
#define SETTLE_WHEEL_MIN_BAND_RPM 12.0f
#define SETTLE_WHEEL_RELATIVE_BAND 0.06f
#define SETTLE_WHEEL_ACCEL_MILLI_RPM_PER_S 1000
#define SETTLE_FF_AXIS_RPM 0.1f
#define DRIVE_RATIO (32.0f / 11.0f)
#define STEER_RATIO (8.0f / 11.0f)

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
/* SET_TARGET_FF (0x110+unitId): steer angular-rate FF applied to the
 * controller, plus wheel-accel FF received/logged only (not yet consumed by
 * the controller -- reserved for a future extension). */
static bool ff_received = false;
static uint32_t last_ff_ms = 0U;
static uint32_t last_ff_log_ms = 0U;
static float can_steer_rate_ff_rpm = 0.0f;
static float can_steer_accel_ff_rpm_per_s = 0.0f;
static int32_t can_wheel_accel_ff_rpm_milli_per_s = 0;
static float applied_steer_rate_ff_rpm = 0.0f;
static float applied_steer_accel_ff_rpm_per_s = 0.0f;
/* Normal STATUS periods are defined above. SET_CONFIG index 22 temporarily
 * overrides STATUS1/2 to 1..100ms for bench identification; zero restores
 * the normal 20/50ms periods. */
static uint32_t status_period_ms = 0U;
static bool steer_in_band = false;
static bool wheel_in_band = false;
static bool motion_settled = false;
static bool settle_candidate_active = false;
static uint32_t settle_candidate_since_ms = 0U;

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

static void write_i32_le(uint8_t *data, int32_t value)
{
    const uint32_t raw = (uint32_t)value;
    data[0] = (uint8_t)raw;
    data[1] = (uint8_t)(raw >> 8U);
    data[2] = (uint8_t)(raw >> 16U);
    data[3] = (uint8_t)(raw >> 24U);
}

static void write_u16_le(uint8_t *data, uint16_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8U);
}

static void write_u32_le(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8U);
    data[2] = (uint8_t)(value >> 16U);
    data[3] = (uint8_t)(value >> 24U);
}

static void reset_settle_state(void)
{
    steer_in_band = false;
    wheel_in_band = false;
    motion_settled = false;
    settle_candidate_active = false;
    settle_candidate_since_ms = 0U;
}

static bool target_is_fresh(uint32_t now_ms)
{
    return target_received &&
           (uint32_t)(now_ms - last_target_ms) < TARGET_TIMEOUT_MS;
}

static bool ff_is_fresh(uint32_t now_ms)
{
    return ff_received &&
           (uint32_t)(now_ms - last_ff_ms) < TARGET_FF_TIMEOUT_MS;
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
    SET_CONFIG_STEER_ACCEL_FF_GAIN = 18U,
    SET_CONFIG_MOVING_ANGLE_KP = 19U,
    SET_CONFIG_STEER_DECEL_FF_GAIN = 20U,
    SET_CONFIG_STEER_FRICTION_FF_CURRENT = 21U,
    SET_CONFIG_STATUS_PERIOD_MS = 22U,
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
        /* Axis rpm; 60rpm = 360deg/s. Range x4 with the 8/11 ratio fix. */
        applied = clampf(value, 0.0f, 60.0f);
        controller.config.steer_max_rpm = applied;
        break;
    case SET_CONFIG_STEER_MIN_RPM:
        applied = clampf(value, 0.0f, 5.0f);
        controller.config.steer_min_rpm = applied;
        break;
    case SET_CONFIG_STEER_ACCEL_RPM_PER_S:
        applied = clampf(value, 0.0f, 2000.0f);
        controller.config.steer_accel_rpm_per_s = applied;
        break;
    case SET_CONFIG_WHEEL_ACCEL_RPM_PER_S:
        applied = clampf(value, 0.0f, 5000.0f);
        controller.config.wheel_accel_rpm_per_s = applied;
        break;
    case SET_CONFIG_MODE_INTEGRAL_LIMIT:
        applied = clampf(value, 0.0f, 2000.0f);
        controller.config.mode_integral_limit = applied;
        break;
    case SET_CONFIG_CURRENT_LIMIT:
        /* Ceiling raised 2000->6000 (~7.3A of C620's 20A full scale) with
         * user approval 2026-07-08 for response tuning; M3508 rated 10A
         * continuous. */
        applied = clampf(value, 0.0f, 6000.0f);
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
    case SET_CONFIG_STEER_ACCEL_FF_GAIN:
        applied = clampf(value, 0.0f, 10.0f);
        controller.config.steer_accel_ff_current_per_mode_rpm_per_s = applied;
        break;
    case SET_CONFIG_MOVING_ANGLE_KP:
        applied = clampf(value, 0.0f, 10.0f);
        controller.config.moving_angle_kp_rpm_per_deg = applied;
        break;
    case SET_CONFIG_STEER_DECEL_FF_GAIN:
        applied = clampf(value, 0.0f, 10.0f);
        controller.config.steer_decel_ff_current_per_mode_rpm_per_s = applied;
        break;
    case SET_CONFIG_STEER_FRICTION_FF_CURRENT:
        applied = clampf(value, 0.0f, 1000.0f);
        controller.config.steer_friction_ff_current = applied;
        break;
    case SET_CONFIG_STATUS_PERIOD_MS:
        /* Existing STATUS1/2 payloads, but at a bench-selected period. Zero
         * restores normal 20/50ms service. One millisecond is safe on the
         * otherwise lightly loaded central bench CAN and avoids blocking the
         * 1kHz loop on the 115200-baud debug UART. */
        applied = value <= 0.0f ? 0.0f : clampf(value, 1.0f, 100.0f);
        status_period_ms = (uint32_t)(applied + 0.5f);
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
                   frame.id == CAN_ID_SET_TARGET_FF && frame.dlc == 8U) {
            const int32_t steer_rate_ff_mdeg_per_s = read_i32_le(&frame.data[0]);
            const int32_t wheel_accel_ff_rpm_milli_per_s =
                read_i32_le(&frame.data[4]);
            const float new_steer_rate_ff_rpm =
                (float)steer_rate_ff_mdeg_per_s /
                (float)STEER_RATE_FF_MDEG_PER_S_TO_RPM_DIV;
            const uint32_t ff_period_ms = now_ms - last_ff_ms;
            if (ff_received && ff_period_ms > 0U && ff_period_ms <= 100U) {
                can_steer_accel_ff_rpm_per_s = clampf(
                    (new_steer_rate_ff_rpm - can_steer_rate_ff_rpm) *
                        (1000.0f / (float)ff_period_ms),
                    -1000.0f, 1000.0f);
            } else {
                can_steer_accel_ff_rpm_per_s = 0.0f;
            }
            can_steer_rate_ff_rpm = new_steer_rate_ff_rpm;
            can_wheel_accel_ff_rpm_milli_per_s = wheel_accel_ff_rpm_milli_per_s;
            last_ff_ms = now_ms;
            ff_received = true;
            if ((uint32_t)(now_ms - last_ff_log_ms) >= 500U) {
                last_ff_log_ms = now_ms;
                debug_printf("SET_TARGET_FF_RX steerRate=%d wheelAccel=%d\n",
                             steer_rate_ff_mdeg_per_s,
                             wheel_accel_ff_rpm_milli_per_s);
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

static void send_status2(void)
{
    fdcan_frame_t frame = {
        .id = CAN_ID_STATUS2,
        .dlc = 8U,
        .extended = false,
        .remote = false,
    };
    /* COMMUNICATION_NAMING_AND_IDS.md STATUS2: motor rotor rpm x1000.
     * C620 feedback rpm is already the signed motor-rotor speed. */
    write_i32_le(&frame.data[0], (int32_t)motors[0].feedback.rpm * 1000);
    write_i32_le(&frame.data[4], (int32_t)motors[1].feedback.rpm * 1000);
    (void)fdcan_send(FDCAN_BUS_CENTRAL, &frame);
}

static void send_status1(float steer_deg, float wheel_rpm)
{
    fdcan_frame_t frame = {
        .id = CAN_ID_STATUS1,
        .dlc = 8U,
        .extended = false,
        .remote = false,
    };
    write_i32_le(&frame.data[0], to_milli(steer_deg));
    write_i32_le(&frame.data[4], to_milli(wheel_rpm));
    (void)fdcan_send(FDCAN_BUS_CENTRAL, &frame);
}

static void send_status3(uint16_t status_flags, uint32_t error_flags)
{
    fdcan_frame_t frame = {
        .id = CAN_ID_STATUS3,
        .dlc = 8U,
        .extended = false,
        .remote = false,
    };
    /* Bus voltage ADC is not connected in this bench target. 0xffff is the
     * protocol's explicit "unavailable" value, not a fabricated reading. */
    write_u16_le(&frame.data[0], UINT16_MAX);
    write_u16_le(&frame.data[2], status_flags);
    write_u32_le(&frame.data[4], error_flags);
    (void)fdcan_send(FDCAN_BUS_CENTRAL, &frame);
}

int main(void)
{
    static const unit_controller_config_t control_config = {
        .motor_max_rpm = 469.0f,
        /* Rescaled x4 on 2026-07-08 when STEER_RATIO was corrected 2/11->8/11
         * (values are true steer-axis rpm now); physical behavior identical
         * to the tuned 10rpm/150 set: 90deg step <0.5deg in ~0.7-0.9s. */
        .steer_max_rpm = 40.0f,
        .steer_min_rpm = 0.0f,
        .steer_accel_rpm_per_s = 600.0f,
        /* 4000 + drive Kp=30 + current_limit 4000: 0->500rpm rise 0.41s,
         * full +-500 reversal 0.51s, steer held <1.2deg, current peak
         * ~3700, temp 29C (2026-07-08, user-approved limit raise). */
        .wheel_accel_rpm_per_s = 4000.0f,
        .angle_kp_rpm_per_deg = 4.0f,
        .moving_angle_kp_rpm_per_deg = 1.0f,
        .angle_deadband_deg = 0.3f,
        /* High-rate STATUS-based repeat test selected 120/50 with a 2ms
         * measured-mode filter. 11/12 moves met the 0.5deg dwell criterion;
         * the remaining cold/static-friction case ended at 0.088deg but
         * entered the band too late. This is the best current gain-only
         * package; see auto-tune/2026-07-30T17-31-36Z. */
        .steer_mode_kp = 120.0f,
        .steer_mode_ki = 50.0f,
        /* Kp=20 also trims the integral-floor overspeed bias at 25rpm to
         * ~+8% with no stick (see CONTROL_LOOP_TUNING.md 2026-07-08). */
        .drive_mode_kp = 30.0f,
        .drive_mode_ki = 20.0f,
        /* Above worst-case breakaway (~850-950 raw, 2026-07-05/06 measurements) so the
         * integral can still defeat static friction, below current_limit so a
         * stuck-phase charge cannot release as a full-limit jump. */
        .mode_integral_limit = 1200.0f,
        .mode_rpm_filter_tau_s = 0.002f,
        /* Raised 2000->4000 (~4.9A, M3508 rated 10A continuous) with user
         * approval 2026-07-08; acceleration peaks reach ~3700 with temps
         * steady at 29C on the bench. SET_CONFIG ceiling is 6000. */
        .current_limit = 4000.0f,
        .steer_motor_sign = 1.0f,
        /* Measured inertial FF gain at the adopted high-acceleration profile;
         * reduces braking overshoot without reaching the current clamp. */
        .steer_accel_ff_current_per_mode_rpm_per_s = 0.5f,
        .steer_decel_ff_current_per_mode_rpm_per_s = 0.5f,
        .steer_friction_ff_current = 0.0f,
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
    uint32_t last_status1_ms = last_control_ms;
    uint32_t last_status2_ms = last_control_ms;
    uint32_t last_status3_ms = last_control_ms;
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
            reset_settle_state();
        } else if (!active && unit_enabled && target_is_fresh(now_ms) &&
                   amt_ok && feedback_is_fresh(now_ms)) {
            active = true;
            test_target_deg = can_target_steer_deg;
            unit_controller_reset(&controller);
            reset_settle_state();
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
            reset_settle_state();
        }

        if (active && !target_is_fresh(now_ms)) {
            debug_printf("STOP: target timeout\n");
            active = false;
            unit_enabled = false;
            unit_controller_reset(&controller);
            reset_settle_state();
        }

        if (active && (!amt_ok || !feedback_is_fresh(now_ms))) {
            debug_printf("STOP: sensor/C620 timeout\n");
            active = false;
            unit_enabled = false;
            unit_controller_reset(&controller);
            reset_settle_state();
        }

        if (active && (motors[0].feedback.temperature_c >= MOTOR_TEMPERATURE_LIMIT_C ||
                       motors[1].feedback.temperature_c >= MOTOR_TEMPERATURE_LIMIT_C)) {
            debug_printf("STOP: motor temperature m1=%u m2=%u\n",
                         (uint32_t)motors[0].feedback.temperature_c,
                         (uint32_t)motors[1].feedback.temperature_c);
            active = false;
            unit_enabled = false;
            unit_controller_reset(&controller);
            reset_settle_state();
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
            /* FF falls back to 0 (pre-FF behavior) once stale/never received,
             * per the 200ms SET_TARGET_FF timeout. */
            applied_steer_rate_ff_rpm =
                ff_is_fresh(now_ms) ? can_steer_rate_ff_rpm : 0.0f;
            applied_steer_accel_ff_rpm_per_s =
                ff_is_fresh(now_ms) ? can_steer_accel_ff_rpm_per_s : 0.0f;
            unit_controller_set_steer_rate_ff_rpm(&controller,
                                                  applied_steer_rate_ff_rpm);
            unit_controller_set_steer_accel_ff_rpm_per_s(
                &controller, applied_steer_accel_ff_rpm_per_s);
            unit_controller_update(&controller, &measurement, dt_s, &output);

            if (absf(output.angle_error_deg) * 1000.0f >
                (float)ANGLE_DIVERGENCE_STOP_DEG_MILLI) {
                debug_printf("STOP: angle diverged err=%d\n",
                             to_milli(output.angle_error_deg));
                active = false;
                unit_enabled = false;
                unit_controller_reset(&controller);
                reset_settle_state();
            } else {
                current1 = output.motor1_current;
                current2 = output.motor2_current;

                const float steer_axis_measured_rpm =
                    output.steer_mode_measured_rpm * STEER_RATIO;
                const float wheel_measured_rpm =
                    output.drive_mode_measured_rpm * DRIVE_RATIO;
                const float wheel_band_rpm = clampf(
                    absf(can_target_wheel_rpm) * SETTLE_WHEEL_RELATIVE_BAND,
                    SETTLE_WHEEL_MIN_BAND_RPM, 100.0f);
                steer_in_band =
                    absf(output.angle_error_deg) <= SETTLE_ANGLE_BAND_DEG &&
                    absf(steer_axis_measured_rpm) <= SETTLE_STEER_AXIS_RPM &&
                    absf(applied_steer_rate_ff_rpm) <= SETTLE_FF_AXIS_RPM;
                wheel_in_band =
                    absf(wheel_measured_rpm - can_target_wheel_rpm) <=
                    wheel_band_rpm &&
                    can_wheel_accel_ff_rpm_milli_per_s <=
                        SETTLE_WHEEL_ACCEL_MILLI_RPM_PER_S &&
                    can_wheel_accel_ff_rpm_milli_per_s >=
                        -SETTLE_WHEEL_ACCEL_MILLI_RPM_PER_S;
                if (steer_in_band && wheel_in_band) {
                    if (!settle_candidate_active) {
                        settle_candidate_active = true;
                        settle_candidate_since_ms = now_ms;
                    }
                    motion_settled =
                        (uint32_t)(now_ms - settle_candidate_since_ms) >=
                        SETTLE_DWELL_MS;
                } else {
                    settle_candidate_active = false;
                    motion_settled = false;
                }
            }
        }

        send_currents(current1, current2);
        const uint32_t status1_period_ms = status_period_ms > 0U
            ? status_period_ms : STATUS1_NORMAL_PERIOD_MS;
        const uint32_t status2_period_ms = status_period_ms > 0U
            ? status_period_ms : STATUS2_NORMAL_PERIOD_MS;
        const float raw_motor1_output_rpm =
            (float)motors[0].feedback.rpm / (float)M3508_INTERNAL_REDUCTION;
        const float raw_motor2_output_rpm =
            (float)motors[1].feedback.rpm / (float)M3508_INTERNAL_REDUCTION;
        const float status_wheel_rpm = active
            ? output.drive_mode_measured_rpm * DRIVE_RATIO
            : (raw_motor1_output_rpm - raw_motor2_output_rpm) * 0.5f *
              DRIVE_RATIO;
        if ((uint32_t)(now_ms - last_status1_ms) >= status1_period_ms) {
            last_status1_ms = now_ms;
            send_status1(current_angle_deg, status_wheel_rpm);
        }
        if ((uint32_t)(now_ms - last_status2_ms) >= status2_period_ms) {
            last_status2_ms = now_ms;
            send_status2();
        }
        if ((uint32_t)(now_ms - last_status3_ms) >= STATUS3_PERIOD_MS) {
            last_status3_ms = now_ms;
            uint16_t status_flags = 0U;
            status_flags |= active ? STATUS_FLAG_ACTIVE : 0U;
            status_flags |= target_is_fresh(now_ms)
                ? STATUS_FLAG_TARGET_FRESH : 0U;
            status_flags |= feedback_is_fresh(now_ms)
                ? STATUS_FLAG_FEEDBACK_OK : 0U;
            status_flags |= amt_ok ? STATUS_FLAG_AMT_OK : 0U;
            status_flags |= steer_in_band ? STATUS_FLAG_STEER_IN_BAND : 0U;
            status_flags |= wheel_in_band ? STATUS_FLAG_WHEEL_IN_BAND : 0U;
            status_flags |= motion_settled ? STATUS_FLAG_MOTION_SETTLED : 0U;
            status_flags |= (active && output.limiting_active)
                ? STATUS_FLAG_LIMITING_ACTIVE : 0U;
            send_status3(status_flags, 0U);
        }
        status_led_write(active);

        if (active && (uint32_t)(now_ms - last_report_ms) >= REPORT_PERIOD_MS) {
            last_report_ms = now_ms;
            debug_printf("run=%u step=%u angle=%d target=%d err=%d steer=%d "
                         "m1=%d/%d i1=%d q1=%d t1=%u m2=%d/%d i2=%d q2=%d t2=%u "
                         "steerMode=%d/%d iSteer=%d sInt=%d "
                         "driveMode=%d/%d iDrive=%d dInt=%d mov=%u onset=%u onsetN=%u floor=%u scale=%u "
                         "wheel=%d ffS=%d ffA=%d aFF=%d\n",
                         active ? 1U : 0U, 0U,
                         to_milli(current_angle_deg),
                         to_milli(test_target_deg),
                         to_milli(output.angle_error_deg),
                         to_milli(output.steer_rpm_command),
                         (int32_t)motors[0].feedback.rpm,
                         to_milli(output.motor1_target_rpm),
                         (int32_t)current1,
                         (int32_t)motors[0].feedback.torque_current,
                         (uint32_t)motors[0].feedback.temperature_c,
                         (int32_t)motors[1].feedback.rpm,
                         to_milli(output.motor2_target_rpm),
                         (int32_t)current2,
                         (int32_t)motors[1].feedback.torque_current,
                         (uint32_t)motors[1].feedback.temperature_c,
                         to_milli(output.steer_mode_target_rpm),
                         to_milli(output.steer_mode_measured_rpm),
                         to_milli(output.steer_mode_current),
                         to_milli(output.steer_mode_integral),
                         to_milli(output.drive_mode_target_rpm),
                         to_milli(output.drive_mode_measured_rpm),
                         to_milli(output.drive_mode_current),
                         to_milli(output.drive_mode_integral),
                         (uint32_t)output.drive_in_motion,
                         (uint32_t)output.drive_onset_active,
                         output.drive_onset_count,
                         (uint32_t)output.drive_integral_floor_active,
                         (uint32_t)output.torque_scaling_active,
                         to_milli(output.wheel_rpm_command),
                         to_milli(applied_steer_rate_ff_rpm),
                         to_milli(applied_steer_accel_ff_rpm_per_s),
                         to_milli(output.steer_accel_ff_current));
        } else if (!active &&
                   (uint32_t)(now_ms - last_report_ms) >= IDLE_REPORT_PERIOD_MS) {
            last_report_ms = now_ms;
            debug_printf("idle angle=%d amtOk=%u fdbkOk=%u en=%u tgtOk=%u can2psr=%x\n",
                         to_milli(current_angle_deg), amt_ok ? 1U : 0U,
                         feedback_is_fresh(now_ms) ? 1U : 0U,
                         unit_enabled ? 1U : 0U,
                         target_is_fresh(now_ms) ? 1U : 0U,
                         fdcan_protocol_status(FDCAN_BUS_C620));
        }
    }
}
