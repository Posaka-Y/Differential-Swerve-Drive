#!/usr/bin/env python3
"""DualSense input and safety mapping for the mini PC.

This module intentionally has no motor, CAN, or serial output.  It turns the
Linux evdev representation of a Sony DualSense into a body-twist preview that
can later be handed to the Teensy USB transport.  Keeping input acquisition
separate from the transport makes it possible to test disconnect and deadman
behaviour without energising the drivetrain.
"""

from __future__ import annotations

import argparse
import errno
import json
import math
import select
import signal
import threading
import time
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Optional, Tuple

from evdev import InputDevice, ecodes, list_devices


SONY_VENDOR_ID = 0x054C
DUALSENSE_PRODUCT_ID = 0x0CE6


@dataclass(frozen=True)
class ControlConfig:
    stick_deadzone: float = 0.10
    stick_linear_mix: float = 0.35
    minimum_speed_scale: float = 0.25
    max_linear_speed_mps: float = 1.0
    max_angular_speed_rad_s: float = 3.0


@dataclass(frozen=True)
class ControlSnapshot:
    connected: bool
    device_path: str
    device_name: str
    transport: str
    controller_id: str
    sample_sequence: int
    sample_age_ms: Optional[float]
    left_x: float
    left_y: float
    right_x: float
    right_y: float
    left_trigger: float
    right_trigger: float
    deadman: bool
    options: bool
    ps: bool
    speed_scale: float
    command_active: bool
    vx_mps: float
    vy_mps: float
    omega_rad_s: float

    def to_dict(self) -> dict:
        return asdict(self)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_centered(raw: int, minimum: int = 0, maximum: int = 255) -> float:
    """Normalize an asymmetric integer stick range to [-1, 1]."""
    if maximum <= minimum:
        return 0.0
    center = (minimum + maximum) * 0.5
    if raw >= center:
        denominator = maximum - center
    else:
        denominator = center - minimum
    if denominator <= 0.0:
        return 0.0
    return _clamp((raw - center) / denominator, -1.0, 1.0)


def normalize_trigger(raw: int, minimum: int = 0, maximum: int = 255) -> float:
    if maximum <= minimum:
        return 0.0
    return _clamp((raw - minimum) / float(maximum - minimum), 0.0, 1.0)


def radial_deadzone(x: float, y: float, deadzone: float) -> Tuple[float, float]:
    """Apply a circular deadzone and remap the remaining radius to [0, 1]."""
    deadzone = _clamp(deadzone, 0.0, 0.95)
    magnitude = math.hypot(x, y)
    if magnitude <= deadzone or magnitude == 0.0:
        return 0.0, 0.0
    limited = min(magnitude, 1.0)
    remapped = (limited - deadzone) / (1.0 - deadzone)
    scale = remapped / magnitude
    return _clamp(x * scale, -1.0, 1.0), _clamp(y * scale, -1.0, 1.0)


def response_curve(value: float, linear_mix: float) -> float:
    linear_mix = _clamp(linear_mix, 0.0, 1.0)
    return linear_mix * value + (1.0 - linear_mix) * value * value * value


