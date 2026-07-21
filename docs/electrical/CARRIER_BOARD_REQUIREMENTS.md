# 差動ステアユニット基板(STM32G474自作基板)要件

## 目的

各差動ステアユニットに載せる、STM32G474直載せの自作基板をKiCadで設計する。

> **確定(2026-07-02): キャリアボード方式は不採用。STM32G474を直接実装した自作基板とする。**
> 購入済みのMatek CAN-G474を主なファーム開発・2バスCAN検証用に使い、NUCLEO-G474REはSWD・ピン自由度が必要な場合の予備とする。CAN-G474はG474CE(LQFP48)であり、G474RET6向け現行ファームを無変更では使えない。
> 回路・実装の参考としてMatek CAN-L431、Matek CAN-G474、ARK CANnode、CANable 2.0を使う。ただし各基板の電源条件、MCU、CAN系統数、トランシーバ、保護回路の差を確認し、ブロック単位で採否を決める。基板全体の無検証コピーはしない。
> FDCANの具体ピン(FDCAN1: PA11/PA12またはPB8/PB9、FDCAN2: PB12/PB13等)はCubeMXで割当を確定する。NUCLEOでの検証時も同じピン割当を使うこと。

パッケージはNUCLEO-G474REと同じ**LQFP64のSTM32G474RET6で確定**とする(2026-07-17、10個購入済み)。0.5mmピッチで、フラックス+ドラッグはんだまたはリフローで実装可能。Flash 512KBで将来の制御・診断・更新機能にも余裕があり、NUCLEOで検証したピン割当をそのまま使える。

## 参考ボードと利用範囲(2026-07-06確定)

