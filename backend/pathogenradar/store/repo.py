"""Storage layer: signals as Parquet, derived artifacts as Parquet/JSON, plus a small
SQLite catalog. Deliberately simple and file-based for the MVP; swappable later.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from ..config import SEED_DIR
from ..domain.models import SignalRecord

SIGNALS_PARQUET = "signals.parquet"
RISK_PARQUET = "risk.parquet"
QUALITY_PARQUET = "quality.parquet"
ALERTS_JSON = "alerts.json"
CATALOG_DB = "catalog.db"


def _region() -> str:
    from ..config import get_settings

    return get_settings().region


def region_dir(region: str | None = None) -> Path:
    d = SEED_DIR / (region or _region())
    return d


def _path(name: str, region: str | None = None) -> Path:
    return region_dir(region) / name


# --------------------------------------------------------------------------------------
# Signals
# --------------------------------------------------------------------------------------


def signals_to_frame(records: list[SignalRecord]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "district_id": r.district_id,
                "date": pd.Timestamp(r.date),
                "signal_type": r.signal_type.value,
                "value": r.value,
                "source_id": r.source_id,
            }
            for r in records
        ]
    )


def write_signals(df: pd.DataFrame, region: str | None = None) -> Path:
    region_dir(region).mkdir(parents=True, exist_ok=True)
    path = _path(SIGNALS_PARQUET, region)
    df.to_parquet(path, index=False)
    _register(SIGNALS_PARQUET, len(df), region)
    return path


def read_signals(region: str | None = None) -> pd.DataFrame:
    path = _path(SIGNALS_PARQUET, region)
    if not path.exists():
        return pd.DataFrame(columns=["district_id", "date", "signal_type", "value", "source_id"])
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


# --------------------------------------------------------------------------------------
# Generic frame artifacts (risk, quality)
# --------------------------------------------------------------------------------------


def write_frame(df: pd.DataFrame, name: str, region: str | None = None) -> Path:
    region_dir(region).mkdir(parents=True, exist_ok=True)
    path = _path(name, region)
    df.to_parquet(path, index=False)
    _register(name, len(df), region)
    return path


def read_frame(name: str, region: str | None = None) -> pd.DataFrame:
    path = _path(name, region)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


# --------------------------------------------------------------------------------------
# JSON artifacts (alerts, etc.)
# --------------------------------------------------------------------------------------


def write_json(obj, name: str, region: str | None = None) -> Path:
    region_dir(region).mkdir(parents=True, exist_ok=True)
    path = _path(name, region)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, default=str, indent=2)
    return path


def read_json(name: str, default=None, region: str | None = None):
    path = _path(name, region)
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------------------
# SQLite catalog (lightweight provenance / freshness tracking)
# --------------------------------------------------------------------------------------


def _register(artifact: str, rows: int, region: str | None = None) -> None:
    region_dir(region).mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(_path(CATALOG_DB, region))
    try:
        con.execute(
            "CREATE TABLE IF NOT EXISTS catalog ("
            "artifact TEXT PRIMARY KEY, rows INTEGER, updated_at TEXT)"
        )
        con.execute(
            "INSERT INTO catalog(artifact, rows, updated_at) VALUES(?,?,datetime('now')) "
            "ON CONFLICT(artifact) DO UPDATE SET "
            "rows=excluded.rows, updated_at=excluded.updated_at",
            (artifact, rows),
        )
        con.commit()
    finally:
        con.close()


def catalog(region: str | None = None) -> list[dict]:
    db = _path(CATALOG_DB, region)
    if not db.exists():
        return []
    con = sqlite3.connect(db)
    try:
        rows = con.execute("SELECT artifact, rows, updated_at FROM catalog").fetchall()
        return [{"artifact": a, "rows": r, "updated_at": u} for a, r, u in rows]
    finally:
        con.close()
