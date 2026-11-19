from __future__ import annotations

from neraca.domain.enums import CheckResult, CheckStatus, ProvenanceLabel
from neraca.domain.models import (
    Account,
    AccountTerms,
    AccountYear,
    BillingCheck,
    CheckRef,
    DeclaredUse,
    Number,
    Range,
    Region,
    ScenarioResult,
)
from neraca.domain.npa import NpaTable
from neraca.repositories.seed import SeedStore

DECLARED_UNIT = "m3/yr"
MONEY_UNIT = "IDR/yr"
PER_M3_UNIT = "IDR/m3"
VALIDATED_METHOD = "validated_16km_split"
DEMAND_METHOD = "demand_4km"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


class AccountService:
    """Module A: declared vs estimated use, the gap, and its price."""

    def __init__(self, seed: SeedStore) -> None:
        self.seed = seed
        self.npa = NpaTable(seed.npa)
        self._checks = {check.code: check for check in seed.validation}

    def latest_year(self) -> int:
        years = self.seed.available_years()
        if not years:
            raise RuntimeError("no declared-use years in the seed data")
        return years[-1]

    def list_accounts(
        self,
        year: int | None = None,
        *,
        wilayah: str | None = None,
    ) -> list[Account]:
        selected_year = year or self.latest_year()
        regions = sorted(self.seed.regions.values(), key=lambda region: region.name)
        if wilayah:
            regions = [region for region in regions if region.wilayah == wilayah]
        return [self._build(region, selected_year) for region in regions]

    def get_account(self, region_id: str, year: int | None = None) -> Account:
        region = self.seed.region(region_id)
        return self._build(region, year or self.latest_year())

    def history(self, region_id: str) -> list[AccountYear]:
        region = self.seed.region(region_id)
        points: list[AccountYear] = []
        for year in self.seed.available_years():
            record = self.seed.declared_for(region.id, year)
            npa_value = Number.missing(MONEY_UNIT)
            if record is not None and record.npa_value_idr is not None:
                npa_value = Number(
                    value=record.npa_value_idr,
                    unit=MONEY_UNIT,
                    label=ProvenanceLabel.OFFICIAL,
                    source_ids=list(record.source_ids),
                )
            points.append(
                AccountYear(
                    year=year,
                    declared=self._declared_number(record),
                    npa_value_total=npa_value,
                )
            )
        return points

    def scenario(self, region_id: str, undeclared_m3: float) -> ScenarioResult:
        region = self.seed.region(region_id)
        band = self.npa.scenario_tax(region.wilayah, undeclared_m3)
        per_m3 = self.npa.undeclared_tax_band(region.wilayah)
        return ScenarioResult(
            region=region,
            undeclared_m3=undeclared_m3,
            npa=Range(
                low=per_m3.low_npa_idr,
                high=per_m3.high_npa_idr,
                unit=PER_M3_UNIT,
                label=ProvenanceLabel.OFFICIAL,
                source_ids=list(per_m3.source_ids),
                note="NPA for business groups K4-K2, top volume tier.",
            ),
            tax=Range(
                low=band.low_tax_idr,
                high=band.high_tax_idr,
                unit=MONEY_UNIT,
                label=ProvenanceLabel.CALCULATED,
                source_ids=list(band.source_ids),
                note="0.20 x NPA x the undeclared volume set by the user.",
            ),
            tax_rate=self.npa.tax_rate,
            note=(
                "Scenario, not a finding. The app prices an assumption the user sets, "
                "never an undeclared volume it measured."
            ),
        )

    def billing_check(self, region_id: str, year: int | None = None) -> BillingCheck:
        region = self.seed.region(region_id)
        selected_year = year or self.latest_year()
        record = self.seed.declared_for(region.id, selected_year)
        declared = self._declared_number(record)
        check = self._check_ref("V1")
        band = self.npa.undeclared_tax_band(region.wilayah)
        return BillingCheck(
            region=region,
            year=selected_year,
            check=check,
            realised_tax=Number.missing(MONEY_UNIT, note="APBD/LKPJ realisation has not been obtained."),
            declared_volume=declared,
            implied_tax_per_m3=Number.missing(PER_M3_UNIT, note="Requires realised tax divided by declared volume."),
            expected_band=Range(
                low=band.low_tax_idr,
                high=band.high_tax_idr,
                unit=PER_M3_UNIT,
                label=ProvenanceLabel.CALCULATED,
                source_ids=list(band.source_ids),
                note="0.20 x NPA for business groups K4-K2 at the top tier.",
            ),
            note=(
                "V1 is planned. It needs the realised groundwater tax from the APBD or LKPJ; "
                "the figure is not in the open dataset. The expected band is a reference, not a result."
            ),
        )

    def _build(self, region: Region, year: int) -> Account:
        record = self.seed.declared_for(region.id, year)
        declared = self._declared_number(record)
        estimate = self.seed.estimate_for(region.id, year, VALIDATED_METHOD)
        demand = self.seed.estimate_for(region.id, year, DEMAND_METHOD)
        terms = self.seed.terms_for(region.id, year)

        estimated_validated = Range.missing(DECLARED_UNIT)
        if estimate is not None:
            estimated_validated = Range(
                low=estimate.low_m3,
                central=estimate.central_m3,
                high=estimate.high_m3,
                unit=DECLARED_UNIT,
                label=estimate.label,
                source_ids=list(estimate.source_ids),
                note=estimate.note,
            )

        estimated_demand: Range | None = None
        if demand is not None:
            estimated_demand = Range(
                low=demand.low_m3,
                central=demand.central_m3,
                high=demand.high_m3,
                unit=DECLARED_UNIT,
                label=demand.label,
                source_ids=list(demand.source_ids),
                note=demand.note,
            )

        gap = self._gap(declared, estimated_validated, terms)
        undeclared = self.npa.undeclared_tax_band(region.wilayah)
        declared_band = self.npa.declared_tax_band(region.wilayah)

        tax_per_m3 = Range(
            low=undeclared.low_tax_idr,
            high=undeclared.high_tax_idr,
            unit=PER_M3_UNIT,
            label=ProvenanceLabel.CALCULATED,
            source_ids=list(undeclared.source_ids),
            note="Tax on one cubic metre of undeclared business use, K4-K2 top tier.",
        )

        if declared.value is not None:
            declared_base = Range(
                low=round(declared.value * declared_band.low_tax_idr),
                high=round(declared.value * declared_band.high_tax_idr),
                unit=MONEY_UNIT,
                label=ProvenanceLabel.CALCULATED,
                source_ids=_unique(list(declared.source_ids) + list(declared_band.source_ids)),
                note="The size of the declared tax base, not realised revenue.",
            )
        else:
            declared_base = Range.missing(MONEY_UNIT)

        npa_value = Number.missing(MONEY_UNIT)
        if record is not None and record.npa_value_idr is not None:
            npa_value = Number(
                value=record.npa_value_idr,
                unit=MONEY_UNIT,
                label=ProvenanceLabel.OFFICIAL,
                source_ids=list(record.source_ids),
                note="NPA value reported by ESDM. This is the tax base, not realised tax.",
            )

        checks = [self._check_ref(code) for code in ("V1", "V2") if code in self._checks]
        return Account(
            region=region,
            year=year,
            declared=declared,
            estimated_validated=estimated_validated,
            estimated_demand=estimated_demand,
            gap=gap,
            tax_per_m3=tax_per_m3,
            declared_tax_base=declared_base,
            npa_value_total=npa_value,
            checks=checks,
        )

    def _declared_number(self, record: DeclaredUse | None) -> Number:
        if (
            record is None
            or record.declared_m3 is None
            or (record.declared_m3 == 0 and record.npa_value_idr in (0, None))
        ):
            return Number.missing(
                DECLARED_UNIT,
                note="No declared volume for this region and year in the open dataset.",
            )
        return Number(
            value=record.declared_m3,
            unit=DECLARED_UNIT,
            label=ProvenanceLabel.OFFICIAL,
            source_ids=list(record.source_ids),
        )

    def _gap(
        self,
        declared: Number,
        estimate: Range,
        terms: AccountTerms | None,
    ) -> Range:
        if (
            declared.value is None
            or estimate.label is ProvenanceLabel.MISSING
            or estimate.low is None
            or estimate.high is None
        ):
            return Range.missing(
                DECLARED_UNIT,
                note="Needs both a declared volume and the validated 16 km estimate.",
            )

        sources = _unique(list(declared.source_ids) + list(estimate.source_ids))
        if terms is None:
            low = estimate.low - declared.value
            high = estimate.high - declared.value
            central = estimate.central - declared.value if estimate.central is not None else None
            return Range(
                low=low,
                central=central,
                high=high,
                unit=DECLARED_UNIT,
                label=ProvenanceLabel.CALCULATED,
                source_ids=sources,
                note="Estimated total minus declared. Household and public terms not entered.",
            )

        sources = _unique(sources + list(terms.source_ids))
        low = estimate.low - terms.household_wells_high_m3 - terms.public_supply_high_m3 - declared.value
        high = estimate.high - terms.household_wells_low_m3 - terms.public_supply_low_m3 - declared.value
        central = None
        if estimate.central is not None:
            household_mid = (terms.household_wells_low_m3 + terms.household_wells_high_m3) / 2
            public_mid = (terms.public_supply_low_m3 + terms.public_supply_high_m3) / 2
            central = estimate.central - household_mid - public_mid - declared.value
        if low > high:
            low, high = high, low
        return Range(
            low=round(low),
            central=round(central) if central is not None else None,
            high=round(high),
            unit=DECLARED_UNIT,
            label=ProvenanceLabel.CALCULATED,
            source_ids=sources,
            note=terms.note or "Estimated total minus exempt household wells, public supply wells, and declared use.",
        )

    def _check_ref(self, code: str) -> CheckRef:
        check = self._checks.get(code)
        if check is None:
            return CheckRef(code=code, status=CheckStatus.NOT_RUN, result=CheckResult.WAITING)
        return CheckRef(code=check.code, status=check.status, result=check.result)
