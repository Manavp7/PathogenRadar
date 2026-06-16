"""Federated averaging (FedAvg) over a logistic-regression outbreak classifier.

Pure NumPy. Each client trains locally from the shared global weights; the server averages the
returned weights (sample-size weighted). Only weights cross the boundary — never raw data.
"""

from __future__ import annotations

import numpy as np

N_FEATURES = 5  # [search, hospital, social, wastewater, weather] anomaly intensities


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def _make_dataset(rng: np.random.Generator, n: int, outbreak_rate: float):
    """Synthesize labeled feature vectors. Outbreak rows have elevated signals."""
    y = (rng.random(n) < outbreak_rate).astype(float)
    x = np.empty((n, N_FEATURES))
    for i in range(n):
        center = 0.58 if y[i] else 0.38  # overlapping classes -> non-trivial task
        x[i] = np.clip(rng.normal(center, 0.22, N_FEATURES), 0, 1)
    return x, y


def make_clients(n_clients: int = 4, per_client: int = 200, seed: int = 0):
    """Non-IID clients: different outbreak base rates per client (district)."""
    rng = np.random.default_rng(seed)
    rates = np.linspace(0.25, 0.6, n_clients)
    return [_make_dataset(rng, per_client, float(rates[c])) for c in range(n_clients)]


def make_test_set(seed: int = 999, n: int = 600):
    return _make_dataset(np.random.default_rng(seed), n, outbreak_rate=0.45)


def _train_local(x, y, w, b, epochs, lr):
    """Local gradient descent from the provided (global) weights. Data stays local."""
    w = w.copy()
    n = len(y)
    for _ in range(epochs):
        p = _sigmoid(x @ w + b)
        err = p - y
        w -= lr * (x.T @ err) / n
        b -= lr * err.mean()
    return w, b


def fedavg(clients, rounds: int = 20, local_epochs: int = 3, lr: float = 0.5):
    """Run FedAvg. The server only ever receives per-client weights + sample counts."""
    w = np.zeros(N_FEATURES)
    b = 0.0
    sizes = np.array([len(y) for _, y in clients], dtype=float)
    total = sizes.sum()
    for _ in range(rounds):
        weights, biases = [], []
        for x, y in clients:
            lw, lb = _train_local(x, y, w, b, local_epochs, lr)  # runs "on" the client
            weights.append(lw)
            biases.append(lb)
        w = np.average(np.stack(weights), axis=0, weights=sizes)
        b = float(np.average(np.array(biases), weights=sizes))
    return w, b, int(total)


def train_centralized(clients, epochs: int = 60, lr: float = 0.5):
    """Baseline: pool all data and train once (the privacy-violating alternative)."""
    x = np.vstack([c[0] for c in clients])
    y = np.concatenate([c[1] for c in clients])
    return _train_local(x, y, np.zeros(N_FEATURES), 0.0, epochs, lr)


def accuracy(model, x, y) -> float:
    w, b = model[0], model[1]
    pred = (_sigmoid(x @ w + b) >= 0.5).astype(float)
    return float((pred == y).mean())
