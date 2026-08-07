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
| mini PC - ESP32-C3 | Wi-Fi/UDP、50Hz | DualSenseの手動車体twist要求 |
| ESP32-C3 - Teensy CAN2 | Classic CAN 1Mbps | `MANUAL_TWIST_CMD`。ESP32は3輪IKを行わない |
| Teensy CAN3 - Unit MCU FDCAN1 | 駆動中央CAN(CAN FD nominal 1Mbps/data 2Mbps、BRS) | 時刻付き軌道、状態、キャリブレーション |
| Unit MCU - C620 | C620専用CAN(1Mbps固定、FDCAN2想定) | M3508制御、フィードバック取得 |
| Teensy CAN1 - F405 | センサーCAN(Classic CAN 1Mbps) | オドメトリ/IMU |
| Unit MCU - AMT22 | SPI | ステア絶対角取得 |

ESP32-C3内蔵TWAIはClassic CAN専用なので、CAN FDフレームが流れる駆動CAN3へ接続しない。
手動入力ゲートウェイは汎用拡張のTeensy CAN2へ接続し、Teensyが受信した車体twistを
通常の中央プロファイラ・3輪IKへ渡す。物理配線とUDP詳細は
`docs/software/ESP32_DUALSENSE_CAN_GATEWAY.md`を正本とする。

## 手動入力CAN2プロトコル

`MANUAL_TWIST_CMD`は標準11bit ID、Classic CAN 8byte、1Mbps、50Hz。複数バイト整数は
little-endian。ESP32はUDPが150ms以上途絶した場合、速度をすべて0、flagsを0にして送る。

| CAN ID | 方向 | 名前 | 内容 |
|---:|---|---|---|
| `0x080` | ESP32-C3 -> Teensy CAN2 | `MANUAL_TWIST_CMD` | 手動車体速度要求。安全Enableやユニット目標ではない |

| offset | フィールド | 型 | 単位/意味 |
|---:|---|---|---|
| 0 | `vxMmPerS` | int16 | 車体+X前、mm/s |
| 2 | `vyMmPerS` | int16 | 車体+Y左、mm/s |
| 4 | `omegaMradPerS` | int16 | 反時計回り正、mrad/s |
| 6 | `sequenceLow` | uint8 | UDP sequence下位8bit |
| 7 | `flags` | uint8 | bit0=`DEADMAN`、bit1=`WIFI_FRESH`。両方1でのみ有効 |

Teensy側でもCAN受信watchdogを持ち、freshな連番と両flagを確認できない場合は手動twistを0へ
ランプダウンする。無線の停止要求は補助停止であり、`ESTOP`やハードNCループの代替にしない。

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

## 駆動中央CANプロトコル

(旧RS485フレーム案は2026-07-02に廃止。SOF/CRC16/SEQ等の独自フレームはCANのアービトレーション・CRC・ACKで置き換えられるため不要になった)

前提:

- CAN FD、標準11bit ID、nominal 1Mbps/data 2Mbps、BRS有効。ペイロードは最大64バイト。
- Teensyは`TRAJECTORY_FD`を200〜250Hzで3ユニットへ送り、最後に
  `TRAJECTORY_COMMIT`をbroadcastする。各G474は受信区間を局所1kHzで補間する。
- G474は`UNIT_STATUS_FD`を200Hzで返す。実ハーネスでbit stuffing込みbus loadを測り、
  定常50%以下を目標とする。
- C620専用CANとF405センサーCANはClassic CAN 1Mbpsのまま別物理バスに置く。
- 既存8byte `SET_TARGET`/`SET_TARGET_FF`/`STATUS1..3`はベンチ・移行期の互換経路として残す。
- FD軌道の古い指令はsequenceと受信タイムアウトの両方で検出する。
- ユニット同士は直接送信しない(IDを持たない)。

### CAN ID設計

11bit IDは `機能ベースID + unitId(下位3bit)` とする。IDが小さいほど優先度が高い。

