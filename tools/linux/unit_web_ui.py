#!/usr/bin/env python3
"""unit_web_ui.py - Browser-based manual test UI for a single differential-steer
unit (unitId=1, Linux mini PC, can0 + VCP debug log).

Single file, stdlib + pyserial only (no python-can, no web framework). Serves
a dark, offline-only HTML/JS page (no external CDN/fonts) with sliders for
steer angle / wheel speed / steer rate / steer acceleration,
Enable/STOP/Disable buttons, and a live telemetry readout, backed by a tiny
JSON API.

CAN socket handling (SocketCAN AF_CAN/SOCK_RAW/CAN_RAW, struct "=IB3x8s") and
the VCP serial capture pattern are copied from tools/linux/unit_bench.py --
see that file for the detailed CAN message spec comments. This file
intentionally keeps its own copies rather than importing from unit_bench.py,
so it can be read and modified standalone.

CAN message spec (unitId=1):

    SET_TARGET     ID 0x101  DLC 8  int32 LE steer_mdeg, int32 LE wheel_rpm_milli
                   Sent unconditionally at 200Hz for as long as this server runs
                   (independent of enabled state -- the firmware only acts on
                   it while enabled, but keeping it flowing means enable can
                   happen at any time without a stale target).
    SET_TARGET_FF  ID 0x111  DLC 8  int32 LE steer_rate_mdeg_per_s, int32 LE 0
                   Sent immediately before SET_TARGET every cycle, including
                   the final zero needed to clear rate/acceleration FF.
    UNIT_CTRL      ID 0x121  DLC 2  enable = 01 01, disable = 01 00

VCP telemetry (default /dev/ttyACM0, 115200 8N1), one line per period, e.g.:

    run=1 step=0 angle=315352 target=315352 err=0 steer=0 m1=3762/171875 i1=74
    t1=29 m2=-3748/-171875 i2=-158 t2=28 steerMode=.../... iSteer=...
    driveMode=171875/197789 iDrive=... ffS=5000 scale=0 wheel=500000

    angle/target/err are mdeg. i1/i2 are commanded current (raw). t1/t2 are
    degC. ffS is milli-rpm (divide by 1000 for the steer-rate feedforward in
    "rpm-like" units, as given). Actual wheel rpm = driveMode's 2nd value
    (milli) / 1000 * 32 / 11 (gear ratio). A "STOP: <reason>" line means the
    firmware latched itself to disabled; we mirror that in our own state.

SAFETY:

  1. Lift the wheel off the ground / let it spin free before pressing Enable.
  2. STOP first ramps wheel to 0 at the configured deceleration rate and waits
     current_rpm/decel + margin before sending UNIT_CTRL disable.  This avoids
     both uncontrolled coast and a regenerative-voltage spike from an abrupt
     high-rpm stop.
  3. Disable is the immediate/emergency path: it sends UNIT_CTRL disable
     right away with no wait.
  4. A dead-man watch runs the STOP sequence automatically if the browser
     stops polling /api/status for more than 3 seconds while enabled.
  5. SIGINT, any unhandled exception, and normal process exit all trigger a
     best-effort UNIT_CTRL disable (atexit safety net + try/finally).

Usage:

    python3 tools/linux/unit_web_ui.py                       # can0, :8080, /dev/ttyACM0
    python3 tools/linux/unit_web_ui.py --port 9000
    python3 tools/linux/unit_web_ui.py --can-iface can1 --vcp-port /dev/ttyACM1
    python3 tools/linux/unit_web_ui.py --check                # offline self-check, no CAN/serial
"""

import argparse
import atexit
import json
import math
import socket
import struct
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# --------------------------------------------------------------------------
# CAN message IDs / payload constants (unitId=1) -- copied from unit_bench.py
# --------------------------------------------------------------------------

SET_TARGET_ID = 0x101
SET_TARGET_FF_ID = 0x111
UNIT_CTRL_ID = 0x121
STATUS1_ID = 0x181
STATUS2_ID = 0x191
STATUS3_ID = 0x1A1

STATUS_FLAG_ACTIVE = 1 << 0
STATUS_FLAG_TARGET_FRESH = 1 << 1
STATUS_FLAG_FEEDBACK_OK = 1 << 2
STATUS_FLAG_AMT_OK = 1 << 3
STATUS_FLAG_STEER_IN_BAND = 1 << 4
STATUS_FLAG_WHEEL_IN_BAND = 1 << 5
STATUS_FLAG_MOTION_SETTLED = 1 << 6
STATUS_FLAG_LIMITING_ACTIVE = 1 << 7

ENABLE_PAYLOAD = bytes([0x01, 0x01])
DISABLE_PAYLOAD = bytes([0x01, 0x00])

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = REPO_ROOT / "firmware" / "logs"

# classic (non-FD) SocketCAN frame: struct can_frame { u32 can_id; u8 can_dlc;
# u8 pad[3]; u8 data[8]; }
CAN_FRAME_FMT = "=IB3x8s"
CAN_FRAME_SIZE = struct.calcsize(CAN_FRAME_FMT)

TARGET_HZ = 200.0
DEADMAN_TIMEOUT_S = 3.0
STOP_SETTLE_MARGIN_S = 0.5

STEER_DEG_MIN, STEER_DEG_MAX = 0.0, 360.0
WHEEL_RPM_MIN, WHEEL_RPM_MAX = -1360.0, 1360.0
STEER_RATE_DPS_MIN, STEER_RATE_DPS_MAX = 0.0, 240.0
STEER_ACCEL_DPS2_MIN, STEER_ACCEL_DPS2_MAX = 30.0, 3600.0
STEER_ACCEL_DPS2_DEFAULT = 3600.0
STEER_DECEL_DPS2_MIN, STEER_DECEL_DPS2_MAX = 30.0, 3600.0
STEER_DECEL_DPS2_DEFAULT = 2250.0
WHEEL_ACCEL_RPM_PER_S_MIN, WHEEL_ACCEL_RPM_PER_S_MAX = 100.0, 4000.0
WHEEL_DECEL_RPM_PER_S_MIN, WHEEL_DECEL_RPM_PER_S_MAX = 100.0, 4000.0
WHEEL_ACCEL_RPM_PER_S_DEFAULT = 1000.0
WHEEL_DECEL_RPM_PER_S_DEFAULT = 500.0

WHEEL_GEAR_RATIO = 32.0 / 11.0
STEER_GEAR_RATIO = 8.0 / 11.0
MOTOR_MAX_RPM = 469.0
MOTOR_PLANNED_RPM = MOTOR_MAX_RPM * 0.90
STEER_AXIS_MAX_RPM = 40.0
TRAJECTORY_TIME_SCALE_DEFAULT = 2.0
TRAJECTORY_TIME_SCALE_MIN, TRAJECTORY_TIME_SCALE_MAX = 1.0, 4.0
# Initial measured p99-like profile-end -> STATUS3 settled residual on the
# lifted-wheel 12-trial acceptance batch was about 0.31s (including the
# firmware's 100ms dwell). Keep a small observation margin above it.
PERFORMANCE_ADDITIVE_MARGIN_S = 0.35


# --------------------------------------------------------------------------
# SocketCAN helpers (stdlib only, no python-can) -- copied from unit_bench.py
# --------------------------------------------------------------------------


def open_can_socket(ifname, timeout=None):
    """Open and bind a raw SocketCAN socket on ifname (e.g. 'can0')."""
    sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    sock.bind((ifname,))
    if timeout is not None:
        sock.settimeout(timeout)
    return sock


def build_can_frame(can_id, data):
    dlc = len(data)
    if dlc > 8:
        raise ValueError(f"CAN payload too long ({dlc} bytes): {data!r}")
    padded = data.ljust(8, b"\x00")
    return struct.pack(CAN_FRAME_FMT, can_id, dlc, padded)


def parse_can_frame(frame):
    can_id, dlc, data = struct.unpack(CAN_FRAME_FMT, frame)
    can_id &= socket.CAN_EFF_MASK if (can_id & socket.CAN_EFF_FLAG) else socket.CAN_SFF_MASK
    return can_id, data[:dlc]


def send_set_target(sock, steer_mdeg, wheel_rpm_milli):
    data = struct.pack("<ii", steer_mdeg, wheel_rpm_milli)
    sock.send(build_can_frame(SET_TARGET_ID, data))


def send_set_target_ff(sock, steer_rate_mdeg_per_s, wheel_accel_rpm_milli_per_s=0):
    data = struct.pack("<ii", steer_rate_mdeg_per_s, wheel_accel_rpm_milli_per_s)
    sock.send(build_can_frame(SET_TARGET_FF_ID, data))


def send_unit_ctrl(sock, enable):
    sock.send(build_can_frame(UNIT_CTRL_ID, ENABLE_PAYLOAD if enable else DISABLE_PAYLOAD))


