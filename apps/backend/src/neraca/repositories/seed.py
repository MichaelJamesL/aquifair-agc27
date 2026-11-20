from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from neraca.core.errors import NotFoundError
from neraca.domain.models import (
    AccountTerms,
    DeclaredUse,
    Estimate,
    Lead,
    Region,
    Source,
    ValidationCheck,
)
from neraca.domain.npa import NpaFile
from neraca.repositories.seed_models import (
    DeclaredUseFile,
    EstimateFile,
    LeadFile,
    PipeCellFile,
    PipesFile,
    RegionFile,
    SourceFile,
    TermsFile,
    ValidationFile,
)


class SeedStore:
    """Read-only, in-memory view of the curated real-data files."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.sources = self._load_sources()
        self.regions = self._load_regions()
        self.declared = self._load_declared()
        self.estimates = self._load_estimates()
        self.terms = self._load_terms()
        self.leads = self._load_leads()
        self.pipe_cells = self._load_pipe_cells()
        self.pipes = self._load_pipes()
        self.validation = self._load_validation()
        self.npa = self._load_npa()
        self.geometry = self._load_geometry()
        self.layers: dict[str, dict[str, Any]] = {
            "zones": self._read_json("zones.geojson"),
            "zone_wells": self._read_json("zone_wells.json"),
            "pdam_coverage": self._read_json("pdam_coverage.json"),
        }
        self._assert_source_links()

    def _read_json(self, name: str) -> Any:
        path = self.data_dir / name
        if not path.exists():
            raise RuntimeError(f"seed file not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_sources(self) -> dict[str, Source]:
        parsed = SourceFile.model_validate({"sources": self._read_json("sources.json")})
        return {source.id: source for source in parsed.sources}

    def _load_regions(self) -> dict[str, Region]:
        parsed = RegionFile.model_validate({"regions": self._read_json("regions.json")})
        return {region.id: region for region in parsed.regions}

    def _load_declared(self) -> dict[tuple[str, int], DeclaredUse]:
        parsed = DeclaredUseFile.model_validate({"records": self._read_json("accounts.json")})
        return {(record.region_id, record.year): record for record in parsed.records}

    def _load_estimates(self) -> dict[tuple[str, int, str], Estimate]:
        parsed = EstimateFile.model_validate({"records": self._read_json("estimates.json")})
        return {(record.region_id, record.year, record.method): record for record in parsed.records}

    def _load_terms(self) -> dict[tuple[str, int], AccountTerms]:
        parsed = TermsFile.model_validate({"records": self._read_json("account_terms.json")})
        return {(record.region_id, record.year): record for record in parsed.records}

    def _load_leads(self) -> LeadFile:
        return LeadFile.model_validate(self._read_json("leads.json"))

    def _load_pipe_cells(self) -> PipeCellFile:
        return PipeCellFile.model_validate(self._read_json("pipe_cells.json"))

    def _load_pipes(self) -> PipesFile:
        return PipesFile.model_validate(self._read_json("pipes.json"))

    def _load_validation(self) -> list[ValidationCheck]:
        parsed = ValidationFile.model_validate({"checks": self._read_json("validation.json")})
        return parsed.checks

    def _load_npa(self) -> NpaFile:
        return NpaFile.model_validate(self._read_json("npa.json"))

    def _load_geometry(self) -> dict[str, Any]:
        path = self.data_dir / "regions.geojson"
        if not path.exists():
            return {"type": "FeatureCollection", "features": []}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"regions.geojson must contain an object: {path}")
        return payload

    def _assert_source_links(self) -> None:
        referenced: set[str] = set()
        for source in self.sources.values():
            if not source.id:
                raise RuntimeError("source id cannot be empty")
        for region in self.regions.values():
            referenced.update(region.source_ids)
        for declared in self.declared.values():
            referenced.update(declared.source_ids)
        for estimate in self.estimates.values():
            referenced.update(estimate.source_ids)
        for terms in self.terms.values():
            referenced.update(terms.source_ids)
        for lead in self.leads.items:
            referenced.update(lead.source_ids)
        for cell in self.pipe_cells.items:
            referenced.update(cell.source_ids)
        for period in self.pipes.periods:
            referenced.update(period.source_ids)
        referenced.update(self.pipes.spam.source_ids)
        for check in self.validation:
            referenced.update(check.source_ids)
        referenced.update(self.npa.source_ids)
        referenced.add(self.layers["zones"]["source"]["source_id"])
        for row in self.layers["pdam_coverage"]["items"]:
            referenced.update(row["source_ids"])
        unknown = sorted(referenced - set(self.sources))
        if unknown:
            raise RuntimeError(f"seed data references unknown sources: {unknown}")

    def region(self, region_id: str) -> Region:
        try:
            return self.regions[region_id]
        except KeyError as exc:
            raise NotFoundError(f"region {region_id!r} not found") from exc

    def source(self, source_id: str) -> Source:
        try:
            return self.sources[source_id]
        except KeyError as exc:
            raise NotFoundError(f"source {source_id!r} not found") from exc

    def declared_for(self, region_id: str, year: int) -> DeclaredUse | None:
        return self.declared.get((region_id, year))

    def estimate_for(self, region_id: str, year: int, method: str) -> Estimate | None:
        return self.estimates.get((region_id, year, method))

    def terms_for(self, region_id: str, year: int) -> AccountTerms | None:
        return self.terms.get((region_id, year))

    def available_years(self) -> list[int]:
        return sorted({year for _, year in self.declared})

    def lead(self, lead_id: str) -> Lead:
        for lead in self.leads.items:
            if lead.id == lead_id:
                return lead
        raise NotFoundError(f"lead {lead_id!r} not found")