| CAN ID | 方向 | 名前 | 内容 |
|---:|---|---|---|
| `0x010` | Teensy -> 全体 | `ESTOP` | 緊急停止ブロードキャスト。最優先 |
| `0x020` | Teensy -> Unit x3 | `TRAJECTORY_COMMIT` | 同一sequenceの軌道を全3輪で同時適用 |
| `0x100+id` | Teensy -> Unit | `SET_TARGET` | 目標ステア角、目標ホイールrpm |
| `0x110+id` | Teensy -> Unit | `SET_TARGET_FF` | ステア角速度FF、ホイール加速度FF(協調制御用、2026-07-06追加) |
| `0x120+id` | Teensy -> Unit | `UNIT_CTRL` | enable/disable、キャリブレーション指令(サブコマンド式) |
| `0x130+id` | Teensy -> Unit | `TRAJECTORY_FD` | 1区間のsteer/wheel状態・微分、32byte |
| `0x140+id` | Teensy -> Unit | `SET_CONFIG` | 制御パラメータ書込 |
| `0x150+id` | Teensy -> Unit | `REQUEST` | CONFIG/CALIB_RESULT等の読出要求 |
| `0x160+id` | mini PC bench -> Unit | `SET_TARGET_ACCEL_FF` | 明示ステア角加速度FF、Classic CAN移行ベンチ専用 |
| `0x180+id` | Unit -> Teensy | `STATUS1` | 現在ステア角、現在ホイールrpm |
| `0x190+id` | Unit -> Teensy | `STATUS2` | モーター1/2のrpm |
| `0x1A0+id` | Unit -> Teensy | `STATUS3` | バス電圧、状態フラグ、エラーフラグ |
| `0x1B0+id` | Unit -> Teensy | `UNIT_STATUS_FD` | 追従状態・mode電流・制約状態、48byte |
| `0x1C0+id` | Unit -> Teensy | `CONFIG` / `CALIB_RESULT` | REQUESTへの応答 |

- `id` = unitId 1〜7。`0x100+0` のようなid=0はブロードキャスト用に予約。
- ユニットは自分宛(下位3bit一致)、`ESTOP`、`TRAJECTORY_COMMIT`のみ受信するようFDCANフィルタを設定する。

## TRAJECTORY_FD / COMMIT payload

`TRAJECTORY_FD`は32バイト。3ユニット分を先にpendingへ受信し、同じsequenceの
`TRAJECTORY_COMMIT`を受けた時点で一斉に適用する。これによりTeensy/G474間の絶対時刻同期を
必須にせず、3輪の開始時刻断面を揃える。

| offset | フィールド | 型 | 単位 |
|---:|---|---|---|
| 0 | `sequence` | uint32 | 制御区間番号 |
| 4 | `segmentDurationUs` | uint32 | 区間時間 |
| 8 | `targetSteerMdeg` | int32 | 連続unwrap mdeg |
| 12 | `targetSteerRateMdegPerS` | int32 | mdeg/s |
| 16 | `targetSteerAccelMdegPerS2` | int32 | mdeg/s^2 |
| 20 | `targetWheelRpmMilli` | int32 | rpm x1000 |
| 24 | `targetWheelAccelRpmMilliPerS` | int32 | rpm/s x1000 |
| 28 | `flagsReserved` | uint32 | 初期0、将来拡張 |

`TRAJECTORY_COMMIT`は8バイトの短い高優先度フレームとし、`sequence` uint32と
`controllerTimeUs` uint32を載せる。各ユニットは同sequenceのpendingがなければ前区間を
安全に継続し、`TRAJECTORY_MISSING`を立てる。古いsequence、重複commit、duration=0は拒否する。

`UNIT_STATUS_FD`は48バイトとし、少なくともsequence echo、ユニット時刻、連続steer角、
実steer/wheel rpm、motor 1/2 rpm、steer/drive mode電流と積分値、bus電圧、最高温度、
planned/hard包絡scale、状態/エラーフラグを含める。詳細offsetは実装時に固定する。