def emergency_disable(can_iface):
    """Best-effort disable using a brand new socket. Never raises."""
    try:
        sock = open_can_socket(can_iface, timeout=0.5)
        try:
            send_unit_ctrl(sock, False)
            send_unit_ctrl(sock, False)
        finally:
            sock.close()
    except OSError as exc:
        print(f"[unit_web_ui] WARNING: emergency disable failed: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------
# Logging -- same pattern as unit_bench.py's BenchLogger
# --------------------------------------------------------------------------


class WebUiLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._fh = open(self.path, "a", buffering=1, encoding="utf-8")
        self.write("WEBUI", f"log opened: {self.path}")

    def write(self, prefix, message):
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        line = f"{ts} {prefix} {message}"
        with self._lock:
            self._fh.write(line + "\n")
        print(line)

    def close(self):
        self.write("WEBUI", "log closed")
        with self._lock:
            self._fh.close()


def default_log_path():
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S") + "Z"
    return DEFAULT_LOG_DIR / f"webui-{stamp}.log"


# --------------------------------------------------------------------------
# Telemetry line parsing
# --------------------------------------------------------------------------


def parse_telemetry_line(line):
    """Parse one VCP line.

    Returns ("stop", reason_str) for a "STOP: <reason>" line, ("telemetry",
    fields_dict) for a normal key=value line, or None if the line has no
    recognizable key=value tokens.

    Tokens of the form key=a/b (e.g. driveMode=171875/197789) are parsed into
    a 2-tuple of ints when possible; plain key=value tokens are parsed as int,
    then float, then left as a raw string.
    """
    line = line.strip()
    if not line:
        return None
    if line.startswith("STOP:"):
        return ("stop", line[len("STOP:") :].strip())

    fields = {}
    for tok in line.split():
        if "=" not in tok:
            continue
        key, _, val = tok.partition("=")
        if not key:
            continue
        if "/" in val:
            parts = val.split("/")
            try:
                fields[key] = tuple(int(p) for p in parts)
                continue
            except ValueError:
                fields[key] = val
                continue
        try:
            fields[key] = int(val)
        except ValueError:
            try:
                fields[key] = float(val)
            except ValueError:
                fields[key] = val
    if not fields:
        return None
    return ("telemetry", fields)


def summarize_telemetry(fields):
    """Reduce a raw parsed telemetry dict to the friendly values the UI shows."""

    def scalar(key):
        v = fields.get(key)
        return v if isinstance(v, (int, float)) else None

    angle = scalar("angle")
    target = scalar("target")
    err = scalar("err")
    i1 = scalar("i1")
    i2 = scalar("i2")
    q1 = scalar("q1")
    q2 = scalar("q2")
    t1 = scalar("t1")
    t2 = scalar("t2")
    ffs = scalar("ffS")
    ffa = scalar("ffA")
    accel_ff_current = scalar("aFF")
    steer_integral = scalar("sInt")
    drive_integral = scalar("dInt")
    status_flags = scalar("statusFlags")

    wheel_rpm_actual_milli = scalar("wheelActual")
    wheel_rpm_actual = (
        wheel_rpm_actual_milli / 1000.0
        if wheel_rpm_actual_milli is not None else None)
    drive_mode = fields.get("driveMode")
    if wheel_rpm_actual is None and isinstance(drive_mode, tuple) and len(drive_mode) == 2:
        wheel_rpm_actual = (drive_mode[1] / 1000.0) * WHEEL_GEAR_RATIO

    def mode_pair(key):
        value = fields.get(key)
        if isinstance(value, tuple) and len(value) == 2:
            return value[0] / 1000.0, value[1] / 1000.0
        return None, None

    steer_mode_target, steer_mode_measured = mode_pair("steerMode")
    drive_mode_target, drive_mode_measured = mode_pair("driveMode")

    motor1_rotor_rpm_milli = scalar("motor1RotorRpmMilli")
    motor2_rotor_rpm_milli = scalar("motor2RotorRpmMilli")
    steer_axis_rpm_actual = None
    if motor1_rotor_rpm_milli is not None and motor2_rotor_rpm_milli is not None:
        motor1_output_rpm = motor1_rotor_rpm_milli / 1000.0 / 19.0
        motor2_output_rpm = motor2_rotor_rpm_milli / 1000.0 / 19.0
        steer_axis_rpm_actual = (
            (motor1_output_rpm + motor2_output_rpm) * 0.5 * STEER_GEAR_RATIO)
    elif steer_mode_measured is not None:
        steer_axis_rpm_actual = steer_mode_measured * STEER_GEAR_RATIO

    return {
        "angle_deg": angle / 1000.0 if angle is not None else None,
        "target_deg": target / 1000.0 if target is not None else None,
        "err_deg": err / 1000.0 if err is not None else None,
        "wheel_rpm_actual": wheel_rpm_actual,
        "steer_rpm_actual": steer_axis_rpm_actual,
        "steer_mode_target_rpm": steer_mode_target,
        "steer_mode_measured_rpm": steer_mode_measured,
        "drive_mode_target_rpm": drive_mode_target,
        "drive_mode_measured_rpm": drive_mode_measured,
        "steer_mode_current": (
            scalar("iSteer") / 1000.0 if scalar("iSteer") is not None else None),
        "drive_mode_current": (
            scalar("iDrive") / 1000.0 if scalar("iDrive") is not None else None),
        "ffs_rpm": ffs / 1000.0 if ffs is not None else None,
        "steer_accel_ff_rpm_per_s": (
            ffa / 1000.0 if ffa is not None else None),
        "steer_accel_ff_current": (
            accel_ff_current / 1000.0 if accel_ff_current is not None else None),
        "i1": i1,
        "i2": i2,
        "q1": q1,
        "q2": q2,
        "t1": t1,
        "t2": t2,
        "steer_integral": (
            steer_integral / 1000.0 if steer_integral is not None else None),
        "drive_integral": (
            drive_integral / 1000.0 if drive_integral is not None else None),
        "drive_in_motion": scalar("mov"),
        "drive_onset_active": scalar("onset"),
        "drive_onset_count": scalar("onsetN"),
        "drive_integral_floor_active": scalar("floor"),
        "torque_scaling_active": scalar("scale"),
        # Present only on "idle" lines: firmware-side start-condition health
        # (fdbkOk=0 means no C620 feedback -> enable will silently not start,
        # typically the 24V motor power is off).
        "fdbk_ok": scalar("fdbkOk"),
        "amt_ok": scalar("amtOk"),
        "status_flags": status_flags,
        "steer_in_band": (
            bool(int(status_flags) & STATUS_FLAG_STEER_IN_BAND)
            if status_flags is not None else None),
        "wheel_in_band": (
            bool(int(status_flags) & STATUS_FLAG_WHEEL_IN_BAND)
            if status_flags is not None else None),
        "motion_settled": (
            bool(int(status_flags) & STATUS_FLAG_MOTION_SETTLED)
            if status_flags is not None else None),
        "limiting_active_status": (
            bool(int(status_flags) & STATUS_FLAG_LIMITING_ACTIVE)
            if status_flags is not None else None),
    }


# --------------------------------------------------------------------------
# Shared server state
# --------------------------------------------------------------------------


class AppState:
    def __init__(self):
        self.lock = threading.Lock()
        # Non-reentrant "only one STOP sequence at a time" guard (manual
        # /api/stop vs. the dead-man watchdog racing each other).
        self.stop_lock = threading.Lock()

        # Last commanded values (as set via /api/set), in real units.
        self.steer_deg = 0.0
        self.wheel_rpm = 0.0
        self.steer_rate_dps = 0.0
        self.steer_accel_dps2 = STEER_ACCEL_DPS2_DEFAULT
        self.steer_decel_dps2 = STEER_DECEL_DPS2_DEFAULT
        self.wheel_accel_rpm_per_s = WHEEL_ACCEL_RPM_PER_S_DEFAULT
        self.wheel_decel_rpm_per_s = WHEEL_DECEL_RPM_PER_S_DEFAULT
        self.trajectory_time_scale = TRAJECTORY_TIME_SCALE_DEFAULT

        # Internally ramped steer target actually transmitted in SET_TARGET,
        # in mdeg (float, wrapped into [0, 360000)). Equals steer_deg*1000
        # whenever steer_rate_dps == 0; otherwise advances by
        # steer_rate_dps*1000*dt each tx cycle.
        self.effective_steer_mdeg = 0.0
        # Signed velocity of the server-side steer target profile.  Keeping
        # this state lets target velocity ramp down before arrival instead of
        # dropping SET_TARGET_FF abruptly from full speed to zero.
        self.profile_steer_rate_dps = 0.0
        self.effective_wheel_rpm = 0.0

        self.enabled = False
        # A normal STOP line can still be buffered in the VCP when the next
        # enable is sent.  Track the enable edge so that stale "disabled"
        # echoes cannot cancel the new run in the server state.
        self.last_enable_time = None

        self.telemetry = None       # last parsed fields dict, or None
        self.telemetry_raw = None   # last raw VCP line
        self.telemetry_time = None  # time.monotonic() of last telemetry line
        self.telemetry_sequence = 0 # increments once per fresh VCP/CAN sample
        self.motion_timing = None

        self.last_stop_reason = None

        # Updated on every GET /api/status; the dead-man watchdog trips if
        # this goes stale for more than DEADMAN_TIMEOUT_S while enabled.
        self.last_poll_time = None


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def mod_360000(mdeg):
    return mdeg % 360000.0


def steer_rate_available_dps(wheel_rpm, motor_budget_rpm=MOTOR_PLANNED_RPM):
    """Steer-axis rate that preserves the requested wheel rpm.

    This is the single-module form of the differential-mode envelope:
    |wheel|/(32/11) + |steer_rpm|/(8/11) <= 469.
    """
    drive_mode_rpm = abs(wheel_rpm) / WHEEL_GEAR_RATIO
    steer_mode_available_rpm = max(0.0, motor_budget_rpm - drive_mode_rpm)
    steer_axis_available_rpm = min(
        STEER_AXIS_MAX_RPM,
        steer_mode_available_rpm * STEER_GEAR_RATIO,
    )
    return steer_axis_available_rpm * 6.0


def wheel_rate_available_rpm(steer_rate_dps, motor_budget_rpm=MOTOR_PLANNED_RPM):
    steer_axis_rpm = abs(steer_rate_dps) / 6.0
    steer_mode_rpm = steer_axis_rpm / STEER_GEAR_RATIO
    return max(0.0, (motor_budget_rpm - steer_mode_rpm) * WHEEL_GEAR_RATIO)


def steer_profile_min_time_s(distance_deg, max_rate_dps,
                             accel_dps2, decel_dps2):
    """Rest-to-rest asymmetric trapezoid/triangle duration."""
    distance_deg = abs(distance_deg)
    max_rate_dps = abs(max_rate_dps)
    if distance_deg <= 1e-9:
        return 0.0
    if max_rate_dps <= 0.0 or accel_dps2 <= 0.0 or decel_dps2 <= 0.0:
        return None
    accel_distance = max_rate_dps * max_rate_dps / (2.0 * accel_dps2)
    decel_distance = max_rate_dps * max_rate_dps / (2.0 * decel_dps2)
    critical_distance = accel_distance + decel_distance
    if distance_deg >= critical_distance:
        return (max_rate_dps / accel_dps2
                + (distance_deg - critical_distance) / max_rate_dps
                + max_rate_dps / decel_dps2)
    peak_rate = math.sqrt(
        2.0 * distance_deg / (1.0 / accel_dps2 + 1.0 / decel_dps2))
    return peak_rate / accel_dps2 + peak_rate / decel_dps2


def wheel_profile_min_time_s(start_rpm, destination_rpm,
                             accel_rpm_per_s, decel_rpm_per_s):
    if accel_rpm_per_s <= 0.0 or decel_rpm_per_s <= 0.0:
        return None
    if start_rpm * destination_rpm < 0.0:
        return (abs(start_rpm) / decel_rpm_per_s
                + abs(destination_rpm) / accel_rpm_per_s)
    speeding_up = abs(destination_rpm) > abs(start_rpm)
    rate = accel_rpm_per_s if speeding_up else decel_rpm_per_s
    return abs(destination_rpm - start_rpm) / rate


def motion_timing(distance_deg, start_wheel_rpm, wheel_rpm,
                  requested_rate_dps, accel_dps2, decel_dps2,
                  wheel_accel_rpm_per_s, wheel_decel_rpm_per_s, time_scale):
    """Return hard/planned reference times for a steady wheel target."""
    hard_rate = min(
        abs(requested_rate_dps),
        steer_rate_available_dps(wheel_rpm, MOTOR_MAX_RPM))
    planned_rate = min(
        abs(requested_rate_dps),
        steer_rate_available_dps(wheel_rpm, MOTOR_PLANNED_RPM))
    hard_steer_min = steer_profile_min_time_s(
        distance_deg, hard_rate, accel_dps2, decel_dps2)
    planned_steer_min = steer_profile_min_time_s(
        distance_deg, planned_rate, accel_dps2, decel_dps2)
    wheel_min = wheel_profile_min_time_s(
        start_wheel_rpm, wheel_rpm,
        wheel_accel_rpm_per_s, wheel_decel_rpm_per_s)
    hard_min = (None if hard_steer_min is None or wheel_min is None
                else max(hard_steer_min, wheel_min))
    planned_min = (None if planned_steer_min is None or wheel_min is None
                   else max(planned_steer_min, wheel_min))
    deadline = None
    if planned_min is not None:
        deadline = time_scale * planned_min + PERFORMANCE_ADDITIVE_MARGIN_S
    return {
        "distance_deg": distance_deg,
        "hard_rate_dps": hard_rate,
        "planned_rate_dps": planned_rate,
        "wheel_transition_min_s": wheel_min,
        "steer_hard_min_s": hard_steer_min,
        "steer_planned_min_s": planned_steer_min,
        "hard_min_s": hard_min,
        "planned_min_s": planned_min,
        "command_profile_s": (
            time_scale * planned_min if planned_min is not None else None),
        "performance_deadline_s": deadline,
        "time_scale": time_scale,
    }


# --------------------------------------------------------------------------
# CAN tx thread: unconditional 200Hz SET_TARGET + SET_TARGET_FF
# --------------------------------------------------------------------------


def shortest_diff_mdeg(a, b):
    """Shortest signed angular difference a-b in mdeg, in [-180000, 180000)."""
    return (a - b + 180000.0) % 360000.0 - 180000.0


def move_toward(value, target, max_delta):
    if value < target:
        return min(value + max_delta, target)
    return max(value - max_delta, target)


def profile_wheel_step(current_rpm, destination_rpm, accel_rpm_per_s,
                       decel_rpm_per_s, dt_s):
    """Ramp wheel rpm, using the slower decel ramp for stops/reversals."""
    if dt_s <= 0.0:
        return current_rpm
    if current_rpm * destination_rpm < 0.0:
        # Never command a direct current-sign reversal.  Regenerate down to
        # zero first, then start accelerating the other way on a later tick.
        return move_toward(
            current_rpm, 0.0, max(0.0, decel_rpm_per_s) * dt_s)
    speeding_up = abs(destination_rpm) > abs(current_rpm)
    rate = accel_rpm_per_s if speeding_up else decel_rpm_per_s
    return move_toward(current_rpm, destination_rpm, max(0.0, rate) * dt_s)


def profile_steer_step(effective_mdeg, destination_mdeg, velocity_dps,
                       max_rate_dps, max_accel_dps2, max_decel_dps2, dt_s):
    """Advance one acceleration-limited steer-target profile step.

    The braking-speed bound sqrt(2*a*remaining_distance) starts deceleration
    early enough to reach the destination at zero target velocity.  When the
    destination changes too late to stop, the profile is allowed a small,
    acceleration-limited overshoot instead of discontinuously forcing FF to
    zero; it then returns smoothly.
    """
    destination_mdeg = mod_360000(destination_mdeg)
    effective_mdeg = mod_360000(effective_mdeg)
    if (max_rate_dps <= 0.0 or max_accel_dps2 <= 0.0
            or max_decel_dps2 <= 0.0 or dt_s <= 0.0):
        return destination_mdeg, 0.0

    diff_mdeg = shortest_diff_mdeg(destination_mdeg, effective_mdeg)
    if abs(diff_mdeg) < 0.001 and abs(velocity_dps) < 0.001:
        return destination_mdeg, 0.0

    direction = 1.0 if diff_mdeg >= 0.0 else -1.0
    remaining_deg = abs(diff_mdeg) / 1000.0
    braking_rate_dps = math.sqrt(2.0 * max_decel_dps2 * remaining_deg)
    desired_rate_dps = direction * min(max_rate_dps, braking_rate_dps)
    speeding_up = (velocity_dps * desired_rate_dps >= 0.0
                   and abs(desired_rate_dps) > abs(velocity_dps))
    rate_limit_dps2 = max_accel_dps2 if speeding_up else max_decel_dps2
    max_rate_delta = rate_limit_dps2 * dt_s
    previous_velocity_dps = velocity_dps
    velocity_dps = move_toward(
        velocity_dps, desired_rate_dps, max_rate_delta)
    velocity_dps = clamp(velocity_dps, -max_rate_dps, max_rate_dps)

    step_mdeg = velocity_dps * 1000.0 * dt_s
    moving_toward_destination = velocity_dps * diff_mdeg > 0.0
    if (moving_toward_destination and abs(step_mdeg) >= abs(diff_mdeg)
            and abs(previous_velocity_dps) <= max_rate_delta):
        # Land exactly on the destination, but keep the final sub-step FF
        # decay acceleration-limited.  It reaches zero on the next tick.
        arrival_velocity_dps = move_toward(
            previous_velocity_dps, 0.0, max_rate_delta)
        return destination_mdeg, arrival_velocity_dps
    return mod_360000(effective_mdeg + step_mdeg), velocity_dps


# The physical steer axis cannot always follow the commanded rate (the two
# motors share the motor_max_rpm budget with the wheel, and the firmware's
# steer_max_rpm clamp caps the axis rate). If the target keeps advancing
# open-loop past what the axis can do, the angle error grows until the
# firmware's 120deg divergence guard latches the unit off. Leash the target:
# never let it lead the measured angle by more than this.
TARGET_LEASH_MDEG = 45000.0
# Ignore telemetry older than this for leash purposes (10Hz run= lines).
LEASH_TELEMETRY_MAX_AGE_S = 0.5


def can_tx_loop(stop_event, state, can_sock, can_lock):
    interval = 1.0 / TARGET_HZ
    next_tick = time.monotonic()
    last_time = next_tick
    while not stop_event.is_set():
        now = time.monotonic()
        dt = now - last_time
        last_time = now
        with state.lock:
            if state.enabled:
                previous_wheel_rpm = state.effective_wheel_rpm
                state.effective_wheel_rpm = profile_wheel_step(
                    state.effective_wheel_rpm,
                    state.wheel_rpm,
                    state.wheel_accel_rpm_per_s / state.trajectory_time_scale,
                    state.wheel_decel_rpm_per_s / state.trajectory_time_scale,
                    dt,
                )
                wheel_accel_ff_rpm_per_s = (
                    (state.effective_wheel_rpm - previous_wheel_rpm) / dt
                    if dt > 0.0 else 0.0)
            else:
                # A disabled unit is stationary by contract.  Do not let the
                # profile advance off-line and create a step on next enable.
                state.effective_wheel_rpm = 0.0
                wheel_accel_ff_rpm_per_s = 0.0

            # steer_rate_dps is the maximum approach speed toward steer_deg.
            # The effective target follows an acceleration-limited trapezoid
            # (triangular on short moves), with braking based on remaining
            # distance.  Thus SET_TARGET_FF approaches zero smoothly instead
            # of dropping from max rate to zero at the destination.
            rate_dps = min(
                abs(state.steer_rate_dps),
                steer_rate_available_dps(state.effective_wheel_rpm),
            )
            time_scale = state.trajectory_time_scale
            rate_dps /= time_scale
            ff_mdeg_s = 0
            if rate_dps > 0.0:
                dest_mdeg = mod_360000(state.steer_deg * 1000.0)
                advanced, profile_rate_dps = profile_steer_step(
                    state.effective_steer_mdeg,
                    dest_mdeg,
                    state.profile_steer_rate_dps,
                    rate_dps,
                    state.steer_accel_dps2 / (time_scale * time_scale),
                    state.steer_decel_dps2 / (time_scale * time_scale),
                    dt,
                )
                telem = state.telemetry
                telem_fresh = (
                    telem is not None
                    and isinstance(telem.get("angle"), (int, float))
                    and (now - state.telemetry_time) < LEASH_TELEMETRY_MAX_AGE_S
                )
                if telem_fresh:
                    lead = shortest_diff_mdeg(advanced, float(telem["angle"]))
                    if lead > TARGET_LEASH_MDEG and profile_rate_dps > 0.0:
                        advanced = mod_360000(
                            float(telem["angle"]) + TARGET_LEASH_MDEG)
                    elif lead < -TARGET_LEASH_MDEG and profile_rate_dps < 0.0:
                        advanced = mod_360000(
                            float(telem["angle"]) - TARGET_LEASH_MDEG)
                state.effective_steer_mdeg = advanced
                state.profile_steer_rate_dps = profile_rate_dps
                ff_mdeg_s = int(round(profile_rate_dps * 1000.0))
            else:
                state.profile_steer_rate_dps = 0.0
            steer_mdeg = int(round(state.effective_steer_mdeg))
            wheel_rpm_milli = int(round(state.effective_wheel_rpm * 1000.0))
            wheel_accel_milli_per_s = int(round(
                wheel_accel_ff_rpm_per_s * 1000.0))

        try:
            with can_lock:
                # Publish zero too. Omitting the final zero left the unit
                # holding the last small non-zero rate until its 200ms FF
                # timeout, which adds avoidable terminal motion and also
                # prevents a clean acceleration-FF derivative at arrival.
                send_set_target_ff(
                    can_sock, ff_mdeg_s, wheel_accel_milli_per_s)
                send_set_target(can_sock, steer_mdeg, wheel_rpm_milli)
        except OSError:
            pass  # best-effort; next cycle will retry

        next_tick += interval
        sleep_for = next_tick - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)
        else:
            next_tick = time.monotonic()


