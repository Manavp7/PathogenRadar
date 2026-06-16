"""P3.2 — genomic surveillance: emerging variant detection + SEIR coupling."""

from __future__ import annotations

from datetime import date

from pathogenradar.genomics import (
    current_shares,
    detect_emerging,
    r0_multiplier,
    variant_frequencies,
)
from pathogenradar.simulation.seir import simulate

AS_OF = date(2024, 6, 30)


def test_variant_frequencies_sum_to_one():
    _, shares = variant_frequencies("kerala", days=120, as_of=AS_OF)
    n = len(next(iter(shares.values())))
    for t in range(n):
        total = sum(series[t] for series in shares.values())
        assert abs(total - 1.0) < 1e-6


def test_emerging_variant_detected():
    _, shares = variant_frequencies("kerala", days=120, as_of=AS_OF)
    emerging = detect_emerging(shares)
    assert emerging
    assert emerging[0]["variant"] == "denvx"
    assert emerging[0]["current_share"] > 0.1


def test_emerging_variant_raises_effective_r_and_peak():
    _, shares = variant_frequencies("kerala", days=120, as_of=AS_OF)
    mult = r0_multiplier(current_shares(shares))
    assert mult > 1.0  # emerging variant is more transmissible

    base = simulate("ernakulam", "dengue", days=160)
    variant_adjusted = simulate("ernakulam", "dengue", days=160, r0_multiplier=mult)
    assert variant_adjusted.effective_r > base.effective_r
    assert variant_adjusted.peak_infected_baseline > base.peak_infected_baseline
