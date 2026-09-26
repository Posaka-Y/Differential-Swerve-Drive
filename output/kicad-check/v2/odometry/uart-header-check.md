# ODOM V2 UART header check — 2026-09-23

Replaced TP901 (MCU TX), TP902 (MCU RX), and TP903 (GND) on the V2 root schematic with J9 `Connector_Generic:Conn_01x03`. Its footprint is `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` (three through-hole 1.7 mm pads on 2.54 mm centers; pad 1 is square).

| J9 pin | Net | MCU |
|---:|---|---|
| 1 | GND | GND |
| 2 | USART2_TX | F405 U1 PA2/pin16, MCU transmit |
| 3 | USART2_RX | F405 U1 PA3/pin17, MCU receive |

The header carries 3.3 V UART logic only; there is no power pin. No SWD, encoder, CAN, or other circuit change was made. J8 remains Cortex Debug 10-pin, and U3/U7/U9 buffer pins 2=GND and 5=PWR_3.3V remain connected.

KiCad 10 ERC: **0 errors / 0 warnings**. Fresh before/after XML netlists match for all **85 existing connectivity groups** when the removed TP901–TP903 and new J9 are excluded. J9 pins 1–3 were checked in `netlist.xml`; `Oddom board-schematic.pdf` root page was rendered to `uart-header-root.png` and inspected. `before-uart-header.kicad_sch` and `before-uart-header-netlist.xml` preserve the exact input; `after-uart-header-readback.kicad_sch` matches the final on-disk schematic hash.

| Item | Before SHA-256 | After SHA-256 |
|---|---|---|
| V2 schematic | `8E5368F18549FF738ACDDE3E4B4F32CDA8742AA423AC5F61BBD0A5F6453DBD37` | `54108771B7340E4AB34955E3DBE29BE677349A53B2D5A020D0CB86BA42F37FE6` |
| V2 PCB | `44103119ED39950D6AC97538EF0CAECB463D385B02D30FB40472E483FEACF6FC` | same |
| V1 schematic | `F0E01B1D4301B5858E39CCDE9C6308616BBF0BECF658C0A76AF5E919ADAEB176` | same |

The user will update the PCB. Its UART TP footprints and old SWD connector remain unsynchronized with this schematic.
