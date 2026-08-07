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
    WHEEL_LOW_SPEED_TRANSITION_RPM = 30,
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

static const float steer_gain_knot_speeds_rpm[UNIT_STEER_GAIN_KNOT_COUNT] = {
    0.0f, 60.0f, 100.0f, 150.0f,
};

static float lerpf(float lower, float upper, float fraction)
{
    return lower + (upper - lower) * fraction;
}

static void interpolate_steer_gain_schedule(
    const unit_controller_t *controller, float schedule_rpm,
    unit_steer_gain_knot_t *scheduled)
{
    if (schedule_rpm <= controller->steer_gain_knots[0].speed_rpm) {
        const unit_steer_gain_knot_t *knot = &controller->steer_gain_knots[0];
        scheduled->speed_rpm = schedule_rpm;
        scheduled->mode_kp = knot->mode_kp;
        scheduled->mode_ki = knot->mode_ki;
        scheduled->accel_ff_gain = knot->accel_ff_gain;
        scheduled->decel_ff_gain = knot->decel_ff_gain;
        scheduled->backcalc_gain = knot->backcalc_gain;
        scheduled->brake_kp_multiplier = knot->brake_kp_multiplier;
        return;
    }

    for (uint8_t upper_index = 1U;
         upper_index < UNIT_STEER_GAIN_KNOT_COUNT; upper_index++) {
        const unit_steer_gain_knot_t *upper =
            &controller->steer_gain_knots[upper_index];
        if (schedule_rpm <= upper->speed_rpm) {
            const unit_steer_gain_knot_t *lower =
                &controller->steer_gain_knots[upper_index - 1U];
            const float span_rpm = upper->speed_rpm - lower->speed_rpm;
            const float fraction = span_rpm > 0.0f
                ? clampf((schedule_rpm - lower->speed_rpm) / span_rpm,
                         0.0f, 1.0f)
                : 0.0f;
            scheduled->speed_rpm = schedule_rpm;
            scheduled->mode_kp = lerpf(
                lower->mode_kp, upper->mode_kp, fraction);
            scheduled->mode_ki = lerpf(
                lower->mode_ki, upper->mode_ki, fraction);
            scheduled->accel_ff_gain = lerpf(
                lower->accel_ff_gain, upper->accel_ff_gain, fraction);
            scheduled->decel_ff_gain = lerpf(
                lower->decel_ff_gain, upper->decel_ff_gain, fraction);
            scheduled->backcalc_gain = lerpf(
                lower->backcalc_gain, upper->backcalc_gain, fraction);
            scheduled->brake_kp_multiplier = lerpf(
                lower->brake_kp_multiplier,
                upper->brake_kp_multiplier, fraction);
            return;
        }
    }

    const unit_steer_gain_knot_t *knot =
        &controller->steer_gain_knots[UNIT_STEER_GAIN_KNOT_COUNT - 1U];
    scheduled->speed_rpm = schedule_rpm;
    scheduled->mode_kp = knot->mode_kp;
    scheduled->mode_ki = knot->mode_ki;
    scheduled->accel_ff_gain = knot->accel_ff_gain;
    scheduled->decel_ff_gain = knot->decel_ff_gain;
    scheduled->backcalc_gain = knot->backcalc_gain;
    scheduled->brake_kp_multiplier = knot->brake_kp_multiplier;
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
    controller->config.steer_brake_kp_multiplier =
        config->steer_brake_kp_multiplier >= 1.0f
            ? config->steer_brake_kp_multiplier : 1.0f;
    controller->config.drive_mode_kp = config->drive_mode_kp;
    controller->config.drive_mode_ki = config->drive_mode_ki;
    controller->config.steer_mode_backcalc_gain =
        config->steer_mode_backcalc_gain;
    controller->config.drive_mode_backcalc_gain =
        config->drive_mode_backcalc_gain;
    controller->config.mode_integral_limit = config->mode_integral_limit;
    controller->config.mode_rpm_filter_tau_s = config->mode_rpm_filter_tau_s;
    controller->config.steer_schedule_filter_tau_s =
        config->steer_schedule_filter_tau_s;
    controller->config.steer_observer_correction_tau_s =
        config->steer_observer_correction_tau_s;
    controller->config.current_limit = config->current_limit;
    controller->config.steer_motor_sign = config->steer_motor_sign;
    controller->config.steer_accel_ff_current_per_mode_rpm_per_s =
        config->steer_accel_ff_current_per_mode_rpm_per_s;
    controller->config.steer_decel_ff_current_per_mode_rpm_per_s =
        config->steer_decel_ff_current_per_mode_rpm_per_s;
    controller->config.steer_friction_ff_current =
        config->steer_friction_ff_current;
    controller->config.steer_friction_ff_fade_axis_rpm =
        config->steer_friction_ff_fade_axis_rpm;
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
    unit_controller_set_uniform_steer_gain_schedule(controller);
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

void unit_controller_set_uniform_steer_gain_schedule(
    unit_controller_t *controller)
{
    for (uint8_t index = 0U; index < UNIT_STEER_GAIN_KNOT_COUNT; index++) {
        unit_steer_gain_knot_t *knot = &controller->steer_gain_knots[index];
        knot->speed_rpm = steer_gain_knot_speeds_rpm[index];
        knot->mode_kp = controller->config.steer_mode_kp;
        knot->mode_ki = controller->config.steer_mode_ki;
        knot->accel_ff_gain =
            controller->config.steer_accel_ff_current_per_mode_rpm_per_s;
        knot->decel_ff_gain =
            controller->config.steer_decel_ff_current_per_mode_rpm_per_s;
        knot->backcalc_gain =
            controller->config.steer_mode_backcalc_gain;
        knot->brake_kp_multiplier =
            controller->config.steer_brake_kp_multiplier;
    }
}

void unit_controller_set_uniform_steer_brake_kp_schedule(
    unit_controller_t *controller)
{
    for (uint8_t index = 0U; index < UNIT_STEER_GAIN_KNOT_COUNT; index++) {
        controller->steer_gain_knots[index].brake_kp_multiplier =
            controller->config.steer_brake_kp_multiplier;
    }
}

uint8_t unit_controller_set_steer_gain_knot(
    unit_controller_t *controller, uint8_t index,
    float mode_kp, float mode_ki, float accel_ff_gain,
    float decel_ff_gain, float backcalc_gain)
{
    if (index >= UNIT_STEER_GAIN_KNOT_COUNT) {
        return 0U;
    }
    unit_steer_gain_knot_t *knot = &controller->steer_gain_knots[index];
    knot->speed_rpm = steer_gain_knot_speeds_rpm[index];
    knot->mode_kp = mode_kp;
    knot->mode_ki = mode_ki;
    knot->accel_ff_gain = accel_ff_gain;
    knot->decel_ff_gain = decel_ff_gain;
    knot->backcalc_gain = backcalc_gain;
    return 1U;
}

uint8_t unit_controller_set_steer_brake_kp_knot(
    unit_controller_t *controller, uint8_t index,
    float brake_kp_multiplier)
{
    if (index >= UNIT_STEER_GAIN_KNOT_COUNT) {
        return 0U;
    }
    controller->steer_gain_knots[index].brake_kp_multiplier =
        brake_kp_multiplier;
    return 1U;
}

void unit_controller_reset(unit_controller_t *controller)
{
    controller->steer_rpm_state = 0.0f;
    controller->wheel_rpm_state = 0.0f;
    controller->steer_mode_integral = 0.0f;
    controller->drive_mode_integral = 0.0f;
    controller->steer_mode_filtered_rpm = 0.0f;
    controller->drive_mode_filtered_rpm = 0.0f;
    controller->steer_angle_observer_deg = 0.0f;
    controller->steer_schedule_rpm = 0.0f;
    controller->steer_saturation_duration_s = 0.0f;
    controller->steer_observer_initialized = 0U;
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

    /* Update measured modes and the observer before the outer position loop.
     * This is the same filter update formerly performed immediately before
     * the mode PI; moving it earlier does not change the PI input for this
     * cycle, and makes the current observer rate available for friction-FF
     * scheduling below. */
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

    /* Complementary steer observer. The C620 common-mode velocity supplies
     * the short-term prediction and AMT22 absolute angle removes drift. */
    const float observer_motor_axis_rpm =
        controller->steer_mode_filtered_rpm * steer_ratio;
    if (!controller->steer_observer_initialized || dt_s <= 0.0f) {
        controller->steer_angle_observer_deg =
            unit_normalize_angle_deg(measurement->steer_deg);
        controller->steer_observer_initialized = 1U;
        output->steer_observer_innovation_deg = 0.0f;
        output->steer_axis_observer_rpm = observer_motor_axis_rpm;
    } else {
        const float predicted_angle_deg = unit_normalize_angle_deg(
            controller->steer_angle_observer_deg +
            observer_motor_axis_rpm * 6.0f * dt_s);
        const float innovation_deg = shortest_angle_error(
            measurement->steer_deg, predicted_angle_deg);
        const float correction_alpha =
            controller->config.steer_observer_correction_tau_s <= 0.0f
            ? 1.0f
            : dt_s /
              (controller->config.steer_observer_correction_tau_s + dt_s);
        const float correction_deg = correction_alpha * innovation_deg;
        controller->steer_angle_observer_deg = unit_normalize_angle_deg(
            predicted_angle_deg + correction_deg);
        output->steer_observer_innovation_deg = innovation_deg;
        output->steer_axis_observer_rpm =
            observer_motor_axis_rpm + correction_deg / (6.0f * dt_s);
    }
    output->steer_angle_observer_deg =
        controller->steer_angle_observer_deg;

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
    /* Continuous error shaping instead of a hard deadband cutoff
     * (docs/control/CENTRAL_COORDINATED_CONTROL.md P1 "hard deadbandを...
     * 連続な誤差整形へ変更する"): the old code set the P-term to exactly
     * zero for |error| < angle_deadband_deg, so crossing the boundary
     * stepped the command discontinuously between 0 and
     * angle_kp*angle_deadband_deg. That step is what a mechanism sitting
     * right at the boundary chatters on. A quadratic taper is used instead:
     * it equals angle_kp*error exactly at |error| == angle_deadband_deg (no
     * discontinuity there) and shrinks to exactly zero only at error == 0,
     * so near-target commands shrink smoothly rather than toggling. */
    float requested_steer_rpm;
    if (controller->config.angle_deadband_deg > 0.0f &&
        absf(output->angle_error_deg) <
        controller->config.angle_deadband_deg) {
        const float taper =
            absf(output->angle_error_deg) /
            controller->config.angle_deadband_deg;
        requested_steer_rpm =
            angle_kp * output->angle_error_deg * taper;
    } else {
        requested_steer_rpm = angle_kp * output->angle_error_deg;
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

    /* Joint hard-protection envelope
     * (docs/control/CENTRAL_COORDINATED_CONTROL.md "mode要求を包絡へ射影する"):
     * |steer_mode|+|drive_mode| <= motor_max_rpm is the same 469rpm diamond
     * the central planner targets. The previous scheme clamped steer first
     * and gave drive whatever motor budget remained, which silently favored
     * steer whenever both requests were large at once. Scaling both
     * requests by one common factor instead preserves their ratio (and thus
     * the commanded motion direction) while still enforcing the same
     * budget. Mode conversion is linear, so applying the scale here (before
     * each mode's own accel ramp) is equivalent to applying it to the
     * motor-mode values directly. */
    const float requested_steer_mode_rpm =
        sign * requested_steer_rpm / steer_ratio;
    const float requested_drive_mode_rpm =
        controller->target.target_wheel_rpm / drive_ratio;
    const float requested_mode_sum =
        absf(requested_steer_mode_rpm) + absf(requested_drive_mode_rpm);
    float envelope_scale = 1.0f;
    if (requested_mode_sum > controller->config.motor_max_rpm &&
        requested_mode_sum > 0.0f) {
        envelope_scale =
            controller->config.motor_max_rpm / requested_mode_sum;
    }
    output->limiting_active = envelope_scale < 0.999f;
    const float envelope_steer_rpm = requested_steer_rpm * envelope_scale;
    const float envelope_wheel_rpm =
        controller->target.target_wheel_rpm * envelope_scale;

    const float max_steer_delta =
        controller->config.steer_accel_rpm_per_s * dt_s;
    const float steer_delta = clampf(
        envelope_steer_rpm - controller->steer_rpm_state,
        -max_steer_delta, max_steer_delta);
    controller->steer_rpm_state += steer_delta;
    output->steer_rpm_command = controller->steer_rpm_state;

    /* P2 continuous gain schedule. Reference speed makes the high-speed gain
     * arrive before acceleration; observer speed keeps it active through
     * braking. The 10ms LPF and linear interpolation avoid knot steps. */
    const float schedule_reference_rpm = absf(output->steer_rpm_command);
    const float schedule_observer_rpm =
        absf(output->steer_axis_observer_rpm);
    const float schedule_raw_rpm = schedule_reference_rpm >
        schedule_observer_rpm ? schedule_reference_rpm : schedule_observer_rpm;
    controller->steer_schedule_rpm = lowpass_update(
        controller->steer_schedule_rpm, schedule_raw_rpm,
        controller->config.steer_schedule_filter_tau_s, dt_s);
    output->steer_schedule_rpm = controller->steer_schedule_rpm;
    unit_steer_gain_knot_t scheduled_steer_gain;
    interpolate_steer_gain_schedule(
        controller, controller->steer_schedule_rpm, &scheduled_steer_gain);
    const uint8_t steer_ff_is_braking =
        absf(controller->target.steer_accel_ff_rpm_per_s) > 0.01f &&
        controller->target.steer_accel_ff_rpm_per_s *
        controller->target.steer_rate_ff_rpm <= 0.0f;
    if (steer_ff_is_braking) {
        scheduled_steer_gain.mode_kp *=
            scheduled_steer_gain.brake_kp_multiplier;
    }
    output->scheduled_steer_mode_kp = scheduled_steer_gain.mode_kp;
    output->scheduled_steer_mode_ki = scheduled_steer_gain.mode_ki;
    output->scheduled_steer_accel_ff_gain =
        scheduled_steer_gain.accel_ff_gain;
    output->scheduled_steer_decel_ff_gain =
        scheduled_steer_gain.decel_ff_gain;
    output->scheduled_steer_backcalc_gain =
        scheduled_steer_gain.backcalc_gain;

    /* Ramp the drive target like the steer target, so a step wheel command
     * cannot hit the drive PI unfiltered. */
    const float max_wheel_delta =
        controller->config.wheel_accel_rpm_per_s * dt_s;
    const float wheel_delta = clampf(
        envelope_wheel_rpm - controller->wheel_rpm_state,
        -max_wheel_delta, max_wheel_delta);
    controller->wheel_rpm_state += wheel_delta;
    output->wheel_rpm_command = controller->wheel_rpm_state;

    /* Motor-space mode targets: steer mode is the common-mode rpm, drive mode is
     * the differential-mode rpm (matches wheelRpm=1.4545*(m1-m2),
     * steerRpm=0.3636*(m1+m2)). */
    const float steer_mode_target = sign * output->steer_rpm_command / steer_ratio;
    const float drive_mode_target = output->wheel_rpm_command / drive_ratio;

    output->motor1_target_rpm = drive_mode_target + steer_mode_target;
    output->motor2_target_rpm = -drive_mode_target + steer_mode_target;
    output->steer_mode_target_rpm = steer_mode_target;
    output->drive_mode_target_rpm = drive_mode_target;

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
        scheduled_steer_gain.mode_kp, scheduled_steer_gain.mode_ki,
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
    output->steer_braking_active = steer_ff_is_braking;
    const float steer_accel_ff_gain = steer_ff_is_braking
        ? scheduled_steer_gain.decel_ff_gain
        : scheduled_steer_gain.accel_ff_gain;
    output->steer_accel_ff_current =
        steer_accel_ff_gain * steer_accel_ff_mode_rpm_per_s;
    output->steer_mode_current += output->steer_accel_ff_current;
    /* Coulomb-style breakaway assist, tapered out as wheel rpm rises
     * (2026-07-31 diagnosis in firmware/PROGRESS.md): a flat friction FF
     * shortens the wheel=0 stick-slip stall (measured commanded current sat
     * well below the ~850-950raw breakaway threshold, so the mode PI's pure
     * integral took seconds to climb there for small residual errors) but
     * measurably slows wheel!=0 convergence (1.1-1.4s -> 2.4-4.0s at
     * wheel=265rpm in an A/B), which is why a flat FF was rejected before.
     * Tapering it to 0 by WHEEL_LOW_SPEED_TRANSITION_RPM keeps the wheel=0/near-0
     * benefit (this is the pre-steer use case that motivates it) while
     * leaving normal wheel!=0 motion untouched. */
    const float wheel_friction_taper = clampf(
        1.0f - absf(controller->target.target_wheel_rpm) /
        (float)WHEEL_LOW_SPEED_TRANSITION_RPM,
        0.0f, 1.0f);
    /* Localized breakaway boost over a mechanical defect (2026-07-31 finding
     * in firmware/PROGRESS.md: a 48-trial 8-direction sweep showed wheel=0
     * stalls concentrated at 90-225deg AMT angle -- user traced this to a
     * print-layer seam bump on this 3D-printed part, confirmed by physical
     * inspection, not something worth chasing in the control loop alone).
     * Ramp the extra current in/out over ANGLE_FRICTION_BUMP_RAMP_DEG so the
     * band edges don't add a torque step, and keep the existing wheel taper
     * on top so this still only fires near wheel=0. Position-triggered
     * rather than integral-triggered, so it helps regardless of how large
     * the residual angle error is when the mechanism enters the band. */
    enum {
        ANGLE_FRICTION_BUMP_LOW_DEG = 80,
        ANGLE_FRICTION_BUMP_HIGH_DEG = 235,
    };
    const float angle_friction_ramp_deg = 5.0f;
    float angle_friction_boost = 0.0f;
    if (measurement->steer_deg >= (float)ANGLE_FRICTION_BUMP_LOW_DEG &&
        measurement->steer_deg <= (float)ANGLE_FRICTION_BUMP_HIGH_DEG) {
        const float distance_from_low =
            measurement->steer_deg - (float)ANGLE_FRICTION_BUMP_LOW_DEG;
        const float distance_from_high =
            (float)ANGLE_FRICTION_BUMP_HIGH_DEG - measurement->steer_deg;
        const float distance_from_edge = distance_from_low < distance_from_high
            ? distance_from_low : distance_from_high;
        angle_friction_boost = clampf(
            distance_from_edge / angle_friction_ramp_deg, 0.0f, 1.0f);
    }
    if (absf(steer_mode_target) > 0.01f &&
        controller->config.steer_friction_ff_current > 0.0f &&
        wheel_friction_taper > 0.0f) {
        const float observer_friction_taper =
            controller->config.steer_friction_ff_fade_axis_rpm <= 0.0f
            ? 1.0f
            : clampf(
                1.0f - absf(output->steer_axis_observer_rpm) /
                controller->config.steer_friction_ff_fade_axis_rpm,
                0.0f, 1.0f);
        const float friction_ff =
            controller->config.steer_friction_ff_current * wheel_friction_taper *
            observer_friction_taper * (1.0f + angle_friction_boost);
        output->steer_mode_current += steer_mode_target > 0.0f
            ? friction_ff : -friction_ff;
    }
    output->drive_mode_current = pi_update_mode(
        drive_mode_target, controller->drive_mode_filtered_rpm,
        controller->config.drive_mode_kp, controller->config.drive_mode_ki,
        dt_s, controller->config.current_limit,
        controller->config.mode_integral_limit,
        controller->combined_saturated,
        controller->config.drive_integral_floor_current, drive_in_motion,
        &controller->drive_mode_integral);
    /* Kinetic-friction feedforward, added in the direction of actual motion
     * before mode-current combination and the current_limit clamp below.
     * Zero drive_kinetic_ff_current (default) makes this a no-op. */
    if (drive_in_motion) {
        const float ff_sign =
            controller->drive_mode_filtered_rpm >= 0.0f ? 1.0f : -1.0f;
        output->drive_mode_current +=
            ff_sign * controller->config.drive_kinetic_ff_current;
    }

    output->steer_mode_current_unsaturated = output->steer_mode_current;
    const float drive_mode_current_unsaturated = output->drive_mode_current;

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
    output->steer_mode_current_applied = output->steer_mode_current;
    output->steer_saturation_residual =
        output->steer_mode_current_applied -
        output->steer_mode_current_unsaturated;
    const float drive_saturation_residual =
        output->drive_mode_current - drive_mode_current_unsaturated;

    /* Back-calculation uses the final shared-scale residual and only changes
     * the stored integral for the next control cycle. The current cycle's
     * applied motor command is therefore identical when enabling/tuning Kaw;
     * zero gains reproduce the previous controller exactly. */
    const float previous_steer_integral = controller->steer_mode_integral;
    const float previous_drive_integral = controller->drive_mode_integral;
    if (dt_s > 0.0f) {
        controller->steer_mode_integral = clampf(
            controller->steer_mode_integral +
            scheduled_steer_gain.backcalc_gain *
            output->steer_saturation_residual * dt_s,
            -controller->config.mode_integral_limit,
            controller->config.mode_integral_limit);
        controller->drive_mode_integral = clampf(
            controller->drive_mode_integral +
            controller->config.drive_mode_backcalc_gain *
            drive_saturation_residual * dt_s,
            -controller->config.mode_integral_limit,
            controller->config.mode_integral_limit);
    }
    output->steer_backcalc_correction =
        controller->steer_mode_integral - previous_steer_integral;
    output->drive_backcalc_correction =
        controller->drive_mode_integral - previous_drive_integral;
    output->steer_mode_integral = controller->steer_mode_integral;
    output->drive_mode_integral = controller->drive_mode_integral;
    if (absf(output->steer_saturation_residual) > 0.01f && dt_s > 0.0f) {
        controller->steer_saturation_duration_s += dt_s;
    } else {
        controller->steer_saturation_duration_s = 0.0f;
    }
    const float saturation_duration_ms =
        controller->steer_saturation_duration_s * 1000.0f;
    output->steer_saturation_duration_ms = saturation_duration_ms >=
        4294967040.0f ? UINT32_MAX : (uint32_t)(saturation_duration_ms + 0.5f);
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
