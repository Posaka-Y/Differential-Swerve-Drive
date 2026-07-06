#!/usr/bin/env sh
set -eu
configuration="${1:-debug}"
firmware_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
"$firmware_root/scripts/build.sh" "$configuration"
image="$firmware_root/build/$configuration/differential_swerve_firmware.hex"
command -v STM32_Programmer_CLI >/dev/null 2>&1 || {
  echo "STM32_Programmer_CLI is not in PATH." >&2
  exit 1
}
STM32_Programmer_CLI -c port=SWD -w "$image" -v -rst
