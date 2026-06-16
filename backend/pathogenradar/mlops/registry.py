"""Versioned model registry (JSON metadata + optional artifacts).

Each registered model gets an incrementing version with metrics, params and lineage, so model
provenance is auditable and rollbacks are possible. File-based for the MVP; the same interface
could back onto MLflow/S3 in production.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from ..config import DATA_DIR

REGISTRY_DIR = DATA_DIR / "models" / "registry"


def _model_dir(name: str) -> Path:
    return REGISTRY_DIR / name


def history(name: str) -> list[dict]:
    d = _model_dir(name)
    if not d.exists():
        return []
    versions = []
    for vdir in sorted(d.iterdir()):
        meta = vdir / "metadata.json"
        if meta.exists():
            with open(meta, encoding="utf-8") as fh:
                versions.append(json.load(fh))
    versions.sort(key=lambda m: m["version"])
    return versions


def register_model(
    name: str,
    metrics: dict | None = None,
    params: dict | None = None,
    artifact_src: str | Path | None = None,
    framework: str = "custom",
) -> dict:
    """Register a new model version. Returns the metadata."""
    existing = history(name)
    version = f"v{len(existing) + 1}"
    vdir = _model_dir(name) / version
    vdir.mkdir(parents=True, exist_ok=True)

    artifact_rel = None
    if artifact_src is not None and Path(artifact_src).exists():
        dest = vdir / Path(artifact_src).name
        shutil.copy2(artifact_src, dest)
        artifact_rel = str(dest.relative_to(DATA_DIR))

    meta = {
        "name": name,
        "version": version,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "framework": framework,
        "metrics": metrics or {},
        "params": params or {},
        "artifact": artifact_rel,
    }
    with open(vdir / "metadata.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return meta


def list_latest() -> list[dict]:
    """Latest version metadata for every registered model."""
    if not REGISTRY_DIR.exists():
        return []
    out = []
    for mdir in sorted(REGISTRY_DIR.iterdir()):
        if not mdir.is_dir():
            continue
        versions = history(mdir.name)
        if versions:
            latest = versions[-1]
            out.append({**latest, "total_versions": len(versions)})
    return out
