# 24V Addressable LED CAN Node Rev.A - KiCad entry reference

> **Status: controlled mechanical-transcription source, 2026-09-14.**
> The person or model entering KiCad must not infer a pin, value, orientation, protection part, or connector family.  Copy only rows marked **FIXED**.  A row marked **DNP** receives a footprint but is not populated; a row marked **STOP** is not drawn into a fabrication release.

## 0. Transfer contract

1. Use a flat A3 landscape schematic, with zones left-to-right: input/pass-through, buck/LDO, F303, CAN, LED buffer/output.
2. RefDes and net labels below are literal.  Do not auto-rename.
3. Finish one zone, export a netlist and compare its listed pins to this document before entering the next.
4. ERC clean does **not** prove orientation, voltage domain, pin correspondence, connector mating rating, or tape-current capacity.  Review Section 7 manually.
5. `LED-01` through `LED-04` remain release blockers.  Do not substitute a plausible part.

## 1. Sheet-wide net names

| Net | Meaning |
|---|---|
| `VIN_LED` | 12-24V branch at J101 input. |
| `VIN_LED_PROT` | protected input and tape-power pass-through source. |
| `PWR_5V_LED` / `PWR_3V3_LED` | local logic rails only. |
| `GND_PWR` | shared local power/logic ground plane. |
| `COMM_A` / `COMM_B` | abstract CANH/CANL bus names; A=CANH, B=CANL. |
| `CAN_TX` / `CAN_RX` | F303 to/from transceiver logic. |
| `LED_DATA_TIM` / `LED_DATA_OE_N` | F303 local waveform / active-low buffer enable. |
| `LED_DATA_BUF` / `LED_DATA_5V` | before / after connector damping resistor. |

## 2. Connector and protection entry

| RefDes | Symbol/footprint | Pin | Net | Status / instruction |
|---|---|---:|---|---|
| J101 | `Connector_Generic:Conn_01x02`; `Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal` | 1 | `VIN_LED` | FIXED: separately 1A-fused logic tap from the externally 5A-fused tape branch. |
| J101 | same | 2 | `GND_PWR` | FIXED. |
| D101 | `Device:D` / `Diode_SMD:D_SOD-123F` | A/K | `VIN_LED` / `VIN_LED_PROT` | FIXED: Diodes Inc. `B160S1F-7` series reverse-polarity diode. |
| D102 | `Device:D` / `Diode_SMD:D_SMB` | K/A | `VIN_LED_PROT` / `GND_PWR` | FIXED: Littelfuse SMBJ33A unidirectional TVS. |
| J301 | `Connector_Generic:Conn_01x02`; `Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal` | 1 | `COMM_A` | FIXED. |
| J301 | same | 2 | `COMM_B` | FIXED. |
| J401 | `Connector_Generic:Conn_01x02`; `Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal` | 1 | `LED_DATA_5V` | FIXED: data/reference adapter harness. |
| J401 | same | 2 | `GND_PWR` | FIXED. |

The board's 1A logic tap is externally fused before J101.  D101/TVS D102 protect only the logic board.  The tape 24V/high-current GND is not a PCB net: it is externally fused at 5A and runs directly to the tape's supplied 3pin SM-style input; J401's data/GND joins it in the adapter harness.

## 3. Fixed 5V/3.3V power circuit

> **Correction 2026-09-17 (TI SLUSEY1B Rev.B, Table 5-1 / Section 8.2.2.2, read directly):** the 2026-09-14 U101 rows were wrong on three points and are replaced below.  (a) DBV pin order is `1 CB(BOOT) 2 GND 3 FB 4 EN 5 VIN 6 SW`, not `1 GND 2 FB 3 EN 4 VIN 5 SW 6 BOOT`.  (b) The orderable part is `LMR51606XDBVR` (SOT-23-6 DBV); `LMR51606XDDCR` does not appear in the datasheet's Device Comparison Table.  (c) VREF is 0.8V, so the former R101/R102 = 100k/24.9k gives 4.0V, not 5V; the datasheet 5V example 118k/22.1k (5.07V) is adopted.  Footprint `Package_TO_SOT_SMD:SOT-23-6` exists in the KiCad 10 standard library.  See `output/pdf/LED_CAN_NODE_REV_A_SCHEMATIC_2026-09-17.pdf` S02.

