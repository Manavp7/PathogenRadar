from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.domain.models import InterventionType, SimulationRequest
from pathogenradar_api.layers.pipeline import IntelligencePipeline


def test_report_states_generation_does_not_predict() -> None:
    report = IntelligencePipeline(DemoRepository()).district_intelligence("kerala-ernakulam").report

    assert "does not make predictions" in " ".join(report.limitations)
    assert report.key_drivers
    assert report.recommended_actions


def test_simulation_interventions_reduce_projected_cases() -> None:
    pipeline = IntelligencePipeline(DemoRepository())
    with_interventions = pipeline.district_intelligence(
        "kerala-ernakulam",
        SimulationRequest(
            interventions=[InterventionType.VECTOR_CONTROL, InterventionType.PUBLIC_COMMUNICATION],
            compliance=0.8,
        ),
    ).simulation
    without_interventions = pipeline.district_intelligence(
        "kerala-ernakulam",
        SimulationRequest(interventions=[], compliance=0.0),
    ).simulation

    assert with_interventions.intervention_projected_cases < without_interventions.baseline_projected_cases
    assert with_interventions.estimated_cases_averted > 0
