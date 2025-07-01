"""
Router principal para API v1 del servicio de atomización agéntico
"""

from fastapi import APIRouter
from .endpoints import atomization, health, pipeline

router = APIRouter()

# Include endpoint routers
router.include_router(
    atomization.router,
    prefix="/atomization",
    tags=["atomization"]
)

router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# Nueva ruta para pipeline independiente
router.include_router(
    pipeline.router,
    prefix="/pipeline",
    tags=["pipeline"]
) 