# --------------------------------------------------------------------------
# VCP rx thread -- same pattern as unit_bench.py's vcp_rx_loop
# --------------------------------------------------------------------------


def vcp_rx_loop(stop_event, state, logger, port, baud):
    import serial  # local import: only needed when actually capturing VCP

    try:
        ser = serial.Serial(port, baudrate=baud, timeout=0.2)
    except Exception as exc:  # noqa: BLE001
        logger.write("VCP", f"ERROR: could not open {port}: {exc}")
        return
    try:
        buf = b""
        while not stop_event.is_set():
            try:
                chunk = ser.read(256)
            except Exception as exc:  # noqa: BLE001 - e.g. device unplugged
                logger.write("VCP", f"ERROR: read failed (device disconnected?): {exc}")
                break
            if not chunk:
                continue
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode("utf-8", errors="replace").rstrip("\r")
                if not text:
                    continue
                logger.write("VCP", text)
                parsed = parse_telemetry_line(text)
                if parsed is None:
                    continue
                kind, payload = parsed
                now = time.monotonic()
                with state.lock:
                    if kind == "stop":
                        stale_normal_stop = (
                            payload == "disabled"
                            and state.enabled
                            and state.last_enable_time is not None
                            and (now - state.last_enable_time) < 0.75
                        )
                        if stale_normal_stop:
                            logger.write(
                                "WEBUI",
                                "ignored delayed STOP: disabled after new enable",
                            )
                        else:
                            state.last_stop_reason = payload
                            # Safety STOP reasons are never ignored. Mirror
                            # firmware disabled state into the UI/dead-man.
                            state.enabled = False
                    elif "angle" in payload:
                        # Only run=/idle lines carry the AMT angle; RX echo
                        # lines (SET_TARGET_RX etc.) must not replace the
                        # telemetry snapshot or enable-seeding loses the angle.
                        # Keep STATUS2/3-only fields (actual steer rpm and
                        # convergence flags) when a slower UART run=/idle
                        # snapshot arrives between CAN frames.
                        merged = dict(state.telemetry or {})
                        merged.update(payload)
                        state.telemetry = merged
                        state.telemetry_raw = text
                        state.telemetry_time = now
                        state.telemetry_sequence += 1
    finally:
        ser.close()


