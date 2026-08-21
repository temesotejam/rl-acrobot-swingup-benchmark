from __future__ import annotations

from dataclasses import dataclass

import gymnasium as gym
import numpy as np

from .environment import PhysicsConfig, SensorNoiseConfig, make_acrobot_env


# Later levels deliberately keep substantial mass on easier starts.  v3 showed
# that jumping directly from mixed_upper to mixed_full could still collapse SAC,
# so v4 inserts mixed_mid and softens the full/downward distributions.
RESET_MIXTURES: dict[str, tuple[tuple[str, float], ...]] = {
    "near_upright": (("near_upright", 1.0),),
    "upper": (("upper", 1.0),),
    "full": (("full", 1.0),),
    "downward_mix": (("downward_mix", 1.0),),
    "mixed_upper": (("near_upright", 0.30), ("upper", 0.70)),
    "mixed_mid": (("near_upright", 0.20), ("upper", 0.50), ("full", 0.30)),
    "mixed_full": (("near_upright", 0.15), ("upper", 0.35), ("full", 0.50)),
    "mixed_downward": (
        ("near_upright", 0.10),
        ("upper", 0.20),
        ("full", 0.30),
        ("evaluation_downward", 0.40),
    ),
}

ADAPTIVE_LEVELS = ("mixed_upper", "mixed_mid", "mixed_full", "mixed_downward")


@dataclass(frozen=True)
class AdaptiveDecision:
    action: str
    next_level: int
    reason: str


def ready_to_advance(record: dict, level: int) -> bool:
    """Return True when downward evaluation justifies harder reset starts."""
    capture = float(record["capture_rate"])
    goal = float(record["goal_ratio"])
    stable = float(record["final_stable_rate"])
    if stable > 0.0:
        return True
    if level == 0:
        return capture >= 0.10 or goal >= 0.05
    if level == 1:
        return capture >= 0.20 or goal >= 0.07
    if level == 2:
        return capture >= 0.30 or goal >= 0.10
    return False


def severe_regression(current: dict, best: dict | None) -> bool:
    """Detect a meaningful loss of previously demonstrated control skill."""
    if best is None:
        return False
    current_stable = float(current["final_stable_rate"])
    current_capture = float(current["capture_rate"])
    current_goal = float(current["goal_ratio"])
    best_stable = float(best["final_stable_rate"])
    best_capture = float(best["capture_rate"])
    best_goal = float(best["goal_ratio"])

    if best_stable >= 0.10 and current_stable < 0.50 * best_stable:
        return True
    if best_capture >= 0.10 and current_capture < 0.50 * best_capture:
        return True
    if best_goal >= 0.05 and current_goal < 0.50 * best_goal:
        return True
    return False


def decide_transition(
    current: dict,
    best_before_block: dict | None,
    level: int,
    blocks_at_level: int,
    max_blocks_per_level: int,
    advance_streak: int,
    required_advance_streak: int,
) -> AdaptiveDecision:
    if severe_regression(current, best_before_block):
        return AdaptiveDecision(
            action="rollback",
            next_level=max(0, level - 1),
            reason="downward evaluation regressed relative to the retained best checkpoint",
        )
    if level < len(ADAPTIVE_LEVELS) - 1 and ready_to_advance(current, level):
        if advance_streak >= required_advance_streak:
            return AdaptiveDecision(
                action="advance",
                next_level=level + 1,
                reason=f"advancement gate confirmed for {advance_streak} consecutive blocks",
            )
        return AdaptiveDecision(
            action="hold",
            next_level=level,
            reason=f"advancement gate met; awaiting {required_advance_streak} consecutive confirmations",
        )
    if level < len(ADAPTIVE_LEVELS) - 1 and blocks_at_level >= max_blocks_per_level:
        return AdaptiveDecision(
            action="advance",
            next_level=level + 1,
            reason="maximum hold blocks reached without severe regression",
        )
    return AdaptiveDecision(action="hold", next_level=level, reason="continue consolidating current level")


class ResetMixtureWrapper(gym.Wrapper):
    """Choose an underlying reset region on every episode reset."""

    def __init__(self, env: gym.Env, reset_mode: str = "near_upright"):
        super().__init__(env)
        self._rng: np.random.Generator | None = None
        self.set_reset_mode(reset_mode)

    def set_reset_mode(self, mode: str) -> None:
        if mode not in RESET_MIXTURES:
            raise ValueError(f"Unknown curriculum reset mode: {mode}")
        self.reset_mode = mode

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        if self._rng is None or seed is not None:
            self._rng = np.random.default_rng(seed)
        assert self._rng is not None
        mixture = RESET_MIXTURES[self.reset_mode]
        probabilities = np.asarray([probability for _, probability in mixture], dtype=np.float64)
        probabilities /= probabilities.sum()
        index = int(self._rng.choice(len(mixture), p=probabilities))
        component = mixture[index][0]
        self.env.set_reset_mode(component)
        return self.env.reset(seed=seed, options=options)


def make_training_env(
    physics: PhysicsConfig,
    sensor_noise: SensorNoiseConfig,
    reset_mode: str = "near_upright",
) -> gym.Env:
    base = make_acrobot_env(
        physics=physics,
        sensor_noise=sensor_noise,
        reset_mode="near_upright",
    )
    return ResetMixtureWrapper(base, reset_mode=reset_mode)
