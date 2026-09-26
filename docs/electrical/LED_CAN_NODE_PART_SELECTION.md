# 24V Addressable LED CAN Node Rev.A - part selection and data-sheet record

> **Status: Data-sheet-checked parts for schematic entry (2026-09-14).**
> This file records design decisions.  The following `LED_CAN_NODE_KICAD_ENTRY_REFERENCE.md` is the only source to mechanically transcribe pins and nets.  A `TBD` item is not allowed into a fabrication schematic.

## 1. Fixed parts

| RefDes group | Function | Adopted part | Package / status | Fixed electrical basis |
|---|---|---|---|---|
| U101 | 12-24V to 5V buck | TI `LMR51606XDBVR` (corrected 2026-09-17; `XDDCR` is not in SLUSEY1B's Device Comparison Table) | SOT-23-6 (DBV), Active | 4-65V input; 0.6A synchronous buck; fixed 400kHz/PFM variant. DBV pins: 1 CB, 2 GND, 3 FB, 4 EN, 5 VIN, 6 SW (SLUSEY1B Table 5-1). VREF=0.8V. |
| U102 | 5V to 3.3V logic LDO | TI `TLV76133DCYR` | SOT-223-4, Active | 2.5-18V input, 3.3V/1A, ceramic-stable; tab is OUT. |
| U201 | MCU | ST `STM32F303K8T6` | LQFP-32, Active | 2.0-3.6V, 64KB Flash/12KB SRAM, Classic CAN, timer/DMA. |
| U301 | CAN physical layer | TI `TCAN1051VDRQ1` | SOIC-8, Active | 5V VCC, 3.3V VIO, CAN 2Mbps capable; run at Classic 1Mbps. |
| D301 | CAN ESD | TI `ESD2CAN24DBZRQ1` | SOT-23-3, Active | 2-channel bidirectional 24V-working CAN protection. |
| U401 | 3.3V-to-5V data buffer | TI `SN74AHCT1G125DCKR` | SC70-5, Active | 4.5-5.5V supply, TTL input, tri-state output; explicitly suited to 3.3V-to-5V translation. |
| Y201 | HSE | `FC3BAEBDI8.0-T1` | 3225 4-pad | Project-common 8MHz, CL=8pF crystal. |
| D101 | board reverse-polarity diode | Diodes Inc. `B160S1F-7` | SOD-123F, Active | 60V/1A Schottky.  It carries node-electronics current only, not tape power. |
| D102 | board-input TVS | Littelfuse `SMBJ33A` | DO-214AA/SMB, Active | 33V stand-off, 53.3V maximum clamp at 11.3A.  Below the 65V buck input limit. |
| L101 | buck inductor | Bourns `SRN6045TA-330M` | 6x6mm SMD | 33uH, 1.8A Irms, 2.5A Isat; KiCad has the matching `L_Bourns_SRN6045TA` footprint. |
| D401 | tape-data ESD | Nexperia `PESD5V0V1BA-Q` | SOD-323, Active | 5V standoff, bidirectional, 11pF typical, IEC 61000-4-2 level 4. |
| J301 | CAN harness | JST `SM02B-GHS-TB` | GH 2-pin SMT | CAN-only central harness: 1=`COMM_A`, 2=`COMM_B`. |
| J401 | tape data/reference | JST `SM02B-GHS-TB` | GH 2-pin SMT | 1=`LED_DATA_5V`, 2=`GND_PWR`; it enters an external adapter harness, not the tape's high-current power path. |

The tape has its supplied 3pin SM-style connector.  Its `+24V` wire is fed directly from the distribution branch's external 5A fuse; the board supplies only data plus the data reference.  This removes tape-current connector and PCB-copper assumptions from the control-board release.

## 2. Buck reference circuit - U101 (`LMR51606XDBVR`)

The 24V-to-5V block uses the vendor 24V/5V 400kHz application basis: 33uH inductor and 22uF output capacitance.  The values below are fixed for schematic review and the inductor MPN/footprint is selected.

> **Correction 2026-09-17 (SLUSEY1B Rev.B read directly):** VREF is 0.8V (0.788-0.812V), so the 2026-09-14 divider 100k/24.9k would have produced 4.0V, below the 4.5V minimum of TCAN1051V VCC and SN74AHCT1G125 VCC.  R101/R102 are replaced by the datasheet 5V example (RFBB=22.1k, RFBT=118k, 5.07V).  The DNP UVLO divider recomputed with VEN(R)=1.227V typ / VEN(F)=1.0V typ gives 10.4V rising / 8.5V falling, not 8.0V.

| RefDes | Value / requirement | Connection intent |
|---|---|---|
| C101, C102 | 2.2uF, X7R, >=50V, 1206 | `VIN_LED_PROT` to `GND_PWR`, at U101 VIN/GND loop. |
| C103 | 100nF, X7R, >=16V, 0603 | U101 BOOT to SW, immediately beside U101. |
| L101 | Bourns `SRN6045TA-330M`, 33uH, 1.8A Irms / 2.5A Isat | U101 SW to `PWR_5V_LED`. |
| C104 | 22uF, X7R, >=10V, 1206 | `PWR_5V_LED` to `GND_PWR`, at L101 output. |
| R101 | 118k, 1%, 0603 (was 100k until 2026-09-17) | `PWR_5V_LED` to U101 FB. |
| R102 | 22.1k, 1%, 0603 (was 24.9k until 2026-09-17) | U101 FB to `GND_PWR`; VOUT = 0.8V x (1 + 118/22.1) = 5.07V. |
| R103 | 100k, 1%, 0603 | `VIN_LED_PROT` to U101 EN. |
| R104 | 13.3k, 1%, 0603 | U101 EN to `GND_PWR`; with SLUSEY1B EN thresholds this gives about 10.4V rising / 8.5V falling (the earlier "8.0V typical" note was not from the datasheet). |

The UVLO divider is a **proposal**, not a fabrication fact: it protects against low-voltage brownout from an exhausted 6S pack but must be verified against the current `LMR51606X` EN threshold table before release.  Consequently, R103/R104 are DNP; direct `VIN_LED_PROT -> EN` is the approved Rev.A population.

## 3. Logic, MCU and CAN-common blocks

| Block | Fixed values / connection rule |
|---|---|
| U102 TLV76133 | C111=100nF + C112=10uF from IN to GND; C113=100nF + C114=10uF from OUT to GND.  Pin 2 and exposed tab are `PWR_3V3_LED`; pin 1 GND; pin 3 `PWR_5V_LED`. |
| U201 power | Every VDD and VDDA=3.3V; every VSS/VSSA=GND; every VDD has 100nF.  VDDA is fed through FB201 (`BLM18AG601SN1D`) and has 100nF + 1uF locally.  VREF+ is tied to VDDA with 10nF + 1uF local capacitors. |
| Clock/reset/boot | Y201 with C201/C202=10pF C0G.  NRST=100nF to GND and SWD header.  BOOT0=10k to GND plus test pad to 3.3V. |
| CAN | Use the project-common exact block in `CAN_COMMON_BLOCK_PART_SELECTION.md`: U301 pin 1=TXD, 2=GND, 3=5V, 4=RXD, 5=3.3V VIO, 6=CANL/`COMM_B`, 7=CANH/`COMM_A`, 8=S=GND; VCC/VIO each 100nF.  D301 is connector-side.  R301=120R plus SW301=`JS102011SAQN` makes an optional end termination. |

## 4. LED data output block

| RefDes | Value / connection rule |
|---|---|
| U401 | `SN74AHCT1G125DCKR`: 1=`LED_DATA_OE_N`, 2=`LED_DATA_TIM`, 3=GND, 4=`LED_DATA_BUF`, 5=5V.  Its active-low OE is held HIGH by R401=100k to 5V, thus disabled during reset/unpowered MCU. |
| R402 | 100k, 0603, from `LED_DATA_TIM` to GND: input is deterministically low before firmware configures PA6. |
| R403 | 33R, 0603, from `LED_DATA_BUF` to `LED_DATA_5V`: initial source damping value, fitted near J401. |
| R404 | 100k, 0603, `LED_DATA_5V` to GND: cable-side default low. |
| D401 | Nexperia `PESD5V0V1BA-Q`, SOD-323, bidirectional low-capacitance 5V ESD diode at J401 data pin. |
| C401 | 100nF, X7R, 0603, U401 VCC to GND at the package. |

The AHCT data sheet explicitly specifies a VCC pull-up on OE to preserve high impedance while power is coming up/down.  F303 PA6 uses `TIM3_CH1` AF2, and PA7 drives OE low only after self-test and a valid command.

## 5. Explicitly unresolved - stop conditions

| ID | Blocking fact | Required before fabrication |
|---|---|---|
| LED-01 | Actual tape maximum all-white W/m/current and pixel-group count | 2m / 630 packages/m / 24V WS2811 and a 5m injection rule are known.  Measure all-white current before increasing the external 5A fuse or setting firmware's final brightness ceiling. |
| LED-02 | Tape-side ESD component | **Closed:** `PESD5V0V1BA-Q`, SOD-323, 5V/11pF bidirectional. |
| LED-03 | EN-UVLO divider verification | L101 is **closed** as `SRN6045TA-330M`.  Keep R103/R104 DNP and EN=protected input until the vendor EN threshold calculation is independently checked. |
| LED-04 | Bus physical topology | Confirm whether this board is a CAN bus end.  Populate SW301/R301 only at an actual bus end. |

## 6. Data-sheet records

- [ST STM32F303K8 product page / DS9866](https://www.st.com/en/microcontrollers-microprocessors/stm32f303k8.html): active device, 64KB Flash, 12KB SRAM, Classic CAN, and timer peripherals.
- [TI LMR51606](https://www.ti.com/product/LMR51606): active 4.5-65V, 0.6A buck; 24V/5V curve uses 33uH and 22uF output conditions.
- [TI TLV761](https://www.ti.com/product/TLV761): active fixed-output SOT-223 LDO; 1uF ceramic minimum, 3.3V option.
- [TI TCAN1051V-Q1](https://www.ti.com/product/TCAN1051V-Q1): VIO version with 3.3V I/O level shifting and 5V VCC.
- [TI SN74AHCT1G125](https://www.ti.com/product/SN74AHCT1G125): pin 1 OE, 2 A, 3 GND, 4 Y, 5 VCC; OE high disables output, and 5V AHCT input threshold accepts a 3.3V F303 output.
- [Littelfuse SMBJ33A](https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/surface-mount/smbj/smbj33a): 33V stand-off and 53.3V maximum clamp.
- [Diodes Inc. B160S1F](https://www.diodes.com/datasheet/download/B160S1F.pdf): 60V/1A Schottky reverse-protection diode.
- [Bourns SRN6045TA](https://www.bourns.com/docs/Product-Datasheets/SRN6045TA.pdf): `SRN6045TA-330M` current ratings.
- [Nexperia PESD5V0V1BA-Q](https://assets.nexperia.com/documents/data-sheet/PESD5V0V1BA-Q.pdf): 5V 11pF bidirectional ESD, SOD-323.
