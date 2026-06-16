"""Phase 3.9 — API surface (FastAPI TestClient against a seeded scenario)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    # Seed a deterministic dengue scenario so the API has data to serve.
    from pathogenradar.acquisition.synthetic import dengue_outbreak
    from pathogenradar.pipeline import run_pipeline

    end = date(2024, 6, 30)
    start = end - timedelta(days=120)
    outbreak = dengue_outbreak("ernakulam", end - timedelta(days=22), magnitude=1.9)
    run_pipeline(start, end, outbreaks=[outbreak], persist=True)

    from pathogenradar.api.main import app
    from pathogenradar.api.state import state

    state.reload()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_meta_and_districts(client):
    assert client.get("/api/meta").json()["region"] == "Kerala"
    districts = client.get("/api/districts").json()
    assert len(districts) == 14


def test_geojson(client):
    gj = client.get("/api/geojson").json()
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) == 14


def test_risk_endpoints(client):
    risk = client.get("/api/risk").json()
    assert len(risk) == 14
    ek = client.get("/api/risk/ernakulam").json()
    assert ek["latest"]["district_id"] == "ernakulam"
    assert len(ek["timeseries"]) > 0
    assert client.get("/api/risk/nowhere").status_code == 404


def test_forecast_and_alerts(client):
    fc = client.get("/api/forecast").json()
    assert len(fc) == 14
    alerts = client.get("/api/alerts").json()
    # The seeded outbreak should raise at least one alert, led by Ernakulam.
    assert any(a["district_id"] == "ernakulam" for a in alerts)


def test_simulation(client):
    body = {
        "district_id": "ernakulam",
        "disease": "dengue",
        "days": 120,
        "intervention": {"masking": 0.6, "vaccination_rate": 0.2},
    }
    r = client.post("/api/simulation", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["peak_infected_baseline"] > 0
    assert data["cases_averted"] is not None


def test_diseases_and_briefing(client):
    diseases = client.get("/api/diseases").json()
    assert any(d["id"] == "dengue" for d in diseases)
    briefing = client.get("/api/reports/briefing").json()
    assert briefing["provider"] == "template"
    assert "Kerala" in briefing["body"]


def test_signals_endpoint(client):
    sig = client.get("/api/signals/ernakulam").json()
    assert "series" in sig
    assert "hospital_admissions" in sig["series"]


def test_system_status(client):
    sys = client.get("/api/system").json()
    assert sys["offline_mode"] is True  # default: no external services
    assert sys["connectors"]["synthetic"]["enabled"] is True
    assert sys["llm"]["provider"] == "template"
    assert sys["llm"]["required"] is False
    assert sys["security"]["api_key_required"] is False
    assert sys["forecast_model"] == "deterministic"  # default; gnn is opt-in
    assert sys["alerting"]["policy"] == "fixed"
    assert isinstance(sys["warnings"], list)


def test_timeline_and_historical_snapshot(client):
    timeline = client.get("/api/timeline").json()
    assert len(timeline["dates"]) > 30
    assert "mean" in timeline["series"][0]

    # A historical snapshot before the outbreak should be calmer than the latest.
    early_date = timeline["dates"][5]
    early = client.get(f"/api/risk?as_of={early_date}").json()
    assert len(early) == 14
    early_top = max(r["risk_score"] for r in early)
    latest_top = max(r["risk_score"] for r in client.get("/api/risk").json())
    assert early_top <= latest_top

    # Unknown date -> 404.
    assert client.get("/api/risk?as_of=1999-01-01").status_code == 404
