"""P2.3 — RL alert optimization: environment, training, evaluation vs fixed policy."""

from __future__ import annotations

import numpy as np

from pathogenradar.rl.agent import QLearningAgent, evaluate, load_alert_threshold, save_policy
from pathogenradar.rl.env import HOLD, RAISE, AlertingEnv, generate_episode


def test_episode_generation():
    rng = np.random.default_rng(0)
    ob = generate_episode(rng, outbreak=True)
    assert ob.is_outbreak and ob.onset >= 0
    assert ob.risk.max() > 40  # an outbreak ramps up
    null = generate_episode(rng, outbreak=False)
    assert not null.is_outbreak and null.onset == -1


def test_env_rewards_detection_and_penalizes_false_alarm():
    rng = np.random.default_rng(1)
    env = AlertingEnv()

    outbreak = generate_episode(rng, outbreak=True)
    env.reset(outbreak)
    while env.t < outbreak.onset + 2:  # advance past onset
        env.step(HOLD)
    _, reward, done = env.step(RAISE)
    assert reward > 0 and done  # correct, timely detection is rewarded

    null = generate_episode(rng, outbreak=False)
    env.reset(null)
    _, reward, done = env.step(RAISE)
    assert reward < 0 and done  # alerting with no outbreak is penalised


def test_agent_beats_fixed_baseline():
    agent = QLearningAgent(seed=0)
    agent.train(n_episodes=5000)
    m = evaluate(agent, n=600)
    rl, fixed = m["rl"], m["fixed"]
    # Detect at least as well, with no more false alarms, and meaningfully earlier.
    assert rl["detection_rate"] >= 0.95
    assert rl["false_alarm_rate"] <= fixed["false_alarm_rate"] + 0.02
    assert rl["mean_delay_days"] < fixed["mean_delay_days"]


def test_policy_save_and_load():
    agent = QLearningAgent(seed=2)
    agent.train(n_episodes=2000)
    save_policy(agent, {"note": "test"})
    thr = load_alert_threshold()
    assert thr is not None
    assert 0 <= thr <= 100
