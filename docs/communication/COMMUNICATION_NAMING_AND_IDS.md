# 通信・命名・ID設計

## 方針

中央制御と差動ステアユニット間は中央CANで通信する(2026-07-02確定。NUCLEO-G474REのFDCAN 2系統を使う2バスCAN構成)。

外部ハーネスは以下の4線を基本にする。

```text
VIN_CONTROL
GND_CTRL
COMM_A
COMM_B
```

`COMM_A/B` は物理層を抽象化した名前とする。実体は中央CANのCAN_H/CAN_L。シルクにも `COMM_A/B` と書き、`CAN_H/L` とは書かない。

ユニット内部では、NUCLEO-G474REがC620 x2と別バスのCANで通信する。C620 CANはユニット内部専用とし、中央制御には直接露出させない。

```text
中央Teensy
  |
  | VIN_CONTROL / GND_CTRL / COMM_A / COMM_B
  v
差動ステアユニットMCU
  |
  | C620_CAN_H / C620_CAN_L
  v
C620 x2
```

## 通信レイヤー

| レイヤー | 物理層 | 役割 |
|---|---|---|
| mini PC - Teensy | USBシリアル、将来Ethernet | GUI、ログ、設定 |
| Teensy - Unit MCU | 中央CAN(クラシックCAN 1Mbps、FDCAN1想定) | 目標値、状態、キャリブレーション |
| Unit MCU - C620 | C620専用CAN(1Mbps固定、FDCAN2想定) | M3508制御、フィードバック取得 |
| Unit MCU - AMT22 | SPI | ステア絶対角取得 |

## ネット名

### 電源

| ネット名 | 意味 |
|---|---|
| `VBAT_6S` | 6S LiPo入力 |
| `PWR_24V_MOTOR` | C620用24V系 |
| `PWR_12V_PC` | mini PC用12V |
| `PWR_5V_CTRL` | 制御系5V |
| `PWR_3V3_UNIT` | ユニット内3.3V |
| `GND_PWR` | モータ大電流リターン |
| `GND_CTRL` | 制御系GND |

`GND_PWR` と `GND_CTRL` は中央分電盤のスター点で合流させる。

### 中央-ユニット通信

| ネット名 | 意味 |
|---|---|
| `COMM_A` | 中央CANのCAN_H |
| `COMM_B` | 中央CANのCAN_L |
| `COMM_TX` | MCU -> 中央CANトランシーバ |
| `COMM_RX` | 中央CANトランシーバ -> MCU |

ハーネスやコネクタのシルクは `COMM_A/B` とし、`CAN_H/L` とは書かない。RS485時代の `COMM_DE` / `COMM_RE_N` は廃止(CANでは不要)。

### ユニット内CAN

| ネット名 | 意味 |
|---|---|
| `C620_CAN_H` | C620専用CAN High |
| `C620_CAN_L` | C620専用CAN Low |
| `C620_CAN_TX` | MCU -> CANトランシーバ |
| `C620_CAN_RX` | CANトランシーバ -> MCU |

中央-ユニット通信と混同しないため、ユニット内CANには必ず `C620_` 接頭辞を付ける。

### AMT22 SPI

| ネット名 | 意味 |
|---|---|
| `AMT22_SCLK` | SPI clock |
| `AMT22_MOSI` | MCU -> AMT22 |
| `AMT22_MISO` | AMT22 -> MCU |
| `AMT22_CS_N` | AMT22 chip select、Low active |
| `AMT22_5V` | AMT22電源 |

### 安全・状態

| ネット名 | 意味 |
|---|---|
| `ESTOP_N` | 非常停止入力、Lowで停止 |
| `MOTOR_PWR_EN` | メインリレー/コンタクタ制御 |
| `MOTOR_PWR_SENSE` | C620側24V有無検出 |
| `STATUS_LED_R` | 赤表示 |
| `STATUS_LED_Y` | 黄表示 |
| `STATUS_LED_G` | 緑表示 |

信号名に `_N` が付くものはLow activeに統一する。

## ユニットID

ユニットIDは、位置ではなくユニット自身のIDとして扱う。

| ID | 初期割当 |
|---:|---|
| 1 | Front(駆動ユニット) |
| 2 | Rear Left(駆動ユニット) |
| 3 | Rear Right(駆動ユニット) |
| 4 | オドメトリユニット |
| 5-7 | 予備 |
| 0 | ブロードキャスト/予約 |

STATUS系メッセージのpayload意味は**ユニット種別ごとに定義**する(CAN IDの仕組みは共通)。中央側はunitId→種別の対応表を設定で持つ。

IDは0Ωジャンパ列、DIPスイッチ、またはピンヘッダジャンパで設定する。初期は3bit用意し、最大7ユニットまで拡張可能にする。

```text
UNIT_ID0
UNIT_ID1
UNIT_ID2
```

ファーム上の名前は位置名ではなく `unitId` とする。位置対応は中央側の設定で管理する。

## 中央CANプロトコル案

