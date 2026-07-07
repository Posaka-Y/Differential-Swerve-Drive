#!/usr/bin/env sh
set -eu
configuration="${1:-debug}"
firmware_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
"$firmware_root/scripts/build.sh" "$configuration"
image="$firmware_root/build/$configuration/differential_swerve_firmware.bin"
command -v st-flash >/dev/null 2>&1 || {
  echo "st-flash is not in PATH. Install with: sudo apt-get install stlink-tools" >&2
  exit 1
}
st-flash --reset write "$image" 0x08000000
