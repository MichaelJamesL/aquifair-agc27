from __future__ import annotations

from fastapi import APIRouter

from neraca.api.deps import RoleDep, SeedDep, SessionDep
from neraca.domain.enums import LeadStage, UseClass, ZoneClass
from neraca.domain.models import (
    Feedback,
    HitRate,
    Lead,
    LeadCollection,
    LeadSummaryCollection,
)
from neraca.repositories.sql_feedback import SqlFeedbackRepository
from neraca.schemas.feedback import FeedbackCreate
from neraca.services.leads import LeadService

router = APIRouter(prefix="/leads", tags=["B - inspection leads"])


@router.get("", response_model=LeadCollection)
def list_leads(
    role: RoleDep,
    seed: SeedDep,
    session: SessionDep,
    district: str | None = None,
    use_class: UseClass | None = None,
    zone: ZoneClass | None = None,
    stage: LeadStage = LeadStage.LEAD,
) -> LeadCollection:
    service = LeadService(seed, SqlFeedbackRepository(session))
    return service.list_leads(role, district=district, use_class=use_class, zone=zone, stage=stage)


@router.get("/public/summary", response_model=LeadSummaryCollection)
def public_summary(seed: SeedDep, session: SessionDep) -> LeadSummaryCollection:
    service = LeadService(seed, SqlFeedbackRepository(session))
    return service.public_summary()


@router.get("/stats/hit-rate", response_model=list[HitRate])
def hit_rate(role: RoleDep, seed: SeedDep, session: SessionDep) -> list[HitRate]:
    service = LeadService(seed, SqlFeedbackRepository(session))
    return service.hit_rate(role)


@router.get("/{lead_id}", response_model=Lead)
def get_lead(lead_id: str, role: RoleDep, seed: SeedDep, session: SessionDep) -> Lead:
    service = LeadService(seed, SqlFeedbackRepository(session))
    return service.get_lead(role, lead_id)


@router.get("/{lead_id}/feedback", response_model=list[Feedback])
def list_feedback(lead_id: str, role: RoleDep, seed: SeedDep, session: SessionDep) -> list[Feedback]:
    service = LeadService(seed, SqlFeedbackRepository(session))
    return service.feedback_for_lead(role, lead_id)


@router.post("/{lead_id}/feedback", response_model=Feedback, status_code=201)
def add_feedback(
    lead_id: str,
    body: FeedbackCreate,
    role: RoleDep,
    seed: SeedDep,
    session: SessionDep,
) -> Feedback:
    service = LeadService(seed, SqlFeedbackRepository(session))
    return service.add_feedback(
        role,
        lead_id,
        inspector=body.inspector,
        outcome=body.outcome,
        note=body.note,
        visited_at=body.visited_at,
    )
