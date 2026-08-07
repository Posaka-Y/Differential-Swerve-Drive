# 高速ステア用ゲインスケジューリング実装計画

## 目的

正逆転最短化後の最大90deg操舵を、低速・静止摩擦域の収束性を維持したまま高速化する。
モーターrpm hard包絡は純操舵約341 axis rpmまで余裕があるが、現行の固定PI/固定加減速FFでは
100rpm超から制動追従が先に限界になる。電流上限を先に広げず、局所servoを速度帯に適応させる。

## 2026-07-31 実機根拠

unit 1、wheel浮上、90deg正逆、原点校正後の結果。安全停止・温度異常は全試験で0件、最高28degC。

| 条件 | 結果 |
|---|---|
| 60rpm既定、12移動 | 平均settle 0.802s、最悪1.391s、overshoot最大4.57deg、電流最大1717raw |
| 100rpm上限、既定加減速、12移動 | 平均0.789s、最悪0.898s、overshoot最大6.68deg、電流最大1942raw |
| 100rpm、Kp=160/Ki=50、decel FF=1.5、4移動screen | 平均0.696s、最悪0.787s、overshoot最大3.78deg |
| accel 900rpm/s、対称profile 5400deg/s2、decel FF=1.5 | profile peak約117rpm、overshoot最大13.71deg、電流最大3779raw |
| 同条件、decel FF=2.5 | overshoot最大8.53deg、電流最大2402raw |
| accel 1200rpm/s、対称profile 7200deg/s2、decel FF=2.5 | profile peak134rpm、実速度peak145rpm、overshoot最大14.77deg、電流最大3289raw |
| accel 2000rpm/s、非対称profile 12000/5400deg/s2、decel FF=2.5 | profile peak137rpm、実速度peak156rpm、overshoot 10.20〜13.01deg、4000rawへ約70〜80ms飽和 |

高rpm自体は出ている。問題は、referenceが減速へ入った後も実速度が残り、固定PI/FFでは
制動電流の位相と大きさを両立できないこと。4000raw未満でも大overshootが発生しているため、
電流上限は一次原因ではない。FFを3.0〜3.5へ上げて4000rawへ張り付かせても反動が悪化した。

## 採用する制御構造

### スケジュール変数

1kHz局所ループで次を計算する。

```text
omega_sched_raw = max(abs(omega_steer_ref), abs(omega_steer_observer))
omega_sched = LPF(omega_sched_raw, tau=10ms)
```

referenceだけを使うと減速開始時に高速ゲインが早く抜け、実速度だけを使うと加速開始が遅れるため、
両者の最大値を使う。単位はsteer axis rpm。離散的なモード切替は行わず、隣接knot間を線形補間する。

初期knotは`0/60/100/150rpm`。0〜60rpmは現行採用値を完全に維持する。100/150rpmの値は
速度mode IDで同定し、閉ループ90deg試験で確定する。将来200rpm以上へ広げる場合はknotを追加する。

各knotが持つ値:

- steer mode `Kp`, `Ki`
- acceleration FF gain
- braking FF gain
- mode rpm LPF時定数(必要な場合のみ。初版は2ms固定)
- back-calculation gain `Kaw`
- 制動phase限定Kp倍率

加速/制動の判定は`target_accel * target_rate < 0`を制動とする。ゼロ交差付近は直前phaseを
5ms保持し、CAN jitterによるFF gain切替を防ぐ。

### Bumplessな補間

- `Kp/Ki/FF/Kaw`は連続線形補間し、knot境界で電流段差を作らない。
- PI積分状態はすでにcurrent単位なので、Ki変更時に積分値を倍率変換しない。
- Kp変更による出力変化は`omega_sched`の10ms LPFで制限する。
- disabled/reset時は低速knotへ戻し、積分・schedule速度・phaseを初期化する。

## 実装フェーズ

### P0: 計測を先に追加

`unit_control_output_t`とmini PC telemetry/CAN FD statusへ以下を追加する。

- `steer_schedule_rpm`, `scheduled_kp`, `scheduled_ki`
- `scheduled_accel_ff_gain`, `scheduled_decel_ff_gain`
- `steer_current_unsaturated`, `steer_current_applied`
- `steer_saturation_residual`, `steer_saturation_duration_ms`
- `steer_braking_active`

