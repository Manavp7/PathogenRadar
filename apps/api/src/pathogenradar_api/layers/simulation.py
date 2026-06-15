from pathogenradar_api.domain.models import DiseaseState, InterventionType, SimulationRequest, SimulationResult


EFFECTS: dict[InterventionType, float] = {
    InterventionType.SCHOOL_CLOSURE: 0.11,
    InterventionType.MASKING: 0.14,
    InterventionType.VACCINATION: 0.18,
    InterventionType.TRAVEL_RESTRICTION: 0.13,
    InterventionType.VECTOR_CONTROL: 0.22,
    InterventionType.WATER_SANITATION: 0.2,
    InterventionType.PUBLIC_COMMUNICATION: 0.08,
    InterventionType.HOSPITAL_PREPAREDNESS: 0.04,
}


class EpidemiologicalSimulator:
    """Small deterministic SEIR-style scenario comparator."""

    def run(self, request: SimulationRequest, disease_state: DiseaseState) -> SimulationResult:
        intensity = min(1.0, sum(disease_state.state_vector) / 1.5)
        susceptible = disease_state.district.population * 0.38
        initial_exposed = max(25, int(disease_state.district.population * intensity * 0.00008))
        reproduction_number = 1.0 + (intensity * 1.15)
        growth_cycles = request.horizon_days / 7
        baseline_cases = int(initial_exposed * (reproduction_number**growth_cycles))

        combined_effect = 0.0
        for intervention in request.interventions:
            combined_effect += EFFECTS.get(intervention, 0.0) * request.compliance
        combined_effect = min(0.72, combined_effect)
        intervention_cases = int(baseline_cases * (1 - combined_effect))
        effective_r = reproduction_number * (1 - combined_effect)

        return SimulationResult(
            district_id=disease_state.district.id,
            horizon_days=request.horizon_days,
            baseline_projected_cases=min(int(susceptible), baseline_cases),
            intervention_projected_cases=min(int(susceptible), intervention_cases),
            estimated_cases_averted=max(0, baseline_cases - intervention_cases),
            effective_reproduction_number=round(effective_r, 2),
            assumptions=[
                "Synthetic district-level demo data only",
                "Simple deterministic SEIR-style growth approximation",
                "Intervention effects are illustrative, not clinically validated",
            ],
        )