| RefDes | Part / footprint | Pin | Net | Status |
|---|---|---:|---|---|
| U101 | **custom `DifferentialSwerve:LMR51606XDBVR` symbol required**; `Package_TO_SOT_SMD:SOT-23-6` (standard; verify pad 1 against TI DBV drawing) | 1 CB (BOOT) | `BUCK_BOOT` | FIXED (corrected 2026-09-17). Custom symbol required because KiCad 10 standard library has no LMR51606 entry. |
| U101 | same | 2 GND | `GND_PWR` | FIXED (corrected 2026-09-17). |
| U101 | same | 3 FB | `BUCK_FB` | FIXED (corrected 2026-09-17). |
| U101 | same | 4 EN | `VIN_LED_PROT` | FIXED first bring-up (corrected 2026-09-17). R103/R104 DNP. |
| U101 | same | 5 VIN | `VIN_LED_PROT` | FIXED (corrected 2026-09-17). |
| U101 | same | 6 SW | `BUCK_SW` | FIXED (corrected 2026-09-17). |
| C101/C102 | 2.2uF 50V 1206 | 1/2 | `VIN_LED_PROT` / `GND_PWR` | FIXED. |
| C103 | 100nF 16V 0603 | 1/2 | `BUCK_BOOT` / `BUCK_SW` | FIXED. |
| L101 | Bourns `SRN6045TA-330M`; `Inductor_SMD:L_Bourns_SRN6045TA` | 1/2 | `BUCK_SW` / `PWR_5V_LED` | FIXED. |
| C104 | 22uF 10V 1206 | 1/2 | `PWR_5V_LED` / `GND_PWR` | FIXED. |
| R101 | 118k 1% 0603 | 1/2 | `PWR_5V_LED` / `BUCK_FB` | FIXED (corrected 2026-09-17; was 100k). VOUT = 0.8V x (1 + 118/22.1) = 5.07V. |
| R102 | 22.1k 1% 0603 | 1/2 | `BUCK_FB` / `GND_PWR` | FIXED (corrected 2026-09-17; was 24.9k). |
| R103/R104 | 100k / 13.3k 1% 0603 | -- | EN divider | **DNP** until LED-03. |
| U102 | `Regulator_Linear:TLV76133DCY`; `Package_TO_SOT_SMD:SOT-223-3_TabPin2` | 1 GND | `GND_PWR` | FIXED. |
| U102 | same | 2 OUT + tab | `PWR_3V3_LED` | FIXED. |
| U102 | same | 3 IN | `PWR_5V_LED` | FIXED. |
| C111/C113 | 100nF 0603 | 1/2 | rail / `GND_PWR` | FIXED, U102 pins adjacent. |
| C112/C114 | 10uF 10V 0805 | 1/2 | rail / `GND_PWR` | FIXED, U102 pins adjacent. |

## 4. F303 exact nets (U201 = `MCU_ST_STM32F3:STM32F303K8Tx`)

> **Correction 2026-09-17:** the 2026-09-14 table listed LQFP-48 (STM32F303C8) pin contents (VBAT, PC13/PC14/PC15, VSSA, VDD at 21...) against LQFP-32 pin numbers and did not match the STM32F303K8T6.  The table below follows the KiCad 10 standard symbol `MCU_ST_STM32F3:STM32F303K8Tx` (32 pins, checked on disk 2026-09-17).  The ST DS9866 PDF could not be downloaded during that session (st.com unreachable), so the **STOP** rule below still applies: compare against DS9866 Table 13 before entry.  Consequences: there is no VBAT pin (C201 becomes the pin-1 VDD decoupling), no separate VSSA/VREF+ pins (VDDA/VREF+ share pin 5, so C208/C209 merge into C206/C207), and no PC13 -> `LED_FAULT` needs a new pin.  `PB0` (pin 14) is the **proposal**; it is not fixed until the requirements document is updated.  Net assignments themselves are unchanged from the 2026-09-14 version.

