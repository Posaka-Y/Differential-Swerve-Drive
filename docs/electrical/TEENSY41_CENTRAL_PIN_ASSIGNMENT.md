> **2026-09-29:** Teensy使用40pad/予約NC8padの用途global labelを維持し、周辺回路を接続。GPIOの4pin×4組は[最新配線記録](CENTRAL_NONPOWER_WIRING_2026-09-29.md)のJ507〜J510に反映済み。GPIO4/5は個別E-stop監視廃止により予約。

# Teensy 4.1中央基板 ピン割当

> **2026-09-29ラベル反映:** 現行`central-board-placement`のJ210へ全使用端子の用途global labelを設定。GPIO4/5は個別E-stop監視廃止後の予約NC。予約NCはpad6/7/25/29/30/31/36/37。GPIO9/pad11のUSB faultは提案扱いを維持。誤記`READ_SW_N`を`REARM_SW_N`へ統一。現行対応は`tools/kicad/central-teensy-pinmap.json`と2026-09-29 PDF p05を参照。

> 2026-09-26更新: 本文の旧Rev.A表よりARCHITECTURE_DECISIONSとRev.1転記表を優先。Teensy pin9/socket pad11はUSB側eFuse U102の`PWR_USB_FAULT_N`入力候補へ変更（提案）。pin14/socket pad36はNC。旧AUX_OUTPUT_EN/MOTOR_PWR_SENSEは復活させない。pin2/socket pad4はMOTOR_PWR_ENを維持。GPIO端子の電源のみJP505で3.3V/5Vを一括選択し、IO信号は3.3V固定。 詳細: [Rev.1転記表](CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md)。

作成: 2026-08-04
対象: 中央制御基板 Rev.A

## 方針

- PJRC公式Teensy 4.1ピンカードの表面側スルーホール48pinだけを使う。
- CAN3はCAN FD対応の駆動バスへ固定し、CAN1をセンサー、CAN2を拡張へ使う。
- 安全入力、コンタクタ許可、電源監視は他の多重化機能より優先して専用化する。
- Teensy GPIOは3.3V専用で、5V tolerantではない。外部24V信号は必ず絶縁または保護回路を通す。
- pin 13はオンボードLED負荷があるためSPI SCK以外の安全入力には使わない。

## 固定ピン割当

「socket pad」は中央基板上のTeensyソケット用回路図pin番号であり、GPIO番号とは異なる。

| socket pad | Teensy pin | 信号 | 方向 | 用途 |
|---:|---:|---|---|---|
| 2 | 0 | `CAN2_RX` | In | 汎用拡張CAN受信 |
| 3 | 1 | `CAN2_TX` | Out | 汎用拡張CAN送信 |
| 4 | 2 | `MOTOR_PWR_EN` | Out | コンタクタ低側MOSFET許可。起動時Low |
| 5 | 3 | `ESTOP_LOOP_OK_N` | In | 直列NCループ監視。Low=ループ成立 |
| 6 | 4 | 未使用（旧ESTOP1） | - | 2026-09-26個別監視省略。予約、再割当なし |
| 7 | 5 | 未使用（旧ESTOP2） | - | 2026-09-26個別監視省略。予約、再割当なし |
| 8 | 6 | `REARM_SW_N` | In | 物理再アーム押しボタン。Low=押下 |
| 9 | 7 | `STATUS_G_LED` | Out | 基板状態LED緑 |
| 10 | 8 | `STATUS_R_LED` | Out | 基板状態LED赤 |
| 11 | 9 | `AUX_OUTPUT_EN` | Out | 外部24V出力基板のハード許可。起動時Low |
| 12 | 10 | `SPI_CS0_N` | Out | 汎用SPI CS0 |
| 13 | 11 | `SPI_MOSI` | Out | 汎用SPI MOSI |
| 14 | 12 | `SPI_MISO` | In | 汎用SPI MISO |
| 35 | 13 | `SPI_SCK` | Out | 汎用SPI SCK、TeensyオンボードLED併用 |
| 36 | 14/A0 | `MOTOR_PWR_SENSE` | Analog In | コンタクタ後24Vモータバス電圧 |
| 37 | 15/A1 | `BAT_MON_ALERT_N` | Reserve / NC | Matek I2C-INA-BMはGH4にALERTを出さないためRev.Aでは未使用 |
| 38 | 16/A2 | `I2C1_SCL` | I/O | 第2拡張I2C |
| 39 | 17/A3 | `I2C1_SDA` | I/O | 第2拡張I2C |
| 40 | 18/A4 | `I2C0_SDA` | I/O | Matek I2C-INA-BM＋第1拡張I2C |
| 41 | 19/A5 | `I2C0_SCL` | I/O | Matek I2C-INA-BM＋第1拡張I2C |
| 44 | 22/A8 | `CAN1_TX` | Out | センサーCAN送信、Classic 1Mbps |
| 45 | 23/A9 | `CAN1_RX` | In | センサーCAN受信、Classic 1Mbps |
| 20 | 28 | `UART7_RX` | In | デバッグ/拡張UART 1 |
| 21 | 29 | `UART7_TX` | Out | デバッグ/拡張UART 1 |
| 22 | 30 | `CAN3_RX` | In | 駆動CAN受信、CAN FD |
| 23 | 31 | `CAN3_TX` | Out | 駆動CAN送信、CAN FD |
| 24 | 32 | `PWR_5V_FAULT_N` | In | 5V主入力eFuse fault |
| 26 | 34 | `UART8_RX` | In | 拡張UART 2 |
| 27 | 35 | `UART8_TX` | Out | 拡張UART 2 |
| 28 | 36 | `SPI_CS1_N` | Out | 汎用SPI CS1 |

