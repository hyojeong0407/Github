from dataclasses import dataclass


@dataclass(frozen=True)
class ConsumptionStage:
    icon: str
    name: str
    max_kwh: float | None
    meaning: str
    next_guidance: str


# Lower monthly usage receives a friendlier stage. The open final range is intentional.
CONSUMPTION_STAGES = (
    ConsumptionStage("🌰", "씨앗", 50.0, "아주 적은 전력으로 사용하는 단계입니다.", "새싹까지 월간 사용량을 50 kWh 이하로 유지해 보세요."),
    ConsumptionStage("🌱", "새싹", 100.0, "가볍고 균형 있게 사용하는 단계입니다.", "잎새 단계까지 월간 사용량을 100 kWh 이하로 유지해 보세요."),
    ConsumptionStage("🌿", "잎새", 200.0, "보통 수준의 전력을 사용하는 단계입니다.", "나무 단계까지 월간 사용량을 200 kWh 이하로 줄여 보세요."),
    ConsumptionStage("🌳", "나무", 300.0, "사용량이 비교적 큰 단계입니다.", "큰 나무 단계가 되기보다 월간 사용량을 300 kWh 이하로 줄여 보세요."),
    ConsumptionStage("🌲", "큰 나무", None, "나무가 커졌다는 뜻이 아니라 전력 사용량이 많은 단계입니다.", "월간 사용량을 300 kWh 이하로 줄여 나무 단계에 도전해 보세요."),
)


def classify_consumption(monthly_kwh: float) -> ConsumptionStage:
    """Return the first stage whose configured upper bound contains usage."""
    if monthly_kwh < 0:
        raise ValueError("월간 사용량은 음수일 수 없습니다.")
    for stage in CONSUMPTION_STAGES:
        if stage.max_kwh is None or monthly_kwh <= stage.max_kwh:
            return stage
    raise AssertionError("소비 단계 설정에 마지막 구간이 없습니다.")
