# 24V Actuator CAN Node Rev.A requirements

> 2026-09-23変更: 中央とのCANはCOMM_A/COMM_B/GNDの3pin。コイルdriverを中央基板へ移す基本案のため、本文の折り取りCONTACTOR_DRIVERは次回発注の前提から外す。汎用スイッチング負荷は独立CANノードを維持し、今回PCB発注対象外。 詳細: [次回PCB一括発注計画](PCB_BATCH_V2_CENTRAL_PLAN.md)。

> **Status: Rev.A architecture fixed; human-review block diagram and preliminary BOM created (2026-09-17); pin-level human-review schematic `output/pdf/ACTUATOR_CAN_NODE_REV_A_SCHEMATIC_2026-09-17.pdf` created the same day. KiCad schematic not yet created.**
> This is the source of truth for the self-powered 12-24V CAN actuator node and its reusable contactor-driver edge block. The contactor block is installed at the central board, not operated across the CAN-node harness.

## 1. Role and boundaries

This is a small, reusable actuator controller. The Teensy only sends high-level CAN commands; this node makes the local switching waveform.

Included:

- Four protected 24V low-side outputs for lamps, relays, valves, solenoids, and buzzers.
- One protected H-bridge for a small 24V brushed DC motor: direction plus PWM.
- CAN command/status, local command timeout, and hardware-off reset behavior.
- A separately reusable `CONTACTOR_DRIVER` block for the central board's E-stop/contactor circuit.

Not included:

- C620 / traction-motor drive, motor-bus main current, regenerative brake chopper, or precharge power stage.
- LED-tape pixel waveform generation (that remains a separate LED node).

The node may **never** be made the primary E-stop path. The E-stop path stays on the central board and is a hard series circuit, not a CAN feature.

## 2. Electrical envelope