| U201 pin | Net | Status |
|---:|---|---|
| 1 VDD | `PWR_3V3_LED` | FIXED, C201=100nF to GND at the pin. |
| 2 PF0-OSC_IN | `HSE_IN` | FIXED. |
| 3 PF1-OSC_OUT | `HSE_OUT` | FIXED. |
| 4 NRST | `NRST` | FIXED: C203=100nF to GND, J501-4. |
| 5 VDDA/VREF+ | `PWR_3V3_A` | FIXED via FB201; C206=100nF/C207=1uF. |
| 6 PA0 | `VIN_LED_SENSE` | FIXED ADC divider - divider values STOP pending input protection. |
| 7 PA1 | `PWR_5V_LED_SENSE` | FIXED ADC divider: 33k/22k + 10nF, clamp approach uses existing project-common design. |
| 8 PA2 | `LED_RUN` | FIXED GPIO. |
| 9 PA3 | `LED_COMM` | FIXED GPIO. |
| 10 PA4 | NC | FIXED NC. |
| 11 PA5 | `LED_PWR` | FIXED GPIO. |
| 12 PA6 | `LED_DATA_TIM` | FIXED AF2 = TIM3_CH1. |
| 13 PA7 | `LED_DATA_OE_N` | FIXED GPIO, output low enables U401 only after firmware self-test. |
| 14 PB0 | `LED_FAULT` | **PROPOSAL 2026-09-17** (replaces non-existent PC13); confirm in `LED_CAN_NODE_REQUIREMENTS.md` before entry. |
| 15 PB1 | NC | FIXED NC. |
| 16 VSS | `GND_PWR` | FIXED. |
| 17 VDD | `PWR_3V3_LED` | FIXED, C211=100nF to GND at the pin. |
| 18 PA8 | `SERVICE_IN` | FIXED GPIO, 100k pulldown. |
| 19 PA9 | `DBG_TX` | FIXED USART1_TX. |
| 20 PA10 | `DBG_RX` | FIXED USART1_RX. |
| 21 PA11 | `CAN_RX` | FIXED CAN1_RX from U301 RXD. |
| 22 PA12 | `CAN_TX` | FIXED CAN1_TX to U301 TXD. |
| 23 PA13 | `SWDIO` | FIXED. |
| 24 PA14 | `SWCLK` | FIXED. |
| 25 PA15 | NC | FIXED NC. |
| 26 PB3 | NC | FIXED NC. |
| 27 PB4 | NC | FIXED NC. |
| 28 PB5 | NC | FIXED NC. |
| 29 PB6 | NC | FIXED NC. |
| 30 PB7 | NC | FIXED NC. |
| 31 BOOT0 | `BOOT0` | FIXED: 10k to GND + test pad (dedicated pin on LQFP-32). |
| 32 VSS | `GND_PWR` | FIXED. |

**Update 2026-09-17 (later):** ST's official `STM32_open_pin_data` (CubeMX database) `STM32F303K(6-8)Tx.xml` was read and matches every pin number in this table and the KiCad symbol.  **STOP before entry:** confirm U201 standard-library pin numbers against DS9866 LQFP-32 Table 13.  The nets above are fixed; the table is deliberately a required human pin-number comparison rather than an invitation for a model to repair a mismatch.

HSE: Y201 pins 1/3=`HSE_IN/HSE_OUT`; pins 2/4=GND. C204 from HSE_IN to GND and C205 from HSE_OUT to GND are each 10pF C0G.  `PWR_3V3_A` = `PWR_3V3_LED` -> FB201 `BLM18AG601SN1D`; C206=100nF/C207=1uF to GND.  VREF+ shares pin 5 with VDDA on LQFP-32, so the former C208=10nF/C209=1uF are proposed to be removed (merged into C206/C207; open item, 2026-09-17).

## 5. CAN and data output exact connections

