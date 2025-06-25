"""
Servicio Agéntico de Generación de Preguntas
"""
import structlog
from typing import List, Dict, Any
import json
import re

from ....src.schemas import (
    QuestionGenerationRequest, QuestionGenerationResponse, GeneratedQuestion,
    Question, QuestionType
)

logger = structlog.get_logger()

class AgenticQuestionService:
    """
    Servicio para generar preguntas educativas usando un agente de IA.
    """

    def __init__(
        self,
        question_repository,  # PostgresQuestionRepository
        agentic_orchestrator, # AgenticOrchestratorClient
    ):
        self.question_repository = question_repository
        self.agentic_orchestrator = agentic_orchestrator

    async def generate_questions_for_atom(
        self, request: QuestionGenerationRequest
    ) -> QuestionGenerationResponse:
        """
        Genera preguntas para un átomo de aprendizaje usando el agente de IA.
        """
        task = self._build_question_generation_task(request)
        agent_result = await self.agentic_orchestrator.process_educational_task(task)
        
        generated_questions = self._extract_questions_from_agent_response(agent_result)

        # Crear objetos Question para persistencia
        questions_to_save = [
            Question(
                atom_id=request.atom_id,
                question_text=q.question_text,
                question_type=q.question_type,
                difficulty_level=request.difficulty,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation
            ) for q in generated_questions
        ]

        if questions_to_save:
            await self.question_repository.save_many(questions_to_save)

        return QuestionGenerationResponse(
            atom_id=request.atom_id,
            generated_questions=generated_questions,
            agent_metadata=agent_result.get("agent_metadata", {})
        )

    def _build_question_generation_task(self, request: QuestionGenerationRequest) -> Dict[str, Any]:
        """Construye la tarea para el agente generador de preguntas."""
        
        prompt = f"""
        TAREA: Generar {request.num_questions} preguntas educativas de alta calidad para el siguiente átomo de aprendizaje.

        CONTENIDO DEL ÁTOMO:
        ---
        {request.atom_content}
        ---

        REQUISITOS DE LAS PREGUNTAS:
        - Tipos de Pregunta: {', '.join([qt.value for qt in request.question_types])}
        - Nivel de Dificultad: {request.difficulty.value}
        - Deben evaluar la comprensión del contenido, no la memorización.
        - Para opción múltiple, los distractores deben ser plausibles y basados en errores comunes.
        - Cada pregunta debe tener una explicación clara de la respuesta correcta.

        FORMATO DE RESPUESTA:
        Devuelve una lista de objetos JSON. Cada objeto debe seguir esta estructura:
        ```json
        [
            {{
                "question_text": "Texto de la pregunta generada.",
                "question_type": "open_ended | multiple_choice | ...",
                "options": [
                    {{"option_text": "Opción A", "is_correct": false}},
                    {{"option_text": "Opción B", "is_correct": true}}
                ],
                "correct_answer": "Texto de la respuesta correcta (para preguntas abiertas).",
                "explanation": "Explicación detallada de por qué la respuesta es correcta."
            }}
        ]
        ```
        """
        return {
            "query": prompt,
            "user_id": request.user_id,
            "task_type": "QUESTION_GENERATION",
            "context": {
                "atom_id": request.atom_id,
                "difficulty": request.difficulty.value
            }
        }
    
    def _extract_questions_from_agent_response(self, agent_result: Dict[str, Any]) -> List[GeneratedQuestion]:
        """Extrae y valida las preguntas de la respuesta del agente."""
        try:
            answer = agent_result.get("answer", "")
            json_pattern = r'```json\s*(.*?)\s*```'
            match = re.search(json_pattern, answer, re.DOTALL)
            if match:
                questions_data = json.loads(match.group(1))
                return [GeneratedQuestion(**q) for q in questions_data]
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse questions from agent response", error=str(e))
        
        return [] 