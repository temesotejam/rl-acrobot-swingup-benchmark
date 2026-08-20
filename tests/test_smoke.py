from __future__ import annotations

import math

import numpy as np

from src.curriculum import RESET_MIXTURES, ResetMixtureWrapper
from src.environment import ContinuousAcrobotEnv, PhysicsConfig, SensorNoiseConfig, make_acrobot_env
from src.reporting import select_best_record


def test_downward_reset_and_finite_step() -> None:
    physics = PhysicsConfig(max_episode_s=40.0)
    env = make_acrobot_env(physics=physics, sensor_noise=SensorNoiseConfig(enabled=False), reset_mode="evaluation_downward")
    obs, info = env.reset(seed=123)
    theta1, theta2 = info["true_state"][:2]
    assert abs(math.degrees(theta1)) <= 5.1
    assert abs(math.degrees(theta2)) <= 5.1
    obs, reward, terminated, truncated, info = env.step(np.array([0.0], dtype=np.float32))
    assert obs.shape == (6,)
    assert np.isfinite(obs).all()
    assert np.isfinite(reward)
    assert not terminated
    assert not truncated
    env.close()


def test_upright_geometry_and_40s_horizon() -> None:
    env = ContinuousAcrobotEnv(PhysicsConfig(max_episode_s=40.0), reset_mode="near_upright")
    env.reset(seed=1)
    assert env.max_steps == 2000
    env.state[:] = [math.pi, 0.0, 0.0, 0.0]
    assert abs(env.tip_height_m() - 2.0) < 1e-9
    env.state[:] = [0.0, 0.0, 0.0, 0.0]
    assert abs(env.tip_height_m() + 2.0) < 1e-9
    env.close()


def test_mixed_curriculum_preserves_old_regions() -> None:
    assert RESET_MIXTURES["mixed_upper"] == (("near_upright", 0.20), ("upper", 0.80))
    assert RESET_MIXTURES["mixed_full"] == (("near_upright", 0.10), ("upper", 0.20), ("full", 0.70))
    assert RESET_MIXTURES["mixed_downward"][-1] == ("evaluation_downward", 0.65)

    base = make_acrobot_env(sensor_noise=SensorNoiseConfig(enabled=False), reset_mode="near_upright")
    env = ResetMixtureWrapper(base, reset_mode="mixed_downward")
    seen: set[str] = set()
    for seed in range(100):
        obs, info = env.reset(seed=seed)
        assert np.isfinite(obs).all()
        seen.add(str(info["reset_mode"]))
    assert "evaluation_downward" in seen
    assert len(seen) >= 3
    env.close()


def test_sensor_wrapper_stays_finite() -> None:
    env = make_acrobot_env(reset_mode="full")
    obs, _ = env.reset(seed=7)
    for _ in range(100):
        assert obs.shape == (6,)
        assert np.isfinite(obs).all()
        obs, _, _, truncated, _ = env.step(env.action_space.sample())
        if truncated:
            obs, _ = env.reset()
    env.close()


def test_best_checkpoint_prefers_control_success_over_return() -> None:
    records = [
        {
            "stage": "random", "final_stable_rate": 0.0, "capture_rate": 0.0,
            "goal_ratio": 0.0, "mean_return": 1000.0,
        },
        {
            "stage": "50_percent", "final_stable_rate": 0.0, "capture_rate": 0.25,
            "goal_ratio": 0.04, "mean_return": 300.0,
        },
        {
            "stage": "100_percent", "final_stable_rate": 0.0, "capture_rate": 0.0,
            "goal_ratio": 0.0, "mean_return": 500.0,
        },
    ]
    assert select_best_record(records)["stage"] == "50_percent"
