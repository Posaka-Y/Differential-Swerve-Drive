# 24V Addressable LED CAN Node Rev.A requirements

> 2026-09-23変更: 中央とのCANをCOMM_A/COMM_B/GNDの3pinとする。本文のCAN2線のみ記述は撤回。電力帰路は電源ハーネスとしCAN参照GNDを負荷電流帰路にしない。今回PCB発注対象外。 詳細: [次回PCB一括発注計画](PCB_BATCH_V2_CENTRAL_PLAN.md)。

> **Status: Rev.A architecture fixed; schematic and PCB have not yet been created (2026-09-14).**
> This is the source of truth for the self-powered addressable-LED CAN node. It deliberately sends the LED waveform locally; the central board sends effect commands only.

## 1. Role and boundary

This board controls decorative/status **24V addressable tape LEDs** from the expansion CAN bus.  It accepts the same two-wire CAN-only central harness as the actuator node, makes its own 5V/3.3V rails from the local LED power branch, and drives a strip-compatible data signal.

Included:

- Classic CAN 1Mbps command/status node;
- local 800kbps, one-wire waveform generation for **WS2811-compatible 24V tape**;
- local effects (solid, blink, chase, rainbow, status pattern), brightness limiting, and a fail-safe output state;
- a protected logic-power input and a data/GND reference connector for the external tape-power adapter harness.

Not included:

- switching the total tape current with a small PCB MOSFET;
- sending per-pixel RGB frames continuously from the central board;
- an E-stop or safety indication.  Required safety indicators remain electrically independent of this decorative tape.

`WS2811-compatible` is intentional.  Most 24V addressable tape products use the WS2811-style single data wire, but their physical pixel group is product-dependent (often 3 LEDs, sometimes 6 LEDs).  Firmware counts **addressable pixel groups**, never individual LED packages.

## 2. Electrical envelope

| Domain | Rev.A specification |
|---|---|
| Local input | `VIN_LED` / `GND_PWR`, nominal 24V; normal 9-30V; 6S maximum 25.2V.  It is tapped from the tape's externally fused 24V branch, not central-board 5V. |
| Input protection | Separate external 1A logic-branch fuse, `B160S1F-7` reverse-polarity diode, and `SMBJ33A` TVS at the board input. |
| 5V rail | `LMR51606XDDCR` (4-65V synchronous buck), 5.0V / 0.6A.  It powers MCU, CAN transceiver, and the data-level buffer only. |
| 3.3V rail | `TLV76133DCYR` from local 5V, with 100nF + 10uF X7R at input and output. |
| Tape power | The tape's `+24V` and high-current `GND` run directly from the externally fused distribution branch to the tape input.  They do **not** pass through this PCB; the 0.6A buck only supplies node electronics. |
| Tape branch | Rev.A harness is limited by an external **5A automotive fuse** at the 24V distribution point.  This is a protective maximum, not an asserted tape consumption.  Measure the selected tape's all-white current before raising it. |
| PCB | 4 layers; 1oz outer copper minimum; continuous L2 GND; keep the low-current buck/data connector side separated from CAN/MCU.  No 5A tape-current path exists on this PCB. |

The tape current must be measured from the selected tape's worst-case all-white mode before raising the 5A external fuse rating.  Voltage injection at multiple points is preferred to forcing a long-strip return current through a narrow data-controller PCB.

### Confirmed tape harness envelope

The supplied `S04f88715a8f44ab39bec21ae629b863cw.pdf` manual and the user-supplied installation target establish: **24V FCOB WS2811 IC RGB tape, 2.0m, 630 LED packages/m (1260 packages total)**.  The manual specifies a 3-wire input in this order: `+24V`, `Data input`, `GND`, and recommends additional voltage injection every 5m.  Therefore Rev.A uses a single injection at the data-input end for the 2m run.  The manual is generic and does not state W/m or maximum current, so it cannot justify a larger fuse or a component current rating.

## 3. MCU, CAN, and service

| Block | Adopted implementation | Reason |
|---|---|---|
| MCU | `STM32F303K8T6`, LQFP-32 | Same small, available MCU family as the actuator node.  Native Classic CAN, timer PWM plus DMA, 64KB Flash and 12KB SRAM are ample for local effects and a bounded RGB framebuffer. |
| Clock | 8MHz HSE + C0G load capacitors | Robust 1Mbps CAN timing and deterministic LED timer clock. |
| CAN transceiver | `TCAN1051VDRQ1` + `ESD2CAN24DBZRQ1`, 100nF local decoupling | Project-common 5V-VCC / 3.3V-VIO CAN block. |
| CAN connector | Locked JST GH 2pin: pin 1=`COMM_A`, pin 2=`COMM_B` | The only central-to-node harness. |
| Debug | JST GH 6pin SWD, project-common pinout | Bring-up and firmware update. |
| Status | PWR, RUN, COMM, FAULT LEDs; test points at 24V, 5V, 3.3V, GND, `COMM_A/B`, `LED_DATA` | Bench diagnostics without touching the tape. |

CAN2 is Classic CAN at 1Mbps.  Rev.A node ID is fixed to **6** (actuator node uses 5).  The two-wire CAN harness relies on the common `GND_PWR` at the shared 12-24V distribution system.  If placement/harness testing proves that common-mode noise exceeds the transceiver margin, use an isolated-CAN Rev.B (`ISO1042` plus isolated bus-side supply); do not quietly add an unplanned third wire.

### F303K initial pin allocation

