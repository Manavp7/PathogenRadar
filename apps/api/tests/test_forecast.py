from pathogenradar_api.data.demo_repository import DemoRepository
from pathogenradar_api.layers.pipeline import IntelligencePipeline


def test_forecast_returns_required_horizons() -> None:
    forecast = IntelligencePipeline(DemoRepository()).district_intelligence("kerala-ernakulam").forecast

    assert [point.horizon_days for point in forecast.points] == [7, 14, 21, 30]


def test_higher_mobility_weight_increases_downstream_probability() -> None:
    forecast = IntelligencePipeline(DemoRepository()).district_intelligence("kerala-ernakulam").forecast
    day_7 = forecast.points[0].district_probabilities

    assert day_7["kerala-thiruvananthapuram"] > day_7["maharashtra-mumbai"]
