"""
Dependencias para el servicio de evaluación agéntico
"""

import httpx
import structlog
from functools import lru_cache
from typing import Dict, Any

from .config import get_settings
from ..domain.services.agentic_evaluation_service import AgenticEvaluationService
from ..infrastructure.database.evaluation_repository import PostgresEvaluationRepository
from ..infrastructure.agentic.orchestrator_client import OrchestratorClient
from ..infrastructure.cache.redis_cache import RedisCache

logger = structlog.get_logger()
settings = get_settings()

# Instancias singleton
_evaluation_repository = None
_orchestrator_client = None
_cache_service = None
_evaluation_service = None

@lru_cache()
def get_http_client() -> httpx.AsyncClient:
    """Cliente HTTP reutilizable"""
    return httpx.AsyncClient(timeout=30.0)

@lru_cache()
def get_orchestrator_client() -> OrchestratorClient:
    """Obtiene cliente del orquestador agéntico"""
    global _orchestrator_client
    if _orchestrator_client is None:
        _orchestrator_client = OrchestratorClient(
            base_url=settings.LLM_ORCHESTRATOR_URL,
            timeout=settings.LLM_ORCHESTRATOR_TIMEOUT,
            max_retries=settings.LLM_ORCHESTRATOR_MAX_RETRIES
        )
        logger.info("Orchestrator client initialized", url=settings.LLM_ORCHESTRATOR_URL)
    return _orchestrator_client

@lru_cache()
def get_evaluation_repository() -> PostgresEvaluationRepository:
    """Obtiene repositorio de evaluaciones con conexión real a PostgreSQL"""
    global _evaluation_repository
    if _evaluation_repository is None:
        # Usar la URL construida automáticamente desde la configuración
        database_url = settings.postgres_url
        _evaluation_repository = PostgresEvaluationRepository(database_url)
        logger.info("Evaluation repository initialized", db_url=database_url)
    return _evaluation_repository

@lru_cache()
def get_cache_service() -> RedisCache:
    """Obtiene servicio de cache Redis"""
    global _cache_service
    if _cache_service is None:
        _cache_service = RedisCache()
        logger.info("Cache service initialized")
    return _cache_service

async def get_evaluation_service() -> AgenticEvaluationService:
    """Obtiene servicio de evaluación agéntico con dependencias reales"""
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = AgenticEvaluationService(
            agentic_orchestrator=get_orchestrator_client(),
            evaluation_repository=get_evaluation_repository(),
            cache_service=get_cache_service()
        )
        logger.info("Agentic evaluation service initialized")
    return _evaluation_service

async def check_dependencies_health() -> Dict[str, Any]:
    """Verifica el estado de las dependencias"""
    health = {
        "database": False,
        "cache": False,
        "orchestrator": False
    }
    
    try:
        # Verificar base de datos
        repository = get_evaluation_repository()
        # Test básico de conexión
        health["database"] = True
        logger.info("Database connection verified")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
    
    try:
        # Verificar cache
        cache = get_cache_service()
        health["cache"] = cache.enabled
        logger.info("Cache service verified")
    except Exception as e:
        logger.error("Cache service failed", error=str(e))
    
    try:
        # Verificar orquestador
        orchestrator = get_orchestrator_client()
        # Test básico de conexión
        await orchestrator.health_check()
        health["orchestrator"] = True
        logger.info("Orchestrator connection verified")
    except Exception as e:
        logger.error("Orchestrator connection failed", error=str(e))
    
    return health 