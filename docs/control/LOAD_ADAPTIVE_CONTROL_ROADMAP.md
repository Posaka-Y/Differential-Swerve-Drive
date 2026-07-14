# 負荷適応制御ロードマップ

作成: 2026-07-09(状態: **将来設計方針として確定、実装は接地評価後**)

## 結論

差動ステアユニットの負荷対応は、現行の mode PI 制御を土台にして段階的に強化する。

```text
現行: P_theta + PI_d + PI_s
  -> FF強化
  -> 摩擦補償
  -> mode-space DOB
  -> 状態推定
  -> 必要なら上位MPC
```

最初からMPCやRLへ進まない。現時点で最も相性がよい候補は以下。

```text
P_theta + PI_d + PI_s + FF + DOB_d + DOB_s
```

理由:

- 既存実装が drive mode / steer mode に分離済みで、追加制御を mode 電流指令へ自然に足せる。
- 負荷下で最初に問題化しやすいのは、最適化不足ではなく摩擦、飽和、干渉、負荷変動の帯域不足。
- G474は1kHz局所制御と安全停止に集中させ、3輪協調や制約最適化はTeensy/mini PC側へ置く方が責務分離がよい。

## 負荷下で想定する崩れ方

### 1. 静止摩擦

軽い指令では動かず、PI積分が溜まった後に一気にブレークアウェイする。

```text
誤差あり
  -> I項が溜まる
  -> 静止摩擦突破
  -> 急加速
  -> overshoot / stick-slip
```

浮きベンチでは、低速drive側でブレークアウェイと維持電流の差がstick-slip原因になることを確認済み。
接地後はステア側でも同様の症状が出る可能性が高い。

### 2. 姿勢・荷重依存のステア負荷

ステア負荷は一定ではない。

- 車輪横力
- タイヤ摩擦
- ケーブル抵抗
- ベアリング摩擦
- 機構偏心
- 3輪間の拘束

定常負荷はPI積分で吸収できるが、負荷変動の帯域がPIより速いと追従遅れや角度誤差として出る。

### 3. drive / steer の残留干渉

理想式では、

```text
motor1 = drive + steer
motor2 = -drive + steer
```

だが、実機では以下により純driveにsteerが混ざる、または純steerにdriveが混ざる可能性がある。

- ギア効率差
- モーター個体差
- 摩擦非対称
- バックラッシュ
- 片側だけの温度上昇
- C620電流制御差

この干渉が大きい場合、単なるゲイン調整ではなく、mode空間での補償・診断が必要になる。

## 発展段階

### Level 0: 接地評価とログ強化

高度制御を入れる前に、負荷下で何が破綻しているかを切り分ける。

最低限ログする値:

| 値 | 用途 |
|---|---|
| `theta_s` | 実ステア角 |
| `theta_s_ref` | 目標ステア角 |
| `omega_d`, `omega_d_ref` | drive mode 実測/目標 |
| `omega_s`, `omega_s_ref` | steer mode 実測/目標 |
| `I_d`, `I_s` | mode電流 |
| `I_1`, `I_2` | C620電流指令 |
| `T_1`, `T_2` | C620温度 |
| `limiting_active`, `torque_scaling_active` | 飽和検出 |

比較条件:

- ステア停止中
- ステア回転中
- ホイール無負荷
- ホイール接地
- 旋回中
- 急加減速

ここで、PIゲイン不足、摩擦、電流飽和、CAN遅延、機構拘束を分ける。

### Level 1: Feedforward強化

現行のステア角速度FFは維持する。

```text
omega_s_ref = Kp_theta * angle_error + omega_s_ff
```

次に、drive側の `targetWheelAccelRpmMilliPerS` を実際の電流FFへ接続する。

```text
I_d_cmd = PI_d(e_d) + I_d_ff
I_d_ff = K_a_d * domega_d_ref + K_v_d * omega_d_ref + K_c_d * softsign(omega_d_ref)
```

steer側も同じ形を候補にする。

```text
I_s_cmd = PI_s(e_s) + I_s_ff
I_s_ff = K_a_s * domega_s_ref + K_v_s * omega_s_ref + K_c_s * softsign(omega_s_ref)
```

役割分担:

```text
FF = 予測できる必要電流を先に出す
PI = 予測から外れた誤差を修正する
```

### Level 2: 摩擦補償

摩擦補償は、精密に作り込みすぎず、平均的な既知分を打ち消す程度に留める。

候補:

```text
I_fric = I_c * tanh(k * omega) + B * omega
```

または低リスクな初期形:

```text
I_fric = I_c * softsign(omega)
```

注意:

- `sgn(omega)` のみだとゼロ速度付近でチャタリングしやすい。
- 摩擦は温度、荷重、摩耗、組付けで変わる。
- 摩擦FFを過度に精密化するより、残差はDOBに任せる。

### Level 3: mode-space DOB

本命は drive mode / steer mode それぞれの外乱オブザーバ。

```text
I_d_cmd = PI_d + FF_d + Fric_d + DOB_d
I_s_cmd = PI_s + FF_s + Fric_s + DOB_s
```

