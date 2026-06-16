"""Federated learning (Phase 3 — SIMULATION).

Demonstrates privacy-preserving training across institutions: each simulated client (district /
hospital) trains a local outbreak-classifier on its OWN data; only model weights are shared and
averaged (FedAvg). Raw data never leaves a client. This simulates the federated protocol — a
production deployment would run clients on separate nodes.
"""

from .fedavg import (
    accuracy,
    fedavg,
    make_clients,
    make_test_set,
    train_centralized,
)

__all__ = ["accuracy", "fedavg", "make_clients", "make_test_set", "train_centralized"]
