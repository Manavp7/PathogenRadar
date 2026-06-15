"""Region helpers: load districts from config as typed domain objects."""

from __future__ import annotations

from functools import lru_cache
from math import asin, cos, radians, sin, sqrt

import networkx as nx

from .config import load_region_config
from .domain.models import District


@lru_cache(maxsize=1)
def get_districts() -> list[District]:
    cfg = load_region_config()
    return [District(**d) for d in cfg["districts"]]


@lru_cache(maxsize=1)
def get_district_map() -> dict[str, District]:
    return {d.id: d for d in get_districts()}


def get_district(district_id: str) -> District:
    return get_district_map()[district_id]


def get_region_name() -> str:
    return load_region_config()["name"]


@lru_cache(maxsize=1)
def build_district_graph() -> nx.Graph:
    """Undirected adjacency graph of districts, weighted by inverse-distance gravity.

    Edge weight ~ (pop_i * pop_j) / distance^2, normalised. Used by the deterministic
    spread-forecast diffusion model in Phase 1 (a GNN replaces/augments this in Phase 2).
    """

    def haversine_km(a: District, b: District) -> float:
        r = 6371.0
        dlat = radians(b.lat - a.lat)
        dlon = radians(b.lon - a.lon)
        h = sin(dlat / 2) ** 2 + cos(radians(a.lat)) * cos(radians(b.lat)) * sin(dlon / 2) ** 2
        return 2 * r * asin(sqrt(h))

    districts = get_districts()
    dmap = {d.id: d for d in districts}
    g = nx.Graph()
    for d in districts:
        g.add_node(d.id, population=d.population, lat=d.lat, lon=d.lon, name=d.name)

    for d in districts:
        for nb in d.neighbors:
            if g.has_edge(d.id, nb):
                continue
            other = dmap[nb]
            dist = max(haversine_km(d, other), 1.0)
            gravity = (d.population * other.population) / (dist * dist)
            g.add_edge(d.id, nb, distance_km=dist, gravity=gravity)

    # Normalise gravity weights to 0..1 for stable diffusion.
    gravities = [data["gravity"] for _, _, data in g.edges(data=True)]
    if gravities:
        gmax = max(gravities)
        for _, _, data in g.edges(data=True):
            data["weight"] = data["gravity"] / gmax
    return g
