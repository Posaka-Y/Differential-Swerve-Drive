# 動的制御 実装プラン

## 方針

動的制御は、静的制御を土台にして段階的に変数化する。

静的制御は動的制御の特殊ケースなので、逆運動学と基本の配分構造は共通化する。変更する中心は、配分レイヤーの「操舵用に天引きするrpm量」を定数から変数にすること。

制御は以下の3レイヤーに分ける。

| レイヤー | 役割 |
|---|---|
| 目標生成 | 速度目標、操舵速度目標を作る |
| 配分 | モーターrpm上限内で駆動と操舵を配分する |
| 逆運動学 | 駆動rpm、操舵rpmからモーターrpmを求める |

最初に完成させるのは逆運動学と静的配分。そこから動的配分、平滑化、優先ポリシー、可視化の順に進める。

## 確定済みの運動学

### 順運動学

モーターrpmから、駆動rpmとステアrpmを求める。

$$
n_{drive} = 1.4545 (n_1 - n_2)
$$

$$
n_{steer} = 0.0909 (n_1 + n_2)
$$

### 逆運動学

駆動rpmとステアrpmから、モーターrpmを求める。

$$
n_1 = \frac{n_{drive}}{2.909} + \frac{n_{steer}}{0.1818}
$$

$$
n_2 = -\frac{n_{drive}}{2.909} + \frac{n_{steer}}{0.1818}
$$

## フェーズ0: 静的版を完成させる

まず、逆運動学と静的配分を実装して、動く基準点を作る。

静的配分では、操舵用rpmを固定値として先に天引きする。

$$
n_{drive\_max}
= \left(N_{MAX} - \frac{n_{steer\_fixed}}{0.1818}\right) \times 2.909
$$

ここで、

- `N_MAX`: モーターrpm上限
- `n_steer_fixed`: 固定で確保する操舵rpm
- `n_drive_max`: その条件で使える最大駆動rpm

### 実装イメージ

```cpp
struct MotorRpm {
    double n1;
    double n2;
};

struct ModuleRpm {
    double drive;
    double steer;
};

constexpr double DRIVE_RATIO = 2.909090909;
constexpr double STEER_RATIO = 0.181818182;

double clamp(double x, double minValue, double maxValue) {
    if (x < minValue) return minValue;
    if (x > maxValue) return maxValue;
    return x;
}

MotorRpm inverseKinematics(double nDrive, double nSteer) {
    MotorRpm out;
    out.n1 =  nDrive / DRIVE_RATIO + nSteer / STEER_RATIO;
    out.n2 = -nDrive / DRIVE_RATIO + nSteer / STEER_RATIO;
    return out;
}

double staticDriveMax(double motorMaxRpm, double steerFixedRpm) {
    double steerCost = std::abs(steerFixedRpm) / STEER_RATIO;
    double driveBudget = motorMaxRpm - steerCost;
    if (driveBudget < 0.0) driveBudget = 0.0;
    return driveBudget * DRIVE_RATIO;
}
```

### 検証

- 操舵ゼロで直進できる
- 操舵固定で旋回できる
- `n1`, `n2` が `N_MAX` を超えない
- 飽和時の挙動がログで追える

## フェーズ1: 天引きを変数化する

静的配分の `n_steer_fixed` を、その瞬間の操舵指令 `n_steer_cmd(t)` に置き換える。

$$
n_{drive\_max}(t)
= \left(N_{MAX} - \frac{|n_{steer}(t)|}{0.1818}\right) \times 2.909
$$

絶対値を取るのは、左右どちらの操舵でもモーターrpm予算の消費量は同じだから。

### 実装イメージ

```cpp
double dynamicDriveMax(double motorMaxRpm, double steerCmdRpm) {
    double steerCost = std::abs(steerCmdRpm) / STEER_RATIO;
    double driveBudget = motorMaxRpm - steerCost;
    if (driveBudget < 0.0) driveBudget = 0.0;
    return driveBudget * DRIVE_RATIO;
}

MotorRpm commandSteerPriority(
    double driveCmdRpm,
    double steerCmdRpm,
    double motorMaxRpm
) {
    double driveMaxRpm = dynamicDriveMax(motorMaxRpm, steerCmdRpm);
    double limitedDrive = clamp(driveCmdRpm, -driveMaxRpm, driveMaxRpm);
    return inverseKinematics(limitedDrive, steerCmdRpm);
}
```

### 検証

- 操舵ゼロ時に `n_drive_max = N_MAX * 2.909`
- `N_MAX = 469 rpm` なら、操舵ゼロ時の駆動上限は約 `1364 rpm`
- 操舵を増やすと駆動上限が下がる
- 操舵を固定値にすればフェーズ0と同じ結果になる

この時点で、直進時は最高速、操舵時は駆動を削ってモーター上限内に収める挙動になる。

## フェーズ2: 平滑化を入れる

フェーズ1のままだと、操舵指令が急変したときに `drive_budget` も急変する。これにより、駆動rpmが段差状に落ちる可能性がある。

対策は2つ。

| 処理 | 目的 |
|---|---|
| 操舵指令のレートリミット | 急操舵を抑える |
| 駆動上限のローパス | 駆動上限の急変を抑える |

### レートリミット

```cpp
double rateLimit(double target, double previous, double maxRatePerSec, double dt) {
    double maxDelta = maxRatePerSec * dt;
    double delta = target - previous;
    return previous + clamp(delta, -maxDelta, maxDelta);
}
```

