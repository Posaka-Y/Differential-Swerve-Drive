# UTM-30LX LiDAR Bench Test

目的: Hokuyo UTM-30LX が PC から認識され、測距データを取得できることを確認する。

## 準備物

* UTM-30LX 本体
* UTM-30LX 用電源
* USB ケーブル
* Windows PC
* UrgBenriPlus

## 使用ファイル

* `UTM-30LX/UrgBenriPlus_2.3.2(rev.343)_1721794791/UrgBenriPlus_2.3.2(rev.343)_installer.exe`
* `UTM-30LX/URG_USB_DRIVER_Win_1432173221/URG_USB_Driver/URG_USB_Driver.inf`
* `UTM-30LX/Manual_MRS0039A_utm-30lx.pdf`
* `UTM-30LX/URG_SCIP20_1607911140.pdf`

## 手順

1. UTM-30LX に電源を入れる。
2. UTM-30LX と PC を USB 接続する。
3. Windows のデバイスマネージャーを開く。
4. `ポート (COM と LPT)` または不明なデバイスとして UTM-30LX が見えるか確認する。
5. ドライバ未適用の場合は、`URG_USB_Driver.inf` を使ってドライバを適用する。
6. `UrgBenriPlus_2.3.2(rev.343)_installer.exe` を実行して UrgBenriPlus をインストールする。
7. UrgBenriPlus を起動する。
8. 接続先に UTM-30LX の COM ポートを指定する。
9. 通信方式は SCIP 2.0 として接続する。
10. スキャン表示を開始し、障害物を置いて距離プロットが変化することを確認する。

## 合格条件

* Windows 上で UTM-30LX の COM ポートが確認できる。
* UrgBenriPlus から接続できる。
* スキャン画面で距離データが連続更新される。
* センサ前方に物体を置くと、表示される測距点が変化する。

## 記録項目

* テスト日:
* PC:
* OS:
* COM ポート:
* 電源電圧:
* UrgBenriPlus バージョン:
* 接続結果:
* スキャン表示結果:
* 気づいた問題:

## トラブルシュート

### COM ポートが出ない

* UTM-30LX の電源を確認する。
* USB ケーブルを交換する。
* デバイスマネージャーで不明なデバイスがないか確認する。
* `URG_USB_Driver.inf` を手動指定してドライバを適用する。

### UrgBenriPlus で接続できない

* COM ポート番号が合っているか確認する。
* 他のソフトが同じ COM ポートを開いていないか確認する。
* 一度 USB を抜き差しし、UrgBenriPlus を再起動する。

### 距離データが出ない

* センサ前面の保護フィルムや遮蔽物を確認する。
* 近すぎる物体だけで確認していないか確認する。
* 室内の壁や箱など、安定した対象物で確認する。

## 次の段階

単体測距が確認できたら、次は PC 側で SCIP 2.0 の生データ取得、または ROS/独自ノードへの取り込みを確認する。