## 汎用GPIO/ADCヘッダ

Rev.Aでは次の8本を予約する。各ピンは直列100ohmを介してGHへ出し、外部から5Vを印加しない。

| socket pad | Teensy pin | シルク | 備考 |
|---:|---:|---|---|
| 42 | 20/A6 | `IO20_A6` | ADC可 |
| 43 | 21/A7 | `IO21_A7` | ADC可 |
| 16 | 24/A10 | `IO24_A10` | ADC/I2C2 SCL可 |
| 17 | 25/A11 | `IO25_A11` | ADC/I2C2 SDA可 |
| 18 | 26/A12 | `IO26_A12` | ADC可 |
| 19 | 27/A13 | `IO27_A13` | ADC可 |
| 32 | 40/A16 | `IO40_A16` | ADC可 |
| 33 | 41/A17 | `IO41_A17` | ADC可 |

Teensy pin 33、37、38、39はRev.Aでは未使用とし、ソケットpinへNo Connect（×）を付ける。基板内テストパッドにも引き出さない。

## 電源・ソケットpin

| socket pad | Teensy表示 | 接続 |
|---:|---|---|
| 1, 34, 47 | GND | `GND_CTRL` |
| 15, 46 | 3.3V | `+3V3_TEENSY`出力。外部から給電しない |
| 48 | VIN | 保護後`+5V_SYS` |

- VUSBは通常の48pinソケットに含めず、Teensy裏面のVUSB-VINジャンパを組立時に切断する。
- TeensyはPJRC推奨のSullins `PPPC241LFBN-RC`または`PPTC241LFBN-RC` 1x24 socket 2本へ挿入する。Teensy側header候補はAmphenol `68000-224HLF`。列中心間15.24mm、USB側の向きをシルクと組立図へ明記し、Teensy直下は裏面部品との干渉を避ける全面keepoutとする。
- Program/On-Off/VBAT/USB Host/Ethernetの追加pinはRev.Aでは接続しない。Teensy本体のProgramボタンとmicro USBへ組付け後もアクセス可能な配置にする。

## ファームウェアの初期状態

2026-09-26確定: 起動・reset・Hi-Z時は外付けpulldownでMOTOR_PWR_ENをLowへ保持。E-stop解除だけでは復帰しない。

再アームの共通条件:

1. ESTOP_LOOP_OK_Nが成立（個別ボタン監視は省略）。
2. GUI、駆動MCU3基、ODOMとの通信がfresh、他の停止原因なし。
3. 動作指令ゼロ。
4. GUIからの新規ARM要求、またはSW211の新規押下エッジ。

GUIとSW211は同じTeensy判定へ入れる。ARM成立時はMOTOR_PWR_ENをON、運転出力はゼロで保持。成立後の新しい運転要求だけで動作を許可する。停止で許可を破棄し、再起動・GUI再接続時も新規ARMを要求する。保持中ボタン・停止前要求・古い指令を再利用しない。

MOTOR_PWR_SENSEやコンタクタ補助接点は搭載しないため再アーム条件には使わない。コンタクタOFF中はC620無応答が正常なので、駆動MCUの通信正常とC620の応答を区別する。ARM後の運転開始にはC620立上がり・応答fresh確認を別途要求する。

判定コア: central_firmware/include/control/arm_controller.h。GPIO/USB/GUIアダプタは未実装。詳細: software/MINIPC_GUI_AND_TEENSY.md。

## 根拠資料

- PJRC, Teensy 4.1 pinout card Rev.3/Rev.4
- PJRC, Teensy 4.1 product page (3 CAN、CAN FD x1、3.3V I/O、VIN/VUSB注意)
- `docs/ARCHITECTURE_DECISIONS.md`
- `docs/communication/COMMUNICATION_NAMING_AND_IDS.md`
