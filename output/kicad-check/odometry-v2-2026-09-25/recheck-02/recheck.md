# ODOM V2 read-only recheck 02 — 2026-09-25

Saved source project files were snapshotted and hashed in this directory. The source was not edited. No zone refill was necessary. The project `.kicad_pro` hash is still `61D8FDF32F32DC2B5974607D88D013A2B51CCEA1113731D0D1FEE2B4B1C23B2B`; DRC exclusions and ignored-check settings are unchanged.

## Result

- DRC **7 violations + 1 unconnected item**, improved from recheck 01's **8 + 3**. The R9-input dangling via and two of the three unconnected items are resolved. No track-width or net-clearance errors.
- ERC: 0 electrical errors, 2 footprint-link warnings for unqualified J3/J8 names. Schematic parity: 6 footprint issues, same categories as recheck 01.
- Netlist vs PCB pad audit: no functional net mismatch. The sole string difference is U5 pad 4's NC name escape (`N/C` versus `N{slash}C`). J3 SWD, J8 CAN, J9 UART, and the intentional encoder order J4/J5/J6 `1=A, 2=+5V, 3=B, 4=GND` remain consistent with the current schematic.

## Remaining DRC

| Type | Position / item | Finding |
|---|---|---|
| Copper-edge clearance ×2 | J8 mounting pads 4 `(74.675,113.375)` and 5 `(68.475,113.375)` mm | Actual 0.225 mm vs 0.500 mm rule |
| Dangling track | `(76.5765,105.825)` mm | PWR_3.3V, Power Signal layer, 2.0142 mm segment |
| Isolated copper | GND Plane zone, board rectangle origin `(67.5,85)` mm | Isolated fill warning |
| Embedded footprint/library mismatch ×3 | SW3 `(108.925,96.3375)`, J7 `(129.525,112.15)`, U7 `(123.575,93.475)` mm | Requires geometry review before updating |
| Unconnected item ×1 | PWR_3.3V F.Cu track `(104.725,104.7352)` to PWR_3.3V Power Signal track `(109.475,103.1852)` mm | Missing copper connection |

The full KiCad reports are `erc.rpt`, `drc.rpt`, and `drc-parity.rpt`; `netlist.xml` and `pads.txt` contain the electrical pad comparison.
