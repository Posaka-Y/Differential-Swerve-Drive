#!/usr/bin/env python3
"""Analyze ESP32 radio telemetry and emit tracking metrics plus a plot."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import statistics
import sys
from typing import Iterable


@dataclass(frozen=True)
class Sample:
    ms: int
    bt: int
    armed: int
    enable: int
    unit_active: int
    target_steer_mdeg: int
    actual_steer_mdeg: int
    steer_error_mdeg: int
    target_wheel_mrpm: int
    actual_wheel_mrpm: int
    wheel_error_mrpm: int
    rpm_limit: int
    controller_age_ms: int
    unit_age_ms: int
    uart_rx_frames: int
    uart_rx_bad: int
    uart_rx_gaps: int
    uart_tx_fail: int


def percentile(values: Iterable[float], percent: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = (len(ordered) - 1) * percent / 100.0
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def counter_delta(samples: list[Sample], field: str) -> int:
    if len(samples) < 2:
        return 0
    return max(0, getattr(samples[-1], field) - getattr(samples[0], field))


def angle_delta_mdeg(target: int, previous: int) -> int:
    delta = (target - previous) % 360000
    return delta - 360000 if delta > 180000 else delta


def read_samples(path: Path) -> list[Sample]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        missing = [name for name in Sample.__dataclass_fields__ if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"missing CSV fields: {', '.join(missing)}")
        return [
            Sample(**{name: int(row[name]) for name in Sample.__dataclass_fields__})
            for row in reader
        ]


def find_steady_samples(samples: list[Sample]) -> list[Sample]:
    steady: list[Sample] = []
    last_change_ms = samples[0].ms if samples else 0
    previous: Sample | None = None
    for sample in samples:
        if previous is None or (
            abs(angle_delta_mdeg(
                sample.target_steer_mdeg, previous.target_steer_mdeg
            )) > 1000
            or abs(sample.target_wheel_mrpm - previous.target_wheel_mrpm) > 10000
            or sample.enable != previous.enable
        ):
            last_change_ms = sample.ms
        if (
            sample.enable
            and sample.unit_active
            and 0 <= sample.unit_age_ms <= 250
            and sample.ms - last_change_ms >= 500
        ):
            steady.append(sample)
        previous = sample
    return steady


def find_stop_latencies(samples: list[Sample]) -> list[float]:
    latencies: list[float] = []
    for index in range(1, len(samples)):
        if (
            samples[index - 1].enable != 1
            or samples[index - 1].unit_active != 1
            or samples[index].enable != 0
        ):
            continue
        start_ms = samples[index].ms
        for stopped in samples[index:]:
            if stopped.ms - start_ms > 2000:
                break
            if abs(stopped.actual_wheel_mrpm) <= 30000 and not stopped.unit_active:
                latencies.append((stopped.ms - start_ms) / 1000.0)
                break
    return latencies


def signed_degrees(mdeg: int) -> float:
    degrees = (mdeg / 1000.0) % 360.0
    return degrees - 360.0 if degrees > 180.0 else degrees


def make_plot(samples: list[Sample], output: Path) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    start = samples[0].ms
    time_s = [(sample.ms - start) / 1000.0 for sample in samples]
    target_steer = [signed_degrees(sample.target_steer_mdeg) for sample in samples]
    actual_steer = [signed_degrees(sample.actual_steer_mdeg) for sample in samples]
    target_wheel = [sample.target_wheel_mrpm / 1000.0 for sample in samples]
    actual_wheel = [sample.actual_wheel_mrpm / 1000.0 for sample in samples]

    figure, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    axes[0].plot(time_s, target_steer, label="target", linewidth=1.2)
    axes[0].plot(time_s, actual_steer, label="actual", linewidth=1.0)
    axes[0].set_ylabel("steer [deg]")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    axes[1].plot(time_s, target_wheel, label="target", linewidth=1.2)
    axes[1].plot(time_s, actual_wheel, label="actual", linewidth=1.0)
    axes[1].set_ylabel("wheel [rpm]")
    axes[1].set_xlabel("time [s]")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze DSD radio telemetry CSV.")
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    path = args.csv.resolve()

    try:
        samples = read_samples(path)
    except (OSError, ValueError) as exc:
        print(f"analyze: {exc}", file=sys.stderr)
        return 2
    if len(samples) < 2:
        print("analyze: at least two samples are required", file=sys.stderr)
        return 3

    valid = [sample for sample in samples if 0 <= sample.unit_age_ms <= 250]
    commanded = [sample for sample in valid if sample.enable]
    active = [sample for sample in valid if sample.enable and sample.unit_active]
    rejected = [sample for sample in valid if sample.enable and not sample.unit_active]
    steady = find_steady_samples(valid)
    stop_latencies = find_stop_latencies(samples)
    sample_periods = [
        (samples[index].ms - samples[index - 1].ms) / 1000.0
        for index in range(1, len(samples))
        if 0 < samples[index].ms - samples[index - 1].ms < 1000
    ]

    active_steer_error = [abs(sample.steer_error_mdeg) / 1000.0 for sample in active]
    active_wheel_error = [abs(sample.wheel_error_mrpm) / 1000.0 for sample in active]
    steady_steer_error = [abs(sample.steer_error_mdeg) / 1000.0 for sample in steady]
    steady_wheel_error = [abs(sample.wheel_error_mrpm) / 1000.0 for sample in steady]
    steady_wheel_relative = [
        abs(sample.wheel_error_mrpm) / abs(sample.target_wheel_mrpm) * 100.0
        for sample in steady
        if abs(sample.target_wheel_mrpm) >= 75000
    ]

    duration_s = (samples[-1].ms - samples[0].ms) / 1000.0
    sample_hz = 1.0 / statistics.median(sample_periods) if sample_periods else 0.0
    rx_bad = counter_delta(samples, "uart_rx_bad")
    rx_gaps = counter_delta(samples, "uart_rx_gaps")
    tx_fail = counter_delta(samples, "uart_tx_fail")

    suggestions: list[str] = []
    if not commanded:
        suggestions.append("有効走行サンプルがない。OPTIONSでarm後、R1を保持した操作を記録する。")
    elif not active:
        suggestions.append(
            "ESPはenableを指令したがNUCLEOのunit_activeが一度も成立していない。"
            "NUCLEO VCPのSTOP理由、C620/AMT feedback freshness、再armラッチを確認する。"
        )
    elif rejected:
        rejected_ratio = len(rejected) / len(commanded) * 100.0
        if rejected_ratio > 5.0:
            suggestions.append(
                f"enable指令中のunit inactive率が{rejected_ratio:.1f}%ある。"
                "NUCLEOの停止イベントと時刻を突き合わせる。"
            )
    if rx_bad or rx_gaps or tx_fail:
        suggestions.append(
            f"UART品質を先に確認する（bad={rx_bad}, gap={rx_gaps}, txFail={tx_fail}）。"
        )
    if steady_steer_error and percentile(steady_steer_error, 95) > 2.0:
        suggestions.append("定常ステア誤差p95が2°超。外側角度P、摩擦補償、機械バックラッシュを確認する。")
    if steady_wheel_relative and percentile(steady_wheel_relative, 95) > 5.0:
        suggestions.append("定常ホイール速度誤差p95が5%超。drive PIと摩擦補償を速度帯別に確認する。")
    if stop_latencies and max(stop_latencies) > 0.30:
        suggestions.append("R1解除後の停止が300ms超。disable経路と減速率を分けて確認する。")
    if active and not steady:
        suggestions.append("入力静止区間が不足。スティックを各位置で0.5秒以上保持する試験を追加する。")
    if not suggestions:
        suggestions.append("今回の閾値では明確な追従・通信問題なし。次は速度帯別/接地負荷で比較する。")

    report = path.with_suffix(".summary.md")
    plot = path.with_suffix(".png")
    plot_created = make_plot(samples, plot)

    def metric(values: list[float], percent: float) -> str:
        return f"{percentile(values, percent):.3f}" if values else "n/a"

    lines = [
        f"# Radio telemetry summary: {path.name}",
        "",
        f"- Duration: {duration_s:.2f} s",
        f"- Samples: {len(samples)} ({sample_hz:.1f} Hz median)",
        f"- Valid status samples: {len(valid)}",
        f"- Enable-commanded samples: {len(commanded)}",
        f"- Active samples: {len(active)}",
        f"- Enable-commanded but inactive samples: {len(rejected)}",
        f"- Steady samples (target held >=0.5 s): {len(steady)}",
        f"- UART deltas: bad={rx_bad}, gaps={rx_gaps}, txFail={tx_fail}",
        "",
        "## Tracking metrics",
        "",
        f"- Active steer |error|: p50={metric(active_steer_error, 50)}°, "
        f"p95={metric(active_steer_error, 95)}°, max={metric(active_steer_error, 100)}°",
        f"- Steady steer |error|: p50={metric(steady_steer_error, 50)}°, "
        f"p95={metric(steady_steer_error, 95)}°, max={metric(steady_steer_error, 100)}°",
        f"- Active wheel |error|: p50={metric(active_wheel_error, 50)} rpm, "
        f"p95={metric(active_wheel_error, 95)} rpm, max={metric(active_wheel_error, 100)} rpm",
        f"- Steady wheel |error|: p50={metric(steady_wheel_error, 50)} rpm, "
        f"p95={metric(steady_wheel_error, 95)} rpm, max={metric(steady_wheel_error, 100)} rpm",
        f"- Steady wheel relative |error|: p95={metric(steady_wheel_relative, 95)}%",
        f"- R1 release stop latency: p50={metric(stop_latencies, 50)} s, "
        f"max={metric(stop_latencies, 100)} s",
        "",
        "## Suggested next checks",
        "",
    ]
    lines.extend(f"- {suggestion}" for suggestion in suggestions)
    if plot_created:
        lines.extend(["", f"![target vs actual]({plot.name})"])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines[:-2] if plot_created else lines))
    print(f"analyze: report={report}")
    if plot_created:
        print(f"analyze: plot={plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
