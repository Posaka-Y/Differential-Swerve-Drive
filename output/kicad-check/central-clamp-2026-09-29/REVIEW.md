# D405 SMBJ33CA clamp — 2026-09-29

User authorized replacing X401 with the proposed bidirectional TVS. Selected manufacturer is Alpha & Omega Semiconductor (the source linked in the immediately preceding response), MPN SMBJ33CA. The earlier Littelfuse discussion remains historical; do not mix its 11.3A pulse parameter with AOS 11.6A.

- Symbol: Device:D_TVS (bidirectional); ref D405, retaining original instance UUID.
- Footprint: Diode_SMD:D_SMB; two 2.5 × 2.3 mm lands, centers ±2.15 mm, inner gap 1.8 mm.
- [AOS package outline](https://www.aosmd.com/sites/default/files/res/package/DO-214AA.pdf): minimum land dimensions 2.16 × 2.26 mm, maximum inner gap 2.74 mm. Standard footprint satisfies these. Bidirectional device has no functional mounting polarity.
- [AOS datasheet](https://www.aosmd.com/sites/default/files/res/datasheets/SMBJ33CA.pdf): VRWM33V; VBR36.7–40.6V at1mA; VC53.3V at11.6A. 600W rating is for the specified 10/1000us pulse, with datasheet mounting/temperature conditions; it is not guaranteed solely by assigning this footprint. Local official PDFs archived here.
- D405.1 = J402.1 (ESTOP_LOOP_RETURN), D405.2 = J402.2 (COIL_NEG). Whole exported netlist identical after ref rename. Other schematic file hashes unchanged.
- ERC before/after: 4 errors, 0 warnings, all pre-existing in CAN. Visual SVG inspection completed.

Pending: actual harness/temperature/pulse energy validation, Q401 OFF and NC opening transients, actual contact release within10ms. X402 return connection, fuse and connector selection remain unresolved. No PCB, PDF or firmware changes.