### UNIT_CTRL サブコマンド(payload byte0)

| 値 | 名前 |
|---:|---|
| `0x01` | `SET_ENABLE`(byte1: 0=無効, 1=有効) |
| `0x02` | `CALIB_START` |
| `0x03` | `CALIB_SAVE_ZERO` |
| `0x04` | `CALIB_CLEAR` |
| `0x05` | `PING`(ユニットは`CALIB_RESULT`を即時返信) |

`CALIB_SAVE_ZERO`と`CALIB_CLEAR`は、ユニット無効・AMT読取正常・C620フィードバック正常・
両モーター出力軸速度1rpm以下の場合だけ受理する。`CALIB_START`はFlashを書き換えない状態確認、
`PING`は保存状態の読出しに使う。

### CALIB_RESULT payload(8バイト、2026-07-31実装)

`UNIT_CTRL`の`CALIB_START` / `CALIB_SAVE_ZERO` / `CALIB_CLEAR` / `PING`に対し、
`0x1C0+id`で即時返信する。複数バイト整数はlittle-endian。

| offset | フィールド | 型 | 内容 |
|---:|---|---|---|
| 0 | `zeroPositionCounts` | uint16 | 保存済みAMT生カウント。未校正は`0xFFFF` |
| 2 | `currentRawPositionCounts` | uint16 | 現在のAMT生カウント。stale/無効は`0xFFFF` |
| 4 | `sequence` | uint16 | 保存レコードsequence下位16bit |
| 6 | `flags` | uint16 | 下表 |

| flags bit | 名前 | 意味 |
|---:|---|---|
| 0 | `CALIBRATED` | 有効なCRC付き原点レコードあり |
| 1 | `CRC_ERROR` | ページ内に破損/電断途中レコードあり。以前の有効レコードは使用可能 |
| 2 | `PAGE_FULL` | 追記領域なし。明示`CALIB_CLEAR`が必要 |
| 3 | `LAST_OP_FAILED` | 直前の指令を安全条件またはFlashエラーで拒否 |
| 4 | `RAW_FRESH` | 現在生カウントが100ms以内 |

AMT角の適用式は`(rawPositionCounts - zeroPositionCounts) & 0x0FFF`。G474REのFlash最終
2KiBページをファーム領域から予約し、24byte CRC32付きレコードを追記する。通常保存では
ページを自動消去せず、書込み途中でも直前の有効レコードを残す。ページ消去はGUIで確認を
伴う`CALIB_CLEAR`だけが行う。

## SET_TARGET payload(8バイト)

単位は固定小数点にする。浮動小数点を通信に直接載せない。
複数バイト整数はlittle-endianで載せる。

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

## SET_TARGET_ACCEL_FF payload(8バイト、Classic CANベンチ移行用)

CAN FDの`TRAJECTORY_FD.targetSteerAccelMdegPerS2`を実装・評価するまで、現行MTU=16の
単体ベンチだけで使う互換フレーム。mini PCは`SET_TARGET_FF`と同じ200Hzで送る。

| offset | フィールド | 型 | 単位 |
|---:|---|---|---|
| 0 | `targetSteerAccelMdegPerS2` | int32 | mdeg/s^2 |
| 4 | `reserved` | int32 | 0固定 |

G474は200ms以内の明示加速度を受信中、これを加速/制動phase判定と加速度FFへ優先使用する。
値は現コミッショニング範囲の±2000 axis rpm/sへclampする。フレームが途絶した場合は、既存
`SET_TARGET_FF`角速度の受信周期差分(±1000 axis rpm/s clamp)へ自動復帰する。最終構成では
同じ値を`TRAJECTORY_FD`へ統合し、このIDは単体ベンチ互換経路だけに残す。

## SET_CONFIG payload(8バイト、ベンチ調整用)

| offset | フィールド | 型 | 単位 |
|---:|---|---|---|
| 0 | `parameterIndex` | uint8 | 下表のindex |
| 1 | reserved | uint8[3] | 0 |
| 4 | `valueMilli` | int32 | パラメータ値 x1000 |

