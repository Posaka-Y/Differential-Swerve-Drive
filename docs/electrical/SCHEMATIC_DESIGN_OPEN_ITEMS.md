> **2026-09-29採用更新:** ユーザー承認によりX401を **D405: Alpha & Omega Semiconductor SMBJ33CA（双方向TVS）**へ置換。J402-1（ESTOP_LOOP_RETURN/COIL_POS）とJ402-2（COIL_NEG）の間へ並列。symbol=`Device:D_TVS`、footprint=`Diode_SMD:D_SMB`。型番選定・KiCad反映済み、実ハーネスでのサージ/吸収エネルギー/解放10ms以内は実測残件。X402帰路結合は未確定。

> **中央 2026-09-29:** 電源/CAN以外をKiCadへ配線。F402=LED枝保護TBD、X401=コイルクランプTBD、X402=帰路結合TBD（3ネット間の導通なし）として可視化。部品選定/帰路確定が完了した意味ではない。[詳細と残件](CENTRAL_NONPOWER_WIRING_2026-09-29.md)。

# 回路設計 未確定事項・着手順

## 目的

中央Teensy基板、差動ステアユニット基板、オドメトリ基板のKiCad回路図を作る前に、未確定事項と決定順を固定する。

回路ブロック、部品調査、ERC、配置配線制約の整理はAI支援で行う。PCB上の最終配置・配線は人がKiCad GUIで行い、各ブロックの制約表を基にチャットで逐次レビューする。

## 優先度

| 優先度 | 意味 |
|---|---|
| P0 | 決まらないと回路ブロックまたはコネクタ仕様を確定できない |
| P1 | 仮回路を作れるが、PCB配置開始前に確定が必要 |
| P2 | 回路図作成と並行可能。PCB外形・配置・製造前までに確定する |

## 共通部品選定基準

候補部品は次の順序ではなく、全項目を比較表にして総合評価する。

| 評価軸 | 確認内容 |
|---|---|
| 入手性 | DigiKey/Mouser/LCSC等の正規流通在庫、複数調達先、Active状態、代替候補 |
| 価格 | 試作5～10台相当の少量単価、最小発注数、送料を除く実装単価 |
| 採用実績 | メーカー評価基板、複数の公開回路・実働プロジェクトでの使用例。コピー数ではなく独立した設計例を確認 |
| 信頼性 | データシート定格、保護機能、温度範囲、ディレーティング、メーカー品質情報 |
| 実装性 | ステンシル＋リフローでの実装余裕、ピッチ、露出パッド、部品方向、AOI/目視検査性 |
| 修理性 | ホットエア/はんだごてでの交換性、ピンへのアクセス、代替部品とのフットプリント互換性 |

Rev.Aは受動部品0603以上、LQFP/SOIC/TSSOP/SOT系ICを優先する。BGA/WLCSP、0201以下は原則不採用。QFN/DFNや露出パッド品は、性能・入手性・基板面積上の利点が明確で、推奨ステンシル開口とサーマルビア条件をデータシートから設定できる場合だけ採用する。

## 最初に解消する文書間不整合(P0)

| ID | 未確定/不整合 | 影響 | 決定・確認方法 |
|---|---|---|---|
| DOC-01 | ~~ユニット要件と製作計画に旧`JST XH`、電源+CAN一体4線が残る~~ | 全基板コネクタ、共通CANブロック | **解消(2026-07-20): AMT22中継を横挿しGH 6pin `SM06B-GHS-TB`へ、製作計画の旧4線コネクタ記述をGH 2pin電源+GH 3pin CAN x2(渡り)へ更新。docs/electricalから旧XH/一体4線記述を除去済み** |
| DOC-02 | ~~SWDが2.54mm/Tag-Connect記載とSTDC14確定事項で不一致~~ | G474共通最小構成 | **解消(2026-07-19): ロボット側をGH 6pinへ統一し、WeAct MiniDebugger側SH 10pinとの専用変換ケーブルを使う** |
| DOC-03 | ~~`can_interface`共通ブロックの旧定義が4pin(COMM_A/B/5V/GND)~~ | 共通階層シート | **解消(2026-07-20): 製作計画の`can_interface`定義は横挿しGH 3pin x2(COMM_A/B/GND)+電源別GH 2pinへ更新済み。旧4pin定義は正本から消滅** |
| DOC-04 | ~~中央CAN3をCAN FD化するか、初版は全バスClassic CAN 1Mbpsにするか未確定~~ | 中央・ユニットCANトランシーバ | **更新(2026-07-31): Teensy CAN3-G474 x3の駆動中央バスをCAN FD nominal 1Mbps/data 2Mbps+BRSとする。F405センサーCANとC620 CANはClassic 1Mbpsを維持。`TCAN1051VDRQ1`はCAN FD 2Mbps対応のためBOM変更なし** |