(旧RS485フレーム案は2026-07-02に廃止。SOF/CRC16/SEQ等の独自フレームはCANのアービトレーション・CRC・ACKで置き換えられるため不要になった)

前提:

- クラシックCAN 2.0A、11bit ID、1Mbps。ペイロードは最大8バイト。
- Teensyが周期送信(SET_TARGETを例えば100Hz)、各ユニットも周期送信(STATUSを例えば50Hz)。ポーリング往復は基本使わない。
- 古い指令の検出はシーケンス番号ではなく「周期送信+受信タイムアウト」で行う。
- ユニット同士は直接送信しない(IDを持たない)。

### CAN ID設計

11bit IDは `機能ベースID + unitId(下位3bit)` とする。IDが小さいほど優先度が高い。

| CAN ID | 方向 | 名前 | 内容 |
|---:|---|---|---|
| `0x010` | Teensy -> 全体 | `ESTOP` | 緊急停止ブロードキャスト。最優先 |
| `0x100+id` | Teensy -> Unit | `SET_TARGET` | 目標ステア角、目標ホイールrpm |
| `0x110+id` | Teensy -> Unit | `SET_TARGET_FF` | ステア角速度FF、ホイール加速度FF(協調制御用、2026-07-06追加) |
| `0x120+id` | Teensy -> Unit | `UNIT_CTRL` | enable/disable、キャリブレーション指令(サブコマンド式) |
| `0x140+id` | Teensy -> Unit | `SET_CONFIG` | 制御パラメータ書込 |
| `0x150+id` | Teensy -> Unit | `REQUEST` | CONFIG/CALIB_RESULT等の読出要求 |
| `0x180+id` | Unit -> Teensy | `STATUS1` | 現在ステア角、現在ホイールrpm |
| `0x190+id` | Unit -> Teensy | `STATUS2` | モーター1/2のrpm |
| `0x1A0+id` | Unit -> Teensy | `STATUS3` | バス電圧、状態フラグ、エラーフラグ |
| `0x1C0+id` | Unit -> Teensy | `CONFIG` / `CALIB_RESULT` | REQUESTへの応答 |

- `id` = unitId 1〜7。`0x100+0` のようなid=0はブロードキャスト用に予約。
- ユニットは自分宛(下位3bit一致)と `ESTOP` のみ受信するようFDCANフィルタを設定する。

### UNIT_CTRL サブコマンド(payload byte0)

| 値 | 名前 |
|---:|---|
| `0x01` | `SET_ENABLE`(byte1: 0=無効, 1=有効) |
| `0x02` | `CALIB_START` |
| `0x03` | `CALIB_SAVE_ZERO` |
| `0x04` | `CALIB_CLEAR` |
| `0x05` | `PING`(ユニットはSTATUS3を即時返信) |

## SET_TARGET payload(8バイト)

単位は固定小数点にする。浮動小数点を通信に直接載せない。

| フィールド | 型 | 単位 |
|---|---|---|
| `targetSteerMdeg` | int32 | mdeg、0.001度 |
| `targetWheelRpmMilli` | int32 | rpm x1000 |

旧案にあった `flags` / `timeoutMs` は8バイトに収めるため移動した。`timeoutMs` は `UnitConfig`(SET_CONFIGで設定、既定値持ち)、制御フラグは `UNIT_CTRL` で扱う。

設定された `timeoutMs` を過ぎて次の有効なSET_TARGETが来なければ、ユニットは安全停止へ移行する。

`targetSteerMdeg` の規約(2026-07-06、協調制御対応):

- **連続unwrap角**とする(±180°で折り返さない。int32 mdegで±約200万度分の巻き数を表現可能)。
- ±180°反転+ホイール速度反転の最短化判断は**中央Teensyのみ**が行う。ユニット側は
  受け取った角度へそのまま追従し、反転・最短化を行わない(3輪の過渡整合を守るため。
  詳細は `docs/control/CENTRAL_COORDINATED_CONTROL.md`)。

## SET_TARGET_FF payload(8バイト、2026-07-06追加)

協調制御のフィードフォワード。SET_TARGETと同周期(例100Hz)で送る。

| フィールド | 型 | 単位 |
|---|---|---|
| `targetSteerRateMdegPerS` | int32 | mdeg/s |
| `targetWheelAccelRpmMilliPerS` | int32 | rpm/s x1000 |

- ユニットはステア角速度FFを速度指令へ直接加算する(`θ̇_FF/6 [rpm]` + 角度P項)。
- FF未受信またはSET_TARGETより古い場合はFF=0として動作する(後方互換。FF無しでも
  従来のステップ追従として成立する)。

## STATUS payload(3フレームに分割)

STATUS1(8バイト):

| フィールド | 型 | 単位 |
|---|---|---|
| `steerMdeg` | int32 | mdeg |
| `wheelRpmMilli` | int32 | rpm x1000 |

STATUS2(8バイト):

| フィールド | 型 | 単位 |
|---|---|---|
| `motor1RpmMilli` | int32 | rpm x1000 |
| `motor2RpmMilli` | int32 | rpm x1000 |

