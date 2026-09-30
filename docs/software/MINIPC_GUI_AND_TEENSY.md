# mini PC GUI と Teensy 制御

## 役割分担

| 要素 | 役割 |
|---|---|
| mini PC | GUI、ログ、設定編集、キャリブレーション操作、デバッグ表示 |
| ESP32-C3 | mini PCのDualSense twistをWi-Fi/UDPで受け、Teensy CAN2へ中継 |
| Teensy | リアルタイム制御、安全I/O、E-stop監視、各ユニットへの指令 |
| ユニットMCU | AMT22読み取り、C620制御、ステア/速度ループ |

mini PCはGUIホスト。Teensyは制御と安全判定。ユニットMCUは現地ループ。手動操作だけは
`mini PC -> Wi-Fi/UDP -> ESP32-C3 -> Classic CAN2 -> Teensy`を使う。ESP32は3輪の目標値を
直接生成せず、車体twist要求の中継に限定する。詳細は`ESP32_DUALSENSE_CAN_GATEWAY.md`。

## GUI画面

| 画面 | 内容 |
|---|---|
| Status | 電源電圧、CAN状態、各ユニット状態、E-stop状態 |
| Calibration | ステア原点合わせ、AMT22ゼロ点保存、ユニットID確認 |
| Start | 起動許可、モータ有効化要求 |
| Debug | 角度、速度、rpm、エラーコード表示 |
| Config | ID、CAN設定、制御パラメータ確認 |

## 起動シーケンス

```text
電源ON
  |
  |-- mini PC起動
  |-- Teensy起動
  |-- mini PC - Teensy通信確認
  |-- 各ユニットCAN探索
  |-- ユニットID確認
  |-- AMT22通信確認
  |-- C620通信確認
  |-- E-stop状態確認
  |
  |-- 未キャリブレーションなら Calibration
  |-- 問題なければ Standby
  |-- GUIのStart要求
  |-- Teensyが安全条件を確認
  |-- Motor Enable
```

## キャリブレーション

GUIから行うこと:

- 各ユニットの現在角度を表示する。
- ステアを機械基準向きに合わせる。
- AMT22現在値をゼロ点として保存する。
- 保存値は各ユニットMCUに記録する。
- mini PC側にもデバッグ用バックアップとして同じ値をログ/設定ファイルに保存する。
- キャリブレーション済みフラグを管理する。

各ユニットに保存する理由:

- ゼロ点は機械ユニット固有の値だから。
- ユニットを挿す位置を変えても、そのユニットのキャリブレーションを保持できるから。

保存方式(2026-07-02確定):

- AMT22内蔵のSet Zero Pointコマンドは使わず、**MCU Flashに保存するソフトウェアオフセット**とする。
- 理由: エンコーダのチャックと軸のずれが起こりうるため、定期的な再ゼロ点調整を運用に組み込む。AMT22内蔵ゼロ点は書込ごとにエンコーダNVMを消費し、静止+内部リセットが必要なため、繰り返し調整には向かない。
- STM32G4はEEPROMを持たないため、Flash最終ページ等を使ったエミュレーション(CRC付きレコード追記式)で実装する。書換回数はページ消去単位で1万回オーダーあり、定期調整用途には十分。
- 再ゼロ点調整はGUIのCalibration画面から `CALIB_SAVE_ZERO`(UNIT_CTRLサブコマンド)で実行できるようにし、機体分解を不要にする。

実装済み操作(2026-07-31、単ユニットWeb UI):

- 「現在位置を0°として保存」は確認ダイアログ後に`CALIB_SAVE_ZERO`を送り、ユニット側の
  disabled・AMT/C620 fresh・両モーター1rpm以下の安全条件を通った場合だけFlashへ追記する。
- 保存後はGUIのinactive targetも0°/0rpmへ再シードし、保存前角度への不意な復帰指令を防ぐ。
- `PING`による状態読出しで、保存count、現在raw count、sequence、CRC、ページ残量状態を表示する。
- 「保存原点をクリア」は別の確認ダイアログを要求し、明示操作時だけFlashページを消去する。
- GUI APIは`POST /api/calibration/save-zero`、`/api/calibration/read`、
  `/api/calibration/clear`。いずれもEnable中は拒否する。

デバッグしやすくするため、mini PC GUIには各ユニットから読み戻したゼロ点を表示し、設定ファイルにもコピーを残す。

## デバッグ表示

表示項目:

- 各ユニットのCAN通信状態
- 現在ステア角
- 目標ステア角
- 駆動rpm
- モーター指令rpm
- C620フィードバック
- AMT22読取エラー
- E-stop入力
- リレー/コンタクタ状態
- バッテリ電圧
- 5V制御電圧
- 12V mini PC電圧

## 安全制約

- GUIのStartだけで即モーター駆動しない。
- Motor Enableの最終判定はTeensyが行う。
- E-stop中はGUI操作を無視する。
- mini PC通信断時はTeensyが安全停止へ移行する。
- Debug画面から直接モーターを動かす場合は、低速・短時間・確認操作付きにする。

