"""Genomic surveillance (Phase 3 — SYNTHETIC).

Models variant/lineage frequency over time, detects emerging variants, and couples their
transmissibility/severity to the SEIR simulator (R0 *= variant multiplier). Data here is
clearly synthetic — a production deployment would ingest real sequencing/GISAID-style feeds
through the same interface.
"""

from .surveillance import (
    DENGUE_VARIANTS,
    Variant,
    current_shares,
    detect_emerging,
    r0_multiplier,
    severity_multiplier,
    variant_frequencies,
)

__all__ = [
    "DENGUE_VARIANTS",
    "Variant",
    "current_shares",
    "detect_emerging",
    "r0_multiplier",
    "severity_multiplier",
    "variant_frequencies",
]
