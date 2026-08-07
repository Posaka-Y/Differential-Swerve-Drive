#include "control/unit_controller.h"

#include <math.h>
#include <stdio.h>

enum { TEST_FAILURE = 1 };

static int failures;

static float circular_error_deg(float target_deg, float actual_deg)
{
    float error = unit_normalize_angle_deg(target_deg) -
                  unit_normalize_angle_deg(actual_deg);
    if (error >= 180.0f) {
        error -= 360.0f;
    } else if (error < -180.0f) {
        error += 360.0f;
    }
    return error;
}

static void expect_near(const char *name, float actual, float expected,
                        float tolerance)
{
    if (fabsf(actual - expected) > tolerance) {
        fprintf(stderr, "FAIL %s: actual=%.6f expected=%.6f tolerance=%.6f\n",
                name, actual, expected, tolerance);
        failures++;
    }
}

static unit_controller_config_t test_config(float observer_tau_s)
{
    const unit_controller_config_t config = {
        .motor_max_rpm = 469.0f,
        .steer_max_rpm = 60.0f,
        .steer_accel_rpm_per_s = 600.0f,
        .angle_kp_rpm_per_deg = 4.0f,
        .moving_angle_kp_rpm_per_deg = 1.0f,
        .wheel_accel_rpm_per_s = 4000.0f,
        .steer_mode_kp = 120.0f,
        .steer_mode_ki = 50.0f,
        .steer_brake_kp_multiplier = 1.0f,
        .drive_mode_kp = 20.0f,
        .drive_mode_ki = 100.0f,
        .steer_mode_backcalc_gain = 0.0f,
        .drive_mode_backcalc_gain = 0.0f,
        .mode_integral_limit = 1200.0f,
        .mode_rpm_filter_tau_s = 0.0f,
        .steer_schedule_filter_tau_s = 0.010f,
        .steer_observer_correction_tau_s = observer_tau_s,
        .current_limit = 4000.0f,
        .steer_motor_sign = 1.0f,
    };
    return config;
}

static void test_first_sample_seeds_absolute_angle(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 271.25f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    const unit_controller_config_t config = test_config(0.050f);

    unit_controller_init(&controller, &config);
    unit_controller_update(&controller, &measurement, 0.001f, &output);

    expect_near("seed angle", output.steer_angle_observer_deg, 271.25f,
                0.0001f);
    expect_near("seed innovation", output.steer_observer_innovation_deg,
                0.0f, 0.0001f);
}

static void test_prediction_crosses_absolute_wrap(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 359.9f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    const unit_controller_config_t config = test_config(0.050f);

    unit_controller_init(&controller, &config);
    unit_controller_update(&controller, &measurement, 0.001f, &output);

    /* 82.5 common-mode motor rpm * 8/11 = 60 axis rpm = 360deg/s. */
    measurement.steer_deg = 0.26f;
    measurement.motor1_rpm = 82.5f;
    measurement.motor2_rpm = 82.5f;
    unit_controller_update(&controller, &measurement, 0.001f, &output);

    expect_near("wrap angle error",
                circular_error_deg(0.26f, output.steer_angle_observer_deg),
                0.0f, 0.001f);
    expect_near("wrap innovation", output.steer_observer_innovation_deg,
                0.0f, 0.001f);
    expect_near("wrap rate", output.steer_axis_observer_rpm, 60.0f, 0.001f);
}

static void test_absolute_angle_removes_integrated_drift(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 0.0f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    const unit_controller_config_t config = test_config(0.050f);

    unit_controller_init(&controller, &config);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    measurement.steer_deg = 10.0f;
    for (unsigned int i = 0; i < 500U; i++) {
        unit_controller_update(&controller, &measurement, 0.001f, &output);
    }

    expect_near("drift correction",
                circular_error_deg(10.0f, output.steer_angle_observer_deg),
                0.0f, 0.001f);
}

