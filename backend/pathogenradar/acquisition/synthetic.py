"""Synthetic multi-signal generator — the primary data source for the MVP.

Produces realistic daily time series per district for every signal family, with seasonal
baselines, weekly patterns and noise, plus *injectable outbreak events* so the detection
pipeline has real anomalies to find. Fully deterministic given a seed.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from ..domain.models import DiseaseCategory, District, SignalRecord, SignalType
from .base import Connector

SOURCE_ID = "synthetic"


# --------------------------------------------------------------------------------------
# Outbreak events
# --------------------------------------------------------------------------------------


@dataclass
class OutbreakEvent:
    """A disease outbreak injected into the synthetic stream."""

    disease: str
    category: DiseaseCategory
    district_id: str
    start: date
    duration_days: int = 50
    peak_day_offset: int = 22
    magnitude: float = 1.0  # overall strength multiplier (~0.5 mild .. 2.5 severe)
    # How strongly each signal responds to this outbreak (relative weights).
    signal_weights: dict[SignalType, float] = field(default_factory=dict)

    def pulse(self, d: date) -> float:
        """Smooth outbreak intensity in [0, 1] for a given date (Gaussian pulse)."""
        t = (d - self.start).days
        if t < 0 or t > self.duration_days:
            return 0.0
        sigma = max(self.duration_days / 5.0, 4.0)
        return math.exp(-((t - self.peak_day_offset) ** 2) / (2 * sigma * sigma))


def dengue_outbreak(
    district_id: str,
    start: date,
    magnitude: float = 1.6,
    duration_days: int = 50,
    peak_day_offset: int = 22,
) -> OutbreakEvent:
    """A vector-borne (dengue) outbreak: fever/rash searches, admissions, PCR, wastewater."""
    return OutbreakEvent(
        disease="Dengue",
        category=DiseaseCategory.VECTOR,
        district_id=district_id,
        start=start,
        duration_days=duration_days,
        peak_day_offset=peak_day_offset,
        magnitude=magnitude,
        signal_weights={
            SignalType.SEARCH_FEVER: 1.0,
            SignalType.SEARCH_RASH: 0.9,
            SignalType.SEARCH_VOMITING: 0.4,
            SignalType.HOSPITAL_ADMISSIONS: 0.8,
            SignalType.ICU_OCCUPANCY: 0.6,
            SignalType.MORTALITY: 0.3,
            SignalType.LAB_PCR_REQUESTS: 1.0,
            SignalType.SOCIAL_MENTIONS: 0.8,
            SignalType.WASTEWATER_VIRAL_LOAD: 0.5,
        },
    )


def respiratory_outbreak(
    district_id: str,
    start: date,
    magnitude: float = 1.4,
    duration_days: int = 50,
    peak_day_offset: int = 22,
) -> OutbreakEvent:
    return OutbreakEvent(
        disease="Influenza-like illness",
        category=DiseaseCategory.RESPIRATORY,
        district_id=district_id,
        start=start,
        duration_days=duration_days,
        peak_day_offset=peak_day_offset,
        magnitude=magnitude,
        signal_weights={
            SignalType.SEARCH_FEVER: 0.9,
            SignalType.SEARCH_COUGH: 1.0,
            SignalType.HOSPITAL_ADMISSIONS: 0.7,
            SignalType.ICU_OCCUPANCY: 0.7,
            SignalType.VENTILATOR_USAGE: 0.6,
            SignalType.LAB_PCR_REQUESTS: 0.8,
            SignalType.SOCIAL_MENTIONS: 0.7,
            SignalType.WASTEWATER_VIRAL_LOAD: 0.9,
        },
    )


def waterborne_outbreak(
    district_id: str,
    start: date,
    magnitude: float = 1.5,
    duration_days: int = 35,
    peak_day_offset: int = 14,
) -> OutbreakEvent:
    return OutbreakEvent(
        disease="Acute diarrheal disease",
        category=DiseaseCategory.WATERBORNE,
        district_id=district_id,
        start=start,
        duration_days=duration_days,
        peak_day_offset=peak_day_offset,
        magnitude=magnitude,
        signal_weights={
            SignalType.SEARCH_DIARRHEA: 1.0,
            SignalType.SEARCH_VOMITING: 0.9,
            SignalType.HOSPITAL_ADMISSIONS: 0.7,
            SignalType.LAB_PCR_REQUESTS: 0.6,
            SignalType.SOCIAL_MENTIONS: 0.7,
            SignalType.WASTEWATER_VIRAL_LOAD: 1.0,
        },
    )


# --------------------------------------------------------------------------------------
# Baseline signal levels
# --------------------------------------------------------------------------------------

# Per-capita-ish baselines (per day). Count signals scale with population.
_POP_SCALED_BASE = {
    SignalType.HOSPITAL_ADMISSIONS: 1 / 60000,
    SignalType.ICU_OCCUPANCY: 1 / 400000,
    SignalType.VENTILATOR_USAGE: 1 / 1500000,
    SignalType.MORTALITY: 1 / 800000,
    SignalType.LAB_PCR_REQUESTS: 1 / 20000,
    SignalType.SOCIAL_MENTIONS: 1 / 25000,
}
# Index-style baselines (Google-Trends-like 0..100 or arbitrary index), pop-independent.
_INDEX_BASE = {
    SignalType.SEARCH_FEVER: 32.0,
    SignalType.SEARCH_COUGH: 30.0,
    SignalType.SEARCH_RASH: 18.0,
    SignalType.SEARCH_VOMITING: 16.0,
    SignalType.SEARCH_DIARRHEA: 20.0,
    SignalType.WASTEWATER_VIRAL_LOAD: 180.0,
}
_ALL_SIGNALS = (
    list(_POP_SCALED_BASE)
    + list(_INDEX_BASE)
    + [
        SignalType.WEATHER_TEMP,
        SignalType.WEATHER_HUMIDITY,
        SignalType.WEATHER_RAINFALL,
    ]
)


def _seed_for(district_id: str, signal: SignalType) -> int:
    key = f"{district_id}:{signal.value}".encode()
    return int(hashlib.sha256(key).hexdigest(), 16) % (2**32)


def _baseline(signal: SignalType, district: District, day_of_year: int) -> float:
    """Deterministic seasonal baseline (no noise)."""
    # Weekly + annual seasonality multipliers.
    annual = 1.0 + 0.15 * math.sin(2 * math.pi * day_of_year / 365.0)

    if signal in _POP_SCALED_BASE:
        return district.population * _POP_SCALED_BASE[signal] * annual
    if signal in _INDEX_BASE:
        return _INDEX_BASE[signal] * annual

    # Weather (Kerala tropical climate) — monsoon-driven rainfall.
    if signal is SignalType.WEATHER_TEMP:
        return 29.0 + 3.0 * math.sin(2 * math.pi * (day_of_year - 100) / 365.0)
    if signal is SignalType.WEATHER_HUMIDITY:
        return 78.0 + 10.0 * _monsoon(day_of_year)
    if signal is SignalType.WEATHER_RAINFALL:
        return 2.0 + 22.0 * _monsoon(day_of_year)
    return 0.0


def _monsoon(day_of_year: int) -> float:
    """0..1 monsoon intensity — peaks Jun–Sep (SW monsoon) for Kerala."""
    return max(0.0, math.sin(math.pi * (day_of_year - 150) / 180.0)) ** 1.5


# --------------------------------------------------------------------------------------
# Connector
# --------------------------------------------------------------------------------------


class SyntheticConnector(Connector):
    source_id = SOURCE_ID
    provides = _ALL_SIGNALS

    def __init__(self, outbreaks: list[OutbreakEvent] | None = None, noise: float = 0.12):
        self.outbreaks = outbreaks or []
        self.noise = noise

    @property
    def live(self) -> bool:
        return False

    def _outbreak_factor(self, signal: SignalType, district_id: str, d: date) -> float:
        """Multiplicative bump (>= 0) added to a signal from active outbreaks."""
        total = 0.0
        for ob in self.outbreaks:
            if ob.district_id != district_id:
                continue
            w = ob.signal_weights.get(signal)
            if not w:
                continue
            total += w * ob.magnitude * ob.pulse(d)
        return total

    def fetch(self, districts: list[District], start: date, end: date) -> list[SignalRecord]:
        records: list[SignalRecord] = []
        ndays = (end - start).days + 1
        dates = [start + timedelta(days=i) for i in range(ndays)]

        for district in districts:
            for signal in self.provides:
                rng = np.random.default_rng(_seed_for(district.id, signal))
                for d in dates:
                    base = _baseline(signal, district, d.timetuple().tm_yday)
                    # Multiplicative gaussian noise (weather gets gentler noise).
                    noise_scale = 0.04 if signal in WEATHER_SET else self.noise
                    val = base * (1.0 + rng.normal(0, noise_scale))
                    # Outbreaks elevate the signal above baseline.
                    bump = self._outbreak_factor(signal, district.id, d)
                    if bump:
                        val += base * bump
                    val = self._clamp(signal, val)
                    records.append(
                        SignalRecord(
                            district_id=district.id,
                            date=d,
                            signal_type=signal,
                            value=round(float(val), 3),
                            source_id=self.source_id,
                        )
                    )
        return records

    @staticmethod
    def _clamp(signal: SignalType, val: float) -> float:
        if signal in _INDEX_BASE and signal is not SignalType.WASTEWATER_VIRAL_LOAD:
            return max(0.0, min(100.0, val))  # search indices 0..100
        if signal is SignalType.WEATHER_HUMIDITY:
            return max(0.0, min(100.0, val))
        if signal in _POP_SCALED_BASE:
            return max(0.0, round(val))  # counts are non-negative integers
        return max(0.0, val)


WEATHER_SET = {SignalType.WEATHER_TEMP, SignalType.WEATHER_HUMIDITY, SignalType.WEATHER_RAINFALL}