class DualSenseMapper:
    """Pure evdev-code to safe command mapper."""

    _AXIS_CODES = {
        ecodes.ABS_X: "left_x",
        ecodes.ABS_Y: "left_y",
        ecodes.ABS_RX: "right_x",
        ecodes.ABS_RY: "right_y",
        ecodes.ABS_Z: "left_trigger",
        ecodes.ABS_RZ: "right_trigger",
    }

    def __init__(self, config: ControlConfig = ControlConfig()) -> None:
        self.config = config
        self.connected = False
        self.device_path = ""
        self.device_name = ""
        self.transport = ""
        self.controller_id = ""
        self.sample_sequence = 0
        self.last_sample_monotonic: Optional[float] = None
        self._axes: Dict[str, float] = {
            "left_x": 0.0,
            "left_y": 0.0,
            "right_x": 0.0,
            "right_y": 0.0,
            "left_trigger": 0.0,
            "right_trigger": 0.0,
        }
        self._buttons: Dict[int, bool] = {}

    def set_connected(
        self,
        connected: bool,
        *,
        device_path: str = "",
        device_name: str = "",
        transport: str = "",
        controller_id: str = "",
    ) -> None:
        self.connected = connected
        self.device_path = device_path if connected else ""
        self.device_name = device_name if connected else ""
        self.transport = transport if connected else ""
        self.controller_id = controller_id if connected else ""
        if not connected:
            self._buttons.clear()
            for key in self._axes:
                self._axes[key] = 0.0
            self.last_sample_monotonic = None
        self.sample_sequence += 1

    def update_axis(
        self,
        code: int,
        raw: int,
        minimum: int = 0,
        maximum: int = 255,
        *,
        now: Optional[float] = None,
    ) -> None:
        name = self._AXIS_CODES.get(code)
        if name is None:
            return
        if name.endswith("trigger"):
            value = normalize_trigger(raw, minimum, maximum)
        else:
            value = normalize_centered(raw, minimum, maximum)
        self._axes[name] = value
        self._sample(now)

    def update_button(self, code: int, pressed: bool, *, now: Optional[float] = None) -> None:
        self._buttons[code] = pressed
        self._sample(now)

    def _sample(self, now: Optional[float]) -> None:
        self.last_sample_monotonic = time.monotonic() if now is None else now
        self.sample_sequence += 1

    def snapshot(self, *, now: Optional[float] = None) -> ControlSnapshot:
        current_time = time.monotonic() if now is None else now
        left_x, left_y = radial_deadzone(
            self._axes["left_x"], self._axes["left_y"], self.config.stick_deadzone
        )
        right_x, right_y = radial_deadzone(
            self._axes["right_x"], self._axes["right_y"], self.config.stick_deadzone
        )
        left_x = response_curve(left_x, self.config.stick_linear_mix)
        left_y = response_curve(left_y, self.config.stick_linear_mix)
        right_x = response_curve(right_x, self.config.stick_linear_mix)
        right_y = response_curve(right_y, self.config.stick_linear_mix)

        deadman = self.connected and self._buttons.get(ecodes.BTN_TR, False)
        options = self.connected and self._buttons.get(ecodes.BTN_START, False)
        ps = self.connected and self._buttons.get(ecodes.BTN_MODE, False)
        speed_scale = self.config.minimum_speed_scale + (
            1.0 - self.config.minimum_speed_scale
        ) * self._axes["right_trigger"]
        speed_scale = _clamp(speed_scale, 0.0, 1.0)
        command_active = bool(deadman)

        if command_active:
            # Body convention is +X forward, +Y left, +omega counter-clockwise.
            vx_mps = -left_y * self.config.max_linear_speed_mps * speed_scale
            vy_mps = -left_x * self.config.max_linear_speed_mps * speed_scale
            omega_rad_s = -right_x * self.config.max_angular_speed_rad_s * speed_scale
        else:
            vx_mps = 0.0
            vy_mps = 0.0
            omega_rad_s = 0.0

        age_ms = None
        if self.connected and self.last_sample_monotonic is not None:
            age_ms = max(0.0, (current_time - self.last_sample_monotonic) * 1000.0)

        return ControlSnapshot(
            connected=self.connected,
            device_path=self.device_path,
            device_name=self.device_name,
            transport=self.transport,
            controller_id=self.controller_id,
            sample_sequence=self.sample_sequence,
            sample_age_ms=age_ms,
            left_x=left_x,
            left_y=left_y,
            right_x=right_x,
            right_y=right_y,
            left_trigger=self._axes["left_trigger"],
            right_trigger=self._axes["right_trigger"],
            deadman=deadman,
            options=options,
            ps=ps,
            speed_scale=speed_scale,
            command_active=command_active,
            vx_mps=vx_mps,
            vy_mps=vy_mps,
            omega_rad_s=omega_rad_s,
        )


def _is_dualsense(device: InputDevice) -> bool:
    return device.info.vendor == SONY_VENDOR_ID and device.info.product == DUALSENSE_PRODUCT_ID


def _transport_name(device: InputDevice) -> str:
    if device.info.bustype == ecodes.BUS_BLUETOOTH:
        return "Bluetooth"
    if device.info.bustype == ecodes.BUS_USB:
        return "USB"
    return f"bus-{device.info.bustype:04x}"


def find_dualsense(preferred_id: str = "") -> Optional[InputDevice]:
    """Find the main DualSense gamepad event node, not motion/touch nodes."""
    candidates = []
    for path in list_devices():
        try:
            device = InputDevice(path)
        except (OSError, PermissionError):
            continue
        if not _is_dualsense(device):
            device.close()
            continue
        capabilities = device.capabilities()
        abs_codes = {
            entry[0] if isinstance(entry, tuple) else entry
            for entry in capabilities.get(ecodes.EV_ABS, [])
        }
        if ecodes.ABS_X not in abs_codes or ecodes.ABS_Y not in abs_codes:
            device.close()
            continue
        preferred = bool(preferred_id and device.uniq.lower() == preferred_id.lower())
        candidates.append((not preferred, path, device))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    selected = candidates[0][2]
    for _, _, device in candidates[1:]:
        device.close()
    return selected