## mini PC通信

mini PCとTeensy間は、初期はUSBシリアルが簡単。

候補:

| 方式 | 特徴 |
|---|---|
| USBシリアル | 実装が簡単。初期検証向き |
| Ethernet/UDP | 拡張性あり。mini PCらしい構成 |
| CAN直結 | 構成は単純だがGUIデータには窮屈 |

GUI・設定・ログはUSBシリアルを維持する。DualSense手動指令は2026-08-01にESP32-C3経由の
Wi-Fi/UDP + CAN2へ変更した。両経路をTeensy側で別ソースとして扱い、手動指令のwatchdog途絶を
GUI USBの切断判定と混同しない。

## DualSense手動操作(2026-08-01)

Sony DualSenseはESP32等を経由せず、mini PCへBluetoothまたはUSBで直接接続する。
LinuxではSony VID/PID `054c:0ce6`のメインgamepad evdevを自動検出し、接続方式が変わっても
同じ入力マッピングを使う。Bluetooth個体のevdev `uniq`は`4c:b9:9b:8a:c3:07`。

初期マッピング:

| 操作 | 車体要求 |
|---|---|
| 左stick 上下 | `vx`。上が車体`+X`前進 |
| 左stick 左右 | `vy`。左が車体`+Y`左移動 |
| 右stick 左右 | `omega`。左が反時計回り正 |
| R1 | デッドマン。押している間だけ非zero twist要求を生成 |
| R2 | 速度倍率。初期25%から最大100% |
| Options | 将来のarm要求用。入力previewではMotor Enableしない |
| PS | 状態入力として取得。E-stopには使用しない |

mini PC入力層とモータ非接続preview GUI:

```bash
sudo apt install python3-evdev
python3 tools/linux/dualsense_control.py --check
python3 tools/linux/test_dualsense_control.py -v
python3 tools/linux/dualsense_web_ui.py --host 0.0.0.0 --port 8766
```

ブラウザで`http://localhost:8766`を開く。GUIは接続方式、stick/trigger、R1 gate、生成した
`vx/vy/omega`を50ms間隔で表示するが、CAN・USBシリアル・モータ出力は持たない。
R1解放またはevdev切断で3軸要求は同じsnapshotから0になる。今後USB-CDC出力を追加しても、
Teensy側に独立した受信timeout、再接続後の再arm要求、E-stop優先を実装する。

## GUI・物理ボタン共通再アーム（2026-09-26確定）

本体ディスプレーのARMボタンと基板のSW211を、Teensyの同じ判定へ接続する。GUIからMOTOR_PWR_ENを直接指定しない。GUIは要求を出し、Teensyの受理応答と状態を表示する。ARMはコイル励磁の許可、RUNは別の運転開始要求とする。解除だけで復帰せず、ARM成功だけでも車輪指令はゼロのまま。

### 接続仕様

- 本体GUI→mini PC→USB-CDC→Teensy。ESP32手動twist中継からARM要求を暗黙生成しない。
- Teensyは起動ごと・GUI再接続ごとに異なる非ゼロboot_sessionを発行し、stop_generationと一緒に状態配信する。GUI再接続は一旦DISARMし判定コアを新sessionで初期化する。
- ARM要求はboot_session/stop_generation/gui_sequenceを含む。sequenceはsession内単調増加。要求は受信した制御周期だけのイベントとし、保留・自動再送・再接続後再利用をしない。
- 停止・E-stop・リンク期限切れ・異常で即DISARM。stop_generationを更新し、それ以前の要求を無効化する。GUI表示は通信freshなTeensy状態を正とし、通信断時は状態不明と表示する。
- SW211はデバウンス済み入力を渡す。安全条件成立中に解放を観測した後の押下だけを受理する。押しっぱなしや安全条件成立前の押下で自動復帰させない。
- 共通ARM条件はNCループ成立、GUI/駆動3基/ODOMのfresh通信、他異常なし、動作指令ゼロ。ファームは判定結果と拒否状態をGUIへ返す。
- ARM後は新しいRUNと動作指令を要求し、モーションsequenceも単調増加で旧指令を除去する。同一周期ARM+RUNを許可しない。RUNアダプタはC620の立上がり確認・キャリブレーション・通常運転の安全条件も確認する。
- OFF中のC620無応答をARM拒否条件にしない。C620はコンタクタON後の確認項目であり、主接点の溶着検出には使用しない。
- GPIO出力は周期ごとのmotor_power_enableを反映し、motion_permitted=falseなら全運転出力ゼロ。リンク異常判定は制御指令の期限切れも含める。

### 実装状況

central_firmwareにハード非依存ArmControllerを追加。起動OFF、共通ARM判定、停止世代token、GUI重複拒否、ボタン押下、ARM/RUN分離を実装した。Teensy実機GPIO・USBプロトコルの符号化/受信処理、本体GUIの画面、タイムアウト/デバウンス/C620立上がりアダプタは未実装。既存単ユニットWeb UIへ中央ARMを追加してはいない。実機投入・テストは未実施。
