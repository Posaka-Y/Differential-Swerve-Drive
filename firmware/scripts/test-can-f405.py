"""Isolated V1 ODOM CAN bench: gs_usb + can_f405.hex, Classic 1 Mbps.

Install python-can, gs-usb, libusb-package in a venv. Windows requires
WinUSB on the CAN interface. Does not flash or change USB firmware.
"""
import argparse
import json
import time

import can
import libusb_package
from usb.backend import libusb1
from gs_usb.gs_usb import GsUsb
from gs_usb.gs_usb_frame import GsUsbFrame, GS_USB_NONE_ECHO_ID
from gs_usb.constants import GS_CAN_MODE_ONE_SHOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', default='003800394633500E20303035')
    parser.add_argument('--count', type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.count <= 100:
        parser.error('count must be 1..100')
    # Preload packaged DLL; gs_usb.scan reuses libusb1's cached backend.
    if libusb1.get_backend(find_library=libusb_package.find_library) is None:
        raise RuntimeError('libusb backend unavailable')
    try:
        devices = [d for d in GsUsb.scan() if d.gs_usb.serial_number == args.serial]
    except (ValueError, OSError) as exc:
        raise RuntimeError('Cannot open USB-CAN descriptors. Check WinUSB on '
                           'canable2 gs_usb (Interface 0), then reconnect USB.') from exc
    if len(devices) != 1:
        raise RuntimeError('Expected one USB-CAN with the requested serial; check WinUSB/BOOT.')
    dev = devices[0]
    timing = can.BitTiming.from_sample_point(
        f_clock=dev.device_capability.fclk_can, bitrate=1_000_000, sample_point=75)
    dev.set_timing(1, timing.tseg1 - 1, timing.tseg2, timing.sjw, timing.brp)
    matched, heartbeats, errors, usb_echoes = 0, 0, 0, 0
    print(json.dumps({'canClockHz': dev.device_capability.fclk_can,
                      'bitTiming': str(timing),
                      'oneShotSupported': bool(dev.device_capability.feature & GS_CAN_MODE_ONE_SHOT)}), flush=True)
    try:
        dev.start(flags=GS_CAN_MODE_ONE_SHOT)
        for seq in range(args.count):
            payload = list(seq.to_bytes(4, 'little') + bytes.fromhex('a55ac33c'))
            frame = GsUsbFrame(can_id=0x6E4, data=payload)
            dev.send(frame)
            deadline = time.monotonic() + 1.0
            got_reply = False
            while time.monotonic() < deadline:
                rx = GsUsbFrame()
                if not dev.read(rx, timeout_ms=50):
                    continue
                if rx.echo_id != GS_USB_NONE_ECHO_ID:
                    usb_echoes += 1
                    continue  # USB transmit echo is NOT a board response.
                if rx.is_error_frame:
                    errors += 1
                    continue
                print(json.dumps({'id': hex(rx.arbitration_id),
                                  'data': list(rx.data[:rx.can_dlc])}), flush=True)
                if rx.arbitration_id == 0x6E6:
                    heartbeats += 1
                if (rx.arbitration_id == 0x6E5 and not rx.is_extended_id
                        and not rx.is_remote_frame and rx.can_dlc == 8
                        and list(rx.data[:8]) == payload):
                    got_reply = True
            matched += int(got_reply)
    finally:
        dev.stop()
    print(json.dumps({'sent': args.count, 'matchedReplies': matched,
                      'heartbeats': heartbeats, 'errorFrames': errors,
                      'usbTxEchoes': usb_echoes}))
    return 0 if matched == args.count and heartbeats > 0 and errors == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
