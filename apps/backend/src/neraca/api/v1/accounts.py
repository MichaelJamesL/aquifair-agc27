from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from neraca.api.deps import SeedDep
from neraca.domain.models import Account, AccountYear, BillingCheck, ScenarioResult
from neraca.services.accounts import AccountService

router = APIRouter(prefix="/accounts", tags=["A - groundwater accounts"])


@router.get("/years", response_model=list[int])
def list_years(seed: SeedDep) -> list[int]:
    return seed.available_years()


@router.get("/{region_id}/history", response_model=list[AccountYear])
def history(region_id: str, seed: SeedDep) -> list[AccountYear]:
    return AccountService(seed).history(region_id)


@router.get("", response_model=list[Account])
def list_accounts(
    seed: SeedDep,
    year: Annotated[int | None, Query(ge=2020, le=2100)] = None,
    wilayah: Annotated[str | None, Query(pattern="^[ABC]$")] = None,
) -> list[Account]:
    return AccountService(seed).list_accounts(year, wilayah=wilayah)


@router.get("/{region_id}", response_model=Account)
def get_account(
    region_id: str,
    seed: SeedDep,
    year: Annotated[int | None, Query(ge=2020, le=2100)] = None,
) -> Account:
    return AccountService(seed).get_account(region_id, year)


@router.get("/{region_id}/scenario", response_model=ScenarioResult)
def scenario(
    region_id: str,
    seed: SeedDep,
    undeclared_m3: Annotated[float, Query(ge=0, description="User-set undeclared volume")],
) -> ScenarioResult:
    return AccountService(seed).scenario(region_id, undeclared_m3)


@router.get("/{region_id}/billing-check", response_model=BillingCheck)
def billing_check(
    region_id: str,
    seed: SeedDep,
    year: Annotated[int | None, Query(ge=2020, le=2100)] = None,
) -> BillingCheck:
    return AccountService(seed).billing_check(region_id, year)
