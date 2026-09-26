# オドメトリ基板(STM32F405)要件

> **2026-09-25 ODOM V2確定:** 基板側エンコーダ端子J4/J5/J6は **1=A、2=+5V、3=B、4=GND**。ユーザーがハーネスのねじれ回避のため変更した配列で、V2では本文の旧配列表に優先する。センサ側コネクタの番号とは区別する。

> **V2改版（2026-09-23着手）**: デバッグ・TP・V1修正の変更要件は[共通V2要件](UNIT_ODOMETRY_V2_REQUIREMENTS.md)を優先する。本文のGH6/SWD・UART一体配列はV1仕様。V2の正式ヘッダ型番とPCB配線は未確定/未完了。

## 目的

3輪オドメトリ(AMT102クアドラチャエンコーダ x3、測定輪)とSPI IMUを扱い、基板上で車体状態を推定してセンサーCANへ配信する専用ノード。unitId=4。

> **センサ変更(2026-07-08確定)**: I2Cホール(磁気)エンコーダ案(MT6701/AS5600)は、
> 測定輪シャフトへの磁石・センサ位置合わせの機械接続が難しいため廃止。AMT102 x3へ戻す。
> ただしZ相は使わず、各センサは**4線(VCC/GND/A/B)**のみを配線する。
> オドメトリは相対移動の積分なので、インデックス(Z)なしで成立する。起動時の絶対位置は不要。
>
> **ユニット基板とは別形状の自作PCBとする(2026-07-17)。** MCU最小構成、電源、CAN、デバッグ回路は共通ブロックとして流用する。
>
> **MCU変更(2026-07-25確定)**: 部室在庫から発掘した`STM32F405RGT6`(LQFP64)を採用し、購入済みG474RET6の消費を1個減らす。
> オドメトリ基板はセンサーCAN1系統のみ必要(C620用の2本目CANが要らない)ため、ユニット基板がG474を選んだ決め手の
> 「FDCAN 2系統必要」という制約がそもそも掛からない。センサーCANは`Classic CAN 1Mbps`固定(`CAN方式・速度`確定事項)
> でCAN FDの機能は使わないため、F405の`bxCAN`(Classic CAN専用、FD非対応)で要件を満たす。
> 詳細ピン割当は`STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`。旧`STM32G474_ODOMETRY_PIN_ASSIGNMENT.md`は履歴として残す。

## 方針

- MCUは**STM32F405RGT6(LQFP64、部室在庫を使用。2026-07-25確定)**。ユニット基板(STM32G474RET6)とはMCUファミリが異なるため、
  KiCad MCU最小構成ブロックとファームのplatform層はユニット基板と共通化できない(F4用に新規作成)。電源・CANトランシーバ・
  コネクタ選定など、MCUに依存しないブロックは`CARRIER_BOARD_REQUIREMENTS.md`と共通のまま流用する。
- 外部接続は電源GH 2pin(5V/GND)とセンサーCAN GH 3pin(COMM_A/B/GND)を分離する。CANは将来センサーノードを追加できるよう、同一バスのGH 3pinを2個載せる。
- 中央CANブロック・電源ブロックは`CARRIER_BOARD_REQUIREMENTS.md`と共通(KiCadブロック流用)。C620用の2本目CANは元々不要(F405はCAN2も持つが未使用)。

## AMT102入力 x3(クアドラチャ、Z相なし)

| 項目 | 内容 |
|---|---|
| センサ | **`AMT102-V`インクリメンタルエンコーダ x3に確定** |
| 配線 | **GH 4pin、1=VCC / 2=GND / 3=A / 4=B。Z相はコネクタにも配線しない** |
| 電源 | AMT102仕様に従う。5V給電を基本とし、基板側5V制御電源から分配 |
| 信号入力 | A/B相をSTM32タイマのEncoder Modeへ入力。Z相なしのため原点復帰・絶対位置検出は行わない |
| レベル | **`SN74LVC2G17DBVR` x3に確定**。3.3V給電、5.5V tolerant Schmitt入力、1エンコーダのA/Bに1 IC。各ICに100nFデカップリング |
| 終端/保護 | **`ESDS452DBZR` x3に確定**。5.5V working、2ch双方向、SOT-23-3。各コネクタ直近でA/Bを保護し、その後段に各線100Ω初期値の直列抵抗を置いて`SN74LVC2G17`へ入れる。順序はコネクタ -> TVS -> 直列R -> Schmitt buffer -> MCU。RCコンデンサはDNP footprintのみ用意し、実波形確認後に定数を決める |
| 分解能 | AMT102側DIP設定で決める。ファームの`countsPerRev`設定と一致させる。x4 decodeなので1回転カウントはPPRの4倍 |
| 方向 | 各輪ごとに符号設定をFlash保存し、手回し検証で+方向を合わせる |

