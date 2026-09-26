# Drive V2 UART header check — 2026-09-23

Replaced TP901 (MCU TX), TP902 (MCU RX), and TP903 (GND) on the V2 root schematic with J9 `Connector_Generic:Conn_01x03`. Its footprint is `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` (three through-hole 1.7 mm pads on 2.54 mm centers; pad 1 is square).

| J9 pin | Net | MCU |
|---:|---|---|
| 1 | GND | GND |
| 2 | DBG_TX | G474 U4 PA2/pin14, MCU transmit |
| 3 | DBG_RX | G474 U4 PA3/pin17, MCU receive |

The header carries 3.3 V UART logic only; there is no power pin. No SWD, encoder, CAN, or other circuit change was made. J7 remains Cortex Debug 10-pin.

KiCad 10 ERC: **0 errors / 0 warnings**. Fresh before/after XML netlists match for all **77 existing connectivity groups** when the removed TP901–TP903 and new J9 are excluded. J9 pins 1–3 were checked in `netlist.xml`; `unit-board-schematic.pdf` root page was rendered to `uart-header-root.png` and inspected. `before-uart-header.kicad_sch` and `before-uart-header-netlist.xml` preserve the exact input; `after-uart-header-readback.kicad_sch` matches the final on-disk schematic hash.

| Item | Before SHA-256 | After SHA-256 |
|---|---|---|
| V2 schematic | `BBAEFB6F494EE7A438743BE0A4E6ABAC6C73E751D3D7F79EFE3A76189A01B7CC` | `2357C5CF302787A12266D7C7C3992C5B06E58F10AA24EFA8DBD49064E7D12C7C` |
| V2 PCB | `92D0B62896F4227BECDD5E48E334F3E3BF79F8646B1AF2C4B31741916A02DDAC` | same |
| V1 schematic | `B86109A6FFD98E718EF52C83562A9735AE3A24D20179AF09E7C4FA591097D5F3` | same |

The user will update the PCB. Its UART TP footprints and old SWD connector remain unsynchronized with this schematic.
