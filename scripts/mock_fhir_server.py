"""Mock ABDM/FHIR server for demonstrating the FHIR hospital connector end-to-end.

Serves FHIR Observation bundles built from synthetic hospital data. Point the connector at it:
    FHIR_BASE_URL=http://localhost:8088 python scripts/seed.py   # (with connector wired in)
Run:  python scripts/mock_fhir_server.py    (serves on :8088)
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi import FastAPI, Query  # noqa: E402

from pathogenradar.acquisition.fhir import build_observation_bundle  # noqa: E402
from pathogenradar.regions import get_district  # noqa: E402

app = FastAPI(title="Mock ABDM/FHIR server")


@app.get("/fhir/Observation")
def observation(
    district: str = Query(...),
    start: str = Query(...),
    end: str = Query(...),
) -> dict:
    d = get_district(district)
    return build_observation_bundle([d], date.fromisoformat(start), date.fromisoformat(end))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8088)
