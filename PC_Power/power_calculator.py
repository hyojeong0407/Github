from data.models import PowerCalculationResult, UserInput


def calculate_power(user_input: UserInput) -> PowerCalculationResult:
    total_w = user_input.pc_power_w + user_input.monitor_power_w * user_input.monitor_count
    daily_kwh = total_w / 1000 * user_input.daily_hours
    return PowerCalculationResult(total_w, daily_kwh, daily_kwh * user_input.monthly_days, data_source=user_input.data_source)
