from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt

FIELDS = [
    "stage", "progress", "timesteps", "training_wall_time_s", "difficulty", "mean_return", "std_return",
    "mean_survival_s", "capture_rate", "mean_capture_time_s", "final_stable_rate", "stable_ratio", "goal_ratio",
    "high_ratio", "max_tip_height_m", "rms_joint_speed_rad_s", "rms_torque_nm",
]


def checkpoint_rank(record: dict) -> tuple[float, float, float, float, float]:
    return (
        float(record["final_stable_rate"]),
        float(record["capture_rate"]),
        float(record.get("stable_ratio", 0.0)),
        float(record["goal_ratio"]),
        float(record["mean_return"]),
    )


def select_best_record(records: list[dict]) -> dict:
    candidates = [record for record in records if record["stage"] not in {"random", "final_model"}]
    if not candidates:
        raise ValueError("No trained checkpoints available")
    return max(candidates, key=checkpoint_rank)


def write_metrics_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)


def _plot(records: list[dict], key: str, ylabel: str, path: Path, scale: float = 1.0) -> None:
    xs = [int(r["timesteps"]) for r in records]
    ys = [float(r[key]) * scale for r in records]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(xs, ys, marker="o")
    ax.set_xlabel("Consumed environment timesteps")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def create_plots(records: list[dict], plots_dir: Path) -> None:
    _plot(records, "mean_return", "Mean evaluation return", plots_dir / "learning_curve.png")
    _plot(records, "capture_rate", "Capture rate [%]", plots_dir / "capture_rate.png", 100.0)
    _plot(records, "final_stable_rate", "Final stable [%]", plots_dir / "final_stable_rate.png", 100.0)
    _plot(records, "stable_ratio", "Stable dwell [%]", plots_dir / "stable_ratio.png", 100.0)
    _plot(records, "goal_ratio", "Time above goal height [%]", plots_dir / "goal_ratio.png", 100.0)
    _plot(records, "rms_torque_nm", "RMS actuator torque [N m]", plots_dir / "torque.png")
    _plot(records, "training_wall_time_s", "Cumulative training wall time [s]", plots_dir / "training_time.png")
    _plot(records, "difficulty", "Curriculum difficulty", plots_dir / "difficulty.png")


def _fmt_time(value: float) -> str:
    return "-" if math.isnan(value) else f"{value:.2f}s"


def write_summary(records: list[dict], path: Path, algorithm: str, preset: str, seed: int) -> None:
    best = select_best_record(records)
    final = next((record for record in reversed(records) if record["stage"] == "final_model"), records[-1])
    lines = [
        f"# Acrobot Swing-up {algorithm.upper()} training result", "",
        f"- Preset: `{preset}`", f"- Seed: `{seed}`", f"- Best checkpoint: `{best['stage']}`",
        f"- Best difficulty: `{float(best['difficulty']):.3f}`",
        f"- Best final-stable rate: `{best['final_stable_rate']*100:.1f}%`",
        f"- Best capture rate: `{best['capture_rate']*100:.1f}%`",
        f"- Best stable dwell: `{best.get('stable_ratio', 0.0)*100:.1f}%`",
        f"- Best goal-height dwell: `{best['goal_ratio']*100:.1f}%`",
        f"- Delivered final model capture rate: `{final['capture_rate']*100:.1f}%`",
        f"- Delivered final model stable dwell: `{final.get('stable_ratio', 0.0)*100:.1f}%`",
        f"- Delivered final model difficulty: `{float(final['difficulty']):.3f}`",
        "", "## Downward-start evaluation", "",
        "| Stage | Steps | Difficulty | Train time | Return | Capture | Capture time | Final stable | Stable dwell | Goal height | RMS torque |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in records:
        lines.append(
            f"| {r['stage']} | {int(r['timesteps']):,} | {float(r['difficulty']):.3f} | "
            f"{r['training_wall_time_s']:.1f}s | {r['mean_return']:.1f} | "
            f"{r['capture_rate']*100:.1f}% | {_fmt_time(float(r['mean_capture_time_s']))} | "
            f"{r['final_stable_rate']*100:.1f}% | {r.get('stable_ratio', 0.0)*100:.1f}% | "
            f"{r['goal_ratio']*100:.1f}% | {r['rms_torque_nm']:.3f} Nm |"
        )
    lines.extend([
        "", "Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.",
        "Stable dwell is the fraction of the full episode satisfying the same height/velocity condition.",
        "Final stable requires that condition for at least 80% of the final 2 s.",
        "The `final_model` row is a fresh evaluation of the model actually saved as `models/final.zip` after any rollback.",
        "Best checkpoint is selected lexicographically by final stability, capture rate, stable dwell, goal-height dwell, then return.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
