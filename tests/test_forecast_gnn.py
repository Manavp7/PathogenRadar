"""P2.1 — mobility graph, metapopulation ground truth, and the GNN forecaster.

The GNN tests are skipped automatically when PyTorch (optional) is not installed; the
deterministic fallback is always tested so the platform is verified either way.
"""

from __future__ import annotations

import pytest

from pathogenradar.forecast.gnn import torch_available
from pathogenradar.forecast.mobility_graph import mobility_matrix, normalized_adjacency
from pathogenradar.forecast.service import active_model, forecast_current
from pathogenradar.simulation.metapop import simulate_metapop


def test_mobility_matrix_symmetric_and_normalized():
    nodes, w = mobility_matrix()
    assert len(nodes) == 14
    assert (w == w.T).all()
    a_hat = normalized_adjacency(w)
    assert a_hat.shape == (14, 14)


def test_metapop_spreads_from_seed():
    node_ids, cum = simulate_metapop({"ernakulam": 90.0}, days=30)
    idx = {n: i for i, n in enumerate(node_ids)}
    # Seed district accumulates the most infection; a far district lags.
    assert cum[30][idx["ernakulam"]] > cum[30][idx["kasaragod"]]
    # Cumulative incidence is non-decreasing.
    assert (cum[30] >= cum[0] - 1e-9).all()


def test_service_falls_back_to_deterministic(monkeypatch):
    monkeypatch.delenv("FORECAST_MODEL", raising=False)
    assert active_model() == "deterministic"
    fc = forecast_current({"ernakulam": 90.0})
    assert len(fc) == 14
    assert all(0.0 <= p.risk_probability <= 1.0 for f in fc for p in f.points)


@pytest.mark.skipif(not torch_available(), reason="PyTorch (optional) not installed")
def test_gnn_trains_and_beats_baseline():
    from pathogenradar.forecast.gnn import forecast_spread_gnn, gnn_available, train_gnn

    meta = train_gnn(n_scenarios=150, epochs=150, seed=1)
    assert meta["gnn_mae"] < meta["deterministic_mae"]
    assert gnn_available()

    fc = forecast_spread_gnn({"ernakulam": 85.0})
    assert len(fc) == 14
    assert all(0.0 <= p.risk_probability <= 1.0 for f in fc for p in f.points)


@pytest.mark.skipif(not torch_available(), reason="PyTorch (optional) not installed")
def test_service_uses_gnn_when_selected(monkeypatch):
    from pathogenradar.forecast.gnn import gnn_available, train_gnn

    if not gnn_available():
        train_gnn(n_scenarios=120, epochs=120, seed=2)
    monkeypatch.setenv("FORECAST_MODEL", "gnn")
    assert active_model() == "gnn"
    fc = forecast_current({"ernakulam": 90.0})
    assert len(fc) == 14
