from pathogenradar_api.domain.models import (
    ExplanationFactor,
    QualityReport,
    RiskAssessment,
    SignalEmbedding,
)

SOURCE_LABELS = {
    "hospital": "Hospital pressure",
    "search": "Search behavior spike",
    "social": "Social symptom cluster",
    "weather": "Weather context",
    "environmental": "Environmental risk",
    "mobility": "Mobility spread context",
    "wastewater": "Wastewater signal",
}


class ExplainabilityEngine:
    def explain(
        self,
        risk_assessment: RiskAssessment,
        embeddings: list[SignalEmbedding],
        quality_report: QualityReport,
    ) -> list[ExplanationFactor]:
        factors: list[ExplanationFactor] = []
        for embedding in sorted(embeddings, key=lambda item: item.intensity, reverse=True)[:5]:
            factors.append(
                ExplanationFactor(
                    label=SOURCE_LABELS.get(embedding.source.value, embedding.source.value),
                    source=embedding.source,
                    contribution=round(embedding.intensity, 3),
                    detail=(
                        f"{embedding.source.value} contributed intensity {embedding.intensity:.2f} "
                        f"with source confidence {embedding.confidence:.2f}."
                    ),
                )
            )

        if quality_report.aggregate_confidence < 0.75:
            factors.append(
                ExplanationFactor(
                    label="Data confidence caveat",
                    source=None,
                    contribution=round(1 - quality_report.aggregate_confidence, 3),
                    detail="Some sources are missing, stale, drifting, or lower reliability.",
                )
            )

        factors.append(
            ExplanationFactor(
                label="Alert threshold",
                source=None,
                contribution=min(1.0, risk_assessment.risk_score / 100),
                detail=(
                    f"Risk score {risk_assessment.risk_score:.1f} maps to "
                    f"{risk_assessment.alert_level.value} status."
                ),
            )
        )
        return factors
