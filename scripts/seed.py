"""Generate synthetic data and run the full pipeline once, persisting artifacts.

Runs a named scenario (default: multi — simultaneous vector + respiratory + waterborne
outbreaks) so the dashboard has a rich story out of the box.
Usage:  python scripts/seed.py [scenario]   # scenario in {dengue,respiratory,waterborne,multi}
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from pathogenradar.scenarios import SCENARIOS, run_scenario  # noqa: E402


def main() -> None:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "multi"
    if scenario not in SCENARIOS:
        print(f"Unknown scenario '{scenario}'. Options: {', '.join(SCENARIOS)}")
        sys.exit(1)
    print(f"PathogenRadar — seeding '{scenario}' scenario (Kerala)...")
    result = run_scenario(scenario)
    on_alert = [a for a in result.alerts]
    print(f"  region        : {result.region}")
    print(f"  window        : {result.start} -> {result.end}")
    print(f"  sources       : {result.source_summary}")
    print(f"  districts      : {len(result.forecasts)}")
    print(f"  active alerts  : {len(on_alert)}")
    for a in on_alert[:5]:
        print(f"    - {a.headline}")
    print("Done. Run `make api` and `make dev-frontend`, or `make demo` for the full walkthrough.")


if __name__ == "__main__":
    main()
