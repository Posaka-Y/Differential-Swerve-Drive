# 動的制御 実装計画

> **ギア比訂正(2026-07-31)**: ステア経路は40:55段だけを通るため、以下の
> `STEER_RATIO`は実機検証済みの`8/11 = 0.7273`を使用する。旧値`2/11 = 0.1818`は
> 60:15ドライブ段を誤ってステア経路にも含めた値であり、使用しない。

> **位置づけの更新(2026-07-06)**: 本書の配分・優先ポリシーは**ユニット単体の保護動作**。
> 車体全体の飽和解消は中央Teensyが3輪同時のデサチュレーション(最悪モジュールに合わせた
> ツイストスケーリング)で先に行う(`CENTRAL_COORDINATED_CONTROL.md`)。1輪だけがローカルに
> 駆動を削ると車体運動の整合が崩れるため、本書のユニット内配分は通常運転では発動しない
> 想定であり、発動(`LIMITING_ACTIVE`)は設計超過のサインとして中央で監視する。

## 方針

静的配分を土台にして、操舵に使うrpm予算を定数から変数へ置き換える。

制御レイヤーは以下。

| レイヤー | 役割 |
|---|---|
| 目標生成 | 上位から駆動速度とステア目標を作る |
| 配分 | モーターrpm上限内で駆動と操舵を割り当てる |
| 逆運動学 | 駆動rpm、操舵rpmから2モーター指令を生成する |

## フェーズ0: 静的版

操舵用rpmを固定値で天引きする。

$$
n_{drive\_max} =
\left(N_{MAX} - \frac{n_{steer\_fixed}}{0.7273}\right) \times 2.909
$$

検証:

- 操舵ゼロで直進する
- 操舵固定で旋回する
- `n1`, `n2` が `N_MAX` を超えない

## フェーズ1: 動的配分

固定値 `n_steer_fixed` を、その瞬間の操舵指令 `n_steer(t)` に置き換える。

$$
n_{drive\_max}(t) =
\left(N_{MAX} - \frac{|n_{steer}(t)|}{0.7273}\right) \times 2.909
$$

```cpp
double dynamicDriveMax(double motorMaxRpm, double steerCmdRpm) {
    constexpr double DRIVE_RATIO = 2.909090909;
    constexpr double STEER_RATIO = 0.727272727;

    double steerCost = std::abs(steerCmdRpm) / STEER_RATIO;
    double driveBudget = motorMaxRpm - steerCost;
    if (driveBudget < 0.0) driveBudget = 0.0;
    return driveBudget * DRIVE_RATIO;
}
```

検証:

- 操舵ゼロ時に `N_MAX * 2.909` の駆動上限になる
- 操舵を増やすと駆動上限が下がる
- 操舵を固定すれば静的版と同じになる

## フェーズ2: 平滑化

操舵指令と駆動上限の急変を抑える。

```cpp
double rateLimit(double target, double previous, double maxRatePerSec, double dt) {
    double maxDelta = maxRatePerSec * dt;
    double delta = target - previous;
    if (delta > maxDelta) delta = maxDelta;
    if (delta < -maxDelta) delta = -maxDelta;
    return previous + delta;
}

double lowPass(double target, double previous, double tau, double dt) {
    double alpha = dt / (tau + dt);
    return previous + alpha * (target - previous);
}
```

主パラメータ:

| パラメータ | 役割 |
|---|---|
| `MAX_STEER_RATE` | 操舵rpm指令の最大変化速度 |
| `DRIVE_MAX_TAU` | 駆動上限ローパスの時定数 |

## フェーズ3: 優先ポリシー

| ポリシー | 挙動 |
|---|---|
| 操舵優先 | 操舵を守り、駆動を削る |
| 駆動優先 | 駆動を守り、操舵を削る |
| 按分 | 両方を同率で削る |

初期実装は操舵優先とする。

## フェーズ4: 可視化

`N_MAX = 469 rpm` の場合:

| n_steer | モーター換算操舵消費 | n_drive_max |
|---:|---:|---:|
| 0 rpm | 0 rpm | 1364 rpm |
| 20 rpm | 27.5 rpm | 1284 rpm |
| 40 rpm | 55 rpm | 1204 rpm |
| 60 rpm | 82.5 rpm | 1124 rpm |
| 80 rpm | 110 rpm | 1044 rpm |
| 341.1 rpm | 469 rpm | 0 rpm |

## リスク

この制御は運動学ベースで、タイヤの横滑り限界は含まない。高速旋回で滑る場合は、速度に応じた操舵rpm制限を別レイヤーで追加する。
