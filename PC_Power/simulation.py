from data.models import SimulationResult, UserInput
from power_calculator import calculate_power
from electricity_bill import calculate_bill


USAGE_PRESETS = ("1시간 줄이기", "2시간 줄이기", "절반으로 줄이기")


def preset_hours(daily_hours: float, preset: str) -> float:
    """Calculate a non-negative changed usage time from the existing input."""
    if preset == "1시간 줄이기":
        return max(0.0, daily_hours - 1.0)
    if preset == "2시간 줄이기":
        return max(0.0, daily_hours - 2.0)
    if preset == "절반으로 줄이기":
        return max(0.0, daily_hours / 2.0)
    raise ValueError(f"지원하지 않는 사용시간 프리셋: {preset}")


def simulate(old_input: UserInput, new_input: UserInput, tariff) -> SimulationResult:
    old = calculate_power(old_input)
    new = calculate_power(new_input)
    old_bill = calculate_bill(old.monthly_kwh, tariff)
    new_bill = calculate_bill(new.monthly_kwh, tariff)
    saved_kwh = old.monthly_kwh - new.monthly_kwh
    saved_cost = (
        old_bill.amount - new_bill.amount
        if old_bill.amount is not None and new_bill.amount is not None
        else None
    )
    rate = saved_cost / old_bill.amount * 100 if saved_cost is not None and old_bill.amount else None
    if saved_cost is None:
        status = "unavailable"
        reason = "요금 기준이 없어 절감액과 절감률을 계산할 수 없습니다."
    elif saved_kwh > 0:
        status = "saved"
        reason = "기존 조건보다 사용량이 감소했습니다." if rate is None else None
    elif saved_kwh < 0:
        status = "increased"
        reason = "변경 조건에서 사용량이 증가했습니다."
    else:
        status = "same"
        reason = "기존 조건과 변경 조건이 같습니다."
    return SimulationResult(
        old.monthly_kwh, new.monthly_kwh, old_bill.amount, new_bill.amount,
        saved_kwh, saved_cost, rate, status, reason,
    )
