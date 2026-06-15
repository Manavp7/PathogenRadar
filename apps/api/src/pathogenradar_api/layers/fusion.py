from pathogenradar_api.domain.models import District, DiseaseState, SignalEmbedding, SignalSource


SOURCE_WEIGHTS: dict[SignalSource, float] = {
    SignalSource.HOSPITAL: 1.35,
    SignalSource.WASTEWATER: 1.25,
    SignalSource.SEARCH: 0.9,
    SignalSource.SOCIAL: 0.85,
    SignalSource.WEATHER: 0.55,
    SignalSource.ENVIRONMENTAL: 0.7,
    SignalSource.MOBILITY: 0.5,
}


class MultimodalFusionEngine:
    """Deterministic weighted fusion standing in for a future fusion transformer."""

    def fuse(self, embeddings: list[SignalEmbedding], district: District) -> DiseaseState:
        if not embeddings:
            return DiseaseState(
                district=district,
                state_vector=[0.0, 0.0, 0.0, 0.0],
                source_contributions={},
                dominant_symptoms=[],
                context={},
                confidence=0.0,
            )

        weighted_vectors = [0.0, 0.0, 0.0, 0.0]
        raw_contributions: dict[SignalSource, float] = {}
        symptoms: set[str] = set()
        total_weight = 0.0
        for embedding in embeddings:
            weight = SOURCE_WEIGHTS[embedding.source] * embedding.confidence
            total_weight += weight
            raw_contributions[embedding.source] = round(weight * embedding.intensity, 4)
            symptoms.update(embedding.extracted_symptoms)
            for index, value in enumerate(embedding.vector):
                weighted_vectors[index] += value * weight

        divisor = max(total_weight, 0.001)
        state_vector = [round(value / divisor, 3) for value in weighted_vectors]
        contribution_total = max(sum(raw_contributions.values()), 0.001)
        source_contributions = {
            source: round(value / contribution_total, 3)
            for source, value in raw_contributions.items()
        }

        return DiseaseState(
            district=district,
            state_vector=state_vector,
            source_contributions=source_contributions,
            dominant_symptoms=sorted(symptoms),
            context={
                "population": district.population,
                "implemented_as": "quality-weighted deterministic fusion",
            },
            confidence=round(sum(embedding.confidence for embedding in embeddings) / len(embeddings), 3),
        )
