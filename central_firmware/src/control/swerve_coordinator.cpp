#include "control/swerve_coordinator.h"

#include <math.h>

namespace dsd {
namespace central {
namespace {

const float kPi = 3.14159265358979323846f;

float absf(float value)
{
    return value < 0.0f ? -value : value;
}

float nearest_equivalent_deg(float wrapped_deg, float reference_deg)
{
    const float turns = floorf((reference_deg - wrapped_deg) / 360.0f + 0.5f);
    return wrapped_deg + 360.0f * turns;
}

void clear_output(CoordinatorOutput *output)
{
    output->common_scale = 0.0f;
    output->limiting_active = false;
    for (int i = 0; i < kDriveModuleCount; ++i) {
        output->modules[i].steer_unwrapped_deg = 0.0f;
        output->modules[i].wheel_rpm = 0.0f;
        output->modules[i].steer_rate_deg_per_s = 0.0f;
        output->modules[i].wheel_accel_rpm_per_s = 0.0f;
        output->modules[i].motor_budget_used_rpm = 0.0f;
        output->modules[i].flipped = false;
        output->modules[i].held_at_zero_speed = true;
    }
}

bool config_valid(const CoordinatorConfig &config)
{
    if (!(config.planned_motor_rpm > 0.0f) ||
        !(config.drive_ratio > 0.0f) ||
        !(config.steer_ratio > 0.0f) ||
        config.zero_speed_epsilon_mps < 0.0f ||
        config.flip_hysteresis_deg < 0.0f ||
        config.flip_max_wheel_rpm < 0.0f) {
        return false;
    }
    for (int i = 0; i < kDriveModuleCount; ++i) {
        if (!(config.modules[i].wheel_radius_m > 0.0f)) {
            return false;
        }
    }
    return true;
}

float motor_budget_used(const CoordinatorConfig &config,
                        const ModuleTarget &target)
{
    const float steer_axis_rpm = target.steer_rate_deg_per_s / 6.0f;
    return absf(target.wheel_rpm) / config.drive_ratio +
           absf(steer_axis_rpm) / config.steer_ratio;
}

}  // namespace

CoordinatorConfig default_coordinator_config()
{
    CoordinatorConfig config = {};
    config.planned_motor_rpm = 469.0f * 0.90f;
    config.drive_ratio = 32.0f / 11.0f;
    config.steer_ratio = 8.0f / 11.0f;
    config.zero_speed_epsilon_mps = 0.001f;
    config.flip_hysteresis_deg = 10.0f;
    config.flip_max_wheel_rpm = 30.0f;
    configure_project_geometry(&config, kProjectWheelRadiusM);
    return config;
}

bool configure_three_module_ring(CoordinatorConfig *config,
                                 float module_radius_m,
                                 float wheel_radius_m,
                                 float phase_deg)
{
    if (config == 0 || !(module_radius_m > 0.0f) ||
        !(wheel_radius_m > 0.0f)) {
        return false;
    }
    for (int i = 0; i < kDriveModuleCount; ++i) {
        const float angle_rad =
            (phase_deg + 120.0f * static_cast<float>(i)) * kPi / 180.0f;
        config->modules[i].x_m = module_radius_m * cosf(angle_rad);
        config->modules[i].y_m = module_radius_m * sinf(angle_rad);
        config->modules[i].wheel_radius_m = wheel_radius_m;
    }
    return true;
}

bool configure_project_geometry(CoordinatorConfig *config,
                                float wheel_radius_m)
{
    return configure_three_module_ring(config, kProjectModuleRadiusM,
                                       wheel_radius_m,
                                       kProjectUnit1PhaseDeg);
}

void reset_coordinator_state(CoordinatorState *state)
{
    for (int i = 0; i < kDriveModuleCount; ++i) {
        state->last_steer_unwrapped_deg[i] = 0.0f;
        state->flipped[i] = false;
        state->initialized[i] = false;
    }
}

bool coordinate_twist(const CoordinatorConfig &config,
                      const Twist2d &twist,
                      const TwistDerivative2d &derivative,
                      const ModuleFeedback feedback[kDriveModuleCount],
                      CoordinatorState *state,
                      CoordinatorOutput *output)
{
    if (feedback == 0 || state == 0 || output == 0) {
        return false;
    }
    clear_output(output);
    if (!config_valid(config)) {
        return false;
    }

    for (int i = 0; i < kDriveModuleCount; ++i) {
        const ModuleGeometry &geometry = config.modules[i];
        ModuleTarget &target = output->modules[i];
        const float vx = twist.vx_mps - twist.omega_rad_per_s * geometry.y_m;
        const float vy = twist.vy_mps + twist.omega_rad_per_s * geometry.x_m;
        const float ax = derivative.ax_mps2 -
                         derivative.alpha_rad_per_s2 * geometry.y_m;
        const float ay = derivative.ay_mps2 +
                         derivative.alpha_rad_per_s2 * geometry.x_m;
        const float speed_squared = vx * vx + vy * vy;
        const float speed = sqrtf(speed_squared);

        float reference_deg = state->last_steer_unwrapped_deg[i];
        float reference_wheel_rpm = 0.0f;
        if (feedback[i].valid) {
            reference_deg = feedback[i].steer_unwrapped_deg;
            reference_wheel_rpm = feedback[i].wheel_rpm;
        } else if (!state->initialized[i]) {
            reference_deg = 0.0f;
        }

        if (speed <= config.zero_speed_epsilon_mps) {
            target.steer_unwrapped_deg = reference_deg;
            target.wheel_rpm = 0.0f;
            target.steer_rate_deg_per_s = 0.0f;
            target.wheel_accel_rpm_per_s = 0.0f;
            target.flipped = state->flipped[i];
            target.held_at_zero_speed = true;
            state->last_steer_unwrapped_deg[i] = reference_deg;
            state->initialized[i] = true;
            continue;
        }

        const float wrapped_normal_deg = atan2f(vy, vx) * 180.0f / kPi;
        const float normal_deg = nearest_equivalent_deg(
            wrapped_normal_deg, reference_deg);
        const float flipped_deg = nearest_equivalent_deg(
            wrapped_normal_deg + 180.0f, reference_deg);
        const float normal_travel = absf(normal_deg - reference_deg);
        const float flipped_travel = absf(flipped_deg - reference_deg);

        bool use_flipped = state->flipped[i];
        if (!state->initialized[i]) {
            use_flipped =
                absf(reference_wheel_rpm) <= config.flip_max_wheel_rpm &&
                flipped_travel + config.flip_hysteresis_deg < normal_travel;
        } else if (absf(reference_wheel_rpm) <= config.flip_max_wheel_rpm) {
            if (use_flipped) {
                if (normal_travel + config.flip_hysteresis_deg < flipped_travel) {
                    use_flipped = false;
                }
            } else if (flipped_travel + config.flip_hysteresis_deg <
                       normal_travel) {
                use_flipped = true;
            }
        }

        const float direction_sign = use_flipped ? -1.0f : 1.0f;
        const float circumference_m = 2.0f * kPi * geometry.wheel_radius_m;
        const float tangential_accel = (vx * ax + vy * ay) / speed;
        target.steer_unwrapped_deg = use_flipped ? flipped_deg : normal_deg;
        target.wheel_rpm = direction_sign * speed / circumference_m * 60.0f;
        target.steer_rate_deg_per_s =
            (vx * ay - vy * ax) / speed_squared * 180.0f / kPi;
        target.wheel_accel_rpm_per_s =
            direction_sign * tangential_accel / circumference_m * 60.0f;
        target.flipped = use_flipped;
        target.held_at_zero_speed = false;

        state->last_steer_unwrapped_deg[i] = target.steer_unwrapped_deg;
        state->flipped[i] = use_flipped;
        state->initialized[i] = true;
    }

    float peak_motor_rpm = 0.0f;
    for (int i = 0; i < kDriveModuleCount; ++i) {
        const float used = motor_budget_used(config, output->modules[i]);
        if (used > peak_motor_rpm) {
            peak_motor_rpm = used;
        }
    }
    output->common_scale = peak_motor_rpm > config.planned_motor_rpm
        ? config.planned_motor_rpm / peak_motor_rpm
        : 1.0f;
    output->limiting_active = output->common_scale < 0.999999f;

    for (int i = 0; i < kDriveModuleCount; ++i) {
        ModuleTarget &target = output->modules[i];
        target.wheel_rpm *= output->common_scale;
        target.steer_rate_deg_per_s *= output->common_scale;
        target.wheel_accel_rpm_per_s *= output->common_scale;
        target.motor_budget_used_rpm = motor_budget_used(config, target);
    }
    return true;
}

void settlement_begin(SettlementTracker *tracker, uint32_t command_sequence)
{
    if (tracker == 0) {
        return;
    }
    tracker->command_sequence = command_sequence;
    for (int i = 0; i < kDriveModuleCount; ++i) {
        tracker->units[i].fresh = false;
        tracker->units[i].settled = false;
        tracker->units[i].seen_unsettled = false;
    }
}

void settlement_update(SettlementTracker *tracker, uint8_t module_index,
                       bool status_fresh, bool motion_settled)
{
    if (tracker == 0 || module_index >= kDriveModuleCount) {
        return;
    }
    UnitSettlementState &unit = tracker->units[module_index];
    unit.fresh = status_fresh;
    unit.settled = status_fresh && motion_settled;
    if (status_fresh && !motion_settled) {
        unit.seen_unsettled = true;
    }
}

bool settlement_complete(const SettlementTracker &tracker,
                         bool central_profile_complete)
{
    if (!central_profile_complete) {
        return false;
    }
    for (int i = 0; i < kDriveModuleCount; ++i) {
        const UnitSettlementState &unit = tracker.units[i];
        if (!unit.fresh || !unit.seen_unsettled || !unit.settled) {
            return false;
        }
    }
    return true;
}

}  // namespace central
}  // namespace dsd
