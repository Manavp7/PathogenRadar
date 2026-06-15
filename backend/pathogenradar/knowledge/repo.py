"""Knowledge-graph interface.

The application depends ONLY on this protocol, so the backing store can be swapped
(NetworkX today, Neo4j later) without touching the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..domain.models import DiseaseCategory


@dataclass
class DiseaseMatch:
    disease: str
    display_name: str
    category: DiseaseCategory
    score: float  # 0..1 match strength given the elevated signals + weather
    matched_signals: list[str] = field(default_factory=list)


@dataclass
class EpiParams:
    r0: float
    incubation_days: float
    infectious_days: float
    ifr: float


@runtime_checkable
class KnowledgeGraphRepo(Protocol):
    def diseases(self) -> list[str]: ...

    def display_name(self, disease: str) -> str: ...

    def category_for(self, disease: str) -> DiseaseCategory: ...

    def epi_params(self, disease: str) -> EpiParams: ...

    def match_diseases(
        self,
        elevated_signals: dict[str, float],
        weather_context: dict[str, str] | None = None,
        top_k: int = 3,
    ) -> list[DiseaseMatch]:
        """Rank diseases by how well their signal/weather profile matches the evidence.

        ``elevated_signals`` maps signal_type -> elevation strength (0..1).
        ``weather_context`` maps a weather driver (rainfall/humidity/temp) -> "high"/"low".
        """

    def neighbors(self, node: str) -> list[str]:
        """Graph neighbours of a node (disease/symptom/vector/signal) — for explainability."""
