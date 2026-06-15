from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SignalSource(StrEnum):
    HOSPITAL = "hospital"
    SEARCH = "search"
    SOCIAL = "social"
    WEATHER = "weather"
    ENVIRONMENTAL = "environmental"
    MOBILITY = "mobility"
    WASTEWATER = "wastewater"


class AlertLevel(StrEnum):
    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    ALERT = "alert"
    EMERGENCY = "emergency"


class DiseaseCategory(StrEnum):
    RESPIRATORY = "respiratory"
    VECTOR = "vector"
    WATERBORNE = "waterborne"
    FOODBORNE = "foodborne"
    UNKNOWN = "unknown"


class InterventionType(StrEnum):
    SCHOOL_CLOSURE = "school_closure"
    MASKING = "masking"
    VACCINATION = "vaccination"
    TRAVEL_RESTRICTION = "travel_restriction"
    VECTOR_CONTROL = "vector_control"
    WATER_SANITATION = "water_sanitation"
    PUBLIC_COMMUNICATION = "public_communication"
    HOSPITAL_PREPAREDNESS = "hospital_preparedness"


class Channel(StrEnum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    API = "api"
    MOBILE_APP = "mobile_app"


class Role(StrEnum):
    NATIONAL_ADMIN = "national_admin"
    STATE_OFFICER = "state_officer"
    DISTRICT_OFFICER = "district_officer"
    RESEARCHER = "researcher"
    PUBLIC_CONSUMER = "public_consumer"


class District(BaseModel):
    id: str
    name: str
    state: str
    population: int
    latitude: float
    longitude: float


class SignalObservation(BaseModel):
    id: str
    district_id: str
    source: SignalSource
    timestamp: datetime
    metric: str
    value: float
    baseline: float
    unit: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MobilityEdge(BaseModel):
    from_district_id: str
    to_district_id: str
    mode: str
    weight: float = Field(ge=0, le=1)


class SourceQualityScore(BaseModel):
    source: SignalSource
    completeness: float = Field(ge=0, le=1)
    outlier_score: float = Field(ge=0, le=1)
    drift_score: float = Field(ge=0, le=1)
    integrity_score: float = Field(ge=0, le=1)
    freshness_score: float = Field(ge=0, le=1)
    reliability: float = Field(ge=0, le=1)
    issues: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    aggregate_confidence: float = Field(ge=0, le=1)
    source_scores: list[SourceQualityScore]
    missing_sources: list[SignalSource] = Field(default_factory=list)


class SignalEmbedding(BaseModel):
    source: SignalSource
    vector: list[float]
    intensity: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    extracted_symptoms: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DiseaseState(BaseModel):
    district: District
    state_vector: list[float]
    source_contributions: dict[SignalSource, float]
    dominant_symptoms: list[str]
    context: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)


class RiskAssessment(BaseModel):
    district: District
    risk_score: float = Field(ge=0, le=100)
    alert_level: AlertLevel
    category: DiseaseCategory
    confidence: float = Field(ge=0, le=1)
    novelty_score: float = Field(default=0, ge=0, le=1)
    is_novel_anomaly: bool = False
    matched_diseases: list[str] = Field(default_factory=list)


class ForecastPoint(BaseModel):
    horizon_days: int
    district_probabilities: dict[str, float]
    confidence: float = Field(ge=0, le=1)


class SpreadForecast(BaseModel):
    origin_district_id: str
    points: list[ForecastPoint]


class SimulationRequest(BaseModel):
    horizon_days: int = Field(default=30, ge=7, le=120)
    interventions: list[InterventionType] = Field(default_factory=list)
    compliance: float = Field(default=0.65, ge=0, le=1)


class SimulationResult(BaseModel):
    district_id: str
    horizon_days: int
    baseline_projected_cases: int
    intervention_projected_cases: int
    estimated_cases_averted: int
    effective_reproduction_number: float
    assumptions: list[str]


class Recommendation(BaseModel):
    intervention: InterventionType
    priority: str
    rationale: str
    expected_effect: str
    burden: str


class ExplanationFactor(BaseModel):
    label: str
    source: SignalSource | None = None
    contribution: float = Field(ge=0, le=1)
    detail: str


class ChannelStatus(BaseModel):
    channel: Channel
    ready: bool
    note: str


class Alert(BaseModel):
    id: str
    district: District
    level: AlertLevel
    title: str
    message: str
    reasons: list[ExplanationFactor]
    recommended_actions: list[Recommendation]
    channels: list[ChannelStatus]
    created_at: datetime


class ExecutiveReport(BaseModel):
    title: str
    audience: str
    generated_at: datetime
    summary: str
    risk_assessment: RiskAssessment
    key_drivers: list[ExplanationFactor]
    recommended_actions: list[Recommendation]
    limitations: list[str]


class ResearchQuery(BaseModel):
    query_type: str = Field(
        description="Allowed demo values: historical_outbreaks, source_reliability, forecast_comparison"
    )
    district_id: str | None = None


class ResearchResult(BaseModel):
    query_type: str
    title: str
    rows: list[dict[str, Any]]
    caveats: list[str]


class DistrictIntelligence(BaseModel):
    district: District
    quality: QualityReport
    embeddings: list[SignalEmbedding]
    disease_state: DiseaseState
    risk_assessment: RiskAssessment
    forecast: SpreadForecast
    simulation: SimulationResult
    recommendations: list[Recommendation]
    explanations: list[ExplanationFactor]
    report: ExecutiveReport
    alert: Alert | None = None


class NationalIntelligence(BaseModel):
    generated_at: datetime
    districts: list[DistrictIntelligence]
    national_summary: str
