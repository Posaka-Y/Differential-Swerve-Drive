#!/usr/bin/env python3
"""unit_web_ui.py - Browser-based manual test UI for a single differential-steer
unit (unitId=1, Linux mini PC, can0 + VCP debug log).

Single file, stdlib + pyserial only (no python-can, no web framework). Serves
a dark, offline-only HTML/JS page (no external CDN/fonts) with sliders for
steer angle / wheel speed / steer rate, Enable/STOP/Disable buttons, and a
live telemetry readout, backed by a tiny JSON API.

CAN socket handling (SocketCAN AF_CAN/SOCK_RAW/CAN_RAW, struct "=IB3x8s") and
the VCP serial capture pattern are copied from tools/linux/unit_bench.py --
see that file for the detailed CAN message spec comments. This file
intentionally keeps its own copies rather than importing from unit_bench.py,
so it can be read and modified standalone.

CAN message spec (unitId=1):

    SET_TARGET     ID 0x101  DLC 8  int32 LE steer_mdeg, int32 LE wheel_rpm_milli
                   Sent unconditionally at 50Hz for as long as this server runs
                   (independent of enabled state -- the firmware only acts on
                   it while enabled, but keeping it flowing means enable can
                   happen at any time without a stale target).
    SET_TARGET_FF  ID 0x111  DLC 8  int32 LE steer_rate_mdeg_per_s, int32 LE 0
                   Sent immediately before SET_TARGET each cycle whenever the
                   commanded steer rate (omega_s) is nonzero.
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
  2. STOP first commands wheel=0 / steer_rate=0 and keeps sending SET_TARGET
     for 1.0s (to let the wheel decelerate under closed-loop control) before
     sending UNIT_CTRL disable -- disabling while the wheel is still fast
     would leave it coasting uncontrolled.
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

ENABLE_PAYLOAD = bytes([0x01, 0x01])
DISABLE_PAYLOAD = bytes([0x01, 0x00])

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = REPO_ROOT / "firmware" / "logs"

# classic (non-FD) SocketCAN frame: struct can_frame { u32 can_id; u8 can_dlc;
# u8 pad[3]; u8 data[8]; }
CAN_FRAME_FMT = "=IB3x8s"
CAN_FRAME_SIZE = struct.calcsize(CAN_FRAME_FMT)

TARGET_HZ = 50.0
DEADMAN_TIMEOUT_S = 3.0
STOP_COAST_S = 1.0

STEER_DEG_MIN, STEER_DEG_MAX = 0.0, 360.0
WHEEL_RPM_MIN, WHEEL_RPM_MAX = -1360.0, 1360.0
STEER_RATE_DPS_MIN, STEER_RATE_DPS_MAX = 0.0, 240.0

WHEEL_GEAR_RATIO = 32.0 / 11.0


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
    t1 = scalar("t1")
    t2 = scalar("t2")
    ffs = scalar("ffS")

    wheel_rpm_actual = None
    drive_mode = fields.get("driveMode")
    if isinstance(drive_mode, tuple) and len(drive_mode) == 2:
        wheel_rpm_actual = (drive_mode[1] / 1000.0) * WHEEL_GEAR_RATIO

    return {
        "angle_deg": angle / 1000.0 if angle is not None else None,
        "target_deg": target / 1000.0 if target is not None else None,
        "err_deg": err / 1000.0 if err is not None else None,
        "wheel_rpm_actual": wheel_rpm_actual,
        "ffs_rpm": ffs / 1000.0 if ffs is not None else None,
        "i1": i1,
        "i2": i2,
        "t1": t1,
        "t2": t2,
        # Present only on "idle" lines: firmware-side start-condition health
        # (fdbkOk=0 means no C620 feedback -> enable will silently not start,
        # typically the 24V motor power is off).
        "fdbk_ok": scalar("fdbkOk"),
        "amt_ok": scalar("amtOk"),
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

        # Internally ramped steer target actually transmitted in SET_TARGET,
        # in mdeg (float, wrapped into [0, 360000)). Equals steer_deg*1000
        # whenever steer_rate_dps == 0; otherwise advances by
        # steer_rate_dps*1000*dt each tx cycle.
        self.effective_steer_mdeg = 0.0

        self.enabled = False

        self.telemetry = None       # last parsed fields dict, or None
        self.telemetry_raw = None   # last raw VCP line
        self.telemetry_time = None  # time.monotonic() of last telemetry line

        self.last_stop_reason = None

        # Updated on every GET /api/status; the dead-man watchdog trips if
        # this goes stale for more than DEADMAN_TIMEOUT_S while enabled.
        self.last_poll_time = None


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def mod_360000(mdeg):
    return mdeg % 360000.0


# --------------------------------------------------------------------------
# CAN tx thread: unconditional 50Hz SET_TARGET (+ SET_TARGET_FF when steering)
# --------------------------------------------------------------------------


def shortest_diff_mdeg(a, b):
    """Shortest signed angular difference a-b in mdeg, in [-180000, 180000)."""
    return (a - b + 180000.0) % 360000.0 - 180000.0


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
            # steer_rate_dps is the approach speed toward the steer_deg
            # destination: the effective target slews toward it (shortest
            # path) at this rate and stops on arrival, with SET_TARGET_FF
            # sent only while moving. Rate 0 means the destination was
            # snapped directly by /api/set (fastest, firmware clamps govern).
            rate_dps = abs(state.steer_rate_dps)
            ff_mdeg_s = 0
            if rate_dps > 0.0:
                dest_mdeg = mod_360000(state.steer_deg * 1000.0)
                diff = shortest_diff_mdeg(dest_mdeg, state.effective_steer_mdeg)
                step = rate_dps * 1000.0 * dt
                if abs(diff) <= step:
                    state.effective_steer_mdeg = dest_mdeg  # arrived: FF=0
                else:
                    direction = 1.0 if diff > 0.0 else -1.0
                    advanced = mod_360000(
                        state.effective_steer_mdeg + direction * step)
                    telem = state.telemetry
                    telem_fresh = (
                        telem is not None
                        and isinstance(telem.get("angle"), (int, float))
                        and (now - state.telemetry_time) < LEASH_TELEMETRY_MAX_AGE_S
                    )
                    if telem_fresh:
                        lead = shortest_diff_mdeg(advanced, float(telem["angle"]))
                        if lead > TARGET_LEASH_MDEG and direction > 0.0:
                            advanced = mod_360000(
                                float(telem["angle"]) + TARGET_LEASH_MDEG)
                        elif lead < -TARGET_LEASH_MDEG and direction < 0.0:
                            advanced = mod_360000(
                                float(telem["angle"]) - TARGET_LEASH_MDEG)
                    state.effective_steer_mdeg = advanced
                    ff_mdeg_s = int(round(direction * rate_dps * 1000.0))
            steer_mdeg = int(round(state.effective_steer_mdeg))
            wheel_rpm_milli = int(round(state.wheel_rpm * 1000.0))

        try:
            with can_lock:
                if ff_mdeg_s != 0:
                    send_set_target_ff(can_sock, ff_mdeg_s, 0)
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
                        state.last_stop_reason = payload
                        # Firmware latches itself to disabled on STOP; mirror
                        # that so the UI/dead-man logic stay consistent.
                        state.enabled = False
                    elif "angle" in payload:
                        # Only run=/idle lines carry the AMT angle; RX echo
                        # lines (SET_TARGET_RX etc.) must not replace the
                        # telemetry snapshot or enable-seeding loses the angle.
                        state.telemetry = payload
                        state.telemetry_raw = text
                        state.telemetry_time = now
    finally:
        ser.close()


# --------------------------------------------------------------------------
# STOP sequence / dead-man watchdog
# --------------------------------------------------------------------------


def perform_stop_sequence(state, can_sock, can_lock, logger, reason):
    """omega_w=0, omega_s=0 -> keep sending SET_TARGET for STOP_COAST_S
    (deceleration under closed-loop control) -> UNIT_CTRL disable.

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
        logger.write("WEBUI", f"STOP sequence start ({reason}): coasting {STOP_COAST_S}s before disable")
        time.sleep(STOP_COAST_S)
        try:
            with can_lock:
                send_unit_ctrl(can_sock, False)
                send_unit_ctrl(can_sock, False)
        except OSError as exc:
            logger.write("WEBUI", f"ERROR: STOP disable send failed: {exc}")
        with state.lock:
            state.enabled = False
            state.last_stop_reason = reason
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
            updated["steer_deg"] = v
        if "wheel_rpm" in body:
            try:
                v = clamp(float(body["wheel_rpm"]), WHEEL_RPM_MIN, WHEEL_RPM_MAX)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid wheel_rpm"}
            state.wheel_rpm = v
            updated["wheel_rpm"] = v
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
        state.steer_deg = state.effective_steer_mdeg / 1000.0
        seeded_mdeg = int(round(state.effective_steer_mdeg))
        wheel_milli = int(round(state.wheel_rpm * 1000.0))
        # Reset the dead-man heartbeat: without this, enabling after an idle
        # browser gap trips the watchdog on the very same cycle.
        state.last_poll_time = time.monotonic()
        state.enabled = True
        state.last_stop_reason = None
    try:
        with can_lock:
            # The firmware latches the last received SET_TARGET at START; the
            # 50Hz tx thread may not have sent the seeded angle yet, so land
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
        state.enabled = False
        state.last_stop_reason = "manual DISABLE (emergency, no coast)"
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
        }
        effective_steer_deg = state.effective_steer_mdeg / 1000.0
        enabled = state.enabled
        last_stop_reason = state.last_stop_reason
        telem = state.telemetry
        telem_raw = state.telemetry_raw
        telem_time = state.telemetry_time

    telemetry_json = None
    if telem is not None:
        telemetry_json = summarize_telemetry(telem)
        telemetry_json["raw_line"] = telem_raw
        telemetry_json["age_s"] = round(now_mono - telem_time, 3) if telem_time is not None else None

    # Feasibility envelope: the two motors share the motor_max_rpm budget,
    # |steer_mode| + |drive_mode| <= 469 with steer priority in the firmware
    # (wheel gets cut). steer axis rpm = 0.7273 * mode, wheel = 2.909 * mode,
    # steer axis further capped at 40rpm (=240deg/s) by steer_max_rpm.
    MOTOR_MAX = 469.0
    DRIVE_RATIO = 32.0 / 11.0
    STEER_AXIS_PER_MODE = 8.0 / 11.0
    steer_mode_used = abs(cfg["steer_rate_dps"]) / 6.0 / STEER_AXIS_PER_MODE
    drive_mode_used = abs(cfg["wheel_rpm"]) / DRIVE_RATIO
    steer_rate_avail_dps = min(
        240.0,
        max(0.0, (MOTOR_MAX - drive_mode_used) * STEER_AXIS_PER_MODE * 6.0),
    )
    wheel_avail_rpm = max(0.0, (MOTOR_MAX - steer_mode_used) * DRIVE_RATIO)

    return {
        "config": cfg,
        "effective_steer_deg": round(effective_steer_deg, 3),
        "enabled": enabled,
        "last_stop_reason": last_stop_reason,
        "telemetry": telemetry_json,
        "envelope": {
            "steer_rate_avail_dps": round(steer_rate_avail_dps, 1),
            "wheel_avail_rpm": round(wheel_avail_rpm, 1),
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
</style>
</head>
<body>
<h1>Unit Web UI (unitId=1, can0)</h1>
<div class="safety">
  <strong>安全注意:</strong> Enable前に必ずホイールを浮かせる/自由回転できる状態にすること。
  STOPボタンはwheel/steerを0へ指令してから1秒間送信を継続し(減速待ち)、その後disableを送信する
  (disableをいきなり送ると空走してカップリングする恐れがあるため)。Disableボタンは待たずに
  即disableする緊急停止用。
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
    <label for="steer_rate_dps_range">&omega;s approach speed to &theta;s (deg/s, 0 = instant step)</label>
    <input type="range" id="steer_rate_dps_range" min="0" max="240" step="5" value="0"
           oninput="onFieldInput('steer_rate_dps', this.value)">
    <input type="number" id="steer_rate_dps_num" min="0" max="240" step="5" value="0"
           onchange="onFieldInput('steer_rate_dps', this.value)">
    <button class="zero" onclick="zeroField('steer_rate_dps')">steer_rate=0</button>
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
    <tr><td class="k">Angle (firmware, actual)</td><td id="st_angle">--</td></tr>
    <tr><td class="k">Angle error</td><td id="st_err">--</td></tr>
    <tr><td class="k">Wheel actual (rpm)</td><td id="st_wheel">--</td></tr>
    <tr><td class="k">ffS (steer-rate FF, rpm units)</td><td id="st_ffs">--</td></tr>
    <tr><td class="k">i1 / i2 (commanded current, raw)</td><td id="st_i1i2">--</td></tr>
    <tr><td class="k">t1 / t2 (temperature)</td><td id="st_t1t2">--</td></tr>
    <tr><td class="k">Telemetry age</td><td id="st_age">--</td></tr>
    <tr><td class="k">Last STOP reason</td><td id="st_stop_reason">--</td></tr>
    <tr><td class="k">&omega;s available (at current &omega;w)</td><td id="st_env_ws">--</td></tr>
    <tr><td class="k">&omega;w available (at current &omega;s)</td><td id="st_env_ww">--</td></tr>
    <tr><td class="k">C620 feedback (idle check)</td><td id="st_fdbk">--</td></tr>
  </table>
  <div class="raw" id="st_raw"></div>
</div>

<script>
const STATUS_URL = "/api/status";
const SET_URL = "/api/set";

let debounceTimers = {};

function postSet(payload) {
  fetch(SET_URL, {
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
    document.getElementById("st_effective_target").textContent = fmt(data.effective_steer_deg, 2) + " deg";
    document.getElementById("st_stop_reason").textContent = data.last_stop_reason || "--";

    if (data.envelope) {
      const wsAvail = data.envelope.steer_rate_avail_dps;
      const wwAvail = data.envelope.wheel_avail_rpm;
      const wsEl = document.getElementById("st_env_ws");
      const wwEl = document.getElementById("st_env_ww");
      wsEl.textContent = fmt(wsAvail, 0) + " deg/s";
      wwEl.textContent = fmt(wwAvail, 0) + " rpm";
      // Highlight when the current request exceeds the feasible envelope
      // (the two motors share the 469rpm budget; firmware cuts wheel first,
      // and the server-side target leash prevents the divergence STOP).
      wsEl.style.color = Math.abs(data.config.steer_rate_dps) > wsAvail ? "#ff6b6b" : "";
      wwEl.style.color = Math.abs(data.config.wheel_rpm) > wwAvail ? "#ff6b6b" : "";
    }

    const t = data.telemetry;
    if (t) {
      document.getElementById("st_angle").textContent = fmt(t.angle_deg, 2) + " deg";
      document.getElementById("st_err").textContent = fmt(t.err_deg, 2) + " deg";
      document.getElementById("st_wheel").textContent = fmt(t.wheel_rpm_actual, 1) + " rpm";
      document.getElementById("st_ffs").textContent = fmt(t.ffs_rpm, 1) + " rpm";
      document.getElementById("st_i1i2").textContent = fmt(t.i1, 0) + " / " + fmt(t.i2, 0);
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
      ["st_angle", "st_err", "st_wheel", "st_ffs", "st_i1i2", "st_t1t2", "st_age"].forEach(function (id) {
        document.getElementById(id).textContent = "--";
      });
      document.getElementById("st_raw").textContent = "";
    }
  }).catch(function () {
    document.getElementById("st_enabled").textContent = "poll error";
  });
}

setInterval(refreshStatus, 200);
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
    deadman_thread = threading.Thread(
        target=deadman_loop, args=(stop_event, state, can_sock, can_lock, logger), daemon=True
    )
    tx_thread.start()
    vcp_thread.start()
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
        "steer_deg", "wheel_rpm", "steer_rate_dps",
        "min=\"0\" max=\"360\"", "min=\"-1360\" max=\"1360\"", "min=\"0\" max=\"240\"",
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
        "m1=3762/171875 i1=74 t1=29 m2=-3748/-171875 i2=-158 t2=28 "
        "steerMode=5/12 iSteer=3 driveMode=171875/197789 iDrive=2 "
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
            "t1": 29,
            "t2": 28,
            "ffs_rpm": 5.0,
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
    r = handle_set(state, {"steer_deg": 999, "wheel_rpm": -9999, "steer_rate_dps": 9999})
    if not r.get("ok"):
        errors.append(f"handle_set() clamping check failed: {r}")
    else:
        if state.steer_deg != STEER_DEG_MAX:
            errors.append(f"steer_deg clamp failed: {state.steer_deg}")
        if state.wheel_rpm != WHEEL_RPM_MIN:
            errors.append(f"wheel_rpm clamp failed: {state.wheel_rpm}")
        if state.steer_rate_dps != STEER_RATE_DPS_MAX:
            errors.append(f"steer_rate_dps clamp failed: {state.steer_rate_dps}")

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
