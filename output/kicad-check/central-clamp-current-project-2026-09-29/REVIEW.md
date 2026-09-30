# Corrected clamp update destination

The previous change targeted central-board-placement only. The current project has since been saved under hardware/central-board/central-board, using safety-1.kicad_sch with a different layout. Applied the same D405 AOS SMBJ33CA / Device:D_TVS / Diode_SMD:D_SMB change to that current sheet, retaining its placement and UUID.

Exported nets are identical after X401 -> D405 reference substitution. D405 is across J402 pins1/2. ERC before0 / after0. Other project file hashes, including PCB, are unchanged. Rendered and visually reviewed safety.png. PCB import remains separate; no D405 footprint was added to PCB in this repair.
