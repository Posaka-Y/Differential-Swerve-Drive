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
    "steer_kp": Parameter("steer_kp", 10.0, 160.0, 120.0, 40.0, config_index=3),
    "steer_ki": Parameter("steer_ki", 0.0, 100.0, 50.0, 20.0, config_index=4),
    "angle_kp": Parameter("angle_kp", 0.5, 10.0, 4.0, 1.0, config_index=5),
    "moving_angle_kp": Parameter(
        "moving_angle_kp", 0.0, 4.0, 1.0, 0.5, config_index=19),
    "steer_min_rpm": Parameter(
        "steer_min_rpm", 0.0, 5.0, 0.0, 1.0, config_index=8),
    "steer_max_rpm": Parameter(
        "steer_max_rpm", 40.0, 60.0, 40.0, 10.0, config_index=7),
    "angle_deadband_deg": Parameter(
        "angle_deadband_deg", 0.1, 1.0, 0.3, 0.3, config_index=6),
    "mode_filter_tau_s": Parameter(
        "mode_filter_tau_s", 0.0, 0.05, 0.002, 0.005, config_index=13),
    "current_limit": Parameter(
        "current_limit", 2000.0, 6000.0, 4000.0, 1000.0, config_index=12),
    "steer_rate_dps": Parameter(
        "steer_rate_dps", 60.0, 240.0, 240.0, 60.0,
        web_field="steer_rate_dps"),
    "steer_accel_dps2": Parameter(
        "steer_accel_dps2", 180.0, 3600.0, 3600.0, 720.0,
        web_field="steer_accel_dps2"),
    "steer_decel_dps2": Parameter(
        "steer_decel_dps2", 180.0, 3600.0, 2250.0, 450.0,
        web_field="steer_decel_dps2"),
    "steer_accel_ff_gain": Parameter(
        "steer_accel_ff_gain", 0.0, 10.0, 0.5, 0.5, config_index=18),
    "steer_decel_ff_gain": Parameter(
        "steer_decel_ff_gain", 0.0, 10.0, 0.5, 0.5, config_index=20),
    "steer_friction_ff_current": Parameter(
        "steer_friction_ff_current", 0.0, 1000.0, 0.0, 200.0,
        config_index=21),
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
                "wheel": telemetry.get("wheel_rpm_actual"),
                "steer_rpm": telemetry.get("steer_rpm_actual"),
                "motion_settled": telemetry.get("motion_settled"),
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
        "overshoot_deg": max(0.0, max(signed_overshoots)),
        "post_profile_peak_abs_deg": max(
            abs(row["destination_error"]) for row in post_profile),
        "terminal_abs_error_deg": abs(rows[-1]["destination_error"]),
        "max_tracking_error_deg": max(tracking) if tracking else math.nan,
        "wheel_mae_rpm": sum(wheel_errors) / len(wheel_errors) if wheel_errors else math.nan,
        "temp_max_c": max(temperatures) if temperatures else math.nan,
        "command_current_peak_raw": max(commanded_currents) if commanded_currents else math.nan,
        "measured_current_peak_raw": max(measured_currents) if measured_currents else math.nan,
        "safety_reason": safety_reason,
        "samples": len(rows),
    }, rows


def trial_score(metrics, timeout_s):
    if metrics["safety_reason"]:
        return 1000.0
    settle = metrics["settle_s"]
    lower_bound = metrics["kinematic_lower_bound_s"]
    if settle is None:
        settle_cost = (
            timeout_s + 5.0 + 2.0 * metrics["terminal_abs_error_deg"]
        ) / lower_bound
    else:
        settle_cost = settle / lower_bound
        if not metrics.get("deadline_met", False):
            settle_cost += 5.0
    wheel_mae = metrics["wheel_mae_rpm"]
    track = metrics["max_tracking_error_deg"]
    return (
        settle_cost
        + 0.30 * metrics["overshoot_deg"]
        + 0.08 * (0.0 if math.isnan(track) else track)
        + 0.02 * (0.0 if math.isnan(wheel_mae) else wheel_mae)
    )


