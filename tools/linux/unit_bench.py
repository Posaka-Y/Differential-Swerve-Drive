#!/usr/bin/env python3
"""unit_bench.py - Differential Swerve Drive unit evaluation/tuning CLI (Linux mini PC).

Sends CAN frames to a single differential-steer unit (unitId=1) over SocketCAN
(can0, classic CAN 1Mbps, e.g. via a CANable running slcand) and, in parallel,
captures the unit's ST-Link VCP debug log (default /dev/ttyACM0, 115200 8N1)
and the CAN traffic seen on can0 into a single timestamped log file.

No external dependency beyond pyserial is used. CAN frames are built and sent
directly with the stdlib socket module (AF_CAN / SOCK_RAW / CAN_RAW), so
python-can is NOT required and is intentionally not used.

CAN message spec (see docs/testing/MINIPC_LINUX_HANDOFF.md, unitId=1):

    SET_TARGET    ID 0x101  DLC 8  int32 LE steer_mdeg, int32 LE wheel_rpm_milli
                  Must be sent periodically (recommended 50Hz). Target timeout
                  is 1000ms on the latest firmware, but older flashed firmware
                  may still use 200ms -- always send at 50Hz to be safe.
    SET_TARGET_FF ID 0x111  DLC 8  int32 LE steer_rate_mdeg_per_s,
                  int32 LE wheel_accel_rpm_milli_per_s (see
                  docs/communication/COMMUNICATION_NAMING_AND_IDS.md
                  "SET_TARGET_FF payload"). Steer-rate FF is added to the
                  unit's angle-P term; the unit falls back to FF=0 if this
                  frame is not seen for 200ms, so it must be sent at >=50Hz
                  whenever used (this tool sends it right before SET_TARGET
                  each cycle when enabled -- see --steer-rate-dps / the CSV
                  steer_rate_mdeg_s column).
    UNIT_CTRL     ID 0x121  DLC 2  enable = 01 01, disable = 01 00
    SET_CONFIG    ID 0x141  DLC 8  byte0=param index (uint8), byte1..3=0,
                  byte4..7 = int32 LE value*1000 (milli units)

SAFETY (read before running "run" or "profile"):

  1. Lift the wheel off the ground / free-spin it before enabling. A target
     command can spin the wheel and/or rotate the steer axis immediately
     after enable.
  2. Keep a second terminal open with the disable command ready to run:
         python3 tools/linux/unit_bench.py disable
     so you can cut power to the motors immediately if something looks wrong.
  3. This tool always sends UNIT_CTRL disable on exit (normal completion,
     exception, or Ctrl-C) via a try/finally block, plus a best-effort
     atexit safety net. It cannot protect against the process being killed
     with SIGKILL or the machine losing power -- the firmware-side target
     timeout (1000ms, possibly 200ms on old firmware) is the last line of
     defense in that case.
  4. This script never sends anything to can0 on its own; it only sends when
     you run "run", "set-param", or "profile". "--help" and "python3 -m
     py_compile" do not touch can0.

Examples:

    # Evaluate steer=90deg, wheel=500rpm for 5s at 50Hz, auto log path.
    python3 tools/linux/unit_bench.py run --steer-deg 90 --wheel-rpm 500 --duration 5

    # Tune gains (drive_kp=0.5, drive_ki=0.1) without enabling the unit.
    python3 tools/linux/unit_bench.py set-param --index 1 --value 0.5 --index 2 --value 0.1

    # Emergency stop from a second terminal.
    python3 tools/linux/unit_bench.py disable

    # Replay a step profile from CSV (time_s, steer_mdeg, wheel_rpm_milli).
    python3 tools/linux/unit_bench.py profile --csv profile.csv --rate 50

    # Same, plus a 4th optional CSV column steer_rate_mdeg_s: sends
    # SET_TARGET_FF (steer rate only) each cycle whenever that cell is filled.
    python3 tools/linux/unit_bench.py profile --csv profile_with_ff.csv --rate 50

    # Ramp the steer target continuously at 30deg/s (sends SET_TARGET_FF
    # every cycle) while holding wheel at 0rpm for 5s.
    python3 tools/linux/unit_bench.py run --steer-deg 0 --wheel-rpm 0 \\
        --steer-rate-dps 30 --duration 5
"""