## 全基板共通ブロック

| ID | 優先度 | 未確定事項 | 影響基板 | 決定・確認方法 |
|---|---|---|---|---|
| COM-01 | P0 | **回路図段階解消(2026-07-19): `ECS-80-8-33Q-JES-TR`、C0G 10pF x2を初期実装** | ユニット、オドメトリ | 8MHz、CL=8pF、ESR max 500Ω、±20ppm、−40～125℃。部品は共通化し、G474/F405各実基板で8.2/10/12pFを評価して最終調整。詳細は`STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md`と`STM32F405_ODOMETRY_PIN_ASSIGNMENT.md` |
| COM-02 | P2 | **上挿し`BM06B-GHS-TBT`、ラッチ側を基板内側に確定。** 1番を向ける基板方向のみ未確定 | ユニット、オドメトリ | `GHR-06V-S`+`SSHL-002T-P0.2`。配列は1=GND、2=SWCLK、3=SWDIO、4=NRST、5=DBG_TX、6=DBG_RX。配置時にシルクの1番表示とケーブル引出方向を確定する |
| COM-03 | P0 | **解消(2026-07-19): `TCAN1051VDRQ1`採用、`TJA1051T/3`代替候補** | 全基板 | VCC=5V、VIO=3.3V、SOIC-8、バスフォルト±58V。詳細は`CAN_COMMON_BLOCK_PART_SELECTION.md` |
| COM-04 | P0 | **解消(2026-07-19): `ESD2CAN24DBZRQ1`採用** | 全基板 | SOT-23、2ch双方向、±24V working。旧PESD1CAN-UはNot for Design Inのため不採用 |
| COM-05 | P0 | **解消(2026-07-19、2026-09-06部品更新): `TLV76133DCYR`、入出力各100nF+10uF X7Rを採用** | ユニット、オドメトリ | SOT-223のVOUTタブへ放熱銅箔を設け、実負荷で温度確認。詳細は`POWER_5V_COMMON_BLOCK_PART_SELECTION.md` |
| COM-06 | P0 | **解消(2026-08-04): MCUノード=`LM66100DCKR`、中央5A主入力=`TPS259470LRPWR`** | 全基板 | 中央入力逆接は別の60V級series保護が必要。eFuse UVLO/OVLOはworst-case計算後に抵抗値を確定する |
| COM-07 | P1 | **ユニット基板のみ解消(2026-07-19): 分圧、10nF、上下クランプをPA0へ接続** (分圧は2026-09-21にR13=22kΩ/R14=10kΩ=0.3125倍へ変更、クランプは`BAT54S-HF`) | ユニット | 5Vを0.3125倍。長いADC sample timeと基板別校正を使う。F405オドメトリRev.AはPA0をTIM2_CH1へ使うため5V監視ADCを非実装。詳細は各基板要件 |
| COM-08 | P1 | **MCUノード側解消(2026-07-19、F405流用2026-07-25): Lite-On C190シリーズ緑/黄/赤、各1kΩ** | 全基板 | PWR/RUN=`LTST-C190KGKT`、COMM=`LTST-C190KSKT`、ERR=`LTST-C190KRKT`。中央基板固有LEDは別途決定 |
| COM-09 | P1 | **解消(2026-07-19): CAN=`SM03B-GHS-TB`、5V=`SM02B-GHS-TB`。ハウジングは各極数の`GHR`、端子`SSHL-002T-P0.2`** | 全基板 | 常設電源/CANは横挿し・AWG26を原則とし、デバッグGH 6pinだけ上挿し |
| COM-10 | P1 | **解消(2026-07-19): 終端スイッチ`JS102011SAQN`、抵抗`RC0603FR-07120RL`** | 全基板 | SPDTのCommonと片側throwを使用し、`TERM ON/OFF`をシルク表示する |
| COM-11 | P2 | **G474主要ネットは`S1751-46R`、高密度信号は1.0～1.5mm露出銅padに確定** | 全基板 | 主要電源/CAN/Reset/BOOT/SWOはフック対応SMT loop。中央基板の必要個数は回路図作成時に確定 |

