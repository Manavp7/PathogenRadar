"""Phase 3.7 — deterministic spread forecast across the district graph."""

from __future__ import annotations

from pathogenradar.forecast.deterministic import forecast_spread
from pathogenradar.regions import get_district


def _by_id(forecasts):
    return {f.district_id: f for f in forecasts}


def test_outbreak_spreads_to_neighbours_first():
    # Seed a strong outbreak in Ernakulam only.
    current = {"ernakulam": 90.0}
    forecasts = _by_id(forecast_spread(current))

    neighbour = "thrissur"  # adjacent to Ernakulam
    far = "kasaragod"  # opposite end of Kerala

    assert neighbour in get_district("ernakulam").neighbors
    n30 = forecasts[neighbour].points[-1].risk_probability
    f30 = forecasts[far].points[-1].risk_probability
    # A direct neighbour must show higher 30-day spread probability than a far district.
    assert n30 > f30


def test_spread_probability_monotonic_in_horizon():
    forecasts = _by_id(forecast_spread({"ernakulam": 90.0}))
    for f in forecasts.values():
        probs = [p.risk_probability for p in f.points]
        assert probs == sorted(probs)  # non-decreasing over 7/14/21/30 days


def test_seed_district_stays_highest():
    forecasts = forecast_spread({"ernakulam": 90.0})
    top = forecasts[0]  # sorted by 30-day probability desc
    assert top.district_id == "ernakulam"


def test_no_outbreak_no_spread():
    forecasts = forecast_spread({})
    assert all(p.risk_probability == 0.0 for f in forecasts for p in f.points)
