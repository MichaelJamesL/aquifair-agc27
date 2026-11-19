from __future__ import annotations

from neraca.domain.enums import QualityClass
from neraca.domain.npa import NpaTable
from neraca.repositories.seed import SeedStore
from tests.conftest import DATA_DIR


def table() -> NpaTable:
    return NpaTable(SeedStore(DATA_DIR).npa)


def test_wilayah_c_printed_values() -> None:
    npa = table()
    assert npa.npa(wilayah="C", group=1, tier_index=0) == 37_277
    assert npa.npa(wilayah="C", group=1, tier_index=4) == 78_575
    assert npa.npa(wilayah="C", group=2, tier_index=4) == 67_143
    assert npa.npa(wilayah="C", group=3, tier_index=4) == 55_701
    assert npa.npa(wilayah="C", group=4, tier_index=4) == 44_269
    assert npa.npa(wilayah="C", group=5, tier_index=4) == 32_826


def test_tax_bands_match_the_report() -> None:
    npa = table()
    undeclared = npa.undeclared_tax_band("C")
    assert undeclared.low_tax_idr == 8_854
    assert undeclared.high_tax_idr == 13_429

    declared = npa.declared_tax_band("C")
    assert declared.low_tax_idr == 11_140
    assert declared.high_tax_idr == 13_429


def test_hab_region_and_quality_variants() -> None:
    npa = table()
    good = npa.npa(wilayah="A", group=1, tier_index=0)
    poor = npa.npa(wilayah="A", quality=QualityClass.POOR, alternative=False, group=1, tier_index=0)
    assert good == 33_805
    assert poor == 10_756
    assert npa.npa(wilayah="B", group=1, tier_index=0) == 36_894


def test_scenario_prices_one_million_cubic_metres() -> None:
    npa = table()
    band = npa.scenario_tax("C", 1_000_000)
    assert band.low_tax_idr == 8_853_800_000
    assert band.high_tax_idr == 13_428_600_000
