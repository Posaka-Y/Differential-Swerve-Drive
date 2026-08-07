#!/usr/bin/env python3
"""Coarse-to-fine hardware tuner for one differential-swerve unit.

The Web UI must already be running.  This tool uses its profiled target and
safe STOP APIs, while SET_CONFIG parameters are sent directly over SocketCAN.
It performs a pattern search: evaluate the current center plus/minus one span
for every selected parameter, keep the best point, shrink all spans, repeat.

Every candidate is tested with paired +90/-90 degree moves so the steer axis
returns near the same absolute angle.  Results are written incrementally to
CSV.  A dependency-free SVG plots score versus every searched parameter.
"""

import argparse
import atexit
import csv
import json
import math
import random
import socket
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from unit_bench import emergency_disable, open_can_socket, send_set_config


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULT_DIR = REPO_ROOT / "firmware" / "logs" / "auto-tune"
TUNER_STATUS_PERIOD_MS = 5.0
# Operational steering acceptance: reaching the useful angular neighborhood
# matters more than waiting for the unloaded mechanism to remain below 1rpm.
# The old strict settle gate is retained in reports as a diagnostic.
ACCEPT_FIRST_ENTRY_2DEG_S = 0.50
# Response-first commissioning gate requested for the 150->300rpm push.
# A 20deg transient on a 90deg unloaded bench move is accepted provided the
# useful 2deg neighborhood is reached quickly and terminal error remains low.
# The old 4deg/no-oscillation view remains visible as the strict diagnostic.
ACCEPT_OVERSHOOT_DEG = 20.0
ACCEPT_TERMINAL_ERROR_DEG = 1.0
STRICT_ACCEPT_OVERSHOOT_DEG = 4.0
STRICT_ACCEPT_WORST_SETTLE_S = 0.9


@dataclass(frozen=True)
class Parameter:
    name: str
    minimum: float
    maximum: float
    default: float
    span: float
    config_index: int | None = None
    web_field: str | None = None


PARAMETERS = {
    "steer_kp": Parameter("steer_kp", 10.0, 300.0, 120.0, 40.0, config_index=3),
    "steer_ki": Parameter("steer_ki", 0.0, 100.0, 50.0, 20.0, config_index=4),
    "angle_kp": Parameter("angle_kp", 0.5, 10.0, 4.0, 1.0, config_index=5),
    "moving_angle_kp": Parameter(
        "moving_angle_kp", 0.0, 4.0, 1.0, 0.5, config_index=19),
    "steer_min_rpm": Parameter(
        "steer_min_rpm", 0.0, 5.0, 0.0, 1.0, config_index=8),
    "steer_max_rpm": Parameter(
        "steer_max_rpm", 40.0, 341.1, 120.0, 20.0, config_index=7),
    "steer_accel_limit_rpm_per_s": Parameter(
        "steer_accel_limit_rpm_per_s", 100.0, 4000.0, 2000.0, 500.0,
        config_index=9),
    "angle_deadband_deg": Parameter(
        "angle_deadband_deg", 0.1, 1.0, 0.3, 0.3, config_index=6),
    "mode_filter_tau_s": Parameter(
        "mode_filter_tau_s", 0.0, 0.05, 0.002, 0.005, config_index=13),
    "steer_observer_tau_s": Parameter(
        "steer_observer_tau_s", 0.005, 0.5, 0.050, 0.025,
        config_index=23),
    "steer_friction_ff_fade_axis_rpm": Parameter(
        "steer_friction_ff_fade_axis_rpm", 0.0, 100.0, 10.0, 5.0,
        config_index=24),
    "steer_backcalc_gain": Parameter(
        "steer_backcalc_gain", 0.0, 20.0, 0.0, 2.0, config_index=25),
    "drive_backcalc_gain": Parameter(
        "drive_backcalc_gain", 0.0, 20.0, 0.0, 2.0, config_index=26),
    "steer_brake_kp_multiplier": Parameter(
        "steer_brake_kp_multiplier", 1.0, 4.0, 2.0, 0.5,
        config_index=47),
    "current_limit": Parameter(
        "current_limit", 2000.0, 6000.0, 4000.0, 1000.0, config_index=12),
    "steer_rate_dps": Parameter(
        "steer_rate_dps", 60.0, 2046.0, 720.0, 120.0,
        web_field="steer_rate_dps"),
    "steer_commissioning_cap_rpm": Parameter(
        "steer_commissioning_cap_rpm", 5.0, 341.0, 120.0, 20.0,
        web_field="steer_commissioning_cap_rpm"),
    "steer_accel_dps2": Parameter(
        "steer_accel_dps2", 180.0, 12000.0, 5400.0, 720.0,
        web_field="steer_accel_dps2"),
    "steer_decel_dps2": Parameter(
        "steer_decel_dps2", 180.0, 12000.0, 2000.0, 450.0,
        web_field="steer_decel_dps2"),
    "steer_jerk_dps3": Parameter(
        "steer_jerk_dps3", 0.0, 500000.0, 0.0, 100000.0,
        web_field="steer_jerk_dps3"),
    "steer_accel_ff_gain": Parameter(
        "steer_accel_ff_gain", 0.0, 10.0, 0.5, 0.5, config_index=18),
    "steer_decel_ff_gain": Parameter(
        "steer_decel_ff_gain", 0.0, 10.0, 0.5, 0.5, config_index=20),
    "steer_friction_ff_current": Parameter(
        "steer_friction_ff_current", 0.0, 1000.0, 200.0, 200.0,
        config_index=21),
    # Per-band schedule parameters. Legacy scalar indices above are applied
    # first and establish the uniform baseline; these later entries then
    # override only the selected 100/150rpm knots (SET_CONFIG 37..46).
    "steer_kp_100": Parameter(
        "steer_kp_100", 10.0, 300.0, 140.0, 20.0, config_index=37),
    "steer_ki_100": Parameter(
        "steer_ki_100", 0.0, 100.0, 50.0, 20.0, config_index=38),
    "steer_accel_ff_gain_100": Parameter(
        "steer_accel_ff_gain_100", 0.0, 10.0, 0.5, 0.5, config_index=39),
    "steer_decel_ff_gain_100": Parameter(
        "steer_decel_ff_gain_100", 0.0, 10.0, 2.5, 0.5, config_index=40),
    "steer_backcalc_gain_100": Parameter(
        "steer_backcalc_gain_100", 0.0, 20.0, 0.0, 2.0, config_index=41),
    "steer_brake_kp_multiplier_100": Parameter(
        "steer_brake_kp_multiplier_100", 1.0, 4.0, 2.0, 0.5,
        config_index=50),
    "steer_kp_150": Parameter(
        "steer_kp_150", 10.0, 300.0, 140.0, 20.0, config_index=42),
    "steer_ki_150": Parameter(
        "steer_ki_150", 0.0, 100.0, 50.0, 20.0, config_index=43),
    "steer_accel_ff_gain_150": Parameter(
        "steer_accel_ff_gain_150", 0.0, 10.0, 0.5, 0.5, config_index=44),
    "steer_decel_ff_gain_150": Parameter(
        "steer_decel_ff_gain_150", 0.0, 10.0, 2.5, 0.5, config_index=45),
    "steer_backcalc_gain_150": Parameter(
        "steer_backcalc_gain_150", 0.0, 20.0, 0.0, 2.0, config_index=46),
    "steer_brake_kp_multiplier_150": Parameter(
        "steer_brake_kp_multiplier_150", 1.0, 4.0, 2.0, 0.5,
        config_index=51),
}


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def angle_error(actual_deg, target_deg):
    return (actual_deg - target_deg + 180.0) % 360.0 - 180.0


