# Unit V2 silkscreen reference hiding — 2026-09-25

Backed up `unit-board.kicad_pcb` before editing (SHA256 `F2B81B8C05F4B1F1EAA4EC8A45D55E5526E4884B96FBA159B525C17AB91BEED1`). Set all **55** visible F.Silkscreen footprint Reference fields to hidden; there were no visible B.Silkscreen reference fields or `${REFERENCE}` graphics. The non-reference board text, including the B.Silkscreen product/title text, was preserved.

After saving and reloading, visible F/B silkscreen references and reference graphics are **0**. All footprint reference identifiers remain stored. Before/after non-reference fingerprint of footprint positions, pads/nets, other fields, tracks/vias, and zones matched: `220f9f4b3ff524284efdc2fcfc3270a08094b7699e147bfae96e99a3e45a1234`. Source PCB and readback copy SHA256 both equal `9709797F78A2A06F84D92798295B2DEAD76182454F93D7638E530BA2C173D42E`. ERC/DRC were not rerun for this display-only edit.
