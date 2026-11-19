from __future__ import annotations

import pytest

from neraca.core.errors import InvalidScenarioError
from neraca.repositories.seed import SeedStore
from neraca.services.pipes import DEFAULT_WEIGHTS, PipeService, interpret_spam_test
from tests.conftest import DATA_DIR


def test_subsidence_periods_are_real_medians() -> None:
    periods = PipeService(SeedStore(DATA_DIR)).periods()
    assert [period.key for period in periods] == ["2014_17", "2018_22", "2023_26"]
    assert periods[0].fast_mm_yr > periods[2].fast_mm_yr
    assert periods[0].fast_mm_yr == pytest.approx(112.777, rel=1e-4)


def test_spam_test_is_not_run_and_makes_no_claim() -> None:
    test = PipeService(SeedStore(DATA_DIR)).spam_test()
    assert test.status.value == "not_run"
    wording = interpret_spam_test(test)
    assert "has not been run" in wording
    assert "no claim" in wording.lower()


def test_priority_is_unavailable_without_cells() -> None:
    collection = PipeService(SeedStore(DATA_DIR)).priority()
    assert collection.status == "unavailable"
    assert collection.items == []
    assert collection.weights == DEFAULT_WEIGHTS


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
