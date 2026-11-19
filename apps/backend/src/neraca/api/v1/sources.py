from __future__ import annotations

from fastapi import APIRouter

from neraca.api.deps import SeedDep
from neraca.domain.enums import ProvenanceLabel
from neraca.domain.models import Source
from neraca.services.sources import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[Source])
def list_sources(
    seed: SeedDep,
    label: ProvenanceLabel | None = None,
    q: str | None = None,
) -> list[Source]:
    return SourceService(seed).list_sources(label=label, query=q)


@router.get("/{source_id}", response_model=Source)
def get_source(source_id: str, seed: SeedDep) -> Source:
    return SourceService(seed).get_source(source_id)
