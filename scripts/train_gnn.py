"""Train the GNN spread forecaster on simulated outbreaks.

Requires the optional ML deps:  pip install -r requirements-ml.txt
Usage:  python scripts/train_gnn.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from pathogenradar.forecast.gnn import torch_available, train_gnn  # noqa: E402


def main() -> None:
    if not torch_available():
        print("PyTorch not installed. Run: pip install -r requirements-ml.txt")
        sys.exit(1)
    print("Training GNN spread forecaster on simulated outbreaks...")
    meta = train_gnn()
    print(f"  region            : {meta['region']}")
    print(f"  scenarios/epochs  : {meta['n_scenarios']} / {meta['epochs']}")
    print(f"  GNN MAE           : {meta['gnn_mae']}")
    print(f"  deterministic MAE : {meta['deterministic_mae']}")
    better = meta["gnn_mae"] < meta["deterministic_mae"]
    print(f"  GNN beats baseline: {better}")
    print("Set FORECAST_MODEL=gnn to use it.")


if __name__ == "__main__":
    main()