タイマEncoder Mode割当案:

| センサ | タイマ | A相 | B相 |
|---|---|---|---|
| Wheel 1 | TIM2 | PA0 (TIM2_CH1) | PA1 (TIM2_CH2) |
| Wheel 2 | TIM3 | PA6 (TIM3_CH1) | PA7 (TIM3_CH2) |
| Wheel 3 | TIM4 | PB6 (TIM4_CH1) | PB7 (TIM4_CH2) |

共通部: CAN1=PA11/PA12、デバッグUART=PA2/PA3、LED=PA5/PB10/PB11、SWD=PA13/PA14、HSE=PH0/PH1、BOOT0=専用ピン。
**GPIO名はユニット基板(G474)と同一だが、機能ブロック名・専用ピンの有無はF405で変わっている点に注意(下記F405固有要件を参照)。**

**ユニット基板(G474)との差分に注意**:

- ID: ユニット基板と共通の3bit DIPスイッチ(PC6/PC7/PC8、内部プルアップ、ON=GND)を実装し、unitId=4(0b100)に設定する(2026-07-20確定)。起動時にRUN LEDをID回数点滅させる動作も共通。GPIO名はG474と同じPC6/PC7/PC8のまま流用できる。
- 5V監視ADC: **Rev.Aでは非実装に確定**。PA0/PA1はTIM2に専用し、PC0への移設も行わない。
- PB6/PB7はTIM4で使うため、I2C1や他機能には使わない。

## F405固有の要件(G474との回路差分)

MCUファミリが変わったことによる、単なるピン名の読み替えでは済まない差分。回路図に反映が必要。

| 項目 | G474(ユニット基板) | F405(オドメトリ基板) |
|---|---|---|
| デバッグUART | LPUART1(PA2/PA3, AF12) | **USART2**(PA2/PA3, AF7)。ピンは同じだがLPUART1が存在しないため置き換え |
| HSE水晶 | PF0/PF1 | **PH0/PH1**。unit board採用品の8MHz水晶とC0G 10pF初期値を流用し、負荷容量はF405実基板で確認 |
| BOOT0 | PB8と共用のGPIO(10kΩプルダウン) | **GPIO非共用の専用ピン**。10kΩプルダウン+テストポイントは踏襲 |
| VCAP_1/VCAP_2 | 無し(G4は不要) | **必須。各2.2µF(X5R/X7R、ESR < 2Ω)を追加。** 内蔵レギュレータの安定化用で、省略するとMCUが正常起動しない |
| VREF+ | 専用ピンあり(VDDA経由で分離) | **専用ピン無し。内部でVDDAに直結。** VREF+用のフットプリント・配線は不要 |
| VDD/VSSデカップリング | 各VDDピンに100nF | VDD=pin 19/32/48/64へ各100nF、全体に4.7µF以上。VSS=pin 18/63を全てGNDへ接続 |
| CANペリフェラル | FDCAN(Classic CANモードで使用) | **bxCAN**(元々Classic CAN専用、CAN FD非対応)。センサーCANはClassic CAN 1Mbps固定なので機能上の差分なし |

物理ピン番号はST公式DS8626 Rev.12を正とし、KiCad 10標準`STM32F405RGTx`シンボルと相互照合済み。

## ファーム要件