auto tunerは実速度peak、reference/actualの減速開始差、正負別飽和時間をCSVへ保存する。

2026-07-31 P0a実装済み。schedule信号は10ms LPFまで並走計算するが、まだ固定gainへ
フィードバックしない。現在のmini PCベンチはClassic CAN MTU=16のため、`0x1B0+id`を
3pageの`UNIT_STATUS_DIAG`として送信し、STATUS3 bit11/12でもscale/制動phaseを20ms周期で返す。
CAN FD 48byte transportへの統合はFDCAN1/Teensy CAN3のFD化時に行う。

### P1: back-calculation anti-windup

現在の一周期遅れconditional freezeを残したまま、最終的に適用されたmode電流との差を使う。

```text
I_unsat = P + I_state + FF + friction
I_applied = I_unsat * common_current_scale
I_state += (Ki * speed_error + Kaw * (I_applied - I_unsat)) * dt
```

steer/driveを別々に戻し、既存の共通current scaleによるmode比率維持は変更しない。
まず4000raw固定で飽和解除後の積分残りを減らす。current limit引上げより先に完了させる。

2026-07-31にP1コードとhost testを追加。`SET_CONFIG idx25/26`でsteer/drive別Kawを
0〜20/s変更でき、既定0は従来出力と完全互換。共通scale後の残差を当該周期の最終出力には
戻さず、次周期の積分状態だけへ反映する。実機A/BでKawを確定するまでは既定0を維持する。

### P2: 速度mode単体同定とschedule作成

外周angle P、摩擦FF、加速度FFを切り、wheel=0で正負step/PRBSを行う。

1. 60rpm: 現行`120/50`を回帰基準にする。
2. 100rpm: Kp 120/140/160、Ki 25/50/75を再同定する。
3. 150rpm: Kpを160から開始し、安定限界を探してからKiを決める。
4. wheel=265/600rpmでも同じbandを測り、drive modeとの帯域変化を確認する。

2026-07-31に連続補間、実PI/FF/Kaw接続、host test、個別knot用`SET_CONFIG idx27..46`、
補間後DIAG telemetryまで実装・Flash済み。unit 1空走では140/50を100/150rpm候補とし、
制動FF=2.5、profile decel=1450deg/s2で12移動のovershoot最大3.252degを得た。一方worst settleは
0.998sで0.9s gate未達のため既定化せず、unit 2/3または接地評価後にP2完了判定する。

各bandでovershootを直接最小化せず、速度追従帯域・位相余裕・定常誤差からPIを決める。
その後に連続補間tableとして閉ループへ入れる。

### P3: 明示target accelerationとモデルFF

現在の200Hz rate差分はCAN jitterを含み、±1000rpm/s clampも高速profileを欠落させる。
`TRAJECTORY_FD`の`thetaDot/thetaDDot`をG474が1kHz補間し、加速度を明示入力する。

```text
I_ff = Ka(speed, phase) * target_accel
     + Kv(speed) * target_speed
     + Ic * softsign(target_speed)
```

正負差が再現する場合だけ方向別係数を持つ。角度別gain tableは作らず、機構局所抵抗は
既存friction補償と将来のbounded DOBへ任せる。

2026-07-31にP3aとして、現行Classic CANベンチ用`SET_TARGET_ACCEL_FF (0x160+id)`を追加した。
Webプロファイラが200Hzで実際のprofile rate差分をmdeg/s^2として送信し、G474はfreshな間だけ
明示値を優先する。途絶時は従来の受信時刻差分へ戻るため旧ツール互換を維持する。診断
`diagFlags bit2`とauto tunerの`steer_accel_explicit_active`で適用を確認できる。P3bではこれを
本来の`TRAJECTORY_FD`受信・1kHz補間へ移し、Classic専用IDを本番制御には使わない。

### P4: jerk制限付き非対称軌道

中央Teensyで加速・制動・jerkを独立制約にする。ユニット内部のrpm rampは通常軌道生成ではなく
hard guardへ変更し、中央profileとの二重ランプを除去する。追従遅れのp99から制動開始余裕を決め、
3輪は最遅ユニットへ同一時刻断面で同期する。

