from __future__ import annotations

from neraca.domain.enums import ProvenanceLabel
from neraca.domain.models import Source
from neraca.repositories.seed import SeedStore


class SourceService:
    """Output O5: the source register behind every number."""

    def __init__(self, seed: SeedStore) -> None:
        self.seed = seed

    def list_sources(
        self,
        *,
        label: ProvenanceLabel | None = None,
        query: str | None = None,
    ) -> list[Source]:
        items = sorted(self.seed.sources.values(), key=lambda source: source.id)
        if label:
            items = [source for source in items if source.label is label]
        if query:
            needle = query.lower()
            items = [
                source
                for source in items
                if needle in source.name.lower()
                or needle in source.publisher.lower()
                or needle in (source.note or "").lower()
            ]
        return items

    def get_source(self, source_id: str) -> Source:
        return self.seed.source(source_id)