- TIM2/TIM3/TIM4をEncoder Mode(x4 decode)で動かし、固定周期(1kHz)で各カウンタ差分を読む。
- 16bitタイマを使う場合は符号付き差分でwrapを処理する。TIM2は32bitでも、3輪で同じ差分処理に揃えてよい。
- 差分countから各測定輪の移動量・輪速へ変換し、3輪オムニの順運動学でvx/vy/ωへ変換、x/y/θを積分する。
- ホイール配置(半径、取付角、車体中心からの距離)、エンコーダ`countsPerRev`、各輪の符号を`UnitConfig`としてFlashに保存し、SET_CONFIGで書き換え可能にする。
- 座標系は+X前/+Y左/+θ反時計(CCW)。θは折り返さず連続値で保持する。
- 配信: STATUS1/2(pose)を100Hz、STATUS3(健全性: カウンタ更新、差分飽和、設定不整合等)を10Hz(`COMMUNICATION_NAMING_AND_IDS.md`参照)。
- `ODOM_RESET`(UNIT_CTRLサブコマンド0x10)で原点リセット。
- **F405移行に伴うファーム注記(2026-07-25)**: `firmware/src/platform/`配下は現状STM32G4専用実装(`stm32g4xx_min.h`、`system_stm32g4xx.c`、`startup_stm32g4xx.s`等)。
  オドメトリ基板用ファームはこれを流用できず、STM32F4向けのクロック初期化・GPIO・USART・bxCANドライバを新規に書く必要がある。
  既存`unit_controller`は差動ステア制御専用なので、そのまま流用しない。固定小数点変換、CRC等の汎用部だけを分離して再利用し、
  3輪オドメトリ運動学・積分・F4 Flash sector管理・種別固有STATUS生成はオドメトリ用アプリケーションとして新規実装する。

## SPI IMU / センサーフュージョン

