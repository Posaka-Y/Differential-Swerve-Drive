# Central nonpower wiring — 2026-09-29

Scope and results: [design record](../../../docs/electrical/CENTRAL_NONPOWER_WIRING_2026-09-29.md).

Before snapshot is under `before/central-board-placement/`. `before.net` / `after.net` are KiCad exports, `expected-pins.json` is the migration pin contract, `audit.json` contains the independent connector / Teensy / preserved-sheet checks. `before-erc.rpt` / `after-erc.rpt` use the existing project rules without changing exclusions.

ERC 193 → 4; four remaining errors are power-pin drive declarations in excluded CAN sheets. Safety TBDs are still unresolved even when ERC is clear. X401/X402 are functional placeholders with no selected device/footprint; X402 does not join its three nets.

Rendered SVG/PNG files are visual QA, not a fabrication release. No PCB or firmware changes.
