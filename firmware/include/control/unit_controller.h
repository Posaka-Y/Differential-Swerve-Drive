#pragma once

#include <stdint.h>

typedef struct {
    float motor_max_rpm;
    float steer_max_rpm;
    /* Commanded speeds below the mechanism's re-stick speed cause stick-slip
     * limit cycles; outside the deadband the steer command magnitude is floored
     * to this value so the final approach stays in continuous motion. */
    float steer_min_rpm;
    float steer_accel_rpm_per_s;
    float angle_kp_rpm_per_deg;
    /* Lower outer-loop gain used while steer-rate FF is large. It prevents
     * small moving-reference errors from kicking the cruise-rate command.
     * The controller blends back to angle_kp_rpm_per_deg as FF approaches 0. */
    float moving_angle_kp_rpm_per_deg;
    float angle_deadband_deg;

    /* Ramp on the drive (wheel) target, mirroring steer_accel_rpm_per_s.
     * Without it a step wheel target hits the drive PI unfiltered. */
    float wheel_accel_rpm_per_s;

    /* Mode-coordinate PI gains (steer = common mode, drive = differential mode).
     * Friction is rejected by the integral term alone; current_limit must have
     * margin over the worst-case measured breakaway current for this to work. */
    float steer_mode_kp;
    float steer_mode_ki;
    float drive_mode_kp;
    float drive_mode_ki;

    /* Separate clamp on each mode integral (RoboMaster-style max_iout).
     * Must sit above the worst-case breakaway current (so the integral can
     * still defeat static friction) but below current_limit, so the charge
     * stored while stuck cannot release as a full-limit torque jump. */
    float mode_integral_limit;

    /* First-order low-pass applied to the measured mode rpm before the PI. */
    float mode_rpm_filter_tau_s;

    float current_limit;
    float steer_motor_sign;

    /* Steer acceleration feedforward. The CAN layer differentiates the
     * profiled steer-axis rate command at its update period and holds the
     * resulting axis rpm/s until the next FF frame. This gain converts the
     * corresponding motor-mode rpm/s into C620 current-command units. */
    float steer_accel_ff_current_per_mode_rpm_per_s;
    float steer_decel_ff_current_per_mode_rpm_per_s;
    /* Coulomb-friction feedforward in steer mode. Applied in the direction
     * of a nonzero steer-mode target; zero disables. */
    float steer_friction_ff_current;

    /* Kinetic-friction feedforward: while |filtered drive-mode rpm| exceeds
     * drive_motion_threshold_rpm (i.e. the wheel is actually moving), this
     * much current is added to the drive-mode output in the direction of
     * motion, before mode-current combination and the current_limit clamp.
     * Zero disables (default, unchanged behavior). */
    float drive_kinetic_ff_current;

    /* Floor on the drive-mode integral toward the commanded direction while
     * the wheel is moving (see drive_motion_threshold_rpm): the integral is
     * not allowed to decay below this magnitude in the direction of
     * target_wheel_rpm. Zero disables (default, unchanged behavior). */
    float drive_integral_floor_current;

    /* Motion threshold (M3508 output-shaft rpm) used by both the kinetic-
     * friction feedforward and the integral floor above. */
    float drive_motion_threshold_rpm;

    /* Onset clamp: on the stuck->moving rising edge of drive_in_motion, the
     * drive-mode integral magnitude is clamped down to this value (sign
     * preserved) before that cycle's drive PI runs, so the breakaway charge
     * cannot release as a full torque kick. Zero disables (default,
     * unchanged behavior). */
    float drive_onset_integral_clamp_current;
} unit_controller_config_t;

typedef struct {
    float target_wheel_rpm;
    float target_steer_deg;
    /* Steer angular-rate feedforward (rpm), added to the angle-P term before
     * the steer_min_rpm/steer_max_rpm/steer_accel clamps. Zero (default,
     * set by unit_controller_init/reset callers not calling the setter below)
     * reproduces the pre-FF behavior exactly. Set via
     * unit_controller_set_steer_rate_ff_rpm(), independent of
     * unit_controller_set_target() so a CAN-side FF timeout can zero it
     * without touching the angle/wheel targets. */
    float steer_rate_ff_rpm;
    float steer_accel_ff_rpm_per_s;
} unit_target_t;

typedef struct {
    float steer_deg;
    float motor1_rpm;
    float motor2_rpm;
} unit_measurement_t;

typedef struct {
    int16_t motor1_current;
    int16_t motor2_current;
    float angle_error_deg;
    float steer_rpm_command;
    float wheel_rpm_command;
    float motor1_target_rpm;
    float motor2_target_rpm;
    float steer_mode_target_rpm;
    float drive_mode_target_rpm;
    float steer_mode_measured_rpm;
    float drive_mode_measured_rpm;
    float steer_mode_current;
    float steer_accel_ff_current;
    float drive_mode_current;
    /* Integral states are exposed for tuning telemetry.  They are the stored
     * mode-PI I terms before P addition/current scaling. */
    float steer_mode_integral;
    float drive_mode_integral;
    uint8_t drive_in_motion;
    uint8_t drive_onset_active;
    uint8_t drive_integral_floor_active;
    uint32_t drive_onset_count;
    uint8_t limiting_active;
    /* Set when the combined per-motor current exceeded current_limit and both
     * mode currents were scaled down proportionally. */
    uint8_t torque_scaling_active;
} unit_control_output_t;

typedef struct {
    unit_controller_config_t config;
    unit_target_t target;
    float steer_rpm_state;
    float wheel_rpm_state;
    float steer_mode_integral;
    float drive_mode_integral;
    float steer_mode_filtered_rpm;
    float drive_mode_filtered_rpm;
    /* Previous-cycle combined saturation; freezes both integrals for one cycle
     * (conditional integration against cross-mode windup). */
    uint8_t combined_saturated;
    /* Previous-cycle drive_in_motion state, used to detect the stuck->moving
     * rising edge for drive_onset_integral_clamp_current. */
    uint8_t drive_was_in_motion;
    uint32_t drive_onset_count;
} unit_controller_t;

void unit_controller_init(unit_controller_t *controller,
                          const unit_controller_config_t *config);
void unit_controller_set_target(unit_controller_t *controller,
                                float wheel_rpm, float steer_deg);
/* Sets the steer angular-rate feedforward (rpm). Call every control cycle
 * with 0 once the source (e.g. SET_TARGET_FF over CAN) goes stale/timed out,
 * so the FF cannot get stuck at a stale nonzero value. */
void unit_controller_set_steer_rate_ff_rpm(unit_controller_t *controller,
                                           float steer_rate_ff_rpm);
void unit_controller_set_steer_accel_ff_rpm_per_s(
    unit_controller_t *controller, float steer_accel_ff_rpm_per_s);
void unit_controller_reset(unit_controller_t *controller);
void unit_controller_update(unit_controller_t *controller,
                            const unit_measurement_t *measurement,
                            float dt_s, unit_control_output_t *output);

/* Returns angle normalized to [0, 360). */
float unit_normalize_angle_deg(float angle_deg);
