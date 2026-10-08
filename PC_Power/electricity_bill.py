from data.models import BillResult, TariffConfig


def calculate_bill(monthly_kwh: float, tariff: TariffConfig) -> BillResult:
    """Calculate only when the supplied tariff is explicitly usable."""
    if tariff.status not in ("verified", "example"):
        return BillResult(
            monthly_kwh, None, tariff, tariff.status,
            f"실제 청구액 아님: 요금 기준 {tariff.status}",
        )
    amount = tariff.basic_charge + monthly_kwh * tariff.energy_charge + tariff.other_charges
    label = "예시 기준 예상 요금(실제 청구액 아님)" if tariff.status == "example" else "참고용 예상 요금"
    return BillResult(monthly_kwh, amount, tariff, tariff.status, label)
