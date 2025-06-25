"""
Inyección de dependencias para el servicio
"""

from functools import lru_cache
from typing import Optional

from ..domain.services.agentic_evaluation_service import AgenticEvaluationService
from ..infrastructure.database.evaluation_repository import EvaluationRepository
from ..infrastructure.cache.redis_cache import RedisCache
from ..infrastructure.agentic.orchestrator_client import OrchestratorClient
from .config import settings


@lru_cache()
def get_orchestrator_client() -> OrchestratorClient:
    """Obtiene cliente del LLM Orchestrator"""
    return OrchestratorClient()


@lru_cache()
def get_evaluation_repository() -> EvaluationRepository:
    """Obtiene repositorio de evaluaciones"""
    return EvaluationRepository(
        database_url=get_database_url(),
        pool_size=settings.DATABASE_POOL_SIZE
    )


_redis_cache: Optional[RedisCache] = None

def get_cache_service() -> Optional[RedisCache]:
    """Obtiene servicio de cache si está habilitado"""
    global _redis_cache
    if settings.ENABLE_CACHE:
        if _redis_cache is None:
            _redis_cache = RedisCache()
        return _redis_cache
    return None


_evaluation_service: Optional[AgenticEvaluationService] = None

def get_evaluation_service() -> AgenticEvaluationService:
    """Obtiene instancia del servicio de evaluación agéntica"""
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = AgenticEvaluationService(
            evaluation_repository=get_evaluation_repository(),
            cache_service=get_cache_service(),
            agentic_orchestrator=get_orchestrator_client()
        )
    return _evaluation_service

def get_database_url() -> str:
    """Obtiene la URL de la base de datos con fallback"""
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    # Usar la URL de PostgreSQL construida
    return settings.postgres_url 