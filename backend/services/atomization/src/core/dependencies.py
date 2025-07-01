"""
Dependencias para inyección en FastAPI
"""

from functools import lru_cache
from typing import AsyncGenerator, Optional

from ..domain.services.agentic_atomization_service import AgenticAtomizationService
from ..infrastructure.database.mongodb_repository import MongoDBAtomRepository
from ..infrastructure.database.neo4j_repository import Neo4jRepository
from ..infrastructure.cache.redis_cache import RedisCacheService
from ..infrastructure.agentic.orchestrator_client import OrchestratorClient
from .config import get_settings


@lru_cache()
def get_orchestrator_client() -> OrchestratorClient:
    """Obtiene el cliente del orquestador agéntico."""
    settings = get_settings()
    return OrchestratorClient(
        base_url=settings.LLM_ORCHESTRATOR_URL
    )


@lru_cache()
def get_atom_repository() -> MongoDBAtomRepository:
    """Obtiene repositorio de átomos"""
    settings = get_settings()
    return MongoDBAtomRepository(
        mongodb_url=settings.MONGODB_URL,
        db_name=settings.MONGODB_DB_NAME
    )


@lru_cache()
def get_neo4j_repository() -> Neo4jRepository:
    """Obtiene repositorio de grafos Neo4j"""
    settings = get_settings()
    return Neo4jRepository(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
        database="neo4j"  # Base de datos por defecto
    )


@lru_cache()
def get_cache_service() -> RedisCacheService:
    """Obtiene servicio de cache"""
    settings = get_settings()
    return RedisCacheService(
        redis_url=settings.REDIS_URL,
        default_ttl=settings.CACHE_TTL_SECONDS
    )


def get_agentic_atomization_service() -> AgenticAtomizationService:
    """Obtiene servicio de atomización agéntico con todas las dependencias"""
    atom_repo = get_atom_repository()
    orchestrator_client = get_orchestrator_client()
    cache_service = get_cache_service()
    neo4j_repo = get_neo4j_repository()
    
    _atomization_service = AgenticAtomizationService(
        atom_repository=atom_repo,
        graph_repository=neo4j_repo,
        cache_service=cache_service,
        agentic_orchestrator=orchestrator_client
    )
    return _atomization_service 