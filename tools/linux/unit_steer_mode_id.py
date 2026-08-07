#!/usr/bin/env python3
"""Identify the steer-mode velocity loop with the outer angle loop disabled.

The script uses the existing SET_TARGET_FF input as a direct steer-axis speed
command after temporarily setting both outer-loop angle gains to zero.  Motor
speed is captured from STATUS2 on the central CAN, avoiding high-rate blocking
UART output.  All changed runtime parameters are restored and the unit is
disabled on every normal/error/interrupt exit.
"""

import argparse
import atexit
import csv
import json
import math
import select
import socket
import struct
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import serial
except ImportError:  # pragma: no cover - reported cleanly before hardware use
    serial = None

from unit_bench import (
    CAN_FRAME_SIZE,
    emergency_disable,
    open_can_socket,
    parse_can_frame,
    send_set_config,
    send_set_target,
    send_set_target_ff,
    send_unit_ctrl,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "firmware" / "logs" / "steer-mode-id"
STATUS1_ID = 0x181
STATUS2_ID = 0x191
STATUS3_ID = 0x1A1
STATUS_FLAG_ACTIVE = 1 << 0
STATUS_FLAG_FEEDBACK_OK = 1 << 2
BUS_VOLTAGE_UNAVAILABLE_MV = 0xFFFF
HIGH_SPEED_MONITOR_THRESHOLD_RPM = 260.0
UNMONITORED_MAX_DECEL_RPM_S = 500.0
M3508_REDUCTION = 19.0
STEER_RATIO = 8.0 / 11.0
# Paces this tool's own wheel target ramps (spin-up before excitation,
# spin-down before disable). Matches unit_web_ui.py's WHEEL_DECEL_RPM_PER_S_DEFAULT.
WHEEL_DECEL_RPM_PER_S = 500.0

# Values flashed as of 2026-07-31. The ID setup is deliberately complete so a
# stale SET_CONFIG value from a previous bench run cannot leak into a trial.
RESTORE_CONFIG = {
    3: 120.0,      # steer mode Kp
    4: 50.0,       # steer mode Ki
    5: 4.0,        # hold angle Kp
    7: 60.0,       # accepted steer-axis commissioning max rpm
    8: 0.0,        # steer-axis minimum rpm
    9: 600.0,      # local steer-axis acceleration rpm/s
    13: 0.002,     # mode-speed LPF tau
    18: 0.5,       # acceleration FF gain
    19: 1.0,       # moving angle Kp
    20: 0.5,       # deceleration FF gain
    21: 200.0,     # steer friction FF (wheel-tapered in unit_controller.c)
    22: 0.0,       # high-rate STATUS2 disabled
    23: 0.050,     # complementary steer observer AMT correction tau
    24: 10.0,      # adopted observer-speed friction FF fade threshold
    25: 0.0,       # steer back-calculation gain
    26: 0.0,       # drive back-calculation gain
    47: 1.0,       # braking-only steer Kp multiplier
}


def parse_idle_angle(port, baud, timeout_s):
    if serial is None:
        raise RuntimeError("pyserial is required to read the safe seed angle")
    deadline = time.monotonic() + timeout_s
    with serial.Serial(port, baud, timeout=0.2) as stream:
        stream.reset_input_buffer()
        while time.monotonic() < deadline:
            line = stream.readline().decode("ascii", errors="replace").strip()
            if not line.startswith("idle "):
                continue
            for token in line.split():
                if token.startswith("angle="):
                    return int(token.split("=", 1)[1])
    raise RuntimeError(f"no idle angle received from {port} within {timeout_s:.1f}s")


def ensure_web_ui_stopped(web_url, timeout_s):
    """Refuse command-source contention before becoming the CAN target owner."""
    if web_url:
        try:
            with urllib.request.urlopen(
                    web_url.rstrip("/") + "/api/status",
                    timeout=min(timeout_s, 2.0)) as response:
                json.load(response)
        except (OSError, ValueError):
            pass
        else:
            raise RuntimeError(
                "Web UI is running and would overwrite identification targets; "
                "stop unit_web_ui.py before this test")


def read_seed_angle_from_can(sock, timeout_s):
    """Read a fresh disabled-unit angle from STATUS1, not buffered VCP text."""
    drain_socket(sock)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        readable, _, _ = select.select([sock], [], [], 0.1)
        if not readable:
            continue
        feedback = receive_feedback(sock)
        if feedback is not None and feedback[0] == "status1":
            return feedback[1][0]
    raise RuntimeError(f"no fresh STATUS1 angle within {timeout_s:.1f}s")


def apply_config(sock, values):
    for index, value in values.items():
        send_set_config(sock, index, value)
        time.sleep(0.012)


def step_command(elapsed, amplitude_rpm, pulse_s, zero_s, decel_rpm_s,
                 direction="both"):
    # A zero phase includes enough time to ramp the preceding command to zero,
    # followed by the requested zero-speed dwell.  Without this extension a
    # short --zero-s can end the test (or start the reverse pulse) while the
    # rotor is still regenerating into the DC bus.
    brake_s = amplitude_rpm / decel_rpm_s
    if direction == "both":
        edges = (
            (zero_s, 0.0, "zero_pre"),
            (zero_s + pulse_s, amplitude_rpm, "positive"),
            (2.0 * zero_s + pulse_s + brake_s, 0.0, "zero_mid"),
            (2.0 * zero_s + 2.0 * pulse_s + brake_s,
             -amplitude_rpm, "negative"),
            (3.0 * zero_s + 2.0 * pulse_s + 2.0 * brake_s,
             0.0, "zero_post"),
        )
    else:
        sign = 1.0 if direction == "positive" else -1.0
        edges = (
            (zero_s, 0.0, "zero_pre"),
            (zero_s + pulse_s, sign * amplitude_rpm, direction),
            (2.0 * zero_s + pulse_s + brake_s, 0.0, "zero_post"),
        )
    for end, command, phase in edges:
        if elapsed < end:
            return command, phase
    return 0.0, "done"


def prbs_bits():
    """31-chip maximum-length sequence, followed by its inverse (zero bias)."""
    state = 0x1F
    first = []
    for _ in range(31):
        first.append(1.0 if state & 1 else -1.0)
        feedback = ((state >> 0) ^ (state >> 2)) & 1
        state = (state >> 1) | (feedback << 4)
    return first + [-value for value in first]


def command_for_time(pattern, elapsed, amplitude_rpm, pulse_s, zero_s,
                     chip_s, bits, decel_rpm_s, step_direction="both"):
    if pattern == "step":
        return step_command(
            elapsed, amplitude_rpm, pulse_s, zero_s, decel_rpm_s,
            step_direction)
    if elapsed < zero_s:
        return 0.0, "zero_pre"
    chip = int((elapsed - zero_s) / chip_s)
    if chip < len(bits):
        return amplitude_rpm * bits[chip], f"prbs_{chip}"
    brake_s = amplitude_rpm / decel_rpm_s
    if elapsed < zero_s + len(bits) * chip_s + brake_s + zero_s:
        return 0.0, "zero_post"
    return 0.0, "done"


def move_toward(value, target, maximum_delta):
    if value < target:
        return min(value + maximum_delta, target)
    return max(value - maximum_delta, target)


def slew_command(value, target, accel_rpm_s, decel_rpm_s, dt_s):
    """Apply independent acceleration and regenerative-braking limits.

    A sign reversal first ramps to zero using the deceleration limit.  The
    remaining part of that sample is intentionally not reused to accelerate
    in the opposite direction, keeping the transition conservative.
    """
    if value == target:
        return target
    if value * target < 0.0:
        target = 0.0
        rate = decel_rpm_s
    elif abs(target) < abs(value):
        rate = decel_rpm_s
    else:
        rate = accel_rpm_s
    return move_toward(value, target, max(0.0, rate * dt_s))


def total_duration(args, bits):
    brake_s = args.amplitude_rpm / args.steer_decel_rpm_s
    if args.pattern == "step":
        if args.step_direction != "both":
            return 2.0 * args.zero_s + args.pulse_s + brake_s
        return 3.0 * args.zero_s + 2.0 * args.pulse_s + 2.0 * brake_s
    return 2.0 * args.zero_s + len(bits) * args.chip_s + brake_s


def receive_feedback(sock):
    frame = sock.recv(CAN_FRAME_SIZE)
    can_id, data = parse_can_frame(frame)
    if can_id == STATUS1_ID and len(data) == 8:
        angle_mdeg, wheel_rpm_milli = struct.unpack("<ii", data)
        return "status1", (angle_mdeg, wheel_rpm_milli)
    if can_id == STATUS2_ID and len(data) == 8:
        motor1_milli, motor2_milli = struct.unpack("<ii", data)
        motor1_rotor_rpm = motor1_milli * 0.001
        motor2_rotor_rpm = motor2_milli * 0.001
        mode_rpm = (motor1_rotor_rpm + motor2_rotor_rpm) / (2.0 * M3508_REDUCTION)
        return "status2", (motor1_rotor_rpm, motor2_rotor_rpm, mode_rpm)
    if can_id == STATUS3_ID and len(data) == 8:
        bus_mv, status_flags, error_flags = struct.unpack("<HHI", data)
        return "status3", (bus_mv, status_flags, error_flags)
    return None


def drain_socket(sock):
    while True:
        try:
            sock.recv(CAN_FRAME_SIZE)
        except BlockingIOError:
            return


def step_metrics(rows, amplitude_axis_rpm):
    metrics = {}
    target_mode = amplitude_axis_rpm / STEER_RATIO
    for phase, sign in (("positive", 1.0), ("negative", -1.0)):
        samples = [row for row in rows if row["phase"] == phase]
        if not samples:
            metrics[phase] = {"samples": 0}
            continue
        start_t = samples[0]["time_s"]
        signed = [sign * row["measured_mode_rpm"] for row in samples]
        peak = max(signed)
        tail_start = start_t + 0.5 * (samples[-1]["time_s"] - start_t)
        tail = [sign * row["measured_mode_rpm"] for row in samples
                if row["time_s"] >= tail_start]
        rise_90 = next((row["time_s"] - start_t for row in samples
                        if sign * row["measured_mode_rpm"] >= 0.9 * target_mode), None)
        metrics[phase] = {
            "samples": len(samples),
            "target_mode_rpm": target_mode,
            "rise_90_s": rise_90,
            "peak_mode_rpm": peak,
            "overshoot_pct": 100.0 * max(0.0, peak - target_mode) / target_mode,
            "tail_mean_mode_rpm": sum(tail) / len(tail) if tail else math.nan,
            "tail_mae_rpm": (sum(abs(value - target_mode) for value in tail) / len(tail)
                             if tail else math.nan),
        }
    return metrics


def run(args):
    if not args.yes_wheel_lifted:
        raise RuntimeError("hardware motion refused: pass --yes-wheel-lifted")
    if args.amplitude_rpm <= 0.0 or args.amplitude_rpm > 300.0:
        raise RuntimeError("--amplitude-rpm must be in (0, 300]")
    if args.rate_hz < 50.0 or args.rate_hz > 500.0:
        raise RuntimeError("--rate-hz must be within 50..500")
    if args.wheel_rpm < 0.0 or args.wheel_rpm > 1360.0:
        raise RuntimeError("--wheel-rpm must be within 0..1360")
    if args.steer_accel_rpm_s <= 0.0 or args.steer_accel_rpm_s > 4000.0:
        raise RuntimeError("--steer-accel-rpm-s must be within (0, 4000]")
    if args.steer_decel_rpm_s <= 0.0 or args.steer_decel_rpm_s > 4000.0:
        raise RuntimeError("--steer-decel-rpm-s must be within (0, 4000]")
    if (args.amplitude_rpm > HIGH_SPEED_MONITOR_THRESHOLD_RPM
            and not args.yes_24v_monitored
            and args.steer_decel_rpm_s > UNMONITORED_MAX_DECEL_RPM_S):
        raise RuntimeError(
            f"steer speed above {HIGH_SPEED_MONITOR_THRESHOLD_RPM:.0f}rpm "
            "without an external 24V monitor requires "
            f"--steer-decel-rpm-s <= {UNMONITORED_MAX_DECEL_RPM_S:.0f}; "
            "connect a monitor and pass --yes-24v-monitored to test faster braking")
    if (args.amplitude_rpm > HIGH_SPEED_MONITOR_THRESHOLD_RPM
            and not args.yes_24v_monitored):
        print(
            "WARNING: 24V bus is not measured; using the unmonitored "
            f"deceleration ceiling {UNMONITORED_MAX_DECEL_RPM_S:.0f}rpm/s",
            file=sys.stderr,
        )

    tx = open_can_socket(args.can_iface)
    rx = open_can_socket(args.can_iface)
    rx.setblocking(False)
    cleanup = True
    wheel_rpm_milli = int(round(args.wheel_rpm * 1000))
    # Tracks the last wheel target actually sent, so the safety-net restore()
    # path (atexit / exceptions / Ctrl-C) knows whether it needs to ramp down
    # before disabling. Sending UNIT_CTRL disable while the wheel is still at
    # speed cuts current immediately (no controlled deceleration) and
    # regenerates a DC-bus voltage spike -- confirmed the hard way on
    # 2026-07-31 with unit_bench.py's old unconditional-disable behavior; see
    # firmware/PROGRESS.md and docs/ARCHITECTURE_DECISIONS.md "駆動目標の加減速・停止".
    current_wheel_milli = [0]
    seed_holder = [0]
    latest_actual_angle_mdeg = [0]

    def ramp_wheel_to(tx_sock, target_milli, seed, rate_hz):
        """Step the wheel target from current_wheel_milli[0] to target_milli
        at WHEEL_DECEL_RPM_PER_S, holding the steer target at seed (no steer
        excitation during ramps)."""
        interval_s = 1.0 / rate_hz
        step_milli = WHEEL_DECEL_RPM_PER_S * 1000.0 * interval_s
        while current_wheel_milli[0] != target_milli:
            delta = target_milli - current_wheel_milli[0]
            if abs(delta) <= step_milli:
                current_wheel_milli[0] = target_milli
            else:
                current_wheel_milli[0] += int(step_milli) if delta > 0 else -int(step_milli)
            send_set_target_ff(tx_sock, 0, 0)
            send_set_target(tx_sock, seed, int(current_wheel_milli[0]))
            time.sleep(interval_s)

    def restore():
        nonlocal cleanup
        if not cleanup:
            return
        try:
            if current_wheel_milli[0] != 0:
                ramp_wheel_to(tx, 0, seed_holder[0], args.rate_hz)
            send_unit_ctrl(tx, False)
            apply_config(tx, RESTORE_CONFIG)
            send_unit_ctrl(tx, False)
        except OSError as exc:
            print(f"WARNING: config restore failed: {exc}", file=sys.stderr)
        emergency_disable(args.can_iface)

    atexit.register(restore)
    try:
        send_unit_ctrl(tx, False)
        time.sleep(0.1)
        ensure_web_ui_stopped(args.web_url, args.seed_timeout)
        seed_mdeg = read_seed_angle_from_can(rx, args.seed_timeout)
        seed_holder[0] = seed_mdeg
        latest_actual_angle_mdeg[0] = seed_mdeg
        trial_config = {
            3: args.kp,
            4: args.ki,
            5: 0.0,
            7: max(args.amplitude_rpm, 5.0),
            8: 0.0,
            # Firmware uses one symmetric hard guard.  Keep it above both
            # host-side rates; the host waveform below owns the asymmetric
            # acceleration/deceleration profile.
            9: max(args.steer_accel_rpm_s, args.steer_decel_rpm_s),
            13: args.filter_tau_s,
            18: 0.0,
            19: 0.0,
            20: 0.0,
            21: 0.0,
            22: args.status_period_ms,
        }
        apply_config(tx, trial_config)

        zero_frames = max(5, int(args.rate_hz * 0.1))
        for _ in range(zero_frames):
            send_set_target_ff(tx, 0, 0)
            send_set_target(tx, seed_mdeg, 0)
            time.sleep(1.0 / args.rate_hz)
        send_unit_ctrl(tx, True)

        # Refuse to record a zero trace when enable was never acknowledged.
        # Also refresh the measured-angle target before the excitation starts.
        active_acknowledged = False
        enable_bus_mv = BUS_VOLTAGE_UNAVAILABLE_MV
        enable_status_flags = 0
        active_deadline = time.monotonic() + 0.5
        next_enable_heartbeat = time.monotonic()
        while time.monotonic() < active_deadline and not active_acknowledged:
            now = time.monotonic()
            if now >= next_enable_heartbeat:
                send_set_target_ff(tx, 0, 0)
                send_set_target(tx, latest_actual_angle_mdeg[0], 0)
                next_enable_heartbeat += 1.0 / args.rate_hz
            wait_s = max(0.0, min(
                next_enable_heartbeat - time.monotonic(),
                active_deadline - time.monotonic(),
                0.02,
            ))
            readable, _, _ = select.select([rx], [], [], wait_s)
            if not readable:
                continue
            while True:
                try:
                    feedback = receive_feedback(rx)
                except BlockingIOError:
                    break
                if feedback is None:
                    continue
                if feedback[0] == "status1":
                    latest_actual_angle_mdeg[0] = feedback[1][0]
                elif feedback[0] == "status3":
                    bus_mv, status_flags, error_flags = feedback[1]
                    enable_bus_mv = bus_mv
                    enable_status_flags = status_flags
                    if error_flags:
                        raise RuntimeError(
                            f"firmware error while enabling: 0x{error_flags:08x}")
                    if not status_flags & STATUS_FLAG_FEEDBACK_OK:
                        raise RuntimeError(
                            "C620 feedback is not fresh while enabling")
                    active_acknowledged = bool(status_flags & STATUS_FLAG_ACTIVE)
        if not active_acknowledged:
            raise RuntimeError("firmware did not acknowledge ACTIVE")

        if wheel_rpm_milli != 0:
            # Spin up to the target wheel speed before any steer excitation,
            # using the firmware's own wheel_accel_rpm_per_s ramp (unchanged
            # by trial_config); WHEEL_DECEL_RPM_PER_S paces our own target
            # steps, which is a safe lower bound on how fast the firmware
            # will actually follow.
            ramp_wheel_to(tx, wheel_rpm_milli, seed_mdeg, args.rate_hz)
            settle_frames = max(5, int(args.rate_hz * 0.2))
            for _ in range(settle_frames):
                send_set_target_ff(tx, 0, 0)
                send_set_target(tx, seed_mdeg, wheel_rpm_milli)
                time.sleep(1.0 / args.rate_hz)

        bits = prbs_bits()
        duration = total_duration(args, bits)
        interval = 1.0 / args.rate_hz
        drain_socket(rx)
        started = time.monotonic()
        next_send = started
        rows = []
        latest_command = 0.0
        latest_phase = "zero_pre"
        target_mdeg = float(seed_mdeg)
        last_command_update = started
        active_seen = True
        latest_bus_mv = enable_bus_mv
        latest_status_flags = enable_status_flags
        status3_samples = 0
        feedback_drop_count = 0
        measured_bus_mv = []
        while True:
            now = time.monotonic()
            elapsed = now - started
            if now >= next_send:
                command_dt_s = now - last_command_update
                last_command_update = now
                desired_command, new_phase = command_for_time(
                    args.pattern, elapsed, args.amplitude_rpm, args.pulse_s,
                    args.zero_s, args.chip_s, bits,
                    args.steer_decel_rpm_s, args.step_direction)
                next_command = slew_command(
                    latest_command,
                    desired_command,
                    args.steer_accel_rpm_s,
                    args.steer_decel_rpm_s,
                    command_dt_s,
                )
                latest_command = next_command
                latest_phase = new_phase
                # Both outer angle gains are zero during this identification.
                # Keep SET_TARGET on the latest measured AMT angle solely to
                # satisfy the independent 120deg divergence guard; integrating
                # commanded velocity here makes normal inner-loop lag look
                # like an angle fault above ~250rpm.
                target_mdeg = float(latest_actual_angle_mdeg[0])
                target_mdeg_int = int(round(target_mdeg))
                seed_holder[0] = target_mdeg_int
                send_set_target_ff(tx, int(round(latest_command * 6000.0)), 0)
                send_set_target(tx, target_mdeg_int, wheel_rpm_milli)
                next_send += interval
                if elapsed >= duration:
                    break
            wait_s = max(0.0, min(next_send - time.monotonic(), 0.01))
            readable, _, _ = select.select([rx], [], [], wait_s)
            if not readable:
                continue
            while True:
                try:
                    feedback = receive_feedback(rx)
                except BlockingIOError:
                    break
                if feedback is None:
                    continue
                kind, payload = feedback
                if kind == "status1":
                    latest_actual_angle_mdeg[0] = payload[0]
                    continue
                if kind == "status3":
                    bus_mv, status_flags, error_flags = payload
                    latest_bus_mv = bus_mv
                    latest_status_flags = status_flags
                    status3_samples += 1
                    if bus_mv != BUS_VOLTAGE_UNAVAILABLE_MV:
                        measured_bus_mv.append(bus_mv)
                    active = bool(status_flags & STATUS_FLAG_ACTIVE)
                    if error_flags:
                        raise RuntimeError(
                            f"firmware error during identification: 0x{error_flags:08x}")
                    if not status_flags & STATUS_FLAG_FEEDBACK_OK:
                        feedback_drop_count += 1
                        raise RuntimeError(
                            "C620 feedback lost during identification")
                    if active:
                        active_seen = True
                    elif active_seen:
                        raise RuntimeError(
                            "firmware left ACTIVE state during identification")
                    continue
                motor1, motor2, measured_mode = payload
                rows.append({
                    "time_s": time.monotonic() - started,
                    "phase": latest_phase,
                    "target_angle_mdeg": int(round(target_mdeg)),
                    "command_axis_rpm": latest_command,
                    "command_mode_rpm": latest_command / STEER_RATIO,
                    "measured_mode_rpm": measured_mode,
                    "measured_axis_rpm": measured_mode * STEER_RATIO,
                    "motor1_rotor_rpm": motor1,
                    "motor2_rotor_rpm": motor2,
                    "bus_voltage_mv": latest_bus_mv,
                    "status_flags": latest_status_flags,
                    "feedback_ok": int(bool(
                        latest_status_flags & STATUS_FLAG_FEEDBACK_OK)),
                })

        # The duration calculation above should leave a full zero-speed dwell,
        # but explicitly finish the controlled ramp before Disable as a final
        # guard against scheduler delay or a future pattern change.
        while abs(latest_command) > 1e-6:
            latest_command = slew_command(
                latest_command, 0.0, args.steer_accel_rpm_s,
                args.steer_decel_rpm_s, interval)
            send_set_target_ff(tx, int(round(latest_command * 6000.0)), 0)
            send_set_target(tx, latest_actual_angle_mdeg[0], wheel_rpm_milli)
            time.sleep(interval)
        send_set_target_ff(tx, 0, 0)
        final_target_mdeg = int(round(target_mdeg))
        seed_holder[0] = final_target_mdeg
        send_set_target(tx, final_target_mdeg, wheel_rpm_milli)
        time.sleep(0.1)
        if current_wheel_milli[0] != 0:
            ramp_wheel_to(tx, 0, final_target_mdeg, args.rate_hz)
        send_unit_ctrl(tx, False)
        if len(rows) < 10:
            raise RuntimeError(f"too few STATUS2 samples ({len(rows)}); is index 22 flashed?")

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        output_dir = args.output_dir / stamp
        output_dir.mkdir(parents=True, exist_ok=False)
        with (output_dir / "samples.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        metrics = step_metrics(rows, args.amplitude_rpm) if args.pattern == "step" else {}
        sample_times = [row["time_s"] for row in rows]
        max_sample_gap_s = max(
            (later - earlier
             for earlier, later in zip(sample_times, sample_times[1:])),
            default=math.nan,
        )
        metadata = {
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "arguments": vars(args) | {"output_dir": str(args.output_dir)},
            "seed_angle_mdeg": seed_mdeg,
            "samples": len(rows),
            "effective_sample_hz": len(rows) / duration,
            "metrics": metrics,
            "safety": {
                "external_24v_monitor_confirmed": args.yes_24v_monitored,
                "status3_samples": status3_samples,
                "feedback_drop_count": feedback_drop_count,
                "bus_voltage_available": bool(measured_bus_mv),
                "bus_voltage_min_mv": (
                    min(measured_bus_mv) if measured_bus_mv else None),
                "bus_voltage_max_mv": (
                    max(measured_bus_mv) if measured_bus_mv else None),
                "max_status2_sample_gap_s": max_sample_gap_s,
            },
        }
        (output_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        print(f"saved: {output_dir}")
    finally:
        restore()
        cleanup = False
        atexit.unregister(restore)
        rx.close()
        tx.close()


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", choices=("step", "prbs"), default="step")
    parser.add_argument(
        "--step-direction", choices=("positive", "negative", "both"),
        default="both",
        help="run one direction only to minimize high-speed braking events")
    parser.add_argument("--kp", type=float, default=120.0)
    parser.add_argument("--ki", type=float, default=50.0)
    parser.add_argument("--filter-tau-s", type=float, default=0.002)
    parser.add_argument("--amplitude-rpm", type=float, default=20.0,
                        help="steer-axis speed amplitude; 20rpm = 120deg/s")
    parser.add_argument("--wheel-rpm", type=float, default=0.0,
                        help=(
                            "constant wheel rpm held during the steer excitation "
                            "(default: 0, matches the original wheel=0-only "
                            "identification). Ramped up before and down after the "
                            "test at WHEEL_DECEL_RPM_PER_S so disable never happens "
                            "while spinning."
                        ))
    parser.add_argument("--pulse-s", type=float, default=0.20)
    parser.add_argument("--zero-s", type=float, default=0.20)
    parser.add_argument("--chip-s", type=float, default=0.025)
    parser.add_argument("--steer-accel-rpm-s", type=float, default=2000.0)
    parser.add_argument(
        "--steer-decel-rpm-s", type=float, default=500.0,
        help=(
            "steer-axis controlled deceleration rate (default: 500rpm/s); "
            "kept separate from acceleration to limit regenerative DC-bus rise"
        ))
    parser.add_argument("--rate-hz", type=float, default=200.0)
    parser.add_argument("--status-period-ms", type=float, default=1.0,
                        help="STATUS1/2 period in ms during identification")
    parser.add_argument("--can-iface", default="can0")
    parser.add_argument("--vcp-port", default="/dev/ttyACM0")
    parser.add_argument("--vcp-baud", type=int, default=115200)
    parser.add_argument("--seed-timeout", type=float, default=3.0)
    parser.add_argument("--web-url", default="http://127.0.0.1:8080")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--yes-wheel-lifted", action="store_true")
    parser.add_argument(
        "--yes-24v-monitored", action="store_true",
        help=(
            "confirm an external 24V min/max meter or oscilloscope is "
            "connected; without it, braking above 500rpm/s is refused "
            "when steer speed exceeds 260rpm"
        ))
    parser.add_argument("--self-check", action="store_true")
    return parser


def self_check():
    bits = prbs_bits()
    assert len(bits) == 62
    assert sum(bits) == 0.0
    assert step_command(0.0, 20.0, 0.2, 0.2, 100.0)[1] == "zero_pre"
    assert step_command(0.25, 20.0, 0.2, 0.2, 100.0)[1] == "positive"
    assert step_command(0.65, 20.0, 0.2, 0.2, 100.0)[1] == "zero_mid"
    assert step_command(0.85, 20.0, 0.2, 0.2, 100.0)[1] == "negative"
    assert step_command(
        0.25, 20.0, 0.2, 0.2, 100.0, "negative")[1] == "negative"
    assert step_command(
        0.65, 20.0, 0.2, 0.2, 100.0, "negative")[1] == "zero_post"
    assert move_toward(0.0, 300.0, 20.0) == 20.0
    assert move_toward(20.0, 0.0, 20.0) == 0.0
    assert slew_command(300.0, 0.0, 4000.0, 500.0, 0.01) == 295.0
    assert slew_command(5.0, -300.0, 4000.0, 500.0, 0.01) == 0.0
    assert slew_command(0.0, -300.0, 4000.0, 500.0, 0.01) == -40.0
    fake = []
    for phase, command in (("positive", 27.5), ("negative", -27.5)):
        for index in range(20):
            fake.append({"phase": phase, "time_s": index * 0.001,
                         "measured_mode_rpm": command * min(1.0, index / 10.0)})
    metrics = step_metrics(fake, 20.0)
    assert metrics["positive"]["samples"] == 20
    assert metrics["negative"]["rise_90_s"] is not None
    print("SELF_CHECK PASS")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        self_check()
        return 0
    try:
        run(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
