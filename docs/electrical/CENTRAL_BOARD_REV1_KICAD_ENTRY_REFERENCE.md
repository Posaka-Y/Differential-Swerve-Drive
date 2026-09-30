> **2026-09-29採用更新:** ユーザー承認によりX401を **D405: Alpha & Omega Semiconductor SMBJ33CA（双方向TVS）**へ置換。J402-1（ESTOP_LOOP_RETURN/COIL_POS）とJ402-2（COIL_NEG）の間へ並列。symbol=`Device:D_TVS`、footprint=`Diode_SMD:D_SMB`。型番選定・KiCad反映済み、実ハーネスでのサージ/吸収エネルギー/解放10ms以内は実測残件。X402帰路結合は未確定。

> **2026-09-29配線反映:** S02B/S04/S05はKiCadへ接続済み。GPIO4pin×4組の接続、F402/X401/X402の未確定境界、検証結果は[最新配線記録](CENTRAL_NONPOWER_WIRING_2026-09-29.md)を優先。以下の「S05変更前」は今回以前の履歴。

> **2026-09-26 E-stop更新:** 1chループ監視だけを採用。旧本文のボタン個別監視・6pin J401・LTV-847S記述は採用しない。3.4節の更新表を正とする。

> **2026-09-29更新:** 最新の人間向け回路図は[15ページのベクター版](../../output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-29.pdf)。Teensy用途global labelはKiCadへ反映済み。GPIO4pin×4組はPDF p14に転記案を反映、S05は変更前。現在のCAN部品番号は保存版でU/D/R/SW311・312・313、専用J311〜J316へ変更されている。本文旧321/331系との違いに注意。J323汎用4pinは設計要求として残るが現保存版では未配置。

# 中央基板 Rev.1 回路図作成リファレンス(KiCad転記用)

> **2026-09-23最終方針**: 専用CANは横挿しGH3（A/B/GND）。駆動/ODOMのCAN2pin案は撤回。コイルdriverは中央搭載。主接点専用監視は付けずC620 CAN応答を補助診断とする。最新の[一括発注計画](PCB_BATCH_V2_CENTRAL_PLAN.md)を優先し、本文の旧CONTACTOR_STATUS_N案は採用しない。

> **最新版PDF**: [2026-09-23版（13ページ）](../../output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-23.pdf)。今回変更したCAN端子・中央コイルdriver・Teensy寸法は[改訂記録](CENTRAL_BOARD_REV1_PDF_CHANGELOG_2026-09-23.md)と最新版PDFを優先し、本文の旧S03/S04をそのまま転記しない。未確定箇所は同PDFに明示。


作成: 2026-09-14、コンタクタ境界改訂: 2026-09-17。対象: 中央基板 Rev.1(Teensy 4.1、外部5V入力+eFuse、CAN x3、E-stop絶縁監視、別体`CONTACTOR_DRIVER`への3.3V許可信号)。

この文書は、`output/pdf/CENTRAL_BOARD_REV1_HUMAN_SCHEMATIC_2026-09-14.pdf`(S01〜S05のブロック図)を、**人がKiCad GUIで回路図を起こせる粒度**(シート構成、RefDes、部品型番、ピン番号、ネット名、symbol/footprint)まで具体化した転記資料である。KiCadファイルを機械生成するための入力ではない。`UNIT_BOARD_SCHEMATIC_REFERENCE.md`と同じ役割の中央基板Rev.1版。

正本(矛盾時は正本優先。ただし本書でデータシート照合により訂正した箇所は正本側も同日修正済み):

- `../ARCHITECTURE_DECISIONS.md`(2026-09-14までの確定事項)
- `CENTRAL_BOARD_REV1_CONSTITUTION.md`(最上位方針)
- `CENTRAL_BOARD_REQUIREMENTS.md`、`TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`
- `CENTRAL_BOARD_SCHEMATIC_REFERENCE.md`(Rev.A。コンタクタドライバD2、24VセンスD4、INA238 EはRev.1で不採用)
- `CAN_COMMON_BLOCK_PART_SELECTION.md`、`POWER_5V_COMMON_BLOCK_PART_SELECTION.md`
- `ACTUATOR_CAN_NODE_REQUIREMENTS.md`(2026-09-14。切離し後の`CONTACTOR_DRIVER` 5線interfaceを定義)

凡例:

| 印 | 意味 |
|---|---|
| (確定) | 正本に記載がある |
| (DS照合) | 本書作成時にメーカー資料を直接確認した: TI `TPS25947` SLVSFC9C Rev.C(2026-05)、Lite-On `LTV-817/827/847` BNS-OD-C131/A4、Nexperia `PMEG2010EA` |
| (提案) | 正本に無く本書が埋めた値・構成。転記してよいが、8章の表で承認を得てから正本へ反映する |
| (未確定) | 推測で描かない。footprint/ラベルのみ、または空欄 |

Rev.Aリファレンスからの差分: **中央PCBから削除** = コンタクタドライバ(Q1 `IRLML0100`、coil clamp)、`MOTOR_24V`センス分圧、INA238回路、LM76005 Buck。**中央PCBに維持** = Teensy `MOTOR_PWR_EN` 3.3V出力。**追加** = USB diode-OR、`SRV05-4`、汎用CAN 4pinポート、別体`CONTACTOR_DRIVER` interface J402、24V制御入力J403。

---

## 1. 階層シート構成とRefDes体系

シート番号はPDFページ番号に一致させ、RefDesの百の位をシート番号にする。**PDFで既に振られているRefDes(J101/U101/R101〜R105/C101〜C105/D101/D102/F201〜F206/U401/J401〜J403)はそのまま使う。** PDFの「J20」(Matek)は本書でJ501。

| シート名 | PDF | 内容 | RefDes |
|---|---|---|---|
| `S02A_power_input` | S02 | J101 XT30、U101 eFuse、U102 USB側eFuse、バルクC、Teensy diode-OR | 1xx |
| `S02B_star_teensy` | S02 | 枝PPTC x6・枝LED・GH2 x4、Teensyソケット、状態LED、REARM | 2xx |
| `S03_can` | S03 | CAN1/CAN2/CAN3(同一回路を3回描く、またはシート1枚を3インスタンス) | 31x / 32x / 33x |
| `S04_safety` | S04 | `ESTOP_CTRL`、LTV-847S、別体`CONTACTOR_DRIVER` interface | 4xx |
| `S05_io` | S05 | Matek I2C、拡張I2C/UART/SPI/GPIO、TVS、テストポイント | 5xx |

- ルートシートは配線を持たず、5枚のシートブロックと基板名/Rev注記だけを置く。
- 電源レール(`+5V_RAW`、`+5V_SYS`、`+3V3_TEENSY`、`GND_CTRL`等)は電源シンボル+`PWR_FLAG`で扱い、ワイヤで引き回さない。
- シート間の信号は階層ピンで渡す。CANの`CANx_TX/RX`、安全入力`*_OK_N`、拡張I/Oは全てTeensyシート(S02B)が起点。
- `hardware/central-board/reference-2026-09-12/`はU401=CAN1、J201/J202=Teensyなど**別のRefDes体系**なので、流用時は読み替える(Rev.1では作り直しを推奨)。

## 2. ネット名

中央基板の既存正本は`+5V_*`表記のため、`COMMUNICATION_NAMING_AND_IDS.md`の`PWR_5V_CTRL`ではなくこちらを使う。

