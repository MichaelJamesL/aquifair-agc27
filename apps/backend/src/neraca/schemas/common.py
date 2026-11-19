from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from neraca.domain.enums import ProvenanceLabel, Role


class LabelInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: ProvenanceLabel
    meaning: str


class RoleInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Role
    meaning: str


class MetaResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    labels: list[LabelInfo]
    roles: list[RoleInfo]
    units: list[str]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[Any] | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    environment: str
    database: str
    regions: int
    sources: int
    years: list[int] = Field(default_factory=list)
