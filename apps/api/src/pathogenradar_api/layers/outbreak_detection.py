from typing import Any

from pathogenradar_api.domain.models import AlertLevel, DiseaseCategory, DiseaseState, RiskAssessment


class OutbreakDetectionEngine:
    """Threshold classifier for demo alerting."""

    def assess(
        self, disease_state: DiseaseState, knowledge_matches: list[dict[str, Any]] | None = None
    ) -> RiskAssessment:
        vector_risk = min(1.0, sum(disease_state.state_vector) / 1.45)
        contextual_boost = 0.0
        if {"rash", "body_pain"} & set(disease_state.dominant_symptoms):
            contextual_boost += 0.07
        if {"diarrhea", "vomiting"} & set(disease_state.dominant_symptoms):
            contextual_boost += 0.06
        risk_score = round(min(100.0, (vector_risk + contextual_boost) * 100), 1)

        if risk_score >= 85:
            level = AlertLevel.EMERGENCY
        elif risk_score >= 70:
            level = AlertLevel.ALERT
        elif risk_score >= 50:
            level = AlertLevel.WARNING
        elif risk_score >= 25:
            level = AlertLevel.WATCH
        else:
            level = AlertLevel.NORMAL

        matched_diseases = [match["name"] for match in knowledge_matches or []]
        category = self._category(disease_state, knowledge_matches or [])
        return RiskAssessment(
            district=disease_state.district,
            risk_score=risk_score,
            alert_level=level,
            category=category,
            confidence=disease_state.confidence,
            matched_diseases=matched_diseases[:3],
        )

    def _category(
        self, disease_state: DiseaseState, knowledge_matches: list[dict[str, Any]]
    ) -> DiseaseCategory:
        if knowledge_matches:
            category = knowledge_matches[0].get("category", DiseaseCategory.UNKNOWN)
            return DiseaseCategory(category)
        symptoms = set(disease_state.dominant_symptoms)
        if {"rash", "body_pain"} & symptoms:
            return DiseaseCategory.VECTOR
        if {"diarrhea", "vomiting"} & symptoms:
            return DiseaseCategory.WATERBORNE
        if {"cough", "loss_of_smell"} & symptoms:
            return DiseaseCategory.RESPIRATORY
        return DiseaseCategory.UNKNOWN