| ネット | 意味 | 出所 |
|---|---|---|
| `+5V_RAW` | J101入力、eFuse前 | 確定 |
| `+5V_SYS` | eFuse後、スター点 | 確定 |
| `+5V_UNIT1` / `+5V_UNIT2` / `+5V_UNIT3` / `+5V_ODOM` | 枝PPTC後、各GH2へ | 確定 |
| `+5V_TEENSY_F` | F205後、D101前 | 提案(名称) |
| `+5V_EXP` | F206後。汎用CANポート・外部5V | 提案(名称) |
| `VIN_TEENSY` | diode-OR後、socket pad 48 | 確定 |
| `TEENSY_VUSB` | Teensy裏面VUSBパッドからの引込み線。D102とU102 INへ | 確定 |
| `USB_EFUSE_EN` / `USB_EFUSE_OVLO` / `USB_EFUSE_ILM` / `USB_EFUSE_DVDT` | U102周り(2026-09-26追加) | 提案(名称) |
| `PWR_USB_FAULT_N` | U102 FLT→Teensy pin 9 | 提案 |
| `VCC_GPIO_EXT` | GPIOコネクタの電源ピン。JP505で`+3V3_TEENSY`/`+5V_EXP`を選択(2026-09-26) | 確定 |
| `+3V3_TEENSY` | Teensy 3.3V出力(pad 15/46)。**外部から給電しない** | 確定 |
| `GND_CTRL` | 制御GND=基板GNDプレーン | 確定 |
| `+24V_CTRL_IN` | J403から入る24V制御系(ヒューズ後)。基板上で`ESTOP_LOOP_FEED`と`+24V_CTRL_LED`へ分岐 | 提案(3.4節 提案B) |
| `+24V_CTRL_LED` / `GND_CTRL_LED` | E-stop LED・補助接点用24Vとその帰路 | 確定(PDF S04表記) |
| `ESTOP_LOOP_FEED` / `ESTOP_LOOP_RETURN` | 直列NCループの往路/復路。基板上は銅箔通過のみ | 確定 |
| `MOTOR_PWR_EN` | Teensy pin 2から別体`CONTACTOR_DRIVER`へ出す3.3V ON/OFF許可信号。起動時/Reset/Hi-ZはLow | 確定(2026-09-17境界確認) |
| `CONTACTOR_STATUS_N` | 別体driverからの任意status入力。未使用時はNC | 提案 |
| `ESTOP1_AUX_RETURN` / `ESTOP2_AUX_RETURN` | 補助接点の個別戻り | 確定 |
| `SPARE_24V_IN` | LTV ch4予備入力 | 提案(名称) |
| `ESTOP_LOOP_OK_N` / `ESTOP1_AUX_OK_N` / `ESTOP2_AUX_OK_N` / `SPARE_OK_N` | 絶縁監視出力。Low=接点成立 | 確定(SPAREのみ提案) |
| `REARM_SW_N`、`STATUS_G_LED`、`STATUS_R_LED`、`PWR_5V_FAULT_N` | Teensyピン割当表どおり | 確定 |
| `CAN1_TX/RX`、`CAN2_TX/RX`、`CAN3_TX/RX` | Teensy⇔トランシーバ論理 | 確定 |
| `SENSOR_COMM_A/B`、`EXP_COMM_A/B`、`DRIVE_COMM_A/B` | CAN1/CAN2/CAN3バス。シルクは`COMM_A/B` | 確定 |
| `I2C0_SDA/SCL`、`I2C1_SDA/SCL`、`UART7_TX/RX`、`UART8_TX/RX`、`SPI_SCK/MOSI/MISO/CS0_N/CS1_N`、`IO20_A6`〜`IO41_A17` | Teensy側(100Ω内側) | 確定 |
| 上記 + `_EXT` | コネクタ側(TVS側、100Ω外側)。例 `UART7_TX_EXT` | 提案(名称) |

## 3. 接続表

ピン番号欄の`-`は「正本に番号記載なし。KiCadシンボル/データシートで転記時に照合」。

### 3.1 S02A 電源入力・eFuse・diode-OR(1xx)

| Net名 | 部品 | ピン名 | ピン番号 | 接続先 | 備考 |
|---|---|---|---|---|---|
| `+5V_RAW` | J101 `XT30PW-M` | + | 1 | U101 IN、C101 | 横向きTHT。**pad 1が+側であることをAMASS図面とKiCad footprintの両方で確認**(確定) |
| `GND_CTRL` | J101 | − | 2 | GNDプレーン | |
| `+5V_RAW` | U101 `TPS259470LRPWR` | IN | 5 | J101-1、C102 | (DS照合) |
| `+5V_SYS` | U101 | OUT | 6 | C103、C104、スター点 | |
| `GND_CTRL` | U101 | GND | 8 | GNDプレーン | TI RPW0010A図面と取得ランドを照合。project-local footprintの分割角ランドは同じ端子番号へ整理（2026-09-26） |
| `EFUSE_EN` | U101 | EN/UVLO | 1 | R102(IN側)、R103(OVLO側) | 分圧の中点。フロート禁止 |
| `EFUSE_OVLO` | U101 | OVLO | 2 | R103、R104(GND側) | 分圧の下段 |
| - | U101 | AUXOFF | 3 | **No Connect** | open-drain出力。未使用 |
| `PWR_5V_FAULT_N` | U101 | FLT | 4 | R105 10kΩ→`+3V3_TEENSY`、Teensy pad 24(pin 32) | open-drain、Low=fault。**pull-upは3.3V**(Teensyは5V非対応) |
| `EFUSE_DVDT` | U101 | dVdt | 7 | C105 10nF→GND(R106 100Ω直列footprint、10nF時は0Ω) | R106は提案。DS 7.3.5.1 Noteで「CdVdt>10nFは100Ω直列推奨」。22/47nF交換時に必要 |
| `EFUSE_ILM` | U101 | ILM | 9 | R101 750Ω→GND | フロート禁止 |
| - | U101 | ITIMER | 10 | **No Connect** | open=過電流への最速応答 |
| `+5V_RAW`→`EFUSE_EN` | R102 732kΩ 1% | | | | |
| `EFUSE_EN`→`EFUSE_OVLO` | R103 51.1kΩ 1% | | | | |
| `EFUSE_OVLO`→GND | R104 221kΩ 1% | | | | |
| `+5V_RAW` | C101 100uF/10V | | | GND | J101直近。型番未確定 |
| `+5V_RAW` | C102 1uF 0603 X7R | | | GND | U101 IN直近 |
| `+5V_SYS` | C103 1uF 0603 X7R | | | GND | U101 OUT直近 |
| `+5V_SYS` | C104 470uF/10V low-ESR | | | GND | スター点。型番未確定 |
| `+5V_TEENSY_F` | D101 `PMEG2010EA,115` | A | 2 | F205後(3.2節) | SOD-323 **pin 1=K、pin 2=A**(DS照合)。KiCad `Device:D_Schottky`(pin1=K)+`Diode_SMD:D_SOD-323`で向き一致 |
| `VIN_TEENSY` | D101 | K | 1 | Teensy pad 48、D102-K、TP103 | |
| `TEENSY_VUSB` | D102 `PMEG2010EA,115` | A | 2 | J102 | J102=1pinパッド/TP(提案)。Teensy裏面VUSBパッドからの引出し方法は未確定 |
| `VIN_TEENSY` | D102 | K | 1 | 同上 | |
| `TEENSY_VUSB` | U102 `TPS259470ARPWR` | IN | 5 | J102、D102-A、C106 | **2026-09-26追加。** USB→`+5V_SYS`給電用eFuse。U101と同じRPW0010A。auto-retry(`A`)版 |
| `+5V_SYS` | U102 | OUT | 6 | C107、スター点 | U101 OUTと同じネット。両者のtrue RCBで互いに逆流しない |
| `GND_CTRL` | U102 | GND | 8 | GNDプレーン | |
| `USB_EFUSE_EN` | U102 | EN/UVLO | 1 | R108(IN側)、R109(GND側) | UVLO約3.98V。フロート禁止 |
| `USB_EFUSE_OVLO` | U102 | OVLO | 2 | R110(`+5V_RAW`側)、R111(GND側) | **外部5V優先の切替入力。** `+5V_RAW`≥4.41VでU102出力OFF |
| - | U102 | AUXOFF | 3 | **No Connect** | |
| `PWR_USB_FAULT_N` | U102 | FLT | 4 | R112 10kΩ→`+3V3_TEENSY`、Teensy pad 11(pin 9)、TP106 | open-drain、Low=過電流/過熱/逆流。pin 9は旧NC予約を転用(提案) |
| `USB_EFUSE_DVDT` | U102 | dVdt | 7 | C108 10nF→GND | 約25ms立上り。USB突入を約0.2V/ms×負荷容量に抑える |
| `USB_EFUSE_ILM` | U102 | ILM | 9 | R107 3.32kΩ 1%→GND | ILIM 0.85/1.007/1.15A(DS表)。フロート禁止 |
| - | U102 | ITIMER | 10 | **No Connect** | U101と同じ |
| `TEENSY_VUSB`→`USB_EFUSE_EN` | R108 232kΩ 1% | | | | |
| `USB_EFUSE_EN`→GND | R109 100kΩ 1% | | | | |
| `+5V_RAW`→`USB_EFUSE_OVLO` | R110 100kΩ 1% | | | | |
| `USB_EFUSE_OVLO`→GND | R111 37.4kΩ 1% | | | | |
| `TEENSY_VUSB` | C106 1uF 0603 X7R | | | GND | U102 IN直近。USB規格上VBUS側容量は10uF以下に抑える |
| `+5V_SYS` | C107 1uF 0603 X7R | | | GND | U102 OUT直近 |

設計値の根拠(DS照合、TPS25947 SLVSFC9C):

