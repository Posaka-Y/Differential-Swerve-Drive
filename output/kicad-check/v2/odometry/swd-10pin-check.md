# ODOM V2 Cortex Debug 10-pin schematic check — 2026-09-23

Edited only `hardware/odometry-board-v2/Oddom board.kicad_sch`. Replaced J8 GH6 with generic `Connector_Generic:Conn_02x05_Odd_Even`; its Footprint property is deliberately blank pending a keyed header MPN and cable choice. Added separate UART test pads TP901–TP903 with `TestPoint:TestPoint_Pad_D1.5mm` footprints.

| J8 pin | Old connection | New connection | STM32F405 U1 pin |
|---:|---|---|---:|
| 1 | GND | PWR_3.3V (VTref; same digital rail as VDD) | VDD 19/32/48/64 and VBAT 1 |
| 2 | SWCLK | SWDIO / PA13 | 46 |
| 3 | SWDIO | GND | VSS 18/63 and VSSA 12 |
| 4 | NRST | SWCLK / PA14 | 49 |
| 5 | USART2_TX | GND | VSS 18/63 and VSSA 12 |
| 6 | USART2_RX | SWO / PB3 | 55 |
| 7 | — | NC (key/reserved) | — |
| 8 | — | NC (TDI unused in SWD) | — |
| 9 | — | GND detect | VSS 18/63 and VSSA 12 |
| 10 | — | NRST | 7 |

| New test pad | Connection | U1 pin |
|---|---|---:|
| TP901 | USART2_TX / PA2 | 16 |
| TP902 | USART2_RX / PA3 | 17 |
| TP903 | GND | — |

PB3/U1 pin55 was NC before this change, so SWO has no existing function conflict. The U3/U7/U9 buffer power units remain pin2=GND and pin5=PWR_3.3V for all three ICs.

Verification: KiCad 10 schematic ERC **0 errors, 0 warnings** (`Oddom board-erc.rpt`). Fresh before/after XML netlists match for all **82 existing connectivity groups** when the deliberately changed J8, new TP901–TP903 and PB3/U1 pin55 are excluded. The complete new J8 and TP pin mapping above is confirmed by the new XML (`netlist.xml`). The exported five-page PDF (`Oddom board-schematic.pdf`) root page was rendered to `root-after.png` and inspected; J8, TP labels and notes are legible without collisions. `before-swd.kicad_sch` is the pre-edit snapshot; `before-swd-netlist.xml` is its netlist.

| File | Before SHA-256 | After SHA-256 |
|---|---|---|
| ODOM V2 schematic | `F0E01B1D4301B5858E39CCDE9C6308616BBF0BECF658C0A76AF5E919ADAEB176` | `3682A13C46550350106EFC2BBC276F8A5DD6FBB35FA3ECAE03C73DC51712B429` |
| ODOM V2 PCB | `E80CC5C34C815666A16633E474BEA558699948F010E9985673EECB8EE74CE705` | same |
| ODOM V1 schematic | `F0E01B1D4301B5858E39CCDE9C6308616BBF0BECF658C0A76AF5E919ADAEB176` | same |
| ODOM V1 PCB | `A788E20BE7124C2424D44C1F0E9B28A985447B7CAFFA639FBFB083ADD3ECC823` | same |

The V2 PCB still carries the old J8 placement/footprint and is not synchronized or ready for manufacture. No other TP or CAN changes were made.

## 19:48 saved-state readback and reapplication

The saved V2 root schematic was later read back with J8 back at GH6 (`DCD091E6EBAEC8B3BE597969EAB24552E430F6C3ADF57D05A96EF13CC9047F62`). That exact file is preserved as `gh6-readback-2026-09-23.kicad_sch`. Its content matched the prior GH6 snapshot apart from formatting. The same SWD and UART TP change was reapplied without touching the other root circuits. The active schematic and `after-swd-reapply-readback.kicad_sch` both hash to `1E5366F757A86028A18C2AC9B5771B84700D89428121B8ADCF4315BD283A3B2B`.

The restored V2 folder was missing `sym-lib-table` and `fp-lib-table`, so those two existing project tables were copied back from `_restore_backup_2026-09-23T19-48-22-427/`. Their `${KIPRJMOD}/../lib` paths resolve the project library. Fresh ERC then returned **0 errors and 0 warnings**. Fresh XML again matched all 82 baseline connectivity groups outside J8, the new TPs and PB3. U3/U7/U9 pin2=GND and pin5=PWR_3.3V remained connected.

The V2 PCB now hashes to `44103119ED39950D6AC97538EF0CAECB463D385B02D30FB40472E483FEACF6FC`, different from the earlier V2 PCB hash recorded above. This occurred during the intervening saved-state/folder change; this SWD reapplication did not edit the PCB. V1 schematic and PCB hashes remain as recorded above.
