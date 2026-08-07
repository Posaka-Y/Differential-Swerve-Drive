#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
central_dir="$(cd "${script_dir}/.." && pwd)"
build_dir="${central_dir}/build/host"

cmake -S "${central_dir}" -B "${build_dir}" -G Ninja
cmake --build "${build_dir}"
ctest --test-dir "${build_dir}" --output-on-failure
