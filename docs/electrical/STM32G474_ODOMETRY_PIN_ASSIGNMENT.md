# STM32G474RET6 オドメトリ基板ピン割当(廃止・履歴)

> **2026-07-25廃止**: オドメトリ基板のMCUは部室在庫の`STM32F405RGT6`へ変更した。
> 現行のピン割当は`STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`を参照。本書は決定履歴として残す。

対象はAMT102クアドラチャエンコーダ×3を使うオドメトリ基板の `STM32G474RET6` (LQFP64)。Z相は使用しない。

## AMT102×3の割当

| 測定輪 | AMT102信号 | タイマ入力 | GPIO | 物理pin | AF | 基板内接続 |
|---|---|---|---|---:|---:|---|
| Wheel 1 | A | TIM2_CH1 | PA0 | 12 | AF1 | J801-3 → U801A `SN74LVC2G17DBVR` → PA0 |
| Wheel 1 | B | TIM2_CH2 | PA1 | 13 | AF1 | J801-4 → U801B `SN74LVC2G17DBVR` → PA1 |
| Wheel 2 | A | TIM3_CH1 | PA6 | 20 | AF2 | J802-3 → U802A `SN74LVC2G17DBVR` → PA6 |
| Wheel 2 | B | TIM3_CH2 | PA7 | 21 | AF2 | J802-4 → U802B `SN74LVC2G17DBVR` → PA7 |
| Wheel 3 | A | TIM4_CH1 | PB6 | 59 | AF2 | J803-3 → U803A `SN74LVC2G17DBVR` → PB6 |
| Wheel 3 | B | TIM4_CH2 | PB7 | 60 | AF2 | J803-4 → U803B `SN74LVC2G17DBVR` → PB7 |

AMT102コネクタJ801–J803はGH 4pinとし、1=5V、2=GND、3=A、4=B。`SN74LVC2G17DBVR`は3.3V給電とし、各ICに100nFを置く。ESD/直列抵抗/RC定数は未確定。

## 共通インターフェース

| 用途 | MCU信号 | GPIO / 物理pin | AF | 接続先 |
|---|---|---:|---:|---|
| センサCAN RX/TX | FDCAN1_RX / TX | PA11 / 45, PA12 / 46 | AF9 | TCAN1051V RXD/TXD |
| Debug UART TX/RX | LPUART1_TX / RX | PA2 / 14, PA3 / 17 | AF12 | J701-5/J701-6 |
| SWD | SWDIO / SWCLK | PA13 / 49, PA14 / 50 | AF0 | J701-3/J701-2 |
| Reset | NRST | PG10 / 7 | - | J701-4, C313, TP |
| ID | UNIT_ID0/1/2 | PC6 / 38, PC7 / 39, PC8 / 40 | GPIO | SW701; unitId=4 |
| LED | RUN/COMM/ERR | PA5 / 19, PB10 / 30, PB11 / 33 | GPIO | 状態LED |
| HSE | OSC_IN/OUT | PF0 / 5, PF1 / 6 | - | 8 MHz水晶 |
| Boot | BOOT0 | PB8 / 61 | - | 10 kΩ pull-down |
| SWO予約 | TRACESWO | PB3 / 56 | AF0 | TP |

## ユニット基板との差分・競合

- PA0/PA1はTIM2で使う。Rev.Aでは5V監視自体を非実装とし、PC0もNCとする。
- PB6/PB7はTIM4で使うため、PB7をI2C1_SDAとして使用しない。したがってユニット基板のPA15/PB7 I2C予約はオドメトリ基板では削除する。
- C620用FDCAN2とAMT22用SPI3は削除。PC10/PC11/PC12/PD2はSPI IMU候補として予約できるが、IMU型番、CS、Data Readyの割当は未確定。

## 電源ピン

| 物理pin | 名称 | 接続 |
|---:|---|---|
| 1 | VBAT | 3V3 + 100 nF |
| 16, 32, 48, 64 | VDD | 3V3 + 各pin 100 nF |
| 15, 31, 47, 63 | VSS | GND |
| 29 | VDDA | FB301後のVDDA_A + 100 nF + 1 µF |
| 28 | VREF+ | 0 Ω経由VDDA_A + 10 nF + 1 µF |
| 27 | VSSA | GND |

