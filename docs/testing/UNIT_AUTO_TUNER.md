# 単一ユニット自動パラメータ探索

`tools/linux/unit_auto_tuner.py`は、単一差動ステアユニットの実機応答を
粗い探索幅から細かい探索幅へ自動収束させるベンチツールである。
Web UIの安全な目標プロファイル/STOPを使用し、ファームの`SET_CONFIG`は
SocketCANから直接更新する。

探索中は`SET_CONFIG idx22=5ms`でSTATUS1/2を200Hz送信し、Web UIがCAN上のfreshな
角度/wheel/steer rpmを受けて採点する。完了はG474のSTATUS3 `MOTION_SETTLED`を正本とし、
新指令後に一度Lowを観測してからのHighだけを採用する。各サンプルにはWeb UI側sequenceを付け、
同じsnapshotを複数回数えない。探索終了時はidx22=0で通常20/50ms周期へ戻す。
VCPが接続されている場合は、相補observerの推定角、推定軸rpm、AMT innovationも
`samples.csv`へ保存する。observer補正時定数は`steer_observer_tau_s`(`SET_CONFIG idx23`、
既定0.050s)、friction FF減衰速度は`steer_friction_ff_fade_axis_rpm`
(`SET_CONFIG idx24`、既定10rpm)として単独探索できる。observer角/innovation自体は
試行スコアや制御判定には使わない。
Web UIはClassic CAN移行ベンチ用`SET_TARGET_ACCEL_FF`も200Hz送信する。`samples.csv`の
`steer_accel_explicit_active`が1なら、G474は受信周期から再微分した加速度ではなく明示profile
加速度をFF/制動phaseへ使用中である。高速試験ではこの列が運動区間を通じて1であることを確認する。
制動Kp倍率はglobal `steer_brake_kp_multiplier`に加え、100/150rpm knotを
`steer_brake_kp_multiplier_100/150`で個別探索できる。global値を先に送り、個別knotを後から
上書きするため、低速倍率を保ったまま高速制動だけを強められる。

## 目的

手動の「1点試験→ログ確認→次の値を入力」を廃止し、次を同じ条件で比較する。

- 指定角度への0.5deg収束時間
- 運動学的な最短時間に対する応答倍率
- オーバーシュート、追従誤差、終端誤差
- wheel rpm維持誤差
- 指令/実測モータ電流ピーク
- 温度、安全停止、未収束数
- 正逆、wheel停止/回転中、絶対角度依存のばらつき

## 応答倍率

wheel rpmから10%予備付き差動モータrpm包絡線で許される最大steer速度を`V`、
移動角を`D`、加速/制動を`a,d`とする。`Dc=V^2/(2a)+V^2/(2d)`に対し、
非対称台形/三角形の基準軌道最短時間を使う。

```text
if D >= Dc:
    t_min = V/a + (D-Dc)/V + V/d
else:
    Vp = sqrt(2D/(1/a+1/d))
    t_min = Vp/a + Vp/d
response_ratio = measured_settle_time / t_min
```

値は1に近いほどよい。未収束、安全停止、終端誤差、オーバーシュートには
スコア上のペナルティを加え、単に目標プロファイルだけが速い候補を選ばない。
ゲイン性能試験は`--trajectory-time-scale 1`、本番受入は`2`とする。性能期限は最低でも
`2*t_min`を確保し、本番受入では`2*t_min+0.35s`を初期監視期限とする。0.35sは空走実測値で、
接地後の残差p99から更新する。期限超過後も`--trial-timeout`までは診断ログを継続する。

## 探索方式

各ラウンドで中心点と、各パラメータを現在幅だけ正負へ振った点を評価する。
最良点を次の中心にし、既定では幅を0.5倍にして繰り返す(pattern search)。
全組合せgridより実機試行数を抑えながら、粗→細探索ができる。

候補ごとに通常は次を実行する。

```text
enable
  -> wheel=0, +90deg
  -> wheel=target, -90deg
  -> ramp STOP -> disable
```

`--full-scenarios`ではwheel=0/targetの各正逆、計4移動を行う。
`--repeats N`では一式を反復し、平均と最悪値の両方で採点する。

