"""Metapopulation SEIR on the district mobility graph.

This is the richer "ground truth" spatial process: each district runs local SEIR dynamics
coupled to its neighbours through mobility. The deterministic diffusion forecast is a cheap
approximation of this; the Phase-2 GNN is trained to predict it. Pure NumPy (no torch).
"""

from __future__ import annotations

import numpy as np

from ..forecast.mobility_graph import mobility_matrix

DEFAULT_HORIZONS = [7, 14, 21, 30]


def simulate_metapop(
    seed_risk: dict[str, float],
    *,
    r0: float = 2.4,
    incubation_days: float = 5.0,
    infectious_days: float = 6.0,
    coupling: float = 0.35,
    i0_scale: float = 2e-4,
    days: int = 30,
    node_ids: list[str] | None = None,
    w: np.ndarray | None = None,
) -> tuple[list[str], np.ndarray]:
    """Simulate spatial SEIR.

    Returns (node_ids, cumulative_incidence_fraction[day, node]) for day in 0..days.
    ``seed_risk`` maps district_id -> current risk (0..100), used to seed initial infections.
    """
    if node_ids is None or w is None:
        node_ids, w = mobility_matrix()
    n = len(node_ids)

    beta = r0 / infectious_days
    sigma = 1.0 / max(incubation_days, 0.5)
    gamma = 1.0 / max(infectious_days, 0.5)

    idx = {nid: i for i, nid in enumerate(node_ids)}
    i = np.zeros(n)
    for nid, risk in seed_risk.items():
        if nid in idx:
            i[idx[nid]] = max(0.0, risk / 100.0) * i0_scale
    e = i.copy()
    s = 1.0 - i - e  # work in fractions per district
    r = np.zeros(n)

    # Row-normalise mobility for the coupling term.
    row = w.sum(axis=1, keepdims=True)
    m = np.divide(w, row, out=np.zeros_like(w), where=row > 0)

    cum = np.zeros((days + 1, n))
    cum[0] = i + r
    for t in range(1, days + 1):
        # Effective infectious pressure = local + mobility-coupled neighbours.
        pressure = i + coupling * (m @ i)
        new_e = beta * s * pressure
        new_i = sigma * e
        new_r = gamma * i
        s = np.clip(s - new_e, 0.0, 1.0)
        e = np.clip(e + new_e - new_i, 0.0, 1.0)
        i = np.clip(i + new_i - new_r, 0.0, 1.0)
        r = r + new_r
        cum[t] = np.clip(1.0 - s, 0.0, 1.0)  # cumulative ever-infected fraction
    return node_ids, cum


def spread_probability(cum_fraction: np.ndarray, k: float = 60.0) -> np.ndarray:
    """Map cumulative incidence fraction to a 0..1 spread probability."""
    return 1.0 - np.exp(-k * cum_fraction)


def horizon_targets(
    seed_risk: dict[str, float],
    horizons: list[int] | None = None,
    **kwargs,
) -> tuple[list[str], dict[int, np.ndarray]]:
    """Spread probability per district at each horizon (ground-truth labels for the GNN)."""
    horizons = horizons or DEFAULT_HORIZONS
    node_ids, cum = simulate_metapop(seed_risk, days=max(horizons), **kwargs)
    return node_ids, {h: spread_probability(cum[h]) for h in horizons}
