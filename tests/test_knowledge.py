"""Phase 3.5 — disease knowledge graph matching."""

from __future__ import annotations

from pathogenradar.domain.models import DiseaseCategory
from pathogenradar.knowledge import get_knowledge_graph


def test_dengue_is_top_match_for_vector_evidence():
    kg = get_knowledge_graph()
    elevated = {
        "search_fever": 0.9,
        "search_rash": 0.8,
        "hospital_admissions": 0.7,
        "lab_pcr_requests": 0.6,
        "wastewater_viral_load": 0.4,
    }
    weather = {"rainfall": "high", "humidity": "high"}
    matches = kg.match_diseases(elevated, weather, top_k=3)
    assert matches
    assert matches[0].category == DiseaseCategory.VECTOR
    assert matches[0].disease in {"dengue", "chikungunya"}


def test_respiratory_evidence_picks_respiratory():
    kg = get_knowledge_graph()
    elevated = {
        "search_cough": 0.9,
        "search_fever": 0.7,
        "icu_occupancy": 0.6,
        "ventilator_usage": 0.5,
    }
    matches = kg.match_diseases(elevated, {"temp": "low"}, top_k=3)
    assert matches[0].category == DiseaseCategory.RESPIRATORY


def test_epi_params_available_for_all_diseases():
    kg = get_knowledge_graph()
    for disease in kg.diseases():
        epi = kg.epi_params(disease)
        assert epi.r0 > 0
        assert epi.infectious_days > 0