STATUS3(8バイト):

| フィールド | 型 | 単位 |
|---|---|---|
| `busVoltageMv` | uint16 | mV |
| `statusFlags` | uint16 | 状態フラグ |
| `errorFlags` | uint32 | エラーフラグ |

STATUS1は高頻度(制御周期に近い)、STATUS2/3は低頻度(例えば10Hz)で送り分けてよい。

## オドメトリユニット(unitId=4)のSTATUS payload

CAN IDの仕組みは駆動ユニットと共通(STATUS1=0x184、STATUS2=0x194、STATUS3=0x1A4)。payloadの意味だけ種別固有。

STATUS1 `ODOM_POSE_XY`(8バイト、高頻度 例100Hz):

| フィールド | 型 | 単位 |
|---|---|---|
| `poseXTenthMm` | int32 | 0.1mm |
| `poseYTenthMm` | int32 | 0.1mm |

STATUS2 `ODOM_POSE_TH`(8バイト、高頻度):

| フィールド | 型 | 単位 |
|---|---|---|
| `poseThetaMdeg` | int32 | mdeg(連続値、±180°で折り返さない) |
| `omegaMdegPerS` | int32 | mdeg/s |

STATUS3 `ODOM_HEALTH`(8バイト、低頻度 例10Hz):

| フィールド | 型 | 単位 |
|---|---|---|
| `busVoltageMv` | uint16 | mV |
| `statusFlags` | uint16 | エンコーダ3輪の正常フラグ等 |
| `errorFlags` | uint32 | カウンタ飽和、更新遅延等 |

- 座標系はCURRENT_SYSTEM_OVERVIEWの定義(+X前、+Y左、+θ反時計)に従う。
- ポーズ積分はオドメトリ基板側で行い、生カウントは中央CANに流さない(帯域節約、駆動ユニットと同じ抽象化方針)。
- `UNIT_CTRL`(0x124)のサブコマンドでポーズリセット(原点セット)を定義する: `0x10 = ODOM_RESET`。

## 状態フラグ

| bit | 名前 | 意味 |
|---:|---|---|
| 0 | `UNIT_ENABLED` | ユニット有効 |
| 1 | `CALIBRATED` | キャリブレーション済み |
| 2 | `AMT22_OK` | AMT22通信正常 |
| 3 | `C620_1_OK` | C620 #1正常 |
| 4 | `C620_2_OK` | C620 #2正常 |
| 5 | `TARGET_ACTIVE` | 有効な目標値あり |
| 6 | `LIMITING_ACTIVE` | rpm制限中 |
| 7 | `ESTOP_ACTIVE` | 非常停止中 |

## エラーフラグ

| bit | 名前 | 意味 |
|---:|---|---|
| 0 | `ERR_AMT22_TIMEOUT` | AMT22応答なし |
| 1 | `ERR_AMT22_CHECK` | AMT22チェックビット異常 |
| 2 | `ERR_C620_1_TIMEOUT` | C620 #1フィードバックなし |
| 3 | `ERR_C620_2_TIMEOUT` | C620 #2フィードバックなし |
| 4 | `ERR_TARGET_TIMEOUT` | 中央からの指令途絶 |
| 5 | `ERR_OVERRPM_LIMIT` | rpm制限超過 |
| 6 | `ERR_NOT_CALIBRATED` | 未キャリブレーション |
| 7 | `ERR_ESTOP` | 非常停止 |
| 8 | `ERR_CONFIG_CRC` | 保存設定CRC異常 |

## C620 CAN ID

C620 CANはユニット内部専用なので、各ユニットで同じC620 IDを使い回してよい。

推奨:

| 対象 | C620 ID | CAN ID |
|---|---:|---:|
| Motor 1 | 1 | feedback `0x201` |
| Motor 2 | 2 | feedback `0x202` |
| Command | 1-4 group | command `0x200` |

各ユニット内CANが独立していれば、全ユニットでC620 ID 1/2を再利用できる。

1 CAN共有構成を採る場合のみ、C620 x6でIDが衝突しないように1-6を割り当てる。

## ファーム上の命名

| 名前 | 用途 |
|---|---|
| `UnitTarget` | 中央からの目標値 |
| `UnitStatus` | ユニット状態 |
| `UnitConfig` | 保存設定 |
| `CalibrationData` | AMT22ゼロ点 |
| `MotorPairCommand` | C620 x2への指令 |
| `DifferentialKinematics` | 差動運動学 |

## 将来拡張に強い命名ルール

- 外部通信は `COMM_*` と呼び、物理層名を入れない。
- C620専用CANだけ `C620_CAN_*` と明示する。
- 位置名は中央設定に閉じ込め、ユニット側は `unitId` のみを持つ。
- Low active信号は `_N` で終える。
- 電源は `PWR_*`、大元バッテリは `VBAT_*`、GNDは用途別に `GND_PWR` / `GND_CTRL` とする。
- 通信payloadは固定小数点を使い、単位を名前に含める。

