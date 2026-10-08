import pytest
from analyzer import analyze
from data.config import DEFAULT_TARIFF
from data.models import TariffConfig
from electricity_bill import calculate_bill
from power_calculator import calculate_power
from recommendation import generate_recommendations
from simulation import simulate
from validation import validate_input, normalize_input


def valid(**overrides):
    data = {"pc_power_w": 300, "daily_hours": 8, "monthly_days": 20, "monitor_power_w": 30, "monitor_count": 2}
    data.update(overrides); return data

def test_tc001_normal_calculation():
    result = calculate_power(normalize_input(valid()))
    assert result.total_w == 360 and result.daily_kwh == pytest.approx(2.88) and result.monthly_kwh == pytest.approx(57.6)

def test_tc002_zero_invalid_and_no_result():
    errors = validate_input(valid(pc_power_w=0, daily_hours=0)); assert {e['error_code'] for e in errors} >= {'positive', 'hours_range'}

def test_tc003_negative_values():
    assert validate_input(valid(pc_power_w=-1, monitor_power_w=-1, monitor_count=-1, monthly_days=-1))

def test_tc004_string_type():
    assert any(e['error_code'] == 'numeric' for e in validate_input(valid(pc_power_w='300')))

def test_tc005_hours_over_24():
    assert any(e['error_code'] == 'hours_range' for e in validate_input(valid(daily_hours=25)))

def test_tc006_multiple_monitors():
    assert calculate_power(normalize_input(valid(monitor_count=3))).total_w == 390

def test_tc007_time_validation_and_optional():
    assert not validate_input(valid())
    assert any(e['error_code'] == 'time_order' for e in validate_input(valid(start_time='10:00', end_time='09:00')))

def test_tc008_saving():
    tariff = TariffConfig('t','1','','','flat',[],0,10,0,'test','2024','example')
    result = simulate(normalize_input(valid()), normalize_input(valid(daily_hours=4)), tariff)
    assert result.saved_kwh == pytest.approx(28.8) and result.saved_cost == pytest.approx(288)

def test_tc009_kpi_common_result():
    result = calculate_power(normalize_input(valid())); assert result.data_source == 'user_estimate' and result.total_w > 0

def test_tc010_derived_trend_has_input_based_data():
    current = normalize_input(valid(monthly_days=30))
    result = analyze(calculate_power(current), current, period='week')
    assert result.status == 'valid' and len(result.trend) == 5
    assert sum(item['kwh'] for item in result.trend) == pytest.approx(86.4)
    assert all(item['data_source'] == 'user_estimate' for item in result.trend)

def test_tc011_recommendation_evidence_no_amount():
    user = normalize_input(valid(daily_hours=9)); power = calculate_power(user); items = generate_recommendations(user, power, analyze(power, user))
    assert items and all(item.reason and '원' not in item.expected_effect for item in items)

def test_tc012_required_range_shape():
    errors = validate_input({}); assert errors and {'field','error_code','message','severity'} <= errors[0].keys()

def test_tc013_zero_bill_rate_unavailable():
    unavailable = TariffConfig('u', '0', '', None, 'residential', [], 0, 0, 0, '미검증', None, 'unavailable')
    result = simulate(normalize_input(valid()), normalize_input(valid(daily_hours=4)), unavailable)
    assert result.saving_rate is None

def test_tc014_tariff_unavailable():
    unavailable = TariffConfig('u', '0', '', None, 'residential', [], 0, 0, 0, '미검증', None, 'unavailable')
    bill = calculate_bill(10, unavailable)
    assert bill.amount is None and bill.tariff.status == 'unavailable' and '실제 청구액 아님' in bill.display_label


def test_default_example_tariff_calculates_reference_amount():
    bill = calculate_bill(81.6, DEFAULT_TARIFF)
    assert bill.amount == pytest.approx(816)
    assert bill.tariff.status == 'example'
    assert '예시' in bill.display_label and '실제 청구액 아님' in bill.display_label
