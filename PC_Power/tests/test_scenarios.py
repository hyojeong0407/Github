from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from analyzer import analyze
from data.config import DEFAULT_TARIFF
from data.models import TariffConfig
from electricity_bill import calculate_bill
from power_calculator import calculate_power
from recommendation import generate_recommendations
from simulation import simulate
from validation import normalize_input


ROOT = Path(__file__).resolve().parents[1]


def user(**overrides):
    values = {
        "pc_power_w": 300,
        "daily_hours": 8,
        "monthly_days": 20,
        "monitor_power_w": 30,
        "monitor_count": 1,
        "data_source": "user_estimate",
    }
    values.update(overrides)
    return normalize_input(values)


def example_tariff():
    return TariffConfig("test", "1", "", "", "flat", [], 0, 10, 0, "test", "2024", "example")


def test_us001_input_to_kpi_and_reference_bill():
    current = user(pc_power_w=300, monitor_power_w=30, monitor_count=2, daily_hours=8, monthly_days=20)
    power = calculate_power(current)
    bill = calculate_bill(power.monthly_kwh, example_tariff())

    assert power.total_w == pytest.approx(360)
    assert power.daily_kwh == pytest.approx(2.88)
    assert power.monthly_kwh == pytest.approx(57.6)
    assert bill.amount == pytest.approx(576)
    assert power.data_source == "user_estimate"


def test_us002_actual_monitor_count_reaches_equipment_analysis():
    current = user(monitor_power_w=40, monitor_count=2)
    power = calculate_power(current)
    analysis = analyze(power, current)

    assert [item["name"] for item in analysis.equipment] == ["PC", "모니터 1", "모니터 2"]
    assert sum(item["power_w"] for item in analysis.equipment) == pytest.approx(power.total_w)
    assert analysis.equipment[2]["power_w"] == 40


def test_us003_period_selection_and_insufficient_data_are_explicit():
    current = user()
    power = calculate_power(current)
    measured = [{"period": "2024-01-01", "kwh": 2.64}]

    for period in ("day", "week", "month"):
        result = analyze(power, current, period=period, period_data=measured)
        assert result.period == period
        assert result.trend == measured
        assert result.status == "valid"

    derived = analyze(power, current, period="month")
    assert derived.status == "valid"
    assert derived.trend == [{"period": "현재 월", "kwh": power.monthly_kwh, "data_source": "user_estimate", "generation_rule": "균등 분배 추정"}]
    assert derived.usage_pattern["monthly_kwh"] == power.monthly_kwh
    assert derived.usage_pattern["time_source"] == "example"


def test_us004_changed_usage_reports_savings_and_increase():
    old = user(daily_hours=8)
    reduced = user(daily_hours=4)
    increased = user(daily_hours=10)

    saved = simulate(old, reduced, example_tariff())
    more = simulate(old, increased, example_tariff())

    assert saved.saved_kwh == pytest.approx(26.4)
    assert saved.saved_cost == pytest.approx(264)
    assert saved.saving_rate == pytest.approx(50)
    assert saved.status == "saved"
    assert more.saved_kwh < 0
    assert more.status == "increased"
    assert more.reason


def test_us005_recommendations_explain_input_basis_without_uncomputed_amount():
    current = user(daily_hours=9, monitor_count=2)
    power = calculate_power(current)
    recommendations = generate_recommendations(current, power, analyze(power, current))

    assert len(recommendations) == 2
    assert all(item.reason and item.expected_effect for item in recommendations)
    assert all("원" not in item.expected_effect for item in recommendations)


def test_dashboard_apptest_renders_kpi_and_data_states():
    app = AppTest.from_file(str(ROOT / "app.py")).run()

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("월간 예상 전력 사용량", "81.60 kWh"),
        ("월간 예상 전기요금", "816 원"),
        ("하루 평균 사용시간", "8.0 시간"),
        ("예상 절감 가능 금액", "408 원"),
    ]
    assert any("예시 기준 예상 요금" in item.value for item in app.markdown)
    assert any("균등 분배 추정" in item.value for item in app.caption)
    assert any("현재 분석 기간: 월간 사용일수 30일" in item.value for item in app.markdown)
    assert any("근거:" in item.value for item in app.info)


def test_dashboard_apptest_period_selection_changes_analysis():
    app = AppTest.from_file(str(ROOT / "app.py")).run()
    assert not app.exception
    assert app.selectbox[0].value == "day"
    app.selectbox[0].set_value("month")
    app.run()
    assert not app.exception
    assert any("분석 단위: 월" in item.value for item in app.caption)
    assert app.metric[0].value == "81.60 kWh"


def test_dashboard_apptest_accepts_actual_monitor_and_pattern_inputs():
    app = AppTest.from_file(str(ROOT / "app.py")).run()
    app.number_input[0].set_value(300.0)
    app.number_input[1].set_value(6.0)
    app.number_input[2].set_value(22)
    app.number_input[3].set_value(40.0)
    app.number_input[4].set_value(2)
    app.text_input[0].set_value("09:00")
    app.text_input[1].set_value("18:00")
    app.text_input[2].set_value("업무")
    app.run()

    assert not app.exception
    assert app.metric[0].value == "50.16 kWh"
    assert app.metric[2].value == "6.0 시간"
    assert any("모니터 2대" in item.value for item in app.info)
