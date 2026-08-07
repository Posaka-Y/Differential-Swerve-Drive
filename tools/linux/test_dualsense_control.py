#!/usr/bin/env python3

import math
import unittest

from evdev import ecodes

from dualsense_control import (
    ControlConfig,
    DualSenseMapper,
    normalize_centered,
    normalize_trigger,
    radial_deadzone,
)


class NormalizeTest(unittest.TestCase):
    def test_centered_endpoints(self):
        self.assertEqual(normalize_centered(0), -1.0)
        self.assertEqual(normalize_centered(255), 1.0)
        self.assertLess(abs(normalize_centered(128)), 0.01)

    def test_trigger_endpoints(self):
        self.assertEqual(normalize_trigger(0), 0.0)
        self.assertEqual(normalize_trigger(255), 1.0)

    def test_radial_deadzone(self):
        self.assertEqual(radial_deadzone(0.05, -0.05, 0.10), (0.0, 0.0))
        x, y = radial_deadzone(1.0, 1.0, 0.10)
        self.assertAlmostEqual(math.hypot(x, y), 1.0, places=6)


class MapperSafetyTest(unittest.TestCase):
    def setUp(self):
        config = ControlConfig(
            stick_deadzone=0.0,
            stick_linear_mix=1.0,
            minimum_speed_scale=0.25,
            max_linear_speed_mps=2.0,
            max_angular_speed_rad_s=4.0,
        )
        self.mapper = DualSenseMapper(config)
        self.mapper.set_connected(True, device_path="test", device_name="DualSense")

    def test_sticks_cannot_command_without_deadman(self):
        self.mapper.update_axis(ecodes.ABS_Y, 0)
        self.mapper.update_axis(ecodes.ABS_X, 255)
        state = self.mapper.snapshot()
        self.assertFalse(state.command_active)
        self.assertEqual((state.vx_mps, state.vy_mps, state.omega_rad_s), (0.0, 0.0, 0.0))

    def test_body_axis_convention_and_r2_scaling(self):
        self.mapper.update_axis(ecodes.ABS_Y, 0)
        self.mapper.update_axis(ecodes.ABS_X, 255)
        self.mapper.update_axis(ecodes.ABS_RX, 255)
        self.mapper.update_button(ecodes.BTN_TR, True)
        low = self.mapper.snapshot()
        diagonal_component = math.sqrt(0.5)
        self.assertAlmostEqual(low.vx_mps, diagonal_component * 0.5)
        self.assertAlmostEqual(low.vy_mps, -diagonal_component * 0.5)
        self.assertAlmostEqual(low.omega_rad_s, -1.0)

        self.mapper.update_axis(ecodes.ABS_RZ, 255)
        full = self.mapper.snapshot()
        self.assertAlmostEqual(full.vx_mps, diagonal_component * 2.0)
        self.assertAlmostEqual(full.vy_mps, -diagonal_component * 2.0)
        self.assertAlmostEqual(full.omega_rad_s, -4.0)

    def test_deadman_release_zeros_same_snapshot(self):
        self.mapper.update_axis(ecodes.ABS_Y, 0)
        self.mapper.update_button(ecodes.BTN_TR, True)
        self.assertGreater(self.mapper.snapshot().vx_mps, 0.0)
        self.mapper.update_button(ecodes.BTN_TR, False)
        self.assertEqual(self.mapper.snapshot().vx_mps, 0.0)

    def test_disconnect_clears_buttons_and_axes(self):
        self.mapper.update_axis(ecodes.ABS_Y, 0)
        self.mapper.update_button(ecodes.BTN_TR, True)
        self.mapper.set_connected(False)
        state = self.mapper.snapshot()
        self.assertFalse(state.connected)
        self.assertFalse(state.deadman)
        self.assertEqual((state.left_x, state.left_y), (0.0, 0.0))
        self.assertEqual((state.vx_mps, state.vy_mps, state.omega_rad_s), (0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
