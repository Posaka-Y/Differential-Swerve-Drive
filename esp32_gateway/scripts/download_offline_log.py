#!/usr/bin/env python3
"""Receive the latest LittleFS radio log after L1+Create is pressed."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import subprocess
import sys
import time

import serial


def default_output() -> Path:
    stamp = dt.datetime.now().astimezone().strftime("%Y-%m-%dT%H-%M-%S%z")
    root = Path(__file__).resolve().parents[1]
    return root / "logs" / f"radio-offline-{stamp}.csv"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Wait for an ESP32 LittleFS log dump and save it as CSV."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--no-analyze", action="store_true")
    args = parser.parse_args()

    output = (args.output or default_output()).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"download: opening {args.port}")

    try:
        port = serial.Serial(args.port, args.baud, timeout=0.25)
    except serial.SerialException as exc:
        print(f"download: cannot open port: {exc}", file=sys.stderr)
        return 2

    deadline = time.monotonic() + args.timeout
    receiving = False
    lines: list[str] = []
    try:
        with port:
            time.sleep(0.5)
            port.reset_input_buffer()
            port.write(b"D\n")
            port.flush()
            print("download: requested latest LittleFS log")
            while time.monotonic() < deadline:
                raw = port.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                if line == "OFFLINE_LOG_BEGIN":
                    receiving = True
                    lines.clear()
                    print("download: receiving...")
                    continue
                if line == "OFFLINE_LOG_END" and receiving:
                    break
                if receiving:
                    lines.append(line)
    except serial.SerialException as exc:
        print(f"download: serial disconnected: {exc}", file=sys.stderr)
        return 3

    if not receiving or not lines or lines[0] != "ms,bt,armed,enable,unit_active,target_steer_mdeg,actual_steer_mdeg,steer_error_mdeg,target_wheel_mrpm,actual_wheel_mrpm,wheel_error_mrpm,rpm_limit,controller_age_ms,unit_age_ms,uart_rx_frames,uart_rx_bad,uart_rx_gaps,uart_tx_fail":
        print("download: complete log not received", file=sys.stderr)
        return 4

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"download: rows={len(lines) - 1} output={output}")
    if not args.no_analyze:
        analyzer = Path(__file__).with_name("analyze_radio_telemetry.py")
        return subprocess.run([sys.executable, str(analyzer), str(output)]).returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
