from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from neraca.api.errors import install_error_handlers
from neraca.api.health import router as health_router
from neraca.api.v1.router import router as v1_router
from neraca.core.config import Settings, get_settings
from neraca.infrastructure.database import Base, engine
from neraca.infrastructure.orm import LeadFeedbackRow  # noqa: F401 - register the table
from neraca.repositories.seed import SeedStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    app.state.seed = SeedStore(settings.data_dir)
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    logger.info(
        "loaded %s regions and %s sources from %s",
        len(app.state.seed.regions),
        len(app.state.seed.sources),
        settings.data_dir,
    )
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=logging.INFO if settings.environment != "test" else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "NERACA: groundwater accounts, inspection leads, and pipe priority. "
            "Every number carries its provenance label and source links."
        ),
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(v1_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
