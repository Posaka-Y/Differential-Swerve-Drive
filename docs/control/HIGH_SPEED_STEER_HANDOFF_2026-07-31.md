# 高速ステア制御 引継ぎ(2026-07-31)

## P4・300rpm更新(2026-07-31 20:37 JST)

- G474内部rate rampをhard guard化し、runtime上限を4000 axis rpm/sへ拡張。Flash/readback MD5は
  `42e5be8774fc61f3d4ea87c5901cb290`、boot既定600と校正zero=1503/seq1は維持。
- jerk profile 0/100k/200kを120/150rpmで比較。200kは120rpm worst overshootを
  7.12→5.10degへ減らしたがfirst-entryを0.303→0.326sへ遅らせたため、応答優先はjerk=0。
- 空走応答優先gateをfirst-entry<=0.5s、overshoot<=20deg、terminal<=1degへ緩和。
  300rpm cap/profile=1800/12000/9000deg系は6/6合格、worst 0.253s/19.863deg/0.528deg。
- 90degでは三角軌道のため実peakは93〜145rpm。外周P=0の速度stepはC620復旧後300rpmへ到達。
  rise90は正負0.174/0.174s、peakは303/333 axis rpm、速度overshootは1.04/11.06%。
- ただし旧stepは4000rpm/s対称rampで、300→0急制動時に電源保護停止した。改修版は加速と
  制動を分離(制動既定500rpm/s)、制動時間後のzero dwell、0rpm経由反転、zero後Disable、
  単方向pulseを実装した。改修後の正方向1回はpeak 300.9rpm、0.595s制動、実測5rpm未満後
  0.25s待機で完走し、ACTIVE/feedback維持、永続faultなし。4000rpm/s制動は禁止する。
- 負方向300rpmもpeak300.9rpm、overshoot0.87%、feedback drop 0で完走。計測器導入までは
  260rpm超の無計測制動を500rpm/s以下へ強制する。
- ramp制動profile(cap300、12000/3000deg/s2)で4000/4500rawを170deg各4移動A/B。4500rawは
  first-entry平均0.344s、実peak183rpm、overshoot最大16.152degで4/4合格。90deg 4移動も
  worst first-entry0.243s、overshoot15.205degで4/4合格したため、空走応答優先候補とする。
- 現在unit disabled、wheel=0、Web UI port8080起動中、`fdbkOk=1`、AMT正常、角度約315.9deg、
  GUI cap60rpm、RAM current limit4000rawへ復元済み。boot既定は変更していない。

## P3a/P4移行更新(2026-07-31 20:10 JST)

- `SET_TARGET_ACCEL_FF(0x160+id)`で明示profile加速度をClassic CANベンチへ実装。運動sampleを
  含む全sampleで適用を確認し、途絶時は旧rate差分へfallbackする。
- 120rpmはprofile decel=2000deg/s2へ更新。比較4移動で初回±2deg平均0.313s、
  overshoot最大5.625deg。RAM/Webはこのpackageへ復元済み。
- 制動Kp倍率を速度knot化したが、150rpm profileでは高速倍率3〜4の全候補が8deg gateを超えた。
  最良3.5でも10.723deg、4000raw飽和、実peak100.7rpm。電流/Kp増加は停止する。
- 現Flash MD5 `448c6ffa65d452268efcd94da6eb68cb`、unit disabled、wheel=0、zero=1503正常。
- 次はP4 jerk制限+二重ramp除去。4000rawのまま実peak150rpmを成立させる。

## 120rpm級更新(2026-07-31 19:54 JST)

- 実用gateをfirst-entry±2deg<=0.50s、overshoot<=8deg、terminal<=1deg、安全停止なしへ変更。
  strict settleは診断として残す。
- 制動phase限定Kp倍率を追加(`SET_CONFIG idx47`, 1..4, default 1)。倍率2.0を選定。
- unit 1空走候補: max/cap120rpm、100/150 knot=140/50、FF=0.5/2.5、unit accel1000rpm/s、
  Web=720/5400/2250。確認12移動はfirst-entry平均0.301s、実peak119.9rpm、overshoot最大
  7.647deg、terminal最大0.176deg、12/12実用合格、安全停止なし、28degC。