| RefDes | Pin | Net | Status |
|---|---:|---|---|
| U301 **custom `DifferentialSwerve:TCAN1051VDRQ1` symbol required**; `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | 1 TXD | `CAN_TX` | FIXED.  KiCad 10 standard symbols contain no TCAN1051 entry. |
| U301 | 2 GND | `GND_PWR` | FIXED. |
| U301 | 3 VCC | `PWR_5V_LED` | FIXED; C301=100nF to GND. |
| U301 | 4 RXD | `CAN_RX` | FIXED. |
| U301 | 5 VIO | `PWR_3V3_LED` | FIXED; C302=100nF to GND. |
| U301 | 6 CANL | `COMM_B` | FIXED. |
| U301 | 7 CANH | `COMM_A` | FIXED. |
| U301 | 8 S | `GND_PWR` | FIXED Normal mode. |
| D301 **custom `DifferentialSwerve:ESD2CAN24DBZRQ1` symbol required**; `Package_TO_SOT_SMD:SOT-23` | 1/2 | `COMM_A` / `COMM_B` | FIXED; pin 3=`GND_PWR`.  KiCad 10 standard symbols contain no ESD2CAN24 entry. |
| R301 | 1/2 | `COMM_A` / `TERM_A` | FIXED 120R, series path. |
| SW301 JS102011SAQN | common / throw | `TERM_A` / `COMM_B` | FIXED, other throw NC; populate only if LED-04 says bus end. |
| U401 `74xGxx:74AHCT1G125`; `Package_TO_SOT_SMD:SC-70-5` | 1 OE | `LED_DATA_OE_N` | FIXED; R401=100k to 5V. |
| U401 | 2 A | `LED_DATA_TIM` | FIXED; R402=100k to GND. |
| U401 | 3 GND | `GND_PWR` | FIXED. |
| U401 | 4 Y | `LED_DATA_BUF` | FIXED. |
| U401 | 5 VCC | `PWR_5V_LED` | FIXED; C401=100nF to GND. |
| R403 | 1/2 | `LED_DATA_BUF` / `LED_DATA_5V` | FIXED 33R. |
| R404 | 1/2 | `LED_DATA_5V` / `GND_PWR` | FIXED 100k. |
| D401 `Device:D`; `Diode_SMD:D_SOD-323` | 1/2 | `LED_DATA_5V` to `GND_PWR` | FIXED; `PESD5V0V1BA-Q`, bidirectional SOD-323. |

## 6. Debug connector

J501=`Connector_Generic:Conn_01x06` + `Connector_JST:JST_GH_BM06B-GHS-TBT_1x06-1MP_P1.25mm_Vertical`; pin 1=`GND_PWR`, 2=`SWCLK`, 3=`SWDIO`, 4=`NRST`, 5=`DBG_TX`, 6=`DBG_RX`.  It must not source debugger 5V or 3.3V into the target.

## 7. ERC-non-detectable review - human only

- [ ] U101 symbol pin order and footprint pad-1 orientation match the TI DBV drawing; BOOT capacitor is BOOT-to-SW, never to GND.
- [ ] U102 pin 2 **and tab** are 3.3V, not GND; 5V only enters pin 3.
- [ ] TCAN: `PA12 -> TXD pin1`, `RXD pin4 -> PA11`, VCC=5V, VIO=3.3V, S=GND, A=CANH/pin7, B=CANL/pin6.
- [ ] AHCT: U401 pin1 is **active-low** OE and is pulled to 5V.  PA7's boot level must not enable tape data.
- [ ] J401 pin 1 is buffered 5V data after R403; it must never carry raw PA6 3.3V or 24V.
- [ ] Tape `+24V`/power-GND runs directly from the external 5A fused branch, while J401 only carries data and its GND reference; tape current is never forced through the logic-side copper.
- [ ] D101 is series anode=`VIN_LED`, cathode=`VIN_LED_PROT`; D102 cathode=`VIN_LED_PROT`, anode=GND.  The 5A tape fuse is external; J101's logic branch has a separate external 1A fuse.
- [ ] R301/SW301 is ON only at a physical CAN-bus end.

## 8. Mechanical audit commands

```powershell
# after each KiCad zone
kicad-cli sch erc LED-CAN-node.kicad_sch --output erc-zone.json
kicad-cli sch export netlist LED-CAN-node.kicad_sch --output netlist-zone.net
# compare every U101/U102/U201/U301/U401 pin and its net to Sections 3-5
```

Do not use an ERC warning waiver as proof of a row being correct.  Fix the schematic or explicitly record the intentional exception beside its table row.