- UVLO/OVLO: `VUVLO(R)=VOV(R)=1.20V typ`。`VIN_UV = 1.20 × (732+51.1+221)/(51.1+221) = 4.43V`、`VIN_OV = 1.20 × (732+51.1+221)/221 = 5.45V`。分圧漏れ電流 ≈ 5V/1.0MΩ = 5µA。
- ILM: DS電気特性表に`RILM=750Ω → ILIM 3.96 / 4.452 / 4.84 A (min/typ/max)`の直接記載あり。
- dVdt: `CdVdt[pF] = 2000 / SR[V/ms]`。10nF → 0.2V/ms → 5Vで約25ms。
- ラッチ動作: `TPS259470L`は故障後ラッチオフ。復帰はVINを0Vへ落とす電源断、またはEN/UVLOを`VSD(F)`(0.74V typ)未満へ引く操作。**本回路はENが入力分圧固定なので復帰手段は電源断のみ**。運用手順へ明記する。
- 絶対最大: IN 28V、負電圧-15V。24V側サージを5Vへ通さないのはSD-25B-5側の責務。

U102(USB→`+5V_SYS`、2026-09-26追加)の根拠(同DS):

- 目的: USBだけでCAN x3(トランシーバVCC=`+5V_SYS`)とノード1基分の枝5Vを動かす。以前のD102だけの構成ではTeensyしか起動せず、CANは動かなかった。
- ILIM: DS表`RILM=3.32kΩ → 0.850 / 1.007 / 1.150 A`。電流の目安はTeensy約0.1A、中央TCAN1051 x3、ユニット1基で合計0.4〜0.8A(実測で確定)。2基目をつなぐと電流制限へ入る想定。
- auto-retry版を選ぶ理由: 過負荷で過熱停止した後、USBを挿し直さなくても自動で復帰する。latch版(`L`)でも同じfootprint。
- 外部5V優先: OVLOピンは`VOV(R)=1.20V`を超えると出力OFF、`VOV(F)=1.09V`を下回るとON。`R110/R111=100k/37.4k`で`+5V_RAW`の閾値はrising 4.41V / falling 4.00V。U101のUVLO 4.43Vとほぼ同じ点で切り替わる。`+5V_RAW`=5.46V(U101 OVLO)時のOVLOピン電圧は1.49Vで、推奨上限1.5V以内(絶対最大6.5V)。
- `+5V_RAW`が無い時: U101は逆流阻止中なので`+5V_RAW`は分圧で0V付近に保たれ、U102はON。
- 逆流: 外部5V運用中はU102がOFFで、OUT→INの漏れは最大443µA(`IOUTLKG(OVLO)`)。PCのVBUSへはほぼ流れない。
- UVLO: `R108/R109=232k/100k`で`VIN_UV = 1.20 × 332/100 = 3.98V`。ケーブル降下で下がったVBUSでも起動する。ENはVIN<5Vなら直結も許容(DS 6.3 Note 2)だが、UVLOを明示するため分圧にする。
- 切替時のTeensy: 外部5Vの抜き差しの瞬間は`+5V_SYS`がdVdt分(約25ms)落ちる。D102がVUSBからVINを保持するので、TeensyのUSB接続は切れない(ノード側はリセットされ得る)。
- 注意: `TCAN1051V`のVCCは4.5V min。USB単独時はVBUS(4.75V min) − ケーブル降下 − eFuse損失になるので、短く太いケーブルを使う。`+5V_SYS`をTP102で実測して4.5V以上を確認する。

### 3.2 S02B スター分配・Teensyソケット(2xx)

枝(全てPPTC後ネットを枝間で共通化しない):

| 枝 | PPTC | 保護後Net | コネクタ/接続先 | LED+R | TP |
|---|---|---|---|---|---|
| Unit 1 | F201 `1206L050/15YR` | `+5V_UNIT1` | J201 `SM02B-GHS-TB` 1=5V、2=`GND_CTRL` | D201 `LTST-C190KGKT` + R201 1.5kΩ | 省略（2026-09-26） |
| Unit 2 | F202 同 | `+5V_UNIT2` | J202 同 | D202 + R202 | 省略（2026-09-26） |
| Unit 3 | F203 同 | `+5V_UNIT3` | J203 同 | D203 + R203 | 省略（2026-09-26） |
| Odometry | F204 同 | `+5V_ODOM` | J204 同 | D204 + R204 | TP214 |
| Teensy | F205 `1206L075/16WR`(初期値、定格review) | `+5V_TEENSY_F` | D101 A(3.1節) | D205 + R205 | TP215 |
| Expansion | F206 `1206L050/15YR`(初期値、定格review) | `+5V_EXP` | J323-1(3.3節)、外部5V出力 | D206 + R206 | TP216 |

LED結線は`+5V_x → R(1.5kΩ) → LED A→K → GND_CTRL`。枝LEDは「PPTC後に電圧がある」表示であり、ノード正常表示ではない(シルクに枝名)。

2026-09-26ユーザー指定: 駆動Unit 1〜3の給電枝TP211〜TP213は省略。給電状態は枝LEDで確認し、電圧実測はJ201〜J203の電源/GND接点で行う。LED点灯は正確な電圧値を保証しない。

Teensy 4.1ソケット: 2列×24pin、列中心間15.24mm、pad 1=左列USB端、pad 48=右列USB端。

- symbol: 48pin単一シンボル`DifferentialSwerve:Teensy41_Socket`を自作し**pin番号=socket pad番号**にすることを推奨(KiCad 10標準ライブラリにTeensy 4.1シンボルは無い)。代替は`Connector_Generic:Conn_01x24` x2で、J210=pad 1〜24、J211=pad 25〜48(**J211のpin n = pad n+24**、読み替え表を回路図に注記)。
- footprint: `Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical` x2(Sullins `PPPC241LFBN-RC`/`PPTC241LFBN-RC`)。Teensy直下は部品・TP・露出銅を全面禁止、micro USB/Program/microSDの操作空間を確保。
- 組立工程: VUSB-VINパッド切断と導通検査(diode-OR追加後も必須)。

socket pad → Rev.1ネット(`TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`(Rev.A)を基に、Rev.1で機能が消えたピンを(提案)で更新):

| pad | Teensy表示 | Rev.1ネット | 方向 | 備考 |
|---:|---|---|---|---|
| 1 | GND | `GND_CTRL` | PWR | |
| 2 | 0 | `CAN2_RX` | In | CRX2 |
| 3 | 1 | `CAN2_TX` | Out | CTX2 |
| 4 | 2 | `MOTOR_PWR_EN` | Out | 別体`CONTACTOR_DRIVER`への3.3V ON/OFF。起動時Low、外付けpulldownでReset/Hi-Z時もMOSFET OFF |
| 5 | 3 | `ESTOP_LOOP_OK_N` | In | 4xx |
| 6 | 4 | `ESTOP1_AUX_OK_N` | In | 4xx |
| 7 | 5 | `ESTOP2_AUX_OK_N` | In | 4xx |
| 8 | 6 | `REARM_SW_N` | In | SW211 |
| 9 | 7 | `STATUS_G_LED` | Out | D211(RUN) |
| 10 | 8 | `STATUS_R_LED` | Out | D212(ERR) |
| 11 | 9 | `PWR_USB_FAULT_N` | In | U102 FLT(Low=USB側過電流/過熱/逆流)。2026-09-26提案。旧Rev.A `AUX_OUTPUT_EN`枠を転用 |
| 12 | 10 | `SPI_CS0_N` | Out | 5xx |
| 13 | 11 | `SPI_MOSI` | Out | 5xx |
| 14 | 12 | `SPI_MISO` | In | 5xx |
| 15 | 3.3V | `+3V3_TEENSY` | PWR out | PWR_FLAG |
| 16 | 24/A10 | `IO24_A10` | I/O | 5xx |
| 17 | 25/A11 | `IO25_A11` | I/O | |
| 18 | 26/A12 | `IO26_A12` | I/O | |
| 19 | 27/A13 | `IO27_A13` | I/O | |
| 20 | 28 | `UART7_RX` | In | |
| 21 | 29 | `UART7_TX` | Out | |
| 22 | 30 | `CAN3_RX` | In | CRX3(CAN FD) |
| 23 | 31 | `CAN3_TX` | Out | CTX3 |
| 24 | 32 | `PWR_5V_FAULT_N` | In | U101 FLT |
| 25 | 33 | NC | - | 確定(未使用、TP無し) |
| 26 | 34 | `UART8_RX` | In | |
| 27 | 35 | `UART8_TX` | Out | |
| 28 | 36 | `SPI_CS1_N` | Out | |
| 29 | 37 | NC | - | 確定 |
| 30 | 38 | NC | - | 確定 |
| 31 | 39 | NC | - | 確定 |
| 32 | 40/A16 | `IO40_A16` | I/O | |
| 33 | 41/A17 | `IO41_A17` | I/O | |
| 34 | GND | `GND_CTRL` | PWR | |
| 35 | 13 | `SPI_SCK` | Out | オンボードLED併用。安全入力に使わない |
| 36 | 14/A0 | **NC(予約)** | - | Rev.A `MOTOR_PWR_SENSE`。24Vモータバスは中央PCBへ入れない方針のため未使用(提案) |
| 37 | 15/A1 | NC | - | Rev.A `BAT_MON_ALERT_N`予約。Matek GH4にALERTは無い |
| 38 | 16/A2 | `I2C1_SCL` | I/O | |
| 39 | 17/A3 | `I2C1_SDA` | I/O | |
| 40 | 18/A4 | `I2C0_SDA` | I/O | Matek+拡張 |
| 41 | 19/A5 | `I2C0_SCL` | I/O | |
| 42 | 20/A6 | `IO20_A6` | I/O | |
| 43 | 21/A7 | `IO21_A7` | I/O | |
| 44 | 22/A8 | `CAN1_TX` | Out | CTX1 |
| 45 | 23/A9 | `CAN1_RX` | In | CRX1 |
| 46 | 3.3V | `+3V3_TEENSY` | PWR out | |
| 47 | GND | `GND_CTRL` | PWR | |
| 48 | VIN | `VIN_TEENSY` | PWR in | D101/D102カソード |

