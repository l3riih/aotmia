"""
Router principal de la API v1
"""

from fastapi import APIRouter

from .endpoints import evaluation, health

api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(
    health.router,
    prefix="/evaluation",
    tags=["health"]
)

api_router.include_router(
    evaluation.router,
    prefix="/evaluation",
    tags=["evaluation"]
) 