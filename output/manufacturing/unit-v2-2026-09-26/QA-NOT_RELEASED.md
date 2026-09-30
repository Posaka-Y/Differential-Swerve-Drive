# Drive unit V2 manufacturing package — NOT RELEASED

Generated 2026-09-26 from the fixed source snapshot in `source-snapshot/`. The original PCB was not changed; source and snapshot PCB SHA256 both equal `6CA06F7E762D0B9C2C538289C8F422A5A733A9F24DFCE5F2FCED9409B9B91AF8`.

`unit-v2-2026-09-26-NOT_RELEASED.zip` contains fabrication data only: eleven Gerbers (four copper, F/B mask, F/B silk, F/B paste, Edge.Cuts), one job file, and separate Excellon PTH/NPTH drill files. All 14 ZIP members were read back and compared byte-for-byte with the exports. The job manifest's layers match the Gerbers; PTH and NPTH metadata are correctly separated. ZIP SHA256: `6be73e4a430626386258a4f2733c8435833412b0863ec93c91d166fa77b5a9d5`.

Four-layer stack: F.Cu / GND Plane / Power Signal / B.Cu, 1.6 mm thickness. The nominal maximum Edge.Cuts centerline envelope is **45 × 45 mm**, with shaped top/bottom edges and rounded mounting ears; the job reports 45.05 × 45.05 mm including the 0.05 mm outline stroke. Finish remains unspecified (`None`). Drill report: **107 PTH** (104 × 0.30 mm, 3 × 1.00 mm), **6 NPTH** (2 × 0.90 mm, 4 × 2.70 mm). `preview-top.svg` and `preview-top.png` were inspected for the continuous outline and hole locations. Silkscreen reference designators were excluded from Gerber export. Bottom paste has no openings.

## Verification and release blockers

- ERC: zero electrical errors, one J8 footprint-library-link warning.
- DRC: zero error-level routing violations and zero unconnected items; seven warnings remain. Six embedded footprints differ from installed library copies (D2, U1, SW3, logo, J6, D7), and the RX silkscreen text overlaps D2's silkscreen at `(90.85,64.215)` mm.
- Schematic parity: ten warnings, including J8's unqualified footprint ID and PCB/schematic DNP disagreement; four `REF**` mounting holes and QR graphics account for the extra/duplicate-footprint warnings.
- Full schematic netlist versus PCB pad audit: no functional mismatch; U1 pad 4 NC differs only by `N/C` versus `N{slash}C` escaping. All schematic physical components are present. Added logo, QR, and mechanical holes have no signal pad discrepancy.
- Project DRC exclusions are empty. Ignored categories remain courtyard, via-centering, tuning-profile, symbol footprint-filter, and footprint component-type checks. Rules were not relaxed.
- **Independent electrical audit awaiting user decision:** J6's current order is `1=CS, 2=MISO, 3=GND, 4=MOSI, 5=SCLK, 6=+5V`, reversed from the previously specified encoder connector order. R13/R14 are 33k/22k rather than the earlier 22k/10k values. External C620 bus termination remains unconfirmed. The package preserves the current saved source and does not resolve these design decisions.

Reports and snapshots are outside the ZIP. This archive is **NOT RELEASED for fabrication** until the electrical questions and relevant warnings are resolved or explicitly accepted. No board order was placed.

## User confirmation after export — 2026-09-26

J6 reversal is intentional for the cable. Board-to-sensor pin mapping is 1->6, 2->5, 3->4, 4->3, 5->2, 6->1. R13=33k (high side) / R14=22k (low side) is confirmed; the user will procure 33k. Divider ratio is 0.4, requiring the matching V2 firmware scale (firmware not modified). These two questions are resolved; the source and ZIP require no changes for them. External C620 termination, SWD mating/assembly attribute and remaining warnings are still unverified. The NOT_RELEASED name is retained.

## 2026-09-26 C620終端のユーザー確認

2個のGHポートから各ESCへ接続し、各ESCの120Ω終端をONにする構成で確定。ESC①―駆動基板―ESC②の両端終端なので、C620用の基板内終端なしは設計意図に一致し不具合ではない。J6逆順・33k/22k分圧・外部終端の3確認事項はすべて解消。回路/PCB/ZIPは変更不要。電気的ERC/DRCエラー・未接続は0。残るライブラリ/シルク/実装属性・ケーブル機構確認を、この構成確認だけで合格に変更しない。
