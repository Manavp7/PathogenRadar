from typing import Any

from pathogenradar_api.domain.models import DiseaseCategory, DiseaseState, RiskAssessment


class NovelPathogenDetector:
    """Deterministic novelty placeholder for future autoencoder/contrastive models."""

    def score(self, disease_state: DiseaseState, knowledge_matches: list[dict[str, Any]]) -> float:
        known_match_strength = 0.18 * len(knowledge_matches)
        high_signal = min(1.0, sum(disease_state.state_vector) / 1.6)
        unusual_symptoms = 0.2 if len(disease_state.dominant_symptoms) <= 1 and high_signal > 0.5 else 0.0
        return round(max(0.0, min(1.0, high_signal - known_match_strength + unusual_symptoms)), 3)

    def detect(
        self,
        disease_state: DiseaseState,
        risk_assessment: RiskAssessment,
        knowledge_matches: list[dict[str, Any]],
    ) -> RiskAssessment:
        novelty_score = self.score(disease_state, knowledge_matches)
        is_novel = novelty_score >= 0.68 and risk_assessment.risk_score >= 50
        category = DiseaseCategory.UNKNOWN if is_novel else risk_assessment.category
        return risk_assessment.model_copy(
            update={
                "novelty_score": novelty_score,
                "is_novel_anomaly": is_novel,
                "category": category,
            }
        )
