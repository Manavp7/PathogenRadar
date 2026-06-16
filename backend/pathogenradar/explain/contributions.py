"""Explainability: turn the drivers behind a risk score into human-readable contributions.

Mirrors the briefing-style breakdown government officials expect, e.g.:
    Risk 87% — ICU occupancy +21%, fever searches +17%, wastewater +34%, PCR requests +9%
"""

from __future__ import annotations

from ..domain.models import Contribution

SIGNAL_LABELS: dict[str, str] = {
    "hospital_admissions": "Hospital admissions",
    "icu_occupancy": "ICU occupancy",
    "ventilator_usage": "Ventilator usage",
    "mortality": "Mortality",
    "lab_pcr_requests": "PCR test requests",
    "search_fever": "Fever searches",
    "search_cough": "Cough searches",
    "search_rash": "Rash searches",
    "search_vomiting": "Vomiting searches",
    "search_diarrhea": "Diarrhea searches",
    "social_mentions": "Social media mentions",
    "wastewater_viral_load": "Wastewater viral load",
    "multivariate_context": "Unusual joint hospital pattern",
}

WEATHER_LABELS = {
    "rainfall": "Rainfall",
    "humidity": "Humidity",
    "temp": "Temperature",
}


def build_contributions(
    signal_pct: dict[str, float],
    signal_anomaly: dict[str, float],
    weather_state: dict[str, str] | None = None,
    top_k: int = 6,
) -> list[Contribution]:
    """Build a ranked list of contributions.

    ``signal_pct`` maps signal -> percent change vs trailing baseline (for the headline %).
    ``signal_anomaly`` maps signal -> 0..1 anomaly intensity (for ranking importance).
    """
    contribs: list[Contribution] = []
    for signal, anom in signal_anomaly.items():
        if anom <= 0.01:
            continue
        label = SIGNAL_LABELS.get(signal, signal)
        pct = signal_pct.get(signal)
        if pct is not None and signal != "multivariate_context":
            value = round(pct, 1)
            detail = f"{'+' if value >= 0 else ''}{value}% vs baseline"
        else:
            value = round(anom * 100, 1)
            detail = "anomalous pattern"
        contribs.append(Contribution(label=label, value=value, detail=detail))

    contribs.sort(key=lambda c: signal_anomaly.get(_inverse_label(c.label), 0.0), reverse=True)
    contribs = contribs[:top_k]

    # Add weather corroboration as context (not ranked among signals).
    weather_state = weather_state or {}
    for driver, state in weather_state.items():
        if state == "high":
            contribs.append(
                Contribution(
                    label=f"{WEATHER_LABELS.get(driver, driver)} (favourable conditions)",
                    value=0.0,
                    detail="elevated — supports environmental transmission",
                )
            )
    return contribs


def _inverse_label(label: str) -> str:
    for sig, lab in SIGNAL_LABELS.items():
        if lab == label:
            return sig
    return label
