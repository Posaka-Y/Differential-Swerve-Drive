# ギア比・rpm・トルク・運動学

## 前提

- モーター: C620 / M3508前提
- モーター1回転数: `n1`(M3508内蔵19:1減速機の出力軸rpm)
- モーター2回転数: `n2`(M3508内蔵19:1減速機の出力軸rpm)
- 単位: rpm
- 平歯車段: 40T -> 55T
- 傘歯車段: 60T -> 15T
- 操舵はパターン(a)で確定

> C620のCAN `feedback.rpm`は減速機より前のロータrpm。ここで使う`n1`/`n2`へ変換する際は
> 必ず`feedback.rpm / 19.0`とする。469rpmは減速後出力軸の定格値であり、raw値と直接比較しない。

## 駆動ギア比

平歯車段:

$$
\frac{40}{55} = 0.727
$$

傘歯車段:

$$
\frac{60}{15} = 4.0
$$

全体:

$$
0.727 \times 4.0 = 2.909
$$

したがって、駆動出力は **2.909倍増速**。

## 駆動rpm

定格:

$$
469 \times 2.909 = 1364 rpm
$$

空載:

$$
482 \times 2.909 = 1402 rpm
$$

## 駆動トルク

増速比の逆数でトルクは低下する。

モーター単体:

$$
3 \div 2.909 = 1.031 N \cdot m
$$

ユニット2基分:

$$
1.031 \times 2 = 2.063 N \cdot m
$$

ギア効率0.8込み:

$$
2.063 \times 0.8 = 1.65 N \cdot m
$$

拘束トルク4.5N m基準:

$$
4.5 \div 2.909 \times 2 \times 0.8 = 2.48 N \cdot m
$$

## ステアrpm

> **訂正(2026-07-08)**: 旧版はステア経路に60:15段(×15/60)を含めていたが、これは誤り。
> 60:15ベベル段は差動キャリアより先のドライブ経路のみに存在し、ステア軸はモーターから
> 40:55段までで決まる。実機検証: AMT絶対角でステア軸30°/s(=5rpm)回頭中、
> モーター実測から`(n1+n2)/2×40/55`=軸rpmが0.4%以内で一致(旧係数だと4.00倍ズレる)。

$$
n_{steer} = \frac{n_1 + n_2}{2} \times \frac{40}{55}
$$

係数:

$$
\frac{40}{55} = 0.7273
$$

したがって、

$$
n_{steer} = 0.7273 \times \frac{n_1 + n_2}{2}
$$

または、

$$
n_{steer} = 0.3636(n_1 + n_2)
$$

## 駆動rpmの差動式

$$
n_{drive} = \frac{n_1 - n_2}{2} \times \frac{40}{55} \times \frac{60}{15}
$$

係数:

$$
\frac{40}{55} \times \frac{60}{15} = 2.909
$$

したがって、

$$
n_{drive} = 2.909 \times \frac{n_1 - n_2}{2}
$$

または、

$$
n_{drive} = 1.4545(n_1 - n_2)
$$

## 順運動学

$$
n_{drive} = 1.4545(n_1 - n_2)
$$

$$
n_{steer} = 0.3636(n_1 + n_2)
$$

```cpp
struct ModuleRpm {
    double drive;
    double steer;
};

ModuleRpm forwardKinematics(double n1, double n2) {
    constexpr double DRIVE_RATIO = 2.909090909;
    constexpr double STEER_RATIO = 0.727272727;  // 40/55 (2026-07-08訂正)

    return {
        DRIVE_RATIO * (n1 - n2) / 2.0,
        STEER_RATIO * (n1 + n2) / 2.0
    };
}
```

## 逆運動学

$$
n_1 = \frac{n_{drive}}{2.909} + \frac{n_{steer}}{0.7273}
$$

$$
n_2 = -\frac{n_{drive}}{2.909} + \frac{n_{steer}}{0.7273}
$$

```cpp
struct MotorRpm {
    double n1;
    double n2;
};

MotorRpm inverseKinematics(double nDrive, double nSteer) {
    constexpr double DRIVE_RATIO = 2.909090909;
    constexpr double STEER_RATIO = 0.727272727;  // 40/55 (2026-07-08訂正)

    return {
        nDrive / DRIVE_RATIO + nSteer / STEER_RATIO,
       -nDrive / DRIVE_RATIO + nSteer / STEER_RATIO
    };
}
```

## 数値例

| 操作 | n1 | n2 | n_drive | n_steer |
|---|---:|---:|---:|---:|
| 純駆動 | +469 | -469 | 1364 rpm | 0 rpm |
| 純操舵 | +469 | +469 | 0 rpm | 341.1 rpm |
| 片側のみ | +469 | 0 | 682 rpm | 170.5 rpm |

純操舵時の341.1rpm(理論上限)は1回転あたり約0.18秒。実運用ではsteer_max_rpmで
大幅に絞る(2026-07-08時点の既定40rpm=240°/s)。