## 差動ステアユニット基板

| ID | 優先度 | 未確定事項 | 決定・確認方法 |
|---|---|---|---|
| UNIT-01 | P0 | C620側CANコネクタの正式型番・ピン順、C620内部終端の有無 | C620実機、純正ケーブル、公式資料を確認しテスタで終端抵抗を測定 |
| UNIT-02 | P0 | AMT222A側Pico-Lockから基板側GHへ接続するハーネス構成とピン順 | AMT-06C-1-036現物/公式資料を基にストレートまたは変換ハーネスを確定 |
| UNIT-03 | P1 | ~~UNIT_IDを3bit DIP、ジャンパ、Flash設定のどれにするか~~ | **解消(2026-07-20): 3bit DIPスイッチ(PC6-8、内部プルアップ、ON=GND)に確定。起動時RUN LEDのID回数点滅で目視確認、全OFFは未設定エラー。DIP型番は部品選定で確定** |
| UNIT-04 | P1 | C620 CAN終端の実装値/DNP既定 | C620 x2と基板を接続した状態で電源OFF時のCAN_H-L合成抵抗を測る |
| UNIT-05 | P1 | AMT22 SPI各線の直列抵抗実装値/DNP | 配線長と立上りを見て22〜100Ωのフットプリントを設け、実測で確定 |
| UNIT-06 | P1 | 24Vローカル降圧予備フットプリントをRev.Aへ残すか | 5Vハーネス電圧降下の実測結果で判断 |
| UNIT-07 | P2 | 基板外形、取付穴、コネクタの向き、AMT22/C620までの最大ケーブル長 | CAD上の取付空間とサービス方向から決定 |

## オドメトリ基板

| ID | 優先度 | 未確定事項 | 決定・確認方法 |
|---|---|---|---|
| ODOM-01 | P0 | **解消(2026-07-20): `AMT102-V`インクリメンタル x3、GH4は1=5V/2=GND/3=A/4=B、Z相なし** | 現物ハーネスの線色と嵌合面視ピン番号は製作時に再照合 |
| ODOM-02 | P0 | **解消(2026-07-20): `SN74LVC2G17DBVR` x3、3.3V給電、5.5V tolerant Schmitt入力でA/B 6chを受ける** | 各ICに100nF。直列R/ESD/RCはODOM-05で最終確定 |
| ODOM-03 | P0 | **解消(2026-07-25): 購入済み`ICM-42688-P` 8pinブレークアウト x1を3.3V給電・SPI3接続で剛結する** | 信号順はVCC/GND/AD0(MISO)/SDA(MOSI)/SCL(SCLK)/CS/INT1/INT2。物理pin 1、pitch、外形、固定穴は到着後に実測 |
| ODOM-04 | P1 | AMT102のDIP分解能と`countsPerRev`既定値 | 最大輪速時の入力周波数と精度を計算して決定 |
| ODOM-05 | P1 | **解消(2026-07-25): `ESDS452DBZR` x3をコネクタ直近へ置き、A/B各線へ100Ω初期値の直列抵抗。順序はconnector -> TVS -> R -> Schmitt buffer -> MCU** | RCはDNP footprintのみ用意し、最大周波数と実測波形から必要時に実装 |
| ODOM-06 | P1 | ~~unitId=4を固定配線、DIP、Flashのどれで与えるか~~ | **解消(2026-07-20): ユニット基板と共通の3bit DIPスイッチ(PC6-8)をunitId=4に設定。回路ブロックを完全共通化し、起動時RUN LED点滅で誤設定を目視検出** |
| ODOM-07 | P1 | **解消(2026-07-20): Rev.Aは5V監視ADCを非実装。PC0への移設も行わない** | PA0/PA1はTIM2エンコーダ入力に専用 |
| ODOM-08 | P2 | IMU座標軸、基板取付向き、中心からのオフセット許容 | 機体CADと状態推定座標系を合わせ、シルクへXYZを表示 |
| ODOM-09 | P2 | 基板外形、取付穴、AMT102コネクタ方向 | 測定輪ハーネスと振動源から決定 |

