from dataclasses import dataclass, field
from typing import Any, Optional

DATA_SOURCES = ("measured", "manufacturer_estimate", "user_estimate", "example")
SOURCE_PRIORITY = {source: index for index, source in enumerate(DATA_SOURCES)}


def preferred_source(*sources: str) -> str:
    """Return the highest-priority available source without fabricating measurement data."""
    available = [source for source in sources if source in SOURCE_PRIORITY]
    return min(available, key=SOURCE_PRIORITY.__getitem__) if available else "unavailable"

@dataclass
class Device:
    id: str
    name: str
    power_w: float
    count: int = 1
    kind: str = "other"
    data_source: str = "user_estimate"

@dataclass
class UserInput:
    pc_power_w: float
    daily_hours: float
    monthly_days: int
    monitor_power_w: float = 0.0
    monitor_count: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    purpose: Optional[str] = None
    other_devices: list[Device] = field(default_factory=list)
    data_source: str = "user_estimate"
    measured: bool = False
    schema_version: str = "1.1"

@dataclass
class PowerCalculationResult:
    total_w: float
    daily_kwh: float
    monthly_kwh: float
    status: str = "valid"
    data_source: str = "user_estimate"
    formula_version: str = "1.0"

    @property
    def source(self) -> str:
        return self.data_source

@dataclass
class TariffConfig:
    tariff_id: str
    version: str
    effective_from: str
    effective_to: Optional[str]
    tariff_type: str
    usage_ranges: list[dict[str, Any]]
    basic_charge: float
    energy_charge: float
    other_charges: float
    source: str
    verified_date: Optional[str]
    status: str = "unavailable"

@dataclass
class BillResult:
    monthly_kwh: float
    amount: Optional[float]
    tariff: TariffConfig
    status: str
    display_label: str
    data_source: str = "example"

@dataclass
class AnalysisResult:
    period: str
    trend: Optional[list[dict[str, Any]]]
    equipment: list[dict[str, Any]]
    usage_pattern: dict[str, Any]
    previous_comparison: dict[str, Any]
    status: str
    reason: Optional[str]
    data_source: str
    analysis_version: str = "1.0"

@dataclass
class SimulationResult:
    old_monthly_kwh: float
    new_monthly_kwh: float
    old_bill: Optional[float]
    new_bill: Optional[float]
    saved_kwh: float
    saved_cost: Optional[float]
    saving_rate: Optional[float]
    status: str
    reason: Optional[str] = None
    data_source: str = "user_estimate"

@dataclass
class Recommendation:
    title: str
    description: str
    reason: str
    expected_effect: str
    data_source: str
    priority: int = 1
    rank: int = 1
    status: str = "rule_based"
