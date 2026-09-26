# ODOM V2 saved-file baseline audit (2026-09-25)

This audit uses the schematic and PCB saved on disk at the time of the snapshot. It does not include any unsaved KiCad editor state. Source design files were not changed. `baseline/` preserves source copies, ERC/DRC reports, and the KiCad XML netlist.

## Results

- Schematic ERC: **0** errors/warnings.
- Original PCB DRC: **62** violations, **4** unconnected items, with no project DRC exclusions. A zone refill on an isolated candidate copy reduced this to **33** violations and the same 4 unconnected items; many original zone-via violations were stale fill.
- After isolated candidate track-width and dangling-stub fixes: **20** violations and **4** unconnected items. `candidate/drc-dangling.rpt` is the full report. `--schematic-parity` additionally finds **48** parity issues.
- `candidate/Oddom board.kicad_pcb` is a work-in-progress copy, not production-ready. It has refilled zones, 15 RUN/ERR track segments increased from 0.175 to 0.200 mm, and a disconnected 0.0583 mm D1 IO_1 spur removed. It has not been merged into the source board.

## Critical schematic/PCB mismatches

| Circuit | Schematic | Saved PCB |
|---|---|---|
| SWD | J8, Cortex 10pin: 1=3V3, 2=SWDIO, 3/5/9=GND, 4=SWCLK, 6=SWO, 7/8=NC, 10=NRST; footprint unassigned | J3 is the physical 10pin SWD footprint with those nets. Its reference differs from the schematic. |
| Auxiliary 3pin connector | J2, GH3: 1/2=D1 IO_1/IO_2, 3=GND | J8 is the corresponding GH3 footprint; its mounting pads are numbered 4/5. |
| AMT102 connectors J4/J5/J6 | Each 1=5V, 2=GND, 3=A, 4=B (as required by `STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`) | Each 1=A, 2=5V, 3=B, 4=GND. This is a real harness pinout mismatch; do not fabricate or connect sensors in the current layout. |
| Input RC capacitors | C15, C17, C23–C26 specified, one on each buffer input | All six footprints absent. R2/R5/R6–R9 and U3/U7/U9 input nets retain the old `Net-(R*-Pad2)` names. |

J9 UART matches exactly: 1=GND, 2=USART2_TX, 3=USART2_RX. U3/U7/U9 each have pin 2=GND and pin 5=PWR_3.3V in the PCB pad assignments. MCU U1 VCAP_1 (pin 31) and VCAP_2 (pin 47) each connect to a separate capacitor (C20/C21) to GND. These are logical pad assignments; routing connectivity remains subject to DRC.

## Candidate DRC still open

- 9 clearance violations (PWR_3.3V, NRST, RUN, GND, nearby vias/pads). Minimum is 0.200 mm; actual 0.125–0.1968 mm. Several need local rerouting and must not be solved by weakening the rule.
- 5 copper-to-edge violations: J8 old GH3 mounting pads (0.25 mm), D4 (0.45), D1 (0.35), D3 (0.45), against 0.50 mm minimum. These need footprint movement and rerouting, or an explicitly reviewed edge-constraint decision.
- 4 unconnected items: U1 pad 12 GND and three PWR_3.3V trace groups, at positions in `candidate/drc-dangling.rpt`. Refill did not clear them.
- 1 isolated GND-plane copper fill warning.
- 4 library footprint mismatch warnings (SW3, J7, U7, D1). Compare embedded vs installed library geometry before updating footprints. No library substitutions were made.
- The candidate project's copied library tables were adjusted to point to `hardware/lib` so it can be opened independently; that table change is confined to the candidate.

The KiCad project also has several DRC checks set to Ignore, including missing courtyards and selected silkscreen checks. No DRC exclusions were present. Before fabrication, rerun enabled DRC, schematic parity, and a full pad-net audit on the final saved sources.
