> **作業先訂正 2026-09-29:** 現行は `hardware/central-board/central-board/central-board.kicad_pro`。22:45保存版へ移行済みで、クランプD405も `safety-1.kicad_sch` に反映済み。ERC0件。下記のcentral-board-placement対象/既存CAN4件という記載は以前の作業履歴。

> **2026-09-29採用更新:** ユーザー承認によりX401を **D405: Alpha & Omega Semiconductor SMBJ33CA（双方向TVS）**へ置換。J402-1（ESTOP_LOOP_RETURN/COIL_POS）とJ402-2（COIL_NEG）の間へ並列。symbol=`Device:D_TVS`、footprint=`Diode_SMD:D_SMB`。型番選定・KiCad反映済み、実ハーネスでのサージ/吸収エネルギー/解放10ms以内は実測残件。X402帰路結合は未確定。

# 中央基板：電源・CAN以外のKiCad配線

2026-09-29。対象は `hardware/central-board-placement/central-board-placement.kicad_pro`。ユーザーの「電源can以外全部…kicadの回路作成」の指定に基づく。旧 `hardware/central-board/central-board/` は今回の編集対象ではない。

## 反映内容

- S02B：Teensyの既存用途global label（使用40端子・予約NC8端子）とREARM RC回路を維持。D212赤をSTATUS_R_LED/R212へ、D213緑を+5V_SYS/R213へ訂正。D211緑はSTATUS_G_LED/R211。
- S04：J403の24V入力、F401、J401のNCループ往復、J402のコイル、U401 LTV-817S監視、R401/R402/D401、R409、TP401/TP406、U402/Q401の駆動・プルダウン・デカップリングを接続。保存版で消えていたJ401を現行4pin仕様で復元。
- S05：I2C0/1、UART7/8、SPI、GPIO8信号の100Ω直列抵抗とSRV05-4を配線。I2Cの2.2kΩプルアップはJP501〜504を介し、初期OPEN。GPIOをJ507〜J510の4pin×4組へ変更。JP505は4ポート共通の電源選択（初期1-2＝3.3V）。5V選択でも信号は3.3V固定。
- 目次の「未配線」表示を修正し、parts JSON/manifestを現保存版157参照番号へ同期。製造用BOMとしての確定ではない。
- S02A、S03_CAN1/2/3の回路図ファイルは編集前とバイト一致。電源/CAN内のネット構成も保存されている。PCB・ファームは変更していない。

## S04のコネクタと未確定インターフェース

| 端子 | 接続 |
|---|---|
| J403-1 / 2 | +24V_CTRL_IN / GND_24V_RETURN |
| J401-1 | ESTOP_LOOP_OUT（F401後、外部NC1→NC2へ） |
| J401-2 | ESTOP_LOOP_RETURN（外部NC直列の戻り、J402-1と監視抵抗へ） |
| J401-3 / 4 | ESTOP_LED_24V（F402後）/ GND_CTRL_LED |
| J402-1 / 2 | ESTOP_LOOP_RETURN（COIL_POS）/ COIL_NEG |
| X401-1 / 2 | コイル両端。クランプ方式・型番・解放時間未確定の機能ブロック |
| X402-1 / 2 / 3 | GND_CTRL / GND_CTRL_LED / GND_24V_RETURN |

**X402は導通を持つnet tieではない。** 帰路の結合位置・配線方針を未確定のまま見える形にしたインターフェースで、3本のネットを自動的に短絡していない。ドライバを動かすには論理GNDとコイル帰路の基準を確定する必要がある。X401も採用部品ではない。いずれもfootprintなしのTBD。

F401の定格、追加したF402（LED枝保護）の方式/定格、X401、X402、J401/J402/J403の正式品、SW211等の既存未確定品は残る。24V LED約0.3Wのユーザー実測を保持し、測定個数・接点動作・LED極性の未確認を確定扱いにしない。回路図上の配線完了と、実機使用・製造可能な設計の完了は別。

## GPIO4ポート

