"""ABDM / FHIR hospital connector (Phase 3).

Implements the ``Connector`` interface against a FHIR-style endpoint (compatible with India's
ABDM health-data exchange shape). Hospital signals are read as FHIR ``Observation`` resources.

In a sandbox there is no live ABDM endpoint, so a runnable mock server
(``scripts/mock_fhir_server.py``) serves sample bundles built by ``build_observation_bundle``.
Production only needs a real ``FHIR_BASE_URL`` + credentials — no code change. Disabled by
default (offline preserved); enabled when ``FHIR_BASE_URL`` is set.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date

from ..domain.models import HOSPITAL_SIGNALS, District, SignalRecord, SignalType
from .base import Connector
from .synthetic import SyntheticConnector

logger = logging.getLogger("pathogenradar.acquisition.fhir")

SOURCE_ID = "abdm_fhir"
CODE_SYSTEM = "https://pathogenradar.org/fhir/signal"
HOSPITAL_CODES = {s.value for s in HOSPITAL_SIGNALS}

Transport = Callable[[str], dict]


# --------------------------------------------------------------------------------------
# Bundle building (shared by the mock server) + parsing
# --------------------------------------------------------------------------------------


def build_observation_bundle(districts: list[District], start: date, end: date) -> dict:
    """Build a FHIR Bundle of Observation resources for hospital signals (mock data source)."""
    records = SyntheticConnector().fetch(districts, start, end)
    entries = []
    for r in records:
        if r.signal_type.value not in HOSPITAL_CODES:
            continue
        entries.append(
            {
                "resource": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {"coding": [{"system": CODE_SYSTEM, "code": r.signal_type.value}]},
                    "subject": {"reference": f"Location/{r.district_id}"},
                    "effectiveDateTime": r.date.isoformat(),
                    "valueQuantity": {"value": r.value, "unit": "count"},
                }
            }
        )
    return {"resourceType": "Bundle", "type": "searchset", "total": len(entries), "entry": entries}


def parse_bundle(bundle: dict) -> list[SignalRecord]:
    records: list[SignalRecord] = []
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        if res.get("resourceType") != "Observation":
            continue
        coding = (res.get("code", {}).get("coding") or [{}])[0]
        code = coding.get("code")
        if code not in HOSPITAL_CODES:
            continue
        ref = res.get("subject", {}).get("reference", "")
        district_id = ref.split("/")[-1] if "/" in ref else ref
        when = res.get("effectiveDateTime")
        value = res.get("valueQuantity", {}).get("value")
        if not (district_id and when and value is not None):
            continue
        records.append(
            SignalRecord(
                district_id=district_id,
                date=date.fromisoformat(when[:10]),
                signal_type=SignalType(code),
                value=float(value),
                source_id=SOURCE_ID,
            )
        )
    return records


# --------------------------------------------------------------------------------------
# Connector
# --------------------------------------------------------------------------------------


def _requests_transport(base_url: str, timeout: float = 10.0) -> Transport:
    import requests

    def transport(path: str) -> dict:
        resp = requests.get(base_url.rstrip("/") + path, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    return transport


class FHIRConnector(Connector):
    source_id = SOURCE_ID
    provides = HOSPITAL_SIGNALS

    def __init__(self, base_url: str | None = None, transport: Transport | None = None):
        if transport is None and base_url is None:
            raise ValueError("FHIRConnector needs base_url or an injected transport")
        self.transport = transport or _requests_transport(base_url)

    @property
    def live(self) -> bool:
        return True

    def fetch(self, districts: list[District], start: date, end: date) -> list[SignalRecord]:
        records: list[SignalRecord] = []
        for d in districts:
            path = (
                f"/fhir/Observation?district={d.id}&start={start.isoformat()}&end={end.isoformat()}"
            )
            bundle = self.transport(path)
            records.extend(parse_bundle(bundle))
        return records
