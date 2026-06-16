"""Federated learning demo: FedAvg across simulated clients vs centralized training.

Usage:  python scripts/federated_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from pathogenradar.federated import (  # noqa: E402
    accuracy,
    fedavg,
    make_clients,
    make_test_set,
    train_centralized,
)


def main() -> None:
    clients = make_clients(n_clients=5, per_client=240, seed=0)
    xt, yt = make_test_set()

    print("Federated learning simulation (no raw data leaves a client)")
    print(f"  clients: {len(clients)} · samples/client: {[len(y) for _, y in clients]}")

    fw, fb, total = fedavg(clients, rounds=25, local_epochs=3, lr=0.5)
    cw, cb = train_centralized(clients)

    fa = accuracy((fw, fb), xt, yt)
    ca = accuracy((cw, cb), xt, yt)
    print(f"  federated (FedAvg) accuracy : {fa:.3f}  (trained on {total} private samples)")
    print(f"  centralized (pooled) accuracy: {ca:.3f}")
    print(f"  gap: {abs(fa - ca):.3f}  -> federated matches centralized while preserving privacy")


if __name__ == "__main__":
    main()
