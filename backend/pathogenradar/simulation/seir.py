"""SEIR epidemiological simulator with intervention levers.

Deterministic compartmental model (Susceptible → Exposed → Infected → Recovered) seeded with
disease parameters from the knowledge graph. Public-health interventions reduce the effective
transmission rate so officials can answer: "what happens if we intervene now?"
"""

from __future__ import annotations

from ..domain.models import Intervention, SeirCurve, SeirResult
from ..knowledge import KnowledgeGraphRepo, get_knowledge_graph
from ..regions import get_district

# Maximum fractional reduction in transmission attributable to each lever (at full intensity).
LEVER_MAX_REDUCTION = {
    "school_closure": 0.20,
    "masking": 0.35,
    "travel_restriction": 0.15,
}


def transmission_multiplier(intervention: Intervention) -> float:
    """Combined multiplicative effect of non-pharmaceutical interventions on beta (0..1)."""
    factor = 1.0
    factor *= 1.0 - LEVER_MAX_REDUCTION["school_closure"] * _clamp(intervention.school_closure)
    factor *= 1.0 - LEVER_MAX_REDUCTION["masking"] * _clamp(intervention.masking)
    factor *= 1.0 - LEVER_MAX_REDUCTION["travel_restriction"] * _clamp(
        intervention.travel_restriction
    )
    return factor


def _run(
    population: float,
    beta: float,
    sigma: float,
    gamma: float,
    i0: float,
    e0: float,
    vaccinated_fraction: float,
    days: int,
) -> SeirCurve:
    n = population
    vaccinated = vaccinated_fraction * (n - i0 - e0)
    s = n - i0 - e0 - vaccinated
    e, i, r = e0, i0, vaccinated

    days_list, sl, el, il, rl = [], [], [], [], []
    for day in range(days + 1):
        days_list.append(day)
        sl.append(s)
        el.append(e)
        il.append(i)
        rl.append(r)
        new_exposed = beta * s * i / n if n > 0 else 0.0
        new_infectious = sigma * e
        new_recovered = gamma * i
        s = max(0.0, s - new_exposed)
        e = max(0.0, e + new_exposed - new_infectious)
        i = max(0.0, i + new_infectious - new_recovered)
        r = r + new_recovered

    return SeirCurve(
        days=days_list,
        susceptible=[round(x, 1) for x in sl],
        exposed=[round(x, 1) for x in el],
        infected=[round(x, 1) for x in il],
        recovered=[round(x, 1) for x in rl],
    )


def simulate(
    district_id: str,
    disease: str,
    intervention: Intervention | None = None,
    days: int = 160,
    initial_infected: float | None = None,
    kg: KnowledgeGraphRepo | None = None,
    region: str | None = None,
    r0_multiplier: float = 1.0,
) -> SeirResult:
    kg = kg or get_knowledge_graph()
    district = get_district(district_id, region)
    epi = kg.epi_params(disease)

    population = float(district.population)
    effective_r0 = epi.r0 * max(0.1, r0_multiplier)  # genomic transmissibility coupling
    beta = effective_r0 / epi.infectious_days
    sigma = 1.0 / max(epi.incubation_days, 0.5)
    gamma = 1.0 / max(epi.infectious_days, 0.5)

    i0 = initial_infected if initial_infected is not None else max(20.0, population * 2e-5)
    e0 = i0  # assume a comparable pool already incubating

    baseline = _run(population, beta, sigma, gamma, i0, e0, 0.0, days)
    peak_b, peak_day_b = _peak(baseline.infected)

    result = SeirResult(
        district_id=district_id,
        disease=disease,
        population=int(population),
        r0=round(effective_r0, 3),
        effective_r=round(effective_r0 * (1.0 - i0 / population), 3),
        baseline=baseline,
        peak_infected_baseline=round(peak_b, 1),
        peak_day_baseline=peak_day_b,
    )

    if intervention is not None:
        mult = transmission_multiplier(intervention)
        eff_beta = beta * mult
        vacc = _clamp(intervention.vaccination_rate)
        inter = _run(population, eff_beta, sigma, gamma, i0, e0, vacc, days)
        peak_i, peak_day_i = _peak(inter.infected)
        cases_baseline = population - baseline.susceptible[-1]
        cases_inter = (population * (1 - vacc)) - inter.susceptible[-1]
        result.intervention = inter
        result.effective_r = round(effective_r0 * mult * (1.0 - vacc) * (1.0 - i0 / population), 3)
        result.peak_infected_intervention = round(peak_i, 1)
        result.peak_day_intervention = peak_day_i
        result.cases_averted = round(max(0.0, cases_baseline - cases_inter), 1)

    return result


def _peak(series: list[float]) -> tuple[float, int]:
    peak = max(series)
    return peak, series.index(peak)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))
