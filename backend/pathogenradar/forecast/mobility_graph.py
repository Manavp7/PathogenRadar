"""Mobility graph utilities for spread modelling.

Builds a weighted district graph (adjacency + gravity mobility) and the normalised adjacency
matrices used by the metapopulation simulator and the GNN.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from ..regions import build_district_graph


def mobility_matrix(graph: nx.Graph | None = None) -> tuple[list[str], np.ndarray]:
    """Return (node_ids, W) where W[i, j] is the gravity mobility weight between districts."""
    graph = graph if graph is not None else build_district_graph()
    nodes = list(graph.nodes())
    idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    w = np.zeros((n, n), dtype=float)
    for u, v, data in graph.edges(data=True):
        weight = float(data.get("weight", 0.5))
        w[idx[u], idx[v]] = weight
        w[idx[v], idx[u]] = weight
    return nodes, w


def normalized_adjacency(w: np.ndarray) -> np.ndarray:
    """Symmetric-normalised adjacency with self-loops:  D^-1/2 (W + I) D^-1/2."""
    a = w + np.eye(w.shape[0])
    deg = a.sum(axis=1)
    dinv = np.diag(1.0 / np.sqrt(np.clip(deg, 1e-9, None)))
    return dinv @ a @ dinv


def populations(node_ids: list[str]) -> np.ndarray:
    from ..regions import get_district_map

    dmap = get_district_map()
    return np.array([float(dmap[n].population) for n in node_ids])
