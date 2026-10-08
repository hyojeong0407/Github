from dataclasses import asdict
from datetime import datetime
from typing import Any
from data.models import UserInput


def _error(field: str, code: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"field": field, "error_code": code, "message": message, "severity": severity}


def validate_input(raw: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    required = ("pc_power_w", "daily_hours", "monthly_days", "monitor_power_w", "monitor_count")
    for name in required:
        if name not in raw or raw[name] is None or raw[name] == "":
            errors.append(_error(name, "required", "필수 입력입니다."))
    numeric = ("pc_power_w", "daily_hours", "monitor_power_w")
    values: dict[str, float] = {}
    for name in numeric:
        if name in raw and raw[name] not in (None, ""):
            value = raw[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(_error(name, "numeric", "숫자로 입력해야 합니다."))
            else:
                values[name] = float(value)
    integers = ("monthly_days", "monitor_count")
    for name in integers:
        if name in raw and raw[name] not in (None, ""):
            value = raw[name]
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(_error(name, "integer", "정수로 입력해야 합니다."))
    if "pc_power_w" in values and values["pc_power_w"] <= 0:
        errors.append(_error("pc_power_w", "positive", "0보다 커야 합니다."))
    if "daily_hours" in values and not 0 < values["daily_hours"] <= 24:
        errors.append(_error("daily_hours", "hours_range", "0 초과 24 이하이어야 합니다."))
    if isinstance(raw.get("monthly_days"), int) and not 1 <= raw["monthly_days"] <= 31:
        errors.append(_error("monthly_days", "days_range", "1~31 정수이어야 합니다."))
    if "monitor_power_w" in values and values["monitor_power_w"] < 0:
        errors.append(_error("monitor_power_w", "non_negative", "0 이상이어야 합니다."))
    if isinstance(raw.get("monitor_count"), int) and raw["monitor_count"] < 0:
        errors.append(_error("monitor_count", "non_negative", "0 이상이어야 합니다."))
    for name in ("start_time", "end_time"):
        value = raw.get(name)
        if value is not None and value != "":
            try: datetime.strptime(value, "%H:%M")
            except (TypeError, ValueError): errors.append(_error(name, "time_format", "HH:MM 형식이어야 합니다."))
    if not any(e["field"] in ("start_time", "end_time") for e in errors) and raw.get("start_time") and raw.get("end_time") and raw["start_time"] >= raw["end_time"]:
        errors.append(_error("end_time", "time_order", "종료 시간은 시작 시간보다 늦어야 합니다."))
    return errors


def normalize_input(raw: dict[str, Any]) -> UserInput:
    errors = validate_input(raw)
    if errors:
        raise ValueError(errors)
    data_source = raw.get("data_source", raw.get("power_source", "user_estimate"))
    if data_source not in ("measured", "manufacturer_estimate", "user_estimate", "example"):
        raise ValueError([_error("data_source", "source", "지원되는 데이터 출처가 아닙니다.")])
    return UserInput(pc_power_w=float(raw["pc_power_w"]), daily_hours=float(raw["daily_hours"]), monthly_days=raw["monthly_days"], monitor_power_w=float(raw.get("monitor_power_w", 0)), monitor_count=raw.get("monitor_count", 0), start_time=raw.get("start_time") or None, end_time=raw.get("end_time") or None, purpose=raw.get("purpose") or None, other_devices=raw.get("other_devices", []), data_source=data_source, measured=data_source == "measured")
