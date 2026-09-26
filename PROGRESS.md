# Project progress
## 2026-09-25 (駆動V2シルク参照番号を非表示)

- ユーザーの新規配置配線完了後の依頼で駆動V2 PCBを更新。開いているunit-board-v2と最新保存時刻22:55:11から対象を確認。
- F.SilkSのReference表示55件を非表示。保存読戻しでF/B.SilkS参照表示0。部品番号情報、製品名など他文字、配置、pad/net、配線、zoneは保持しfingerprint一致を確認。
- 退避/記録: output/kicad-check/unit-v2-2026-09-25/hide-silk-refs/。表示変更だけなのでERC/DRC再実行なし。ODOMは未変更。次: PCBを開き直して確認、電気的検査は別途実施。

## 2026-09-25 (駆動V2 C620 CAN終端の実装漏れを確認)

- ユーザーの終端有無質問を受け、最新駆動V2 netlistとPCB padネットを確認。C620_CAN_H/Lに接続されるのはU5/D2/J4/J5のみで、基板内終端抵抗はない。
- R1=120RとSW1は中央CAN COMM_A/B側の終端。CARRIER_BOARD_REQUIREMENTS.mdのC620終端120Ω+スライドスイッチ部品表に対し、回路図/PCB未反映。
- 回路図/PCBは今回変更なし。次: C620側/ハーネスの終端有無を踏まえて駆動V2の終端追加を検討。今回生成した製造ZIPはODOM V2で、C620バスは対象外。

## 2026-09-25 (ODOM V2製造ZIP出力・検査残件あり)

- ユーザー依頼で最新保存PCBの固定snapshotから4層Gerber・PTH/NPTHドリルを出力し、output/manufacturing/odometry-v2-2026-09-25/odometry-v2-2026-09-25-NOT_RELEASED.zipを作成。中断後再開時も原本PCBとsnapshotのSHA256一致を確認。
- ZIPは11 Gerber+job+2 drillの14ファイル。展開内容と出力ファイルのbyte一致、4銅箔層、外形中心線65×30mm、PTH113穴/NPTH8穴を検証。原本変更・注文はしていない。
- 最新未接続0。DRC8件（J8固定pad端間隔2、孤立GND、library形状/参照警告等）、別parity7、ERC0エラー/FP警告2が残り、製造検査合格扱いではない。QA-NOT_RELEASED.mdに残件記載。
- 次: J8銅箔端間隔0.225mmと製造条件、library/実装属性等の残件を確認してから発注判断。ZIPは生成済みで、発注は未実施。

## 2026-09-25 (ODOM V2シルク参照番号を非表示)

- ユーザー指定でODOM V2 PCBのF/B.SilkS上のReference表示22件を非表示。保存読戻しで表示参照0件を確認。
- Ref情報、他field、信号表示、pad/net、配置、配線、zoneは保持。変更前後fingerprint一致を確認。表示変更のみのためERC/DRC再実行なし。
- 退避/検証記録: output/kicad-check/odometry-v2-2026-09-25/hide-silk-refs/。PCBを開き直すと反映される。電気的残件は前回検査を参照。

## 2026-09-25 (ODOM V2再確認2: DRC7+未接続1)

- 最新保存PCBをread-only検査。前回DRC8+未接続3から7+未接続1へ改善。U1 GND/3.3V未接続とR9入力のdangling viaは解消。
- 残り: J8固定pad4/5の端間隔0.225mm（要求0.5）、3.3V dangling track、孤立GND、SW3/J7/U7 library差。未接続1は3.3V配線(104.725,104.7352)と(109.475,103.1852)間。
- ERC0エラー/FP警告2、別parity警告6は継続。pad機能不一致0、規則/除外変更なし。原本編集なし。
- 詳細: output/kicad-check/odometry-v2-2026-09-25/recheck-02/recheck.md。次は残る3.3V接続とJ8基板端間隔を修正。

## 2026-09-25 (ODOM V2再確認: DRC8+未接続3)

- ユーザーの修正後をread-only再検査。前回DRC20+未接続4から8+未接続3へ改善。配線間隔/線幅違反0。ERCエラー0/footprint参照警告2、回路図整合の別警告6は継続。規則/除外の変更なし。
- 残件: J8固定padの端間隔2、dangling track/via各1、孤立GND1、library差3。未接続はU1.12 GND、U1.32 3V3、3V3配線の一部。座標はoutput/kicad-check/odometry-v2-2026-09-25/recheck-01/recheck.md。
- エンコーダJ4/J5/J6 1=A/2=+5V/3=B/4=GNDはねじれ防止の意図した変更とユーザー確認。ADR・ODOM要件・ピン割当・V2要件に明記し、旧配列との差を不具合から除外。SWD/CAN/UART/encoderの回路図とPCB接続一致。
- PCB/回路図は今回変更なし。次: 電源/GNDの未接続3件とJ8端間隔を修正する。

## 2026-09-25 (ODOM V2: 保存後の原本へ修正反映)

- ユーザー「保存したから反映して」に従い最新ファイルを退避。PCBは前回baselineと同一、回路図は更新済み。ベタ再充填・LED線幅15本修正・不要枝削除を原本PCBへ反映し、SWD J3のDNPを最新回路図に合わせて解除。
- DRC20+未接続4。ERC0エラー/2警告（J3/J8 footprint library名未指定）。整合検査の別6警告はfootprint ID差2、CAN J8 DNP差1、REF**取付穴extra/duplicate3。規則緩和/除外追加なし。
- 新回路図とPCBのRef/UUID、電気的接続は一致（U5 NCエスケープ差のみ）。J3=SWD/J8=CAN/J9=UART。ユーザーが入力RC6個を削除、encoder J4/J5/J6を1=A/2=5V/3=B/4=GNDに合わせたため旧不一致指摘は解消、資料との仕様差として残した。
- 最新一覧: output/kicad-check/odometry-v2-2026-09-25/REVIEW.md。退避/反映後検査はapplied/。次は未接続4件・配線/端間隔・局所100nF・library/DNP整合を解消する。まだ製造不可。

## 2026-09-25 (ODOM V2 PCB初回監査・修正候補)

- ユーザーからPCB設計完了とエラー一覧/可能な修正依頼。保存済みデータを退避・監査し、output/kicad-check/odometry-v2-2026-09-25/REVIEW.mdへ一覧化。
- ERC0。原本DRC62+未接続4。別candidate PCBへベタ再充填・LED線幅15本0.175→0.200mm・不要短枝線除去を行い、DRC20+未接続4へ削減。原本PCB/回路図は変更していない。
- 残り: clearance10、edge5、孤立ベタ1、lib差4、未接続4。規則緩和/除外追加は行わない。
- 保存済み回路図/PCB間でSWDとCANのRef/UUID、J4/J5/J6のピン割当、入力RC6個等に不一致。PCB SWD J3がDNP。U3/U7の直近100nFも不足。UART J9とbuffer電源padネット割当は一致。
- 回路図エディタに未保存マークあり、保存/終了を質問中。最新保存後に再照合して候補修正を原本へ取り込む必要がある。候補も製造不可。詳細・snapshot・修正候補は同出力フォルダへ保存。

## 2026-09-23 (駆動/ODOM V2: UARTを3pinヘッダ化)

- ユーザー指定で両V2回路図のUART用TP901/902/903を除去し、J9へ置換。共通1=GND、2=MCU TX、3=MCU RX、3.3Vロジック、電源ピンなし。
- Connector_Generic:Conn_01x03とConnector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Verticalを使用。2.54mmピッチのスルーホールで必要時だけヘッダ実装可。
- 駆動J9.2=U4 PA2/pin14、J9.3=PA3/pin17。ODOM J9.2=U1 PA2/pin16、J9.3=PA3/pin17。10pin SWDとODOMバッファ電源修正は維持。
- 両基板ERCエラー0/警告0。旧TP/新J9を除く接続集合は変更前後で一致（駆動77、ODOM85）。検証記録はoutput/kicad-check/v2/{unit,odometry}/uart-header-check.md。
- 今回の対象は回路図で、PCB配置・配線はユーザー担当。次: 変更後回路図を開き直し、PCBへJ9を反映する。SWDの正式ヘッダfootprint選定は残る。

## 2026-09-23 (ODOM V2: 10pin変更の再反映)

- ユーザーから変更が見えないと報告。実ファイルを読むと、19:48:22の保存時点でJ8がGH6へ戻り、V2のライブラリ参照表も無くなっていた。原因は断定しない。
- 現状態を退避し、他の接続を維持してJ8 10pin/UART TPを再反映。ユーザーよりエディタを閉じたと確認。専用symbol/footprintの参照表を復元。
- 保存後の実ファイル読戻し、ERCエラー0/警告0、U3/U7/U9 pin2=GND/pin5=PWR_3.3Vを確認。V1とPCBの編集は行わない。
- 次: hardware/odometry-board-v2/Oddom board.kicad_schを開き直してJ8を確認。PCBはユーザー担当、正式10pinヘッダのfootprintは未選定。

## 2026-09-23 (ODOM V2: J8を10pin SWDへ変更)

- ユーザー指定でhardware/odometry-board-v2/Oddom board.kicad_schのJ8を旧GH6からCortex Debug 10pinへ変更。pin1=PWR_3.3V(VTref)、2=PA13/U1.46、3/5/9=GND、4=PA14/U1.49、6=PB3/U1.55(SWO)、7/8=NC、10=NRST/U1.7。MCUのデジタルVDDと同じレールをVTrefに使用。
- UARTはTP901=USART2_TX(U1.16)、TP902=USART2_RX(U1.17)、TP903=GNDへ分離。既存U3/U7/U9電源修正を維持。
- ERCエラー0/警告0。変更対象を除いた82接続集合が変更前と一致し、回路図PDFも目視確認。レポートはoutput/kicad-check/v2/odometry/swd-10pin-check.md。
- V1とPCBは変更しない作業範囲を維持。J8 footprintは正式ヘッダ/キー/ケーブル未選定のため空欄。
- 次: ヘッダ/ケーブル適合を確定し、ユーザー側でPCBへ同期・配置・配線する。10pin SWD回路図対応は駆動V2とODOM V2の両方完了。残りTPとCAN2pin対象の確認は別作業。

## 2026-09-23 (駆動V2: エンコーダ端子・SWD確認、LED配置方針)

- ユーザー指定のAMT22端子順を駆動V2のJ6で再照合。1=+5V、2=SCLK(R15経由PC10)、3=MOSI(R16経由PC12)、4=GND、5=MISO(R17経由PC11)、6=CHIP SELECT(R18経由PD2)で既に一致し、並べ替えは不要。
- ST-LINK V3用10pin指定を再確認。既存V2 J7は1=VTref(デジタル3.3V)、2=SWDIO、3/5/9=GND、4=SWCLK、6=SWO、7/8=NC、10=NRST。正式コネクタ/ケーブルの機構適合確認は未完了。
- PWR/RUN/COMM/ERRを一か所へまとめる配置方針をADR/V2要件に追加。PCBはユーザー担当で、AIは回路図・接続確認を担当する。
- CAN 2pin化の追加指定あり。駆動V2の中央用J2/J3・C620用J4/J5の両方か、中央用だけかを確認中。現時点ではCAN回路図/PCBの変更なし。
- 次: CAN対象の回答後にGH横挿し2pinへ回路図変更し、ERC・ネット接続を再照合する。V1実機はCAN確認中。

## 2026-09-23 (V2着手前: ODOMバッファのfootprint照合)

- ユーザー指定でSOT-23-6を先に確認。ODOM U3/U7/U9の設計指定はSN74LVC2G17DBVR。TI公式SCES381N/DBV0006AはSOT-23-6、端子pitch 0.95mmで、KiCad割当のパッケージ種別・pitch・番号配置と整合する。
- TI推奨ランド例とKiCad標準ランドは寸法が同一ではない。実購入品の末尾型番は未確認で、DCK版等との取り違えは別途照合が必要。今回は回路図/PCB変更なし。
- 次: 手元品の正式型番と照合し、V2のSWD共通化・測定TP追加へ進む。V1はユーザーがCAN確認中。


## 2026-09-23 (現在地訂正: CAN確認中)

- ユーザーより「今CANの確認中」と訂正。現在の実機作業はCAN確認。前の記録からAMT102手回しを直近作業と推定した案内を撤回する。
- CANの対象基板/バス、送受信結果、他機能の確認結果はこの報告だけでは確定しない。
- 次: 現在のCAN確認を継続し、結果・不具合・ジャンパ修正を記録してV2設計へ反映する。

## 2026-09-23 (進行方針: V1で機能確認、V2で改良を並行)

### やったこと・現在の状態

- ユーザーとV1実機の機能確認を継続しながらV2を改良する方針で合意し、ADR/V2要件へ記録した。
- V1の個体/ファーム/ジャンパ/実測結果を残してV2修正台帳へ反映する。検証中のV1から高価なICを先に回収しない。
- 本区切りは方針記録のみ。実機通電・ファーム書き込み・回路図/PCB変更は実施していない。

### 次の作業

1. ODOM V1のAMT102を手回しし、正逆カウント変化を確認する。記録上、F405の書込/実行/LED確認は済み、エンコーダ機能の成立は未確認。
2. カウントが変わらなければ、センサ5V・A/B→バッファ電源/出力→MCU入力の順に実測して切り分ける。
3. 駆動V1も電源/SWD→AMT22→CAN→統合の段階で確認し、結果をV2のSWD/TP/接続修正へ反映する。
4. V2設計と中央の人手KiCad転記を並行し、機能に関わる未解決点を整理してから次回3種類の製造データを確定する。


## 2026-09-23 (最終方針: CAN横挿しGH3・主接点専用監視なし)

- ユーザー指定でCANコネクタは横挿しJST GH3（1 COMM_A / 2 COMM_B / 3 GND）に確定。同日の駆動/ODOM CAN2pin案を撤回。既存汎用4pinとC620純正ハーネスは別仕様。
- コンタクタ主接点の専用監視を今回省略する方針で合意。C620のCAN応答消失を駆動MCUが検知して中央へ送る補助診断とし、表示は「OFF指令中・C620応答なし」。無応答を遮断成功や溶着検出とみなさず、中央通信断は情報不明として区別する。
- ハードNC E-stop遮断、起動/reset/Hi-Z OFF、明示再アーム、E-stopループ/ボタン補助接点の監視は維持。CONTACTOR_STATUS_N/主接点後24V監視を追加しない。
- ADR・中央要件/転記注記・一括発注計画・V2要件を同期。中央PDF（2026-09-23版、13ページ）の該当箇所も更新し、変更ページを再レンダリング・目視確認。ファーム/GUI/中央KiCad/PCBは未変更。
- 次: 残るコイルclamp・ヒューズ・24V帰路/コイル端子詳細を確定し、人手でKiCadへ転記する。CANシリーズ/極数/向きと主接点監視の要否は未確定から外す。


## 2026-09-23 (中央回路図PDF改版・Teensyソケット寸法訂正)

### やったこと

- ユーザーは中央KiCadの自動編集でなく、見ながら手で転記できる回路図PDFを指定。既存PDFの読みやすさ改善も指定。軽量サブエージェントへ接続照合・PDF作成・フットプリント検証を委譲した。
- 次回PCBの範囲を駆動V2/ODOM V2/中央の3種類とし、中央給電CAN1/3を2pin、別電源LED/スイッチングCANを3pinへ変更。電源2pinとの誤挿入防止とGND共通化条件を計画書へ明記。
- コンタクタ励磁回路を中央へ統合する基本案へ更新。ハードNC E-stop・起動OFF・Teensy直接許可は維持。正式clamp/コネクタ/帰路は未確定を明示する。
- **PJRC公式寸法図で誤記訂正**: Teensy基板幅17.78mmとソケット列中心間15.24mmが混同されていた。関連6資料とADRを訂正。
- `hardware/lib/DifferentialSwerve.pretty/Teensy41_Socket_2x24.kicad_mod`を新規作成。48pad一意、2.54mm pitch、15.24mm列中心間、USB側pad1=GND/pad48=VINを公式ピンカードと照合し、KiCad読込/SVG目視確認。中央PCBへは未配置。
- 専用footprintの説明は`hardware/lib/TEENSY41_SOCKET_FOOTPRINT.md`。既存24pinシンボル2個それぞれへ一体footprintを割り当てず、使用時は1個の48pinシンボルと対応させる。

### 現在の状態・次の作業

- 中央KiCad回路図/PCBは今回変更していない。既存PCBのソケット2列配置は寸法が合わないため、PCB着手時に修正が必要。
- footprintの穴径1.0mmはKiCad標準ソケット基準。購入ソケットの端子径・1:1印刷・実物適合、Teensy下部/USB/microSD空間を確認してから製造する。
- 最終出力は`output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-23.pdf`（A3横13ページ）。生成元`tmp/pdfs/build_central_board_rev1_schematic_2026_09_23.py`、変更記録`docs/electrical/CENTRAL_BOARD_REV1_PDF_CHANGELOG_2026-09-23.md`。旧PDFを保存し、電源/eFuse/USB/分配を分割した独立図へ再描画。全ページをPNG化し、独立レビューと修正を実施。
- 未確定はCAN/コイル端子MPN、F401/clamp定数・過渡/解放時間、24V帰路結合、VUSB取り出し/実ソケット適合等。KiCad手動転記時に該当箇所を確定する。基板発注・部品購入は未実施。


## 2026-09-23 (駆動基板V2: SWD回路図とUART TP)

### やったこと

- `hardware/unit-board-v2/unit-board.kicad_sch`の旧GH6デバッグJ7をCortex Debug 1.27mm 2×5配列に置換。J7 pin1=MCUデジタル3.3VのVTref、2=SWDIO(U4 PA13/pin49)、3/5/9=GND、4=SWCLK(PA14/pin50)、6=SWO(PB3/pin56)、7/8=NC、10=NRST(pin7)。
- UARTを別のTP901(TX=PA2/pin14)、TP902(RX=PA3/pin17)、TP903(GND)へ分離。旧デバッグ枠と見出しを図面から除去。
- KiCad ERCは0エラー/0警告。XML netlistでJ7と新TP以外の既存75ネットの接続集合がV2分岐時の基準と完全一致。回路図PDFのルートページを目視確認。V1回路図/PCBは変更なし。

### 現在の状態・次の作業

- J7の正式MPN、キー形状、嵌合ケーブル、フットプリントは未選定。回路図Footprintは意図的に空欄。V2 PCBは旧GH6のままで、回路図同期・配置・配線と全pad照合が必要。製造不可。
- UART以外の測定TP、SWDコネクタの機構確認、PCB ERC/DRC・実装検査を続ける。

## 2026-09-23 (駆動/ODOM V2着手: デバッグ改善要件・作業データ分離)

### やったこと

- ユーザーのV1反省を`docs/electrical/UNIT_ODOMETRY_V2_REQUIREMENTS.md`へ具体化。VTref付き共通SWD、UART別TP、Pin1/キー/測定点、段階bring-up、回収部品と予備在庫、発注前の回路図/PCB全pin照合を定義。
- V2基本案を1.27mm 2×5 Cortex Debugとし、ST UM2910のMIPI10/STDC14対応表を照合。正式コネクタMPN/ケーブルは未確定。
- `hardware/unit-board-v2/`と`hardware/odometry-board-v2/`へ保存済み作業ツリーから分岐。元の18ファイルはSHA256で変更なしを確認。基準は`hardware/v2-baseline-manifest.json`。
- ODOM共有`AMT102_input.kicad_sch`に74LVC2G17のunit Cを追加し、U3/U7/U9のpin5=PWR_3.3V、pin2=GNDを接続。TI SCES381Nでpinout照合。ERCはエラー3/警告3→0。XML netlistで6電源pinの接続を検証。
- 駆動は複製時ERC 0。レポートは`output/kicad-check/v2-baseline/`と`output/kicad-check/v2/odometry/`。
- 9/22 firmware記録から、V3MINIEによるF405書込/LED成功、バッファ電源ジャンパ施工済み、AMT入力の切り分け継続中を確認。V1の未解決実装問題をV2で根拠なく回路変更しない。

### 現在の状態

- V2は設計途中。SWD/TPの回路置換、ODOM電源のPCB反映・配線、DRC/製造検証は未完了。PCBにはV1の旧配線が残るため発注不可。
- ODOM PCBのU3/U7/U9 pad2/5が未割当のままであることを確認。回路図ERC 0はPCB修正完了を意味しない。
- 元のV1 KiCadデータやユーザー作業中の変更を維持。両プロジェクトに状態READMEを配置。

### 次の作業

1. キー付きSWDヘッダ/接続ケーブルのMPNとメーカー図面・機構スペースを照合し、両回路図へ反映する。
2. UART/電源/CAN/センサTPを追加し、ODOM各バッファの100nFを確認する。
3. その他のジャンパ接続元/先をユーザー記録と照合して修正台帳へ追加。
4. PCBを回路図へ同期し再配置・配線。ERC/DRCと全IC電源pad/回路図対PCB照合後に製造データを生成する。


## 2026-09-21 (実装前チェック: ODOM基板 74LVC2G17電源未接続を発見・組立資料生成)

### やったこと

- 部品着荷を受け、駆動(unit)基板とオドメトリ(ODOM)基板の実装着手前監査を行った。
- `kicad_pcb`のパッド単位でネット未割当と1パッドのみのネットを機械的に抽出した。
  - unit基板(`hardware/unit-board/unit-board.kicad_pcb`): 未接続はGHコネクタの取付脚(MP)のみで正常。
    1パッドネットは未使用の`I2C_SDA`/`I2C_SCL`/`SWO`(U4のみ)で実害なし。
  - **ODOM基板: U3/U7/U9(74LVC2G17)のpad 2(GND)とpad 5(VCC)が全て未接続**。
    発注に使ったコミット`bcd22f1`(2026-07-29のGerber生成元)の`.kicad_pcb`でも同じ状態のため、
    届いた実基板も同じと判断。2026-07-26に回路図側でunit3(電源)を追加した修正が、
    PCBへ`Update PCB from Schematic`されないままGerberが出ている。
  - AMT102 3ch全てがこのバッファ経由(J4/J5/J6 pin1=PWR_5Vで5V出力を3.3Vへ受け直す構成)のため、
    未修正だとエンコーダ入力が全滅する。KiCad DRCの「unconnected pads 0」はネット無しパッドを
    検出しないので、DRCレポートでは気付けない。
- ジャンパ候補位置を抽出した(mm、PCB座標)。U3@(119.6,95.0)/U7@(77.7,102.4)/U9@(110.4,95.1)。
  - GND: 各バッファ隣のDNPコンデンサのGND側パッド(U3=C15/C17 pad2、U7=C23/C24 pad2、U9=C25/C26 pad2)が空きパッドとして使える(約2〜4mm)。
  - 3V3: 最寄りの`PWR_3.3V`ビアはU3=(128.275,104.0)約12.5mm、U7=(80.275,96.8)約6.1mm、U9=(109.475,100.775)約5.8mm。
- 組立用資料を生成した。
  - `output/assembly/unit-board-placement-refdes.pdf`、`output/assembly/odometry-board-placement-refdes.pdf`
    (F.Fab+Edge.Cuts+Courtyard、RefDesのみ、パッド番号表示、DNPは×印)
  - `output/assembly/unit-board-assembly-top.pdf`、`output/assembly/odometry-board-assembly-top.pdf`(値付き)
  - `output/assembly/odometry-board-position.csv`(ODOMの実装座標。unit基板は既存の`output/fabrication/unit-board-revA/unit-board-position.csv`)
- 基板寸法/構成: unit 45.0x45.0mm、ODOM 65.0x27.5mm。両方とも4層1.6mm・内層GNDプレーン・
  裏面実装部品0・裏面ペースト開口0(unitはTHTパッド0、ODOMはJ4/J5/J6/J7のXHのみTHT)。
- BOMと現物の型番差異を確認: `TLV1117LV33DCYR`→`TLV76133DCYR`、`ECS-80-8-33Q-JES-TR`→`FC3BAEBDI8.0-T1`、
  `A6S-3104-H`→`DS04-254-1-03BK-SMT`、`BAT54SLT1G`→`BAT54S-HF`。
  `.kicad_pcb`のValueは更新済みだがfootprintは旧品のまま。特にDIPスイッチは別メーカー別形状のため、
  ペースト印刷前に裸基板で仮置きしてランドの一致を確認する必要がある。

- 実装作業手順書PDFを作成した。`output/pdf/BOARD_ASSEMBLY_PROCEDURE_2026-09-21.pdf`
  (A4横9ページ、生成`tmp/assembly/build_assembly_procedure.py`)。
  p1表紙/対象基板、p2着手前チェック3件、p3 Sn63Pb37プロファイル+ドラッグはんだ、p4チェックリスト式実装手順、
  p5ジャンパ施工図(配線イメージ図つき)、p6通電bring-up、p7極性確認/参照、p8-9配置図。
  `PROJECT_DOCUMENT_INDEX.md`へ9.98として追加。
- **ハンダと表面処理を確定**: 当初はユーザー所有の`Sn42Bi58`(融点138℃、低温鉛フリー)前提で書いたが、
  BiはPbと混ざると Sn-Pb-Bi 三元共晶(約96℃)を作るため、表面処理が有鉛HASLだと使えない。
  ユーザーが実基板を確認して**有鉛HASL**と判明したため、**`Sn63Pb37`(融点183℃)**へ切替えて手順書を作り直した。
  有鉛HASL + Sn63Pb37 は濡れの点で最良の組合せで、合金の相性問題は消滅した。
  なお発注時の表面処理はリポジトリに記録が無く(2026-07-29の「次の作業」以来未決着)、今回実物確認で決着した。
