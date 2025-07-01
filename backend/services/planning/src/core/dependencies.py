"""
Dependencias para el servicio de planificación agéntico
"""

import httpx
import structlog
from functools import lru_cache
from typing import Dict, Any, Optional

from .config import settings
from ..domain.services.agentic_planning_service import AgenticPlanningService
from ..infrastructure.database.planning_repository import PostgresPlanningRepository
from ..infrastructure.database.neo4j_knowledge_graph import Neo4jPlanningRepository
from ..infrastructure.agentic.orchestrator_client import OrchestratorClient
from ..infrastructure.clients.atomization_client import AtomizationClient
from ..infrastructure.clients.evaluation_client import EvaluationClient
from ..domain.algorithms.fsrs_algorithm import FSRSAlgorithm
from ..domain.algorithms.zdp_algorithm import ZDPAlgorithm

logger = structlog.get_logger()

# Instancias singleton para evitar recrear conexiones
planning_service_instance: Optional[AgenticPlanningService] = None
http_client_instance: Optional[httpx.AsyncClient] = None

@lru_cache()
async def get_http_client() -> httpx.AsyncClient:
    """Cliente HTTP reutilizable para comunicación entre servicios"""
    global http_client_instance
    if http_client_instance is None:
        http_client_instance = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True
        )
        logger.info("HTTP client initialized")
    return http_client_instance

@lru_cache()
def get_orchestrator_client() -> OrchestratorClient:
    """Obtiene el cliente del orquestador agéntico."""
    return OrchestratorClient(
        base_url=settings.LLM_ORCHESTRATOR_URL,
        timeout=settings.REQUEST_TIMEOUT_SECONDS
    )

@lru_cache()
def get_atomization_client() -> AtomizationClient:
    """Obtiene el cliente del servicio de atomización."""
    return AtomizationClient(
        base_url=settings.ATOMIZATION_SERVICE_URL
    )

@lru_cache()
def get_evaluation_client() -> EvaluationClient:
    """Obtiene el cliente del servicio de evaluación."""
    return EvaluationClient(
        base_url=settings.EVALUATION_SERVICE_URL
    )

@lru_cache()
def get_planning_repository() -> PostgresPlanningRepository:
    """Obtiene repositorio de planificación con conexión real a PostgreSQL"""
    # Construir URL de base de datos real basada en configuración
    database_url = "postgresql+asyncpg://atomia_user:atomia_password@localhost/atomia_dev"
    logger.info("Initializing planning repository", database_url=database_url)
    return PostgresPlanningRepository(database_url)

@lru_cache()
def get_neo4j_repository() -> Neo4jPlanningRepository:
    """Obtiene repositorio Neo4j para el grafo de conocimiento"""
    return Neo4jPlanningRepository(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
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
        
        # Crear repositorios con conexiones reales
        planning_repository = get_planning_repository()
        graph_repository = get_neo4j_repository()
        
        # Crear clientes de servicios
        atomization_client = get_atomization_client()
        evaluation_client = get_evaluation_client()
        
        # Crear algoritmos
        fsrs_algorithm = FSRSAlgorithm(settings.get_fsrs_params())
        zdp_algorithm = ZDPAlgorithm(settings.ZDP_DIFFICULTY_WINDOW)
        
        # Crear servicio con todas las dependencias reales
        planning_service_instance = AgenticPlanningService(
            planning_repository=planning_repository,
            graph_repository=graph_repository,
            agentic_orchestrator=orchestrator_client,
            atomization_client=atomization_client,
            evaluation_client=evaluation_client,
            fsrs_algorithm=fsrs_algorithm,
            zdp_algorithm=zdp_algorithm
        )
        
        logger.info("Planning service initialized with real dependencies")
    
    return planning_service_instance

async def check_dependencies_health() -> Dict[str, bool]:
    """
    Verifica el estado de las dependencias del servicio.
    """
    health = {
        "database": False,
        "neo4j": False,
        "orchestrator": False,
        "atomization": False,
        "evaluation": False
    }
    
    try:
        # Verificar PostgreSQL
        repository = get_planning_repository()
        # Test básico de inicialización
        health["database"] = True
        logger.info("PostgreSQL connection verified")
    except Exception as e:
        logger.error("PostgreSQL connection failed", error=str(e))
    
    try:
        # Verificar Neo4j
        neo4j_repo = get_neo4j_repository()
        health["neo4j"] = True
        logger.info("Neo4j connection verified")
    except Exception as e:
        logger.error("Neo4j connection failed", error=str(e))
    
    try:
        # Verificar orquestador agéntico
        orchestrator = get_orchestrator_client()
        await orchestrator.health_check()
        health["orchestrator"] = True
        logger.info("Orchestrator connection verified")
    except Exception as e:
        logger.error("Orchestrator connection failed", error=str(e))
    
    try:
        # Verificar servicio de atomización
        atomization = get_atomization_client()
        await atomization.health_check()
        health["atomization"] = True
        logger.info("Atomization service verified")
    except Exception as e:
        logger.error("Atomization service failed", error=str(e))
    
    try:
        # Verificar servicio de evaluación
        evaluation = get_evaluation_client()
        await evaluation.health_check()
        health["evaluation"] = True
        logger.info("Evaluation service verified")
    except Exception as e:
        logger.error("Evaluation service failed", error=str(e))
    
    return health 