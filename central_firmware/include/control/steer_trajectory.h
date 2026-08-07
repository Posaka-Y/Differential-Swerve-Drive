#pragma once

namespace dsd {
namespace central {

struct SteerTrajectoryConfig {
    float max_rate_deg_per_s;
    float max_accel_deg_per_s2;
    float max_decel_deg_per_s2;
    float max_jerk_deg_per_s3;
    float terminal_snap_max_error_deg;
};

struct SteerTrajectoryState {
    float position_unwrapped_deg;
    float rate_deg_per_s;
    float accel_deg_per_s2;
    bool initialized;
};

SteerTrajectoryConfig default_steer_trajectory_config();

void reset_steer_trajectory(SteerTrajectoryState *state,
                            float position_unwrapped_deg);

/* Exact distance required to stop from a positive speed while acceleration
 * slews toward -max_decel at max_jerk, then remains at max deceleration. */
float jerk_limited_stop_distance_deg(float speed_deg_per_s,
                                     float accel_deg_per_s2,
                                     float max_decel_deg_per_s2,
                                     float max_jerk_deg_per_s3);

/* Advances an unwrapped steering target by one central-control time step.
 * Returns false for invalid arguments and leaves an initialized state held
 * at its current position with zero rate/acceleration. */
bool advance_steer_trajectory(const SteerTrajectoryConfig &config,
                              float destination_unwrapped_deg,
                              float dt_s,
                              SteerTrajectoryState *state);

bool steer_trajectory_complete(const SteerTrajectoryState &state,
                               float destination_unwrapped_deg);

}  // namespace central
}  // namespace dsd