- Flash MD5 `63b59d173a7bdef4bc152761b0bb75`。boot既定は60rpm/倍率1のまま、RAM/Webだけ
  120rpm候補を適用しdisabled。主ログ`auto-tune/2026-07-31T10-53-38Z`。

## P2最新更新(2026-07-31 19:35 JST)

- 0/60/100/150rpm連続gain scheduleは実制御接続、host test、個別SET_CONFIG、補間後DIAG、
  ARM build/Flashまで完了。以下のP0/P1記述にある「まだgainへ接続しない」は履歴情報。
- unit 1の高速候補は100/150rpm Kp/Ki=140/50、accel/decel FF=0.5/2.5、Kaw=0。
  profileはrate cap100rpm、accel3600、decel1450deg/s2。
- 最終12移動はovershoot最大3.252degで12/12 gate内、平均/worst settle 0.831/0.998sで
  settle gateは9/12。安全停止・current scaleなし。正式既定化はunit 2/3または接地確認まで保留。
- 現Flash MD5 `2297433648339d3359bc97be64b96a67`。runtimeは全band120/50、max60rpm、
  FF0.5/0.5、Web 360/3600/2250、cap60へ復元。disabled、wheel=0、232.119deg、28/26degC、
  zero=1503/seq1/CRC正常。ログは`auto-tune/2026-07-31T10-35-07Z`。

## 結論

P0 telemetryは実装・Flash・実機回帰まで完了。P1 back-calculationはコード/host test/Flashまで完了。
予備2移動では`Kaw=2`が良好だったが、その後のwheel=0/265rpm・複数絶対角の反復試験では
再現しなかった。現時点で採用候補はなく、Flash既定と現在runtimeは`Kaw=0`へ戻してある。

## 現在の実機状態

- unit 1、AMT zero count `1503`、sequence `1`、CRC正常。
- motor disabled、wheel=0、角度約171.30deg、温度30/29degC、AMT/C620正常。
- Flash済みbin MD5: `5b8ec2aedcf418b7887c6f4da76801f3`。
- runtime: steer Kp/Ki=`120/50`、max=`60rpm`、unit accel=`600rpm/s`、
  accel/decel FF=`0.5/0.5`、steer/drive Kaw=`0/0`、status override=0。
- Web UI: `http://localhost:8080`で起動中。profile rate/accel/decel=`360/3600/2250`、time scale=1。

## 実装済み

### P0 telemetry

- `omega_sched=max(abs(steer_rpm_command), abs(observer_rpm))`を10ms LPFで並走計算。
  gain制御にはまだ接続せず、既存出力へ影響しない。
- fixed configをscheduled Kp/Ki/加速FF/制動FF/Kawとして公開。
- steer mode電流の共通scale前、scale後、残差、連続飽和ms、制動phaseを公開。
- STATUS3 bit11=`TORQUE_SCALING_ACTIVE`、bit12=`STEER_BRAKING_ACTIVE`。
- 現ベンチの`can0`はClassic CAN(MTU=16)なので、`0x1B0+id`を4pageの
  `UNIT_STATUS_DIAG`として暫定送信。将来同IDの`UNIT_STATUS_FD`へ置換する。
- Web UI表示/APIとauto tunerのsamples/trials/summary CSVへ接続。

### P1 back-calculation

- 共通scale後の`applied-unsaturated`をsteer/drive別に次周期の積分へ戻す。
- 現周期のmotor指令は変更しない。既存の一周期遅れconditional freezeも維持。
- `SET_CONFIG idx25=steer Kaw`, `idx26=drive Kaw`、範囲0〜20/s。
- 既定0は以前の制御と完全互換。host testでunsat 137.5→applied 100、残差-37.5、
  `Kaw=2, dt=1ms`時の積分補正-0.075を固定した。

## 実機結果

### P0 60rpm回帰

ログ: `firmware/logs/auto-tune/2026-07-31T09-31-27Z`

- wheel=0/265rpm、正逆90deg、4/4収束。
- 平均settle 0.742s、最悪0.938s、overshoot最大4.043deg。
- 従来60rpm 12移動の平均0.802s/最悪1.391s/最大4.571degに非劣化。
- schedule 0〜77.31rpm、scheduled Kp/Kiは全sample 120/50。
- 最大電流1978rawでscaleなし。unsat=applied、残差/飽和時間=0を確認。

