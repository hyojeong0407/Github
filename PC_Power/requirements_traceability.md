# Requirements Traceability

현재 구현은 PC와 모니터 사용으로 증가한 전력량만 계산한다. 출처 우선순위는 `measured` > `manufacturer_estimate` > `user_estimate` > `example`이며 현재 기본 입력은 `user_estimate`다. 기본 화면의 `data/config.py` 10원/kWh 설정은 공식 대한민국 요금이 아닌 `example` 상태이고 source/version/effective period/status를 표시하므로 금액은 PC 사용분 기준 예상 증가액이며 실제 청구액이 아니다. 공식 단가 검증과 실측 CSV 수집·영속 저장은 보류한다.

| ID 범위 | 구현 모듈 | 검증 | 상태 |
|---|---|---|---|
| FR-001~003 | `input.py`, `validation.py`, `app.py` | TC-002~005, TC-007, TC-012, AppTest | implemented |
| FR-004~006 | `power_calculator.py` | TC-001, TC-006, US-001 | implemented |
| FR-007 | `electricity_bill.py`, `data/config.py`, `dashboard.py` | TC-014, 기본 example 요금/AppTest | example 기준 계산 및 실제 청구액 아님 경고 구현; unavailable 주입 정책도 테스트 |
| FR-008 | `dashboard.py`, 표준 결과 모델 | AppTest KPI smoke | implemented |
| FR-009 | `analyzer.py`, `app.py`, `dashboard.py` | TC-010, AppTest 기간 변경 smoke, US-003 | implemented: 일·주·월 균등 분배 `user_estimate` 추이 및 selectbox 연결 |
| FR-010~011 | `analyzer.py`, `dashboard.py` | TC-006, TC-010, US-002, US-003 | implemented: 장비·평균시간·월간량·예시 시간대 표시; 이전 기간은 데이터 부족 상태 |
| FR-012~013 | `simulation.py`, `dashboard.py` | TC-008, TC-013, US-004 | implemented |
| FR-014 | `recommendation.py`, `dashboard.py` | TC-011, US-005 | 규칙 기반 fallback implemented |
| FR-015 | `dashboard.py`, `data/models.py` | AppTest, TC-014 | implemented |
| NFR-001~002 | 도메인 모듈 및 `data/config.py` | 구조 검토, TC-014 | implemented |
| NFR-003~004 | `app.py`, `dashboard.py`, `validation.py` | AppTest, TC-012 | implemented |
| NFR-005~006 | UI 독립 계산·분석 모듈 | TC-001~014 | implemented |
- [x] FR-016 확장 기능: 프리셋 3종·새싹형 소비 단계·추천 priority/rank를 구현했다. `tests/test_extensions.py`에서 계산·경계·근거 보존을 검증하고 AppTest에서 UI를 확인했다.

- **정책 회귀 테스트**: `tests/test_policy.py`에서 출처 우선순위, measured 상태 보존, 원시 계산값, example/unavailable tariff를 검증한다. UI smoke에서 PC 사용분 기준과 출처·요금 상태·반올림 단위를 표시한다.


사용자가 승인한 원본 Spec 범위 밖 확장이다. 기존 FR/NFR/US/TC ID는 변경하지 않았다.

- 프리셋: `simulation.preset_hours` → `app.py`의 빠른 선택 → 기존 `simulate` 경로
- 소비 단계: `CONSUMPTION_STAGES`와 `classify_consumption` → `dashboard.py` 표시
- 추천 우선순위: `Recommendation.priority/rank` → 근거 보존 및 순위 표시


- **US-001**: 입력 정규화 → 전력 계산 → 요금 모듈 → KPI. 기본·단위·요금 상태를 검증한다.
- **US-002**: 실제 입력된 PC와 모니터만 `analyzer.analyze` 장비 목록과 차트에 표시한다.
- **US-003**: `analyzer.analyze`가 일·주·월을 전력 계산 결과에서 균등 분배한 `user_estimate`로 생성하고, Streamlit selectbox 선택값을 실제 분석 호출에 전달한다. 실측 데이터와 이전 기간 저장소가 없으므로 이전 기간 비교는 데이터 부족 상태로 표시한다.
- **US-004**: 사이드바 변경 사용시간을 기존 입력에 적용해 동일한 계산 경로로 비교하며, 절감·증가·동일·요금 계산 불가 상태를 구분한다.
- **US-005**: 입력·계산 결과에 연결된 규칙 기반 추천과 근거를 표시하며 검증되지 않은 절감액을 생성하지 않는다.

## 검증 결과

- `python -m pytest`: 33 passed, 0 failed, 0 skipped
- `python -m compileall -q .`: passed
- Streamlit `AppTest`: 기본 입력(PC 300W, 8시간, 30일, 모니터 40W 1대)에서 81.60 kWh, 816원, 시뮬레이션 절감액 408원과 example/실제 청구액 아님 경고를 확인했다. 일·주·월 기간 선택, 추이 렌더링, 다중 모니터, 선택 시간·목적 입력, 네 KPI, 사용 패턴·추천 영역도 확인했다.
- `unavailable` TariffConfig 주입 시 금액·절감률이 계산 불가로 유지되는 회귀 테스트를 확인했다.
- 보류/범위 외: 대한민국 공식 요금 출처 검증, 실제 측정 데이터 수집·이전 기간 저장, 영속 저장, 기타 장비 계산 정책. 현재 예시 요금의 출처는 기존 테스트 설정이며 공식 출처로 표시하지 않는다.