## 推奨校正順序

カスケードの全パラメータを最初から同時探索すると、内周の遅れを外周ゲインで隠す候補も
同点になり、負荷が変わったときに崩れやすい。校正パッケージは次の段階に分ける。

1. 外周を切った速度step/PRBSでステア速度プラントを同定し、内周PIと速度フィルタを決める。
2. 内周値を固定して、外周angle Pとdeadbandを決める。生の角度DはAMT22量子化を増幅するため
   使わず、必要な減衰は実測mode速度を用いる。
3. 加速度FF、最大速度、加速/制動を別々にした中央プロファイルを決める。
4. wheel停止/回転、正逆、絶対角度、接地荷重、床材のシナリオ行列で回帰する。
5. 空走値を共通初期値とし、接地時は小さい探索幅だけ再実行する。

床材ごとの別ゲインを最初から持つのではなく、まず全条件で安全な共通ゲインを選び、摩擦FF・
負荷推定で差を吸収する。それでも帯域差が大きい場合だけ、測定可能な負荷状態に基づく
ゲインスケジューリングへ進む。

## ステアmode速度ループ単体同定

`tools/linux/unit_steer_mode_id.py`は、上記手順1のための専用ツールである。
通常の角度追従試験と異なり、試験中だけhold/moving angle Kpを両方0にし、
`SET_TARGET_FF`を直接ステア軸速度目標として使用する。加速/制動FFと摩擦FFも0にするため、
観測対象は速度LPF+steer mode PI+機構だけになる。

観測は既存`STATUS2 (0x190+unitId)`のmotor 1/2 rotor rpmを使用する。UARTを高頻度化すると
115200baudのポーリング送信が1kHz制御を止めるため、`SET_CONFIG idx22`で試験中だけ
STATUS1/2周期を1〜100msに設定する。0で通常周期(20/50ms)へ戻る。

現行Flash値`Kp=120, Ki=50, tau=2ms`の正負step:

```bash
python3 tools/linux/unit_steer_mode_id.py \
  --yes-wheel-lifted --pattern step \
  --kp 120 --ki 50 --filter-tau-s 0.002 \
  --amplitude-rpm 20
```

PRBS入力を保存する例:

```bash
python3 tools/linux/unit_steer_mode_id.py \
  --yes-wheel-lifted --pattern prbs \
  --kp 120 --ki 50 --filter-tau-s 0.002 \
  --amplitude-rpm 20 --chip-s 0.025
```

`amplitude-rpm`はステア軸rpmで、20rpm=120deg/s。stepは正負パルスとゼロ区間を組にし、
PRBSは31chip列とその反転を連結して角度ドリフトを抑える。結果は
`firmware/logs/steer-mode-id/<UTC timestamp>/samples.csv`と`metadata.json`へ保存する。
終了・例外・Ctrl-Cのいずれでもdisableを送り、変更したRAMパラメータを空走採用値へ戻す。
試験中にWeb UIが同じCANへ目標を再送すると角度目標が競合するため、mode IDはWeb UIが
応答中なら実行を拒否する。`unit_web_ui.py`を終了してから実行すること。開始角はbuffer済みVCP
文字列でなくfreshなCAN STATUS1から取り、STATUS3 ACTIVE確認後だけ計測する。外周angle Kp=0中の
安全用SET_TARGETはSTATUS1実角へ追従させ、速度指令は`steer-accel-rpm-s`でrampする。これにより
内周速度追従遅れを120deg angle-divergence異常と誤判定せず、ACTIVE脱落時は即時中止・復帰する。

比較はまずKi=0でKp/tauの安定限界と立上りを決め、次にKiを足して定常偏差を消す順で行う。
LPFを短くすると位相遅れは減るがC620 rpm量子化と機構ノイズが増えるため、立上りだけでなく
正負のovershoot、tail MAE、再現性を同時に確認する。

## 実行例

前提として、wheelを浮かせてWeb UIを起動する。

```bash
python3 tools/linux/unit_web_ui.py --vcp-port /dev/ttyACM0
```

Kp、Ki、中央steer速度/加速度を3ラウンド探索する例:

