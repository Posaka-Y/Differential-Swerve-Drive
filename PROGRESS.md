# Project progress

プロジェクト全体の進捗ログ。セッション終了時に新しいエントリを**上に**追記する。
ファームウェア固有の進捗は `firmware/PROGRESS.md` に書く。

記載フォーマット:

```text
## YYYY-MM-DD
### やったこと
### 現在の状態
### 次の作業
```

---

## 2026-07-22 (ユニット基板 全ブロック回路図入力完了)

### やったこと

- KiCad GUIでユニット基板の全機能ブロックを入力した: 5V入力・逆接保護・3.3V LDO、CAN、STM32G474最小構成、HSE/NRST/BOOT0、AMT22 SPI、デバッグGH6、UNIT_ID 3bit DIP、状態LED、5V監視ADC。
- UNIT_ID DIPをOmron `A6S-3104-H`、KiCad標準footprint `Button_Switch_SMD:SW_DIP_SPSTx03_Slide_Omron_A6S-310x_W8.9mm_P2.54mm`で配置した。
- 5V監視をLM66100後段の`PWR_5V`から33kΩ/22kΩで分圧し、10nFとBAT54Sクランプを介してPA0へ入れるブロックとして入力した。
- KiCad CLIで全階層BOMとERCを試行し、階層ラベル未設定を主因としてエラー57件・警告24件であることを確認した。

### 現在の状態

- 全ブロックの部品配置とブロック内回路入力は完了したが、親子間の階層ピン/階層ラベル設定とルートシート配線は未完了。このため現時点のERC違反は完成判定に使用しない。
- 次回照合事項: 2系統CANのインスタンス/信号名、未使用MCUピンのNo Connect、電源のPWR_FLAG、意図的NC、デバッグGH6の型番・向き、COMM/ERR LEDのValue、R14の正式型番表記、BAT54SLT1GのValue。
- `hardware/unit-board/untitled.kicad_sch`は複製候補のため、確認できるまで未追跡のまま残している。

### 次の作業

1. 各子シートへ階層ラベルを設定し、親シートの階層ピンと1:1で接続する。
2. 中央CAN/C620 CANの2インスタンス化とネット名を正本に合わせる。
3. 未使用ピン、PWR_FLAG、意図的NCを整理し、Value/Footprintを最終照合する。
4. `tools/kicad/check.ps1 -FailOnViolations`でERCを0件まで収束させ、PDF回路図をレビューする。
5. 階層化した全回路図の接続・ERC・PDFレビュー完了後、ユニット（差動ステアモジュール）基板のPCB作成へ移行する（基板外形、部品配置、配線、DRC、製造出力の順）。

## 2026-07-22 (ユニット基板 Block 1・2 回路図入力)

### やったこと

- KiCad GUIでBlock 1「Power Input 3.3V」を`hardware/unit-board/power_3v3.kicad_sch`へ入力し、親`unit-board.kicad_sch`から階層シートとして参照した。
- Block 1へJST GH 2pin入力、`LM66100DCKR`逆接・逆流保護、`TLV1117LV33DCYR` 3.3V LDO、入力/出力コンデンサを配置した。LM66100の`CE_N=VOUT`、TLV1117のtab=VOUT、2.2uF/10uFは0805、100nFは0603の方針で入力した。
- KiCad GUIでBlock 2「CAN Interface」を`hardware/unit-board/can_interface.kicad_sch`へ入力し、親回路図から階層シートとして参照した。
- Block 2へ`TCAN1051VDRQ1`、`ESD2CAN24DBZRQ1`、100nF x2、120Ω終端、`JS102011SAQN`終端スイッチ、JST GH 3pin x2を配置した。TCANのVCC=5V/VIO=3.3V/S=GND、スイッチpin 1=NC/pin 2=COM/pin 3=NOを確認した。

### 現在の状態

- Block 1・2の回路図ファイルは保存済みだが、AIによるS式接続照合とERCは未実施。親子間は階層ラベル/階層ピンで明示接続する必要がある。
- `hardware/unit-board/untitled.kicad_sch`が`power_3v3.kicad_sch`と同じサイズで未追跡のまま残っている。不要ファイルか確認するまで削除しない。
- `JS102011SAQN`専用footprintはメーカー推奨ランドとの最終照合が未完了。C620側コネクタの型番・個数・ピン順も未確定。

### 次の作業

1. Block 1・2のValue、Footprint、ピン接続、階層ラベル方向を正本と1:1照合する。
2. `untitled.kicad_sch`が不要な複製かKiCad GUIで確認し、必要なら正式名へ変更、不要なら削除する。
3. Block 3以降の回路図入力を進め、区切りごとにERCを実行する。

## 2026-07-20 (回路図分業方針の確認・AMT22コネクタGH化・旧XH/4線記述の掃除)

### やったこと

- KiCad作業の分業を再確認: AIは描かず「前(資料・ライブラリ・制約表)と後(S式照合・ERC/DRC・BOM)」、回路図手描き・配置・配線は人がGUIで行う。ピン割当の根拠(ST公式open_pin_data照合+NUCLEO実機動作実績)と、CAN/電源/MCU最小構成の部品選定書が揃っていることを確認。
- AMT22中継コネクタを旧`JST XH 6pin`から横挿しGH 6pin `SM06B-GHS-TB`+`GHR-06V-S`+`SSHL-002T-P0.2`へ確定・修正(`CARRIER_BOARD_REQUIREMENTS.md`)。AMT22と同ピン順でストレート結線、Pico-Lock⇔GH変換ハーネス自作。AMT22はVIH 2.0V/出力High 3.3Vのため全信号直結・レベルシフタ不要(2026-07-02確認済み)。
- DOC-01/DOC-03の旧記述を掃除して解消済みへ: `CARRIER_BOARD_BUILD_PLAN.md`の旧4線一体コネクタ→GH2電源+GH3 CAN x2、`CARRIER_BOARD_REQUIREMENTS.md`の「制御4線」表現を現行ハーネス構成へ、`hardware/README.md`の旧TCAN332記述→`TCAN1051VDRQ1`。
- ユニットID設定を**3bit DIPスイッチに確定**(UNIT-03/ODOM-06解消): PC6-8、内部プルアップ、ON=GND(読み値反転)、起動時に1回読取りRUN LEDをID回数点滅、全OFF(ID=0)は未設定エラー扱い。オドメトリ基板も同一ブロックでunitId=4(0b100)を設定。Flash保存一本化案は不採用。ARCHITECTURE_DECISIONSへ追記済み。DIP型番は部品選定で確定する。
- 回路図の下敷きはNUCLEO回路図ではなく自前の部品選定書3本+candleLightFD/ARK CANnode参考回路とする整理を確認(NUCLEOはST-LINK給電・HSE未実装で回路前提が異なる。実証済みなのはピン割当とファーム)。

- ユニット基板の回路図転記用リファレンス`docs/electrical/UNIT_BOARD_SCHEMATIC_REFERENCE.md`を新規作成: 階層シート6分割案、シート内配置とネットラベル方針、RefDes番号帯割当(シート別100番台)、全接続表(Net/部品/ピン名/ピン番号/電圧)、ブロック別部品一覧、ERCで検出できない誤り8項目(TLV1117タブ=VOUT、LM66100 CE_N=VOUT意図的、BAT54S向き、TCAN Sピン等)、未確定事項12件(C620 CANコネクタ型番が部品リスト未記載と判明、等)。索引9.97へ登録。

### 現在の状態

- docs/electricalの文書間不整合はDOC-01〜04すべて解消。ユニット基板の回路図は「転記リファレンス+ピン表+部品選定書3本」を開けば描ける状態。
- `SM06B-GHS-TB`は既採用のGHシリーズ(SM02B/SM03B)と同系列の6pin横挿し品。発注時に他コネクタと同様の現物確認を行うこと。

### 次の作業

1. KiCad 10 GUIでライブラリロード確認(前回持ち越し)→ G474共通ブロックから回路図手描き開始。
2. 描き終わった回路図をAIがS式でピン表・要件書と突き合わせ、ERC実行。

## 2026-07-20 (KiCad CLI検証環境)

### やったこと

