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
| VDDデカップリング | 各VDDピンに100nF + 全体に10uFバルク |
| VDDA | フェライトビーズ + 100nF + 1uF。ADCを使うため省略しない |
| NRST | 100nF + SWDコネクタへ引き出し |
| BOOT0 | 10kプルダウン + 2.54mmジャンパ(DFU起動用) |
| クロック | **8MHz水晶 + 負荷容量のフットプリントを必ず置く。** HSI16は常温±1%だが全温度で−2/+1.5%(DS12288)であり、CAN 1Mbpsの理論許容(最良設定で約1.58%)を外れうる。モータ近傍で温度が振れる基板なので水晶実装を基本とする。コスト優先ならHSI16で試してからのDNPも可だが、パッドは必ず確保。ファームはHSE起動+CSSでHSIフォールバック |
| SWD | SWDIO(PA13) / SWCLK(PA14) / NRST / GND / 3.3V の5点を2.54mmヘッダまたはTag-Connectで引き出す |
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
| UNIT_ID0/1/2 | PC6 / PC7 / PC8 | GPIO入力 | 内部プルアップ、DIPスイッチでGNDへ |
| LED(電源/動作) | PA5 | GPIO | NUCLEOのLD2と同一。開発時の動作確認互換 |
| LED(通信) | PB10 | GPIO | |
| LED(エラー) | PB11 | GPIO | |
| 5V監視 | PA0 | ADC | 分圧で5Vレール監視(busVoltageMv用) |
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
| IDジャンパ | ユニットID設定 |

C620用24V大電流線はキャリア基板の制御4線と分ける。

## 中央通信(中央CAN)

要件:

- 各ユニットに中央CAN用トランシーバを1個載せる(C620用とは別に、計2個)。
- 中央CANはクラシックCAN 1Mbps。ノードはTeensy+ユニットx3。
- 外部コネクタのシルクは `COMM_A/B` とする(`CAN_H/L` とは書かない)。
- MCU側ネットは `COMM_TX` / `COMM_RX` とし、FDCAN1に割り当てる(C620はFDCAN2)。

バス全体の要件:

- トポロジはデイジーチェーン(渡り配線)とし、スター配線にしない。
- 120Ω終端はバス物理両端の2箇所のみ。Teensy側1個+最遠ユニット1個。各キャリアにはソルダージャンパ付き120Ωを載せ、末端ユニットだけONにする。
- COMM_A/BラインにTVS(PESD1CAN等)を入れる。
- CANはドミナント/リセッシブ方式なので、RS485で必要だったDE/RE制御やフェイルセーフバイアスは不要。

部品選定: C620側と共通化して **TCAN332DR x2** とする(在庫・実装・ファームの共通化)。

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
- CAN_H/LにTVS(PESD1CAN等)を入れる。

部品選定:

| 候補 | 備考 |
|---|---|
| TCAN332DR (TI) | 3.3V、SOIC-8。第一候補 |
| SN65HVD230DR | 3.3V。RSピンのスルーレート設定に注意(GNDへ落とす) |

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

コネクタ: AMT22側はMolex 502578-0600(Pico-Lock 6pin)。検証用ケーブルはAMT-06C-1-036。キャリア側は同コネクタのハーネスを受けるピンヘッダまたはXHで中継する。

AMT22コネクタのピン配置(データシートrev1.10で確認済み、`hardware/reference/datasheets/`に保存):

| ピン | 機能 |
|---:|---|
| 1 | +5V |
| 2 | SCLK |
| 3 | MOSI |
| 4 | GND |
| 5 | MISO |
| 6 | CHIP SELECT |

基板側XH 6pinも同じピン順にすると、ハーネスがストレート結線になる。

## 電源

| 入力 | 用途 |
|---|---|
| 5V | NUCLEO、AMT22、LDO入力 |
| 3.3V | CANトランシーバ等 |

ユニットへの給電は中央からの5V(ハーネス4線: COMM_A/B + 5V + GND)。基板上では5VからLDOで3.3Vを作る。

3.3V負荷はMCU(G474、フル動作で約100〜150mA)+CANトランシーバ2個(各最大約70mA)で、合計300mA程度。5V→3.3V/0.3Aの損失は約0.5WなのでSOT-223のLDOで足りる。**降圧モジュール(スイッチング)は3.3V側には不要。**

| 候補 | 備考 |
|---|---|
| MCP1826S-3302E/DB | 1A、SOT-223、セラミック出力コンデンサで安定。第一候補 |
| AMS1117-3.3 | 入手性は良いが、出力コンデンサにESR条件あり(タンタル22uF推奨)。セラミックのみだと発振リスク。ドロップアウト約1.1Vなので5V入力ギリギリの検討も必要 |

保険として、5V入力部に**広入力レンジ降圧モジュールのフットプリントを予備実装として置く**ことを推奨する(例: OKI-78SR-5/1.5-W36-C、三端子レギュレータ互換ピン配置、入力7〜36V)。ハーネスの電圧降下で5V分配が苦しくなった場合、配線を24V分配に切り替えて同じ基板で受けられる。通常時は未実装+ジャンパでバイパス。

注意:

- LDO近傍に入力側0.1uF+1uF以上を置く。
- LDO出力側にデータシート指定のコンデンサ(種類・容量・ESR)を置く。
- 5VがAMT22の上限5.5Vを超えないようにする。
- AMT22は起動に最大200ms要し、起動中はシャフト静止が必要。ファームの初期化待ちに反映する。