## LQFP64全ピン（オドメトリ基板）

| pin | 名称 | 状態 | 用途 | pin | 名称 | 状態 | 用途 |
|---:|---|---|---|---:|---|---|---|
| 1 | VBAT | 使用 | 3V3 | 33 | PB11 | 使用 | LED_ERR |
| 2 | PC13 | NC | 未使用 | 34 | PB12 | 予約 | スペア/FDCAN2_RX |
| 3 | PC14 | NC | LSE未使用 | 35 | PB13 | 予約 | スペア/FDCAN2_TX |
| 4 | PC15 | NC | LSE未使用 | 36 | PB14 | NC | 未使用 |
| 5 | PF0 | 使用 | HSE OSC_IN | 37 | PB15 | NC | 未使用 |
| 6 | PF1 | 使用 | HSE OSC_OUT | 38 | PC6 | 使用 | UNIT_ID0 |
| 7 | PG10-NRST | 使用 | NRST | 39 | PC7 | 使用 | UNIT_ID1 |
| 8 | PC0 | NC | 5V監視非実装 | 40 | PC8 | 使用 | UNIT_ID2 |
| 9 | PC1 | NC | 未使用 | 41 | PC9 | NC | 未使用 |
| 10 | PC2 | NC | 未使用 | 42 | PA8 | NC | 未使用 |
| 11 | PC3 | NC | 未使用 | 43 | PA9 | NC | 未使用 |
| 12 | PA0 | 使用 | TIM2_CH1 Wheel1 A | 44 | PA10 | NC | 未使用 |
| 13 | PA1 | 使用 | TIM2_CH2 Wheel1 B | 45 | PA11 | 使用 | FDCAN1_RX |
| 14 | PA2 | 使用 | LPUART1_TX | 46 | PA12 | 使用 | FDCAN1_TX |
| 15 | VSS | 使用 | GND | 47 | VSS | 使用 | GND |
| 16 | VDD | 使用 | 3V3 | 48 | VDD | 使用 | 3V3 |
| 17 | PA3 | 使用 | LPUART1_RX | 49 | PA13 | 使用 | SWDIO |
| 18 | PA4 | NC | 未使用 | 50 | PA14 | 使用 | SWCLK |
| 19 | PA5 | 使用 | LED_RUN | 51 | PA15 | NC | I2C予約を削除 |
| 20 | PA6 | 使用 | TIM3_CH1 Wheel2 A | 52 | PC10 | 予約 | SPI IMU SCK候補 |
| 21 | PA7 | 使用 | TIM3_CH2 Wheel2 B | 53 | PC11 | 予約 | SPI IMU MISO候補 |
| 22 | PB0 | NC | 未使用 | 54 | PC12 | 予約 | SPI IMU MOSI候補 |
| 23 | PB1 | NC | 未使用 | 55 | PD2 | 予約 | SPI IMU CS候補 |
| 24 | PB2 | NC | 未使用 | 56 | PB3 | 予約 | SWO TP |
| 25 | PC4 | NC | 未使用 | 57 | PB4 | NC | 未使用 |
| 26 | PC5 | NC | 未使用 | 58 | PB5 | NC | 未使用 |
| 27 | VSSA | 使用 | GND | 59 | PB6 | 使用 | TIM4_CH1 Wheel3 A |
| 28 | VREF+ | 使用 | VREF+ | 60 | PB7 | 使用 | TIM4_CH2 Wheel3 B |
| 29 | VDDA | 使用 | VDDA_A | 61 | PB8-BOOT0 | 使用 | BOOT0 |
| 30 | PB10 | 使用 | LED_COMM | 62 | PB9 | NC | 未使用 |
| 31 | VSS | 使用 | GND | 63 | VSS | 使用 | GND |
| 32 | VDD | 使用 | 3V3 | 64 | VDD | 使用 | 3V3 |