- Windows版KiCad 10.0.4の`kicad-cli`で、`unit-board`のERC、回路図PDF出力、DRCが実行できることを確認。
- `tools/kicad/check.ps1`を追加。既定でユニット基板を検証し、対象プロジェクトと出力先を引数で変更可能にした。
- 厳格確認用に`-FailOnViolations`を用意し、ERC/DRC違反を終了コードへ反映できるようにした。
- `hardware/README.md`へ実行方法を追記した。
- `hardware/blocks/g474_minimum.kicad_sch`を作成し、KiCad 10標準`STM32G474RETx`シンボルへ正式Value `STM32G474RET6`とLQFP64 footprintを設定した。
- ユニット基板ルートへ`G474 Minimum`階層シートを組み込み、確定ピン割当に沿ったCAN、AMT22、SWD/UART、UNIT_ID、LED、予約I2C/SWOの階層I/Oを追加した。
- Rev.Aで使わない26本のGPIOにNo Connectを明示した。I/O名と親子階層ピンはKiCad CLIで解析・PDF出力できることを確認した。
- VDD x4とVBATを`PWR_3V3`へまとめ、VSS x4とVSSAを`GND`へ接続した。中間VDD枝のT字交点には明示ジャンクションを置き、未接続ワイヤ警告0件を確認した。
- `VDDA_A`、`VREF_PLUS`、`HSE_IN`、`HSE_OUT`、`BOOT0`をローカルネットとして分離した。親シートには`PWR_3V3`と`GND`階層ピンを追加した。
- HSE回路を追加: `ECS-80-8-33Q-JES-TR`、10pF x2、OSC_OUT側0Ω調整抵抗を`HSE_IN/HSE_XO/HSE_OUT`へ接続し、水晶ケースGND pin 2/4も接続。HSE部品単体のERC違反0件を確認した。
- VDD/VBAT/VDDA/VREF+用にFB1、R2、C3～C12を配置し、電源ネットへ接続した。FB1は`PWR_3V3`→`VDDA_A`、R2は`VDDA_A`→`VREF_PLUS`。
- NRST用C13、BOOT0用R3、デバッグGH6用J1を配置した（値・footprint・配線は未設定）。

### 現在の状態

- 保存済み`unit-board.kicad_sch`はG474共通階層シートを含み、HSE回路は接続済み。電源デカップリングとReset/BOOT/debugは作成途中。
- 終了時ERCはエラー38件・警告30件。未配線部品を含む作成途中の値で、完成判定ではない。
- C5がオフグリッド。C6～C8はグリッドへ移動済みだが、旧ラベル位置までのワイヤ端が残り、off-grid警告は計6件。KiCadロックファイルなし。
- `unit-board.kicad_pcb`も空のため、DRCはEdge.Cutsなしを1件報告する。
- KiCad GUIで`unit-board`が開かれており、`unit-board.kicad_pro`にはユーザー作業由来の未コミット変更があるため、本セッションでは上書きしていない。

### 次の作業

1. C5をグリッドへ移動し、C6～C8移動前位置へ残ったワイヤ/ラベルを整理する。
2. C3～C12、FB1、R2の未設定Value/footprintを正式型番へ揃える。
3. NRST 100nF、BOOT0 10kΩ pull-down、GH6デバッグ配線を完成させる。
4. 回路完成後に未使用ピンと階層I/Oを再確認し、`check.ps1 -FailOnViolations`でERCを0件にする。

## 2026-07-19 (SamacSysライブラリ取り込みへ方針変更)

### やったこと

- ユーザー要望により、標準ライブラリ流用(前エントリ)からSamacSysダウンロード品の取り込みへ変更。
- Library Loader v2.50が導入済み・アカウント設定済み(ECAD=KiCad、監視=Downloads、自動起動OFF)であることを確認。Chrome自動操作ではCSEのダウンロードがトラッキングリダイレクトで失敗し、ユーザーが別ブラウザで`LIB_TCAN1051VDRQ1/ESD2CAN24DBZRQ1/LM66100DCKR/JS102011SAQN.zip`を手動取得。
- 4部品の`KiCad/*.kicad_sym`を`hardware/lib/DifferentialSwerve.kicad_sym`へ統合。SamacSys原品の誤りを修正:
  - TCAN1051VDRQ1のpin 5が`NC`になっていた(V系列はVIO)→ `VIO`/power_inへ修正
  - 全pinが`passive`だった → データシート通りのelectrical typeへ設定
  - JS102011SAQNのpin 1(切替接点)が`no_connect`型だった → passiveへ修正
  - Footprint欄が裸のIPC名で解決不能 → 照合済みKiCad標準footprintへ変更
- JS102011SAQNのfootprint(SamacSys、2.5mmピッチ3pad+NPTH x2)を`DifferentialSwerve.pretty`へ取り込み(メーカー図面照合は未実施)。
- `LIBRARY_MANIFEST.md`を全面更新(取り込み記録・修正内容・未照合事項)。S式バランス検証済み。

### 現在の状態

- 専用ライブラリはシンボル4個(SamacSys由来+修正)、footprint 2個(Harwin照合済み、JS102011未照合)。
- pin番号・名称はデータシート照合済みの内容と一致。KiCad 10 GUIでのロード確認は未実施。
- 余談: Library Loaderの設定XML(`%APPDATA%\SamacSys\Library Loader\LibraryLoader.xml`)にCSEパスワードが平文保存されている。使い回しなら変更推奨。

### 次の作業

1. KiCad 10 GUIでライブラリをロードし、4シンボル表示とsymbol checkerを確認、保存し直してフォーマット正規化。
2. JS102011SAQNのfootprintをLittelfuse/C&K図面と照合して確定する。
3. G474共通回路図の作成へ着手する。

## 2026-07-19 (自作シンボルを標準ライブラリへ置き換え)

### やったこと

- `hardware/lib/DifferentialSwerve.kicad_sym`の自作シンボル3個を削除し、KiCad 10同梱の標準ライブラリシンボルへ代替。
  - `TCAN1051VDRQ1` → `Interface_CAN_LIN:TJA1051T-3`(8pin全て一致を照合済み。Value書き換えで使用)
  - `ESD2CAN24DBZRQ1` → `Diode:SM712_SOT23`(1/2=ライン、3=GNDでpin番号一致。Value書き換えで使用)
  - `LM66100DCKR` → `Power_Management:LM66100DCK`(同一部品の公式シンボル。定義も自作版と同一)
- 3シンボルとも既定footprintが要件(SOIC-8 3.9x4.9/SOT-23/SC-70-6)と一致することを確認。footprint再割当不要。
- `LIBRARY_MANIFEST.md`を更新(収録表・標準部品表・置き換え照合記録)。`unit-board.kicad_sch`は空でdocs側にも他参照なしのため影響なし。

### 現在の状態

- 専用シンボルライブラリは空(将来の特殊部品用の器として維持)。専用footprintは`Harwin_S1751-46R`のみ。
- LM66100は完全一致だが、TJA1051T-3/SM712_SOT23は別型番名のシンボル流用のため、回路図配置時にValueを正式型番へ書き換える運用。

### 次の作業

1. KiCad 10 GUIで標準3シンボル+`DifferentialSwerve.pretty`のロードを確認する。
2. `JS102011SAQN`推奨land patternのGUI照合とfootprint追加(継続)。
3. G474共通回路図の作成へ着手する。

## 2026-07-19 (KiCad/Codex連携調査)

### やったこと

- KiCad内蔵のCodex公式チャットパネルは現時点でなく、第三者製`KiCad AI Assistant`はOpenAI APIキーと別課金が必要であることを確認。
- Windows版KiCad 10に`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`が同梱済みであることを確認。
- 現在のWSLセッションからWindows EXEを起動するとWSL interopのvsockエラーになることを確認。

### 現在の状態

- KiCad CLIの追加インストールは不要。Windows側からERC/DRC/製造出力へ利用できる見込み。
- WSL上のCodexからの直接実行は未成立。次回はWindows版Codexから`kicad-cli.exe`を呼び出して確認する。

### 次の作業

1. Windows版Codexでリポジトリを開き、`kicad-cli.exe version`を実行する。
2. KiCadライブラリをGUIでロードして初版部品を確認する。
3. 回路図作成後、ERC/DRCをまとめて実行するPowerShellスクリプトを整備する。

## 2026-07-19 (部品ライブラリ初版レビュー)

### やったこと

- `hardware/lib/`初版を公式データシートと1:1照合レビュー。TI 3部品とHarwin図面のPDFを取得し`hardware/reference/datasheets/`へ保存(ti-tcan1051.pdf、ti-esd2can24-q1.pdf、ti-lm66100.pdf、harwin-s1751r-drg-02202.pdf)。
- ピン照合結果: `TCAN1051VDRQ1`(SLLSET0D)、`ESD2CAN24DBZRQ1`(SLVSFW5D)、`LM66100DCKR`(SLVSEZ8A)の3シンボルともピン番号・名称・electrical typeが完全一致。標準footprint割当(SOIC-8 3.9x4.9/SOT-23/SC70-6)も各パッケージ図と一致。`S1751-46R`のpad 3.45x1.85mmはHarwin DRG-02202の推奨pad layoutと一致。全ファイルのS式構文バランスOK。
- 修正1: `sym-lib-table`/`fp-lib-table`のURIを`${KIPRJMOD}/`直下→`${KIPRJMOD}/../lib/`へ変更。テーブルは各基板プロジェクトディレクトリへコピーして使うテンプレートである旨をマニフェストへ追記。
- 修正2: `Harwin_S1751-46R.kicad_mod`のsilk線をy=±1.0→±1.15へ移動(pad縁との隙間が0.015mmしかなく、solder mask expansionでsilk clip警告/pad上印刷になるため)。
- マニフェストへ照合記録(2026-07-19)を追加。
- レビュー指摘を受け、LM66100の`CE_N`接続をGNDからVOUTへ変更。TIデータシート8.3節のRPP+RCB構成として逆極性保護と逆流遮断を両立する方針を電源選定書、ユニット要件、確定事項へ反映。