## Teensy中央基板

| ID | 優先度 | 未確定事項 | 決定・確認方法 |
|---|---|---|---|
| CTR-01 | P0 | **解消(2026-08-04): `TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`へCAN1/2/3、安全I/O、ADC、I2C、SPI、UART、LEDを固定** | PJRC公式pinout Rev.3/4と照合済み。CAN3=pin 30/31 |
| CTR-02 | P0 | **解消(2026-08-04): PJRC推奨Sullins `PPPC241LFBN-RC`/`PPTC241LFBN-RC` x2、Teensy側header候補`68000-224HLF`、列中心間15.24mm** | Teensy直下を全面keepoutとし、micro USB、Program button、microSDのサービス空間をPCBで確認する |
| CTR-03 | P0 | **解消(2026-07-26): KILIGEN E228を実績根拠付きで採用、24V/75〜80mA coil** | 再使用前に接点の摩耗・ピッティングを目視確認する |
| CTR-04 | P0 | **回路方式解消(2026-08-04): `IRLML0100TRPBF`、Gate 100Ω、47kΩ pulldown、diode+TVS clamp** | 3.3V gate駆動、Q1 VDS、coil解放時間を実測してTVS定格を確定する。1N4007単独clampは初期案にしない |
| CTR-05 | P0 | **回路方式解消(2026-08-04): `LTV-847S` 4ch、各入力2.2kΩ x2で直列loop・補助接点x2を絶縁監視** | 約5mA入力で全温度のLow levelと抵抗損失を実測する |
| CTR-06 | P0 | **回路側解消(2026-08-04): `INA238AIDGSR`＋外付け100A/75mV Kelvin shunt。主電流はPCBへ流さない** | 外付けshunt正式型番だけ機械取付寸法確認後に確定する |
| CTR-07 | P0 | **解消(2026-08-04): MCU4枝=`1206L050/15YR`、Teensy=`1206L075/16WR`、拡張=`1206L050/15YR`初期値** | 高温・突入・短絡試験で最終確認する |
| CTR-08 | P0 | **部品解消(2026-08-04): 5V主入力=`XT30PW-M`、主保護=`TPS259470LRPWR`、枝=`SM02B-GHS-TB`** | XT30極性/footprintを二重照合し、UVLO/OVLOをrail/comparator/resistor worst-caseで確定する |
| CTR-09 | P1 | **回路値解消(2026-08-04): 100kΩ+100kΩ/20kΩの1/11、各0.1%、1kΩ+10nF+3.3V clamp** | 40V印加試験と実測校正で判定閾値を確定する |
| CTR-10 | P1 | E-stop内蔵LEDの点灯条件とボタンのNO補助接点有無 | 常時/押下時/モータ遮断時から運用を確定し現物接点を確認 |
| CTR-11 | P1 | 24V安全表示灯の型番、電流、MOSFET出力数 | 赤黄緑+予備の負荷仕様を決める |
| CTR-12 | P1 | テープLEDの方式、電圧、長さ、電力 | Rev.Aでは外付けドライバI/O予約を基本とし、方式確定後に別回路化 |
| CTR-13 | P1 | **解消(2026-08-04): Rev.Aは外部3.3V LDOなし、拡張3.3V合計100mA上限** | 実測でTeensy温度と3.3V railを確認する |
| CTR-14 | P1 | **解消(2026-08-04): Program外出しなし。Teensy本体buttonとmicro USBへ直接アクセス** | PCB配置でサービスkeepoutを確認する |
| CTR-15 | P1 | **解消(2026-08-04): GUI要求に加えて物理`REARM_SW_N`押下を必須化** | ファーム安全状態遷移へ反映する |
| CTR-16 | P0 | **再検討中(2026-08-05): 通信・汎用I/O数は未確定。** 旧案はI2C x2、UART x2、SPI x1(CS x2)、GPIO/ADC x8だったが、専用機能を優先しつつ過度にならない汎用性へ整理し直す | 下記CTR-21〜25を対話で確定後、pin assignmentとschematic referenceを同時更新する。現回路図へはまだ反映しない |
| CTR-17 | P2 | 基板外形、取付穴、NucBox上部への積層高さと吸気/Wi-Fiアンテナ空間 | 機体CAD上でサービスデッキを設計 |
| CTR-18 | P0 | 24V control inputのreverse/surge保護部品、fuse値、TVS定格 | 24V source transientとharness条件を定義して60V級series保護を選定する |
| CTR-19 | P0 | 外付けshunt sense 2線のsource-end fuse/fusible resistor | battery側取付位置、定格、service方法を分電盤設計と同時に確定する |
| CTR-20 | P1 | 物理rearm switchをboard-localにするかoperator panelへ置くか | 操作性と誤投入riskを機体layoutで比較し、片方だけ実装する |
| CTR-21 | P0 | **CAN物理コネクタ数を再検討中。** 候補はCAN1/2/3各1個、合計GH3 x3。旧案の各バスIN/OUT x2（合計6個）は過剰の可能性 | 中央基板を各バス端点とし、デイジーチェーンは下流node側で行えるか、CANable等のservice接続方法も含めて確定する |
| CTR-22 | P0 | **外部通信・GPIO構成を再検討中。** 候補はI2C x2、UART x1、USB-CDC x1、GPIO/ADC 8本。SPI外出し、UART x2維持、GPIO本数は未確定 | GPIOは先行基板の「電源/GND/IO x2」単位を参考に、GH4 x4（1=VCC、2=GND、3/4=IO、IOは3.3V専用）を候補とする。**2026-09-26確定: GPIOの電源ピンは列全体でジャンパ1個(JP505)により3.3V/5V切替、IOは3.3Vのまま**(`CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md` S05)。IO LEDはADC負荷になるため不採用またはDNP、各IOは100ohm、ESD、pull-up/down/ADC-CのDNP footprintを検討する |
| CTR-23 | P0 | **バッテリーA/Bへ付ける市販I2C電圧・電流sensor x2の型番、address、給電、測定位置が未確定。** 現在のINA238＋外付けshunt案を置換するか併用するかも未確定 | 現物型番とdatasheetを確認し、同一address時はI2C0/I2C1分離またはmuxを比較する。確定までINA238回路を削除しない |
| CTR-24 | P0 | **コンタクタ後モータbusの監視と回生chopperは方式検討中。** 必須候補はload側bus電圧監視、analog comparatorによる自律chopper、外付けaluminum resistor、power MOSFET。load側bus電流sensorとchopper電流sensorは必須か未確定 | Chopperはmain fuse/contactorのC620側へ接続し、Teensy/I2C停止中もbus電圧で動作させる。Teensyは`MOTOR_PWR_SENSE`、`BRAKE_ACTIVE`、`BRAKE_FAULT_N`等の監視に限定する案を、停止energy、resistor pulse rating、fuse位置から評価する |
| CTR-25 | P1 | 部室在庫`BM14270AMUV-LBE2`をbusbar非接触電流監視へ使う案、およびchopper抵抗電流に既製sensor moduleを使う案は未確定 | BM14270はI2C magnetic sensorのためbusbar形状・距離・飽和・周辺磁界を含む実装後校正が必要。chopper用moduleは型番、双方向range、bandwidth、出力方式を確認してから接続先を決める |

