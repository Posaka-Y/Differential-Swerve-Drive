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

#include "config/steer_calibration.h"
#include "control/unit_controller.h"
#include "platform/amt22.h"
#include "platform/bench_uart.h"
#include "platform/calibration_flash.h"
#include "platform/clock.h"
#include "platform/fdcan.h"
#include "platform/gpio.h"
#include "platform/uart.h"
#include "protocol/c620.h"

/* Bench-only transport: ESP32 GPIO UART -> USART1 PA9/PA10. Production
 * architecture remains the central CAN-FD bus. */
#define BENCH_CONTROL_UART_ENABLED 1
#define BENCH_SAVE_CURRENT_ZERO_ON_BOOT 0

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
    UNIT_CTRL_CALIB_START = 0x02U,
    UNIT_CTRL_CALIB_SAVE_ZERO = 0x03U,
    UNIT_CTRL_CALIB_CLEAR = 0x04U,
    UNIT_CTRL_PING = 0x05U,
    CAN_ID_SET_CONFIG_BASE = 0x140U,
    CAN_ID_SET_CONFIG = CAN_ID_SET_CONFIG_BASE + UNIT_ID,
    /* Classic-CAN bench companion to TRAJECTORY_FD.thetaDDot.  Production
     * coordinated control will carry this value in TRAJECTORY_FD; keeping a
     * separate 8-byte frame here lets the current MTU=16 bench exercise the
     * same explicit-acceleration path without changing SET_TARGET_FF. */
    CAN_ID_SET_TARGET_ACCEL_FF_BASE = 0x160U,
    CAN_ID_SET_TARGET_ACCEL_FF = CAN_ID_SET_TARGET_ACCEL_FF_BASE + UNIT_ID,
    CAN_ID_STATUS1_BASE = 0x180U,
    CAN_ID_STATUS1 = CAN_ID_STATUS1_BASE + UNIT_ID,
    CAN_ID_STATUS2_BASE = 0x190U,
    CAN_ID_STATUS2 = CAN_ID_STATUS2_BASE + UNIT_ID,
    CAN_ID_STATUS3_BASE = 0x1A0U,
    CAN_ID_STATUS3 = CAN_ID_STATUS3_BASE + UNIT_ID,
    CAN_ID_UNIT_STATUS_DIAG_BASE = 0x1B0U,
    CAN_ID_UNIT_STATUS_DIAG = CAN_ID_UNIT_STATUS_DIAG_BASE + UNIT_ID,
    CAN_ID_CALIB_RESULT_BASE = 0x1C0U,
    CAN_ID_CALIB_RESULT = CAN_ID_CALIB_RESULT_BASE + UNIT_ID,
    TARGET_TIMEOUT_MS = 200U,
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
    /* mdeg/s^2 -> axis rpm/s uses the same degree/revolution conversion. */
    STEER_ACCEL_FF_MDEG_PER_S2_TO_RPM_PER_S_DIV = 6000,
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
    STATUS_FLAG_CALIBRATED = 1U << 8,
    STATUS_FLAG_CONFIG_CRC_ERROR = 1U << 9,
    STATUS_FLAG_CALIB_PAGE_FULL = 1U << 10,
    STATUS_FLAG_TORQUE_SCALING_ACTIVE = 1U << 11,
    STATUS_FLAG_STEER_BRAKING_ACTIVE = 1U << 12,
};

enum {
    ERROR_FLAG_NOT_CALIBRATED = 1UL << 6,
    ERROR_FLAG_CONFIG_CRC = 1UL << 8,
};