### 現在の状態

- シンボル・footprintの寸法/ピンはデータシート照合済み。KiCad 10 GUIでのロード確認とchecker実行は未実施(kicad-cliなし)。ファイルはKiCad 8世代フォーマットのため、GUIで開いて保存し直すと現行フォーマットへ正規化される。
- LM66100の`CE_N`接続はVOUTへ確定し、レビューで見つかった文書不整合は解消済み。
- 軽微(許容範囲として未修正): footprintのcourtyard余白がpad縁から0.1mm(KiCad慣例0.25mm)。

### 次の作業

1. KiCad 10 GUIで`hardware/lib`をロードし、3シンボル表示・footprint link・checkerを確認、保存し直してフォーマット正規化。
2. `JS102011SAQN`推奨land patternのGUI照合とfootprint追加。
3. ライブラリGUI確認後、G474共通回路図へ着手。

## 2026-07-19 (KiCad必要部品ライブラリ初版)

### やったこと

- 回路図作成前に、回路ではなく必要部品ライブラリだけを整備する方針へ変更。
- `hardware/lib/DifferentialSwerve.kicad_sym`へ`TCAN1051VDRQ1`、`ESD2CAN24DBZRQ1`、`LM66100DCKR`の正式pinout付きシンボルを追加。
- Harwin `S1751-46R`のメーカー推奨pad 3.45x1.85mmに基づくリフロー用footprintを追加。
- `hardware/lib/LIBRARY_MANIFEST.md`へ、専用ライブラリとKiCad標準ライブラリの使い分け、STM32/TLV1117/BAT54S/JST GH/水晶の割当を記録。
- 特殊footprintを寸法推測で作らないため、`JS102011SAQN`はメーカー図面とのKiCad上照合まで保留。

### 現在の状態

- 最初のG474/CAN/電源回路に必要な専用シンボル3個とテストポイントfootprintを作成済み。
- この環境には`kicad-cli`がないため、KiCad 10 GUIでのライブラリロード、symbol checker、footprint checkerは未実施。

### 次の作業

1. KiCad 10 GUIで`hardware/lib`を読み込み、3シンボルの表示・pin type・footprint linkを確認する。
2. `JS102011SAQN`の公式推奨land patternをGUI寸法で照合してfootprintを追加する。
3. 必要になった時点でJST GH公式footprintとの差分、TCAN/ESD/LM66100の1:1 pinoutレビューを行う。

## 2026-07-19 (G474 Reset・BOOT・ADC監視・表示部品選定)

### やったこと

- NRSTを内部weak pull-up+100nF、BOOT0を10kΩ pull-down+BOOT/3V3隣接SMTテストポイントに確定。常設Resetボタンと2.54mm BOOTジャンパは不採用。
- 5V監視を33kΩ/22kΩ(0.4倍)、10nF、`BAT54SLT1G`上下クランプでPA0へ入れる構成に確定。
- G474基板表示をPWR/RUN/COMM/ERRの4個とし、Lite-On C190シリーズ緑/緑/黄/赤と1kΩを選定。
- 主要テストポイントをリフロー対応`S1751-46R`、補助信号を1.0～1.5mm露出銅padに確定。
- `STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md`へ回路、定数、配置条件、実機確認を追記。

### 現在の状態

- G474最小構成の主要部品選定は完了。共通回路図をKiCadへ起こせる状態。
- 中央基板固有のLED、テストポイント数、5A主入力保護は別途選定が必要。

### 次の作業

1. KiCadのG474共通階層シートを作成し、電源/HSE/Reset/BOOT/SWD/ADC監視をERCする。
2. CAN共通階層シートと5V入力/LDO階層シートを作成して共通ブロックを接続する。
3. PDF出力でピン番号、極性、ネット名、部品型番を人とレビューする。

## 2026-07-19 (STM32G474 HSE・アナログ電源部品選定)

### やったこと

- `docs/electrical/STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md`を追加。
- HSEを`ECS-80-8-33Q-JES-TR` 8MHz、負荷容量をC0G 10pF x2の初期値に確定。CL式とworst-case gmcrit約1.14mA/Vを記録。
- VDDAフェライトを`BLM18AG601SN1D`、各VDD 100nF、全体4.7uF、VDDA 100nF+1uF、VREF+ 10nF+1uFの正式部品まで選定。
- 水晶、デカップリング、VDDA/VREF+の配置配線制約と、温度・HSE起動・ADCノイズの実機確認項目を明文化。

### 現在の状態

- G474共通ブロックはCAN、5V入力保護、3.3V LDO、HSE、VDDA/VREF+、デバッグGH6まで主要部品が確定。
- HSE負荷容量は回路図初期値10pFで、PCB完成後に8.2/10/12pFから最終調整する。

### 次の作業

1. G474のNRST、BOOT0、状態LED、5V監視ADC、テストポイント部品を確定し、最小構成回路を閉じる。
2. 共通階層シートの回路図をKiCadへ作成し、ERC/PDFレビューする。
3. 試作基板でHSE起動余裕、周波数偏差、VDDAノイズを測定する。

## 2026-07-19 (5V共通電源ブロック部品選定)

### やったこと

- `docs/electrical/POWER_5V_COMMON_BLOCK_PART_SELECTION.md`を追加し、G474基板の入力保護、3.3V LDO、中央基板のG474枝PPTC、GH2、枝LEDを正式選定。
- G474基板の逆接・逆流保護を`LM66100DCKR`、LDOを`TLV1117LV33DCYR`、中央のユニットx3+オドメトリ枝を`1206L050/15YR`に確定。
- 5V横挿しコネクタを`SM02B-GHS-TB`、表示LEDを`LTST-C190KGKT`+1.5kΩに確定。
- `TCAN1051V`のVCCが5Vであることを反映し、旧3.3V負荷見積りを修正。LDO損失とPPTC温度derating、配置配線・実機確認条件を明文化。
- 1.5AのLM66100を中央5A主入力へ使わないこと、0.5A PPTCをTeensy枝へ自動流用しないことを明記。

### 現在の状態

- CAN共通ブロックとG474用5V/3.3V共通電源ブロックは正式型番まで確定。
- 中央5V主入力の逆接/逆流保護、Teensy枝の保護定格、XT30基板側正式型番は未確定。

### 次の作業

1. STM32G474の8MHz HSE水晶、負荷容量、VDDAフェライトビーズ、デカップリングを正式選定する。
2. 各G474基板の5V/3.3V電流を試作機で測り、PPTCとLDOの熱余裕を確認する。
3. 中央5V主入力とTeensy枝の保護部品を、実測電流と突入条件から選定する。

## 2026-07-19 (3基板回路設計の未確定事項・作業順整理)

### やったこと

- 中央Teensy基板、差動ステアユニット基板、オドメトリ基板の未確定事項をP0/P1/P2で分類した`docs/electrical/SCHEMATIC_DESIGN_OPEN_ITEMS.md`を追加。
- 旧XH/電源CAN一体4線と現行GH/電源CAN分離、SWDコネクタ、CAN FD方針など、回路図着手前に解消すべき文書不整合を抽出。
- 共通ブロック→ユニット固有→オドメトリ固有→中央固有の回路図作成順を整理。
- AIは公式資料調査、回路ブロック、ERC、配置配線制約表を担当し、人がKiCad GUIで最終配置配線して段階レビューする役割分担を確定。
- G474各基板のデバッグ方式をWeActStudio MiniDebugger直結へ変更。V1.0回路図からJ2が1.0mm 10極SH系、配列が1=5V、2=GND、3=UART_RX、4=UART_TX、5=NRST、6=SWO、7=GND、8=SWCLK、9=SWDIO、10=デバッガ出力3.3Vと確認。ターゲットケーブルは5〜9番だけ実装し、電源逆流を防ぐ方針を確定。
- JST公式資料からSH 10極の正式部品を`SHR-10V-S-B`、`SSH-003T-P0.2-H`と確認。基板側はサービスしやすい横挿し`SM10B-SRSS-TB`を第一候補、上挿し`BM10B-SRSS-TB`を代替とした。
- ロボット側コネクタ系列統一を優先し、G474各基板のデバッグ端子をGH 6pinへ変更。配列を`GND/SWCLK/SWDIO/NRST/DBG_TX/DBG_RX`とし、WeAct側SH 10pinからの専用変換ケーブルを作る。SWOは基板テストパッドへ残し、デバッガ電源出力は接続しない。
- G474デバッグ用GH 6pinの基板ヘッダは、抜き差しと目視性を優先して上挿し`BM06B-GHS-TBT`に確定。コネクタの1番を向ける方向は基板配置時に決める。
- GHヘッダのラッチ側は基板内側へ向ける方針に確定。CANは各区間30cm未満、総延長1m未満を設計条件とし、電源GNDが共通でも非絶縁CANの基準電位を安定させるためGH 3pinのGND線を残す。
- CAN終端120Ωの切替は小型スライドスイッチ方式に確定。正式スイッチ型番は部品選定で決め、シルクに`TERM ON/OFF`を表示する。
- コネクタ嵌合方向は用途別に分離。各モジュールの常設5V電源GH 2pinとCAN GH 3pinは基板端の横挿し、作業時に使用するデバッグGH 6pinは上挿しとする。
- Rev.Aは中央CAN 3系統と各G474-C620専用CANをすべてClassic CAN 1Mbpsで統一し、CAN FDは対象外とした。G474のFDCANはClassicモードで使用し、トランシーバは1Mbps SOIC-8の`TCAN332DR`を正候補とする。
- 部品選定は入手性、少量価格、複数の公開プロジェクト/評価基板での採用実績、信頼性、ステンシルリフロー性、修理性を比較表で評価する方針に確定。Rev.Aは0603以上とリード付きICを優先し、BGA/WLCSP/0201以下は原則避ける。
- CAN共通ブロックの正式部品選定を実施し、`docs/electrical/CAN_COMMON_BLOCK_PART_SELECTION.md`を追加。トランシーバは旧`TCAN332DR`から、5V VCC/3.3V VIO、AEC-Q100、バスフォルト±58V、SOIC-8の`TCAN1051VDRQ1`へ変更し、公開設計で採用実績の多い`TJA1051T/3`を代替候補とした。
- CAN保護を旧PESD1CAN系からActive品`ESD2CAN24DBZRQ1`へ変更。終端は`RC0603FR-07120RL` 120Ωとリフロー対応スライドスイッチ`JS102011SAQN`、CANコネクタは横挿し`SM03B-GHS-TB`+`GHR-03V-S`+`SSHL-002T-P0.2`に正式化した。

