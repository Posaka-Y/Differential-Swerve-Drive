# ステア・駆動 rpm 関数

## 前提

- モーター: C620系のモーター回転数を入力とする
- モーター1: `n1`
- モーター2: `n2`
- 単位: rpm
- パターン(a)で確定
- モーター側平歯車: 40T
- 中間平歯車: 55T
- 傘歯車: 60T
- ホイールピニオン: 15T

この機構では、2つのモーターの差が駆動、和が操舵に対応する。

## 1. ステア rpm

ステアrpmは、2つのモーターの平均回転に対して、平歯車段と傘歯車段の減速を掛ける。

$$
n_{steer} = \frac{n_1 + n_2}{2} \times \frac{40}{55} \times \frac{15}{60}
$$

係数を畳むと、

$$
\frac{40}{55} \times \frac{15}{60}
= \frac{600}{3300}
= 0.1818
$$

したがって、

$$
\boxed{
n_{steer} = 0.1818 \times \frac{n_1 + n_2}{2}
}
$$

または、

$$
\boxed{
n_{steer} = 0.0909 (n_1 + n_2)
}
$$

## 2. 駆動 rpm

駆動rpmは、2つのモーターの差分平均に対して、平歯車段と傘歯車段の増速を掛ける。

$$
n_{drive} = \frac{n_1 - n_2}{2} \times \frac{40}{55} \times \frac{60}{15}
$$

係数を畳むと、

$$
\frac{40}{55} \times \frac{60}{15}
= \frac{2400}{825}
= 2.909
$$

したがって、

$$
\boxed{
n_{drive} = 2.909 \times \frac{n_1 - n_2}{2}
}
$$

または、

$$
\boxed{
n_{drive} = 1.4545 (n_1 - n_2)
}
$$

この `2.909` は、駆動系で整理した全体増速比と一致する。

## 3. 順運動学

モーターrpmから、駆動rpmとステアrpmを求める関数。

```cpp
struct ModuleRpm {
    double drive;
    double steer;
};

ModuleRpm forwardKinematics(double n1, double n2) {
    constexpr double DRIVE_RATIO = 2.909090909; // (40 / 55) * (60 / 15)
    constexpr double STEER_RATIO = 0.181818182; // (40 / 55) * (15 / 60)

    ModuleRpm out;
    out.drive = DRIVE_RATIO * (n1 - n2) / 2.0;
    out.steer = STEER_RATIO * (n1 + n2) / 2.0;
    return out;
}
```

Pythonで書く場合は以下。

```python
def forward_kinematics(n1: float, n2: float) -> tuple[float, float]:
    drive_ratio = 2.909090909  # (40 / 55) * (60 / 15)
    steer_ratio = 0.181818182  # (40 / 55) * (15 / 60)

    n_drive = drive_ratio * (n1 - n2) / 2.0
    n_steer = steer_ratio * (n1 + n2) / 2.0
    return n_drive, n_steer
```

## 4. 逆運動学

制御では、目標の駆動rpmとステアrpmから、モーター1・モーター2の指令rpmを逆算する。

順方向式は、

$$
n_{drive} = 2.909 \times \frac{n_1 - n_2}{2}
$$

$$
n_{steer} = 0.1818 \times \frac{n_1 + n_2}{2}
$$

これを `n1`, `n2` について解くと、

$$
\boxed{
n_1 = \frac{n_{drive}}{2.909} + \frac{n_{steer}}{0.1818}
}
$$

$$
\boxed{
n_2 = -\frac{n_{drive}}{2.909} + \frac{n_{steer}}{0.1818}
}
$$

コード化すると以下。

```cpp
struct MotorRpm {
    double n1;
    double n2;
};

MotorRpm inverseKinematics(double nDrive, double nSteer) {
    constexpr double DRIVE_RATIO = 2.909090909; // (40 / 55) * (60 / 15)
    constexpr double STEER_RATIO = 0.181818182; // (40 / 55) * (15 / 60)

    MotorRpm out;
    out.n1 =  nDrive / DRIVE_RATIO + nSteer / STEER_RATIO;
    out.n2 = -nDrive / DRIVE_RATIO + nSteer / STEER_RATIO;
    return out;
}
```

Pythonで書く場合は以下。

```python
def inverse_kinematics(n_drive: float, n_steer: float) -> tuple[float, float]:
    drive_ratio = 2.909090909  # (40 / 55) * (60 / 15)
    steer_ratio = 0.181818182  # (40 / 55) * (15 / 60)

    n1 =  n_drive / drive_ratio + n_steer / steer_ratio
    n2 = -n_drive / drive_ratio + n_steer / steer_ratio
    return n1, n2
```

## 5. 数値例

| 操作 | n1 | n2 | n_drive | n_steer |
|---|---:|---:|---:|---:|
| 純駆動、逆転同速 | +469 | -469 | 1364 rpm | 0 rpm |
| 純操舵、同転同速 | +469 | +469 | 0 rpm | 85.3 rpm |
| 片側のみ | +469 | 0 | 682 rpm | 42.6 rpm |

純操舵時のステアrpmは約 `85.3 rpm`。

1回転にかかる時間は、

$$
\frac{60}{85.3} = 0.703 sec
$$

180度旋回にかかる時間は、

$$
0.703 \div 2 = 0.352 sec
$$

よって、定格rpmだけで見ても操舵応答は十分速い。

## 6. モーターrpm上限チェック

駆動と操舵を同時に出す場合、逆運動学で求めた `n1`, `n2` がモーター許容rpmを超えないようにする。

```cpp
double maxAbsMotorRpm(double nDrive, double nSteer) {
    MotorRpm motor = inverseKinematics(nDrive, nSteer);
    return std::max(std::abs(motor.n1), std::abs(motor.n2));
}
```

目標値が上限を超える場合は、`nDrive` と `nSteer` を同じ比率でスケールダウンする。

```cpp
MotorRpm inverseKinematicsLimited(double nDrive, double nSteer, double motorLimitRpm) {
    MotorRpm motor = inverseKinematics(nDrive, nSteer);
    double maxAbs = std::max(std::abs(motor.n1), std::abs(motor.n2));

    if (maxAbs <= motorLimitRpm) {
        return motor;
    }

    double scale = motorLimitRpm / maxAbs;
    return inverseKinematics(nDrive * scale, nSteer * scale);
}
```

この制限を入れると、駆動と操舵を同時に指令したときも、モーターrpmの上限内で同じ駆動・操舵比率を保てる。

## 7. 要約

| 項目 | 式 |
|---|---|
| ステアrpm | `n_steer = 0.0909 * (n1 + n2)` |
| 駆動rpm | `n_drive = 1.4545 * (n1 - n2)` |
| モーター1指令 | `n1 = n_drive / 2.909 + n_steer / 0.1818` |
| モーター2指令 | `n2 = -n_drive / 2.909 + n_steer / 0.1818` |

