from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from neraca.domain.enums import LeadOutcome
from neraca.domain.models import Feedback
from neraca.repositories.sql_feedback import SqlFeedbackRepository


def test_feedback_round_trip(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    repository = SqlFeedbackRepository(session)
    feedback = Feedback(
        id=str(uuid4()),
        lead_id="LEAD-TEST-1",
        inspector="Rina S.",
        outcome=LeadOutcome.UNREGISTERED_WELL,
        note="Found an unregistered well behind the factory.",
        visited_at=date(2026, 11, 19),
        created_at=datetime.now(UTC),
    )
    saved = repository.add(feedback)
    assert saved.id == feedback.id
    assert saved.outcome is LeadOutcome.UNREGISTERED_WELL

    items = list(repository.list_for_lead("LEAD-TEST-1"))
    assert len(items) == 1
    assert items[0].inspector == "Rina S."
    assert len(list(repository.list_all())) == 1
    session.close()


def test_feedback_is_isolated_per_lead(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    repository = SqlFeedbackRepository(session)
    for lead_id in ("LEAD-A", "LEAD-B"):
        repository.add(
            Feedback(
                id=str(uuid4()),
                lead_id=lead_id,
                inspector="Rina S.",
                outcome=LeadOutcome.NO_WELL,
                note=None,
                visited_at=date(2026, 11, 19),
                created_at=datetime.now(UTC),
            )
        )
    assert len(list(repository.list_for_lead("LEAD-A"))) == 1
    assert len(list(repository.list_for_lead("LEAD-B"))) == 1
    assert len(list(repository.list_all())) == 2
    session.close()
