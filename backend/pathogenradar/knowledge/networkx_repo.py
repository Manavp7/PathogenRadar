"""NetworkX-backed implementation of the knowledge graph.

Builds a heterogeneous graph linking diseases to their symptoms, vectors, weather drivers
and observable signals, and ranks candidate diseases against observed evidence.
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import yaml

from ..domain.models import DiseaseCategory
from .repo import DiseaseMatch, EpiParams

DISEASES_FILE = Path(__file__).parent / "diseases.yaml"


class NetworkXGraphRepo:
    def __init__(self, path: Path | None = None):
        with open(path or DISEASES_FILE, encoding="utf-8") as fh:
            self._data = yaml.safe_load(fh)["diseases"]
        self._graph = self._build_graph()

    def _build_graph(self) -> nx.Graph:
        g = nx.Graph()
        for key, info in self._data.items():
            g.add_node(key, kind="disease", **{"display_name": info["display_name"]})
            for sym in info.get("symptoms", []):
                g.add_node(f"symptom:{sym}", kind="symptom")
                g.add_edge(key, f"symptom:{sym}", relation="presents")
            for vec in info.get("vectors", []):
                g.add_node(f"vector:{vec}", kind="vector")
                g.add_edge(key, f"vector:{vec}", relation="transmitted_by")
            for sig in info.get("signals", []):
                g.add_node(f"signal:{sig}", kind="signal")
                g.add_edge(key, f"signal:{sig}", relation="observed_via")
            for driver, effect in info.get("weather_drivers", {}).items():
                if effect == "positive":
                    g.add_node(f"weather:{driver}", kind="weather")
                    g.add_edge(key, f"weather:{driver}", relation="driven_by")
        return g

    # ---- KnowledgeGraphRepo protocol ----

    def diseases(self) -> list[str]:
        return list(self._data.keys())

    def display_name(self, disease: str) -> str:
        return self._data[disease]["display_name"]

    def category_for(self, disease: str) -> DiseaseCategory:
        return DiseaseCategory(self._data[disease]["category"])

    def epi_params(self, disease: str) -> EpiParams:
        epi = self._data[disease]["epi"]
        return EpiParams(
            r0=float(epi["r0"]),
            incubation_days=float(epi["incubation_days"]),
            infectious_days=float(epi["infectious_days"]),
            ifr=float(epi.get("ifr", 0.001)),
        )

    def neighbors(self, node: str) -> list[str]:
        return list(self._graph.neighbors(node)) if node in self._graph else []

    def match_diseases(
        self,
        elevated_signals: dict[str, float],
        weather_context: dict[str, str] | None = None,
        top_k: int = 3,
    ) -> list[DiseaseMatch]:
        weather_context = weather_context or {}
        matches: list[DiseaseMatch] = []
        for key, info in self._data.items():
            disease_signals = set(info.get("signals", []))
            if not disease_signals:
                continue
            # Signal overlap weighted by elevation strength.
            matched = {s: elevated_signals[s] for s in disease_signals if s in elevated_signals}
            if not matched:
                continue
            signal_score = sum(matched.values()) / len(disease_signals)

            # Weather corroboration: reward when a positive driver is currently "high".
            weather_bonus = 0.0
            drivers = info.get("weather_drivers", {})
            for driver, effect in drivers.items():
                state = weather_context.get(driver)
                if effect == "positive" and state == "high":
                    weather_bonus += 0.15
                elif effect == "negative" and state == "low":
                    weather_bonus += 0.10

            score = min(1.0, signal_score + weather_bonus)
            matches.append(
                DiseaseMatch(
                    disease=key,
                    display_name=info["display_name"],
                    category=DiseaseCategory(info["category"]),
                    score=round(score, 4),
                    matched_signals=sorted(matched.keys()),
                )
            )

        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:top_k]
