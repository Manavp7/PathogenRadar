"""P3.4 — RBAC + audit governance."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from pathogenradar.security.rbac import Role, has_permission, resolve_principal

KEYS = "vkey:viewer,akey:analyst,adkey:admin"


def test_open_dev_mode_is_admin(monkeypatch):
    monkeypatch.delenv("PATHOGENRADAR_API_KEY", raising=False)
    monkeypatch.delenv("PATHOGENRADAR_API_KEYS", raising=False)
    from pathogenradar.config import get_settings

    get_settings.cache_clear()
    p = resolve_principal(None)
    assert p is not None and p.role == Role.ADMIN.value and p.authenticated is False
    get_settings.cache_clear()


def test_role_permissions():
    assert has_permission("viewer", "read")
    assert not has_permission("viewer", "simulate")
    assert has_permission("analyst", "simulate")
    assert not has_permission("analyst", "admin")
    assert has_permission("admin", "admin")


@pytest.fixture
def rbac_client(monkeypatch):
    from pathogenradar.acquisition.synthetic import dengue_outbreak
    from pathogenradar.config import get_settings
    from pathogenradar.pipeline import run_pipeline

    end = date(2024, 6, 30)
    run_pipeline(
        end - timedelta(days=90),
        end,
        outbreaks=[dengue_outbreak("ernakulam", end - timedelta(days=22), 1.9)],
        persist=True,
    )
    monkeypatch.setenv("PATHOGENRADAR_API_KEYS", KEYS)
    get_settings.cache_clear()

    from pathogenradar.api.main import app
    from pathogenradar.api.state import state

    state.reload()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def _h(key):
    return {"X-API-Key": key}


def test_unauthenticated_blocked(rbac_client):
    assert rbac_client.get("/api/risk").status_code == 401


def test_viewer_can_read_not_simulate_or_audit(rbac_client):
    assert rbac_client.get("/api/risk", headers=_h("vkey")).status_code == 200
    sim = rbac_client.post(
        "/api/simulation",
        headers=_h("vkey"),
        json={"district_id": "ernakulam", "disease": "dengue"},
    )
    assert sim.status_code == 403
    assert rbac_client.get("/api/audit", headers=_h("vkey")).status_code == 403


def test_analyst_can_simulate_not_audit(rbac_client):
    sim = rbac_client.post(
        "/api/simulation",
        headers=_h("akey"),
        json={"district_id": "ernakulam", "disease": "dengue"},
    )
    assert sim.status_code == 200
    assert rbac_client.get("/api/audit", headers=_h("akey")).status_code == 403


def test_admin_can_access_audit(rbac_client):
    r = rbac_client.get("/api/audit", headers=_h("adkey"))
    assert r.status_code == 200
    entries = r.json()
    assert isinstance(entries, list)
    # Audit captured prior requests with role attribution.
    assert any(e["path"].startswith("/api/") for e in entries)
