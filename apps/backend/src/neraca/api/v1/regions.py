from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from neraca.api.deps import SeedDep
from neraca.domain.models import Region

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=list[Region])
def list_regions(seed: SeedDep) -> list[Region]:
    return sorted(seed.regions.values(), key=lambda region: region.name)


@router.get("/geojson")
def region_geojson(seed: SeedDep) -> dict[str, Any]:
    return seed.geometry


@router.get("/{region_id}", response_model=Region)
def get_region(region_id: str, seed: SeedDep) -> Region:
    return seed.region(region_id)