| コネクタ | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| J507 | VCC_GPIO_EXT | GND_CTRL | IO20_A6_EXT | IO21_A7_EXT |
| J508 | VCC_GPIO_EXT | GND_CTRL | IO24_A10_EXT | IO25_A11_EXT |
| J509 | VCC_GPIO_EXT | GND_CTRL | IO26_A12_EXT | IO27_A13_EXT |
| J510 | VCC_GPIO_EXT | GND_CTRL | IO40_A16_EXT | IO41_A17_EXT |

既存J502/J503と共通のSM04B-GHS-TB、KiCad標準 `JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal` を使用。[JST公式GH資料](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf)の4極型番、端子番号方向、1.25mmピッチ、基板パターンを確認。GHの50V/1A（AWG26）定格はシリーズ値で、回路側の枝制限や外部3.3V合計100mAの予算を増やすものではない。24V側J401等への自動流用はしていない。

## 確認結果と限界

- KiCad 10 CLI exportで指定186端子を照合。別途Teensy全48pad、GPIO4組、LED色と接続、フォトカプラ/逆並列ダイオード、MOSFET G/S/D、JP505、電源ネットの意図しない合流なしを検査。
- 電源/CANの4ファイルのSHA-256一致と、これらの既存部品間接続の一致を検査。
- ERCは編集前193件（error167/warning26）→編集後4件（error4/warning0）。残りは対象外CANのU311 VCC/VIO、U312 VIO、U313 VIOの `power_pin_not_driven`。今回のS02B/S04/S05は既存プロジェクト設定で0件。
- ERC設定・除外設定は変更していない。既存設定ではglobal label片端等4種類が無効のため、ERCだけに依存せずnetlistを照合した。TBD機能ブロックはERCだけでは未完成を検出できない。
- 3シートのSVGを書き出し、全体画像と安全回路拡大で表示を確認。1.27mm接続グリッドへ整列。古いPDFは説明用の前回版であり、今回のKiCad完全一致版ではない。

検証記録・編集前退避：`output/kicad-check/central-nonpower-wiring-2026-09-29/`。検証スクリプト：`tools/kicad/audit-central-nonpower-2026-09-29.py`。作成/整列/同期スクリプトはこの保存版向けの一回限りの移行用で、通常編集後に再実行しない。

次はS04の保護・帰路・コネクタを確定し、対象外CANの電源ERCを別途解消する。KiCadを開いたままの場合は、古い画面を保存せず外部変更を再読込する。


## 追記：TN686実測とX401試作候補（2026-09-29）

現物はユーザー申告TN686・24V/100A、コイル340Ω、内部保護なし。24V時約70.6mA/1.69W。解放10ms未満は掲載仕様で、外付けクランプを含む実測値ではない。

試作候補は **Littelfuse SMBJ33CA（双方向TVS）をJ402のコイル両端へ並列**。正式採用はまだ行わずX401は維持する。[Littelfuse公式SMBJデータシート](https://www.littelfuse.com/assetdocs/littelfuse_tvs_diode_smbj_datasheet.pdf?assetguid=09a6ae9a-73cb-4ac4-acac-e6dab92ab953)はVRWM33V、VBR36.7〜40.6V、VC53.3V@11.3Aを記載。600Wは規定パルス条件の定格で、連続許容電力ではない。実コイル電流での電圧波形・パルス幅・温度から耐量を照合する。

提示仕様110%を仮のコイル供給上限とすれば26.4V、Q401 OFF時の単純な電圧和は26.4+53.3=79.7V。[Q401 IRLML0100公式資料](https://www.infineon.com/part/IRLML0100)の100V耐圧に対する予備検討値であり、実電源上限・配線サージ・温度条件の保証は含まない。NC接点を開く停止ではコイル上側端子が負側へ振れるため、NC接点間にも供給電圧と逆起電圧の和が掛かり得る。MOSFET OFFとNC開放の両方の経路を確認する。

採用までの残件: コイルLまたはOFF時電流波形から蓄積エネルギーを確認、TVSのパルス幅/繰返し/温度ディレーティング、実装ハーネスでのQ401 VDSとNC接点間サージ、接点解放時間の実測（10ms以内）。コイル近傍の配置を優先検討し、基板設置の場合は配線長によるサージも評価する。
