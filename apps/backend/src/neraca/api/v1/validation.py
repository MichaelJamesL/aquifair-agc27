from __future__ import annotations

from fastapi import APIRouter

from neraca.api.deps import SeedDep
from neraca.domain.enums import CheckStatus
from neraca.domain.models import ValidationCheck
from neraca.services.validation import ValidationService

router = APIRouter(prefix="/validation", tags=["validation"])


@router.get("", response_model=list[ValidationCheck])
def list_checks(
    seed: SeedDep,
    module: str | None = None,
    status: CheckStatus | None = None,
) -> list[ValidationCheck]:
    return ValidationService(seed).list_checks(module=module, status=status)


@router.get("/{code}", response_model=ValidationCheck)
def get_check(code: str, seed: SeedDep) -> ValidationCheck:
    return ValidationService(seed).get_check(code)
