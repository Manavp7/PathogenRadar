"""Fusion engine: combine per-detector anomaly scores into a unified risk score.

This is the deterministic, statistical core of the platform (no LLM). Detector weights
reflect signal trust/lead-time; confidence from the data-quality layer tempers the result.
"""

from __future__ import annotations

# Relative importance of each detector family in the fused risk.
DETECTOR_WEIGHTS: dict[str, float] = {
    "hospital": 0.35,  # most specific / actionable
    "search": 0.30,  # earliest leading indicator
    "wastewater": 0.20,  # objective environmental signal
    "social": 0.15,  # noisy but timely
}


def fuse_scores(detector_scores: dict[str, float], confidence: float = 1.0) -> float:
    """Combine detector scores (each 0..1) into a fused signal in [0, 1].

    Missing detectors are ignored and the remaining weights renormalised. ``confidence``
    (0..1) mildly tempers the score so low-quality data cannot raise a full-blown alert.
    """
    num = 0.0
    den = 0.0
    for detector, weight in DETECTOR_WEIGHTS.items():
        score = detector_scores.get(detector)
        if score is None:
            continue
        num += weight * max(0.0, min(1.0, score))
        den += weight
    if den == 0:
        return 0.0
    fused = num / den
    # Confidence in [0,1] scales risk between 70% and 100% of its raw value.
    temper = 0.7 + 0.3 * max(0.0, min(1.0, confidence))
    return float(max(0.0, min(1.0, fused * temper)))


def risk_score(detector_scores: dict[str, float], confidence: float = 1.0) -> float:
    """Fused risk on a 0..100 scale."""
    return round(100.0 * fuse_scores(detector_scores, confidence), 2)
