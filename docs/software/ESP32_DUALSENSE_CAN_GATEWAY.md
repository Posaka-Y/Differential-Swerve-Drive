# ESP32-C3 DualSense Wi-Fi/CANゲートウェイ

## 構成と責務

```text
DualSense -- Bluetooth/USB --> mini PC
  mini PC -- Wi-Fi/UDP 50Hz --> ESP32-C3
  ESP32-C3 -- Classic CAN2 1Mbps --> Teensy 4.1
  Teensy -- CAN FD CAN3 --> G474 unit x3
```

mini PCはLinux evdev入力を車体`vx/vy/omega`へ変換する。ESP32-C3はCRC、sequence、送信元、
150ms watchdog、値域を検査して`MANUAL_TWIST_CMD(0x080)`へ詰め替えるだけとする。3輪IK、
ステア反転、軌道生成、加減速、Enable判定はTeensyの責務であり、ESP32からユニットへ
`SET_TARGET`を直接送らない。

ESP32-C3のTWAIはClassic CAN専用でCAN FD非対応。このため接続先はTeensy CAN2
(汎用拡張、Classic CAN 1Mbps)であり、駆動CAN3へは接続しない。

## 現物と配線

2026-08-01にUSB接続個体を読み出し、ESP32-C3 QFN32 revision 0.4、内蔵Flash 4MB、
USB-Serial/JTAG、MAC `3c:dc:75:31:9b:88`を確認した。

| ESP32-C3 | トランシーバ側 | 備考 |
|---|---|---|
| GPIO4 | `CTX` / `TXD` | ESP32 TWAI TX → トランシーバ入力 |
| GPIO5 | `CRX` / `RXD` | トランシーバ出力 → ESP32 TWAI RX |
| GND | GND | CANノード間の参照GNDも接続 |
| 3V3/5V | モジュール電源 | 実装トランシーバ基板の定格を現物で確認 |
| - | CANH/CANL | Teensy CAN2の`COMM_A/COMM_B`へ接続 |

120Ω終端はバス両端の2か所だけONにする。ESP32-C3のGPIOは3.3Vロジックなので、CRX/RXDへ
5Vを出すトランシーバを直結しない。

`MCP2515`はSPI接続の外付けCANコントローラであり、ESP32のGPIO4/5をCTX/CRXへ直結する
今回の構成とは異なる。現物基板が本当にMCP2515搭載品なら、このTWAIファームは使用せず
CS/SCK/SI/SO/INTを配線した別ドライバが必要。基板上のIC刻印と商品型番をCAN通電前に確認する。

## mini PC → ESP32 UDP

ESP32の既定動作はWPA2アクセスポイント。SSIDは`DSD-ESP32-319B88`、パスワードは
`dsd-control`、ESP32アドレスは`192.168.4.1`、UDP portは4210。認証情報を変更する場合は
`esp32_gateway/include/secrets.example.h`を`secrets.h`へコピーして編集する。`secrets.h`は
git管理しない。mini PCホットスポットへ参加するstation modeも同じファイルで選択できる。

UDP datagramは28byte、network byte order(big-endian)。

| offset | field | type | 内容 |
|---:|---|---|---|
| 0 | magic | char[4] | `DSD1` |
| 4 | version | uint8 | `1` |
| 5 | flags | uint8 | bit0=`CONNECTED`、bit1=`DEADMAN` |
| 6 | reserved | uint16 | 0 |
| 8 | sequence | uint32 | 送信ごとに+1、wrap可 |
| 12 | vx | int32 | mm/s、+X前 |
| 16 | vy | int32 | mm/s、+Y左 |
| 20 | omega | int32 | mrad/s、反時計回り正 |
| 24 | crc32 | uint32 | byte 0..23のIEEE CRC-32 |

ESP32は同一fresh sessionで重複・逆行sequence、CRC不一致、異なる送信元IP、形式不一致を拒否する。
150ms途絶後は新しい送信元/sequenceを再取得できる。境界hard clampは並進±1500mm/s、旋回
±4000mrad/s。

## DualSense割当

| 操作 | 指令 |
|---|---|
| R1保持 | デッドマン。離すと全速度0 |
| 左スティック上下 | 前進/後退`vx` |
| 左スティック左右 | 左右並進`vy` |
| 右スティック左右 | 旋回`omega` |
| R2 | 25%〜100%速度スケール |

DualSense切断、R1解放、送信プロセス終了、Wi-Fi途絶の各段で0指令へ落ちる。これは通常停止要求で、
ハードウェアE-stopではない。

## ビルド・書き込み

PlatformIOを導入した環境でリポジトリルートから実行する。

```bash
pio run -d esp32_gateway
pio run -d esp32_gateway -t upload --upload-port /dev/ttyACM0
pio device monitor -b 115200 -p /dev/ttyACM0
```

mini PCをESP32 APへ接続し、オフライン自己試験後にsenderを起動する。

```bash
python3 tools/linux/dualsense_control.py --check
python3 tools/linux/dualsense_udp_sender.py --check
python3 tools/linux/dualsense_udp_sender.py --host 192.168.4.1 \
  --max-v-mps 0.2 --max-omega-rad-s 0.5
```

初回CAN確認はモータをdisableしたまま行い、別CANノード/CANableでID `0x080`、DLC 8、
20ms周期、R1解放時の全0、Wi-Fi切断150ms後の全0を確認する。CANは送信ノード単体ではACKされず
bus-offになるため、正しい1Mbps受信ノードと両端終端を接続して試験する。
