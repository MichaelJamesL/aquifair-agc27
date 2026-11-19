from __future__ import annotations

from neraca.domain.enums import ProvenanceLabel, QualityClass
from neraca.domain.models import Number, TariffRow, TariffTable
from neraca.domain.npa import NpaTable
from neraca.repositories.seed import SeedStore


class TariffService:
    """The official NPA table, computed from the Pergub formula."""

    def __init__(self, seed: SeedStore) -> None:
        self.npa = NpaTable(seed.npa)
        self._groups = {group.key: group for group in seed.npa.groups}

    def table(
        self,
        wilayah: str,
        *,
        quality: QualityClass = QualityClass.GOOD,
        alternative: bool = True,
    ) -> TariffTable:
        rows: list[TariffRow] = []
        for group in sorted(self._groups):
            for tier_index, tier in enumerate(self.npa.data.tiers):
                npa_idr = self.npa.npa(
                    wilayah=wilayah,
                    quality=quality,
                    alternative=alternative,
                    group=group,
                    tier_index=tier_index,
                )
                tax_idr = self.npa.tax(npa_idr)
                rows.append(
                    TariffRow(
                        group=group,
                        group_name=self._groups[group].name,
                        tier_key=tier.key,
                        tier_label=tier.label,
                        npa_idr=Number(
                            value=npa_idr,
                            unit="IDR/m3",
                            label=ProvenanceLabel.OFFICIAL,
                            source_ids=list(self.npa.source_ids),
                        ),
                        tax_idr=Number(
                            value=tax_idr,
                            unit="IDR/m3",
                            label=ProvenanceLabel.CALCULATED,
                            source_ids=list(self.npa.source_ids),
                            note="0.20 x NPA.",
                        ),
                    )
                )
        return TariffTable(
            regulation=self.npa.data.regulation,
            in_force=self.npa.data.in_force,
            tax_rate=self.npa.tax_rate,
            wilayah=wilayah,
            quality=quality,
            alternative=alternative,
            rows=rows,
            source_ids=list(self.npa.source_ids),
        )
