from __future__ import annotations

import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import imageio.v2 as imageio
import numpy as np

from .environment import PhysicsConfig, SensorNoiseConfig, make_acrobot_env

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


class PredictPolicy(Protocol):
    def predict(self, observation: np.ndarray, deterministic: bool = True): ...


@dataclass
class EpisodeMetrics:
    episode_return: float
    survival_s: float
    captured: bool
    capture_time_s: float
    final_stable: bool
    goal_ratio: float
    high_ratio: float
    max_tip_height_m: float
    rms_joint_speed_rad_s: float
    rms_torque_nm: float


@dataclass
class AggregateMetrics:
    mean_return: float
    std_return: float
    mean_survival_s: float
    capture_rate: float
    mean_capture_time_s: float
    final_stable_rate: float
    goal_ratio: float
    high_ratio: float
    max_tip_height_m: float
    rms_joint_speed_rad_s: float
    rms_torque_nm: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def _action(policy: PredictPolicy | None, env, observation: np.ndarray) -> np.ndarray:
    if policy is None:
        return np.asarray(env.action_space.sample(), dtype=np.float32)
    action, _ = policy.predict(observation, deterministic=True)
    return np.asarray(action, dtype=np.float32)


def evaluate_episode(
    policy: PredictPolicy | None,
    seed: int,
    physics: PhysicsConfig,
    sensor_noise: SensorNoiseConfig,
    video_path: Path | None = None,
) -> EpisodeMetrics:
    env = make_acrobot_env(
        physics=physics,
        sensor_noise=sensor_noise,
        reset_mode="evaluation_downward",
        render_mode="rgb_array" if video_path is not None else None,
    )
    env.action_space.seed(seed + 10000)
    observation, info = env.reset(seed=seed)
    frames: list[np.ndarray] = []
    heights: list[float] = []
    speeds: list[float] = []
    torques: list[float] = []
    stable_flags: list[bool] = []
    episode_return = 0.0
    capture_run = 0
    capture_steps = max(1, int(round(0.5 / physics.dt_s)))
    capture_time = math.nan

    if video_path is not None:
        frame = env.render()
        if frame is not None:
            frames.append(frame)

    terminated = truncated = False
    step_index = 0
    while not (terminated or truncated):
        action = _action(policy, env, observation)
        observation, reward, terminated, truncated, info = env.step(action)
        episode_return += float(reward)
        step_index += 1
        _, _, dtheta1, dtheta2 = [float(v) for v in info["true_state"]]
        height = float(info["tip_height_m"])
        torque = float(info["actual_torque_nm"])
        heights.append(height)
        speeds.append(math.sqrt(0.5 * (dtheta1**2 + dtheta2**2)))
        torques.append(torque)

        stable = height >= 1.0 and abs(dtheta1) <= 1.0 and abs(dtheta2) <= 1.5
        capture_run = capture_run + 1 if stable else 0
        if math.isnan(capture_time) and capture_run >= capture_steps:
            capture_time = float(info["time_s"])
        stable_flags.append(stable)

        if video_path is not None and step_index % 2 == 0:
            frame = env.render()
            if frame is not None:
                frames.append(frame)

    survival_s = float(info.get("time_s", step_index * physics.dt_s))
    env.close()
    if video_path is not None:
        video_path.parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(video_path, frames, fps=25, macro_block_size=1)

    final_window_steps = max(1, int(round(2.0 / physics.dt_s)))
    final_stable = len(stable_flags) >= final_window_steps and float(np.mean(stable_flags[-final_window_steps:])) >= 0.80
    height_arr = np.asarray(heights, dtype=np.float64)
    speed_arr = np.asarray(speeds, dtype=np.float64)
    torque_arr = np.asarray(torques, dtype=np.float64)
    return EpisodeMetrics(
        episode_return=episode_return,
        survival_s=survival_s,
        captured=not math.isnan(capture_time),
        capture_time_s=capture_time,
        final_stable=bool(final_stable),
        goal_ratio=float(np.mean(height_arr >= 1.0)),
        high_ratio=float(np.mean(height_arr >= 1.5)),
        max_tip_height_m=float(np.max(height_arr)),
        rms_joint_speed_rad_s=float(np.sqrt(np.mean(np.square(speed_arr)))),
        rms_torque_nm=float(np.sqrt(np.mean(np.square(torque_arr)))),
    )


def evaluate_policy(
    policy: PredictPolicy | None,
    seeds: list[int],
    physics: PhysicsConfig,
    sensor_noise: SensorNoiseConfig,
) -> AggregateMetrics:
    episodes = [evaluate_episode(policy, seed, physics, sensor_noise) for seed in seeds]
    capture_times = [item.capture_time_s for item in episodes if item.captured]
    returns = np.asarray([item.episode_return for item in episodes], dtype=np.float64)
    return AggregateMetrics(
        mean_return=float(np.mean(returns)),
        std_return=float(np.std(returns)),
        mean_survival_s=float(np.mean([e.survival_s for e in episodes])),
        capture_rate=float(np.mean([e.captured for e in episodes])),
        mean_capture_time_s=float(np.mean(capture_times)) if capture_times else math.nan,
        final_stable_rate=float(np.mean([e.final_stable for e in episodes])),
        goal_ratio=float(np.mean([e.goal_ratio for e in episodes])),
        high_ratio=float(np.mean([e.high_ratio for e in episodes])),
        max_tip_height_m=float(np.mean([e.max_tip_height_m for e in episodes])),
        rms_joint_speed_rad_s=float(np.mean([e.rms_joint_speed_rad_s for e in episodes])),
        rms_torque_nm=float(np.mean([e.rms_torque_nm for e in episodes])),
    )
