"""P3.6 — federated learning (FedAvg) simulation."""

from __future__ import annotations

import numpy as np

from pathogenradar.federated import (
    accuracy,
    fedavg,
    make_clients,
    make_test_set,
    train_centralized,
)
from pathogenradar.federated.fedavg import N_FEATURES


def test_fedavg_matches_centralized():
    clients = make_clients(n_clients=5, per_client=240, seed=0)
    xt, yt = make_test_set()

    fw, fb, total = fedavg(clients, rounds=25, local_epochs=3, lr=0.5)
    cw, cb = train_centralized(clients)

    fed_acc = accuracy((fw, fb), xt, yt)
    central_acc = accuracy((cw, cb), xt, yt)

    assert total == 5 * 240
    assert fed_acc > 0.75  # learns a useful classifier
    assert abs(fed_acc - central_acc) < 0.05  # ~equivalent to pooling the data


def test_clients_are_non_iid():
    clients = make_clients(n_clients=4, seed=1)
    rates = [y.mean() for _, y in clients]
    # Outbreak base rates differ across clients (non-IID).
    assert max(rates) - min(rates) > 0.1


def test_fedavg_returns_weights_only():
    clients = make_clients(n_clients=3, per_client=120, seed=2)
    w, b, _ = fedavg(clients, rounds=10)
    # The server's output is just model parameters — no client data structures.
    assert isinstance(w, np.ndarray) and w.shape == (N_FEATURES,)
    assert isinstance(b, float)


def test_scales_with_more_clients():
    clients = make_clients(n_clients=8, per_client=150, seed=3)
    xt, yt = make_test_set()
    fw, fb, _ = fedavg(clients, rounds=25)
    assert accuracy((fw, fb), xt, yt) > 0.75
