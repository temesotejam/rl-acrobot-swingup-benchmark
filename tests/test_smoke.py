from __future__ import annotations

import math

import numpy as np

from src.curriculum import (
    ResetMixtureWrapper,
    decide_difficulty,
    mixture_for_difficulty,
    readiness_thresholds,
    ready_to_advance,
    severe_regression,
)
from src.environment import (
    ContinuousAcrobotEnv,
    PhysicsConfig,
    SensorNoiseConfig,
    make_acrobot_env,
    reward_metadata,
)
from src.reporting import select_best_record
from src.train import train_for


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


def test_reward_metadata_tracks_stability_shaping() -> None:
    metadata = reward_metadata()
    assert metadata["version"] == "v6-continuous-stability"
    assert float(metadata["stability_reward_weight"]) > 0.0
    assert float(metadata["stability_dtheta1_scale_rad_s"]) == 1.0
    assert float(metadata["stability_dtheta2_scale_rad_s"]) == 1.5


def _mixture_dict(difficulty: float) -> dict[str, float]:
    return dict(mixture_for_difficulty(difficulty))


def test_continuous_curriculum_interpolates_smoothly() -> None:
    easy = _mixture_dict(0.0)
    mid = _mixture_dict(0.175)
    hard = _mixture_dict(1.0)

    assert easy == {"near_upright": 0.30, "upper": 0.70}
    assert abs(mid["near_upright"] - 0.25) < 1e-12
    assert abs(mid["upper"] - 0.60) < 1e-12
    assert abs(mid["full"] - 0.15) < 1e-12
    assert hard == {
        "near_upright": 0.10,
        "upper": 0.20,
        "full": 0.30,
        "evaluation_downward": 0.40,
    }
    assert abs(sum(mid.values()) - 1.0) < 1e-12


def test_continuous_wrapper_can_reach_downward_resets() -> None:
    base = make_acrobot_env(sensor_noise=SensorNoiseConfig(enabled=False), reset_mode="near_upright")
    env = ResetMixtureWrapper(base, reset_mode="near_upright")
    env.set_difficulty(1.0)
    seen: set[str] = set()
    for seed in range(100):
        obs, info = env.reset(seed=seed)
        assert np.isfinite(obs).all()
        assert info["curriculum_difficulty"] == 1.0
        seen.add(str(info["reset_mode"]))
    assert "evaluation_downward" in seen
    assert len(seen) >= 3
    env.close()


def test_readiness_thresholds_increase_with_difficulty() -> None:
    easy = readiness_thresholds(0.0)
    hard = readiness_thresholds(1.0)
    assert len(easy) == 3
    assert all(h > e for e, h in zip(easy, hard, strict=True))


def test_goal_dwell_without_capture_no_longer_advances() -> None:
    record = {
        "capture_rate": 0.0,
        "goal_ratio": 0.30,
        "stable_ratio": 0.0,
        "final_stable_rate": 0.0,
    }
    assert not ready_to_advance(record, 0.0)


def test_continuous_controller_requires_confirmed_success() -> None:
    current = {
        "capture_rate": 0.25,
        "goal_ratio": 0.09,
        "stable_ratio": 0.03,
        "final_stable_rate": 0.0,
    }
    first = decide_difficulty(
        current=current,
        best_before_block=None,
        difficulty=0.20,
        difficulty_step=0.10,
        blocks_at_difficulty=1,
        max_blocks_at_difficulty=3,
        advance_streak=1,
        required_advance_streak=2,
        min_difficulty_step=0.025,
        regression_step_shrink=0.50,
    )
    assert first.action == "hold"
    assert abs(first.next_difficulty - 0.20) < 1e-12

    second = decide_difficulty(
        current=current,
        best_before_block=None,
        difficulty=0.20,
        difficulty_step=0.10,
        blocks_at_difficulty=2,
        max_blocks_at_difficulty=3,
        advance_streak=2,
        required_advance_streak=2,
        min_difficulty_step=0.025,
        regression_step_shrink=0.50,
    )
    assert second.action == "advance"
    assert abs(second.next_difficulty - 0.30) < 1e-12


