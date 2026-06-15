"""Generate synthetic data and run the full pipeline once, persisting artifacts.

Runs the flagship dengue scenario so the dashboard has a meaningful story out of the box.
Usage:  python scripts/seed.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from pathogenradar.pipeline import golden_scenario  # noqa: E402


def main() -> None:
    print("PathogenRadar — seeding flagship dengue scenario (Kerala)...")
    result = golden_scenario()
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
