# Differential Swerve Drive ドキュメント構成

このドキュメント群は、差動ステアユニットを「機構モジュール」「制御モジュール」「電源・安全」「基板」「ソフトウェア」のレイヤーに分けて管理する。

## 読む順番

| 順番 | ファイル | 内容 |
|---:|---|---|
| 1 | `SYSTEM_ARCHITECTURE.md` | 全体構成、大筋、責務分担 |
| 2 | `ARCHITECTURE_DECISIONS.md` | 現時点の確定事項と未解決論点 |
| 3 | `modules/DIFFERENTIAL_STEER_MODULE.md` | 1ユニットの機構・モーター・エンコーダ構成 |
| 4 | `control/KINEMATICS_AND_RPM.md` | ギア比、rpm、トルク、順/逆運動学 |
| 5 | `control/DYNAMIC_CONTROL_PLAN.md` | 静的配分から動的配分へ進める制御計画 |
| 5.5 | `control/CALIBRATION_AND_ADAPTATION_PLAN.md` | 将来計画: CALフェーズの機構自己同定(接地対応)とLESO/LADRC負荷適応 |
| 5.7 | `control/CENTRAL_COORDINATED_CONTROL.md` | 車体協調制御: 中央ツイストプロファイラ、車体IK+FF、デサチュレーション、反転ポリシー、段階導入 |
| 5.75 | `../central_firmware/README.md` | Teensy中央制御の実装入口: ハード非依存3輪IK・共通デサチュレーション・全輪settled集約 |
| 5.8 | `control/LOAD_ADAPTIVE_CONTROL_ROADMAP.md` | 負荷適応制御: mode PIを土台にFF、摩擦補償、mode-space DOB、状態推定、必要時MPCへ進めるロードマップ |
| 5.85 | `control/HIGH_SPEED_STEER_GAIN_SCHEDULING_PLAN.md` | 100rpm超のステア追従: 速度帯連続gain schedule、anti-windup、モデルFF、電流引上げ条件 |
| 5.86 | `control/HIGH_SPEED_STEER_HANDOFF_2026-07-31.md` | P0 telemetry/P1 back-calculation実装、実機Kaw予備A/B、現在値と次作業の引継ぎ |
| 6 | `communication/COMMUNICATION_NAMING_AND_IDS.md` | 中央-ユニット通信、ネット名、ID、メッセージ |
| 7 | `electrical/POWER_DISTRIBUTION_AND_ESTOP.md` | 6S LiPo x2、分電、降圧、非常停止 |
| 8 | `electrical/CARRIER_BOARD_REQUIREMENTS.md` | ユニット基板(STM32G474自作基板)の設計要件 |
| 9 | `electrical/CENTRAL_BOARD_REQUIREMENTS.md` | 中央制御ボード(Teensy 4.1)の設計要件 |
| 9.5 | `electrical/ODOMETRY_BOARD_REQUIREMENTS.md` | オドメトリ基板(AMT102 A/B相 x3、STM32F405RGT6)の設計要件。ピン割当は`electrical/STM32F405_ODOMETRY_PIN_ASSIGNMENT.md` |
| 9.55 | `electrical/ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md` | F405オドメトリ基板をA3横1枚へ転記するための配置、RefDes、接続表、ERCチェック |
| 9.56 | `electrical/ODOMETRY_BOARD_SCHEMATIC_WITH_BOM.html` / `.pdf` | unit board資料と同形式のブロック別簡易回路図＋部品名・値・KiCad Footprint・接続先BOM |
| 9.7 | `electrical/SCHEMATIC_DESIGN_OPEN_ITEMS.md` | 3基板の回路設計前に解消する未確定事項、優先度、ブロック作成順、PCB配置配線の役割分担 |
| 9.8 | `electrical/CAN_COMMON_BLOCK_PART_SELECTION.md` | 全基板共通CANブロックの正式部品、比較、回路・配置配線制約、実機確認 |
| 9.9 | `electrical/POWER_5V_COMMON_BLOCK_PART_SELECTION.md` | 5V枝保護、G474入力逆接保護、3.3V LDO、GH2、枝LEDの正式部品と熱・配置条件 |
| 9.95 | `electrical/STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md` | G474の8MHz HSE、負荷容量、VDDA/VREF+、デカップリング正式部品と配置条件 |
| 9.97 | `electrical/UNIT_BOARD_SCHEMATIC_REFERENCE.md` | ユニット基板回路図のKiCad転記用リファレンス(階層シート案、接続表、RefDes割当、ERC非検出注意点、未確定事項) |
| 10 | `electrical/CARRIER_BOARD_BUILD_PLAN.md` | 基板製作の進め方、検証順序 |
| 11 | `testing/NUCLEO_BENCH_TEST_PLAN.md` | CAN-G474主試験機、CAN-L431対向ノード、NUCLEO予備での通信・差動制御実証手順 |
| 11.2 | `testing/SINGLE_MODULE_LOAD_EVALUATION_PLAN.md` | 単一モジュールの負荷ロバスト性評価: 4隅従動輪治具方針、動作包絡線(理論値・10%マージン)、計測項目、実施順序 |
| 11.3 | `testing/ODOMETRY_IMU_EVALUATION_PLAN.md` | オドメトリ+IMUモジュール評価: 直線スライダー/回頭ピボット試験、センサフュージョン重み付け方針、更新周波数の考え方 |
| 11.4 | `testing/UNIT_AUTO_TUNER.md` | 単一ユニットの粗→細実機パラメータ探索、応答倍率、CSV/SVG出力、空走→接地の再探索手順 |
| 11.5 | `../firmware/docs/MATEK_CAN_G474_PORT.md` | CAN-G474へのファーム移植、ST-LINK書込み、ArduPilot参照範囲 |
| 12 | `software/MINIPC_GUI_AND_TEENSY.md` | mini PC GUI、Teensy、ユニットMCUの役割 |
| 12.2 | `software/ESP32_DUALSENSE_CAN_GATEWAY.md` | DualSense→mini PC UDP→ESP32-C3 TWAI→Teensy CAN2の配線、プロトコル、起動・試験 |
| 12.5 | `software/HOKUYO_LIDAR_SETUP.md` | mini PC上のHokuyo USB LiDARのROS 2/RViz設定と復旧手順 |
| 13 | `checklists/REVIEW_CHECKLIST.md` | 回路・制御・実装レビュー用チェックリスト |

