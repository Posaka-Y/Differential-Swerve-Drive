# 電気設計 進捗スナップショット

保存日: 2026-07-20

## 差動ステアユニット基板

回路構成とSTM32G474RET6ピン割当はほぼ確定。KiCad転記に進める状態。

- FDCAN1: PA11/PA12（中央CAN）
- FDCAN2: PB12/PB13（C620 CAN）
- AMT222A: SPI3 PC10/PC11/PC12 + CS PD2
- AMT222A Molex側の信号順を正とし、GH6変換ハーネスを作る
- Debug UART: J701-5=G474 PA2/TARGET_TX→debugger RX、J701-6=G474 PA3/TARGET_RX←debugger TX
- C620 CANはGHまたはSH 2pin、1=CAN_H、2=CAN_L候補。別経路でGND共通を保証する

残件: C620コネクタ正式型番、ID DIP正式型番、SPI直列R、基板外形/配置、実部品フットプリント照合。

## オドメトリ基板

IMUモジュール購入・現物確認まで回路図確定を保留。

- AMT102-V x3、Z相なし
- GH4: 1=5V、2=GND、3=A、4=B
- Wheel1 PA0/PA1=TIM2_CH1/CH2
- Wheel2 PA6/PA7=TIM3_CH1/CH2
- Wheel3 PB6/PB7=TIM4_CH1/CH2
- A/B 6chは`SN74LVC2G17DBVR` x3、3.3V給電、5.5V tolerant Schmitt入力で受ける。各ICに100nF
- 5V監視ADCはRev.A非実装。PC0もNC
- IMUはIC直載せずAliExpress等のSPIブレークアウト x1を機械的に剛結
- 複数IMU用の汎用拡張はRev.Aでは設けない
- IMU候補バス: SPI3 PC10/PC11/PC12、CS PD2、Data Readyは購入品確認後に空きGPIOへ

残件: IMU商品リンク/現物ピン順/電源/INT、AMT102入力の直列R・ESD・RC定数、基板外形。

## 中央Teensy 4.1基板

次の主要設計対象。進める順番はTeensyピン割当→5V入力/スター分配→CAN x3→E-stop/コンタクタ→監視回路→拡張/サービス端子。

- 将来の電磁弁・24V補助負荷ドライバは中央PCBに含めない
- 将来は別の24V出力ドライバ基板にMOSFET/フライバック/ヒューズ/診断を実装
- 中央との接続はCAN + ハード許可`AUX_OUTPUT_EN`
- 24V負荷電流は中央PCBを通さず分電点から供給

主要残件: Teensy全ピン割当、ソケット、5A主入力保護、コンタクタ正式型番/コイルドライバ、E-stop監視方式、電圧/電流監視、ヒューズ定格、基板外形。

## 生成済み資料

- `UNIT_BOARD_SCHEMATIC_WITH_BOM.pdf`
- `ODOMETRY_G474_PIN_ASSIGNMENT.pdf`
- `STM32G474_UNIT_BOARD_PIN_ASSIGNMENT.md`
- `STM32G474_ODOMETRY_PIN_ASSIGNMENT.md`
- `UNIT_BOARD_SCHEMATIC_REFERENCE.md`
