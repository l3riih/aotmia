"""
Router principal de la API v1 del servicio de planificación
"""

from fastapi import APIRouter

from .endpoints import planning, health

api_router = APIRouter()

# Incluir endpoints
api_router.include_router(
    health.router,
    prefix="/planning",
    tags=["health"]
)

api_router.include_router(
    planning.router,
    prefix="/planning",
    tags=["planning"]
) 