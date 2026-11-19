from __future__ import annotations

from fastapi import APIRouter

from neraca.domain.enums import ProvenanceLabel, Role
from neraca.schemas.common import LabelInfo, MetaResponse, RoleInfo

router = APIRouter(prefix="/meta", tags=["meta"])

LABEL_MEANINGS = {
    ProvenanceLabel.OFFICIAL: "A government regulation, official statistic, or official open data set.",
    ProvenanceLabel.MEASURED: "A satellite or field measurement.",
    ProvenanceLabel.TESTED: "Our method, which passed a test whose pass mark was fixed before the run.",
    ProvenanceLabel.CALCULATED: "Arithmetic on backed inputs. It carries their ranges.",
    ProvenanceLabel.WEAK: "Only one secondary source; shown but flagged until confirmed.",
    ProvenanceLabel.SCENARIO: "An assumption the user sets with a slider, never a finding.",
    ProvenanceLabel.MISSING: "Not obtained yet. The layer is hidden until it is.",
}

ROLE_MEANINGS = {
    Role.PUBLIC: "Public view. District counts only; no lead addresses.",
    Role.REGULATOR: "Tax office view. Accounts and validation.",
    Role.INSPECTOR: "Inspector view. Lead cards and field feedback.",
    Role.PLANNER: "Planner view. Pipe priority and subsidence.",
}


@router.get("/labels", response_model=list[LabelInfo])
def labels() -> list[LabelInfo]:
    return [LabelInfo(label=label, meaning=meaning) for label, meaning in LABEL_MEANINGS.items()]


@router.get("/roles", response_model=list[RoleInfo])
def roles() -> list[RoleInfo]:
    return [RoleInfo(role=role, meaning=meaning) for role, meaning in ROLE_MEANINGS.items()]


@router.get("/config", response_model=MetaResponse)
def config() -> MetaResponse:
    return MetaResponse(
        labels=[LabelInfo(label=label, meaning=meaning) for label, meaning in LABEL_MEANINGS.items()],
        roles=[RoleInfo(role=role, meaning=meaning) for role, meaning in ROLE_MEANINGS.items()],
        units=["m3/yr", "IDR/yr", "IDR/m3", "mm/yr", "m2", "L/s"],
    )
