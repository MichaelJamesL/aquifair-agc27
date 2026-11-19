from __future__ import annotations

from fastapi import APIRouter

from neraca.api.v1 import accounts, leads, meta, regions, sources, tariffs, validation

router = APIRouter()
router.include_router(meta.router)
router.include_router(regions.router)
router.include_router(accounts.router)
router.include_router(tariffs.router)
router.include_router(leads.router)
router.include_router(sources.router)
router.include_router(validation.router)
