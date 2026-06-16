"""Graph Neural Network spread forecaster (Phase 2).

A 2-layer GCN trained self-supervised on the metapopulation SEIR ground truth to predict
per-district spread probability at 7/14/21/30 days. PyTorch is an OPTIONAL dependency: if it
(or a trained model) is unavailable, callers fall back to the deterministic forecaster.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..config import DATA_DIR, get_settings
from ..domain.models import DistrictForecast, ForecastPoint
from ..regions import get_district_map
from .deterministic import DEFAULT_HORIZONS
from .mobility_graph import mobility_matrix, normalized_adjacency, populations

MODELS_DIR = DATA_DIR / "models"


def torch_available() -> bool:
    try:
        import torch  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


def _model_path(region: str) -> Path:
    return MODELS_DIR / f"gnn_{region}.pt"


def _meta_path(region: str) -> Path:
    return MODELS_DIR / f"gnn_{region}.json"


def _pop_norm(node_ids: list[str]) -> np.ndarray:
    pop = populations(node_ids)
    return np.log(pop) / np.log(pop.max())


def _build_gcn(in_dim: int, hidden: int, out_dim: int):
    import torch
    from torch import nn

    class GCN(nn.Module):
        def __init__(self):
            super().__init__()
            self.l1 = nn.Linear(in_dim, hidden)
            self.l2 = nn.Linear(hidden, out_dim)

        def forward(self, x, a_hat):
            h = torch.relu(a_hat @ self.l1(x))
            h = a_hat @ self.l2(h)
            return torch.sigmoid(h)

    return GCN()


# --------------------------------------------------------------------------------------
# Training
# --------------------------------------------------------------------------------------


def train_gnn(
    region: str | None = None,
    n_scenarios: int = 600,
    hidden: int = 16,
    epochs: int = 400,
    lr: float = 0.01,
    seed: int = 0,
    horizons: list[int] | None = None,
) -> dict:
    """Train the GCN on simulated outbreaks; save weights + metadata; return metrics."""
    import torch

    from ..simulation.metapop import horizon_targets

    region = region or get_settings().region
    horizons = horizons or DEFAULT_HORIZONS
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)

    node_ids, w = mobility_matrix()
    n = len(node_ids)
    a_hat = torch.tensor(normalized_adjacency(w), dtype=torch.float32)
    pop_norm = _pop_norm(node_ids)

    def make_scenario():
        seed_risk = {nid: 0.0 for nid in node_ids}
        k = rng.integers(1, 3)
        for j in rng.choice(n, size=k, replace=False):
            seed_risk[node_ids[j]] = float(rng.uniform(40, 100))
        _, targets = horizon_targets(seed_risk, horizons, node_ids=node_ids, w=w)
        x = np.stack([np.array([seed_risk[nid] / 100.0 for nid in node_ids]), pop_norm], axis=1)
        y = np.stack([targets[h] for h in horizons], axis=1)
        return x.astype(np.float32), y.astype(np.float32)

    data = [make_scenario() for _ in range(n_scenarios)]
    split = int(len(data) * 0.85)
    train, test = data[:split], data[split:]

    model = _build_gcn(in_dim=2, hidden=hidden, out_dim=len(horizons))
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = torch.nn.MSELoss()

    xs = [torch.tensor(x) for x, _ in train]
    ys = [torch.tensor(y) for _, y in train]
    for _ in range(epochs):
        opt.zero_grad()
        loss = sum(loss_fn(model(x, a_hat), y) for x, y in zip(xs, ys, strict=False)) / len(xs)
        loss.backward()
        opt.step()

    # Evaluation: GNN vs deterministic baseline against held-out ground truth.
    gnn_mae, det_mae = _evaluate(model, a_hat, test, node_ids, w, horizons)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), _model_path(region))
    meta = {
        "region": region,
        "node_ids": node_ids,
        "horizons": horizons,
        "hidden": hidden,
        "in_dim": 2,
        "gnn_mae": round(float(gnn_mae), 4),
        "deterministic_mae": round(float(det_mae), 4),
        "n_scenarios": n_scenarios,
        "epochs": epochs,
    }
    with open(_meta_path(region), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return meta


def _evaluate(model, a_hat, test, node_ids, w, horizons):
    import torch

    from .deterministic import forecast_spread

    gnn_err, det_err, count = 0.0, 0.0, 0
    with torch.no_grad():
        for x, y in test:
            pred = model(torch.tensor(x), a_hat).numpy()
            gnn_err += np.abs(pred - y).mean()
            # Deterministic baseline from the same seed risk (feature 0 * 100).
            seed_risk = {nid: float(x[i, 0] * 100.0) for i, nid in enumerate(node_ids)}
            fc = {f.district_id: f for f in forecast_spread(seed_risk, horizons)}
            det = np.array([[p.risk_probability for p in fc[nid].points] for nid in node_ids])
            det_err += np.abs(det - y).mean()
            count += 1
    return gnn_err / count, det_err / count


# --------------------------------------------------------------------------------------
# Inference
# --------------------------------------------------------------------------------------


def gnn_available(region: str | None = None) -> bool:
    region = region or get_settings().region
    return torch_available() and _model_path(region).exists() and _meta_path(region).exists()


def forecast_spread_gnn(
    current_risk: dict[str, float],
    horizons: list[int] | None = None,
    region: str | None = None,
) -> list[DistrictForecast]:
    """GNN inference producing the same DistrictForecast shape as the deterministic model."""
    import torch

    region = region or get_settings().region
    with open(_meta_path(region), encoding="utf-8") as fh:
        meta = json.load(fh)
    node_ids = meta["node_ids"]
    model_horizons = meta["horizons"]
    horizons = horizons or model_horizons

    _, w = mobility_matrix()
    a_hat = torch.tensor(normalized_adjacency(w), dtype=torch.float32)
    pop_norm = _pop_norm(node_ids)
    x = torch.tensor(
        np.stack(
            [np.array([current_risk.get(nid, 0.0) / 100.0 for nid in node_ids]), pop_norm],
            axis=1,
        ).astype(np.float32)
    )

    model = _build_gcn(in_dim=meta["in_dim"], hidden=meta["hidden"], out_dim=len(model_horizons))
    model.load_state_dict(torch.load(_model_path(region), weights_only=True))
    model.eval()
    with torch.no_grad():
        pred = model(x, a_hat).numpy()

    names = get_district_map()
    forecasts: list[DistrictForecast] = []
    for i, nid in enumerate(node_ids):
        points = [
            ForecastPoint(horizon_days=h, risk_probability=round(float(pred[i, j]), 4))
            for j, h in enumerate(model_horizons)
            if h in horizons
        ]
        forecasts.append(
            DistrictForecast(
                district_id=nid,
                district_name=names[nid].name if nid in names else nid,
                current_risk=round(current_risk.get(nid, 0.0), 2),
                points=points,
            )
        )
    forecasts.sort(key=lambda f: f.points[-1].risk_probability, reverse=True)
    return forecasts
