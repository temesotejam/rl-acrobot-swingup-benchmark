from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from PIL import Image, ImageDraw


def wrap_angle(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


@dataclass(frozen=True)
class PhysicsConfig:
    gravity: float = 9.8
    link_length_1_m: float = 1.0
    link_length_2_m: float = 1.0
    link_mass_1_kg: float = 1.0
    link_mass_2_kg: float = 1.0
    link_com_1_m: float = 0.5
    link_com_2_m: float = 0.5
    link_moi_1_kg_m2: float = 1.0
    link_moi_2_kg_m2: float = 1.0
    max_torque_nm: float = 1.0
    joint1_damping_nm_per_rad_s: float = 0.02
    joint2_damping_nm_per_rad_s: float = 0.02
    motor_time_constant_s: float = 0.05
    dt_s: float = 0.02
    max_episode_s: float = 20.0
    max_velocity_1_rad_s: float = 4.0 * math.pi
    max_velocity_2_rad_s: float = 9.0 * math.pi

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class SensorNoiseConfig:
    enabled: bool = True
    joint1_angle_noise_std_deg: float = 0.25
    joint1_angle_bias_std_deg: float = 1.0
    joint2_angle_noise_std_deg: float = 0.25
    joint2_angle_bias_std_deg: float = 1.0
    joint1_gyro_noise_std_dps: float = 0.10
    joint1_gyro_bias_std_dps: float = 0.30
    joint2_gyro_noise_std_dps: float = 0.10
    joint2_gyro_bias_std_dps: float = 0.30

    def to_dict(self) -> dict[str, float | bool]:
        return asdict(self)


class ContinuousAcrobotEnv(gym.Env):
    """Continuous-torque Acrobot using Sutton/Barto book dynamics.

    theta1=0 means link 1 points downward. theta2 is relative to link 1.
    Only joint 2 is actuated. The action is normalized to [-1, 1].
    """

    metadata = {"render_modes": ["rgb_array"], "render_fps": 25}
    RESET_MODES = {"near_upright", "upper", "full", "downward_mix", "evaluation_downward"}

    def __init__(
        self,
        physics: PhysicsConfig | None = None,
        reset_mode: str = "downward_mix",
        render_mode: str | None = None,
    ):
        super().__init__()
        self.physics = physics or PhysicsConfig()
        self.render_mode = render_mode
        self.set_reset_mode(reset_mode)
        self.action_space = spaces.Box(-1.0, 1.0, shape=(1,), dtype=np.float32)
        high = np.array(
            [1.0, 1.0, 1.0, 1.0, self.physics.max_velocity_1_rad_s, self.physics.max_velocity_2_rad_s],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)
        self.state = np.zeros(4, dtype=np.float64)
        self.commanded_torque_nm = 0.0
        self.actual_torque_nm = 0.0
        self.steps = 0

    @property
    def max_steps(self) -> int:
        return int(round(self.physics.max_episode_s / self.physics.dt_s))

    def set_reset_mode(self, mode: str) -> None:
        if mode not in self.RESET_MODES:
            raise ValueError(f"Unknown reset mode: {mode}")
        self.reset_mode = mode

    def _sample_angles(self) -> tuple[float, float]:
        rng = self.np_random
        if self.reset_mode == "near_upright":
            return wrap_angle(math.pi + math.radians(rng.uniform(-20.0, 20.0))), math.radians(rng.uniform(-15.0, 15.0))
        if self.reset_mode == "upper":
            return wrap_angle(math.pi + math.radians(rng.uniform(-70.0, 70.0))), math.radians(rng.uniform(-60.0, 60.0))
        if self.reset_mode == "full":
            if rng.random() < 0.25:
                return wrap_angle(math.pi + math.radians(rng.uniform(-35.0, 35.0))), math.radians(rng.uniform(-30.0, 30.0))
            return rng.uniform(-math.pi, math.pi), rng.uniform(-math.pi, math.pi)
        if self.reset_mode == "downward_mix":
            q = rng.random()
            if q < 0.70:
                return math.radians(rng.uniform(-15.0, 15.0)), math.radians(rng.uniform(-15.0, 15.0))
            if q < 0.85:
                return rng.uniform(-math.pi, math.pi), rng.uniform(-math.pi, math.pi)
            return wrap_angle(math.pi + math.radians(rng.uniform(-30.0, 30.0))), math.radians(rng.uniform(-25.0, 25.0))
        return math.radians(rng.uniform(-5.0, 5.0)), math.radians(rng.uniform(-5.0, 5.0))

    def _observation(self) -> np.ndarray:
        theta1, theta2, dtheta1, dtheta2 = self.state
        return np.array(
            [math.cos(theta1), math.sin(theta1), math.cos(theta2), math.sin(theta2), dtheta1, dtheta2],
            dtype=np.float32,
        )

    def tip_height_m(self, state: np.ndarray | None = None) -> float:
        theta1, theta2 = (self.state if state is None else state)[:2]
        p = self.physics
        return float(-p.link_length_1_m * math.cos(theta1) - p.link_length_2_m * math.cos(theta1 + theta2))

    def _info(self) -> dict:
        return {
            "true_state": self.state.astype(float).tolist(),
            "commanded_torque_nm": float(self.commanded_torque_nm),
            "actual_torque_nm": float(self.actual_torque_nm),
            "tip_height_m": self.tip_height_m(),
            "time_s": float(self.steps * self.physics.dt_s),
            "reset_mode": self.reset_mode,
        }

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        del options
        theta1, theta2 = self._sample_angles()
        self.state = np.array(
            [theta1, theta2, self.np_random.uniform(-0.15, 0.15), self.np_random.uniform(-0.15, 0.15)],
            dtype=np.float64,
        )
        self.commanded_torque_nm = 0.0
        self.actual_torque_nm = 0.0
        self.steps = 0
        return self._observation(), self._info()

    def _derivative(self, state: np.ndarray, actuator_torque: float) -> np.ndarray:
        p = self.physics
        theta1, theta2, dtheta1, dtheta2 = [float(v) for v in state]
        m1, m2 = p.link_mass_1_kg, p.link_mass_2_kg
        l1 = p.link_length_1_m
        lc1, lc2 = p.link_com_1_m, p.link_com_2_m
        i1, i2 = p.link_moi_1_kg_m2, p.link_moi_2_kg_m2
        g = p.gravity

        d1 = m1 * lc1**2 + m2 * (l1**2 + lc2**2 + 2.0 * l1 * lc2 * math.cos(theta2)) + i1 + i2
        d2 = m2 * (lc2**2 + l1 * lc2 * math.cos(theta2)) + i2
        phi2 = m2 * lc2 * g * math.cos(theta1 + theta2 - math.pi / 2.0)
        phi1 = (
            -m2 * l1 * lc2 * dtheta2**2 * math.sin(theta2)
            - 2.0 * m2 * l1 * lc2 * dtheta2 * dtheta1 * math.sin(theta2)
            + (m1 * lc1 + m2 * l1) * g * math.cos(theta1 - math.pi / 2.0)
            + phi2
        )

        tau1 = -p.joint1_damping_nm_per_rad_s * dtheta1
        tau2 = actuator_torque - p.joint2_damping_nm_per_rad_s * dtheta2
        denominator = m2 * lc2**2 + i2 - d2**2 / d1
        coriolis2 = m2 * l1 * lc2 * dtheta1**2 * math.sin(theta2)
        ddtheta2 = (tau2 - d2 / d1 * tau1 + d2 / d1 * phi1 - coriolis2 - phi2) / denominator
        ddtheta1 = (tau1 - d2 * ddtheta2 - phi1) / d1
        return np.array([dtheta1, dtheta2, ddtheta1, ddtheta2], dtype=np.float64)

    def _rk4(self, state: np.ndarray, torque: float) -> np.ndarray:
        dt = self.physics.dt_s
        k1 = self._derivative(state, torque)
        k2 = self._derivative(state + 0.5 * dt * k1, torque)
        k3 = self._derivative(state + 0.5 * dt * k2, torque)
        k4 = self._derivative(state + dt * k3, torque)
        return state + dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0

    def step(self, action: np.ndarray):
        p = self.physics
        normalized = float(np.clip(np.asarray(action).reshape(-1)[0], -1.0, 1.0))
        self.commanded_torque_nm = normalized * p.max_torque_nm
        alpha = 1.0 - math.exp(-p.dt_s / max(p.motor_time_constant_s, 1e-6))
        self.actual_torque_nm += alpha * (self.commanded_torque_nm - self.actual_torque_nm)

        next_state = self._rk4(self.state, self.actual_torque_nm)
        next_state[0] = wrap_angle(float(next_state[0]))
        next_state[1] = wrap_angle(float(next_state[1]))
        next_state[2] = float(np.clip(next_state[2], -p.max_velocity_1_rad_s, p.max_velocity_1_rad_s))
        next_state[3] = float(np.clip(next_state[3], -p.max_velocity_2_rad_s, p.max_velocity_2_rad_s))
        self.state = next_state
        self.steps += 1

        theta1, theta2, dtheta1, dtheta2 = self.state
        height = self.tip_height_m()
        height_score = float(np.clip((height + 2.0) / 4.0, 0.0, 1.0))
        extension = 0.5 * (1.0 + math.cos(theta2))
        motion = min((abs(dtheta1) + 0.5 * abs(dtheta2)) / 5.0, 1.0)
        reward = (
            0.05
            + 0.95 * height_score
            + 0.30 * height_score**2
            + 0.10 * height_score * extension
            + 0.03 * (1.0 - height_score) * motion
            - 0.004 * (dtheta1 / 4.0) ** 2
            - 0.002 * (dtheta2 / 8.0) ** 2
            - 0.004 * (self.actual_torque_nm / p.max_torque_nm) ** 2
        )
        if height >= 1.0:
            reward += 0.40
        if height >= 1.4 and abs(dtheta1) <= 0.8 and abs(dtheta2) <= 1.2:
            reward += 0.80

        terminated = False
        truncated = bool(self.steps >= self.max_steps)
        return self._observation(), float(reward), terminated, truncated, self._info()

    def render(self):
        if self.render_mode != "rgb_array":
            return None
        width = height_px = 600
        image = Image.new("RGB", (width, height_px), (248, 249, 251))
        draw = ImageDraw.Draw(image)
        pivot = np.array([width / 2.0, height_px / 2.0], dtype=float)
        scale = 120.0
        theta1, theta2 = self.state[:2]
        p1 = pivot + np.array([p.physics_dummy if False else self.physics.link_length_1_m * math.sin(theta1) * scale, self.physics.link_length_1_m * math.cos(theta1) * scale])
        p2 = p1 + np.array([self.physics.link_length_2_m * math.sin(theta1 + theta2) * scale, self.physics.link_length_2_m * math.cos(theta1 + theta2) * scale])
        target_y = pivot[1] - 1.0 * scale
        draw.line((40, target_y, width - 40, target_y), fill=(130, 130, 135), width=2)
        draw.line((*pivot, *p1), fill=(57, 106, 177), width=14)
        draw.line((*p1, *p2), fill=(205, 73, 62), width=14)
        for point in [pivot, p1, p2]:
            x, y = point
            draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(30, 35, 42))
        draw.text((18, 18), f"mode = {self.reset_mode}", fill=(30, 35, 42))
        draw.text((18, 42), f"tip height = {self.tip_height_m():+.2f} m", fill=(30, 35, 42))
        draw.text((18, 66), f"torque = {self.actual_torque_nm:+.2f} Nm", fill=(30, 35, 42))
        draw.text((18, 90), f"t = {self.steps * self.physics.dt_s:.2f} s", fill=(30, 35, 42))
        return np.asarray(image, dtype=np.uint8)


