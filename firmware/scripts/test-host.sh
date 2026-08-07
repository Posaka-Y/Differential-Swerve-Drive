#!/usr/bin/env sh
set -eu

firmware_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_build_dir=$(mktemp -d)
trap 'rm -rf -- "$test_build_dir"' EXIT HUP INT TERM

cc -std=c11 -Wall -Wextra -Werror \
  -I"$firmware_root/include" \
  "$firmware_root/src/control/unit_controller.c" \
  "$firmware_root/tests/unit_controller_observer_test.c" \
  -lm \
  -o "$test_build_dir/unit_controller_observer_test"

"$test_build_dir/unit_controller_observer_test"

cc -std=c11 -Wall -Wextra -Werror \
  -I"$firmware_root/include" \
  "$firmware_root/src/config/steer_calibration.c" \
  "$firmware_root/tests/steer_calibration_test.c" \
  -o "$test_build_dir/steer_calibration_test"

"$test_build_dir/steer_calibration_test"
