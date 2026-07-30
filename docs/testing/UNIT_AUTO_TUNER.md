# 単一ユニット自動パラメータ探索

`tools/linux/unit_auto_tuner.py`は、単一差動ステアユニットの実機応答を
粗い探索幅から細かい探索幅へ自動収束させるベンチツールである。
Web UIの安全な目標プロファイル/STOPを使用し、ファームの`SET_CONFIG`は
SocketCANから直接更新する。

探索中は`SET_CONFIG idx22=5ms`でSTATUS1/2を200Hz送信し、Web UIがCAN上のfreshな
角度/wheel/steer rpmを受けて採点する。完了はG474のSTATUS3 `MOTION_SETTLED`を正本とし、
新指令後に一度Lowを観測してからのHighだけを採用する。各サンプルにはWeb UI側sequenceを付け、
同じsnapshotを複数回数えない。探索終了時はidx22=0で通常20/50ms周期へ戻す。

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

Flash後の中心点だけを回帰確認する例:

```bash
python3 tools/linux/unit_auto_tuner.py \
  --yes-wheel-lifted --evaluate-only --full-scenarios \
  --params steer_decel_dps2 --center steer_decel_dps2=2250 \
  --repeats 3
```

## 出力

`firmware/logs/auto-tune/<UTC timestamp>/`へ逐次保存する。

- `trials.csv`: 各移動の生評価値
- `summary.csv`: 候補別スコア、平均/最悪収束、失敗数
- `score.svg`: 各パラメータ値とスコアのグラフ(外部plot依存なし)
- `metadata.json`: 引数、開始幅、最良値、最終適用値

プロセス中断、例外、温度上限、ファーム安全停止時も通常はWeb UIの減速STOPを
試みる。Web APIが失われた場合だけ直接disableへフォールバックする。

## 空走値と接地値

空走探索で確定できるのは、センサ/通信遅延、差動干渉、無負荷安定限界、
目標プロファイル追従帯域である。接地時はタイヤ静止摩擦、横力、荷重移動、
3輪拘束が加わるため、空走最良値を中心に狭い幅で再探索する。

接地探索では温度・電流余裕に加え、低速stick-slip率、車体姿勢誤差、
3輪間の飽和/拘束をスコアへ追加して最終値を決める。

## 2026-07-31 空走採用値

- 局所制御: steer mode `Kp=120`, `Ki=50`, hold angle `Kp=4`, moving angle `Kp=1`,
  deadband `0.3deg`, mode速度LPF `tau=2ms`, 加速/制動FF gain `0.5/0.5`
- 中央プロファイル: 最大`240deg/s`, 加速`3600deg/s^2`, 制動`2250deg/s^2`, 生成`200Hz`
- time scale=2の本番受入はwheel 0/265rpm、正逆90deg、12試行でCAN収束12/12、
  deadline `1.273s`以内12/12、平均`1.146s`、最悪`1.250s`、最大overshoot`1.054deg`。
- current limitは`4000 raw`。3000/4000/5000/6000比較では電流クランプが律速でなかった。
- 追加試験では300/360deg/sは内周が追従できず240deg/sより遅かった。steer minimum rpmと
  一定Coulomb摩擦FFも未収束を増やしたため0を維持する。time scale=1のゲイン限界試験は
  収束11/12、`2*Tmin`以内7/12で、終端静止摩擦が残る。接地後は空走値を中心に狭い範囲で
  再探索し、複数バッチのworst/failed数を必ず確認する。
