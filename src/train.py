from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
import yaml
from stable_baselines3 import PPO, SAC, TD3
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.noise import NormalActionNoise

from .curriculum import decide_difficulty, make_training_env, ready_to_advance
from .environment import PhysicsConfig, SensorNoiseConfig
from .evaluation import evaluate_episode, evaluate_policy
from .reporting import checkpoint_rank, create_plots, select_best_record, write_metrics_csv, write_summary

REPO_ROOT = Path(__file__).resolve().parents[1]
ALGORITHMS = {"ppo", "sac", "td3"}
MODEL_CLASSES = {"ppo": PPO, "sac": SAC, "td3": TD3}


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
    difficulty: float,
    policy,
    evaluation_seeds: list[int],
    physics: PhysicsConfig,
    noise: SensorNoiseConfig,
) -> dict:
    metrics = evaluate_policy(policy, evaluation_seeds, physics=physics, sensor_noise=noise)
    record = {
        "stage": stage,
        "progress": progress,
        "timesteps": timesteps,
        "training_wall_time_s": training_wall_time_s,
        "difficulty": float(difficulty),
        **metrics.to_dict(),
    }
    records.append(record)
    capture_t = "-" if math.isnan(metrics.mean_capture_time_s) else f"{metrics.mean_capture_time_s:.2f}s"
    print(
        f"[{stage}] consumed_steps={timesteps:,} difficulty={difficulty:.3f} return={metrics.mean_return:.1f} "
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
        return PPO(
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


def train_for(model, steps: int) -> float:
    started = time.perf_counter()
    model.learn(total_timesteps=steps, reset_num_timesteps=False, progress_bar=False, log_interval=20)
    return time.perf_counter() - started


def save_best_state(
    model,
    record: dict,
    output_dir: Path,
    models_dir: Path,
    videos_dir: Path,
    video_seed: int,
    physics: PhysicsConfig,
    noise: SensorNoiseConfig,
) -> None:
    model.save(models_dir / "best.zip")
    if hasattr(model, "save_replay_buffer"):
        model.save_replay_buffer(models_dir / "best-replay.pkl")
    (output_dir / "best-checkpoint.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    evaluate_episode(model, video_seed, physics, noise, videos_dir / "best.mp4")


def restore_best_state(model, algorithm: str, models_dir: Path):
    env = model.get_env()
    restored = MODEL_CLASSES[algorithm].load(models_dir / "best.zip", env=env, device="cpu")
    replay_path = models_dir / "best-replay.pkl"
    if replay_path.exists() and hasattr(restored, "load_replay_buffer"):
        restored.load_replay_buffer(replay_path)
    return restored


def main() -> None:
    args = parse_args()
    benchmark, algorithm_configs = load_configs()
    set_global_seed(args.seed)
    preset_cfg = benchmark["presets"][args.preset]
    adaptive_cfg = benchmark["adaptive_curriculum"]
    physics = PhysicsConfig(**benchmark["physics"])
    noise = SensorNoiseConfig(**benchmark["sensor_noise"])

    total_timesteps = int(preset_cfg["total_timesteps"])
    warmup_timesteps = int(preset_cfg["warmup_timesteps"])
    block_timesteps = int(preset_cfg["adaptive_block_timesteps"])
    evaluation_episodes = int(preset_cfg["evaluation_episodes"])
    evaluation_seeds = [args.seed + 100 + i for i in range(evaluation_episodes)]
    video_seed = args.seed + 999

    initial_difficulty = float(adaptive_cfg["initial_difficulty"])
    initial_step = float(adaptive_cfg["initial_difficulty_step"])
    min_step = float(adaptive_cfg["min_difficulty_step"])
    regression_step_shrink = float(adaptive_cfg["regression_step_shrink"])
    max_blocks_at_difficulty = int(adaptive_cfg["max_blocks_at_difficulty"])
    required_advance_streak = int(adaptive_cfg["advance_confirmation_blocks"])

    if not 0 < warmup_timesteps < total_timesteps:
        raise ValueError("warmup_timesteps must be between zero and total_timesteps")
    if block_timesteps <= 0:
        raise ValueError("adaptive_block_timesteps must be positive")
    if not 0.0 <= initial_difficulty <= 1.0:
        raise ValueError("initial_difficulty must be in [0, 1]")
    if initial_step <= 0.0 or min_step <= 0.0 or min_step > initial_step:
        raise ValueError("difficulty steps must be positive and min <= initial")
    if not 0.0 < regression_step_shrink <= 1.0:
        raise ValueError("regression_step_shrink must be in (0, 1]")
    if max_blocks_at_difficulty <= 0 or required_advance_streak <= 0:
        raise ValueError("adaptive block counts must be positive")

    output_dir = args.output_dir.resolve()
    models_dir, videos_dir, plots_dir = output_dir / "models", output_dir / "videos", output_dir / "plots"
    for directory in [output_dir, models_dir, videos_dir, plots_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    decisions: list[dict] = []
    record_stage(records, "random", 0.0, 0, 0.0, 0.0, None, evaluation_seeds, physics, noise)
    model = make_model(args.algorithm, args.preset, algorithm_configs, physics, noise, args.seed)

    consumed_timesteps = 0
    training_wall_time_s = 0.0
    best_record: dict | None = None

    warmup_mode = str(adaptive_cfg["warmup_reset_mode"])
    model.get_env().env_method("set_reset_mode", warmup_mode)
    model.get_env().reset()
    print(f"Adaptive warmup reset_mode={warmup_mode} steps={warmup_timesteps:,}")
    training_wall_time_s += train_for(model, warmup_timesteps)
    consumed_timesteps += warmup_timesteps
    warmup_stage = "warmup"
    current = record_stage(
        records, warmup_stage, consumed_timesteps / total_timesteps, consumed_timesteps,
        training_wall_time_s, initial_difficulty, model, evaluation_seeds, physics, noise,
    )
    best_record = dict(current)
    save_best_state(model, best_record, output_dir, models_dir, videos_dir, video_seed, physics, noise)
    print(
        f"New best checkpoint={warmup_stage} difficulty={initial_difficulty:.3f} "
        f"capture={current['capture_rate']*100:.1f}% goal={current['goal_ratio']*100:.1f}%"
    )

    difficulty = initial_difficulty
    difficulty_step = initial_step
    model_difficulty = initial_difficulty
    blocks_at_difficulty = 0
    advance_streak = 0
    block_index = 0

    while consumed_timesteps < total_timesteps:
        block_index += 1
        training_difficulty = difficulty
        steps = min(block_timesteps, total_timesteps - consumed_timesteps)
        model.get_env().env_method("set_difficulty", training_difficulty)
        model.get_env().reset()
        print(
            f"Adaptive block={block_index} difficulty={training_difficulty:.3f} step={difficulty_step:.3f} "
            f"steps={steps:,} consumed_before={consumed_timesteps:,}"
        )
        training_wall_time_s += train_for(model, steps)
        consumed_timesteps += steps
        blocks_at_difficulty += 1
        model_difficulty = training_difficulty
        stage = f"block_{block_index:02d}_d{training_difficulty:.3f}".replace(".", "p")

        best_before_block = dict(best_record) if best_record is not None else None
        current = record_stage(
            records, stage, consumed_timesteps / total_timesteps, consumed_timesteps,
            training_wall_time_s, training_difficulty, model, evaluation_seeds, physics, noise,
        )
        improved = best_record is None or checkpoint_rank(current) > checkpoint_rank(best_record)
        if improved:
            best_record = dict(current)
            save_best_state(model, best_record, output_dir, models_dir, videos_dir, video_seed, physics, noise)
            print(
                f"New best checkpoint={stage} difficulty={training_difficulty:.3f} "
                f"capture={current['capture_rate']*100:.1f}% goal={current['goal_ratio']*100:.1f}%"
            )

        if ready_to_advance(current, training_difficulty):
            advance_streak += 1
        else:
            advance_streak = 0

        decision = decide_difficulty(
            current=current,
            best_before_block=best_before_block,
            difficulty=training_difficulty,
            difficulty_step=difficulty_step,
            blocks_at_difficulty=blocks_at_difficulty,
            max_blocks_at_difficulty=max_blocks_at_difficulty,
            advance_streak=advance_streak,
            required_advance_streak=required_advance_streak,
            min_difficulty_step=min_step,
            regression_step_shrink=regression_step_shrink,
        )
        decisions.append(
            {
                "stage": stage,
                "consumed_timesteps": consumed_timesteps,
                "difficulty_before": training_difficulty,
                "difficulty_step_before": difficulty_step,
                "action": decision.action,
                "next_difficulty": decision.next_difficulty,
                "next_difficulty_step": decision.next_step,
                "reason": decision.reason,
                "advance_streak": advance_streak,
                "best_stage_after_block": None if best_record is None else best_record["stage"],
                "best_difficulty_after_block": None if best_record is None else best_record["difficulty"],
            }
        )
        print(
            f"Adaptive decision={decision.action} difficulty={training_difficulty:.3f}->{decision.next_difficulty:.3f} "
            f"step={difficulty_step:.3f}->{decision.next_step:.3f} "
            f"advance_streak={advance_streak}/{required_advance_streak} reason={decision.reason}"
        )

        if decision.action == "rollback":
            model = restore_best_state(model, args.algorithm, models_dir)
            model_difficulty = float(best_record["difficulty"] if best_record is not None else 0.0)
            print(
                f"Restored best checkpoint={best_record['stage'] if best_record else 'unknown'} "
                f"difficulty={model_difficulty:.3f}"
            )
            blocks_at_difficulty = 0
            advance_streak = 0
        elif decision.action in {"advance", "probe"}:
            blocks_at_difficulty = 0
            advance_streak = 0

        difficulty = decision.next_difficulty
        difficulty_step = decision.next_step

    # Save and freshly evaluate the model that is actually delivered after any
    # last-block rollback.  This keeps Pages metrics aligned with final.mp4.
    model.save(models_dir / "final.zip")
    final_record = record_stage(
        records, "final_model", 1.0, consumed_timesteps, training_wall_time_s,
        model_difficulty, model, evaluation_seeds, physics, noise,
    )
    evaluate_episode(model, video_seed, physics, noise, videos_dir / "final.mp4")
    model_internal_timesteps = int(model.num_timesteps)
    model.get_env().close()

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
        "consumed_total_timesteps": consumed_timesteps,
        "model_internal_timesteps": model_internal_timesteps,
        "training_wall_time_s": training_wall_time_s,
        "evaluation_seeds": evaluation_seeds,
        "video_seed": video_seed,
        "physics": physics.to_dict(),
        "sensor_noise": noise.to_dict(),
        "adaptive_curriculum": adaptive_cfg,
        "adaptive_decisions": decisions,
        "next_planned_difficulty": difficulty,
        "final_model_difficulty": model_difficulty,
        "final_difficulty_step": difficulty_step,
        "best_checkpoint": best_record,
        "final_checkpoint": final_record,
        "algorithm_config": algorithm_configs[args.algorithm],
        "versions": version_info(),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print((output_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
