from __future__ import annotations

from neraca.core.errors import NotFoundError
from neraca.domain.enums import CheckStatus
from neraca.domain.models import ValidationCheck
from neraca.repositories.seed import SeedStore


class ValidationService:
    def __init__(self, seed: SeedStore) -> None:
        self.seed = seed

    def list_checks(
        self,
        *,
        module: str | None = None,
        status: CheckStatus | None = None,
    ) -> list[ValidationCheck]:
        items = list(self.seed.validation)
        if module:
            items = [check for check in items if check.module == module.upper()]
        if status:
            items = [check for check in items if check.status is status]
        return items

    def get_check(self, code: str) -> ValidationCheck:
        for check in self.seed.validation:
            if check.code.lower() == code.lower():
                return check
        raise NotFoundError(f"validation check {code!r} not found")
