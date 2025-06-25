"""
Endpoint para generar preguntas educativas
"""
from fastapi import APIRouter, Depends, HTTPException
from ....src.schemas import QuestionGenerationRequest, QuestionGenerationResponse
from ....src.domain.services.agentic_question_service import AgenticQuestionService
from ....src.core.dependencies import get_question_service

router = APIRouter()

@router.post("/generate", response_model=QuestionGenerationResponse)
async def generate_questions(
    request: QuestionGenerationRequest,
    service: AgenticQuestionService = Depends(get_question_service)
):
    """
    Genera preguntas para un átomo de aprendizaje usando el agente de IA.
    """
    try:
        response = await service.generate_questions_for_atom(request)
        return response
    except Exception as e:
        # En un caso real, manejaríamos errores específicos
        raise HTTPException(status_code=500, detail=str(e)) 