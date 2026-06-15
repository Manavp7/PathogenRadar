from datetime import UTC, datetime

from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.domain.models import SignalObservation, SignalSource
from pathogenradar_api.layers.quality import DataQualityEngine
from pathogenradar_api.layers.signal_intelligence import SignalIntelligenceLayer


def test_missing_sources_lower_confidence() -> None:
    repository = DemoRepository()
    observations = repository.list_signals("kerala-ernakulam")
    full_report = DataQualityEngine().score(observations)
    partial_report = DataQualityEngine().score(
        [signal for signal in observations if signal.source != SignalSource.WASTEWATER]
    )

    assert SignalSource.WASTEWATER in partial_report.missing_sources
    assert partial_report.aggregate_confidence < full_report.aggregate_confidence


def test_extreme_values_are_detected_as_outliers() -> None:
    observation = SignalObservation(
        id="extreme",
        district_id="demo",
        source=SignalSource.HOSPITAL,
        timestamp=datetime.now(UTC),
        metric="icu_occupancy_delta_pct",
        value=500,
        baseline=5,
        unit="percent",
    )
    report = DataQualityEngine().score([observation])
    hospital_score = next(score for score in report.source_scores if score.source == SignalSource.HOSPITAL)

    assert hospital_score.outlier_score < 0.7
    assert any("extreme" in issue for issue in hospital_score.issues)


def test_lower_reliability_reduces_signal_embedding_intensity() -> None:
    repository = DemoRepository()
    observations = repository.list_signals("kerala-ernakulam")
    engine = DataQualityEngine()
    full_report = engine.score(observations)
    stale_observations = [
        signal.model_copy(update={"timestamp": datetime(2020, 1, 1, tzinfo=UTC)})
        for signal in observations
    ]
    stale_report = engine.score(stale_observations)
    encoder = SignalIntelligenceLayer()

    full_hospital = next(
        embedding
        for embedding in encoder.encode(observations, full_report)
        if embedding.source == SignalSource.HOSPITAL
    )
    stale_hospital = next(
        embedding
        for embedding in encoder.encode(stale_observations, stale_report)
        if embedding.source == SignalSource.HOSPITAL
    )

    assert stale_hospital.confidence < full_hospital.confidence
    assert stale_hospital.intensity < full_hospital.intensity
