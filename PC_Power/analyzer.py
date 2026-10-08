from math import ceil

from data.models import AnalysisResult, PowerCalculationResult, UserInput


_PERIOD_LABELS = {"day": "일", "week": "주", "month": "월"}


def _derived_trend(power: PowerCalculationResult, user_input: UserInput, period: str) -> list[dict[str, object]]:
    """Distribute the calculated monthly usage evenly for a demo trend."""
    if period == "day":
        count = user_input.monthly_days
        values = [power.daily_kwh] * count
        labels = [f"{index}일" for index in range(1, count + 1)]
    elif period == "week":
        count = ceil(user_input.monthly_days / 7)
        values = [power.daily_kwh * min(7, user_input.monthly_days - index * 7) for index in range(count)]
        labels = [f"{index + 1}주" for index in range(count)]
    elif period == "month":
        values = [power.monthly_kwh]
        labels = ["현재 월"]
    else:
        raise ValueError(f"지원하지 않는 분석 단위: {period}")
    return [
        {"period": label, "kwh": value, "data_source": power.data_source, "generation_rule": "균등 분배 추정"}
        for label, value in zip(labels, values)
    ]


def analyze(power: PowerCalculationResult, user_input: UserInput, period: str = "day", period_data=None, previous_data=None) -> AnalysisResult:
    """Build analysis data from measured input or an explicit derived estimate."""
    if period not in _PERIOD_LABELS:
        raise ValueError(f"지원하지 않는 분석 단위: {period}")
    equipment = [{"name": "PC", "power_w": user_input.pc_power_w, "share": user_input.pc_power_w / power.total_w * 100 if power.total_w else 0, "data_source": user_input.data_source}]
    for i in range(user_input.monitor_count):
        watts = user_input.monitor_power_w
        equipment.append({"name": f"모니터 {i + 1}", "power_w": watts, "share": watts / power.total_w * 100 if power.total_w else 0, "data_source": user_input.data_source})

    if period_data is not None:
        trend = list(period_data) or None
    else:
        trend = _derived_trend(power, user_input, period)
    trend_status = "valid" if trend else "insufficient_data"
    comparison = previous_data if previous_data is not None else {
        "status": "insufficient_data",
        "reason": "이전 기간 데이터가 없어 비교할 수 없습니다.",
        "data_source": "unavailable",
    }
    usage_pattern = {
        "start_time": user_input.start_time or "09:00 (예시)",
        "end_time": user_input.end_time or "17:00 (예시)",
        "time_source": "user_estimate" if user_input.start_time and user_input.end_time else "example",
        "time_rule": "선택 시간 미입력 시 하루 8시간을 09:00~17:00으로 표시하는 예시 규칙",
        "purpose": user_input.purpose or "미입력",
        "daily_hours": user_input.daily_hours,
        "monthly_kwh": power.monthly_kwh,
        "data_source": user_input.data_source,
    }
    return AnalysisResult(
        period, trend, equipment, usage_pattern, comparison, trend_status,
        None if trend else "기간별 데이터가 없어 추이를 만들 수 없습니다.",
        user_input.data_source,
    )
