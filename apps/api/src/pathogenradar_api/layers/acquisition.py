from typing import Protocol

from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.domain.models import SignalObservation, SignalSource


class DataConnector(Protocol):
    source: SignalSource

    def collect(self, district_id: str | None = None) -> list[SignalObservation]:
        """Collect observations for one district or all available districts."""


class FixtureSignalConnector:
    def __init__(self, repository: DemoRepository, source: SignalSource) -> None:
        self.repository = repository
        self.source = source

    def collect(self, district_id: str | None = None) -> list[SignalObservation]:
        return [
            signal
            for signal in self.repository.list_signals(district_id)
            if signal.source == self.source
        ]


class HospitalSignalConnector(FixtureSignalConnector):
    def __init__(self, repository: DemoRepository) -> None:
        super().__init__(repository, SignalSource.HOSPITAL)


class SearchTrendConnector(FixtureSignalConnector):
    def __init__(self, repository: DemoRepository) -> None:
        super().__init__(repository, SignalSource.SEARCH)


class SocialSignalConnector(FixtureSignalConnector):
    def __init__(self, repository: DemoRepository) -> None:
        super().__init__(repository, SignalSource.SOCIAL)


class WeatherSignalConnector(FixtureSignalConnector):
    def __init__(self, repository: DemoRepository) -> None:
        super().__init__(repository, SignalSource.WEATHER)


class EnvironmentalSignalConnector(FixtureSignalConnector):
    def __init__(self, repository: DemoRepository) -> None:
        super().__init__(repository, SignalSource.ENVIRONMENTAL)


class MobilitySignalConnector(FixtureSignalConnector):
    def __init__(self, repository: DemoRepository) -> None:
        super().__init__(repository, SignalSource.MOBILITY)


class WastewaterSignalConnector(FixtureSignalConnector):
    def __init__(self, repository: DemoRepository) -> None:
        super().__init__(repository, SignalSource.WASTEWATER)


class DataAcquisitionLayer:
    def __init__(self, connectors: list[DataConnector]) -> None:
        self.connectors = connectors

    @classmethod
    def demo(cls, repository: DemoRepository) -> "DataAcquisitionLayer":
        return cls(
            [
                HospitalSignalConnector(repository),
                SearchTrendConnector(repository),
                SocialSignalConnector(repository),
                WeatherSignalConnector(repository),
                EnvironmentalSignalConnector(repository),
                MobilitySignalConnector(repository),
                WastewaterSignalConnector(repository),
            ]
        )

    def collect(self, district_id: str | None = None) -> list[SignalObservation]:
        observations: list[SignalObservation] = []
        for connector in self.connectors:
            observations.extend(connector.collect(district_id))
        return sorted(observations, key=lambda signal: (signal.district_id, signal.source, signal.id))
