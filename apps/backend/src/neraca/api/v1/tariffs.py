from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from neraca.api.deps import SeedDep
from neraca.domain.enums import QualityClass
from neraca.domain.models import TariffTable
from neraca.services.tariffs import TariffService

router = APIRouter(prefix="/tariffs", tags=["A - groundwater accounts"])


@router.get("", response_model=TariffTable)
def get_tariff_table(
    seed: SeedDep,
    wilayah: Annotated[str, Query(pattern="^[ABC]$")] = "C",
    quality: QualityClass = QualityClass.GOOD,
    alternative: bool = True,
) -> TariffTable:
    return TariffService(seed).table(wilayah, quality=quality, alternative=alternative)
