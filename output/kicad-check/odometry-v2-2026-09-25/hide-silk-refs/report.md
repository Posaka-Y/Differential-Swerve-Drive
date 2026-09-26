# ODOM V2 silkscreen reference hiding — 2026-09-25

The PCB was backed up as `before.kicad_pcb` (SHA256 `F2590A5EBA3AEA138658FE76D7B180A2051A0AD0310E2BCADE900857280EDCBE`). All **22** visible footprint Reference fields on F.Silkscreen were set hidden. No B.Silkscreen reference was visible. No silkscreen PCB text or footprint graphic used `${REFERENCE}` or a literal reference designator, so no graphics were removed.

After saving and loading the source board again, visible silkscreen references and reference text graphics are both **0**. Footprint reference identifiers remain stored. A before/after semantic fingerprint of footprints, pads, pad nets and positions, other fields, tracks, vias, and zones matched: `5de4ebc80a10c06197ed85fcc3f985016ff7c9d4ee68abbed6d7f87cfa16cd46`. Board geometry, nets, and non-reference text were not intentionally changed. The final board and `readback.kicad_pcb` hashes match: `95981AA83F985876DC32AAE232E1BD08BE54DA5ED751CDC446A3000C5C141EDD`.

ERC/DRC were not rerun because this change affects only Reference-field visibility.
