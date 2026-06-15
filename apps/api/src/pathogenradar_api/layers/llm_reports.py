from datetime import UTC, datetime

from pathogenradar_api.domain.models import (
    ExecutiveReport,
    ExplanationFactor,
    Recommendation,
    RiskAssessment,
    SpreadForecast,
)


class ReportGenerator:
    """Report generator only; it does not perform outbreak prediction."""

    def generate_executive_briefing(
        self,
        risk_assessment: RiskAssessment,
        forecast: SpreadForecast,
        recommendations: list[Recommendation],
        explanations: list[ExplanationFactor],
        audience: str = "Health Minister",
    ) -> ExecutiveReport:
        day_30 = next(point for point in forecast.points if point.horizon_days == 30)
        highest_forecast = max(day_30.district_probabilities.items(), key=lambda item: item[1])
        summary = (
            f"{risk_assessment.district.name}, {risk_assessment.district.state} is at "
            f"{risk_assessment.alert_level.value.upper()} level with a demo risk score of "
            f"{risk_assessment.risk_score:.1f}/100 for a {risk_assessment.category.value} pattern. "
            f"The 30-day mobility forecast highlights {highest_forecast[0]} with "
            f"{highest_forecast[1]:.0%} spread probability under synthetic assumptions."
        )
        return ExecutiveReport(
            title=f"PathogenRadar briefing: {risk_assessment.district.name}",
            audience=audience,
            generated_at=datetime.now(UTC),
            summary=summary,
            risk_assessment=risk_assessment,
            key_drivers=explanations[:5],
            recommended_actions=recommendations,
            limitations=[
                "Generated from synthetic demo fixtures, not live surveillance data.",
                "Report generation summarizes upstream model outputs and does not make predictions.",
                "All interventions require qualified public-health review before action.",
            ],
        )
