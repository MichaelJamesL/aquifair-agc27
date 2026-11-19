from __future__ import annotations

from neraca.core.errors import InvalidScenarioError
from neraca.domain.enums import PipeTestStatus
from neraca.domain.models import (
    PipeCell,
    PipePriority,
    PipePriorityCollection,
    SpamTest,
    SubsidencePeriod,
)
from neraca.repositories.seed import SeedStore

DEFAULT_WEIGHTS = {"demand": 0.40, "damage": 0.40, "supply": 0.20}


def _normalise(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


class PipeService:
    """Module C: pipe priority and the SPAM before/after test."""

    def __init__(self, seed: SeedStore) -> None:
        self.seed = seed

    def periods(self) -> list[SubsidencePeriod]:
        return list(self.seed.pipes.periods)

    def spam_test(self) -> SpamTest:
        return self.seed.pipes.spam

    def priority(self, weights: dict[str, float] | None = None) -> PipePriorityCollection:
        selected = dict(DEFAULT_WEIGHTS)
        if weights:
            selected.update(weights)
        for key in ("demand", "damage", "supply"):
            if key not in selected:
                raise InvalidScenarioError(f"missing weight {key!r}")
            if not 0 <= selected[key] <= 1:
                raise InvalidScenarioError("each weight must be between 0 and 1")
        total_weight = sum(selected.values())
        if total_weight <= 0:
            raise InvalidScenarioError("at least one weight must be greater than zero")

        if self.seed.pipe_cells.status == "unavailable":
            return PipePriorityCollection(
                status="unavailable",
                reason=self.seed.pipe_cells.reason,
                weights=selected,
                items=[],
            )

        cells: list[PipeCell] = [
            PipeCell(
                id=item.id,
                lon=item.lon,
                lat=item.lat,
                demand_m3_yr=item.demand_m3_yr,
                damage_mm_yr=item.damage_mm_yr,
                supply_m3_yr=item.supply_m3_yr,
                source_ids=list(item.source_ids),
            )
            for item in self.seed.pipe_cells.items
        ]
        demand = _normalise([cell.demand_m3_yr for cell in cells])
        damage = _normalise([cell.damage_mm_yr for cell in cells])
        supply = _normalise([cell.supply_m3_yr for cell in cells])

        scored: list[PipePriority] = []
        for index, cell in enumerate(cells):
            score = (
                selected["demand"] * demand[index]
                + selected["damage"] * damage[index]
                + selected["supply"] * supply[index]
            ) / total_weight
            scored.append(
                PipePriority(
                    cell=cell,
                    score=round(score, 6),
                    demand_share=round(demand[index], 6),
                    damage_share=round(damage[index], 6),
                    supply_share=round(supply[index], 6),
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return PipePriorityCollection(status="available", weights=selected, items=scored)


def interpret_spam_test(test: SpamTest) -> str:
    """The outcome table from section C, in the order the report states it."""
    if test.status is PipeTestStatus.NOT_RUN:
        return (
            "The SPAM Semarang Barat before/after test has not been run. "
            "The app shows the design and the data on disk, but makes no claim."
        )
    if test.placebo_year_clean is False or test.placebo_area_clean is False:
        return "A placebo shows an effect. The method is picking up noise. No claim is made."
    if (
        test.delta_mm_yr is not None
        and test.shift_null_p05 is not None
        and test.delta_mm_yr < test.shift_null_p05
        and test.placebo_year_clean
        and test.placebo_area_clean
    ):
        return "Sinking slowed more where the pipes arrived. This is evidence for pipes as a local fix."
    if test.positive_control_passed is True:
        return (
            "The method can see a known pumping cut and saw no extra slowdown here. Pipe "
            "priority should follow the volume replaced, not the location."
        )
    if test.positive_control_passed is False:
        return "Inconclusive. The app shows the before/after maps without a claim either way."
    return "No claim is made until the test and its placebos are complete."
