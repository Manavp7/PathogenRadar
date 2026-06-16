"""Phase 3.2 — region config, district graph, and storage round-trip."""

from __future__ import annotations

from datetime import date

import pandas as pd

from pathogenradar.domain.models import SignalRecord, SignalType
from pathogenradar.regions import build_district_graph, get_district_map, get_districts
from pathogenradar.store import repo


def test_kerala_has_14_districts():
    districts = get_districts()
    assert len(districts) == 14
    ids = {d.id for d in districts}
    assert "thiruvananthapuram" in ids
    assert "kasaragod" in ids


def test_adjacency_is_symmetric():
    dmap = get_district_map()
    for d in dmap.values():
        for nb in d.neighbors:
            assert nb in dmap, f"{d.id} references unknown neighbor {nb}"
            assert d.id in dmap[nb].neighbors, f"adjacency not symmetric: {d.id}<->{nb}"


def test_district_graph_connected_and_weighted():
    g = build_district_graph()
    assert g.number_of_nodes() == 14
    assert g.number_of_edges() > 0
    # Kerala is a contiguous strip; the adjacency graph must be connected.
    import networkx as nx

    assert nx.is_connected(g)
    for _, _, data in g.edges(data=True):
        assert 0 < data["weight"] <= 1.0


def test_signal_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(repo, "SEED_DIR", tmp_path)
    records = [
        SignalRecord(
            district_id="ernakulam",
            date=date(2024, 1, 1),
            signal_type=SignalType.HOSPITAL_ADMISSIONS,
            value=42.0,
            source_id="synthetic",
        )
    ]
    df = repo.signals_to_frame(records)
    repo.write_signals(df)
    out = repo.read_signals()
    assert len(out) == 1
    assert out.iloc[0]["value"] == 42.0
    assert pd.Timestamp(out.iloc[0]["date"]).date() == date(2024, 1, 1)