```bash
python3 tools/linux/unit_auto_tuner.py \
  --yes-wheel-lifted --apply-best --full-scenarios \
  --params steer_kp,steer_ki,steer_rate_dps,steer_accel_dps2 \
  --center steer_kp=80 --center steer_ki=25 \
  --center steer_rate_dps=240 --center steer_accel_dps2=3600 \
  --span steer_kp=40 --span steer_ki=20 \
  --span steer_rate_dps=60 --span steer_accel_dps2=360 \
  --rounds 3 --trial-timeout 3
```

特定の値を固定して1変数を反復比較する例:

```bash
python3 tools/linux/unit_auto_tuner.py \
  --yes-wheel-lifted --full-scenarios --repeats 2 \
  --params steer_decel_dps2 \
  --fixed steer_kp=80 --fixed steer_ki=25 --fixed steer_rate_dps=240 \
  --fixed steer_accel_dps2=3600 \
  --center steer_decel_dps2=2250 --span steer_decel_dps2=150 \
  --rounds 1
```

候補別の連続バッチによる時間順・絶対角バイアスを避けるため、1変数の明示候補を
インターリーブ比較する例:

```bash
python3 tools/linux/unit_auto_tuner.py \
  --yes-wheel-lifted \
  --params steer_backcalc_gain --compare-values 0,1,2 \
  --repeats 2 --wheel-rpm 265 \
  --fixed steer_kp=160 --fixed steer_ki=50 \
  --fixed steer_max_rpm=150 \
  --fixed steer_accel_limit_rpm_per_s=2000 \
  --fixed steer_rate_dps=900 \
  --fixed steer_accel_dps2=12000 \
  --fixed steer_decel_dps2=5400
```

`--compare-values`は`--params`を1変数に限定する。各wheel条件で毎移動の方向を交互にし、
全候補へ正逆を1回ずつ割り当てて元の絶対角へ戻る。偶数repeatでは最初の方向を反転し、
反対側の絶対角帯も全候補へ均等に割り当てる。各試行後は通常STOP/Disableし、PI積分と
observer状態をリセットしてから次候補を適用する。

Flash後の中心点だけを回帰確認する例:

```bash
python3 tools/linux/unit_auto_tuner.py \
  --yes-wheel-lifted --evaluate-only --full-scenarios \
  --params steer_decel_dps2 --center steer_decel_dps2=2250 \
  --repeats 3
```

`--evaluate-only`は常に1 roundだけ実行する。反復数は`--repeats`で指定し、既定rounds=3による
同一中心点の意図しない3重実行は行わない。高速試験では`steer_commissioning_cap_rpm`を
`--fixed`で指定でき、Web UI capを先に更新してからrateを設定する。100/150rpm個別knotは
`steer_kp_100`等の`Kp/Ki/accel_ff/decel_ff/backcalc`パラメータとして探索できる。

## 出力

`firmware/logs/auto-tune/<UTC timestamp>/`へ逐次保存する。

- `trials.csv`: 各移動の生評価値
- `summary.csv`: 候補別スコア、平均/最悪収束、失敗数
- `score.svg`: 各パラメータ値とスコアのグラフ(外部plot依存なし)
- `metadata.json`: 引数、開始幅、最良値、最終適用値

応答の速さと振り返しを分離するため、`trials.csv`には次も保存する。

- `first_entry_2deg_s`: 初めて目標±2deg境界へ到達した時刻(隣接sample間を線形補間)
- `first_entry_band_s`: 初めてsettle band(既定±0.5deg)境界へ到達した時刻(同補間)
- `first_crossing_s`: 初めて目標角を通過した時刻(同補間)
- `resettle_after_entry_2deg_s`: 初回±2deg進入からSTATUS3 settledまでの時間

高速域では100Hz sample間に数deg進むため、帯内sampleの有無だけでは初回通過を取り逃し、
overshoot後の再進入を初回到達と誤判定する。上記3時刻は移動方向に沿った誤差境界の最初の
crossingを線形補間し、sample rateに起因する合否反転を避ける。

