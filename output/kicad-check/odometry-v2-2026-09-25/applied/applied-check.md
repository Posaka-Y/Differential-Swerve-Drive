# ODOM V2 saved-board correction (2026-09-25)

The user's new save changed the schematic but left the PCB byte-identical to the earlier PCB snapshot (`E083D5B0…`). The full saved project was copied to `before/` before editing. The source schematic was not edited.

Applied to the current source PCB only:

- Refilled zones and saved the board.
- Increased all fifteen original 0.175 mm RUN/ERR segments to 0.200 mm, matching the project minimum width.
- Removed one 0.0583 mm disconnected D1 IO_1 spur; the continuous D1 IO_1 route remains.
- Cleared `Do not populate` on J3 SWD only to match the saved schematic.

Verification: schematic ERC has two footprint-link warnings for unqualified J3/J8 library names and no electrical errors. The corresponding `SamacSys` footprints are embedded in the PCB but no verified `SamacSys` library is configured locally, so no guessed footprint substitution was made. Board DRC changed from 62 violations plus four unconnected items to **20 violations plus four unconnected items**. It is **not fabrication-ready**. Remaining DRC: nine clearance, five copper-edge clearance, one isolated copper, and four library-footprint mismatch warnings; four GND/3V3 routing gaps. No design rules were relaxed.

The saved schematic now matches the existing PCB reference/pad mapping except for the spelling of U5 NC pin 4 (`N/C` vs `N{slash}C`). J3 is SWD, J8 is the 3pin auxiliary connector, and J9 UART is 1=GND, 2=MCU TX, 3=MCU RX. KiCad's schematic-parity DRC still reports six footprint issues: missing configured library prefixes for J3/J8, J8 DNP mismatch, and two `REF**` mounting holes (extra/duplicate). J8 DNP and `REF**` were left unchanged.

**Design mismatch requiring a decision before manufacture:** the saved schematic and PCB now both assign AMT102 J4/J5/J6 pins 1=A, 2=5V, 3=B, 4=GND; `docs/electrical/STM32F405_ODOMETRY_PIN_ASSIGNMENT.md` specifies 1=5V, 2=GND, 3=A, 4=B. The saved schematic also removed C15/C17/C23–C26, which were the six AMT102 buffer input RC capacitors in the earlier schematic. This task did not change these connector nets or restore components.

Artifacts: `before/` snapshot, `before-hashes.txt`, `after-hashes.txt`, `erc-after.rpt`, `drc-after.rpt`, `drc-parity-after.rpt`, `netlist-after.xml`, `pad-audit-after.txt`, and `readback-board.kicad_pcb`.
