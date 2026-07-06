# Matek CAN-G474 制御ファーム移植方針

## 結論

Matek CAN-G474を本プロジェクトの主試験機として使い、差動ステア制御ループのカスタムファームは底面のSWDパッドからST-LINKで書き込む。UART1 DFUとDroneCAN更新は、工場ファームの復旧・配布経路として扱い、初期移植とデバッグの主経路にはしない。

CAN-G474は最終自作基板そのものではない。STM32G474CE(LQFP48)と2系統CANを使った制御・通信の実証機であり、最終基板はSTM32G474RET6(LQFP64)を直接実装する。

## 一次情報

- [Matek公式CAN-G474ページ](https://www.mateksys.com/?portfolio=can-g474)
- [ArduPilot MatekG474共通hwdef](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AP_HAL_ChibiOS/hwdef/MatekG474/hwdef.inc)
- [ArduPilot MatekG474-Periph](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AP_HAL_ChibiOS/hwdef/MatekG474-Periph/hwdef.dat)
- [ArduPilot MatekG474-DShot](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AP_HAL_ChibiOS/hwdef/MatekG474-DShot/hwdef.dat)
- STM32G474データシート、RM0440、AN2606、STM32ハードウェア設計資料

ArduPilotはGPL-3.0である。本リポジトリにはプロジェクト全体のライセンスが未設定なので、ArduPilotのC/C++実装を直接コピーしない。hwdefからピン接続、クロック、Flash配置などのハードウェア事実を確認し、レジスタ実装はSTの一次資料に基づいて本プロジェクト側で実装する。GPLコードを取り込む場合は、先に本プロジェクトの配布ライセンスを決定する。

## ArduPilotファームから参照する内容

| 項目 | CAN-G474定義 | 本プロジェクトでの用途 |
|---|---|---|
| MCU | STM32G474 / 512KB Flash | startup、リンカ、デバイス定義の確認 |
| 外部クロック | 8MHz | 現行クロック初期化との照合 |
| CAN1 | PA11 RX / PA12 TX | 中央CAN |
| CAN2 | PB5 RX / PB6 TX | C620専用CAN |
| SPI2 | PB13 SCK / PB14 MISO / PB15 MOSI | AMT222A-V |
| SPI2 CS | PB12 | `AMT22_CS_N`候補 |
| UART1 | PA9 TX / PA10 RX | DFU・初期ログ候補 |
| LED | PC13 | bring-up実行確認 |
| SWD | PA13 SWDIO / PA14 SWCLK | ST-LINK書込み・デバッグ |
| アプリ配置 | Flash先頭から36KB予約後 | 工場AP_Periphブートローダを残す場合のみ必要 |

AP_Periphのセンサドライバ構成、パラメータ保存、DroneCAN更新は設計参考にはなるが、C620制御や差動ステア制御ループは本プロジェクト固有なので、そのまま流用しない。

## 現行ファームとの差分

| 機能 | NUCLEO-G474RE現行 | Matek CAN-G474 |
|---|---|---|
| CAN1 | PA11 / PA12 | PA11 / PA12 |
| CAN2 | PB12 / PB13 | PB5 / PB6 |
| AMT22 SPI | SPI3 PC10 / PC11 / PC12 | SPI2 PB13 / PB14 / PB15 |
| AMT22 CS | PD2 | PB12 |
| デバッグUART | LPUART1 PA2 / PA3 + ST-LINK VCP | UART1 PA9 / PA10候補。外付けUSB-UARTが必要 |
| ユーザーLED | PA5 | PC13 |
| ユーザーボタン | PC13 | DFUボタン。アプリ操作への流用は要確認 |

`src/platform/`をボード別に切り替え、制御・プロトコル層は共通のまま維持する。最低限、GPIO、FDCAN、AMT22 SPI、UART/ログ、リンカ/ビルド定義を切り替える。

## ST-LINK書込み方針

### 接続

最低限、次を接続する。

- ST-LINK `VTref` -> CAN-G474 `3.3V`
- ST-LINK `GND` -> CAN-G474 `GND`
- ST-LINK `SWDIO` -> 底面`SWD`
- ST-LINK `SWCLK` -> 底面`SWC`
- `NRST`は基板上に接続可能なパッドが確認できた場合に追加する

CAN-G474本体は規定どおり5V端子へ4.5～5.5Vを供給する。ST-LINKの3.3Vを基板電源として注入せず、`VTref`はターゲット電圧検出として接続する。底面パッドの向きと名称は、通電前に公式写真と導通測定で確認する。

### Flash配置の選択

初期移植では次のAを採用する。

**A. 本プロジェクトのファームを`0x08000000`へ直接書く**

- 現行startup/ベクタ配置を維持でき、デバッグが単純。
- 工場出荷のArduPilotブートローダとAP_Periphを上書きする。
- DroneCAN経由更新は使えなくなる。更新はST-LINK、必要ならSTM32 ROM UARTブートローダで行う。

**B. ArduPilotブートローダを残し、アプリを36KB後へ置く**

- DroneCAN更新との互換設計、イメージ形式、ベクタ位置、ブート条件の実装が必要。
- 制御ループの初期bring-upには複雑すぎるため、必要性が出るまで採用しない。

### 初回書込み前

1. 製品型番、基板表裏、パッド名称を写真で記録する。
2. 5V入力、3.3Vレール、GND、SWDIO、SWCLKをテスターで確認する。
3. STM32CubeProgrammerでSWD接続し、Device ID、Flash容量、Option Bytes、RDP状態を記録する。
4. 読出し可能なら工場Flashをバックアップする。読出し保護解除のためのMass Eraseは行わない。
5. Matek公式AP_Periph復旧イメージとUART1 DFU手順を確保する。
6. モーター/C620/AMT22を外した状態で最小LED/GPIOファームを書き込む。

### Bring-up順序

1. PC13 LEDまたは空きGPIOでReset後の実行を確認する。
2. UART1またはRAMマーカでクロックとmain到達を確認する。
3. CAN1内部ループバック。
4. CAN2内部ループバック。
5. CAN-L431をCAN1の対向ノードとして1Mbps通信。
6. C620をCAN2へ接続し、ゼロ電流のままフィードバック受信。
7. SPI2でAMT222A-Vを読み取る。
8. 安全ゲートを有効にした制御ループを動かす。

CLIの書込み成功だけでは完了とせず、LED、通信応答、RAMマーカのいずれかでターゲット側の実行を確認する。

## 実装タスク

1. CMakeへ`MATEK_CAN_G474`/`NUCLEO_G474RE`のボード選択を追加する。
2. FDCANのインスタンスとGPIO/AFをボード定義へ分離する。
3. AMT22のSPIインスタンス、GPIO、CSをボード定義へ分離する。
4. PC13 LEDとUART1ログを追加する。
5. CAN-G474用の最小bring-upターゲットを作る。
6. ST-LINK書込みスクリプトへ対象確認と明示的なボード指定を追加する。
7. 実機確認後に制御ループターゲットを有効化する。
