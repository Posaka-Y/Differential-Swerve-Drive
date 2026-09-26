# Teensy 4.1 socket footprint

`DifferentialSwerve:Teensy41_Socket_2x24` places two 1x24 through-hole socket strips as one 48-pad footprint. It is a reusable library asset; it has not been placed on the central PCB.

## Coordinates and numbering

Viewed from above with the Teensy USB connector at the left:

| Row | Logical pads | Coordinate rule |
|---|---|---|
| Near/bottom row | 1–24, left to right | pad `n`: `x=(n-1)*2.54 mm, y=+7.62 mm` |
| Far/top row | 48–25, left to right | pad `n`: `x=(48-n)*2.54 mm, y=-7.62 mm` |

Pad 1 is Teensy GND and pad 48 is VIN, both at the USB end. This numbering follows `docs/electrical/CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md`; check every pad against its socket-pad table when making the matching 48-pin symbol. A pair of separate 24-pin schematic connectors cannot both be assigned to this single footprint without replacing them with one 48-pin symbol.

PJRC's [official dimension drawing](https://www.pjrc.com/teensy/dimensions_teensy41.png) shows **15.24 mm between the two header-row centers**, 2.54 mm pin pitch, a 60.96 mm long by 17.78 ± 0.6 mm wide board. The 17.78 mm dimension is the **board width, not row spacing**. The F.Fab rectangle depicts that nominal board outline. `USB END` and square pad 1 establish orientation. The F.CrtYd rectangle is a basic board-body envelope, not a proven USB cable or microSD clearance.

The 1.7 mm copper pads and 1.0 mm drills copy KiCad 10's `Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical`. PJRC [recommends](https://www.pjrc.com/store/socket_24x1.html) Sullins `PPPC241LFBN-RC` or `PPTC241LFBN-RC` socket strips. Before fabrication, compare the purchased socket's solder tails with the 1.0 mm drill and 1.7 mm pad, then check a 1:1 print and a physical Teensy/socket fit. PJRC also [warns](https://www.pjrc.com/teensy/eagle_lib.html) that a published Eagle library used header holes that were too small.

Keep components, test points and exposed copper out from under the Teensy, and reserve access for its USB connector, Program button and microSD card. This footprint does not encode a copper keepout, USB collision envelope or 3D model; apply and verify those constraints during PCB placement. Cut and continuity-check the Teensy VUSB–VIN link for the specified external-power diode-OR assembly.
