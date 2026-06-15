from collections import defaultdict
from datetime import UTC, datetime

from pathogenradar_api.domain.models import (
    QualityReport,
    SignalObservation,
    SignalSource,
    SourceQualityScore,
)

EXPECTED_SOURCES = set(SignalSource)


class MissingDataDetector:
    def score(self, observations: list[SignalObservation]) -> tuple[float, list[SignalSource]]:
        present = {observation.source for observation in observations}
        missing = sorted(EXPECTED_SOURCES - present, key=str)
        return len(present) / len(EXPECTED_SOURCES), missing


class OutlierDetector:
    def score(self, observations: list[SignalObservation]) -> tuple[float, list[str]]:
        if not observations:
            return 0.0, ["no observations for source"]
        penalties: list[float] = []
        issues: list[str] = []
        for observation in observations:
            baseline = max(abs(observation.baseline), 0.1)
            ratio = abs(observation.value - observation.baseline) / baseline
            if ratio > 5:
                penalties.append(0.45)
                issues.append(f"{observation.metric} is an extreme outlier")
            elif ratio > 2:
                penalties.append(0.25)
                issues.append(f"{observation.metric} is unusually elevated")
            else:
                penalties.append(0.0)
        return max(0.0, 1.0 - (sum(penalties) / len(observations))), issues


class DriftDetector:
    def score(self, observations: list[SignalObservation]) -> tuple[float, list[str]]:
        if not observations:
            return 0.0, ["no drift baseline available"]
        drift_values = []
        issues: list[str] = []
        for observation in observations:
            baseline = max(abs(observation.baseline), 0.1)
            drift = max(0.0, observation.value - observation.baseline) / baseline
            drift_values.append(drift)
            if drift > 3:
                issues.append(f"{observation.metric} drift exceeds 3x baseline")
        mean_drift = sum(drift_values) / len(drift_values)
        return max(0.0, min(1.0, 1.0 - (mean_drift * 0.12))), issues


class DataIntegrityChecker:
    def score(self, observations: list[SignalObservation]) -> tuple[float, list[str]]:
        issues: list[str] = []
        for observation in observations:
            if observation.value < 0:
                issues.append(f"{observation.id} has negative value")
            if not observation.metric or not observation.unit:
                issues.append(f"{observation.id} missing metric or unit")
            if observation.baseline < 0:
                issues.append(f"{observation.id} has negative baseline")
        return (1.0 if not issues else max(0.0, 1.0 - 0.2 * len(issues))), issues


class SourceReliabilityScorer:
    def freshness(self, observations: list[SignalObservation]) -> tuple[float, list[str]]:
        if not observations:
            return 0.0, ["no fresh observations"]
        now = datetime.now(UTC)
        newest = max(observation.timestamp for observation in observations)
        age_hours = max(0.0, (now - newest).total_seconds() / 3600)
        if age_hours <= 24:
            return 1.0, []
        if age_hours <= 72:
            return 0.75, [f"latest observation is {age_hours:.0f} hours old"]
        return 0.45, [f"latest observation is stale at {age_hours:.0f} hours old"]

    def combine(
        self,
        completeness: float,
        outlier_score: float,
        drift_score: float,
        integrity_score: float,
        freshness_score: float,
    ) -> float:
        return round(
            (0.22 * completeness)
            + (0.18 * outlier_score)
            + (0.2 * drift_score)
            + (0.22 * integrity_score)
            + (0.18 * freshness_score),
            3,
        )


class DataQualityEngine:
    def __init__(self) -> None:
        self.missing_detector = MissingDataDetector()
        self.outlier_detector = OutlierDetector()
        self.drift_detector = DriftDetector()
        self.integrity_checker = DataIntegrityChecker()
        self.reliability_scorer = SourceReliabilityScorer()

    def score(self, observations: list[SignalObservation]) -> QualityReport:
        completeness, missing_sources = self.missing_detector.score(observations)
        by_source: dict[SignalSource, list[SignalObservation]] = defaultdict(list)
        for observation in observations:
            by_source[observation.source].append(observation)

        source_scores: list[SourceQualityScore] = []
        for source in sorted(EXPECTED_SOURCES, key=str):
            source_observations = by_source.get(source, [])
            source_completeness = 1.0 if source_observations else 0.0
            outlier_score, outlier_issues = self.outlier_detector.score(source_observations)
            drift_score, drift_issues = self.drift_detector.score(source_observations)
            integrity_score, integrity_issues = self.integrity_checker.score(source_observations)
            freshness_score, freshness_issues = self.reliability_scorer.freshness(source_observations)
            reliability = self.reliability_scorer.combine(
                source_completeness,
                outlier_score,
                drift_score,
                integrity_score,
                freshness_score,
            )
            source_scores.append(
                SourceQualityScore(
                    source=source,
                    completeness=source_completeness,
                    outlier_score=round(outlier_score, 3),
                    drift_score=round(drift_score, 3),
                    integrity_score=round(integrity_score, 3),
                    freshness_score=round(freshness_score, 3),
                    reliability=reliability,
                    issues=outlier_issues + drift_issues + integrity_issues + freshness_issues,
                )
            )

        aggregate = round(
            (0.55 * completeness)
            + (0.45 * (sum(score.reliability for score in source_scores) / len(source_scores))),
            3,
        )
        return QualityReport(
            aggregate_confidence=aggregate,
            source_scores=source_scores,
            missing_sources=missing_sources,
        )
