from pathogenradar_api.domain.models import (
    AlertLevel,
    DiseaseCategory,
    InterventionType,
    Recommendation,
    RiskAssessment,
    SimulationResult,
    SpreadForecast,
)


class RLDecisionEngine:
    """Rule policy placeholder for future PPO/A3C/DQN decision optimization.

    Future rewards should balance early detection, reduced spread, lower false
    alarms, and lower intervention burden. This demo policy is deterministic and
    human-readable so officials can inspect recommendations.
    """

    def recommend(
        self,
        risk_assessment: RiskAssessment,
        forecast: SpreadForecast,
        simulation_result: SimulationResult,
    ) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        max_forecast = max(
            probability
            for point in forecast.points
            for probability in point.district_probabilities.values()
        )

        if risk_assessment.alert_level in {AlertLevel.WARNING, AlertLevel.ALERT, AlertLevel.EMERGENCY}:
            recommendations.append(
                Recommendation(
                    intervention=InterventionType.PUBLIC_COMMUNICATION,
                    priority="high",
                    rationale="Risk is above warning threshold; communicate symptoms and reporting steps.",
                    expected_effect="Improves early care seeking and reduces rumor-driven response delays.",
                    burden="low",
                )
            )
            recommendations.append(
                Recommendation(
                    intervention=InterventionType.HOSPITAL_PREPAREDNESS,
                    priority="high",
                    rationale="Hospital signal contributes to risk and capacity should be prepared.",
                    expected_effect="Improves triage readiness and diagnostic throughput.",
                    burden="medium",
                )
            )

        if risk_assessment.category == DiseaseCategory.VECTOR:
            recommendations.append(
                Recommendation(
                    intervention=InterventionType.VECTOR_CONTROL,
                    priority="high",
                    rationale="Vector-like symptoms plus rainfall/environmental risk indicate mosquito control.",
                    expected_effect="Reduces vector density and downstream spread probability.",
                    burden="medium",
                )
            )
        elif risk_assessment.category == DiseaseCategory.WATERBORNE:
            recommendations.append(
                Recommendation(
                    intervention=InterventionType.WATER_SANITATION,
                    priority="high",
                    rationale="Waterborne symptom cluster and environmental water-risk signals are elevated.",
                    expected_effect="Reduces exposure from contaminated water sources.",
                    burden="medium",
                )
            )
        elif risk_assessment.category == DiseaseCategory.RESPIRATORY:
            recommendations.append(
                Recommendation(
                    intervention=InterventionType.MASKING,
                    priority="medium",
                    rationale="Respiratory symptom cluster is elevated.",
                    expected_effect="Can reduce droplet/aerosol transmission.",
                    burden="low",
                )
            )

        if max_forecast >= 0.5:
            recommendations.append(
                Recommendation(
                    intervention=InterventionType.TRAVEL_RESTRICTION,
                    priority="medium",
                    rationale="Mobility forecast shows meaningful spread probability outside origin district.",
                    expected_effect="May dampen inter-district propagation while investigation continues.",
                    burden="high",
                )
            )

        if simulation_result.estimated_cases_averted > 500:
            recommendations.append(
                Recommendation(
                    intervention=InterventionType.VACCINATION,
                    priority="evaluate",
                    rationale="Scenario suggests large potential case reduction if disease-specific tools exist.",
                    expected_effect="Could reduce susceptible pool for vaccine-preventable pathogens.",
                    burden="high",
                )
            )

        if not recommendations:
            recommendations.append(
                Recommendation(
                    intervention=InterventionType.PUBLIC_COMMUNICATION,
                    priority="monitor",
                    rationale="Risk remains low; maintain routine surveillance and public guidance.",
                    expected_effect="Preserves readiness without over-escalation.",
                    burden="low",
                )
            )
        return recommendations
