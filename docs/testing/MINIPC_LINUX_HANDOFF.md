# mini PC Linux test handoff

このメモは、Linux mini PC 上の別 Codex セッションへ渡すための引き継ぎ。

## 現状

- 対象: Differential Swerve Drive の単体ユニット評価。
- ユニットMCU: NUCLEO-G474RE / STM32G474。
- 中央CAN: FDCAN1(PA11/PA12)、CANable 経由で mini PC から送る。
- C620 CAN: FDCAN2。
- CAN bitrate: classic CAN 1 Mbps。
- unitId: `1`。
- 最新ワークツリーのファームは、起動時 disabled、`SET_TARGET` と `UNIT_CTRL enable` でのみ駆動する。
- `SET_TARGET` timeout は最新ソースでは `1000ms`。ただし実機にまだ古い `200ms` 版が残っている可能性あり。
- 送信周期はまず 20Hz 以上、評価用途では 50Hz 推奨。
- 終了時は必ず `UNIT_CTRL disable` を送る。

## CAN message

### SET_TARGET

- CAN ID: `0x101`
- DLC: 8
- payload: little-endian signed int32 x2

| bytes | field | unit |
|---:|---|---|
| 0..3 | target steer | mdeg |
| 4..7 | target wheel rpm | milli-rpm |

例: `theta=90000mdeg`, `wheel=500000 milli-rpm`

```bash
cansend can0 101#905F010020A10700
```

### UNIT_CTRL

- CAN ID: `0x121`
- enable payload: `01 01`
- disable payload: `01 00`

```bash
cansend can0 121#0101
cansend can0 121#0100
```

## Linux setup

```bash
sudo apt update
sudo apt install -y can-utils git python3 python3-serial
sudo usermod -aG dialout "$USER"
```

`dialout` 反映のため一度ログアウト/ログインする。

CANable が `/dev/ttyACM0` の場合:

```bash
sudo slcand -o -c -s8 /dev/ttyACM0 can0
sudo ip link set can0 up
ip -details link show can0
```

受信監視:

```bash
candump can0
```

## First smoke test

ホイールを必ず浮かせてから実施。

```bash
cansend can0 101#905F010020A10700
cansend can0 121#0101
sleep 3
cansend can0 121#0100
```

ただし `SET_TARGET` は周期送信が前提なので、この単発 smoke は timeout 動作確認用。
実駆動評価は 20Hz 以上で `SET_TARGET` を送り続けるスクリプトで行う。

## Codex prompt for Linux mini PC

Linux mini PC 側の Codex には以下をそのまま渡す。

```text
この repo の docs/testing/MINIPC_LINUX_HANDOFF.md を読んで、CANable(socketcan can0)から
差動ステアユニットへ SET_TARGET を周期送信する Linux 用評価スクリプトを作って。

要件:
- Python 3 で実装。追加依存はできれば避け、必要なら python-can を提案してから使う。
- can0 へ classic CAN 1Mbps 前提で送る。
- ID 0x101 に steer_mdeg(int32 LE) と wheel_rpm_milli(int32 LE) を 20Hz または 50Hz で送る。
- ID 0x121 に 01 01 で enable、終了時は例外や Ctrl-C でも必ず 01 00 disable を送る。
- まず theta 固定、wheel rpm を 0 -> 500rpm -> 0 にする smoke を実装。
- 次に CSV で time_s, steer_mdeg, wheel_rpm_milli を読んで再生できる形にする。
- 実行コマンド例と、安全確認手順も README かスクリプトヘルプに書く。
```

## Safety notes

- enable 前にホイールが浮いていることを確認する。
- `cansend can0 121#0100` をすぐ打てる端末を別に開いておく。
- 古いファームが flash されている場合、target timeout が `200ms` の可能性がある。最初から 50Hz 送信が無難。
- 評価終了後は `candump` とユニットVCPログの `STOP:` 行を保存する。