インターリーブ比較の空走・応答優先ゲートは、全試行で安全停止なし、`first_entry_2deg_s` 0.50s以下、
overshoot 20deg以下、終端誤差1deg以下。合格候補から平均`first_entry_2deg_s`が短い値を選ぶ。
旧overshoot 4deg/settle 0.9s gateは`strict_settle_failures/pass`へ診断値として残す。
20degはunit 1浮上状態で300rpm commissioningを進めるための一時基準で、接地3輪へは流用しない。

P0高速telemetry実装後は、`samples.csv`へschedule rpm、scheduled Kp/Ki/加速・制動FF、
共通scale前後のsteer電流、残差、連続飽和ms、scale/制動phaseも保存する。`trials.csv`には
実steer peak rpm、reference減速開始、実速度peakで定義した実減速開始、その時間差、
scale総時間/最長連続時間を追加する。正負は既存`direction`列で分離できる。
`steer_backcalc_gain`/`drive_backcalc_gain`は`SET_CONFIG idx25/26`として0〜20/sを探索でき、
各周期のsteer/drive積分補正量も`samples.csv`へ保存する。

プロセス中断、例外、温度上限、ファーム安全停止時も通常はWeb UIの減速STOPを
試みる。Web APIが失われた場合だけ直接disableへフォールバックする。
EnableはCANへ2回送信し、STATUS3 `ACTIVE`を0.5s以内に確認してから最初の目標を送る。
確認できない場合はdisableして候補を失敗扱いにし、未Enable状態のログを性能値へ混ぜない。

高速試験用の入力範囲はsteer rate 2046deg/s、profile accel/decel 12000deg/s2までとする。
いずれもunit側の差動mode hard包絡を解除する値ではない。`steer_accel_limit_rpm_per_s`
(`SET_CONFIG idx9`, 100〜4000rpm/s)を候補に含める場合、試験終了時は開始時runtime値へ戻す。
idx9は通常の軌道生成器ではなくユニット側の最終ガードであり、中央が送る最大加速度より
十分高く設定して二重ランプを避ける。boot既定値600rpm/sは安全な単体起動用として維持する。

## 空走値と接地値

空走探索で確定できるのは、センサ/通信遅延、差動干渉、無負荷安定限界、
目標プロファイル追従帯域である。接地時はタイヤ静止摩擦、横力、荷重移動、
3輪拘束が加わるため、空走最良値を中心に狭い幅で再探索する。

接地探索では温度・電流余裕に加え、低速stick-slip率、車体姿勢誤差、
3輪間の飽和/拘束をスコアへ追加して最終値を決める。

## 2026-07-31 空走採用値

- 局所制御: steer mode `Kp=120`, `Ki=50`, hold angle `Kp=4`, moving angle `Kp=1`,
  deadband `0.3deg`, mode速度LPF `tau=2ms`, 加速/制動FF gain `0.5/0.5`,
  wheel依存テーパ付き摩擦FF `200raw`（30rpmで0、80〜235degは最大2倍）
- 中央プロファイル: 最大`360deg/s`（60軸rpm commissioning段階）、加速`3600deg/s^2`,
  制動`2250deg/s^2`, 生成`200Hz`
- time scale=2の本番受入はwheel 0/265rpm、正逆90deg、12試行でCAN収束12/12、
  deadline `1.273s`以内12/12、平均`1.146s`、最悪`1.250s`、最大overshoot`1.054deg`。
- current limitは`4000 raw`。3000/4000/5000/6000比較では電流クランプが律速でなかった。
- 初期試験でWeb側だけを300/360deg/sへ上げた際は、ユニット側`steer_max_rpm=40`が残って
  いたため240deg/sより遅かった。角度依存stall対策後、ユニット側上限も60rpmへ同時に
  上げた再試験はwheel=0/265rpm・複数絶対角で26/26合格し、60rpm段階を採用した。
  steer minimum rpmと全wheel rpmへ一律に加えるCoulomb摩擦FFは未収束を増やしたため不採用。
  2026-07-31に
  wheel=0近傍だけへテーパ適用する200rawと角度依存ブーストを採用し、time scale=1.0を
  既定化した。接地後は空走値を中心に狭い範囲で再探索し、複数バッチのworst/failed数を
  必ず確認する。

## 2026-07-31 高速域の方針

