"""P3.3 — ABDM/FHIR hospital connector against the mock server."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from pathogenradar.acquisition.fhir import FHIRConnector, build_observation_bundle, parse_bundle
from pathogenradar.acquisition.service import build_connectors
from pathogenradar.domain.models import HOSPITAL_SIGNALS
from pathogenradar.regions import get_districts

HOSPITAL = {s.value for s in HOSPITAL_SIGNALS}


def _mock_transport():
    """Transport backed by the mock FHIR server's FastAPI app."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from mock_fhir_server import app

    client = TestClient(app)

    def transport(path: str) -> dict:
        return client.get(path).json()

    return transport


def test_bundle_roundtrip():
    districts = get_districts()[:2]
    bundle = build_observation_bundle(districts, date(2024, 1, 1), date(2024, 1, 3))
    assert bundle["resourceType"] == "Bundle"
    records = parse_bundle(bundle)
    assert records
    assert all(r.signal_type.value in HOSPITAL for r in records)
    assert all(r.source_id == "abdm_fhir" for r in records)


def test_connector_pulls_from_mock_server():
    conn = FHIRConnector(transport=_mock_transport())
    districts = get_districts()[:3]
    end = date(2024, 1, 10)
    start = end - timedelta(days=5)
    records = conn.fetch(districts, start, end)
    assert records
    got_districts = {r.district_id for r in records}
    assert got_districts == {d.id for d in districts}
    assert all(r.signal_type.value in HOSPITAL for r in records)


def test_fhir_disabled_by_default():
    # Offline default: only the synthetic connector is active.
    ids = {c.source_id for c in build_connectors()}
    assert "abdm_fhir" not in ids
    assert "synthetic" in ids


def test_safe_fetch_never_raises():
    def broken(_path: str) -> dict:
        raise ConnectionError("endpoint down")

    conn = FHIRConnector(transport=broken)
    res = conn.safe_fetch(get_districts()[:1], date(2024, 1, 1), date(2024, 1, 2))
    assert res.records == []
    assert res.status.startswith("error")
