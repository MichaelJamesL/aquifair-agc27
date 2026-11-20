from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from neraca.domain.models import (
    AccountTerms,
    DeclaredUse,
    Estimate,
    FunnelStep,
    Lead,
    Region,
    Source,
    SpamTest,
    SubsidencePeriod,
    ValidationCheck,
)


class LeadFile(BaseModel):
    status: Literal["available", "unavailable"] = "unavailable"
    reason: str | None = None
    method: dict[str, Any] = Field(default_factory=dict)
    funnel: list[FunnelStep] = Field(default_factory=list)
    items: list[Lead] = Field(default_factory=list)


class PipeCellFileItem(BaseModel):
    id: str
    lon: float
    lat: float
    polygon: list[list[float]] = Field(default_factory=list)
    demand_m3_yr: float
    demand_low_m3_yr: float | None = None
    demand_high_m3_yr: float | None = None
    clay_m: float
    sinking_mm_yr: float | None = None
    supply_m3_yr: float
    land_share: float | None = None
    districts: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class PipeCellFile(BaseModel):
    status: Literal["available", "unavailable"] = "unavailable"
    reason: str | None = None
    grid: str | None = None
    spam_allocated_m3_yr: float | None = None
    items: list[PipeCellFileItem] = Field(default_factory=list)


class PipesFile(BaseModel):
    periods: list[SubsidencePeriod]
    spam: SpamTest


class SourceFile(BaseModel):
    sources: list[Source]


class RegionFile(BaseModel):
    regions: list[Region]


class DeclaredUseFile(BaseModel):
    records: list[DeclaredUse]


class EstimateFile(BaseModel):
    records: list[Estimate]


class TermsFile(BaseModel):
    records: list[AccountTerms]


class ValidationFile(BaseModel):
    checks: list[ValidationCheck]
