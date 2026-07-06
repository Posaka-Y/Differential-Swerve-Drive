# NUCLEO-G474RE firmware

STM32G474RET6 向けの GCC/CMake ベアメタルプロジェクトです。NUCLEO-G474RE の B1 USER (PC13、アクティブHigh) を押している間、LD2 (PA5) が点灯します。入力は20 msデバウンスされます。

## 必要なツール

- STM32Cube for Visual Studio Code 拡張
- Arm GNU Toolchain (`arm-none-eabi-gcc`) — `winget install Arm.GnuArmEmbeddedToolchain`
- CMake 3.22 以降
- Ninja
- 書き込み時のみ STM32CubeProgrammer

CMake / Ninja / STM32CubeProgrammer / ST-LINK GDB Server は STM32Cube 拡張が
`%LOCALAPPDATA%\stm32cube\bundles` に導入済みのものを使う。手動で PATH に
追加する必要はない。`scripts/toolchain.ps1` が build/flash 実行時に自動で
発見して PATH へ載せる(優先順: 既存 PATH → 拡張バンドル → Arm GNU Toolchain
既定インストール先)。

VS Code のデバッグ構成 (`.vscode/launch.json`) はバンドル内の
`arm-none-eabi-gdb` / `ST-LINK_gdbserver` / `STM32_Programmer_CLI` を
絶対パスで参照している。拡張がバンドルを更新してバージョンディレクトリが
変わった場合はパスを追従させること。

## CLI

リポジトリのルートから実行します。

```powershell
.\firmware\scripts\build.ps1
.\firmware\scripts\build.ps1 -Configuration Release
.\firmware\scripts\flash.ps1
```

POSIX 環境では `firmware/scripts/build.sh` と `flash.sh` を使えます。生成物は `firmware/build/debug` または `firmware/build/release` に配置されます。

## 構成

- `src/main.c`: アプリケーションのエントリポイント
- `src/platform/`: STM32 固有の startup、clock、GPIO
- `include/app_config.h`: アプリ共通設定
- `linker/`: メモリマップ
- `cmake/`: GCC クロスコンパイル設定
- `scripts/`: 再現可能なビルド・書き込みコマンド

新機能は原則として `src/` と `include/` の対応するモジュールへ追加し、MCU レジスタへの直接アクセスは `platform/` 内に限定します。

自作基板へ移行するときは、最初に `src/platform/gpio.c` のLED・ボタンのポート、ピン番号、入力極性を基板回路に合わせて変更します。

実機書き込みで詰まりやすい点、接続モード、エンコーダの配線・段階テスト、自作基板のSWD要件は [docs/BOARD_BRINGUP.md](docs/BOARD_BRINGUP.md) にまとめています。

現在の完了項目、実機状態、次の作業は [PROGRESS.md](PROGRESS.md) を参照してください。
