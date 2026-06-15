from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.domain.models import (
    DistrictIntelligence,
    InterventionType,
    NationalIntelligence,
    SimulationRequest,
)
from pathogenradar_api.layers.acquisition import DataAcquisitionLayer
from pathogenradar_api.layers.alerts import AlertingSystem
from pathogenradar_api.layers.decision import RLDecisionEngine
from pathogenradar_api.layers.explainability import ExplainabilityEngine
from pathogenradar_api.layers.forecast import SpreadForecastEngine
from pathogenradar_api.layers.fusion import MultimodalFusionEngine
from pathogenradar_api.layers.knowledge_graph import DiseaseKnowledgeGraph
from pathogenradar_api.layers.llm_reports import ReportGenerator
from pathogenradar_api.layers.novel_pathogen import NovelPathogenDetector
from pathogenradar_api.layers.outbreak_detection import OutbreakDetectionEngine
from pathogenradar_api.layers.quality import DataQualityEngine
from pathogenradar_api.layers.signal_intelligence import SignalIntelligenceLayer
from pathogenradar_api.layers.simulation import EpidemiologicalSimulator


class IntelligencePipeline:
    def __init__(self, repository: DemoRepository) -> None:
        self.repository = repository
        self.acquisition = DataAcquisitionLayer.demo(repository)
        self.quality = DataQualityEngine()
        self.signal_intelligence = SignalIntelligenceLayer()
        self.fusion = MultimodalFusionEngine()
        self.knowledge_graph = DiseaseKnowledgeGraph(repository.get_knowledge_graph())
        self.outbreak_detection = OutbreakDetectionEngine()
        self.novel_detector = NovelPathogenDetector()
        self.forecast_engine = SpreadForecastEngine()
        self.simulator = EpidemiologicalSimulator()
        self.decision = RLDecisionEngine()
        self.explainability = ExplainabilityEngine()
        self.reports = ReportGenerator()
        self.alerts = AlertingSystem()

    def district_intelligence(
        self,
        district_id: str,
        simulation_request: SimulationRequest | None = None,
    ) -> DistrictIntelligence:
        district = self.repository.get_district(district_id)
        observations = self.acquisition.collect(district_id)
        quality = self.quality.score(observations)
        embeddings = self.signal_intelligence.encode(observations, quality)
        disease_state = self.fusion.fuse(embeddings, district)
        matches = self.knowledge_graph.related_diseases(disease_state.dominant_symptoms, disease_state.context)
        risk = self.outbreak_detection.assess(disease_state, matches)
        risk = self.novel_detector.detect(disease_state, risk, matches)
        forecast = self.forecast_engine.forecast(risk, self.repository.get_mobility_edges())
        if simulation_request is None:
            simulation_request = SimulationRequest(
                interventions=self._default_interventions(risk.category.value)
            )
        simulation = self.simulator.run(simulation_request, disease_state)
        recommendations = self.decision.recommend(risk, forecast, simulation)
        explanations = self.explainability.explain(risk, embeddings, quality)
        report = self.reports.generate_executive_briefing(risk, forecast, recommendations, explanations)
        alert = self.alerts.build_alert(risk, explanations, recommendations)
        return DistrictIntelligence(
            district=district,
            quality=quality,
            embeddings=embeddings,
            disease_state=disease_state,
            risk_assessment=risk,
            forecast=forecast,
            simulation=simulation,
            recommendations=recommendations,
            explanations=explanations,
            report=report,
            alert=alert,
        )

    def national_intelligence(self) -> NationalIntelligence:
        from datetime import UTC, datetime

        districts = [
            self.district_intelligence(district.id) for district in self.repository.list_districts()
        ]
        highest = max(districts, key=lambda item: item.risk_assessment.risk_score)
        summary = (
            f"Highest synthetic risk is {highest.district.name} at "
            f"{highest.risk_assessment.risk_score:.1f}/100 "
            f"({highest.risk_assessment.alert_level.value})."
        )
        return NationalIntelligence(
            generated_at=datetime.now(UTC),
            districts=sorted(districts, key=lambda item: item.risk_assessment.risk_score, reverse=True),
            national_summary=summary,
        )

    def _default_interventions(self, category: str) -> list[InterventionType]:
        if category == "vector":
            return [InterventionType.VECTOR_CONTROL, InterventionType.PUBLIC_COMMUNICATION]
        if category == "waterborne":
            return [InterventionType.WATER_SANITATION, InterventionType.PUBLIC_COMMUNICATION]
        if category == "respiratory":
            return [InterventionType.MASKING, InterventionType.PUBLIC_COMMUNICATION]
        return [InterventionType.PUBLIC_COMMUNICATION, InterventionType.HOSPITAL_PREPAREDNESS]