## PCB外の電源・将来拡張

| ID | 優先度 | 未確定事項 | 回路図への扱い |
|---|---|---|---|
| SYS-01 | P0 | Rev.Aに将来48V上半身系をどこまで含めるか | 推奨は中央基板に`UPPER_PWR_EN`、電圧センス、外付けドライバ用I/Oだけ予約し、大電力回路は載せない |
| SYS-02 | P1 | LiPo並列の理想ダイオード/逆流防止モジュール | 中央PCB外の分電盤として別設計 |
| SYS-03 | P1 | 主ヒューズ・各LiPoヒューズ最終値 | 実走電流測定後に確定。回路図には定格欄を設ける |
| SYS-04 | P1 | NucBox G2現物の入力定格と専用USB-Cケーブル結線 | 付属アダプタ銘板と実機負荷試験で確定 |
| SYS-05 | P2 | 将来QDDの回生吸収、48V放電、落下対策 | QDD型番・個数・機構確定後に独立電源基板として設計 |
| SYS-06 | P1 | **解消(2026-07-20): 電磁弁等の汎用24V出力は中央PCBに載せず、CAN+`AUX_OUTPUT_EN`で接続する独立ドライバ基板に分離** | 中央基板は`AUX_OUTPUT_EN` GPIOと拡張CANを予約。24V負荷電流は中央PCBを経由させない |

