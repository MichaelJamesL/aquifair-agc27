from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from neraca.domain.enums import (
    CheckResult,
    CheckStatus,
    LeadOutcome,
    PipeTestStatus,
    ProvenanceLabel,
    QualityClass,
    RegionType,
    UseClass,
    ZoneClass,
)


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: ProvenanceLabel
    source_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class Number(BaseModel):
    """One number on screen, with its unit, label, and source links."""

    model_config = ConfigDict(frozen=True)

    value: int | float | None = None
    unit: str
    label: ProvenanceLabel
    source_ids: list[str] = Field(default_factory=list)
    note: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Number:
        if self.label is ProvenanceLabel.MISSING and self.value is not None:
            raise ValueError("a MISSING number cannot carry a value")
        if self.label is not ProvenanceLabel.MISSING and self.value is None:
            raise ValueError("a non-MISSING number must carry a value")
        return self

    @classmethod
    def missing(cls, unit: str, *, note: str | None = None) -> Number:
        return cls(value=None, unit=unit, label=ProvenanceLabel.MISSING, note=note)


class Range(BaseModel):
    """A number with a low/high range. Central is optional when only bounds exist."""

    model_config = ConfigDict(frozen=True)

    low: int | float | None = None
    central: int | float | None = None
    high: int | float | None = None
    unit: str
    label: ProvenanceLabel
    source_ids: list[str] = Field(default_factory=list)
    note: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Range:
        if self.label is ProvenanceLabel.MISSING:
            if any(v is not None for v in (self.low, self.central, self.high)):
                raise ValueError("a MISSING range cannot carry values")
            return self
        if self.low is None or self.high is None:
            raise ValueError("a non-MISSING range needs low and high")
        if self.low > self.high:
            raise ValueError("range low cannot exceed range high")
        return self

    @classmethod
    def missing(cls, unit: str, *, note: str | None = None) -> Range:
        return cls(unit=unit, label=ProvenanceLabel.MISSING, note=note)


