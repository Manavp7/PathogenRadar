"""P3.5 — MLOps: model registry versioning + drift monitoring."""

from __future__ import annotations

from datetime import date, timedelta

from pathogenradar.acquisition.synthetic import dengue_outbreak
from pathogenradar.mlops import drift_report
from pathogenradar.mlops import registry as reg
from pathogenradar.pipeline import run_pipeline


def test_registry_versioning(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "REGISTRY_DIR", tmp_path / "registry")

    m1 = reg.register_model("demo_model", metrics={"mae": 0.5}, framework="test")
    m2 = reg.register_model("demo_model", metrics={"mae": 0.3}, framework="test")
    assert m1["version"] == "v1"
    assert m2["version"] == "v2"

    latest = {m["name"]: m for m in reg.list_latest()}
    assert latest["demo_model"]["version"] == "v2"
    assert latest["demo_model"]["total_versions"] == 2
    assert latest["demo_model"]["metrics"]["mae"] == 0.3

    assert len(reg.history("demo_model")) == 2


def test_drift_report_on_outbreak():
    end = date(2024, 6, 30)
    run_pipeline(
        end - timedelta(days=120),
        end,
        outbreaks=[dengue_outbreak("ernakulam", end - timedelta(days=22), 2.2)],
        persist=True,
        region="kerala",
    )
    report = drift_report("kerala")
    assert report["signals"]
    assert report["max_psi"] >= 0.0
    # Each signal carries a PSI + drift level.
    assert all("psi" in s and "level" in s for s in report["signals"])


def test_drift_report_empty_region():
    report = drift_report("does_not_exist")
    assert report["signals"] == []
    assert report["retrain_recommended"] is False
