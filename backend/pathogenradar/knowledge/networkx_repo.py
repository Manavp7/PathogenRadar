"""NetworkX-backed implementation of the knowledge graph.

Builds a heterogeneous graph linking diseases to their symptoms, vectors, weather drivers
and observable signals, and ranks candidate diseases against observed evidence.
"""

from __future__ import annotations

import math
from collections import Counter
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
        self._idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        """Inverse-document-frequency weight per signal.

        A signal listed by many diseases (e.g. hospital_admissions) is weak evidence for any
        particular one; a distinctive signal (cough, rash, diarrhea) is strong evidence. This
        prevents diseases that share many generic signals from dominating classification.
        """
        n = len(self._data)
        df: Counter[str] = Counter()
        for info in self._data.values():
            for sig in set(info.get("signals", [])):
                df[sig] += 1
        return {sig: math.log((1 + n) / (1 + count)) + 1.0 for sig, count in df.items()}

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
            # IDF-weighted overlap: distinctive symptoms dominate over generic ones.
            matched = {s: elevated_signals[s] for s in disease_signals if s in elevated_signals}
            if not matched:
                continue
            weighted_match = sum(elevated_signals[s] * self._idf.get(s, 1.0) for s in matched)
            total_weight = sum(self._idf.get(s, 1.0) for s in disease_signals)
            signal_score = weighted_match / total_weight if total_weight else 0.0

            # Weather corroboration: a small tiebreaker, never a dominant term.
            weather_bonus = 0.0
            drivers = info.get("weather_drivers", {})
            for driver, effect in drivers.items():
                state = weather_context.get(driver)
                if effect == "positive" and state == "high":
                    weather_bonus += 0.04
                elif effect == "negative" and state == "low":
                    weather_bonus += 0.03

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
