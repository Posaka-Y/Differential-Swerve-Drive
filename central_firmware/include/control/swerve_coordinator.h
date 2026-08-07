#pragma once

#include <stdint.h>

namespace dsd {
namespace central {

enum { kDriveModuleCount = 3 };

const float kProjectModuleRadiusM = 0.250f;
const float kProjectUnit1PhaseDeg = 150.0f;
const float kProjectWheelRadiusM = 0.0325f;

struct Twist2d {
    float vx_mps;
    float vy_mps;
    float omega_rad_per_s;
};

struct TwistDerivative2d {
    float ax_mps2;
    float ay_mps2;
    float alpha_rad_per_s2;
};

struct ModuleGeometry {
    float x_m;
    float y_m;
    float wheel_radius_m;
};

struct ModuleFeedback {
    float steer_unwrapped_deg;
    float wheel_rpm;
    bool valid;
};

struct CoordinatorConfig {
    ModuleGeometry modules[kDriveModuleCount];
    float planned_motor_rpm;
    float drive_ratio;
    float steer_ratio;
    float zero_speed_epsilon_mps;
    float flip_hysteresis_deg;
    float flip_max_wheel_rpm;
};

struct ModuleTarget {
    float steer_unwrapped_deg;
    float wheel_rpm;
    float steer_rate_deg_per_s;
    float wheel_accel_rpm_per_s;
    float motor_budget_used_rpm;
    bool flipped;
    bool held_at_zero_speed;
};

struct CoordinatorOutput {
    ModuleTarget modules[kDriveModuleCount];
    float common_scale;
    bool limiting_active;
};

struct CoordinatorState {
    float last_steer_unwrapped_deg[kDriveModuleCount];
    bool flipped[kDriveModuleCount];
    bool initialized[kDriveModuleCount];
};

/* Returns the documented project defaults including the nominal 65mm wheel
 * diameter. A calibrated effective rolling radius may overwrite each module. */
CoordinatorConfig default_coordinator_config();

/* Fills a three-module 120-degree ring. phase_deg is module 1's angle from
 * body +X toward +Y; module 2/3 follow at +120/+240 degrees. */
bool configure_three_module_ring(CoordinatorConfig *config,
                                 float module_radius_m,
                                 float wheel_radius_m,
                                 float phase_deg);

/* Project mounting convention: unit 1=(-216.5,+125)mm, unit 2=(0,-250)mm,
 * unit 3=(+216.5,+125)mm. The sensor module sits on the +Y edge between
 * units 1 and 3. */
bool configure_project_geometry(CoordinatorConfig *config,
                                float wheel_radius_m);

void reset_coordinator_state(CoordinatorState *state);

/* Converts one body-twist time slice into three mutually consistent module
 * targets. Returns false for invalid/missing geometry and leaves output in a
 * safe all-zero state. The common planned-envelope scale is applied equally
 * to all three modules so the requested chassis direction is preserved. */
bool coordinate_twist(const CoordinatorConfig &config,
                      const Twist2d &twist,
                      const TwistDerivative2d &derivative,
                      const ModuleFeedback feedback[kDriveModuleCount],
                      CoordinatorState *state,
                      CoordinatorOutput *output);

struct UnitSettlementState {
    bool fresh;
    bool settled;
    bool seen_unsettled;
};

struct SettlementTracker {
    uint32_t command_sequence;
    UnitSettlementState units[kDriveModuleCount];
};

/* Starts a new command. A unit's pre-existing SETTLED=1 is deliberately not
 * accepted until that unit has reported SETTLED=0 for this command. */
void settlement_begin(SettlementTracker *tracker, uint32_t command_sequence);
void settlement_update(SettlementTracker *tracker, uint8_t module_index,
                       bool status_fresh, bool motion_settled);
bool settlement_complete(const SettlementTracker &tracker,
                         bool central_profile_complete);

}  // namespace central
}  // namespace dsd
