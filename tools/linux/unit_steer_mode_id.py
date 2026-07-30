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
STATUS2_ID = 0x191
M3508_REDUCTION = 19.0
STEER_RATIO = 8.0 / 11.0

# Values flashed as of 2026-07-31. The ID setup is deliberately complete so a
# stale SET_CONFIG value from a previous bench run cannot leak into a trial.
RESTORE_CONFIG = {
    3: 120.0,      # steer mode Kp
    4: 50.0,       # steer mode Ki
    5: 4.0,        # hold angle Kp
    7: 40.0,       # steer-axis max rpm
    8: 0.0,        # steer-axis minimum rpm
    9: 600.0,      # local steer-axis acceleration rpm/s
    13: 0.002,     # mode-speed LPF tau
    18: 0.5,       # acceleration FF gain
    19: 1.0,       # moving angle Kp
    20: 0.5,       # deceleration FF gain
    21: 0.0,       # steer friction FF
    22: 0.0,       # high-rate STATUS2 disabled
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


def apply_config(sock, values):
    for index, value in values.items():
        send_set_config(sock, index, value)
        time.sleep(0.012)


def step_command(elapsed, amplitude_rpm, pulse_s, zero_s):
    edges = (
        (zero_s, 0.0, "zero_pre"),
        (zero_s + pulse_s, amplitude_rpm, "positive"),
        (zero_s + pulse_s + zero_s, 0.0, "zero_mid"),
        (zero_s + 2.0 * pulse_s + zero_s, -amplitude_rpm, "negative"),
        (3.0 * zero_s + 2.0 * pulse_s, 0.0, "zero_post"),
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


def command_for_time(pattern, elapsed, amplitude_rpm, pulse_s, zero_s, chip_s, bits):
    if pattern == "step":
        return step_command(elapsed, amplitude_rpm, pulse_s, zero_s)
    if elapsed < zero_s:
        return 0.0, "zero_pre"
    chip = int((elapsed - zero_s) / chip_s)
    if chip < len(bits):
        return amplitude_rpm * bits[chip], f"prbs_{chip}"
    if elapsed < zero_s + len(bits) * chip_s + zero_s:
        return 0.0, "zero_post"
    return 0.0, "done"


def total_duration(args, bits):
    if args.pattern == "step":
        return 3.0 * args.zero_s + 2.0 * args.pulse_s
    return 2.0 * args.zero_s + len(bits) * args.chip_s


def receive_status2(sock):
    frame = sock.recv(CAN_FRAME_SIZE)
    can_id, data = parse_can_frame(frame)
    if can_id != STATUS2_ID or len(data) != 8:
        return None
    motor1_milli, motor2_milli = struct.unpack("<ii", data)
    motor1_rotor_rpm = motor1_milli * 0.001
    motor2_rotor_rpm = motor2_milli * 0.001
    mode_rpm = (motor1_rotor_rpm + motor2_rotor_rpm) / (2.0 * M3508_REDUCTION)
    return motor1_rotor_rpm, motor2_rotor_rpm, mode_rpm


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
    if args.amplitude_rpm <= 0.0 or args.amplitude_rpm > 40.0:
        raise RuntimeError("--amplitude-rpm must be in (0, 40]")
    if args.rate_hz < 50.0 or args.rate_hz > 500.0:
        raise RuntimeError("--rate-hz must be within 50..500")

    tx = open_can_socket(args.can_iface)
    rx = open_can_socket(args.can_iface)
    rx.setblocking(False)
    cleanup = True

    def restore():
        nonlocal cleanup
        if not cleanup:
            return
        try:
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
        seed_mdeg = parse_idle_angle(args.vcp_port, args.vcp_baud, args.seed_timeout)
        trial_config = {
            3: args.kp,
            4: args.ki,
            5: 0.0,
            7: min(40.0, max(args.amplitude_rpm, 5.0)),
            8: 0.0,
            9: args.steer_accel_rpm_s,
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

        bits = prbs_bits()
        duration = total_duration(args, bits)
        interval = 1.0 / args.rate_hz
        started = time.monotonic()
        next_send = started
        rows = []
        latest_command = 0.0
        latest_phase = "zero_pre"
        while True:
            now = time.monotonic()
            elapsed = now - started
            if now >= next_send:
                latest_command, latest_phase = command_for_time(
                    args.pattern, elapsed, args.amplitude_rpm, args.pulse_s,
                    args.zero_s, args.chip_s, bits)
                send_set_target_ff(tx, int(round(latest_command * 6000.0)), 0)
                send_set_target(tx, seed_mdeg, 0)
                next_send += interval
                if elapsed >= duration:
                    break
            wait_s = max(0.0, min(next_send - time.monotonic(), 0.01))
            readable, _, _ = select.select([rx], [], [], wait_s)
            if not readable:
                continue
            while True:
                try:
                    status = receive_status2(rx)
                except BlockingIOError:
                    break
                if status is None:
                    continue
                motor1, motor2, measured_mode = status
                rows.append({
                    "time_s": time.monotonic() - started,
                    "phase": latest_phase,
                    "command_axis_rpm": latest_command,
                    "command_mode_rpm": latest_command / STEER_RATIO,
                    "measured_mode_rpm": measured_mode,
                    "measured_axis_rpm": measured_mode * STEER_RATIO,
                    "motor1_rotor_rpm": motor1,
                    "motor2_rotor_rpm": motor2,
                })

        send_set_target_ff(tx, 0, 0)
        send_set_target(tx, seed_mdeg, 0)
        time.sleep(0.1)
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
        metadata = {
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "arguments": vars(args) | {"output_dir": str(args.output_dir)},
            "seed_angle_mdeg": seed_mdeg,
            "samples": len(rows),
            "effective_sample_hz": len(rows) / duration,
            "metrics": metrics,
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
    parser.add_argument("--kp", type=float, default=120.0)
    parser.add_argument("--ki", type=float, default=50.0)
    parser.add_argument("--filter-tau-s", type=float, default=0.002)
    parser.add_argument("--amplitude-rpm", type=float, default=20.0,
                        help="steer-axis speed amplitude; 20rpm = 120deg/s")
    parser.add_argument("--pulse-s", type=float, default=0.20)
    parser.add_argument("--zero-s", type=float, default=0.20)
    parser.add_argument("--chip-s", type=float, default=0.025)
    parser.add_argument("--steer-accel-rpm-s", type=float, default=2000.0)
    parser.add_argument("--rate-hz", type=float, default=200.0)
    parser.add_argument("--status-period-ms", type=float, default=1.0,
                        help="STATUS1/2 period in ms during identification")
    parser.add_argument("--can-iface", default="can0")
    parser.add_argument("--vcp-port", default="/dev/ttyACM0")
    parser.add_argument("--vcp-baud", type=int, default=115200)
    parser.add_argument("--seed-timeout", type=float, default=3.0)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--yes-wheel-lifted", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    return parser


def self_check():
    bits = prbs_bits()
    assert len(bits) == 62
    assert sum(bits) == 0.0
    assert step_command(0.0, 20.0, 0.2, 0.2)[1] == "zero_pre"
    assert step_command(0.25, 20.0, 0.2, 0.2)[1] == "positive"
    assert step_command(0.65, 20.0, 0.2, 0.2)[1] == "negative"
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