状態LED・REARM(全て3.3V論理):

| Net名 | 部品 | 接続 | 備考 |
|---|---|---|---|
| `STATUS_G_LED` | R211 1kΩ → D211 `LTST-C190KGKT`緑 → GND | pad 9 | シルク`RUN` |
| `STATUS_R_LED` | R212 1kΩ → D212 `LTST-C190KRKT`赤 → GND | pad 10 | シルク`ERR` |
| `+5V_SYS` | R213 1.5kΩ → D213 `LTST-C190KGKT`緑 → GND | GPIOなし | シルク`PWR` |
| `COMM` LED | **未確定** | GPIO割当なし | PDF S05の`PWR/RUN/COMM/ERR`のうちCOMMは駆動元が無い。DNP footprintか不採用かを8章で決める |
| `REARM_SW_N` | SW211 タクトSW(1端=`REARM_SW_N`、他端=GND)、R214 10kΩ→`+3V3_TEENSY`、C211 100nF→GND | pad 8 | SW型番・基板/パネル配置は未確定(CTR-20) |
| `+3V3_TEENSY` | C212 100nF | socket pad 15/46直近 | 提案 |

### 3.3 S03 CAN x3(31x=CAN1 Sensor、32x=CAN2 Expansion、33x=CAN3 Drive)

同一回路。表はバスx(1/2/3)の一般形で、RefDesは`3x1`等と読む。

