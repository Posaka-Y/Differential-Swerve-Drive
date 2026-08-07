#include "control/steer_trajectory.h"

#include <math.h>

namespace dsd {
namespace central {
namespace {

float absf(float value)
{
    return value < 0.0f ? -value : value;
}

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

float move_toward(float value, float target, float maximum_delta)
{
    if (value < target) {
        return value + maximum_delta < target
            ? value + maximum_delta : target;
    }
    return value - maximum_delta > target
        ? value - maximum_delta : target;
}

bool config_valid(const SteerTrajectoryConfig &config)
{
    return config.max_rate_deg_per_s > 0.0f &&
           config.max_accel_deg_per_s2 > 0.0f &&
           config.max_decel_deg_per_s2 > 0.0f &&
           config.max_jerk_deg_per_s3 > 0.0f &&
           config.terminal_snap_max_error_deg >= 0.0f;
}

}  // namespace

SteerTrajectoryConfig default_steer_trajectory_config()
{
    SteerTrajectoryConfig config = {};
    config.max_rate_deg_per_s = 720.0f;
    config.max_accel_deg_per_s2 = 5400.0f;
    config.max_decel_deg_per_s2 = 2000.0f;
    config.max_jerk_deg_per_s3 = 100000.0f;
    config.terminal_snap_max_error_deg = 2.0f;
    return config;
}

void reset_steer_trajectory(SteerTrajectoryState *state,
                            float position_unwrapped_deg)
{
    if (state == 0) {
        return;
    }
    state->position_unwrapped_deg = position_unwrapped_deg;
    state->rate_deg_per_s = 0.0f;
    state->accel_deg_per_s2 = 0.0f;
    state->initialized = true;
}

float jerk_limited_stop_distance_deg(float speed_deg_per_s,
                                     float accel_deg_per_s2,
                                     float max_decel_deg_per_s2,
                                     float max_jerk_deg_per_s3)
{
    const float speed = speed_deg_per_s > 0.0f ? speed_deg_per_s : 0.0f;
    if (speed <= 0.0f) {
        return 0.0f;
    }
    if (!(max_decel_deg_per_s2 > 0.0f) ||
        !(max_jerk_deg_per_s3 > 0.0f)) {
        return INFINITY;
    }
    const float accel = accel_deg_per_s2 < -max_decel_deg_per_s2
        ? -max_decel_deg_per_s2 : accel_deg_per_s2;
    const float ramp_time = (accel + max_decel_deg_per_s2) > 0.0f
        ? (accel + max_decel_deg_per_s2) / max_jerk_deg_per_s3 : 0.0f;
    const float stop_during_ramp =
        (accel + sqrtf(accel * accel +
                       2.0f * max_jerk_deg_per_s3 * speed)) /
        max_jerk_deg_per_s3;
    if (stop_during_ramp <= ramp_time) {
        const float t = stop_during_ramp;
        const float distance = speed * t + 0.5f * accel * t * t -
            max_jerk_deg_per_s3 * t * t * t / 6.0f;
        return distance > 0.0f ? distance : 0.0f;
    }
    const float t = ramp_time;
    const float ramp_distance = speed * t + 0.5f * accel * t * t -
        max_jerk_deg_per_s3 * t * t * t / 6.0f;
    const float speed_after_ramp_raw = speed + accel * t -
        0.5f * max_jerk_deg_per_s3 * t * t;
    const float speed_after_ramp = speed_after_ramp_raw > 0.0f
        ? speed_after_ramp_raw : 0.0f;
    return (ramp_distance > 0.0f ? ramp_distance : 0.0f) +
        speed_after_ramp * speed_after_ramp /
        (2.0f * max_decel_deg_per_s2);
}

bool advance_steer_trajectory(const SteerTrajectoryConfig &config,
                              float destination_unwrapped_deg,
                              float dt_s,
                              SteerTrajectoryState *state)
{
    if (state == 0) {
        return false;
    }
    if (!state->initialized) {
        reset_steer_trajectory(state, destination_unwrapped_deg);
    }
    if (!config_valid(config) || !(dt_s > 0.0f)) {
        state->rate_deg_per_s = 0.0f;
        state->accel_deg_per_s2 = 0.0f;
        return false;
    }

    const float error = destination_unwrapped_deg -
        state->position_unwrapped_deg;
    const float jerk_step = config.max_jerk_deg_per_s3 * dt_s;
    if (absf(error) < 1e-6f && absf(state->rate_deg_per_s) < 0.01f) {
        state->position_unwrapped_deg = destination_unwrapped_deg;
        state->rate_deg_per_s = 0.0f;
        state->accel_deg_per_s2 = move_toward(
            state->accel_deg_per_s2, 0.0f, jerk_step);
        return true;
    }

    const float direction = error >= 0.0f ? 1.0f : -1.0f;
    const float remaining = absf(error);
    const float speed_toward = state->rate_deg_per_s * direction;
    const float accel_toward = state->accel_deg_per_s2 * direction;
    float desired_accel_toward;
    if (speed_toward < 0.0f) {
        desired_accel_toward = config.max_accel_deg_per_s2;
    } else {
        const float stop_distance = jerk_limited_stop_distance_deg(
            speed_toward, accel_toward,
            config.max_decel_deg_per_s2,
            config.max_jerk_deg_per_s3);
        const float lookahead = speed_toward * dt_s +
            0.5f * (accel_toward > 0.0f ? accel_toward : 0.0f) *
            dt_s * dt_s;
        if (remaining <= stop_distance + lookahead) {
            desired_accel_toward = -config.max_decel_deg_per_s2;
        } else {
            const float rate_headroom =
                config.max_rate_deg_per_s - speed_toward;
            const float positive_accel = accel_toward > 0.0f
                ? accel_toward : 0.0f;
            const float fade_delta = positive_accel * positive_accel /
                (2.0f * config.max_jerk_deg_per_s3);
            desired_accel_toward = rate_headroom <= fade_delta
                ? 0.0f : config.max_accel_deg_per_s2;
        }
    }

    const float next_accel = move_toward(
        state->accel_deg_per_s2,
        direction * desired_accel_toward,
        jerk_step);
    const float next_rate = clampf(
        state->rate_deg_per_s +
            0.5f * (state->accel_deg_per_s2 + next_accel) * dt_s,
        -config.max_rate_deg_per_s,
        config.max_rate_deg_per_s);
    const float next_speed_toward = next_rate * direction;

    if (speed_toward < 0.0f && next_speed_toward >= 0.0f &&
        remaining <= config.terminal_snap_max_error_deg) {
        state->position_unwrapped_deg = destination_unwrapped_deg;
        state->rate_deg_per_s = 0.0f;
        state->accel_deg_per_s2 = next_accel;
        return true;
    }

    state->position_unwrapped_deg +=
        0.5f * (state->rate_deg_per_s + next_rate) * dt_s;
    state->rate_deg_per_s = next_rate;
    state->accel_deg_per_s2 = next_accel;
    return true;
}

bool steer_trajectory_complete(const SteerTrajectoryState &state,
                               float destination_unwrapped_deg)
{
    return state.initialized &&
        absf(state.position_unwrapped_deg - destination_unwrapped_deg) < 1e-5f &&
        absf(state.rate_deg_per_s) < 1e-5f &&
        absf(state.accel_deg_per_s2) < 1e-5f;
}

}  // namespace central
}  // namespace dsd
