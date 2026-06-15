from collections import defaultdict

from pathogenradar_api.domain.models import (
    QualityReport,
    SignalEmbedding,
    SignalObservation,
    SignalSource,
)


def _normalized_delta(observations: list[SignalObservation]) -> float:
    if not observations:
        return 0.0
    deltas = []
    for observation in observations:
        baseline = max(abs(observation.baseline), 0.1)
        deltas.append(max(0.0, (observation.value - observation.baseline) / baseline))
    return min(1.0, sum(deltas) / len(deltas) / 3)


def _symptoms(observations: list[SignalObservation]) -> list[str]:
    found: set[str] = set()
    for observation in observations:
        found.update(observation.metadata.get("symptoms", []))
    return sorted(found)


class BaseDetector:
    source: SignalSource
    emphasis: tuple[float, float, float, float]

    def encode(self, observations: list[SignalObservation], confidence: float) -> SignalEmbedding:
        intensity = round(_normalized_delta(observations) * confidence, 3)
        symptoms = _symptoms(observations)
        vector = [
            round(intensity * self.emphasis[0], 3),
            round(intensity * self.emphasis[1], 3),
            round(intensity * self.emphasis[2], 3),
            round(intensity * self.emphasis[3], 3),
        ]
        return SignalEmbedding(
            source=self.source,
            vector=vector,
            intensity=intensity,
            confidence=confidence,
            extracted_symptoms=symptoms,
            notes=[f"{self.source.value} baseline detector; replace with trained model later"],
        )


class SearchTrendDetector(BaseDetector):
    source = SignalSource.SEARCH
    emphasis = (0.45, 0.3, 0.15, 0.1)


class HospitalDetector(BaseDetector):
    source = SignalSource.HOSPITAL
    emphasis = (0.5, 0.2, 0.2, 0.1)


class SocialDetector(BaseDetector):
    source = SignalSource.SOCIAL
    emphasis = (0.35, 0.35, 0.2, 0.1)


class WastewaterDetector(BaseDetector):
    source = SignalSource.WASTEWATER
    emphasis = (0.25, 0.2, 0.4, 0.15)


class WeatherEnvironmentalDetector(BaseDetector):
    emphasis = (0.15, 0.25, 0.2, 0.4)

    def __init__(self, source: SignalSource) -> None:
        self.source = source


class SignalIntelligenceLayer:
    def __init__(self) -> None:
        self.detectors: dict[SignalSource, BaseDetector] = {
            SignalSource.HOSPITAL: HospitalDetector(),
            SignalSource.SEARCH: SearchTrendDetector(),
            SignalSource.SOCIAL: SocialDetector(),
            SignalSource.WASTEWATER: WastewaterDetector(),
            SignalSource.WEATHER: WeatherEnvironmentalDetector(SignalSource.WEATHER),
            SignalSource.ENVIRONMENTAL: WeatherEnvironmentalDetector(SignalSource.ENVIRONMENTAL),
            SignalSource.MOBILITY: WeatherEnvironmentalDetector(SignalSource.MOBILITY),
        }

    def encode(
        self, observations: list[SignalObservation], quality_report: QualityReport
    ) -> list[SignalEmbedding]:
        by_source: dict[SignalSource, list[SignalObservation]] = defaultdict(list)
        for observation in observations:
            by_source[observation.source].append(observation)
        confidence_by_source = {
            score.source: score.reliability for score in quality_report.source_scores
        }
        embeddings: list[SignalEmbedding] = []
        for source, detector in self.detectors.items():
            source_observations = by_source.get(source, [])
            if not source_observations:
                continue
            embeddings.append(
                detector.encode(source_observations, confidence_by_source.get(source, 0.0))
            )
        return sorted(embeddings, key=lambda embedding: embedding.source)
