"""Generate synthetic data and run the full pipeline, persisting per-region artifacts.

Seeds ALL configured regions with a named scenario (default: multi — simultaneous vector +
respiratory + waterborne outbreaks) so the dashboard + national roll-up have a rich story.
Usage:  python scripts/seed.py [scenario] [region|all]
        scenario in {dengue,respiratory,waterborne,multi}; region defaults to all.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from pathogenradar.regions import available_regions  # noqa: E402
from pathogenradar.scenarios import SCENARIOS, run_scenario  # noqa: E402


def main() -> None:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "multi"
    target = sys.argv[2] if len(sys.argv) > 2 else "all"
    if scenario not in SCENARIOS:
        print(f"Unknown scenario '{scenario}'. Options: {', '.join(SCENARIOS)}")
        sys.exit(1)

    regions = available_regions() if target == "all" else [target]
    for region in regions:
        print(f"PathogenRadar — seeding '{scenario}' scenario ({region})...")
        result = run_scenario(scenario, region=region)
        print(f"  districts {len(result.forecasts)} · alerts {len(result.alerts)} · {result.end}")
        for a in result.alerts[:3]:
            print(f"    - {a.headline}")
    print("Done. Run `make api` and `make dev-frontend`, or `make demo` for the walkthrough.")


if __name__ == "__main__":
    main()
