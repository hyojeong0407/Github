from data.models import TariffConfig

# Existing example basis used by the original scenario tests: 10 currency units per kWh.
# This is illustrative only and is not an official Korean residential tariff.
DEFAULT_TARIFF = TariffConfig(
    tariff_id="example-flat",
    version="example-1",
    effective_from="",
    effective_to=None,
    tariff_type="example",
    usage_ranges=[],
    basic_charge=0.0,
    energy_charge=10.0,
    other_charges=0.0,
    source="기존 테스트 example_tariff 기준(10원/kWh), 공식 요금 출처 아님",
    verified_date=None,
    status="example",
)
