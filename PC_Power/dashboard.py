from typing import Any

from data.models import AnalysisResult, BillResult, PowerCalculationResult, Recommendation, SimulationResult
from consumption_stage import classify_consumption


def render_dashboard(
    st: Any,
    power: PowerCalculationResult,
    bill: BillResult,
    analysis: AnalysisResult,
    simulation: SimulationResult,
    recommendations: list[Recommendation],
    user_input: Any,
    changed_input: Any,
) -> None:
    """Render the Streamlit presentation using already-calculated domain results."""
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: #ffffff; }
        [data-testid="stSidebar"] { background: #f1f3f5; }
        [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
        .dashboard-caption { color: #747b83; font-size: 0.9rem; margin-top: -0.6rem; }
        .analysis-banner { background: #e8f1ff; border-radius: 0.35rem; color: #174a8b;
            padding: 0.75rem 1rem; margin: 1.2rem 0 1rem; }
        .tariff-banner { background: #fff7d6; border-radius: 0.35rem; color: #6f5b00;
            padding: 0.7rem 1rem; margin: 1rem 0; }
        .dashboard-card { background: #ffffff; border: 1px solid #dfe3e8; border-radius: 0.6rem;
            padding: 1rem; min-height: 7.4rem; box-shadow: 0 1px 2px rgba(23, 42, 70, 0.06); }
        .dashboard-card-label { color: #5f6873; font-size: 0.85rem; margin-bottom: 0.35rem; }
        .dashboard-card-value { color: #172a46; font-size: 1.35rem; font-weight: 700; margin-bottom: 0.35rem; }
        .dashboard-card-detail { color: #747b83; font-size: 0.78rem; line-height: 1.45; }
        .dashboard-card.status-saved { border-top: 4px solid #218739; }
        .dashboard-card.status-increased { border-top: 4px solid #c2410c; }
        .dashboard-card.status-same { border-top: 4px solid #64748b; }
        .dashboard-card.status-unavailable { border-top: 4px solid #b45309; }
        div[data-testid="stMetric"] { padding: 0.25rem 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("# ⚡ PC 전력 사용량 및 전기요금 분석 대시보드")
    st.markdown(
        "<div class='dashboard-caption'>사용자 입력 기반 예상값 · 실제 측정값이 아닌 추정 분석</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='analysis-banner'>현재 분석 기간: 월간 사용일수 {user_input.monthly_days}일 · "
        f"계산 범위: PC 사용분 기준 · 데이터 기준: {_source_label(power.data_source)}</div>",
        unsafe_allow_html=True,
    )

    st.caption("월간 예상 전력 사용량 · 월간 예상 전기요금 · 하루 평균 사용시간 · 예상 절감 가능 금액")
    bill_value = bill.display_label if bill.amount is None else f"{bill.amount:,.0f} 원"
    saving_value = _saving_label(simulation)
    kpis = (
        ("월간 예상 전력 사용량", f"{power.monthly_kwh:.2f} kWh"),
        ("월간 예상 전기요금", bill_value),
        ("하루 평균 사용시간", f"{user_input.daily_hours:.1f} 시간"),
        ("예상 절감 가능 금액", saving_value),
    )
    for col, (label, value) in zip(st.columns(4), kpis):
        col.metric(label, value)

    st.markdown(
        f"<div class='tariff-banner'>{bill.display_label} · 상태: {bill.tariff.status} · {bill.tariff.source}</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"내부 원시값으로 계산 후 kWh 0.01, W 필요 시 0.01, 시간 0.1, 금액 1원 단위로 표시합니다."
    )

    st.subheader("전력 사용량 추이")
    if analysis.trend:
        st.line_chart(analysis.trend)
        st.caption(f"분석 단위: {_period_label(analysis.period)} · 데이터 출처: {analysis.data_source} · 생성 규칙: 균등 분배 추정")
    else:
        st.info(analysis.reason or "기간별 데이터가 없어 추이를 표시할 수 없습니다.")

    st.subheader("장비별 소비전력")
    st.bar_chart({item["name"]: item["power_w"] for item in analysis.equipment})
    st.subheader("사용 패턴")
    pattern = analysis.usage_pattern
    pattern_cards = [
        ("평균 사용시간", f"{pattern['daily_hours']:.1f} 시간", "하루 기준 · user_estimate", ""),
        ("월간 예상 사용량", f"{pattern['monthly_kwh']:.2f} kWh", "전력 계산 결과", ""),
        ("주요 사용 시간대", f"{pattern['start_time']} ~ {pattern['end_time']}", pattern['time_rule'], ""),
        ("데이터 기준 / 상태", _source_label(pattern['data_source']), f"시간대 출처: {_source_label(pattern['time_source'])}", ""),
        ("이전 기간 비교", analysis.previous_comparison.get("change", "데이터 부족"), analysis.previous_comparison.get("reason", "이전 기간 데이터가 있습니다."), ""),
    ]
    _render_cards(st, pattern_cards)
    st.subheader("새싹형 소비 단계")
    stage = classify_consumption(power.monthly_kwh)
    st.markdown(f"### {stage.icon} {stage.name}")
    st.write(stage.meaning)
    st.write(f"월간 예상 사용량: **{power.monthly_kwh:.2f} kWh**")
    st.caption(f"다음 단계 안내: {stage.next_guidance}")

    st.subheader("절감 시뮬레이션")
    simulation_status = _simulation_status(simulation.status)
    simulation_cards = [
        ("기존 사용시간", f"{user_input.daily_hours:.1f} 시간", "현재 입력", ""),
        ("기존 월간 전력량", f"{simulation.old_monthly_kwh:.2f} kWh", "기존 조건", ""),
        ("기존 예상 요금", _amount_label(simulation.old_bill), "기존 조건 · 예시/추정", ""),
        ("변경 사용시간", f"{changed_input.daily_hours:.1f} 시간", "시뮬레이션 입력", ""),
        ("변경 월간 전력량", f"{simulation.new_monthly_kwh:.2f} kWh", "변경 조건", ""),
        ("변경 예상 요금", _amount_label(simulation.new_bill), "변경 조건 · 예시/추정", ""),
        (f"{simulation_status} 전력량", f"{abs(simulation.saved_kwh):.2f} kWh", "절감은 양수, 증가는 증가량으로 표시", simulation.status),
        (f"{simulation_status} 금액", _amount_label(abs(simulation.saved_cost) if simulation.saved_cost is not None else None), "요금 기준에 따른 비교", simulation.status),
        ("절감률", "계산 불가" if simulation.saving_rate is None else f"{simulation.saving_rate:.1f}%", simulation.reason or simulation_status, "unavailable" if simulation.saving_rate is None else simulation.status),
    ]
    _render_cards(st, simulation_cards)
    st.subheader("절전 추천")
    for item in recommendations:
        st.info(f"**{item.rank}순위 · {item.title}**: {item.description}\n\n우선순위: {item.priority} · 근거: {item.reason}\n효과: {item.expected_effect}")
    st.subheader("계산 기준 및 출처")
    tariff = bill.tariff
    effective_period = tariff.effective_from or "미지정"
    if tariff.effective_to:
        effective_period += f" ~ {tariff.effective_to}"
    criteria_cards = [
        ("요금 기준 상태", _tariff_status_label(tariff.status), f"버전: {tariff.version}", ""),
        ("적용 기간", effective_period, f"검증일: {tariff.verified_date or '미지정'}", ""),
        ("계산 기준 요약", "PC 사용으로 증가한 전력", f"PC + 모니터 · 월간 사용량 = 일일 사용량 × {user_input.monthly_days}일", ""),
        ("데이터 출처", _source_label(power.data_source), f"요금 출처: {tariff.source}", ""),
        ("금액 안내", "실제 청구액 아님", bill.display_label, "unavailable" if tariff.status == "unavailable" else ""),
    ]
    _render_cards(st, criteria_cards)


def _render_cards(st: Any, cards: list[tuple[str, str, str, str]]) -> None:
    """Render compact, accessible cards without duplicating domain calculations."""
    columns = st.columns(min(4, len(cards)))
    for index, (label, value, detail, status) in enumerate(cards):
        card_class = f"dashboard-card {status}" if status else "dashboard-card"
        content = (
            f"<div class='{card_class}'>"
            f"<div class='dashboard-card-label'>{label}</div>"
            f"<div class='dashboard-card-value'>{value}</div>"
            f"<div class='dashboard-card-detail'>{detail}</div></div>"
        )
        columns[index % len(columns)].markdown(content, unsafe_allow_html=True)


def _source_label(source: str) -> str:
    return {
        "user_estimate": "사용자 입력 기반 추정",
        "measured": "실측값",
        "manufacturer_estimate": "제조사/사용자 제공 추정",
        "example": "예시값",
        "unavailable": "확인 불가",
    }.get(source, source)


def _tariff_status_label(status: str) -> str:
    return {"verified": "검증됨", "example": "예시 기준", "unverified": "미검증", "unavailable": "계산 불가"}.get(status, status)


def _simulation_status(status: str) -> str:
    return {"saved": "절감", "increased": "증가", "same": "동일", "unavailable": "계산 불가"}.get(status, status)


def _period_label(period: str) -> str:
    return {"day": "일", "week": "주", "month": "월"}[period]


def _amount_label(amount: float | None) -> str:
    return "계산 불가" if amount is None else f"{amount:,.0f} 원"


def _saving_label(simulation: SimulationResult) -> str:
    return _amount_label(simulation.saved_cost)
