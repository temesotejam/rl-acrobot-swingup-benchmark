from __future__ import annotations

import gymnasium as gym
import numpy as np

from .environment import PhysicsConfig, SensorNoiseConfig, make_acrobot_env


RESET_MIXTURES: dict[str, tuple[tuple[str, float], ...]] = {
    "near_upright": (("near_upright", 1.0),),
    "upper": (("upper", 1.0),),
    "full": (("full", 1.0),),
    "downward_mix": (("downward_mix", 1.0),),
    "mixed_upper": (("near_upright", 0.20), ("upper", 0.80)),
    "mixed_full": (("near_upright", 0.10), ("upper", 0.20), ("full", 0.70)),
    "mixed_downward": (
        ("near_upright", 0.05),
        ("upper", 0.10),
        ("full", 0.20),
        ("evaluation_downward", 0.65),
    ),
}


class ResetMixtureWrapper(gym.Wrapper):
    """Choose an underlying reset region on every episode reset.

    Keeping easier regions alive prevents a later curriculum stage from
    completely overwriting a policy that already learned useful control there.
    """

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
