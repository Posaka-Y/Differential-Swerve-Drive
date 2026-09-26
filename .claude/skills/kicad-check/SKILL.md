---
name: kicad-check
description: KiCadで編集中の基板のERC/DRCチェック、警告修正、部品選定の議論を行う。KiCadを別ウィンドウで開いたまま、保存の都度このスキルで確認する運用。「ERCチェックして」「DRCチェックして」「基板レビューして」「見て(KiCad保存後)」「この部品どう思う」「〇〇ボードの警告直して」で起動。
---

# KiCad ERC/DRC チェック・部品選定サポート

KiCad GUIとこのターミナルを並べて開いておき、ユーザーがKiCad上で編集・保存した後に
声をかけられたら、ここに書いた手順でチェック・修正・議論を行う。有料プラグイン(ALT TAB
Circuit Copilot等)は使わない。`kicad-cli`(KiCad 10、`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`)
とテキストである`.kicad_sch`/`.kicad_pcb`を直接扱うだけで同等以上のことができる。

## 対象プロジェクト

| 基板 | `-Project`パス(拡張子なし) | 備考 |
|---|---|---|
| ユニット基板 | `hardware/unit-board/unit-board` | ERC/DRC 0件達成済み・出荷用Gerber確定済み。変更時は再度0件を維持する |
| オドメトリ基板 | `hardware/odometry-board/Oddom board/Oddom board` | ERC/DRC 0件達成済み(2026-07-26)。パスに空白を含むので`"`で囲む |
| 中央基板 Rev.1 (現行) | `hardware/central-board/central-board/central-board` | 作業中。最新状況は`PROGRESS.md`末尾を確認 |
| 中央基板 参考(旧) | `hardware/central-board/reference-2026-09-12/central-board` | `docs/electrical/CENTRAL_BOARD_REV1_CONSTITUTION.md`により**発注対象外**。`.kicad_pcb`なし(ERCのみ) |

## 実行コマンド

```powershell
.\tools\kicad\check.ps1 -Project "hardware/unit-board/unit-board"
.\tools\kicad\check.ps1 -Project "hardware/odometry-board/Oddom board/Oddom board"
.\tools\kicad\check.ps1 -Project "hardware/central-board/central-board/central-board"
```

- 出力は`$env:TEMP\differential-swerve-kicad-check\`配下の`-erc.rpt`/`-drc.rpt`/`-schematic.pdf`。
- `.kicad_pcb`が無いプロジェクト(reference系)は`-SkipDrc`を付けるかERCのみ確認する。
- 基板ではなく`hardware/blocks/g474_minimum.kicad_sch`のような単体シートは
  `kicad-cli sch erc --output <path> <sch>`を直接叩く。

## 修正の進め方(前例: odometry-board 2026-07-26)

1. `check.ps1`でERCレポートを取得し、違反を種類ごとに整理する(未接続ピン、重複ラベル等)。
2. `.kicad_sch`はテキスト(s-expression)なので直接Editで編集できる。KiCad GUIが同じファイルを
   開いたままだと外部変更の再読み込みが必要になる場合があるので、GUIで大きく編集中の対象は
   触らない・触る前にユーザーに確認する。
3. 1回の編集ごとに再度`check.ps1`を回し、違反件数が減っているか確認する(段階的に収束させる)。
4. 0件になったら`git diff`で差分を見せ、`docs/ARCHITECTURE_DECISIONS.md`か該当の
   `docs/electrical/*_SCHEMATIC_REFERENCE.md`に反映が必要か確認する。
5. 大きな変更(部品変更・ネット構成変更)は必ず`PROGRESS.md`に追記する(`AGENTS.md`のルール)。

## 部品選定を議論するときのルール

- **推測で決めない。** `AGENTS.md`の確定ルール通り、部品を変更・提案するときは必ずデータシートを
  確認してから答える。
- 対象基板の要件書(`docs/electrical/*_REQUIREMENTS.md`)と部品選定書
  (`docs/electrical/*_PART_SELECTION.md`、例: `CAN_COMMON_BLOCK_PART_SELECTION.md`、
  `POWER_5V_COMMON_BLOCK_PART_SELECTION.md`、`STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md`)
  を先に読み、既存の確定事項と矛盾しないか確認する。
- 発注用BOM/価格を伴う話は`tools/kicad/digikey-bom.ps1`と`tools/procurement/build-digikey-bom-workbook.mjs`
  が扱っている形式(Refs/Value/Footprint/Manufacturer/Mpn/DigiKey/Category/Owned/Note)に合わせる。
- 決定事項は`docs/ARCHITECTURE_DECISIONS.md`の確定事項テーブルへ日付付きで追記する
  (`AGENTS.md`参照)。

## 「見て」と言われたときの最低限の動作

1. `git status` / `git diff -- hardware/` でKiCad GUI側の未コミット変更を把握する。
2. 変更のあったプロジェクトに対して上記`check.ps1`を実行する。
3. 前回チェック時と比べて違反が増減していないか、新規の警告種別が出ていないかを報告する。
4. 深刻な違反(未接続ピン、電源競合等)があれば修正案を提示し、ユーザーの了承を得てから編集する。
