from __future__ import annotations

import pytest

from neraca.core.errors import InvalidScenarioError
from neraca.domain.enums import PipeTestStatus
from neraca.repositories.seed import SeedStore
from neraca.services.pipes import DEFAULT_WEIGHTS, PipeService, interpret_spam_test
from tests.conftest import DATA_DIR


def test_subsidence_periods_are_real_medians() -> None:
    periods = PipeService(SeedStore(DATA_DIR)).periods()
    assert [period.key for period in periods] == ["2014_17", "2018_22", "2023_26"]
    assert periods[0].fast_mm_yr > periods[2].fast_mm_yr
    assert periods[0].fast_mm_yr == pytest.approx(112.777, rel=1e-4)


def test_spam_test_result_is_inconclusive() -> None:
    test = PipeService(SeedStore(DATA_DIR)).spam_test()
    assert test.status.value == "inconclusive"
    assert test.delta_mm_yr is not None and test.shift_null_p05 is not None
    assert test.delta_mm_yr > test.shift_null_p05  # no extra slowdown in the served kecamatan
    assert interpret_spam_test(test).startswith("Inconclusive")
    assert interpret_spam_test(test.model_copy(update={"status": PipeTestStatus.NOT_RUN})).startswith("The SPAM")


def test_priority_uses_clay_as_damage() -> None:
    collection = PipeService(SeedStore(DATA_DIR)).priority({"demand": 0, "damage": 1, "supply": 0})
    assert collection.status == "available"
    assert collection.weights == {"demand": 0, "damage": 1, "supply": 0}
    clays = [item.cell.clay_m for item in collection.items]
    assert clays == sorted(clays, reverse=True)
    assert PipeService(SeedStore(DATA_DIR)).priority().weights == DEFAULT_WEIGHTS


def test_supply_weight_favours_blocks_without_new_supply() -> None:
    items = PipeService(SeedStore(DATA_DIR)).priority({"demand": 0, "damage": 0, "supply": 1}).items
    assert items[0].cell.supply_m3_yr == 0
    assert items[-1].cell.supply_m3_yr == max(item.cell.supply_m3_yr for item in items)


def test_weights_are_validated() -> None:
    service = PipeService(SeedStore(DATA_DIR))
    with pytest.raises(InvalidScenarioError):
        service.priority({"demand": 1.5})
    with pytest.raises(InvalidScenarioError):
        service.priority({"demand": 0, "damage": 0, "supply": 0})


def test_interpretation_outcome_table() -> None:
    test = PipeService(SeedStore(DATA_DIR)).spam_test()
    pass_case = test.model_copy(
        update={
            "status": "pass",
            "delta_mm_yr": -10,
            "shift_null_p05": -2,
            "placebo_year_clean": True,
            "placebo_area_clean": True,
        }
    )
    assert "evidence for pipes" in interpret_spam_test(pass_case)

    placebo = test.model_copy(update={"status": "pass", "placebo_area_clean": False})
    assert "picking up noise" in interpret_spam_test(placebo)