| Pins / net | Function |
|---|---|
| PA11 / PA12 | `CAN1_RX` / `CAN1_TX` to TCAN1051 |
| PA13 / PA14 | SWDIO / SWCLK |
| PF0 / PF1 | 8MHz HSE |
| PA0 | `VIN_LED_SENSE` ADC via protected divider |
| PA1 | `PWR_5V_LED_SENSE` ADC / power-good diagnostic |
| PA6 | `LED_DATA_TIM` timer + DMA output to the level buffer |
| PA7 | `LED_DATA_ENABLE` (buffer OE; default disabled) |
| PA2 / PA3 / PA5 / PB0 (proposal) | RUN / COMM / PWR / FAULT LEDs.  **2026-09-17:** PC13 does not exist on the LQFP-32 STM32F303K8; the FAULT LED pin must be re-assigned.  PB0 is the proposal in `LED_CAN_NODE_REV_A_SCHEMATIC_2026-09-17.pdf`; not yet fixed. |
| PA8 | service input; PA9 / PA10=debug UART; PA4, PA15, PB1, PB3-PB7 are NC in Rev.A (PB0 reserved for FAULT LED if the proposal is accepted) |

## 4. Tape connector and data interface

| Item | Requirement |
|---|---|
| Tape protocol | WS2811-compatible, 800kbps nominal, one-wire NRZ `LED_DATA`.  It is **not SPI**.  F303 timer+DMA emits the waveform so CAN reception does not perturb frame timing. |
| Board data connector | JST GH 2pin: pin 1=`LED_DATA_5V`, pin 2=`GND_PWR`.  It joins an external short adapter harness that merges this data/GND pair with the direct fused `+24V`/GND tape power wires into the tape's supplied 3pin SM-style connector. |
| Data voltage | `SN74AHCT1G125` powered at 5V translates the F303 3.3V timer signal to a 5V TTL-compatible tape signal. |
| Default-off | Buffer `/OE` has a 100k pull-up to 5V (disabled); F303 asserts it only after boot/self-test and a valid command.  MCU reset, brownout, or unpowered board leaves `LED_DATA` inactive. |
| Signal integrity | 33-100Ω series resistor at the connector, 100k pulldown on the cable-side data net, and a low-capacitance 5V ESD footprint beside the connector.  Select the final resistor after observing the installed cable waveform. |
| Cable topology | Keep data cable short and paired/referenced with GND.  The external adapter harness maps tape `+24V <- fused distribution`, `Data <- LED_DATA_5V`, `GND <- distribution GND + node GND reference`; never reverse the data-direction arrow printed on the tape. |
| Maximum frame buffer | Initially 300 pixel groups (900 bytes RGB) maximum.  Higher counts are permitted only if the final effect engine/RAM budget is measured. |

The strip is continuously powered by its fused 24V branch; normal colour/effect control is by data, not repeated power cycling.  An optional future high-side tape-power switch is a separate thermal/EMI design and is not part of Rev.A.

## 5. CAN control baseline

The central board sends high-level commands rather than RGB data for every pixel every refresh.  Standard 11-bit Classic CAN frames, 8-byte payloads, little-endian fields; final identifiers go in `COMMUNICATION_NAMING_AND_IDS.md` before firmware starts.

| Message | Required behaviour |
|---|---|
| `LED_NODE_CONFIG` | pixel-group count, global brightness ceiling, logical segment layout, configuration sequence |
| `LED_NODE_EFFECT` | effect ID, primary/secondary RGB, speed, direction, brightness, and sequence number |
| `LED_NODE_STATUS_REQUEST` | requests bus voltage, logic rails, MCU reset reason, frame counter, timeout/fault bits |
| `LED_NODE_STATUS` | reports the above and the active effect/configuration |
| Central `ESTOP` broadcast | immediately blank decorative output; tape power need not be disconnected. |

On boot, LED data is disabled and the default visual state is dark.  A 500ms valid-command timeout blanks the strip and latches `CAN_TIMEOUT`; receiving traffic alone must not restore a prior effect—an explicit `LED_NODE_EFFECT` does.  This makes loss of the expansion CAN conspicuous without treating the tape as a safety device.

## 6. Layout and release gates

1. Place only the low-current board-input connector and buck on the PCB.  Keep the 5A tape fuse and tape current loop as an external harness/distribution assembly.
2. Keep buck switching loop compact and away from CANH/CANL, crystal, and `LED_DATA` connector trace.
3. Locate the AHCT buffer, series resistor and ESD at the LED connector; no long 3.3V data trace reaches the harness.
4. Verify 5V and 3.3V first with no tape, then SWD, CAN and reset/default data-low behaviour.
5. Test a known WS2811-compatible 24V tape at low brightness, then all-white worst case with a bench current limit.  Measure connector/copper temperature and the first/last pixel supply voltage.
6. Verify CAN traffic during maximum-rate effects has no frame errors and no waveform glitches; test boot, watchdog reset, brownout, E-stop broadcast and 500ms CAN timeout.
7. Run schematic ERC 0 and PCB DRC 0 before fabrication.

## 7. Primary sources

- ST `STM32F303x6/x8` datasheet DS9866: https://www.st.com/resource/en/datasheet/stm32f303c8.pdf
- ST STM32F3 reference manual RM0316 (timer/DMA): https://www.st.com/resource/en/reference_manual/rm0316-stm32f303xbcde-and-stm32f358xc-advanced-armbased-32bit-mcus-stmicroelectronics.pdf
- TI `TCAN1051V-Q1` datasheet: https://www.ti.com/product/TCAN1051V-Q1
- TI `LMR51606` datasheet: https://www.ti.com/product/LMR51606
- TI `SN74AHCT1G125` datasheet: https://www.ti.com/product/SN74AHCT1G125
