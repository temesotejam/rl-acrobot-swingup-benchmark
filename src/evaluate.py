from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from stable_baselines3 import PPO, SAC, TD3

from .environment import PhysicsConfig, SensorNoiseConfig
from .evaluation import evaluate_episode, evaluate_policy

REPO_ROOT = Path(__file__).resolve().parents[1]
CLASSES = {"ppo": PPO, "sac": SAC, "td3": TD3}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("--algorithm", choices=sorted(CLASSES), required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--video", type=Path, default=None)
    args = parser.parse_args()
    benchmark = yaml.safe_load((REPO_ROOT / "configs" / "benchmark.yaml").read_text(encoding="utf-8"))
    physics = PhysicsConfig(**benchmark["physics"])
    noise = SensorNoiseConfig(**benchmark["sensor_noise"])
    model = CLASSES[args.algorithm].load(args.model, device="cpu")
    seeds = [args.seed + i for i in range(args.episodes)]
    metrics = evaluate_policy(model, seeds, physics, noise)
    if args.video is not None:
        evaluate_episode(model, args.seed, physics, noise, args.video)
    print(json.dumps(metrics.to_dict(), indent=2))


if __name__ == "__main__":
    main()