def candidate_score(scores):
    # Mean rewards general performance; the worst-case term prevents one very
    # good direction hiding a stick/oscillation in the opposite direction.
    return sum(scores) / len(scores) + 0.35 * max(scores)


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
        "overshoot_deg": math.nan,
        "post_profile_peak_abs_deg": math.nan,
        "terminal_abs_error_deg": math.nan,
        "max_tracking_error_deg": math.nan,
        "wheel_mae_rpm": math.nan,
        "temp_max_c": math.nan,
        "command_current_peak_raw": math.nan,
        "measured_current_peak_raw": math.nan,
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

    if args.self_check:
        candidates = build_candidates(center, spans, names)
        expected_max = 1 + 2 * len(names)
        assert 1 <= len(candidates) <= expected_max
        assert all(PARAMETERS[n].minimum <= c[n] <= PARAMETERS[n].maximum
                   for c in candidates for n in names)
        print(f"SELF_CHECK PASS parameters={len(names)} candidates={len(candidates)}")
        return 0
    if not args.yes_wheel_lifted:
        parser.error("hardware motion refused: pass --yes-wheel-lifted")

    api = WebApi(args.web_url)
    initial = api.status()
    if initial.get("enabled"):
        parser.error("unit is already enabled; STOP it before auto tuning")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    result_dir = args.output_dir / stamp
    result_dir.mkdir(parents=True, exist_ok=False)
    trial_fields = [
        "round", "candidate", *names, "repeat", "direction", "wheel_rpm", "start_deg",
        "destination_deg", "profile_s", "settle_s", "kinematic_lower_bound_s",
        "performance_deadline_s", "deadline_met", "response_ratio", "overshoot_deg",
        "post_profile_peak_abs_deg", "terminal_abs_error_deg",
        "max_tracking_error_deg", "wheel_mae_rpm", "temp_max_c",
        "command_current_peak_raw", "measured_current_peak_raw",
        "safety_reason", "samples", "trial_score",
    ]
    summary_fields = [
        "round", "candidate", *names, "score", "mean_settle_s",
        "worst_settle_s", "mean_response_ratio", "worst_response_ratio",
        "worst_overshoot_deg", "worst_terminal_abs_error_deg",
        "temp_max_c", "command_current_peak_raw", "measured_current_peak_raw",
        "failed_trials",
    ]
    trials_csv = IncrementalCsv(result_dir / "trials.csv", trial_fields)
    summary_csv = IncrementalCsv(result_dir / "summary.csv", summary_fields)
    sample_fields = [
        "round", "candidate", "repeat", "direction", "wheel_rpm",
        "t", "sequence", "destination_error", "tracking_error",
        "profile_rate_dps", "wheel", "steer_rpm", "motion_settled",
        "temp1", "temp2", "i1", "i2",
        "q1", "q2",
    ]
    samples_csv = IncrementalCsv(result_dir / "samples.csv", sample_fields)
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "arguments": vars(args) | {"output_dir": str(args.output_dir)},
        "starting_center": center,
        "starting_spans": spans,
        "score_formula": "mean(trial_score)+0.35*max(trial_score)",
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
                score = candidate_score(scores) if scores else 1000.0
                settled = [m["settle_s"] for m in metrics_list if m["settle_s"] is not None]
                response_ratios = [m["response_ratio"] for m in metrics_list
                                   if m["response_ratio"] is not None]
                summary = {
                    "round": round_number,
                    "candidate": candidate_number,
                    **candidate,
                    "score": score,
                    "mean_settle_s": sum(settled) / len(settled) if settled else "",
                    "worst_settle_s": max(settled) if settled else "",
                    "mean_response_ratio": (
                        sum(response_ratios) / len(response_ratios)
                        if response_ratios else ""),
                    "worst_response_ratio": max(response_ratios) if response_ratios else "",
                    "worst_overshoot_deg": max((m["overshoot_deg"] for m in metrics_list), default=""),
                    "worst_terminal_abs_error_deg": max((m["terminal_abs_error_deg"] for m in metrics_list), default=""),
                    "temp_max_c": max((m["temp_max_c"] for m in metrics_list if not math.isnan(m["temp_max_c"])), default=""),
                    "command_current_peak_raw": max(
                        (m["command_current_peak_raw"] for m in metrics_list
                         if not math.isnan(m["command_current_peak_raw"])), default=""),
                    "measured_current_peak_raw": max(
                        (m["measured_current_peak_raw"] for m in metrics_list
                         if not math.isnan(m["measured_current_peak_raw"])), default=""),
                    "failed_trials": sum(
                        m["settle_s"] is None or not m.get("deadline_met", False)
                        or bool(m["safety_reason"])
                                         for m in metrics_list),
                }
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
            api.set({"trajectory_time_scale": 2.0})
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
