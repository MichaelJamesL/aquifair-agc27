from __future__ import annotations

import json
from pathlib import Path

from neraca.repositories.seed import SeedStore

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_seed_store_loads_and_links_every_source() -> None:
    seed = SeedStore(DATA_DIR)
    assert len(seed.regions) == 35
    assert len(seed.sources) >= 30
    assert seed.available_years() == [2020, 2021, 2022, 2023]


def test_every_region_has_an_official_npa_region() -> None:
    seed = SeedStore(DATA_DIR)
    assert {region.wilayah for region in seed.regions.values()} == {"A", "B", "C"}
    assert len([region for region in seed.regions.values() if region.wilayah == "A"]) == 15
    assert len([region for region in seed.regions.values() if region.wilayah == "B"]) == 15
    assert len([region for region in seed.regions.values() if region.wilayah == "C"]) == 5


def test_accounts_have_no_value_without_a_declared_volume() -> None:
    seed = SeedStore(DATA_DIR)
    for record in seed.declared.values():
        if record.npa_value_idr is not None:
            assert record.declared_m3 is not None


def test_semarang_2023_is_the_documented_value() -> None:
    seed = SeedStore(DATA_DIR)
    record = seed.declared_for("3374", 2023)
    assert record is not None
    assert record.declared_m3 == 10_069_814


def test_geojson_has_exactly_the_35_regions() -> None:
    seed = SeedStore(DATA_DIR)
    features = seed.geometry["features"]
    assert len(features) == 35
    ids = {feature["properties"]["region_id"] for feature in features}
    assert ids == set(seed.regions)


def test_no_synthetic_records_are_marked_available() -> None:
    seed = SeedStore(DATA_DIR)
    if seed.leads.status == "available":
        assert seed.leads.items, "available leads must contain records"
    else:
        assert seed.leads.items == []
    if seed.pipe_cells.status == "available":
        assert seed.pipe_cells.items, "available pipe cells must contain records"
    else:
        assert seed.pipe_cells.items == []


def test_all_seed_files_are_valid_json() -> None:
    for path in sorted(DATA_DIR.glob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