## 回路ブロック作成順

### フェーズA: 設計入力の固定

1. DOC-01〜04の文書不整合を解消する。
2. GHの正式コネクタ型番と、WeAct MiniDebugger 10極ポートのコネクタシリーズ・ピッチ・1番方向を決める。
3. G474、Teensyのピンマップを固定する。
4. Rev.Aの範囲を固定し、将来48V系は予約I/Oに留めるか決める。

### フェーズB: 公式資料調査と共通部品確定

1. G474最小構成、水晶、STDC14。
2. 5V入力保護、3.3V LDO。
3. CANトランシーバ、TVS、終端、GH渡りコネクタ。
4. 各部品について、採用根拠、定格計算、データシートURL/版数、配置配線制約を記録する。

### フェーズC: 共通KiCadブロック

1. `g474_minimum`
2. `power_5v_3v3`
3. `can_interface`
4. `stdc14_debug`
5. `status_led`

各ブロックは単独でERCし、PDF出力して目視レビューする。

### フェーズD: ユニット基板固有ブロック

1. AMT222A SPI。
2. C620 CANとコネクタ。
3. UNIT_ID、ADC監視、テストポイント。
4. ルートシートへ共通ブロックを統合してERCする。

### フェーズE: オドメトリ基板固有ブロック

1. AMT102入力方式の比較・選定・6ch回路。
2. IMU比較・選定・SPI/Data Ready回路。
3. unitId、ADC監視、テストポイント。
4. ルートシートへ共通ブロックを統合してERCする。

### フェーズF: 中央基板固有ブロック

1. Teensyソケットと全ピンマップ。
2. CAN x3。
3. 5V入力・スター分配・枝保護。
4. E-stop監視、コンタクタドライバ、24Vセンス。
5. バッテリー監視、状態LED、拡張I/O、サービス端子。
6. 全体ERC、BOM、電源ピン/コネクタ整合チェック。

### フェーズG: 人によるPCB配置配線

AI側は各回路ブロックについて次の制約表を渡し、人がKiCad GUIで配置・配線する。

| 制約分類 | 例 |
|---|---|
| 最優先近接 | 水晶と負荷容量をMCU OSCピン直近、VDDデカップリングを対象ピン直近 |
| コネクタ近接 | CAN TVSとトランシーバを外部CANコネクタ近く、保護素子をコネクタ側に置く |
| 最大配線長 | 水晶、SPI、CANスタブ、スイッチングノードなどブロックごとに目標を示す |
| リターン経路 | 信号直下の連続GND、デカップリングの最短ループ、GND分断を跨がない |
| 離隔 | IMUを熱源/コネクタ/取付穴から離す、ADCをCAN/コイル/LEDスイッチングから離す |
| 電流/幅 | 電源枝ごとの最大電流から銅厚・温度上昇込みで配線幅を決める |
| サービス性 | STDC14、Program、終端、ID、テストポイントを組付け後も触れる位置に置く |
| シルク/誤挿入 | コネクタの1番、電圧、信号名、終端状態、基板Revを明示する |

配置完了時、配線途中、配線完了時の3回を基本レビュー点とする。AIは画像/PDF/DRC結果とネット別条件を照合し、最終判断と操作は人が行う。

## 完了条件

- P0がすべて解消または明示的にRev.A対象外となっている。
- 全採用部品にメーカー資料と正式発注型番が紐付いている。
- 3基板の電源・CANコネクタのピン順とネット名が一致している。
- 各階層シート単独および基板全体でERCを実行している。
- 配置配線制約表を人が確認してからPCB作業を開始している。