class ConsumerSensorWrapper(gym.ObservationWrapper):
    def __init__(self, env: gym.Env, noise: SensorNoiseConfig | None = None):
        super().__init__(env)
        self.noise = noise or SensorNoiseConfig()
        self._bias = np.zeros(4, dtype=np.float64)

    def reset(self, **kwargs):
        observation, info = self.env.reset(**kwargs)
        if self.noise.enabled:
            self._bias = np.array(
                [
                    math.radians(self.np_random.normal(0.0, self.noise.joint1_angle_bias_std_deg)),
                    math.radians(self.np_random.normal(0.0, self.noise.joint2_angle_bias_std_deg)),
                    math.radians(self.np_random.normal(0.0, self.noise.joint1_gyro_bias_std_dps)),
                    math.radians(self.np_random.normal(0.0, self.noise.joint2_gyro_bias_std_dps)),
                ],
                dtype=np.float64,
            )
        else:
            self._bias[:] = 0.0
        return self.observation(observation), info

    def observation(self, observation: np.ndarray) -> np.ndarray:
        if not self.noise.enabled:
            return np.asarray(observation, dtype=np.float32)
        theta1 = math.atan2(float(observation[1]), float(observation[0])) + self._bias[0]
        theta2 = math.atan2(float(observation[3]), float(observation[2])) + self._bias[1]
        theta1 += math.radians(self.np_random.normal(0.0, self.noise.joint1_angle_noise_std_deg))
        theta2 += math.radians(self.np_random.normal(0.0, self.noise.joint2_angle_noise_std_deg))
        dtheta1 = float(observation[4]) + self._bias[2] + math.radians(self.np_random.normal(0.0, self.noise.joint1_gyro_noise_std_dps))
        dtheta2 = float(observation[5]) + self._bias[3] + math.radians(self.np_random.normal(0.0, self.noise.joint2_gyro_noise_std_dps))
        return np.array([math.cos(theta1), math.sin(theta1), math.cos(theta2), math.sin(theta2), dtheta1, dtheta2], dtype=np.float32)

    def set_reset_mode(self, mode: str) -> None:
        self.unwrapped.set_reset_mode(mode)


def make_acrobot_env(
    physics: PhysicsConfig | None = None,
    sensor_noise: SensorNoiseConfig | None = None,
    reset_mode: str = "downward_mix",
    render_mode: str | None = None,
) -> gym.Env:
    return ConsumerSensorWrapper(
        ContinuousAcrobotEnv(physics=physics, reset_mode=reset_mode, render_mode=render_mode),
        noise=sensor_noise,
    )
