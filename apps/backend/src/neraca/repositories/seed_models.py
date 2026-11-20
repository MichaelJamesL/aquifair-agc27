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
    demand_m3_yr: float
    damage_mm_yr: float
    supply_m3_yr: float
    source_ids: list[str] = Field(default_factory=list)


class PipeCellFile(BaseModel):
    status: Literal["available", "unavailable"] = "unavailable"
    reason: str | None = None
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
