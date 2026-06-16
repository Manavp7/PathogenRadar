"""Tabular Q-learning agent for alert timing + evaluation vs the fixed-threshold policy."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..config import DATA_DIR, get_settings
from .env import (
    HOLD,
    N_ACTIONS,
    N_STATES,
    RAISE,
    RISK_BUCKETS,
    AlertingEnv,
    Episode,
    discretize,
    generate_episode,
)

MODELS_DIR = DATA_DIR / "models"
FIXED_ALERT_THRESHOLD = 55.0  # the Phase-1 fixed Alert boundary


class QLearningAgent:
    def __init__(
        self, alpha: float = 0.2, gamma: float = 0.95, epsilon: float = 0.2, seed: int = 0
    ):
        self.q = np.zeros((N_STATES, N_ACTIONS))
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.rng = np.random.default_rng(seed)

    def act(self, state: int, explore: bool = True) -> int:
        if explore and self.rng.random() < self.epsilon:
            return int(self.rng.integers(N_ACTIONS))
        return int(np.argmax(self.q[state]))

    def train(self, n_episodes: int = 4000, outbreak_prob: float = 0.5) -> None:
        env = AlertingEnv()
        for _ in range(n_episodes):
            outbreak = self.rng.random() < outbreak_prob
            ep = generate_episode(self.rng, outbreak)
            s = env.reset(ep)
            done = False
            while not done:
                a = self.act(s)
                s2, r, done = env.step(a)
                best_next = 0.0 if done else float(np.max(self.q[s2]))
                self.q[s, a] += self.alpha * (r + self.gamma * best_next - self.q[s, a])
                s = s2

    def policy_alert_threshold(self) -> float:
        """Lowest risk (with a sustained rising trend) at which the policy chooses to alert."""
        for r in range(RISK_BUCKETS):
            for growth in (3.0, 8.0):  # rising / steep
                state = discretize(r * 10 + 5, growth, persistent=1)
                if int(np.argmax(self.q[state])) == RAISE:
                    return float(r * 10)
        return FIXED_ALERT_THRESHOLD


def save_policy(agent: QLearningAgent, metrics: dict, region: str | None = None) -> Path:
    region = region or get_settings().region
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"rl_policy_{region}.json"
    payload = {
        "region": region,
        "alert_threshold": agent.policy_alert_threshold(),
        "q": agent.q.tolist(),
        "metrics": metrics,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return path


def load_alert_threshold(region: str | None = None) -> float | None:
    region = region or get_settings().region
    path = MODELS_DIR / f"rl_policy_{region}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as fh:
        return float(json.load(fh)["alert_threshold"])


# --------------------------------------------------------------------------------------
# Evaluation: RL policy vs fixed threshold
# --------------------------------------------------------------------------------------


def _detect_day_fixed(ep: Episode, threshold: float) -> int | None:
    hits = np.where(ep.risk >= threshold)[0]
    return int(hits[0]) if len(hits) else None


def _detect_day_rl(ep: Episode, agent: QLearningAgent) -> int | None:
    env = AlertingEnv()
    s = env.reset(ep)
    done = False
    while not done:
        a = agent.act(s, explore=False)
        if a == RAISE:
            return env.t
        s, _, done = env.step(HOLD)
    return None


def evaluate(agent: QLearningAgent, n: int = 1000, seed: int = 123) -> dict:
    rng = np.random.default_rng(seed)
    fixed_thr = FIXED_ALERT_THRESHOLD
    out = {"rl": _Stats(), "fixed": _Stats()}
    for _ in range(n):
        outbreak = rng.random() < 0.5
        ep = generate_episode(rng, outbreak)
        for name, day in (
            ("rl", _detect_day_rl(ep, agent)),
            ("fixed", _detect_day_fixed(ep, fixed_thr)),
        ):
            st = out[name]
            if outbreak:
                if day is not None and day >= ep.onset:
                    st.detected += 1
                    st.lead_days.append(day - ep.onset)
                else:
                    st.missed += 1
                st.outbreaks += 1
            else:
                if day is not None:
                    st.false_alarms += 1
                st.nulls += 1
    return {
        "rl": out["rl"].summary(),
        "fixed": out["fixed"].summary(),
        "rl_alert_threshold": agent.policy_alert_threshold(),
    }


class _Stats:
    def __init__(self):
        self.detected = self.missed = self.false_alarms = 0
        self.outbreaks = self.nulls = 0
        self.lead_days: list[int] = []

    def summary(self) -> dict:
        return {
            "detection_rate": round(self.detected / max(self.outbreaks, 1), 3),
            "false_alarm_rate": round(self.false_alarms / max(self.nulls, 1), 3),
            "mean_delay_days": round(float(np.mean(self.lead_days)) if self.lead_days else 0.0, 2),
        }
