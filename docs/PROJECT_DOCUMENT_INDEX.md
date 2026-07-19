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
| 5.8 | `control/LOAD_ADAPTIVE_CONTROL_ROADMAP.md` | 負荷適応制御: mode PIを土台にFF、摩擦補償、mode-space DOB、状態推定、必要時MPCへ進めるロードマップ |
| 6 | `communication/COMMUNICATION_NAMING_AND_IDS.md` | 中央-ユニット通信、ネット名、ID、メッセージ |
| 7 | `electrical/POWER_DISTRIBUTION_AND_ESTOP.md` | 6S LiPo x2、分電、降圧、非常停止 |
| 8 | `electrical/CARRIER_BOARD_REQUIREMENTS.md` | ユニット基板(STM32G474自作基板)の設計要件 |
| 9 | `electrical/CENTRAL_BOARD_REQUIREMENTS.md` | 中央制御ボード(Teensy 4.1)の設計要件 |
| 9.5 | `electrical/ODOMETRY_BOARD_REQUIREMENTS.md` | オドメトリ基板(AMT102 A/B相 x3、G474)の設計要件 |
| 9.7 | `electrical/SCHEMATIC_DESIGN_OPEN_ITEMS.md` | 3基板の回路設計前に解消する未確定事項、優先度、ブロック作成順、PCB配置配線の役割分担 |
| 9.8 | `electrical/CAN_COMMON_BLOCK_PART_SELECTION.md` | 全基板共通CANブロックの正式部品、比較、回路・配置配線制約、実機確認 |
| 9.9 | `electrical/POWER_5V_COMMON_BLOCK_PART_SELECTION.md` | 5V枝保護、G474入力逆接保護、3.3V LDO、GH2、枝LEDの正式部品と熱・配置条件 |
| 9.95 | `electrical/STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md` | G474の8MHz HSE、負荷容量、VDDA/VREF+、デカップリング正式部品と配置条件 |
| 10 | `electrical/CARRIER_BOARD_BUILD_PLAN.md` | 基板製作の進め方、検証順序 |
| 11 | `testing/NUCLEO_BENCH_TEST_PLAN.md` | CAN-G474主試験機、CAN-L431対向ノード、NUCLEO予備での通信・差動制御実証手順 |
| 11.5 | `../firmware/docs/MATEK_CAN_G474_PORT.md` | CAN-G474へのファーム移植、ST-LINK書込み、ArduPilot参照範囲 |
| 12 | `software/MINIPC_GUI_AND_TEENSY.md` | mini PC GUI、Teensy、ユニットMCUの役割 |
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
