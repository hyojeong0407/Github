from dataclasses import replace

import streamlit as st

from analyzer import analyze
from dashboard import render_dashboard
from data.config import DEFAULT_TARIFF
from electricity_bill import calculate_bill
from power_calculator import calculate_power
from recommendation import generate_recommendations
from simulation import USAGE_PRESETS, preset_hours, simulate
from validation import normalize_input, validate_input


st.set_page_config(page_title="PC Power Dashboard", page_icon="⚡", layout="wide")

with st.sidebar:
    st.markdown("## 입력 패널")
    st.caption("PC와 모니터 사용 정보를 입력하세요.")
    raw = {
        "pc_power_w": st.number_input("PC 소비전력 (W)", min_value=0.0, value=300.0, step=10.0),
        "daily_hours": st.number_input("하루 평균 사용시간 (시간)", min_value=0.0, max_value=24.0, value=8.0, step=0.5),
        "monthly_days": st.number_input("월간 사용일수 (일)", min_value=1, max_value=31, value=30, step=1),
        "monitor_power_w": st.number_input("모니터 대당 소비전력 (W)", min_value=0.0, value=40.0, step=5.0),
        "monitor_count": st.number_input("모니터 개수 (대)", min_value=0, value=1, step=1),
    }
    st.divider()
    st.markdown("### 선택 입력")
    raw["start_time"] = st.text_input("시작 시간 (HH:MM)")
    raw["end_time"] = st.text_input("종료 시간 (HH:MM)")
    raw["purpose"] = st.text_input("PC 사용 목적", placeholder="예: 업무, 학습, 게임")
    simulation_preset = st.radio(
        "빠른 사용시간 선택",
        ["직접 입력", *USAGE_PRESETS],
        horizontal=True,
        help="현재 하루 사용시간을 기준으로 변경 시간을 계산합니다.",
    )
    simulation_hours = st.number_input(
        "시뮬레이션 변경 사용시간 (시간)", min_value=0.0, max_value=24.0,
        value=4.0, step=0.5,
        disabled=simulation_preset != "직접 입력",
    )
    if simulation_preset != "직접 입력":
        simulation_hours = preset_hours(float(raw["daily_hours"]), simulation_preset)
        st.caption(f"{simulation_preset}: {simulation_hours:.2f}시간")

errors = validate_input(raw)
if errors:
    for error in errors:
        st.error(f"{error['field']}: {error['message']}")
else:
    user_input = normalize_input(raw)
    power = calculate_power(user_input)
    bill = calculate_bill(power.monthly_kwh, DEFAULT_TARIFF)
    selected_period = st.selectbox(
        "분석 단위", ["day", "week", "month"],
        format_func=lambda value: {"day": "일", "week": "주", "month": "월"}[value],
    )
    analysis = analyze(power, user_input, period=selected_period)
    changed_input = replace(user_input, daily_hours=float(simulation_hours))
    simulation = simulate(user_input, changed_input, DEFAULT_TARIFF)
    recommendations = generate_recommendations(user_input, power, analysis)
    render_dashboard(st, power, bill, analysis, simulation, recommendations, user_input, changed_input)
