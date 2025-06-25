"""
Dependencias para el servicio de preguntas
"""
import httpx
from functools import lru_cache

from .config import settings
from ..domain.services.agentic_question_service import AgenticQuestionService
from ..infrastructure.database.question_repository import PostgresQuestionRepository
# Asumimos que existe un cliente similar en una librería compartida
# from ....shared.clients import AgenticOrchestratorClient
# Por ahora, lo definimos aquí para que sea autocontenido
class OrchestratorClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    async def process_educational_task(self, task: dict):
        # Simulación
        return {"answer": '```json[{"question_text": "Pregunta de prueba", "question_type": "open_ended", "correct_answer": "Respuesta de prueba", "explanation": "Explicación de prueba"}]```'}

@lru_cache()
def get_question_repository() -> PostgresQuestionRepository:
    return PostgresQuestionRepository(database_url=settings.DATABASE_URL)

@lru_cache()
def get_orchestrator_client() -> OrchestratorClient:
    return OrchestratorClient(base_url=settings.LLM_ORCHESTRATOR_URL)

def get_question_service() -> AgenticQuestionService:
    return AgenticQuestionService(
        question_repository=get_question_repository(),
        agentic_orchestrator=get_orchestrator_client(),
    ) 