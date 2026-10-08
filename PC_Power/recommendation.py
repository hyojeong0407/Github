from data.models import AnalysisResult, PowerCalculationResult, Recommendation, UserInput


def generate_recommendations(user_input: UserInput, power: PowerCalculationResult, analysis: AnalysisResult) -> list[Recommendation]:
    candidates = []
    if user_input.daily_hours >= 8:
        candidates.append(Recommendation(
            "사용 시간 줄이기",
            "사용하지 않는 시간에는 PC를 종료하거나 절전 모드로 전환하세요.",
            f"일일 사용 시간이 {user_input.daily_hours:g}시간으로 길게 입력되었습니다.",
            "사용 시간에 따라 소비전력이 감소할 수 있음(금액 산출 안 함)",
            "user_estimate",
            priority=1,
        ))
    if user_input.monitor_count > 1:
        candidates.append(Recommendation(
            "사용하지 않는 모니터 끄기",
            "사용하지 않는 모니터의 전원을 끄세요.",
            f"모니터 {user_input.monitor_count}대가 입력되었습니다.",
            "모니터 수에 따라 소비전력이 감소할 수 있음(금액 산출 안 함)",
            "user_estimate",
            priority=2,
        ))
    if not candidates:
        candidates.append(Recommendation(
            "절전 설정 확인",
            "운영체제의 절전 및 화면 끄기 시간을 확인하세요.",
            f"입력 총 전력은 {power.total_w:g}W입니다.",
            "사용 패턴에 따라 소비전력이 감소할 수 있음(금액 산출 안 함)",
            "user_estimate",
            priority=1,
        ))
    candidates.sort(key=lambda item: item.priority)
    return [Recommendation(
        item.title, item.description, item.reason, item.expected_effect,
        item.data_source, item.priority, rank, item.status,
    ) for rank, item in enumerate(candidates, start=1)]
