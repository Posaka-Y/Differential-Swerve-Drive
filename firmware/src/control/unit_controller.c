#include "control/unit_controller.h"

enum {
    /* Per-motor gear train 40:55:60:15. Drive path goes through both stages:
     * mode * (40/55)*(60/15) = 32/11. Steer path only reaches the 40:55
     * stage (the 60:15 bevel is after the differential): mode * 40/55 = 8/11.
     * The old 2/11 wrongly included the 60/15 stage; bench-verified 2026-07-08
     * (AMT axis rate 30deg/s vs motor-derived rate matched 8/11 within 0.4%). */
    DRIVE_RATIO_NUM = 32,
    DRIVE_RATIO_DEN = 11,
    STEER_RATIO_NUM = 8,
    STEER_RATIO_DEN = 11,
};

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

float unit_normalize_angle_deg(float angle_deg)
{
    while (angle_deg >= 360.0f) {
        angle_deg -= 360.0f;
    }
    while (angle_deg < 0.0f) {
        angle_deg += 360.0f;
    }
    return angle_deg;
}

static float shortest_angle_error(float target_deg, float current_deg)
{
    float error = unit_normalize_angle_deg(target_deg) -
                  unit_normalize_angle_deg(current_deg);
    if (error >= 180.0f) {
        error -= 360.0f;
    } else if (error < -180.0f) {
        error += 360.0f;
    }
    return error;
}

/* Single-pole low-pass, time-constant form so behavior is independent of dt jitter. */
static float lowpass_update(float previous, float raw, float tau_s, float dt_s)
{
    if (tau_s <= 0.0f || dt_s <= 0.0f) {
        return raw;
    }
    const float alpha = dt_s / (tau_s + dt_s);
    return previous + alpha * (raw - previous);
}

/* Friction is treated as a steady disturbance and rejected by the integral term
 * alone; there is no feedforward. This requires current_limit to have margin
 * over the worst-case measured breakaway current for every mode/direction.
 *
 * The integral is clamped to +/-integral_limit independently of the output
 * limit (RoboMaster-style max_iout): while the mechanism is stuck the integral
 * may only charge up to integral_limit, so breakaway cannot release a
 * full-limit torque jump. freeze_integral holds the integral for cycles that
 * follow combined per-motor saturation (conditional integration). */
static float pi_update_mode(float target, float measured_filtered, float kp,
                           float ki, float dt_s, float limit,
                           float integral_limit, uint8_t freeze_integral,
                           float integral_floor, uint8_t apply_integral_floor,
                           float *integral)
{
    const float error = target - measured_filtered;

    if (!freeze_integral) {
        const float candidate_integral = clampf(
            *integral + ki * error * dt_s, -integral_limit, integral_limit);
        const float candidate_output = kp * error + candidate_integral;
        if (!((candidate_output > limit && error > 0.0f) ||
              (candidate_output < -limit && error < 0.0f))) {
            *integral = candidate_integral;
        }
    }

    /* While moving in the commanded direction, do not let the integral decay
     * below integral_floor toward that direction (guarded by floor > 0 so a
     * zero floor, the default, never changes behavior). */
    if (apply_integral_floor && integral_floor > 0.0f) {
        if (target > 0.0f && *integral < integral_floor) {
            *integral = integral_floor;
        } else if (target < 0.0f && *integral > -integral_floor) {
            *integral = -integral_floor;
        }
    }

    return clampf(kp * error + *integral, -limit, limit);
}

