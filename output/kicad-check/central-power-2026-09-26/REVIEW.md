# 中央電源回路確認 — 2026-09-26

対象: `hardware/central-board-placement/S02A_power_input-1.kicad_sch`の17:56:40保存版。snapshotと原本のbyte一致を確認。確認のみで電源回路の原本は編集していない。Teensy J210の表示順修正は別途S02Bへ反映済み。

## 修正が必要な箇所

1. **R104の接続先が違う。** 現在はR102.1/R103.1/IC1.1(EN/UVLO)とR104.2が同じネット。正本はR102→EN→R103→OVLO→R104→GNDの直列3抵抗。R104の上側をIC1.2(OVLO)/R103.2へ接続する。現状は5VでEN≈5×221/(732+221)=1.16V、1.20V typのUVLO閾値に届かない。OVLOもR103経由でEN電圧へ寄るため、仕様の4.43/5.46V窓にならない。
2. **C103とC104のpin1が未接続。** pin2のみ+5V_SYSへ接続されている。もう片側をGND_CTRLへつなぐ。C104は購入型番・極性を確定して正負を合わせる。
3. **F205が電源シート内で2個ある。** 0.75AのD101給電用F205と、0.5Aの独立LED枝F205が共存。D205/R205は正本ではTeensy用F205の保護後ネット+5V_TEENSY_Fを表示する。現在の独立0.5A枝はその給電枝の電圧を表示していない。Teensy枝を正本の1本へ整理する。
4. **S02A/S02Bに給電枝のRefが重複している。** 新作成電源回路と旧仮配置のF201〜F206/R201〜R206/D201〜D206/J201〜J204が共存し、F205はプロジェクト全体で3個。電源回路へ統合するなら、旧仮配置を整理して重複を解消する。注釈エラーがあるため、全体netlistの同一Refを合格判定に使わない。
5. **Part Loader部品の分割ランド番号に注意。** SamacSysのTPS259470LRPWRはsymbol/footprintとも14番号。TI公式RPW0010Aは10端子で、1/4/7/10はL字ランド。取り込みfootprintの11/12/13/14はその角部にあり、11→10、12→1、13→4、14→7と同じ電気端子として扱う必要がある。現在は11〜14へNCが付いている。同一pad番号を使う10pin対応footprint/symbolへ整理してからPCBへ転送する。角部ランドを単純削除する意味ではない。
6. **IC1のfootprint IDにlibrary prefixがない。** 現在は`TPS259470LRPWR`のみ。ローカルに実在する名前は`SamacSys:TPS259470LRPWR`。前項の番号修正を施したプロジェクト用footprintを用意してから割当する。
7. **USB側回路はまだ未配線でページ外。** U102=(742.95,252.73)、R108=(346.71,-111.76)、C106=(270.51,-60.96)などA2の外にあり、今回の電源図SVGに現れない。J102→D102→VIN経路はできているが、USB→U102→+5V_SYSは未成立。USB単独のCAN/ノード給電はまだできない。
8. **信号・GND命名とシート間接続を統一する。** 現在のFLT pull-upラベルは`3.3V_TEENSY`、GND電源シンボルは`GND`。正本は`+3V3_TEENSY`/`GND_CTRL`。+5V_SYSやVIN_TEENSYはlocal labelなので他シートへ同名を書くだけでは接続されない。global/hierarchical信号等で実接続を作る。

## 接続を確認できた部分

- J101.1→IC1 IN5、C101/C102入力デカップリング、IC1 GND8、R101 750Ω→ILM9、R106/C105→DVDT7の主要経路は正本と整合。
- D101/D102はpin1(K)をVIN_TEENSYへ集約、D102 pin2(A)をJ102 VUSBへ接続する向きになっている。
- 駆動3枝/ODOM枝のPPTC→コネクタと抵抗→LED→GNDの接続形は正本と整合。入力分圧・重複Ref等の修正を済ませるまで動作成立扱いにはしない。

## 証拠・資料

- `snapshot/`、`svg/power.png`、`../central-teensy-pin-order-2026-09-26/erc.rpt`と`placement.net`。ERCにC103/C104未接続、footprint prefix不足、枝端の未接続等が記載されている。
- TI公式[電気端子表とRPW0010Aランド例](https://www.ti.com/lit/ds/symlink/tps25947.pdf): 5〜6ページ、73ページ。メーカーPDFを保存し`official-land-pattern.png`へ描画して確認。
- `docs/electrical/CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md` 3.1/3.2。

電源側は確認のみ。回路図は作成途中であり、通電・製造用の合格ではない。
