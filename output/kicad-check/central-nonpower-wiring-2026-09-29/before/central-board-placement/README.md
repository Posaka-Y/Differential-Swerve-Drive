> **E-stop 2026-09-26更新:** U401 LTV-817S 1ch、J401は4pin（型番未確定）。ボタン別/予備監視16部品を削除。現在158実部品。前回ERCは変更前の記録。

# 中央基板 — 階層回路図・部品配置からの設計開始

> **2026-09-29更新:** J210の使用端子40本は用途global label、予約8本はNCで区別。新規global label30個、再アーム誤記READ_SW_N→REARM_SW_Nを訂正。C212/GNDだけ表示干渉を避けて移動し、同名3V3で接続。全48padのネット対応と既存ネット分断なしを検証。ERC217→194件（未配線等が残る）。最新人間向けPDFは`output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-29.pdf`。KiCadで開いている場合は再読込してから編集を続ける。

> **2026-09-26現在: ユーザーがS02A電源回路の手配線を開始。** 以下の未配線/部品数/ERC一覧は初期配置時点の履歴。生成器で原本を再生成しない。電源回路は修正・再確認済み。最新記録は`output/kicad-check/central-power-fix-2026-09-26/REVIEW.md`を参照。現在174実部品、電源シートERC0件、全体383件。既にエディタで開いている場合は古い画面を保存せず再読込すること。

2026-09-23のユーザー指定に基づく、手配線用の新規プロジェクト。
トップシートを目次とし、機能別の子シートへシンボルを配置する。
**電源回路は配線・修正済み。他回路は未配線。製造用の完成回路図ではない。**

## 開き方

このフォルダの `central-board-placement.kicad_pro` をKiCadで開き、回路図エディタから
トップシート内の各階層シートを開く。
以後の手編集はこの新規プロジェクトで行う。
既存の `../central-board/central-board/` は別の作業データであり、今回置換しない。

トップ＋7子シート、178部品（LTV-847Sの4ユニットを含め181シンボル）。

| 子シート | 用紙 | 部品数 |
|---|---|---:|
| 5V入力・eFuse・USB diode-OR | A2 | 32 |
| 5V分配・Teensy・表示 | A2 | 38 |
| CAN1 センサ | A3 | 10 |
| CAN2 拡張 | A3 | 11 |
| CAN3 駆動 | A3 | 10 |
| E-stop監視・中央コイルdriver | A2 | 33 |
| Matek監視端子・外部I/O | A2 | 44 |

## 作業の境界

- 部品配置のみ。配線、ネットラベル、階層信号ピン、電源シンボル、NC指定は未作成。
- RefDesと部品値を付け、機能ごとの配線用余白を設ける。
- 未確定の部品値・型番・footprintはTBD/REVIEW等で明示する。
- 多ユニット部品は同一RefDesの各unitとして配置する。
- 未接続に関するERC結果はこの段階では意図された状態。ERC合格や製造可能とは扱わない。
- PCB配置・配線は含まない。

## 仕様参照

優先する資料:

1. `docs/ARCHITECTURE_DECISIONS.md`
2. `docs/electrical/PCB_BATCH_V2_CENTRAL_PLAN.md`
3. `docs/electrical/CENTRAL_BOARD_REV1_PDF_CHANGELOG_2026-09-23.md`
4. `docs/electrical/CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md`

2026-09-23版のCAN端子・中央コイルdriver・Teensy一体ソケットを基準とし、
旧資料の別体driver、基板内Buck、主接点専用監視回路を復活させない。
専用CANはGH3、汎用拡張CANだけは既存GH4の区別を保つ。
未確定箇所は接続・footprint・購入型番を確定してからPCBへ進める。

### 旧資料を参照するときの注意

- `reference-2026-09-12/modules-native/POWER_A_B1.kicad_sch` の旧eFuseシンボルは
  TPS259470LRPWRのpin番号が正本と異なるため流用しない。
  正番号はEN/UVLO=1、OVLO=2、AUXOFF=3、FLT=4、IN=5、OUT=6、
  dVdt=7、GND=8、ILM=9、ITIMER=10。
- Teensyのpad4は`MOTOR_PWR_EN`に使用する。旧転記表末尾のNC列挙より
  正式な48pin対応表を優先する。配置時点ではNCシンボル自体を置かない。
- Teensyの一体48pad footprintは2個の24pinシンボルへ重複して割り当てない。

## 再生成について

`tools/kicad/generate-central-placement.py` と部品一覧JSONは初期配置の生成元。
**手配線を始めた後は再生成で上書きしないこと。**
必要な変更はKiCad上で行うか、別出力先へ生成して比較する。

## 初期配置の確認結果

### 2026-09-26仕様差分の反映

- Teensy J210の右列表示順を48→25へ訂正（左列1→24、USB側を上）。ライブラリと回路図内cache、生成器を同期。全48pinの番号/信号名対応とソケットfootprintは保持。USB END表示を追加。PDFのTeensy図は元からこの順序。

- 同日追加指定で駆動Unit 1〜3の給電枝TP211〜TP213を削除。LEDで給電状態を見て、必要時はJ201〜J203で電圧を実測する。最新ERCは未接続493/入力未駆動13/電源未駆動15。

- USB側U102 `TPS259470ARPWR`、R107〜R112、C106〜C108、TP106を追加。外部5V優先のOVLO分圧、約1A制限、既存D102保持経路は転記表3.1に従う。
- GPIO電源列選択JP505を追加。1=3V3、2=VCC_GPIO_EXT（J507-1）、3=5V_EXP。ショートピン1個、出荷時1-2。IO/TVSは3.3Vのまま。
- J210のpad11/pin9はUSB fault入力候補と注記（提案）。pad36はNC。接続は手配線時に作成する。
- 既存全素子の座標/向き/UUIDを保持し、電源シートをA2へ拡張して下側へ追加した。元ファイルは`output/kicad-check/central-placement-2026-09-26/before/`へ退避。
- U101 `TPS259470LRPWR` / U102 `TPS259470ARPWR` のRPW footprintは未割当。ユーザーがPart Loaderで取得予定。JP505はKiCad標準1x3ヘッダfootprintを使用し、購入型番は未確定。
- 手配線用回路図: `output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-26.pdf`（15ページ、14=USB eFuse、15=GPIO電源選択）。9月23日版は履歴として保持。
- ERCは未接続496、入力未駆動13、電源未駆動15のみ。配線前の状態であり製造用のERC合格ではない。

以下は2026-09-23初期配置時点の結果。最新版の検査は上記9月26日記録を参照。

KiCad 10のSVG/netlist出力成功。部品一覧との全件照合、Ref/unit重複なし、
主要ICのpin番号、割当footprintの実在、配線/ラベル/NCなしを検査した。
8ページを画像化して重なり・ページ外はみ出しを目視確認済み。
ERCは意図的な未接続464件・未駆動24件で、off-grid/library mismatchはない。
検査記録は `output/kicad-check/central-placement/`。
