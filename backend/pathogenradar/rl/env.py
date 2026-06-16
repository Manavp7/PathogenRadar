"""Outbreak-alerting environment + synthetic risk-trajectory generator.

An episode is a per-district daily risk trajectory that either develops into a true outbreak
or is a noisy null. The agent decides each day whether to HOLD or RAISE an alert. Reward
favours early correct detection and penalises false alarms and misses.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

HOLD, RAISE = 0, 1
N_ACTIONS = 2

# State discretisation.
RISK_BUCKETS = 10  # 0..100 in tens
GROWTH_BUCKETS = 4  # falling / flat / rising / steep
PERSIST_STATES = 2  # whether risk has been elevated for >=2 consecutive days
N_STATES = RISK_BUCKETS * GROWTH_BUCKETS * PERSIST_STATES
PERSIST_FLOOR = 15.0  # risk above this on consecutive days = persistent (not a transient spike)


@dataclass
class Episode:
    risk: np.ndarray
    is_outbreak: bool
    onset: int


def generate_episode(rng: np.random.Generator, outbreak: bool, length: int = 60) -> Episode:
    """Generate a risk trajectory (0..100)."""
    risk = np.clip(rng.normal(3.0, 2.5, size=length), 0, 100)
    onset = -1
    if outbreak:
        onset = int(rng.integers(8, 30))
        peak = rng.uniform(60, 95)
        ramp = rng.uniform(8, 16)
        for t in range(onset, length):
            logistic = peak / (1.0 + np.exp(-(t - onset - ramp / 2) / (ramp / 4)))
            risk[t] = np.clip(logistic + rng.normal(0, 3), 0, 100)
    else:
        # Null episodes get transient noise spikes to tempt false alarms.
        for _ in range(int(rng.integers(1, 4))):
            d = int(rng.integers(0, length))
            risk[d] = min(100.0, risk[d] + rng.uniform(20, 45))
    return Episode(risk=risk, is_outbreak=outbreak, onset=onset)


def discretize(risk: float, growth: float, persistent: int = 0) -> int:
    r = min(RISK_BUCKETS - 1, int(risk // 10))
    if growth < -1:
        g = 0
    elif growth < 1:
        g = 1
    elif growth < 6:
        g = 2
    else:
        g = 3
    return (r * GROWTH_BUCKETS + g) * PERSIST_STATES + persistent


class AlertingEnv:
    def __init__(
        self, miss_penalty: float = 8.0, fp_penalty: float = 30.0, detect_reward: float = 12.0
    ):
        self.miss_penalty = miss_penalty
        self.fp_penalty = fp_penalty
        self.detect_reward = detect_reward

    def reset(self, ep: Episode) -> int:
        self.ep = ep
        self.t = 0
        return self._state()

    def _growth(self) -> float:
        if self.t < 3:
            return 0.0
        return float(self.ep.risk[self.t] - self.ep.risk[self.t - 3])

    def _persistent(self) -> int:
        if self.t < 1:
            return 0
        now = self.ep.risk[self.t] >= PERSIST_FLOOR
        prev = self.ep.risk[self.t - 1] >= PERSIST_FLOOR
        return int(now and prev)

    def _state(self) -> int:
        return discretize(float(self.ep.risk[self.t]), self._growth(), self._persistent())

    def step(self, action: int) -> tuple[int, float, bool]:
        if action == RAISE:
            if self.ep.is_outbreak and self.t >= self.ep.onset:
                delay = self.t - self.ep.onset
                reward = max(1.0, self.detect_reward - 0.4 * delay)
            else:
                reward = -self.fp_penalty  # alerted on noise or before any real onset
            return self._state(), reward, True

        # HOLD -> advance time.
        self.t += 1
        if self.t >= len(self.ep.risk):
            # Episode ended without alerting.
            reward = -self.miss_penalty if self.ep.is_outbreak else 2.0
            return self._state() if self.t < len(self.ep.risk) else 0, reward, True
        return self._state(), 0.0, False
