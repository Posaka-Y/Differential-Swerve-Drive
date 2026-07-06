# Differential Swerve Drive 開発ガイド(Claude / Codex 共通)

差動ステアユニット3基の移動機構。M3508+C620(ユニットあたり2組)、AMT222A-V、STM32G474自作基板、中央Teensy 4.1、mini PC GUIで構成する。

## セッション開始時に必ず読むもの

1. `PROGRESS.md` — プロジェクト全体の現在地と次の作業
2. `docs/ARCHITECTURE_DECISIONS.md` — 確定事項(ここに書いてあることを再議論しない)
3. 作業対象に応じて `docs/PROJECT_DOCUMENT_INDEX.md` から該当ドキュメント
4. ファームを触るなら `firmware/AGENTS.md` と `firmware/PROGRESS.md`

## 主要な確定事項(詳細はARCHITECTURE_DECISIONS.md)

- ユニット基板: STM32G474RET6(LQFP64)直載せ自作基板。NUCLEO-G474REは開発検証用
- 通信: 2バスCAN(中央CAN=FDCAN1、C620専用CAN=FDCAN2、各1Mbps)。RS485案は廃止
- 中央制御: Teensy 4.1(汎用CANマスタボードとして設計)。mini PCとはUSB-CDC
- 給電: 中央24V→5V降圧を4線ハーネス(COMM_A/B+5V+GND)で分配。基板上で3.3V生成
- エンコーダ: AMT222A-V(12bit、5mmボア)をステア軸1:1直結。ゼロ点はMCU Flash保存
- オドメトリ: 3輪構成(I2Cホール磁気エンコーダx3、MT6701第一候補。AMT102案は2026-07-06廃止)、専用G474基板(unitId=4)がx/y/θを中央CANへ配信
- コネクタ: 信号JST XH、電源XTシリーズ
- 推奨ピン割当: `docs/electrical/CARRIER_BOARD_REQUIREMENTS.md` の表が正本

## ルール

- 設計判断が確定したら `docs/ARCHITECTURE_DECISIONS.md` の確定事項テーブルへ日付付きで追記する。
- **セッション終了時(またはキリの良い区切り)に `PROGRESS.md` へ「やったこと・現在の状態・次の作業」を追記する。** ファーム作業は `firmware/PROGRESS.md` 側に書く。
- docsの正本は `docs/electrical/`、`docs/communication/` 等の階層側。ルート直下の `DIFFERENTIAL_STEER_CARRIER_BOARD_REQUIREMENTS.md` 等は旧版メモ(冒頭に注記あり)。
- ネット名・信号名の命名規則は `docs/communication/COMMUNICATION_NAMING_AND_IDS.md` に従う(COMM_A/B抽象名、`_N`はLow active等)。
- 部品を変更する場合はデータシートを確認してから要件書を更新する(推測で書かない)。

## ビルド・書き込み(firmware)

```powershell
.\firmware\scripts\build.ps1          # Debugビルド
.\firmware\scripts\flash.ps1          # ビルド+SWD書き込み
```

ツールチェーンは `firmware/scripts/toolchain.ps1` が自動発見する(Arm GCC 14.2、STM32Cube拡張バンドルのCMake/Ninja/Programmer)。手動PATH設定は不要。

## 作業パスの注意

作業フォルダに日本語(`趣味`)が含まれる。cmd.exe経由で絶対パスを渡すツールは文字化けすることがある(CMakeのPOST_BUILDで実際に発生し、相対パス化で回避済み)。ビルド系の追加スクリプトは相対パスで書くこと。
