# CURRENT_SYSTEM_OVERVIEW.md

# Robotics Platform - Current System Overview

> Last Updated: 2026-06-26

---

# Goal

ロボットごとに電子回路やソフトウェアを作り直すのではなく、
再利用可能なモジュール群を構築する。

最終的には各モジュールを組み合わせるだけで新しいロボットを開発できることを目標とする。

---

# Overall Architecture

```
                Jetson / MiniPC
                       │
        ┌──────────────┴──────────────┐
        │                             │
    Motor Network                Sensor Network
        │                             │
  Drive Unit ×3                Sensor Fusion Node
        │                             │
        │                        LiDAR Node (Future)
        │
   Power Distribution
```

---

# Planned Modules

## 1. Drive Unit Controller (Highest Priority)

### Purpose

差動ステアユニットをローカルで制御する。

中央からは

* target RPM
* target Steering Angle

のみを受け取り、

内部で

* Steering PID
* Drive PID

を実行する。

---

### Hardware

* STM32G4 Series
* C620 ×2
* M3508 ×2
* AMT222 Absolute Encoder
* CAN
* USB-C Debug

---

### Inputs

* target_rpm
* target_steering_angle

---

### Outputs

* current_rpm
* current_steering_angle
* motor_current
* temperature
* status

---

### Internal Control Loop

1000Hz

* Read CAN Feedback
* Read AMT222
* Steering PID
* Drive PID
* Send Current Command

---

# 2. Sensor Fusion Node

### Purpose

自己位置推定用センサーノード

ロボット本体とは独立した汎用センサモジュールとする。

---

### Hardware

* STM32G4 Series
* IMU ×1
* Encoder ×3
* CAN
* USB-C

---

### Outputs

* x

* y

* theta

* vx

* vy

* omega

* raw encoder

* gyro

* accel

* status

---

### Future

LiDARとのセンサフュージョンを前提とする。

---

# 3. Odometry Unit

### Purpose

取り外し可能な自己位置推定ユニット

構成

* Omni Wheel ×3
* Encoder ×3
* Sensor Fusion Board

通信

* CAN
* Power

のみで動作することを目標とする。

---

# 4. LiDAR Node (Future)

未設計

将来的に

* LiDAR
* IMU
* Scan Matching

を担当する独立ノードとする予定。

---

# Common Design Rules

## MCU

STM32G4 Series

**確定(2026-07-02): STM32G474(NUCLEO-G474RE)。** FDCAN 3系統が決め手。

---

## Communication

**確定(2026-07-02): 2バスCAN(中央CAN + C620専用CAN、各クラシックCAN 1Mbps)。** RS485案は廃止。

---

## Debug

USB Type-C

---

## Logic Voltage

3.3V

---

## Input Voltage

TBD

(24V想定)

---

## Coordinate System

```
+X : Forward

+Y : Left

+Theta : Counter Clockwise
```

---

# Software Philosophy

各モジュールは

"入力 → 処理 → 出力"

のみを担当する。

上位から見ればブラックボックスとして扱える設計を目指す。

---

# Future Modules

候補

* Power Distribution Board
* CAN Logger
* IO Expansion Board
* Battery Management Board
* USB Debug Adapter
* Wireless Debug Module

---

# Open Issues

* ~~STM32G431 or STM32G474~~ → STM32G474で確定(2026-07-02)
* ~~CAN FD採用~~ → 当面クラシックCAN 1Mbps(C620が1Mbps固定のため。中央CANのFD化は将来検討)
* 電源構成 → `electrical/POWER_DISTRIBUTION_AND_ESTOP.md` にパーツ選定済み
* IMU選定
* Connector規格
* ~~CAN ID規則~~ → `communication/COMMUNICATION_NAMING_AND_IDS.md` に中央CAN ID案を記載

---

# Development Roadmap

Phase0

* 全体仕様策定

Phase1

* Drive Unit Controller

Phase2

* 3 Unit Integration

Phase3

* Sensor Fusion Node

Phase4

* Odometry Unit

Phase5

* LiDAR Integration

---

# Design Philosophy

設計の目的は

「一台のロボットを完成させること」

ではなく

「再利用可能なロボットプラットフォームを構築すること」

とする。