| ボード | 主な参照箇所 | この設計との差 |
|---|---|---|
| [Matek CAN-L431](https://www.mateksys.com/?portfolio=can-l431) | 購入済み実機。5V入力、CANコネクタ、1Mbps CANの配線・終端・実装、ベンチ通信試験 | STM32L431、CAN 1系統。最終2バス構成の代用にはならない |
| [Matek CAN-G474](https://www.mateksys.com/?portfolio=can-g474) | 購入済み主試験機。STM32G474、CAN 2系統、SWD、電源、コネクタ配置、ArduPilot hwdefのピン割当 | STM32G474CE(LQFP48)で、本基板のG474RET6(LQFP64)とはパッケージと露出ピンが異なる |
| [ARK CANnode](https://github.com/ARK-Electronics/ARK_CANNODE) | 公開回路/BOM、MCU最小構成、5V→3.3V、CAN、SWD、保護・デカップリング | STM32F412、CAN 1系統、DroneCANセンサ用途 |
| CANable 2.0 | 公開回路、STM32G4最小構成、CANトランシーバ、USB-CAN実装 | USB-CAN用途。USB回路は本基板では原則不要 |

Matek CAN-G474のファーム用ピン定義はArduPilotの`MatekG474` hwdefを参照する。公開回路図が確認できない箇所は、基板写真やhwdefだけから回路定数を推測せず、STM32/TI等の部品データシートを正本とする。

## MCU最小構成(CANable流用部分+G474固有)

| 項目 | 要件 |
|---|---|
| VDDデカップリング | 各VDDピンに`GRM188R71A104KA01D` 100nF + 全体に`GRM21BR71A475KA73L` 4.7uF。LDO側10uFも併用 |
| VDDA/VREF+ | `BLM18AG601SN1D`後にVDDA 100nF+1uF。VREF+はVDDAへ0Ω接続し10nF+1uF。ADCを使うため省略しない |
| NRST | 100nF + デバッグGH6 + SMTテストポイントへ引き出し。内部weak pull-upを使い外付けpull-upなし |
| BOOT0 | `RC0603FR-0710KL` 10kΩ pull-down + BOOT0/3V3隣接SMTテストポイント。2.54mmジャンパは載せない |
| クロック | **`ECS-80-8-33Q-JES-TR` 8MHzを実装し、C0G 10pF x2を初期値とする。** HSI16は常温±1%だが全温度で−2/+1.5%(DS12288)であり、CAN 1Mbpsの理論許容を外れうる。負荷容量は実基板評価で8.2/10/12pFから調整。ファームはHSE起動+CSSでHSIフォールバック |
| SWD/デバッグUART | **ロボット側JST GH 6pinへ統一。** 1=GND、2=SWCLK(PA14)、3=SWDIO(PA13)、4=NRST、5=DBG_TX(PA2、ターゲット→デバッガ)、6=DBG_RX(PA3、デバッガ→ターゲット)。WeActStudio MiniDebugger側SH 10pinとの専用変換ケーブルを使う。SWO(PB3)は基板上テストパッドへ残す。デバッガ側5V/3.3Vは接続せず、ターゲットを通常の5V入力から自己給電する |
| デバッグUART | 1ch分をヘッダに出しておく(printf/ログ用) |

初回書き込み・ブリングアップ手順は `firmware/docs/BOARD_BRINGUP.md` の「自作基板へ移行するときのSWD要件」に従う。

## 推奨ピン割当(STM32G474RET6 / LQFP64)

NUCLEO-G474REのmorphoに全ピンが出ており、開発ボードと自作基板で同一割当を使える構成。

> **AF成立確認済み(2026-07-06)**: ST公式の[STM32_open_pin_data](https://github.com/STMicroelectronics/STM32_open_pin_data)(CubeMXと同一DB、`STM32G474R(B-C-E)Tx.xml`)で下表全ピンの信号割当を照合し、全て成立を確認した。FDCAN1_RX/TX=PA11/PA12、FDCAN2_RX/TX=PB12/PB13、SPI3=PC10/PC11/PC12、LPUART1_TX/RX=PA2/PA3、I2C1_SCL/SDA=PA15/PB7、SWO=PB3、BOOT0共用=PB8、OSC=PF0/PF1。なおG4のNRSTピンはPG10(LQFP64のpin7)。CubeMXでの.iocプロジェクト化は未実施(ファーム設定時に行う)。

| 機能 | ピン | AF | 備考 |
|---|---|---|---|
| FDCAN1_RX(中央CAN) | PA11 | AF9 | USB共用ピンだが本基板はUSB不使用 |
| FDCAN1_TX(中央CAN) | PA12 | AF9 | |
| FDCAN2_RX(C620) | PB12 | AF9 | |
| FDCAN2_TX(C620) | PB13 | AF9 | PB13をSPI2に使わないこと |
| SPI3_SCK(AMT22) | PC10 | AF6 | |
| SPI3_MISO(AMT22) | PC11 | AF6 | |
| SPI3_MOSI(AMT22) | PC12 | AF6 | |
| AMT22_CS_N | PD2 | GPIO | バイト間ウェイトが必要なのでソフト制御CS |
| デバッグUART | PA2 / PA3 | LPUART1 | NUCLEOのST-LINK VCPと同一。開発時printfがそのまま使える |
| UNIT_ID0/1/2 | PC6 / PC7 / PC8 | GPIO入力 | 内部プルアップ、3bit DIPスイッチでGNDへ(ON=Low、読み値反転)。起動時に1回読取り、RUN LEDをID回数点滅 |
| LED(電源/動作) | PA5 | GPIO | NUCLEOのLD2と同一。開発時の動作確認互換 |
| LED(通信) | PB10 | GPIO | |
| LED(エラー) | PB11 | GPIO | |
| 5V監視 | PA0 | ADC | 33kΩ/22kΩ分圧+10nF+`BAT54SLT1G`クランプで保護後5Vを監視 |
| SWD | PA13 / PA14 | - | 専用。他用途に使わない |
| SWO(予約) | PB3 | - | トレース用に空けておく |
| BOOT0 | PB8 | - | G4はPB8がBOOT0共用。10kプルダウン+ジャンパ。GPIOとして使わない |
| HSE水晶 | PF0 / PF1 | - | 8MHz |
| 拡張I2C(予約) | PA15(SCL) / PB7(SDA) | AF4 | IMU等の将来拡張用。ヘッダに出しておく |

選定理由:

- FDCAN1にPB8/PB9を使わない: PB8はBOOT0共用のため。
- AMT22をSPI1(PA5/PA6/PA7)にしない: PA5がNUCLEOのLD2と衝突し、開発時に不便なため。SPI3(PCポート)は競合がない。
- PC13を使わない: NUCLEOのB1ボタンと衝突するため。
- NUCLEO検証時はPA2/PA3がST-LINK VCP直結なので、デバッグUARTがUSB経由でそのまま見える。

## 外部インターフェース

| 信号 | 用途 |
|---|---|
| 5V | 制御電源 |
| GND_CTRL | 制御GND |
| COMM_A / COMM_B | 中央制御との通信。実体は中央CANのCAN_H/L |
| C620 CAN | C620 x2との通信 |
| AMT22 SPI | ステア角取得 |
| ID DIPスイッチ | ユニットID設定(3bit) |

C620用24V大電流線はキャリア基板の制御ハーネス(5V/GNDのGH 2pin、COMM_A/B/GNDのGH 3pin)と分ける。

## 中央通信(中央CAN)

要件:

- 各ユニットに中央CAN用トランシーバを1個載せる(C620用とは別に、計2個)。
- 中央CANはクラシックCAN 1Mbps。ノードはTeensy+ユニットx3。
- 外部コネクタのシルクは `COMM_A/B` とする(`CAN_H/L` とは書かない)。
- MCU側ネットは `COMM_TX` / `COMM_RX` とし、FDCAN1に割り当てる(C620はFDCAN2)。

バス全体の要件:

- トポロジはデイジーチェーン(渡り配線)とし、スター配線にしない。
- 120Ω終端はバス物理両端の2箇所のみ。Teensy側1個+最遠ユニット1個。各キャリアには`RC0603FR-07120RL`と`JS102011SAQN`スライドスイッチを載せ、末端ユニットだけONにする。
- COMM_A/Bラインに`ESD2CAN24DBZRQ1`を入れる。
- CANはドミナント/リセッシブ方式なので、RS485で必要だったDE/RE制御やフェイルセーフバイアスは不要。

部品選定: C620側と共通化して **`TCAN1051VDRQ1` x2** とする。VCC=5V、VIO=3.3V。詳細は`CAN_COMMON_BLOCK_PART_SELECTION.md`。

## C620 CAN

要件:

- 各ユニットにC620専用CANトランシーバを1個載せる。
- MCUのCAN_TX/CAN_RXをCAN_H/CAN_Lへ直結しない。
- C620_CAN_H/Lはユニット内だけで使う。
- ユニット内CANの終端120Ωは実配線長とC620側終端有無を確認して決める。
- スタブを短くする。
- トランシーバ近傍に0.1uFを置く。
- C620のCANビットレートは1Mbps固定。FDCANはクラシックCAN 1Mbpsで設定する。
- C620のIDはSETボタンで設定する(ユーザーガイド参照)。ユニット内で#1/#2を組立時に設定し、ケースに明記する。
- CAN_H/Lに`ESD2CAN24DBZRQ1`を入れる。

部品選定:

| 候補 | 備考 |
|---|---|
| `TCAN1051VDRQ1` (TI) | **採用**。5V VCC、3.3V VIO、SOIC-8、バスフォルト±58V、AEC-Q100 |
| `TJA1051T/3` (NXP) | 基本ピン配列が一致する代替候補。公開CAN設計での採用実績が多い |

## AMT22 / SPI

型式確定(2026-07-02): **AMT222A-V**(12bitシングルターン、radial、ボア5mm)。分解能4096cnt(0.088°/cnt)。ステア軸に1:1直結。12bit応答の下位2bit(L0/L1)は常に0なので、読み値は2bit右シフトして使う。

AMT22は5V駆動(VDD 3.8〜5.5V)、MCUは3.3V系。

データシート確認済みの電気仕様(Same Sky AMT22 rev1.09):

| 項目 | 値 |
|---|---|
| 入力High(VIH) | min 2.0V / max 5.5V |
| 出力High | 3.3V |
| SPIモード | Mode 0 |
| 最大クロック | 2MHz |

結論: **全信号直結でよい。MISO分圧は不要。**

| 信号 | 方向 | 対策 |
|---|---|---|
| SCLK | MCU -> AMT22 | 直結(VIH 2.0Vなので3.3V駆動で成立) |
| MOSI | MCU -> AMT22 | 直結 |
| CS | MCU -> AMT22 | 直結 |
| MISO | AMT22 -> MCU | 直結(AMT22出力Highは3.3V)。保険で100Ω直列を入れてもよい |

タイミング制約(ファーム実装で必須):

| 項目 | 値 |
|---|---|
| T_CLK: CS↓から最初のクロックまで | ≥2.5µs |
| T_B: バイト間 | ≥2.5µs |
| T_R: 最終クロックからCS↑まで | ≥3µs |
| T_CS: リード間隔 | ≥40µs |

バイト間ウェイトが必要なため、2バイトを連続DMA転送すると読めない。1バイトずつ送る。応答上位2bitはチェックビット(奇偶パリティ)なので必ず検証する。

コネクタ: AMT22側はMolex 502578-0600(Pico-Lock 6pin)。検証用ケーブルはAMT-06C-1-036。キャリア側はJST GH 6pin横挿し(`SM06B-GHS-TB`)で中継し、Pico-Lock⇔GHの変換ハーネスを作る(GH側ハウジングはデバッグ用と共通の`GHR-06V-S`+`SSHL-002T-P0.2`)。

AMT22コネクタのピン配置(データシートrev1.10で確認済み、`hardware/reference/datasheets/`に保存):

| ピン | 機能 |
|---:|---|
| 1 | +5V |
| 2 | SCLK |
| 3 | MOSI |
| 4 | GND |
| 5 | MISO |
| 6 | CHIP SELECT |

基板側GH 6pinも同じピン順にすると、ハーネスがストレート結線になる。

## 電源

| 入力 | 用途 |
|---|---|
| 5V | NUCLEO、AMT22、LDO入力 |
| 3.3V | STM32G474、CANトランシーバVIO、ロジック等 |

ユニットへの給電は中央から独立したGH 2pinの5V/GNDで受ける。CANのGH 3pinとは別ハーネスとする。基板入力を`LM66100DCKR`で逆接・逆流保護し、保護後5VからLDOで3.3Vを作る。

`TCAN1051VDRQ1`の主電源VCCは5V、3.3V側はVIOだけである。3.3V負荷を150～300mAと仮定するとLDO損失は0.255～0.510W。SOT-223のVOUTタブへ放熱銅箔を設け、最大負荷で温度を実測する。1A定格をそのまま連続使用可能電流とは扱わない。

| 候補 | 備考 |
|---|---|
| `TLV1117LV33DCYR` | **採用**。1A、SOT-223、セラミック安定、代表dropout 455mV |
| `MCP1826S-3302E/DB` | 成立するが、少量価格と流通性から代替候補 |

保険として、5V入力部に**広入力レンジ降圧モジュールのフットプリントを予備実装として置く**ことを推奨する(例: OKI-78SR-5/1.5-W36-C、三端子レギュレータ互換ピン配置、入力7〜36V)。ハーネスの電圧降下で5V分配が苦しくなった場合、配線を24V分配に切り替えて同じ基板で受けられる。通常時は未実装+ジャンパでバイパス。

注意:

- LDO近傍に入力側100nF+10uF X7Rを置く。
- LDO出力側に100nF+10uF X7Rを置き、DC bias後もデータシート最小容量を満たす。
- 5VがAMT22の上限5.5Vを超えないようにする。
- AMT22は起動に最大200ms要し、起動中はシャフト静止が必要。ファームの初期化待ちに反映する。

## 部品リスト

| ブロック | 部品 | 実装 |
|---|---|---|
| 中央CAN | `TCAN1051VDRQ1` | SOIC-8、リフロー |
| 中央CAN終端 | `RC0603FR-07120RL` + `JS102011SAQN` | 120Ω + SMTスライドスイッチ |
| 中央CAN保護 | `ESD2CAN24DBZRQ1` | SOT-23、リフロー |
| C620 CAN | `TCAN1051VDRQ1` | SOIC-8、リフロー |
| C620 CAN終端 | `RC0603FR-07120RL` + `JS102011SAQN` | 120Ω + SMTスライドスイッチ |
| C620 CAN保護 | `ESD2CAN24DBZRQ1` | SOT-23、リフロー |
| 5V入力保護 | `LM66100DCKR` | SC70-6、CE_N=VOUT、1.5A、RPP+RCB |
| LDO | `TLV1117LV33DCYR` | SOT-223、タブ=VOUT |
| MCU | STM32G474RET6(LQFP64) | 0.5mmピッチ、ドラッグはんだ |
| 水晶 | `ECS-80-8-33Q-JES-TR` + `GRM1885C1H100JA01D` x2 | 8MHz、3225-4pad、10pF C0G x2 |
| SWD/デバッグUART | JST GH: `GHR-06V-S` + `SSHL-002T-P0.2`、基板側は上挿し`BM06B-GHS-TBT` | WeAct SH 10pin→ロボットGH 6pin専用ケーブルを作る |
| BOOT0 | `RC0603FR-0710KL` + BOOT0/3V3 `S1751-46R` | 10kΩ pull-down、隣接TPを治具で短絡 |
| ID設定 | 3bit DIPスイッチ(型番は部品選定で確定) | PC6-8、内部プルアップ、ON=GND短絡。起動時にRUN LEDをID回数点滅、ID=0(全OFF)は未設定エラー扱い |
| デカップリング | VDD 100nF x4 + 4.7uF、VBAT 100nF、VDDA用`BLM18AG601SN1D`+100nF+1uF、VREF+ 10nF+1uF | 0603/0805、詳細はG474最小構成選定書 |
| AMT22中継 | `SM06B-GHS-TB` + `GHR-06V-S` + `SSHL-002T-P0.2`(AMT22側は純正Molex Pico-Lockケーブル、変換ハーネス自作) | 横挿しGH6、1.25mm、AMT22と同ピン順でストレート結線 |
| 外部電源 | `SM02B-GHS-TB` + `GHR-02V-S` | 横挿しGH2、1=5V、2=GND、AWG26、CANと分離 |
| 中央CANパススルー | 横挿しJST GH 3pin x2(COMM_A/COMM_B/GND) | `SM03B-GHS-TB`、基板上でIN/OUT直結 |
| 予備降圧 | OKI-78SR-5互換フットプリント + バイパスジャンパ(通常未実装) | スルーホール |
| 5V監視 | 33kΩ/22kΩ + 10nF + `BAT54SLT1G` | PA0、0.4倍、SOT-23クランプ |
| 状態LED | `LTST-C190KGKT`緑、`LTST-C190KSKT`黄、`LTST-C190KRKT`赤 + 各1kΩ | PWR/RUN/COMM/ERRの4表示、0603 |
| テストポイント | `S1751-46R` | 主要5V/3.3V/GND/CAN/NRST/BOOT0/SWO。補助信号は露出銅pad |

## 回路図作成メモ(2026-07-06確認)

KiCad 10標準ライブラリに以下の検証済みシンボルがあり、ピン配置の正本として使える(自作シンボル起こし不要):

| 部品 | シンボル | 確認済みピン |
|---|---|---|
| STM32G474RET6 | `MCU_ST_STM32G4:STM32G474RETx` | 64pin。NRST=PG10(pin7)、BOOT0=PB8(pin61)、VDD=16/32/48/64、VSS=15/31/47/63、VDDA=29、VSSA=27、VREF+=28、VBAT=1 |
| `TCAN1051VDRQ1` | 自作または検証済み互換シンボル | 1=TXD、2=GND、3=VCC(5V)、4=RXD、5=VIO(3.3V)、6=CANL、7=CANH、8=S |
| `TLV1117LV33DCYR` | `Regulator_Linear:TLV1117-33`を公式pinoutと照合 | 1=GND、2=VOUT、3=VIN、タブ=VOUT |
| `LM66100DCKR` | `Power_Management:LM66100DCK` | 1=VIN、2=GND、3=CE_N、4=NC、5=ST、6=VOUT。CE_N→VOUTでRPP+RCB |
| OKI-78SR-5(予備降圧) | `Converter_DCDC:OKI-78SR-5_1.5-W36-C` | 7805互換3pin |

`ESD2CAN24DBZRQ1`は公式データシートでピン配置とSOT-23(DBZ)推奨ランドを確認し、KiCad標準シンボル/フットプリントの一致を検証する。不一致なら`hardware/lib/`に自作シンボルを起こす。

ARK CANnode Rev 1回路図(`hardware/reference/ARK_CANNODE/`)から流用検討する回路ブロック:

- 逆接・逆流保護: `LM66100DCKR`(VIN側2.2uF以上、CE_N=VOUT、1.5A、RPP+RCB)
- CANコネクタを同一バスで2個並列に載せ、基板上でデイジーチェーンの渡りを作る(中央CANの渡り配線と一致する構成)
- 外部に出る信号線に1ラインESDダイオードを挿入
- 終端120ΩをFETで切替(本基板は物理スライドスイッチ方式なので参考のみ)

## 評価ボードとの関係

(旧「第二段階への移行」。2026-07-02に自作基板方式へ一本化したため、MCU最小構成は冒頭の必須要件に統合した)

- Matek CAN-G474を2系統CANとG474上での主なファーム検証に使う。公式/ArduPilot hwdef上のCAN割当はCAN1=PA11/PA12、CAN2=PB5/PB6。
- CAN-G474でAMT22を接続する場合は、基板上に露出しているSPI2(PB13/PB14/PB15、CS=PB12)へボード別設定を追加する。現行NUCLEO用SPI3(PC10/PC11/PC12、CS=PD2)のままでは使えない。
- NUCLEO-G474REはSWDの確実な復旧、自由なピン引き出し、現行ファームの回帰確認用として保持する。CAN-G474のカスタムファーム書込みと必要I/Oが確認できれば、通常試験では省略可能。
- ピン名はNUCLEOコネクタ番号ではなく `PAx` / `PBx` で管理し、自作基板とNUCLEOで同じ割当を使う。これによりファームを無改造で移植できる。
- NUCLEOで使用済みのピン(LD2=PA5、B1=PC13、VCP=PA2/PA3)は、自作基板では自由に使えるが、NUCLEO検証中は避けるか競合を理解して使う。
- 将来さらに小型化する場合もFDCAN 2系統以上のMCU(STM32G474/G473系)を維持する。STM32G431K系はFDCAN 1系統なので不可。
