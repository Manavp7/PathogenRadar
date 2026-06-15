from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.domain.models import AlertLevel, DiseaseCategory, SignalSource
from pathogenradar_api.layers.pipeline import IntelligencePipeline


def test_district_pipeline_returns_vector_alert_with_explanations() -> None:
    intelligence = IntelligencePipeline(DemoRepository()).district_intelligence("kerala-ernakulam")

    assert intelligence.risk_assessment.risk_score >= 50
    assert intelligence.risk_assessment.alert_level in {
        AlertLevel.WARNING,
        AlertLevel.ALERT,
        AlertLevel.EMERGENCY,
    }
    assert intelligence.risk_assessment.category == DiseaseCategory.VECTOR
    assert intelligence.recommendations
    assert intelligence.explanations
    assert SignalSource.HOSPITAL in intelligence.disease_state.source_contributions


def test_all_expected_sources_produce_embeddings() -> None:
    intelligence = IntelligencePipeline(DemoRepository()).district_intelligence("kerala-ernakulam")
    sources = {embedding.source for embedding in intelligence.embeddings}

    assert sources == set(SignalSource)
