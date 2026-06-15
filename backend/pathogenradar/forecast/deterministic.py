"""Deterministic spread forecast (Phase 1).

Diffuses current district risk across the gravity-weighted adjacency graph using a discrete
SI-style process on the network. This is fully deterministic and explainable — a learned GNN
spread model is a Phase 2 upgrade that plugs in behind the same interface.

Update rule per day for district i:
    pressure_i = Σ_j w_ij · p_j           (inflow from connected districts)
    growth_i   = intrinsic · p_i + beta · pressure_i
    p_i(t+1)   = p_i + (1 - p_i) · growth_i      (saturating, bounded to [0, 1])
"""

from __future__ import annotations

import networkx as nx

from ..domain.models import DistrictForecast, ForecastPoint
from ..regions import build_district_graph, get_district_map

DEFAULT_HORIZONS = [7, 14, 21, 30]


def forecast_spread(
    current_risk: dict[str, float],
    horizons: list[int] | None = None,
    beta: float = 0.085,
    intrinsic: float = 0.04,
    graph: nx.Graph | None = None,
) -> list[DistrictForecast]:
    """Forecast per-district spread probability at the given horizons.

    ``current_risk`` maps district_id -> risk score (0..100).
    """
    horizons = sorted(horizons or DEFAULT_HORIZONS)
    graph = graph if graph is not None else build_district_graph()
    names = get_district_map()

    nodes = list(graph.nodes())
    p = {n: max(0.0, min(1.0, current_risk.get(n, 0.0) / 100.0)) for n in nodes}

    # Precompute weighted neighbour lists.
    neighbours = {
        n: [(nb, graph[n][nb].get("weight", 0.5)) for nb in graph.neighbors(n)] for n in nodes
    }

    max_h = max(horizons)
    snapshots: dict[int, dict[str, float]] = {}
    for day in range(1, max_h + 1):
        new_p = {}
        for n in nodes:
            pressure = sum(w * p[nb] for nb, w in neighbours[n])
            growth = intrinsic * p[n] + beta * pressure
            new_p[n] = min(1.0, p[n] + (1.0 - p[n]) * growth)
        p = new_p
        if day in horizons:
            snapshots[day] = dict(p)

    forecasts: list[DistrictForecast] = []
    for n in nodes:
        district = names.get(n)
        points = [
            ForecastPoint(horizon_days=h, risk_probability=round(snapshots[h][n], 4))
            for h in horizons
        ]
        forecasts.append(
            DistrictForecast(
                district_id=n,
                district_name=district.name if district else n,
                current_risk=round(current_risk.get(n, 0.0), 2),
                points=points,
            )
        )
    forecasts.sort(key=lambda f: f.points[-1].risk_probability, reverse=True)
    return forecasts
