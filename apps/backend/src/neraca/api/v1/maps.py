from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from neraca.api.deps import SeedDep

router = APIRouter(prefix="/maps", tags=["map layers"])


@router.get("/zones")
def zones(seed: SeedDep) -> dict[str, Any]:
    """Official 2022 conservation zones of CAT Semarang-Demak, digitised from the ESDM vector map."""
    return seed.layers["zones"]


@router.get("/zone-wells")
def zone_wells(seed: SeedDep) -> dict[str, Any]:
    """The 'Sumur Bor' markers printed on the same official map (permitted deep wells)."""
    return seed.layers["zone_wells"]


@router.get("/pdam-coverage")
def pdam_coverage(seed: SeedDep) -> dict[str, Any]:
    """Piped-water coverage per kecamatan: the proxy for lead filter 4."""
    return seed.layers["pdam_coverage"]
