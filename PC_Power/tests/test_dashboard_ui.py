import pytest


streamlit_testing = pytest.importorskip("streamlit.testing")
from streamlit.testing.v1 import AppTest


def _markdown_text(app):
    return "\n".join(str(item.value) for item in app.markdown)


def test_dashboard_uses_cards_for_pattern_simulation_and_tariff_details():
    app = AppTest.from_file("app.py").run(timeout=30)
    assert not app.exception
    rendered = _markdown_text(app)

    assert "평균 사용시간" in rendered
    assert "월간 예상 사용량" in rendered
    assert "주요 사용 시간대" in rendered
    assert "사용자 입력 기반 추정" in rendered
    assert "기존 사용시간" in rendered
    assert "변경 사용시간" in rendered
    assert "절감 전력량" in rendered
    assert "절감 금액" in rendered
    assert "절감률" in rendered
    assert "요금 기준 상태" in rendered
    assert "적용 기간" in rendered
    assert "계산 기준 요약" in rendered
    assert "데이터 출처" in rendered
    assert "실제 청구액 아님" in rendered
    assert "dashboard-card" in rendered