2026-07-31にWebベンチと中央host coreへ加速度state、jerk制限、jerk過渡込み停止距離を実装した。
100k/200k deg/s3はhost試験と実機比較を通過したが、120rpmでは200kがovershootを減らす一方で
first-entryを約23ms遅らせた。応答優先commissioningはjerk=0を維持し、non-zero jerkのproduction
採用は接地3輪で決める。G474のrate rampはruntime最大4000 axis rpm/sのhard guardへ移し、
通常profileとの二重rampを除去した。

300rpm capの90deg試験は6/6実用合格したが、三角profileの実peakは145rpm以下。外周angle Pを
切った速度stepでは300rpm実速度へ到達した。一方、旧速度stepは加速/制動とも4000rpm/sで、
300→0急制動時に電源保護停止が発生した。速度能力と安全停止を分け、改修版は加速4000rpm/s、
制動既定500rpm/s、0rpm dwell後Disable、単方向1 pulseとした。改修後の正方向300rpm試験は
peak 300.9rpm、0.595s制動、実測5rpm未満後0.25s待機で完走し、feedback/ACTIVEを維持した。
負方向もpeak300.9rpm、feedback drop 0で完走した。計測器導入までは、無計測の260rpm超試験を
制動500rpm/s以下へ制限し、ソフト上の正常だけで回生余裕を判定しない。

### P5: current limit拡張の条件

4000rawのままP0〜P4を完了する。次をすべて満たす場合だけ`4500 -> 5000 -> 5500 -> 6000`と上げる。

- acceleration区間で`torque_scaling_active`が20ms以上継続する。
- tracking errorの符号が要求加速方向と一致し、電流不足を示す。
- braking/overshoot区間の誤位相飽和ではない。
- 4000rawでschedule/anti-windup/FFを調整済み。
- C620電流・24V bus・回生電圧・温度が上限内。

各段階は正逆90degを最低12移動、wheel=0/265rpmで実施する。電流を上げてovershootが増える場合は
即座に前段へ戻す。

2026-07-31の暫定P5評価では、170deg・wheel265負方向の4000rawで加速9 sample中7 sampleが
current scaleとなり、未飽和要求5375rawに対し適用3934raw、first-entry0.605sだったため、
4500rawへ1段だけ進める条件を満たした。4000/4500rawの170degインターリーブ各4移動では、
4500がfirst-entry平均0.344s、settle平均0.888s、overshoot最大16.152degで4/4実用合格。
別の170deg 4移動と90deg 4移動も4500rawで全合格し、計12移動を確認した。ただし24V peakが
未計測なのでP5正式完了・boot採用とはせず、5000rawへは進まない。試験後RAMは4000rawへ戻した。

## テストと合格条件

### host test

- knot値、区間中央、上下端clampの補間値
- 59.9/60.0/60.1rpmで電流指令が連続
- reference下降中も実速度が高ければ高速gainを維持
- reset/disableで低速scheduleへ戻る
- saturation時のanti-windup、解除後の積分回復
- current common scale後もsteer/drive mode比率を維持
- 既存observer、摩擦FF、0/360deg wrap試験を全て維持

### 実機ゲート

1. 60rpm回帰: 現行12移動に非劣化。
2. 100rpm: wheel=0/265、正逆各6。overshoot 4deg以下、最悪settle 0.9s以下。
3. 120〜150rpm: peak実速度、飽和時間、回生電圧を確認しながら10〜15rpm刻み。
4. unit 1で成立後、unit 2/3でも同一試験。共通tableは3台の最悪値で決める。
5. 共通tableで成立しない定常的な個体差だけ、Flash保存するunit別trim(`Kp/Ki/Ka`倍率)を許可する。
6. 接地3輪で`PRESTEER -> DEPART`、共通desaturation、全輪settledを確認する。

初期合格はovershoot 4deg以下、最終目標は1deg以下。3輪接地で摩擦が支配的になった場合も、
床材名や絶対角による手動gain切替は行わず、observer速度・電流残差・DOBで適応する。

## 実装順序まとめ

```text
P0 telemetry
 -> P1 back-calculation anti-windup
 -> P2 continuous speed gain schedule
 -> P3 explicit accel + model FF
 -> P4 jerk-limited central trajectory
 -> P5 evidence-gated current increase
 -> 3 units / grounded validation
```
