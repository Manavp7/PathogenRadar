"""Core domain models shared across the pipeline and the API.

Pydantic is used so the same models serialise cleanly to JSON for the dashboard.
"""

from __future__ import annotations

from datetime import date as Date
from enum import Enum

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------------------
# Reference / config
# --------------------------------------------------------------------------------------


class District(BaseModel):
    id: str
    name: str
    population: int
    lat: float
    lon: float
    neighbors: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------------------
# Signals
# --------------------------------------------------------------------------------------


class SignalType(str, Enum):
    """The raw signal families ingested by the platform."""

    HOSPITAL_ADMISSIONS = "hospital_admissions"
    ICU_OCCUPANCY = "icu_occupancy"
    VENTILATOR_USAGE = "ventilator_usage"
    MORTALITY = "mortality"
    LAB_PCR_REQUESTS = "lab_pcr_requests"
    SEARCH_FEVER = "search_fever"
    SEARCH_COUGH = "search_cough"
    SEARCH_RASH = "search_rash"
    SEARCH_VOMITING = "search_vomiting"
    SEARCH_DIARRHEA = "search_diarrhea"
    SOCIAL_MENTIONS = "social_mentions"
    WASTEWATER_VIRAL_LOAD = "wastewater_viral_load"
    WEATHER_TEMP = "weather_temp"
    WEATHER_HUMIDITY = "weather_humidity"
    WEATHER_RAINFALL = "weather_rainfall"


# Signals grouped by the detector family that consumes them.
SEARCH_SIGNALS = [
    SignalType.SEARCH_FEVER,
    SignalType.SEARCH_COUGH,
    SignalType.SEARCH_RASH,
    SignalType.SEARCH_VOMITING,
    SignalType.SEARCH_DIARRHEA,
]
HOSPITAL_SIGNALS = [
    SignalType.HOSPITAL_ADMISSIONS,
    SignalType.ICU_OCCUPANCY,
    SignalType.VENTILATOR_USAGE,
    SignalType.MORTALITY,
    SignalType.LAB_PCR_REQUESTS,
]
WEATHER_SIGNALS = [
    SignalType.WEATHER_TEMP,
    SignalType.WEATHER_HUMIDITY,
    SignalType.WEATHER_RAINFALL,
]


class SignalRecord(BaseModel):
    district_id: str
    date: Date
    signal_type: SignalType
    value: float
    source_id: str


# --------------------------------------------------------------------------------------
# Data quality
# --------------------------------------------------------------------------------------


class SourceReliability(BaseModel):
    source_id: str
    reliability: float  # 0..1
    completeness: float  # 0..1
    stability: float  # 0..1
    notes: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    district_id: str
    date: Date
    confidence: float  # 0..1 overall confidence in this district/day's signals
    missing_ratio: float
    outlier_ratio: float
    drift_score: float
    sources: list[SourceReliability] = Field(default_factory=list)


# --------------------------------------------------------------------------------------
# Signal intelligence (anomaly detectors)
# --------------------------------------------------------------------------------------


class SignalScore(BaseModel):
    """Output of a per-source anomaly detector for one district/day."""

    district_id: str
    date: Date
    detector: str  # e.g. "search", "hospital", "social", "wastewater"
    score: float  # 0..1 anomaly intensity
    drivers: dict[str, float] = Field(default_factory=dict)  # signal -> contribution


# --------------------------------------------------------------------------------------
# Fusion + detection
# --------------------------------------------------------------------------------------


class OutbreakLevel(str, Enum):
    NORMAL = "Normal"
    WATCH = "Watch"
    WARNING = "Warning"
    ALERT = "Alert"
    EMERGENCY = "Emergency"


class DiseaseCategory(str, Enum):
    RESPIRATORY = "Respiratory"
    VECTOR = "Vector"
    WATERBORNE = "Waterborne"
    FOODBORNE = "Foodborne"
    UNKNOWN = "Unknown"


class Contribution(BaseModel):
    label: str
    value: float  # signed contribution to the risk score (percentage points)
    detail: str = ""


class RiskAssessment(BaseModel):
    """The fused, classified, explained risk for one district/day."""

    district_id: str
    district_name: str
    date: Date
    risk_score: float  # 0..100
    level: OutbreakLevel
    category: DiseaseCategory
    likely_diseases: list[str] = Field(default_factory=list)
    confidence: float  # 0..1 (from data quality)
    signal_scores: dict[str, float] = Field(default_factory=dict)  # detector -> score
    contributions: list[Contribution] = Field(default_factory=list)
    novelty_score: float = 0.0  # 0..1 — how unlike any known disease the pattern is
    novel_pathogen: bool = False  # flagged when high-risk pattern matches no known disease


# --------------------------------------------------------------------------------------
# Forecast
# --------------------------------------------------------------------------------------


class ForecastPoint(BaseModel):
    horizon_days: int
    risk_probability: float  # 0..1


class DistrictForecast(BaseModel):
    district_id: str
    district_name: str
    current_risk: float  # 0..100
    points: list[ForecastPoint] = Field(default_factory=list)


# --------------------------------------------------------------------------------------
# Simulation (SEIR)
# --------------------------------------------------------------------------------------


class Intervention(BaseModel):
    school_closure: float = 0.0  # 0..1 intensity
    masking: float = 0.0
    vaccination_rate: float = 0.0  # fraction of susceptibles vaccinated at start
    travel_restriction: float = 0.0


class SeirCurve(BaseModel):
    days: list[int]
    susceptible: list[float]
    exposed: list[float]
    infected: list[float]
    recovered: list[float]


class SeirResult(BaseModel):
    district_id: str
    disease: str
    population: int
    r0: float
    effective_r: float
    baseline: SeirCurve
    intervention: SeirCurve | None = None
    peak_infected_baseline: float
    peak_day_baseline: int
    peak_infected_intervention: float | None = None
    peak_day_intervention: int | None = None
    cases_averted: float | None = None


# --------------------------------------------------------------------------------------
# Alerting
# --------------------------------------------------------------------------------------


class Alert(BaseModel):
    id: str
    district_id: str
    district_name: str
    date: Date
    level: OutbreakLevel
    category: DiseaseCategory
    risk_score: float
    headline: str
    reasons: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------------------
# Briefing
# --------------------------------------------------------------------------------------


class Briefing(BaseModel):
    region: str
    date: Date
    provider: str  # which LLMProvider produced it (e.g. "template")
    title: str
    body: str