enum {
    CALIB_RESULT_CALIBRATED = 1U << 0,
    CALIB_RESULT_CRC_ERROR = 1U << 1,
    CALIB_RESULT_PAGE_FULL = 1U << 2,
    CALIB_RESULT_LAST_OP_FAILED = 1U << 3,
    CALIB_RESULT_RAW_FRESH = 1U << 4,
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
/* A local safety stop must not be undone by the next 20ms UART frame while
 * the operator still holds the deadman. It is cleared only after an explicit
 * enable=0 frame (R1 released). */
static bool enable_rearm_required = false;
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
/* Legacy fallback derived from SET_TARGET_FF receive intervals. */
static float can_steer_accel_ff_rpm_per_s = 0.0f;
static int32_t can_wheel_accel_ff_rpm_milli_per_s = 0;
/* Explicit bench thetaDDot. Fresh explicit data takes precedence over the
 * receive-time derivative above; timeout restores backward compatibility. */
static bool accel_ff_received = false;
static uint32_t last_accel_ff_ms = 0U;
static float can_explicit_steer_accel_ff_rpm_per_s = 0.0f;
static float applied_steer_rate_ff_rpm = 0.0f;
static float applied_steer_accel_ff_rpm_per_s = 0.0f;
static bool applied_steer_accel_ff_is_explicit = false;
/* Normal STATUS periods are defined above. SET_CONFIG index 22 temporarily
 * overrides STATUS1/2 to 1..100ms for bench identification; zero restores
 * the normal 20/50ms periods. */
static uint32_t status_period_ms = 0U;
static bool steer_in_band = false;
static bool wheel_in_band = false;
static bool motion_settled = false;
static bool settle_candidate_active = false;
static uint32_t settle_candidate_since_ms = 0U;
static bool latest_amt_ok = false;
static uint16_t latest_amt_position = 0U;
static uint32_t latest_amt_ms = 0U;
static bool calibration_last_op_failed = false;

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

static void write_i16_le(uint8_t *data, int16_t value)
{
    write_u16_le(data, (uint16_t)value);
}

static int16_t float_to_i16(float value)
{
    const float clamped = clampf(value, -32768.0f, 32767.0f);
    return (int16_t)(clamped >= 0.0f ? clamped + 0.5f : clamped - 0.5f);
}

static uint16_t float_to_u16_scaled(float value, float scale)
{
    const float scaled = clampf(value * scale, 0.0f, 65535.0f);
    return (uint16_t)(scaled + 0.5f);
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

static bool explicit_accel_ff_is_fresh(uint32_t now_ms)
{
    return accel_ff_received &&
           (uint32_t)(now_ms - last_accel_ff_ms) < TARGET_FF_TIMEOUT_MS;
}

static bool calibration_raw_is_fresh(uint32_t now_ms)
{
    return latest_amt_ok && (uint32_t)(now_ms - latest_amt_ms) < 100U;
}

static bool calibration_motion_is_stopped(uint32_t now_ms)
{
    return !unit_enabled && calibration_raw_is_fresh(now_ms) &&
           motors[0].received && motors[1].received &&
           (uint32_t)(now_ms - motors[0].last_rx_ms) < FEEDBACK_TIMEOUT_MS &&
           (uint32_t)(now_ms - motors[1].last_rx_ms) < FEEDBACK_TIMEOUT_MS &&
           motors[0].feedback.rpm >= -(int16_t)M3508_INTERNAL_REDUCTION &&
           motors[0].feedback.rpm <= (int16_t)M3508_INTERNAL_REDUCTION &&
           motors[1].feedback.rpm >= -(int16_t)M3508_INTERNAL_REDUCTION &&
           motors[1].feedback.rpm <= (int16_t)M3508_INTERNAL_REDUCTION;
}

static void send_calibration_result(uint32_t now_ms)
{
    const calibration_flash_status_t calibration = calibration_flash_status();
    uint16_t flags = 0U;
    flags |= calibration.calibrated ? CALIB_RESULT_CALIBRATED : 0U;
    flags |= calibration.crc_error ? CALIB_RESULT_CRC_ERROR : 0U;
    flags |= calibration.page_full ? CALIB_RESULT_PAGE_FULL : 0U;
    flags |= calibration_last_op_failed ? CALIB_RESULT_LAST_OP_FAILED : 0U;
    flags |= calibration_raw_is_fresh(now_ms) ? CALIB_RESULT_RAW_FRESH : 0U;
    fdcan_frame_t frame = {
        .id = CAN_ID_CALIB_RESULT,
        .dlc = 8U,
        .extended = false,
        .remote = false,
    };
    write_u16_le(&frame.data[0], calibration.calibrated
        ? calibration.zero_position_counts : UINT16_MAX);
    write_u16_le(&frame.data[2], calibration_raw_is_fresh(now_ms)
        ? latest_amt_position : UINT16_MAX);
    write_u16_le(&frame.data[4], (uint16_t)calibration.sequence);
    write_u16_le(&frame.data[6], flags);
    (void)fdcan_send(FDCAN_BUS_CENTRAL, &frame);
}

static void handle_calibration_command(uint8_t command, uint32_t now_ms)
{
    bool attempted = false;
    bool ok = true;
    if (command == UNIT_CTRL_CALIB_START || command == UNIT_CTRL_PING) {
        ok = command == UNIT_CTRL_PING || !unit_enabled;
    } else if (command == UNIT_CTRL_CALIB_SAVE_ZERO) {
        attempted = true;
        ok = calibration_motion_is_stopped(now_ms) &&
             calibration_flash_save_zero(latest_amt_position);
    } else if (command == UNIT_CTRL_CALIB_CLEAR) {
        attempted = true;
        ok = calibration_motion_is_stopped(now_ms) &&
             calibration_flash_clear();
    } else {
        return;
    }
    calibration_last_op_failed = !ok;
    const calibration_flash_status_t calibration = calibration_flash_status();
    debug_printf("CALIB cmd=%u ok=%u raw=%u zero=%u seq=%u flags=%x\n",
                 (uint32_t)command, ok ? 1U : 0U,
                 calibration_raw_is_fresh(now_ms)
                     ? (uint32_t)latest_amt_position : UINT32_MAX,
                 calibration.calibrated
                     ? (uint32_t)calibration.zero_position_counts : UINT32_MAX,
                 calibration.sequence,
                 (calibration.calibrated ? CALIB_RESULT_CALIBRATED : 0U) |
                 (calibration.crc_error ? CALIB_RESULT_CRC_ERROR : 0U) |
                 (calibration.page_full ? CALIB_RESULT_PAGE_FULL : 0U) |
                 (!ok ? CALIB_RESULT_LAST_OP_FAILED : 0U));
    if (attempted && ok) {
        unit_controller_reset(&controller);
        reset_settle_state();
    }
    send_calibration_result(now_ms);
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
    SET_CONFIG_STEER_OBSERVER_TAU_S = 23U,
    SET_CONFIG_STEER_FRICTION_FF_FADE_AXIS_RPM = 24U,
    SET_CONFIG_STEER_BACKCALC_GAIN = 25U,
    SET_CONFIG_DRIVE_BACKCALC_GAIN = 26U,
    /* Four knots x five fields, ordered kp/ki/accelFF/decelFF/Kaw.
     * Indices 27..46 let bench tools tune one speed band without changing
     * the legacy scalar indices 3/4/18/20/25 (which still mean all bands). */
    SET_CONFIG_STEER_GAIN_KNOT_BASE = 27U,
    SET_CONFIG_STEER_GAIN_KNOT_END = 47U,
    SET_CONFIG_STEER_BRAKE_KP_MULTIPLIER = 47U,
    SET_CONFIG_STEER_BRAKE_KP_KNOT_BASE = 48U,
    SET_CONFIG_STEER_BRAKE_KP_KNOT_END = 52U,
};

enum {
    STEER_GAIN_KNOT_FIELD_KP = 0U,
    STEER_GAIN_KNOT_FIELD_KI = 1U,
    STEER_GAIN_KNOT_FIELD_ACCEL_FF = 2U,
    STEER_GAIN_KNOT_FIELD_DECEL_FF = 3U,
    STEER_GAIN_KNOT_FIELD_BACKCALC = 4U,
    STEER_GAIN_KNOT_FIELD_COUNT = 5U,
};

static void apply_set_config(uint8_t idx, int32_t value_milli)
{
    const float value = (float)value_milli * 0.001f;
    float applied;
    if (idx >= SET_CONFIG_STEER_GAIN_KNOT_BASE &&
        idx < SET_CONFIG_STEER_GAIN_KNOT_END) {
        const uint8_t offset = idx - SET_CONFIG_STEER_GAIN_KNOT_BASE;
        const uint8_t knot_index = offset / STEER_GAIN_KNOT_FIELD_COUNT;
        const uint8_t field = offset % STEER_GAIN_KNOT_FIELD_COUNT;
        unit_steer_gain_knot_t knot = controller.steer_gain_knots[knot_index];
        switch (field) {
        case STEER_GAIN_KNOT_FIELD_KP:
            applied = clampf(value, 0.0f, 500.0f);
            knot.mode_kp = applied;
            break;
        case STEER_GAIN_KNOT_FIELD_KI:
            applied = clampf(value, 0.0f, 500.0f);
            knot.mode_ki = applied;
            break;
        case STEER_GAIN_KNOT_FIELD_ACCEL_FF:
            applied = clampf(value, 0.0f, 10.0f);
            knot.accel_ff_gain = applied;
            break;
        case STEER_GAIN_KNOT_FIELD_DECEL_FF:
            applied = clampf(value, 0.0f, 10.0f);
            knot.decel_ff_gain = applied;
            break;
        case STEER_GAIN_KNOT_FIELD_BACKCALC:
        default:
            applied = clampf(value, 0.0f, 20.0f);
            knot.backcalc_gain = applied;
            break;
        }
        (void)unit_controller_set_steer_gain_knot(
            &controller, knot_index, knot.mode_kp, knot.mode_ki,
            knot.accel_ff_gain, knot.decel_ff_gain, knot.backcalc_gain);
        debug_printf("SET_CONFIG idx=%u val=%d\n",
                     (uint32_t)idx, to_milli(applied));
        return;
    }
    if (idx >= SET_CONFIG_STEER_BRAKE_KP_KNOT_BASE &&
        idx < SET_CONFIG_STEER_BRAKE_KP_KNOT_END) {
        const uint8_t knot_index =
            idx - SET_CONFIG_STEER_BRAKE_KP_KNOT_BASE;
        applied = clampf(value, 1.0f, 4.0f);
        (void)unit_controller_set_steer_brake_kp_knot(
            &controller, knot_index, applied);
        debug_printf("SET_CONFIG idx=%u val=%d\n",
                     (uint32_t)idx, to_milli(applied));
        return;
    }
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
        unit_controller_set_uniform_steer_gain_schedule(&controller);
        break;
    case SET_CONFIG_STEER_MODE_KI:
        applied = clampf(value, 0.0f, 500.0f);
        controller.config.steer_mode_ki = applied;
        unit_controller_set_uniform_steer_gain_schedule(&controller);
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
        /* Axis rpm.  The runtime tuning ceiling follows the wheel=0 hard
         * motor envelope: 469 * (8/11) = 341.1 axis rpm.  The much lower
         * commissioning guard (currently 60rpm, then 80/100rpm) is owned by
         * the central/Web profiler; unit_controller_update() independently
         * projects combined steer+drive demand onto the 469rpm diamond. */
        applied = clampf(value, 0.0f, 341.1f);
        controller.config.steer_max_rpm = applied;
        break;
    case SET_CONFIG_STEER_MIN_RPM:
        applied = clampf(value, 0.0f, 5.0f);
        controller.config.steer_min_rpm = applied;
        break;
    case SET_CONFIG_STEER_ACCEL_RPM_PER_S:
        /* This is the unit-local target-rate guard, not the normal motion
         * profiler. The central profiler publishes explicit acceleration up
         * to 2000 axis rpm/s (12000deg/s2), so allow 2x headroom here to
         * avoid stacking two equal ramps while retaining a finite fallback
         * limit for stale/legacy target senders. Boot default stays 600. */
        applied = clampf(value, 0.0f, 4000.0f);
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
        unit_controller_set_uniform_steer_gain_schedule(&controller);
        break;
    case SET_CONFIG_MOVING_ANGLE_KP:
        applied = clampf(value, 0.0f, 10.0f);
        controller.config.moving_angle_kp_rpm_per_deg = applied;
        break;
    case SET_CONFIG_STEER_DECEL_FF_GAIN:
        applied = clampf(value, 0.0f, 10.0f);
        controller.config.steer_decel_ff_current_per_mode_rpm_per_s = applied;
        unit_controller_set_uniform_steer_gain_schedule(&controller);
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
    case SET_CONFIG_STEER_OBSERVER_TAU_S:
        /* Zero is a useful diagnostic (AMT-direct estimate); normal tuning
         * range is milliseconds to one second. */
        applied = clampf(value, 0.0f, 1.0f);
        controller.config.steer_observer_correction_tau_s = applied;
        break;
    case SET_CONFIG_STEER_FRICTION_FF_FADE_AXIS_RPM:
        applied = clampf(value, 0.0f, 100.0f);
        controller.config.steer_friction_ff_fade_axis_rpm = applied;
        break;
    case SET_CONFIG_STEER_BACKCALC_GAIN:
        applied = clampf(value, 0.0f, 20.0f);
        controller.config.steer_mode_backcalc_gain = applied;
        unit_controller_set_uniform_steer_gain_schedule(&controller);
        break;
    case SET_CONFIG_DRIVE_BACKCALC_GAIN:
        applied = clampf(value, 0.0f, 20.0f);
        controller.config.drive_mode_backcalc_gain = applied;
        break;
    case SET_CONFIG_STEER_BRAKE_KP_MULTIPLIER:
        applied = clampf(value, 1.0f, 4.0f);
        controller.config.steer_brake_kp_multiplier = applied;
        unit_controller_set_uniform_steer_brake_kp_schedule(&controller);
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
                   frame.id == CAN_ID_SET_TARGET_ACCEL_FF && frame.dlc == 8U) {
            const int32_t steer_accel_ff_mdeg_per_s2 =
                read_i32_le(&frame.data[0]);
            /* Match the unit's current 2000 axis-rpm/s commissioning guard.
             * This removes the legacy derivative's tighter +/-1000 clamp
             * without allowing a bench sender to bypass the local limit. */
            can_explicit_steer_accel_ff_rpm_per_s = clampf(
                (float)steer_accel_ff_mdeg_per_s2 /
                    (float)STEER_ACCEL_FF_MDEG_PER_S2_TO_RPM_PER_S_DIV,
                -2000.0f, 2000.0f);
            last_accel_ff_ms = now_ms;
            accel_ff_received = true;
        } else if (!frame.extended && !frame.remote &&
                   frame.id == CAN_ID_UNIT_CTRL && frame.dlc >= 2U) {
            if (frame.data[0] == UNIT_CTRL_SET_ENABLE) {
                unit_enabled = frame.data[1] != 0U;
                debug_printf("UNIT_CTRL enable=%u\n", unit_enabled ? 1U : 0U);
            } else {
                handle_calibration_command(frame.data[0], now_ms);
            }
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

static void receive_bench_uart(uint32_t now_ms)
{
    bench_uart_command_t command;
    while (bench_uart_receive_command(&command)) {
        const bool first_command = !target_received;
        can_target_steer_deg = (float)command.steer_mdeg * 0.001f;
        can_target_wheel_rpm = (float)command.wheel_rpm_milli * 0.001f;
        last_target_ms = now_ms;
        target_received = true;
        const bool previous_enabled = unit_enabled;
        if (!command.enable) {
            unit_enabled = false;
            enable_rearm_required = false;
        } else if (!enable_rearm_required) {
            unit_enabled = true;
        }
        if (unit_enabled != previous_enabled) {
            debug_printf("UART_CTRL enable=%u\n", unit_enabled ? 1U : 0U);
        }
        if (first_command) {
            last_target_log_ms = now_ms;
            debug_printf("UART_LINK_OK steer=%d wheel=%d\n",
                         command.steer_mdeg, command.wheel_rpm_milli);
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
     * protocol's explicit "unavailable" value, not a fabricated reading.
     *
     * On the custom unit board the 5 V rail reaches PA0 through R13/R14.
     * Those are 22k (high side) / 10k (low side) as of 2026-09-21, not the
     * 33k/22k the older docs show, so the conversion is
     *   Vin = raw / 4095.0f * 3.3f / 0.3125f
     * See docs/ARCHITECTURE_DECISIONS.md for why the divider changed. */
    write_u16_le(&frame.data[0], UINT16_MAX);
    write_u16_le(&frame.data[2], status_flags);
    write_u32_le(&frame.data[4], error_flags);
    (void)fdcan_send(FDCAN_BUS_CENTRAL, &frame);
}

/* Classic-CAN migration form of UNIT_STATUS_FD. The final FD transport will
 * replace these four 8-byte pages on the same 0x1B0+id identifier. Keeping
 * it page-multiplexed now avoids extending the blocking 115200-baud debug
 * line, which would perturb the 1kHz loop being measured. */
static void send_unit_status_diag(bool active, uint8_t page)
{
    fdcan_frame_t frame = {
        .id = CAN_ID_UNIT_STATUS_DIAG,
        .dlc = 8U,
        .extended = false,
        .remote = false,
    };
    const uint8_t diag_flags = active
        ? ((output.torque_scaling_active ? 1U : 0U) |
           (output.steer_braking_active ? 2U : 0U) |
           (applied_steer_accel_ff_is_explicit ? 4U : 0U))
        : 0U;
    frame.data[0] = page;
    frame.data[1] = diag_flags;
    if (page == 0U) {
        write_u16_le(&frame.data[2], float_to_u16_scaled(
            active ? output.steer_schedule_rpm : 0.0f, 100.0f));
        write_u16_le(&frame.data[4], float_to_u16_scaled(
            active ? output.scheduled_steer_mode_kp : 0.0f, 10.0f));
        write_u16_le(&frame.data[6], float_to_u16_scaled(
            active ? output.scheduled_steer_mode_ki : 0.0f, 10.0f));
    } else if (page == 1U) {
        write_u16_le(&frame.data[2], float_to_u16_scaled(
            active ? output.scheduled_steer_accel_ff_gain : 0.0f,
            1000.0f));
        write_u16_le(&frame.data[4], float_to_u16_scaled(
            active ? output.scheduled_steer_decel_ff_gain : 0.0f,
            1000.0f));
        write_u16_le(&frame.data[6], active &&
            output.steer_saturation_duration_ms < UINT16_MAX
            ? (uint16_t)output.steer_saturation_duration_ms
            : (active ? UINT16_MAX : 0U));
    } else if (page == 2U) {
        write_i16_le(&frame.data[2], float_to_i16(
            active ? output.steer_mode_current_unsaturated : 0.0f));
        write_i16_le(&frame.data[4], float_to_i16(
            active ? output.steer_mode_current_applied : 0.0f));
        write_i16_le(&frame.data[6], float_to_i16(
            active ? output.steer_saturation_residual : 0.0f));
    } else {
        write_u16_le(&frame.data[2], float_to_u16_scaled(
            active ? output.scheduled_steer_backcalc_gain : 0.0f, 1000.0f));
        write_i16_le(&frame.data[4], float_to_i16(
            active ? output.steer_backcalc_correction * 1000.0f : 0.0f));
        write_i16_le(&frame.data[6], float_to_i16(
            active ? output.drive_backcalc_correction * 1000.0f : 0.0f));
    }
    (void)fdcan_send(FDCAN_BUS_CENTRAL, &frame);
}

int main(void)
{
    static const unit_controller_config_t control_config = {
        .motor_max_rpm = 469.0f,
        /* Rescaled x4 on 2026-07-08 when STEER_RATIO was corrected 2/11->8/11
         * (values are true steer-axis rpm now); physical behavior identical
         * to the tuned 10rpm/150 set: 90deg step <0.5deg in ~0.7-0.9s. */
        /* 40->60rpm commissioning stage accepted 26/26 across wheel=0/265,
         * absolute-angle boundary and 90deg tests on 2026-07-31. */
        .steer_max_rpm = 60.0f,
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
         * package; see auto-tune/2026-07-30T17-31-36Z.
         *
         * 2026-07-31: a wheel=0 outer-loop-disabled step/PRBS grid found
         * Kp=60/Ki=100 gives a cleaner isolated mode-velocity step response
         * (0% overshoot vs 34% for Kp=120 at Ki=0). Tried it as the new
         * default and flashed it, but a same-day closed-loop A/B via
         * unit_web_ui.py's production profile + MOTION_SETTLED (the metric
         * that actually matters) showed it REGRESSES real 90deg convergence:
         * ~1.8-3.7s (one 6s+ non-convergence) vs 120/50's steady ~1.1-1.2s
         * over 6 trials each. Lower Kp slows the inner loop's response to
         * the outer angle-P loop's velocity commands enough to hurt final
         * approach/settling, which the open-loop mode-step test can't see.
         * Reverted to 120/50. Lesson: validate any inner-loop candidate
         * against the full closed-loop MOTION_SETTLED metric before
         * adopting it, not just the isolated step/PRBS response. */
        .steer_mode_kp = 120.0f,
        .steer_mode_ki = 50.0f,
        .steer_brake_kp_multiplier = 1.0f,
        /* Kp=20 also trims the integral-floor overspeed bias at 25rpm to
         * ~+8% with no stick (see CONTROL_LOOP_TUNING.md 2026-07-08). */
        .drive_mode_kp = 30.0f,
        .drive_mode_ki = 20.0f,
        /* Enabled only after saturation A/B. Zero exactly preserves the
         * adopted conditional-integration controller. */
        .steer_mode_backcalc_gain = 0.0f,
        .drive_mode_backcalc_gain = 0.0f,
        /* Above worst-case breakaway (~850-950 raw, 2026-07-05/06 measurements) so the
         * integral can still defeat static friction, below current_limit so a
         * stuck-phase charge cannot release as a full-limit jump. */
        .mode_integral_limit = 1200.0f,
        .mode_rpm_filter_tau_s = 0.002f,
        .steer_schedule_filter_tau_s = 0.010f,
        /* Complementary observer: motor-mode velocity is the high-frequency
         * predictor, AMT22 angle corrects drift over 50ms. The estimated rate
         * schedules friction FF; angle feedback and settled checks stay raw. */
        .steer_observer_correction_tau_s = 0.050f,
        /* Raised 2000->4000 (~4.9A, M3508 rated 10A continuous) with user
         * approval 2026-07-08; acceleration peaks reach ~3700 with temps
         * steady at 29C on the bench. SET_CONFIG ceiling is 6000. */
        .current_limit = 4000.0f,
        .steer_motor_sign = 1.0f,
        /* Measured inertial FF gain at the adopted high-acceleration profile;
         * reduces braking overshoot without reaching the current clamp. */
        .steer_accel_ff_current_per_mode_rpm_per_s = 0.5f,
        .steer_decel_ff_current_per_mode_rpm_per_s = 0.5f,
        /* 2026-07-31: tapered to 0 above WHEEL_LOW_SPEED_TRANSITION_RPM=30 in
         * unit_controller.c, so this only assists the wheel=0/near-0 case
         * (the stick-slip stall diagnosis and A/B in firmware/PROGRESS.md).
         * A flat (non-tapered) 200-300 fixed the wheel=0 stall too but
         * regressed wheel=265rpm convergence 1.1-1.4s -> 2.4-4.0s; with the
         * taper wheel=265/600rpm A/B showed no regression (1.18-1.44s). */
        .steer_friction_ff_current = 200.0f,
        /* Full breakaway assist at rest, linearly removed by 10 axis rpm.
         * A/B on 2026-07-31 cut wheel=0 mean settle 0.956->0.757s and
         * worst 2.040->0.975s without changing wheel>=30rpm behavior. */
        .steer_friction_ff_fade_axis_rpm = 10.0f,
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
    bench_uart_init(115200U);
    amt22_init();
    unit_controller_init(&controller, &control_config);
    calibration_flash_init();

#if BENCH_SAVE_CURRENT_ZERO_ON_BOOT
    /* One-shot bench calibration image. The caller has positioned the lifted,
     * disabled unit at mechanical zero. Restore this macro to 0 immediately
     * after verifying the stored position. */
    clock_delay_ms(250U);
    amt22_sample_t zero_sample;
    const bool zero_read_ok = amt22_read(&zero_sample) &&
                              zero_sample.check_bits_ok;
    const bool zero_save_ok = zero_read_ok &&
                              calibration_flash_save_zero(zero_sample.position);
    debug_printf("ZERO_ON_BOOT raw=%u read=%u save=%u\n",
                 zero_read_ok ? (uint32_t)zero_sample.position : UINT32_MAX,
                 zero_read_ok ? 1U : 0U,
                 zero_save_ok ? 1U : 0U);
#endif

    const calibration_flash_status_t boot_calibration = calibration_flash_status();

    debug_printf("\n=== CAN target differential unit test ===\n");
    debug_printf("WHEEL MUST BE LIFTED CLEAR OF THE GROUND before UNIT_CTRL enable.\n");
    debug_printf("boots disabled; press B1 any time to abort and latch disabled\n");
    debug_printf("calibration: valid=%u zero=%u seq=%u crcErr=%u full=%u\n",
                 boot_calibration.calibrated ? 1U : 0U,
                 boot_calibration.calibrated
                     ? (uint32_t)boot_calibration.zero_position_counts : UINT32_MAX,
                 boot_calibration.sequence,
                 boot_calibration.crc_error ? 1U : 0U,
                 boot_calibration.page_full ? 1U : 0U);
    debug_printf("limit=%d iLimit=%d wheelAccel=%drpm/s targetTimeout=%ums\n",
                 (int32_t)control_config.current_limit,
                 (int32_t)control_config.mode_integral_limit,
                 (int32_t)control_config.wheel_accel_rpm_per_s,
                 TARGET_TIMEOUT_MS);
    clock_delay_ms(250U);

#if !BENCH_CONTROL_UART_ENABLED
    if (!fdcan_init(FDCAN_BUS_CENTRAL, FDCAN_MODE_NORMAL)) {
        debug_printf("FDCAN1 init FAILED\n");
        for (;;) {
            status_led_write(((clock_millis() / 100U) & 1U) != 0U);
        }
    }
#endif

    if (!fdcan_init(FDCAN_BUS_C620, FDCAN_MODE_NORMAL)) {
        debug_printf("FDCAN2 init FAILED\n");
        for (;;) {
            status_led_write(((clock_millis() / 100U) & 1U) != 0U);
        }
    }

    send_currents(0, 0);
    debug_printf("ready: UART1 PA9/TX PC5/RX 115200 CRC8, unitId=%u\n",
                 UNIT_ID);

    bool active = false;
    uint32_t last_control_ms = clock_millis();
    uint32_t last_report_ms = last_control_ms;
    uint32_t last_status1_ms = last_control_ms;
    uint32_t last_status2_ms = last_control_ms;
    uint32_t last_status3_ms = last_control_ms;
    uint32_t last_status_diag_ms = last_control_ms;
    uint8_t status_diag_page = 0U;
    float current_angle_deg = 0.0f;
    float test_target_deg = 0.0f;

    for (;;) {
        const uint32_t now_ms = clock_millis();
#if BENCH_CONTROL_UART_ENABLED
        receive_bench_uart(now_ms);
#else
        receive_central_can(now_ms);
#endif
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
            latest_amt_ok = true;
            latest_amt_position = encoder.position;
            latest_amt_ms = now_ms;
            const calibration_flash_status_t calibration =
                calibration_flash_status();
            const uint16_t calibrated_position = calibration.calibrated
                ? steer_calibration_apply(encoder.position,
                                          calibration.zero_position_counts)
                : encoder.position;
            current_angle_deg =
                (float)calibrated_position * (360.0f / 4096.0f);
        } else {
            latest_amt_ok = false;
        }

        const bool pressed = user_button_is_pressed();
        if (active && pressed) {
            debug_printf("STOP: B1 abort\n");
            active = false;
            unit_enabled = false;
            enable_rearm_required = true;
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
            enable_rearm_required = true;
            unit_controller_reset(&controller);
            reset_settle_state();
        }

        if (active && (!amt_ok || !feedback_is_fresh(now_ms))) {
            debug_printf("STOP: sensor/C620 timeout\n");
            active = false;
            unit_enabled = false;
            enable_rearm_required = true;
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
            enable_rearm_required = true;
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
            applied_steer_accel_ff_is_explicit =
                explicit_accel_ff_is_fresh(now_ms);
            applied_steer_accel_ff_rpm_per_s =
                applied_steer_accel_ff_is_explicit
                ? can_explicit_steer_accel_ff_rpm_per_s
                : (ff_is_fresh(now_ms)
                   ? can_steer_accel_ff_rpm_per_s : 0.0f);
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
                enable_rearm_required = true;
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
#if BENCH_CONTROL_UART_ENABLED
            bench_uart_send_status(to_milli(current_angle_deg),
                                   to_milli(status_wheel_rpm), active);
#else
            send_status1(current_angle_deg, status_wheel_rpm);
#endif
        }
#if !BENCH_CONTROL_UART_ENABLED
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
            const calibration_flash_status_t calibration =
                calibration_flash_status();
            status_flags |= calibration.calibrated
                ? STATUS_FLAG_CALIBRATED : 0U;
            status_flags |= calibration.crc_error
                ? STATUS_FLAG_CONFIG_CRC_ERROR : 0U;
            status_flags |= calibration.page_full
                ? STATUS_FLAG_CALIB_PAGE_FULL : 0U;
            status_flags |= (active && output.torque_scaling_active)
                ? STATUS_FLAG_TORQUE_SCALING_ACTIVE : 0U;
            status_flags |= (active && output.steer_braking_active)
                ? STATUS_FLAG_STEER_BRAKING_ACTIVE : 0U;
            uint32_t error_flags = 0U;
            error_flags |= calibration.calibrated
                ? 0U : ERROR_FLAG_NOT_CALIBRATED;
            error_flags |= calibration.crc_error
                ? ERROR_FLAG_CONFIG_CRC : 0U;
            send_status3(status_flags, error_flags);
        }
        if ((uint32_t)(now_ms - last_status_diag_ms) >= status1_period_ms) {
            last_status_diag_ms = now_ms;
            send_unit_status_diag(active, status_diag_page);
            status_diag_page = (uint8_t)((status_diag_page + 1U) % 4U);
        }
#else
        (void)status2_period_ms;
        (void)last_status2_ms;
        (void)last_status3_ms;
        (void)last_status_diag_ms;
        (void)status_diag_page;
#endif
        status_led_write(active);

        if (active && (uint32_t)(now_ms - last_report_ms) >= REPORT_PERIOD_MS) {
            last_report_ms = now_ms;
#if BENCH_CONTROL_UART_ENABLED
            debug_printf("run angle=%d target=%d wheel=%d en=%u tgt=%u\n",
                         to_milli(current_angle_deg),
                         to_milli(test_target_deg),
                         to_milli(output.drive_mode_measured_rpm * DRIVE_RATIO),
                         unit_enabled ? 1U : 0U,
                         target_is_fresh(now_ms) ? 1U : 0U);
#else
            debug_printf("run=%u step=%u angle=%d target=%d err=%d steer=%d "
                         "m1=%d/%d i1=%d q1=%d t1=%u m2=%d/%d i2=%d q2=%d t2=%u "
                         "steerMode=%d/%d iSteer=%d sInt=%d "
                         "driveMode=%d/%d iDrive=%d dInt=%d mov=%u onset=%u onsetN=%u floor=%u scale=%u "
                         "wheel=%d ffS=%d ffA=%d ffExplicit=%u aFF=%d "
                         "obsA=%d obsR=%d obsE=%d\n",
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
                         applied_steer_accel_ff_is_explicit ? 1U : 0U,
                         to_milli(output.steer_accel_ff_current),
                         to_milli(output.steer_angle_observer_deg),
                         to_milli(output.steer_axis_observer_rpm),
                         to_milli(output.steer_observer_innovation_deg));
#endif
        } else if (!active &&
                   (uint32_t)(now_ms - last_report_ms) >= IDLE_REPORT_PERIOD_MS) {
            last_report_ms = now_ms;
            const calibration_flash_status_t calibration =
                calibration_flash_status();
#if BENCH_CONTROL_UART_ENABLED
            debug_printf("idle angle=%d fdbk=%u en=%u tgt=%u uartB=%u uartE=%u\n",
                         to_milli(current_angle_deg),
                         feedback_is_fresh(now_ms) ? 1U : 0U,
                         unit_enabled ? 1U : 0U,
                         target_is_fresh(now_ms) ? 1U : 0U,
                         bench_uart_rx_byte_count(),
                         bench_uart_rx_error_count());
            (void)calibration;
#else
            debug_printf("idle angle=%d raw=%u amtOk=%u fdbkOk=%u en=%u tgtOk=%u "
                         "uartBytes=%u uartErr=%u cal=%u zero=%u calSeq=%u "
                         "calErr=%u calFull=%u can2psr=%x\n",
                         to_milli(current_angle_deg),
                         amt_ok ? (uint32_t)encoder.position : UINT32_MAX,
                         amt_ok ? 1U : 0U,
                         feedback_is_fresh(now_ms) ? 1U : 0U,
                         unit_enabled ? 1U : 0U,
                         target_is_fresh(now_ms) ? 1U : 0U,
                         bench_uart_rx_byte_count(),
                         bench_uart_rx_error_count(),
                         calibration.calibrated ? 1U : 0U,
                         calibration.calibrated
                             ? (uint32_t)calibration.zero_position_counts
                             : UINT32_MAX,
                         calibration.sequence,
                         calibration.crc_error ? 1U : 0U,
                         calibration.page_full ? 1U : 0U,
                         fdcan_protocol_status(FDCAN_BUS_C620));
#endif
        }
    }
}
