from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from neraca.api.deps import SeedDep, SessionDep
from neraca.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request, seed: SeedDep, session: SessionDep) -> HealthResponse:
    try:
        session.execute(text("SELECT 1"))
        database = "ok"
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    return HealthResponse(
        status="ok",
        environment=request.app.state.settings.environment,
        database=database,
        regions=len(seed.regions),
        sources=len(seed.sources),
        years=seed.available_years(),
    )