void unit_controller_init(unit_controller_t *controller,
                          const unit_controller_config_t *config)
{
    /* Field-by-field copy, not a struct assignment: this build is -nostdlib
     * and a whole-struct copy of this size gets lowered to a memcpy() call
     * with no libc to satisfy it. */
    controller->config.motor_max_rpm = config->motor_max_rpm;
    controller->config.steer_max_rpm = config->steer_max_rpm;
    controller->config.steer_min_rpm = config->steer_min_rpm;
    controller->config.steer_accel_rpm_per_s = config->steer_accel_rpm_per_s;
    controller->config.angle_kp_rpm_per_deg = config->angle_kp_rpm_per_deg;
    controller->config.moving_angle_kp_rpm_per_deg =
        config->moving_angle_kp_rpm_per_deg;
    controller->config.angle_deadband_deg = config->angle_deadband_deg;
    controller->config.wheel_accel_rpm_per_s = config->wheel_accel_rpm_per_s;
    controller->config.steer_mode_kp = config->steer_mode_kp;
    controller->config.steer_mode_ki = config->steer_mode_ki;
    controller->config.drive_mode_kp = config->drive_mode_kp;
    controller->config.drive_mode_ki = config->drive_mode_ki;
    controller->config.mode_integral_limit = config->mode_integral_limit;
    controller->config.mode_rpm_filter_tau_s = config->mode_rpm_filter_tau_s;
    controller->config.current_limit = config->current_limit;
    controller->config.steer_motor_sign = config->steer_motor_sign;
    controller->config.steer_accel_ff_current_per_mode_rpm_per_s =
        config->steer_accel_ff_current_per_mode_rpm_per_s;
    controller->config.steer_decel_ff_current_per_mode_rpm_per_s =
        config->steer_decel_ff_current_per_mode_rpm_per_s;
    controller->config.steer_friction_ff_current =
        config->steer_friction_ff_current;
    controller->config.drive_kinetic_ff_current = config->drive_kinetic_ff_current;
    controller->config.drive_integral_floor_current =
        config->drive_integral_floor_current;
    controller->config.drive_motion_threshold_rpm =
        config->drive_motion_threshold_rpm;
    controller->config.drive_onset_integral_clamp_current =
        config->drive_onset_integral_clamp_current;
    controller->target.target_wheel_rpm = 0.0f;
    controller->target.target_steer_deg = 0.0f;
    controller->target.steer_rate_ff_rpm = 0.0f;
    controller->target.steer_accel_ff_rpm_per_s = 0.0f;
    unit_controller_reset(controller);
}

void unit_controller_set_target(unit_controller_t *controller,
                                float wheel_rpm, float steer_deg)
{
    controller->target.target_wheel_rpm = wheel_rpm;
    controller->target.target_steer_deg = unit_normalize_angle_deg(steer_deg);
}

void unit_controller_set_steer_rate_ff_rpm(unit_controller_t *controller,
                                           float steer_rate_ff_rpm)
{
    controller->target.steer_rate_ff_rpm = steer_rate_ff_rpm;
}

void unit_controller_set_steer_accel_ff_rpm_per_s(
    unit_controller_t *controller, float steer_accel_ff_rpm_per_s)
{
    controller->target.steer_accel_ff_rpm_per_s =
        steer_accel_ff_rpm_per_s;
}

void unit_controller_reset(unit_controller_t *controller)
{
    controller->steer_rpm_state = 0.0f;
    controller->wheel_rpm_state = 0.0f;
    controller->steer_mode_integral = 0.0f;
    controller->drive_mode_integral = 0.0f;
    controller->steer_mode_filtered_rpm = 0.0f;
    controller->drive_mode_filtered_rpm = 0.0f;
    controller->combined_saturated = 0U;
    controller->drive_was_in_motion = 0U;
    controller->drive_onset_count = 0U;
}