### 現在の状態

- KiCad 10の空ディレクトリ構成は用意済みだが、回路図ファイルは未作成。
- 最初にDOC-01〜04の文書不整合、正式コネクタ、G474/Teensyピンマップ、Rev.A範囲を確定する段階。

### 次の作業

1. GH 2pin/3pinの正式型番と、WeAct MiniDebugger 10極ポートのコネクタシリーズ・ピッチ・基板側正式型番を現物確認する。
2. 旧4線一体/XH記述を正本から除去し、共通CANブロック仕様を更新する。
3. Teensy 4.1全ピンマップと初版CAN FD採否を確定する。
4. 水晶、LDO、入力保護、CANトランシーバ、TVSの公式資料調査へ進む。

## 2026-07-19 (E-stop 2個・コンタクタ励磁・状態表示LED要件整理)

### やったこと

- 非常停止ボタンを2個とし、NC安全接点をコンタクタコイルループへ直列接続する方針を確定。
- 各E-stopの24V内蔵LEDをTeensy非依存の`24V_CTRL`ハードワイヤ回路で点灯する要件を追加。
- Teensy中央基板へコンタクタコイル用MOSFETドライバを組み込み、E-stopハード遮断を主、Teensyを励磁許可とする構成を整理。
- Teensyからもコンタクタを解放できる遠隔停止、停止ラッチ、明示的再アーム、主接点開放診断の要件を追加。
- ミッション達成、状態、バッテリー残量用のテープLED/表示LEDを、安全表示灯とは独立して追加する要件を整理。
- mini PCをGMKtec NucBox G2に確定し、常時通電12V系から給電する方針を追加。流通仕様12V/3Aに対して既存候補`SD-50B-12`(12V/4.2A)を採用候補として維持。
- 所有リレーをKILIGEN `E228`(24V DC、100A表記)と特定。販売情報では連続50〜60A目安かつ24V DC負荷遮断定格の正式資料がないため、メインコンタクタには採用しない方針とした。

### 現在の状態

- E-stop個数、安全接点の接続、コンタクタ励磁回路の配置、演出LEDと安全表示の分離は確定。
- E-stop内蔵LEDの点灯条件、代替メインコンタクタの正式型番/コイル/接点仕様、テープLED方式と電源容量は未確定。

### 次の作業

1. 24V DC負荷遮断定格がメーカー資料に明記された代替メインコンタクタを選定する。
2. E-stop LEDを常時点灯、押下時点灯、モータ電源遮断時点灯のどれにするか確定する。
3. E-stopボタンが安全用NCとは別にNO補助接点を持つか確認する。
4. テープLEDの電圧、方式、長さ、LED密度から最大電流を計算し、専用DC-DC要否を決める。
5. コンタクタ仕様に合わせてMOSFET、クランプ、コネクタ、配線太さを確定する。
6. NucBox G2現物のACアダプタ銘板と給電専用USB-C仕様を確認し、高負荷時消費電流を実測する。

## 2026-07-17 (KiCad向け3基板構成・中央配線方針整理)

### やったこと

- PCBをユニット基板、オドメトリ/IMU状態推定基板、Teensy 4.1中央汎用基板の3種類に分け、G474最小構成・CAN・電源・STDC14等をKiCad共通ブロックとして流用する方針を整理。
- 従来の電源+CAN一体4線案を見直し、5V/GNDは中央基板からスター分配、CANはCOMM_A/B/GNDをデイジーチェーン接続する方針へ変更。
- Teensy CAN1=駆動ユニットx3、CAN3=オドメトリ/IMU等センサー、CAN2=汎用拡張/予備としてバスを分離。
- オドメトリ基板をAMT102 x3(Zなし、GH 4pinのVCC/GND/A/B)にSPI IMUを加えた状態推定ノードへ発展させる方針を追加。
- 購入済み24V→5V/5A DC-DCを中央基板へ入力し、各ノードへ個別保護付きで分配する構成を整理。
- バッテリー電圧・電流監視を中央TeensyのI2Cへ接続する方針を追加。
- 基板シルクのQRコードから基板Rev別ドキュメントを開く案を設計要望として整理。

### 現在の状態

- 3基板の役割、MCU、通信バス、電源の大枠が決まり、KiCad回路図へ入る前の主要な構成判断は概ね収束。
- G474は`STM32G474RET6`を10個確保済み。信号・小電流コネクタはJST GH、デバッグはSTDC14を採用する。
- QRコードのリンク先、サイズ、生成方法はPCBレイアウト時に決める。

### 次の作業

1. バッテリー電圧・電流監視IC、シャント定格、I2C絶縁要否を確定する。
2. SPI IMUの候補をデータシート、在庫、価格、リフロー性で比較して型番を確定する。
3. AMT102 A/B 6chのレベル変換/シュミット入力回路を確定する。
4. 所有済みリレーの型番・入力/コイル・接点仕様を確認して中央安全I/Oを確定する。
5. GH各コネクタの正確な型番、許容電流、ケーブル線径と5V電圧降下を確定する。
6. G474共通ブロックと中央基板の電源/CAN分配回路からKiCad設計を開始する。

## 2026-07-17 (G474実装MCUの型番・必要数確定)

### やったこと

- ユニット基板x3とオドメトリ基板x1の実装MCUを`STM32G474RET6`(LQFP64、Flash 512KB)で確定。
- `STM32G474RET6`を10個購入し、実装必要数4個に加えて試作・交換用予備を確保。
- H753への変更検討を終了し、NUCLEO-G474REと同じパッケージ・ピン割当・現行ファーム資産を維持する方針を確定。

### 現在の状態

- G474の型番・Flash容量・調達不足はKiCad設計開始時の未確定事項ではなくなった。
- ユニット基板とオドメトリ基板でG474最小構成、電源、STDC14、中央CANを共通化できる。

### 次の作業

1. JST GHコネクタとSTDC14デバッグヘッダを共通要件へ反映する。
2. G474共通回路ブロックとユニット基板のKiCad回路図作成を開始する。
3. AMT102 A/B 6ch入力回路と既存リレーに合わせた中央基板I/Oを確定する。

## 2026-07-09 (負荷適応制御ロードマップ保存)

### やったこと

- 接地・負荷増加後の制御発展順序を、現行mode PIを土台にした `FF強化 → 摩擦補償 → mode-space DOB → 状態推定 → 必要時MPC` として確定。
- `docs/control/LOAD_ADAPTIVE_CONTROL_ROADMAP.md` を追加し、負荷下での崩れ方、段階導入、`unit_controller_update()` へのFF/DOB挿入点、ログ先行の実装順序を整理。
- `docs/ARCHITECTURE_DECISIONS.md` と `docs/PROJECT_DOCUMENT_INDEX.md` に参照を追加。

### 現在の状態

- 将来の本命構成は `P_theta + PI_d + PI_s + FF + DOB_d + DOB_s`。
- G474は1kHz局所ロバスト制御、Teensy/mini PCは3輪協調・制約処理・必要時の最適化という責務分担で進める。

### 次の作業

1. 接地評価前に `unit_control_output_t` へFF/DOB/外乱推定ログ項目を追加するか検討する。
2. `targetWheelAccelRpmMilliPerS` をdrive accel FFへ接続する実装案を作る。
3. 接地・負荷ありで、摩擦・飽和・drive/steer干渉を分けてログ評価する。

---


## 2026-07-08 (オドメトリセンサをAMT102へ戻し)

### やったこと

