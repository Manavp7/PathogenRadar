import json
from pathlib import Path
from typing import Any

from pathogenradar_api.domain.models import District, MobilityEdge, SignalObservation

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load_json(name: str) -> Any:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as fixture:
        return json.load(fixture)


class DemoRepository:
    """Fixture-backed repository for deterministic demo intelligence."""

    def __init__(self) -> None:
        self._districts = tuple(District.model_validate(row) for row in _load_json("districts.json"))
        self._observations = tuple(
            SignalObservation.model_validate(row) for row in _load_json("signals.json")
        )
        self._mobility_edges = tuple(
            MobilityEdge.model_validate(row) for row in _load_json("mobility_edges.json")
        )
        self._knowledge_graph = _load_json("disease_knowledge_graph.json")

    def list_districts(self) -> tuple[District, ...]:
        return self._districts

    def get_district(self, district_id: str) -> District:
        for district in self.list_districts():
            if district.id == district_id:
                return district
        raise KeyError(f"Unknown district_id: {district_id}")

    def _signals(self) -> tuple[SignalObservation, ...]:
        return self._observations

    def list_signals(self, district_id: str | None = None) -> list[SignalObservation]:
        signals = list(self._signals())
        if district_id is None:
            return signals
        return [signal for signal in signals if signal.district_id == district_id]

    def get_mobility_edges(self) -> tuple[MobilityEdge, ...]:
        return self._mobility_edges

    def get_knowledge_graph(self) -> dict[str, Any]:
        return self._knowledge_graph
