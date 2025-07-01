"""
Endpoint para generar preguntas educativas
"""
from fastapi import APIRouter, Depends, HTTPException
import structlog

from src.schemas import QuestionGenerationRequest, QuestionGenerationResponse
from src.domain.services.agentic_question_service import AgenticQuestionService
from src.core.dependencies import get_question_service

router = APIRouter()
logger = structlog.get_logger()

@router.post("/generate", response_model=QuestionGenerationResponse)
async def generate_questions(
    request: QuestionGenerationRequest,
    service: AgenticQuestionService = Depends(get_question_service)
):
    """
    Genera preguntas para un átomo de aprendizaje usando el agente de IA.
    
    Este endpoint utiliza el sistema agéntico para generar preguntas educativas
    de alta calidad basadas en principios pedagógicos y el contenido del átomo.
    """
    try:
        logger.info(
            "Generating questions",
            atom_id=request.atom_id,
            question_types=[qt.value for qt in request.question_types],
            difficulty=request.difficulty.value,
            num_questions=request.num_questions
        )
        
        response = await service.generate_questions_for_atom(request)
        
        logger.info(
            "Questions generated successfully",
            atom_id=request.atom_id,
            questions_count=len(response.generated_questions),
            request_id=str(response.request_id)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Question generation failed",
            error=str(e),
            atom_id=request.atom_id,
            user_id=request.user_id
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Error generando preguntas: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check del servicio de preguntas"""
    from src.core.dependencies import check_dependencies_health
    
    try:
        health = await check_dependencies_health()
        
        status = "healthy" if all(health.values()) else "degraded"
        
        return {
            "service": "questions",
            "status": status,
            "version": "1.0.0",
            "dependencies": health,
            "features": {
                "agentic_generation": True,
                "multiple_question_types": True,
                "pedagogical_validation": True,
                "database_persistence": health["database"]
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}") 