import argparse
import atexit
import csv
import socket
import struct
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# CAN message IDs / payload constants (unitId=1, see MINIPC_LINUX_HANDOFF.md)
# --------------------------------------------------------------------------

SET_TARGET_ID = 0x101
SET_TARGET_FF_ID = 0x111
UNIT_CTRL_ID = 0x121
SET_CONFIG_ID = 0x141

ENABLE_PAYLOAD = bytes([0x01, 0x01])
DISABLE_PAYLOAD = bytes([0x01, 0x00])

PARAM_INDEX_HELP = (
    "1=drive_kp 2=drive_ki 3=steer_kp 4=steer_ki 5=angle_kp 6=angle_deadband_deg "
    "7=steer_max_rpm 8=steer_min_rpm 9=steer_accel 10=wheel_accel 11=integral_limit "
    "12=current_limit 13=rpm_filter_tau 14=drive_kinetic_ff_current "
    "15=drive_integral_floor_current 16=drive_motion_threshold_rpm"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = REPO_ROOT / "firmware" / "logs"

# classic (non-FD) SocketCAN frame: struct can_frame { u32 can_id; u8 can_dlc;
# u8 pad[3]; u8 data[8]; }
CAN_FRAME_FMT = "=IB3x8s"
CAN_FRAME_SIZE = struct.calcsize(CAN_FRAME_FMT)


# --------------------------------------------------------------------------
# SocketCAN helpers (stdlib only, no python-can)
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


def send_set_config(sock, index, value):
    milli = int(round(value * 1000))
    data = struct.pack("<B3xi", index & 0xFF, milli)
    sock.send(build_can_frame(SET_CONFIG_ID, data))


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
        print(f"[unit_bench] WARNING: emergency disable failed: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------
# Logging: merges CAN rx and VCP serial rx into one timestamped file + stdout
# --------------------------------------------------------------------------


class BenchLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._fh = open(self.path, "a", buffering=1, encoding="utf-8")
        self.write("BENCH", f"log opened: {self.path}")

    def write(self, prefix, message):
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        line = f"{ts} {prefix} {message}"
        with self._lock:
            self._fh.write(line + "\n")
        print(line)

    def close(self):
        self.write("BENCH", "log closed")
        with self._lock:
            self._fh.close()


def default_log_path():
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S") + "Z"
    return DEFAULT_LOG_DIR / f"bench-{stamp}.log"


def resolve_log_path(log_arg):
    return Path(log_arg) if log_arg else default_log_path()


# --------------------------------------------------------------------------
# Background capture threads
# --------------------------------------------------------------------------


def can_rx_loop(stop_event, logger, ifname):
    try:
        sock = open_can_socket(ifname, timeout=0.2)
    except OSError as exc:
        logger.write("CAN", f"ERROR: could not open {ifname}: {exc}")
        return
    try:
        while not stop_event.is_set():
            try:
                frame = sock.recv(CAN_FRAME_SIZE)
            except socket.timeout:
                continue
            except OSError as exc:
                logger.write("CAN", f"ERROR: recv failed: {exc}")
                break
            try:
                can_id, data = parse_can_frame(frame)
            except struct.error:
                continue
            logger.write("CAN", f"id={can_id:03x} dlc={len(data)} data={data.hex()}")
    finally:
        sock.close()


def vcp_rx_loop(stop_event, logger, port, baud):
    import serial  # local import: only needed when actually capturing VCP

    try:
        ser = serial.Serial(port, baudrate=baud, timeout=0.2)
    except Exception as exc:  # noqa: BLE001 - report and give up, don't crash the bench
        logger.write("VCP", f"ERROR: could not open {port}: {exc}")
        return
    try:
        buf = b""
        while not stop_event.is_set():
            try:
                chunk = ser.read(256)
            except Exception as exc:  # noqa: BLE001 - e.g. device unplugged mid-run
                logger.write("VCP", f"ERROR: read failed (device disconnected?): {exc}")
                break
            if not chunk:
                continue
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode("utf-8", errors="replace").rstrip("\r")
                if text:
                    logger.write("VCP", text)
    finally:
        ser.close()


# --------------------------------------------------------------------------
# CSV profile loading (profile subcommand)
# --------------------------------------------------------------------------


def load_profile(csv_path):
    required = {"time_s", "steer_mdeg", "wheel_rpm_milli"}
    optional_ff_col = "steer_rate_mdeg_s"
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing = required - fieldnames
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        has_ff_col = optional_ff_col in fieldnames
        for row in reader:
            steer_rate_mdeg_s = None
            if has_ff_col and row.get(optional_ff_col, "") != "":
                steer_rate_mdeg_s = int(float(row[optional_ff_col]))
            rows.append(
                (
                    float(row["time_s"]),
                    int(float(row["steer_mdeg"])),
                    int(float(row["wheel_rpm_milli"])),
                    steer_rate_mdeg_s,
                )
            )
    if not rows:
        raise ValueError(f"CSV has no data rows: {csv_path}")
    rows.sort(key=lambda r: r[0])
    return rows


def profile_value_at(rows, t):
    """Zero-order-hold step lookup: last row whose time_s <= t (no interpolation)."""
    current = rows[0]
    for row in rows:
        if row[0] <= t:
            current = row
        else:
            break
    return current


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------


def _start_capture_threads(args, logger):
    stop_event = threading.Event()
    rx_thread = threading.Thread(
        target=can_rx_loop, args=(stop_event, logger, args.can_iface), daemon=True
    )
    vcp_thread = threading.Thread(
        target=vcp_rx_loop, args=(stop_event, logger, args.vcp_port, args.vcp_baud), daemon=True
    )
    rx_thread.start()
    vcp_thread.start()
    return stop_event, rx_thread, vcp_thread


def _stop_capture_threads(stop_event, rx_thread, vcp_thread, grace_s=0.3):
    # Give the VCP/CAN threads a moment to flush any final lines (e.g. a
    # firmware "STOP:" line printed in reaction to the disable frame).
    time.sleep(grace_s)
    stop_event.set()
    rx_thread.join(timeout=1.0)
    vcp_thread.join(timeout=1.0)


def cmd_run(args):
    steer_mdeg = int(round(args.steer_deg * 1000))
    wheel_rpm_milli = int(round(args.wheel_rpm * 1000))
    rate = args.rate
    if rate <= 0:
        raise ValueError("--rate must be > 0")
    interval = 1.0 / rate
    steer_rate_dps = args.steer_rate_dps
    # mdeg/s, int32 payload sent in SET_TARGET_FF each cycle while nonzero.
    steer_rate_mdeg_per_s = int(round(steer_rate_dps * 1000))

    logger = BenchLogger(resolve_log_path(args.log))
    atexit.register(emergency_disable, args.can_iface)
    stop_event, rx_thread, vcp_thread = _start_capture_threads(args, logger)

    tx_sock = open_can_socket(args.can_iface)
    try:
        logger.write(
            "BENCH",
            f"run: steer={args.steer_deg}deg ({steer_mdeg}mdeg) "
            f"wheel={args.wheel_rpm}rpm ({wheel_rpm_milli}milli-rpm) "
            f"rate={rate}Hz duration={args.duration}s "
            f"steer_rate={steer_rate_dps}dps ({steer_rate_mdeg_per_s}mdeg/s)",
        )
        send_unit_ctrl(tx_sock, True)
        logger.write("BENCH", "enable sent")

        # Continuous steer-rate FF injection: the steer target itself is also
        # advanced by rate*dt each cycle (wrapped into [0, 360000) mdeg) so
        # the angle-P term and the FF stay consistent with each other, per
        # docs/control/CENTRAL_COORDINATED_CONTROL.md. Wrapping here is fine
        # for this single-unit bench (unlike the central controller's
        # continuous-unwrap contract) because the firmware's shortest-angle
        # error only ever sees both sides mod 360 deg anyway.
        steer_target_mdeg = float(steer_mdeg) % 360000.0
        end_time = time.monotonic() + args.duration
        next_tick = time.monotonic()
        while time.monotonic() < end_time:
            if steer_rate_dps != 0:
                send_set_target_ff(tx_sock, steer_rate_mdeg_per_s, 0)
            send_set_target(tx_sock, int(round(steer_target_mdeg)), wheel_rpm_milli)
            steer_target_mdeg = (
                steer_target_mdeg + steer_rate_dps * 1000.0 * interval
            ) % 360000.0
            next_tick += interval
            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
    except KeyboardInterrupt:
        logger.write("BENCH", "interrupted by Ctrl-C")
    finally:
        try:
            send_unit_ctrl(tx_sock, False)
            send_unit_ctrl(tx_sock, False)
            logger.write("BENCH", "disable sent")
        except OSError as exc:
            logger.write("BENCH", f"ERROR: disable send failed: {exc}")
        _stop_capture_threads(stop_event, rx_thread, vcp_thread)
        tx_sock.close()
        logger.close()


def cmd_set_param(args):
    if len(args.index) != len(args.value):
        raise ValueError(
            f"--index and --value counts must match ({len(args.index)} vs {len(args.value)})"
        )
    sock = open_can_socket(args.can_iface)
    try:
        for i, (index, value) in enumerate(zip(args.index, args.value)):
            if not (1 <= index <= 17):
                raise ValueError(f"param index out of range (1-17): {index}")
            send_set_config(sock, index, value)
            print(f"set-param: index={index} value={value} (milli={int(round(value * 1000))})")
            if i != len(args.index) - 1:
                time.sleep(0.02)
    finally:
        sock.close()


def cmd_disable(args):
    sock = open_can_socket(args.can_iface)
    try:
        send_unit_ctrl(sock, False)
        send_unit_ctrl(sock, False)
        print(f"disable sent on {args.can_iface}")
    finally:
        sock.close()


def cmd_profile(args):
    rows = load_profile(args.csv)
    rate = args.rate
    if rate <= 0:
        raise ValueError("--rate must be > 0")
    interval = 1.0 / rate
    total_duration = rows[-1][0]

    logger = BenchLogger(resolve_log_path(args.log))
    atexit.register(emergency_disable, args.can_iface)
    stop_event, rx_thread, vcp_thread = _start_capture_threads(args, logger)

    tx_sock = open_can_socket(args.can_iface)
    try:
        logger.write(
            "BENCH",
            f"profile: csv={args.csv} rows={len(rows)} rate={rate}Hz "
            f"total_duration={total_duration}s",
        )
        send_unit_ctrl(tx_sock, True)
        logger.write("BENCH", "enable sent")

        start = time.monotonic()
        next_tick = start
        last_row = None
        while True:
            elapsed = time.monotonic() - start
            if elapsed > total_duration:
                break
            row = profile_value_at(rows, elapsed)
            if row != last_row:
                ff_note = f" ffRate={row[3]}mdeg/s" if row[3] is not None else ""
                logger.write(
                    "BENCH",
                    f"step t={elapsed:.3f}s -> steer={row[1]}mdeg wheel={row[2]}milli-rpm"
                    + ff_note,
                )
                last_row = row
            if row[3] is not None:
                send_set_target_ff(tx_sock, row[3], 0)
            send_set_target(tx_sock, row[1], row[2])
            next_tick += interval
            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
    except KeyboardInterrupt:
        logger.write("BENCH", "interrupted by Ctrl-C")
    finally:
        try:
            send_unit_ctrl(tx_sock, False)
            send_unit_ctrl(tx_sock, False)
            logger.write("BENCH", "disable sent")
        except OSError as exc:
            logger.write("BENCH", f"ERROR: disable send failed: {exc}")
        _stop_capture_threads(stop_event, rx_thread, vcp_thread)
        tx_sock.close()
        logger.close()


# --------------------------------------------------------------------------
# argparse wiring
# --------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="unit_bench.py",
        description=(
            "Differential swerve unit CAN/VCP evaluation & tuning bench (Linux mini PC, "
            "unitId=1). See docs/testing/MINIPC_LINUX_HANDOFF.md for the CAN spec."
        ),
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--can-iface", default="can0", help="SocketCAN interface (default: can0)")
    parser.add_argument(
        "--vcp-port", default="/dev/ttyACM0", help="VCP serial device (default: /dev/ttyACM0)"
    )
    parser.add_argument("--vcp-baud", type=int, default=115200, help="VCP baud rate (default: 115200)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser(
        "run",
        help="Send SET_TARGET periodically for a fixed duration (enable at start, disable at end).",
    )
    p_run.add_argument("--steer-deg", type=float, required=True, help="target steer angle (deg)")
    p_run.add_argument("--wheel-rpm", type=float, required=True, help="target wheel speed (rpm)")
    p_run.add_argument("--duration", type=float, required=True, help="run duration (s)")
    p_run.add_argument("--rate", type=float, default=50.0, help="SET_TARGET send rate in Hz (default: 50)")
    p_run.add_argument(
        "--steer-rate-dps", type=float, default=0.0,
        help=(
            "steer angular-rate feedforward (deg/s, default: 0=disabled). When "
            "nonzero, the steer target is also advanced by rate*dt each cycle "
            "(wrapped mod 360deg) and a SET_TARGET_FF frame (steer rate only, "
            "wheel accel FF=0) is sent immediately before each SET_TARGET."
        ),
    )
    p_run.add_argument(
        "--log", type=str, default=None,
        help="log file path (default: firmware/logs/bench-<UTC ISO>.log)",
    )
    p_run.set_defaults(func=cmd_run)

    p_set = sub.add_parser(
        "set-param",
        help="Send one or more SET_CONFIG frames (no enable needed). " + PARAM_INDEX_HELP,
    )
    p_set.add_argument(
        "--index", type=int, action="append", required=True,
        help="param index (1-17, repeatable, paired in order with --value). " + PARAM_INDEX_HELP,
    )
    p_set.add_argument(
        "--value", type=float, action="append", required=True,
        help="param value in real units, sent as value*1000 (int32 milli, repeatable)",
    )
    p_set.set_defaults(func=cmd_set_param)

    p_dis = sub.add_parser("disable", help="Send UNIT_CTRL disable only (emergency stop).")
    p_dis.set_defaults(func=cmd_disable)

    p_prof = sub.add_parser(
        "profile",
        help="Replay a CSV target profile as a step sequence (no time interpolation).",
    )
    p_prof.add_argument(
        "--csv", type=str, required=True,
        help=(
            "CSV file with columns: time_s, steer_mdeg, wheel_rpm_milli, and "
            "optional 4th column steer_rate_mdeg_s (steer-rate FF, mdeg/s; "
            "sent via SET_TARGET_FF each cycle when the cell is non-empty)"
        ),
    )
    p_prof.add_argument("--rate", type=float, default=50.0, help="SET_TARGET send rate in Hz (default: 50)")
    p_prof.add_argument(
        "--log", type=str, default=None,
        help="log file path (default: firmware/logs/bench-<UTC ISO>.log)",
    )
    p_prof.set_defaults(func=cmd_profile)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (OSError, ValueError) as exc:
        print(f"[unit_bench] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
