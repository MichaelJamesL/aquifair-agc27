from __future__ import annotations

from neraca.domain.enums import ProvenanceLabel
from neraca.repositories.seed import SeedStore
from neraca.services.accounts import AccountService
from tests.conftest import DATA_DIR


def service() -> AccountService:
    return AccountService(SeedStore(DATA_DIR))


def test_semarang_2023_declared_and_estimate() -> None:
    account = service().get_account("3374", 2023)
    assert account.declared.value == 10_069_814
    assert account.declared.label is ProvenanceLabel.OFFICIAL
    assert account.estimated_validated.low == 27_900_000
    assert account.estimated_validated.central == 43_800_000
    assert account.estimated_validated.high == 54_700_000
    assert account.estimated_validated.label is ProvenanceLabel.TESTED


def test_semarang_gap_range_is_honest() -> None:
    account = service().get_account("3374", 2023)
    assert account.gap.low is not None
    assert account.gap.high is not None
    assert account.gap.low < 0
    assert 40_000_000 < account.gap.high < 50_000_000


def test_tax_per_m3_matches_report() -> None:
    account = service().get_account("3374", 2023)
    assert account.tax_per_m3.low == 8_854
    assert account.tax_per_m3.high == 13_429
    assert account.declared_tax_base.low is not None
    assert 112_000_000_000 < account.declared_tax_base.low < 113_000_000_000
    assert 135_000_000_000 < account.declared_tax_base.high < 136_000_000_000


def test_scenario_is_calculated_not_a_finding() -> None:
    result = service().scenario("3374", 5_000_000)
    assert result.tax.low == 44_269_000_000
    assert result.tax.high == 67_143_000_000
    assert result.tax.label is ProvenanceLabel.CALCULATED
    assert "Scenario" in result.note


def test_region_without_estimate_is_missing() -> None:
    account = service().get_account("3301", 2023)
    assert account.declared.value is not None
    assert account.estimated_validated.label is ProvenanceLabel.MISSING
    assert account.gap.label is ProvenanceLabel.MISSING


def test_2020_zero_rows_are_missing_not_zero() -> None:
    account = service().get_account("3309", 2020)
    assert account.declared.label is ProvenanceLabel.MISSING
    assert account.declared.value is None
