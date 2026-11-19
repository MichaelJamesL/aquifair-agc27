from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from neraca.domain.models import Feedback


class FeedbackRepository(Protocol):
    def add(self, feedback: Feedback) -> Feedback: ...

    def list_for_lead(self, lead_id: str) -> Sequence[Feedback]: ...

    def list_all(self) -> Sequence[Feedback]: ...
