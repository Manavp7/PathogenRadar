from fastapi.testclient import TestClient

from pathogenradar_api.main import create_app

client = TestClient(create_app())


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_district_intelligence_endpoint() -> None:
    response = client.get("/intelligence/district/kerala-ernakulam")
    payload = response.json()

    assert response.status_code == 200
    assert payload["risk_assessment"]["risk_score"] >= 50
    assert payload["forecast"]["points"]
    assert payload["explanations"]
    assert payload["recommendations"]
    assert payload["report"]["summary"]


def test_forecast_endpoint() -> None:
    response = client.get("/forecasts/district/kerala-ernakulam")

    assert response.status_code == 200
    assert [point["horizon_days"] for point in response.json()["points"]] == [7, 14, 21, 30]


def test_simulation_endpoint() -> None:
    response = client.post(
        "/simulations/district/kerala-ernakulam",
        json={"interventions": ["vector_control"], "compliance": 0.7, "horizon_days": 30},
    )

    assert response.status_code == 200
    assert response.json()["estimated_cases_averted"] > 0


def test_alerts_and_reports_endpoints() -> None:
    alerts = client.get("/alerts")
    report = client.get("/reports/executive")

    assert alerts.status_code == 200
    assert report.status_code == 200
    assert report.json()["recommended_actions"]
