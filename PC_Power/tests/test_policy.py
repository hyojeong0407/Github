import pytest

from data.models import TariffConfig, preferred_source
from electricity_bill import calculate_bill
from power_calculator import calculate_power
from validation import normalize_input


def user(**overrides):
    values = {
        "pc_power_w": 300,
        "daily_hours": 8,
        "monthly_days": 30,
        "monitor_power_w": 40,
        "monitor_count": 1,
    }
    values.update(overrides)
    return normalize_input(values)


def test_source_precedence_keeps_highest_quality_available_source():
    assert preferred_source("example", "user_estimate") == "user_estimate"
    assert preferred_source("user_estimate", "manufacturer_estimate") == "manufacturer_estimate"
    assert preferred_source("example", "measured", "manufacturer_estimate") == "measured"
    assert preferred_source() == "unavailable"


def test_source_and_measurement_status_are_preserved():
    measured = user(data_source="measured")
    result = calculate_power(measured)
    assert measured.measured is True
    assert result.data_source == "measured"
    assert result.source == "measured"


def test_raw_calculation_is_not_rounded_before_display():
    result = calculate_power(user(pc_power_w=333.33, monitor_power_w=17.77, daily_hours=3.7, monthly_days=31))
    assert result.total_w == pytest.approx(351.1)
    assert result.monthly_kwh == pytest.approx(40.27117)


def test_example_and_unavailable_tariff_status_are_explicit():
    example = TariffConfig("example", "v1", "2024-01-01", "2024-12-31", "flat", [], 0, 10, 0, "비공식 예시", None, "example")
    unavailable = TariffConfig("none", "", "", None, "residential", [], 0, 0, 0, "미확인", None, "unavailable")
    assert calculate_bill(12.345, example).amount == pytest.approx(123.45)
    assert calculate_bill(12.345, unavailable).amount is None