- リフロープロファイル(基板温度基準): 予熱130〜150℃×90〜120秒 → ピーク200〜215℃(183℃超えで45〜75秒) →
  自然冷却。プレート設定は基板温度より10〜20℃高めが目安(4層1.6mm・内層GNDプレーンのため)。
- **5V監視の分圧を変更(2026-09-21確定)**: 実装時にR13の33kΩの現物が無かったため、在庫のある値で
  **R13=22kΩ(5V側) / R14=10kΩ(GND側)**へ組み替えた。分圧比0.400→0.3125、5.00V入力時のADC電圧
  2.000V→1.5625V、測定上限8.25V→10.56V、分圧電流91µA→156µA。過電圧クランプはD7(BAT54S-HF)が
  担うため保護性能は変化しない。在庫は10kΩ 10個(R4で4個使用)、22kΩ 10個なので4枚分を賄える。
  22kΩ/22kΩ(比0.5)案も成立するが、22kΩ在庫をほぼ使い切るため不採用。
  **ファームのADCスケールは`Vin = raw/4095*3.3/0.3125`**。`firmware/src/main.c`の`send_status3()`へ
  コメントで明記した(ADC自体は未実装)。
  反映先: `hardware/unit-board/5V monitoring.kicad_sch`、`unit-board.kicad_pcb`のValue、
  `ARCHITECTURE_DECISIONS.md`、`CARRIER_BOARD_REQUIREMENTS.md`(2箇所)、
  `UNIT_BOARD_SCHEMATIC_REFERENCE.md`(R304/R305表記の3箇所)。
  変更後に`kicad-cli sch erc`で駆動基板0件を確認し、配置図/座標CSV/フラット結線表/実装手順書PDFを再生成した。
- 作業中に参照する回路図資料を3種類整備した。
  1. `output/pdf/UNIT_BOARD_SCHEMATIC_KICAD_2026-09-21.pdf`(6ページ)、
     `output/pdf/ODOMETRY_BOARD_SCHEMATIC_KICAD_2026-09-21.pdf`(5ページ) — `kicad-cli sch export pdf`で
     実回路図をそのまま出力。正確だが階層シート構成で追いづらい。
  2. `output/pdf/BOARD_FLAT_NETLIST_2026-09-21.pdf`(5ページ、生成`tmp/assembly/build_flat_netlist.py`) —
     **階層を潰したフラット結線表**。製造された`.kicad_pcb`のネットリストから、MCU全64ピン→ネット、
     ネット→接続ピン(RefDes.pad(ピン名))、部品一覧を起こす。RefDes・ピン番号が実基板シルクと完全一致するので
     テスターを当てながら使える。ネット未割当パッドの検出結果も各基板の末尾に出力する
     (unit=無し、ODOM=U3.2/U3.5/U7.2/U7.5/U9.2/U9.5)。
  3. 既存の`docs/electrical/UNIT_BOARD_SCHEMATIC_WITH_BOM.pdf`等(2026-07-21) — 機能別1ページで読みやすいが、
     RefDesが旧番号体系(U301/U401/J401…)で実基板(U4/U3/U5/J2-J5…)と**一致しない**。参照時は注意。
- **追加で判明**: ODOM基板の74LVC2G17は、PCBだけでなく**回路図側でもunit 3(VCC/GND)が未配置**
  (`AMT102_input.kicad_sch`に配置されているのはunit 1とunit 2のみ)。2026-07-26のエントリにある
  「unit3を新規配置しERC 0件」は現在のワーキングツリーの内容と一致しない。2026-09-07に記録した
  ERCエラー3件(電源unit C未配置)が現状の正しい姿。Rev.B以降では回路図→PCBの順で修正が必要。
- HASLはパッドが平坦でないためステンシルが密着せず、LQFP64(0.5mmピッチ)で印刷ブリッジが出やすい。
  対策(捨て基板で囲う/スキージ45°1回/印刷直後のルーペ確認)と、逃げ道としてLQFP64のみ
  フラックス+ドラッグはんだで手付けする手順を手順書へ入れた。

### 現在の状態

- 実装未着手。ODOM基板は上記バッファ電源のジャンパ対応が前提。unit基板は製造データ上の阻害要因なし。
- 現行ファームはHSI 16MHz動作でLED_RUN=PA5(NUCLEOと同じピン)のため、unit基板の初回生存確認に流用できる。
  F405 ODOM基板用のファームは未着手。

### 次の作業

1. 実基板でU3/U7/U9 pin5-3V3、pin2-GNDの導通をテスターで確認し、ジャンパ要否を確定する。
2. DIPスイッチ(DS04-254-1-03BK-SMT)とその他置換品を裸基板へ仮置きしてランド適合を確認する。
3. unit基板1枚を先行実装し、電流制限電源で5V→3.3V、SWD Device ID、PA5点滅まで確認する。
4. ODOM基板を実装し、ジャンパ後にAMT102 A/B波形をバッファ出力で確認する。
5. ODOM回路図の`AMT102_input.kicad_sch`へ74LVC2G17のunit 3(VCC=PWR_3.3V / GND)を配置してERC 0件にし、
   PCBへUpdate PCB from Schematicを流す(Rev.B用。今回の実基板はジャンパで対応)。

## 2026-09-17 (24VアクチュエータCANノード Rev.A 人が読む回路図PDF・訂正と提案)

