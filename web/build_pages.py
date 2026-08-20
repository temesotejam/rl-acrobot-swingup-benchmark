from __future__ import annotations

import argparse
import csv
import html
import json
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


def build(root: Path, output: Path, run_url: str) -> None:
    sources = discover(root)
    if not sources:
        raise FileNotFoundError("No benchmark metadata.json found")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    final_rows = []
    stage_rows = []
    cards = []
    for algorithm in ORDER:
        if algorithm not in sources:
            continue
        src = sources[algorithm]
        metadata = json.loads((src / "metadata.json").read_text(encoding="utf-8"))
        rows = list(csv.DictReader((src / "metrics.csv").open(encoding="utf-8")))
        final = rows[-1]
        dst = output / algorithm
        dst.mkdir(parents=True)
        for directory in ["videos", "plots"]:
            if (src / directory).exists():
                shutil.copytree(src / directory, dst / directory)
        final_rows.append(
            "<tr>"
            f"<td>{algorithm.upper()}</td><td>{int(float(final['timesteps'])):,}</td>"
            f"<td>{pct(final['capture_rate'])}</td><td>{float(final['mean_capture_time_s']):.2f}s</td>"
            f"<td>{pct(final['final_stable_rate'])}</td><td>{pct(final['goal_ratio'])}</td>"
            f"<td>{float(final['rms_torque_nm']):.3f} Nm</td><td>{float(metadata.get('training_wall_time_s', 0)):.1f}s</td>"
            "</tr>"
        )
        for row in rows:
            capture = row["mean_capture_time_s"]
            capture_text = "-" if capture.lower() == "nan" else f"{float(capture):.2f}s"
            stage_rows.append(
                "<tr>"
                f"<td>{algorithm.upper()}</td><td>{html.escape(row['stage'])}</td><td>{int(float(row['timesteps'])):,}</td>"
                f"<td>{float(row['mean_return']):.1f}</td><td>{pct(row['capture_rate'])}</td><td>{capture_text}</td>"
                f"<td>{pct(row['final_stable_rate'])}</td><td>{pct(row['goal_ratio'])}</td><td>{float(row['rms_torque_nm']):.3f}</td>"
                "</tr>"
            )
        cards.append(
            f"<article class='card'><h2>{algorithm.upper()}</h2>"
            f"<video controls muted loop playsinline src='{algorithm}/videos/04_100_percent.mp4'></video>"
            f"<p>Training wall time: <strong>{float(metadata.get('training_wall_time_s', 0)):.1f}s</strong></p>"
            f"<img src='{algorithm}/plots/learning_curve.png' alt='{algorithm} learning curve'></article>"
        )

    page = f"""<!doctype html><html lang='ja'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Acrobot Swing-up Benchmark</title><style>
:root{{font-family:system-ui,sans-serif;color-scheme:dark}}body{{margin:0;background:#0d1117;color:#e6edf3}}main{{max-width:1200px;margin:auto;padding:28px 18px 64px}}
.hero,.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:20px;margin:16px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}}
video,img{{width:100%;border-radius:10px;background:#000}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:8px;border-bottom:1px solid #30363d;text-align:right}}th:first-child,td:first-child{{text-align:left}}a{{color:#58a6ff}}code{{background:#21262d;padding:2px 5px;border-radius:5px}}
</style></head><body><main>
<section class='hero'><h1>Continuous Acrobot Swing-up Benchmark</h1><p>同一の2リンク劣駆動系を PPO / SAC / TD3 で比較します。肩は非駆動、肘だけが連続トルク入力です。</p><p><a href='{html.escape(run_url)}'>GitHub Actions run</a></p></section>
<section class='card'><h2>最終比較</h2><div style='overflow:auto'><table><thead><tr><th>Algorithm</th><th>Steps</th><th>Capture</th><th>Capture time</th><th>Final stable</th><th>Goal height</th><th>RMS torque</th><th>Train time</th></tr></thead><tbody>{''.join(final_rows)}</tbody></table></div></section>
<section class='grid'>{''.join(cards)}</section>
<section class='card'><h2>全チェックポイント</h2><div style='overflow:auto'><table><thead><tr><th>Algorithm</th><th>Stage</th><th>Steps</th><th>Return</th><th>Capture</th><th>Capture time</th><th>Final stable</th><th>Goal height</th><th>RMS torque</th></tr></thead><tbody>{''.join(stage_rows)}</tbody></table></div></section>
<section class='card'><h2>評価条件</h2><p>全方式で同じ物理、reward、センサノイズ、カリキュラム、評価seedを使用。Captureは先端高さ1.0 m以上かつ低角速度を0.5秒維持、Final stableは最終2秒の80%以上で同条件を満たすことです。</p></section>
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
