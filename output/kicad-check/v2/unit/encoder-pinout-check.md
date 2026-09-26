# Drive V2 AMT22 connector J6 pinout check (2026-09-23)

The requested order is already present in `hardware/unit-board-v2/unit-board.kicad_sch`. No schematic, PCB, or V1 edits were needed.

| J6 pin | Requested signal | Existing connection traced in fresh KiCad XML netlist | Result |
|---:|---|---|---|
| 1 | +5V | `/CAN Interface/PWR_5V` | match |
| 2 | SCLK | R15 pin1 -> R15 pin2 -> `/G474 Minimum/SPI3_SCK` -> U4 pin52 | match |
| 3 | MOSI | R16 pin1 -> R16 pin2 -> `/G474 Minimum/SPI3_MOSI` -> U4 pin54 | match |
| 4 | GND | `GND` | match |
| 5 | MISO | R17 pin1 -> R17 pin2 -> `/G474 Minimum/SPI3_MISO` -> U4 pin53 | match |
| 6 | CHIP SELECT | R18 pin1 -> R18 pin2 -> `/G474 Minimum/AMT22_CS_N` -> U4 pin55 | match |

The four series resistors R15-R18 remain 0 ohm. J6 remains `SM06B-GHS-TB` with `Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal`.

KiCad 10 `sch erc` on the current V2 schematic: 0 violations. Fresh netlist: `netlist.xml`. Fresh PDF: `unit-board-schematic.pdf`; its root page was rendered to `root.png` and the J6 wiring was visually checked. Because the schematic was not edited, all other connections remain unchanged.

SHA-256 before and after the check:

| File | SHA-256 |
|---|---|
| `hardware/unit-board-v2/unit-board.kicad_sch` | `BBAEFB6F494EE7A438743BE0A4E6ABAC6C73E751D3D7F79EFE3A76189A01B7CC` |
| `hardware/unit-board-v2/unit-board.kicad_pcb` | `92D0B62896F4227BECDD5E48E334F3E3BF79F8646B1AF2C4B31741916A02DDAC` |
| `hardware/unit-board/unit-board.kicad_sch` | `B86109A6FFD98E718EF52C83562A9735AE3A24D20179AF09E7C4FA591097D5F3` |
| `hardware/unit-board/unit-board.kicad_pcb` | `92D0B62896F4227BECDD5E48E334F3E3BF79F8646B1AF2C4B31741916A02DDAC` |

Separate inventory only: J2/J3 (main CAN) and J4/J5 (C620 CAN) are currently horizontal JST GH 3-pin connectors with pins 1=A/H, 2=B/L, 3=GND. No CAN change was made during this check.