60〜156rpmの空走試験により、100rpm超は固定PI/固定FFのまま電流上限だけを増やす方針を
採らない。実速度は156rpmまで到達したが、120〜150rpm帯では減速後の速度残りによって
overshootが10〜15degへ増えた。4000raw未満でも同現象が出たため、一次原因は電流不足ではない。

今後は`docs/control/HIGH_SPEED_STEER_GAIN_SCHEDULING_PLAN.md`に従い、telemetryと
back-calculation anti-windupを先行実装した後、0/60/100/150rpmの速度帯で連続補間する。
current limitは加速中の不足が計測で確認された場合だけ段階的に上げる。

同日P4ではauto tunerの再現可能な既定値を120rpm packageへ更新し、`steer_max/cap=120rpm`、
unit hard guard=2000rpm/s、profile=720/5400/2000deg系、100/150 knot Kp/Ki=140/50、
decel FF=2.5、brake Kp倍率2を使う。300rpm段は必ず`--fixed`でmax/cap/rate/accel/decelを明示する。
300rpm capの90deg試験は6/6実用合格した。当初の連続実速度確認はmode IDの260rpmまでだった。

同日の復旧後試験で300rpm実速度へ到達したが、`unit_steer_mode_id.py`旧版の対称4000rpm/s
rampによる300→0急制動で電源保護停止が発生した。改修版は`--steer-decel-rpm-s`既定500rpm/s、
制動所要時間+zero dwell、0rpm経由の反転、zero確認後Disableを使う。最初の再確認は
`--step-direction positive`の単方向1 pulseで実施し、peak 300.9rpm、0.595s制動、feedback維持で
完走した。4000rpm/s制動は再使用せず、追加反復前に24V bus peakを計測する。

## 24V回生計測ゲート

現ベンチの`STATUS3.busVoltageMv`は未実装値`0xffff`で、G474基板のADCは5V制御電源監視専用。
C620のCAN feedbackも角度・速度・トルク電流・温度だけで24V入力値を含まない。このため
260 axis rpmを超える`unit_steer_mode_id.py`試験は、外部24V計測なしでは
`--steer-decel-rpm-s <= 500`を強制する。外部計測器を接続し`--yes-24v-monitored`を明示した
場合だけ、500rpm/sを超える制動試験を許可する。

計測はC620へ入る24V/GND間を、single-shotオシロまたは十分な過渡捕捉能力を持つmin/max計で
観測する。接地型オシロを使う場合は、電源負極・保護接地との関係を確認し、接地クリップで
短絡を作らない。必要なら定格の合う差動プローブまたは絶縁された計測器を使う。

最初の計測条件はwheel浮上、単方向1 pulse、300rpm、pulse 0.3s、加速4000rpm/s、制動500rpm/s:

```bash
python3 tools/linux/unit_steer_mode_id.py \
  --yes-wheel-lifted --yes-24v-monitored \
  --pattern step --step-direction positive \
  --amplitude-rpm 300 --pulse-s 0.30 --zero-s 0.25 \
  --steer-accel-rpm-s 4000 --steer-decel-rpm-s 500
```

初期電圧、制動中peak、電源型番・OVP設定/表示、C620 LED、feedback drop数を記録する。
DJI公式C620ガイドが明示するのはrated 24Vで、最大連続入力電圧は記載されていないため、
推測したC620上限を合否値にしない。使用電源のOVP仕様とC620の追加一次資料が揃うまでは、
「電源が落ちなかった」だけで減速率を500rpm/sより上げない。

計測器導入前のランプ吸収評価では、負方向300rpmもpeak300.9rpm、feedback drop 0で完走した。
位置profileも制動3000deg/s2(500 axis rpm/s)へ制限した。応答優先の空走候補は
cap300rpm、加速12000deg/s2、制動3000deg/s2、current limit4500raw。4000/4500rawを170degで
各4移動インターリーブし、4500はfirst-entry平均0.344s、overshoot最大16.152degで4/4実用合格。
90deg full 4移動もfirst-entry最悪0.243s、overshoot最大15.205degで4/4合格した。
試験後はcurrent limit4000raw、GUI cap60rpmへ戻し、boot既定は変更しない。