def steer_profile_min_time_s(distance_deg, max_rate_dps,
                             accel_dps2, decel_dps2):
    distance_deg = abs(distance_deg)
    max_rate_dps = abs(max_rate_dps)
    if distance_deg <= 1e-9:
        return 0.0
    if max_rate_dps <= 0.0 or accel_dps2 <= 0.0 or decel_dps2 <= 0.0:
        raise ValueError("invalid steer profile limits")
    critical = (max_rate_dps * max_rate_dps / (2.0 * accel_dps2)
                + max_rate_dps * max_rate_dps / (2.0 * decel_dps2))
    if distance_deg >= critical:
        return (max_rate_dps / accel_dps2
                + (distance_deg - critical) / max_rate_dps
                + max_rate_dps / decel_dps2)
    peak_rate = math.sqrt(
        2.0 * distance_deg / (1.0 / accel_dps2 + 1.0 / decel_dps2))
    return peak_rate / accel_dps2 + peak_rate / decel_dps2


def parse_assignments(items, known):
    values = {}
    for item in items:
        try:
            name, raw = item.split("=", 1)
            value = float(raw)
        except ValueError as exc:
            raise ValueError(f"expected NAME=VALUE, got {item!r}") from exc
        if name not in known:
            raise ValueError(f"unknown parameter {name!r}")
        values[name] = value
    return values


def build_candidates(center, spans, names):
    """Pattern-search points: center and each coordinate at +/- current span."""
    candidates = [dict(center)]
    seen = {tuple(round(center[n], 9) for n in names)}
    for name in names:
        spec = PARAMETERS[name]
        for sign in (-1.0, 1.0):
            candidate = dict(center)
            candidate[name] = clamp(
                center[name] + sign * spans[name], spec.minimum, spec.maximum)
            key = tuple(round(candidate[n], 9) for n in names)
            if key not in seen:
                seen.add(key)
                candidates.append(candidate)
    return candidates


