from __future__ import annotations

from dataclasses import dataclass

import gymnasium as gym
import numpy as np

from .environment import PhysicsConfig, SensorNoiseConfig, make_acrobot_env


# Continuous difficulty interpolates smoothly between the distributions that
# were useful in v4.  This avoids a single large mixed_upper -> mixed_mid jump.
DIFFICULTY_COMPONENTS = ("near_upright", "upper", "full", "evaluation_downward")
DIFFICULTY_ANCHORS: tuple[tuple[float, tuple[float, float, float, float]], ...] = (
    (0.00, (0.30, 0.70, 0.00, 0.00)),
    (0.35, (0.20, 0.50, 0.30, 0.00)),
    (0.70, (0.15, 0.35, 0.50, 0.00)),
    (1.00, (0.10, 0.20, 0.30, 0.40)),
)

RESET_MIXTURES: dict[str, tuple[tuple[str, float], ...]] = {
    "near_upright": (("near_upright", 1.0),),
    "upper": (("upper", 1.0),),
    "full": (("full", 1.0),),
    "downward_mix": (("downward_mix", 1.0),),
}


@dataclass(frozen=True)
class DifficultyDecision:
    action: str
    next_difficulty: float
    next_step: float
    reason: str


def mixture_for_difficulty(difficulty: float) -> tuple[tuple[str, float], ...]:
    """Interpolate reset probabilities continuously over difficulty [0, 1]."""
    difficulty = float(np.clip(difficulty, 0.0, 1.0))
    xs = np.asarray([anchor[0] for anchor in DIFFICULTY_ANCHORS], dtype=np.float64)
    matrix = np.asarray([anchor[1] for anchor in DIFFICULTY_ANCHORS], dtype=np.float64)
    weights = np.asarray(
        [np.interp(difficulty, xs, matrix[:, index]) for index in range(matrix.shape[1])],
        dtype=np.float64,
    )
    weights = np.clip(weights, 0.0, None)
    weights /= weights.sum()
    return tuple(
        (component, float(weight))
        for component, weight in zip(DIFFICULTY_COMPONENTS, weights, strict=True)
        if weight > 1e-12
    )


def readiness_thresholds(difficulty: float) -> tuple[float, float]:
    """Increase the evidence required as the reset distribution gets harder."""
    difficulty = float(np.clip(difficulty, 0.0, 1.0))
    capture_threshold = 0.10 + 0.25 * difficulty
    goal_threshold = 0.05 + 0.07 * difficulty
    return capture_threshold, goal_threshold


def ready_to_advance(record: dict, difficulty: float) -> bool:
    capture = float(record["capture_rate"])
    goal = float(record["goal_ratio"])
    stable = float(record["final_stable_rate"])
    if stable > 0.0:
        return True
    capture_threshold, goal_threshold = readiness_thresholds(difficulty)
    return capture >= capture_threshold or goal >= goal_threshold


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


def decide_difficulty(
    current: dict,
    best_before_block: dict | None,
    difficulty: float,
    difficulty_step: float,
    blocks_at_difficulty: int,
    max_blocks_at_difficulty: int,
    advance_streak: int,
    required_advance_streak: int,
    min_difficulty_step: float,
    regression_step_shrink: float,
) -> DifficultyDecision:
    difficulty = float(np.clip(difficulty, 0.0, 1.0))
    difficulty_step = max(float(difficulty_step), float(min_difficulty_step))

    if severe_regression(current, best_before_block):
        best_difficulty = 0.0
        if best_before_block is not None:
            best_difficulty = float(best_before_block.get("difficulty", 0.0))
        next_step = max(float(min_difficulty_step), difficulty_step * float(regression_step_shrink))
        return DifficultyDecision(
            action="rollback",
            next_difficulty=float(np.clip(best_difficulty, 0.0, 1.0)),
            next_step=next_step,
            reason="downward evaluation regressed; restore best state and refine the difficulty step",
        )

    if difficulty >= 1.0 - 1e-12:
        return DifficultyDecision("hold", 1.0, difficulty_step, "maximum difficulty reached")

    if ready_to_advance(current, difficulty):
        if advance_streak >= required_advance_streak:
            return DifficultyDecision(
                action="advance",
                next_difficulty=min(1.0, difficulty + difficulty_step),
                next_step=difficulty_step,
                reason=f"advancement gate confirmed for {advance_streak} consecutive blocks",
            )
        return DifficultyDecision(
            action="hold",
            next_difficulty=difficulty,
            next_step=difficulty_step,
            reason=f"advancement gate met; awaiting {required_advance_streak} consecutive confirmations",
        )

    if blocks_at_difficulty >= max_blocks_at_difficulty:
        return DifficultyDecision(
            action="probe",
            next_difficulty=min(1.0, difficulty + difficulty_step),
            next_step=difficulty_step,
            reason="maximum consolidation blocks reached; probe a slightly harder distribution",
        )

    return DifficultyDecision("hold", difficulty, difficulty_step, "continue consolidating current difficulty")


class ResetMixtureWrapper(gym.Wrapper):
    """Choose an underlying reset region on every episode reset."""

    def __init__(self, env: gym.Env, reset_mode: str = "near_upright"):
        super().__init__(env)
        self._rng: np.random.Generator | None = None
        self._difficulty: float | None = None
        self.set_reset_mode(reset_mode)

    def set_reset_mode(self, mode: str) -> None:
        if mode not in RESET_MIXTURES:
            raise ValueError(f"Unknown curriculum reset mode: {mode}")
        self.reset_mode = mode
        self._difficulty = None

    def set_difficulty(self, difficulty: float) -> None:
        difficulty = float(difficulty)
        if not 0.0 <= difficulty <= 1.0:
            raise ValueError("difficulty must be in [0, 1]")
        self._difficulty = difficulty
        self.reset_mode = "continuous"

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        if self._rng is None or seed is not None:
            self._rng = np.random.default_rng(seed)
        assert self._rng is not None
        mixture = (
            mixture_for_difficulty(self._difficulty)
            if self._difficulty is not None
            else RESET_MIXTURES[self.reset_mode]
        )
        probabilities = np.asarray([probability for _, probability in mixture], dtype=np.float64)
        probabilities /= probabilities.sum()
        index = int(self._rng.choice(len(mixture), p=probabilities))
        component = mixture[index][0]
        self.env.set_reset_mode(component)
        observation, info = self.env.reset(seed=seed, options=options)
        info = dict(info)
        info["curriculum_difficulty"] = self._difficulty
        return observation, info


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