void unit_controller_update(unit_controller_t *controller,
                            const unit_measurement_t *measurement,
                            float dt_s, unit_control_output_t *output)
{
    const float drive_ratio =
        (float)DRIVE_RATIO_NUM / (float)DRIVE_RATIO_DEN;
    const float steer_ratio =
        (float)STEER_RATIO_NUM / (float)STEER_RATIO_DEN;
    const float sign = controller->config.steer_motor_sign;

    output->angle_error_deg = shortest_angle_error(
        controller->target.target_steer_deg, measurement->steer_deg);

    /* Angle-P term (deadband applied), then the steer-rate feedforward is
     * added to the sum before the steer_min_rpm/steer_max_rpm clamps below
     * (docs/control/CENTRAL_COORDINATED_CONTROL.md "SET_TARGET_FF"):
     * steer_rpm_cmd = angle_kp*error + FF. With steer_rate_ff_rpm == 0
     * (default / FF timed out) this reduces exactly to the pre-FF behavior. */
    /* Two-degree-of-freedom outer loop. During fast reference motion, a
     * small target-tracking error must not pull a saturated cruise command
     * sharply down and then release it (visible mid-move jerk). Blend from a
     * lower moving-reference gain to the full hold gain over the final 5rpm
     * of rate FF, so terminal stiffness is unchanged and the transition is
     * continuous. */
    const float moving_gain_blend = clampf(
        absf(controller->target.steer_rate_ff_rpm) / 5.0f, 0.0f, 1.0f);
    const float angle_kp =
        controller->config.angle_kp_rpm_per_deg + moving_gain_blend *
        (controller->config.moving_angle_kp_rpm_per_deg -
         controller->config.angle_kp_rpm_per_deg);
    float requested_steer_rpm = 0.0f;
    if (absf(output->angle_error_deg) >
        controller->config.angle_deadband_deg) {
        requested_steer_rpm =
            angle_kp * output->angle_error_deg;
    }
    requested_steer_rpm += controller->target.steer_rate_ff_rpm;
    if (requested_steer_rpm > 0.0f &&
        requested_steer_rpm < controller->config.steer_min_rpm) {
        requested_steer_rpm = controller->config.steer_min_rpm;
    } else if (requested_steer_rpm < 0.0f &&
               requested_steer_rpm > -controller->config.steer_min_rpm) {
        requested_steer_rpm = -controller->config.steer_min_rpm;
    }
    requested_steer_rpm = clampf(
        requested_steer_rpm, -controller->config.steer_max_rpm,
        controller->config.steer_max_rpm);

    const float max_steer_delta =
        controller->config.steer_accel_rpm_per_s * dt_s;
    const float steer_delta = clampf(
        requested_steer_rpm - controller->steer_rpm_state,
        -max_steer_delta, max_steer_delta);
    controller->steer_rpm_state += steer_delta;
    output->steer_rpm_command = controller->steer_rpm_state;

    /* Motor-space mode targets: steer mode is the common-mode rpm, drive mode is
     * the differential-mode rpm (matches wheelRpm=1.4545*(m1-m2),
     * steerRpm=0.3636*(m1+m2)). */
    const float steer_mode_target = sign * output->steer_rpm_command / steer_ratio;
    float available_drive_motor_rpm =
        controller->config.motor_max_rpm - absf(steer_mode_target);
    if (available_drive_motor_rpm < 0.0f) {
        available_drive_motor_rpm = 0.0f;
    }
    const float wheel_rpm_limit = available_drive_motor_rpm * drive_ratio;
    const float limited_wheel_rpm = clampf(
        controller->target.target_wheel_rpm, -wheel_rpm_limit,
        wheel_rpm_limit);
    output->limiting_active =
        absf(limited_wheel_rpm -
             controller->target.target_wheel_rpm) > 0.01f;

    /* Ramp the drive target like the steer target, so a step wheel command
     * cannot hit the drive PI unfiltered. */
    const float max_wheel_delta =
        controller->config.wheel_accel_rpm_per_s * dt_s;
    const float wheel_delta = clampf(
        limited_wheel_rpm - controller->wheel_rpm_state,
        -max_wheel_delta, max_wheel_delta);
    controller->wheel_rpm_state += wheel_delta;
    output->wheel_rpm_command = controller->wheel_rpm_state;

    const float drive_mode_target = output->wheel_rpm_command / drive_ratio;

    output->motor1_target_rpm = drive_mode_target + steer_mode_target;
    output->motor2_target_rpm = -drive_mode_target + steer_mode_target;
    output->steer_mode_target_rpm = steer_mode_target;
    output->drive_mode_target_rpm = drive_mode_target;

    const float raw_drive_mode_rpm =
        (measurement->motor1_rpm - measurement->motor2_rpm) * 0.5f;
    const float raw_steer_mode_rpm =
        sign * (measurement->motor1_rpm + measurement->motor2_rpm) * 0.5f;

    controller->drive_mode_filtered_rpm = lowpass_update(
        controller->drive_mode_filtered_rpm, raw_drive_mode_rpm,
        controller->config.mode_rpm_filter_tau_s, dt_s);
    controller->steer_mode_filtered_rpm = lowpass_update(
        controller->steer_mode_filtered_rpm, raw_steer_mode_rpm,
        controller->config.mode_rpm_filter_tau_s, dt_s);

    output->drive_mode_measured_rpm = controller->drive_mode_filtered_rpm;
    output->steer_mode_measured_rpm = controller->steer_mode_filtered_rpm;

    /* "Moving" for the kinetic-friction feedforward and integral-floor logic
     * below: the drive mode is actually turning, not just commanded to. */
    const uint8_t drive_in_motion =
        absf(controller->drive_mode_filtered_rpm) >
        controller->config.drive_motion_threshold_rpm;
    output->drive_in_motion = drive_in_motion;
    output->drive_onset_active = 0U;
    output->drive_integral_floor_active =
        drive_in_motion &&
        controller->config.drive_integral_floor_current > 0.0f;

    /* Onset clamp: the instant the drive mode transitions stuck->moving
     * (rising edge), clamp the drive integral magnitude down before this
     * cycle's drive PI runs, so the breakaway charge (built up while stuck,
     * up to mode_integral_limit) cannot release as a full torque kick. Sign
     * is preserved; steer integral is untouched. Zero clamp value disables. */
    if (drive_in_motion && !controller->drive_was_in_motion &&
        controller->config.drive_onset_integral_clamp_current > 0.0f) {
        output->drive_onset_active = 1U;
        controller->drive_onset_count++;
        const float clamp = controller->config.drive_onset_integral_clamp_current;
        if (controller->drive_mode_integral > clamp) {
            controller->drive_mode_integral = clamp;
        } else if (controller->drive_mode_integral < -clamp) {
            controller->drive_mode_integral = -clamp;
        }
    }
    controller->drive_was_in_motion = drive_in_motion;
    output->drive_onset_count = controller->drive_onset_count;

    output->steer_mode_current = pi_update_mode(
        steer_mode_target, controller->steer_mode_filtered_rpm,
        controller->config.steer_mode_kp, controller->config.steer_mode_ki,
        dt_s, controller->config.current_limit,
        controller->config.mode_integral_limit,
        controller->combined_saturated,
        0.0f, 0U,
        &controller->steer_mode_integral);
    /* Two-degree-of-freedom acceleration feedforward: the PI still rejects
     * model/friction error, while predictable trajectory acceleration does
     * not have to wait for a velocity error. Gain=0 preserves old behavior. */
    const float steer_accel_ff_mode_rpm_per_s =
        sign * controller->target.steer_accel_ff_rpm_per_s / steer_ratio;
    const uint8_t steer_ff_is_braking =
        absf(controller->target.steer_accel_ff_rpm_per_s) > 0.01f &&
        controller->target.steer_accel_ff_rpm_per_s *
        controller->target.steer_rate_ff_rpm <= 0.0f;
    const float steer_accel_ff_gain = steer_ff_is_braking
        ? controller->config.steer_decel_ff_current_per_mode_rpm_per_s
        : controller->config.steer_accel_ff_current_per_mode_rpm_per_s;
    output->steer_accel_ff_current =
        steer_accel_ff_gain * steer_accel_ff_mode_rpm_per_s;
    output->steer_mode_current += output->steer_accel_ff_current;
    if (absf(steer_mode_target) > 0.01f &&
        controller->config.steer_friction_ff_current > 0.0f) {
        output->steer_mode_current += steer_mode_target > 0.0f
            ? controller->config.steer_friction_ff_current
            : -controller->config.steer_friction_ff_current;
    }
    output->drive_mode_current = pi_update_mode(
        drive_mode_target, controller->drive_mode_filtered_rpm,
        controller->config.drive_mode_kp, controller->config.drive_mode_ki,
        dt_s, controller->config.current_limit,
        controller->config.mode_integral_limit,
        controller->combined_saturated,
        controller->config.drive_integral_floor_current, drive_in_motion,
        &controller->drive_mode_integral);
    output->steer_mode_integral = controller->steer_mode_integral;
    output->drive_mode_integral = controller->drive_mode_integral;

    /* Kinetic-friction feedforward, added in the direction of actual motion
     * before mode-current combination and the current_limit clamp below.
     * Zero drive_kinetic_ff_current (default) makes this a no-op. */
    if (drive_in_motion) {
        const float ff_sign =
            controller->drive_mode_filtered_rpm >= 0.0f ? 1.0f : -1.0f;
        output->drive_mode_current +=
            ff_sign * controller->config.drive_kinetic_ff_current;
    }

    /* If the combined per-motor demand exceeds current_limit, scale both mode
     * currents by a common factor instead of clamping each motor separately.
     * Clamping only one motor would silently change the steer/drive torque
     * ratio (cross-coupling); proportional scaling preserves the torque
     * direction, matching how RoboMaster power limiting scales all motors. */
    const float peak_motor_current =
        absf(output->steer_mode_current) + absf(output->drive_mode_current);
    output->torque_scaling_active =
        peak_motor_current > controller->config.current_limit;
    if (output->torque_scaling_active) {
        const float scale = controller->config.current_limit / peak_motor_current;
        output->steer_mode_current *= scale;
        output->drive_mode_current *= scale;
    }
    controller->combined_saturated = output->torque_scaling_active;

    const float motor1_current = clampf(
        output->steer_mode_current + output->drive_mode_current,
        -controller->config.current_limit, controller->config.current_limit);
    const float motor2_current = clampf(
        output->steer_mode_current - output->drive_mode_current,
        -controller->config.current_limit, controller->config.current_limit);

    output->motor1_current = (int16_t)(
        motor1_current >= 0.0f ? motor1_current + 0.5f : motor1_current - 0.5f);
    output->motor2_current = (int16_t)(
        motor2_current >= 0.0f ? motor2_current + 0.5f : motor2_current - 0.5f);
}