class DualSenseReader:
    """Reconnect-capable background evdev reader."""

    def __init__(
        self,
        mapper: Optional[DualSenseMapper] = None,
        *,
        preferred_id: str = "",
        reconnect_interval_s: float = 1.0,
    ) -> None:
        self.mapper = mapper or DualSenseMapper()
        self.preferred_id = preferred_id
        self.reconnect_interval_s = reconnect_interval_s
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="dualsense-reader", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        with self._lock:
            self.mapper.set_connected(False)

    def snapshot(self) -> ControlSnapshot:
        with self._lock:
            return self.mapper.snapshot()

    def _initialize_from_device(self, device: InputDevice) -> None:
        active_keys = set(device.active_keys())
        with self._lock:
            self.mapper.set_connected(
                True,
                device_path=device.path,
                device_name=device.name,
                transport=_transport_name(device),
                controller_id=device.uniq or "",
            )
            for code in DualSenseMapper._AXIS_CODES:
                try:
                    info = device.absinfo(code)
                except OSError:
                    continue
                if info is not None:
                    self.mapper.update_axis(code, info.value, info.min, info.max)
            for code in (ecodes.BTN_TR, ecodes.BTN_START, ecodes.BTN_MODE):
                self.mapper.update_button(code, code in active_keys)

    def _run(self) -> None:
        while not self._stop.is_set():
            device = find_dualsense(self.preferred_id)
            if device is None:
                with self._lock:
                    if self.mapper.connected:
                        self.mapper.set_connected(False)
                self._stop.wait(self.reconnect_interval_s)
                continue

            try:
                self._initialize_from_device(device)
                self._read_device(device)
            except OSError as exc:
                if exc.errno not in (errno.ENODEV, errno.EIO, errno.EBADF):
                    time.sleep(0.05)
            finally:
                device.close()
                with self._lock:
                    self.mapper.set_connected(False)

    def _read_device(self, device: InputDevice) -> None:
        while not self._stop.is_set():
            ready, _, _ = select.select([device.fd], [], [], 0.25)
            if not ready:
                continue
            for event in device.read():
                with self._lock:
                    if event.type == ecodes.EV_ABS:
                        info = device.absinfo(event.code)
                        if info is not None:
                            self.mapper.update_axis(event.code, event.value, info.min, info.max)
                    elif event.type == ecodes.EV_KEY:
                        self.mapper.update_button(event.code, event.value != 0)


def _self_check() -> None:
    mapper = DualSenseMapper()
    mapper.set_connected(True, device_path="test", device_name="test", transport="test")
    mapper.update_axis(ecodes.ABS_Y, 0)
    mapper.update_axis(ecodes.ABS_X, 255)
    mapper.update_axis(ecodes.ABS_RX, 255)
    mapper.update_axis(ecodes.ABS_RZ, 255)
    inactive = mapper.snapshot()
    assert inactive.vx_mps == 0.0 and inactive.vy_mps == 0.0
    mapper.update_button(ecodes.BTN_TR, True)
    active = mapper.snapshot()
    assert active.command_active
    assert active.vx_mps > 0.0 and active.vy_mps < 0.0 and active.omega_rad_s < 0.0
    mapper.set_connected(False)
    disconnected = mapper.snapshot()
    assert not disconnected.command_active
    assert disconnected.vx_mps == 0.0
    print("dualsense_control self-check: PASS")


def _monitor(reader: DualSenseReader) -> None:
    previous = None
    try:
        while True:
            snapshot = reader.snapshot().to_dict()
            rendered = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
            if rendered != previous:
                print(rendered, flush=True)
                previous = rendered
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Read and safely map a Sony DualSense")
    parser.add_argument("--preferred-id", default="", help="Bluetooth MAC/evdev uniq to prefer")
    parser.add_argument("--max-v-mps", type=float, default=1.0)
    parser.add_argument("--max-omega-rad-s", type=float, default=3.0)
    parser.add_argument("--check", action="store_true", help="run an offline self-check")
    args = parser.parse_args(argv)

    if args.check:
        _self_check()
        return 0

    config = ControlConfig(
        max_linear_speed_mps=max(0.0, args.max_v_mps),
        max_angular_speed_rad_s=max(0.0, args.max_omega_rad_s),
    )
    reader = DualSenseReader(DualSenseMapper(config), preferred_id=args.preferred_id)
    signal.signal(signal.SIGTERM, lambda _signum, _frame: raise_keyboard_interrupt())
    reader.start()
    try:
        _monitor(reader)
    finally:
        reader.stop()
    return 0


def raise_keyboard_interrupt() -> None:
    raise KeyboardInterrupt


if __name__ == "__main__":
    raise SystemExit(main())
