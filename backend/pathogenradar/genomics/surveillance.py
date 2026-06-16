"""Synthetic variant-frequency surveillance + emerging-variant detection."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np


@dataclass(frozen=True)
class Variant:
    id: str
    name: str
    transmissibility: float  # multiplier vs baseline R0 (1.0 = neutral)
    severity: float  # multiplier vs baseline IFR (1.0 = neutral)


# Synthetic dengue lineage panel with one emerging, more transmissible variant.
DENGUE_VARIANTS: list[Variant] = [
    Variant("denv1", "DENV-1", 1.00, 1.00),
    Variant("denv2", "DENV-2", 1.05, 1.10),
    Variant("denv3", "DENV-3", 1.00, 1.00),
    Variant("denvx", "DENV-X (emerging)", 1.40, 1.30),
]
EMERGING_ID = "denvx"


def _seed_for(region: str) -> int:
    return int(hashlib.sha256(region.encode()).hexdigest(), 16) % (2**32)


def variant_frequencies(
    region: str,
    days: int = 120,
    as_of: date | None = None,
    variants: list[Variant] | None = None,
    seed: int | None = None,
) -> tuple[list[date], dict[str, list[float]]]:
    """Daily lineage shares (summing to 1) per variant, with one variant emerging logistically."""
    variants = variants or DENGUE_VARIANTS
    end = as_of or date.today()
    rng = np.random.default_rng(seed if seed is not None else _seed_for(region))
    dates = [end - timedelta(days=days - 1 - i) for i in range(days)]

    # Stable baseline weights for established variants + a logistically growing emerging one.
    base = {v.id: rng.uniform(2.0, 4.0) for v in variants if v.id != EMERGING_ID}
    onset = int(days * 0.65)
    ramp = days * 0.5

    shares: dict[str, list[float]] = {v.id: [] for v in variants}
    for t in range(days):
        emerging_raw = 0.1 + 9.0 / (1.0 + np.exp(-(t - onset) / (ramp / 4)))
        raw = {v.id: base.get(v.id, emerging_raw) * (1.0 + rng.normal(0, 0.03)) for v in variants}
        total = sum(raw.values())
        for v in variants:
            shares[v.id].append(max(0.0, raw[v.id] / total))
    return dates, shares


def current_shares(shares: dict[str, list[float]]) -> dict[str, float]:
    return {vid: series[-1] for vid, series in shares.items()}


def detect_emerging(
    shares: dict[str, list[float]],
    window: int = 60,
    slope_threshold: float = 0.10,
    min_share: float = 0.20,
) -> list[dict]:
    """Variants that have risen materially over the window and are now significant."""
    out = []
    for vid, series in shares.items():
        if len(series) <= window:
            continue
        slope = series[-1] - series[-window]
        if slope >= slope_threshold and series[-1] >= min_share:
            out.append(
                {"variant": vid, "current_share": round(series[-1], 4), "slope": round(slope, 4)}
            )
    out.sort(key=lambda x: x["slope"], reverse=True)
    return out


def r0_multiplier(shares_now: dict[str, float], variants: list[Variant] | None = None) -> float:
    """Share-weighted transmissibility multiplier to apply to baseline R0."""
    variants = variants or DENGUE_VARIANTS
    vmap = {v.id: v for v in variants}
    total = sum(shares_now.get(v.id, 0.0) for v in variants) or 1.0
    return sum(shares_now.get(v.id, 0.0) * vmap[v.id].transmissibility for v in variants) / total


def severity_multiplier(
    shares_now: dict[str, float], variants: list[Variant] | None = None
) -> float:
    variants = variants or DENGUE_VARIANTS
    vmap = {v.id: v for v in variants}
    total = sum(shares_now.get(v.id, 0.0) for v in variants) or 1.0
    return sum(shares_now.get(v.id, 0.0) * vmap[v.id].severity for v in variants) / total
