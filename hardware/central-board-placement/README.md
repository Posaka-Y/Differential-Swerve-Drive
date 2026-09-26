# 中央基板 — 階層回路図・部品配置からの設計開始

2026-09-23のユーザー指定に基づく、手配線用の新規プロジェクト。
トップシートを目次とし、機能別の子シートへシンボルを配置する。
**電気配線は未作成。PCBへ転送して製造するための完成回路図ではない。**

## 開き方

このフォルダの `central-board-placement.kicad_pro` をKiCadで開き、回路図エディタから
トップシート内の各階層シートを開く。
以後の手編集はこの新規プロジェクトで行う。
既存の `../central-board/central-board/` は別の作業データであり、今回置換しない。

トップ＋7子シート、169部品（LTV-847Sの4ユニットを含め172シンボル）。

| 子シート | 用紙 | 部品数 |
|---|---|---:|
| 5V入力・eFuse・USB diode-OR | A3 | 21 |
| 5V分配・Teensy・表示 | A2 | 41 |
| CAN1 センサ | A3 | 10 |
| CAN2 拡張 | A3 | 11 |
| CAN3 駆動 | A3 | 10 |
| E-stop監視・中央コイルdriver | A2 | 33 |
| Matek監視端子・外部I/O | A2 | 43 |

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

KiCad 10のSVG/netlist出力成功。部品一覧との全件照合、Ref/unit重複なし、
主要ICのpin番号、割当footprintの実在、配線/ラベル/NCなしを検査した。
8ページを画像化して重なり・ページ外はみ出しを目視確認済み。
ERCは意図的な未接続464件・未駆動24件で、off-grid/library mismatchはない。
検査記録は `output/kicad-check/central-placement/`。
