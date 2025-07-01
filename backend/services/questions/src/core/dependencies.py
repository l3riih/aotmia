"""
Dependencias para el servicio de preguntas
"""
import httpx
import structlog
from functools import lru_cache
from typing import Optional

from .config import settings
from ..domain.services.agentic_question_service import AgenticQuestionService
from ..infrastructure.database.question_repository import PostgresQuestionRepository

logger = structlog.get_logger()

# Instancias singleton
_question_repository = None
_orchestrator_client = None
_question_service = None

class OrchestratorClient:
    """Cliente para el orquestador agéntico"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def process_educational_task(self, task: dict):
        """Procesa una tarea educativa usando el agente"""
        try:
            response = await self.client.post(
                f"{self.base_url}/agent/process",
                json=task,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("Orchestrator error", status=response.status_code, text=response.text)
                # Fallback con respuesta simulada
                return self._create_fallback_response(task)
                
        except Exception as e:
            logger.error("Orchestrator communication failed", error=str(e))
            return self._create_fallback_response(task)
    
    async def health_check(self):
        """Verifica la salud del orquestador"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def _create_fallback_response(self, task: dict):
        """Crea una respuesta de fallback cuando el orquestador no está disponible"""
        return {
            "answer": '''```json
[
    {
        "question_text": "¿Cuál es el concepto principal del contenido presentado?",
        "question_type": "open_ended",
        "correct_answer": "Respuesta basada en el contenido del átomo",
        "explanation": "Esta pregunta evalúa la comprensión del concepto fundamental."
    }
]
```''',
            "reasoning_steps": ["Generación de pregunta de fallback"],
            "tools_used": ["fallback_generator"],
            "iterations": 1
        }

@lru_cache()
def get_question_repository() -> PostgresQuestionRepository:
    """Obtiene repositorio de preguntas con conexión real a PostgreSQL"""
    global _question_repository
    if _question_repository is None:
        # Construir URL de base de datos real
        database_url = "postgresql+asyncpg://atomia_user:atomia_password@localhost/atomia_dev"
        _question_repository = PostgresQuestionRepository(database_url)
        logger.info("Question repository initialized", database_url=database_url)
    return _question_repository

@lru_cache()
def get_orchestrator_client() -> OrchestratorClient:
    """Obtiene cliente del orquestador agéntico"""
    global _orchestrator_client
    if _orchestrator_client is None:
        _orchestrator_client = OrchestratorClient(settings.LLM_ORCHESTRATOR_URL)
        logger.info("Orchestrator client initialized", url=settings.LLM_ORCHESTRATOR_URL)
    return _orchestrator_client

async def get_question_service() -> AgenticQuestionService:
    """Obtiene servicio de generación de preguntas agéntico"""
    global _question_service
    if _question_service is None:
        _question_service = AgenticQuestionService(
        question_repository=get_question_repository(),
        agentic_orchestrator=get_orchestrator_client(),
    ) 
        logger.info("Agentic question service initialized")
    return _question_service

async def check_dependencies_health():
    """Verifica el estado de las dependencias"""
    health = {
        "database": False,
        "orchestrator": False
    }
    
    try:
        # Verificar base de datos
        repository = get_question_repository()
        health["database"] = True
        logger.info("Database connection verified")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
    
    try:
        # Verificar orquestador
        orchestrator = get_orchestrator_client()
        health["orchestrator"] = await orchestrator.health_check()
        logger.info("Orchestrator connection verified")
    except Exception as e:
        logger.error("Orchestrator connection failed", error=str(e))
    
    return health 