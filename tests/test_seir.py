"""Phase 3.8 — SEIR simulator and intervention effects."""

from __future__ import annotations

from pathogenradar.domain.models import Intervention
from pathogenradar.simulation.seir import simulate, transmission_multiplier


def test_baseline_epidemic_peaks():
    res = simulate("ernakulam", "dengue", days=160)
    assert res.peak_infected_baseline > 0
    assert 0 < res.peak_day_baseline < 160
    # SEIR conservation: compartments always sum to population (within rounding).
    last = -1
    total = (
        res.baseline.susceptible[last]
        + res.baseline.exposed[last]
        + res.baseline.infected[last]
        + res.baseline.recovered[last]
    )
    assert abs(total - res.population) / res.population < 0.01


def test_interventions_reduce_and_flatten_peak():
    none = simulate("ernakulam", "covid_like", days=160, intervention=Intervention())
    strong = simulate(
        "ernakulam",
        "covid_like",
        days=160,
        intervention=Intervention(
            school_closure=1.0, masking=1.0, travel_restriction=1.0, vaccination_rate=0.3
        ),
    )
    assert strong.peak_infected_intervention < none.peak_infected_baseline
    assert strong.cases_averted > 0
    # Strong intervention lowers the effective reproduction number.
    assert strong.effective_r < none.r0


def test_transmission_multiplier_monotonic():
    base = transmission_multiplier(Intervention())
    masked = transmission_multiplier(Intervention(masking=1.0))
    everything = transmission_multiplier(
        Intervention(school_closure=1.0, masking=1.0, travel_restriction=1.0)
    )
    assert base == 1.0
    assert masked < base
    assert everything < masked


def test_stronger_intervention_averts_more_cases():
    mild = simulate("kozhikode", "dengue", days=160, intervention=Intervention(masking=0.3))
    strong = simulate("kozhikode", "dengue", days=160, intervention=Intervention(masking=1.0))
    assert strong.cases_averted >= mild.cases_averted
