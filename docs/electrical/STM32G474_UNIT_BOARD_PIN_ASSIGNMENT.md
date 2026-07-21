# STM32G474RET6 ユニット基板ピン割当

対象は差動ステアユニット基板 Rev.Aの `STM32G474RET6` (LQFP64)。物理ピン番号はSTデータシート DS12288 Rev.6 Figure 7のLQFP64 top viewに従う。

> `CARRIER_BOARD_BUILD_PLAN.md`にあるCAN1=PA11/PA12、CAN2=PB5/PB6、SPI2=PB13/PB14/PB15はMatek CAN-G474試験機のボード別設定。本自作基板の割当ではない。

## インターフェース別割当

| 用途 | MCU信号 | GPIO / 物理pin | AF | 接続先 |
|---|---|---:|---:|---|
| 中央CAN RX | FDCAN1_RX | PA11 / 45 | AF9 | U401 RXD pin 4から |
| 中央CAN TX | FDCAN1_TX | PA12 / 46 | AF9 | U401 TXD pin 1へ |
| C620 CAN RX | FDCAN2_RX | PB12 / 34 | AF9 | U501 RXD pin 4から |
| C620 CAN TX | FDCAN2_TX | PB13 / 35 | AF9 | U501 TXD pin 1へ |
| AMT22 SCLK | SPI3_SCK | PC10 / 52 | AF6 | R601経由 J601-2 |
| AMT22 MISO | SPI3_MISO | PC11 / 53 | AF6 | R603経由 J601-5から |
| AMT22 MOSI | SPI3_MOSI | PC12 / 54 | AF6 | R602経由 J601-3へ |
| AMT22 CS | AMT22_CS_N | PD2 / 55 | GPIO | R604経由 J601-6へ |
| デバッグUART TX | LPUART1_TX | PA2 / 14 | AF12 | J701-5へ（基板視点TX） |
| デバッグUART RX | LPUART1_RX | PA3 / 17 | AF12 | J701-6から（基板視点RX） |
| SWD | SWDIO / SWCLK | PA13 / 49, PA14 / 50 | AF0 | J701-3 / J701-2 |
| Reset | NRST | PG10 / 7 | - | J701-4, C313, TP |
| SWO予約 | TRACESWO | PB3 / 56 | AF0 | TPのみ |
| 拡張I2C予約 | I2C1_SCL / SDA | PA15 / 51, PB7 / 60 | AF4 | 拡張ヘッダTBD |
| 5 V監視 | ADC_5V_MON | PA0 / 12 | ADC | R304/R305/C314/D301 |
| ID | UNIT_ID0/1/2 | PC6 / 38, PC7 / 39, PC8 / 40 | GPIO input | SW701; internal pull-up, ON=Low |
| LED | RUN / COMM / ERR | PA5 / 19, PB10 / 30, PB11 / 33 | GPIO output | R702/D702, R703/D703, R704/D704 |
| HSE | OSC_IN / OSC_OUT | PF0 / 5, PF1 / 6 | - | X301, C311/C312, R302 |
| Boot | BOOT0 | PB8 / 61 | - | R303 10 kΩ pull-down, TP |

## 電源ピン

| 物理pin | ピン名 | 接続 |
|---:|---|---|
| 1 | VBAT | 3V3; C305 100 nFを直近配置 |
| 16, 32, 48, 64 | VDD | 3V3; C301–C304 100 nFを各pinに1個 |
| 15, 31, 47, 63 | VSS | GND plane |
| 29 | VDDA | FB301後のVDDA_A; C306 100 nF + C307 1 µF |
| 28 | VREF+ | R301 0 ΩでVDDA_Aへ; C308 10 nF + C309 1 µF |
| 27 | VSSA | GND; VDDA/VREF+コンデンサ帰路 |

## LQFP64全ピン

`NC`はRev.A回路図で未接続。ファームでは原則アナログ入力・プル無しに設定するが、最終方針はAN5093とCubeMX設定時に再確認する。