- Rev.AはIMU IC直載せず、**市販ブレークアウトモジュールを1個固定実装**する。汎用の複数IMU拡張コネクタは設けない。
- モジュールはピンヘッダのみで揺れる取付けを避け、スペーサ/ネジまたは低背コネクタ+機械固定でオドメトリ基板に剛結する。重要なのはPCB全体の厚さより、モジュールの相対姿勢が変化しないことである。
- **IMUは`ICM-42688-P`搭載ブレークアウトモジュールに確定し、2026-07-25購入済み。** 購入先は
  [AliExpress item 1005012473450791](https://ja.aliexpress.com/item/1005012473450791.html)。
- ホスト接続は4-wire SPIとし、F405 SPI3のPC10=SCK、PC11=MISO、PC12=MOSI、PD2=`IMU_CS_N`へ接続する。
  `IMU_INT1`はPC4、`IMU_INT2`はPC5へ接続する。Rev.AはINT1をData Readyに使用し、INT2は予備割り込みとする。
- 購入モジュールの8pin表記は`VCC / GND / AD0(MISO) / SDA(MOSI) / SCL(SCLK) / CS / INT1 / INT2`。
  SPI使用時は次表のとおり接続する。

  | モジュールpin | F405信号 | GPIO | 備考 |
  |---|---|---|---|
  | VCC | PWR_3V3 | - | モジュールは5V/3.3V給電対応表記だが、本基板では3.3V固定 |
  | GND | GND | - | - |
  | AD0/MISO | SPI3_MISO | PC11 | I2C時はアドレス選択、SPI時はMISO |
  | SDA/MOSI | SPI3_MOSI | PC12 | I2C時はSDA、SPI時はMOSI |
  | SCL/SCLK | SPI3_SCK | PC10 | - |
  | CS | IMU_CS_N | PD2 | Low active |
  | INT1 | IMU_INT1 | PC4 | Data Ready |
  | INT2 | IMU_INT2 | PC5 | 予備割り込み |

- モジュールは5V/3.3V給電対応だが、F405との信号電圧を確実に揃えるため**VCC=3.3V固定**とする。
  IC単体のVDD/VDDIO定格は1.71～3.6Vであり、5VをIC信号へ直接加えない。
  キャリア側にも100nF+2.2µFをモジュール電源直近へ置き、unit board採用品を流用する。
- 初回bring-upはSPI Mode 0、SCK 1MHz以下で開始し、`WHO_AM_I`(register `0x75`)が`0x47`であることを確認してから周期取得へ進む。
  IC仕様上の4-wire SPI上限は24MHzだが、Rev.Aの通常動作速度は配線波形とエラーログを確認して決める。
- ヘッダの信号順は購入品のシルクで上記8pinと確認済み。物理pin 1の向き、pin pitch、外形、固定穴、
  オンボードLDO/レベル変換回路は到着後に表裏写真、寸法、導通で確認し、フットプリントと機械固定寸法を確定する。
- 測定輪オドメトリとジャイロ角速度をMCU上で融合し、pose/twist、IMU健全性、温度をセンサーCANへ配信する。
- 生IMUの高周期配信は行わない方針とする。F405の`bxCAN`はCAN FDに対応しないため(2026-07-25、MCU変更に伴い確定)、
  融合結果をClassic CAN 1Mbpsで配信する現行方針を継続し、生IMU高周期配信が必要になった場合は
  データ量を間引く・専用フレームに分割するなどClassic CANの範囲で対応する。

## 基板シルク方針

- 抵抗・コンデンサ・ICなどの部品番号(`R*`、`C*`、`U*`等)は常時表示しない。実装照合にはKiCad組立図/F.Fabを使用する。
- 部品外形とpin 1/極性マークは、実装方向を誤る可能性がある部品について残す。
- 基板上へ追加する機能シルクは以下を優先する。
  - 基板名、`Rev.A`、製造年月または設計リビジョン
  - 電源入力`5V`/`GND`と極性、センサーCANの`COMM_A`/`COMM_B`/`GND`
  - AMT102コネクタの`WHEEL 1`/`WHEEL 2`/`WHEEL 3`、pin 1、`5V/GND/A/B`
  - IMUコネクタのpin 1、`3V3/GND/SCK/MISO/MOSI/CS/INT1/INT2`、基板座標に対する`+X/+Y`方向
  - CAN終端スイッチの`TERM OFF/ON`
  - 3bit ID DIPの`ID0/ID1/ID2`、`ON`方向、通常設定`unitId=4 (100)`
  - LEDの`PWR`/`RUN`/`COMM`/`ERR`
  - デバッグコネクタのpin 1、`SWD`、`UART`
  - `BOOT0`、`NRST`、主要電源テストポイント(`5V`、`3V3`、`GND`)
- コネクタ直下へ隠れる文字、パッド/露出銅上の文字、基板端で欠ける文字は避ける。最終配置後にF.SilkS Gerberを確認する。

## 検証

1. 1輪だけ接続し、手回しでカウント増減、回転方向の符号、1回転あたりcount数を確認。
2. AMT102のDIP分解能設定とファーム`countsPerRev`が一致することを確認。
3. 3輪接続し、車体を既知距離だけ直進・並進・回転させてx/y/θの誤差を測る。
4. モーター通電状態でA/B入力の誤カウント有無を確認する。停止中にカウントが増えないこと、一定回転で差分が滑らかなことを見る。

## 部品リスト差分(ユニット基板との違い)

| ブロック | 内容 |
|---|---|
| 追加 | AMT102 GH 4pin x3(5V/GND/A/B)、`SN74LVC2G17DBVR` x3、`ESDS452DBZR` x3、A/B直列抵抗100Ω x6、RC調整用DNP footprint x6、固定実装のSPI IMUブレークアウト x1、VCAP_1/VCAP_2用2.2µF x2(F405必須) |
| 削除 | C620 CANトランシーバ一式、AMT22(SPI)コネクタ、I2C磁気エンコーダコネクタ、I2Cプルアップ、VREF+専用フットプリント(F405はVDDA直結のため不要) |
| 流用 | `LM66100DCKR`、`TLV76133DCYR`、`TCAN1051VDRQ1`、8MHz HSE、VDDAフェライト/コンデンサ、GHコネクタ、LED、SWD/UART回路。正式型番は`STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`の流用表を正本とする |
| 変更 | 5V監視ADCはRev.Aで非実装。デバッグUARTはLPUART1→USART2、HSE pinはPF0/PF1→PH0/PH1、BOOT0はGPIO共用→専用pin(いずれもF405移行に伴う変更) |

## 廃止案(磁気エンコーダ x3、2026-07-08廃止)の記録

2026-07-06にAMT102からI2Cホール磁気エンコーダ(MT6701第一候補、AS5600代替)へ一度変更した。
センサ費は安いが、測定輪シャフト端への磁石固定、センサ基板とのギャップ・同軸度確保、
マウント調整が必要で、現機構ではシャフト接続の難易度が高いと判断して廃止。
電気的にはI2Cバス3本(I2C1=PA15/PB7、I2C2=PA9/PA8、I2C3=PC8/PC9)案だった。