- オドメトリセンサ方針をI2Cホール磁気エンコーダ(MT6701/AS5600)からAMT102 x3へ戻した。
- Z相は使わず、各センサ4線(VCC/GND/A/B)のみでTIM2/TIM3/TIM4 Encoder Modeに入力する方針へ更新。
- `docs/electrical/ODOMETRY_BOARD_REQUIREMENTS.md`、`docs/ARCHITECTURE_DECISIONS.md`、AGENTS/INDEX/README/ベンチ計画の記述を更新。

### 現在の状態

- オドメトリ基板はG474 + AMT102 A/B相 x3が正本。
- 磁気エンコーダ案は、シャフトへの磁石・センサ位置合わせの機械接続が難しいため廃止扱い。

### 次の作業

1. AMT102の最新データシートで電源範囲、出力形式、ピン/線色、DIP分解能設定を最終確認して部品表・コネクタ表へ反映する。
2. A/B 6ch分の5V→3.3V入力方式(レベル変換/保護/シュミット化)を決める。
3. NUCLEOでTIM2/TIM3/TIM4 Encoder Modeの最小ファームを作り、1輪手回しでカウント方向と1回転countを確認する。

## 2026-07-08 (Linux mini PC評価環境確立、低速stick-slip対策完了)

### やったこと

- Linux mini PC側の評価環境を確立: can-utils/python3-serial、slcandでcan0(CANableは
  `/dev/ttyACM1`、`/dev/ttyACM0`はST-Link V3 VCP)、`st-flash`でのflashも初成功。
- `tools/linux/unit_bench.py`(socketcan直、run/set-param/disable/profile)を追加。
- ファームへCAN `SET_CONFIG`(0x140+unitId、17パラメータ、安全クランプ付き)を実装し、
  reflash不要のランタイム調整を可能にした。
- 動摩擦電流を実測同定(~200 raw、速度非依存・正逆対称)。低速stick-slipの原因を
  「ブレークアウェイ~850 vs 維持~200の差」と定量確定し、積分フロア(200)+driveKp10+
  動作開始時積分クランプ(400)で40rpm p-p 213→16、25rpm固着46%→0%を達成。
  確定値は`main.c`既定値へ焼き込み済み。コミット`781b516`。

### 現在の状態

- 無負荷単体ユニット(NUCLEO)で、mini PCからCAN経由で25〜1360rpm+ステアの
  安定制御が成立。残るばらつきは機構の角度依存の引っかかり由来。

### 次の作業

1. 連続軌道評価(`unit_bench.py profile`、速度ゼロクロス反転を含む)。
2. 接地・負荷での摩擦再同定とフロア/クランプ見直し。
3. 中央Teensy 4.1のbring-up。

## 2026-07-07 (mini PC Linux評価引き継ぎ)

### やったこと

- Linux mini PC上の別Codexセッションへ渡すため、`docs/testing/MINIPC_LINUX_HANDOFF.md`を追加。
- CANable/socketcan前提の初期セットアップ、CAN ID/payload、smoke手順、Linux側Codexへの依頼文を整理。

### 現在の状態

- `main`と`origin/main`は同一コミットだが、ローカルには未コミット変更が残っている。
- このCodexセッションでは`.git/index.lock`を作れず、commit/pushは不可。

### 次の作業

1. ローカル端末側で未コミット変更をcommit/pushする。
2. Linux mini PC側で`docs/testing/MINIPC_LINUX_HANDOFF.md`をCodexに読ませ、周期送信+CSV再生スクリプトを作る。
3. 実機評価前に`UNIT_CTRL disable`を即送れる端末を用意する。

## 2026-07-07 (未コミット成果のリモート同期)

### やったこと

- CANable bring-up以降の未コミット成果を確認し、ファーム・ドキュメント・チューニングログ・補助スクリプトをGit管理へ同期する準備を実施。
- `firmware/scripts/build.ps1`でDebugビルド成功を確認。
- Codex実行権限では`.git/index.lock`を作れず、さらにGitHubへの443接続もブロックされたため、コミット・pushは未完了。

### 現在の状態

- `main`には未コミット変更が残っている。ローカル端末側で`git add -A`、commit、pushが必要。

### 次の作業

1. ローカル端末側で未コミット変更をコミットし、`origin/main`へpushする。
2. push後、必要なら実機consoleを終了してtimeout修正版をflashする。
3. console再確認でVCPログの`STOP:`行を確認する。

---


## 2026-07-07 (CANable中央CAN指令bring-up)

### やったこと

- NUCLEO-G474REの中央CAN(FDCAN1 PA11/PA12)をCANable(COM16)から制御する経路を実機確認。
- ファームを、起動時disabled、`SET_TARGET(0x101)` + `UNIT_CTRL(0x121)` enableでのみ駆動する構成へ変更。
- CANable送信用スクリプトを追加し、hardware-session経由でflash→短時間smoke→disableを実行できるようにした。
- `θs=179.912°`, `ωw=500rpm`を20Hz送信し、enable後に実駆動、disableで停止することを確認。
- 続けて、CANableから手入力で`θs`/`ωw`を調整するconsole sessionスクリプトを追加。

### 現在の状態

- 最新CAN制御ファームがflash/verify/reset済み。
- 実機は起動時disabledで、最後にCANableから`UNIT_CTRL disable`をBody/SafeIdle両方で送信済み。
- 無負荷ではPC(CANable)から`θs`/`ωw`司令で動作できる段階に到達。
- 手入力確認は `firmware/scripts/run-canable-target-console-session.ps1` から実行可能。
- 手入力consoleで周期的に落ちるような挙動を確認。timeout 200msが主候補のため、
  ワークツリー上では1000ms化+timeout停止ラッチを実装・ビルド済みだが、console sessionが
  mutexを保持していたため未flash。console側は±1200rpm上限を追加済み。

### 次の作業

1. 手元consoleで`q`を押してmutexを解放し、timeout修正版をflash。
2. console sessionで手入力操作を再確認し、VCPログの`STOP:`行で落ち原因を確定する。
3. PC側送信ツールを任意軌道/CSV再生へ拡張し、指令生成とログ保存を分離する。
4. その後、中央Teensy相当の周期送信・timeout・disable手順へ移植する。

---


## 2026-07-06 (7)

### やったこと

- 未コミットだった設計資料、ファームウェア、CAD、開発設定を整理してGit管理へ追加。
- `hardware/reference/ARK_CANNODE` と `hardware/reference/candleLightFD` を、壊れた埋め込み
  リポジトリ参照ではなく正式なGit submoduleとして登録。
- firmware Debugビルド成功を確認し、`main`を`origin/main`へ同期。

### 現在の状態

- 2026-07-06までのプロジェクト成果がリモートリポジトリへ反映済み。

### 次の作業

1. 駆動モードの発散ガード見直しと再チューニング。
2. CAN-G474の実機bring-upと、CAN 2系統の同時1Mbps試験。

---


## 2026-07-06 (6)

### やったこと

- ユーザーがステア軸の手回し点検(引っかかり・ガタ・異音・AMT連れ回りズレ)実施、異常なしを確認。
  Ki=200発振→-114°逆走以降中断していた通電試験を再開。
- gain-tuningスキルでゲイン調整3イテレーション実施(詳細は`firmware/PROGRESS.md`):
  積分クランプ(mode_integral_limit=1200)込みの再現確認に成功 → steer_mode_ki=125で
  収束~3.0秒・終端誤差0.02°まで改善 → 150は125より悪化のため125を確定値に採用。
- gain-tuningスキルのシリアル監視時間を45秒→15秒へ短縮(ユーザー要望、収束が~3秒のため十分)。

### 現在の状態