- `output/pdf/ACTUATOR_CAN_NODE_REV_A_BLOCK_DIAGRAM_AND_BOM_2026-09-17.pdf`(ブロック図+暫定BOM)を、LEDノードと同じ粒度の部品・ピン番号・ネット名付き回路図 `output/pdf/ACTUATOR_CAN_NODE_REV_A_SCHEMATIC_2026-09-17.pdf`(A3横9ページ: S01全体/訂正一覧、S02入力保護/GNDスター/Buck/LDO/24Vセンス、S03 F303K8全32pin+TIM AF、S04 CAN、S05 OUT2-4 (AHCT125+IRLML0100)、S06 DRV8251A、S07 分離式CONTACTOR_DRIVER、S08 KiCad割当/BOM数量、S09 ERC非検出13項目+未確定11件)に描き直した。生成は`tmp/actuator-node/build_actuator_rev_a_schematic.py`。PNG化→目視→修正を5周。
- データシート直接照合: TI DRV8251A SLVSFU6(DDA pin 1 IPROPI/2 IN2/3 IN1/4 VREF/5 VM/6 OUT1/7 GND/8 OUT2、`ITRIP×AIPROPI=VREF/RIPROPI`、AIPROPI 1575µA/A、VREF 0〜3.6V、IN内蔵100k PD)、SN74AHCT125 SCLS264R(PW 14pin)、TCAN1051-Q1 SLLSET0D、ESD2CAN24-Q1 SLVSFW5D、Infineon IRLML0100(1G 2S 3D、RDS(on) max 235mΩ@4.5V)。STM32F303K8はst.comに繋がらないため、ST公式GitHub `STM32_open_pin_data` の`STM32F303K(6-8)Tx.xml`とGPIO modes XMLでピン番号とAF番号を取得(LEDノードのU201ピン表もこれで裏付け、転記表へ注記)。
- 訂正: LMR51606のMPN/ピン順/FB分圧(LEDノードと同じ誤り)を要件書§2へ反映。前版ブロック図のRefDes重複(J501がSWDとMOTORの両方)を解消し、SWD=J201、MOTOR=J501、OUT1タブ=U601/Q601/J601/J602/J603とした。
- 提案(未承認、要件書に PROPOSAL として追記): OUT1〜4=PA6/PA7/PB0/PB1(TIM3_CH1〜4 AF2)で§9-1のSTOPを解消案。PA9 service inputはSWDヘッダのUART(PA9/PA10)と衝突するため、SERVICE_IN=PB5、LED_COMM/FAULT=PB3/PB4、PWR LEDは3.3V直結。GND_PWR/GND_CTRLはNT101で1点結合。
- 新たに見つけた正本内の矛盾: §4「未分離時ESTOP_LOOP_RETURNは未接続」と「VIN_ACTがタブを渡る」が両立しない(未分離OUT1負荷の24V供給元が不明)。PDFでは24Vタブ橋を破線の解釈として描き、要件書に未解決注記。 また中央基板Rev.1転記表のJ402-4は`GND_CTRL`、本要件書のパッド4は`GND_PWR`で不一致(未確定#12)。
- 次: (1) 未確定#1〜#3(GPIO/PA9/LED割当)と#6(24Vタブ橋)をユーザー判断で確定 → (2) 入力段・RIPROPI・clamp・コネクタのSTOPは実測後 → (3) 自作symbol(LMR51606XDBVR/TCAN1051VDRQ1/ESD2CAN24DBZRQ1/DRV8251ADDA)を作成 → (4) KiCad転記+`kicad-check`。

## 2026-09-17 (中央基板Rev.1 PDFのコンタクタ制御境界訂正)

### やったこと

- `output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-14.pdf`の旧表現「アクチュエータCANノードがCAN指令でコンタクタを励磁」を削除し、中央Teensyの`MOTOR_PWR_EN` 3.3V ON/OFFを別体`CONTACTOR_DRIVER`へ直接渡す構成へ訂正した。
- S01/S02B/S04/S06/S07を更新し、Teensy pin 2、J402 5線interface、ハードNCループ、別体gate buffer/low-side MOSFET、Reset/Hi-Z時OFFの関係を明記した。
- `ARCHITECTURE_DECISIONS.md`、`CENTRAL_BOARD_REV1_CONSTITUTION.md`、`CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md`、PDF生成スクリプトを同じ境界へ同期した。

### 現在の状態

- 中央PCBは24VコイルMOSFETを持たず、3.3V許可信号だけを出力する。E228 24Vコイルの励磁MOSFET/clampは別体`CONTACTOR_DRIVER`側に置き、コンタクタ制御はCANノードを経由しない。
- PDFは8ページを再生成し、全ページのレンダリング、主要ページの文字切れ・重なり、旧表現の残存なしを確認済み。

### 次の作業

1. J402の正式コネクタ型式とpin順、`CONTACTOR_STATUS_N`の実装有無を別体driver回路図と同時に確定する。
2. KiCad転記時に`MOTOR_PWR_EN`の起動時Low、driver入力/gate pulldown、Reset/Hi-Z時Q1 OFFを実測確認する。

## 2026-09-17 (LED CANノード Rev.A 人が読む回路図PDF・転記表の誤り3件訂正)

- `output/pdf/LED_CAN_NODE_REV_A_HUMAN_SCHEMATIC_2026-09-14.pdf`(ブロック図)を、中央基板Rev.1と同じ流れで部品・ピン番号・ネット名付きの回路図PDF `output/pdf/LED_CAN_NODE_REV_A_SCHEMATIC_2026-09-17.pdf`(A3横6ページ: S01全体/訂正一覧、S02電源、S03 F303K8 LQFP-32全32pin、S04 CAN+AHCTデータ出力、S05ハーネス/TP/KiCadライブラリ割当、S06 ERC非検出13項目+未確定11件+チェック手順)に描き直した。生成スクリプトは`tmp/led-node/build_led_rev_a_schematic.py`(KiCad同梱Python + schemdraw + reportlab)。PyMuPDFでPNG化→目視→ラベル衝突修正を5周。`PROJECT_DOCUMENT_INDEX.md`へ9.11として追加(9.10は旧版注記)。
- **データシート照合で転記表の誤り3件を発見・訂正**(TI `LMR51606` SLUSEY1B Rev.B / `TLV761` SBVS349D / `SN74AHCT1G125` SCLS378P はcurlで取得しpymupdfで本文抽出。STM32F303K8はst.comに接続できずKiCad 10標準symbol `STM32F303K8Tx` の32pinで照合、DS9866 Table 13での再確認は未):
  1. U101 LMR51606 DBVのピン順。旧「1 GND 2 FB 3 EN 4 VIN 5 SW 6 BOOT」→ 正「1 CB(BOOT) 2 GND 3 FB 4 EN 5 VIN 6 SW」。MPNも`XDDCR`はDSのDevice Comparison Tableに無く`LMR51606XDBVR`が正。footprintは標準`SOT-23-6`で可。
  2. U101 FB分圧。VREF=0.8Vのため旧R101/R102=100k/24.9kは4.0V出力(TCAN1051V/AHCTのVCC min 4.5V未満)。DS例の118k/22.1k(5.07V)へ変更。DNPのUVLO分圧100k/13.3kはDS閾値で10.4V rising/8.5V falling(旧記載8.0Vは根拠なし)。
  3. U201のLQFP-32ピン表がLQFP-48(F303C8)の内容(VBAT/PC13/PC14/PC15/VSSA、VDD=21等)で誤り。正: 1 VDD 2 PF0 3 PF1 4 NRST 5 VDDA/VREF+ 6〜13 PA0〜PA7 14 PB0 15 PB1 16 VSS 17 VDD 18〜25 PA8〜PA15 26〜30 PB3〜PB7 31 BOOT0 32 VSS。PC13が無いため`LED_FAULT`はPB0を提案(未確定)。VREF+用C208/C209はVDDAと同一ピンのためC206/C207へ統合を提案。
- 訂正は`LED_CAN_NODE_KICAD_ENTRY_REFERENCE.md` §3/§4(日付付き注記+表差替え)、`LED_CAN_NODE_PART_SELECTION.md` §1/§2、`LED_CAN_NODE_REQUIREMENTS.md` §3ピン表(PC13→PB0提案)へ反映。TLV76133DCY(1 GND 2 OUT+tab 3 IN)、AHCT1G125(1 OE 2 A 3 GND 4 Y 5 VCC)、TCAN1051/ESD2CAN24は正本どおりで問題なし。
- 正本に無く本資料が提案RefDesで埋めたもの: 状態LED R211〜R214/D211〜D214(1k、0603)、BOOT0 R201 10k+TP201、SERVICE_IN R202 100k+TP202、センス分圧R105〜R108/C105/C106、TP101〜104/TP301/302/TP401。S06未確定表で承認後に正本へ追記する。
- 次: (1) 未確定#2(LED_FAULTピン)・#3(C208/C209削除)・#5(VIN_LED_SENSE分圧)・#6(GH2誤挿入防止)をユーザー判断で確定 → (2) DS9866 Table 13でU201ピン番号を再確認(st.com復旧後) → (3) 自作symbol 3種(LMR51606XDBVR/TCAN1051VDRQ1/ESD2CAN24DBZRQ1)をDifferentialSwerveライブラリへ作成 → (4) ゾーンごとにKiCad転記+`kicad-check`でERC 0件。

## 2026-09-17 (24VアクチュエータCANノード ブロック図+BOM作成)

### やったこと

- `output/pdf/ACTUATOR_CAN_NODE_REV_A_BLOCK_DIAGRAM_AND_BOM_2026-09-17.pdf`を作成。A3横9ページで、全体構成、入力保護/5V/3.3V、F303+CAN、安全状態機械、4ch low-side MOS、DRV8251A H bridge、分離式CONTACTOR_DRIVER、暫定BOM、release gatesを整理した。
- 主要部品をメーカー資料で再照合し、`DRV8251ADDA`の8pinには`nFAULT`が存在しないことを確認。正本のpin budget、protection記述、status記述、bring-up記述を訂正した。
- `OUT1=breakaway contactor`の4ch境界と旧GPIO表のPA5+PA6-PB1(合計5制御)が矛盾するため、KiCad転記前のSTOP項目に変更した。
- BOMは確定部品、回路分割PROPOSAL、DNP/STOPを区別。入力逆接/TVS、power connector/fuse、負荷別clamp、motor bulk、`RIPROPI`/`VREF`は実負荷/波形測定前に発注確定しない構成とした。

### 現在の状態

- 人間レビュー用ブロック図と基板1枚あたりの暫定BOMは完成。PDFはレンダリングして9ページすべての文字切れ、重なり、表崩れがないことを確認済み。
- KiCad回路図/PCBは未作成。PDFは発注用・製造releaseではない。

### 次の作業

1. OUT1をbreakaway上に置く前提でF303の4ch GPIO/PWM割当を確定する。
2. 実DC motorのstall currentから`RIPROPI`/`VREF`、bulk capacitor、connector/fuseを計算する。
3. 入力最大同時電流とハーネスtransientを測り、逆接保護、入力TVS、J101、外部ヒューズを選定する。
4. 各OUT負荷を確定し、flyback diode/TVS/connectorを選定後、KiCad転記用1pin-1net表を作る。

## 2026-09-14 (中央基板Rev.1 KiCad転記用リファレンス作成・LTV-847Sピン対応の誤り訂正)

- `output/pdf/CENTRAL_BOARD_REV1_HUMAN_SCHEMATIC_2026-09-14.pdf`(S01〜S05ブロック図)を、人がKiCad GUIで回路図を起こせる粒度へ具体化した`docs/electrical/CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md`を作成。シート構成とRefDes体系(PDFページ番号=百の位、PDF既出のRefDesは維持)、全ネット名、Teensy socket 48pad表(Rev.1で不要になったpin 2/9/14はNC提案)、部品ごとのピン番号付き接続表、KiCad標準/自作symbol・footprint割当、ERC非検出注意17項目、未確定事項17件、転記後チェック手順を収録。`PROJECT_DOCUMENT_INDEX.md`へ9.25として追加。
- データシート直接照合: TI `TPS25947`(SLVSFC9C Rev.C 2026-05)のRPW 10pin配置(1 EN/UVLO、2 OVLO、3 AUXOFF、4 FLT、5 IN、6 OUT、7 dVdt、8 GND、9 ILM、10 ITIMER)、`RILM=750Ω`→ILIM 3.96/4.45/4.84A(DS表値)、`CdVdt[pF]=2000/SR[V/ms]`(10nF→約25ms、>10nFは100Ω直列推奨)、UVLO/OVLO閾値1.20V、故障ラッチ復帰は電源断のみ(EN固定分圧のため)。Nexperia `PMEG2010EA` SOD-323はpin1=K/pin2=A。
- **訂正**: `LTV-847S`のチャネル対応。Rev.A `CENTRAL_BOARD_SCHEMATIC_REFERENCE.md` D3と`reference-2026-09-12/`安全シートの「ch1=A1/K2, E9/C10」はLite-On図面(BNS-OD-C131/A4 内部接続図)と不一致。正しくはミラー対でch1=1/2↔16/15、ch2=3/4↔14/13、ch3=5/6↔12/11、ch4=7/8↔10/9。旧対応のまま描くとループ監視と予備ch、補助接点1/2が入れ替わる。D3は修正済み、9/12 KiCad参照シートは未修正(Rev.1で作り直す前提)。
- KiCad 10標準ライブラリ確認: `Isolator:LTV-847S`(既定footprint `SMDIP-16_W9.53mm`、実物照合要)、`Power_Protection:SRV05-4`、JST GH SM02/03/04/07/10B横挿し、Molex `43650-0600`、AMASS `XT30PW-M`、`PinSocket_1x24`は存在。`TPS259470` RPWのsymbol/footprintとTeensy 4.1 socket symbolは標準に無く自作が必要(9/14ドラフトのfootprint名`WQFN-10-1EP_2x2mm_P0.5mm_EP0.75x1.6mm`は標準ライブラリに存在しない)。
- 転記リファレンスから人が読む回路図PDF `output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-14.pdf`(A3横8ページ: 全体構成/S02A電源/S02Bスター+Teensy 48pad/S03 CAN/S04安全/S05 I/O/ERC非検出注意/未確定事項)を生成。生成スクリプトは`tmp/pdfs/build_central_board_rev1_schematic.py`(KiCad同梱Python + schemdraw 0.23 + reportlab、日本語はYu Gothic/HeiseiKakuGo)。schemdrawの`Ic`は直前要素の向きを継承するため`.theta(0)`、`Rect`の座標は`.at()`相対、ピン並びはリスト逆順(下→上)という3点に注意が必要だった。
- 同日追記の`ACTUATOR_CAN_NODE_REQUIREMENTS.md`(`J_SAFE`=1 `ESTOP_LOOP_RETURN`/2 `GND_PWR`、ノード5Vは中央CAN2 4pinポートから)に合わせ、J402=`J_SAFE`対、J403=`+24V_CTRL_IN`入力の提案Bで記述。**文書間不整合**: PDF S04は「2本ともノードへ」、ノード仕様書はループ往路24Vを供給しない。往路24V/LED 24Vの供給元(ノード経由か24V制御系直接か)と、`GND_CTRL_LED`(=ノード`GND_PWR`参照)を`GND_CTRL`と結合しない扱いはユーザー判断待ち。
- 作業フロー(再利用用): (1) ブロック図PDFと正本docs(決定事項・要件・ピン割当・Rev.A参照・部品選定)を全部読み、PDFに無い前提と矛盾を洗い出す → (2) ピン配置が誤りやすい部品(TPS25947/LTV-847S/PMEG2010EA)はメーカーPDFを取得しpymupdfで本文抽出、図面ページはPNG化して目視で照合 → (3) KiCad 10標準ライブラリを`ls`/`grep`してsymbol/footprintの実在を確認、無いものは「自作」と明記 → (4) 転記用Markdownを「シート/RefDes体系 → ネット名 → シート別ピン番号付き接続表 → BOM+ライブラリ割当 → ERC非検出注意 → 未確定事項 → チェック手順」の順で書き、確定/DS照合/提案/未確定を印で分離 → (5) 同日追記の関連docs(ノード仕様)と突き合わせて矛盾を未確定表へ → (6) schemdraw+reportlabで1シート1ページのPDFを生成し、pymupdfでPNG化→目視→修正を数周 → (7) PROGRESS/索引/旧docの訂正注記を更新。
- 次: 未確定事項(J402/J403の型式・ピン順と24V供給元、`GND_CTRL_LED`と`GND_CTRL`の結合、Teensy pin 2/9/14の扱い、CANポート数、F205/F206定格)をユーザー判断で確定→`TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`をRev.1へ更新→KiCad転記→`kicad-check`でERC 0件。

## 2026-09-14 (24VアクチュエータCANノード Rev.A仕様固定)

- 中央基板から分離したコンタクタコイル/24V負荷駆動について、`docs/electrical/ACTUATOR_CAN_NODE_REQUIREMENTS.md`を新設してRev.Aの設計境界を固定した。
- MCUは`STM32F303K8T6`（Classic CAN 1MbpsのCAN2には十分、LQFP32）、CANは`TCAN1051VDRQ1`、E228コイル専用低側MOSFETは`IRLML0100TRPBF`、汎用24V低側4chも同MOSFET、DCモーターは`DRV8251ADDA`の保護付きHブリッジ1chを採用した。
- DCモーターchは24V、連続1.5A、短時間3Aに限定し、C620/走行輪や主電流には使わない。CAN timeout、watchdog/reset、E-stopで全出力OFF・明示再アーム必須とした。
- 追加方針: アクチュエータノードは`VIN_ACT=12〜24V`から局所`LMR51606XDDCR` Buckで5V/3.3Vを作る自己給電構成に変更し、中央とのハーネスを`COMM_A/B`のCAN 2線だけにした。コンタクタQ1は、通常はnodeのOUT1、分離時は中央E-stop loopと直接`MOTOR_PWR_EN`を使う`CONTACTOR_DRIVER`になる共用edge blockとした。
- `CONTACTOR_DRIVER`の実装形態を更新: CANノード上で未分離なら通常の`OUT1`、mouse-biteで切り離した場合だけ中央基板用のE228 coil driverになる。切断境界の両側には通常未実装の2.54mm 1x5 through-hole interface padsを置き、中央へ使う時だけpin headerまたは電線をはんだ付けする。

### 次の作業

1. この要件を基にKiCadプロジェクト/回路図を作成し、電源・MCU/CAN・contactor・Hブリッジ・汎用出力を階層化する。
2. E228実コイルでrelease waveformを測り、Q1のflyback diode/TVS最終定数を決める。
3. 使用するDCモーター候補のstall currentを測り、1.5A継続定格内かを判定する。

## 2026-09-14 (KiCadスキル導入・中央基板アーキテクチャ再修正・電源回路ドラフト着手)

- `.claude/skills/kicad-check/SKILL.md`を追加。KiCad ERC/DRCチェックと部品選定を有料プラグイン(ALT TAB Circuit Copilot)なしでkicad-cli+Claude Codeで回す運用に統一。`AGENTS.md`にもCodex向け参照リンクを追記(スキル自動起動はClaude Code専用だが手順書として読める)。
- unit-board/odometry-boardは発注済みのため今回ノータッチ。central-boardに絞って作業。
- **アーキテクチャ変更1**: コンタクタ含む24V/12V機器駆動を中央基板から独立CANノード基板へ分離する方針に変更(2026-07-19・2026-09-12確定分を撤回)。中央基板はE-stopボタン2個の集約・絶縁監視のみ担い、ハードNCループを2pinコネクタ×2でノード基板へ延長する。ノード基板の詳細は未設計。`ARCHITECTURE_DECISIONS.md`・`CENTRAL_BOARD_REV1_CONSTITUTION.md`更新済み。
- **アーキテクチャ変更2**: 中央基板の24V→5V Buck内蔵化(LM76005、2026-09-12確定)を撤回し、外部`SD-25B-5`モジュールで降圧済みの5Vを入力する旧方式に復帰。`ARCHITECTURE_DECISIONS.md`・`CENTRAL_BOARD_REV1_CONSTITUTION.md`更新、`CENTRAL_BOARD_POWER_BLOCK_REV1.md`は冒頭に不採用注記を追加して参考保存。
- 電源回路(XT30入力→TPS259470 eFuse→5V分配)をAI一括生成ではなく1コンポーネントずつのドラフト方式に変更。`hardware/central-board/central-board/modules-generated/`にJ101(XT30)・R105(FAULT pull-up)まで作成。U101(TPS259470)のピン名は初回誤り(TI別eFuse系統と混同)と判明し要修正: パッケージはRPW=10-pin VQFN-HR(HotRod QFN)2x2mm、確認済み実ピンはVIN/VOUT/GND/EN(UVLO)/ILIM/dVdT(SLEW)/FAULT、正確なpin1-10対応は未確認(ユーザーがデータシートをローダーで読んで確認予定)。
- 次: TPS259470の正確なピン配置確認→電源回路ドラフト完成→KiCad GUIで取り込み・実シンボル化。CANノード基板(コンタクタ)の設計は未着手。

## 2026-09-12 (root generated artifact cleanup)

ルート直下の参照なし `.ai_*` 生成物10件を `archive/cleanup-2026-09-12/root-ai/` へ回復可能な移動。CAD・KiCad・BOM・ログ・ソース・仕様、lock、他出力先は変更なし。

## 2026-09-12 (組付け後の差動ステア高応答化計画)

### やったこと

- unit制御、ESP UART入力、中央trajectory coreと既存試験記録を監査し、`docs/control/RESPONSE_IMPROVEMENT_PLAN_2026-09-12.md`へ12チケットの実装計画を作成した。
- 現行UARTでは操舵FFが供給されない点、boot値と7月RAM候補の差、同期UARTログによる周期遅延候補、固定角度摩擦boost、Python/C++のjerk=0非互換を整理した。

### 現在の状態

- 文書のみ変更。制御実装、boot設定、実機状態は変更していない。実機への接続・書込み・試験は未実施。

### 次の作業

- R01の設定/試験metadata、R02の共通応答解析、R03の周期計測から着手し、組付け後の基準を取得する。

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

## 2026-09-07 (駆動4枚 DigiKey発注BOM最終化)

### やったこと

- 駆動モジュール基板4枚（実機3枚＋基板単位の完全予備1枚）について、
  現行KiCad回路図/BOMと電気設計資料から調達BOMを作成した。ODOM基板分は発注済みのため今回の購入数から除外し、組立確認用内訳だけ残した。
- DigiKey Japanの2026-09-07時点の在庫・数量別単価を確認し、必要数＋実装予備を確保しつつ、
  10/25/50/100個の価格境界で総額が下がる品目は境界数量へ最適化した。
- `outputs/differential-swerve-bom-drive-only-20260907/Differential-Swerve_DigiKey-BOM_Drive4_2026-09-07.xlsx`に
  サマリー、統合発注BOM、基板別内訳、数量判断、全品の在庫・価格段階・Footprint/電気仕様監査を収録した。
  税抜概算は11,617.60円、税込参考は12,779.36円（送料・価格変動を除く）。
- DigiKey BOM Manager投入用CSVを
  `output/procurement/digikey-bom-drive4-only-2026-09-07.csv`として作成した。
- 手持ちのSTM32G474RET6、研究室在庫のSTM32F405RGT6、購入済みICM-42688-P breakoutは発注から除外した。
  ODOMのDNP（C15/C17/C23-C26）も購入・実装対象から除外した。
- 欠品している元品について、LM66100DCKR→DCKT、SN74LVC2G17DBVR→DBVTは同一IC/同一外形の
  カットテープ梱包へ切替えた。8MHz水晶は周波数、CL=8pF、ESR=500Ω、3225 4padが一致する
  `FC3BAEBDI8.0-T1`へ切替えた。
- 手持ち連絡を反映し、JST GHの2極横向き、6極横向き、6極垂直を発注CSVから除外した。
  STM32類は当初から発注対象外。
- DigiKey Quick Viewで`BAT54SLT1G`を追加できずDiotec品も在庫表示が不安定だったため、メーカー資料で
  直列2ダイオード、30V、200mA、SOT-23、同一ピン構成を確認したComchip `BAT54S-HF`へ置換した。
  DigiKey品番は`641-BAT54S-HFCT-ND`、発注数は10個（6個との差額1円、確認在庫306,288個）。
  `TLV1117LV33DCYR`も生産中止表示のため、既存SOT-223 footprintと同一ピン配置で、1A、
  セラミック出力コンデンサ対応の`TLV76133DCYR`へ変更した。候補表示されたROHM品はTO-252で
  footprint不一致、NCP1117系は低ESRセラミックでの安定条件が既存回路と一致しないため不採用。
  DigiKey品番は`296-TLV76133DCYRCT-ND`、発注数6個。
  ODOM発注済みの訂正反映後は27発注行、税抜概算11,617.60円、税込参考12,779.36円。

### 現在の状態

- DigiKey発注CSVは27行・310個で、Customer Referenceはすべて`UNIT:`のみ。ODOM品は含まない。
- `SM03B-GHS-TB`だけは確認時に在庫0/繰越注文表示で、形状互換を保証できない代替品は採用していない。
- Excelは式エラー0件を確認し、全6シートをレンダリングしてレイアウト確認済み。
- BOMは基板実装部品を対象とし、相手側ハウジング・圧着端子・ケーブル、PCB、ステンシル、はんだ材料は別手配と明記した。
- KiCad 10.0.4でERCを再実行し、駆動基板は0件。ODOM基板は既存の`74LVC2G17` 3個について
  電源unit C未配置エラー3件＋警告3件が残る（部品数量には影響しないが基板発注前に要修正）。

### 次の作業

1. CSVをDigiKey BOM Managerへ投入し、`SM03B-GHS-TB`の最新納期と全品の最終単価/在庫を確認する。
2. 手持ちMCUに加え、駆動用GH 2極横4個・6極横4個・6極垂直4個を満たすか現物確認してから発注を確定する。
3. 初号機実装後、Fox水晶の発振開始/周波数、CAN、TLV761の3.3V・温度・負荷変動を通電試験する。
4. ODOM回路図のU3/U7/U9に電源unit Cを配置し、ERC 0件を確認してからPCBを発注する。

## 2026-08-01 (DualSense Bluetooth復旧・mini PC入力preview実装)

### やったこと

- Sony DualSense(`4C:B9:9B:8A:C3:07`、VID/PID `054c:0ce6`)をmini PCのRealtek Bluetoothへ
  接続した。保存済みbondの不整合でBlueZがHID接続を`!bonded device`として拒否していたため、
  古いdeviceを削除して新規pair/trust/connectし直した。
- Bluetooth接続後にLinux入力`/dev/input/event19`、`/dev/input/js2`が生成され、triggerを含む
  実イベントを確認した。DualSenseはmini PCへBluetooth/USB直結、ESP32-C3/MCP2515は入力中継に
  使わない構成を確定し、アーキテクチャ決定へ追記した。
- `tools/linux/dualsense_control.py`を追加。VID/PIDとgamepad capabilityによる自動検出、
  Bluetooth/USB共通mapping、radial deadzone、応答curve、R2速度倍率、R1 deadman、切断時zero化を
  モータ/CAN/serial非接続の独立層として実装した。
- `tools/linux/dualsense_web_ui.py`を追加し、接続状態、stick/trigger/button、生成した車体
  `vx/vy/omega`を表示するpreview GUIをport8766で起動した。offline self-checkとunit test 7件は全PASS。

### 現在の状態

- DualSenseは`Paired=yes / Trusted=yes / Connected=yes`、Bluetooth evdev入力も認識済み。
- preview GUIは`http://localhost:8766`で起動中。R1解放時の指令は0で、CAN・USBシリアル・
  モータ出力は未実装のため機体は動かない。
- 既存の単ユニットCAN bench GUIと新previewは別プロセスであり、指令sourceの競合はない。

### 次の作業

1. mini PC-Teensy間のUSB-CDC command/status frameを固定し、sequence/CRCとTeensy受信timeoutを実装する。
2. Teensyへarm/standby/stop状態機械、R1解放時の通常zero、通信断時disable、再接続後の再arm要求を実装する。
3. Teensy CAN3の3輪CAN FD配信とcentral coordinator coreを接続後、主電源OFFでend-to-end試験し、
   接地はハードE-stopを有効にした低速・低加速から開始する。

## 2026-07-31 (GUIへ空走ベスト設定を明示適用)

### やったこと

- ユーザー指示で、3機構の空走試験に合格した共通高応答候補をGUI/RAMへ全項目明示適用した。
  cap/max=300rpm、profile=1800/12000/3000deg系、jerk=0、unit hard guard=4000rpm/s、
  current limit=4500raw、0/60rpm Kp/Ki=120/50、100/150rpm Kp/Ki=140/50、
  高速decel FF=2.5、brake Kp倍率2、wheel accel/decel=1000/500rpm/s。
- 操作感は高トルク・高応答で良好だが、現ウレタンロープ巻きトレッドは本番負荷で摩擦・固定界面が
  先に負ける可能性が高いと確認した。機械的抜け止めを持つ鋳込みウレタンタイヤを次期候補とする。
- 高グリップ化後はwheel回転数と独立オドメトリ車体速度の差から個輪slipを推定し、駆動トルクを
  ramp制限するtraction controlが必要になる可能性を記録した。方式・採用は接地ログ取得後に確定する。

### 現在の状態

- 機構unit3/controller unitId1、GUI port8080起動中、unit disabled、AMT/C620正常。
- GUI/RAMは空走ベスト候補。未計測の接地起動を永続化しないためFlash boot既定60rpmは変更なし。

### 次の作業

1. 接地ラジコン動作では低いwheel指令から開始し、横振れ・current scale・電源状態を確認する。
2. 外部24V/current計測後に高負荷域の採用可否を確定する。
3. ホイール寸法・輪荷重を基に鋳込みウレタンの硬度/厚さ/抜け止め形状を決め、接地ログ後に
   traction controlの必要slip閾値とトルク復帰rampを設計する。

## 2026-07-31 (機構unit3空走回帰)

### やったこと

- 機構unit3へ切り替え、AMT Flash zeroを再校正せず`zero=1503/seq1`のまま段階回帰した。
  controller CAN IDはunitId=1のまま、機構側unit3として記録する。
- 60rpm・wheel=0・正逆90degは2/2実用合格。初回±2deg到達0.350/0.358s、
  overshoot最大3.60deg、terminal最大0.175deg、実peak61.9rpm。
- 120rpm候補をwheel=0/265rpm・正逆90degで4移動し4/4実用合格。初回到達
  0.302〜0.323s、overshoot最大4.22deg、terminal最大0.264deg、実peak93.6rpm。
  wheel=265正方向だけstrict settleが1.240sだったが実用gateは合格した。
- ramp制動付き300rpm設定/current limit4500rawの90deg fullは4/4実用合格。初回到達
  0.210〜0.237s、overshoot最大15.65deg、terminal最大0.176deg、実peak140.4rpm。
- 同設定の170deg fullも4/4実用合格。初回到達0.328〜0.371s、overshoot最大15.01deg、
  terminal最大0.332deg、実peak160.6rpm。全段階で安全停止、AMT/C620脱落、温度上昇なし。
- unit1/2/3の300rpm設定を同じ補間指標で再集計した。90degのfirst-entry平均は
  0.221/0.230/0.219s、170degは0.348/0.338/0.348sで個体差は小さく、空走では個体trim不要、
  共通table継続と判断した。170deg実peakは172.2/173.4/160.6rpmでunit3が約7%低いため、
  接地時の監視項目として残す。

### 現在の状態

- 機構unit3/controller unitId1はdisabled、wheel=0、27/26degC、`fdbkOk=1`、AMT正常。
  Flash校正は`zero=1503/seq1`、CRC正常のまま変更なし。
- GUI cap60rpm、profile=360/3600/2250deg系、unit max60rpm、unit accel600rpm/s、
  current limit4000rawへ安全復元済み。
- 主要ログは60rpm `auto-tune/2026-07-31T12-22-54Z`、120rpm `12-23-13Z`、
  300rpm設定90deg `12-23-32Z`、170deg `12-23-51Z`。

### 次の作業

1. 外部電流/24V計測器導入後に実300rpmの回生peakを測る。
2. 接地試験用の応答・車体横振れgateを定義して低速から再検証する。
3. unit3の接地実peakが他2台より低い場合だけ個体trimを再検討する。

## 2026-07-31 (機構unit2空走回帰・高速到達指標の補間化)

### やったこと

- 機構ユニット切替ではAMTとステア軸の相対原点は変化しないため、再校正は行わず
  `zero=1503/seq1`を維持した。取付向きやカップリングの回転を理由にFlash zeroを更新するという
  先の判断は撤回した。現ベンチのcontroller CAN IDは引き続きunitId=1で、機構側をunit2へ
  切り替えた状態として記録する。
- unit2を60rpm・wheel=0・正逆90degで回帰し2/2実用合格。初回±2deg到達約0.354s、
  overshoot最大3.34deg、terminal最大0.088deg、実peak60.8rpm。
- 120rpm候補をwheel=0/265rpm・正逆90degで4移動し4/4実用合格。初回到達
  0.324〜0.384s、overshoot最大2.81deg、terminal最大0.264deg。strict settleだけ1本が
  0.991sで0.9sを超えた。
- ramp制動付き300rpm設定/current limit 4500rawを90degで4移動し4/4実用合格。
  初回到達0.202〜0.424s、overshoot最大14.85deg、terminal最大0.352deg、実peak142.4rpm。
- 170deg反復で100Hz sample間に±2deg帯を飛び越え、overshoot後の再進入を初回到達と
  誤認する評価不具合を確認した。方向付き誤差が帯境界を横切る時刻を隣接sample間で線形補間する
  よう`unit_auto_tuner.py`を修正し、自己試験へ正負の帯飛び越しcaseを追加した。
- 修正前8移動を再評価すると初回到達worstは0.666→0.371sとなり8/8合格。修正版の正式な
  170deg 4移動も4/4実用合格で、初回到達0.336〜0.340s、overshoot最大13.43deg、
  terminal最大0.195deg、実peak173.4rpmだった。

### 現在の状態

- 機構unit2/controller unitId1はdisabled、wheel=0、27/26degC、`fdbkOk=1`、AMT正常、
  永続faultなし。Flash校正は`zero=1503/seq1`、CRC正常のまま変更なし。
- GUIは安全側cap60rpm、profile=360/3600/2250deg系、jerk=0、unit max60rpm、
  unit accel600rpm/s、current limit4000rawへ復元済み。
- 主要ログは60rpm `auto-tune/2026-07-31T12-15-31Z`、120rpm `12-15-59Z`、
  300rpm設定90deg `12-16-22Z`、補間修正版170deg `12-19-52Z`。

### 次の作業

1. unit3も同じ60→120→300rpm設定の順で回帰し、共通tableか個体trimかを判断する。
2. 外部電流/24V計測器導入後に実300rpmの回生peakを測り、500rpm/s制動制約を再評価する。
3. 接地では空走20deg overshoot gateを流用せず、車体横振れを含む基準を定義する。

## 2026-07-31 (P4・300rpm応答優先コミッショニング)

### やったこと

- Web/中央coreへ加速度state、jerk制限、jerk過渡込み停止距離を実装した。100k/200k deg/s3を
  host testし、中央coreにも同じ軌道生成器と試験を追加した。120rpm実機比較ではlegacy
  jerk=0が±2deg初回到達平均0.303sで最速、200kは0.326sへ遅くなる代わりにworst overshootを
  7.12→5.10degへ低減したため、応答優先値はjerk=0を維持した。
- G474の`SET_CONFIG idx9`上限を2000→4000 axis rpm/sへ拡張し、中央profileより上のhard guardと
  して二重rampを除去した。boot既定600は維持。build/flash/readback MD5一致を確認した。
- 実用gateをユーザー方針に合わせてfirst-entry 0.5s、overshoot 20deg、terminal 1degへ変更し、
  strict 4deg/0.9sは診断として維持。300rpm cap/profile(1800/12000/9000 deg系)をwheel=0/265rpmで
  6移動確認し6/6実用合格。worst first-entry 0.253s、overshoot 19.863deg、terminal 0.528deg。
- 外側angle Pを切った速度mode試験を修正し、CAN STATUS1実角を安全targetへ使い、fresh CAN seed、
  ACTIVE ack、指令rampを追加した。260 axis rpmはrise90 0.158/0.153s、overshoot 0.79/0%で定常到達。
- C620 24V復旧後、300 axis rpmの正負速度stepを実施した。rise90は正負0.174/0.174s、peakは
  303/333 axis rpm、速度overshootは1.04/11.06%で、300rpm実速度への到達自体を確認した。
  ただし4000rpm/sの対称rampで300→0へ急制動した際に電源保護停止をユーザーが確認したため、
  この試行を安全な300rpm完了判定には使わない。
- `unit_steer_mode_id.py`の加速/制動を分離した。制動既定500rpm/s、制動時間後にzero dwellを追加、
  反転は0rpm経由、Disable前にも明示zero rampを完遂する。単方向stepも追加し、高速制動回数を
  1回へ減らせるようにした。self-check、py_compile、diff checkはPASS。
- 改修版で正方向300rpmを1回確認した。rise90 0.174s、peak 300.9rpm、overshoot 0.85%。
  指令は0.595sで300→0、実測はその3ms後に5rpm未満となり、0.25s zero dwell後にDisableした。
  試験中ACTIVE維持、終了後`fdbkOk=1`、AMT正常、永続faultなしで急制動停止の再発なし。
- 現ベンチは24V計測不能と確認した。STATUS3は`0xffff`、G474 ADCは5V専用、C620 CANにも
  入力電圧なし。ユーザー方針で計測器導入は後段とし、260rpm超・無計測時は制動500rpm/s以下を
  強制、外部計測確認時だけそれ以上を許可する。FEEDBACK_OK脱落は即時失敗としてログへ残す。
- 公式C620ガイドではrated 24Vのみで最大連続入力電圧は明示されないため、推測上限を置かず、
  外部計測手順と電源OVP値の記録項目を`docs/testing/UNIT_AUTO_TUNER.md`へ追加した。
- 改修版の負方向300rpmもrise90 0.174s、peak 300.9rpm、overshoot 0.87%、feedback drop 0で完走。
  正負とも500rpm/s停止を確認した。
- 回生をランプで抑える暫定profileとしてcap300rpm、加速12000deg/s2、制動3000deg/s2を評価した。
  170deg・4000rawはwheel=265負方向だけfirst-entry 0.605sで4本中1本不合格。加速中に未飽和要求
  5375raw/適用3934raw、9 sample中7 sample scaleを確認し、電流上限4500rawへ1段だけ進めた。
- 4000/4500rawの170degインターリーブ各4移動は双方実用合格。4500はfirst-entry平均
  0.356→0.344s、settle 0.941→0.888s、実peak 167→183rpm、overshoot 14.66→16.15deg。
  応答優先で4500rawを空走候補とした。4500rawの90deg full 4移動も4/4合格し、first-entry
  平均/最悪0.225/0.243s、実peak141rpm、overshoot最大15.205deg、terminal最大0.175deg。

### 現在の状態

- Flash bin 16064byte、MD5 `42e5be8774fc61f3d4ea87c5901cb290`、zero=1503/seq1保持。
- unitはdisabled、wheel=0、Web UIはport 8080で起動中。`fdbkOk=1`、AMT正常、
  永続faultなし。角度約315.9deg、zero=1503/seq1保持、GUI capは安全側60rpm、RAM current limitは
  4000rawへ復元済み。
- unit 1浮上・wheel=0では300rpmの速度能力と500rpm/s安全停止波形を各1回確認済み。
  旧4000rpm/s急制動は禁止し、unit 2/3・接地・実電源条件での採用判定は別途行う。

### 次の作業

1. unit 1空走では4500raw/ramp制動候補を追加反復せず、次はunit 2/3または接地へ移る。
2. 電流/電圧計測器導入後に24V peakと電源OVPを測り、500rpm/s暫定制約を再評価する。
3. 接地では20deg空走gateを流用せず、車体横振れを含む基準で再設定する。

## 2026-07-31 (P3a明示加速度を実機化・150rpm段はP4へ継続)

### やったこと

- Classic CANベンチ用`SET_TARGET_ACCEL_FF(0x160+id)`を追加し、Webの200Hz profile加速度を
  G474へ明示送信した。freshな明示値を受信時刻差分より優先し、200ms途絶時は旧差分へ戻る。
  診断bitとauto tuner CSVを追加し、運動中76/76を含む125/125 sampleで明示経路適用を確認した。
- 明示加速度前提で120rpm profile decel=1800/2000/2250deg/s2を各4移動比較。全12移動が
  実用合格し、2000は初回±2deg平均0.313s、overshoot最大5.625degで総合最良だった。
- 制動Kp倍率を0/60/100/150rpm knotで連続補間できるよう拡張した。150rpm段で高速倍率
  3.0/3.5/4.0を比較したが全候補不合格。最良3.5でもovershoot 10.723deg、4000raw飽和、
  実peak 100.7rpmとなり、Kp強化では150rpm到達と制動を両立できなかった。

### 現在の状態

- Flashは明示加速度+速度別制動Kp版(MD5 `448c6ffa65d452268efcd94da6eb68cb`)。
  boot既定は安全側60rpm/倍率1のまま、校正zero=1503/seq1/CRC正常。
- RAM/Webは合格済み120rpm packageへ復元し、明示加速度前提のprofile decelだけ
  2250→2000deg/s2へ更新。unit disabled、wheel=0、約306.0deg、28/26degC。
- Web UIはport 8080で起動中。主要ログは`auto-tune/2026-07-31T11-04-58Z`、
  `11-06-00Z`、`11-08-44Z`、`11-09-08Z`。

### 次の作業

1. P4として中央/Web軌道へ加速度stateとjerk制限を追加し、制動距離へjerk過渡を含める。
2. ユニット内steer rpm rampを通常profile生成からhard guardへ変更し、中央との二重rampを除去する。
3. 4000rawを維持して実peak150rpmを再評価し、overshoot 8deg以下成立後に200rpmへ進む。

## 2026-07-31 (実用到達基準へ変更・120rpm級高応答候補を確立)

### やったこと

- 低速の微小振動を含む厳格settle時間をgain探索の合否から外し、全試行で安全停止なし、
  ±2deg初回到達0.50s以下、overshoot 8deg以下、終端誤差1deg以下を実用基準に確定した。
  旧overshoot 4deg/settle 0.9sは診断列として維持する。
- 制動phaseだけscheduled steer Kpを増幅する`steer_brake_kp_multiplier`を実装。
  `SET_CONFIG idx47`、範囲1〜4、既定1で従来互換。倍率2.0が絶対角間の再現性を含め最良だった。
- 120rpm cap、Kp/Ki=140/50、加速/制動FF=0.5/2.5、brake Kp倍率2.0、
  profile=720/5400/2250を12移動確認。±2deg到達平均/最悪0.301/0.313s、
  実steer peak 119.9rpm、overshoot最大7.647deg、終端誤差最大0.176degで12/12実用合格。

### 現在の状態

- unit 1空走の高応答候補は上記120rpm package。安全停止なし、最大指令/実測電流
  3348/2470raw、最高28degC。current scale最長30msがあるため電流上限は4000rawを維持する。
- Flashにはbrake Kp機能を実装済み(MD5 `63b59d173a7bdef4bc152761b0bb75`)だが、
  boot既定は安全側60rpm/倍率1.0のまま。現在RAM/Webは高応答候補を残し、unitはdisabled、wheel=0。
- 確認ログは`firmware/logs/auto-tune/2026-07-31T10-53-38Z`。

### 次の作業

1. torque scaling 30msが加速不足か制動時の意図的飽和かをphase別に分解する。
2. unit 2/3と接地状態で120rpm packageを確認し、共通table/個体trimを判断する。
3. 接地でも実用基準を満たした後にboot既定を60→120rpmへ変更する。

## 2026-07-31 (P2連続gain schedule実機評価・100rpm制動profile選定)

### やったこと

- 0/60/100/150rpmの連続gain tableを実制御へ接続し、legacy scalar設定は全band同値を維持、
  `SET_CONFIG idx27..46`で各knotのKp/Ki/加速FF/制動FF/Kawを個別設定できるようにした。
- 速度mode同定を100/150rpmへ拡張。角度目標を速度指令から積分追従させ、STATUS3 ACTIVE脱落を
  即時検出するよう修正した。Web UIとの指令競合も起動時に拒否する。
- 150rpm速度stepでKp/Kiを比較し、140/50を高速band候補に選定。160/50は負方向peakが
  32.3%へ悪化し、低ゲイン70/20は帯域低下に対して改善が小さかった。
- 100rpm閉ループでは速度PI/FF/外周Pよりprofile減速開始が支配的と確認。decelを
  2250から1450deg/s2へ前倒しし、確認12移動でovershoot最大3.252deg、平均settle 0.831s、
  最悪0.998s。全12移動がovershoot gate、安全/飽和なし、settle gateは9/12だった。
- DIAGが補間後gainでなく旧scalar値を送っていた不具合を修正し、実schedule最大約121rpm、
  Kp最大140、制動FF最大2.5をCSVで確認した。

### 現在の状態

- 高速候補は`100/150rpm Kp/Ki=140/50、accel/decel FF=0.5/2.5、profile decel=1450`。
  overshootは合格したがworst settleが0.9s gateを約0.1s超えるため、Flash既定には未採用。
- 実機runtimeはKp/Ki=120/50、max60rpm、unit accel600rpm/s、FF=0.5/0.5、Kaw=0、
  Web profile=360/3600/2250、cap60rpm、time scale1へ明示復元済み。
- unit 1はdisabled、wheel=0、角度約232.12deg、温度28/26degC、zero=1503/seq1/CRC正常。
  Web UIはport 8080で起動中。現Flash MD5は`2297433648339d3359bc97be64b96a67`。

### 次の作業

1. 1450deg/s2候補のsettle外れ値を絶対角・方向別に分解し、単体浮上への過適合を避けて
   unit 2/3または接地条件で同じ表を評価する。
2. 3台共通でovershoot<=4degかつworst settle<=0.9sを満たすまで高速表を既定化しない。
3. 収束外れ値がprofile/gainで再現制御できなければ、P3の明示target accelerationとmodel FFへ進む。

## 2026-07-31 (応答指標分離・Kawインターリーブ比較で既定0を維持)

### やったこと

- auto tunerへ初回±2deg/settle band進入、初回目標通過、±2deg進入後の再収束時間を追加し、
  初動応答とovershoot後の振り返しを分離した。
- `--compare-values`を追加。各候補へ同じ絶対角対、正逆、wheel=0/265rpmを均等配分し、
  毎試行後に通常STOP/DisableしてPI/observer状態をリセットするインターリーブ比較とした。
- Kaw=0/1/2を1反復12移動でscreen。Kaw=1は平均settle 0.684s、worst 0.797sと良好だったが、
  初回±2deg進入は0.326sでKaw=0の0.288sより遅く、改善は再収束時間の短縮だった。
  最大overshoot 5.977degで4deg gateは不合格。
- 独立seedの2反復24移動で確認したところ、平均settleはKaw=0/1/2で
  0.689/0.757/0.924s、初回±2deg進入は0.292/0.318/0.320s、最大overshootは
  5.273/13.447/12.217deg。Kaw=1の優位は再現せず、全候補がgate不合格だった。

### 現在の状態

- P1 back-calculationはコード・telemetryを残すが、単独で再現する応答改善は得られずKaw=0を維持。
- Kp/Ki=120/50、max=60rpm、unit accel=600rpm/s、FF=0.5/0.5、Kaw=0/0、
  profile=360/3600/2250、time scale=1へ復元済み。
- unit 1はdisabled、wheel=0、角度約179.74deg、温度28/27degC、AMT/C620正常。
- ログは`firmware/logs/auto-tune/2026-07-31T09-58-59Z`と`2026-07-31T10-00-21Z`。

### 次の作業

1. P2の0/60/100/150rpm連続gain tableを全knot同値から実装し、境界連続性をhost testする。
2. 低速knotはKaw=0を維持し、高速knotのKawは速度schedule・制動FFと組み合わせて評価する。
3. 総合scoreだけで採否を決めず、overshoot/worst settle gate通過後に初回進入時間で比較する。

## 2026-07-31 (P1 back-calculation反復評価・Kaw採用見送り)

### やったこと

- P1 back-calculationの追試として、Kaw=`3 -> 0 -> 4 -> 1 -> 2`の順で、wheel=0/265rpm、
  正逆90deg、複数絶対角を評価した。Kaw=0/1/2/4は各8移動、Kaw=3は設定上のrounds既定値により
  24移動となり、合計56/56で収束、安全停止・温度異常は0件だった。
- Kaw=0/1/2/3/4の平均settleはそれぞれ0.793/0.854/0.847/0.857/0.888s、最悪settleは
  0.938/1.573/1.925/1.432/1.179s、最大overshootは10.02/10.72/9.84/12.57/8.00deg。
  予備2移動で良好だったKaw=2は再現せず、Kaw=0のworst settleを上回る候補もなかったため、
  Flash既定化と60rpm採用回帰は見送った。
- `samples.csv`で各試験の`scheduled_kaw`が指令値と一致し、Kaw>0ではback-calculation補正が
  実際に発生していることを確認した。設定未反映ではなく、絶対角・方向・wheel回転による
  ばらつきがKaw単独の効果より大きい結果と判断した。
- 試験後、Kp/Ki=120/50、max=60rpm、unit accel=600rpm/s、FF=0.5/0.5、Kaw=0/0、
  current limit=4000、profile=360/3600/2250、time scale=1へ明示復元した。

### 現在の状態

- P1コード・telemetry・host testは維持するが、Kaw既定値は0のまま。今回の結果では採用候補なし。
- unit 1はdisabled、wheel=0、角度約171.30deg、温度30/29degC、AMT/C620正常。
  zero=1503/seq1/CRC正常。Web UIはport 8080で起動中。
- 追試ログは`firmware/logs/auto-tune/2026-07-31T09-45-01Z`、`09-45-54Z`、
  `09-46-24Z`、`09-46-51Z`、`09-47-20Z`。

### 次の作業

1. Kaw候補を候補単位の連続バッチではなく、同じ開始角・方向の対ごとにインターリーブして
   再評価できる試験手順へ変更し、時間順・機構摩擦の偏りを減らす。
2. wheel=0/265rpm、方向、到着絶対角ごとに飽和残差・補正量・外れ値を分解し、Kaw単独でなく
   制動FF/速度scheduleとの組合せで評価すべきか判断する。
3. 再現する候補が得られるまでKaw=0を維持し、60rpm回帰・Flash既定化は行わない。

## 2026-07-31 (高速ステアP0 telemetry完了・P1 back-calculation予備A/B)

### やったこと

- 将来のgain schedule用に`max(|steer command|, |observer rpm|)`の10ms LPFを並走計算し、
  scheduled gain、共通scale前後電流、残差、連続飽和時間、制動phaseを制御出力へ追加した。
  現行Classic CANベンチでは`0x1B0+id`の4page診断としてWeb UI/auto tunerへ接続した。
- 60rpm、wheel=0/265、正逆4移動で4/4収束。平均0.742s、最悪0.938s、overshoot最大4.043degで
  従来12移動の平均0.802s/最悪1.391s/最大4.571degに非劣化。未飽和時の残差0も確認した。
- 共通current scale後の残差を次周期の積分へ戻すsteer/drive別back-calculationを実装。
  `SET_CONFIG idx25/26`で0〜20/s変更可能、既定0は従来互換。host test/ARM build/Flash済み。
- 150rpm級条件でsteer Kaw=0/2/4を正逆各1回予備比較。Kaw=0の最大overshoot 11.426degに対し、
  Kaw=2は3.340deg、Kaw=4は3.867deg。Kaw=2は2/2 deadline内だったが試行不足のため未採用。
- 詳細引継ぎを`docs/control/HIGH_SPEED_STEER_HANDOFF_2026-07-31.md`へ作成した。

### 現在の状態

- P0完了、P1はコード完成・予備A/Bまで。Kaw採用値の反復検証が未完了。
- Flash bin MD5 `5b8ec2aedcf418b7887c6f4da76801f3`。unit 1 zero=1503/seq1保持。
- runtimeはKp/Ki=120/50、max60rpm、accel600rpm/s、FF=0.5/0.5、Kaw=0/0へ復元。
  disabled、wheel=0、温度27/26degC、AMT/C620正常。Web UIはport 8080で起動中。

### 次の作業

1. Kaw=0/1/2/3/4をwheel=0/265rpm、正逆・絶対角を分散して各最低6移動再評価する。
2. Kaw=2前後が再現すれば60rpmを12移動回帰し、Flash既定への採否を決める。
3. P1確定後、全knot同値から0/60/100/150rpm連続gain tableを実装する。

## 2026-07-31 (100rpm超の実機評価・連続ゲインスケジューリング計画を確定)

### やったこと

- unit 1をwheel浮上・正逆90degで60〜156rpmまで段階評価した。60rpm既定は12移動平均
  0.802s/overshoot最大4.57deg、100rpmは平均0.789s/最大6.68deg。100rpmで
  `Kp=160/Ki=50/decel FF=1.5`は4移動平均0.696s/最大3.78degまで改善した。
- profile peak 134〜137rpmでは実速度145〜156rpmへ到達した一方、overshootは10.20〜14.77deg。
  4000raw未満でも最大14.77degが発生し、FFを強めて4000rawへ飽和させると反動が悪化したため、
  高rpm到達能力や電流上限より減速位相・積分残りが現在の律速と判断した。
- `docs/control/HIGH_SPEED_STEER_GAIN_SCHEDULING_PLAN.md`を新設。observer/reference速度の
  最大値を10ms LPFし、0/60/100/150rpm knot間でKp/Ki/加速・制動FF/Kawを連続補間する。
  telemetry、back-calculation、速度mode同定、明示加速度FF、jerk制限軌道の順に実装し、
  電流は加速中の不足が計測された場合だけ4000→4500→5000→5500→6000rawと段階評価する。
- 高速試験に必要なWeb UI/auto tunerのrpm・加減速レンジをhard包絡内へ拡張し、Enable後は
  STATUS3 ACTIVEを確認してから動作を始めるようにした。試験後は既定60rpm、Kp/Ki=120/50、
  accel limit=600rpm/s、FF=0.5/0.5へ戻した。

### 現在の状態

- unit 1のFlash内容はAMT原点保存済み採用版のまま。runtime設定は60rpm採用値へ復元済みで、
  motor disabled、wheel=0、温度28/27degC、AMT/C620正常。
- 100rpmは固定PIでも改善余地があるが、120〜150rpm域は固定PI/固定FFを電流だけ増やしても
  安定な制動と短い収束を両立できない。高速化の正本は上記実装計画とする。

### 次の作業

1. schedule rpm/gain、未飽和・適用電流、飽和残差/時間、制動phaseのtelemetryを追加する。
2. 共通current scale後の実適用値を使うback-calculation anti-windupを4000raw固定で実装する。
3. 速度mode単体同定後に0/60/100/150rpm連続scheduleを導入し、60rpm非劣化から段階検証する。
4. unit 2/3でも同じ試験を行い、共通tableは3台の最悪値、個体trimは再現する差だけに限定する。

## 2026-07-31 (AMTソフトウェア原点をFlash保存・実機適用)

### やったこと

- G474REの最終2KiB Flashページ(`0x0807F800`)をリンカでファーム領域から分離し、
  AMT生カウントのCRC32付き24byteレコードを追記保存する実装を追加した。通常保存は消去せず、
  magic/version/CRC/commitを検査して最新sequenceを選ぶため、書込み途中でも直前値を保持する。
- `UNIT_CTRL`の`CALIB_SAVE_ZERO/CLEAR/PING`と`CALIB_RESULT(0x1C0+id)`を実装。
  保存/消去はdisabled、AMT/C620 fresh、両モーター出力軸1rpm以下でだけ許可する。
- 単ユニットWeb UIへ原点保存・状態読出し・確認付きクリアと、保存count/raw count/CRC/sequence表示を追加。
  保存成功時は次回Enable前のGUI目標も0deg/0rpmへ再シードする。
- ユーザーが機械原点へ合わせた実機unit 1で、生count `1503`をsequence `1`として保存。
  表示が`132.100deg`から`0.000deg`へ変わり、CRC errorなし。MCU reset後もboot時
  `valid=1 zero=1503 seq=1`、CAN/VCP角`0.000deg`を確認した。

### 現在の状態

- unit 1はAMT原点校正済み。Web UIは`http://localhost:8080`で起動中、モータはdisabled、
  wheel=0、AMT/C620正常。保存ページはsequence 1で空きあり。
- unit 2/3は同じ機械基準姿勢で個別に保存する必要がある。
- 正逆転最短化を使うため個々のステア実移動は最悪90deg。全輪共通原点からの純旋回は
  この120deg配置では`+60/0/-60deg`で表現できる。

### 次の作業

1. unit 2/3を接続し、各ユニット固有のAMT raw countを同じ手順で保存・reset保持確認する。
2. 現在の60rpmコミッショニング上限を、wheel=0で100→150→200→300 axis rpmと段階評価する。
   差動のhard包絡(純操舵約341rpm)は残し、wheel速度に応じて動的に下げる。
3. 3輪接地後、中央のflip最短化、共通desaturation、`PRESTEER→DEPART`を確認する。

## 2026-07-31 (単体の過適合を止め、Teensy 3輪協調制御コアへ移行)

### やったこと

- 150deg到着の1.4166s外れ値を追加追試する準備まで進めたが、3ユニットの個体差と接地摩擦が
  支配的という実機条件を踏まえ、単体浮上・特定角度への追加チューニングを中止した。
  Web UIはEnable前に終了し、ユニットは一度も駆動せずdisableのまま維持した。
- `central_firmware/`を新設し、Teensy固有I/Oから分離したC++11の3輪協調制御コアを実装した。
  車体twist/微分から3輪のsteer連続角、wheel rpm、steer rate FF、wheel accel FFを同時算出する。
- flipは中央だけが判断し、10degヒステリシス付き・実wheel 30rpm以下に限定。停止特異点では
  直前steer角を保持する。3輪の最悪motor-mode要求に合わせ、planned 422.1rpm包絡へ全輪を
  同一scaleで収めるため車体指令方向を維持する。
- 中央プロファイル完了に加え、新指令後に各STATUS3の`MOTION_SETTLED=0`を一度確認してから
  全3輪Highになった場合だけ完了する集約器を実装した。古いHighや1輪の通信staleでは完了しない。
- 直進、純旋回、停止角保持、低速flip、高速flip禁止、共通デサチュレーション、全輪settledの
  ホスト試験を追加し全件PASS。ユーザー確認により3ユニットは半径0.250mの円上へ120deg等配と
  確定。センサーモジュール搭載辺のunit 1/3を`+Y`側、unit 2を`-Y`側とし、座標を
  `(-216.5,+125)/(0,-250)/(+216.5,+125)mm`へ固定する設定関数を追加した。車輪半径は
  公称径65mmから0.0325mへ確定し既定設定へ反映。接地後は実効半径で上書き可能とし、半径が
  0以下なら全出力0で`false`を返す。

### 現在の状態

- 単ユニットfirmwareは前回採用版のまま。追加実機動作・Flash変更なし、disabled。
- 中央コアはホスト上で成立。Teensy 4.1のCAN/USB/安全I/Oにはまだ接続していない。
- 90deg収束は現プロファイル理論約0.38sに100ms settled dwellが加わるため、判定上の理想下限は
  約0.48s。実測中央値約0.71〜0.75sとの差を単体ごとに詰めるより、中央`PRESTEER`で出発待ちを
  隠し、3輪接地の最遅ユニットへ同期する方針とした。

### 次の作業

1. Teensy 4.1へCAN3 FlexCAN_T4アダプタと100Hz twist profilerを実装する。
2. 3ユニットを接地して共通scale、全輪settled、`PRESTEER→DEPART`を実機検証する。
3. 既知距離の直進から接地変形を含む実効車輪半径をユニット別に校正する。

## 2026-07-31 (observer速度でfriction FFを整形し収束時間を約21%短縮)

### やったこと

- observer推定速度の制御利用をA/Bした。終端速度ダンピングはwheel=265rpmで基準平均
  0.752sに対し10ms候補0.854sへ悪化したため、実装から除去した。
- wheel=0のbreakaway用friction FF=200rawを、observer軸速度0rpmで全量、10rpmで0まで
  線形に減衰する方式を実装した。静止時の突破力は維持し、移動中の余分な電流だけを抜く。
- 触れていない90deg・絶対角4点の12対12 A/Bで、従来一定FFは平均0.9555s/中央値0.7800s/
  最悪2.0402s、速度減衰FFは平均0.7570s/中央値0.7190s/最悪0.9747s。平均20.8%短縮、
  最悪52.2%短縮。`SET_CONFIG idx24`で減衰完了軸rpmを0〜100rpm変更可能にした。
- 既定10rpmへ変更してFlash後、wheel=0を12移動、wheel=265rpmを8移動し20/20収束。
  wheel=0平均0.7636s/最悪1.4166s、wheel=265平均0.7735s/最悪0.9726sだった。

### 現在の状態

- 採用firmwareをFlash済み(bin MD5 `5a48f40f44db9f6f19a6faee545043a3`)。
- observerはfriction FFの速度スケジュールにだけ使用。角度P、settled、安全判定は従来のまま。
- 通常STOP/disable後idle、最終角59.854deg、wheel=0、AMT/C620正常。
- A/Bログは`firmware/logs/webui-2026-07-31T08-18-51Z.log`、採用版回帰は
  `firmware/logs/webui-2026-07-31T08-21-54Z.log`。

### 次の作業

1. 残った1.4166sの絶対角150deg到着外れ値を、角度依存機構抵抗とobserver速度/PI積分で解析する。
2. wheel=1〜29rpmのfade遷移域と接地・3輪条件を回帰し、10rpm閾値を必要なら再調整する。
3. observer角を角度P、安全、settledへ接続するのはfault試験とinnovation閾値確定後に行う。

## 2026-07-31 (P1.5 相補observerを診断専用で実装・実機確認)

### やったこと

- G474の1kHz局所ループへ、2ms LPF後のmotor steer-mode速度を高周波予測、AMT22絶対角を
  低周波補正に使う相補observerを追加した。補正時定数は既定50ms、初回/reset後はAMTで
  再シードし、innovationはshortest angle errorで0/360deg境界を連続に扱う。
- 推定角`obsA`、推定軸rpm`obsR`、AMT innovation`obsE`をVCP/Web UIへ追加し、自動チューナの
  `samples.csv`にも保存するようにした。`SET_CONFIG idx23`で0〜1sをruntime変更できる。
- observerは現段階では診断専用とし、既存の角度P、`MOTION_SETTLED`、安全停止判定へは
  接続していない。専用ホスト試験で初回seed、wrap、ドリフト補正、tau=0、resetを固定した。
- build/flash/verify後、wheel=0と実wheel=265rpm保持で330↔30degのwrap通過を含む実機回帰。
  全移動が収束し、生VCP 292点でinnovation最大2.172deg/p95 0.954deg、静止時observer-AMT差
  p95 0.086deg。±360degスパイクなし。idx23を20msへ変更後50msへ復元する応答も確認した。

### 現在の状態

- observer入りfirmwareをFlash済み(bin MD5 `36452ab63553e842c338604a8c802cdb`)。
  runtime補正時定数は既定50msへ復元済み。
- 実機は通常STOP/disable後idle。最終角30.146deg、wheel=0、AMT/C620正常。
- observerは既存制御へ影響しない診断段階。実機ログは
  `firmware/logs/webui-2026-07-31T08-05-04Z.log`。

### 次の作業

1. 接地・3輪条件でinnovationの正常p95/p99と角速度推定誤差を計測し、滑り/バックラッシュの
   診断閾値と連続時間条件を決める。
2. 閾値を決めるまではobserverを制御・settled・安全判定へ接続しない。
3. P1.2 back-calculation anti-windup、P0.1連続unwrap角、CAN FD軌道は従来計画どおり別工程。

## 2026-07-31 (引継ぎ継続: 角度依存stall回帰完了・60rpm段階採用)

### やったこと

- 既存の角度依存friction補償を、10deg刻み境界42試行とwheel=75/265rpm各24試行で回帰し、
  合計90/90収束。15rpmはステア自体0.049degへ収束したが既知のdrive stick-slipで総合判定外。
- ロードマップ手順2の加速/制動FF 0/0.5/1.0を比較。絶対角4点を含む再試験で候補値に
  外れ値が残ったため、既定0.5/0.5を維持した。
- 手順4を継続し、ユニット側上限も含めた60rpm試験を26/26合格としてcommissioning既定へ
  昇格。80rpmは14/14収束したが60rpmより遅くなったため不採用、100rpmは未試験。
- firmware既定`steer_max_rpm=60`、Web既定cap=60rpm/rate=360deg/sへ更新しflash/verify。
  runtime `SET_CONFIG`上限はhard包絡相当341.1rpmへ拡張した。
- 自動試験ツールの旧friction FF=0・旧time scale=2復元バグを修正し、採用済み構成を
  試験後に壊さないようにした。詳細数値とログ場所は`firmware/PROGRESS.md`参照。

### 現在の状態

- 実機は60rpm既定の新firmwareで回帰14/14後、通常STOPしてidle。温度28/27degC。
- angle補償境界とwheelカップリングは解消確認済み。60rpm段階まで採用、80rpmは保留。
- 未コミット変更と本セッションの自動試験ログが残っている。

### 次の作業

1. 80rpmで増えた収束外れ値を内周追従・加速/制動FF・絶対角別に切り分ける。
2. 接地/3輪が利用可能になればロードマップ手順5へ進む。
3. P1.2 anti-windupはcurrent scalingを安全に再現する専用試験後に実装する。
4. P0.1連続unwrap角、CAN FD時刻付き軌道、Teensy中央実装は保留。

## 2026-07-31 (セッション総括: 実機収束をtime_scale理論値まで短縮・角度依存stall解消)

### やったこと

本セッションは前半でP0.3(mode包絡射影)・P1.4(連続デッドバンド)をコードレビューで
実装し、後半は実機(can0接続・ホイール浮上)へ長時間介入して収束性能を追い込んだ。
詳細な試行ログ・数値は`firmware/PROGRESS.md`の各セクション参照。

- P0.3/P1.4を実装・flash。wheel=0/265/600/1000/1200rpmの回帰で健全性確認。
- Kp=60/Ki=100を開ループstep応答の良さから一度flashしたが、closed-loop MOTION_SETTLED
  A/Bで明確な悪化(1.1-1.2s→1.8-3.7s)と判明し即座に120/50へ復元。**教訓: inner loop
  ゲインは開ループ応答だけで採否を決めず、必ずclosed-loop指標で検証する。**
  同日中に別件で`unit_bench.py`の即時disableがDCバス電圧スパイクを起こす事故が発生し
  (ユーザー指摘で発覚)、減速→disableの安全策を追加した。
- telemetry診断で間欠非収束の原因(commanded currentがbreakaway電流の半分程度しかなく
  純積分の立ち上がりを待っていた)を特定。wheel依存テーパ付きfriction FF=200を実装・flash
  し、wheel=0のstallを解消(wheel≠0は無影響)。
- ロードマップ「time scale段階縮小」を実機で完遂: 2.0→1.5→1.25→1.1→**1.0(理論値
  そのもの)** を複数絶対角・複数wheel rpmで34/34+追加trialすべて成功させ、既定値を
  1.0へ格上げした。
- mode ID(速度ループ単体同定)をwheel=0のみからwheel=265/600/1000/1200rpmへ展開
  (`unit_steer_mode_id.py --wheel-rpm`を新規実装)。wheel≠0では現行ゲインで良好・
  対称であることを確認し、非対称・非収束はwheel=0近傍に集中していると裏付けた。
- commissioning cap(40→60rpm)の動的化に実は入力側の固定クランプが残っていて
  無効化されていたバグを発見・修正。修正後cap=60は動作確認(15/16)したが、既定は
  40のまま据え置いた。
- **8方向×3往復(48試行)で間欠stallの角度依存性を定量化し、90-225deg帯への明確な
  偏りを実測で特定。** ユーザーが物理点検し、3Dプリント部品の積層継ぎ目の出っ張りが
  原因と判断(機構修正はせず制御で吸収する方針)。角度80-235deg(5degランプイン/アウト)
  でfriction FFを最大2倍にブーストする位置トリガー式補償を実装・flashし、**同じ
  8方向×3往復で48/48に完全解消**(修正前45/48)。

### 現在の状態

- Flash済みfirmware: Kp=120/Ki=50/tau=2ms、wheel依存テーパ付きfriction FF=200、
  角度依存(80-235deg)ブースト最大2倍、P0.3(mode包絡射影)、P1.4(連続デッドバンド)。
- `unit_web_ui.py`既定`trajectory_time_scale=1.0`(旧2.0)、`steer_commissioning_cap_rpm`
  は40のまま(動的化バグは修正済み)。
- `unit_bench.py`・`unit_steer_mode_id.py`とも、wheel≠0時の安全な減速→disableに対応。
- ハードウェアはidle・健全。本セッションの実機トライアル総数は概算250件超。
- 未コミット。変更ファイル: `firmware/src/control/unit_controller.c`、`firmware/src/main.c`、
  `tools/linux/unit_web_ui.py`、`tools/linux/unit_bench.py`、`tools/linux/unit_steer_mode_id.py`、
  `PROGRESS.md`、`firmware/PROGRESS.md`。

### 次の作業

1. より細かい角度刻み(10-15deg)でバンド境界(80/235deg)の精度を追い込む
   (このセッションでは着手直前で中断)。
2. wheel≠0での角度依存帯とのカップリング確認。
3. 他3基が同じ3Dプリント部品を使う場合、同様の角度依存点検・補償の要否を確認する。
4. ロードマップ手順2(加速・制動FF同定)、手順4(commissioning cap 60→80→100段階拡張、
   角度依存stallの目処が立ってから)、P1.2(back-calculation anti-windup)、
   P0.1(連続unwrap角)・pre-steer状態遷移は保留のまま。
5. Teensy中央実装は未着手(ドキュメントのみ)。

## 2026-07-31 (実機介入: mode包絡射影flash・stall原因特定・テーパ付きfriction FF採用)

### やったこと

- 前セクションのP0.3/P1.4実装後、実機(can0接続・ホイール浮上済み)へ直接介入し、
  `unit_steer_mode_id.py`で外周を切ったwheel=0 steer速度step/PRBSを70+試行実施した。
  Kp=60/Ki=100が開ループでは0% overshootの良好な候補と判明。
- Kp=60/Ki=100をmain.c既定へ反映しflashしたが、`unit_web_ui.py`のMOTION_SETTLED
  (製品契約のclosed-loop指標)でA/B検証したところ**明確に悪化**(1.1-1.2s→1.8-3.7s、
  1回未収束)と判明し、即座にKp=120/Ki=50へ復元・再flash・再検証した。
  教訓: inner loopゲインは開ループstep応答だけで採否を決めず、必ずclosed-loop
  MOTION_SETTLEDで検証してから採用する。
- 5-6回に1回起きる間欠非収束(0.5deg強で数秒粘る)をtelemetryで直接診断。
  commanded current(~450raw)が既知のbreakaway電流(850-950raw)を大きく下回ったまま
  `steer_min_rpm=0`で床が無く、純積分だけでbreakawayへ到達するのを待つ構造が原因と特定した。
- 定数Coulomb FF(既存の`steer_friction_ff_current`)を再検証。wheel=0のstallは解消するが
  wheel=265rpmの収束を1.1-1.4s→2.4-4.0sへ悪化させるトレードオフを確認(過去の不採用判断と
  整合)。`unit_controller.c`へ`target_wheel_rpm`30rpmで0まで線形テーパするロジックを追加し、
  wheel=0近傍だけに効かせる設計へ変更。wheel=0で14/14 stall解消、wheel=265/600rpmは無影響
  (1.18-1.59s)を確認してflash採用した。
- 実機介入中に重大インシデントが1件発生: `unit_bench.py run`がduration経過後
  `UNIT_CTRL disable`を無条件即送信する実装で、wheel=600-1200rpmのフル回転中に繰り返し
  切断したところ、ユーザーから「制動が急すぎて電圧上昇で電源落ちる」と警告を受けた。
  `unit_bench.py run`へ減速→disableの安全策(`--wheel-decel-rpm-per-s`等)を追加し再発防止。
  ハードウェア損傷は確認されていない(idle・feedback OK・温度正常に復帰)。詳細は
  `firmware/PROGRESS.md`。

### 現在の状態

- Flash済み既定値: Kp=120/Ki=50/tau=2ms(従来値のまま)、`steer_friction_ff_current=200`
  (新規、wheel 30rpm以上でテーパアウト)、P0.3(mode包絡射影)・P1.4(連続デッドバンド)込み。
- wheel=0/265/600(/一部1000/1200)で実機A/B・回帰とも良好。ユニットはidle・健全。
- `unit_bench.py`にwheel≠0時の安全な停止手順を追加済み。

### 次の作業

1. wheel=1000/1200rpmでのfriction FFテーパ後の回帰を実機確認する。
2. 絶対角を変えた反復試験で、残る間欠変動(0.5deg弱で数百ms)の統計を取る。
3. `docs/control/CENTRAL_COORDINATED_CONTROL.md`のロードマップ手順3(time scale 2.0→1.5→…→1.0)
   へ進む。
4. P0.1(連続unwrap角)・pre-steer状態遷移・P1.2(back-calculation anti-windup)は
   引き続き保留(理由は`firmware/PROGRESS.md`参照)。

## 2026-07-31 (P0/P1実装: mode包絡射影・動的commissioning guard・連続デッドバンド)

### やったこと

- ユーザーがwheel=0外周切りのsteer mode速度step/PRBS同定(`unit_steer_mode_id.py`)を
  実機で実施中の並行作業として、実装計画のP0/P1項目をコード側から自走で進めた
  (詳細は`firmware/PROGRESS.md`)。いずれもfirmwareは書き込みまで、Web UIは再起動まで
  現在進行中の実機テストへは影響しない変更。
- **P0.3 mode要求の包絡射影**: `unit_controller.c`の「steerを先にclampしdriveが残りを
  受け取る」非対称スキームを、`|steer_mode|+|drive_mode|<=motor_max_rpm`への共通scale射影
  へ置き換えた。両モード要求の比(=指令方向)を保ったまま469rpm diamondを守る。
  通常のwheel=0/265rpm試験のような非飽和域では無変化(469rpm予算に対して十分小さいため)。
- **固定40rpm上限→動的commissioning guard**: `tools/linux/unit_web_ui.py`の
  `steer_rate_available_dps()`にNoneで無効化できる`commissioning_cap_rpm`引数を追加し、
  `AppState.steer_commissioning_cap_rpm`(既定40rpmのまま、`/api/set`で変更・null化可能)
  経由でGUI/API双方から段階拡張できるようにした。既定挙動・self-check・240dps上限は変更なし。
- **P1.4 連続デッドバンド整形**: `unit_controller.c`のangle P項を、deadband境界で0へ不連続に
  落ちる旧実装から、境界でangle_kp*errorと連続に一致する二次テーパへ変更した。現在実施中の
  外周切りmode ID試験はこのコードパスを通らないため無影響。
- firmware Linux CMakeビルド(`firmware/scripts/build.sh`)、`unit_web_ui.py --check`、
  JS構文チェック、`git diff --check`はすべて合格。
- P1.2(back-calculation anti-windup)とP0.1(連続unwrap角)+pre-steer状態遷移は
  実機チューニング/大きな設計判断が必要なため今回は見送り、理由付きで次回へ持ち越した。

### 現在の状態

- `firmware/src/control/unit_controller.c`と`tools/linux/unit_web_ui.py`にコード変更あり
  (未コミット)。実機への反映(build.ps1/flash.ps1、Web UI再起動)はユーザー側の判断で実施。
- wheel=0速度step/PRBS同定は実機で進行中。実測ログはまだこのセッションでは確認していない。

### 次の作業

1. P0.3/P1.4を含む新ファームをbuild/flashし、wheel=0/265rpm正逆90degの回帰(現行12/12基準)が
   崩れていないことを確認してから、mode ID結果の反映(Kp/Ki/LPF更新)へ進む。
2. mode ID実測ログを基に速度PI・LPFを再同定し、time scale 2.0→1.5→...→1.0を段階的に縮小する。
3. P1.2(back-calculation anti-windup)は実機ログでFF起因とPI起因の飽和を切り分けてから設計する。
4. P0.1(連続unwrap角)とwheel=0 pre-steer状態遷移は、上記の局所帯域向上が一段落してから着手する。
## 2026-08-07 (ラジコン操作による走行動作を確認)

### やったこと

- ユーザー実施のラジコン試験で、無線操作から機体の走行動作まで成立したことを確認した。
- 操作入力から走行系までの統合経路が実機でつながったため、開発段階を単体・空走中心の確認から、接地状態の安全性・再現性・負荷評価へ進める。
- 試験結果の扱いと次段階の確認項目を`docs/testing/RC_DRIVE_TEST_2026-08-07.md`へ記録した。

### 現在の状態

- ラジコン操作による走行成立は確認済み。ただし、速度、走行時間、試験路面、battery条件、実施maneuver、電圧・電流・温度の定量logは未記録であり、性能または安全の受入試験完了とは扱わない。
- 高速走行・急制動へ進む前に、通信断、送信機停止、CAN timeout、E-stop、再起動時の不意再始動防止を確認する必要がある。

### 次の作業

1. 低速で前後・左右・旋回・斜行・並進旋回を正逆実施し、再現性とunit方向／steer反転を確認する。
2. battery A/B電圧・電流、contactor後motor bus電圧、C620 rpm/current/temperature、指令値、停止時刻を同一時系列で記録する。
3. 通常減速、送信機断、CAN断、E-stop、電源再投入を分けて試験し、安全状態遷移を確認する。
4. 25%から段階的に速度を上げ、急制動時の回生energyからbrake resistorとchopper要件を決める。

## 2026-08-06 (主電源遮断方式の再確認)

### やったこと

- C620主電源の遮断をMOSFET式solid-state switchへ置換する案を比較した。
- 回生時にOFF状態で双方向遮断するにはback-to-back MOSFET、high-side gate driver、並列均流、熱・SOA・短絡保護が必要になるため、Rev.Aの主遮断は機械式コンタクタを継続すると再確認した。
- `POWER_DISTRIBUTION_AND_ESTOP.md`に残っていたKILIGEN E228の採用／不採用の矛盾を、2026-07-26の実績根拠付き採用決定へ統一した。

### 現在の状態

- 主遮断はKILIGEN E228、コイル駆動はTeensy制御のlow-side MOSFETとする。
- prechargeと回生brake chopperは独立MOSFET回路として検討を続け、主遮断機能は担わせない。
- E228には正式なDC負荷遮断datasheetがないため、約83Aの過去実績を超えないこと、接点状態、実負荷時の温度確認が残る。

### 次の作業

1. E228主接点の摩耗・ピッティング・溶着兆候を目視確認する。
2. 負荷試験logから最大・連続電流を確認し、E228の約83A実績範囲内か判定する。
3. 独立precharge／brake chopper基板の回路要件と抵抗定格を確定する。

## 2026-08-05 (中央Teensy基板 I/O・回生制動仕様の再検討を保存)

### やったこと

- 中央基板の通信port、汎用GPIO、battery監視、contactor後監視、回生brake chopperについて対話で整理した。
- 旧I/O案を確定仕様として進めず、`SCHEMATIC_DESIGN_OPEN_ITEMS.md`のCTR-16を再オープンし、CTR-21〜25へ検討内容を保存した。
- 現時点の候補として、CAN1/2/3各GH3 x1、I2C x2、UART x1、USB-CDC、2信号単位のGH4 GPIO port、load側bus電圧監視、独立analog comparator式chopperを記録した。
- battery A/Bの市販I2C sensor x2、部室在庫`BM14270AMUV-LBE2`、chopper用既製current sensor moduleの案を記録した。

### 現在の状態

- 上記はすべて未確定の検討メモ。中央基板requirements、Teensy pin assignment、architecture decisions、KiCad回路図には反映していない。
- 特にCAN connector数、I2C sensor型番/address、UART/SPI/GPIO port数、INA238を残すか、chopperをRev.Aへ含めるかが未確定。

### 次の作業

1. 対話を再開し、中央基板の外部接続機器一覧から通信port数を1項目ずつ確定する。
2. battery sensorとchopper current sensor moduleの型番を確認する。
3. 全項目の合意後にrequirements、pin assignment、architecture decisions、回路図を一括更新する。

## 2026-08-05 (Teensy socket pinの階層ラベル／未使用pin整理)

### やったこと

- `hardware/central-board/central-board/modules/200-teensy.kicad_sch`で、使用する44 socket pinの信号名を階層ラベルとしてJ1/J2のpin端へ直接接続した。
- 未使用のTeensy pin 33/37/38/39（socket pad 25/29/30/31）はtest pointへ出さず、回路図上でNo Connect（×）を付けた。
- 再生成用の`tools/kicad/annotate-teensy-hierarchical-pins.ps1`を追加し、pin割当正本とarchitecture decisionsも同じ方針へ更新した。
- KiCad 10 CLIでchild PDF出力、root netlist出力、ERC実行を行い、Teensy sheet内のpin未接続、label dangling、No Connect danglingが各0件であることを確認した。

### 現在の状態

- Teensy socket sheet単体では、使用pinと未使用pinを回路図上で直接判別できる。
- root sheet symbolにはTeensy childの階層pinをまだ配置していないため、root ERCには41種類の`hier_label_mismatch`が残る。他moduleを含む正式な親子sheet接続/ERC収束は未完了。

### 次の作業

1. rootのTeensy sheet symbolへ階層pinを取り込み、CAN・電源・安全・拡張module側の同名netへ接続する。
2. 他moduleも正式symbol／階層labelへ揃え、module単体からroot全体の順でERC 0へ収束させる。

## 2026-08-04 (中央基板 参照回路図＋簡易BOM PDFへ作り直し)

### やったこと

- 前回のKiCad階層sheet PDFは配線表を分割しただけで、人間が回路を追うreview資料として不適切だったため正本扱いをやめた。
- `UNIT_BOARD_SCHEMATIC_WITH_BOM`と`ODOMETRY_BOARD_SCHEMATIC_WITH_BOM`のA3横templateを再確認し、同じ「1機能=1ページ、大きな簡易回路図、重要caption、簡易BOM、page footer」構成で中央基板版を作成した。
- `docs/electrical/CENTRAL_BOARD_SCHEMATIC_WITH_BOM.html`をsource、`output/pdf/CENTRAL_BOARD_SCHEMATIC_WITH_BOM.pdf`をreview PDFとして作成した。全7ページ:
  1. 5 V input/eFuse/star distribution
  2. Teensy socket/pin function/mechanical keepout
  3. CAN interface x3
  4. E-stop hardware loop/contactor driver
  5. isolated E-stop monitor/rearm/24 V sense
  6. INA238/external Kelvin shunt
  7. expansion I/O/test access/review gates
- HTML各pageを1600x1051 PNGへrenderし、全ページを目視確認した。右端clip、CAN bus assignment欠け、Teensy socket label重なり、safety page下端labelを修正後、PDFを再出力した。

### 現在の状態

- オドメトリ／駆動module基板の既存PDFと同じ読み方で、中央基板を機能単位にreviewできる。
- KiCad階層sheetは転記/ERC用の下位資料。人間reviewの正本は新しい`SCHEMATIC_WITH_BOM` PDF。

### 次の作業

1. 新PDFをpage 1から順に人間reviewし、eFuse threshold、24 V protection、coil TVS、shunt source fuse、rearm位置を確定する。
2. 確定内容をKiCad正式symbolへ転記し、module単体からERC 0へ収束させる。

## 2026-08-04 (中央基板回路図を責務別moduleへ再構成)

### やったこと

- A3 1枚へ全回路を詰めた初版は人間reviewに不向きだったため廃止し、`central-board.sch`をroot index、以下6枚をchild sheetとする階層構成へ作り直した。
  - 100 Power input/eFuse/star distribution
  - 200 Teensy socket/pin map/safety GPIO default
  - 300-500 CAN communication x3
  - 600 E-stop/contactor/isolated monitor/motor bus sense
  - 700 INA238/external Kelvin shunt interface
  - 800-900 expansion/test access
- `tools/kicad/generate-central-board-modules.ps1`を追加し、詳細回路generatorから責務別sheetを再現可能にした。
- KiCad CLIでroot＋6 child sheetsの読込み、7ページPDF、netlist、各sheet SVG出力を確認し、全ページを画像renderして目視確認した。

### 現在の状態

- 担当者はroot sheetから自分の機能sheetだけを開いて、部品、pin、保護、TBD gateを独立してreviewできる。
- sheet間はglobal labelで接続している。現段階は引き続きreview draftであり、正式symbol化とERC 0件化は次工程。

### 次の作業

1. 各担当moduleでdatasheet対照reviewを行い、TBDとpin mappingを閉じる。
2. legacy child sheetsを現行KiCad形式へ変換し、正式symbol/pin type/footprintへ置換する。
3. module単体→root全体の順でERC 0件へ収束させる。

## 2026-08-04 (Teensy中央基板 人間レビュー用回路図作成)

### やったこと

- `hardware/central-board/central-board.sch`へA3横1枚のflat schematicを作成した。100=5V/eFuse、200=Teensy socket、300/400/500=CAN1/2/3、600=E-stop/contactor、700=INA238、800/900=expansion/testの機能blockに分け、pin番号・net名・TBD事項を図面上で追えるようにした。
- `output/pdf/central-board-review.pdf`をKiCad CLIから出力し、SVG/PNG renderでA3全体のblock配置、文字欠け、title blockを目視確認した。生成元は`tools/kicad/generate-central-board-schematic.ps1`へ保存した。
- Teensy 4.1はPJRC推奨24x1 socket x2を使い、Teensy直下面を部品/test point/露出copper禁止keepoutとする方針へ修正した。
- review中に判明した設計修正をrequirements、schematic reference、architecture decisions、open itemsへ反映した。
  - Micro-Fitはsingle-row `43650-0600` / `43645-0600`へ修正。旧`43025-0600`はdual-rowで嵌合しない。
  - LTV-847S入力を6.8kΩ x2から2.2kΩ x2、約5mAへ修正。
  - contactor clampを1N4007単独からdiode+TVSの実測選定へ変更。
  - TPS259470 OVLO、24V input reverse/surge保護、shunt sense source fuseを未確定gateとして明示。
- `hardware/central-board/README.md`へ回路図の開き方、review手順、`.kicad_sch`移行後にERC 0件をPCB開始条件とすることを記録した。

### 現在の状態

- 部品、pin番号、net、安全経路を人が照合できるRev.A review draftとPDFがある。KiCad 10で回路図/PDF/netlistを読み出せる。
- 現回路図はpin-explicit generic symbolとlegacy `.sch` labelを含むため、ERC acceptance対象ではない。正式symbolへ置換し現行`.kicad_sch`へ保存した後のERC 0件がPCB着手条件。
- PCBは未作成。Teensy socket方式は確定したが、stacking高さと機体内サービス空間はCAD照合が必要。

### 次の作業

1. KiCad GUIで`central-board.sch`を開いて現行`.kicad_sch`へ変換し、TPS259470/TCAN1051/INA238/LTV-847S/Teensyの正式symbolとpin typeへ置換する。
2. eFuse threshold worst-case計算、24V reverse/surge部品、contactor TVS、shunt source fuse、rearm button配置を確定し、図中TBDを閉じる。
3. No Connect/PWR_FLAGを整理してERC 0件へ収束させ、人間cross-check後にPCB placementへ進む。

## 2026-08-04 (Teensy 4.1中央基板 Rev.A 要件・回路入力固定)

### やったこと

- 中央基板のP0未解決事項を整理し、PJRC公式pinoutに基づくCAN1/2/3、安全I/O、I2C、SPI、UART、ADC、GPIOの全ピン割当を`docs/electrical/TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`へ固定した。
- Teensy 4.1はSamtec `SSQ-124-03-G-S` x2のsocket実装、VUSB-VIN pad切断、CAN3=Drive FD、CAN1=Sensor、CAN2=Expansionとした。
- 5V主入力を`XT30PW-M`+`TPS259470LRPWR`へ確定し、逆接・逆流・突入・過電流・過熱を保護する方針、`RILM=750Ω` typ 4.45A、Teensy枝`1206L075/16YR`を決めた。
- E-stop監視を`LTV-847S`、contactor driverを`IRLML0100TRPBF`+1N4007、操作panelをMicro-Fit 3.0 6pin、物理再アームbutton必須へ固定した。
- バッテリー監視を`INA238AIDGSR`+外付け100A/75mV Kelvin shuntとし、83A級主電流を中央PCBへ流さない構成へ決めた。
- 回路block、接続値、connector pin、PCB配置配線制約、bring-up試験を`docs/electrical/CENTRAL_BOARD_SCHEMATIC_REFERENCE.md`へ記録し、architecture decisions・中央要件・open items・document indexを更新した。
- `git diff --check`で文書差分にwhitespace errorがないことを確認した。

### 現在の状態

- 中央基板Rev.Aの電気要件とKiCad転記入力は固定済み。KiCad回路図・PCBはまだ未作成。
- PCBは4層、暫定100mm x 80mm、四隅M3として開始できる。最終外形・取付穴・connector引出方向は機体CADとの照合が必要。
- 外付けshuntは電気仕様100A/75mV、Kelvin端子まで固定し、正式型番は分電盤の機械寸法確認待ち。

### 次の作業

1. `hardware/central-board/`へKiCad projectとA3 flat schematicを作成し、power、Teensy、CAN x3、安全I/O、battery monitor、expansionの順にERCを収束させる。
2. BOMとfootprintを正式発注型番へ紐付け、Teensy socket列間・XT30極性・Micro-Fit pin 1を現物/図面で二重照合する。
3. 機体CADから基板許容外形、取付穴、USB/CAN/5V/24V harnessの引出方向を確定し、placement/routing、DRC、製造出力へ進む。

## 2026-07-31 (ステア応答高速化・wheel=0操舵 実装計画)

### やったこと

- 最高steer rpmだけを広げず、速度mode単体同定→加速/制動FF同定→time scale縮小→
  速度/加速度包絡拡張→接地3輪回帰の順で理論限界へ近づけるロードマップを
  `docs/control/CENTRAL_COORDINATED_CONTROL.md`へ追加した。
- wheel rpm=0でもsteer角を独立制御することを正式な契約とし、停止角保持、明示pre-steer、
  ETAへの操舵時間算入、ゼロ速度付近の角度ヒステリシス、純操舵非干渉試験を計画へ追加した。
- 主要運用を「指定poseへ到着→タスク→別poseへ移動」とし、`ARRIVE_SETTLED→TASK_HOLD→
  PRESTEER→DEPART`を中央状態遷移へ追加した。低速域は固定40rpmを最終値にせず、
  `Tsettle/Tfeasible`で理論限界への接近を評価する。
- 現行の`min(40rpm, planned包絡)`はcommissioning guardへ格下げし、本番は
  `margin*469rpm`から実効wheel profile rpmを差し引く連続包絡を通常上限にする方針を追加した。
  初期margin=0.90ではwheel=0/265/1200rpm時の上限は307.0/240.7/6.98 steer軸rpmとなる。
- 現コードレビューから、連続unwrap角、時刻付き1kHz局所補間、mode要求の包絡射影、
  back-calculation anti-windup、motor速度+AMT角observer、モデル加速FF、bounded DOB、
  2x2 mode非干渉補償を優先度付き実装項目として追加した。
- 駆動中央バスをTeensy CAN3-G474 FDCAN1のCAN FD nominal 1Mbps/data 2Mbps+BRSへ更新した。
  32byte軌道を200〜250Hzで3輪へ送り、broadcast commit後にG474が1kHz補間する。
  F405センサーCANとC620 CANはClassic 1Mbpsを維持する。

### 現在の状態

- wheel=0の正逆90deg操舵は現ファームと空走試験ですでに成立している。
- 速度mode単体同定ツールは実装済みだが、`firmware/logs/steer-mode-id/`の実測ログはまだない。

### 次の作業

1. 固定治具・ガード・非常停止を準備し、現行Kp=120/Ki=50/LPF=2msのwheel=0速度step/PRBS基準ログを取る。
2. 純操舵中の実wheel rpmと正味回転量を記録し、mode非干渉を確認する。
3. タスク側からpre-steer許可を受ける中央状態遷移と、ゼロ速度時の明示steer目標保持を実装する。
4. Web UIの固定40rpm上限を無効化可能なcommissioning guardへ変更し、planned/hard動的包絡を中央・ユニットで共通化する。
5. 連続unwrap角と時刻付き軌道契約を先に実装し、中央プロファイルとファーム内ランプの二重化を解消する。
6. G474 FDCAN1とTeensy CAN3を64byte/BRS対応にし、32byte軌道+commitと48byte状態を実装する。
7. 内周速度帯域を確定後、time scaleを2.0から段階的に1.0へ縮小する。

## 2026-07-31 (リアルタイムベクトル操作・空走制御セーブポイント)

### やったこと

- 2D速度ベクトルGUIを、Enter確定式からEnable中約30Hzのリアルタイム指令へ変更した。
  矢印キー/Shift微調整/ドラッグ/Escゼロをサポートし、最新入力だけを送信する。
- Enable時はAMT実角度をsteer初期目標に採用し、wheel目標/プロファイルを0へ初期化することで、
  Disable中のdraftや以前の指令による意図しない発進を防ぐ。
- wheel rpmから200Hzでplanned/hard包絡線を再計算し、高wheel rpmほどsteer rpmを連続的に
  減らす本番目標生成をGUIにも適用した。
- 実機でwheel=100rpm、steer=59.854→69.854degを30Hz相当で連続入力し、
  最終70.049deg/104.2rpm、`MOTION_SETTLED=1`を確認した。試験後のSTOPでwheel 0へ復帰した。
- Python構文、Web UIセルフチェック、JavaScript構文、`git diff --check`は合格。

### 現在の状態

- 空走単体制御は、本番形式のwheel rpm+指定角度、time scale=2、rpm包絡線、CAN収束判定、
  リアルタイムGUIまで一続きで動作している。現最良制御はG474へFlash済み。
- Web UIはport 8080で稼働中。保存時点の実wheel/実効wheelは0rpm。Unit Enable状態はtrueのため、
  操作終了時はGUIのSTOPまたはDisableで明示的に停止すること。
- 空走の手応えは強いが、手で回転輪へ負荷を与える試験は再現性と安全性がないため今後行わない。

### 次の作業

1. モータDisable・ステア静止を条件に、治具で機械正面を合わせてAMTゼロオフセットをFlash保存する。
   再起動後に0/90/180/270degと回転方向を検証する。GUIからのゼロ保存操作も追加候補。
2. 固定治具・ガード・非常停止を用意し、代表実車輪荷重でwheel=75/265/1200rpm、正逆90deg、
   急反転、連続8の字を実施する。手で負荷は掛けない。
3. `2*Tmin+0.35s`、角度定常誤差0.5deg、wheel誤差`max(12rpm, 6%)`を暫定受入条件とし、
   電流・母線電圧・温度・包絡線制限率を保存する。失敗時は摩擦補償/トルクFFを先に調整する。

## 2026-07-31 (理論時間x2軌道・CAN収束フラグ・現最良制御の焼込み)

### やったこと

- wheel rpmによる差動モータ包絡、steer最大rpm、非対称加減速を含む台形/三角形の
  `hard Tmin`/10%予備付き`planned Tmin`をWeb UIへ実装した。通常指令はtime scale=2とし、
  steer速度1/2・加速度1/4、wheel rpmランプ1/2で本番相当の目標を生成する。
- G474へSTATUS3を実装し、角度0.5deg、実steer軸1rpm、wheel追従、steer/wheel FF停止を
  100ms連続で満たすと`MOTION_SETTLED`を立てるようにした。STATUS1/3=20ms、STATUS2=50msを
  通常送信し、idx22はベンチ高周期overrideへ変更した。
- 現最良の空走値`steer PI=120/50、mode LPF=2ms、angle Kp=4/moving=1、deadband=0.3deg、
  accel/decel FF=0.5/0.5`を起動時既定へ反映し、G474へFlash/verifyした。
- 本番契約と同じ`SET_TARGET(wheel rpm, 指定角度)`+`SET_TARGET_FF`で、wheel=0/265rpm、
  正負90degを各3回回帰した。time scale=2の12試行はCAN収束12/12、監視期限
  `2*Tmin+0.35s=1.273s`以内12/12、平均1.146s、最悪1.250s、最大overshoot 1.054degだった。
- GUIへwheel/steer実rpm、hard/planned理論時間、2倍軌道、CAN収束状態を表示した。
  2D速度ベクトルの先端を矢印キー/ドラッグで動かすと、Enable中は約30Hzで
  方向=steer角、長さ=wheel rpmをリアルタイム送信するパッドを追加した。Disable中はdraftのみで、
  Enable時は実角度+wheel 0から安全に開始する。最大長は10%予備付きpure-wheel上限1228rpm。
- 実機へ30Hz相当で59.854→69.854degを連続入力しながらwheel=100rpmを指令した。
  最終70.049deg/104.2rpmでCAN収束flagを確認し、STOP後はDisable・wheel 0rpmへ復帰した。
- wheel=1200rpm定常ではplanned steer上限6.98軸rpm、time scale=2後の実指令3.49軸rpmを確認。
  wheel rpmの増減に応じて毎200Hz周期で包絡線を再計算し、steer rpm上限を連続的に増減する。

### 現在の状態

- 最終ファームをG474へ書込み・検証済み。リアルタイム版Web UIはport 8080で起動中、ユニットはDisable。
- 単一ユニット空走では2倍軌道+0.35s監視余裕を12/12で満たす。倍率1の厳しいゲイン試験は
  収束11/12・2*Tmin以内7/12で、終端静止摩擦は残る。

### 次の作業

1. 接地荷重・床材・バッテリー電圧を跨ぐ回帰で追従残差p99を測り、0.35s監視余裕を更新する。
2. Teensy中央100Hzへ10%予備包絡、3輪共通time scaling、STATUS3完了集約を移植する。
3. 終端摩擦は一定floorでなく、摩擦推定/DOBまたは終端専用補償で改善する。

## 2026-07-31 (ステア自動校正・理論速度への接近)

### やったこと

- 実機の粗→細自動探索をKp/Kiだけでなく、angle P/deadband、mode速度LPF、電流上限、
  加速度FF、ステア加速/制動へ拡張した。指令/実測電流peakと運動学的下限比も自動集計する。
- 中央側ベンチ目標生成を200Hzへ上げ、ステア加速3600deg/s^2と制動2250deg/s^2を分離した。
- 局所既定値をsteer mode Kp/Ki=80/25、angle Kp=4、速度LPF=10ms、加速度FF=0.75へ更新し、
  build/flash/verifyした。
- wheel=0/265rpm、正逆90degを各3反復したFlash後回帰は12/12成功。平均0.760s、最悪0.924s、
  理論0.375s比の平均2.03、最大overshoot 2.64deg、温度peak 30degCだった。旧平均1.185sから約36%短縮。
- 電流上限3000〜6000raw比較では指令peakが約2000rawに留まり、電流クランプが律速でないことを確認した。
- 校正を「内周速度PI→外周angle P→FF/プロファイル→負荷・床材ロバスト検証」に分ける手順を
  `docs/testing/UNIT_AUTO_TUNER.md`へ記録し、非対称ステア加速/制動を設計決定へ追加した。
- 巡航中の外周Kp干渉による中間カクつきへ、moving angle Kp=1からhold Kp=4へ連続補間する
  2自由度外周を追加しflashした。加速FF=0.75、制動FF=1.0も分離した。
- 300/360deg/sはovershoot増加で240deg/sより遅く、内周速度帯域が次の律速と判定した。
  最低速度floorと一定steer摩擦FFも悪化したため0へ戻した。
- 定常の多くは0.68〜0.92sだが、冷間1発目が0.527deg残る11/12バッチもあり、初回静止摩擦と
  絶対角依存の再現性は未解決。全ログは`firmware/logs/auto-tune/`へ保存済み。

### 現在の状態

- 最新ファームを書込み済み。200Hz Web UIは起動中、ユニットはDisable。
- 空走採用値はファーム/Web UI/自動調整器で一致している。

### 次の作業

1. **次セッション最優先:** 外周を切ったsteer mode速度step/PRBS同定モードを追加し、
   10ms→5ms以下の速度LPFで内周Kp/Kiを再同定する。
2. 接地時は空走値近傍だけ再探索し、床材・荷重を跨いだ最悪値で共通ゲインを決める。
3. Teensy中央制御へ非対称ステア加速/制動と200Hz相当の目標生成を移植・検証する。

## 2026-07-31 (差動ステア制御の高速収束・rpm包絡線・回生減速方針)

### やったこと

- 機構抵抗低下後の操舵発振を実機ログで切り分け、中央側目標生成を定速スルーから制動付き
  台形/三角形プロファイルへ変更した。90deg収束は最大240deg/s・加減速720deg/s^2を採用。
- `KINEMATICS_AND_RPM.md`の実測済みステア比`8/11`を正本として照合し、
  `DYNAMIC_CONTROL_PLAN.md`と`CENTRAL_COORDINATED_CONTROL.md`に残っていた旧`2/11`の
  包絡線式・数値表を修正した。
- 中央からユニットへの主目標を`omega_w, theta_s`、軌道微分をFFとして併送、中央100Hz・
  ユニット局所1kHzとする指令契約を`CENTRAL_COORDINATED_CONTROL.md`へ明記した。
- 単一モジュール式`|n_drive|/1364 + |n_steer|/341.1 <= 1`をWebUI目標生成へ接続し、
  wheel=1300rpm時のsteer要求240deg/sが96.5deg/sへ自動制限されることを実機確認した。
- 高rpm急減速の回生電圧上昇対策として、中央でwheelを非対称ランプに通し、反転は0rpm経由、
  通常STOPは減速完了見込み後にdisableする方針を`ARCHITECTURE_DECISIONS.md`へ確定事項として追加した。

### 現在の状態

- 改良版WebUIは起動中、ユニットはDisable。ファーム局所ループは1kHzのまま。
- WebUI既定はsteer加減速720deg/s^2、wheel加速1000rpm/s・減速500rpm/s。
- 500rpmからのSTOPは1.51s待機し、disable時実測0.015rpm。ビルド・セルフチェック合格。

### 次の作業

1. WebUIで検証したプロファイル・包絡線・非対称wheelランプを中央Teensy 100Hz制御へ移植する。
2. DCバス電圧を測定し、高rpm減速率500rpm/sの安全余裕を確認する。
3. 低抵抗化後の25/40rpm積分フロアA/Bを完了し、摩擦補償値を再同定する。

## 2026-07-29 (シルク手直し後 Gerber・ステンシルZIP再生成)

### やったこと

- ユーザーによる表面シルク手直し後のPCB(2026-07-29 13:12:32保存)を対象に製造出力を再生成した。
- ゾーン再フィル込みDRCで違反0件・未接続0件・Footprint error 0件を確認した。
- 既存のGerber ZIP、ステンシルZIP、展開ディレクトリを最新内容で置き換えた。
- F.Pasteは234開口、B.Pasteは0開口のため、ステンシルZIPはF.Paste+Edge.Cutsの片面用とした。

### 現在の状態

- `output/fabrication/odometry-board-revA-gerbers.zip`と`odometry-board-revA-stencil.zip`はシルク手直し後の最新版。

### 次の作業

1. 発注サイトのGerber viewerで手直し後シルク、基板外形、穴を最終確認する。

---

## 2026-07-29 (F405オドメトリ基板 Gerber・ステンシル製造ZIP作成)

### やったこと

- 保存後の最新PCBで、IMUコネクタ機能シルク6文字を0.6mmから基板制約の0.8mmへ修正した。
- 埋込みQR/ロゴおよび意図的なローカルFootprint差分について、ライブラリ比較DRCをignoreへ設定した。
- ゾーン再フィル込みDRCで違反0件・未接続0件・Footprint error 0件を確認した。
- 4層銅、表裏マスク/シルク、外形、PTH/NPTHドリルを含む`odometry-board-revA-gerbers.zip`を作成した。
- F.Paste(234開口)+Edge.Cutsを含む片面用`odometry-board-revA-stencil.zip`を作成した。B.Pasteは0開口のためステンシルZIPから除外した。

### 現在の状態

- 製造用Gerber ZIPと表面ステンシルZIPは`output/fabrication/`に作成・検証済み。

### 次の作業

1. 発注サイトのGerber viewerで層構成、外形、表裏シルク、穴を最終目視確認する。
2. ステンシル発注では片面(F.Paste)として指定し、厚さとフレーム有無を選択する。

---

## 2026-07-29 (F405オドメトリ基板 機能シルク仮配置)

### やったこと

- 基板名/Rev、AMT WHEEL 1/2/3とpin配列、PWR/RUN/COMM/ERR、SENSOR CAN、CAN TERM、5V IN、SWD/UART、ID DIP、IMUの機能シルクをF.SilkSへ仮配置した。
- 後から人が個別に移動できるよう、26個の独立したPCB textとして配置した。
- シルク文字高さを基板制約の0.8mm以上、線幅を0.1mmへ統一し、長いSWD/IMU pin列は2行へ分割した。
- KiCad 10トップ面レンダリングで内容を確認し、ゾーン再フィル込みDRCで違反0件・未接続0件・Footprint error 0件を確認した。

### 現在の状態

- 機能シルクは基板内へ仮配置済み。密集部では部品外形・コネクタ・他ラベルとの重なりがあるため、最終位置はPCB Editorで人が調整する。

### 次の作業

1. PCB Editorで各ラベルを見やすい位置へ移動し、コネクタ実装後も読めることを確認する。
2. F.SilkS Gerberを出力し、基板端欠け・パッド上・コネクタ下の文字がないことを最終確認する。

---

## 2026-07-29 (F405オドメトリ基板 部品番号非表示・DRC 0件化)

### やったこと

- PCB上の全68個のFootprint Referenceを非表示にし、部品外形・pin 1/極性マークは残した。
- 同一座標に重複していたGND viaを1個削除し、意図的なローカルFootprint差分チェックはDRCでignoreへ設定した。
- ゾーン再フィル込みのKiCad 10 CLI DRCで、違反0件・未接続0件・Footprint error 0件を確認した。
- 残すべき機能シルクを`ODOMETRY_BOARD_REQUIREMENTS.md`へ列挙した。

### 現在の状態

- 部品番号シルクは非表示。基板上には機能シルクを今後配置する余地がある。
- 電気的DRCは0件。シルククリアランス、Footprintライブラリ差分などの意図的なチェックはignore設定。

### 次の作業

1. 要件書の一覧に従い、基板名/Rev、コネクタ信号、AMT輪番号、LED、ID DIP、CAN終端、デバッグ、IMU軸方向の機能シルクをPCBへ配置する。
2. F.SilkS Gerberを出力し、コネクタ下・パッド上・基板端で文字が欠けないことを確認する。

---

## 2026-07-28 (F405オドメトリ基板 配線DRC収束・共有)

### やったこと

- ユーザーがKiCad PCB Editorでオドメトリ基板の配線を修正し、未接続を0件へ収束させた。
- シルク自体は残し、`silk_edge_clearance`、`silk_over_copper`、`silk_overlap`をDRCの`ignore`へ設定した。
- KiCad 10.0.4 CLIでPCB未接続0件を確認した。
- push前確認で、回路図には`U3/U7/U9 74LVC2G17`の電源ユニットC未配置によるERC error 3件、warning 3件が残っていることを確認した。

### 現在の状態

- PCBの電気的未接続は0件。
- DRCの残りはローカル変更Footprintのライブラリ差分と重複穴の警告で、シルク関連警告は非表示。
- 回路図ERCは未収束で、`74LVC2G17` x3の電源ユニット配置が必要。

### 次の作業

1. AMT102入力3シートへ`U3C/U7C/U9C`を配置し、3.3V/GNDへ接続してERCを再実行する。
2. 重複穴警告の対象を確認し、実重複なら片方を削除する。
3. ローカルFootprint差分を確認し、意図した差分だけ個別除外する。

---

## 2026-07-26 (中央基板 メインコンタクタ確定)

### やったこと

- モジュール評価計画の策定に続けて、中央Teensy基板の要件を固めて回路作成に入る段階へ移った。`docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md`を確認し、CAN構成・mini PC接続・安全I/Oの設計思想は既に確定済みで、回路作成前の唯一のブロッカーがメインコンタクタの正式型番であることを特定した。
- 所有品`KILIGEN E228`(24V DC、100A表記)について、販売情報上の連続使用目安50〜60Aに対し正式なDC負荷遮断定格データシートが無い問題を確認し、採用可否の判断手順(コイル電流確定→想定電流の上限設計→実負荷相当での遮断試験+接点目視検査)を`ARCHITECTURE_DECISIONS.md`・`CENTRAL_BOARD_REQUIREMENTS.md`へ暫定採用として記録した。
- ユーザーがコイル仕様(定格コイル電圧24V DC、コイル電力1.8W、コイル抵抗300Ω、動作電圧14〜16V、解放電圧6〜8V、最大印加電圧28V DC)を確認。計算上のコイル電流は約75〜80mAで、コイル抵抗・電力表記が相互に整合することを確認し、コイルドライバ設計(ロジックレベルNch MOSFET、Vgs(th) 2V以下、Vds 40〜60V級+1N4007フライバック)に反映した。
- 主接点側のDC負荷遮断定格について、ユーザーから前回ロボコン機体でこの個体を使用し、約2000W(24V換算で約83A)の通電中にE-stop等で遮断できた実績があるとの確認を得た。販売情報上の連続使用目安50〜60Aを上回る電流での負荷遮断実績のため、正式データシートの代替根拠として採用し、フル再検証キャンペーンは不要と判断した。残る作業は再利用前の主接点摩耗・ピッティングの目視検査のみとした。
- `docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md`と`docs/ARCHITECTURE_DECISIONS.md`のメインコンタクタ関連記述を上記内容で更新した。

### 現在の状態

- メインコンタクタは`KILIGEN E228`で確定。コイル側の設計値は確定済み、主接点側は前回ロボコンでの実績を根拠として採用し、残作業は目視検査のみに縮小した。
- コイルドライバの具体的なMOSFET品番はまだ選定していない(Vgs(th) 2V以下、Vds 40〜60V級という条件のみ確定)。
- 中央基板の他の未確定事項(5A主入力の逆接/逆流保護、Teensy/拡張枝のヒューズ定格)は今回のセッションでは着手していない。

### 次の作業

1. `KILIGEN E228`の主接点を目視検査し、摩耗・ピッティングがないか確認する。
2. コイルドライバのMOSFET品番を選定する(Vgs(th) 2V以下、Vds 40〜60V級)。
3. 中央基板の残る未確定事項(5A主入力逆接/逆流保護、Teensy/拡張枝ヒューズ定格)を確定し、回路図入力へ進む。

---

## 2026-07-26 (オドメトリ+IMUモジュール評価計画の策定)

### やったこと

- 単一モジュール評価計画の策定に続けて、オドメトリ基板(3輪AMT102+ICM-42688-P、unitId=4)のpose精度をどう評価するかを検討した。
- 2次元経路(XY全体)をトレースする治具は製作難度が高いため不採用とし、代わりに**直線スライダー試験(各輪独立、既知距離で線形換算精度を確認)+回頭ピボット試験(既知角度、平行2輪の差分計算に使うトレッド幅の校正誤差を確認)**の2試験で系統誤差を切り分ける方針とした。直線試験だけでは回頭誤差(トレッド幅誤り)が原理的に検出できない(平行2輪は直線移動中は差分が常時ゼロになるため)ことを確認し、2試験が両方必要と結論した。
- IMUセンサフュージョンの重み付けについて、手動チューニングではなく各センサの誤差特性を先に測定してから重みを導出する方針とした。ジャイロは静止積分によるドリフト特性測定、ホイールオドメトリのθ誤差は回頭ピボット試験(スリップが出やすい条件を振る)で測定する。
- オドメトリ+IMUノードの更新周波数を「①推定値そのものの精度(内部積算レートで決まる)」と「②消費側が使う値の鮮度(配信レートで決まる)」に分けて整理した。中央Teensyの車体逆運動学が100Hzで動く設計(`control/CENTRAL_COORDINATED_CONTROL.md`)であることから、配信は100Hzが妥当と結論し、これが既存の`ODOMETRY_BOARD_REQUIREMENTS.md`のpose 100Hz配信仕様と整合することを確認した。ユニットMCUの1kHzループはSET_TARGET追従用の別経路でオドメトリを消費しないため、そちらに配信レートを合わせる理由はないことも整理した。
- 上記を`docs/testing/ODOMETRY_IMU_EVALUATION_PLAN.md`へ新規文書化し、`docs/PROJECT_DOCUMENT_INDEX.md`へ11.3として登録した。

### 現在の状態

- 評価計画は文書化済み。治具製作・実測はまだ着手していない。

### 次の作業

1. 直線スライダー試験用の治具(定規+スライダー)を用意し、各輪独立で線形換算精度を確認する。
2. 回頭ピボット試験用の治具(固定ピボット+角度ゲージ)を用意し、トレッド幅校正誤差を確認する。
3. ジャイロ静止ドリフト試験を実施し、上記2試験の結果と合わせてセンサフュージョンの重みを導出する。

---

## 2026-07-26 (単一モジュール負荷ロバスト性評価計画の策定)

### やったこと

- ロボコンでの雑談を発端に、差動ステアユニット1基の単体テストの難しさ(steer/wheelが1モータの合成/差分で決まり、機構的に独立評価できない)を整理し、負荷試験の治具方針・評価項目・実施順序を確定した。
- 治具は「実機3モジュール同時稼働」「単輪+台車+重り」を不採用とし、**4隅従動輪+中央に評価対象モジュール1基**を採用した。荷重をシャーシ経由で接地点に伝えつつ、駆動は1モジュールのみで独立評価を維持する。5点接地の静定性は従動輪側のコンプライアンスで確保する方針。
- `docs/control/KINEMATICS_AND_RPM.md`の数値(モータ定格469rpm、DRIVE_RATIO=32/11、STEER_RATIO=8/11)から、wheel/steerが2モータの共有電流予算を通じて1枚の動作包絡線(菱形)を成すことを導出した: `|n_drive|/1364 + |n_steer|/341.1 ≤ 1`。マージン10%を適用した目標境界は`|n_drive|/1228 + |n_steer|/307.0 ≤ 1`で、目標wheel上限1228rpmは既存の2026-07-07実測1200rpm(p-p 3.5〜4rpm)とほぼ一致し、マージンの妥当性を裏付けた。steer軸は理論比で大幅余裕がある(現行ソフト上限40rpm=240°/sは理論比12%)ため、目標値は理論マージンでなく競技要求から決める方針とした。
- 制御ループ周期を確認し、`firmware/src/main.c`の`CONTROL_PERIOD_MS=1`で既に1kHz制御ループが実装済みであることを確定した。これはC620自体のCANプロトコルが1kHz固定であることに整合しており、デジタルループ側はほぼ天井に到達済みで、残る改善余地は機構帯域(バックラッシュ・摩擦)側にあると整理した。
- 計測方針として、wheel rpmはモータエンコーダ由来の計算値(`feedback.rpm/19×DRIVE_RATIO`)をまず信頼性確認する(steer固定・純駆動条件で無負荷/負荷双方を検証)ことを優先し、問題があれば`AMT102`(オドメトリ基板採用品と同型)を出力軸へ仮設する方針とした。オドメトリ基板は駆動輪と別の専用従動輪を使うため、今回の単体評価には流用できないと結論した。
- 負荷試験で追加すべき計測として`torque_current`(C620フィードバック、`c620.c`でデコード済みだが現状ログ未出力)と`temperature_c`を特定した。
- 実施順序を「0. wheel rpm信頼性確認 → 1. 独立軸試験(無負荷、大部分実施済み) → 2. 同時指令試験(無負荷、治具不要) → 3. 4隅従動輪治具の製作 → 4. 負荷試験本体」に確定した。2は差動の合成数式に起因する現象で負荷に依存しないため、治具製作を待たずに着手できる。
- 上記を`docs/testing/SINGLE_MODULE_LOAD_EVALUATION_PLAN.md`へ新規文書化し、`docs/PROJECT_DOCUMENT_INDEX.md`へ11.2として登録した。

### 現在の状態

- 評価計画・治具方針・動作包絡線の数値・実施順序は文書化済み。ファーム・治具の実装はまだ着手していない。
- 動作包絡線を可視化したチャート(Artifact)を作成済み。理論境界・目標境界(菱形)、実測点、現行steer上限帯を表示。

### 次の作業

1. steer固定・純駆動条件でのwheel rpm信頼性確認試験を無負荷/負荷双方で実施する。
2. `main.c`のテレメトリに`torque_current`のログ出力を追加する。
3. 同時指令試験(steer Δθ複数段 × wheel rpm複数点、無負荷)を既存NUCLEOベンチで実施し、クロスカップリングデータを取得する。
4. 4隅従動輪治具を製作する(従動輪側のコンプライアンス機構を含む)。
## 2026-07-26 (F405オドメトリ基板 DRC一次確認)

### やったこと

- `hardware/odometry-board/Oddom board/Oddom board.kicad_pcb`の保存済み状態へKiCad 10.0.4 CLI DRCを実行した。
- 現状はDRC違反152件、未接続13件。ゾーン再フィル後も未接続13件は変わらず、実配線の修正が必要と確認した。
- 自動配線案は密集部で他ネットとの交差・短絡を生じるため基板本体へ適用せず、ユーザーの既存PCB/プロジェクト変更を保持した。
- PCB Editorは同時書き込み防止のため正常終了した。未保存状態のSchematic Editorは閉じずに残した。
- ユーザーがGUI上で配線DRCを0件まで修正した。シルクを基板から削除せず、DRCの`silk_edge_clearance`、`silk_over_copper`、`silk_overlap`だけを`ignore`へ変更した。

### 現在の状態

- 基板本体へ今回の自動修正は入れていない。
- 重要項目は未接続13件、J2取付パッドの基板端クリアランス1件、重複GND via 1組、dangling 3.3V via 1件。
- 残りの大半はシルク重なり/銅箔上シルク、基板端シルク、ローカル変更済みFootprintとライブラリの差分警告。

### 次の作業

1. KiCadインタラクティブルータでDRCレポート記載の未接続13件を接続し、GNDは内層`GND Plane`へのvia追加を基本にする。
2. J2のMPと基板端、重複via、dangling viaを修正する。
3. シルク文字を移動/非表示化し、意図したローカルFootprint差分だけ個別除外してDRCを再実行する。
---

## 2026-07-26 (F405オドメトリ回路図 転記中の部品・接続確認)

### やったこと

- ユーザーがKiCad上でA3横1枚のオドメトリ回路図を転記する過程で、AMT102入力回路とF405最小回路の接続を再確認した。
- `ESDS452DBZR`はAMT102のA/B各信号をGNDへクランプする2ch双方向TVSであり、A-B間を短絡する部品ではないことを確認した。pin 1/2をA/B、pin 3をGNDとし、AMTコネクタ1個につき1個をコネクタ直近へ配置する。
- KiCad 10標準ライブラリには`ESDS452DBZR`の型番固有シンボルがないことを確認した。SOT-23フットプリントは標準にあるため、シンボルは双方向2ch・pin 1/2=IO・pin 3=GNDを満たすものを作成またはピン割当を検証して使用する。
- `SN74LVC2G17DBVR`はKiCad 10標準`74xGxx:74LVC2G17`を使用でき、DBVには`Package_TO_SOT_SMD:SOT-23-6`を割り当てることを確認した。3.3V給電、最大5.5V入力対応の非反転2ch Schmitt bufferとして、AMTの5V A/B信号を整形してF405へ3.3V出力する。
- `C511-C516`は`R511-R516`とRCローパスを構成する入力-GND間の調整用パッドで、初期実装はDNPと再確認した。`C501-C503`の100nFはSchmitt bufferの必須デカップリングであり、役割を区別した。
- STM32F405RGT6のpin 63はVSSであることをST資料とKiCad 10標準`STM32F405RGTx`で再確認した。KiCadシンボルではpin 18のVSSと同一座標に重ねた非表示pinのため、表示上はpin 18だけに見えるが、VSSをGNDへ接続すればpin 63も同一ネットになる。
- BOOT0は専用pin 60から10kΩでGNDへpull-downし、BOOT0テストポイントと隣接3V3テストポイントを設け、ROM bootloader使用時だけ短絡してリセットする接続と再確認した。

### 現在の状態

- 回路図の正本要件、簡易回路図、部品・Footprint・接続表は揃っており、ユーザーがKiCadへ手動転記中。
- 今回はKiCad回路図本体を変更していない。
- AMT入力は`connector -> ESDS452 -> 100Ω -> SN74LVC2G17 -> F405 timer input`、RCコンデンサは初期DNPで確定済み。

### 次の作業

1. `hardware/odometry-board/Oddom board/`の回路図転記を続け、F405電源、BOOT0、AMT102 x3、CAN、IMU、Debug/ID/LEDをA3横1枚へ配置・配線する。
2. `ESDS452DBZR`はpin 1/2=保護IO、pin 3=GNDとなる型番固有シンボルを用意するか、採用する代用シンボルのピン番号と双方向表現をTIデータシートに照合する。
3. 転記完了後、ERC、ネットリスト、PDFを出力し、特にVSS pin 18/63、VDD pin 19/32/48/64、VCAP_1/2、BOOT0 pin 60、AMT A/B全6chを接続表と照合する。

---

## 2026-07-25 (オドメトリ基板 簡易回路図＋BOM作成)

### やったこと

- unit board版`UNIT_BOARD_SCHEMATIC_WITH_BOM`と同じA3横レイアウトで、ブロック別の簡易回路図＋BOMを作成した。
- 6ページ構成: 5V/3.3V電源、F405最小回路、センサーCAN、AMT102 x3、ICM-42688-P、Debug/ID/LED。
- 各ページへRefDes、部品名/値、KiCad Footprint、接続先・注意事項を併記した。
- 電源はunit board共通図を流用し、F405固有回路とCAN/AMT102/IMU/Debug図はオドメトリ用信号名で新規作成した。
- PDF全6ページをレンダリングし、文字切れ・重なり・図欠落がないことを目視確認した。

### 現在の状態

- HTML: `docs/electrical/ODOMETRY_BOARD_SCHEMATIC_WITH_BOM.html`
- PDF: `docs/electrical/ODOMETRY_BOARD_SCHEMATIC_WITH_BOM.pdf`
- 配布用PDF: `output/pdf/odometry-board-schematic-with-bom.pdf`
- KiCad回路図本体は変更していない。

### 次の作業

1. 簡易回路図を見ながらKiCadのA3横1枚へ回路を転記する。
2. IMU現物到着後にJ601 Footprint、pin 1、pitch、外形、固定穴を追記する。
3. 転記後にERC/PDF出力し、簡易回路図の各ネットと1:1照合する。

---

## 2026-07-25 (オドメトリ回路図リファレンス HTML/PDF化)

### やったこと

- Markdown版の接続仕様を、図表・機能ゾーン・信号フロー付きのHTMLへ再構成した。
- ユーザー意図に合わせ、回路図そのものではなく「部品名・値・KiCad Footprint・接続先」を追える回路図転記表へ修正した。
- Chrome印刷用CSSでA4横7ページのPDFを生成した。
- PDF全7ページをPNGへレンダリングし、文字化け、表の切れ、重なりがないことを目視確認した。
- 一時的に作成したKiCad自動生成ドラフトは要求範囲外と判明したため、正規成果物から除外した。ユーザー編集中の`Oddom board.kicad_sch`は変更していない。

### 現在の状態

- HTML: `output/html/odometry_board_schematic_reference.html`
- PDF: `output/pdf/odometry_board_schematic_reference.pdf`
- 回路図本体はKiCad GUIでロック中のため未変更。

### 次の作業

1. HTML/PDFを横に表示しながら、KiCadのA3横1枚へ100番台順で部品を配置する。
2. 回路図保存・終了後、ERC/PDF出力と接続表の1:1照合を行う。

---

## 2026-07-25 (オドメトリ基板 フラット回路図方針確定)

### やったこと

- オドメトリ基板Rev.Aは階層シートを使わず、A3横1枚のフラット回路図へまとめる方針を確定した。
- 電源、F405、CAN、AMT102 x3、ICM-42688-P、Debug/ID/LEDのゾーン配置、100番台RefDes、ローカルネットラベル、接続表を`ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md`へ整理した。
- AMT102入力は`ESDS452DBZR` x3を正式選定し、connector -> TVS -> 100Ω初期値の直列抵抗 -> Schmitt buffer -> MCUの順に確定した。RCはDNP footprintのみ用意する。
- `hardware/odometry-board/Oddom board/`にKiCad 10の新規プロジェクトが作成されていることを確認した。

### 現在の状態

- 新規回路図は空のA4シートで、KiCad GUIにより編集中ロックされている。
- 同時編集による破損を避けるため、今回はこちらから`.kicad_sch`本体を書き換えていない。
- 1枚へ転記する接続仕様とRefDesは準備完了。

### 次の作業

1. KiCad上で用紙をA3横へ変更し、リファレンス資料のゾーン順に部品を配置・配線する。
2. 保存・終了後、`tools/kicad/check.ps1`でERC/PDF出力を行い、接続表とネットリストを照合する。

---

## 2026-07-25 (ICM-42688-P IMUモジュール購入反映)

### やったこと

- ユーザー購入品を`ICM-42688-P`搭載ブレークアウトモジュールとして採用確定した。購入先はAliExpress item `1005012473450791`。
- TDK公式仕様で6軸、VDD/VDDIO=1.71～3.6V、I2C/I3C/SPI対応を確認し、オドメトリ基板では3.3V・4-wire SPIを使用する方針とした。
- F405側をSPI3 PC10=SCK、PC11=MISO、PC12=MOSI、PD2=`IMU_CS_N`、PC4=`IMU_INT1` Data Ready、PC5=`IMU_INT2`予約に確定した。
- キャリア側のIMU電源デカップリングはunit board採用品の100nF+2.2µFを流用する。
- 初回bring-upはSPI Mode 0・1MHz以下で`WHO_AM_I` register `0x75`から`0x47`を確認し、その後に周期取得と速度引上げを行う手順へ確定した。
- 購入モジュールが5V/3.3V給電、I2C/SPI両対応の8pin構成
  (`VCC/GND/AD0(MISO)/SDA(MOSI)/SCL(SCLK)/CS/INT1/INT2`)であることをユーザー情報から確認した。
  本基板ではVCC=3.3V固定、4-wire SPI、INT1/INT2両方を配線する。

### 現在の状態

- IC型式とMCU側信号割当は確定した。
- ヘッダ信号構成は確定。物理pin 1方向、pitch、外形、固定穴、オンボードLDO/レベル変換回路は未確認。

### 次の作業

1. 到着後にモジュールの表裏写真、pin 1方向、pitch、外形寸法、固定穴を確認する。
2. 3.3V/GNDとIC VDD/VDDIO、SPI/INT端子の導通を確認し、オンボード回路を確定する。
3. 確定した外形とpin順をF405オドメトリ回路図・PCB固定方法へ反映する。

---

## 2026-07-25 (F405オドメトリ資料レビュー・unit board部品流用確定)

### やったこと

- Claude作成のF405変更資料を、ST公式DS8626 Rev.12、AN4488、KiCad 10標準`STM32F405RGTx`シンボルと照合した。
- 初稿の「PD2はF405 LQFP64に存在しない」は誤りで、PD2はpin 54に存在することを確認した。SPI IMUのCSはG474案と同じPD2を維持し、PA15はハードウェアNSSが必要な場合だけの代替候補へ戻した。
- 初稿のLQFP64物理pin表にあった複数のずれを修正した。CAN1=PA11/PA12(pin 44/45)、SWD=PA13/PA14(pin 46/49)、VCAP_2=pin 47、SPI3=PC10/11/12(pin 51/52/53)を含む使用pinを確定した。
- F405の電源pinをVDD=19/32/48/64、VSS=18/63と確定し、VDD各100nF+全体4.7µF以上、VCAP_1/2各2.2µF・ESR<2Ωを要件化した。KiCadシンボルではなくSTデータシートを正本とする記述へ修正した。
- F405固有部を除き、unit board採用品を優先流用する方針を確定した。`LM66100DCKR`、`TLV1117LV33DCYR`、`TCAN1051VDRQ1`、8MHz HSE、VDD/VDDAコンデンサ、GHコネクタ、LED、SWD/UART回路を共通化し、VCAP 2.2µFにも在庫共通化できる`GCM21BR71E225KA73L`を割り当てた。
- `AGENTS.md`、`hardware/README.md`、G474最小回路資料、NUCLEOベンチ試験資料に残っていた「オドメトリ=G474」をF405へ更新した。既存`unit_controller`は差動ステア専用のため、オドメトリへそのまま流用しないことも明記した。

### 現在の状態

- F405採用判断は妥当。Classic CAN 1Mbps、TIM2/TIM3/TIM4 Encoder Mode、USART2、SPI3の機能割当競合はない。
- ドキュメント上のF405 pinoutと必須電源回路は確定し、KiCad回路図へ転記できる状態。
- `hardware/odometry-board/`はG474の旧階層シート断片だけで、F405スキーマへの置換は未着手。

### 次の作業

1. `hardware/odometry-board/`へルート回路図とF405最小回路シートを作り、unit boardの電源/CANブロックを流用して接続する。
2. VCAP用`GCM21BR71E225KA73L`のメーカー特性で実装条件におけるESR < 2Ωを確認する。
3. F405回路図完成後にERCを0件へ収束させ、電源pin、CAN TX/RX、3組のEncoder入力をネットリストで自動照合する。

---

## 2026-07-25 (LEDテープ制御を独立CANノード化)

### やったこと

- LEDテープを中央Teensyの直接DATA配線ではなく、独立したCANノード基板で制御する方針を確定した。
- CANではモード、色、明るさ、速度、状態などの高位コマンドだけを送り、全ピクセルRGBの連続転送は行わず、アニメーションをLEDノード側で生成する要件を追加した。
- LED電力は中央PCBを経由させず、24V分電点から専用ヒューズ経由でLED制御基板へ供給する方針を維持した。

### 現在の状態

- 中央基板にはLED専用DATA線を設けず、LEDノードは拡張CANへ接続する。
- LEDテープは12V WS2815系または24Vアドレサブル系を候補とし、2m・高密度を想定している。電圧、密度、最大電力は製品選定後に確定する。
- LEDノードへの`STM32G474RET6`採用はオーバースペックとして不採用。第一候補は64MHz Cortex-M0+、FDCAN x2、128KB Flash、32pin QFNの`STM32G0B1KBU6N`。2026-07-25確認時点でDigiKey在庫2,768個、少量単価US$4.24。手実装・修理性を優先する場合は同系列LQFP32品を在庫と価格から再確認する。
- DC-DC、枝数、ヒューズ定格、電流監視回路は未選定。

### 次の作業

1. 12V個別アドレス品と24Vセグメントアドレス品からテープを正式選定する。
2. `STM32G0B1KBU6N`の電源、FDCAN、SWD、LED出力、ADCピンを割り当て、QFN32実装性を確認して正式採用する。
3. CANメッセージIDとLED高位コマンドを`docs/communication/COMMUNICATION_NAMING_AND_IDS.md`へ割り当てる。
4. テープ実電力からDC-DC、ヒューズ、AWG20電源線、XT30、基板配線幅を確定する。

## 2026-07-25 (オドメトリ基板 MCUをSTM32F405RGT6へ変更)

### やったこと

- 部室在庫から発掘した`STM32F405RGT6`(LQFP64)をオドメトリ基板のMCUとして採用することを確定した。
  オドメトリ基板はセンサーCAN1系統のみ必要で、ユニット基板がG474を選んだ決め手だった
  「FDCANが2系統必要」という制約が掛からないため成立する。センサーCANはClassic CAN 1Mbps固定
  (CAN FD未使用)なので、F405の`bxCAN`(Classic CAN専用)で要件を満たす。
- データシート(`STM32F405xx/STM32F407xx` Doc ID 022152)のピン定義表を確認し、AMT102用TIM2/TIM3/TIM4
  (PA0/PA1、PA6/PA7、PB6/PB7)、CAN1(PA11/PA12)、SWD(PA13/PA14)、LED(PA5/PB10/PB11)、
  ID DIP(PC6/PC7/PC8)、SPI IMU候補(PC10/PC11/PC12)がG474版と同じGPIO名で使えることを確認した。
- F405固有で新規に必要な回路差分を洗い出した: VCAP_1/VCAP_2用2.2µF×2(必須、省略不可)、
  HSEがPF0/PF1→PH0/PH1へ移動、デバッグUARTがLPUART1(無し)→USART2へ変更、BOOT0がG474の
  GPIO共用(PB8)から専用ピンへ変更、VREF+専用ピンが無く内部でVDDAに直結することを確認した。
  SPI IMU CSのPD2に関する初回確認は誤りだったため、直上のレビュー記録で訂正済み。
- ドキュメントを更新: `docs/electrical/ODOMETRY_BOARD_REQUIREMENTS.md`(MCU記載とF405固有要件の節を追加)、
  新規`docs/electrical/STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`(旧`STM32G474_ODOMETRY_PIN_ASSIGNMENT.md`は
  廃止注記を付けて履歴として保持)、`docs/ARCHITECTURE_DECISIONS.md`(オドメトリ関連行とMCU調達数の更新、
  新規決定行を追加)、`docs/PROJECT_DOCUMENT_INDEX.md`の該当説明文。
- KiCadスキーマ(`hardware/odometry-board/*.kicad_sch`)は未着手。MCUシンボルの差し替えはKiCad GUIで
  公式`STM32F405RGTx`シンボルへ置き換える方針とし、本セッションではドキュメントのみ更新した
  (物理ピン番号はデータシートTable 5のテキスト抽出では折り返しの影響で一部確定できず、
  GPIO名を正本として記載し、物理番号はシンボル配置時に照合する方針とした)。

### 現在の状態

- オドメトリ基板は依然スキーマブロックのみの段階(`.kicad_pro`/`.kicad_pcb`未作成)。MCU変更はドキュメント上で完了、
  KiCad上の反映はこれから。
- ファームウェアのオドメトリ実装はまだ存在しない(`firmware/src`はユニット基板用のSTM32G4専用実装のみ)。
  F405用のクロック・GPIO・USART・bxCANドライバは新規実装が必要になる。
- ユニット基板の調達計画(2026-07-25付BOM等)は旧来の「オドメトリ含め必要4個」を前提に計算済みのままなので、
  次回G474調達を見直す際は「ユニットx3のみで必要3個」に更新すること。

### 次の作業

1. `hardware/odometry-board/STM32G474 Minimum System.kicad_sch`をKiCad GUIで開き、公式`STM32F405RGTx`
   シンボルに差し替えて`STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`の割当で再配線する。VCAP_1/VCAP_2の追加、
   HSE/BOOT0/UARTの回路変更を反映する。
2. 確定済み物理pin番号を回路図へ転記し、STデータシートとネットリストで再照合する。
3. F405向けファーム platform層(クロック初期化、GPIO、USART、bxCAN)を新規実装する。

---

## 2026-07-25 (中央基板 `ESTOP_CTRL`ポート要件追加)

### やったこと

- 中央基板へ24V制御系を収容する方針に合わせ、2個のE-stop操作パネルを1本のハーネスで接続する専用`ESTOP_CTRL`ポートを追加した。
- 暫定6pinを、ハード直列NCループ往復、独立保護した24V LED電源/GND、E-stop 1/2補助接点リターンへ割り当てた。
- コネクタ抜去・断線時にNCループが開いてコンタクタが解放されるfail-safe要件と、LED系短絡が安全ループへ波及しない別保護要件を明記した。

### 現在の状態

- `docs/ARCHITECTURE_DECISIONS.md`と`docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md`へ確定事項として反映済み。
- コネクタはキー付き・ロック付き・60V以上を条件とし、正式型番と電流定格はメインコンタクタの24Vコイル電流確定後に選定する。

### 次の作業

1. メインコンタクタの正式型番とコイル電流を確定する。
2. `ESTOP_LOOP_RETURN`と補助接点入力の絶縁・保護回路を選定する。
3. 中央基板回路図へ`ESTOP_CTRL` 6pin、分離保護、コンタクタドライバを実装する。

## 2026-07-25 (ユニット基板 最新シルク反映・製造ZIP再生成)

### やったこと

- ユーザー更新後の`unit-board.kicad_pcb`を再検証し、追加ロゴ、QR、裏面説明シルクを含む最新版を製造出力へ反映した。
- QRフットプリント名に入っていたSSH URLがKiCadからライブラリIDとして誤解釈される問題を修正した。QR図形・格納内容は変更していない。
- 裏面説明文へミラー指定を追加し、基板外へ伸びていた文字揃えを修正した。既知の基板内シルク差異に対する`lib_footprint_mismatch`通知除外も復元した。
- ロゴフットプリントをB.Cu側へ正しく反転し、完成基板の裏面から正向きに読めることを3Dレンダーで確認した。
- KiCad 10.0.4でERC 0件、DRC 0件、未接続0件を確認した。
- 旧`output/fabrication/unit-board-revA`とZIPを削除し、表面ステンシル用`F.Paste`を含むGerber 10層、PTH/NPTHドリル、IPC-D-356、位置CSV、統計、STEPからなる21ファイルの製造ZIPを再生成した。裏面実装パッドは0個のため空の`B.Paste`は含めていない。
- `tools/kicad/fabricate.ps1`へJLCPCB列名のBOM自動出力を追加した。`unit-board-jlcpcb-bom.csv`は32品目・実装対象60個・Designator重複0。LCSC部品番号は回路図に未登録のため全行空欄で、登録済みメーカー型番は4品目に保持した。BOM追加後の製造ZIPは22ファイル。
- 追加製作4枚を基準に、全60リファレンスを31調達品へ割り当てた`tools/kicad/digikey-bom.ps1`を追加した。汎用値の抵抗・コンデンサにもメーカー型番とDigiKey品番を設定し、漏れ・重複・空品番0を自動検査する。
- 4枚の実装必要数240点に対して、受動部品は20%以上かつ2個以上、その他は1個の予備を加え、注文数334点とした。購入済み`STM32G474RET6`は手持ち10個を計上し、必要4個・追加注文0個とした。
- DigiKey投入用30行の`unit-board-digikey-bom-4boards.csv`と、手持ち・必要数・予備を含む31行の`unit-board-procurement-plan-4boards.csv`を製造スクリプトから自動生成し、製造ZIPへ同梱した。
- 今後のG474/CAN系基板でも流用できる`LabStock`調達プロファイルを追加した。4枚の必要数240点は維持しつつ、100nF・0Ω・1kΩは各100個、10k/22k/33kは各50個、その他の受動部品は20～25個、コネクタ・IC・保護部品は用途に応じ10～30個を在庫目標とし、注文合計887点とした。
- 最低限版334点に加えて、在庫込みの`unit-board-digikey-bom-4boards-plus-stock.csv`と数量根拠を含む`unit-board-procurement-plan-4boards-plus-stock.csv`を自動生成する。高価な`STM32G474RET6`は手持ち10個で在庫目標を満たすため、どちらの購入CSVでも追加0個。
- DigiKey調達で使用するコンデンサAVLとLM66100/TLV1117LV周辺の正式型番を、正本の部品選定資料へ2026-07-25付で追記した。HSE/VREF+はC0G、ADCフィルタはX7Rという回路要件を維持している。

### 現在の状態

- 最新製造ZIPは`output/fabrication/unit-board-revA.zip`。
- 最新ZIPは最低限版と共通在庫版のDigiKey BOM計4ファイルを含む26ファイルで、DRC 0件・未接続0件を再確認済み。
- ZIPのSHA-256は`eb22ae9fc2c7c63369b402a837e13c7f1a63ab9febd1684b24c7d99eb1dbc7b0`。

### 次の作業

1. 発注先オンラインビューアへZIPを投入し、表裏シルク、QR、内層、PTH/NPTH、外形の向きを最終目視確認する。
2. 発注先の4層標準stackupと現行1.6mm設定を照合する。
3. 通常はDigiKeyへ`unit-board-digikey-bom-4boards-plus-stock.csv`を投入する。予算を抑える場合だけ最低限版`unit-board-digikey-bom-4boards.csv`を使い、注文時点の在庫、価格、梱包単位、特にJST GH 3極/6極を再確認する。

## 2026-07-24 (ユニット基板 DRC/ERC 0件・配線収束)

### やったこと

- 前セッションの配置・配線済み`unit-board.kicad_pcb`を保持したまま、消失していた`ADC_ANALOG`、`CAN`、`HSE`、`POWER_3V3`、`POWER_5V`、`SPI`ネットクラス、現行階層ネットへの割当、配線幅・ビアプリセット、製造最小制約を`unit-board.kicad_pro`へ復元した。
- 全ネットクラスの最小離隔を製造最小0.20mmへ統一した。5V/3.3Vの既定線幅0.75/0.40mmは維持し、狭ピッチパッド直近だけ0.20mmへネックダウンした。
- `unit-board.kicad_dru`はネットクラスと重複していた片側評価のgeometryルールを削除し、HSEのF.Cu限定・ビア禁止だけを残した。
- HSE直下のIn1.Cu keepoutから`copperpour not_allowed`だけを外し、信号配線・ビア禁止を維持したままGND planeを再注入した。
- NRSTのデバッグコネクタ側とMCU側をIn2.Cuで接続し、TLV1117のpin 2と放熱タブを接続した。電源幹線、3.3V幹線、LED_COMM、U3/D6周辺などを再配線して、未接続、dangling via、短絡、交差、クリアランス違反を0件へ収束させた。
- 密集して読めなかった64個のReferenceシルクを非表示にし、部品番号はF.Fab・回路図・BOMへ残した。SW1と重複していた小型部品4個の外形シルクをF.Fabへ移し、シルク重複・銅箔重なり・基板端警告を0件へ収束させた。
- 意図的にライブラリ原本とシルクだけ異なるため、`lib_footprint_mismatch`は通知対象外とした。その他のパッド、courtyard、銅箔、接続検査は有効のまま。
- SW1の壊れた裸ファイル名モデル参照とPC固有の絶対パス参照を整理し、表示できていたモデルの姿勢（Y=0、Z=0.25mm、X=-90°）を保持した単一の`${KIPRJMOD}/../lib/DifferentialSwerve.3dshapes/JS102011SAQN.stp`参照へ統一した。プロジェクト内フットプリント原本にも同じ3D定義とF.Fab外形を反映し、SW1のライブラリ差異を解消した。
- 消失していた追加6ネットクラスと現行階層ネット16件への割当を再復元した。全クラスclearance 0.20mm、製造最小via 0.60/0.30mm、annular ring 0.15mmを適用し、電源既定幅は3.3V=0.40mm、5V=0.75mmを維持した。
- ECS公式ECX-33Q、Littelfuse/C&K公式JS、JST公式GH図面と照合し、Y1はpad 1/3=信号・2/4=GND、SW1は端子2.5mm pitch・1.2x2.5mm land・φ0.9mm NPTH中心間6.8mm、J7/GH3はpad寸法・pin 1方向が基板と一致することを確認した。
- `tools/kicad/fabricate.ps1`を追加し、Gerber 9ファイル、PTH/NPTH Excellon、ドリルマップ/集計、IPC-D-356、位置CSV、統計、実装済みSTEP、製造ZIPを`output/fabrication/unit-board-revA`へ生成した。gbrjob参照欠落0、Gerber/Excellon終端異常0、STEP内SW1モデル有りを確認した。
- 操作・デバッグ用シルクを追加した。表面はLED `PWR/RUN/COM/ERR`、MCU pin 1、`TERM`、UNIT IDの`1/2/4`を部品近傍へ表示し、裏面は基板名、LED凡例、J1〜J7・SW1・SW3用途一覧を表示した。
- 裏面に`https://github.com/Posaka-Y/Differential-Swerve-Drive`を示す約12.25mm角のQRコード（誤り訂正H）をB.SilkSの矩形として追加した。SW1位置決め穴とのシルク干渉を避け、3Dレンダーで外観を確認した。リンク先は現在privateのため、一般利用前にGitHub側をpublicへ変更する。
- KiCad 10.0.4で`tools/kicad/check.ps1 -FailOnViolations -OutputDirectory output/kicad`を実行し、ERC 0件、DRC 0件、未接続0件を確認した。最終3Dレンダーも目視し、部品Referenceの重なりが解消したことを確認した。

### 現在の状態

- `output/kicad/unit-board-erc.rpt`と`output/kicad/unit-board-drc.rpt`は0 violation。
- HSEはF.Cu・ビアなしを維持し、直下のIn1.CuはGND plane、他信号のtrack/via/pad/footprintは禁止。
- 電気系・シルク系ともKiCad DRCは0件。部品位置、基板外形、銅箔形状は3Dレンダーで読込み可能。
- SW1の3Dモデルはプロジェクト相対パスから1個だけ読み込まれ、別PCへ移しても同じ構成で解決できる。
- 裏面QRコードはGitHubリポジトリのHTTPS URLを直接保持し、Gerberへ画像依存なしで出力される。
- 製造データ一式と機体CAD照合用`unit-board.step`は生成済み。ただしPCBのphysical stackupは1.6mm・4層・各銅35µmの仮設定で、発注先標準stackupとの照合は未完了。
- ReferenceはF.SilkSへ出さない方針のため、実装時はF.Fabプロット、回路図、BOMを併用する。

### 次の作業

1. `output/fabrication/unit-board-revA/unit-board.step`を機体CADへ挿入し、45x45mm外形、39x39mm取付穴、SW1張出し、GH挿抜/曲げ空間、最大高さを承認する。
2. 発注先の4層標準stackupへ合わせて層厚・銅厚・表面処理・最小穴径を確定し、必要ならCAN配線条件を再確認して製造ZIPを再生成する。
3. KiCad Gerber Viewerまたは発注先オンラインビューアで、全9 GerberとPTH/NPTHの層対応・向き・外形を目視確認する。
4. 組立図ではF.FabのReferenceを出力し、初号機の電源投入前に5V/3.3V/GND短絡、NRST、HSE、両CAN終端を確認する。

## 2026-07-23 (ユニット基板 4層・配線ルール初期設定)

### やったこと

- `unit-board.kicad_pcb`を4層構成として整理し、`In1.Cu`をGND plane、`In2.Cu`をPower / Signal層として命名した。板厚は既定の1.6mmを維持した。
- PCBの製造最小制約を試作しやすい値へ設定した: clearance 0.20mm、silk clearance 0.15mm、silk文字線幅0.12mm、via最小径0.60mm、annular ring最小0.15mm。外形銅箔離隔0.50mmは維持した。
- 配線幅プリセット0.20/0.25/0.40/0.50/0.75/1.00mm、ビアプリセット0.60/0.30、0.70/0.35、0.80/0.40mmを追加した。
- `CAN`、`POWER_5V`、`POWER_3V3`、`HSE`、`SPI`、`ADC_ANALOG`ネットクラスを追加し、現行ネット名へ割り当てた。
- `unit-board.kicad_dru`を追加し、CAN、5V、3.3V、HSE、アナログの最小線幅・離隔とHSEのF.Cu限定・ビア禁止ルールを定義した。KiCad 10で非対応の`constraint layer`を使わず、条件式+`disallow track/via`で記述した。
- `JS102011SAQN.stp`を`hardware/lib/DifferentialSwerve.3dshapes/`へ追加し、専用footprintと基板内footprintの3Dモデル参照を`${KIPRJMOD}`基準の相対パスへ修正した。

### 現在の状態

- `.kicad_pro`はNode.jsのJSONパーサで構文正常を確認済み。
- 製造会社固有の4層stackup、CAN差動インピーダンス、基板外形、取付穴、ゾーン形状は未確定のため設定していない。
- Windows版KiCad CLIによる読込み/DRCは、WSL interopの`UtilBindVsockAnyPort`エラーで起動できず未確認。基板にはまだ外形・配線・ゾーンがない。

### 次の作業

1. KiCad GUIで基板を開き、Board SetupのPhysical Stackup、Constraints、Net Classes、Custom Rulesが読み込まれることを確認する。
2. 機体CADから基板外形、取付穴、コネクタ差込方向、高さ制限を確定する。
3. 外形確定後に配置し、`In1.Cu`全面GND、`In2.Cu`の5V/3.3Vゾーン、表裏GNDゾーンとスティッチングビアを作成する。
4. 発注先決定後、その標準4層stackupを入力し、必要ならCAN配線幅/間隔を再計算する。

## 2026-07-23 (ユニット基板 ERC 0件・ネットリスト整合修正)

### やったこと

- KiCad 10.0.4で現行ユニット基板を再解析し、開始時のERC 52エラー/19警告を0エラー/0警告まで収束させた。
- 親子階層名と方向を修正した: `PWR_5V`、`CAN_TX/RX`、`SPI3_MOSI/MISO`、`LED_RUN/COMM/ERR`、`DBG_TX/RX`。誤記`5.5V`、`CANFD]_TX`も除去した。
- MCUのRev.A未使用GPIO 26本へNo Connectを設定し、LM66100のSTにも意図的NCを設定した。入力5V/GNDとVDDAへ`PWR_FLAG`を追加した。
- ERCでは検出できなかったCAN論理方向の逆接続をネットリストで発見し、両バスとも`MCU TX -> TCAN TXD(pin 1)`、`TCAN RXD(pin 4) -> MCU RX`へ修正した。
- GH2電源入力のピン極性を`J1-1=PWR_5V_IN`、`J1-2=GND`へ修正した。
- 中央CANへ2個目のGH3(J3)を追加し、J2/J3を`COMM_A/COMM_B/GND`の並列パススルーにした。C620側J4/J5は`C620_CAN_H/L/GND`で維持した。
- 主要ローカルネットを`PWR_5V_IN`、`COMM_A/B`、`C620_CAN_H/L`、`HSE_IN/OUT`、`VDDA_A`、`VREF_PLUS`へ正規化した。
- デバッグGH6を確定部品`BM06B-GHS-TBT`と垂直footprintへ修正し、COMM/ERR LEDを黄`LTST-C190KSKT`/赤`LTST-C190KRKT`、ADCクランプを`BAT54SLT1G`、22kΩを`RC0603FR-0722KL`表記へ揃えた。
- 45箇所の主要ピン接続、MCU NC 26本、BOM 62部品のValue/Footprint有無、Ref重複なしをネットリストで自動確認した。
- `tools/kicad/check.ps1`へ`-SkipDrc`を追加し、PCB未着手でも`-FailOnViolations -SkipDrc`で回路図だけを厳格確認できるようにした。使用例を`hardware/README.md`へ追記した。
- 最終ERCレポート、ネットリスト、回路図PDFを`output/kicad/`へ、回路図PDFを`output/pdf/unit-board-schematic.pdf`へ出力した。

### 現在の状態

- `tools/kicad/check.ps1 -FailOnViolations -SkipDrc -OutputDirectory output/kicad`は成功し、ERCは0エラー/0警告。
- 電源、中央CAN、C620 CAN、AMT22、SWD/UART、UNIT_ID、LED、5V監視の主要ピン番号はネットリスト上で正本と一致している。
- PDF/SVG書き出しは成功したが、この実行環境にPoppler/Python画像レンダラと利用可能なアプリ内ブラウザがなかったため、ページ画像による目視レビューは未完了。
- PCBは空のままで、DRC/部品配置/配線は未着手。`untitled.kicad_sch`の要否も未確定のため削除していない。

### 次の作業

1. KiCad GUIまたはPDFレンダラのある環境で全6ページを目視し、ラベル重なり、線の交差、可読性を確認する。
2. 正本で要求する主要テストポイント(`PWR_5V_IN`、`PWR_5V`、3.3V、`VDDA_A`、GND、NRST、BOOT0、SWO、両CAN線)を回路図へ追加する。
3. CAN終端抵抗、LED抵抗、残りの受動部品Valueを正式型番表記へ揃え、JS102011SAQN footprintのメーカー推奨ランド照合を完了する。
4. `untitled.kicad_sch`をGUIで確認し、不要な複製なら削除する。
5. 回路図目視レビュー後、PCB外形・配置・配線へ進み、DRCを収束させる。

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
## 2026-07-12 (Hokuyo USB LiDAR接続・RViz表示)

### やったこと

- mini PCへUSB接続したHokuyo URGシリーズをROS 2 Humbleの`urg_node2_nl`で確認し、
  hardware ID `00905840`、`/scan`のLaserScan実データ取得まで確認。
- USB再接続時に`/dev/ttyACM0`から`/dev/ttyACM1`へ番号が変わることを確認。CANable等との
  競合を避けるため、Hokuyo固有の`/dev/serial/by-id/...`永続パスを使う設定へ変更。
- USB用launchとRViz設定を追加。RVizは`laser`固定フレーム、`/scan`、`Best Effort` QoSで表示する。
- 詳細手順を`docs/software/HOKUYO_LIDAR_SETUP.md`へ記録。

### 現在の状態

- HokuyoはUSB再接続後も永続パス経由で認識され、距離走査をRViz表示できる。

### 次の作業

1. 機体座標系へ取り付ける際は、`base_link`から`laser`への静的TFを追加する。
2. 障害物回避や自己位置推定へ使う場合は、2 mの表示範囲とLiDAR取付高さを実機要件に合わせて見直す。

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

## 2026-07-26 (オドメトリ基板 ERC 0件収束)

- `hardware/odometry-board/Oddom board/`のKiCadプロジェクトを対象に、前セッションからの続きでERCを54件→0件（Errors 0 / Warnings 0）まで収束させた。
- 前セッション分（このセッション開始時点で未コミット）: ルートシート未使用MCUピン25本へNo-Connect追加、電源系PWR_FLAG追加（VIN/VDDA/VSSA系統3箇所）、BOOT0の無効な`hierarchical_label`を`label`へ修正、浮いた配線・GNDシンボル整理。`Oddom board/`にsym-lib-table/fp-lib-tableを追加しDifferentialSwerveライブラリ未認識警告を解消。CAN_interfaceシートはVCCへPWR_FLAG追加で0件化。ルートシートとCAN_interfaceシートはこの時点で0件。
- このセッション: 残り18件（AMT102_inputテンプレート、3輪分×6件）を解消。
  - `AMT102_input.kicad_sch`（3シートAMT102_input/1/2で共有するテンプレート）で、チャンネルA/Bを別々の74LVC2G17（2部品、各ゲートB=unit2のみ使用、電源unit3未配置）で受けていた構成を、承認済み方針どおり1部品3ユニット構成へ統合。
    - unit1（ゲートA、pin1/6）= 旧チャンネルA用チップの位置・配線をそのまま流用（座標が同一のため配線変更不要）。
    - unit2（ゲートB、pin3/4）= 既存のチャンネルB用ブロックをそのまま維持。
    - unit3（電源、pin2=GND/pin5=VCC）を新規配置し、GNDシンボルと`global_label "PWR_3.3V"`（ルートシートの3.3Vレールと同名。`ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md`の電源表でバッファは3V3給電と確定済み）へ接続。
    - 各ユニットブロックの`instances`パスを3シート分（U3/U7/U9）に統一し、旧チャンネルA用の重複リファレンス（U5/U6/U8）を削除。GND新規シンボルの参照は`#PWR044`〜`046`。
  - `kicad-cli sch erc`で0 violations確認済み（`fresh_erc*.rpt`はスクラッチ確認用で削除済み、リポジトリには残していない）。
- 次の作業: PCBレイアウト（`Oddom board.kicad_pcb`）側へ配置配線を進める。まだ`hardware/odometry-board/Oddom board/`一式は未コミット（`git status`で確認要）。

## 2026-08-02 ESP32 Bluetooth→UART ベンチ受信機

- ESP32-C3 Super MiniのWi-Fi経路は切り上げ、通常ESP32（30ピン、CH340）へ
  DualSenseをBluetooth直結するベンチ構成へ変更。
- MCP2551中央CANベンチ配線は5V RXDレベルと物理層切り分けの手間から撤去し、
  ESP32↔NUCLEO間を3.3V UART 115200bps、固定長14byte+CRC8へ変更。
- 配線はESP GPIO17/TX→NUCLEO D0=PC5/RX、NUCLEO CN10-21=PA9/TX→
  ESP GPIO22/RX、GND共通。NUCLEOのUSBデバッグPA2/PA3は維持。
- `brltty-udev`停止とCH341ドライバ再ロード後、CH340を`/dev/ttyUSB0`で認識。
  ESP32-D0WD-V3へ安全ロック版を書き込み・verify・再起動まで成功。
- NUCLEO USART1のFIFO/overrun復帰を追加。ESP→NUCLEOは約690byte/s、
  NUCLEO→ESPはSTATUS 50frame/sで連続通信し、`tgt=1`、`fdbk=1`を確認。
- DualSenseをBluepad32で認識（VID 054c/PID 0ce6）。AMT現在位置（raw約3258）を
  0°としてFlash保存し、再起動後もゼロ点が維持されることを確認。
- 車輪浮上状態でOPTIONS arm + R1デッドマンを実動確認。約15rpm指令で車輪速度が
  14.6rpm付近へ追従し、操舵も目標付近へ追従する良好な挙動を確認。
- 安全停止中もR1を保持すると20msごとに再enableしていたため、NUCLEO側に
  「異常停止後はenable=0受信まで再arm禁止」のラッチを追加。ESP側の操舵指令も
  現在角との差を最大±90°へ制限した。
- 操作系をラジコン型へ変更。左スティックX=操舵（中央0°、端±90°。実機確認後に
  左右符号を反転）、右スティックY=正逆スロットル。速度上限は起動時500rpm、十字キー
  上下で250rpmずつ変更（250〜1300rpm、変更時に短く振動）。OPTIONS armとR1デッドマンは維持。
- ESP/NUCLEOともビルド・書き込み成功。現在は車輪浮上試験用として
  `DSD_MOTOR_ENABLE_ALLOWED=1`。
- 次: 新しい分離操作で左右・前後の符号と操作感を確認し、必要なら軸反転・最大速度・
  操舵範囲を調整する。

## 2026-08-04 AMT原点再校正

- ユーザー指定の機械位置を新しい0°として、AMT raw=331をSTM32 Flashへ保存。
- 校正ワンショット版で`save=1`、`zero=331`、sequence=3、CRC errorなしを確認。
- ワンショット設定を無効へ戻した通常版を再ビルド・書き込みし、再起動後も
  `zero=331`が保持され、現在角が359.824°（0°に対して-0.176°）付近であることを確認。
- ST-Link仮想ドライブはHEXが容量を超えたため、同内容のBIN（約11KB）で書き込んだ。

## 2026-08-07 ラジコン同期ログ・PCなし記録

- ESP32へ20Hz同期テレメトリを追加。ESP指令とNUCLEO返信を同じ行へ記録する。
  steer/wheelのtarget/actual/error、enable/unit_active、速度上限、UART bad/gap/txFailを含む。
- `capture_radio_telemetry.py`、`analyze_radio_telemetry.py`を追加し、CSV保存、定常/過渡の
  分離集計、R1停止時間、通信品質、target/actualグラフ、Markdownレポート生成を自動化。
- 車輪浮上状態の90秒ラジコンログ（20Hz、1801sample）を取得。
  - UART bad/gap/txFail=すべて0、enable指令1388sample中active成立1387sample。
  - 定常ステア絶対誤差p95=0.439°、max=1.170°。
  - 定常wheel絶対誤差p95=13.059rpm、相対p95=1.086%。
  - 急な左右切返しではsteer errorが最大90°（ESP側command clamp）へ達するが、保持後の
    定常追従は良好。直接角度指令のrate/profile整形が次の改善候補。
  - R1解除後の30rpm以下到達はmedian 75ms、最大750ms。最大値は解除直前約235rpmで、
    immediate disable後の惰性停止。通常停止の閉ループ減速と緊急disableの分離が候補。
- ユーザー指摘どおりUSB接続・浮上試験だけでは実走評価にならないため、ESP内蔵LittleFSへ
  PCなしで20Hz CSV保存する機能を追加。十字左で開始/停止、走行後USB接続時にPCから
  `D`コマンドを送って自動dumpする。
  録画中はUSB TEL出力を止め、Flashへ保存する。新規録画時は`/radio.csv`を上書き。
- `download_offline_log.py`を追加。USB再接続後の`D`送信、dump受信、自動解析に対応。
- LittleFS mount成功（`LittleFS=1`）、ESP↔NUCLEO UART返信正常、ビルド・ESP書き込み成功。
- PC USBを外した状態で録画し、再接続後に自動回収・解析するend-to-end試験が成立。
  96.09秒/1920sampleを回収し、UART bad/gap/txFail=0、定常steer誤差p95=0.264°・
  max=0.527°、定常wheel相対誤差p95=2.928%、R1停止median=25ms・max=350ms。
  この記録も車輪浮上の無負荷基準であり、接地性能の判定には使わない。
- 最新の内蔵ログ79.08秒/1581sampleも回収。UART bad/gap/txFail=0、定常steer誤差
  p95=0.364°・max=0.777°、定常wheel絶対誤差p95=24.129rpm（相対p95=5.539%）、
  R1停止median=75ms・max=1.300s。単輪の定常操舵と通信は3輪試験へ進める水準と判断した。
- 次: 3輪浮上状態で回転方向・ステア原点・指令mappingを確認し、成立後は250〜500rpm上限から
  接地試験へ進む。3輪同時動作時の電源・通信・停止ログを採り、profileと通常停止を調整する。

## 2026-09-12 中央基板・回路図リファレンス

- `hardware/central-board/reference-2026-09-12/central-board.kicad_sch`へ電源A/B1・安全D・監視E・拡張F/F1の4階層シートを追加し、既存Teensy/CAN1/2/3を含む9ページのKiCadネイティブPDFを出力した。成果物は`output/pdf/CENTRAL_BOARD_MODULAR_REFERENCE_2026-09-12.pdf`。
- 全追加シートはKiCad 10で開けることを確認し、PDFをレンダリングして概観を確認した。USB diode-ORは`+5V_SYS -> F101 -> D101 -> VIN_TEENSY`および`TEENSY_VUSB_PAD -> D102 -> VIN_TEENSY`のリファレンスとして反映した。
- これは組立・発注用ではない。最新ERCは420件で、拡張I/Oの実配線・安全フォトカプラのピン検証・TVS/eFuseの確定・全ERC解消が残る。
- 購入済みMatek `I2C-INA-BM`の情報に合わせて監視Eを更新した。外付けINA238/100Aシャント案は撤回し、外部モジュールのGH4を`GND/I2C0_SDA/I2C0_SCL/+5V_SYS`として描いた。Matek側I2C pull-upが3.3V安全である実測確認は通電前必須。
- 主入力はTPS259470の内蔵逆極性/逆流保護を使う方針へ整理し、SD-25B-5を5.00Vへ封印、UVLO/OVLO divider（732k/51.1k/221k、typ 4.43V/5.46V）、入力/出力bulk、FLT pull-up、USB OR用PMEG2010EAを回路図へ反映した。LTV-847Sは実pin mappingへ修正し、各使用入力を2.2k x2＋逆並列1N4148W、各出力10k pull-upとした。拡張全信号の100R、I2C 2.2k＋normally-open jumperも追加した。
- LTV-847Sは標準SOIC-16に適合しないため、仮footprintを削除した。購入リールとLite-On outlineからwide 2.54mm-pitch SMD用footprintを作成・実物照合するまでPCB配置不可。
- 中央基板は外部5V入力の旧案を停止し、`docs/electrical/CENTRAL_BOARD_REV1_CONSTITUTION.md`をRev.1最上位正本として追加した。24V+USB共存、基板上24V→5V Buck、24V優先ORing、TN686のMCU非依存E-stop、数chの汎用24Vローサイド出力、危険出力default OFF、終了条件、実装順を固定。既存`hardware/central-board/reference-2026-09-12/`とPDFはRev.1発注対象外。次は24V入力・Buck・USB ORingを部品と定数まで確定する。
- ただし根本ERCは544件のまま。現行reference生成形式のglobal labelが多数の未接続として報告されるため、次段階は発注前に各シートを本配線へ置換してERCを0へ収束すること。コイルTVSは実コンタクタのrelease waveformを測るまで未決定。

## 2026-09-12 中央基板 Rev.1 Buck選定

- Rev.1の24V→5V電源を基板内蔵へ確定。TI `LM76005RNPR`（60V入力、5A同期整流、内部補償）を採用し、400kHz・6.8µH・FB 100kΩ/24.9kΩ・5V印加時COUT実効180µF以上を初期定数とした。詳細は`docs/electrical/CENTRAL_BOARD_POWER_BLOCK_REV1.md`。
- 24V入力保護（XT30/Fuse/Pch MOS/TVS）、USBとの24V優先ORing、LiPo UVLOの責務、正式COUT型番は未決。次はBuck入力側の逆接保護とTVSを定数・部品まで決める。
## 2026-09-14 24V addressable LED CAN node Rev.A specification

- 演出/状態用24VテープLEDを独立CANノード化する仕様を`docs/electrical/LED_CAN_NODE_REQUIREMENTS.md`へ固定した。
- MCUはアクチュエータノードと同じ`STM32F303K8T6`、CANは`TCAN1051VDRQ1`、ローカル電源は`VIN_LED`(12〜24V)→`LMR51606XDDCR` 5V→`TLV76133DCYR` 3.3V。中央-ノード間は共通GND分電を前提に`COMM_A/B`のCAN 2線だけ。
- テープ方式はSPIではなくWS2811互換の5V・800kbps・1線アドレサブル方式。F303 timer+DMAでローカル波形を作り、`SN74AHCT1G125`で3.3V→5Vへ変換する。テープの物理LED数ではなく製品依存のpixel group数を扱う。
- テープ電流を小型制御基板へ無理に通さない。基板経由は5A連続/8A短時間の暫定上限、長尺/大電流は24Vをテープ現地へ直接注入する。起動/CAN timeout/E-stop broadcastでは装飾データをblankする。
- 次: この正本を元にA3人間レビュー用回路図（電源、F303/CAN、AHCTデータ出力、テープ電力注入）を作成し、選定する実テープの全白電流・pixel group長・コネクタ/ヒューズを確定する。
## 2026-09-14 (LED CAN node - selection-to-KiCad transfer chain created)

### やったこと

- ユーザー提示の「判断と機械転記を分離する」型に従い、LED CANノードについて要件書の次に`LED_CAN_NODE_PART_SELECTION.md`（データシート照合済み部品・停止条件）と`LED_CAN_NODE_KICAD_ENTRY_REFERENCE.md`（RefDes、固定ネット名、1ピン1ネット、DNP/STOP、目視レビュー）を追加した。
- F303K/TCAN1051/TLV761/LMR51606/AHCTの回路図転記対象を固定し、特に`PA12 -> TCAN TXD pin1`、`TCAN RXD pin4 -> PA11`、TCAN VCC=5V/VIO=3.3V/S=GND、AHCTのOE pull-upによるreset時データ無効を接続表に明記した。
- 24V WS2811互換テープ出力は`PA6 (TIM3_CH1) -> SN74AHCT1G125 -> 33R -> LED_DATA_5V`として固定。CAN timeout/E-stopでbufferを無効化する安全動作を維持した。
- `ARCHITECTURE_DECISIONS.md`の中央4pin CAN拡張ポート記述へ、自己給電アクチュエータ/LEDノードには5V/GNDを用いず`COMM_A/B` 2線だけを使う例外を追記し、ハーネス要件の矛盾を除去した。
- ユーザー提示のテープ仕様PDFを全8ページ確認。対象は24V・WS2811 IC RGB・2m・630 LED packages/m（計1260 packages）、3線`+24V/Data/GND`、データ矢印方向厳守、追加電源注入目安5mであることを確認した。2mなら始端1点の注入でよい。
- PDFはW/m/最大電流を明示していないため、テープ電流を制御PCBへ通す案を撤回。24V/GNDは外部5A fuseからテープへ直結し、基板はGH2経由の5VデータとGND referenceだけを外部adapter harnessへ出す。これにより基板パターン/コネクタの大電流推測を排除した。
- 電源/ESDのSTOPを追加解消: node electronics用逆接は`B160S1F-7`(60V/1A)、入力TVSは`SMBJ33A`(33V standoff/53.3V clamp)、Buck L101は`SRN6045TA-330M`(33uH/1.8A Irms/2.5A Isat)、テープData ESDは`PESD5V0V1BA-Q`(5V/11pF/SOD-323)に固定。UVLO分圧だけはDNPのままEN直結で開始する。

### 現在の状態

- MCU/CAN/降圧/LDO/LEDデータ出力は、推測なしでKiCadへ1部品・1ブロックずつ転記できる。
- `LED-01`（実テープのpixel group、全白電流、長さ）、`LED-02`（データESD）、`LED-03`（L101実装部品/UVLO確認）、`LED-04`（CAN終端位置）はSTOP扱い。J101/J401、テープ電源ヒューズ、逆接MOSFET/TVSを発注図へ入れる判断はまだ行わない。

### 次の作業

1. 実際に使用する24Vテープの型番・長さ・W/m（または最大A）を確定し、LED-01を閉じる。
2. J401/fuse/TVS/reverse MOSFET/L101の正式MPNとfootprintを部品選定書へ追加し、STOPを解消する。
3. 接続表を機械転記してKiCad ERC 0、netlist差分0、Section 7の人手レビュー完了後に人間レビューPDFを生成する。
## 2026-09-14 (LED CAN node - human schematic PDF / transfer-audit flow)

### やったこと

- 指定された7段階フローでLED CANノードを再監査した。要件書、部品選定書、KiCad転記表、提供されたテープマニュアルPDFを突き合わせ、2m/630 packages/m・24V WS2811・3線入力・5mごとの電源追加という根拠を回路図の外部ハーネス条件へ反映した。
- 文書間の矛盾を訂正: 旧「基板上の5A tape power pass-through」表現を撤回し、テープ24V/GNDは外部5A fuseからテープ直結、基板は外部1A fuseのlogic tapとJ401のData/GND referenceだけを担当する構成へ統一した。
- KiCad 10標準ライブラリを実ディスク照合。`STM32F303K8Tx`、`TLV76133DCY`、`74AHCT1G125`、GH connector、SOD-123F/SMB/SOD-323、SRN6045TA footprintは存在する。一方`LMR51606XDDCR`、`TCAN1051VDRQ1`、`ESD2CAN24DBZRQ1` symbolは標準に無いため`DifferentialSwerve`自作symbol必須として転記表に明記した。
- `output/pdf/LED_CAN_NODE_REV_A_HUMAN_SCHEMATIC_2026-09-14.pdf`を生成。A3横4ページ(S01電源、S02 F303最小回路、S03 CAN/LED Data、S04 harness/release checklist)をPyMuPDFでPNG化して全ページ目視し、配線ラベルがブロック内の文字に重なった初回出力を修正して再生成した。

### 現在の状態

- PDFとKiCad転記表は同じRefDes/net/pinを使う。PDFは人間レビュー用であり、KiCad発注回路図ではない。
- 残る未確定はLED-01（実テープの全白電流/pixel group数）、LED-03（UVLO dividerはDNP、EN直結で初期実装）、LED-04（CAN物理末端/終端実装）。未確定を推測してPDF/表へ埋めていない。

### 次の作業

1. `LED_CAN_NODE_KICAD_ENTRY_REFERENCE.md`を1ブロックずつKiCadへ機械転記し、各ブロックでERC/netlist diffを行う。
2. 実テープの全白電流を測り、5A fuseとbrightness ceilingを確定する。
3. CANの物理末端を決め、R301/SW301の実装状態を確定してからPCB設計へ進む。

## 2026-09-23 (中央基板: 未配線の階層シンボル配置プロジェクト作成)

### やったこと

- ユーザー指定「schematicは部品を置くだけ、配線不要」「階層化」を実施。低レイヤー作業をサブエージェントへ分担し、rootが仕様整理と最終目視を担当。
- 新規hardware/central-board-placement/central-board-placement.kicad_proを作成。トップ＋7子シート（電源、Teensy/分配、CAN1/2/3、安全、外部I/O）、169部品/172symbol unit。少部品4頁A3、多部品3頁A2。
- 最新中央仕様の外部5V/eFuse、GH3 CAN、中央コイルdriver、Matek端子、Teensy一体48padを反映。未確定部品はREVIEW/footprint空欄、クランプ等方式未確定は注記として残す。
- 旧参考eFuseシンボルの誤pin番号を検出し、正本の10pin対応で新規symbol作成。Teensy48pinを専用footprintの全padと照合。Q401は標準MOSFET図形。LTV847は4unitすべて配置。
- 初回の機械的ページ分割を目視で改善し、同じ機能を同一頁へ集約。独立検査でSW211のunit0部品欠落を検出・修正。

### 現在の状態

- 配線/ラベル/NC/電源シンボルなし。KiCad SVG/netlist出力成功、169部品と一覧一致、重複ref-unitなし、共有接続netなし、footprint指定は全件実在。
- ERCは意図された未接続464/未駆動24のみ。off-grid/library mismatchなし。完成回路・製造可の判定ではない。
- 全8頁のSVG→PNGを目視確認。検査output/kicad-check/central-placement/、独立監査independent-review.md PASS。
- 既存中央プロジェクトの19ファイルは作業前後SHA256一致、PCB変更なし。
- 生成元tools/kicad/generate-central-placement.pyとcentral-placement-parts.json、Teensy別照合central-teensy-pinmap.json。ユーザーの手編集後は再生成で上書きしない。

### 次の作業

- 新規プロジェクトをKiCadで開き、各子シートへユーザーが配線する。未確定値・コネクタ・footprintを順次確定し、階層pin/電源/NCはその段階で追加。
- 配線後にERCと正本接続表を照合する。V1 ODOMは本日CAN実機10/10成功、明日はIMU→ジャンパ→エンコーダの順（詳細firmware/PROGRESS.md）。
