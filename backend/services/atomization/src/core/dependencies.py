"""
Dependencias para inyección en FastAPI
"""

from functools import lru_cache
from typing import AsyncGenerator, Optional

from ..domain.services.agentic_atomization_service import AgenticAtomizationService
from ..infrastructure.database.mongodb_repository import MongoDBAtomRepository
from ..infrastructure.database.neo4j_repository import Neo4jRepository
from ..infrastructure.cache.redis_cache import RedisCache
from ..infrastructure.agentic.orchestrator_client import OrchestratorClient
from .config import settings


@lru_cache()
def get_orchestrator_client() -> OrchestratorClient:
    """Obtiene el cliente del orquestador agéntico."""
    return OrchestratorClient(
        base_url=settings.LLM_ORCHESTRATOR_URL
    )


@lru_cache()
def get_atom_repository() -> MongoDBAtomRepository:
    """Obtiene repositorio de átomos"""
    return MongoDBAtomRepository(
        mongodb_url=settings.MONGODB_URL,
        db_name=settings.MONGODB_DB_NAME
    )


@lru_cache()
def get_neo4j_repository() -> Neo4jRepository:
    """Obtiene repositorio de grafos Neo4j"""
    return Neo4jRepository(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )


@lru_cache()
def get_cache_service() -> RedisCache:
    """Obtiene servicio de cache"""
    return RedisCache(
        redis_url=settings.REDIS_URL,
        default_ttl=settings.CACHE_TTL_SECONDS
    )


def get_agentic_atomization_service() -> AgenticAtomizationService:
    """Obtiene servicio de atomización agéntico con todas las dependencias"""
    _atomization_service = AgenticAtomizationService(
        atom_repository=get_atom_repository(),
        graph_repository=get_neo4j_repository(),
        cache_service=get_cache_service(),
        agentic_orchestrator=get_orchestrator_client()
    )
    return _atomization_service 