### P1 Kaw予備A/B

共通条件: wheel=0、正逆90deg各1、Kp/Ki=160/50、steer max=150rpm、unit accel=2000rpm/s、
profile rate/accel/decel=900/12000/5400deg系、FF=0.5/2.5、current limit=4000raw。

| Kaw | ログ | 平均/最悪settle | overshoot最大 | scale総時間/最長 | deadline |
|---:|---|---|---:|---:|---:|
| 0 | `09-36-29Z` | 0.777/0.938s | 11.426deg | 0.202/0.061s | 1/2 |
| 2 | `09-36-15Z` | 0.620/0.646s | 3.340deg | 0.110/0.070s | 2/2 |
| 4 | `09-36-40Z` | 0.595/0.656s | 3.867deg | 0.070/0.040s | 1/2(7ms超過) |

`Kaw=2`は予備結果で明確に良いが、試行数・絶対角・実行順が不足しているため未採用。
`brake_onset_lag_s`はこの条件では-0.17〜-0.20sとなり、実速度peakがreference減速開始より
先だった。高rpm制動遅れの代表指標として使う前に定義/検出法を再確認する。

### P1 Kaw反復評価

候補順`3 -> 0 -> 4 -> 1 -> 2`、wheel=0/265rpm、正逆90deg、複数絶対角で再評価した。
Kaw=0/1/2/4は各8移動、Kaw=3は24移動。全56/56収束、安全停止・温度異常なし。

| Kaw | 移動数 | 平均/最悪settle | overshoot最大 | deadline |
|---:|---:|---:|---:|---:|
| 0 | 8 | 0.793/0.938s | 10.019deg | 1/8 |
| 1 | 8 | 0.854/1.573s | 10.723deg | 3/8 |
| 2 | 8 | 0.847/1.925s | 9.844deg | 1/8 |
| 3 | 24 | 0.857/1.432s | 12.569deg | 1/24 |
| 4 | 8 | 0.888/1.179s | 7.998deg | 1/8 |

`scheduled_kaw`は全ログで指令値と一致し、Kaw>0の補正も非ゼロだった。Kaw=2の予備優位は
再現せず、Kaw=0のworst settleを改善しながらovershoot目標4deg以下を満たす候補はなかった。
ログは`09-45-01Z`、`09-45-54Z`、`09-46-24Z`、`09-46-51Z`、`09-47-20Z`。

### P1 到達指標分離・インターリーブ確認

初回±2deg進入と、その後STATUS3 settledまでの再収束時間を分離した。Kaw=0/1/2を
同じ絶対角対へインターリーブし、各試行後にSTOP/Disableして状態をリセットした。

- 1反復screenではKaw=1が平均settle 0.684sまで改善したが、初回進入はKaw=0より遅く、
  改善は再収束だけだった。overshoot 5.977degでgate不合格。
- 独立seedの2反復確認では平均settleがKaw=0/1/2で0.689/0.757/0.924s、最大overshootが
  5.273/13.447/12.217degとなり、Kaw=1の優位は再現しなかった。
- 全36移動は収束し安全異常なし。Kaw>0の単独採用は止め、低速既定Kaw=0のままP2へ進む。

## 次に行うこと

1. P2の0/60/100/150rpm連続gain tableを実装する。まず値は全knot同一にして連続性を
   host testし、100/150rpmの速度mode ID結果からKp/Ki/FF/Kawを埋める。
2. 低速knotのKawは0を維持し、高速knotではKp/Ki/制動FFと同じ試験行列で決める。
5. CAN FD driver/48byte `UNIT_STATUS_FD`はTRAJECTORY_FD統合時に実装する。現在のClassic pageを
   先に消さない。

## 運用上の注意

- auto tunerの`--fixed`値は試験終了後もruntimeへ残る。高速試験後は必ずKp/Ki/max/accel/FF/Kawを
  採用値へ明示復元し、診断pageでKp/Ki/Kawを確認する。
- Web UIのSTOPはprofile rateを0へする。STOP後に次回用360deg/sを再設定する。
- current limitは4000rawのまま。P2/P3前に上げない。
- Flash書込みは校正用最終ページ`0x0807F800`へ触れないため、zero=1503は保持されている。