| Net名 | 部品 | ピン名 | ピン番号 | 接続先 | 備考 |
|---|---|---|---|---|---|
| `CANx_TX` | U3x1 `TCAN1051VDRQ1` | TXD | 1 | Teensy(下表) | 3.3V論理 |
| `GND_CTRL` | U3x1 | GND | 2 | GND | |
| `+5V_SYS` | U3x1 | VCC | 3 | C3x1 100nF→GND | ピン直近 |
| `CANx_RX` | U3x1 | RXD | 4 | Teensy | |
| `+3V3_TEENSY` | U3x1 | VIO | 5 | C3x2 100nF→GND | **VIOをNC/5Vにしない** |
| `*_COMM_B` | U3x1 | CANL | 6 | D3x1、R3x1/SW3x1、J3x1-2/J3x2-2 | |
| `*_COMM_A` | U3x1 | CANH | 7 | D3x1、J3x1-1/J3x2-1 | |
| `GND_CTRL` | U3x1 | S | 8 | GND直結 | **フロート禁止**(Normal mode) |
| `*_COMM_A` | D3x1 `ESD2CAN24DBZRQ1` | IO_1 | 1 | | 1/2=ライン(区別なし)、3=GND。コネクタ直近 |
| `*_COMM_B` | D3x1 | IO_2 | 2 | | |
| `GND_CTRL` | D3x1 | GND | 3 | | |
| `*_COMM_A` | R3x1 120Ω `RC0603FR-07120RL` | | | SW3x1 COM(pin 2) | 終端: COMM_A—120Ω—SW—COMM_B |
| `*_COMM_B` | SW3x1 `JS102011SAQN` | throw | 3(N.O.)または1 | | COMと片側throwのみ使用、逆側throwはNC。シルク`TERM ON/OFF`。どちらのthrowをONにするかはfootprint/シルク方向で決める(未確定#12相当) |
| `*_COMM_A` | J3x1 / J3x2 `SM03B-GHS-TB` | | 1 | | 横挿しGH3 x2をIN/OUT区別なく並列。シルク`COMM_A` |
| `*_COMM_B` | J3x1 / J3x2 | | 2 | | |
| `GND_CTRL` | J3x1 / J3x2 | | 3 | | GND参照線を省略しない |

バス別の差分:

| バス | RefDes | Teensy TX(pad) | Teensy RX(pad) | バスNet | 通信 | 追加 |
|---|---|---|---|---|---|---|
| CAN1 Sensor | 311系 | pin 22(pad 44) | pin 23(pad 45) | `SENSOR_COMM_A/B` | Classic 1Mbps | - |
| CAN2 Expansion | 321系 | pin 1(pad 3) | pin 0(pad 2) | `EXP_COMM_A/B` | Classic 1Mbps | J323 4pinポート |
| CAN3 Drive | 331系 | pin 31(pad 23) | pin 30(pad 22) | `DRIVE_COMM_A/B` | CAN FD 1M/2M BRS | 差動100Ω、スタブ10mm以下 |

J323 汎用CAN拡張ポート(確定: 2026-09-12「中央基板 汎用CAN拡張ポート」。CAN2への配置は`ACTUATOR_CAN_NODE_REQUIREMENTS.md`が「central CAN2 port」からGH4pin `PWR_5V_CTRL/GND_CTRL/COMM_A/COMM_B`で5VとCANを受けると定めたことで確定扱い): `SM04B-GHS-TB`、**1=`+5V_EXP`、2=`GND_CTRL`、3=`EXP_COMM_A`、4=`EXP_COMM_B`**(憲法の順序5V/GND/CANH/CANL)。アクチュエータノードのロジック5V(F303K+TCAN+74AHCT)はこの枝(F206)から供給される。ユニット/オドメトリ用の内部ハーネスはGH2電源+GH3 CANの分離方式を維持し、この4pinを使わない。

各バスのGH3を2個にするか1個にするか(CTR-21)は7章の未確定事項。回路図では上記(GH3 x2 + CAN2にJ323)で描き、削減はレビュー後に行う。

### 3.4 S04 E-stop集約・絶縁監視・別体CONTACTOR_DRIVER interface(4xx)

**以下は旧6pin・別体driver案の履歴（採用禁止）。現行は後段の2026-09-26更新および CENTRAL_NONPOWER_WIRING_2026-09-29.md を参照。**

旧J401 `ESTOP_CTRL`(6pin):

| pin | Net | 用途 |
|---:|---|---|
| 1 | `ESTOP_LOOP_FEED` | NC直列ループへの往路(24V)。基板上はJ403-1(`+24V_CTRL_IN`)から銅箔で直通(提案B) |
| 2 | `ESTOP_LOOP_RETURN` | E-stop 1/2のNC接点を通過した復路。J402のcoil-loop pinへ直通、LTV ch1がタップ |
| 3 | `+24V_CTRL_LED` | ボタン内蔵LED・補助接点用24V(安全ループとは別保護) |
| 4 | `GND_CTRL_LED` | LED・補助接点の帰路 |
| 5 | `ESTOP1_AUX_RETURN` | E-stop 1補助接点(NC)の戻り。パネル側で`+24V_CTRL_LED → 補助接点 → pin 5` |
| 6 | `ESTOP2_AUX_RETURN` | E-stop 2補助接点の戻り |

J402は、アクチュエータCANノードから切り離して使う別体`CONTACTOR_DRIVER`へのinterfaceとする。コンタクタはCAN指令で直接励磁せず、中央Teensyの`MOTOR_PWR_EN` 3.3V ON/OFFをdriverのゲートバッファへ渡す。J402/J403の**コネクタ型式と最終pin順は未確定**だが、必要信号は次のとおり:

| コネクタ | pin | Net | 意味 |
|---|---:|---|---|
| J402(→別体`CONTACTOR_DRIVER`) | 1 | `PWR_5V_CTRL` | driverの`74AHCT1G125`用5V。中央側の保護済み5V枝から供給 |
| J402 | 2 | `MOTOR_PWR_EN` | Teensy pin 2の3.3V ON/OFF。driver入力にpulldownを置く |
| J402 | 3 | `ESTOP_LOOP_RETURN` | NC直列通過後、driverの`COIL+`へ出る24V |
| J402 | 4 | `GND_CTRL` | driverロジック/MOSFET sourceの基準。分電盤スターとの結合を1点に保つ |
| J402 | 5 | `CONTACTOR_STATUS_N` | 任意status。未実装時はNC |
| J403(24V_CTRL入力) | 1 | `+24V_CTRL_IN` | 24V制御系分電(ヒューズ後)から**入る**。基板上で`ESTOP_LOOP_FEED`と`+24V_CTRL_LED`へ分岐 |
| J403 | 2 | `GND_CTRL_LED` | 24V側帰路 |

- 旧PDFの「アクチュエータCANノードがCAN指令で励磁」は誤り。CANノードと別体`CONTACTOR_DRIVER`を分離し、中央3.3V信号を直接使う。
- `+24V_CTRL_IN`から`ESTOP_LOOP_FEED`と`+24V_CTRL_LED`への分岐にRev.Aの「F1(ループ)/F2(LED)分離ヒューズ」を復活させるか(F401/F402 footprint)、ヒューズは全て基板外とするかも7章#3。
- J402は5線ロック付き、J403は2線ロック付きとし、誤挿入できないシリーズ/極数を選ぶ。J402の正式型式はdriver回路図と同時に確定する。
- 基板上のループ経路(J403-1→J401-1、J401-2→J402-3)は**半導体を挟まない銅箔(+必要ならヒューズ)だけ**にする。コイルを切るQ1は別体driver側に置く。
- `MOTOR_PWR_EN`は中央基板上で24Vをスイッチしない。3.3VロジックとしてJ402-2へ出し、driver側`74AHCT1G125`、100Ω gate resistor、100k input/gate pulldownを経て`IRLML0100TRPBF`を駆動する。
- 24V配線の沿面/空間距離を基板端の24V I/O領域に閉じ込め、5V/3.3V領域と分離する。

U401 `LTV-817S`（2026-09-26確定、1ch）。Lite-On DS-70-96-0016 Rev.Nの内部接続図・CTR・外形を確認。

| 端子 | 接続 |
|---|---|
| 1 A | ESTOP_LOOP_RETURN → R401 2.2k → R402 2.2k → U401-1 |
| 2 K | GND_CTRL_LED |
| 4 C | ESTOP_LOOP_OK_N → Teensy pad5(pin3)、TP401、R409 10k → +3V3_TEENSY |
| 3 E | GND_CTRL |

D401 1N4148WはA=U401-2、K=U401-1の逆並列。24V時IF約5.2mA、各2.2k抵抗約60mW。Low=ループ成立、High=ループ開放または24Vなし。NC接点の直列コイル遮断はMCUを通さない。

- ボタン別補助接点・予備入力は省略。R403〜R408/R410〜R412、D402〜D404、TP402〜TP405を削除。
- J401は4pin: 1=ESTOP_LOOP_OUT、2=ESTOP_LOOP_RETURN、3=ESTOP_LED_24V、4=GND_CTRL_LED。正式MPN未確定。旧6pinコネクタは採用しない。
- J402コンタクタ側はCOIL_POS/COIL_NEGの2線。主接点フィードバックは設けない。
- U401 footprintは標準`Package_DIP:SMDIP-4_W9.53mm`を候補として割当。メーカー外形はpitch2.54mm、端子先端スパン10.16±0.3mm。購入実物との照合をPCB作業前に行う。
- GND_CTRL_LEDとGND_CTRLの基板上結合方針は従来どおり未確定。フォトカプラ採用だけでシステム全体のガルバニック絶縁を保証しない。

### 3.5 S05 I/O・監視・拡張(5xx)

信号順序は全て **コネクタ → TVS(SRV05-4) → 100Ω直列 → Teensy**。コネクタ側ネットは`_EXT`、Teensy側は無印。

コネクタ:

| RefDes | 型番 | pin順 | Net | 備考 |
|---|---|---|---|---|
| J501(旧J20) | `SM04B-GHS-TB` Matek `I2C-INA-BM` | 1 GND / 2 SDA / 3 SCL / 4 5V | `GND_CTRL` / `I2C0_SDA_EXT` / `I2C0_SCL_EXT` / `+5V_SYS` | Matekは5Vピンに4〜9Vが必要。**3.3V枝に繋がない**。addr既定0x45。モジュール側pull-upが3.3V基準であることを通電前に実測(確定) |
| J502 | `SM04B-GHS-TB` I2C0拡張 | 1 3V3 / 2 GND / 3 SDA / 4 SCL | `+3V3_TEENSY` / `GND_CTRL` / `I2C0_SDA_EXT` / `I2C0_SCL_EXT` | J501と同一I2C0バス |
| J503 | `SM04B-GHS-TB` I2C1拡張 | 同上 | `I2C1_SDA_EXT` / `I2C1_SCL_EXT` | |
| J504 | `SM03B-GHS-TB` UART7 | 1 GND / 2 TX / 3 RX | `GND_CTRL` / `UART7_TX_EXT` / `UART7_RX_EXT` | TX=Teensy送信(基板視点) |
| J505 | `SM03B-GHS-TB` UART8 | 同上 | `UART8_TX_EXT` / `UART8_RX_EXT` | |
| J506 | `SM07B-GHS-TB` SPI | 1 3V3 / 2 GND / 3 SCK / 4 MOSI / 5 MISO / 6 CS0_N / 7 CS1_N | `SPI_*_EXT` | |
| J507〜J510 | `SM04B-GHS-TB` GPIO/ADC 4pin×4組 | 各1 VCC / 2 GND / 3〜4 IO | J507=IO20/21、J508=IO24/25、J509=IO26/27、J510=IO40/41（各_EXT）。全組JP505共通VCC | `VCC 3V3/5V`、`IO 3.3V ONLY` |

3.3V外部負荷はJ502/J503/J506/J507〜J510合計100mA以下(確定)。J507を5Vにした時は`+5V_EXP`(F206 0.5A、J323と共用)から取る。

#### GPIO電源の列切替(2026-09-26ユーザー確定)

GPIOコネクタの電源ピンを、**コネクタ列全体でジャンパ1個**で3.3V/5Vに切り替える。ピンごとの切替はスペースを取るので行わない。**切り替えるのは電源ピンだけで、IO信号は3.3Vのまま**(Teensy 4.1は5V非対応)。5V電源で動き、3.3V信号を出すセンサ向け。

```text
+3V3_TEENSY ── JP505-1
                JP505-2 ── VCC_GPIO_EXT ── J507-1(GPIOが複数コネクタになった場合は全VCCピン)
+5V_EXP     ── JP505-3
ショートピン: 1-2=3.3V(出荷時)、2-3=5V
```

| RefDes | 部品 | 接続 | 備考 |
|---|---|---|---|
| JP505 | 2.54mm 1x3ピンヘッダ+ショートピン(型番は在庫で確定) | 1=`+3V3_TEENSY`、2=`VCC_GPIO_EXT`、3=`+5V_EXP` | 出荷時は1-2(3.3V)。シルクに`3V3`/`5V`の向きを表示 |

- 3パッドのはんだジャンパではなくピンヘッダにした理由: ショートピン1個なら構造上3.3Vと5Vを同時に繋げない。はんだジャンパは1-2のパターンを切り忘れて2-3を繋ぐと、3.3Vと5Vがショートする。
- `SRV05-4`(U505/U506)のpin 5は`+3V3_TEENSY`のまま。5V電源側にしても、IO側のクランプ基準は3.3V。
- CTR-22でGPIOがGH4 x4案(各1=VCC)になった場合も、4個の1番ピンを全部`VCC_GPIO_EXT`にしてJP505の1個で切り替える。
- I2C(J502/J503)とSPI(J506)の電源ピンは3.3V固定のまま(プルアップやIOレベルと合わせるため)。

TVS `SRV05-4`(SOT-23-6、pin 1/3/4/6=I/O、pin 2=GND、pin 5=VCC。KiCad `Power_Protection:SRV05-4`のpin番号を照合):

| RefDes | pin 1 | pin 3 | pin 4 | pin 6 | pin 2 | pin 5 |
|---|---|---|---|---|---|---|
| U501 | `I2C0_SDA_EXT` | `I2C0_SCL_EXT` | `I2C1_SDA_EXT` | `I2C1_SCL_EXT` | `GND_CTRL` | `+3V3_TEENSY` |
| U502 | `UART7_TX_EXT` | `UART7_RX_EXT` | `UART8_TX_EXT` | `UART8_RX_EXT` | 同 | 同 |
| U503 | `SPI_SCK_EXT` | `SPI_MOSI_EXT` | `SPI_MISO_EXT` | `SPI_CS0_N_EXT` | 同 | 同 |
| U504 | `SPI_CS1_N_EXT` | NC | NC | NC | 同 | 同 |
| U505 | `IO20_A6_EXT` | `IO21_A7_EXT` | `IO24_A10_EXT` | `IO25_A11_EXT` | 同 | 同 |
| U506 | `IO26_A12_EXT` | `IO27_A13_EXT` | `IO40_A16_EXT` | `IO41_A17_EXT` | 同 | 同 |

**pin 5は`+3V3_TEENSY`**(5Vではない)。3.3Vへ吊ることで通常HIGHで導通しない(確定)。

直列抵抗 100Ω 0603(全外部信号。`*_EXT` → R → 無印Net):

| 信号群 | RefDes |
|---|---|
| I2C0 SDA/SCL、I2C1 SDA/SCL | R511〜R514 |
| UART7 TX/RX、UART8 TX/RX | R521〜R524 |
| SPI SCK/MOSI/MISO/CS0_N/CS1_N | R531〜R535 |
| IO20/21/24/25/26/27/40/41 | R541〜R548 |

I2C pull-up 2.2kΩ(Teensy側Netと`+3V3_TEENSY`の間、**normally-open solder jumper**の内側):

| Net | R | JP |
|---|---|---|
| `I2C0_SDA` | R551 | JP501 |
| `I2C0_SCL` | R552 | JP502 |
| `I2C1_SDA` | R553 | JP503 |
| `I2C1_SCL` | R554 | JP504 |

I2C0はMatekモジュールがpull-upを持つ前提でJP501/502は開放のまま。外部デバイス側にpull-upが無い場合だけ閉じる。

アクティビティLED: Rev.1回路図では**描かない**(確定: footprintのみDNP。idle HIGHの単純タップは表示にならない)。将来のRC one-shot/バッファ回路確定後に追加。

テストポイント(電源/CANは`S1751-46R`、信号は1.0〜1.5mm露出パッド):

| TP | Net | シート |
|---|---|---|
| TP101〜TP106 | `+5V_RAW`、`+5V_SYS`、`VIN_TEENSY`、`GND_CTRL`、`PWR_5V_FAULT_N`、`PWR_USB_FAULT_N` | S02A |
| TP214〜TP216 | ODOM/Teensy/Expansionの各枝PPTC後。駆動TP211〜TP213は省略 | S02B |
| TP217/TP218 | `+3V3_TEENSY`、`GND_CTRL` | S02B |
| TP311/312、TP321/322、TP331/332 | 各バス`COMM_A`/`COMM_B` | S03 |
| TP401〜TP406 | `ESTOP_LOOP_OK_N`、`ESTOP1_AUX_OK_N`、`ESTOP2_AUX_OK_N`、`SPARE_24V_IN`、`SPARE_OK_N`、`GND_CTRL_LED` | S04 |
| TP501 | `GND_CTRL` | S05 |

憲法の最低限TP `24V / 5V / 3.3V / GND / CANH / CANL`は、24Vが基板上に無い(ループ通過のみ)ため`GND_CTRL_LED`+ループNetの露出は置かず、上記で代替する(提案)。

## 4. 部品一覧とKiCadライブラリ割当

KiCad 10標準ライブラリの存在は2026-09-14に確認済み。「自作」は`hardware/lib/DifferentialSwerve.*`へ追加する。

### IC・半導体

| RefDes | 型番 | パッケージ | Symbol | Footprint | 状態 |
|---|---|---|---|---|---|
| U101 | TI `TPS259470LRPWR` | RPW 10pin VQFN-HR 2x2mm | **自作**(1 EN/UVLO、2 OVLO、3 AUXOFF、4 FLT、5 IN、6 OUT、7 dVdt、8 GND、9 ILM、10 ITIMER) | **自作**: TI RPW0010A land pattern。9/14ドラフトの`WQFN-10-1EP_2x2mm_P0.5mm_EP0.75x1.6mm`は標準ライブラリに存在しない | DS照合済み(pin)。仮配置では`DifferentialSwerve:TPS25947_RPW_10Pin`を使用（2026-09-26、取得ランド形状を保持し番号整理） |
| U311/U321/U331 | TI `TCAN1051VDRQ1` | SOIC-8 | `DifferentialSwerve:TCAN1051VDRQ1` | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | 照合済み |
| D311/D321/D331 | TI `ESD2CAN24DBZRQ1` | SOT-23 | `DifferentialSwerve:ESD2CAN24DBZRQ1` | `Package_TO_SOT_SMD:SOT-23` | 照合済み |
| U401 | Lite-On `LTV-817S` | SMD DIP-4 | `Isolator:LTV-817S`（1 A、2 K、3 E、4 C） | `Package_DIP:SMDIP-4_W9.53mm`候補 | 購入実物照合待ち |
| U501〜U506 | `SRV05-4`(Littelfuse/Bourns/Semtech/onsemi同等) | SOT-23-6 | `Power_Protection:SRV05-4` | `Package_TO_SOT_SMD:SOT-23-6` | pin番号照合要 |
| D101/D102 | Nexperia `PMEG2010EA,115` | SOD-323 | `Device:D_Schottky` | `Diode_SMD:D_SOD-323` | pin1=K/pin2=A DS照合済み |
| D401〜D404 | `1N4148W` | SOD-123 | `Diode:1N4148W` | `Diode_SMD:D_SOD-123` | |
| D201〜D206、D211、D213 | `LTST-C190KGKT`緑 | 0603 | `Device:LED` | `LED_SMD:LED_0603_1608Metric` | |
| D212 | `LTST-C190KRKT`赤 | 0603 | 同上 | 同上 | |

### 受動部品(0603、指定なき抵抗は1%)

| RefDes | 値 | 型番/仕様 |
|---|---|---|
| R101 | 750Ω | Yageo `RC0603FR-07750RL`(発注時照合) |
| R102 / R103 / R104 | 732kΩ / 51.1kΩ / 221kΩ | `RC0603FR-07732KL` / `RC0603FR-0751K1L` / `RC0603FR-07221KL`(発注時照合) |
| R105、R214、R409〜R412 | 10kΩ | `RC0603FR-0710KL` |
| R106 | 0Ω(10nF時)/100Ω(22nF以上) | 提案 |
| R201〜R206、R213 | 1.5kΩ | `RC0603FR-071K5L` |
| R211、R212 | 1kΩ | `RC0603FR-071KL` |
| R311/R321/R331 | 120Ω | `RC0603FR-07120RL` |
| R401〜R408 | 2.2kΩ | `RC0603FR-072K2L` |
| R511〜R548(21本) | 100Ω | `RC0603FR-07100RL` |
| R551〜R554 | 2.2kΩ | `RC0603FR-072K2L` |
| C101 | 100uF/10V | 電解/ポリマー、型番未確定 |
| C102、C103 | 1uF X7R | `C1608X7R1E105K080AB`(25V、プロジェクト共通品) |
| C104 | 470uF/10V low-ESR | 型番未確定 |
| C105 | 10nF C0G | `C1608C0G1H103J080AA`(プロジェクト共通品) |
| C211、C212、C3x1、C3x2 | 100nF X7R | `GRM188R71A104KA01D`等 |

### 保護・スイッチ・コネクタ・その他

| RefDes | 型番 | Symbol | Footprint |
|---|---|---|---|
| F201〜F204、F206 | Littelfuse `1206L050/15YR` | `Device:Polyfuse` | `Fuse:Fuse_1206_3216Metric` |
| F205 | Littelfuse `1206L075/16WR`(定格review) | 同上 | 同上 |
| SW311/321/331 | C&K `JS102011SAQN` | `DifferentialSwerve:JS102011SAQN`(1=N.C.、2=COM、3=N.O.) | `DifferentialSwerve:JS102011SAQN`(図面照合未) |
| SW211 | タクトSW、型番未確定 | `Switch:SW_Push` | 未確定 |
| J101 | AMASS `XT30PW-M` | `Connector_Generic:Conn_01x02` | `Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal` |
| J102 | VUSB引込みパッド | `Connector:TestPoint`等 | 未確定 |
| J201〜J204 | JST `SM02B-GHS-TB` | `Conn_01x02` | `Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal` |
| J210/J211 | Sullins `PPPC241LFBN-RC` x2 | 自作`Teensy41_Socket`または`Conn_01x24` x2 | `Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical` x2 |
| J311/312、J321/322、J331/332 | JST `SM03B-GHS-TB` | `Conn_01x03` | `Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal` |
| J323、J501〜J503 | JST `SM04B-GHS-TB` | `Conn_01x04` | `Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal` |
| J504/J505 | JST `SM03B-GHS-TB` | `Conn_01x03` | 同上GH3 |
| J506 | JST `SM07B-GHS-TB` | `Conn_01x07` | `Connector_JST:JST_GH_SM07B-GHS-TB_1x07-1MP_P1.25mm_Horizontal` |
| J507〜J510 | JST `SM04B-GHS-TB` | `Conn_01x04` | `Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal` |
| J401 | 未確定、E-stop 4pin | `Conn_01x04` | 未割当。旧6pin品は採用しない |
| J402 | 未確定、コイル2線 | `Conn_01x02` | 未割当。中央搭載driverからCOIL_POS/COIL_NEGを出す |
| J403 | 未確定(提案: Molex `43650-0200`) | `Conn_01x02` | 未確定。24V制御入力 |
| JP501〜JP504 | solder jumper N.O. | `Jumper:SolderJumper_2_Open` | `Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm` |
| JP505 | 2.54mm 1x3ピンヘッダ+ショートピン | `Jumper:Jumper_3_Open` | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` |
| TP群 | Harwin `S1751-46R` / 露出パッド | `Connector:TestPoint` | `DifferentialSwerve:Harwin_S1751-46R` / `TestPoint:TestPoint_Pad_D1.5mm` |

GH相手側: `GHR-0xV-S`ハウジング+`SSHL-002T-P0.2`、AWG26。

## 5. 回路上の注意点(ERCで検出できないもの)

1. **LTV-847Sのチャネル対**。LED 1/2はTr 16/15、LED 7/8はTr 10/9(ミラー)。KiCad標準シンボルの各ユニットがこの対になっているかシンボルエディタで確認してから配置する。旧資料の「ch1=E9/C10」を見て「修正」しない。
2. **1N4148Wの向き**。LEDの逆並列(A=LEDカソード側)。順方向に置くと入力抵抗経由で常時導通し、LEDが点かず「常に接点開」に見える。
3. **TPS259470の分圧鎖**。R103はEN/UVLO–OVLO間であり、EN–GND間ではない。AUXOFF/ITIMERはNo Connect。FLTのpull-upは3.3V。故障ラッチの復帰は電源断のみ(EN固定分圧のため)。
4. **PMEG2010EAの向き**。D101はアノード=`+5V_TEENSY_F`(F205後)、D102はアノード=`TEENSY_VUSB`。KiCad `D_SOD-323`のpad 1=カソード。逆にするとUSB単独起動が不可、または5V系がUSBへ逆流する。
5. **VUSB-VINパッド切断**は組立手順の必須項目。切らないとD101/D102が無意味になり、PC USBと`+5V_SYS`が衝突する。
6. **TCAN1051VのSピン**はGND直結。フロートでSilent modeに入り通信不能になる。VIOは`+3V3_TEENSY`。
7. **SRV05-4 pin 5は3.3V**。5Vへ吊るとTeensy GPIOのHIGH(3.3V)より高い電圧までクランプしない。
8. **Teensy 3.3V(pad 15/46)は出力**。`+3V3_TEENSY`へ外部LDOや他電源を繋がない。PWR_FLAGを置き、power_outとして扱う。
9. **Teensy pin 13(pad 35)**はオンボードLED負荷があり、SPI SCK専用。安全入力に使わない。
10. **XT30PW-Mの極性**。footprint pad 1と実物「+」の対応をAMASS図面で確認。逆だとTPS259470の逆極性保護(-15V)で救われるが起動しない。
11. **J403→J401→J402のループは銅箔のみ**。抵抗・ダイオード・MOSFETを挟まない(ヒューズの要否だけ7章#3)。LTV ch1のタップは`ESTOP_LOOP_RETURN`から4.4kΩ経由で分岐するだけ。
12. **`GND_CTRL_LED`と`GND_CTRL`**。別ネットで描く。ERCは「未接続の電源」を警告し得るが、意図的。結合時はNet-Tie 1点(8章で決める)。
13. **各PPTC後のネットは共通化しない**。J201〜J204、J323、D101側を1本の`+5V`にまとめると枝保護が無意味になる。
14. **Teensy pad 4(pin 2)**は`MOTOR_PWR_EN` 3.3V出力。起動時Low、外付けpulldown、Reset/Hi-Zで別体driverのMOSFETがOFFになることを実測する。pad 11(pin 9)は`PWR_USB_FAULT_N`入力(2026-09-26提案)、pad 36(pin 14)はNC。
15. **I2C0のpull-up二重化**。Matekモジュール内蔵pull-upとJP501/502を同時に有効にしない。Matek側pull-up電圧が5Vだった場合はTeensy GPIOに5Vが掛かるので、通電前実測が必須。
16. **コネクタpin番号は基板面視**(JST図面=KiCad footprint番号)。嵌合面視では左右反転して見える。ハーネス圧着前に図面で照合。
17. **CAN終端のthrow側**。JS102011SAQNのCOM(pin 2)と片側throwだけ使い、シルクの`ON`方向とfootprintの物理位置を一致させる。

## 6. 電源・電流の目安(転記時の妥当性確認用)

| 項目 | 値 | 根拠 |
|---|---|---|
| eFuse過電流閾値 | 3.96 / 4.45 / 4.84 A | RILM=750Ω、DS表 |
| U102(USB側)過電流閾値 | 0.85 / 1.007 / 1.15 A | RILM=3.32kΩ、DS表 |
| U102 OFFになる`+5V_RAW` | rising 4.41V / falling 4.00V | 1.20V・1.09V × 137.4/37.4 |
| eFuse UVLO / OVLO(rising) | 4.43V / 5.45V | 1.20V × 分圧比 |
| 出力立上り | 約25ms(10nF) | CdVdt=2000/SR |
| `VIN_TEENSY` | 約4.65V(5V系)、約4.65V(USB) | PMEG2010EA VF≈0.35V@1A、Teensy VIN 3.6〜5.5V |
| LTV入力電流 | 約5.2mA@24V、6.5mA@30V | (V−1.2)/4.4kΩ |
| LTV入力抵抗損失 | 約60mW/個@24V | 0603 100mWの範囲 |
| 3.3V外部負荷合計 | ≤100mA | Rev.A確定 |
| 5V枝 | 0.5A hold(20℃)、高温derating | 1206L050/15YR |

## 7. 未確定事項(推測で描かないこと)

| # | 未確定内容 | 本書の暫定 | 決め方 |
|---:|---|---|---|
| 1 | J401/J402/J403のコネクタ型式 | J401=4pin、J402=コイル2pin、J403=24V入力2pin | 正式品と誤挿入対策を確定。現行pin順は2026-09-29配線記録。J403のXH footprintは暫定で採用確定ではない |
| 2 | 制御GNDと24V帰路の結合点 | 分電盤側の1点結合を維持 | J402/J403/driverを含む実ハーネスで第2結合点が無いことを導通確認 |
| 3 | ループ往路24VとLED 24Vの供給元 | 24V制御系分電から中央J403へ直接入力 | F401/F402復活要否とdriver側coil returnをハーネス図で確定 |
| 4 | Teensy pad 4/11/36(pin 2/9/14) | pad4=`MOTOR_PWR_EN`、pad11=`PWR_USB_FAULT_N`(2026-09-26提案)、pad36=NC | pin 2は起動時Low。driver入力pulldownを含めReset/Hi-Z OFFを試験 |
| 5 | CANポート数(CTR-21) | 各バスGH3 x2、CAN2にJ323(J323の配置はノード仕様書で確定扱い) | 中央基板を各バス端点にできるか、CANableサービス接続方法 |
| 6 | F205/F206の定格 | 0.75A / 0.5A | Teensy+拡張の実測電流と突入 |
| 7 | LTV-817S footprint | SMDIP-4_W9.53mm候補 | Lite-On図面確認済み、購入実物照合待ち |
| 8 | TPS259470 RPW symbol/footprint | 仮配置は10端子モデルとproject-local footprintへ修正済み | PCB実装時にステンシル開口・製造条件を確認 |
| 9 | COMM LED | 未実装 | DNP footprintを残すか、廃止か |
| 10 | REARMスイッチの位置・型番(CTR-20) | 基板上タクトSW | パネル配置なら基板はGH2で引き出す |
| 11 | Teensy VUSBパッドの引出し方法 | J102 1pinパッド | リード線 / ポゴピン / 裏面パッド直下のPCBパッド |
| 12 | LTV ch4予備入力の実装 | 抵抗・ダイオード実装、TPのみ | DNPにするか、コネクタを出すか |
| 13 | J501(Matek)とJ323の5V保護 | J501=`+5V_SYS`(正本)、J323=`+5V_EXP` | J501もF206後へ移すか |
| 14 | C101/C104の型番 | 未定 | 10V定格、リプル電流、高さ制約 |
| 15 | R106(dVdt直列100Ω) | 0Ω実装 | C105を22nF以上へ変えるなら100Ω |
| 16 | GPIOヘッダ形式(CTR-22) | GH10 x1(PDF S05どおり) | GH4 x4(3V3/GND/IO/IO)案との比較 |
| 17 | SW311等のON方向 | - | JS102011SAQN footprint(図面照合未)とシルクの整合 |
| 18 | TeensyのUSB→VUSB経路の電流上限(2026-09-26) | U102経由で最大約1.15Aが流れる前提 | PJRC Teensy 4.1回路図で、USBコネクタ→VUSB間の保護素子の有無と定格を確認。J102の引出し線は1A以上で選ぶ |
| 19 | USB単独時の実負荷(2026-09-26) | 0.4〜0.8A見込み | Teensy+CAN x3+ユニット1基の実測。PCのUSB2ポート(500mA)では不足し得るので、USB3ポートかセルフパワーハブを運用手順に書く |
| 20 | `TPS259470ARPWR`の在庫 | auto-retry版を指定 | 欠品なら`TPS259470LRPWR`(latch版、同footprint)で代替。その場合、過負荷後はUSB挿し直しで復帰 |

## 8. 参照回路図(ASCII。正は3章の接続表)

### 8.1 電源入力・eFuse・diode-OR

```text
J101 XT30PW-M                U101 TPS259470LRPWR                          スター点
 1 ●── +5V_RAW ──┬──┬────── 5 IN        6 OUT ──┬──┬── +5V_SYS ──┬── F201..F206 → 各枝
 2 ●──┐          │  │                           │  │              │
      │        C101 C102   1 EN/UVLO ◄─R102 732k─┘ C103 C104      └── F205 → +5V_TEENSY_F → D101 ─┐
     GND       100uF 1uF   2 OVLO ◄──R103 51.1k──┘(EN)   1uF 470uF                                 ├── VIN_TEENSY → pad 48
                            │      └──R104 221k──┐                    TEENSY_VUSB(J102) → D102 ─┘
                            │                   GND                   (VUSB-VINパッド切断)
                            9 ILM ──R101 750R── GND
                            7 dVdt ──R106 0R──C105 10nF── GND
                            4 FLT ──┬──────────────── PWR_5V_FAULT_N → pad 24
                                   R105 10k → +3V3_TEENSY
                            3 AUXOFF: NC   10 ITIMER: NC   8 GND: GND_CTRL

USB→+5V_SYS(2026-09-26追加)
J102 TEENSY_VUSB ──┬── C106 1uF ── GND        U102 TPS259470ARPWR
                   ├── D102 → VIN_TEENSY(上図)
                   └──────────────────────── 5 IN        6 OUT ──┬── C107 1uF ── +5V_SYS(スター点)
                     R108 232k ─ 1 EN/UVLO ─ R109 100k ─ GND
  +5V_RAW ── R110 100k ─ 2 OVLO ─ R111 37.4k ─ GND     (+5V_RAW≥4.41VでU102 OFF = 外部5V優先)
                            9 ILM ──R107 3.32k── GND   (ILIM≈1A)
                            7 dVdt ──C108 10nF── GND
                            4 FLT ──┬── PWR_USB_FAULT_N → pad 11(pin 9)、TP106
                                   R112 10k → +3V3_TEENSY
                            3 AUXOFF: NC   10 ITIMER: NC   8 GND: GND_CTRL
```

### 8.2 CAN(バスx共通)

```text
Teensy                U3x1 TCAN1051VDRQ1                    外部
CANx_TX ───────────► 1 TXD      CANH 7 ──┬──────┬────┬──● J3x1-1 COMM_A ── J3x2-1
CANx_RX ◄─────────── 4 RXD      CANL 6 ──┼──┐   │    └──● J3x1-2 COMM_B ── J3x2-2
+5V_SYS ──C3x1┐───── 3 VCC         S 8 ──┴─GND │       ● J3x1-3 GND ────── J3x2-3
+3V3 ─────C3x2┐───── 5 VIO                     │
GND ───────────────── 2 GND     D3x1 ESD2CAN24  R3x1 120R
                                1←COMM_A        │
                                2←COMM_B       SW3x1 COM(2)──throw──COMM_B   TERM ON/OFF
                                3←GND
CAN2のみ追加: J323 GH4  1=+5V_EXP 2=GND 3=EXP_COMM_A 4=EXP_COMM_B
配置順: コネクタ → TVS → トランシーバ、スタブ20mm以下(CAN3は10mm以下)
```

### 8.3 E-stop集約・絶縁監視(ch1。ch2/3/4も同形)

```text
24V制御系分電(fused)                    中央基板                                        操作パネル
 24V_CTRL ─► J403-1 ── +24V_CTRL_IN ──┬── ESTOP_LOOP_FEED ─────────────────────────► J401-1 ─► E-stop1 NC ─► E-stop2 NC ─┐
 24V GND  ─► J403-2 ── GND_CTRL_LED   └── +24V_CTRL_LED ──────────────────────────► J401-3 ─► 内蔵LED / 補助接点(NC) ─► J401-5/6 → ch2/ch3
                                                                                      J401-4 ◄── GND_CTRL_LED
別体 CONTACTOR_DRIVER (CANノードではない)
 J402-1 PWR_5V_CTRL ───────────────► 74AHCT1G125 VCC
 J402-2 MOTOR_PWR_EN (3.3V) ───────► input pulldown → gate buffer → Q1 IRLML0100
 J402-3 ESTOP_LOOP_RETURN ─────────► COIL+ → E228 24V coil → COIL- → Q1 drain
 J402-4 GND_CTRL ──────────────────► buffer GND / Q1 source
 J402-5 CONTACTOR_STATUS_N ────────► optional
                                               │
                                    R401 2.2k + R402 2.2k
                                               │
                                    ┌──────────┴─ A(1)  U401 ch1  C(16) ──┬── ESTOP_LOOP_OK_N → pad 5
                                    │ D401 1N4148W      K(2)      E(15) ──┼── GND_CTRL
                                    │  (逆並列)          │                R409 10k → +3V3_TEENSY
                                    └────────────────────┴── GND_CTRL_LED
往路(J403-1→J401-1)と復路(J401-2→J402-3)は銅箔のみ(ヒューズ要否は7章#3)。中央PCBは3.3V許可信号のみ出す。
コイル低側MOSFETとclampは別体driver側。フォトカプラ出力は診断専用。
```

### 8.4 拡張I/O(1信号の一般形)

```text
GHコネクタ pin ── SIG_EXT ──┬── R5xx 100R ── SIG ── Teensy pad
                            │                  │(I2Cのみ) R55x 2.2k ── JP50x(N.O.) ── +3V3_TEENSY
                       U50x SRV05-4 I/O
                       pin2=GND_CTRL  pin5=+3V3_TEENSY
```

## 9. 転記後のチェック手順

1. `.kicad_sch`保存後、3章の接続表とネットリストを突き合わせる(AI照合可: `kicad-check`スキル)。特にLTV-847S 16pin、TPS259470 10pin、Teensy 48padの1:1確認。
2. `kicad-cli sch erc`を実行し、0件へ収束させる。`GND_CTRL_LED`の意図的分離、Teensy 3.3V出力のPWR_FLAG、NCピン(pad 4/11/25/29/30/31/36/37、U101 pin 3/10、U504未使用I/O)を整理する。
3. 5章の17項目を目視レビューする。
4. BOM出力で個数照合: 100nF x8(C211/C212/C3x1/C3x2)、2.2kΩ x12(R401〜R408+R551〜R554)、100Ω x21、10kΩ x6、SRV05-4 x6、PPTC x6、GH2 x4/GH3 x8/GH4 x4/GH7 x1/GH10 x1。
5. 7章の未確定事項を正本(`ARCHITECTURE_DECISIONS.md`、`TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`、`CENTRAL_BOARD_REQUIREMENTS.md`)へ日付付きで反映してからPCBへ進む。

## 参照資料

- TI `TPS25947` datasheet SLVSFC9C Rev.C(2026-05): 5 Pin Configuration and Functions、6.5 Electrical Characteristics、7.3.2/7.3.3 UVLO/OVLO、7.3.5.1 dVdt、7.3.9 fault latch
- Lite-On `LTV-817/827/847 Series` BNS-OD-C131/A4: LTV-847/LTV-847S outline dimensions と内部接続図
- Nexperia `PMEG2010EA` product data sheet: pinning、IF(AV)、VF
- PJRC Teensy 4.1 pinout card(socket pad順序は`TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`の確定表)
- `hardware/lib/LIBRARY_MANIFEST.md`(TCAN1051V/ESD2CAN24/JS102011の照合記録)
