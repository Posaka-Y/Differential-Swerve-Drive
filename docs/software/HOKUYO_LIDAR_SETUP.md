# Hokuyo USB LiDAR 設定・表示手順

最終確認日: 2026-07-12

mini PCにUSB接続したHokuyo URGシリーズをROS 2 Humbleで使い、RVizで2D走査を表示するための引き継ぎ情報。

## 確認済み構成

| 項目 | 値 |
|---|---|
| LiDAR | Hokuyo Data Flex for USB URG-Series USB Driver |
| 接続 | USB CDC ACM |
| ROS 2 | Humble |
| ドライバ | `urg_node2_nl` |
| ハードウェアID | `00905840` |
| メッセージ型 | `sensor_msgs/msg/LaserScan` |
| トピック | `/scan` |
| frame_id | `laser` |
| 通信QoS | `Best Effort` |
| 実測角度範囲 | 約 -135 deg から +135 deg |
| 表示範囲設定 | 0.1 m から 2.0 m |

Hokuyoは3D点群ではなく、LiDARの高さにおける2Dの距離走査を出力する。RVizでは `PointCloud2` ではなく `LaserScan` 表示を使う。

## USBデバイス名の扱い

USBを抜き差しすると、Linuxの一時的なデバイス名は `/dev/ttyACM0` と `/dev/ttyACM1` の間で変わる。CANableなど他のUSB-CDC機器もあるため、`/dev/ttyACM0` を固定で指定してはならない。

Hokuyo固有の永続パスを使用する。

```text
/dev/serial/by-id/usb-Hokuyo_Data_Flex_for_USB_URG-Series_USB_Driver-if00
```

現在の接続先は次で確認できる。

```bash
ls -l /dev/serial/by-id/usb-Hokuyo_Data_Flex_for_USB_URG-Series_USB_Driver-if00
```

このリンクが `ttyACM0` または `ttyACM1` のどちらを指していても、ROS設定の変更は不要。

## ROSワークスペース側の設定

ROSワークスペースは `/home/tirobot/Harurobo_2025_WS`。

| ファイル | 役割 |
|---|---|
| `src/urg_node2_nl/config/params_serial.yaml` | Hokuyoの永続USBパス、115200 baud、`laser` frameを指定 |
| `src/urg_node2_nl/launch/usb_view.launch.py` | LiDARノードとRVizを同時に起動 |
| `src/urg_node2_nl/config/usb_scan.rviz` | `/scan` のLaserScan表示、`Best Effort` QoS、固定フレーム `laser` |

既存の `urg_node2.launch.py` はEthernet接続の2台構成 (`192.168.0.10` / `192.168.0.12`) 用であり、USB接続のHokuyoには使用しない。

## 起動

```bash
cd ~/Harurobo_2025_WS
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch urg_node2_nl usb_view.launch.py
```

このlaunchでLiDARノードとRVizが起動する。RVizでは赤い点列が表示され、原点の座標軸はLiDAR本体位置を表す。

## RVizで手動設定する場合

1. Fixed Frameを `laser` にする。
2. `Add` から `LaserScan` を追加する。
3. Topicを `/scan` にする。
4. Reliability Policyを `Best Effort` にする。

HokuyoノードはSensorDataQoSでpublishするため、RVizを `Reliable` のままにするとQoS不一致で何も表示されない。

## 動作確認と切り分け

LiDARデータを直接確認する。

```bash
source /opt/ros/humble/setup.bash
source ~/Harurobo_2025_WS/install/setup.bash
ros2 topic echo /scan --qos-reliability best_effort --once
```

正常時の目安:

- `frame_id: laser`
- `angle_min: -2.356...`、`angle_max: 2.356...`
- `range_min: 0.1`、`range_max: 2.0`
- `ranges` に距離値が並ぶ。反射がない方向は `nan` になる。

`/scan` にデータがない場合は、USBを抜き差ししてから永続パスの存在を確認し、上記のlaunchを再起動する。`/dev/ttyACM*` の番号を手で設定ファイルに書き戻さない。

## 表示の読み方

LiDARの出力はカメラ画像ではない。壁は線状、机の脚や人は点の塊として、LiDARの高さで切った断面が見える。今回の設定では最大2 mまでを表示するため、それより遠い物体は表示されない。
