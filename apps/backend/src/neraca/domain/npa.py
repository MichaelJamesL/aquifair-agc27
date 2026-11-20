from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from neraca.core.errors import InvalidScenarioError
from neraca.domain.enums import QualityClass


class NpaTier(BaseModel):
    key: str
    label: str
    min_m3: int
    max_m3: int | None


class NpaGroup(BaseModel):
    key: int
    name: str
    description: str


class NpaFile(BaseModel):
    regulation: str
    in_force: str
    tax_rate: float
    source_ids: list[str]
    hab_idr_per_m3: dict[str, int]
    resource_component: dict[str, int]
    use_component: dict[str, list[float]]
    tiers: list[NpaTier]
    groups: list[NpaGroup]
    note: str | None = None


@dataclass(frozen=True)
class TaxBand:
    low_npa_idr: int
    high_npa_idr: int
    low_tax_idr: int
    high_tax_idr: int
    source_ids: list[str]


class NpaTable:
    """The official NPA formula from Pergub Jateng 7/2025.

    NPA = HAB x BAT, where BAT = 0.6 * S + 0.4 * P.
    S depends on water quality and whether an alternative source exists.
    P depends on the use group and the volume tier.
    """

    def __init__(self, data: NpaFile) -> None:
        self.data = data
        self.tax_rate = data.tax_rate
        self.source_ids = list(data.source_ids)
        self._tiers = data.tiers
        self._groups = {group.key: group for group in data.groups}

    def _resource_component(self, quality: QualityClass, alternative: bool) -> int:
        if quality is QualityClass.GOOD and alternative:
            return self.data.resource_component["good_alternative"]
        if quality is QualityClass.GOOD and not alternative:
            return self.data.resource_component["good_no_alternative"]
        if quality is QualityClass.POOR and alternative:
            return self.data.resource_component["poor_alternative"]
        return self.data.resource_component["poor_no_alternative"]

    def _validate_group(self, group: int) -> None:
        if group not in self._groups:
            raise InvalidScenarioError(f"use group must be one of {sorted(self._groups)}")

    def _validate_tier(self, tier_index: int) -> None:
        if not 0 <= tier_index < len(self._tiers):
            raise InvalidScenarioError(f"tier index must be between 0 and {len(self._tiers) - 1}")

    def npa(
        self,
        *,
        wilayah: str,
        quality: QualityClass = QualityClass.GOOD,
        alternative: bool = True,
        group: int = 3,
        tier_index: int = 4,
    ) -> int:
        self._validate_group(group)
        self._validate_tier(tier_index)
        if wilayah not in self.data.hab_idr_per_m3:
            raise InvalidScenarioError(f"unknown NPA region {wilayah!r}")
        s = self._resource_component(quality, alternative)
        p = self.data.use_component[str(group)][tier_index]
        bat = 0.6 * s + 0.4 * p
        return round(self.data.hab_idr_per_m3[wilayah] * bat)

    def tax(self, npa_idr: int) -> int:
        return round(npa_idr * self.tax_rate)

    def band(
        self,
        *,
        wilayah: str,
        group_low: int,
        group_high: int,
        tier_index: int = 4,
    ) -> TaxBand:
        low_npa = self.npa(wilayah=wilayah, group=group_low, tier_index=tier_index)
        high_npa = self.npa(wilayah=wilayah, group=group_high, tier_index=tier_index)
        return TaxBand(
            low_npa_idr=low_npa,
            high_npa_idr=high_npa,
            low_tax_idr=self.tax(low_npa),
            high_tax_idr=self.tax(high_npa),
            source_ids=list(self.source_ids),
        )

    def undeclared_tax_band(self, wilayah: str) -> TaxBand:
        """K4-K2 at the top tier: the report's Rp 8.9-13.4 billion per 1 Mm3."""
        return self.band(wilayah=wilayah, group_low=4, group_high=2, tier_index=len(self._tiers) - 1)

    def declared_tax_band(self, wilayah: str) -> TaxBand:
        """K3-K2 at the top tier: the report's Rp 112-135 billion for 10.07 Mm3."""
        return self.band(wilayah=wilayah, group_low=3, group_high=2, tier_index=len(self._tiers) - 1)

    def scenario_tax(self, wilayah: str, undeclared_m3: float) -> TaxBand:
        if undeclared_m3 < 0:
            raise InvalidScenarioError("undeclared volume cannot be negative")
        band = self.undeclared_tax_band(wilayah)
        return TaxBand(
            low_npa_idr=band.low_npa_idr,
            high_npa_idr=band.high_npa_idr,
            low_tax_idr=round(band.low_npa_idr * self.tax_rate * undeclared_m3),
            high_tax_idr=round(band.high_npa_idr * self.tax_rate * undeclared_m3),
            source_ids=list(band.source_ids),
        )


class Npa2018File(BaseModel):
    regulation: str
    in_force: str
    valid_until_year: int
    formula: str
    tax_rate: float
    groups: list[str]
    tiers: list[str]
    hda_idr_per_m3: dict[str, list[list[int]]]
    wilayah_by_region: dict[str, str]
    source_ids: list[str]


class Hda2018Table:
    """The pre-2025 regime: NPA = volume x HDA (Pergub Jateng 19/2017, annex replaced by Pergub 54/2018)."""

    def __init__(self, data: Npa2018File) -> None:
        self.data = data

    def applies_to(self, year: int) -> bool:
        return year <= self.data.valid_until_year

    def billing_band(self, region_id: str) -> TaxBand:
        """V1 band: 0.20 x the HDA range of groups 2-4 (niaga kecil .. niaga besar), all volume tiers."""
        wilayah = self.data.wilayah_by_region[region_id]
        rows = self.data.hda_idr_per_m3[wilayah][1:4]
        low_npa, high_npa = min(min(r) for r in rows), max(max(r) for r in rows)
        return TaxBand(
            low_npa_idr=low_npa,
            high_npa_idr=high_npa,
            low_tax_idr=round(low_npa * self.data.tax_rate),
            high_tax_idr=round(high_npa * self.data.tax_rate),
            source_ids=list(self.data.source_ids),
        )