| pin | 名称 | Rev.A状態 | 用途 / ネット | pin | 名称 | Rev.A状態 | 用途 / ネット |
|---:|---|---|---|---:|---|---|---|
| 1 | VBAT | 使用 | 3V3 | 33 | PB11 | 使用 | LED_ERR |
| 2 | PC13 | NC | 未使用 | 34 | PB12 | 使用 | FDCAN2_RX |
| 3 | PC14-OSC32_IN | NC | LSE未使用 | 35 | PB13 | 使用 | FDCAN2_TX |
| 4 | PC15-OSC32_OUT | NC | LSE未使用 | 36 | PB14 | NC | 未使用 |
| 5 | PF0-OSC_IN | 使用 | HSE OSC_IN | 37 | PB15 | NC | 未使用 |
| 6 | PF1-OSC_OUT | 使用 | HSE OSC_OUT | 38 | PC6 | 使用 | UNIT_ID0 |
| 7 | PG10-NRST | 使用 | NRST | 39 | PC7 | 使用 | UNIT_ID1 |
| 8 | PC0 | NC | 未使用 | 40 | PC8 | 使用 | UNIT_ID2 |
| 9 | PC1 | NC | 未使用 | 41 | PC9 | NC | 未使用 |
| 10 | PC2 | NC | 未使用 | 42 | PA8 | NC | 未使用 |
| 11 | PC3 | NC | 未使用 | 43 | PA9 | NC | 未使用 |
| 12 | PA0 | 使用 | ADC_5V_MON | 44 | PA10 | NC | 未使用 |
| 13 | PA1 | NC | 未使用 | 45 | PA11 | 使用 | FDCAN1_RX |
| 14 | PA2 | 使用 | LPUART1_TX | 46 | PA12 | 使用 | FDCAN1_TX |
| 15 | VSS | 使用 | GND | 47 | VSS | 使用 | GND |
| 16 | VDD | 使用 | 3V3 | 48 | VDD | 使用 | 3V3 |
| 17 | PA3 | 使用 | LPUART1_RX | 49 | PA13 | 使用 | SWDIO |
| 18 | PA4 | NC | 未使用 | 50 | PA14 | 使用 | SWCLK |
| 19 | PA5 | 使用 | LED_RUN | 51 | PA15 | 予約 | I2C1_SCL |
| 20 | PA6 | NC | 未使用 | 52 | PC10 | 使用 | SPI3_SCK |
| 21 | PA7 | NC | 未使用 | 53 | PC11 | 使用 | SPI3_MISO |
| 22 | PB0 | NC | 未使用 | 54 | PC12 | 使用 | SPI3_MOSI |
| 23 | PB1 | NC | 未使用 | 55 | PD2 | 使用 | AMT22_CS_N |
| 24 | PB2 | NC | 未使用 | 56 | PB3 | 予約 | SWO TP |
| 25 | PC4 | NC | 未使用 | 57 | PB4 | NC | 未使用 |
| 26 | PC5 | NC | 未使用 | 58 | PB5 | NC | 未使用 |
| 27 | VSSA | 使用 | GND | 59 | PB6 | NC | 未使用 |
| 28 | VREF+ | 使用 | VREF+ | 60 | PB7 | 予約 | I2C1_SDA |
| 29 | VDDA | 使用 | VDDA_A | 61 | PB8-BOOT0 | 使用 | BOOT0 |
| 30 | PB10 | 使用 | LED_COMM | 62 | PB9 | NC | 未使用 |
| 31 | VSS | 使用 | GND | 63 | VSS | 使用 | GND |
| 32 | VDD | 使用 | 3V3 | 64 | VDD | 使用 | 3V3 |

## 注意

- PB8はBOOT0専用とし、GPIOに再利用しない。
- PA13/PA14はSWD専用。PB3はSWO用に予約する。
- PB13は本基板でFDCAN2_TXのため、Matek CAN-G474用SPI2割当と併用できない。
- PA15/PB7は拡張I2C予約。ヘッダ型番とピン順は未確定。
- DBG_TX/RXは基板視点の名称。WeAct側とのケーブル結線を最終照合する。