## 部品リスト

| ブロック | 部品 | 実装 |
|---|---|---|
| 中央CAN | TCAN332DR | SOIC-8 |
| 中央CAN終端 | 120Ω + ソルダージャンパ(末端ユニットのみON) | 手ハンダ可 |
| 中央CAN保護 | PESD1CAN | SOT-23 |
| C620 CAN | TCAN332DR | SOIC-8 |
| C620 CAN終端 | 120Ω + ソルダージャンパ | 手ハンダ可 |
| C620 CAN保護 | PESD1CAN | SOT-23 |
| LDO | MCP1826S-3302E/DB | SOT-223 |
| MCU | STM32G474RET6(LQFP64) | 0.5mmピッチ、ドラッグはんだ |
| 水晶 | 8MHz + 負荷容量 | 3225等 |
| SWD | 2.54mm 5pinヘッダ or Tag-Connect TC2030 | - |
| BOOT0 | 10kプルダウン + ジャンパ | 手ハンダ可 |
| ID設定 | 3bit DIPスイッチ または 2.54mmジャンパ | 手ハンダ可 |
| デカップリング | 0.1uF x VDDピン数 + 10uF、VDDA用FB+100nF+1uF | 手ハンダ可 |
| AMT22中継 | JST XH 6pin(AMT22側は純正Molex Pico-Lockケーブル) | 2.5mm |
| 外部4線ハーネス | JST XH 4pin(〜3A)。電流が厳しければ電源2線のみXT30に分離 | スルーホール |
| 予備降圧 | OKI-78SR-5互換フットプリント + バイパスジャンパ(通常未実装) | スルーホール |
| 状態LED | 電源/通信/エラー各1 | 手ハンダ可 |
| テストポイント | 5V / 3.3V / GND / COMM_A/B / C620_CAN_H/L / SWO | 手ハンダ可 |

## 回路図作成メモ(2026-07-06確認)

KiCad 10標準ライブラリに以下の検証済みシンボルがあり、ピン配置の正本として使える(自作シンボル起こし不要):

| 部品 | シンボル | 確認済みピン |
|---|---|---|
| STM32G474RET6 | `MCU_ST_STM32G4:STM32G474RETx` | 64pin。NRST=PG10(pin7)、BOOT0=PB8(pin61)、VDD=16/32/48/64、VSS=15/31/47/63、VDDA=29、VSSA=27、VREF+=28、VBAT=1 |
| TCAN332DR | `Interface_CAN_LIN:TCAN332` | 1=TXD、2=GND、3=VCC、4=RXD、5=NC、6=CANL、7=CANH、8=NC |
| MCP1826S-3302E/DB | `Regulator_Linear:MCP1826S` | 1=VIN、2=GND、3=VOUT(SOT-223、タブ=pin2 GND) |
| LM66100(逆接保護の候補) | `Power_Management:LM66100DCK` | 1=VIN、2=GND、3=CE̅、4=NC、5=ST、6=VOUT。ARK CANnodeの逆接保護と同一(CE̅→GND、1.5A) |
| OKI-78SR-5(予備降圧) | `Converter_DCDC:OKI-78SR-5_1.5-W36-C` | 7805互換3pin |

PESD1CANは標準ライブラリに無い。ピン配置はデータシートrev04で確認済み: **1=ライン1、2=ライン2、3=共通(GND)**(SOT-23)。`hardware/lib/`に自作シンボルを起こす。

ARK CANnode Rev 1回路図(`hardware/reference/ARK_CANNODE/`)から流用検討する回路ブロック:

- 逆接保護: LM66100DCK(VIN側2.2uF、CE̅=GND、電流制限1.5A)
- CANコネクタを同一バスで2個並列に載せ、基板上でデイジーチェーンの渡りを作る(中央CANの渡り配線と一致する構成)
- 外部に出る信号線に1ラインESDダイオードを挿入
- 終端120ΩをFETで切替(本基板はソルダージャンパ方式を採用済みなので参考のみ)

## 評価ボードとの関係

(旧「第二段階への移行」。2026-07-02に自作基板方式へ一本化したため、MCU最小構成は冒頭の必須要件に統合した)

- Matek CAN-G474を2系統CANとG474上での主なファーム検証に使う。公式/ArduPilot hwdef上のCAN割当はCAN1=PA11/PA12、CAN2=PB5/PB6。
- CAN-G474でAMT22を接続する場合は、基板上に露出しているSPI2(PB13/PB14/PB15、CS=PB12)へボード別設定を追加する。現行NUCLEO用SPI3(PC10/PC11/PC12、CS=PD2)のままでは使えない。
- NUCLEO-G474REはSWDの確実な復旧、自由なピン引き出し、現行ファームの回帰確認用として保持する。CAN-G474のカスタムファーム書込みと必要I/Oが確認できれば、通常試験では省略可能。
- ピン名はNUCLEOコネクタ番号ではなく `PAx` / `PBx` で管理し、自作基板とNUCLEOで同じ割当を使う。これによりファームを無改造で移植できる。
- NUCLEOで使用済みのピン(LD2=PA5、B1=PC13、VCP=PA2/PA3)は、自作基板では自由に使えるが、NUCLEO検証中は避けるか競合を理解して使う。
- 将来さらに小型化する場合もFDCAN 2系統以上のMCU(STM32G474/G473系)を維持する。STM32G431K系はFDCAN 1系統なので不可。
