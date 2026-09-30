# Teensy central-control firmware

`central_firmware`はTeensy 4.1中央制御のハードウェア非依存コアから実装を始める。
現段階ではCAN/USB/安全I/Oドライバを含まず、`control/swerve_coordinator`と
`control/steer_trajectory`が次を担当する。

- 車体twistとtwist微分から3ユニットのsteer角、wheel rpm、FFを同一時刻断面で算出
- 低速時だけの中央flip判断と連続unwrap角
- 停止特異点で直前steer角を保持
- 3ユニットの最悪要求に合わせたplanned motor-rpm包絡の共通scale
- 新指令後のSTATUS3 Low→Highを要求する3輪`MOTION_SETTLED`集約
- rate/accel/decel/jerk制約とjerk過渡込み停止距離を持つunwrapped steer軌道

駆動ユニットは半径0.250mの円上へ120deg等配する。車体`+X前・+Y左`でunit 1/3間の辺を
`+Y`側(センサーモジュール搭載側)に置き、unit 1=`(-216.5,+125)mm`、
unit 2=`(0,-250)mm`、unit 3=`(+216.5,+125)mm`とする。
公称車輪径は65mmなので、`default_coordinator_config()`は半径0.0325mと上記座標を設定する。
接地変形や製造差を実走距離から校正した場合は、各`wheel_radius_m`を実効半径で上書きできる。
半径が0以下のユニットを含む設定は指令生成を拒否し、全出力を0に保つ。

ホスト試験:

```bash
central_firmware/scripts/test-host.sh
```

次段階は、正本の機体寸法を設定したうえでTeensy 4.1のFlexCAN_T4アダプタ、200Hz
twist/steer profiler、通常STOP/ESTOP状態機械をこのコアの外側へ接続する。空走P4では
jerk=100k/200kを評価したが応答優先ではjerk=0が最速だったため、production configの
non-zero jerk採用値は接地3輪試験後に確定する。

## 再アーム判定コア（2026-09-26）

control/arm_controllerを追加。GUI ARMイベントとSW211押下を同じ安全判定へ入力し、ARMによるコイル許可とRUNによる運転許可を分離する。詳細はdocs/software/MINIPC_GUI_AND_TEENSY.md。

アダプタは毎周期ArmInputsを構築する。初期値は安全側（未許可）。GPIOにmotor_power_enableを反映し、motion_permitted=falseでは車輪出力をゼロにする。boot_sessionは起動/GUI再接続ごとに新しい値を供給し、再接続時はコントローラを再初期化する。USB受信イベントをキューへ保持せず、期限切れリンク/指令をlinks_ok=falseへ反映する。run_eventはC620立上がりや運転の他条件を確認したイベントだけを渡す。

これは判定コアの実装であり、Teensy GPIO/USB、本体ディスプレーGUIとの接続は未実装。今回ビルド・テスト・書き込みは実施していない。
