#!/usr/bin/env sh
set -eu
configuration="${1:-debug}"
case "$configuration" in
  debug|release) ;;
  *) echo "Usage: $0 [debug|release]" >&2; exit 2 ;;
esac
firmware_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$firmware_root"
cmake --preset "$configuration"
cmake --build --preset "$configuration"
