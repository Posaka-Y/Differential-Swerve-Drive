# ラジコン操作テレメトリ

ESP32のUSBシリアルへ20Hzで`TEL,...`を出し、指令値とNUCLEOから返る実測値を
同じ時刻で記録する。NUCLEOの1kHz制御ループやデバッグUART出力は変更しない。

## 採取

```bash
python3 esp32_gateway/scripts/capture_radio_telemetry.py \
  --port /dev/ttyUSB0 --duration 90
```

既定では`esp32_gateway/logs/radio-<timestamp>.csv`へ保存し、終了後に解析とグラフ生成を
自動実行する。時間を指定せず手動終了したい場合は`--duration 0`を使い、Ctrl-Cで止める。

## 推奨操作

1. 2秒以上ニュートラルを保持する。
2. 500rpm上限で前進、停止、後退を各2秒以上保持する。
3. スロットル0でステア中央、左端、右端を各2秒以上保持する。
4. 500rpm付近を維持してステアを左右へ操作する。
5. 上限を750/1000/1250/1300rpmへ上げ、各速度で2秒以上保持する。
6. 最後に走行中のR1を離し、停止を記録する。高速から正逆を直接切り替えず、必ず0rpmを経由する。

解析は、全有効区間に加えて目標を0.5秒以上保持した定常区間を分けて集計する。
独立した物理角検証が必要な場合だけ、ステア出力へ目印を付けた動画を併用する。

## PCなしの接地試験

ESP32とNUCLEOを車体側5Vで給電し、PCとのUSBを外した状態でも内蔵Flashへ記録できる。

1. DualSenseの十字キー左を押す。短い振動で録画開始。Create（Share）が認識される
   コントローラではCreateも使用できる。
2. 接地状態で走行試験する。録画中も20Hzで`/radio.csv`へ保存する。
3. 十字キー左をもう一度押す。長い振動で録画停止。
4. 走行後にESP32のUSBをPCへ接続し、次を実行する。

```bash
python3 esp32_gateway/scripts/download_offline_log.py --port /dev/ttyUSB0
```

5. スクリプトがESPへ`D`コマンドを送り、保存ログをUSBへ転送して自動解析する。
   コントローラー側の回収操作は不要。

新しい録画を開始すると前回の`/radio.csv`を上書きする。Bluetooth切断時は記録中ファイルを
flush/closeして、それまでのデータを保持する。
