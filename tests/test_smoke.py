from __future__ import annotations

import math

import numpy as np

from src.environment import ContinuousAcrobotEnv, PhysicsConfig, SensorNoiseConfig, make_acrobot_env


def test_downward_reset_and_finite_step() -> None:
    env = make_acrobot_env(sensor_noise=SensorNoiseConfig(enabled=False), reset_mode="evaluation_downward")
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


def test_upright_geometry() -> None:
    env = ContinuousAcrobotEnv(PhysicsConfig(), reset_mode="near_upright")
    env.reset(seed=1)
    env.state[:] = [math.pi, 0.0, 0.0, 0.0]
    assert abs(env.tip_height_m() - 2.0) < 1e-9
    env.state[:] = [0.0, 0.0, 0.0, 0.0]
    assert abs(env.tip_height_m() + 2.0) < 1e-9
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
