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
| 5.87 | `control/RESPONSE_IMPROVEMENT_PLAN_2026-09-12.md` | 組付け後の高応答化: 現行UARTと高速CANベンチの差、周期計測、軌道/FF整合、段階実装チケット |
| 6 | `communication/COMMUNICATION_NAMING_AND_IDS.md` | 中央-ユニット通信、ネット名、ID、メッセージ |
| 7 | `electrical/POWER_DISTRIBUTION_AND_ESTOP.md` | 6S LiPo x2、分電、降圧、非常停止 |
| 8 | `electrical/CARRIER_BOARD_REQUIREMENTS.md` | ユニット基板(STM32G474自作基板)の設計要件 |
| 9 | `electrical/CENTRAL_BOARD_REQUIREMENTS.md` | 中央制御ボード(Teensy 4.1)の設計要件 |
| 9.05 | `electrical/CENTRAL_BOARD_REV1_CONSTITUTION.md` | **中央基板Rev.1の最上位設計方針**。24V+USB共存、5V Logic、CAN、E-stop、24V汎用出力、発注終了条件 |
| 9.06 | `electrical/ACTUATOR_CAN_NODE_REQUIREMENTS.md` | **24VアクチュエータCANノードRev.Aの正本**。コンタクタ、汎用24V出力、保護付き小型DCモーターHブリッジの境界・部品・安全条件 |
| 9.065 | `../output/pdf/ACTUATOR_CAN_NODE_REV_A_BLOCK_DIAGRAM_AND_BOM_2026-09-17.pdf` | **24VアクチュエータCANノードA3人間レビュー図+暫定BOM**。全体電力/制御、4ch low-side MOS、DRV8251A H bridge、breakaway contactor、STOP項目を9ページで可視化（発注用ではない） |
| 9.066 | `../output/pdf/ACTUATOR_CAN_NODE_REV_A_SCHEMATIC_2026-09-17.pdf` | **24VアクチュエータCANノードA3人間レビュー回路図(部品・ピン番号付き、9ページ)**。S01全体/訂正一覧、S02電源、S03 F303K8全ピン(TIM AF付き)、S04 CAN、S05 OUT2-4、S06 DRV8251A、S07 分離式CONTACTOR_DRIVER、S08 KiCad割当/BOM、S09 ERC非検出・未確定(発注用ではない)。生成: `tmp/actuator-node/build_actuator_rev_a_schematic.py` |
| 9.07 | `electrical/LED_CAN_NODE_REQUIREMENTS.md` | **24VアドレサブルLED CANノードRev.Aの正本**。F303K、CAN、12〜24V自己給電、WS2811互換テープのローカル波形生成、電力注入境界 |
| 9.08 | `electrical/LED_CAN_NODE_PART_SELECTION.md` | LED CANノードのデータシート照合済み部品と、推測禁止の未確定部品・選定停止条件 |
| 9.09 | `electrical/LED_CAN_NODE_KICAD_ENTRY_REFERENCE.md` | **LED CANノードKiCad機械転記用正本**。RefDes/ネット名/1ピン1ネット、DNP/STOP、ERC非検出の人手レビュー表 |
| 9.10 | `../output/pdf/LED_CAN_NODE_REV_A_HUMAN_SCHEMATIC_2026-09-14.pdf` | LED CANノードA3ブロック図(旧版)。9.11の回路図PDFに置き換え |
| 9.11 | `../output/pdf/LED_CAN_NODE_REV_A_SCHEMATIC_2026-09-17.pdf` | **LED CANノードA3人間レビュー回路図(部品・ピン番号付き、6ページ)**。S01全体/訂正一覧、S02電源(LMR51606/TLV761)、S03 F303K8 LQFP-32全ピン、S04 CAN+AHCTデータ出力、S05ハーネス/TP/ライブラリ割当、S06 ERC非検出・未確定(発注用ではない)。生成: `tmp/led-node/build_led_rev_a_schematic.py` |
| 9.1 | `electrical/TEENSY41_CENTRAL_PIN_ASSIGNMENT.md` | 中央Teensyの全ピン割当、socket pad対応、起動時安全状態 |
| 9.2 | `electrical/CENTRAL_BOARD_SCHEMATIC_REFERENCE.md` | 中央基板Rev.Aの責務別階層sheet、正式部品、接続、PCB制約、試験条件 |
| 9.25 | `electrical/CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md` | **中央基板Rev.1のKiCad転記用リファレンス**。シート構成・RefDes・ピン番号付き接続表・symbol/footprint・ERC非検出注意・未確定事項を具体化。2026-09-17にコンタクタを別体`CONTACTOR_DRIVER`へ分離し、中央`MOTOR_PWR_EN` 3.3V直結へ訂正 |
| 9.255 | `../hardware/lib/TEENSY41_SOCKET_FOOTPRINT.md` | Teensy 4.1一体48padソケット、列中心間15.24mm、USB側pad1/48、1mm穴と実物適合の確認条件 |
| 9.257 | `../output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-23.pdf` | **中央基板・人手転記用回路図の最新版（A3横13ページ）**。回路拡大、横挿しGH3 CAN仕様、中央コイルdriver搭載案、Teensy列中心間15.24mm訂正、未確定一覧 |
| 9.258 | `electrical/CENTRAL_BOARD_REV1_PDF_CHANGELOG_2026-09-23.md` | 改訂PDFの変更点・出典・未確定事項。旧転記表のCAN/安全境界との差分正本 |
| 9.259 | `../hardware/central-board-placement/README.md` | 中央基板の新規KiCad階層回路図。機能別シンボル配置のみ、配線はユーザーが実施。既存中央プロジェクトとは別 |
| 9.26 | `../output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-14.pdf` | **旧版。9.257へ更新済み。**  9.25の接続表を人が読む回路図にしたA3横8ページ。2026-09-17改訂版は3.3V ON/OFF→別体gate buffer/MOSFET→E228 24V coilの境界を明記。生成は`tmp/pdfs/build_central_board_rev1_schematic.py` |
| 9.3 | `electrical/CENTRAL_BOARD_SCHEMATIC_WITH_BOM.html` / `../output/pdf/CENTRAL_BOARD_SCHEMATIC_WITH_BOM.pdf` | オドメトリ／駆動基板資料と同形式の、中央基板1機能1ページ回路図＋注意点＋簡易BOM |
| 9.44 | `electrical/PCB_BATCH_V2_CENTRAL_PLAN.md` | 次回3基板一括発注方針、横挿しGH3 CAN、中央コイルdriver搭載案、共通部品予備数量方針 |
| 9.45 | `electrical/UNIT_ODOMETRY_V2_REQUIREMENTS.md` | **駆動/ODOM V2改版要件**。共通SWD（VTref付き）、TP、V1修正台帳、段階実装、回収/在庫、発注前接続監査。V2作業プロジェクトあり、製造未完了 |
| 9.5 | `electrical/ODOMETRY_BOARD_REQUIREMENTS.md` | オドメトリ基板(AMT102 A/B相 x3、STM32F405RGT6)の設計要件。ピン割当は`electrical/STM32F405_ODOMETRY_PIN_ASSIGNMENT.md` |
| 9.55 | `electrical/ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md` | F405オドメトリ基板をA3横1枚へ転記するための配置、RefDes、接続表、ERCチェック |
| 9.56 | `electrical/ODOMETRY_BOARD_SCHEMATIC_WITH_BOM.html` / `.pdf` | unit board資料と同形式のブロック別簡易回路図＋部品名・値・KiCad Footprint・接続先BOM |
| 9.7 | `electrical/SCHEMATIC_DESIGN_OPEN_ITEMS.md` | 3基板の回路設計前に解消する未確定事項、優先度、ブロック作成順、PCB配置配線の役割分担 |
| 9.8 | `electrical/CAN_COMMON_BLOCK_PART_SELECTION.md` | 全基板共通CANブロックの正式部品、比較、回路・配置配線制約、実機確認 |
| 9.9 | `electrical/POWER_5V_COMMON_BLOCK_PART_SELECTION.md` | 5V枝保護、G474入力逆接保護、3.3V LDO、GH2、枝LEDの正式部品と熱・配置条件 |
| 9.95 | `electrical/STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md` | G474の8MHz HSE、負荷容量、VDDA/VREF+、デカップリング正式部品と配置条件 |
| 9.97 | `electrical/UNIT_BOARD_SCHEMATIC_REFERENCE.md` | ユニット基板回路図のKiCad転記用リファレンス(階層シート案、接続表、RefDes割当、ERC非検出注意点、未確定事項) |
| 9.98 | `../output/pdf/BOARD_ASSEMBLY_PROCEDURE_2026-09-21.pdf` | **駆動(unit)基板・ODOM基板の実装作業手順書(A4横9ページ)**。着手前チェック3件(ODOM U3/U7/U9の電源未接続、有鉛HASLでの印刷ブリッジ、置換部品)、Sn63Pb37(183℃)リフロープロファイル+LQFP64ドラッグはんだ、チェックリスト式実装手順、ジャンパ施工図、通電bring-up順、配置図2枚。生成: `tmp/assembly/build_assembly_procedure.py` |
| 9.985 | `../output/pdf/BOARD_FLAT_NETLIST_2026-09-21.pdf` | **駆動基板・ODOM基板のフラット結線表(5ページ)**。階層シートを潰し、製造された`.kicad_pcb`のネットリストからMCU全ピン→ネット、ネット→接続ピン、部品一覧、未接続パッド検出を出力。RefDes/ピン番号は実基板シルクと一致。生成: `tmp/assembly/build_flat_netlist.py` |
| 9.986 | `../output/pdf/UNIT_BOARD_SCHEMATIC_KICAD_2026-09-21.pdf` / `../output/pdf/ODOMETRY_BOARD_SCHEMATIC_KICAD_2026-09-21.pdf` | KiCad実回路図のPDF出力(6ページ / 5ページ)。`kicad-cli sch export pdf`。正確だが階層構成のため追いづらい。読みやすさ優先なら9.985 |
| 10 | `electrical/CARRIER_BOARD_BUILD_PLAN.md` | 基板製作の進め方、検証順序 |
| 11 | `testing/NUCLEO_BENCH_TEST_PLAN.md` | CAN-G474主試験機、CAN-L431対向ノード、NUCLEO予備での通信・差動制御実証手順 |
| 11.2 | `testing/SINGLE_MODULE_LOAD_EVALUATION_PLAN.md` | 単一モジュールの負荷ロバスト性評価: 4隅従動輪治具方針、動作包絡線(理論値・10%マージン)、計測項目、実施順序 |
| 11.3 | `testing/ODOMETRY_IMU_EVALUATION_PLAN.md` | オドメトリ+IMUモジュール評価: 直線スライダー/回頭ピボット試験、センサフュージョン重み付け方針、更新周波数の考え方 |
| 11.4 | `testing/UNIT_AUTO_TUNER.md` | 単一ユニットの粗→細実機パラメータ探索、応答倍率、CSV/SVG出力、空走→接地の再探索手順 |
| 11.5 | `../firmware/docs/MATEK_CAN_G474_PORT.md` | CAN-G474へのファーム移植、ST-LINK書込み、ArduPilot参照範囲 |
| 11.6 | `testing/RC_DRIVE_TEST_2026-08-07.md` | ラジコン操作による走行成立の記録、未評価項目、次回の安全・負荷試験順序 |
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
