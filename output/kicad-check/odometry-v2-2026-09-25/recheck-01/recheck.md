# ODOM V2 read-only recheck — 2026-09-25

The saved source project was copied before checking. Source PCB SHA256 `10D08826275137C0CB295220E385B46A812CA67F258BA001A54D70A3E0034071` was unchanged by this recheck. No zone refill or edits were made.

## Result

- ERC: 0 electrical errors, 2 footprint-library-link warnings (J3/J8 symbols use unqualified footprint names while `SamacSys` library is not configured).
- PCB DRC: **8 violations + 3 unconnected items**, improved from the prior **20 + 4**. No clearance or track-width errors now.
- Schematic parity: 6 footprint issues, unchanged from the prior check: two unqualified J3/J8 footprint identifiers, J8 DNP mismatch, and two extra `REF**` mounting holes (one duplicate-reference warning).
- XML schematic netlist vs PCB pads: all ordinary named pads match. One textual NC-net escape differs at U5 pad 4 (`N/C` vs `N{slash}C`); both denote the same unconnected pin. Extra empty-number pads are footprint graphics/mechanical features.
- J3 SWD: 1=3V3, 2=SWDIO, 3/5/9=GND, 4=SWCLK, 6=SWO, 7/8=NC, 10=NRST; PCB J3 DNP is clear. J8 is the 3pin CAN connector. J9 UART is 1=GND, 2=USART2_TX, 3=USART2_RX.
- The user's intentional encoder order is consistent across all three PCB connectors and current schematic: J4/5/6 1=A, 2=5V, 3=B, 4=GND.

## Remaining DRC, with locations in mm

| Type | Location | Detail |
|---|---|---|
| Copper-edge clearance | J8 mounting pads 4 `(74.675,113.375)` and 5 `(68.475,113.375)` | 0.225 mm to edge; configured minimum 0.500 mm |
| Dangling track | `(76.5765,105.825)` | PWR_3.3V on `Power Signal`, length 2.0142 mm |
| Dangling via | `(75.3375,92.7125)` | `Net-(R9-Pad2)`, F.Cu–B.Cu |
| Isolated fill | GND Plane, board rectangle origin `(67.5,85)` | KiCad isolated-copper warning |
| Library footprint mismatch | SW3 `(108.925,96.3375)`, J7 `(129.525,112.15)`, U7 `(123.575,93.475)` | Embedded footprints differ from current installed library copies; inspect geometry before updating |
| Unconnected GND | U1 pad 12 `(92.1253,101.0504)` to C14 pad 2 `(95.673,101.152)` | Missing copper connection |
| Unconnected 3V3 | U1 pad 32 `(88.2362,91.6105)` to 3V3 track `(94.5673,94.4718)` | Missing copper connection |
| Unconnected 3V3 | Track `(104.725,104.7352)` to track `(111.025,104.7352)` | Missing copper connection |

The project `.kicad_pro` hash remains `61D8FDF32F32DC2B5974607D88D013A2B51CCEA1113731D0D1FEE2B4B1C23B2B`, unchanged from the previous applied check; ignored DRC categories and exclusions were not changed. The report lists ignored courtyard, via-centering, tuning-profile, footprint-filter, silkscreen, and component-type checks. No DRC exclusions are recorded.
