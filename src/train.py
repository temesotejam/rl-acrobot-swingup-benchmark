from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import random
import shutil
import time
from pathlib import Path

import numpy as np
import torch
import yaml
from stable_baselines3 import PPO, SAC, TD3
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.noise import NormalActionNoise

from .curriculum import make_training_env
from .environment import PhysicsConfig, SensorNoiseConfig
from .evaluation import evaluate_episode, evaluate_policy
from .reporting import checkpoint_rank, create_plots, select_best_record, write_metrics_csv, write_summary

REPO_ROOT = Path(__file__).resolve().parents[1]
ALGORITHMS = {"ppo", "sac", "td3"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train PPO/SAC/TD3 on continuous Acrobot swing-up.")
    parser.add_argument("--algorithm", choices=sorted(ALGORITHMS), required=True)
    parser.add_argument("--preset", choices=["quick", "normal", "long"], default="normal")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    return parser.parse_args()


def load_configs() -> tuple[dict, dict]:
    benchmark = yaml.safe_load((REPO_ROOT / "configs" / "benchmark.yaml").read_text(encoding="utf-8"))
    algorithms = yaml.safe_load((REPO_ROOT / "configs" / "algorithms.yaml").read_text(encoding="utf-8"))
    return benchmark, algorithms


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(2)


def version_info() -> dict[str, str]:
    return {name: importlib.metadata.version(name) for name in ["gymnasium", "stable-baselines3", "torch", "numpy"]}


def record_stage(
    records: list[dict],
    stage: str,
    progress: float,
    timesteps: int,
    training_wall_time_s: float,
    policy,
    evaluation_seeds: list[int],
    video_seed: int,
    videos_dir: Path,
    video_index: int,
    physics: PhysicsConfig,
    noise: SensorNoiseConfig,
) -> dict:
    metrics = evaluate_policy(policy, evaluation_seeds, physics=physics, sensor_noise=noise)
    evaluate_episode(policy, video_seed, physics, noise, videos_dir / f"{video_index:02d}_{stage}.mp4")
    record = {
        "stage": stage,
        "progress": progress,
        "timesteps": timesteps,
        "training_wall_time_s": training_wall_time_s,
        **metrics.to_dict(),
    }
    records.append(record)
    capture_t = "-" if math.isnan(metrics.mean_capture_time_s) else f"{metrics.mean_capture_time_s:.2f}s"
    print(
        f"[{stage}] steps={timesteps:,} return={metrics.mean_return:.1f} "
        f"capture={metrics.capture_rate*100:.1f}% capture_t={capture_t} "
        f"final_stable={metrics.final_stable_rate*100:.1f}% train_wall={training_wall_time_s:.1f}s"
    )
    return record


def make_model(
    algorithm: str,
    preset: str,
    config: dict,
    physics: PhysicsConfig,
    noise: SensorNoiseConfig,
    seed: int,
):
    cfg = config[algorithm]
    if algorithm == "ppo":
        n_envs = int(cfg["n_envs"])
        train_env = make_vec_env(
            lambda: make_training_env(physics=physics, sensor_noise=noise, reset_mode="near_upright"),
            n_envs=n_envs,
            seed=seed,
        )
        n_steps = int(cfg["n_steps_quick"] if preset == "quick" else cfg["n_steps"])
        batch_size = int(cfg["batch_size_quick"] if preset == "quick" else cfg["batch_size"])
        model = PPO(
            "MlpPolicy",
            train_env,
            learning_rate=float(cfg["learning_rate"]),
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=int(cfg["n_epochs"]),
            gamma=float(cfg["gamma"]),
            gae_lambda=float(cfg["gae_lambda"]),
            clip_range=float(cfg["clip_range"]),
            ent_coef=float(cfg["ent_coef"]),
            use_sde=bool(cfg["use_sde"]),
            sde_sample_freq=int(cfg["sde_sample_freq"]),
            policy_kwargs={"net_arch": [int(v) for v in cfg["net_arch"]]},
            seed=seed,
            device="cpu",
            verbose=1,
        )
        return model

    train_env = make_training_env(physics=physics, sensor_noise=noise, reset_mode="near_upright")
    common = dict(
        learning_rate=float(cfg["learning_rate"]),
        buffer_size=int(cfg["buffer_size"]),
        learning_starts=int(cfg["learning_starts"]),
        batch_size=int(cfg["batch_size"]),
        tau=float(cfg["tau"]),
        gamma=float(cfg["gamma"]),
        train_freq=int(cfg["train_freq"]),
        gradient_steps=int(cfg["gradient_steps"]),
        policy_kwargs={"net_arch": [int(v) for v in cfg["net_arch"]]},
        seed=seed,
        device="cpu",
        verbose=1,
    )
    if algorithm == "sac":
        return SAC(
            "MlpPolicy",
            train_env,
            ent_coef=str(cfg["ent_coef"]),
            target_update_interval=int(cfg["target_update_interval"]),
            **common,
        )

    sigma = float(cfg["action_noise_sigma"])
    action_noise = NormalActionNoise(mean=np.zeros(1), sigma=sigma * np.ones(1))
    return TD3(
        "MlpPolicy",
        train_env,
        action_noise=action_noise,
        policy_delay=int(cfg["policy_delay"]),
        target_policy_noise=float(cfg["target_policy_noise"]),
        target_noise_clip=float(cfg["target_noise_clip"]),
        **common,
    )


def main() -> None:
    args = parse_args()
    benchmark, algorithm_configs = load_configs()
    set_global_seed(args.seed)
    preset_cfg = benchmark["presets"][args.preset]
    physics = PhysicsConfig(**benchmark["physics"])
    noise = SensorNoiseConfig(**benchmark["sensor_noise"])
    total_timesteps = int(preset_cfg["total_timesteps"])
    evaluation_episodes = int(preset_cfg["evaluation_episodes"])
    evaluation_seeds = [args.seed + 100 + i for i in range(evaluation_episodes)]
    video_seed = args.seed + 999

    output_dir = args.output_dir.resolve()
    models_dir, videos_dir, plots_dir = output_dir / "models", output_dir / "videos", output_dir / "plots"
    for directory in [output_dir, models_dir, videos_dir, plots_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    record_stage(records, "random", 0.0, 0, 0.0, None, evaluation_seeds, video_seed, videos_dir, 0, physics, noise)
    model = make_model(args.algorithm, args.preset, algorithm_configs, physics, noise, args.seed)

    cumulative_target = 0
    training_wall_time_s = 0.0
    best_record: dict | None = None
    last_stage = ""
    for video_index, item in enumerate(benchmark["curriculum"], start=1):
        stage = str(item["stage"])
        mode = str(item["reset_mode"])
        fraction = float(item["fraction"])
        target = int(round(total_timesteps * fraction))
        additional = target - cumulative_target
        if additional <= 0:
            raise ValueError("Curriculum fractions must increase strictly")
        model.get_env().env_method("set_reset_mode", mode)
        model.get_env().reset()
        print(f"Curriculum stage={stage} reset_mode={mode} additional_steps={additional:,}")
        started = time.perf_counter()
        model.learn(total_timesteps=additional, reset_num_timesteps=False, progress_bar=False, log_interval=20)
        training_wall_time_s += time.perf_counter() - started
        cumulative_target = target
        last_stage = stage
        stage_model_path = models_dir / f"{stage}.zip"
        model.save(stage_model_path)
        current = record_stage(
            records, stage, fraction, int(model.num_timesteps), training_wall_time_s, model,
            evaluation_seeds, video_seed, videos_dir, video_index, physics, noise,
        )
        if best_record is None or checkpoint_rank(current) > checkpoint_rank(best_record):
            best_record = dict(current)
            shutil.copy2(stage_model_path, models_dir / "best.zip")
            (output_dir / "best-checkpoint.json").write_text(
                json.dumps(best_record, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(
                f"New best checkpoint={stage} final_stable={current['final_stable_rate']*100:.1f}% "
                f"capture={current['capture_rate']*100:.1f}% goal={current['goal_ratio']*100:.1f}%"
            )

    model.get_env().close()
    if not last_stage:
        raise RuntimeError("No curriculum stage completed")
    shutil.copy2(models_dir / f"{last_stage}.zip", models_dir / "final.zip")
    best_record = select_best_record(records)
    write_metrics_csv(records, output_dir / "metrics.csv")
    create_plots(records, plots_dir)
    write_summary(records, output_dir / "summary.md", args.algorithm, args.preset, args.seed)
    metadata = {
        "environment": "continuous-acrobot-swingup",
        "algorithm": args.algorithm,
        "preset": args.preset,
        "seed": args.seed,
        "requested_total_timesteps": total_timesteps,
        "actual_final_timesteps": int(model.num_timesteps),
        "training_wall_time_s": training_wall_time_s,
        "evaluation_seeds": evaluation_seeds,
        "video_seed": video_seed,
        "physics": physics.to_dict(),
        "sensor_noise": noise.to_dict(),
        "curriculum": benchmark["curriculum"],
        "best_checkpoint": best_record,
        "algorithm_config": algorithm_configs[args.algorithm],
        "versions": version_info(),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print((output_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
