#!/usr/bin/env python3
"""Capture ESP32 radio telemetry as CSV, then run the offline analyzer."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
import subprocess
import sys
import time

import serial


FIELDS = [
    "ms",
    "bt",
    "armed",
    "enable",
    "unit_active",
    "target_steer_mdeg",
    "actual_steer_mdeg",
    "steer_error_mdeg",
    "target_wheel_mrpm",
    "actual_wheel_mrpm",
    "wheel_error_mrpm",
    "rpm_limit",
    "controller_age_ms",
    "unit_age_ms",
    "uart_rx_frames",
    "uart_rx_bad",
    "uart_rx_gaps",
    "uart_tx_fail",
]


def default_output() -> Path:
    stamp = dt.datetime.now().astimezone().strftime("%Y-%m-%dT%H-%M-%S%z")
    root = Path(__file__).resolve().parents[1]
    return root / "logs" / f"radio-{stamp}.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture 20 Hz TEL records from the ESP32 USB serial port."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--duration",
        type=float,
        default=90.0,
        help="capture seconds; use 0 to run until Ctrl-C (default: 90)",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--no-analyze", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = (args.output or default_output()).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    events_output = output.with_suffix(".events.log")

    row_count = 0
    malformed_count = 0
    disconnect_error: str | None = None
    started = time.monotonic()
    last_progress = started

    print(f"capture: port={args.port} baud={args.baud} output={output}")
    print("capture: OPTIONS=arm, R1=enable; Ctrl-C stops early")

    try:
        port = serial.Serial(args.port, args.baud, timeout=0.25)
    except serial.SerialException as exc:
        print(f"capture: cannot open {args.port}: {exc}", file=sys.stderr)
        return 2

    try:
        with port, output.open("w", newline="", encoding="utf-8") as csv_file, \
                events_output.open("w", encoding="utf-8") as events_file:
            writer = csv.writer(csv_file)
            writer.writerow(FIELDS)
            try:
                while args.duration <= 0 or time.monotonic() - started < args.duration:
                    try:
                        raw = port.readline()
                    except serial.SerialException as exc:
                        disconnect_error = str(exc)
                        events_file.write(f"SERIAL_DISCONNECT {disconnect_error}\n")
                        print(f"capture: serial disconnected: {exc}", file=sys.stderr)
                        break
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    if not line.startswith("TEL,"):
                        events_file.write(line + "\n")
                        events_file.flush()
                        continue

                    values = line.split(",")[1:]
                    if len(values) != len(FIELDS):
                        malformed_count += 1
                        events_file.write(f"MALFORMED {line}\n")
                        continue
                    try:
                        parsed = [int(value) for value in values]
                    except ValueError:
                        malformed_count += 1
                        events_file.write(f"MALFORMED {line}\n")
                        continue

                    writer.writerow(parsed)
                    row_count += 1
                    if row_count % 20 == 0:
                        csv_file.flush()

                    now = time.monotonic()
                    if now - last_progress >= 5.0:
                        print(
                            f"capture: {now - started:5.1f}s rows={row_count} "
                            f"enable={parsed[3]} wheel={parsed[9] / 1000:.1f}rpm "
                            f"steerErr={parsed[7] / 1000:.2f}deg"
                        )
                        last_progress = now
            except KeyboardInterrupt:
                print("\ncapture: stopped by user")
    finally:
        pass

    elapsed = time.monotonic() - started
    print(
        f"capture: complete duration={elapsed:.1f}s rows={row_count} "
        f"malformed={malformed_count}"
    )
    if disconnect_error is not None:
        print("capture: retained and analyzing the partial log")
    print(f"capture: csv={output}")
    print(f"capture: events={events_output}")
    if row_count == 0:
        print("capture: no TEL records received", file=sys.stderr)
        return 3

    if not args.no_analyze:
        analyzer = Path(__file__).with_name("analyze_radio_telemetry.py")
        result = subprocess.run([sys.executable, str(analyzer), str(output)])
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