def can_status_rx_loop(stop_event, state, logger, can_iface):
    """Merge STATUS1/2/3 into one fresh unit telemetry snapshot."""
    try:
        sock = open_can_socket(can_iface, timeout=0.2)
    except OSError as exc:
        logger.write("CANRX", f"ERROR: could not open {can_iface}: {exc}")
        return
    try:
        while not stop_event.is_set():
            try:
                frame = sock.recv(CAN_FRAME_SIZE)
            except socket.timeout:
                continue
            except OSError as exc:
                logger.write("CANRX", f"ERROR: receive failed: {exc}")
                break
            can_id, data = parse_can_frame(frame)
            if len(data) != 8 or can_id not in (STATUS1_ID, STATUS2_ID, STATUS3_ID):
                continue
            now = time.monotonic()
            with state.lock:
                merged = dict(state.telemetry or {})
                if can_id == STATUS1_ID:
                    angle_mdeg, wheel_rpm_milli = struct.unpack("<ii", data)
                    merged["angle"] = angle_mdeg
                    merged["wheelActual"] = wheel_rpm_milli
                    raw_line = (
                        f"STATUS1 angle={angle_mdeg} wheelActual={wheel_rpm_milli}")
                    state.telemetry_sequence += 1
                elif can_id == STATUS2_ID:
                    motor1_rpm_milli, motor2_rpm_milli = struct.unpack("<ii", data)
                    merged["motor1RotorRpmMilli"] = motor1_rpm_milli
                    merged["motor2RotorRpmMilli"] = motor2_rpm_milli
                    raw_line = (
                        f"STATUS2 m1={motor1_rpm_milli} m2={motor2_rpm_milli}")
                else:
                    bus_mv, status_flags, error_flags = struct.unpack("<HHI", data)
                    merged["busVoltageMv"] = bus_mv
                    merged["statusFlags"] = status_flags
                    merged["errorFlags"] = error_flags
                    raw_line = (
                        f"STATUS3 bus={bus_mv} flags=0x{status_flags:04x} "
                        f"errors=0x{error_flags:08x}")
                state.telemetry = merged
                state.telemetry_raw = raw_line
                state.telemetry_time = now
    finally:
        sock.close()


# --------------------------------------------------------------------------
# STOP sequence / dead-man watchdog
# --------------------------------------------------------------------------


def perform_stop_sequence(state, can_sock, can_lock, logger, reason):
    """omega_w=0, omega_s=0 -> ramp to zero -> UNIT_CTRL disable.

    Guarded by state.stop_lock so a manual /api/stop and the dead-man
    watchdog never run concurrently; if one is already in flight, the other
    call is a no-op (the in-flight sequence will disable regardless).
    """
    if not state.stop_lock.acquire(blocking=False):
        logger.write("WEBUI", f"stop sequence already in progress, ignoring: {reason}")
        return
    try:
        with state.lock:
            state.wheel_rpm = 0.0
            state.steer_rate_dps = 0.0
            state.profile_steer_rate_dps = 0.0
            current_wheel_rpm = abs(state.effective_wheel_rpm)
            wheel_decel_rpm_per_s = state.wheel_decel_rpm_per_s
            trajectory_time_scale = state.trajectory_time_scale
        ramp_time_s = current_wheel_rpm / max(
            wheel_decel_rpm_per_s / trajectory_time_scale,
            WHEEL_DECEL_RPM_PER_S_MIN / trajectory_time_scale)
        stop_wait_s = ramp_time_s + STOP_SETTLE_MARGIN_S
        logger.write(
            "WEBUI",
            f"STOP sequence start ({reason}): wheel={current_wheel_rpm:.1f}rpm "
            f"decel={wheel_decel_rpm_per_s / trajectory_time_scale:.1f}rpm/s "
            f"wait={stop_wait_s:.2f}s",
        )
        time.sleep(stop_wait_s)
        try:
            with can_lock:
                send_unit_ctrl(can_sock, False)
                send_unit_ctrl(can_sock, False)
        except OSError as exc:
            logger.write("WEBUI", f"ERROR: STOP disable send failed: {exc}")
        with state.lock:
            state.enabled = False
            state.last_stop_reason = reason
            state.motion_timing = None
        logger.write("WEBUI", f"STOP sequence complete ({reason})")
    finally:
        state.stop_lock.release()


def deadman_loop(stop_event, state, can_sock, can_lock, logger):
    poll = 0.2
    while not stop_event.is_set():
        time.sleep(poll)
        with state.lock:
            enabled = state.enabled
            last_poll = state.last_poll_time
        if enabled and last_poll is not None and (time.monotonic() - last_poll) > DEADMAN_TIMEOUT_S:
            perform_stop_sequence(
                state, can_sock, can_lock, logger,
                reason=f"dead-man: /api/status polling stalled >{DEADMAN_TIMEOUT_S:.0f}s",
            )


# --------------------------------------------------------------------------
# API handlers
# --------------------------------------------------------------------------