class Source(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    publisher: str
    url: str | None = None
    label: ProvenanceLabel
    accessed: date | None = None
    note: str | None = None


class Region(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    type: RegionType
    wilayah: Literal["A", "B", "C"]
    source_ids: list[str] = Field(default_factory=list)


class DeclaredUse(BaseModel):
    model_config = ConfigDict(frozen=True)

    region_id: str
    year: int
    declared_m3: int | float | None
    npa_value_idr: int | float | None
    source_ids: list[str] = Field(default_factory=list)


class Estimate(BaseModel):
    model_config = ConfigDict(frozen=True)

    region_id: str
    year: int
    method: str
    low_m3: int | float
    central_m3: int | float | None = None
    high_m3: int | float
    label: ProvenanceLabel
    source_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class AccountTerms(BaseModel):
    model_config = ConfigDict(frozen=True)

    region_id: str
    year: int
    household_wells_low_m3: int | float
    household_wells_high_m3: int | float
    public_supply_low_m3: int | float
    public_supply_high_m3: int | float
    source_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class TaxBand(BaseModel):
    model_config = ConfigDict(frozen=True)

    low_npa_idr: int | float
    high_npa_idr: int | float
    low_tax_idr: int | float
    high_tax_idr: int | float
    source_ids: list[str] = Field(default_factory=list)


class CheckRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    status: CheckStatus
    result: CheckResult


class Account(BaseModel):
    model_config = ConfigDict(frozen=True)

    region: Region
    year: int
    declared: Number
    estimated_validated: Range
    estimated_demand: Range | None
    gap: Range
    tax_per_m3: Range
    declared_tax_base: Range
    npa_value_total: Number
    checks: list[CheckRef] = Field(default_factory=list)


class ScenarioResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    region: Region
    undeclared_m3: float
    npa: Range
    tax: Range
    tax_rate: float
    note: str


class AccountYear(BaseModel):
    model_config = ConfigDict(frozen=True)

    year: int
    declared: Number
    npa_value_total: Number


class BillingCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    region: Region
    year: int
    check: CheckRef
    realised_tax: Number
    declared_volume: Number
    implied_tax_per_m3: Number
    expected_band: Range
    note: str


class Lead(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    district: str
    lon: float
    lat: float
    footprint_m2: int | float
    built_year: int
    use_class: UseClass
    zone: ZoneClass
    pdam_status: str
    sinking_mm_yr: float | None = None
    source_ids: list[str] = Field(default_factory=list)
    labels: dict[str, ProvenanceLabel] = Field(default_factory=dict)


class LeadCollection(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["available", "unavailable"]
    reason: str | None = None
    items: list[Lead] = Field(default_factory=list)


class LeadSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    district: str
    leads: int
    by_use_class: dict[str, int] = Field(default_factory=dict)
    note: str | None = None


class LeadSummaryCollection(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["available", "unavailable"]
    reason: str | None = None
    items: list[LeadSummary] = Field(default_factory=list)


class Feedback(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    lead_id: str
    inspector: str
    outcome: LeadOutcome
    note: str | None = None
    visited_at: date
    created_at: datetime


class HitRate(BaseModel):
    model_config = ConfigDict(frozen=True)

    lead_class: str
    visits: int
    unregistered: int
    unregistered_rate: float | None
    interval_90_low: float | None
    interval_90_high: float | None
    confirmed_water_user: int
    confirmed_rate: float | None
    note: str | None = None


class SubsidencePeriod(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    fast_mm_yr: float
    land_mm_yr: float
    source_ids: list[str] = Field(default_factory=list)


class PipeCell(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    lon: float
    lat: float
    demand_m3_yr: float
    damage_mm_yr: float
    supply_m3_yr: float
    source_ids: list[str] = Field(default_factory=list)


class PipePriority(BaseModel):
    model_config = ConfigDict(frozen=True)

    cell: PipeCell
    score: float
    demand_share: float
    damage_share: float
    supply_share: float


class PipePriorityCollection(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["available", "unavailable"]
    reason: str | None = None
    weights: dict[str, float]
    items: list[PipePriority] = Field(default_factory=list)


class SpamTest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    status: PipeTestStatus
    design_capacity_lps: float | None = None
    uptake_lps_2024_01: float | None = None
    uptake_m3_yr_2024: float | None = None
    connections_target: int | None = None
    connections_actual_2024_09: int | None = None
    commercial_operation_date: date | None = None
    districts: list[str] = Field(default_factory=list)
    delta_mm_yr: float | None = None
    shift_null_p05: float | None = None
    placebo_year_clean: bool | None = None
    placebo_area_clean: bool | None = None
    positive_control_passed: bool | None = None
    outcome_code: str | None = None
    outcome_wording: str
    source_ids: list[str] = Field(default_factory=list)


class ValidationCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str
    module: Literal["A", "B", "C"]
    pass_mark: str
    status: CheckStatus
    result: CheckResult
    source_ids: list[str] = Field(default_factory=list)


class NpaContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    wilayah: Literal["A", "B", "C"]
    quality: QualityClass
    alternative: bool
    group: int
    tier_index: int


class NpaValue(BaseModel):
    model_config = ConfigDict(frozen=True)

    npa_idr: int
    tax_idr: int
    hab_idr: int
    bat: float
    tax_rate: float
    source_ids: list[str] = Field(default_factory=list)


class TariffRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    group: int
    group_name: str
    tier_key: str
    tier_label: str
    npa_idr: Number
    tax_idr: Number


class TariffTable(BaseModel):
    model_config = ConfigDict(frozen=True)

    regulation: str
    in_force: str
    tax_rate: float
    wilayah: str
    quality: QualityClass
    alternative: bool
    rows: list[TariffRow]
    source_ids: list[str] = Field(default_factory=list)


class RegionGeometry(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str
    coordinates: Any


class RegionFeature(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["Feature"] = "Feature"
    properties: dict[str, Any]
    geometry: RegionGeometry | None = None


class RegionFeatureCollection(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[RegionFeature]