現行実装の追加パラメータ:

| index | 名前 | 範囲 | 既定値 | 備考 |
|---:|---|---:|---:|---|
| 22 | `status_period_ms` | 0、1〜100ms | 0 | 0でSTATUS1/2を通常周期へ戻す |
| 23 | `steer_observer_correction_tau_s` | 0〜1s | 0.050s | motor mode速度予測をAMT22絶対角へ戻す相補observer時定数。0はAMT直接追従 |
| 24 | `steer_friction_ff_fade_axis_rpm` | 0〜100rpm | 10rpm | observer軸速度0でfriction FFを全量、指定速度で0まで線形減衰。0は減衰無効 |
| 25 | `steer_mode_backcalc_gain` | 0〜20/s | 0 | 共通current scale後のsteer残差を積分へ戻す。0は無効 |
| 26 | `drive_mode_backcalc_gain` | 0〜20/s | 0 | 共通current scale後のdrive残差を積分へ戻す。0は無効 |
| 27〜31 | steer gain knot 0 (0rpm) | field依存 | 既定scalar値 | 順に`Kp/Ki/accelFF/decelFF/Kaw` |
| 32〜36 | steer gain knot 1 (60rpm) | field依存 | 既定scalar値 | 順に`Kp/Ki/accelFF/decelFF/Kaw` |
| 37〜41 | steer gain knot 2 (100rpm) | field依存 | 既定scalar値 | 順に`Kp/Ki/accelFF/decelFF/Kaw` |
| 42〜46 | steer gain knot 3 (150rpm) | field依存 | 既定scalar値 | 順に`Kp/Ki/accelFF/decelFF/Kaw` |
| 47 | `steer_brake_kp_multiplier` | 1〜4 | 1 | target加速度と速度が逆符号の制動phaseだけscheduled Kpへ乗算 |
| 48〜51 | steer brake Kp multiplier knot | 1〜4 | index 47の値 | 順に0/60/100/150rpm。速度scheduleで連続補間し、制動phaseだけ適用 |

gain knot各fieldの範囲は`Kp/Ki=0〜500`、`accelFF/decelFF=0〜10`、
`Kaw=0〜20/s`。legacy scalar index 3/4/18/20/25を書き込むと全knotを同じ値へ戻す。
index 47も全brake倍率knotを同じ値へ戻す。したがって個別knotはscalar値より後に送信する。

observer出力はindex 24のfriction FFスケジュールだけに使用する。角度P、保護判定、
`MOTION_SETTLED`は従来のAMT角/mode速度を使用する。

## STATUS payload(3フレームに分割)

STATUS1(8バイト):

| フィールド | 型 | 単位 |
|---|---|---|
| `steerMdeg` | int32 | mdeg |
| `wheelRpmMilli` | int32 | rpm x1000 |

STATUS2(8バイト):

| フィールド | 型 | 単位 |
|---|---|---|
| `motor1RpmMilli` | int32 | モータrotor rpm x1000 |
| `motor2RpmMilli` | int32 | モータrotor rpm x1000 |

M3508+C620ではC620フィードバックのrotor rpmを格納する。減速機出力軸rpmや
drive/steer mode rpmへ変換せず、受信側がM3508内部減速比19と差動運動学を適用する。
通常周期はSTATUS1=20ms、STATUS2=50ms。ベンチ同定時は`SET_CONFIG idx22`に周期ms
(1〜100)を設定して両方を高頻度送信できる。idx22=0は通常周期へ戻す。

STATUS3(8バイト):

| フィールド | 型 | 単位 |
|---|---|---|
| `busVoltageMv` | uint16 | mV |
| `statusFlags` | uint16 | 状態フラグ |
| `errorFlags` | uint32 | エラーフラグ |

`busVoltageMv=0xffff`は電圧計測未実装を表す。現行G474ベンチ実装の`statusFlags`:

| bit | 名前 | 条件 |
|---:|---|---|
| 0 | `ACTIVE` | 局所制御が有効 |
| 1 | `TARGET_FRESH` | SET_TARGETがtimeout内 |
| 2 | `FEEDBACK_OK` | C620 x2 feedbackがfresh |
| 3 | `AMT_OK` | AMT22読出し/check bit正常 |
| 4 | `STEER_IN_BAND` | 角度誤差0.5deg以下、実steer軸1rpm以下、steer FF 0.1rpm以下 |
| 5 | `WHEEL_IN_BAND` | wheel誤差がmax(12rpm, 目標の6%)以下、wheel加速度FFが±1rpm/s以下 |
| 6 | `MOTION_SETTLED` | bit4/5を100ms連続で満たした |
| 7 | `LIMITING_ACTIVE` | ユニット内rpm包絡の保護制限が作動 |
| 8 | `CALIBRATED` | CRC付きAMT原点をFlashから読出し済み |
| 9 | `CONFIG_CRC_ERROR` | 校正ページにCRC不一致/途中書込みレコードあり |
| 10 | `CALIB_PAGE_FULL` | 校正追記ページに空きなし |
| 11 | `TORQUE_SCALING_ACTIVE` | 合成motor電流が上限を超え、steer/driveを共通scale中 |
| 12 | `STEER_BRAKING_ACTIVE` | 現行加速度FFが制動gainを選択中 |

中央は新しい指令後に一度`MOTION_SETTLED=0`を確認してから立上りを採用し、前指令の残留フラグを
完了と誤認しない。中央自身のプロファイル完了も同時に必要で、フラグ単独を経路完了にしない。
現行周期はSTATUS1/3=20ms、STATUS2=50ms。idx22使用時もSTATUS3は20msを維持する。

### UNIT_STATUS_DIAG(移行用Classic CAN、2026-07-31実装)

中央CANをCAN FDへ切り替える前の実機ベンチでは、`0x1B0+id`を8byte×4pageで巡回送信する。
通常はSTATUS1と同じ20msごとに1page、`SET_CONFIG idx22`使用時は指定周期ごとに1pageを送る。
最終的には同じIDの`UNIT_STATUS_FD`へ置換し、このpage形式は互換ベンチ経路だけに残す。

共通byte:

| offset | フィールド | 型 | 内容 |
|---:|---|---|---|
| 0 | `page` | uint8 | 0〜2 |
| 1 | `diagFlags` | uint8 | bit0=current scale、bit1=steer braking、bit2=explicit steer accel active |

page 0:

| offset | フィールド | 型 | 単位 |
|---:|---|---|---|
| 2 | `steerScheduleRpmCenti` | uint16 | steer axis rpm x100 |
| 4 | `scheduledKpDeci` | uint16 | Kp x10 |
| 6 | `scheduledKiDeci` | uint16 | Ki x10 |

page 1:

| offset | フィールド | 型 | 単位 |
|---:|---|---|---|
| 2 | `scheduledAccelFfMilli` | uint16 | gain x1000 |
| 4 | `scheduledDecelFfMilli` | uint16 | gain x1000 |
| 6 | `steerSaturationDurationMs` | uint16 | 現在の連続飽和時間、65535でclamp |

page 2:

| offset | フィールド | 型 | 単位 |
|---:|---|---|---|
| 2 | `steerCurrentUnsaturated` | int16 | current raw、共通scale前 |
| 4 | `steerCurrentApplied` | int16 | current raw、共通scale後 |
| 6 | `steerSaturationResidual` | int16 | applied - unsaturated |

page 3:

| offset | フィールド | 型 | 単位 |
|---:|---|---|---|
| 2 | `scheduledSteerKawMilli` | uint16 | back-calculation gain x1000 |
| 4 | `steerBackcalcCorrectionMilli` | int16 | 当該1kHz周期の積分補正current raw x1000 |
| 6 | `driveBackcalcCorrectionMilli` | int16 | 当該1kHz周期の積分補正current raw x1000 |

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
