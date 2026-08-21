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
from stable_baselines3.common.utils import get_schedule_fn

from .curriculum import decide_difficulty, make_training_env, ready_to_advance
from .environment import PhysicsConfig, SensorNoiseConfig, reward_metadata
from .evaluation import evaluate_episode, evaluate_policy
from .reporting import checkpoint_rank, create_plots, select_best_record, write_metrics_csv, write_summary

REPO_ROOT = Path(__file__).resolve().parents[1]
ALGORITHMS = {"ppo", "sac", "td3"}
OFF_POLICY_ALGORITHMS = {"sac", "td3"}
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
        f"stable_dwell={metrics.stable_ratio*100:.1f}% "
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


def apply_learning_rate(model, learning_rate: float) -> None:
    """Replace the constant SB3 learning-rate schedule and active optimizers."""
    learning_rate = float(learning_rate)
    model.learning_rate = learning_rate
    model.lr_schedule = get_schedule_fn(learning_rate)
    optimizers = []
    for name in ("policy", "actor", "critic"):
        obj = getattr(model, name, None)
        optimizer = getattr(obj, "optimizer", None)
        if optimizer is not None and optimizer not in optimizers:
            optimizers.append(optimizer)
    ent_optimizer = getattr(model, "ent_coef_optimizer", None)
    if ent_optimizer is not None and ent_optimizer not in optimizers:
        optimizers.append(ent_optimizer)
    for optimizer in optimizers:
        for group in optimizer.param_groups:
            group["lr"] = learning_rate


def train_for(model, steps: int, recovery_refill_steps: int = 0) -> float:
    """Train for exactly `steps`, optionally collecting fresh replay first."""
    started = time.perf_counter()
    refill = min(max(int(recovery_refill_steps), 0), int(steps))
    if refill > 0 and hasattr(model, "gradient_steps"):
        original_gradient_steps = int(model.gradient_steps)
        print(f"Recovery replay refill: {refill:,} steps with gradient updates disabled")
        model.gradient_steps = 0
        model.learn(total_timesteps=refill, reset_num_timesteps=False, progress_bar=False, log_interval=20)
        model.gradient_steps = original_gradient_steps
    remaining = int(steps) - refill
    if remaining > 0:
        model.learn(total_timesteps=remaining, reset_num_timesteps=False, progress_bar=False, log_interval=20)
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


def restore_best_state(
    model,
    algorithm: str,
    models_dir: Path,
    restore_replay_buffer: bool = True,
):
    env = model.get_env()
    restored = MODEL_CLASSES[algorithm].load(models_dir / "best.zip", env=env, device="cpu")
    replay_path = models_dir / "best-replay.pkl"
    if restore_replay_buffer and replay_path.exists() and hasattr(restored, "load_replay_buffer"):
        restored.load_replay_buffer(replay_path)
    return restored


def main() -> None:
    args = parse_args()
    benchmark, algorithm_configs = load_configs()
    set_global_seed(args.seed)
    preset_cfg = benchmark["presets"][args.preset]
    adaptive_cfg = benchmark["adaptive_curriculum"]
    algorithm_cfg = algorithm_configs[args.algorithm]
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

    current_learning_rate = float(algorithm_cfg["learning_rate"])
    min_learning_rate = float(algorithm_cfg.get("min_learning_rate", current_learning_rate))
    rollback_lr_factor = float(algorithm_cfg.get("rollback_learning_rate_factor", 1.0))
    configured_refill_steps = int(algorithm_cfg.get("recovery_refill_steps", 0))
    restore_replay_on_rollback = bool(algorithm_cfg.get("restore_replay_buffer_on_rollback", True))

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
    if min_learning_rate <= 0.0 or rollback_lr_factor <= 0.0 or rollback_lr_factor > 1.0:
        raise ValueError("off-policy learning-rate recovery settings are invalid")

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
    rollback_count = 0
    pending_recovery_refill = 0

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
        f"capture={current['capture_rate']*100:.1f}% stable_dwell={current['stable_ratio']*100:.1f}% "
        f"goal={current['goal_ratio']*100:.1f}%"
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
        refill_this_block = min(pending_recovery_refill, steps)
        print(
            f"Adaptive block={block_index} difficulty={training_difficulty:.3f} step={difficulty_step:.3f} "
            f"lr={current_learning_rate:.6g} refill={refill_this_block:,} "
            f"steps={steps:,} consumed_before={consumed_timesteps:,}"
        )
        training_wall_time_s += train_for(model, steps, recovery_refill_steps=refill_this_block)
        pending_recovery_refill = 0
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
                f"capture={current['capture_rate']*100:.1f}% stable_dwell={current['stable_ratio']*100:.1f}% "
                f"goal={current['goal_ratio']*100:.1f}%"
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
        learning_rate_before = current_learning_rate
        next_learning_rate = current_learning_rate

        print(
            f"Adaptive decision={decision.action} difficulty={training_difficulty:.3f}->{decision.next_difficulty:.3f} "
            f"step={difficulty_step:.3f}->{decision.next_step:.3f} "
            f"advance_streak={advance_streak}/{required_advance_streak} reason={decision.reason}"
        )

        if decision.action == "rollback":
            rollback_count += 1
            if args.algorithm in OFF_POLICY_ALGORITHMS:
                next_learning_rate = max(min_learning_rate, current_learning_rate * rollback_lr_factor)
            model = restore_best_state(
                model,
                args.algorithm,
                models_dir,
                restore_replay_buffer=(
                    restore_replay_on_rollback if args.algorithm in OFF_POLICY_ALGORITHMS else True
                ),
            )
            if args.algorithm in OFF_POLICY_ALGORITHMS:
                apply_learning_rate(model, next_learning_rate)
                pending_recovery_refill = configured_refill_steps
                recovery_seed = args.seed + 100_000 + rollback_count * 997
                np.random.seed(recovery_seed)
                torch.manual_seed(recovery_seed)
                action_noise = getattr(model, "action_noise", None)
                if action_noise is not None and hasattr(action_noise, "reset"):
                    action_noise.reset()
                model.get_env().seed(recovery_seed)
                print(
                    f"Off-policy recovery: lr={learning_rate_before:.6g}->{next_learning_rate:.6g}, "
                    f"replay={'restored' if restore_replay_on_rollback else 'fresh'}, "
                    f"refill_next={pending_recovery_refill:,}, recovery_seed={recovery_seed}"
                )
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
                "learning_rate_before": learning_rate_before,
                "next_learning_rate": next_learning_rate,
                "recovery_refill_next": pending_recovery_refill,
                "best_stage_after_block": None if best_record is None else best_record["stage"],
                "best_difficulty_after_block": None if best_record is None else best_record["difficulty"],
            }
        )
        current_learning_rate = next_learning_rate
        difficulty = decision.next_difficulty
        difficulty_step = decision.next_step

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
        "reward": reward_metadata(),
        "adaptive_curriculum": adaptive_cfg,
        "adaptive_decisions": decisions,
        "next_planned_difficulty": difficulty,
        "final_model_difficulty": model_difficulty,
        "final_difficulty_step": difficulty_step,
        "rollback_count": rollback_count,
        "final_learning_rate": current_learning_rate,
        "best_checkpoint": best_record,
        "final_checkpoint": final_record,
        "algorithm_config": algorithm_cfg,
        "versions": version_info(),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print((output_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
