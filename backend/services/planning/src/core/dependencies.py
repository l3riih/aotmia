"""
Dependencias del servicio de planificación
"""

from typing import AsyncGenerator
import httpx
import structlog
from functools import lru_cache
from typing import Optional

from .config import settings
from ..domain.services.agentic_planning_service import AgenticPlanningService
from ..infrastructure.agentic.orchestrator_client import OrchestratorClient
from ..infrastructure.database.planning_repository import PostgresPlanningRepository
from ..infrastructure.database.neo4j_repository import Neo4jPlanningRepository
from ..infrastructure.algorithms.fsrs import FSRSAlgorithm
from ..infrastructure.algorithms.zdp import ZDPAlgorithm
from ..infrastructure.clients.atomization_client import AtomizationClient
from ..infrastructure.clients.evaluation_client import EvaluationClient

logger = structlog.get_logger()

# Cliente HTTP global
http_client: httpx.AsyncClient = None

# Instancias de servicios
planning_service_instance: AgenticPlanningService = None


async def get_http_client() -> httpx.AsyncClient:
    """Obtiene cliente HTTP reutilizable"""
    global http_client
    
    if http_client is None:
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.REQUEST_TIMEOUT_SECONDS),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    
    return http_client


@lru_cache()
def get_orchestrator_client() -> OrchestratorClient:
    """Obtiene el cliente del orquestador LLM."""
    return OrchestratorClient(
        base_url=settings.LLM_ORCHESTRATOR_URL,
        timeout=30
    )


async def get_planning_service() -> AgenticPlanningService:
    """
    Obtiene instancia del servicio de planificación.
    Usa patrón singleton para reutilizar conexiones.
    """
    global planning_service_instance
    
    if planning_service_instance is None:
        # Obtener dependencias
        http_client = await get_http_client()
        
        # Crear clientes
        orchestrator_client = get_orchestrator_client()
        
        # Crear repositorios
        planning_repository = PostgresPlanningRepository(settings.DATABASE_URL)
        graph_repository = Neo4jPlanningRepository(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
        
        # Crear clientes de servicios (mock por ahora)
        atomization_client = get_atomization_client()
        evaluation_client = get_evaluation_client()
        
        # Crear algoritmos
        fsrs_algorithm = FSRSAlgorithm(settings.get_fsrs_params())
        zdp_algorithm = ZDPAlgorithm(settings.ZDP_DIFFICULTY_WINDOW)
        
        # Crear servicio
        planning_service_instance = AgenticPlanningService(
            planning_repository=planning_repository,
            graph_repository=graph_repository,
            orchestrator_client=orchestrator_client,
            atomization_client=atomization_client,
            evaluation_client=evaluation_client,
            fsrs_algorithm=fsrs_algorithm,
            zdp_algorithm=zdp_algorithm
        )
        
        logger.info("Planning service initialized")
    
    return planning_service_instance


async def close_connections():
    """Cierra todas las conexiones"""
    global http_client, planning_service_instance
    
    if http_client:
        await http_client.aclose()
        http_client = None
    
    # Cerrar conexiones de base de datos
    if planning_service_instance and planning_service_instance.planning_repository:
        await planning_service_instance.planning_repository.close_connection()

    planning_service_instance = None
    logger.info("All connections closed")


# Health check dependencies
async def check_orchestrator_health() -> bool:
    """Verifica salud del orquestador agéntico"""
    try:
        client = await get_http_client()
        response = await client.get(f"{settings.LLM_ORCHESTRATOR_URL}/health")
        return response.status_code == 200
    except Exception as e:
        logger.error("Orchestrator health check failed", error=str(e))
        return False


async def check_database_health() -> bool:
    """Verifica salud de la base de datos"""
    # TODO: Implementar check real de PostgreSQL
    return True  # Mock por ahora


async def check_dependencies_health() -> dict:
    """Verifica salud de todas las dependencias"""
    orchestrator_ok = await check_orchestrator_health()
    database_ok = await check_database_health()
    
    return {
        "orchestrator": orchestrator_ok,
        "database": database_ok,
        "atomization_service": True,  # TODO: Implementar
        "evaluation_service": True    # TODO: Implementar
    } 