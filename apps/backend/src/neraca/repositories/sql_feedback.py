from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from neraca.domain.enums import LeadOutcome
from neraca.domain.models import Feedback
from neraca.infrastructure.orm import LeadFeedbackRow


class SqlFeedbackRepository:
    """Postgres-backed feedback store. The only write path in the application."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, feedback: Feedback) -> Feedback:
        row = LeadFeedbackRow(
            id=feedback.id,
            lead_id=feedback.lead_id,
            inspector=feedback.inspector,
            outcome=feedback.outcome.value,
            note=feedback.note,
            visited_at=feedback.visited_at,
            created_at=feedback.created_at,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_domain(row)

    def list_for_lead(self, lead_id: str) -> Sequence[Feedback]:
        rows = self.session.scalars(
            select(LeadFeedbackRow).where(LeadFeedbackRow.lead_id == lead_id).order_by(LeadFeedbackRow.created_at.asc())
        ).all()
        return [self._to_domain(row) for row in rows]

    def list_all(self) -> Sequence[Feedback]:
        rows = self.session.scalars(select(LeadFeedbackRow).order_by(LeadFeedbackRow.created_at.asc())).all()
        return [self._to_domain(row) for row in rows]

    def _to_domain(self, row: LeadFeedbackRow) -> Feedback:
        return Feedback(
            id=row.id,
            lead_id=row.lead_id,
            inspector=row.inspector,
            outcome=LeadOutcome(row.outcome),
            note=row.note,
            visited_at=row.visited_at,
            created_at=row.created_at,
        )