def handle_set(state, body):
    if not isinstance(body, dict):
        return {"ok": False, "error": "body must be a JSON object"}
    updated = {}
    with state.lock:
        # Apply steer_rate_dps before steer_deg: when both arrive in one
        # request, the destination's snap-vs-slew decision must see the new
        # rate, or a rate sent together with the angle is silently bypassed.
        if "steer_rate_dps" in body:
            try:
                v = clamp(float(body["steer_rate_dps"]), STEER_RATE_DPS_MIN, STEER_RATE_DPS_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid steer_rate_dps"}
            state.steer_rate_dps = v
            updated["steer_rate_dps"] = v
        if "steer_accel_dps2" in body:
            try:
                v = clamp(float(body["steer_accel_dps2"]),
                          STEER_ACCEL_DPS2_MIN, STEER_ACCEL_DPS2_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid steer_accel_dps2"}
            state.steer_accel_dps2 = v
            updated["steer_accel_dps2"] = v
        if "steer_decel_dps2" in body:
            try:
                v = clamp(float(body["steer_decel_dps2"]),
                          STEER_DECEL_DPS2_MIN, STEER_DECEL_DPS2_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid steer_decel_dps2"}
            state.steer_decel_dps2 = v
            updated["steer_decel_dps2"] = v
        if "wheel_accel_rpm_per_s" in body:
            try:
                v = clamp(float(body["wheel_accel_rpm_per_s"]),
                          WHEEL_ACCEL_RPM_PER_S_MIN, WHEEL_ACCEL_RPM_PER_S_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid wheel_accel_rpm_per_s"}
            state.wheel_accel_rpm_per_s = v
            updated["wheel_accel_rpm_per_s"] = v
        if "wheel_decel_rpm_per_s" in body:
            try:
                v = clamp(float(body["wheel_decel_rpm_per_s"]),
                          WHEEL_DECEL_RPM_PER_S_MIN, WHEEL_DECEL_RPM_PER_S_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid wheel_decel_rpm_per_s"}
            state.wheel_decel_rpm_per_s = v
            updated["wheel_decel_rpm_per_s"] = v
        if "trajectory_time_scale" in body:
            try:
                v = clamp(float(body["trajectory_time_scale"]),
                          TRAJECTORY_TIME_SCALE_MIN,
                          TRAJECTORY_TIME_SCALE_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid trajectory_time_scale"}
            state.trajectory_time_scale = v
            updated["trajectory_time_scale"] = v
        if "steer_deg" in body:
            try:
                v = clamp(float(body["steer_deg"]), STEER_DEG_MIN, STEER_DEG_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid steer_deg"}
            state.steer_deg = v
            # steer_deg is the destination. With steer_rate_dps == 0 the
            # effective (transmitted) target snaps to it (fastest, firmware
            # clamps govern); with a nonzero rate the tx loop slews the
            # effective target toward it at that speed (profiled approach).
            if state.steer_rate_dps == 0.0:
                state.effective_steer_mdeg = mod_360000(v * 1000.0)
                state.profile_steer_rate_dps = 0.0
            updated["steer_deg"] = v
        if "wheel_rpm" in body:
            try:
                v = clamp(float(body["wheel_rpm"]), WHEEL_RPM_MIN, WHEEL_RPM_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid wheel_rpm"}
            state.wheel_rpm = v
            updated["wheel_rpm"] = v
        if state.enabled and ("steer_deg" in updated or "wheel_rpm" in updated):
            telem = state.telemetry or {}
            actual_mdeg = telem.get("angle")
            if not isinstance(actual_mdeg, (int, float)):
                actual_mdeg = state.effective_steer_mdeg
            actual_wheel_milli = telem.get("wheelActual")
            start_wheel_rpm = (
                actual_wheel_milli / 1000.0
                if isinstance(actual_wheel_milli, (int, float))
                else state.effective_wheel_rpm)
            distance_deg = abs(shortest_diff_mdeg(
                state.steer_deg * 1000.0, float(actual_mdeg))) / 1000.0
            requested_rate_dps = (
                state.steer_rate_dps
                if state.steer_rate_dps > 0.0 else STEER_RATE_DPS_MAX)
            state.motion_timing = motion_timing(
                distance_deg,
                start_wheel_rpm,
                state.wheel_rpm,
                requested_rate_dps,
                state.steer_accel_dps2,
                state.steer_decel_dps2,
                state.wheel_accel_rpm_per_s,
                state.wheel_decel_rpm_per_s,
                state.trajectory_time_scale,
            )
            state.motion_timing["started_monotonic"] = time.monotonic()
        elif not state.enabled:
            state.motion_timing = None
    if not updated:
        return {"ok": False, "error": "no recognized fields in body"}
    return {"ok": True, "updated": updated}


def handle_enable(state, can_sock, can_lock, logger):
    with state.lock:
        telem = state.telemetry
        if telem is None or "angle" not in telem or not isinstance(telem["angle"], (int, float)):
            return {"ok": False, "error": "no telemetry received yet; refusing to enable"}, 400
        angle_mdeg = telem["angle"]
        # Seed the internal target with the unit's actual current angle so
        # enabling doesn't immediately command a large angle step (angle
        # divergence guard).
        state.effective_steer_mdeg = mod_360000(float(angle_mdeg))
        state.profile_steer_rate_dps = 0.0
        state.effective_wheel_rpm = 0.0
        state.wheel_rpm = 0.0
        state.steer_deg = state.effective_steer_mdeg / 1000.0
        seeded_mdeg = int(round(state.effective_steer_mdeg))
        wheel_milli = 0
        # Reset the dead-man heartbeat: without this, enabling after an idle
        # browser gap trips the watchdog on the very same cycle.
        state.last_poll_time = time.monotonic()
        state.last_enable_time = state.last_poll_time
        state.enabled = True
        state.last_stop_reason = None
        state.motion_timing = None
    try:
        with can_lock:
            # The firmware latches the last received SET_TARGET at START; the
            # The tx thread may not have sent the seeded angle yet, so land
            # one fresh frame before enabling or the divergence guard trips
            # on the stale target.
            send_set_target(can_sock, seeded_mdeg, wheel_milli)
        time.sleep(0.05)
        with can_lock:
            send_unit_ctrl(can_sock, True)
    except OSError as exc:
        with state.lock:
            state.enabled = False
        return {"ok": False, "error": f"CAN send failed: {exc}"}, 500
    logger.write("WEBUI", f"enable sent (seeded steer target={state.steer_deg:.3f}deg)")
    return {"ok": True, "steer_deg": state.steer_deg}, 200


def handle_stop(state, can_sock, can_lock, logger):
    perform_stop_sequence(state, can_sock, can_lock, logger, reason="manual STOP")
    return {"ok": True}


def handle_disable(state, can_sock, can_lock, logger):
    try:
        with can_lock:
            send_unit_ctrl(can_sock, False)
            send_unit_ctrl(can_sock, False)
    except OSError as exc:
        logger.write("WEBUI", f"ERROR: emergency disable send failed: {exc}")
        return {"ok": False, "error": str(exc)}
    with state.lock:
        # Zero targets too so a subsequent Enable doesn't resume old motion.
        state.wheel_rpm = 0.0
        state.steer_rate_dps = 0.0
        state.profile_steer_rate_dps = 0.0
        state.effective_wheel_rpm = 0.0
        state.enabled = False
        state.last_stop_reason = "manual DISABLE (emergency, no coast)"
        state.motion_timing = None
    logger.write("WEBUI", "emergency disable sent")
    return {"ok": True}


def build_status_json(state):
    now_mono = time.monotonic()
    with state.lock:
        state.last_poll_time = now_mono
        cfg = {
            "steer_deg": state.steer_deg,
            "wheel_rpm": state.wheel_rpm,
            "steer_rate_dps": state.steer_rate_dps,
            "steer_accel_dps2": state.steer_accel_dps2,
            "steer_decel_dps2": state.steer_decel_dps2,
            "wheel_accel_rpm_per_s": state.wheel_accel_rpm_per_s,
            "wheel_decel_rpm_per_s": state.wheel_decel_rpm_per_s,
            "trajectory_time_scale": state.trajectory_time_scale,
        }
        effective_steer_deg = state.effective_steer_mdeg / 1000.0
        profile_steer_rate_dps = state.profile_steer_rate_dps
        effective_wheel_rpm = state.effective_wheel_rpm
        enabled = state.enabled
        last_stop_reason = state.last_stop_reason
        telem = state.telemetry
        telem_raw = state.telemetry_raw
        telem_time = state.telemetry_time
        telem_sequence = state.telemetry_sequence
        timing = dict(state.motion_timing) if state.motion_timing is not None else None

    telemetry_json = None
    if telem is not None:
        telemetry_json = summarize_telemetry(telem)
        telemetry_json["raw_line"] = telem_raw
        telemetry_json["age_s"] = round(now_mono - telem_time, 3) if telem_time is not None else None
        telemetry_json["sequence"] = telem_sequence
        if telemetry_json.get("angle_deg") is not None:
            telemetry_json["destination_error_deg"] = (
                shortest_diff_mdeg(
                    cfg["steer_deg"] * 1000.0,
                    telemetry_json["angle_deg"] * 1000.0) / 1000.0)

    if timing is not None:
        started = timing.pop("started_monotonic")
        elapsed_s = max(0.0, now_mono - started)
        timing["elapsed_s"] = elapsed_s
        deadline = timing.get("performance_deadline_s")
        motion_settled_now = bool(
            telemetry_json and telemetry_json.get("motion_settled"))
        timing["deadline_state"] = (
            "settled" if motion_settled_now
            else "late" if deadline is not None and elapsed_s > deadline
            else "tracking")

    # Feasibility envelope: the two motors share the motor_max_rpm budget.
    # The tx profiler uses this same bound, so unlike the old warning-only
    # display it actively preserves wheel rpm by reducing steer rate first.
    requested_steer_rate = (
        cfg["steer_rate_dps"] if cfg["steer_rate_dps"] > 0.0
        else STEER_RATE_DPS_MAX)
    wheel_avail_rpm = wheel_rate_available_rpm(requested_steer_rate)

    return {
        "config": cfg,
        "effective_steer_deg": round(effective_steer_deg, 3),
        "profile_steer_rate_dps": round(profile_steer_rate_dps, 3),
        "effective_wheel_rpm": round(effective_wheel_rpm, 3),
        "enabled": enabled,
        "last_stop_reason": last_stop_reason,
        "telemetry": telemetry_json,
        "timing": timing,
        "envelope": {
            "steer_rate_avail_dps": round(
                steer_rate_available_dps(effective_wheel_rpm), 1),
            "steer_rate_hard_dps": round(
                steer_rate_available_dps(effective_wheel_rpm, MOTOR_MAX_RPM), 1),
            "wheel_avail_rpm": round(wheel_avail_rpm, 1),
            "motor_budget_planned_rpm": round(MOTOR_PLANNED_RPM, 1),
            "motor_budget_hard_rpm": MOTOR_MAX_RPM,
            "wheel_axis_max_planned_rpm": round(
                MOTOR_PLANNED_RPM * WHEEL_GEAR_RATIO, 1),
        },
        "server_time_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    }


# --------------------------------------------------------------------------
# HTML/CSS/JS (single inline page, no external resources)
# --------------------------------------------------------------------------

INDEX_HTML = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Unit Web UI - Differential Swerve Drive</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    background: #101214; color: #e6e6e6;
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    margin: 0; padding: 16px 20px 60px;
  }
  h1 { font-size: 1.25rem; margin: 0 0 8px; }
  .safety {
    background: #3a2200; border: 1px solid #a55b00; color: #ffd699;
    border-radius: 6px; padding: 10px 14px; margin-bottom: 16px; font-size: 0.9rem;
    line-height: 1.5;
  }
  .panel {
    background: #191c1f; border: 1px solid #2a2e33; border-radius: 8px;
    padding: 14px 16px; margin-bottom: 14px;
  }
  .field { display: flex; align-items: center; gap: 10px; margin: 10px 0; flex-wrap: wrap; }
  .field label { width: 220px; flex: 0 0 220px; font-size: 0.9rem; color: #b9c2cc; }
  .field input[type=range] { flex: 1 1 220px; min-width: 160px; }
  .field input[type=number] { width: 90px; background: #0d0f11; color: #e6e6e6; border: 1px solid #3a3f45; border-radius: 4px; padding: 4px 6px; }
  .field button.zero { font-size: 0.75rem; padding: 3px 8px; background: #2a2e33; color: #cfd6dd; border: 1px solid #40464d; border-radius: 4px; cursor: pointer; }
  .field button.zero:hover { background: #363b41; }
  .actions { display: flex; gap: 14px; margin-top: 4px; flex-wrap: wrap; }
  .btn { font-size: 1rem; padding: 12px 22px; border-radius: 6px; border: none; cursor: pointer; font-weight: 600; }
  .btn.enable { background: #1f9d55; color: #fff; }
  .btn.enable:hover { background: #24b863; }
  .btn.stop { background: #c62828; color: #fff; font-size: 1.4rem; padding: 18px 40px; box-shadow: 0 0 0 3px #ff6b6b55; }
  .btn.stop:hover { background: #e53935; }
  .btn.disable { background: #555b63; color: #fff; }
  .btn.disable:hover { background: #6b7178; }
  table.status { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
  table.status td { padding: 5px 8px; border-bottom: 1px solid #24282c; }
  table.status td.k { color: #9aa4ad; width: 46%; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
  .badge.on { background: #1f9d55; color: #fff; }
  .badge.off { background: #444; color: #ccc; }
  .raw { font-family: ui-monospace, monospace; font-size: 0.78rem; color: #7d8790; word-break: break-all; margin-top: 6px; }
  .vector-wrap { display: flex; flex-wrap: wrap; align-items: center; gap: 18px; }
  .vector-pad { width: min(360px, 90vw); height: auto; background: #0b0d0f; border: 1px solid #3d454d; border-radius: 12px; touch-action: none; cursor: crosshair; }
  .vector-axis { stroke: #36404a; stroke-width: 1; }
  .vector-ring { fill: none; stroke: #59636d; stroke-width: 2; }
  .vector-line { stroke: #45a3ff; stroke-width: 5; stroke-linecap: round; }
  .vector-tip { fill: #ffca45; stroke: #fff2bd; stroke-width: 2; }
  .vector-readout { min-width: 260px; line-height: 1.8; }
  .vector-readout .value { color: #ffca45; font-family: ui-monospace, monospace; }
</style>
</head>
<body>
<h1>Unit Web UI (unitId=1, can0)</h1>
<div class="safety">
  <strong>安全注意:</strong> Enable前に必ずホイールを浮かせる/自由回転できる状態にすること。
  STOPボタンはwheelを設定した減速率で0へランプし、ゼロ到達見込み+余裕時間を待ってから
  disableを送信する(急減速の回生電圧上昇と、disable後の空走カップリングを避けるため)。
  Disableボタンは待たずに即disableする緊急停止用。
  操作: Enable中は矢印キーまたはドラッグで青い速度ベクトルの先端を動かすと、
  角度+wheel rpmを約30Hzでリアルタイム送信する。Shift併用は微調整、Escでベクトルを中央へ戻す。
</div>

<div class="panel">
  <h2>Velocity vector command</h2>
  <div class="vector-wrap">
    <svg id="vector_pad" class="vector-pad" viewBox="0 0 220 220"
         role="img" aria-label="wheel velocity vector command pad">
      <circle class="vector-ring" cx="110" cy="110" r="90"></circle>
      <line class="vector-axis" x1="20" y1="110" x2="200" y2="110"></line>
      <line class="vector-axis" x1="110" y1="20" x2="110" y2="200"></line>
      <text x="196" y="104" fill="#8f9ba6" font-size="9">0&deg;</text>
      <text x="115" y="28" fill="#8f9ba6" font-size="9">90&deg;</text>
      <line id="vector_line" class="vector-line" x1="110" y1="110" x2="110" y2="110"></line>
      <circle id="vector_tip" class="vector-tip" cx="110" cy="110" r="7"></circle>
    </svg>
    <div class="vector-readout">
      <div>矢印キー/ドラッグ: ベクトル先端を移動・リアルタイム送信</div>
      <div>Shift+矢印: 微調整 / Esc: 中央へ戻す</div>
      <div>Disable中はdraftのみ、Enable中は約30Hzで反映</div>
      <div>Draft angle: <span id="vector_angle" class="value">--</span></div>
      <div>Draft wheel: <span id="vector_rpm" class="value">0 rpm</span></div>
      <button class="btn enable" onclick="applyVectorCommand()">現在ベクトルを再送</button>
      <button class="zero" onclick="centerVectorDraft()">ベクトルを0へ</button>
    </div>
  </div>
</div>

<div class="panel">
  <div class="field">
    <label for="steer_deg_range">Steer target &theta;s (deg, 0-360)</label>
    <input type="range" id="steer_deg_range" min="0" max="360" step="0.1" value="0"
           oninput="onFieldInput('steer_deg', this.value)">
    <input type="number" id="steer_deg_num" min="0" max="360" step="0.1" value="0"
           onchange="onFieldInput('steer_deg', this.value)">
  </div>
  <div class="field">
    <label for="wheel_rpm_range">Wheel speed &omega;w (rpm, -1360..+1360)</label>
    <input type="range" id="wheel_rpm_range" min="-1360" max="1360" step="5" value="0"
           oninput="onFieldInput('wheel_rpm', this.value)">
    <input type="number" id="wheel_rpm_num" min="-1360" max="1360" step="5" value="0"
           onchange="onFieldInput('wheel_rpm', this.value)">
    <button class="zero" onclick="zeroField('wheel_rpm')">wheel=0</button>
  </div>
  <div class="field">
    <label for="wheel_accel_rpm_per_s_range">Wheel acceleration (rpm/s)</label>
    <input type="range" id="wheel_accel_rpm_per_s_range" min="100" max="4000" step="100" value="1000"
           oninput="onFieldInput('wheel_accel_rpm_per_s', this.value)">
    <input type="number" id="wheel_accel_rpm_per_s_num" min="100" max="4000" step="100" value="1000"
           onchange="onFieldInput('wheel_accel_rpm_per_s', this.value)">
  </div>
  <div class="field">
    <label for="wheel_decel_rpm_per_s_range">Wheel deceleration / reversal ramp (rpm/s)</label>
    <input type="range" id="wheel_decel_rpm_per_s_range" min="100" max="4000" step="100" value="500"
           oninput="onFieldInput('wheel_decel_rpm_per_s', this.value)">
    <input type="number" id="wheel_decel_rpm_per_s_num" min="100" max="4000" step="100" value="500"
           onchange="onFieldInput('wheel_decel_rpm_per_s', this.value)">
  </div>
  <div class="field">
    <label for="steer_rate_dps_range">&omega;s maximum approach speed to &theta;s (deg/s, 0 = instant step)</label>
    <input type="range" id="steer_rate_dps_range" min="0" max="240" step="5" value="0"
           oninput="onFieldInput('steer_rate_dps', this.value)">
    <input type="number" id="steer_rate_dps_num" min="0" max="240" step="5" value="0"
           onchange="onFieldInput('steer_rate_dps', this.value)">
    <button class="zero" onclick="zeroField('steer_rate_dps')">steer_rate=0</button>
  </div>
  <div class="field">
    <label for="steer_accel_dps2_range">Steer profile acceleration (deg/s&sup2;)</label>
    <input type="range" id="steer_accel_dps2_range" min="30" max="3600" step="30" value="3600"
           oninput="onFieldInput('steer_accel_dps2', this.value)">
    <input type="number" id="steer_accel_dps2_num" min="30" max="3600" step="30" value="3600"
           onchange="onFieldInput('steer_accel_dps2', this.value)">
  </div>
  <div class="field">
    <label for="steer_decel_dps2_range">Steer profile braking deceleration (deg/s&sup2;)</label>
    <input type="range" id="steer_decel_dps2_range" min="30" max="3600" step="30" value="2250"
           oninput="onFieldInput('steer_decel_dps2', this.value)">
    <input type="number" id="steer_decel_dps2_num" min="30" max="3600" step="30" value="2250"
           onchange="onFieldInput('steer_decel_dps2', this.value)">
  </div>
  <div class="field">
    <label for="trajectory_time_scale_range">Trajectory time scale (1=minimum, 2=adopted margin)</label>
    <input type="range" id="trajectory_time_scale_range" min="1" max="4" step="0.1" value="2"
           oninput="onFieldInput('trajectory_time_scale', this.value)">
    <input type="number" id="trajectory_time_scale_num" min="1" max="4" step="0.1" value="2"
           onchange="onFieldInput('trajectory_time_scale', this.value)">
  </div>

  <div class="actions">
    <button class="btn enable" onclick="callAction('/api/enable')">ENABLE</button>
    <button class="btn stop" onclick="callAction('/api/stop')">STOP</button>
    <button class="btn disable" onclick="callAction('/api/disable')">Disable</button>
  </div>
</div>

<div class="panel">
  <table class="status">
    <tr><td class="k">Enabled</td><td><span id="st_enabled" class="badge off">--</span></td></tr>
    <tr><td class="k">Effective target (server-side, ramped)</td><td id="st_effective_target">--</td></tr>
    <tr><td class="k">Profile steer rate (actual FF)</td><td id="st_profile_rate">--</td></tr>
    <tr><td class="k">Profile wheel target (ramped)</td><td id="st_effective_wheel">--</td></tr>
    <tr><td class="k">Angle (firmware, actual)</td><td id="st_angle">--</td></tr>
    <tr><td class="k">Angle error</td><td id="st_err">--</td></tr>
    <tr><td class="k">Wheel actual (rpm)</td><td id="st_wheel">--</td></tr>
    <tr><td class="k">Steer actual (axis rpm)</td><td id="st_steer_rpm">--</td></tr>
    <tr><td class="k">CAN convergence</td><td><span id="st_settled" class="badge off">--</span></td></tr>
    <tr><td class="k">Hard / planned Tmin</td><td id="st_timing_min">--</td></tr>
    <tr><td class="k">2x command / performance deadline</td><td id="st_timing_budget">--</td></tr>
    <tr><td class="k">Elapsed / deadline state</td><td id="st_timing_state">--</td></tr>
    <tr><td class="k">ffS (steer-rate FF, rpm units)</td><td id="st_ffs">--</td></tr>
    <tr><td class="k">i1 / i2 (commanded current, raw)</td><td id="st_i1i2">--</td></tr>
    <tr><td class="k">q1 / q2 (C620 torque feedback, raw)</td><td id="st_q1q2">--</td></tr>
    <tr><td class="k">PI integrals steer / drive (raw)</td><td id="st_integrals">--</td></tr>
    <tr><td class="k">Drive motion / onset count / floor / scale</td><td id="st_drive_flags">--</td></tr>
    <tr><td class="k">t1 / t2 (temperature)</td><td id="st_t1t2">--</td></tr>
    <tr><td class="k">Telemetry age</td><td id="st_age">--</td></tr>
    <tr><td class="k">Last STOP reason</td><td id="st_stop_reason">--</td></tr>
    <tr><td class="k">Steer rate limit planned / hard</td><td id="st_env_ws">--</td></tr>
    <tr><td class="k">&omega;w available (at current &omega;s)</td><td id="st_env_ww">--</td></tr>
    <tr><td class="k">C620 feedback (idle check)</td><td id="st_fdbk">--</td></tr>
  </table>
  <div class="raw" id="st_raw"></div>
</div>

<script>
const STATUS_URL = "/api/status";
const SET_URL = "/api/set";

let debounceTimers = {};
let vectorX = 0;
let vectorY = 0;
let vectorDirty = false;
let vectorWheelMaxRpm = 1228;
let vectorUnitEnabled = false;
let vectorSendTimer = null;
let vectorRevision = 0;
let vectorPointerActive = false;
const VECTOR_SEND_INTERVAL_MS = 33;

function postSet(payload) {
  return fetch(SET_URL, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  }).catch(function (err) { console.error("set failed", err); });
}

function onFieldInput(name, value) {
  document.getElementById(name + "_num").value = value;
  document.getElementById(name + "_range").value = value;
  clearTimeout(debounceTimers[name]);
  debounceTimers[name] = setTimeout(function () {
    const payload = {};
    payload[name] = parseFloat(value);
    postSet(payload);
  }, 100);
}

function zeroField(name) {
  onFieldInput(name, 0);
}

function clampVectorDraft() {
  const magnitude = Math.hypot(vectorX, vectorY);
  if (magnitude > 1) {
    vectorX /= magnitude;
    vectorY /= magnitude;
  }
}

function vectorCommandValues() {
  const magnitude = Math.min(1, Math.hypot(vectorX, vectorY));
  let angle = Math.atan2(vectorY, vectorX) * 180 / Math.PI;
  if (angle < 0) angle += 360;
  return {angle: angle, rpm: Math.floor(magnitude * vectorWheelMaxRpm / 5) * 5};
}

function renderVectorDraft() {
  clampVectorDraft();
  const px = 110 + vectorX * 90;
  const py = 110 - vectorY * 90;
  document.getElementById("vector_line").setAttribute("x2", px.toFixed(2));
  document.getElementById("vector_line").setAttribute("y2", py.toFixed(2));
  document.getElementById("vector_tip").setAttribute("cx", px.toFixed(2));
  document.getElementById("vector_tip").setAttribute("cy", py.toFixed(2));
  const command = vectorCommandValues();
  document.getElementById("vector_angle").textContent =
    (command.rpm === 0 ? "hold current" : command.angle.toFixed(1) + " deg");
  document.getElementById("vector_rpm").textContent = command.rpm.toFixed(0) + " rpm";
}

function syncVectorFromCommand(config) {
  if (vectorDirty || !config) return;
  let rpm = Number(config.wheel_rpm) || 0;
  let angle = Number(config.steer_deg) || 0;
  if (rpm < 0) {
    rpm = -rpm;
    angle += 180;
  }
  const magnitude = Math.min(1, rpm / vectorWheelMaxRpm);
  const radians = angle * Math.PI / 180;
  vectorX = magnitude * Math.cos(radians);
  vectorY = magnitude * Math.sin(radians);
  renderVectorDraft();
}

function applyVectorCommand() {
  const command = vectorCommandValues();
  const payload = {wheel_rpm: command.rpm, steer_rate_dps: 240};
  if (command.rpm > 0) payload.steer_deg = command.angle;
  document.getElementById("wheel_rpm_num").value = command.rpm;
  document.getElementById("wheel_rpm_range").value = command.rpm;
  if (command.rpm > 0) {
    document.getElementById("steer_deg_num").value = command.angle.toFixed(1);
    document.getElementById("steer_deg_range").value = command.angle.toFixed(1);
  }
  document.getElementById("steer_rate_dps_num").value = 240;
  document.getElementById("steer_rate_dps_range").value = 240;
  const revision = ++vectorRevision;
  vectorDirty = true;
  postSet(payload).then(function () {
    if (revision === vectorRevision) vectorDirty = false;
  });
}

function scheduleVectorCommand() {
  if (!vectorUnitEnabled || vectorSendTimer !== null) return;
  vectorSendTimer = setTimeout(function () {
    vectorSendTimer = null;
    applyVectorCommand();
  }, VECTOR_SEND_INTERVAL_MS);
}

function centerVectorDraft() {
  vectorX = 0;
  vectorY = 0;
  vectorDirty = true;
  renderVectorDraft();
  scheduleVectorCommand();
}

function updateVectorFromPointer(event) {
  const pad = document.getElementById("vector_pad");
  const rect = pad.getBoundingClientRect();
  vectorX = ((event.clientX - rect.left) / rect.width * 220 - 110) / 90;
  vectorY = -(((event.clientY - rect.top) / rect.height * 220 - 110) / 90);
  vectorDirty = true;
  renderVectorDraft();
  scheduleVectorCommand();
}

document.getElementById("vector_pad").addEventListener("pointerdown", function (event) {
  vectorPointerActive = true;
  this.setPointerCapture(event.pointerId);
  updateVectorFromPointer(event);
});

document.getElementById("vector_pad").addEventListener("pointermove", function (event) {
  if (vectorPointerActive) updateVectorFromPointer(event);
});

document.getElementById("vector_pad").addEventListener("pointerup", function (event) {
  vectorPointerActive = false;
  updateVectorFromPointer(event);
});

document.getElementById("vector_pad").addEventListener("pointercancel", function () {
  vectorPointerActive = false;
});

document.addEventListener("keydown", function (event) {
  const tag = (event.target && event.target.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select" || tag === "button" ||
      (event.target && event.target.isContentEditable)) return;
  const step = event.shiftKey ? 0.02 : 0.10;
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    vectorX += event.key === "ArrowRight" ? step : -step;
  } else if (event.key === "ArrowUp" || event.key === "ArrowDown") {
    vectorY += event.key === "ArrowUp" ? step : -step;
  } else if (event.key === "Enter") {
    event.preventDefault();
    applyVectorCommand();
    return;
  } else if (event.key === "Escape") {
    event.preventDefault();
    centerVectorDraft();
    return;
  } else {
    return;
  }
  event.preventDefault();
  vectorDirty = true;
  renderVectorDraft();
  scheduleVectorCommand();
});

function callAction(url) {
  fetch(url, {method: "POST"})
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (!data.ok) { alert("Error: " + (data.error || "unknown")); }
      refreshStatus();
    })
    .catch(function (err) { alert("Request failed: " + err); });
}

function fmt(v, digits) {
  if (v === null || v === undefined) return "--";
  return Number(v).toFixed(digits === undefined ? 1 : digits);
}

function refreshStatus() {
  fetch(STATUS_URL).then(function (r) { return r.json(); }).then(function (data) {
    const en = document.getElementById("st_enabled");
    en.textContent = data.enabled ? "ENABLED" : "disabled";
    en.className = data.enabled ? "badge on" : "badge off";
    vectorUnitEnabled = Boolean(data.enabled);
    document.getElementById("st_effective_target").textContent = fmt(data.effective_steer_deg, 2) + " deg";
    document.getElementById("st_profile_rate").textContent =
      fmt(data.profile_steer_rate_dps / 6, 2) + " axis rpm (" +
      fmt(data.profile_steer_rate_dps, 1) + " deg/s)";
    document.getElementById("st_effective_wheel").textContent = fmt(data.effective_wheel_rpm, 1) + " rpm";
    document.getElementById("st_stop_reason").textContent = data.last_stop_reason || "--";
    if (data.envelope && data.envelope.wheel_axis_max_planned_rpm) {
      vectorWheelMaxRpm = data.envelope.wheel_axis_max_planned_rpm;
    }
    syncVectorFromCommand(data.config);

    if (data.envelope) {
      const wsAvail = data.envelope.steer_rate_avail_dps;
      const wsHard = data.envelope.steer_rate_hard_dps;
      const wwAvail = data.envelope.wheel_avail_rpm;
      const wsEl = document.getElementById("st_env_ws");
      const wwEl = document.getElementById("st_env_ww");
      wsEl.textContent = fmt(wsAvail / 6, 1) + " / " + fmt(wsHard / 6, 1) +
        " axis rpm (" + fmt(wsAvail, 0) + " / " + fmt(wsHard, 0) + " deg/s)";
      wwEl.textContent = fmt(wwAvail, 0) + " rpm";
      // Highlight when the current request exceeds the feasible envelope
      // (the two motors share the 469rpm budget; firmware cuts wheel first,
      // and the server-side target leash prevents the divergence STOP).
      wsEl.style.color = Math.abs(data.config.steer_rate_dps) > wsAvail ? "#ff6b6b" : "";
      wwEl.style.color = Math.abs(data.config.wheel_rpm) > wwAvail ? "#ff6b6b" : "";
    }

    if (data.timing) {
      document.getElementById("st_timing_min").textContent =
        fmt(data.timing.hard_min_s, 3) + " / " + fmt(data.timing.planned_min_s, 3) + " s";
      document.getElementById("st_timing_budget").textContent =
        fmt(data.timing.command_profile_s, 3) + " / " +
        fmt(data.timing.performance_deadline_s, 3) + " s";
      document.getElementById("st_timing_state").textContent =
        fmt(data.timing.elapsed_s, 3) + " s / " + data.timing.deadline_state;
    } else {
      ["st_timing_min", "st_timing_budget", "st_timing_state"].forEach(function (id) {
        document.getElementById(id).textContent = "--";
      });
    }

    const t = data.telemetry;
    if (t) {
      document.getElementById("st_angle").textContent = fmt(t.angle_deg, 2) + " deg";
      document.getElementById("st_err").textContent =
        fmt(t.destination_error_deg !== undefined ? t.destination_error_deg : t.err_deg, 2) + " deg";
      document.getElementById("st_wheel").textContent = fmt(t.wheel_rpm_actual, 1) + " rpm";
      document.getElementById("st_steer_rpm").textContent = fmt(t.steer_rpm_actual, 2) + " rpm";
      const settled = document.getElementById("st_settled");
      settled.textContent = t.motion_settled ? "SETTLED" : "tracking";
      settled.className = t.motion_settled ? "badge on" : "badge off";
      document.getElementById("st_ffs").textContent = fmt(t.ffs_rpm, 1) + " rpm";
      document.getElementById("st_i1i2").textContent = fmt(t.i1, 0) + " / " + fmt(t.i2, 0);
      document.getElementById("st_q1q2").textContent = fmt(t.q1, 0) + " / " + fmt(t.q2, 0);
      document.getElementById("st_integrals").textContent =
        fmt(t.steer_integral, 1) + " / " + fmt(t.drive_integral, 1);
      document.getElementById("st_drive_flags").textContent =
        fmt(t.drive_in_motion, 0) + " / " + fmt(t.drive_onset_count, 0) + " / " +
        fmt(t.drive_integral_floor_active, 0) + " / " + fmt(t.torque_scaling_active, 0);
      document.getElementById("st_t1t2").textContent = fmt(t.t1, 0) + " / " + fmt(t.t2, 0) + " C";
      document.getElementById("st_age").textContent = fmt(t.age_s, 2) + " s ago";
      document.getElementById("st_raw").textContent = t.raw_line || "";
      const fdbkEl = document.getElementById("st_fdbk");
      if (t.fdbk_ok === 0) {
        fdbkEl.textContent = "NG - C620 feedback missing (24V motor power off?)";
        fdbkEl.style.color = "#ff6b6b";
      } else if (t.fdbk_ok === 1) {
        fdbkEl.textContent = "OK";
        fdbkEl.style.color = "";
      } else {
        fdbkEl.textContent = "(running)";
        fdbkEl.style.color = "";
      }
    } else {
      ["st_angle", "st_err", "st_wheel", "st_steer_rpm", "st_ffs", "st_i1i2", "st_q1q2",
       "st_integrals", "st_drive_flags", "st_t1t2", "st_age"].forEach(function (id) {
        document.getElementById(id).textContent = "--";
      });
      document.getElementById("st_raw").textContent = "";
      document.getElementById("st_settled").textContent = "--";
      document.getElementById("st_settled").className = "badge off";
    }
  }).catch(function () {
    document.getElementById("st_enabled").textContent = "poll error";
  });
}

setInterval(refreshStatus, 200);
renderVectorDraft();
refreshStatus();
</script>
</body>
</html>
"""


def render_index_html():
    return INDEX_HTML


# --------------------------------------------------------------------------
# HTTP server
# --------------------------------------------------------------------------

GET_ROUTES = {"/", "/api/status"}
POST_ROUTES = {"/api/set", "/api/enable", "/api/stop", "/api/disable"}


class UnitWebUiServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr, handler_cls, state, can_sock, can_lock, logger):
        super().__init__(addr, handler_cls)
        self.app_state = state
        self.can_sock = can_sock
        self.can_lock = can_lock
        self.logger = logger


class Handler(BaseHTTPRequestHandler):
    server_version = "UnitWebUI/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass  # keep stdout limited to our own WEBUI/VCP/CAN log lines

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def do_GET(self):
        if self.path == "/":
            self._send_html(render_index_html())
        elif self.path == "/api/status":
            self._send_json(build_status_json(self.server.app_state))
        else:
            self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        state = self.server.app_state
        can_sock = self.server.can_sock
        can_lock = self.server.can_lock
        logger = self.server.logger

        # Any command from the browser counts as a dead-man heartbeat, not
        # just /api/status polls.
        with state.lock:
            state.last_poll_time = time.monotonic()

        if self.path == "/api/set":
            body = self._read_json_body()
            result = handle_set(state, body)
            self._send_json(result, status=200 if result.get("ok") else 400)
        elif self.path == "/api/enable":
            result, status = handle_enable(state, can_sock, can_lock, logger)
            self._send_json(result, status=status)
        elif self.path == "/api/stop":
            result = handle_stop(state, can_sock, can_lock, logger)
            self._send_json(result)
        elif self.path == "/api/disable":
            result = handle_disable(state, can_sock, can_lock, logger)
            self._send_json(result, status=200 if result.get("ok") else 500)
        else:
            self._send_json({"error": "not found"}, status=404)


# --------------------------------------------------------------------------
# Server bring-up / shutdown
# --------------------------------------------------------------------------


def run_server(args):
    state = AppState()
    can_lock = threading.Lock()
    can_sock = open_can_socket(args.can_iface)
    logger = WebUiLogger(default_log_path())
    atexit.register(emergency_disable, args.can_iface)

    stop_event = threading.Event()
    tx_thread = threading.Thread(
        target=can_tx_loop, args=(stop_event, state, can_sock, can_lock), daemon=True
    )
    vcp_thread = threading.Thread(
        target=vcp_rx_loop, args=(stop_event, state, logger, args.vcp_port, args.vcp_baud), daemon=True
    )
    can_rx_thread = threading.Thread(
        target=can_status_rx_loop,
        args=(stop_event, state, logger, args.can_iface), daemon=True,
    )
    deadman_thread = threading.Thread(
        target=deadman_loop, args=(stop_event, state, can_sock, can_lock, logger), daemon=True
    )
    tx_thread.start()
    vcp_thread.start()
    can_rx_thread.start()
    deadman_thread.start()

    server = UnitWebUiServer(("", args.port), Handler, state, can_sock, can_lock, logger)
    logger.write(
        "WEBUI",
        f"listening on :{args.port} can_iface={args.can_iface} vcp_port={args.vcp_port}",
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.write("WEBUI", "interrupted by Ctrl-C")
    finally:
        stop_event.set()
        try:
            with can_lock:
                send_unit_ctrl(can_sock, False)
                send_unit_ctrl(can_sock, False)
            logger.write("WEBUI", "disable sent (shutdown)")
        except OSError as exc:
            logger.write("WEBUI", f"ERROR: shutdown disable send failed: {exc}")
        server.server_close()
        tx_thread.join(timeout=1.0)
        vcp_thread.join(timeout=1.0)
        can_rx_thread.join(timeout=1.0)
        can_sock.close()
        logger.close()
    return 0


# --------------------------------------------------------------------------
# --check: offline self-check (no CAN/serial, no server bind)
# --------------------------------------------------------------------------


def run_self_check():
    errors = []

    html = render_index_html()
    if not isinstance(html, str) or len(html) < 500:
        errors.append("render_index_html() produced unexpectedly short output")
    required_snippets = [
        "/api/status", "/api/set", "/api/enable", "/api/stop", "/api/disable",
        "steer_deg", "wheel_rpm", "steer_rate_dps", "steer_accel_dps2",
        "steer_decel_dps2",
        "trajectory_time_scale",
        "wheel_accel_rpm_per_s", "wheel_decel_rpm_per_s",
        "vector_pad", "vector_tip", "applyVectorCommand", "scheduleVectorCommand",
        "pointermove", "ArrowLeft",
        "wheel_axis_max_planned_rpm",
        "min=\"0\" max=\"360\"", "min=\"-1360\" max=\"1360\"", "min=\"0\" max=\"240\"",
        "min=\"30\" max=\"3600\"",
    ]
    for snippet in required_snippets:
        if snippet not in html:
            errors.append(f"HTML missing expected reference: {snippet!r}")

    expected_get = {"/", "/api/status"}
    expected_post = {"/api/set", "/api/enable", "/api/stop", "/api/disable"}
    if GET_ROUTES != expected_get:
        errors.append(f"GET_ROUTES mismatch: {GET_ROUTES}")
    if POST_ROUTES != expected_post:
        errors.append(f"POST_ROUTES mismatch: {POST_ROUTES}")

    # Telemetry parser sanity check against a realistic sample line.
    sample = (
        "run=1 step=0 angle=315352 target=315352 err=0 steer=0 "
        "m1=3762/171875 i1=74 q1=70 t1=29 m2=-3748/-171875 i2=-158 q2=-150 t2=28 "
        "steerMode=5/12 iSteer=3 sInt=12500 driveMode=171875/197789 "
        "iDrive=2 dInt=200000 mov=1 onset=0 onsetN=3 floor=1 "
        "ffS=5000 scale=0 wheel=500000"
    )
    parsed = parse_telemetry_line(sample)
    if parsed is None or parsed[0] != "telemetry":
        errors.append("parse_telemetry_line() failed on sample telemetry line")
    else:
        fields = parsed[1]
        summary = summarize_telemetry(fields)
        checks = {
            "angle_deg": 315.352,
            "target_deg": 315.352,
            "err_deg": 0.0,
            "i1": 74,
            "i2": -158,
            "q1": 70,
            "q2": -150,
            "t1": 29,
            "t2": 28,
            "ffs_rpm": 5.0,
            "steer_integral": 12.5,
            "drive_integral": 200.0,
            "drive_in_motion": 1,
            "drive_onset_active": 0,
            "drive_onset_count": 3,
            "drive_integral_floor_active": 1,
            "torque_scaling_active": 0,
        }
        for key, expected in checks.items():
            got = summary.get(key)
            if got is None or abs(got - expected) > 1e-6:
                errors.append(f"summarize_telemetry()[{key}] = {got!r}, expected {expected!r}")
        expected_wheel = (197789 / 1000.0) * WHEEL_GEAR_RATIO
        got_wheel = summary.get("wheel_rpm_actual")
        if got_wheel is None or abs(got_wheel - expected_wheel) > 1e-6:
            errors.append(f"summarize_telemetry()[wheel_rpm_actual] = {got_wheel!r}, expected {expected_wheel!r}")

    stop_parsed = parse_telemetry_line("STOP: overcurrent")
    if stop_parsed != ("stop", "overcurrent"):
        errors.append(f"parse_telemetry_line() STOP-line parse failed: {stop_parsed!r}")

    # Config clamping / partial update sanity check (no CAN/serial involved).
    state = AppState()
    r = handle_set(state, {
        "steer_deg": 999,
        "wheel_rpm": -9999,
        "steer_rate_dps": 9999,
        "steer_accel_dps2": 99999,
        "steer_decel_dps2": 99999,
        "wheel_accel_rpm_per_s": 99999,
        "wheel_decel_rpm_per_s": -1,
        "trajectory_time_scale": 99,
    })
    if not r.get("ok"):
        errors.append(f"handle_set() clamping check failed: {r}")
    else:
        if state.steer_deg != STEER_DEG_MAX:
            errors.append(f"steer_deg clamp failed: {state.steer_deg}")
        if state.wheel_rpm != WHEEL_RPM_MIN:
            errors.append(f"wheel_rpm clamp failed: {state.wheel_rpm}")
        if state.steer_rate_dps != STEER_RATE_DPS_MAX:
            errors.append(f"steer_rate_dps clamp failed: {state.steer_rate_dps}")
        if state.steer_accel_dps2 != STEER_ACCEL_DPS2_MAX:
            errors.append(f"steer_accel_dps2 clamp failed: {state.steer_accel_dps2}")
        if state.steer_decel_dps2 != STEER_DECEL_DPS2_MAX:
            errors.append(f"steer_decel_dps2 clamp failed: {state.steer_decel_dps2}")
        if state.wheel_accel_rpm_per_s != WHEEL_ACCEL_RPM_PER_S_MAX:
            errors.append(
                f"wheel_accel_rpm_per_s clamp failed: {state.wheel_accel_rpm_per_s}")
        if state.wheel_decel_rpm_per_s != WHEEL_DECEL_RPM_PER_S_MIN:
            errors.append(
                f"wheel_decel_rpm_per_s clamp failed: {state.wheel_decel_rpm_per_s}")
        if state.trajectory_time_scale != TRAJECTORY_TIME_SCALE_MAX:
            errors.append(
                f"trajectory_time_scale clamp failed: {state.trajectory_time_scale}")

    # Wheel reversal must decelerate to exactly zero before any command with
    # the opposite sign, and must use the configured slower decel slope.
    wheel_rpm = 1000.0
    wheel_samples = []
    reversal_check_steps = math.ceil(4.0 * TARGET_HZ)
    for _ in range(reversal_check_steps):
        previous_wheel_rpm = wheel_rpm
        wheel_rpm = profile_wheel_step(
            wheel_rpm, -1000.0,
            WHEEL_ACCEL_RPM_PER_S_DEFAULT,
            WHEEL_DECEL_RPM_PER_S_DEFAULT,
            1.0 / TARGET_HZ,
        )
        wheel_samples.append(wheel_rpm)
        if previous_wheel_rpm > 0.0 and abs(wheel_rpm - previous_wheel_rpm) > (
                WHEEL_DECEL_RPM_PER_S_DEFAULT / TARGET_HZ + 1e-6):
            errors.append("profile_wheel_step() exceeded reversal decel slope")
            break
    try:
        zero_index = wheel_samples.index(0.0)
    except ValueError:
        errors.append("profile_wheel_step() reversal did not pass through zero")
        zero_index = -1
    if zero_index >= 0 and any(v < 0.0 for v in wheel_samples[:zero_index]):
        errors.append("profile_wheel_step() crossed sign before zero sample")
    if abs(wheel_samples[-1] + 1000.0) > 1e-6:
        errors.append(
            f"profile_wheel_step() did not reach reversed target: {wheel_samples[-1]}")

    # A 90deg move at the UI's maximum requested speed must form a smooth
    # triangular/trapezoidal profile: respect velocity/acceleration limits,
    # settle at the destination, and reduce FF before arrival.
    position_mdeg = 0.0
    velocity_dps = 0.0
    velocities = []
    dt_s = 1.0 / TARGET_HZ
    steer_check_steps = math.ceil(2.0 * TARGET_HZ)
    for _ in range(steer_check_steps):
        previous_velocity = velocity_dps
        position_mdeg, velocity_dps = profile_steer_step(
            position_mdeg, 90000.0, velocity_dps,
            STEER_RATE_DPS_MAX, STEER_ACCEL_DPS2_DEFAULT,
            STEER_DECEL_DPS2_DEFAULT, dt_s)
        velocities.append(abs(velocity_dps))
        speeding_up = (velocity_dps * previous_velocity >= 0.0
                       and abs(velocity_dps) > abs(previous_velocity))
        expected_limit = (STEER_ACCEL_DPS2_DEFAULT if speeding_up
                          else STEER_DECEL_DPS2_DEFAULT)
        if abs(velocity_dps - previous_velocity) > expected_limit * dt_s + 1e-6:
            errors.append("profile_steer_step() exceeded accel/decel limit")
            break
    if abs(shortest_diff_mdeg(90000.0, position_mdeg)) > 0.01 or abs(velocity_dps) > 0.001:
        errors.append(
            "profile_steer_step() did not settle at 90deg: "
            f"position={position_mdeg}, velocity={velocity_dps}")
    if max(velocities, default=0.0) > STEER_RATE_DPS_MAX + 1e-6:
        errors.append("profile_steer_step() exceeded rate limit")
    peak_index = velocities.index(max(velocities)) if velocities else 0
    if not any(0.0 < v < velocities[peak_index] for v in velocities[peak_index + 1:]):
        errors.append("profile_steer_step() did not ramp FF down before arrival")

    # The target generator must use the same wheel/steer rpm envelope as the
    # firmware, rather than merely warning about an impossible combination.
    if abs(steer_rate_available_dps(0.0) - 240.0) > 1e-6:
        errors.append("steer envelope at wheel=0 should hit the 240deg/s software cap")
    high_wheel_rate = steer_rate_available_dps(1300.0, MOTOR_MAX_RPM)
    expected_high_wheel_rate = (
        (MOTOR_MAX_RPM - 1300.0 / WHEEL_GEAR_RATIO)
        * STEER_GEAR_RATIO * 6.0
    )
    if abs(high_wheel_rate - expected_high_wheel_rate) > 1e-6:
        errors.append(
            "steer envelope at wheel=1300 is wrong: "
            f"got {high_wheel_rate}, expected {expected_high_wheel_rate}")
    combined_motor_rpm = (
        1300.0 / WHEEL_GEAR_RATIO
        + (high_wheel_rate / 6.0) / STEER_GEAR_RATIO
    )
    if combined_motor_rpm > MOTOR_MAX_RPM + 1e-6:
        errors.append("steer envelope permits motor rpm budget overflow")
    if steer_rate_available_dps(1300.0) != 0.0:
        errors.append("planned 10% motor reserve should leave no steer budget at wheel=1300")
    planned_rates = [steer_rate_available_dps(rpm) for rpm in (0.0, 600.0, 1200.0)]
    if not (planned_rates[0] >= planned_rates[1] >= planned_rates[2]):
        errors.append(
            f"planned steer envelope must decrease with wheel rpm: {planned_rates}")

    expected_90deg_min_s = (
        STEER_RATE_DPS_MAX / STEER_ACCEL_DPS2_DEFAULT
        + (90.0
           - STEER_RATE_DPS_MAX ** 2 / (2.0 * STEER_ACCEL_DPS2_DEFAULT)
           - STEER_RATE_DPS_MAX ** 2 / (2.0 * STEER_DECEL_DPS2_DEFAULT))
        / STEER_RATE_DPS_MAX
        + STEER_RATE_DPS_MAX / STEER_DECEL_DPS2_DEFAULT)
    got_90deg_min_s = steer_profile_min_time_s(
        90.0, STEER_RATE_DPS_MAX,
        STEER_ACCEL_DPS2_DEFAULT, STEER_DECEL_DPS2_DEFAULT)
    if abs(got_90deg_min_s - expected_90deg_min_s) > 1e-9:
        errors.append(
            f"90deg theoretical time wrong: {got_90deg_min_s} vs {expected_90deg_min_s}")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("PASS")
    return 0


# --------------------------------------------------------------------------
# argparse wiring
# --------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="unit_web_ui.py",
        description=(
            "Browser test UI for a single differential-steer unit (unitId=1) "
            "over SocketCAN + VCP debug log. See module docstring for the "
            "CAN/telemetry spec and safety notes."
        ),
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--port", type=int, default=8080, help="HTTP port (default: 8080)")
    parser.add_argument("--can-iface", default="can0", help="SocketCAN interface (default: can0)")
    parser.add_argument(
        "--vcp-port", default="/dev/ttyACM0", help="VCP serial device (default: /dev/ttyACM0)"
    )
    parser.add_argument("--vcp-baud", type=int, default=115200, help="VCP baud rate (default: 115200)")
    parser.add_argument(
        "--check", action="store_true",
        help="Offline self-check only: verify HTML generation and routing table "
        "consistency, without opening CAN or serial or binding a port. Prints "
        "PASS/FAIL and exits.",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.check:
        return run_self_check()
    try:
        return run_server(args)
    except OSError as exc:
        print(f"[unit_web_ui] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
