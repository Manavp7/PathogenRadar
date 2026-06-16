"""Region helpers — region-aware and config-driven.

A region may define its districts explicitly (Kerala) or have them auto-derived from a GeoJSON
(Tamil Nadu): centroids, area-share populations and shared-boundary adjacency. Adding a state
is therefore configuration, not engineering.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from math import asin, cos, radians, sin, sqrt

import networkx as nx
import yaml

from .config import GEO_DIR, get_settings
from .domain.models import District


@lru_cache(maxsize=1)
def _all_regions() -> dict:
    settings = get_settings()
    with open(settings.region_config_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def available_regions() -> list[str]:
    return list(_all_regions().keys())


def _resolve(region: str | None) -> str:
    return region or get_settings().region


def region_meta(region: str | None = None) -> dict:
    region = _resolve(region)
    data = _all_regions()
    if region not in data:
        raise KeyError(f"Region '{region}' not in regions.yaml")
    return data[region]


def get_region_name(region: str | None = None) -> str:
    return region_meta(region)["name"]


def region_geojson_path(region: str | None = None):
    return GEO_DIR / region_meta(region)["geojson"]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


@lru_cache(maxsize=8)
def get_districts(region: str | None = None) -> list[District]:
    region = _resolve(region)
    meta = region_meta(region)
    if "districts" in meta:
        return [District(**d) for d in meta["districts"]]
    return _derive_districts(region, meta)


@lru_cache(maxsize=8)
def get_district_map(region: str | None = None) -> dict[str, District]:
    return {d.id: d for d in get_districts(_resolve(region))}


def get_district(district_id: str, region: str | None = None) -> District:
    return get_district_map(_resolve(region))[district_id]


# --------------------------------------------------------------------------------------
# GeoJSON-derived districts
# --------------------------------------------------------------------------------------


def _rings(geom: dict) -> list[list[list[float]]]:
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    if geom["type"] == "MultiPolygon":
        return [ring for poly in geom["coordinates"] for ring in poly]
    return []


def _ring_area_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    """Return (|area|, centroid_lon, centroid_lat) for a ring (lon/lat degrees, cos-corrected)."""
    n = len(ring)
    if n < 3:
        return 0.0, ring[0][0], ring[0][1]
    lat0 = radians(sum(p[1] for p in ring) / n)
    scale = cos(lat0)
    area = 0.0
    cx = cy = 0.0
    for i in range(n - 1):
        x1, y1 = ring[i][0] * scale, ring[i][1]
        x2, y2 = ring[i + 1][0] * scale, ring[i + 1][1]
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area *= 0.5
    if abs(area) < 1e-12:
        return 0.0, ring[0][0], ring[0][1]
    cx /= 6 * area
    cy /= 6 * area
    return abs(area), cx / scale, cy


def _derive_districts(region: str, meta: dict) -> list[District]:
    path = GEO_DIR / meta["geojson"]
    name_prop = meta.get("geojson_name_property", "DISTRICT")
    total_pop = int(meta.get("total_population", 1_000_000))
    with open(path, encoding="utf-8") as fh:
        gj = json.load(fh)

    feats = gj["features"]
    info = []  # (id, name, area, lon, lat, boundary_pts)
    for f in feats:
        name = f["properties"].get(name_prop) or f["properties"].get("district_id")
        did = f["properties"].get("district_id") or _slug(name)
        rings = _rings(f["geometry"])
        # Largest ring drives centroid; total area sums all rings.
        best = max(rings, key=len) if rings else [[0, 0], [0, 0], [0, 0]]
        area_total = sum(_ring_area_centroid(r)[0] for r in rings)
        _, lon, lat = _ring_area_centroid(best)
        pts = {(round(x, 3), round(y, 3)) for r in rings for x, y in r}
        info.append((did, name, area_total, lon, lat, pts))

    area_sum = sum(a for _, _, a, _, _, _ in info) or 1.0
    # Shared-boundary adjacency.
    neighbors: dict[str, list[str]] = {d[0]: [] for d in info}
    for i in range(len(info)):
        for j in range(i + 1, len(info)):
            if len(info[i][5] & info[j][5]) >= 2:
                neighbors[info[i][0]].append(info[j][0])
                neighbors[info[j][0]].append(info[i][0])

    districts = []
    for did, name, area, lon, lat, _ in info:
        pop = max(50_000, int(total_pop * area / area_sum))
        districts.append(
            District(id=did, name=name, population=pop, lat=lat, lon=lon, neighbors=neighbors[did])
        )
    return districts


# --------------------------------------------------------------------------------------
# District graph
# --------------------------------------------------------------------------------------


@lru_cache(maxsize=8)
def build_district_graph(region: str | None = None) -> nx.Graph:
    """Undirected adjacency graph weighted by inverse-distance gravity."""
    region = _resolve(region)

    def haversine_km(a: District, b: District) -> float:
        r = 6371.0
        dlat = radians(b.lat - a.lat)
        dlon = radians(b.lon - a.lon)
        h = sin(dlat / 2) ** 2 + cos(radians(a.lat)) * cos(radians(b.lat)) * sin(dlon / 2) ** 2
        return 2 * r * asin(sqrt(h))

    districts = get_districts(region)
    dmap = {d.id: d for d in districts}
    g = nx.Graph()
    for d in districts:
        g.add_node(d.id, population=d.population, lat=d.lat, lon=d.lon, name=d.name)

    for d in districts:
        for nb in d.neighbors:
            if nb not in dmap or g.has_edge(d.id, nb):
                continue
            other = dmap[nb]
            dist = max(haversine_km(d, other), 1.0)
            gravity = (d.population * other.population) / (dist * dist)
            g.add_edge(d.id, nb, distance_km=dist, gravity=gravity)

    gravities = [data["gravity"] for _, _, data in g.edges(data=True)]
    if gravities:
        gmax = max(gravities)
        for _, _, data in g.edges(data=True):
            data["weight"] = data["gravity"] / gmax
    return g
