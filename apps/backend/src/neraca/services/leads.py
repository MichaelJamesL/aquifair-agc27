from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from neraca.core.errors import InvalidFeedbackError, NotFoundError, RoleForbiddenError
from neraca.domain.enums import LeadOutcome, LeadStage, Role, UseClass, ZoneClass
from neraca.domain.models import (
    Feedback,
    HitRate,
    Lead,
    LeadCollection,
    LeadSummary,
    LeadSummaryCollection,
)
from neraca.repositories.protocols import FeedbackRepository
from neraca.repositories.seed import SeedStore

INSPECTOR_ONLY = "Lead addresses are for inspectors only. The public view shows counts per district (risk R7)."


def wilson_interval(successes: int, total: int, *, z: float = 1.6448536269514722) -> tuple[float | None, float | None]:
    """90 % Wilson interval for a binomial proportion."""
    if total == 0:
        return None, None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def in_stage(lead: Lead, stage: LeadStage) -> bool:
    """True when the candidate passes filters 1..N of the stage (a filter not applied counts as passed)."""
    if stage is LeadStage.UNKNOWN:
        return lead.use_class is UseClass.UNKNOWN and lead.filters.get("3") is True
    return all(lead.filters.get(str(n)) is not False for n in range(1, int(stage.value[-1]) + 1))


class LeadService:
    """Module B: the lead list, the public counts, and the field-feedback loop."""

    def __init__(self, seed: SeedStore, feedback: FeedbackRepository) -> None:
        self.seed = seed
        self.feedback = feedback

    def list_leads(
        self,
        role: Role,
        *,
        district: str | None = None,
        use_class: UseClass | None = None,
        zone: ZoneClass | None = None,
        stage: LeadStage = LeadStage.LEAD,
    ) -> LeadCollection:
        self._require_inspector(role)
        if self.seed.leads.status == "unavailable":
            return LeadCollection(
                status="unavailable",
                reason=self.seed.leads.reason,
                items=[],
            )
        items = [lead for lead in self.seed.leads.items if in_stage(lead, stage)]
        if district:
            items = [lead for lead in items if lead.district.lower() == district.lower()]
        if use_class:
            items = [lead for lead in items if lead.use_class is use_class]
        if zone:
            items = [lead for lead in items if lead.zone is zone]
        return LeadCollection(
            status="available",
            funnel=list(self.seed.leads.funnel),
            method=dict(self.seed.leads.method),
            items=items,
        )

    def get_lead(self, role: Role, lead_id: str) -> Lead:
        self._require_inspector(role)
        return self.seed.lead(lead_id)

    def public_summary(self) -> LeadSummaryCollection:
        if self.seed.leads.status == "unavailable":
            return LeadSummaryCollection(
                status="unavailable",
                reason=self.seed.leads.reason,
                items=[],
            )
        grouped: dict[str, Counter[str]] = defaultdict(Counter)
        for lead in self.seed.leads.items:
            if in_stage(lead, LeadStage.LEAD):  # earlier funnel steps and site checks are not leads
                grouped[lead.district][lead.use_class.value] += 1
        items = [
            LeadSummary(
                district=district,
                leads=sum(counter.values()),
                by_use_class=dict(sorted(counter.items())),
                note="Counts only; no addresses or coordinates.",
            )
            for district, counter in sorted(grouped.items())
        ]
        return LeadSummaryCollection(status="available", funnel=list(self.seed.leads.funnel), items=items)

    def chip_path(self, role: Role, lead_id: str, year: int) -> Path:
        """Before/after Sentinel-2 true-colour chip for the lead card (inspectors only, like the card)."""
        self._require_inspector(role)
        self.seed.lead(lead_id)
        path = self.seed.data_dir / "lead_chips" / f"{lead_id}_{year}.png"
        if not path.exists():
            raise NotFoundError(f"no {year} image for lead {lead_id!r}")
        return path

    def add_feedback(
        self,
        role: Role,
        lead_id: str,
        *,
        inspector: str,
        outcome: LeadOutcome,
        note: str | None,
        visited_at: date | None,
    ) -> Feedback:
        self._require_inspector(role)
        self.seed.lead(lead_id)
        now = datetime.now(UTC)
        feedback = Feedback(
            id=str(uuid4()),
            lead_id=lead_id,
            inspector=inspector.strip(),
            outcome=outcome,
            note=note.strip() if note else None,
            visited_at=visited_at or now.date(),
            created_at=now,
        )
        if not feedback.inspector:
            raise InvalidFeedbackError("inspector name is required")
        return self.feedback.add(feedback)

    def feedback_for_lead(self, role: Role, lead_id: str) -> list[Feedback]:
        self._require_inspector(role)
        self.seed.lead(lead_id)
        return list(self.feedback.list_for_lead(lead_id))

    def hit_rate(self, role: Role) -> list[HitRate]:
        self._require_inspector(role)
        by_use_class: dict[str, list[Feedback]] = defaultdict(list)
        for item in self.feedback.list_all():
            try:
                lead = self.seed.lead(item.lead_id)
            except NotFoundError:
                lead_class = "unknown"
            else:
                lead_class = lead.use_class.value
            by_use_class[lead_class].append(item)

        results: list[HitRate] = []
        for lead_class, visits in sorted(by_use_class.items()):
            total = len(visits)
            unregistered = sum(1 for visit in visits if visit.outcome is LeadOutcome.UNREGISTERED_WELL)
            confirmed = sum(
                1 for visit in visits if visit.outcome in (LeadOutcome.REGISTERED_WELL, LeadOutcome.PDAM_CUSTOMER)
            )
            low, high = wilson_interval(unregistered, total)
            results.append(
                HitRate(
                    lead_class=lead_class,
                    visits=total,
                    unregistered=unregistered,
                    unregistered_rate=unregistered / total if total else None,
                    interval_90_low=low,
                    interval_90_high=high,
                    confirmed_water_user=confirmed,
                    confirmed_rate=confirmed / total if total else None,
                    note="Hit = an unregistered well was found. Reported per lead class (V6).",
                )
            )
        return results

    def _require_inspector(self, role: Role) -> None:
        if role is not Role.INSPECTOR:
            raise RoleForbiddenError(INSPECTOR_ONLY)