static void test_zero_tau_tracks_amt_directly(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 42.0f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    const unit_controller_config_t config = test_config(0.0f);

    unit_controller_init(&controller, &config);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    measurement.steer_deg = 43.5f;
    measurement.motor1_rpm = 20.0f;
    measurement.motor2_rpm = 20.0f;
    unit_controller_update(&controller, &measurement, 0.001f, &output);

    expect_near("zero tau angle", output.steer_angle_observer_deg, 43.5f,
                0.0001f);
}

static void test_reset_reseeds_without_old_state(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 12.0f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    const unit_controller_config_t config = test_config(0.050f);

    unit_controller_init(&controller, &config);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    measurement.steer_deg = 123.0f;
    unit_controller_reset(&controller);
    unit_controller_update(&controller, &measurement, 0.001f, &output);

    expect_near("reset seed", output.steer_angle_observer_deg, 123.0f,
                0.0001f);
    expect_near("reset innovation", output.steer_observer_innovation_deg,
                0.0f, 0.0001f);
}

static void test_observer_speed_fades_breakaway_feedforward(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 0.0f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    unit_controller_config_t config = test_config(0.050f);
    config.steer_mode_kp = 0.0f;
    config.steer_mode_ki = 0.0f;
    config.steer_friction_ff_current = 200.0f;
    config.steer_friction_ff_fade_axis_rpm = 10.0f;

    unit_controller_init(&controller, &config);
    unit_controller_set_target(&controller, 0.0f, 10.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("stationary friction feedforward", output.steer_mode_current,
                200.0f, 0.001f);

    measurement.steer_deg = 0.06f;
    measurement.motor1_rpm = 13.75f;
    measurement.motor2_rpm = 13.75f;
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("moving friction feedforward faded",
                output.steer_mode_current, 0.0f, 0.001f);
}

static void test_high_speed_p0_telemetry_is_behavior_neutral(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 0.0f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    unit_controller_config_t config = test_config(0.050f);
    config.current_limit = 100.0f;
    config.steer_mode_kp = 0.0f;
    config.steer_mode_ki = 0.0f;
    config.steer_accel_rpm_per_s = 100000.0f;
    config.steer_accel_ff_current_per_mode_rpm_per_s = 1.0f;
    config.steer_decel_ff_current_per_mode_rpm_per_s = 2.0f;

    unit_controller_init(&controller, &config);
    unit_controller_set_target(&controller, 0.0f, 0.0f);
    unit_controller_set_steer_rate_ff_rpm(&controller, 10.0f);
    unit_controller_set_steer_accel_ff_rpm_per_s(&controller, 100.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);

    expect_near("schedule 10ms LPF first sample", output.steer_schedule_rpm,
                10.0f / 11.0f, 0.0001f);
    expect_near("scheduled Kp mirrors fixed config",
                output.scheduled_steer_mode_kp, 0.0f, 0.0001f);
    expect_near("scheduled Ki mirrors fixed config",
                output.scheduled_steer_mode_ki, 0.0f, 0.0001f);
    expect_near("scheduled accel FF mirrors fixed config",
                output.scheduled_steer_accel_ff_gain, 1.0f, 0.0001f);
    expect_near("scheduled brake FF mirrors fixed config",
                output.scheduled_steer_decel_ff_gain, 2.0f, 0.0001f);
    expect_near("unsaturated steer mode current",
                output.steer_mode_current_unsaturated, 137.5f, 0.001f);
    expect_near("applied steer mode current",
                output.steer_mode_current_applied, 100.0f, 0.001f);
    expect_near("steer saturation residual",
                output.steer_saturation_residual, -37.5f, 0.001f);
    expect_near("existing output remains applied current",
                output.steer_mode_current, 100.0f, 0.001f);
    expect_near("saturation duration first cycle",
                (float)output.steer_saturation_duration_ms, 1.0f, 0.001f);
    expect_near("acceleration phase", (float)output.steer_braking_active,
                0.0f, 0.001f);

    unit_controller_set_steer_accel_ff_rpm_per_s(&controller, -100.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("braking feedforward selected",
                output.steer_mode_current_unsaturated, -275.0f, 0.001f);
    expect_near("braking applied current",
                output.steer_mode_current_applied, -100.0f, 0.001f);
    expect_near("braking residual", output.steer_saturation_residual,
                175.0f, 0.001f);
    expect_near("saturation duration second cycle",
                (float)output.steer_saturation_duration_ms, 2.0f, 0.001f);
    expect_near("braking phase", (float)output.steer_braking_active,
                1.0f, 0.001f);

    unit_controller_reset(&controller);
    expect_near("reset schedule state", controller.steer_schedule_rpm,
                0.0f, 0.0001f);
    expect_near("reset saturation duration",
                controller.steer_saturation_duration_s, 0.0f, 0.0001f);
}

static void test_braking_kp_multiplier_only_applies_while_braking(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 0.0f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    unit_controller_config_t config = test_config(0.050f);
    config.steer_mode_kp = 10.0f;
    config.steer_mode_ki = 0.0f;
    config.steer_brake_kp_multiplier = 2.0f;
    config.steer_accel_rpm_per_s = 100000.0f;

    unit_controller_init(&controller, &config);
    unit_controller_set_target(&controller, 0.0f, 0.0f);
    unit_controller_set_steer_rate_ff_rpm(&controller, 10.0f);
    unit_controller_set_steer_accel_ff_rpm_per_s(&controller, 100.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("acceleration Kp unchanged",
                output.scheduled_steer_mode_kp, 10.0f, 0.0001f);
    expect_near("acceleration P current", output.steer_mode_current,
                137.5f, 0.001f);

    unit_controller_reset(&controller);
    unit_controller_set_steer_rate_ff_rpm(&controller, 10.0f);
    unit_controller_set_steer_accel_ff_rpm_per_s(&controller, -100.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("braking Kp multiplied",
                output.scheduled_steer_mode_kp, 20.0f, 0.0001f);
    expect_near("braking P current", output.steer_mode_current,
                275.0f, 0.001f);

    if (!unit_controller_set_steer_brake_kp_knot(
            &controller, 0U, 1.0f) ||
        !unit_controller_set_steer_brake_kp_knot(
            &controller, 1U, 2.0f) ||
        !unit_controller_set_steer_brake_kp_knot(
            &controller, 2U, 3.0f) ||
        !unit_controller_set_steer_brake_kp_knot(
            &controller, 3U, 4.0f)) {
        fprintf(stderr, "FAIL valid brake Kp knot rejected\n");
        failures++;
    }
    if (unit_controller_set_steer_brake_kp_knot(
            &controller, UNIT_STEER_GAIN_KNOT_COUNT, 2.0f)) {
        fprintf(stderr, "FAIL invalid brake Kp knot accepted\n");
        failures++;
    }
    controller.config.steer_schedule_filter_tau_s = 0.0f;
    controller.config.steer_max_rpm = 100.0f;
    controller.config.current_limit = 30000.0f;
    unit_controller_reset(&controller);
    unit_controller_set_steer_rate_ff_rpm(&controller, 80.0f);
    unit_controller_set_steer_accel_ff_rpm_per_s(&controller, -100.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    /* 80rpm lies halfway from 60 to 100: multiplier 2.5, base Kp 10. */
    expect_near("scheduled braking Kp multiplier interpolation",
                output.scheduled_steer_mode_kp, 25.0f, 0.0001f);

    controller.config.steer_brake_kp_multiplier = 1.5f;
    unit_controller_set_uniform_steer_brake_kp_schedule(&controller);
    unit_controller_reset(&controller);
    unit_controller_set_steer_rate_ff_rpm(&controller, 80.0f);
    unit_controller_set_steer_accel_ff_rpm_per_s(&controller, -100.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("uniform braking Kp multiplier compatibility",
                output.scheduled_steer_mode_kp, 15.0f, 0.0001f);
}

static void test_continuous_gain_schedule_interpolation(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 0.0f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    unit_controller_config_t config = test_config(0.050f);
    config.steer_max_rpm = 250.0f;
    config.steer_accel_rpm_per_s = 1000000.0f;
    config.steer_schedule_filter_tau_s = 0.0f;
    config.mode_integral_limit = 0.0f;
    config.current_limit = 30000.0f;

    unit_controller_init(&controller, &config);
    if (!unit_controller_set_steer_gain_knot(
            &controller, 0U, 100.0f, 10.0f, 1.0f, 2.0f, 0.0f) ||
        !unit_controller_set_steer_gain_knot(
            &controller, 1U, 160.0f, 20.0f, 2.0f, 3.0f, 1.0f) ||
        !unit_controller_set_steer_gain_knot(
            &controller, 2U, 200.0f, 30.0f, 3.0f, 4.0f, 2.0f) ||
        !unit_controller_set_steer_gain_knot(
            &controller, 3U, 250.0f, 40.0f, 4.0f, 5.0f, 3.0f)) {
        fprintf(stderr, "FAIL valid gain knot rejected\n");
        failures++;
    }
    if (unit_controller_set_steer_gain_knot(
            &controller, UNIT_STEER_GAIN_KNOT_COUNT,
            1.0f, 1.0f, 1.0f, 1.0f, 1.0f)) {
        fprintf(stderr, "FAIL invalid gain knot accepted\n");
        failures++;
    }

    unit_controller_set_target(&controller, 0.0f, 0.0f);
    /* With a zero reference, measured/observer speed must keep the high-speed
     * gain active through braking. 165 motor-mode rpm * 8/11 = 120 axis rpm. */
    measurement.motor1_rpm = 165.0f;
    measurement.motor2_rpm = 165.0f;
    unit_controller_set_steer_rate_ff_rpm(&controller, 0.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("observer holds high-speed schedule",
                output.steer_schedule_rpm, 120.0f, 0.001f);
    expect_near("120rpm interpolated Kp", output.scheduled_steer_mode_kp,
                220.0f, 0.001f);

    unit_controller_reset(&controller);
    measurement.motor1_rpm = 0.0f;
    measurement.motor2_rpm = 0.0f;
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("0rpm lower knot", output.scheduled_steer_mode_kp,
                100.0f, 0.001f);

    unit_controller_set_steer_rate_ff_rpm(&controller, 80.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("80rpm scheduled Kp", output.scheduled_steer_mode_kp,
                180.0f, 0.0001f);
    expect_near("80rpm scheduled Ki", output.scheduled_steer_mode_ki,
                25.0f, 0.0001f);
    expect_near("80rpm scheduled accel FF",
                output.scheduled_steer_accel_ff_gain, 2.5f, 0.0001f);
    expect_near("80rpm scheduled decel FF",
                output.scheduled_steer_decel_ff_gain, 3.5f, 0.0001f);
    expect_near("80rpm scheduled Kaw",
                output.scheduled_steer_backcalc_gain, 1.5f, 0.0001f);
    /* 80 axis rpm / (8/11) = 110 motor-mode rpm. Integral is clamped at 0,
     * so this also proves the interpolated Kp drives the actual PI path. */
    expect_near("scheduled Kp applied to PI", output.steer_mode_current,
                19800.0f, 0.01f);

    unit_controller_set_steer_rate_ff_rpm(&controller, 59.9f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("59.9rpm continuity", output.scheduled_steer_mode_kp,
                159.9f, 0.001f);
    unit_controller_set_steer_rate_ff_rpm(&controller, 60.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("60rpm knot", output.scheduled_steer_mode_kp,
                160.0f, 0.001f);
    unit_controller_set_steer_rate_ff_rpm(&controller, 60.1f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("60.1rpm continuity", output.scheduled_steer_mode_kp,
                160.1f, 0.001f);

    unit_controller_set_steer_rate_ff_rpm(&controller, 100.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("100rpm knot", output.scheduled_steer_mode_kp,
                200.0f, 0.001f);
    unit_controller_set_steer_rate_ff_rpm(&controller, 150.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("150rpm knot", output.scheduled_steer_mode_kp,
                250.0f, 0.001f);

    unit_controller_set_steer_rate_ff_rpm(&controller, 200.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("schedule upper clamp", output.scheduled_steer_mode_kp,
                250.0f, 0.001f);

    unit_controller_reset(&controller);
    expect_near("schedule reset state", controller.steer_schedule_rpm,
                0.0f, 0.0001f);
    unit_controller_set_steer_rate_ff_rpm(&controller, 80.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("gain table survives reset", output.scheduled_steer_mode_kp,
                180.0f, 0.0001f);

    controller.config.steer_mode_kp = 123.0f;
    controller.config.steer_mode_ki = 45.0f;
    controller.config.steer_accel_ff_current_per_mode_rpm_per_s = 0.5f;
    controller.config.steer_decel_ff_current_per_mode_rpm_per_s = 0.75f;
    controller.config.steer_mode_backcalc_gain = 0.0f;
    unit_controller_set_uniform_steer_gain_schedule(&controller);
    unit_controller_update(&controller, &measurement, 0.001f, &output);
    expect_near("uniform runtime Kp compatibility",
                output.scheduled_steer_mode_kp, 123.0f, 0.0001f);
    expect_near("uniform runtime Ki compatibility",
                output.scheduled_steer_mode_ki, 45.0f, 0.0001f);
}

static void test_backcalculation_uses_shared_scale_residual(void)
{
    unit_controller_t controller;
    unit_control_output_t output;
    unit_measurement_t measurement = {
        .steer_deg = 0.0f,
        .motor1_rpm = 0.0f,
        .motor2_rpm = 0.0f,
    };
    unit_controller_config_t config = test_config(0.050f);
    config.current_limit = 100.0f;
    config.steer_mode_kp = 0.0f;
    config.steer_mode_ki = 0.0f;
    config.steer_accel_rpm_per_s = 100000.0f;
    config.steer_accel_ff_current_per_mode_rpm_per_s = 1.0f;
    config.steer_mode_backcalc_gain = 2.0f;

    unit_controller_init(&controller, &config);
    unit_controller_set_target(&controller, 0.0f, 0.0f);
    unit_controller_set_steer_rate_ff_rpm(&controller, 10.0f);
    unit_controller_set_steer_accel_ff_rpm_per_s(&controller, 100.0f);
    unit_controller_update(&controller, &measurement, 0.001f, &output);

    /* Unsat 137.5 -> applied 100 -> residual -37.5. With Kaw=2/s and
     * dt=1ms, the next-cycle integral correction is -0.075 current raw. */
    expect_near("backcalc unsaturated demand",
                output.steer_mode_current_unsaturated, 137.5f, 0.001f);
    expect_near("backcalc current-cycle command unchanged",
                output.steer_mode_current_applied, 100.0f, 0.001f);
    expect_near("backcalc correction", output.steer_backcalc_correction,
                -0.075f, 0.0001f);
    expect_near("backcalc stored integral", output.steer_mode_integral,
                -0.075f, 0.0001f);
    expect_near("drive backcalc unaffected", output.drive_backcalc_correction,
                0.0f, 0.0001f);
}

int main(void)
{
    test_first_sample_seeds_absolute_angle();
    test_prediction_crosses_absolute_wrap();
    test_absolute_angle_removes_integrated_drift();
    test_zero_tau_tracks_amt_directly();
    test_reset_reseeds_without_old_state();
    test_observer_speed_fades_breakaway_feedforward();
    test_high_speed_p0_telemetry_is_behavior_neutral();
    test_braking_kp_multiplier_only_applies_while_braking();
    test_continuous_gain_schedule_interpolation();
    test_backcalculation_uses_shared_scale_residual();

    if (failures != 0) {
        fprintf(stderr, "unit_controller_observer_test: %d failure(s)\n",
                failures);
        return TEST_FAILURE;
    }
    puts("unit_controller_observer_test: PASS");
    return 0;
}
