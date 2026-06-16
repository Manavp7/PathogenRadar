"""Train the RL alert-timing agent and compare it to the fixed-threshold policy.

Usage:  python scripts/train_rl.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from pathogenradar.rl.agent import QLearningAgent, evaluate, save_policy  # noqa: E402


def main() -> None:
    print("Training RL alert-timing agent (tabular Q-learning)...")
    agent = QLearningAgent(seed=0)
    agent.train(n_episodes=6000)
    metrics = evaluate(agent)
    save_policy(agent, metrics)

    rl, fixed = metrics["rl"], metrics["fixed"]
    print(f"  learned alert threshold : {metrics['rl_alert_threshold']:.0f}/100 (fixed = 55)")
    print(
        f"  RL    : detect {rl['detection_rate']:.0%}  "
        f"FP {rl['false_alarm_rate']:.0%}  delay {rl['mean_delay_days']}d"
    )
    print(
        f"  Fixed : detect {fixed['detection_rate']:.0%}  "
        f"FP {fixed['false_alarm_rate']:.0%}  delay {fixed['mean_delay_days']}d"
    )
    print("Set ALERTING_POLICY=rl to use the learned threshold.")


if __name__ == "__main__":
    main()
