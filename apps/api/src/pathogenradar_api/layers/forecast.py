from collections import defaultdict

from pathogenradar_api.domain.models import ForecastPoint, MobilityEdge, RiskAssessment, SpreadForecast


class SpreadForecastEngine:
    """Baseline mobility-graph propagation for 7/14/21/30 day forecasts."""

    HORIZONS = (7, 14, 21, 30)

    def forecast(
        self, risk_assessment: RiskAssessment, mobility_edges: list[MobilityEdge] | tuple[MobilityEdge, ...]
    ) -> SpreadForecast:
        origin = risk_assessment.district.id
        district_ids = {origin}
        outgoing: dict[str, list[MobilityEdge]] = defaultdict(list)
        for edge in mobility_edges:
            district_ids.add(edge.from_district_id)
            district_ids.add(edge.to_district_id)
            outgoing[edge.from_district_id].append(edge)

        base_probability = risk_assessment.risk_score / 100
        current = {district_id: 0.0 for district_id in district_ids}
        current[origin] = base_probability
        points: list[ForecastPoint] = []

        for horizon in self.HORIZONS:
            damping = min(0.92, 0.34 + (horizon / 45))
            propagated = {district_id: probability * 0.72 for district_id, probability in current.items()}
            for district_id, probability in current.items():
                for edge in outgoing.get(district_id, []):
                    propagated[edge.to_district_id] = max(
                        propagated.get(edge.to_district_id, 0.0),
                        probability * edge.weight * damping,
                    )
            propagated[origin] = max(propagated[origin], base_probability * (1 + horizon / 90))
            current = {
                district_id: round(min(0.98, probability), 3)
                for district_id, probability in propagated.items()
            }
            points.append(
                ForecastPoint(
                    horizon_days=horizon,
                    district_probabilities=dict(sorted(current.items())),
                    confidence=round(risk_assessment.confidence * (1 - horizon / 140), 3),
                )
            )

        return SpreadForecast(origin_district_id=origin, points=points)
