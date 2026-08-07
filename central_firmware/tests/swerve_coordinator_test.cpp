#include "control/swerve_coordinator.h"
#include "control/steer_trajectory.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

using dsd::central::CoordinatorConfig;
using dsd::central::CoordinatorOutput;
using dsd::central::CoordinatorState;
using dsd::central::ModuleFeedback;
using dsd::central::SettlementTracker;
using dsd::central::Twist2d;
using dsd::central::TwistDerivative2d;
using dsd::central::SteerTrajectoryConfig;
using dsd::central::SteerTrajectoryState;
using dsd::central::advance_steer_trajectory;
using dsd::central::coordinate_twist;
using dsd::central::configure_three_module_ring;
using dsd::central::configure_project_geometry;
using dsd::central::default_coordinator_config;
using dsd::central::default_steer_trajectory_config;
using dsd::central::jerk_limited_stop_distance_deg;
using dsd::central::kDriveModuleCount;
using dsd::central::reset_coordinator_state;
using dsd::central::reset_steer_trajectory;
using dsd::central::settlement_begin;
using dsd::central::settlement_complete;
using dsd::central::settlement_update;
using dsd::central::steer_trajectory_complete;

namespace {

int failures = 0;

void expect_true(bool value, const char *message)
{
    if (!value) {
        fprintf(stderr, "FAIL: %s\n", message);
        ++failures;
    }
}

void expect_near(float actual, float expected, float tolerance,
                 const char *message)
{
    if (fabsf(actual - expected) > tolerance) {
        fprintf(stderr, "FAIL: %s actual=%.6f expected=%.6f\n",
                message, actual, expected);
        ++failures;
    }
}

CoordinatorConfig test_config()
{
    CoordinatorConfig config = default_coordinator_config();
    expect_near(config.modules[0].x_m, -0.21650635f, 1e-5f,
                "unit 1 project x");
    expect_near(config.modules[0].y_m, 0.125f, 1e-5f,
                "unit 1 project y");
    expect_near(config.modules[1].x_m, 0.0f, 1e-5f,
                "unit 2 project x");
    expect_near(config.modules[1].y_m, -0.250f, 1e-5f,
                "unit 2 project y");
    expect_near(config.modules[2].x_m, 0.21650635f, 1e-5f,
                "unit 3 project x");
    expect_near(config.modules[2].y_m, 0.125f, 1e-5f,
                "unit 3 project y");
    expect_near(config.modules[0].wheel_radius_m, 0.0325f, 1e-7f,
                "nominal 65mm wheel diameter");
    return config;
}

void clear_feedback(ModuleFeedback feedback[kDriveModuleCount])
{
    for (int i = 0; i < kDriveModuleCount; ++i) {
        feedback[i].steer_unwrapped_deg = 0.0f;
        feedback[i].wheel_rpm = 0.0f;
        feedback[i].valid = true;
    }
}

void test_missing_geometry_fails_safe()
{
    CoordinatorConfig config = default_coordinator_config();
    config.modules[1].wheel_radius_m = 0.0f;
    CoordinatorState state;
    reset_coordinator_state(&state);
    ModuleFeedback feedback[kDriveModuleCount];
    clear_feedback(feedback);
    CoordinatorOutput output;
    const Twist2d twist = {1.0f, 0.0f, 0.0f};
    const TwistDerivative2d derivative = {0.0f, 0.0f, 0.0f};
    expect_true(!coordinate_twist(config, twist, derivative, feedback,
                                  &state, &output),
                "missing wheel radius must reject target generation");
    expect_near(output.modules[0].wheel_rpm, 0.0f, 1e-6f,
                "invalid geometry output must remain zero");
}

void test_straight_and_zero_hold()
{
    CoordinatorConfig config = test_config();
    CoordinatorState state;
    reset_coordinator_state(&state);
    ModuleFeedback feedback[kDriveModuleCount];
    clear_feedback(feedback);
    CoordinatorOutput output;
    const Twist2d straight = {1.0f, 0.0f, 0.0f};
    const TwistDerivative2d no_accel = {0.0f, 0.0f, 0.0f};
    expect_true(coordinate_twist(config, straight, no_accel, feedback,
                                 &state, &output),
                "straight IK should succeed");
    const float expected_rpm =
        60.0f / (2.0f * 3.14159265358979323846f * 0.0325f);
    for (int i = 0; i < kDriveModuleCount; ++i) {
        expect_near(output.modules[i].steer_unwrapped_deg, 0.0f, 1e-4f,
                    "straight steer angle");
        expect_near(output.modules[i].wheel_rpm, expected_rpm, 1e-3f,
                    "straight wheel rpm");
    }

    for (int i = 0; i < kDriveModuleCount; ++i) {
        feedback[i].steer_unwrapped_deg = 37.0f + 10.0f * i;
    }
    const Twist2d stopped = {0.0f, 0.0f, 0.0f};
    expect_true(coordinate_twist(config, stopped, no_accel, feedback,
                                 &state, &output),
                "zero-speed hold should succeed");
    for (int i = 0; i < kDriveModuleCount; ++i) {
        expect_near(output.modules[i].steer_unwrapped_deg,
                    feedback[i].steer_unwrapped_deg, 1e-6f,
                    "zero speed must hold the last explicit angle");
        expect_true(output.modules[i].held_at_zero_speed,
                    "zero speed must be marked as held");
    }
}

void test_pure_rotation()
{
    CoordinatorConfig config = test_config();
    CoordinatorState state;
    reset_coordinator_state(&state);
    ModuleFeedback feedback[kDriveModuleCount];
    clear_feedback(feedback);
    CoordinatorOutput output;
    const Twist2d twist = {0.0f, 0.0f, 1.0f};
    const TwistDerivative2d derivative = {0.0f, 0.0f, 0.0f};
    expect_true(coordinate_twist(config, twist, derivative, feedback,
                                 &state, &output),
                "pure rotation IK should succeed");
    const float magnitude = fabsf(output.modules[0].wheel_rpm);
    for (int i = 1; i < kDriveModuleCount; ++i) {
        expect_near(fabsf(output.modules[i].wheel_rpm), magnitude, 1e-3f,
                    "equilateral pure-rotation wheel magnitudes");
    }
}

void test_flip_and_moving_lockout()
{
    CoordinatorConfig config = test_config();
    ModuleFeedback feedback[kDriveModuleCount];
    clear_feedback(feedback);
    for (int i = 0; i < kDriveModuleCount; ++i) {
        feedback[i].steer_unwrapped_deg = 170.0f;
    }
    CoordinatorState state;
    reset_coordinator_state(&state);
    CoordinatorOutput output;
    const Twist2d straight = {1.0f, 0.0f, 0.0f};
    const TwistDerivative2d derivative = {0.0f, 0.0f, 0.0f};
    expect_true(coordinate_twist(config, straight, derivative, feedback,
                                 &state, &output),
                "low-speed flip calculation should succeed");
    expect_true(output.modules[0].flipped,
                "near-180 feedback should select flipped solution");
    expect_near(output.modules[0].steer_unwrapped_deg, 180.0f, 1e-4f,
                "flipped target should be nearest 180deg equivalent");
    expect_true(output.modules[0].wheel_rpm < 0.0f,
                "flipped target must reverse wheel sign");

    reset_coordinator_state(&state);
    for (int i = 0; i < kDriveModuleCount; ++i) {
        state.initialized[i] = true;
        state.flipped[i] = false;
        state.last_steer_unwrapped_deg[i] = 170.0f;
        feedback[i].wheel_rpm = config.flip_max_wheel_rpm + 1.0f;
    }
    expect_true(coordinate_twist(config, straight, derivative, feedback,
                                 &state, &output),
                "moving flip-lockout calculation should succeed");
    expect_true(!output.modules[0].flipped,
                "flip choice must not change above low-speed threshold");
    expect_true(output.modules[0].wheel_rpm > 0.0f,
                "moving lockout must preserve wheel sign choice");
}

void test_common_desaturation()
{
    CoordinatorConfig config = test_config();
    CoordinatorState state;
    reset_coordinator_state(&state);
    ModuleFeedback feedback[kDriveModuleCount];
    clear_feedback(feedback);
    CoordinatorOutput output;
    const Twist2d excessive = {10.0f, 0.0f, 2.0f};
    const TwistDerivative2d derivative = {0.0f, 4.0f, 0.0f};
    expect_true(coordinate_twist(config, excessive, derivative, feedback,
                                 &state, &output),
                "desaturation calculation should succeed");
    expect_true(output.limiting_active,
                "excessive demand should activate common scale");
    expect_true(output.common_scale > 0.0f && output.common_scale < 1.0f,
                "common scale must be bounded");
    float peak = 0.0f;
    for (int i = 0; i < kDriveModuleCount; ++i) {
        if (output.modules[i].motor_budget_used_rpm > peak) {
            peak = output.modules[i].motor_budget_used_rpm;
        }
    }
    expect_near(peak, config.planned_motor_rpm, 1e-3f,
                "worst module must land on planned motor envelope");
}

void test_settlement_tracker()
{
    SettlementTracker tracker;
    settlement_begin(&tracker, 42U);
    for (int i = 0; i < kDriveModuleCount; ++i) {
        settlement_update(&tracker, static_cast<uint8_t>(i), true, true);
    }
    expect_true(!settlement_complete(tracker, true),
                "stale pre-command settled highs must not complete");
    for (int i = 0; i < kDriveModuleCount; ++i) {
        settlement_update(&tracker, static_cast<uint8_t>(i), true, false);
        settlement_update(&tracker, static_cast<uint8_t>(i), true, true);
    }
    expect_true(!settlement_complete(tracker, false),
                "all units cannot complete before central profile");
    expect_true(settlement_complete(tracker, true),
                "all fresh low-to-high units plus profile should complete");
    settlement_update(&tracker, 1U, false, true);
    expect_true(!settlement_complete(tracker, true),
                "one stale unit must block three-unit completion");
}

void test_jerk_limited_steer_trajectory()
{
    const float simple_stop_distance = 720.0f * 720.0f /
        (2.0f * 2000.0f);
    expect_true(jerk_limited_stop_distance_deg(
                    720.0f, 5400.0f, 2000.0f, 100000.0f) >
                    simple_stop_distance,
                "stop distance must include the positive-accel jerk ramp");

    const float dt_s = 0.005f;
    const float test_jerks[] = {100000.0f, 200000.0f};
    for (unsigned int test_index = 0U;
         test_index < sizeof(test_jerks) / sizeof(test_jerks[0]);
         ++test_index) {
        SteerTrajectoryConfig config = default_steer_trajectory_config();
        config.max_jerk_deg_per_s3 = test_jerks[test_index];
        SteerTrajectoryState state;
        reset_steer_trajectory(&state, 0.0f);
        float largest_jerk = 0.0f;
        float largest_rate = 0.0f;
        for (int step = 0; step < 400; ++step) {
            const float previous_accel = state.accel_deg_per_s2;
            expect_true(advance_steer_trajectory(
                            config, 90.0f, dt_s, &state),
                        "valid jerk trajectory step should succeed");
            const float measured_jerk =
                fabsf(state.accel_deg_per_s2 - previous_accel) / dt_s;
            if (measured_jerk > largest_jerk) {
                largest_jerk = measured_jerk;
            }
            if (fabsf(state.rate_deg_per_s) > largest_rate) {
                largest_rate = fabsf(state.rate_deg_per_s);
            }
            if (steer_trajectory_complete(state, 90.0f)) {
                break;
            }
        }
        expect_true(steer_trajectory_complete(state, 90.0f),
                    "jerk trajectory must settle within two seconds");
        expect_true(largest_jerk <= config.max_jerk_deg_per_s3 + 1.0f,
                    "trajectory must obey jerk limit");
        expect_true(largest_rate <= config.max_rate_deg_per_s + 1e-3f,
                    "trajectory must obey rate limit");
    }

    SteerTrajectoryState invalid_state;
    reset_steer_trajectory(&invalid_state, 12.0f);
    SteerTrajectoryConfig invalid_config = default_steer_trajectory_config();
    invalid_config.max_jerk_deg_per_s3 = 0.0f;
    expect_true(!advance_steer_trajectory(
                    invalid_config, 90.0f, dt_s, &invalid_state),
                "zero-jerk production config must fail safe");
    expect_near(invalid_state.position_unwrapped_deg, 12.0f, 1e-6f,
                "invalid profile must hold its current position");
}

}  // namespace

int main()
{
    test_missing_geometry_fails_safe();
    test_straight_and_zero_hold();
    test_pure_rotation();
    test_flip_and_moving_lockout();
    test_common_desaturation();
    test_settlement_tracker();
    test_jerk_limited_steer_trajectory();
    if (failures != 0) {
        fprintf(stderr, "swerve_coordinator_test: %d failure(s)\n", failures);
        return EXIT_FAILURE;
    }
    puts("swerve_coordinator_test: PASS");
    return EXIT_SUCCESS;
}
