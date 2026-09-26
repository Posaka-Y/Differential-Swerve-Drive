# ODOM V2 component/layout audit (versioned saved-file snapshots)

## 2026-09-25 18:13 saved schematic update

The user saved the editor after the initial snapshot below. The new root schematic SHA-256 is `A2F4A7C09849111A95E8CE5AED9D5D15C15C3BAEF9B9A07A132F4DBBC034A9F9`. A fresh KiCad XML netlist export to `tmp/pdfs/odom_v2_latest_2026-09-25.xml` establishes:

- **The earlier J8/SWD vs J3/orphan finding is resolved in the newly saved schematic.** Root J3 is now `FTSH-105-01-L-DV-K-P`, symbol UUID `17446a2e-9e6d-48e0-80b5-f19b6ebbe132`, matching PCB J3 path. J8 is the CAN sheet's `BM03B-GHS-TBT(LF)(SN)`, UUID `752e8945-8ca7-475a-a6b2-e18d0bc2851a`, matching PCB J8 path. J9 UUID `179092da-efeb-49c3-aad8-b3258df33855` matches PCB J9.
- Latest schematic J3 pin nets: 1 `PWR_3.3V` (VTref), 2 SWDIO, 3/5/9 GND, 4 SWCLK, 6 SWO, 7/8 NC, 10 NRST. J9: 1 GND, 2 USART2_TX, 3 USART2_RX. U3/U7/U9: pin 2 GND and pin 5 `PWR_3.3V`.
- Latest schematic J3 is `(dnp no)`, while the saved PCB snapshot J3 is `(attr smd dnp)`; the PCB update should clear this assembly mismatch if J3 is to be fitted. The separate PCB repair agent is updating a candidate. The connector/cable pin-7 fit and local buffer decoupling findings below remain open until PCB placement and parts are reviewed.

The next section records the **earlier, pre-save** snapshot for traceability; its first J8/J3 mismatch is no longer current.

Read-only review on 2026-09-25 of `hardware/odometry-board-v2/Oddom board.kicad_pcb` (then last saved 2026-09-24 00:05:29; SHA-256 `E083D5B01C538ED794A6CB6537A5BC357CC32824D3408EF69E4FFA39D555C1C3`). The KiCad editor then contained unsaved changes. No PCB or schematic was edited for this review.

## Confirmed mismatches in the saved files

1. The current schematic calls **J8** the Cortex Debug 10-pin connector (root symbol UUID `dfcbf895-c956-4ade-92ed-07736ff78b6e`, blank footprint). The saved PCB's **J8** is a 3-pin JST GH CAN connector (`SamacSys:BM03BGHSTBTLFSN`): pad 1/2 are CAN TVS nets, pad 3 is GND, pads 4/5 are mechanical. The saved PCB's 10-pin SWD connector is instead **J3** (`SamacSys:FTSH10501LDVKP`, path `/17446a2e-9e6d-48e0-80b5-f19b6ebbe132`), whose path does not match the current schematic J8 UUID. This is an old-footprint/ref synchronization error, not evidence that the new J8 has been implemented.
2. PCB J3 is marked `(attr smd dnp)`. For the currently placed SWD header this means DNP in board data, so confirm desired assembly status when replacing/synchronizing it. Its saved pad nets are electrically in the intended order: 1 VTref (`PWR_3.3V`), 2 SWDIO, 3/5/9 GND, 4 SWCLK, 6 SWO, 7/8 NC, 10 NRST.

## Physical/layout review

- The saved J3 value/MPN is Samtec `FTSH-105-01-L-DV-K-P`. [Samtec's product page](https://www.samtec.com/products/ftsh-105-01-l-dv-k-p) confirms 10 contacts, 2 rows, 1.27 mm pitch, SMT, a keying notch, and a pick-and-place pad. Local footprint rows have 1.27 mm along-row pad pitch; the pin-1 silk dot is on the same end as pad 1. The SamacSys description says “Unshrouded,” whereas Samtec identifies the configured `-K` as a keying notch: use the exact manufacturer configuration and mating drawing for the final mechanical review. The footprint contains physical pad/pin 7 even though the Cortex/MIPI definition labels position 7 KEY/NC. A blocked-hole cable may not mate; exact cable/adapter and pin-7 mechanical treatment remain **unverified**, and a keying notch alone does not prove compatibility.
- UART J9 is present on saved PCB as `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical`, with pin 1 GND at (88.985, 113.225), pin 2 `USART2_TX` at (91.525, 113.225), pin 3 `USART2_RX` at (94.065, 113.225) mm. It is on the board's lower edge. These pad nets match the 2026-09-23 [V2 requirement](../../../docs/electrical/UNIT_ODOMETRY_V2_REQUIREMENTS.md) and the current schematic J9 UUID `179092da-efeb-49c3-aad8-b3258df33855`. Its final pin-1/GND/TX/RX silkscreen readability and probe/cable access should be inspected at actual print scale.
- U3/U7/U9 `SN74LVC2G17DBVR` pad 2 is assigned GND and pad 5 is assigned `PWR_3.3V` in the saved PCB. Placement does **not** yet satisfy the stated “each IC nearby 100 nF” intent: nearest capacitor bridging 3.3 V/GND is C28 100 nF 18.29 mm from U3, C4 100 nF 16.91 mm from U7, and C8 100 nF 4.96 mm from U9 (footprint-center distances). U3/U7 have no local 100 nF within 8 mm. Add/relocate local decouplers in the schematic/placement phase and recheck actual rail routing; this is a design recommendation, not a change made in this audit.
- The saved U1 MCU's VDD/GND/VCAP pads have assigned nets; buffer power pins likewise have assigned nets. Net assignment alone does not establish copper connectivity. Detailed ERC/DRC, pad-to-net, and route checks are covered by the separate electrical audit.

## Review boundary

The current saved PCB still predates the in-editor save; all conclusions above describe that exact disk snapshot. Before release, compare the final chosen SWD header's manufacturer land pattern, its top/bottom and mating view, true pin 1, physical position 7, and the actual debugger cable against the completed PCB. The V2 requirements intentionally leave exact SWD connector/cable selection open.
