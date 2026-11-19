from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from neraca.api.deps import SeedDep
from neraca.domain.models import PipePriorityCollection, SpamTest, SubsidencePeriod
from neraca.services.pipes import PipeService, interpret_spam_test

router = APIRouter(prefix="/pipes", tags=["C - pipes instead of pumps"])


@router.get("/periods", response_model=list[SubsidencePeriod])
def list_periods(seed: SeedDep) -> list[SubsidencePeriod]:
    return PipeService(seed).periods()


@router.get("/spam-test", response_model=SpamTest)
def spam_test(seed: SeedDep) -> SpamTest:
    test = PipeService(seed).spam_test()
    return test.model_copy(update={"outcome_wording": interpret_spam_test(test)})


@router.get("/priority", response_model=PipePriorityCollection)
def priority(
    seed: SeedDep,
    w_demand: Annotated[float | None, Query(ge=0, le=1)] = None,
    w_damage: Annotated[float | None, Query(ge=0, le=1)] = None,
    w_supply: Annotated[float | None, Query(ge=0, le=1)] = None,
) -> PipePriorityCollection:
    weights = {
        key: value
        for key, value in (
            ("demand", w_demand),
            ("damage", w_damage),
            ("supply", w_supply),
        )
        if value is not None
    }
    return PipeService(seed).priority(weights)