### ローパス

```cpp
double lowPass(double target, double previous, double tau, double dt) {
    double alpha = dt / (tau + dt);
    return previous + alpha * (target - previous);
}
```

### 動的配分への組み込み

```cpp
struct DynamicControlState {
    double steerCmdPrev = 0.0;
    double driveMaxPrev = 0.0;
};

MotorRpm commandSteerPrioritySmoothed(
    double driveCmdRpm,
    double steerCmdRawRpm,
    double motorMaxRpm,
    double maxSteerRateRpmPerSec,
    double driveMaxTau,
    double dt,
    DynamicControlState& state
) {
    double steerCmd = rateLimit(
        steerCmdRawRpm,
        state.steerCmdPrev,
        maxSteerRateRpmPerSec,
        dt
    );

    double driveMaxRaw = dynamicDriveMax(motorMaxRpm, steerCmd);
    double driveMax = lowPass(driveMaxRaw, state.driveMaxPrev, driveMaxTau, dt);

    double limitedDrive = clamp(driveCmdRpm, -driveMax, driveMax);
    MotorRpm motor = inverseKinematics(limitedDrive, steerCmd);

    state.steerCmdPrev = steerCmd;
    state.driveMaxPrev = driveMax;

    return motor;
}
```

### 検証

- 高速直進中に急操舵を入れても駆動上限が階段状に落ちない
- `n_drive_max` が振動しない
- `MAX_STEER_RATE` を上げると操舵応答が速くなる
- `TAU` を上げると駆動上限の変化がなだらかになる

主要チューニングパラメータは以下。

| パラメータ | 役割 |
|---|---|
| `MAX_STEER_RATE` | 操舵rpm指令の最大変化速度 |
| `TAU` | 駆動上限ローパスの時定数 |

## フェーズ3: 優先ポリシーを確定する

駆動と操舵が同時に大きなrpmを要求したとき、モーター上限を超えないようにどちらかを削る必要がある。

候補は3つ。

| ポリシー | 挙動 | 向いている場面 |
|---|---|---|
| 操舵優先 | 操舵を守り、駆動を削る | 機動性重視 |
| 駆動優先 | 駆動を守り、操舵を削る | 速度維持重視 |
| 按分 | 両方を同率で削る | 操作感の一貫性重視 |

差動ステアの強みを活かすなら、まずは操舵優先が自然。

フェーズ1、フェーズ2の実装は操舵優先になっている。

## フェーズ4: 可視化と調整

操舵rpmに対して、使用可能な駆動rpmがどう減るかをグラフ化する。

式は、

$$
n_{drive\_max}
= \left(N_{MAX} - \frac{|n_{steer}|}{0.1818}\right) \times 2.909
$$

`N_MAX = 469 rpm` の場合、代表値は以下。

| n_steer | モーター換算操舵消費 | n_drive_max |
|---:|---:|---:|
| 0 rpm | 0 rpm | 1364 rpm |
| 20 rpm | 110 rpm | 1044 rpm |
| 40 rpm | 220 rpm | 724 rpm |
| 60 rpm | 330 rpm | 404 rpm |
| 80 rpm | 440 rpm | 84 rpm |
| 85.3 rpm | 469 rpm | 0 rpm |

純操舵の最大値は約 `85.3 rpm`。このときモーターrpm予算をすべて操舵に使うため、駆動rpmはゼロになる。

## リスク

この制御は運動学ベースであり、タイヤのグリップ限界はまだ入っていない。

高速旋回で横滑りが出る場合は、速度に応じて操舵rpmを制限する別レイヤーが必要になる。

例:

```cpp
double limitSteerByDriveSpeed(double steerCmdRpm, double driveRpm) {
    // TODO: 実機ログから速度別の操舵上限を決める。
    return steerCmdRpm;
}
```

フェーズ4まで終えて実機ログを取ってから、速度依存の操舵制限を追加する。

## 実装順序

| フェーズ | 作業 | 主パラメータ | 検証 |
|---|---|---|---|
| 0 | 逆運動学と静的配分 | `N_MAX`, `n_steer_fixed` | 飽和が起きない |
| 1 | 天引き量の変数化 | なし | 操舵ゼロでフル速度 |
| 2 | 平滑化 | `MAX_STEER_RATE`, `TAU` | 過渡が滑らか |
| 3 | 優先ポリシー確定 | 配分順序 | 操作思想と一致 |
| 4 | 可視化と調整 | `N_MAX` マージン | トレードオフ把握 |

## 最終的な制御ループ

```cpp
// 1. 上位制御から目標値を受け取る
double driveCmdRpm = targetDriveRpm;
double steerCmdRpm = targetSteerRpm;

// 2. 必要なら速度依存の操舵制限をかける
steerCmdRpm = limitSteerByDriveSpeed(steerCmdRpm, driveCmdRpm);

// 3. 操舵優先の動的配分を行う
MotorRpm motor = commandSteerPrioritySmoothed(
    driveCmdRpm,
    steerCmdRpm,
    N_MAX,
    MAX_STEER_RATE,
    DRIVE_MAX_TAU,
    dt,
    state
);

// 4. 最終安全確認
motor.n1 = clamp(motor.n1, -N_MAX, N_MAX);
motor.n2 = clamp(motor.n2, -N_MAX, N_MAX);

// 5. モーターへ指令
setMotorRpm(1, motor.n1);
setMotorRpm(2, motor.n2);
```

