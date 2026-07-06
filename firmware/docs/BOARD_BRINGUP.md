# Matek CAN-G474 / NUCLEO-G474RE Bring-up and programming notes

この文書は、Matek CAN-G474を主試験機、NUCLEO-G474REを予備として使い、後にSTM32G4系の
自作基板へ移行するための書き込み・配線・切り分け手順をまとめたものです。

## 現在の基準ハードウェア

- 主試験機: Matek CAN-G474 / STM32G474CE / CAN 2系統
- 主試験機ピン: CAN1 PA11/PA12、CAN2 PB5/PB6、SPI2 PB13/PB14/PB15、CS候補PB12
- 書込み候補: 底面SWD、またはUART1 DFU。初回はSWD接続とDevice IDを確認してから書き込む
- 予備・回帰確認: NUCLEO-G474RE / STM32G474RET6

- 以下はNUCLEO-G474REを使う場合の既知の環境:
- MCU: STM32G474RET6
- ST-LINKシリアル: `004F002C3532510731333430`
- ST-LINK firmware: `V3J17M10`（2026-07-01更新）
- STM32CubeProgrammer: `2.22.0`
- STM32Cube CMake bundle: `4.3.1+st.1`
- STM32Cube Ninja bundle: `1.13.2+st.1`
- LD2 USER: PA5、Highで点灯
- B1 USER: PC13、未押下Low、押下High
- 接続電圧確認値: 3.30 V
- SWD: オンボードSTLINK-V3E

ボード名は思い込みで決めず、毎回CubeProgrammerの検出結果を確認すること。
今回も当初想定のNUCLEO-G431KBではなく、実際にはNUCLEO-G474REが接続されていた。

## 通常のFlash書き込み

CAN-G474への初回カスタムファーム書込みは底面SWD/SWCパッドとST-LINKを使う。接続、工場ブートローダとのFlash配置競合、復旧準備、段階試験は`MATEK_CAN_G474_PORT.md`を正本とする。UART1 DFUは副経路であり、制御ファームの初期デバッグはSWDを優先する。

永続的に動かす通常経路では、GCC/CMakeでELFとHEXを生成し、HEXをFlashへ書く。

```powershell
.\firmware\scripts\build.ps1
.\firmware\scripts\flash.ps1
```

必要なCLI:

- `arm-none-eabi-gcc`
- CMake
- Ninja
- `STM32_Programmer_CLI`

書き込みスクリプトは次の設定を使用する。

```text
interface: SWD
image: firmware/build/debug/differential_swerve_firmware.hex
verify: enabled
reset after programming: enabled
```

Flash書き込み時は、対象MCU、リンカスクリプトのFlash/RAM容量、開始アドレス
`0x08000000`が一致していることを先に確認する。自作基板のMCU型番が確定したら、
リンカ設定をデータシートのメモリ構成に合わせて再確認する。

## 今回詰まった点

### 接続ボードが想定と違った

NUCLEO-G431KB向けのPB8設定では、NUCLEO-G474REのLD2は制御できない。
CubeProgrammerの`-l st-link`でボード名、Device ID、電圧を先に確認する。

### GCCが未導入だった

STM32CubeのCMake、Ninja、Programmerは導入済みだったが、GCCは見つからなかった。
このため、通常のHEX生成ではなく、診断用の最小コードをSRAMから実行した。

### GDB ServerがST-LINK firmware更新を要求した

ST-LINK GDB Server 7.13.0は、接続中の`V3J9M3`を古いとして接続を拒否した。
初期診断はCubeProgrammerで継続し、その後、公式STLinkUpgrade 3.17.10を使って
`V3J17M10`へ更新した。更新後はCubeProgrammerで再認識され、GDB Serverが
`Waiting for debugger connection`まで進むことを確認した。

更新はデバッグ環境全体へ影響する。実行前に対象シリアル、接続台数、電源電圧を
確認し、更新中はUSBを切断しない。

### 周辺レジスタへの`-w32`直接書き込みが失敗した

CubeProgrammerの`-w32`はSRAMへの書き込みには使えたが、GPIOのBSRRなど
周辺レジスタへの直接書き込みはdownload errorになった。周辺レジスタ操作は、
CPUで実行するコードから行う方が再現性が高い。

### SRAM先頭が既存ファームウェアに上書きされた

`0x20000000`へ診断コードを置くと、Flash上の既存デモが起動時に`.data`と`.bss`
を初期化し、SRAMコードを破壊した。診断コードは使用状況を確認した高位SRAMへ
配置した。固定アドレスを恒久運用せず、リンクマップとスタック位置を確認すること。

### SRAMイメージにもベクタテーブルが必要だった

CubeProgrammerの`go`では、先頭に次の2ワードを持つ正規のCortex-Mイメージが必要だった。

1. 初期スタックポインタ
2. Thumbビット付きReset Handlerアドレス