| Domain | Rev.A specification |
|---|---|
| Node input | `VIN_ACT` / `GND_PWR`, nominal 12-24V. Normal operating range is 9-30V; 6S maximum is 25.2V. Node input is separate from the central PCB's 5V distribution |
| Input protection | External fuse + reverse-polarity protection + 33V-class TVS at the node connector. Actual TVS part is selected after harness transient measurement; the downstream buck must itself be 60V-class |
| Local 5V | `LMR51606XDBVR` (corrected 2026-09-17: `XDDCR` is not in TI SLUSEY1B's Device Comparison Table), 4-65V synchronous buck, 5.0V / 0.6A. SOT-23-6 DBV pins 1 CB / 2 GND / 3 FB / 4 EN / 5 VIN / 6 SW. VREF=0.8V, so FB divider is 118k/22.1k (5.07V), not 100k/24.9k (4.0V). Enough for MCU, CAN, LEDs, and gate buffers, but never for an external load |
| Local logic rail | `PWR_3V3_ACT`, `TLV76133DCYR` from local 5V; input/output 100nF + 10uF X7R |
| Actuator supply | `VIN_ACT` / `GND_PWR` after the local fuse/protection. No actuator current flows through the central PCB |
| Ground | `GND_PWR` and `GND_CTRL` meet only at the node's defined power-entry star point. No split GND plane under CAN or MCU |
| PCB | 4 layers, 1oz outer copper minimum; L2 continuous GND; motor/H-bridge loop and logic/CAN areas separated |

## 3. MCU, CAN, and service interface

| Block | Adopted part / implementation | Reason |
|---|---|---|
| MCU | `STM32F303K8T6`, LQFP-32 | Active, easy-to-inspect package, 64KB Flash, 16KB SRAM, CAN 2.0B, ADC, timer PWM, analog comparators, and independent watchdog. It exactly matches the Classic CAN-only CAN2 node role without paying for unused CAN FD. |
| Clock | 8MHz HSE + C0G load capacitors | Required for robust 1Mbps CAN timing; use the project-common 8MHz crystal selection workflow. |
| CAN transceiver | `TCAN1051VDRQ1` + `ESD2CAN24DBZRQ1`, 100nF | Same validated 5V-VCC/3.3V-VIO CAN block as the other boards. |
| CAN connector | Locked JST GH 2pin: pin 1=`COMM_A`, pin 2=`COMM_B` | The only central-to-node harness. Silkscreen uses `COMM_A/B`, not CANH/L. |
| Debug | JST GH 6pin SWD, same project pinout convention | Firmware write/debug after assembly. |
| Status | PWR, RUN, COMM, FAULT LEDs; test points at 24V, 5V, 3.3V, GND, COMM_A, COMM_B | Safe bench bring-up. |

CAN2 is Classic CAN at 1Mbps. Node ID is fixed to **5** for Rev.A (the existing unit-ID range reserves 5-7).

The two-wire CAN harness is valid only because the node and central board share `GND_PWR` at the 12-24V distribution system. It is not a floating two-wire system. If later placement makes those grounds independent, or harness tests show excessive common-mode noise, use the populated alternative footprint for an isolated CAN transceiver (`ISO1042`) and an isolated bus-side supply; do not add an unplanned signal-GND wire to the CAN cable.

### F303K pin budget

The 32-pin package is sufficient; no pin is shared between CAN, SWD, and actuator safety outputs.

| Pin group | Assigned function |
|---|---|
| PA11 / PA12 | CAN1_RX / CAN1_TX to TCAN1051 |
| PA13 / PA14 | SWDIO / SWCLK |
| PF0 / PF1 | 8MHz HSE |
| PA0 / PA1 | `PWR_24V_ACT` ADC / `IPROPI` motor-current ADC |
| PA2 / PA3 | DRV8251A IN1 / IN2 (direction + PWM) |
| PA4 | Spare. `DRV8251A` has no discrete `nFAULT` pin. |
| PA5 / PA6 / PA7 / PB0 / PB1 | **STOP before KiCad:** allocate exactly four `OUT1` to `OUT4` gate-buffer inputs, with `OUT1` on the breakaway block. The older PA5 contactor plus PA6-PB1 OUT1-4 listing described five controls and contradicted the four-channel/OUT1 boundary. **PROPOSAL 2026-09-17 (not yet approved):** OUT1=PA6, OUT2=PA7, OUT3=PB0, OUT4=PB1 = TIM3_CH1..CH4 (AF2, one common PWM period); PA5 NC. AF numbers from ST `STM32_open_pin_data` `STM32F303K(6-8)Tx.xml`. PA2/PA3 are TIM15_CH1/CH2 (AF9) for motor PWM. |
| PA8 / PA9 | status LED / physical service input. **Conflict found 2026-09-17:** the project SWD/UART header convention puts `DBG_TX/DBG_RX` on pins 5/6 = USART1 PA9/PA10 (AF7). PROPOSAL: PA9/PA10 = debug UART, `SERVICE_IN` = PB5, `LED_COMM` = PB3, `LED_FAULT` = PB4, PWR LED hard-wired to 3.3V. |
| PA10 / PA15 | spare / node service output |
| PB3 to PB7 | remaining spare GPIO, I2C/UART service, or Rev.B diagnostics |

## 4. `OUT1 / CONTACTOR_DRIVER` - breakaway edge block

```text
24V_CTRL -> fuse -> E-stop 1 NC -> E-stop 2 NC
         -> ESTOP_LOOP_RETURN -> E228 coil + -> E228 coil -
         -> Q1 low-side MOSFET -> GND_PWR
```

| Item | Requirement |
|---|---|
| Normal (uncut) role | This is **OUT1** of the CAN actuator node. F303K drives its gate exactly like an ordinary low-side channel; no connector is populated at the breakaway interface. |
| Breakaway role | The block sits on the node PCB edge, joined by a defined mouse-bite/tab line. Once separated, it becomes the central board's `CONTACTOR_DRIVER` daughterboard. It is not installed at the central board while still electrically joined to the node. |
| Interface pads | Put two unpopulated, through-hole 2.54mm `1x5` header-pad rows (one on the node side and one on the breakaway side) adjacent to the cut line. They are **pads only** in the normal node build. For central use, solder pin headers or wires to the breakaway-side pads and matching central-board pads. |
| Interface nets | 1=`PWR_5V_CTRL`, 2=`CONT_EN_3V3`, 3=`ESTOP_LOOP_RETURN`, 4=`GND_PWR`, 5=`CONTACTOR_STATUS_N` (optional). In the uncut build, nets 1/2/4 are supplied by the node and `ESTOP_LOOP_RETURN` is unconnected; after separation, the central board supplies all required nets. |
| PCB constraint | `VIN_ACT` feed and the OUT1 gate-control trace cross the tab region only while the section is attached. Use at least three wide copper tabs/parallel bridges and verify the fabrication house's depanelization rule. OUT1's 1A rating applies only to the uncut board; the separated contactor module is rated only for the E228's 80mA coil. |
| Coil connector | Separate keyed 2pin on the block; `COIL+` from the hard NC loop, `COIL-` from Q1. It must not mate with a 5V or CAN connector. |
| Q1 | `IRLML0100TRPBF`, 100V SOT-23 N-MOSFET. It is adequate for the verified 75-80mA E228 coil, with substantial VDS margin. |
| Gate drive | `74AHCT1G125` buffer, 100R gate resistor, 100k gate pulldown, and 100k input pulldown. The input is F303K OUT1 while uncut; after separation it is central `CONT_EN_3V3` / `MOTOR_PWR_EN`. A reset, unpowered MCU/Teensy, Hi-Z GPIO, or open command path must leave Q1 OFF. |
| Clamp | Fit a default flyback diode footprint and a parallel TVS footprint. Do **not** select/finalize the TVS voltage until the E228 coil release waveform is measured. A plain diode is allowed only for initial safe functional testing; release time is then measured. |
| Energize condition | In the separated central-board use: `physical NC loop present AND central explicit arm AND MOTOR_PWR_EN`. The logic output cannot energize Q1 if the NC loop is open. In the uncut node use, it is an ordinary OUT1 and is not a contactor safety channel. |
| Failure response | In separated use, E-stop, central reset, brownout, Hi-Z, or `MOTOR_PWR_EN=0` forces Q1 OFF. Re-arm policy is implemented by the central Teensy safety state machine. |

**Cross-document mismatch (2026-09-17):** pad 4 is `GND_PWR` here, but `CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md` J402-4 names it `GND_CTRL`. Align both documents before either KiCad entry.

**Open contradiction (2026-09-17):** the interface-nets row says `ESTOP_LOOP_RETURN` is unconnected in the uncut build, while the PCB-constraint row says the `VIN_ACT` feed crosses the tab. In the uncut build OUT1's load needs 24V on `COIL+`; the schematic PDF S07 draws a 24V tab bridge to `COIL_POS` as an interpretation only. Resolve before KiCad entry.

This preserves the original safety property in separated use: `MOTOR_PWR_EN` is a direct central logic signal for the coil driver and is never the primary E-stop path.

## 5. Four general 24V low-side channels

| Parameter | Rev.A value |
|---|---|
| Channels | `OUT1` to `OUT4`, independent low-side N-MOSFET outputs |
| MOSFET | `IRLML0100TRPBF` per channel, 100V SOT-23 |
| Gate drive | `74AHCT125` (5V) outputs, each with 100R series gate resistor and 100k gate pulldown; MCU pins have external 100k pulldowns |
| Rated load | 1.0A per channel maximum, 3.0A combined board total, subject to connector/fuse/thermal validation |
| Switching | ON/OFF and PWM to 1kHz only. PWM is not available on the contactor channel. |
| Load connector | Four individually keyed 2pin connectors, each `PWR_24V_ACT` + `OUTn`. External load fuse is mandatory. |
| Inductive protection | Each channel has diode and TVS footprints at the connector side. Fit values only after the connected load and release-time requirement are known. |
| Diagnostic | MCU ADC measures the 24V actuator rail. Per-output current/opens are not claimed in Rev.A; use a load-specific sensor in Rev.B if required. |

This output bank is for small auxiliaries, **not** a DC traction motor, C620 supply, or un-fused high-power heater.

## 6. Brushed DC motor H-bridge channel

| Parameter | Rev.A value |
|---|---|
| Driver | TI `DRV8251ADDA` (HSOP-8 PowerPAD) |
| Motor supply | `PWR_24V_ACT`, separately fused, 4.5-48V device operating range |
| Motor connector | Dedicated keyed 2pin `MOTOR_A` / `MOTOR_B`; must not share the contactor or generic-output connector family |
| Motor capability | 24V brushed motor, **1.5A continuous design limit**, **3.0A short pulse limit** pending thermal validation; the IC has 4.1A peak protection capability but that is not the board's continuous rating |
| Control | IN1/IN2 direction + PWM; coast/brake modes explicitly defined in firmware. Hardware inputs have pulldowns so reset is coast/Hi-Z. |
| Current limit (DS-checked 2026-09-17, SLVSFU6) | `ITRIP x AIPROPI = VREF / RIPROPI`, AIPROPI = 1575uA/A, VREF recommended 0-3.6V. With VREF tied to 3.3V: RIPROPI 698R -> 3.0A, 1.40k -> 1.5A. IN1/IN2 have internal 100k pulldowns (reset = coast). DDA pins: 1 IPROPI, 2 IN2, 3 IN1, 4 VREF, 5 VM, 6 OUT1, 7 GND, 8 OUT2. Final RIPROPI stays STOP until motor stall current is measured. |
| Protection | Integrated current regulation, current mirror, UVLO, OCP, and TSD; MCU samples `IPROPI`. `DRV8251ADDA` has no discrete `nFAULT` output, so Rev.A must not claim direct fault-pin telemetry. Add local bulk ceramic/electrolytic capacitance and input TVS/fuse at `PWR_24V_ACT`. |
| Safety | Motor H-bridge is disabled on CAN command timeout, watchdog reset, node fault, and central `ESTOP` CAN broadcast. It may not be used as a safety brake. |

The selected driver accepts 3.3V logic and is rated to 48V, leaving real margin above the 25.2V 6S maximum. The 1.5A continuous limit is intentionally thermal-conservative for a first HSOP board. Larger motors must use a future external power stage/node rather than silently exceeding this limit.

## 7. CAN protocol baseline

All messages use standard 11-bit IDs, Classic CAN 8-byte frames, little-endian fields. The detailed offsets belong in `COMMUNICATION_NAMING_AND_IDS.md` before firmware work, but the safety behavior is fixed now:

1. `ACTUATOR_ARM` is accepted only after boot self-test, no local fault, and an explicit re-arm command.
2. `ACTUATOR_CMD` contains sequence, contactor request, OUT1-4 bitmap/PWM, motor direction/PWM, and enable flags.
3. A 100ms valid-command timeout disables OUT1-4 and the H-bridge. It does not auto-restart after traffic resumes.
4. `ACTUATOR_STATUS` returns arm state, node fault bits, 24V/5V/3.3V health, motor-current sample, and output state. H-bridge UVLO/OCP/TSD are internal protections and are not directly distinguishable through a fault pin on `DRV8251ADDA`.
5. A central `ESTOP` broadcast also causes immediate local shutdown. The central hard NC loop remains authoritative for motor power.

## 8. Bring-up and release gates

1. 5V-only: verify 3.3V, reset default outputs OFF, SWD, CAN, watchdog reset.
2. 24V input with no loads: check TVS, rail ADC, H-bridge input/output and internal-protection behavior. Do not expect a discrete `nFAULT` signal from `DRV8251ADDA`.
3. Resistive loads at 0.25A, 0.5A, and 1A per output; verify thermal rise and fault behavior.
4. Small brushed motor: measure stall current before connection; start with a fuse/current limit below 1.5A continuous. Verify direction, PWM, OCP, thermal rise, and timeout stop.
5. On the central block, dummy 24V/80mA coil: test panel unplug, each NC open, Teensy reset, and brownout. All must de-energize Q1.
6. E228 actual coil: record release time and Q1 VDS. Select the final diode/TVS population only after that measurement.
7. Run schematic ERC 0 and PCB DRC 0 before fabrication.

## 9. Pre-KiCad stop items found during block-diagram review (2026-09-17)

1. Resolve the four-channel GPIO allocation described in the pin-budget table. `OUT1` remains the breakaway contactor channel; do not create a fifth MOS channel by transcribing the obsolete overlapping rows.
2. Calculate the `DRV8251A` `RIPROPI` and `VREF` network from the measured motor stall current and ADC range. The device has no `nFAULT` pin.
3. Select the high-current reverse-polarity stage, input connector, input fuse, and input TVS after the simultaneous-load and harness-transient measurements. The LED node's 1A series Schottky solution is not reusable here.
4. Select each output connector, flyback diode, and TVS from the actual attached load and measured release waveform.
5. The current human-review drawing and preliminary BOM are `output/pdf/ACTUATOR_CAN_NODE_REV_A_BLOCK_DIAGRAM_AND_BOM_2026-09-17.pdf`; the pin-level schematic with RefDes, KiCad symbol/footprint assignment and open-item table is `output/pdf/ACTUATOR_CAN_NODE_REV_A_SCHEMATIC_2026-09-17.pdf` (generator `tmp/actuator-node/build_actuator_rev_a_schematic.py`). RefDes in that PDF supersede the block-diagram BOM (SWD = J201, motor = J501, OUT1 tab = U601/Q601/J601/J602/J603).
6. Resolve the PA9 service-input vs debug-UART conflict and the uncut-build 24V tab-bridge contradiction described above.

## 10. Primary sources

- ST `STM32F303x6/x8` datasheet DS9866: https://www.st.com/resource/en/datasheet/stm32f303c8.pdf
- TI `TCAN1051V-Q1` datasheet: https://www.ti.com/product/TCAN1051V-Q1
- Infineon `IRLML0100TRPBF` datasheet: https://www.infineon.com/dgdl/irlml0100pbf-1.pdf
- TI `DRV8251A` datasheet: https://www.ti.com/lit/ds/symlink/drv8251a.pdf
- TI `LMR51606` datasheet: https://www.ti.com/product/LMR51606
- TI `ISO1042` datasheet: https://www.ti.com/product/ISO1042
