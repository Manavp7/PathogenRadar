"""Retrain Phase-2 models and register versioned artifacts in the model registry.

Usage:  python scripts/retrain.py     (GNN requires requirements-ml.txt)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from pathogenradar.config import DATA_DIR  # noqa: E402
from pathogenradar.detection.novelty import NoveltyDetector  # noqa: E402
from pathogenradar.mlops.registry import list_latest, register_model  # noqa: E402
from pathogenradar.rl.agent import QLearningAgent, evaluate, save_policy  # noqa: E402


def main() -> None:
    print("Retraining models + registering versions...")

    # RL alerting policy (numpy; always available).
    agent = QLearningAgent(seed=0)
    agent.train(n_episodes=6000)
    metrics = evaluate(agent)
    save_policy(agent, metrics)
    register_model(
        "rl_alerting",
        metrics={
            "rl_false_alarm_rate": metrics["rl"]["false_alarm_rate"],
            "rl_mean_delay_days": metrics["rl"]["mean_delay_days"],
            "fixed_mean_delay_days": metrics["fixed"]["mean_delay_days"],
        },
        params={"alert_threshold": metrics["rl_alert_threshold"]},
        framework="numpy-qlearning",
    )
    print("  registered rl_alerting")

    # Novelty PCA detector (config-only; deterministic).
    nd = NoveltyDetector()
    register_model(
        "novelty_pca",
        metrics={"p95_recon_error": round(nd.p95, 4)},
        params={"signals": len(nd.signals)},
        framework="sklearn-pca",
    )
    print("  registered novelty_pca")

    # GNN spread forecaster (optional torch).
    try:
        from pathogenradar.forecast.gnn import torch_available, train_gnn

        if torch_available():
            meta = train_gnn()
            artifact = DATA_DIR / "models" / f"gnn_{meta['region']}.pt"
            register_model(
                "gnn_spread",
                metrics={
                    "gnn_mae": meta["gnn_mae"],
                    "deterministic_mae": meta["deterministic_mae"],
                },
                params={"hidden": meta["hidden"], "epochs": meta["epochs"]},
                artifact_src=artifact,
                framework="pytorch-gcn",
            )
            print("  registered gnn_spread")
        else:
            print("  skipped gnn_spread (torch not installed)")
    except Exception as exc:  # noqa: BLE001
        print(f"  gnn_spread training failed: {exc}")

    print("\nRegistry:")
    for m in list_latest():
        print(f"  {m['name']:14s} {m['version']}  metrics={m['metrics']}")


if __name__ == "__main__":
    main()