コード先頭へ直接`go`しても成功表示だけが返り、実際には目的の処理が動かなかった。
SRAMへ実行確認値を書き戻し、CPUが本当にコードを実行したことを検証した。

### 既存ファームウェアの割り込み状態が残った

単純なジャンプでは、既存デモが設定したSysTickなどが残る可能性がある。
診断コードでは割り込みを無効化して干渉を避けた。製品コードではリセット経由で
startupを実行し、クロック、割り込み、VTOR、周辺回路を明示的に初期化する。

### 「元のファームウェア」の意味

Flashには以前からSTのデモが保存されていた。このデモはB1を押すたびにLD2の
点滅周期を変える。SRAM診断コードはRESETまたは電源断で失われ、その後はFlashの
デモが再び起動する。期待と違う点滅を見た場合、Flashデモへ戻っていないか確認する。

## 接続モードの使い分け

- Normal: 通常の停止、書き込み、リセットに使用する。
- Hot Plug: 動作中の状態を極力変えずに接続、読み出しするときに使用する。
- Under Reset: クロック設定不良、低消費電力、GPIO再設定などで通常接続できないときに使う。

Hot Plugでも読み出し値を無条件に信用しない。今回、周辺レジスタの直接読み出しが
実際の入力状態と一致しなかった。重要な判定ではCPU自身に値をSRAMへコピーさせ、
SRAM側を読み戻して確認する。

大量消去、Option Byte変更、Readout Protection変更は通常のBring-upでは行わない。
必要になった場合は、変更内容と復旧手順を明示してから実行する。

## エンコーダ接続前の確認

エンコーダの型式と出力方式を最初に確定する。

- インクリメンタルA/B/Z、プッシュプル
- インクリメンタルA/B/Z、オープンコレクタ
- 差動A/A̅、B/B̅、Z/Z̅
- SPI、SSI、I2Cなどの絶対値エンコーダ
- 電源電圧と出力High電圧
- 最大パルス周波数

STM32へ直接入れてよいのは、電圧と出力形式がGPIO仕様に合う場合だけである。
5 V出力は対象ピンが5 V tolerantでも、電源OFF時注入電流やアナログ機能との制約を
確認する。差動信号は直接GPIOへ入れず、規格に合う差動レシーバを使用する。
オープンコレクタ出力には3.3 Vへの適切なプルアップを設ける。

配線時は次を守る。

- ボードとエンコーダのGNDを接続する。
- 電源極性と定格を確認してから給電する。
- A/Bを同一タイマのCH1/CH2へ割り当てる。
- Z相は必要に応じてEXTIまたはタイマ入力へ割り当てる。
- モータ線とエンコーダ線を分離し、長い配線ではツイスト、シールド、終端を検討する。
- 未使用入力を浮かせない。

## エンコーダの段階テスト

いきなりモータを回さず、次の順で確認する。

1. 無給電で短絡、GND、電源極性を確認する。
2. エンコーダだけ給電し、A/Bの静止電圧を測る。
3. GPIO入力としてA/BのHigh/Low変化を低速で確認する。
4. CPUポーリングで立ち上がり回数を確認する。
5. タイマEncoder Modeへ移し、正転・逆転でカウント符号を確認する。
6. 1回転あたりカウント数を仕様値と比較する。
7. 一定周期で差分を取り、速度へ変換する。
8. 最大予定回転数で取りこぼし、ノイズ、カウンタwrapを確認する。
9. 最後にモータ駆動と組み合わせる。

各段階で、入力生値、タイマカウント、差分、計算後速度を分けて観測する。
異常時にどの層で壊れたか判別できるようにする。

## 自作基板へ移行するときのSWD要件

最低限、デバッグコネクタへ次を引き出す。

- SWDIO: PA13
- SWCLK: PA14
- NRST
- GND
- Target VREF / 3.3 V検出

BOOT0の既定状態、NRSTのプルアップと容量、電源デカップリング、VDDA/VREF+、
発振回路をデータシートとハードウェア設計ガイドに合わせる。PA13/PA14を別用途と
共用する場合も、初期Bring-up中はSWDを無効化しない。

自作基板の初回書き込みでは、最初に接続電圧とDevice IDを確認し、LEDまたは空きGPIOの
単純な出力、入力ピン、通信、タイマ、モータ制御の順で機能を増やす。

## 推奨する記録

実機テストごとに次を残す。

- ボードリビジョンとMCU型番
- 書き込んだGit commitまたはELF/HEXのハッシュ
- Debug/Release設定
- ProgrammerとST-LINK firmwareのバージョン
- 配線図とエンコーダ型式
- 再現手順、期待値、実測値

「書き込み成功」というCLI表示だけで完了とせず、GPIO、SRAMマーカ、通信応答など、
ターゲットCPU側の観測結果で実行を確認する。
