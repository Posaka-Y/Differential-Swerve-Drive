# Central board schematic

## Files

- `central-board.sch`: 責務別child sheetを並べたroot index。
- `modules/100-power.sch`: 5V入力、eFuse、star distribution。
- `modules/200-teensy.sch`: Teensy 4.1 socket、固定pin map、安全出力のdefault state。
- `modules/300-can.sch`: Sensor / Expansion / DriveのCAN 3系統。
- `modules/600-safety.sch`: 24V E-stop loop、contactor driver、絶縁監視、motor bus sense。
- `modules/700-monitoring.sch`: INA238と外付けKelvin shunt interface。
- `modules/800-expansion.sch`: I2C/UART/SPI/GPIO、rearm、test access。
- `../../tools/kicad/generate-central-board-modules.ps1`: root＋6 moduleの再生成script。
- `../../tools/kicad/generate-central-board-schematic.ps1`: module生成の入力になる詳細回路generator。通常は直接実行しない。
- `../../docs/electrical/CENTRAL_BOARD_SCHEMATIC_WITH_BOM.html`: オドメトリ／駆動module資料と同じA3横テンプレートのreview正本。
- `../../output/pdf/CENTRAL_BOARD_SCHEMATIC_WITH_BOM.pdf`: 1機能1ページの回路図＋注意点＋簡易BOM、全7ページ。

## 開き方

KiCad Schematic Editorから`central-board.sch`を直接開き、rootのsheet blockから担当moduleへ移動する。初回保存時にKiCadの現行`.kicad_sch`形式へ変換してよい。変換後は生成scriptによる上書きを止め、`.kicad_sch`と変換されたchild sheetsを正本へ切り替える。

## 現段階の使い方

人間reviewでは`CENTRAL_BOARD_SCHEMATIC_WITH_BOM.pdf`を先に使い、1機能ずつ信号の流れ、注意点、BOMを確認する。KiCad sheetはその結果を転記してERCするための下位資料であり、review PDFの代用にはしない。TPS259470、TCAN1051、INA238、LTV-847Sなどの正式pinはdatasheetとKiCad symbolの両方で最終照合する。

PCBへ進む前に次を行う。

1. generic symbolを正式なlibrary symbolへ置換し、pin typeとfootprintをdatasheetに対して照合する。
2. 図中`TBD`をすべて閉じる。特にeFuse UVLO/OVLO、24V input保護、contactor clamp、shunt sense source fuse。
3. `docs/electrical/CENTRAL_BOARD_SCHEMATIC_REFERENCE.md`の接続表とcross-checkする。
4. No Connect、PWR_FLAG、power pin typeを整理し、ERC 0件へ収束させる。

現時点のKiCad ERCはgeneric pin-explicit symbolとlegacy `.sch` labelのためacceptance判定に使用しない。PDF/netlist出力が可能なことまでは確認済みで、PCB開始条件は`.kicad_sch`化後のERC 0件である。
