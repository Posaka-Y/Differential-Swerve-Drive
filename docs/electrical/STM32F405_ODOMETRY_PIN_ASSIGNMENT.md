# STM32F405RGT6 オドメトリ基板ピン割当

> **2026-09-25 ODOM V2確定:** 基板側エンコーダ端子J4/J5/J6は **1=A、2=+5V、3=B、4=GND**。ユーザーがハーネスのねじれ回避のため変更した配列で、V2では本文の旧配列表に優先する。センサ側コネクタの番号とは区別する。

> **V2改版（2026-09-23着手）**: デバッグ・TP・V1修正の変更要件は[共通V2要件](UNIT_ODOMETRY_V2_REQUIREMENTS.md)を優先する。本文のGH6/SWD・UART一体配列はV1仕様。V2の正式ヘッダ型番とPCB配線は未確定/未完了。

対象はAMT102クアドラチャエンコーダ×3を使うオドメトリ基板の`STM32F405RGT6`(LQFP64)。Z相は使用しない。
2026-07-25、部室在庫の`STM32F405RGT6`採用に伴い`STM32G474_ODOMETRY_PIN_ASSIGNMENT.md`から書き換え。

> **正本**: ST公式[STM32F405xx/STM32F407xxデータシート DS8626 Rev.12](https://www.st.com/resource/en/datasheet/stm32f405vg.pdf)
> のLQFP64 pinout/pin definitionを正とする。
> KiCad 10標準`STM32F405RGTx`シンボルは転記先であり、データシートと照合してから使用する。

## AMT102×3の割当

G474版から**GPIO名は変更なし**。TIM2/TIM3/TIM4のCH1/CH2はG474・F405共通の標準AF配置である。
ただしLQFP64の物理pin番号とパッケージ上の位置はG474と異なるため、MCU周辺の部品配置・配線はF405 pinoutで引き直す。

| 測定輪 | AMT102信号 | タイマ入力 | GPIO | AF | 基板内接続 |
|---|---|---|---|---:|---|
| Wheel 1 | A | TIM2_CH1 | PA0 | AF1 | J801-3 → U801A `SN74LVC2G17DBVR` → PA0 |
| Wheel 1 | B | TIM2_CH2 | PA1 | AF1 | J801-4 → U801B `SN74LVC2G17DBVR` → PA1 |
| Wheel 2 | A | TIM3_CH1 | PA6 | AF2 | J802-3 → U802A `SN74LVC2G17DBVR` → PA6 |
| Wheel 2 | B | TIM3_CH2 | PA7 | AF2 | J802-4 → U802B `SN74LVC2G17DBVR` → PA7 |
| Wheel 3 | A | TIM4_CH1 | PB6 | AF2 | J803-3 → U803A `SN74LVC2G17DBVR` → PB6 |
| Wheel 3 | B | TIM4_CH2 | PB7 | AF2 | J803-4 → U803B `SN74LVC2G17DBVR` → PB7 |

AMT102コネクタJ801–J803はGH 4pinとし、1=5V、2=GND、3=A、4=B。`SN74LVC2G17DBVR`は3.3V給電とし、各ICに100nFを置く。ESD/直列抵抗/RC定数は未確定(G474版から継続の未決事項)。

## 共通インターフェース

| 用途 | MCU信号 | GPIO | AF | 接続先 | G474版からの変更 |
|---|---|---|---:|---|---|
| センサCAN RX/TX | CAN1_RX / CAN1_TX | PA11 / PA12 | AF9 | TCAN1051V RXD/TXD | ペリフェラルが`FDCAN`→`bxCAN`(Classic CAN専用)。GPIOは同じ |
| Debug UART TX/RX | USART2_TX / USART2_RX | PA2 / PA3 | AF7 | J701-5/J701-6 | ペリフェラルが`LPUART1`→`USART2`(AF番号も12→7)。GPIOは同じ |
| SWD | SWDIO / SWCLK | PA13 / PA14 | AF0 | J701-3/J701-2 | 変更なし |
| Reset | NRST | 専用ピン | - | J701-4, C313, TP | 変更なし(ピン名`PG10-NRST`→`NRST`はG474側の命名の違いで、F405も専用リセットピン) |
| ID | UNIT_ID0/1/2 | PC6 / PC7 / PC8 | GPIO | SW701; unitId=4 | 変更なし |
| LED | RUN/COMM/ERR | PA5 / PB10 / PB11 | GPIO | 状態LED | 変更なし |
| HSE | OSC_IN/OUT | PH0 / PH1 | - | 8 MHz水晶 | **PF0/PF1→PH0/PH1に移動**。unit board採用品とC0G 10pF初期値を流用し、F405実基板で確認 |
| Boot | BOOT0 | 専用ピン | - | 10 kΩ pull-down | **G474はPB8と共用GPIOだったが、F405は完全な専用ピン**。回路(10kΩプルダウン)は踏襲可 |
| SWO予約 | TRACESWO | PB3 | AF0 | TP | 変更なし |
| SPI IMU (候補) | SPI3_SCK/MISO/MOSI | PC10 / PC11 / PC12 | AF6 | 未確定IMUモジュール | クロック/データ線は変更なし |
| SPI IMU CS候補 | GPIO出力 | PD2 | GPIO | 未確定IMUモジュール | **G474版の割当を維持。F405 LQFP64にもPD2(pin 54)は存在する**。ハードウェアNSSが必要な場合のみPA15(AF6)を代替候補とする |
| SPI IMU割り込み | IMU_INT1 / IMU_INT2 | PC4 / PC5 | GPIO/EXTI | `ICM-42688-P`モジュール | INT1をData Readyに使用。INT2もヘッダから配線し予備割り込みとする |
| VCAP (新規) | VCAP_1 / VCAP_2 | 専用ピン | - | 2.2µF ×2(X5R/X7R、ESR < 2Ω) | **F405で新規必須。** 内蔵レギュレータ安定化用、省略不可 |

## 電源ピン

| 名称 | 個数目安 | 接続 | G474版からの変更 |
|---|---|---|---|
| VBAT | 1 | 3V3 + 100 nF | 変更なし |
| VDD | 4(pin 19/32/48/64) | 3V3 + 各pin 100 nF、パッケージ全体に4.7 µF以上 | F405の実pin数で確定 |
| VSS | 2(pin 18/63) | GND | VDDと1対1ではない。全pinを接続 |
| VDDA | 1 | FB経由VDDA_A + 100 nF + 1 µF | 変更なし |
| VREF+ | **無し** | ― | **LQFP64パッケージには専用ピンが無く、内部でVDDAに直結。** フットプリント・配線とも不要 |
| VSSA | 1 | GND | 変更なし |
| VCAP_1 / VCAP_2 | 2 | 各2.2 µF、ESR < 2Ωを直近からGNDへ | **新規追加(必須)** |

## LQFP64物理ピン番号

ST公式DS8626 Rev.12とKiCad 10標準シンボルを相互照合した値。

| 物理pin | 名称 | 用途 |
|---:|---|---|
| 1 | VBAT | 3V3 |
| 5 | PH0-OSC_IN | HSE |
| 6 | PH1-OSC_OUT | HSE |
| 7 | NRST | NRST |
| 13 | VDDA | VDDA(VREF+も内部でここに接続) |
| 14 | PA0-WKUP | TIM2_CH1 Wheel1 A |
| 15 | PA1 | TIM2_CH2 Wheel1 B |
| 16 | PA2 | USART2_TX |
| 17 | PA3 | USART2_RX |
| 18 | VSS | GND |
| 19 | VDD | 3V3 |
| 21 | PA5 | LED_RUN |
| 22 | PA6 | TIM3_CH1 Wheel2 A |
| 23 | PA7 | TIM3_CH2 Wheel2 B |
| 24 | PC4 | IMU_INT1 |
| 25 | PC5 | IMU_INT2予約 |
| 26 | PB0 | 未使用 |
| 29 | PB10 | LED_COMM |
| 30 | PB11 | LED_ERR |
| 31 | VCAP_1 | 2.2µF |
| 32 | VDD | 3V3 |
| 37 | PC6 | UNIT_ID0 |
| 38 | PC7 | UNIT_ID1 |
| 39 | PC8 | UNIT_ID2 |
| 41 | PA8 | 未使用 |
| 42 | PA9 | 未使用 |
| 43 | PA10 | 未使用 |
| 44 | PA11 | CAN1_RX |
| 45 | PA12 | CAN1_TX |
| 46 | PA13 | SWDIO |
| 47 | VCAP_2 | 2.2µF |
| 48 | VDD | 3V3 |
| 49 | PA14 | SWCLK |
| 50 | PA15 | SPI3_NSS代替候補 |
| 51 | PC10 | SPI3_SCK |
| 52 | PC11 | SPI3_MISO |
| 53 | PC12 | SPI3_MOSI |
| 54 | PD2 | SPI IMU CS候補 |
| 55 | PB3 | SWO予約 |
| 58 | PB6 | TIM4_CH1 Wheel3 A |
| 59 | PB7 | TIM4_CH2 Wheel3 B |
| 60 | BOOT0 | BOOT0(専用ピン) |
| 61 | PB8 | 未使用 |
| 62 | PB9 | 未使用 |
| 63 | VSS | GND |
| 64 | VDD | 3V3 |

## ユニット基板(G474)との差分・競合

- PA0/PA1はTIM2で使う。Rev.Aでは5V監視自体を非実装とし、PC0もNCとする(変更なし)。
- PB6/PB7はTIM4で使うため、PB7をI2C1_SDAとして使用しない(変更なし)。
- C620用の2本目CAN(ユニット基板ではFDCAN2)とAMT22用SPIは元々オドメトリ基板に無い。
  購入済み`ICM-42688-P`モジュールへPC10/PC11/PC12/PD2を4-wire SPI、PC4をData Ready割り込みとして割り当てる。
  PC5はモジュールのINT2へ配線し、ファームで必要になるまで予備割り込みとして無効化する。

## unit board採用品の流用

MCUファミリ固有部を除き、unit boardで確定済みの部品を優先して流用する。

| 用途 | 流用品 | F405側の扱い |
|---|---|---|
| 5V入力逆接・逆流保護 | `LM66100DCKR` | 回路ブロックごと流用 |
| 3.3V LDO | `TLV76133DCYR` | 旧TLV1117LV33DCYRと同一SOT-223ピン配置。F405最大負荷時の電流・熱は別途再計算 |
| CANトランシーバ | `TCAN1051VDRQ1` | CAN1/bxCANへ接続して流用 |
| HSE | `FC3BAEBDI8.0-T1`、C0G 10 pF初期値 | 8MHz、CL=8pF、ESR max 500Ω、3225-4pad。負荷容量はAN2867に従い実基板で確認 |
| VDDデカップリング | `C0603C104K5RACTU` 100 nF | VDD 4pinへ各1個 |
| VDDバルク | `GRM21BZ71E475KE15K` 4.7 µF | 1個以上 |
| VDDA | `BLM18AG601SN1D`、100 nF、`C1608X7R1E105K080AB` 1 µF | 回路ブロックを流用。LQFP64には独立VREF+ pinなし |
| VCAP_1/2 | `GCM21BR71E225KA73L` 2.2 µF、25 V、X7R、0805 | unit boardのLM66100入力用と同一品を各1個流用。各VCAP直近からGNDへ接続し、他用途に接続しない。実装条件でESR < 2Ωを満たすことをメーカー特性で確認 |
| IMUモジュール電源 | `C0603C104K5RACTU` 100 nF + `GCM21BR71E225KA73L` 2.2 µF | キャリア側3.3V入口に追加。モジュール搭載済みコンデンサと並列でも実装する |
| デバッグ・CAN・電源コネクタ、LED | unit board採用品 | pin数・色・シルクを合わせて流用 |

公式参照:

- [STM32F405xx/STM32F407xx datasheet DS8626 Rev.12](https://www.st.com/resource/en/datasheet/stm32f405vg.pdf)
- [AN4488 STM32F4xxxx hardware development](https://www.st.com/resource/en/application_note/an4488-getting-started-with-stm32f4xxxx-mcu-hardware-development-stmicroelectronics.pdf)
- [AN2867 oscillator design guide](https://www.st.com/resource/en/application_note/an2867-guidelines-for-oscillator-design-on-stm8afals-and-stm32-mcusmpus-stmicroelectronics.pdf)
- [TDK ICM-42688-P product page](https://product.tdk.com/ja/search/sensor/mortion-inertial/imu/info?part_no=ICM-42688-P)
