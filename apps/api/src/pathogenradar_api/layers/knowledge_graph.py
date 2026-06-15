from typing import Any


class DiseaseKnowledgeGraph:
    """Fixture-backed disease graph with a future Neo4j replacement point."""

    def __init__(self, graph: dict[str, Any]) -> None:
        self.graph = graph
        self.diseases = graph.get("diseases", [])

    def related_diseases(
        self, symptoms: list[str], weather_context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        symptom_set = set(symptoms)
        weather_values = set(str(value).lower() for value in (weather_context or {}).values())
        matches: list[tuple[float, dict[str, Any]]] = []
        for disease in self.diseases:
            disease_symptoms = set(disease.get("symptoms", []))
            overlap = len(symptom_set & disease_symptoms)
            weather_bonus = 0
            for dependency in disease.get("weather_dependencies", []):
                if dependency.lower() in weather_values:
                    weather_bonus += 1
            denominator = max(1, len(disease_symptoms))
            score = (overlap / denominator) + (weather_bonus * 0.08)
            if score > 0:
                matches.append((score, disease))
        return [disease for _, disease in sorted(matches, key=lambda item: item[0], reverse=True)]

    def risk_factors_for(self, disease_name: str) -> dict[str, Any]:
        for disease in self.diseases:
            if disease["name"] == disease_name:
                return {
                    "vectors": disease.get("vectors", []),
                    "transmission": disease.get("transmission", []),
                    "weather_dependencies": disease.get("weather_dependencies", []),
                    "population_risk": disease.get("population_risk", []),
                }
        return {}

    def explain_links(self, disease_name: str) -> list[str]:
        factors = self.risk_factors_for(disease_name)
        links: list[str] = []
        for key, values in factors.items():
            if values:
                links.append(f"{disease_name} links to {key}: {', '.join(values)}")
        return links