def test_continuous_controller_rolls_back_and_refines_step() -> None:
    best = {
        "capture_rate": 0.50,
        "goal_ratio": 0.12,
        "stable_ratio": 0.06,
        "final_stable_rate": 0.0,
        "difficulty": 0.20,
    }
    current = {
        "capture_rate": 0.0,
        "goal_ratio": 0.01,
        "stable_ratio": 0.0,
        "final_stable_rate": 0.0,
    }
    assert severe_regression(current, best)
    decision = decide_difficulty(
        current=current,
        best_before_block=best,
        difficulty=0.30,
        difficulty_step=0.10,
        blocks_at_difficulty=1,
        max_blocks_at_difficulty=3,
        advance_streak=0,
        required_advance_streak=2,
        min_difficulty_step=0.025,
        regression_step_shrink=0.50,
    )
    assert decision.action == "rollback"
    assert abs(decision.next_difficulty - 0.20) < 1e-12
    assert abs(decision.next_step - 0.05) < 1e-12


def test_continuous_controller_probes_after_consolidation() -> None:
    current = {
        "capture_rate": 0.0,
        "goal_ratio": 0.0,
        "stable_ratio": 0.0,
        "final_stable_rate": 0.0,
    }
    decision = decide_difficulty(
        current=current,
        best_before_block=None,
        difficulty=0.0,
        difficulty_step=0.10,
        blocks_at_difficulty=3,
        max_blocks_at_difficulty=3,
        advance_streak=0,
        required_advance_streak=2,
        min_difficulty_step=0.025,
        regression_step_shrink=0.50,
    )
    assert decision.action == "probe"
    assert abs(decision.next_difficulty - 0.10) < 1e-12


def test_recovery_refill_collects_before_gradient_updates() -> None:
    class DummyModel:
        gradient_steps = 1

        def __init__(self) -> None:
            self.calls: list[tuple[int, int]] = []

        def learn(self, total_timesteps: int, **kwargs):
            self.calls.append((int(total_timesteps), int(self.gradient_steps)))
            return self

    model = DummyModel()
    train_for(model, 100, recovery_refill_steps=25)
    assert model.calls == [(25, 0), (75, 1)]
    assert model.gradient_steps == 1


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


def test_best_checkpoint_prefers_more_stable_dwell() -> None:
    records = [
        {
            "stage": "block_a", "difficulty": 0.1, "final_stable_rate": 0.0, "capture_rate": 0.50,
            "stable_ratio": 0.02, "goal_ratio": 0.15, "mean_return": 1200.0,
        },
        {
            "stage": "block_b", "difficulty": 0.1, "final_stable_rate": 0.0, "capture_rate": 0.50,
            "stable_ratio": 0.08, "goal_ratio": 0.13, "mean_return": 1100.0,
        },
    ]
    assert select_best_record(records)["stage"] == "block_b"


def test_best_checkpoint_ignores_delivered_final_alias() -> None:
    records = [
        {
            "stage": "random", "difficulty": 0.0, "final_stable_rate": 0.0, "capture_rate": 0.0,
            "stable_ratio": 0.0, "goal_ratio": 0.0, "mean_return": 1000.0,
        },
        {
            "stage": "block_04_d0p200", "difficulty": 0.2, "final_stable_rate": 0.0, "capture_rate": 0.25,
            "stable_ratio": 0.04, "goal_ratio": 0.04, "mean_return": 300.0,
        },
        {
            "stage": "final_model", "difficulty": 0.2, "final_stable_rate": 0.0, "capture_rate": 0.25,
            "stable_ratio": 0.04, "goal_ratio": 0.04, "mean_return": 300.0,
        },
    ]
    assert select_best_record(records)["stage"] == "block_04_d0p200"
