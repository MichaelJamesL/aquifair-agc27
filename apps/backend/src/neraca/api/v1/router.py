from __future__ import annotations

from fastapi import APIRouter

from neraca.api.v1 import meta, regions, sources, validation

router = APIRouter()
router.include_router(meta.router)
router.include_router(regions.router)
router.include_router(sources.router)
router.include_router(validation.router)