## レイヤー構造

```text
機体全体
  |
  |-- mini PC
  |     |-- GUI
  |     |-- ログ
  |     |-- キャリブレーション操作
  |
  |-- 中央制御基板 / Teensy
  |     |-- リアルタイム制御
  |     |-- 安全I/O
  |     |-- E-stop監視
  |     |-- 各ユニットへの目標値配信
  |
  |-- 電源・安全系
  |     |-- 6S LiPo x2
  |     |-- 24V分配
  |     |-- 12V mini PC
  |     |-- 5V制御系
  |     |-- メインリレー / DCコンタクタ
  |
  |-- 差動ステアユニット x3
        |-- ユニット基板(STM32G474自作)
        |-- M3508 x2
        |-- C620 x2
        |-- AMT22 x1
        |-- 差動ステア機構
```

## 既存ファイルとの関係

過去に作成した以下のファイルは、詳細メモとして残す。

| 既存ファイル | 新体系での主な移行先 |
|---|---|
| `STEER_DRIVE_RPM_FUNCTIONS.md` | `control/KINEMATICS_AND_RPM.md` |
| `DYNAMIC_CONTROL_PLAN.md` | `control/DYNAMIC_CONTROL_PLAN.md` |
| `DIFFERENTIAL_STEER_CARRIER_BOARD_REQUIREMENTS.md` | `electrical/*`, `software/*`, `checklists/*` |

今後は新しい階層構造側を正本として更新する。