- ファームは`steer_mode_ki=125`・`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・
  verify・reset済み。操舵(steer)のゲインは実用水準に到達。

### 次の作業

1. angle_kp/steer_accelの追加チューニング、または駆動モード(wheel≠0)の実走テストへ。
2. `drive_mode_ki`は操舵専用試験では未検証のため、駆動実走時に個別調整すること。

---


## 2026-07-06 (5)

### やったこと

- **車体協調制御をゴールとして明文化し、現状とのギャップを仕様レベルで解消**:
  `docs/control/CENTRAL_COORDINATED_CONTROL.md` を新規作成(レイヤー責務=mini PC計画/
  Teensy 100Hzプロファイラ+車体IK+デサチュレーション/ユニット1kHz FF付き追従、
  車体IKとステア角速度FFの式、特異点処理、反転ポリシー、段階導入0〜4)。
- ギャップ4点を確定・文書化:
  1. SET_TARGETにFFがない → `SET_TARGET_FF`(0x110+id、ステア角速度+ホイール加速度、
     FF欠落時=0で後方互換)をCAN仕様へ追加
  2. 飽和処理がユニット単位 → 中央デサチュレーション(3輪最悪値でツイストスケール)を正、
     DYNAMIC_CONTROL_PLANのユニット内配分は保護動作へ位置づけ変更
  3. 反転判断者が未定義 → 中央のみが判断、ユニットへは連続unwrap角(int32 mdeg)と規約化
  4. ユニット内ランプ(steer_accel等)→ 協調制御後は安全ガードへ格下げ(通常は当たらない値に)
- ARCHITECTURE_DECISIONSへ2行追記(協調制御の責務分担、SET_TARGET_FF)。INDEXに5.7追加。

### 現在の状態

- 協調制御の中央⇔ユニット契約が仕様として確定。ファーム実装は未着手(段階0=現行ベンチは
  この変更の影響なし)。ベンチ状況は(3)(4)のエントリから変化なし(手回し点検待ち)。

### 次の作業

1. (変わらず)手回し点検 → 再現確認 → ゲイン詰め → 駆動実走。
2. ベンチのついでに**モード非干渉の実証**(純操舵 n1=n2 でホイールが転がらないこと)を検証項目に追加。
   残留カップリングがあればユニットIKへ補正項が必要(CENTRAL_COORDINATED_CONTROL.md 検証項目1)。
3. モジュール取付位置 r_i・車輪半径 R の正本値をCADから転記(未文書化)。

---


## 2026-07-06 (4)

### やったこと

- **オドメトリセンサを確定変更**: AMT102 x3(約¥9,000)→ I2Cホール磁気エンコーダ x3
  (MT6701第一候補、AS5600代替、約¥1,000〜1,500)。I2Cバス3本分離
  (I2C1=PA15/PB7、I2C2=PA9/PA8、I2C3=PC8/PC9、AF成立確認済み)、プルアップ2.2kΩ、
  バスリカバリ必須、磁石マウントはCAD側。オドメトリ基板ではIDをPB13-15へ移動
  (PC8衝突のため)。`ODOMETRY_BOARD_REQUIREMENTS.md`を全面改訂し、AMT102案は
  差し戻し先として文末に記録。ARCHITECTURE_DECISIONS / AGENTS.md / INDEX / hardware
  READMEも更新。
- **基板の自作vs購入の再検討**: Matek CAN-G474(約¥3,000)×3+オドメトリで約¥11,000と、
  自作(¥18,000〜25,000+設計工数)より安い。CAN-G474ベンチ試験(既定路線)を
  本番採用可否の判定に兼ねる方針。判定材料: CAN2トランシーバ/終端/TVSの実物確認、
  AMT22のSPIパッド直はんだの信頼性(最大の懸念)、オドメトリのホスト選定。
  ユニットIDはMCU Flash保存で代替可(ゼロ点保存と同じ領域)。**決定はベンチ後**。

### 現在の状態

- ユニット基板方式(自作で確定)の決定は、CAN-G474ベンチ結果次第で購入方式へ
  変更の可能性あり。回路図の下準備((2)のエントリ)は自作続行時にそのまま使う。

### 次の作業

1. CAN-G474到着後のベンチで本番採用可否も判定(上記判定材料)。
2. MT6701/AS5600モジュールと磁石の調達、測定輪への磁石ホルダー設計。

---


## 2026-07-06 (3)

### やったこと

- 制御ループをRoboMaster系オープン実装と比較し3点導入(積分独立クランプ
  `mode_integral_limit`=1200、合成電流飽和時のモード比例スケーリング+積分凍結、
  駆動目標ランプ`wheel_accel_rpm_per_s`)。ビルド確認済み・実機未検証。
  詳細: `firmware/PROGRESS.md`、`firmware/docs/CONTROL_LOOP_TUNING.md`。
- 接地移行の議論: 角度ループは流用可、電流系3点(limit/integral_limit/min_rpm)は
  接地実測から引き直し、という整理を確定。
- **将来計画を新規文書化**: `docs/control/CALIBRATION_AND_ADAPTATION_PLAN.md`。
  CALフェーズにブレークアウェイ・時定数の自己同定を追加して電流系パラメータを自動導出
  (重量・床変更へCAL再実行で追従)、走行中変動には将来LESO/LADRC、HARD_MAXは
  自動化しない、駆動同定はCALに含めない、の設計ルール込み。
- gain-tuningスキルのパラメータ表に新パラメータ2つを追記(950未満禁止の注意含む)。

### 現在の状態

- ファームは新制御パラメータ込みでビルド可、`CLOSED_LOOP_TEST_ENABLED=0`の安全待機。
  通電試験は引き続き機構手回し点検待ち。

### 次の作業

1. 手回し点検 → イテレーション3再現確認(積分クランプ込み)→ Ki/angle_kp詰め → 駆動実走。
2. 接地移行時は`CALIBRATION_AND_ADAPTATION_PLAN.md`の段階1(手動再特性化)から。

---


## 2026-07-06 (2)

### やったこと

- ARK CANnodeの公式リポジトリを `hardware/reference/ARK_CANNODE/` へ取得(Rev 1回路図PDF+BOM)。
  回路図を精読し、流用候補ブロック(LM66100逆接保護、CANコネクタ2個並列のデイジーチェーン渡り、
  外部信号ESDダイオード)を `CARRIER_BOARD_REQUIREMENTS.md` の新設「回路図作成メモ」に整理。
- **推奨ピン割当表の全ピンAF成立を机上確認**(ST公式STM32_open_pin_dataのG474Rx XMLと照合)。
  FDCAN1=PA11/12、FDCAN2=PB12/13、SPI3=PC10-12、LPUART1=PA2/3、I2C1=PA15/PB7、SWO=PB3、
  BOOT0=PB8、NRST=PG10(pin7)。要件書の「CubeMXで確認してから」注記を確認済みに更新。
- 主要部品のピン配置をデータシート/KiCad公式シンボルで確認し要件書へ記録:
  TCAN332(SOIC-8)、MCP1826S(SOT-223)、LM66100DCK(SC70-6)、PESD1CAN(SOT-23、標準ライブラリに
  無いので自作シンボルが必要)、OKI-78SR-5。KiCad 10標準ライブラリのシンボル名も表に記載。
- AMT22データシートrev1.10でコネクタピン順を確認(1=+5V/2=SCLK/3=MOSI/4=GND/5=MISO/6=CS)、
  要件書に追記。AMT22/PESD1CANのPDFを `hardware/reference/datasheets/` に保存。
- 回路図のKiCadファイル自動生成も試みたが、**回路図はKiCad GUIで手描きする方針に変更**(ユーザー判断)。
  書きかけの生成スクリプトは削除済み。

### 現在の状態

- 回路図作成(フェーズ2)の前提が全て揃った: ピン割当確定レベルの机上検証済み、参考回路
  (candleLightFD KiCadソース+ARK CANnode PDF+CANable PDF)取得済み、主要部品のシンボル所在と
  ピン配置確認済み。KiCad 10がインストール済み。
- `hardware/blocks/` `unit-board/` 等は骨組みのみ(.gitkeep)。MB1367回路図PDFのみ手動DL待ち。

### 次の作業

1. KiCad GUIで `blocks/`(can_interface / power_input_5v / mcu_min_g474 / status_led)と
   `unit-board/` の回路図を作成する(要件書「回路図作成メモ」と `CARRIER_BOARD_BUILD_PLAN.md`
   フェーズ2のブロック一覧に従う)。PESD1CANの自作シンボルを `hardware/lib/` に作る。
2. CAN-G474到着後のベンチ確認(前エントリの1〜3)は並行して進む。

---


## 2026-07-06

### やったこと

- `docs/S815e87aa382049149032f707af3370877.pdf` を確認。RC FPV Drone Storeが添付した
  汎用製品マニュアルであり、基板の回路・ピン配置・電源・CAN仕様は含まれていないと判明。
- 参考候補のARK CANnodeについて、公式資料と公開ハードウェアリポジトリの所在を確認。
- Matek CAN-L431をベンチ用CANノードとして使う方針を確定。基板製作ではCAN-L431、
  CAN-G474、ARK CANnode、CANable 2.0を参考にすることを設計文書へ反映。
- 購入済みMatek CAN-G474を主試験機へ変更。CAN-L431は対向ノード、NUCLEO-G474REは
  書込み復旧・回帰確認用の予備とする方針を確定。
- CAN-G474のArduPilot hwdef/AP_Periphをファーム設計参考に使い、制御ループは底面SWDから
  ST-LINKで書き込む方針を文書化。GPL実装はライセンス決定前に直接コピーしない。

### 現在の状態

- 対象商品の技術資料は未入手。現PDFのみでは基板設計への直接的な反映はできない。
- ARK CANnodeはSTM32・5V給電・CAN・SWD等の実装参考になるが、G474・2系統FDCAN・
  モーター周辺ノイズ環境との差分評価が必要。
- CAN-G474実機でG474上の2バス同時動作を検証できる。ただし現行NUCLEO用ファームとは
  CAN2・AMT22 SPIのピンが異なるため、ボード別platform設定の追加が必要。
- CAN-L431はCAN物理層・配線・終端・1Mbps通信の対向ノードに使う。

### 次の作業

1. CAN-G474到着後、5V給電、SWD/UART1 DFU、Device ID、LED/GPIO実行を確認する。
2. CAN-G474用ボード定義を追加し、CAN 2系統の同時1Mbps試験を行う。CAN-L431を対向ノードに使う。
3. CAN-G474のhwdefとARK CANnode/CANable公開回路を、現行の`CARRIER_BOARD_REQUIREMENTS.md`とブロック単位で比較する。

---


## 2026-07-05

### やったこと

- ベンチテストを大きく前進: C620フィードバック受信(段階2)→低電流動作確認(段階3)→
  AMT222+C620x2の閉ループ制御まで到達。
- 制御方式を確定: モード座標PI(操舵=モーター和/駆動=差)。摩擦フィードフォワードは
  実測ばらつき(ブレークアウェイ150〜950mA、角度・方向依存)を理由に**廃止**し、
  PI積分のみで摩擦を吸収する構成に。電流上限2000mA(実測最悪値の約2倍マージン)。
- スティックスリップ対策として最低ステア速度フロア(steer_min_rpm=2rpm)を導入。
- ゲイン調整4イテレーション実施。ベスト構成で**+10°ステップを約3.5秒、
  終端誤差0.37°、オーバーシュートなし**を実機達成。Ki=200は激発振でNG確定。
- ゲイン調整の反復作業を下位モデルへ委譲できるようパイプライン化:
  `.claude/skills/gain-tuning/SKILL.md`(手順・判定基準・安全ルール)と
  `.claude/agents/gain-tuner.md`(sonnet固定エージェント)。
- 詳細ログ: `firmware/PROGRESS.md` と `firmware/docs/CONTROL_LOOP_TUNING.md`。

### 現在の状態

- ファームは安全待機(`CLOSED_LOOP_TEST_ENABLED=0`、電流常時0)で書き込み済み。
- **要注意**: Ki=200発振の直後の試験でステア軸が目標から-114°逆走して発散停止した。
  機構(ベルト/ギア/カップリング)に何か起きた可能性があり、通電試験は中断中。
- 操舵制御は「まともに動く」水準に到達。駆動(ホイール回転)側の実走は未実施。

### 次の作業

1. **ステア軸の手回し点検**(引っかかり・ガタ・異音・AMT連れ回りズレの確認)← 最優先
2. 点検OKならベスト構成の再現確認 → `/gain-tuning`(またはgain-tunerエージェント)で
   Ki 100〜150 / angle_kp の詰め。
3. 駆動モードの実走テスト(wheel≠0)、目標角の連続追従評価。

---


## 2026-07-02

### やったこと

- 電装計画の全docsをレビューし、パーツ選定を具体化(AMT22直結化、TCAN332、MCP1826S、SD-25B-5/SD-50B-12、XT90-S、MIDIヒューズ、EVリレー等)。
- AMT22データシートを確認し、MISO分圧不要(全信号3.3V直結可)と判明。要件書を修正。
- 主要アーキテクチャを確定: G474自作基板 / 2バスCAN / Teensy 4.1 / AMT222A-V(5mmボア) / 4線5V給電 / XH+XT / ゼロ点MCU Flash保存。
- 中央CANのID設計案を作成(`docs/communication/COMMUNICATION_NAMING_AND_IDS.md`)。
- STM32G474RET6の推奨ピン割当表を作成(`docs/electrical/CARRIER_BOARD_REQUIREMENTS.md`)。
- 中央ボード要件書を新規作成(`docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md`)。
- KiCad共通ブロック方針を策定(`docs/electrical/CARRIER_BOARD_BUILD_PLAN.md`冒頭)。
- STM32書き込み環境を整備: Arm GCC 14.2導入、toolchain.ps1追加、launch.json修正、日本語パス起因のobjcopy失敗を修正。
- NUCLEO-G474REへFlash書き込み成功、B1→LD2動作を実機確認済み。
- AGENTS.md / CLAUDE.md / PROGRESS.md(本ファイル)を整備。
- オドメトリを確定: 3輪AMT102+専用G474基板(unitId=4)、x/y/θを中央CANへ配信。要件書とCAN payload定義を作成。
- ベンチテスト計画を作成(`docs/testing/NUCLEO_BENCH_TEST_PLAN.md`)。MCP2551の3.3V接続可否をデータシートで確認済み(TXD直結可、RXDはFTピン受け)。
- `hardware/` を整備: lib/blocks/基板3種/referenceの構成。candleLightFD(KiCadソース、CERN-OHL)とMKS CANable V2.0回路図を収集。ST MB1367回路図のみ手動DL待ち(README記載)。

### 現在の状態

- docs体系はG474自作基板+2バスCAN前提で一貫。電装3枚(ユニット/中央/分電盤)の要件が揃った。
- ファームはB1→LD2の最小構成がFlashで動作中。ビルド・書き込みはスクリプトで再現可能。
- KiCad未着手。ピン割当はCubeMX未確認(表はドラフト)。

### 次の作業

1. **ベンチテスト**: `docs/testing/NUCLEO_BENCH_TEST_PLAN.md` に従い、NUCLEO+MCP2551+AMT222A-V+差動モジュール実機で段階テスト1〜7を進める。ファーム実装(FDCAN/C620/AMT22ドライバ、制御ループ)もこの中で行う。
2. CubeMXでピン割当のAF成立確認 → 要件書の表を確定版に更新。
3. `hardware/` ディレクトリ骨組み+KiCad共通ブロック(can_interface等)の作成。
4. 中央ボード用にコンタクタ・E-stopスイッチの型番確定(コイル仕様がドライバ回路に効く)。
5. オドメトリ(AMT102)の受け側MCUを決める(Teensyならレベルシフタ、G474なら直結)。

## 2026-07-07 ゲイン調整セッション保存

- C620の `feedback.rpm` はM3508内蔵19:1減速前のロータRPMで、制御側の差動ステア運動学は減速後出力軸RPMとして扱う方針に整理した。
- ファーム側ではC620フィードバックを `M3508_INTERNAL_REDUCTION` で除算して `unit_controller_update()` に渡す前提へ修正・文書化した。
- 単点RPM試験用に、サブエージェント契約、コンパクトログ収集、実機mutexラッパを追加した。
- 40 wheel-rpm単点試験:
  - Run1: drive Kp/Ki=5/20、steer Kp/Ki=50/20で10秒完走。
  - 後半平均 33.999 RPM、範囲 -0.032〜243.561 RPM、角度誤差peak 1.670°。
  - 周期的stick-slipのためFAIL判定。
  - Run2はログ未生成で評価不能のため採用せず、追加駆動なし。
- 現在状態:
  - `CLOSED_LOOP_TEST_ENABLED=0`
  - clean build後、safe-idle flash/verify/reset成功済み。
  - 40rpmは失敗境界として扱い、次は50rpm以上の安定域から下限探索または試験ハーネス高速化を優先する。

## 2026-07-07 ゲイン調整セッション保存(2)

- `invoke-hardware-session.ps1`経由でstaircase試験を実施し、各回の終了後にsafe-idleを
  flash/verify/resetした。最終状態は`CLOSED_LOOP_TEST_ENABLED=0`のsafe-idle。
- 標準staircase(40/45/50/60/75/100/150rpm)は全stepが`STEP_OK`で完走。
  `STEP_OK`直前1秒では40rpmも平均40.74rpm、角度誤差max 0.97°まで入った。
- 低速staircase(25/30/35/40rpm)も追加実施。25rpm/35rpmは`STEP_OK`、
  30rpm/40rpmはtimeout。最大角度誤差10.37°。結果が非単調で、低速限界は
  始動角・局所摩擦・駆動→操舵カップリングに強く依存している可能性が高い。
- 暫定判断: 現ゲインの正転・無負荷では40rpm以上は動作可能だが、30〜40rpm帯は
  安定採用には未確定。次は角度外乱対策として操舵保持側ゲインを少し戻すか、
  30/35/40rpmを開始角・正逆方向を変えて複数回試験する。

## 2026-07-07 ゲイン調整セッション保存(3)

- 操舵保持を強化して再試験:
  - `steer_max_rpm=1.0`
  - `angle_kp_rpm_per_deg=0.2`
  - `steer_mode_ki=30`
  - step内角度誤差6°/300msでstep FAIL、`scale=`ログ追加。
- 30/35/40rpm再試験では、40rpmのみ`STEP_OK`。30/35rpmは角度ではなく駆動側stick-slipで
  timeout。操舵外乱は最大3.43°まで低下したため、下限は暫定40rpm。
- 中高速staircase(40/75/150/250/350rpm)は全step`STEP_OK`、電流スケーリング0%、
  角度保持良好。350rpm直前1秒は平均345.75rpm、角度誤差max 0.79°。
- 最終状態: 実機はsafe-idle。`firmware/src/main.c`も`CLOSED_LOOP_TEST_ENABLED=0`。
  次は500/750/1000rpm級へ段階拡張して、理論wheel上限(約1360rpm)へ近づける。

## 2026-07-07 ゲイン調整セッション保存(4)

- ユーザー指摘により、各stepの保持時間を長くした拘束領域試験へ移行。
  `STEP_MIN_DWELL_MS=10000`、`STEP_STABLE_MS=3000`、`STEP_TIMEOUT_MS=25000`。
  上限拘束時に要求rpmとの差で失敗しないよう、判定基準を`wheel_rpm_command`へ変更。
- 500/750/1000/1200/1400rpm要求の長時間staircaseを実施し、全step`STEP_OK`。
  500〜1200rpmは直前1秒でp-p 2.5〜5.1rpm程度、角度誤差max 0.62°以下。
  1400rpm要求では制御器が約1363rpmへ制限し、実測平均1363.49rpm、角度誤差max 0.62°。
- 暫定レンジ: 無負荷・正転では下限40rpm、上限は`motor_max_rpm=469`由来の約1360rpm。
  30/35rpmはstick-slipで不採用。次は逆転側と、接地/拘束での温度・電流余裕確認。

## 2026-07-07 ゲイン調整セッション保存(5)

- 逆転代表点 -40/-500/-1400rpm を長時間保持で確認。
  全step`STEP_OK`、終了後safe-idle書き戻し済み。
- 直前1秒:
  - -40rpm: 平均 -42.39rpm、p-p 9.02rpm、角度誤差max 0.53°
  - -500rpm: 平均 -500.31rpm、p-p 1.90rpm、角度誤差max 0.62°
  - -1400rpm要求: cmd約 -1363rpm、実測平均 -1362.55rpm、p-p 2.26rpm、角度誤差max 0.70°
- 結論: 無負荷では正逆とも`|ωw|=40〜約1360rpm`で安定。次は接地/拘束状態での
  温度・電流余裕・低速stick-slip再評価。

## 2026-07-07 ゲイン調整セッション保存(6)

- 接地試験ができないため、`ωw`固定中に`θs`を動かす同時指令試験へ移行。
- `ωw=500rpm`、起動角から`θs=+10°`を実施。
  初回はstep内角度誤差6°ガードが意図せず働いたため、角度step用に12°へ緩和して再試験。
- 再試験結果: `STEP_OK`。角度誤差は約1.0秒で1°以内、final-halfでは
  wheel平均500.11rpm、p-p 9.91rpm、角度誤差max 0.77°、scale 0%、maxTemp 29°C。
- 判断: 無負荷では`ωw=500rpm`を維持しながら`θs=+10°`へ収束できる。
  次は`θs`往復(+10/-10/0)または`ωw=40/1200rpm`代表点で同じ角度step。

## 2026-07-07 ゲイン調整セッション保存(7)

- 目視切り分けしやすくするため、`ωw=500rpm`のまま`θs=+90°`を試験。
- `steer_min_rpm=2`ではログ上は約0.9秒で到達するが、終端で±2〜3°のリミットサイクルが出て
  安定判定timeout。`steer_min_rpm=0`では`STEP_OK`。
- `steer_min_rpm=0`試験のログではAMT角が約49.9°→138.5°へ約90°変化し、wheel平均500.01rpm、
  p-p 6.85rpm、角度誤差max 0.44°、scale 0%、maxTemp 30°C。
- ただしユーザー目視ではステア変化が見えなかった。ログ上のAMT角と物理ステア出力の対応が
  未確認。次は通電せず、ステア出力を手で動かしてAMT角が同じだけ変わるかを確認する。

## 2026-07-07 ゲイン調整セッション保存(8)

- `ωw=500rpm`を先に定常化し、その後`θs=base/+90/+180/+270/+0°`へ90°刻みでstepする試験を実施。
- step0〜3は全て`STEP_OK`。final-half wheel平均はほぼ500rpm、p-pは約5.8〜8.1rpm、
  角度誤差maxは0.62°以内。
- step4(+0°戻し)も`STEP_OK`だが、ユーザーが最終stepでホイールに触れたため外乱あり。
  p-p 93rpmは速度制御評価から除外する。
- 判断: ログ上は500rpm定常中に90°刻みの`θs`変更へ追従でき、ユーザー目視でも良さそう。
  AMT角ログと物理ステア出力は概ね一致している扱いで次へ進める。最終stepはホイール接触外乱あり。

## 2026-07-07 ゲイン調整セッション保存(9)

- 90°刻み同時指令を低速40rpmと高速1200rpmへ展開。
- 40rpmは全step完走し角度は概ね追従するが、wheel p-pが大きく、機構摩擦を超える瞬間の
  オーバーシュート/stick-slip境界。実用下限は40rpmではなく75rpmから扱う方針。
- 1200rpmは全step`STEP_OK`、scale 0%。定常化後のstep1〜4はwheel p-p約3.6rpm、
  角度誤差max 0.70°以内。maxTempは30→36°C。
- 結論: 無負荷単体ユニットでは、実用域`|ωw|>=75rpm`で`ωw, θs`指令制御は成立。

## 2026-07-07 中央CAN受信ログ準備

- 2個目のCANトランシーバをFDCAN1(PA11/PA12)へ接続する前提で、ファームに中央CAN初期化を追加。
- safe-idleのまま、FDCAN1受信フレームをVCPへ`CENTRAL_RX`表示。
- `0x101` DLC8を`SET_TARGET`としてlittle-endian int32 x2で仮decodeし、
  `SET_TARGET_RX steer=... wheel=...`を表示。まだ制御には接続していない。
- `docs/communication/COMMUNICATION_NAMING_AND_IDS.md`へSET_TARGET little-endian規約を追記。
- Debugビルドとflash/verify/reset完了。次はCANableから`0x101`を送ってG474 VCPで受信確認。

## 2026-07-07 中央CAN受信確認

- CANableはWindows上で`COM16`、G474 VCPは`COM15`として認識。
- CANable(SLCAN)から`S8`(1Mbps)、`O`後に`0x101` DLC8を送信。
  payload `90 5F 01 00 20 A1 07 00`。
- G474 VCPで以下を確認:
  - `CENTRAL_RX id=101 dlc=8 data=90 5f 1 0 20 a1 7 0`
  - `SET_TARGET_RX steer=90000 wheel=500000`
- 中央CAN受信経路は成立。次はenable/timeout付きで`SET_TARGET`を制御目標へ接続。

## 2026-07-20 ユニット基板 参照回路図の図面化(CircuitikZ + schemdraw SVG)

- `UNIT_BOARD_SCHEMATIC_REFERENCE.md` 3章の接続表を正として、6ブロックの参照回路図を作成。
  1. 電源チェーン(J101→LM66100(CE_N=VOUT明示)→PWR_5V→TLV1117LV33→3V3)
  2. CANブロック(TCAN1051V ピン1-8、ESD2CAN24、120Ω+SPDT終端、GH3パススルーx2、TXD/RXD方向矢印)
  3. MCU電源・デカップリング(VDD x4各100nF、VBAT、VDDA/VREF+島、C310バルク)
  4. HSE+NRST+BOOT0 / 5. 5V監視ADC(33k/22k+BAT54S) / 6. AMT22・デバッグ・ID DIP・LED
- 成果物:
  - `docs/electrical/figures/unit-board-circuitikz.tex`(article 1本に6図。ローカルにLaTeX環境が
    無いため未コンパイル。pdflatex互換のためtex内注記は英語)
  - `docs/electrical/figures/unit-board-block1.svg`〜`block6.svg`(schemdraw 0.23でレンダリング済み、
    日本語注記付き、テキストはパス化済みでフォント非依存)
- 未確定注記を図中に明記: C620側コネクタ(6章#1)、DIP型番(#2)、R601-604値(#3)、LM66100/TLV1117
  ピン番号(#4,#5)、水晶pad番号(#6)、DBG_TX/RX方向(#7)。
- 生成スクリプトはscratchpad(セッションtemp)の`gen_figs.py`。再生成が必要ならschemdrawで同様に可能。

## 2026-07-23 ユニット基板 回路図ブロック作成・AI監査セーブポイント

- KiCadの`hardware/unit-board/unit-board.kicad_sch`を親シートとして、電源入力/3.3V生成、
  5V監視、STM32G474最小回路、中央CAN、C620 CAN、AMT22/デバッグ/ID DIP/LEDの各ブロックを作成。
- 階層シートからモジュール基板PCBを作成する段階へ進む方針。ユニット基板を正本として整備し、
  オドメトリ基板など派生基板は用途別プロジェクトへ複製して不要ブロックを差し替える。
- AI監査で、5V監視ADCノードの未接続とAMT22 SPI配線の微小ギャップを修正。
- 2026-07-23の保存時点でKiCad CLIから回路図を読み込み可能。ERCは71件
  （Errors 52 / Warnings 19）で、まだPCB更新へ進める品質ではない。
- 未解決の重要項目:
  - 電源入力GH2のpin 1/2極性を要件（pin 1=PWR_5V、pin 2=GND）と一致させる。
  - 4pad水晶Y1を`Device:Crystal_GND24`相当へ変更し、信号pad 1/3、GND pad 2/4を正しく接続する。
  - 親子シート間で`PWR_5V`、`CAN_TX/RX`、`SPI3_MOSI/MISO`などの階層ラベル名を統一する。
  - PWR_FLAG、未使用ピンのNo Connect、電源ピン駆動元を整理してERCを収束させる。
  - J7を縦型`BM06B-GHS-TBT`へ、COMM/ERR LED色とD7/R14のvalueを部品表どおりに直す。
- 次の作業: 上記の重要項目を回路図へ反映し、ERC/BOM/netlistを再検証してからPCBレイアウトへ進む。
