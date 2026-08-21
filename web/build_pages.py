from __future__ import annotations

import argparse
import csv
import html
import json
import math
import shutil
from pathlib import Path

ORDER = ["ppo", "sac", "td3"]


def discover(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for metadata_path in root.rglob("metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        algorithm = str(metadata.get("algorithm", "")).lower()
        if algorithm in ORDER and algorithm not in found:
            found[algorithm] = metadata_path.parent
    return found


def pct(value: str | float) -> str:
    return f"{float(value) * 100:.1f}%"


def capture_time(value: str | float) -> str:
    number = float(value)
    return "-" if math.isnan(number) else f"{number:.2f}s"


def difficulty_text(row: dict) -> str:
    try:
        return f"{float(row.get('difficulty', 0.0)):.3f}"
    except (TypeError, ValueError):
        return "-"


def comparison_row(algorithm: str, row: dict, train_time_s: float) -> str:
    return (
        "<tr>"
        f"<td>{algorithm.upper()}</td><td>{html.escape(str(row['stage']))}</td>"
        f"<td>{int(float(row['timesteps'])):,}</td><td>{difficulty_text(row)}</td>"
        f"<td>{pct(row['capture_rate'])}</td><td>{capture_time(row['mean_capture_time_s'])}</td>"
        f"<td>{pct(row['final_stable_rate'])}</td><td>{pct(row.get('stable_ratio', 0.0))}</td>"
        f"<td>{pct(row['goal_ratio'])}</td><td>{float(row['rms_torque_nm']):.3f} Nm</td>"
        f"<td>{train_time_s:.1f}s</td>"
        "</tr>"
    )


def build(root: Path, output: Path, run_url: str) -> None:
    sources = discover(root)
    if not sources:
        raise FileNotFoundError("No benchmark metadata.json found")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    best_rows = []
    final_rows = []
    stage_rows = []
    cards = []
    for algorithm in ORDER:
        if algorithm not in sources:
            continue
        src = sources[algorithm]
        metadata = json.loads((src / "metadata.json").read_text(encoding="utf-8"))
        rows = list(csv.DictReader((src / "metrics.csv").open(encoding="utf-8")))
        final = metadata.get("final_checkpoint") or next(
            (row for row in reversed(rows) if row.get("stage") == "final_model"), rows[-1]
        )
        best = metadata.get("best_checkpoint") or final
        dst = output / algorithm
        dst.mkdir(parents=True)
        for directory in ["videos", "plots"]:
            if (src / directory).exists():
                shutil.copytree(src / directory, dst / directory)

        best_rows.append(comparison_row(algorithm, best, float(best.get("training_wall_time_s", 0.0))))
        final_rows.append(comparison_row(algorithm, final, float(metadata.get("training_wall_time_s", 0.0))))
        for row in rows:
            stage_rows.append(
                "<tr>"
                f"<td>{algorithm.upper()}</td><td>{html.escape(row['stage'])}</td>"
                f"<td>{int(float(row['timesteps'])):,}</td><td>{difficulty_text(row)}</td>"
                f"<td>{float(row['mean_return']):.1f}</td><td>{pct(row['capture_rate'])}</td>"
                f"<td>{capture_time(row['mean_capture_time_s'])}</td><td>{pct(row['final_stable_rate'])}</td>"
                f"<td>{pct(row.get('stable_ratio', 0.0))}</td><td>{pct(row['goal_ratio'])}</td>"
                f"<td>{float(row['rms_torque_nm']):.3f}</td>"
                "</tr>"
            )
        rollback_count = int(metadata.get("rollback_count", 0))
        final_lr = metadata.get("final_learning_rate")
        recovery_text = ""
        if final_lr is not None:
            recovery_text = (
                f"<p>Rollbacks: <strong>{rollback_count}</strong> / final LR: "
                f"<strong>{float(final_lr):.3g}</strong></p>"
            )
        cards.append(
            f"<article class='card'><h2>{algorithm.upper()}</h2>"
            f"<h3>Best checkpoint</h3><video controls muted loop playsinline src='{algorithm}/videos/best.mp4'></video>"
            f"<p><strong>{html.escape(str(best['stage']))}</strong> / {int(float(best['timesteps'])):,} steps / "
            f"difficulty {difficulty_text(best)} / Capture {pct(best['capture_rate'])} / "
            f"Stable dwell {pct(best.get('stable_ratio', 0.0))}</p>"
            f"<h3>Delivered final model</h3><video controls muted loop playsinline src='{algorithm}/videos/final.mp4'></video>"
            f"<p>difficulty {difficulty_text(final)} / Capture <strong>{pct(final['capture_rate'])}</strong> / "
            f"Stable dwell <strong>{pct(final.get('stable_ratio', 0.0))}</strong> / Goal {pct(final['goal_ratio'])}</p>"
            f"{recovery_text}"
            f"<p>Total training wall time: <strong>{float(metadata.get('training_wall_time_s', 0)):.1f}s</strong></p>"
            f"<img src='{algorithm}/plots/learning_curve.png' alt='{algorithm} learning curve'>"
            f"<img src='{algorithm}/plots/stable_ratio.png' alt='{algorithm} stable dwell'>"
            f"<img src='{algorithm}/plots/difficulty.png' alt='{algorithm} curriculum difficulty'></article>"
        )

    table_head = "<thead><tr><th>Algorithm</th><th>Checkpoint</th><th>Consumed steps</th><th>Difficulty</th><th>Capture</th><th>Capture time</th><th>Final stable</th><th>Stable dwell</th><th>Goal height</th><th>RMS torque</th><th>Train time</th></tr></thead>"
    page = f"""<!doctype html><html lang='ja'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Acrobot Swing-up Benchmark</title><style>
:root{{font-family:system-ui,sans-serif;color-scheme:dark}}body{{margin:0;background:#0d1117;color:#e6edf3}}main{{max-width:1200px;margin:auto;padding:28px 18px 64px}}
.hero,.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:20px;margin:16px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}}
video,img{{width:100%;border-radius:10px;background:#000;margin-top:6px}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:8px;border-bottom:1px solid #30363d;text-align:right}}th:first-child,td:first-child{{text-align:left}}a{{color:#58a6ff}}code{{background:#21262d;padding:2px 5px;border-radius:5px}}h3{{margin-bottom:8px}}
</style></head><body><main>
<section class='hero'><h1>Continuous Acrobot Swing-up Benchmark</h1><p>同一の2リンク劣駆動系を PPO / SAC / TD3 で比較します。40秒episode、連続difficulty curriculum、best checkpoint rollbackを使用します。</p><p>v6では高位置かつ低速度を連続的に評価するstability shapingを追加し、off-policy rollbackでは同じreplayを再演せずfresh replayへ切り替えて学習率を下げます。</p><p><a href='{html.escape(run_url)}'>GitHub Actions run</a></p></section>
<section class='card'><h2>Best checkpoint 比較</h2><div style='overflow:auto'><table>{table_head}<tbody>{''.join(best_rows)}</tbody></table></div></section>
<section class='card'><h2>実際に保存された final model</h2><p>rollback後にfresh evaluationした数値です。下の動画と同じモデルを評価しています。</p><div style='overflow:auto'><table>{table_head}<tbody>{''.join(final_rows)}</tbody></table></div></section>
<section class='grid'>{''.join(cards)}</section>
<section class='card'><h2>全評価チェックポイント</h2><div style='overflow:auto'><table><thead><tr><th>Algorithm</th><th>Stage</th><th>Consumed steps</th><th>Difficulty</th><th>Return</th><th>Capture</th><th>Capture time</th><th>Final stable</th><th>Stable dwell</th><th>Goal height</th><th>RMS torque</th></tr></thead><tbody>{''.join(stage_rows)}</tbody></table></div></section>
<section class='card'><h2>評価条件</h2><p>全方式で同じ物理、reward、センサノイズ、評価seedを使用。Captureは先端高さ1.0 m以上かつ低角速度を0.5秒維持、Stable dwellはepisode全体で同条件を満たす割合、Final stableは最終2秒の80%以上で同条件を満たすことです。</p></section>
</main></body></html>"""
    (output / "index.html").write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-url", default="")
    args = parser.parse_args()
    build(args.root, args.output, args.run_url)


if __name__ == "__main__":
    main()
