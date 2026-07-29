# Differential Swerve Drive

差動ステアユニット3基で構成する移動機構の、機構・制御・基板・ファームウェアをまとめた開発リポジトリです。

各ユニットはM3508+C620を2組とAMT222A-Vを持ち、ユニット内で差動の操舵・駆動制御を完結します。中央Teensy 4.1が3ユニットを協調制御し、mini PCはUSB-CDC経由でGUI・ログ・キャリブレーション操作を担います。

## 現在の構成

```text
mini PC (GUI / log)
  | USB-CDC
Teensy 4.1 (中央制御・安全I/O)
  |-- CAN1: 差動ステアユニット x3
  |     `-- STM32G474RET6 + C620 x2 + M3508 x2 + AMT222A-V
  |
  `-- CAN3: オドメトリ/IMUノード (unitId=4)
        `-- STM32F405RGT6 + AMT102 x3 + ICM-42688-P
```

- 中央CANとユニット内C620 CANは、いずれもClassic CAN 1 Mbpsの別バス。
- 制御系は中央の24V→5V降圧から`COMM_A / COMM_B / +5V / GND`で分配し、各基板で3.3Vを生成する。
- 確定事項の唯一の正本は[docs/ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md)。

## まず読むもの

| 目的 | 文書 |
|---|---|
| 文書全体の案内 | [docs/PROJECT_DOCUMENT_INDEX.md](docs/PROJECT_DOCUMENT_INDEX.md) |
| 現在地・次の作業 | [PROGRESS.md](PROGRESS.md) |
| 設計上の確定事項 | [docs/ARCHITECTURE_DECISIONS.md](docs/ARCHITECTURE_DECISIONS.md) |
| 全体構成と責務 | [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) |
| ユニット基板・中央基板・オドメトリ基板 | [docs/electrical/](docs/electrical/) |
| 制御・運動学 | [docs/control/](docs/control/) |
| CAN・ネット名・メッセージ | [docs/communication/COMMUNICATION_NAMING_AND_IDS.md](docs/communication/COMMUNICATION_NAMING_AND_IDS.md) |
| ファームウェア | [firmware/README.md](firmware/README.md) と [firmware/PROGRESS.md](firmware/PROGRESS.md) |
| KiCad基板設計 | [hardware/README.md](hardware/README.md) |

階層化済みの`docs/control/`、`docs/electrical/`、`docs/communication/`などが更新対象です。`docs/`直下の旧メモは履歴として保存しており、更新対象ではありません。

## よく使うコマンド

リポジトリルートで実行します。

```powershell
# STM32G474 ファームウェア
.\firmware\scripts\build.ps1
.\firmware\scripts\flash.ps1

# KiCad設計のERC・PDF・DRC確認
.\tools\kicad\check.ps1
```

ファームウェア用ツールチェーンはスクリプトが自動検出します。パスに日本語を含むため、ビルド系スクリプトでは絶対パスを`cmd.exe`経由で渡さず、相対パスを使います。

## リポジトリ構成

```text
docs/       設計仕様、設計判断、試験計画
firmware/   STM32G474向けファームウェアとベンチ検証記録
hardware/   KiCadプロジェクト、共通ライブラリ、参照回路
tools/      KiCad検証などの補助スクリプト
```