簡略モデル:

```text
J * domega = Kt * I - tau_dist
tau_dist = Kt * I - J_n * domega
```

実装では、推定値をQフィルタで帯域制限する。

```text
dist_hat = Q( Kt * I_cmd - J_n * domega_measured )
I_dob = dist_hat / Kt
```

設計上の注意:

- まず補償せず、推定値をログだけ出す。
- Qフィルタ帯域を高くしすぎると速度計測ノイズを拾う。
- C620 rpm量子化、AMT22角度量子化、1kHz周期ジッタを前提にする。
- DOB出力も最終的には既存のmode電流スケーリングへ通す。

### Level 4: 状態推定

必要になったら、AMT22角度、C620 rpm、電流指令、IMU、オドメトリを組み合わせる。

候補状態:

```text
x = [ theta_s, omega_s, tau_load ]^T
```

候補:

- Kalman Filter
- ESO / LESO
- DOB推定値を含めた状態診断

目的は、AMT22角度微分ノイズ、C620 rpm量子化、負荷変動をまとめて扱うこと。

### Level 5: MPC

MPCを使うならG474ではなく、Teensyまたはmini PC側が候補。

```text
mini PC:
  trajectory planning / optional optimization

Teensy:
  body IK
  3輪同時目標
  desaturation
  steer flip
  optional simple MPC

G474 x3:
  angle control
  mode PI
  FF
  friction compensation
  DOB
  safety clamp
```

MPCが有効になる条件:

- 電流・rpm・ステア速度制約を同時に扱う必要がある。
- 3輪の過渡整合が単純なデサチュレーションでは不足する。
- モデル同定とリアルタイム計算コストを許容できる。

## `unit_controller_update()` への挿入点

現状の流れ:

```text
1. angle_error計算
2. steer rpm command生成
3. steer rpm clamp / ramp
4. wheel rpm limit / ramp
5. drive/steer mode target計算
6. motor1/motor2 target rpm計算
7. measured drive/steer mode rpm計算
8. mode rpm lowpass
9. drive/steer PIでmode current生成
10. mode current合成前の比例スケーリング
11. motor1/motor2 currentへ合成
```

追加後の流れ:

```text
mode target rpm
  -> target accel / FF入力
  -> PI_d / PI_s
  + accel FF
  + friction FF
  + DOB compensation
  -> mode current
  -> existing current scaling
  -> motor current合成
```

実装上は、`pi_update_mode()` の直後に足す。

```c
output->steer_mode_current =
    pi_update_mode(...)
    + output->steer_accel_ff_current
    + output->steer_friction_ff_current
    + output->steer_dob_current;

output->drive_mode_current =
    pi_update_mode(...)
    + output->drive_accel_ff_current
    + output->drive_friction_ff_current
    + output->drive_dob_current;
```

その後は現行と同じ。

```text
peak_motor_current = abs(I_s) + abs(I_d)
if peak > current_limit:
    I_s, I_d を同率スケール
motor1 = I_s + I_d
motor2 = I_s - I_d
```

この順番なら、FF/DOB追加後も既存の電流保護とmode比率維持が効く。

## 実装順序

1. `unit_control_output_t` に将来用のログ項目を追加する。初期値はすべて0。
   - `drive_accel_ff_current`
   - `steer_accel_ff_current`
   - `drive_friction_ff_current`
   - `steer_friction_ff_current`
   - `drive_disturbance_est_current`
   - `steer_disturbance_est_current`
   - `drive_dob_current`
   - `steer_dob_current`
2. ログだけ出して接地評価する。補償はまだ有効化しない。
3. `targetWheelAccelRpmMilliPerS` を drive accel FF へ接続する。
4. 接地・負荷ありで `K_a`, `K_v`, `K_c` を粗く同定する。
5. 摩擦FFを追加する。過補償を避ける。
6. DOB推定値をログする。
7. DOB補償を小さいゲインから有効化する。

## 重要な判断基準

高度制御が必要になる原因は「負荷が掛かるから」ではない。以下のどれかが観測された時に段階を上げる。

- 負荷変動の帯域がPIで吸収できない。
- 非線形摩擦が大きい。
- 飽和に頻繁に入る。
- drive/steerの干渉が強い。
- 3輪拘束が局所制御では解決できない。

予想される問題順:

```text
摩擦・ガタ
  -> 電流飽和
  -> 3輪間の操舵ずれ
  -> 急激な接地負荷変動
```

## 関連ドキュメント

- `docs/control/KINEMATICS_AND_RPM.md` — mode空間と差動運動学
- `docs/control/CENTRAL_COORDINATED_CONTROL.md` — Teensy側の3輪協調、FF生成、デサチュレーション
- `docs/control/CALIBRATION_AND_ADAPTATION_PLAN.md` — 接地での再特性化、LESO/LADRC候補
- `firmware/docs/CONTROL_LOOP_TUNING.md` — 現行PI制御と実験ログ
- `firmware/src/control/unit_controller.c` — 実装対象
