"""Flagship end-to-end walkthrough.

Injects a dengue outbreak in one Kerala district and narrates the full pipeline from raw
signals to executive decision — the nine Done-Criteria steps. Persists artifacts so the
dashboard immediately reflects the scenario.

Usage:  python scripts/demo_scenario.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from pathogenradar.detection.engine import latest_by_district  # noqa: E402
from pathogenradar.domain.models import Intervention  # noqa: E402
from pathogenradar.llm.briefing import generate_briefing  # noqa: E402
from pathogenradar.pipeline import golden_scenario  # noqa: E402
from pathogenradar.simulation.seir import simulate  # noqa: E402

BAR = "=" * 78


def step(n: int, title: str) -> None:
    print(f"\n{BAR}\n  STEP {n}: {title}\n{BAR}")


def main() -> None:
    print("PathogenRadar — end-to-end disease intelligence walkthrough (Kerala)")
    district = "ernakulam"

    step(1, "Acquire signals + inject a synthetic dengue outbreak")
    result = golden_scenario(district_id=district, persist=True)
    print(f"  region={result.region}  window={result.start}..{result.end}")
    print(f"  data sources: {result.source_summary}")
    print(
        "  source reliability: "
        + ", ".join(
            f"{s.source_id}={s.reliability:.0%}" for s in result.quality.source_reliability.values()
        )
    )

    latest = latest_by_district(result.assessments)
    ek = latest[district]

    step(2, "Detect signal anomalies (per-source intelligence)")
    for det, score in sorted(ek.signal_scores.items(), key=lambda x: -x[1]):
        print(f"  {det:<12} anomaly {score:.2f}")

    step(3, "Fuse signals -> unified risk score + classification")
    print(f"  {ek.district_name}: RISK {ek.risk_score:.0f}/100  ->  {ek.level.value.upper()}")
    print(f"  category: {ek.category.value}   likely: {', '.join(ek.likely_diseases[:3])}")
    print(f"  confidence: {ek.confidence:.0%}")

    step(4, "District heatmap (risk across all 14 districts)")
    for a in sorted(latest.values(), key=lambda x: -x.risk_score)[:6]:
        print(f"  {a.district_name:<20} {a.risk_score:5.1f}  {a.level.value}")

    step(5, "Why? — explainability")
    for c in ek.contributions[:6]:
        print(f"  + {c.label:<28} {c.detail}")

    step(6, "Spread forecast — neighbouring districts (deterministic diffusion)")
    for f in result.forecasts[:6]:
        pts = "  ".join(f"{p.horizon_days}d={p.risk_probability:.0%}" for p in f.points)
        print(f"  {f.district_name:<20} {pts}")

    step(7, "SEIR simulation — project cases & test interventions")
    sim = simulate(
        district,
        "dengue",
        intervention=Intervention(
            school_closure=0.5, masking=0.7, vaccination_rate=0.2, travel_restriction=0.3
        ),
    )
    peak_b = f"{sim.peak_infected_baseline:,.0f}"
    peak_i = f"{sim.peak_infected_intervention:,.0f}"
    print(f"  baseline peak infected : {peak_b} (day {sim.peak_day_baseline})")
    print(f"  with interventions     : {peak_i} (R {sim.r0} -> {sim.effective_r})")
    print(f"  cases averted          : {sim.cases_averted:,.0f}")

    step(8, "Alerting — escalation + recommended actions")
    for al in result.alerts:
        print(f"  [{al.level.value}] {al.headline}")
        print(f"     channels: {', '.join(al.channels)}")
        for act in al.recommended_actions[:3]:
            print(f"     - {act}")

    step(9, "Minister briefing (generated offline, no LLM required)")
    briefing = generate_briefing(
        region=result.region,
        as_of=result.as_of,
        risk_latest=[a.model_dump(mode="json") for a in latest.values()],
        forecasts=[f.model_dump(mode="json") for f in result.forecasts],
        source_summary=result.source_summary,
    )
    print(f"  provider: {briefing.provider}")
    print()
    for line in briefing.body.splitlines():
        print(f"  {line}")

    print(f"\n{BAR}")
    print("  Pipeline complete: raw signals -> executive decision.")
    print("  Launch the platform:  make api   +   make dev-frontend   (http://localhost:5173)")
    print(BAR)


if __name__ == "__main__":
    main()
