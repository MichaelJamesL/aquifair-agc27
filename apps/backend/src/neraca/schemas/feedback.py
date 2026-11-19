from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from neraca.domain.enums import LeadOutcome


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspector: str = Field(min_length=1, max_length=120)
    outcome: LeadOutcome
    note: str | None = Field(default=None, max_length=2000)
    visited_at: date | None = None