class WebApi:
    def __init__(self, base_url, timeout_s=5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _request(self, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        method = "GET" if body is None else "POST"
        request = urllib.request.Request(
            self.base_url + path, data=data, method=method,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            return json.load(response)

    def status(self):
        return self._request("/api/status")

    def set(self, values):
        return self._request("/api/set", values)

    def enable(self):
        return self._request("/api/enable", {})

    def stop(self):
        return self._request("/api/stop", {})


class IncrementalCsv:
    def __init__(self, path, fieldnames):
        self.path = path
        self.file = path.open("w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.file, fieldnames=fieldnames)
        self.writer.writeheader()
        self.file.flush()

    def write(self, row):
        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        self.file.close()


def apply_parameters(can_sock, api, values):
    web_values = {}
    for name, value in values.items():
        spec = PARAMETERS[name]
        if spec.config_index is not None:
            send_set_config(can_sock, spec.config_index, value)
            time.sleep(0.025)
        elif spec.web_field is not None:
            web_values[spec.web_field] = value
    # steer_rate_dps is clamped against the cap that was active before the
    # request, so update the commissioning cap first in a separate request.
    if "steer_commissioning_cap_rpm" in web_values:
        cap_result = api.set({
            "steer_commissioning_cap_rpm":
                web_values.pop("steer_commissioning_cap_rpm")})
        if not cap_result.get("ok"):
            raise RuntimeError(f"Web UI rejected commissioning cap: {cap_result}")
    if web_values:
        result = api.set(web_values)
        if not result.get("ok"):
            raise RuntimeError(f"Web UI rejected parameters: {result}")


def wait_for_wheel(api, target_rpm, timeout_s, tolerance_rpm):
    deadline = time.monotonic() + timeout_s
    latest = None
    while time.monotonic() < deadline:
        latest = api.status()
        if not latest.get("enabled"):
            raise RuntimeError(
                f"unit disabled during wheel ramp: {latest.get('last_stop_reason')}")
        actual = (latest.get("telemetry") or {}).get("wheel_rpm_actual")
        if actual is not None and abs(actual - target_rpm) <= tolerance_rpm:
            return latest
        time.sleep(0.04)
    raise RuntimeError(f"wheel failed to reach {target_rpm}rpm; last={latest}")


def high_speed_trace_metrics(rows, direction):
    """Extract braking lag and scaling duration from one fresh-sample trace.

    The actual deceleration start is represented by the directional-speed
    peak.  This remains measurable when the plant continues accelerating
    after the reference has begun braking, which is the high-rpm failure mode
    this telemetry is intended to expose.
    """
    speed_samples = [
        (row["t"], direction * row["steer_rpm"])
        for row in rows if row.get("steer_rpm") is not None
    ]
    if speed_samples:
        actual_peak_time_s, actual_peak_rpm = max(
            speed_samples, key=lambda item: item[1])
        actual_peak_rpm = max(0.0, actual_peak_rpm)
    else:
        actual_peak_time_s = math.nan
        actual_peak_rpm = math.nan

    reference_decel_start_s = math.nan
    previous_rate = None
    for row in rows:
        rate = row.get("profile_rate_dps")
        if rate is None:
            continue
        directional_rate = max(0.0, direction * rate)
        if (previous_rate is not None and previous_rate > 1.0 and
                directional_rate < previous_rate - 0.1):
            reference_decel_start_s = row["t"]
            break
        previous_rate = directional_rate
    brake_onset_lag_s = (
        actual_peak_time_s - reference_decel_start_s
        if math.isfinite(actual_peak_time_s) and
        math.isfinite(reference_decel_start_s) else math.nan)

    saturation_total_s = 0.0
    saturation_longest_s = 0.0
    saturation_run_s = 0.0
    for index in range(len(rows) - 1):
        dt_s = max(0.0, min(0.1, rows[index + 1]["t"] - rows[index]["t"]))
        if rows[index].get("torque_scaling_active"):
            saturation_total_s += dt_s
            saturation_run_s += dt_s
            saturation_longest_s = max(saturation_longest_s, saturation_run_s)
        else:
            saturation_run_s = 0.0

    return {
        "actual_steer_peak_rpm": actual_peak_rpm,
        "reference_decel_start_s": reference_decel_start_s,
        "actual_decel_start_s": actual_peak_time_s,
        "brake_onset_lag_s": brake_onset_lag_s,
        "steer_saturation_total_s": saturation_total_s,
        "steer_saturation_longest_s": saturation_longest_s,
    }


def first_directional_threshold_crossing(rows, direction, threshold):
    """Interpolate the first crossing of a directional error threshold.

    At 150 axis rpm the steer angle advances about 9 degrees between 100 Hz
    HTTP samples.  Looking only for a sample inside a +/-2 degree band can
    therefore miss the first pass completely and report the post-overshoot
    re-entry as the initial response.  The target approach starts with
    ``direction * destination_error`` negative, so a band entry is the
    crossing of ``-band`` and the target crossing is the crossing of zero.
    """
    previous = None
    for row in rows:
        error = row.get("destination_error")
        sample_time = row.get("t")
        if error is None or sample_time is None:
            continue
        directional_error = direction * error
        if directional_error >= threshold:
            if previous is not None:
                previous_time, previous_error = previous
                delta = directional_error - previous_error
                if previous_error < threshold and delta > 0.0:
                    fraction = (threshold - previous_error) / delta
                    fraction = max(0.0, min(1.0, fraction))
                    return previous_time + fraction * (sample_time - previous_time)
            return sample_time
        previous = (sample_time, directional_error)
    return None


def first_arrival_metrics(rows, direction, settle_time, settle_band_deg):
    """Keep fast arrival separate from overshoot recovery and final settling."""
    first_entry_2deg_s = first_directional_threshold_crossing(
        rows, direction, -2.0)
    first_entry_band_s = first_directional_threshold_crossing(
        rows, direction, -settle_band_deg)
    first_crossing_s = first_directional_threshold_crossing(
        rows, direction, 0.0)
    resettle_after_entry_2deg_s = (
        max(0.0, settle_time - first_entry_2deg_s)
        if settle_time is not None and first_entry_2deg_s is not None else None)
    return {
        "first_entry_2deg_s": first_entry_2deg_s,
        "first_entry_band_s": first_entry_band_s,
        "first_crossing_s": first_crossing_s,
        "resettle_after_entry_2deg_s": resettle_after_entry_2deg_s,
    }


def build_interleaved_schedule(candidate_count, repeats, wheel_rpms, rng):
    """Balance every candidate across direction while alternating every move.

    A block contains one move in each direction for every candidate and ends
    at its starting angle. Odd/even repeats use opposite adjacent 90-degree
    sectors so absolute-angle effects are shared across all candidates.
    """
    if candidate_count < 2:
        raise ValueError("interleaved comparison needs at least two candidates")
    schedule = []
    for repeat_number in range(1, repeats + 1):
        first_direction = 1 if repeat_number % 2 == 1 else -1
        for wheel_rpm in wheel_rpms:
            first_order = list(range(candidate_count))
            rng.shuffle(first_order)
            shift = rng.randrange(1, candidate_count)
            return_order = first_order[shift:] + first_order[:shift]
            for first_candidate, return_candidate in zip(
                    first_order, return_order):
                schedule.append((repeat_number, wheel_rpm,
                                 first_direction, first_candidate))
                schedule.append((repeat_number, wheel_rpm,
                                 -first_direction, return_candidate))
    return schedule


def run_move(api, direction, wheel_rpm, move_deg, timeout_s, poll_hz,
             settle_band_deg, settle_dwell_s, temp_limit_c):
    api.set({"wheel_rpm": wheel_rpm})
    state = wait_for_wheel(
        api, wheel_rpm, timeout_s=min(3.0, timeout_s),
        tolerance_rpm=max(12.0, abs(wheel_rpm) * 0.06))
    telemetry = state.get("telemetry") or {}
    physical_rate_dps = ((state.get("envelope") or {}).get(
        "steer_rate_avail_dps") or 0.0)
    if physical_rate_dps <= 0.0:
        raise RuntimeError("no steer-rate envelope available at requested wheel rpm")
    config = state.get("config") or {}
    requested_rate_dps = abs(config.get("steer_rate_dps") or physical_rate_dps)
    profile_rate_limit_dps = min(requested_rate_dps, physical_rate_dps)
    kinematic_lower_bound_s = steer_profile_min_time_s(
        move_deg, profile_rate_limit_dps,
        float(config.get("steer_accel_dps2") or 3600.0),
        float(config.get("steer_decel_dps2") or 2250.0))
    trajectory_time_scale = float(config.get("trajectory_time_scale") or 1.0)
    performance_deadline_s = max(
        2.0 * kinematic_lower_bound_s,
        trajectory_time_scale * kinematic_lower_bound_s + 0.35)
    start_deg = telemetry.get("angle_deg")
    if start_deg is None:
        raise RuntimeError("angle telemetry missing before steer move")
    destination_deg = (start_deg + direction * move_deg) % 360.0
    result = api.set({"steer_deg": destination_deg})
    if not result.get("ok"):
        raise RuntimeError(f"steer target rejected: {result}")

    start_time = time.monotonic()
    interval = 1.0 / poll_hz
    rows = []
    stable_since = None
    settle_time = None
    local_settle_time = None
    can_settle_time = None
    can_seen_unsettled = False
    can_flag_available = False
    profile_time = None
    safety_reason = ""
    last_telemetry_sequence = None
    while time.monotonic() - start_time < timeout_s:
        loop_start = time.monotonic()
        state = api.status()
        elapsed = time.monotonic() - start_time
        if not state.get("enabled"):
            safety_reason = str(state.get("last_stop_reason") or "disabled")
            break
        telemetry = state.get("telemetry") or {}
        temperatures = [value for value in (telemetry.get("t1"), telemetry.get("t2"))
                        if value is not None]
        if temperatures and max(temperatures) >= temp_limit_c:
            safety_reason = f"temperature limit {max(temperatures):.0f}C >= {temp_limit_c:.0f}C"
            break
        actual = telemetry.get("angle_deg")
        effective = state.get("effective_steer_deg")
        telemetry_sequence = telemetry.get("sequence")
        if (telemetry_sequence is not None and
                telemetry_sequence == last_telemetry_sequence):
            delay = interval - (time.monotonic() - loop_start)
            if delay > 0.0:
                time.sleep(delay)
            continue
        last_telemetry_sequence = telemetry_sequence
        if actual is not None and effective is not None:
            destination_error = angle_error(actual, destination_deg)
            effective_error = angle_error(effective, destination_deg)
            if profile_time is None and abs(effective_error) <= 0.5:
                profile_time = elapsed
            steer_rpm_actual = telemetry.get("steer_rpm_actual")
            wheel_actual = telemetry.get("wheel_rpm_actual")
            wheel_band_rpm = max(12.0, abs(wheel_rpm) * 0.06)
            locally_in_band = (
                abs(destination_error) <= settle_band_deg
                and steer_rpm_actual is not None
                and abs(steer_rpm_actual) <= 1.0
                and wheel_actual is not None
                and abs(wheel_actual - wheel_rpm) <= wheel_band_rpm)
            if profile_time is not None and locally_in_band:
                if stable_since is None:
                    stable_since = elapsed
                if elapsed - stable_since >= settle_dwell_s:
                    local_settle_time = stable_since
            else:
                stable_since = None
            motion_settled = telemetry.get("motion_settled")
            if motion_settled is not None:
                can_flag_available = True
                if motion_settled is False:
                    can_seen_unsettled = True
                elif can_seen_unsettled and can_settle_time is None:
                    # STATUS3 is authoritative and already includes the
                    # firmware's 100ms angle/rate/wheel dwell. Requiring a
                    # false sample first rejects the previous command's stale
                    # SETTLED flag during the first few milliseconds.
                    can_settle_time = elapsed
            rows.append({
                "t": elapsed,
                "sequence": telemetry_sequence,
                "destination_error": destination_error,
                "tracking_error": telemetry.get("err_deg"),
                "profile_rate_dps": state.get("profile_steer_rate_dps"),
                "profile_accel_dps2": state.get(
                    "profile_steer_accel_dps2"),
                "wheel": telemetry.get("wheel_rpm_actual"),
                "steer_rpm": telemetry.get("steer_rpm_actual"),
                "motion_settled": telemetry.get("motion_settled"),
                "observer_angle": telemetry.get("steer_observer_angle_deg"),
                "observer_rpm": telemetry.get("steer_observer_rpm"),
                "observer_innovation": telemetry.get(
                    "steer_observer_innovation_deg"),
                "schedule_rpm": telemetry.get("steer_schedule_rpm"),
                "scheduled_kp": telemetry.get("scheduled_steer_kp"),
                "scheduled_ki": telemetry.get("scheduled_steer_ki"),
                "scheduled_accel_ff": telemetry.get("scheduled_accel_ff_gain"),
                "scheduled_decel_ff": telemetry.get("scheduled_decel_ff_gain"),
                "scheduled_kaw": telemetry.get(
                    "scheduled_steer_backcalc_gain"),
                "steer_current_unsaturated": telemetry.get(
                    "steer_current_unsaturated"),
                "steer_current_applied": telemetry.get("steer_current_applied"),
                "steer_saturation_residual": telemetry.get(
                    "steer_saturation_residual"),
                "steer_saturation_duration_ms": telemetry.get(
                    "steer_saturation_duration_ms"),
                "steer_backcalc_correction": telemetry.get(
                    "steer_backcalc_correction"),
                "drive_backcalc_correction": telemetry.get(
                    "drive_backcalc_correction"),
                "torque_scaling_active": telemetry.get("torque_scaling_active"),
                "steer_braking_active": telemetry.get("steer_braking_active"),
                "steer_accel_explicit_active": telemetry.get(
                    "steer_accel_explicit_active"),
                "temp1": telemetry.get("t1"),
                "temp2": telemetry.get("t2"),
                "i1": telemetry.get("i1"),
                "i2": telemetry.get("i2"),
                "q1": telemetry.get("q1"),
                "q2": telemetry.get("q2"),
            })
        if can_settle_time is not None:
            break
        delay = interval - (time.monotonic() - loop_start)
        if delay > 0.0:
            time.sleep(delay)

    if not rows:
        raise RuntimeError("no telemetry samples collected during steer move")
    settle_time = can_settle_time if can_flag_available else local_settle_time
    profile_time = profile_time if profile_time is not None else timeout_s
    post_profile = [row for row in rows if row["t"] >= profile_time] or rows[-1:]
    signed_overshoots = [direction * row["destination_error"] for row in post_profile]
    tracking = [abs(row["tracking_error"]) for row in rows
                if row["tracking_error"] is not None]
    wheel_errors = [abs(row["wheel"] - wheel_rpm) for row in rows
                    if row["wheel"] is not None]
    temperatures = [value for row in rows for value in (row["temp1"], row["temp2"])
                    if value is not None]
    commanded_currents = [abs(value) for row in rows for value in (row["i1"], row["i2"])
                          if value is not None]
    measured_currents = [abs(value) for row in rows for value in (row["q1"], row["q2"])
                         if value is not None]
    high_speed_metrics = high_speed_trace_metrics(rows, direction)
    arrival_metrics = first_arrival_metrics(
        rows, direction, settle_time, settle_band_deg)
    return {
        "direction": direction,
        "wheel_rpm": wheel_rpm,
        "start_deg": start_deg,
        "destination_deg": destination_deg,
        "profile_s": profile_time,
        "settle_s": settle_time,
        "kinematic_lower_bound_s": kinematic_lower_bound_s,
        "performance_deadline_s": performance_deadline_s,
        "deadline_met": (
            settle_time is not None and settle_time <= performance_deadline_s),
        "response_ratio": (
            settle_time / kinematic_lower_bound_s
            if settle_time is not None else None),
        **arrival_metrics,
        "overshoot_deg": max(0.0, max(signed_overshoots)),
        "post_profile_peak_abs_deg": max(
            abs(row["destination_error"]) for row in post_profile),
        "terminal_abs_error_deg": abs(rows[-1]["destination_error"]),
        "max_tracking_error_deg": max(tracking) if tracking else math.nan,
        "wheel_mae_rpm": sum(wheel_errors) / len(wheel_errors) if wheel_errors else math.nan,
        "temp_max_c": max(temperatures) if temperatures else math.nan,
        "command_current_peak_raw": max(commanded_currents) if commanded_currents else math.nan,
        "measured_current_peak_raw": max(measured_currents) if measured_currents else math.nan,
        **high_speed_metrics,
        "safety_reason": safety_reason,
        "samples": len(rows),
    }, rows


def trial_score(metrics, timeout_s):
    if metrics["safety_reason"]:
        return 1000.0
    first_entry = metrics["first_entry_2deg_s"]
    arrival_cost = (4.0 * first_entry if first_entry is not None
                    else 4.0 * timeout_s + 10.0)
    wheel_mae = metrics["wheel_mae_rpm"]
    track = metrics["max_tracking_error_deg"]
    return (
        arrival_cost
        + 0.30 * metrics["overshoot_deg"]
        + 0.50 * metrics["terminal_abs_error_deg"]
        + 0.08 * (0.0 if math.isnan(track) else track)
        + 0.02 * (0.0 if math.isnan(wheel_mae) else wheel_mae)
    )


def candidate_score(scores):
    # Mean rewards general performance; the worst-case term prevents one very
    # good direction hiding a stick/oscillation in the opposite direction.
    return sum(scores) / len(scores) + 0.35 * max(scores)


def summarize_candidate(round_number, candidate_number, candidate,
                        metrics_list, scores):
    settled = [m["settle_s"] for m in metrics_list
               if m["settle_s"] is not None]
    response_ratios = [m["response_ratio"] for m in metrics_list
                       if m["response_ratio"] is not None]
    first_entries = [m["first_entry_2deg_s"] for m in metrics_list
                     if m["first_entry_2deg_s"] is not None]
    resettle_delays = [m["resettle_after_entry_2deg_s"] for m in metrics_list
                       if m["resettle_after_entry_2deg_s"] is not None]
    strict_acceptance_failures = (0 if metrics_list else 1) + sum(
        bool(m["safety_reason"])
        or m["settle_s"] is None
        or m["settle_s"] > STRICT_ACCEPT_WORST_SETTLE_S
        or not math.isfinite(m["overshoot_deg"])
        or m["overshoot_deg"] > STRICT_ACCEPT_OVERSHOOT_DEG
        for m in metrics_list)
    acceptance_failures = (0 if metrics_list else 1) + sum(
        bool(m["safety_reason"])
        or m["first_entry_2deg_s"] is None
        or m["first_entry_2deg_s"] > ACCEPT_FIRST_ENTRY_2DEG_S
        or not math.isfinite(m["overshoot_deg"])
        or m["overshoot_deg"] > ACCEPT_OVERSHOOT_DEG
        or not math.isfinite(m["terminal_abs_error_deg"])
        or m["terminal_abs_error_deg"] > ACCEPT_TERMINAL_ERROR_DEG
        for m in metrics_list)
    return {
        "round": round_number,
        "candidate": candidate_number,
        **candidate,
        "score": candidate_score(scores) if scores else 1000.0,
        "mean_first_entry_2deg_s": (
            sum(first_entries) / len(first_entries) if first_entries else ""),
        "worst_first_entry_2deg_s": max(first_entries) if first_entries else "",
        "mean_resettle_after_entry_2deg_s": (
            sum(resettle_delays) / len(resettle_delays)
            if resettle_delays else ""),
        "worst_resettle_after_entry_2deg_s": (
            max(resettle_delays) if resettle_delays else ""),
        "mean_settle_s": sum(settled) / len(settled) if settled else "",
        "worst_settle_s": max(settled) if settled else "",
        "mean_response_ratio": (
            sum(response_ratios) / len(response_ratios)
            if response_ratios else ""),
        "worst_response_ratio": max(response_ratios) if response_ratios else "",
        "worst_overshoot_deg": max(
            (m["overshoot_deg"] for m in metrics_list), default=""),
        "worst_terminal_abs_error_deg": max(
            (m["terminal_abs_error_deg"] for m in metrics_list), default=""),
        "temp_max_c": max(
            (m["temp_max_c"] for m in metrics_list
             if not math.isnan(m["temp_max_c"])), default=""),
        "command_current_peak_raw": max(
            (m["command_current_peak_raw"] for m in metrics_list
             if not math.isnan(m["command_current_peak_raw"])), default=""),
        "measured_current_peak_raw": max(
            (m["measured_current_peak_raw"] for m in metrics_list
             if not math.isnan(m["measured_current_peak_raw"])), default=""),
        "actual_steer_peak_rpm": max(
            (m["actual_steer_peak_rpm"] for m in metrics_list
             if not math.isnan(m["actual_steer_peak_rpm"])), default=""),
        "worst_brake_onset_lag_s": max(
            (m["brake_onset_lag_s"] for m in metrics_list
             if not math.isnan(m["brake_onset_lag_s"])), default=""),
        "steer_saturation_total_s": sum(
            m["steer_saturation_total_s"] for m in metrics_list
            if not math.isnan(m["steer_saturation_total_s"])),
        "worst_steer_saturation_s": max(
            (m["steer_saturation_longest_s"] for m in metrics_list
             if not math.isnan(m["steer_saturation_longest_s"])), default=""),
        "failed_trials": sum(
            m["settle_s"] is None or not m.get("deadline_met", False)
            or bool(m["safety_reason"])
            for m in metrics_list),
        "acceptance_failures": acceptance_failures,
        "acceptance_pass": acceptance_failures == 0,
        "strict_settle_failures": strict_acceptance_failures,
        "strict_settle_pass": strict_acceptance_failures == 0,
    }


def failed_trial(direction, wheel_rpm, reason):
    """Metric-shaped record so one invalid candidate cannot kill a sweep."""
    return {
        "direction": direction,
        "wheel_rpm": wheel_rpm,
        "start_deg": math.nan,
        "destination_deg": math.nan,
        "profile_s": math.nan,
        "settle_s": None,
        "kinematic_lower_bound_s": math.nan,
        "performance_deadline_s": math.nan,
        "deadline_met": False,
        "response_ratio": None,
        "first_entry_2deg_s": None,
        "first_entry_band_s": None,
        "first_crossing_s": None,
        "resettle_after_entry_2deg_s": None,
        "overshoot_deg": math.nan,
        "post_profile_peak_abs_deg": math.nan,
        "terminal_abs_error_deg": math.nan,
        "max_tracking_error_deg": math.nan,
        "wheel_mae_rpm": math.nan,
        "temp_max_c": math.nan,
        "command_current_peak_raw": math.nan,
        "measured_current_peak_raw": math.nan,
        "actual_steer_peak_rpm": math.nan,
        "reference_decel_start_s": math.nan,
        "actual_decel_start_s": math.nan,
        "brake_onset_lag_s": math.nan,
        "steer_saturation_total_s": math.nan,
        "steer_saturation_longest_s": math.nan,
        "safety_reason": reason,
        "samples": 0,
    }


def svg_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_svg(path, summaries, parameter_names, best):
    width = 1100
    panel_w = 320
    panel_h = 230
    columns = 3
    rows_count = math.ceil(len(parameter_names) / columns)
    height = 120 + rows_count * 285
    colors = ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fafafa"/>',
        '<style>text{font-family:system-ui,sans-serif;fill:#172033}.axis{stroke:#64748b;stroke-width:1}.grid{stroke:#e2e8f0;stroke-width:1}.pt{opacity:.78}</style>',
        '<text x="40" y="38" font-size="24" font-weight="700">Differential Swerve Auto Tune</text>',
        f'<text x="40" y="66" font-size="14">best score={best["score"]:.3f} | ' +
        svg_escape(", ".join(f"{n}={best[n]:.4g}" for n in parameter_names)) + '</text>',
        '<text x="40" y="88" font-size="12">Lower score is better. Color indicates coarse-to-fine round.</text>',
    ]
    finite_scores = [row["score"] for row in summaries if math.isfinite(row["score"])]
    y_min = min(finite_scores) if finite_scores else 0.0
    y_max = max(finite_scores) if finite_scores else 1.0
    if y_max <= y_min:
        y_max = y_min + 1.0
    for index, name in enumerate(parameter_names):
        col = index % columns
        row_index = index // columns
        x0 = 55 + col * 350
        y0 = 125 + row_index * 285
        values = [row[name] for row in summaries]
        x_min, x_max = min(values), max(values)
        if x_max <= x_min:
            x_max = x_min + 1.0
        parts += [
            f'<text x="{x0}" y="{y0 - 12}" font-size="16" font-weight="600">{svg_escape(name)}</text>',
            f'<line class="axis" x1="{x0}" y1="{y0 + panel_h}" x2="{x0 + panel_w}" y2="{y0 + panel_h}"/>',
            f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + panel_h}"/>',
        ]
        for tick in range(5):
            yy = y0 + panel_h * tick / 4
            score_label = y_max - (y_max - y_min) * tick / 4
            parts.append(f'<line class="grid" x1="{x0}" y1="{yy:.1f}" x2="{x0 + panel_w}" y2="{yy:.1f}"/>')
            parts.append(f'<text x="{x0 - 8}" y="{yy + 4:.1f}" font-size="10" text-anchor="end">{score_label:.2f}</text>')
        for item in summaries:
            px = x0 + panel_w * (item[name] - x_min) / (x_max - x_min)
            py = y0 + panel_h * (y_max - item["score"]) / (y_max - y_min)
            color = colors[(int(item["round"]) - 1) % len(colors)]
            parts.append(f'<circle class="pt" cx="{px:.2f}" cy="{py:.2f}" r="5" fill="{color}"><title>round {item["round"]}, score {item["score"]:.3f}</title></circle>')
        parts.append(f'<text x="{x0}" y="{y0 + panel_h + 22}" font-size="10">{x_min:.4g}</text>')
        parts.append(f'<text x="{x0 + panel_w}" y="{y0 + panel_h + 22}" font-size="10" text-anchor="end">{x_max:.4g}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", default="steer_kp,steer_rate_dps,steer_accel_dps2",
                        help="comma-separated search parameters: " + ",".join(PARAMETERS))
    parser.add_argument("--center", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--span", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--fixed", action="append", default=[], metavar="NAME=VALUE",
                        help="hold an unsearched parameter at this value")
    parser.add_argument(
        "--compare-values", default=None, metavar="V1,V2,...",
        help="interleave explicit values for exactly one --params name; "
             "each value gets both directions at wheel=0/--wheel-rpm")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--shrink", type=float, default=0.5)
    parser.add_argument("--wheel-rpm", type=float, default=265.0)
    parser.add_argument("--move-deg", type=float, default=90.0)
    parser.add_argument("--trial-timeout", type=float, default=3.0)
    parser.add_argument("--poll-hz", type=float, default=100.0)
    parser.add_argument("--settle-band-deg", type=float, default=0.5)
    parser.add_argument("--settle-dwell", type=float, default=0.5)
    parser.add_argument("--temp-limit-c", type=float, default=55.0)
    parser.add_argument("--wheel-accel", type=float, default=500.0)
    parser.add_argument("--wheel-decel", type=float, default=500.0)
    parser.add_argument("--trajectory-time-scale", type=float, default=1.0,
                        help="reference time dilation; 1 for gain test, 2 for production acceptance")
    parser.add_argument("--full-scenarios", action="store_true",
                        help="test +/- moves at both wheel=0 and --wheel-rpm (4 moves/candidate)")
    parser.add_argument("--repeats", type=int, default=1,
                        help="repeat the complete scenario set per candidate")
    parser.add_argument("--seed", type=int, default=20260731)
    parser.add_argument("--web-url", default="http://127.0.0.1:8080")
    parser.add_argument("--can-iface", default="can0")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULT_DIR)
    parser.add_argument("--apply-best", action="store_true",
                        help="leave best parameters applied; default restores starting center")
    parser.add_argument("--evaluate-only", action="store_true",
                        help="run only the center point (useful for regression after flashing)")
    parser.add_argument("--yes-wheel-lifted", action="store_true",
                        help="required acknowledgement before hardware motion")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    names = [name.strip() for name in args.params.split(",") if name.strip()]
    if not names or len(set(names)) != len(names):
        parser.error("--params must contain unique parameter names")
    unknown = [name for name in names if name not in PARAMETERS]
    if unknown:
        parser.error(f"unknown --params: {','.join(unknown)}")
    if args.rounds < 1 or args.repeats < 1 or not (0.0 < args.shrink < 1.0):
        parser.error("--rounds/--repeats must be >=1 and 0 < --shrink < 1")
    if args.evaluate_only:
        # Repetition belongs to --repeats. Running the same center once per
        # search round caused the default --rounds 3 to triple regression
        # motion unexpectedly.
        args.rounds = 1
    if not (1.0 <= args.trajectory_time_scale <= 4.0):
        parser.error("--trajectory-time-scale must be in [1,4]")

    center_overrides = parse_assignments(args.center, PARAMETERS)
    span_overrides = parse_assignments(args.span, PARAMETERS)
    fixed_values = parse_assignments(args.fixed, PARAMETERS)
    overlap = sorted(set(fixed_values) & set(names))
    if overlap:
        parser.error(f"parameters cannot be both searched and --fixed: {','.join(overlap)}")
    center = {name: center_overrides.get(name, PARAMETERS[name].default) for name in names}
    spans = {name: span_overrides.get(name, PARAMETERS[name].span) for name in names}
    for name in names:
        spec = PARAMETERS[name]
        center[name] = clamp(center[name], spec.minimum, spec.maximum)
        if spans[name] <= 0.0:
            parser.error(f"span must be positive: {name}={spans[name]}")

    compare_candidates = None
    if args.compare_values is not None:
        if len(names) != 1:
            parser.error("--compare-values requires exactly one --params name")
        try:
            compare_values = [float(raw.strip())
                              for raw in args.compare_values.split(",")
                              if raw.strip()]
        except ValueError as exc:
            parser.error(f"invalid --compare-values: {exc}")
        spec = PARAMETERS[names[0]]
        compare_values = [clamp(value, spec.minimum, spec.maximum)
                          for value in compare_values]
        if len(compare_values) < 2 or len(set(compare_values)) != len(compare_values):
            parser.error("--compare-values needs at least two unique values")
        compare_candidates = [{names[0]: value} for value in compare_values]

    if args.self_check:
        candidates = build_candidates(center, spans, names)
        expected_max = 1 + 2 * len(names)
        assert 1 <= len(candidates) <= expected_max
        assert all(PARAMETERS[n].minimum <= c[n] <= PARAMETERS[n].maximum
                   for c in candidates for n in names)
        trace_metrics = high_speed_trace_metrics([
            {"t": 0.00, "profile_rate_dps": 60.0, "steer_rpm": 5.0,
             "torque_scaling_active": 0},
            {"t": 0.01, "profile_rate_dps": 120.0, "steer_rpm": 10.0,
             "torque_scaling_active": 1},
            {"t": 0.02, "profile_rate_dps": 100.0, "steer_rpm": 12.0,
             "torque_scaling_active": 1},
            {"t": 0.03, "profile_rate_dps": 80.0, "steer_rpm": 11.0,
             "torque_scaling_active": 0},
        ], direction=1)
        assert abs(trace_metrics["actual_steer_peak_rpm"] - 12.0) < 1e-9
        assert abs(trace_metrics["reference_decel_start_s"] - 0.02) < 1e-9
        assert abs(trace_metrics["brake_onset_lag_s"]) < 1e-9
        assert abs(trace_metrics["steer_saturation_total_s"] - 0.02) < 1e-9
        assert abs(trace_metrics["steer_saturation_longest_s"] - 0.02) < 1e-9
        arrival = first_arrival_metrics([
            {"t": 0.10, "destination_error": -8.0},
            {"t": 0.20, "destination_error": -1.5},
            {"t": 0.30, "destination_error": -0.4},
            {"t": 0.40, "destination_error": 0.2},
        ], direction=1, settle_time=0.55, settle_band_deg=0.5)
        assert abs(arrival["first_entry_2deg_s"] - 0.19230769230769232) < 1e-9
        assert abs(arrival["first_entry_band_s"] - 0.2909090909090909) < 1e-9
        assert abs(arrival["first_crossing_s"] - 0.3666666666666667) < 1e-9
        assert abs(arrival["resettle_after_entry_2deg_s"] -
                   0.3576923076923077) < 1e-9
        for direction, errors in ((1, (-8.0, 4.0)), (-1, (8.0, -4.0))):
            skipped_band = first_arrival_metrics([
                {"t": 0.10, "destination_error": errors[0]},
                {"t": 0.11, "destination_error": errors[1]},
            ], direction=direction, settle_time=0.30, settle_band_deg=0.5)
            assert abs(skipped_band["first_entry_2deg_s"] - 0.105) < 1e-9
            assert abs(skipped_band["first_crossing_s"] -
                       0.10666666666666667) < 1e-9
        schedule = build_interleaved_schedule(
            3, 2, [0.0, 265.0], random.Random(1234))
        assert len(schedule) == 24
        for repeat_number in (1, 2):
            expected_direction = 1 if repeat_number == 1 else -1
            for wheel_rpm in (0.0, 265.0):
                block = [item for item in schedule
                         if item[0] == repeat_number and item[1] == wheel_rpm]
                assert all(item[2] == (expected_direction
                                       if index % 2 == 0 else -expected_direction)
                           for index, item in enumerate(block))
                for direction in (-1, 1):
                    assert sorted(item[3] for item in block
                                  if item[2] == direction) == [0, 1, 2]
        print(f"SELF_CHECK PASS parameters={len(names)} candidates={len(candidates)}")
        return 0
    if not args.yes_wheel_lifted:
        parser.error("hardware motion refused: pass --yes-wheel-lifted")

    api = WebApi(args.web_url)
    initial = api.status()
    if initial.get("enabled"):
        parser.error("unit is already enabled; STOP it before auto tuning")
    initial_config = initial.get("config") or {}
    initial_time_scale = initial_config.get(
        "trajectory_time_scale", args.trajectory_time_scale)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    result_dir = args.output_dir / stamp
    result_dir.mkdir(parents=True, exist_ok=False)
    trial_fields = [
        "round", "candidate", *names, "repeat", "direction", "wheel_rpm", "start_deg",
        "destination_deg", "profile_s", "settle_s", "kinematic_lower_bound_s",
        "performance_deadline_s", "deadline_met", "response_ratio",
        "first_entry_2deg_s", "first_entry_band_s", "first_crossing_s",
        "resettle_after_entry_2deg_s", "overshoot_deg",
        "post_profile_peak_abs_deg", "terminal_abs_error_deg",
        "max_tracking_error_deg", "wheel_mae_rpm", "temp_max_c",
        "command_current_peak_raw", "measured_current_peak_raw",
        "actual_steer_peak_rpm", "reference_decel_start_s",
        "actual_decel_start_s", "brake_onset_lag_s",
        "steer_saturation_total_s", "steer_saturation_longest_s",
        "safety_reason", "samples", "trial_score",
    ]
    summary_fields = [
        "round", "candidate", *names, "score", "mean_settle_s",
        "worst_settle_s", "mean_first_entry_2deg_s", "worst_first_entry_2deg_s",
        "mean_resettle_after_entry_2deg_s", "worst_resettle_after_entry_2deg_s",
        "mean_response_ratio", "worst_response_ratio",
        "worst_overshoot_deg", "worst_terminal_abs_error_deg",
        "temp_max_c", "command_current_peak_raw", "measured_current_peak_raw",
        "actual_steer_peak_rpm", "worst_brake_onset_lag_s",
        "steer_saturation_total_s", "worst_steer_saturation_s",
        "failed_trials", "acceptance_failures", "acceptance_pass",
        "strict_settle_failures", "strict_settle_pass",
    ]
    trials_csv = IncrementalCsv(result_dir / "trials.csv", trial_fields)
    summary_csv = IncrementalCsv(result_dir / "summary.csv", summary_fields)
    sample_fields = [
        "round", "candidate", "repeat", "direction", "wheel_rpm",
        "t", "sequence", "destination_error", "tracking_error",
        "profile_rate_dps", "profile_accel_dps2", "wheel", "steer_rpm",
        "motion_settled",
        "observer_angle", "observer_rpm", "observer_innovation",
        "schedule_rpm", "scheduled_kp", "scheduled_ki",
        "scheduled_accel_ff", "scheduled_decel_ff", "scheduled_kaw",
        "steer_current_unsaturated", "steer_current_applied",
        "steer_saturation_residual", "steer_saturation_duration_ms",
        "steer_backcalc_correction", "drive_backcalc_correction",
        "torque_scaling_active", "steer_braking_active",
        "steer_accel_explicit_active",
        "temp1", "temp2", "i1", "i2",
        "q1", "q2",
    ]
    samples_csv = IncrementalCsv(result_dir / "samples.csv", sample_fields)
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "arguments": vars(args) | {"output_dir": str(args.output_dir)},
        "starting_center": center,
        "starting_spans": spans,
        "score_formula": (
            "mean(trial_score)+0.35*max(trial_score); trial score uses "
            "first-entry/overshoot/terminal-error, not strict settle"),
        "acceptance_gate": (
            f"all trials first-entry-2deg<={ACCEPT_FIRST_ENTRY_2DEG_S}s, "
            f"overshoot<={ACCEPT_OVERSHOOT_DEG}deg, terminal-error<="
            f"{ACCEPT_TERMINAL_ERROR_DEG}deg, and no safety reason"),
        "strict_diagnostic_gate": (
            f"all trials overshoot<={STRICT_ACCEPT_OVERSHOOT_DEG}deg and "
            f"settle<={STRICT_ACCEPT_WORST_SETTLE_S}s"),
    }
    (result_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    can_sock = open_can_socket(args.can_iface)
    send_set_config(can_sock, 22, TUNER_STATUS_PERIOD_MS)
    time.sleep(0.05)
    cleanup_needed = True

    def emergency_cleanup():
        if cleanup_needed:
            emergency_disable(args.can_iface)

    atexit.register(emergency_cleanup)
    summaries = []
    best = None
    final_apply_values = None
    rng = random.Random(args.seed)
    starting_center = dict(center)
    # A search over a subset must still be reproducible. Do not inherit stale
    # runtime values from a prior manual Web UI test for unsearched controls.
    baseline_values = {name: spec.default for name, spec in PARAMETERS.items()}
    for name, value in fixed_values.items():
        spec = PARAMETERS[name]
        baseline_values[name] = clamp(value, spec.minimum, spec.maximum)
    try:
        api.set({
            "wheel_rpm": 0.0,
            "steer_rate_dps": 0.0,
            "wheel_accel_rpm_per_s": args.wheel_accel,
            "wheel_decel_rpm_per_s": args.wheel_decel,
            # Gain-performance deadline is measured against an undilated
            # minimum-time reference. Production/GUI operation restores x2.
            "trajectory_time_scale": args.trajectory_time_scale,
        })
        if compare_candidates is not None:
            # Establish every non-compared parameter once. Between matched
            # moves only the explicitly compared value is changed.
            comparison_baseline = dict(baseline_values)
            comparison_baseline.update(starting_center)

            per_candidate = [
                {"metrics": [], "scores": []}
                for _ in compare_candidates
            ]
            schedule = build_interleaved_schedule(
                len(compare_candidates), args.repeats,
                [0.0, args.wheel_rpm], rng)
            aborted = False
            try:
                for move_number, (repeat_number, wheel_rpm, direction,
                                  candidate_index) in enumerate(schedule, 1):
                    candidate = compare_candidates[candidate_index]
                    full_candidate = dict(comparison_baseline)
                    full_candidate.update(candidate)
                    enabled_for_move = False
                    try:
                        # STOP after every scored move resets PI/observer state,
                        # preventing one Kaw candidate's integral from leaking
                        # into the next candidate. STOP also zeros profile rate,
                        # so the complete test condition is reapplied here.
                        apply_parameters(can_sock, api, full_candidate)
                        api.set({"wheel_rpm": 0.0})
                        api.status()
                        api.enable()
                        enabled_for_move = True
                        metrics, trace = run_move(
                            api, direction, wheel_rpm, args.move_deg,
                            args.trial_timeout, args.poll_hz,
                            args.settle_band_deg, args.settle_dwell,
                            args.temp_limit_c)
                    except Exception as exc:
                        metrics = failed_trial(
                            direction, wheel_rpm, f"trial error: {exc}")
                        trace = []
                    finally:
                        if enabled_for_move:
                            api.stop()
                    candidate_number = candidate_index + 1
                    for sample in trace:
                        samples_csv.write({
                            "round": 1,
                            "candidate": candidate_number,
                            "repeat": repeat_number,
                            "direction": direction,
                            "wheel_rpm": wheel_rpm,
                            **sample,
                        })
                    score = trial_score(metrics, args.trial_timeout)
                    per_candidate[candidate_index]["metrics"].append(metrics)
                    per_candidate[candidate_index]["scores"].append(score)
                    trials_csv.write({
                        "round": 1,
                        "candidate": candidate_number,
                        **candidate,
                        "repeat": repeat_number,
                        **metrics,
                        "trial_score": score,
                    })
                    print(
                        f"  move {move_number}/{len(schedule)} "
                        f"candidate={candidate_number} values={candidate} "
                        f"wheel={wheel_rpm:.0f} dir={direction:+d} "
                        f"entry2={metrics.get('first_entry_2deg_s')} "
                        f"settle={metrics.get('settle_s')} "
                        f"overshoot={metrics.get('overshoot_deg')}")
                    if metrics["safety_reason"]:
                        aborted = True
                        break
            finally:
                try:
                    if api.status().get("enabled"):
                        api.stop()
                except (OSError, urllib.error.URLError, socket.timeout):
                    emergency_disable(args.can_iface)

            round_rows = []
            for candidate_index, candidate in enumerate(compare_candidates):
                data = per_candidate[candidate_index]
                summary = summarize_candidate(
                    1, candidate_index + 1, candidate,
                    data["metrics"], data["scores"])
                summaries.append(summary)
                round_rows.append(summary)
                summary_csv.write(summary)
                print(
                    f"  summary candidate={candidate_index + 1} "
                    f"values={candidate} "
                    f"entry2={summary['mean_first_entry_2deg_s']} "
                    f"settle={summary['mean_settle_s']} "
                    f"overshoot={summary['worst_overshoot_deg']} "
                    f"accept={summary['acceptance_pass']}")

            passing = [row for row in round_rows if row["acceptance_pass"]]
            selection_pool = passing if passing else round_rows
            if passing:
                best = min(
                    selection_pool,
                    key=lambda row: row["mean_first_entry_2deg_s"])
            else:
                best = min(selection_pool, key=lambda row: row["score"])
            write_svg(result_dir / "score.svg", summaries, names, best)
            best_values = {name: float(best[name]) for name in names}
            final_full_values = dict(baseline_values)
            if args.apply_best and passing and not aborted:
                final_full_values.update(best_values)
            else:
                final_full_values.update(starting_center)
            final_apply_values = final_full_values
            metadata["completed_utc"] = datetime.now(timezone.utc).isoformat()
            metadata["best"] = best_values | {"score": best["score"]}
            metadata["accepted"] = bool(passing) and not aborted
            metadata["left_applied"] = (
                best_values if args.apply_best and passing and not aborted
                else starting_center)
            (result_dir / "metadata.json").write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding="utf-8")
            print(
                f"BEST score={best['score']:.3f} values={best_values} "
                f"accepted={bool(passing) and not aborted}")
            print(f"results: {result_dir}")
            return 0

        for round_number in range(1, args.rounds + 1):
            candidates = ([dict(center)] if args.evaluate_only
                          else build_candidates(center, spans, names))
            # Center first establishes a local baseline; randomize the rest to
            # reduce monotonic temperature/time bias across parameter values.
            tail = candidates[1:]
            rng.shuffle(tail)
            candidates = candidates[:1] + tail
            round_rows = []
            print(f"round {round_number}/{args.rounds}: center={center} spans={spans} candidates={len(candidates)}")
            for candidate_number, candidate in enumerate(candidates, 1):
                full_candidate = dict(baseline_values)
                full_candidate.update(candidate)
                apply_parameters(can_sock, api, full_candidate)
                # Do not overwrite steer_rate_dps here: it may itself be a
                # searched parameter. Enable seeds steer_deg to the measured
                # angle, so a non-zero profile rate cannot cause an angle jump.
                api.set({"wheel_rpm": 0.0})
                api.status()
                api.enable()
                if args.full_scenarios:
                    base_scenarios = [(0.0, 1), (0.0, -1), (args.wheel_rpm, 1),
                                      (args.wheel_rpm, -1)]
                else:
                    base_scenarios = [(0.0, 1), (args.wheel_rpm, -1)]
                scenarios = []
                for repeat_number in range(1, args.repeats + 1):
                    ordered = (base_scenarios if repeat_number % 2 == 1
                               else list(reversed(base_scenarios)))
                    scenarios.extend((repeat_number, wheel, direction)
                                     for wheel, direction in ordered)
                metrics_list = []
                scores = []
                try:
                    for repeat_number, wheel_rpm, direction in scenarios:
                        try:
                            metrics, trace = run_move(
                                api, direction, wheel_rpm, args.move_deg,
                                args.trial_timeout, args.poll_hz,
                                args.settle_band_deg, args.settle_dwell,
                                args.temp_limit_c)
                        except Exception as exc:
                            metrics = failed_trial(
                                direction, wheel_rpm, f"trial error: {exc}")
                            trace = []
                        for sample in trace:
                            samples_csv.write({
                                "round": round_number,
                                "candidate": candidate_number,
                                "repeat": repeat_number,
                                "direction": direction,
                                "wheel_rpm": wheel_rpm,
                                **sample,
                            })
                        score = trial_score(metrics, args.trial_timeout)
                        metrics_list.append(metrics)
                        scores.append(score)
                        row = {"round": round_number, "candidate": candidate_number,
                               **candidate, "repeat": repeat_number,
                               **metrics, "trial_score": score}
                        trials_csv.write(row)
                        if metrics["safety_reason"]:
                            break
                finally:
                    api.stop()
                summary = summarize_candidate(
                    round_number, candidate_number, candidate,
                    metrics_list, scores)
                score = summary["score"]
                summaries.append(summary)
                round_rows.append(summary)
                summary_csv.write(summary)
                print(f"  candidate {candidate_number}/{len(candidates)} score={score:.3f} values={candidate}")
                if any(str(m["safety_reason"]).startswith("temperature limit")
                       for m in metrics_list):
                    raise RuntimeError("temperature limit reached; aborting sweep")
            round_best = min(round_rows, key=lambda row: row["score"])
            center = {name: float(round_best[name]) for name in names}
            spans = {name: span * args.shrink for name, span in spans.items()}
            best = round_best if best is None or round_best["score"] < best["score"] else best
            write_svg(result_dir / "score.svg", summaries, names, best)

        final_values = {name: float(best[name]) for name in names}
        final_full_values = dict(baseline_values)
        final_full_values.update(final_values if args.apply_best else starting_center)
        # Apply only after the final STOP in the finally block. STOP
        # intentionally zeros steer_rate_dps, so applying before it would make
        # --apply-best silently lose the best Web-profile parameters.
        final_apply_values = final_full_values
        metadata["completed_utc"] = datetime.now(timezone.utc).isoformat()
        metadata["best"] = final_values | {"score": best["score"]}
        metadata["left_applied"] = final_values if args.apply_best else starting_center
        (result_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"BEST score={best['score']:.3f} values={final_values}")
        print(f"results: {result_dir}")
        return 0
    finally:
        try:
            api.stop()
        except (OSError, urllib.error.URLError, socket.timeout):
            emergency_disable(args.can_iface)
        if final_apply_values is not None:
            apply_parameters(can_sock, api, final_apply_values)
        try:
            # Restore the operator's starting Web UI state.  The historical
            # hard-coded 2.0 here silently undid the adopted 1.0 default after
            # every tuning run.
            api.set({"trajectory_time_scale": initial_time_scale})
        except (OSError, urllib.error.URLError, socket.timeout):
            pass
        send_set_config(can_sock, 22, 0.0)
        cleanup_needed = False
        can_sock.close()
        trials_csv.close()
        summary_csv.close()
        samples_csv.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrupted; unit stop requested", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
