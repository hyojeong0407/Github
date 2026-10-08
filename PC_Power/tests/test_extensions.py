import pytest
from streamlit.testing.v1 import AppTest

from analyzer import analyze
from consumption_stage import classify_consumption
from data.config import DEFAULT_TARIFF
from power_calculator import calculate_power
from recommendation import generate_recommendations
from simulation import USAGE_PRESETS, preset_hours
from validation import normalize_input


def user(**overrides):
    values = {"pc_power_w": 300, "daily_hours": 8, "monthly_days": 30, "monitor_power_w": 40, "monitor_count": 1}
    values.update(overrides)
    return normalize_input(values)


def test_usage_presets_use_existing_hours_and_never_go_negative():
    assert preset_hours(8, "1시간 줄이기") == 7
    assert preset_hours(8, "2시간 줄이기") == 6
    assert preset_hours(8, "절반으로 줄이기") == 4
    assert preset_hours(1, "2시간 줄이기") == 0
    assert set(USAGE_PRESETS) == {"1시간 줄이기", "2시간 줄이기", "절반으로 줄이기"}


def test_consumption_stage_boundaries_and_default_usage():
    assert classify_consumption(0).name == "씨앗"
    assert classify_consumption(50).name == "씨앗"
    assert classify_consumption(50.01).name == "새싹"
    assert classify_consumption(100).name == "새싹"
    assert classify_consumption(100.01).name == "잎새"
    assert classify_consumption(200.01).name == "나무"
    assert classify_consumption(300.01).name == "큰 나무"
    assert classify_consumption(81.60).name == "새싹"


def test_recommendations_are_ranked_without_losing_evidence():
    current = user(daily_hours=9, monitor_count=2)
    power = calculate_power(current)
    items = generate_recommendations(current, power, analyze(power, current))
    assert [item.rank for item in items] == [1, 2]
    assert [item.priority for item in items] == [1, 2]
    assert all(item.reason and item.data_source == "user_estimate" for item in items)
    assert all("원" not in item.expected_effect for item in items)


def test_changed_input_recalculates_existing_power_path():
    current = user(daily_hours=8)
    changed = user(daily_hours=preset_hours(current.daily_hours, "절반으로 줄이기"))
    assert calculate_power(changed).monthly_kwh == pytest.approx(calculate_power(current).monthly_kwh / 2)


def test_dashboard_apptest_shows_extension_ui():
    app = AppTest.from_file("app.py").run(timeout=10)
    assert not app.exception
    assert any("새싹형 소비 단계" in item.value for item in app.subheader)
    assert any("🌱 새싹" in item.value for item in app.markdown)
    assert any("1순위" in item.value for item in app.info)
    app.radio[0].set_value("2시간 줄이기")
    app.run(timeout=10)
    assert not app.exception
    assert any("2시간 줄이기: 6.00시간" in item.value for item in app.caption)
