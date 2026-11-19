from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Header, Query, Request
from sqlalchemy.orm import Session

from neraca.domain.enums import Role
from neraca.infrastructure.database import get_session
from neraca.repositories.seed import SeedStore


def get_seed(request: Request) -> SeedStore:
    return cast(SeedStore, request.app.state.seed)


def get_role(
    x_role: Annotated[str | None, Header(alias="X-Role")] = None,
    role: Annotated[str | None, Query()] = None,
) -> Role:
    """Role from the UI dropdown. There is no login; this only gates views."""
    selected = x_role or role
    if not selected:
        return Role.PUBLIC
    try:
        return Role(selected.strip().lower())
    except ValueError:
        return Role.PUBLIC


SeedDep = Annotated[SeedStore, Depends(get_seed)]
SessionDep = Annotated[Session, Depends(get_session)]
RoleDep = Annotated[Role, Depends(get_role)]
