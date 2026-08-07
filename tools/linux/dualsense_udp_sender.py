#!/usr/bin/env python3
"""Send fail-safe DualSense body-twist commands to the ESP32 gateway."""

from __future__ import annotations

import argparse
import signal
import socket
import struct
import time
import zlib
from dataclasses import dataclass
from typing import Iterable, Optional

from dualsense_control import ControlConfig, DualSenseMapper, DualSenseReader


MAGIC = b"DSD1"
PROTOCOL_VERSION = 1
DEFAULT_HOST = "192.168.4.1"
DEFAULT_PORT = 4210
FLAG_CONNECTED = 1 << 0
FLAG_DEADMAN = 1 << 1
PACKET_WITHOUT_CRC = struct.Struct("!4sBBHIiii")
PACKET = struct.Struct("!4sBBHIiiiI")


@dataclass(frozen=True)
class GatewayCommand:
    sequence: int
    connected: bool
    deadman: bool
    vx_mm_s: int
    vy_mm_s: int
    omega_mrad_s: int


def encode_command(command: GatewayCommand) -> bytes:
    flags = 0
    if command.connected:
        flags |= FLAG_CONNECTED
    if command.deadman:
        flags |= FLAG_DEADMAN
    prefix = PACKET_WITHOUT_CRC.pack(
        MAGIC,
        PROTOCOL_VERSION,
        flags,
        0,
        command.sequence & 0xFFFFFFFF,
        int(command.vx_mm_s),
        int(command.vy_mm_s),
        int(command.omega_mrad_s),
    )
    return prefix + struct.pack("!I", zlib.crc32(prefix) & 0xFFFFFFFF)


def decode_command(packet: bytes) -> GatewayCommand:
    if len(packet) != PACKET.size:
        raise ValueError(f"invalid packet size: {len(packet)}")
    magic, version, flags, reserved, sequence, vx, vy, omega, received_crc = (
        PACKET.unpack(packet)
    )
    if magic != MAGIC or version != PROTOCOL_VERSION or reserved != 0:
        raise ValueError("invalid header")
    expected_crc = zlib.crc32(packet[:-4]) & 0xFFFFFFFF
    if received_crc != expected_crc:
        raise ValueError("CRC mismatch")
    return GatewayCommand(
        sequence=sequence,
        connected=bool(flags & FLAG_CONNECTED),
        deadman=bool(flags & FLAG_DEADMAN),
        vx_mm_s=vx,
        vy_mm_s=vy,
        omega_mrad_s=omega,
    )


def _self_check() -> None:
    original = GatewayCommand(0xFFFFFFFE, True, True, 1000, -250, -3000)
    encoded = encode_command(original)
    assert len(encoded) == 28
    assert decode_command(encoded) == original
    damaged = bytearray(encoded)
    damaged[12] ^= 0x01
    try:
        decode_command(bytes(damaged))
    except ValueError:
        pass
    else:
        raise AssertionError("damaged packet was accepted")
    print("dualsense_udp_sender self-check: PASS")


def _make_command(reader: DualSenseReader, sequence: int) -> GatewayCommand:
    snapshot = reader.snapshot()
    active = snapshot.connected and snapshot.command_active
    return GatewayCommand(
        sequence=sequence,
        connected=snapshot.connected,
        deadman=active,
        vx_mm_s=round(snapshot.vx_mps * 1000.0) if active else 0,
        vy_mm_s=round(snapshot.vy_mps * 1000.0) if active else 0,
        omega_mrad_s=round(snapshot.omega_rad_s * 1000.0) if active else 0,
    )


def _send_stop_frames(sock: socket.socket, destination: tuple[str, int], sequence: int) -> None:
    for _ in range(5):
        sequence = (sequence + 1) & 0xFFFFFFFF
        sock.sendto(encode_command(GatewayCommand(sequence, False, False, 0, 0, 0)), destination)
        time.sleep(0.01)


def _run_sender(
    reader: DualSenseReader,
    host: str,
    port: int,
    rate_hz: float,
) -> None:
    destination = (host, port)
    period_s = 1.0 / rate_hz
    sequence = int(time.monotonic_ns()) & 0xFFFFFFFF
    next_send = time.monotonic()
    last_print = 0.0
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        while True:
            command = _make_command(reader, sequence)
            sock.sendto(encode_command(command), destination)
            now = time.monotonic()
            if now - last_print >= 1.0:
                print(
                    f"udp->{host}:{port} connected={int(command.connected)} "
                    f"deadman={int(command.deadman)} "
                    f"twist={command.vx_mm_s},{command.vy_mm_s},"
                    f"{command.omega_mrad_s}",
                    flush=True,
                )
                last_print = now
            sequence = (sequence + 1) & 0xFFFFFFFF
            next_send += period_s
            delay = next_send - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_send = time.monotonic()
    finally:
        try:
            _send_stop_frames(sock, destination, sequence)
        finally:
            sock.close()


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Send DualSense commands to the DSD ESP32 Wi-Fi/CAN gateway"
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="ESP32 IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--rate-hz", type=float, default=50.0)
    parser.add_argument("--preferred-id", default="")
    parser.add_argument("--max-v-mps", type=float, default=1.0)
    parser.add_argument("--max-omega-rad-s", type=float, default=3.0)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        _self_check()
        return 0
    if not (1.0 <= args.rate_hz <= 200.0):
        parser.error("--rate-hz must be between 1 and 200")
    if not (1 <= args.port <= 65535):
        parser.error("--port must be between 1 and 65535")

    config = ControlConfig(
        max_linear_speed_mps=max(0.0, args.max_v_mps),
        max_angular_speed_rad_s=max(0.0, args.max_omega_rad_s),
    )
    reader = DualSenseReader(DualSenseMapper(config), preferred_id=args.preferred_id)
    signal.signal(signal.SIGTERM, lambda _signum, _frame: raise_keyboard_interrupt())
    reader.start()
    try:
        _run_sender(reader, args.host, args.port, args.rate_hz)
    except KeyboardInterrupt:
        pass
    finally:
        reader.stop()
    return 0


def raise_keyboard_interrupt() -> None:
    raise KeyboardInterrupt


if __name__ == "__main__":
    raise SystemExit(main())
