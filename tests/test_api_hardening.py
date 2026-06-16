"""H3 — API robustness: error envelope, pagination, validation, API-key enforcement."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

KEY = "secret-test-key"
H = {"X-API-Key": KEY}


@pytest.fixture
def keyed_client(monkeypatch):
    from pathogenradar.acquisition.synthetic import dengue_outbreak
    from pathogenradar.config import get_settings
    from pathogenradar.pipeline import run_pipeline

    end = date(2024, 6, 30)
    start = end - timedelta(days=90)
    run_pipeline(
        start,
        end,
        outbreaks=[dengue_outbreak("ernakulam", end - timedelta(days=22), 1.9)],
        persist=True,
    )

    monkeypatch.setenv("PATHOGENRADAR_API_KEY", KEY)
    get_settings.cache_clear()

    from pathogenradar.api.main import app
    from pathogenradar.api.state import state

    state.reload()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def test_health_is_open(keyed_client):
    # Health never requires a key.
    assert keyed_client.get("/health").status_code == 200


def test_api_key_enforced(keyed_client):
    assert keyed_client.get("/api/risk").status_code == 401
    assert keyed_client.get("/api/risk", headers=H).status_code == 200


def test_error_envelope_on_404(keyed_client):
    r = keyed_client.get("/api/risk/nowhere", headers=H)
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == 404
    assert "message" in body["error"]


def test_pagination(keyed_client):
    full = keyed_client.get("/api/risk", headers=H).json()
    assert len(full) == 14
    limited = keyed_client.get("/api/risk?limit=3", headers=H).json()
    assert len(limited) == 3
    offset = keyed_client.get("/api/risk?limit=3&offset=3", headers=H).json()
    assert offset[0]["district_id"] != limited[0]["district_id"]


def test_validation_error_envelope(keyed_client):
    # days below the allowed minimum -> 422 with structured details.
    r = keyed_client.post(
        "/api/simulation",
        headers=H,
        json={"district_id": "ernakulam", "disease": "dengue", "days": 5},
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == 422
    assert body["error"]["details"]


def test_unknown_disease_is_400(keyed_client):
    r = keyed_client.post(
        "/api/simulation",
        headers=H,
        json={"district_id": "ernakulam", "disease": "nonexistent"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == 400
