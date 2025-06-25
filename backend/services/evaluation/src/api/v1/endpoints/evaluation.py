"""
Endpoints de evaluación agéntica
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import structlog
from fastapi.encoders import jsonable_encoder

from ....schemas import (
    EvaluationRequest, EvaluationResponse,
    BatchEvaluationRequest, BatchEvaluationResponse
)
from ....core.dependencies import get_evaluation_service
from functools import partial
from ....core.logging import log_agentic_operation
from ....domain.services.agentic_evaluation_service import AgenticEvaluationService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_student_response(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    service: AgenticEvaluationService = Depends(get_evaluation_service)
) -> EvaluationResponse:
    """
    Evalúa la respuesta de un estudiante usando el agente educativo.
    
    Implementa el workflow completo Plan-Execute-Observe-Reflect para:
    - Analizar la respuesta del estudiante
    - Detectar conceptos erróneos
    - Generar feedback constructivo
    - Calcular progreso de aprendizaje
    """
    try:
        # Log operación agéntica
        log_agentic_operation(
            operation="evaluation_start",
            user_id=request.user_id,
            question_id=request.question_id,
            evaluation_type=request.evaluation_type.value
        )
        
        # Procesar evaluación agéntica
        evaluation_response = await service.evaluate_student_response(request)
        
        # Tareas en background
        background_tasks.add_task(
            log_evaluation_analytics,
            evaluation_response,
            request
        )
        
        return evaluation_response
        
    except Exception as e:
        logger.error(
            "Evaluation endpoint error",
            error=str(e),
            user_id=request.user_id,
            question_id=request.question_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error en evaluación agéntica: {str(e)}"
        )


@router.post("/batch-evaluate")
async def batch_evaluate_responses(
    request: BatchEvaluationRequest,
    background_tasks: BackgroundTasks,
    service: AgenticEvaluationService = Depends(get_evaluation_service)
):
    """
    Evalúa múltiples respuestas de estudiantes en lote.
    
    Útil para:
    - Evaluación de exámenes completos
    - Procesamiento de tareas grupales
    - Análisis comparativo de respuestas
    """
    try:
        import uuid
        from datetime import datetime
        
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        start_time = datetime.utcnow()
        evaluations = []
        
        logger.info(
            "Starting batch evaluation",
            batch_id=batch_id,
            count=len(request.evaluations)
        )
        
        # Procesar cada evaluación
        for eval_request in request.evaluations:
            try:
                evaluation = await service.evaluate_student_response(eval_request)
                evaluations.append(evaluation)
            except Exception as e:
                logger.error(
                    "Error in batch evaluation item",
                    error=str(e),
                    user_id=eval_request.user_id,
                    question_id=eval_request.question_id
                )
                # Continuar con las demás evaluaciones
        
        # Calcular resumen
        processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        summary = {
            "total_evaluations": len(request.evaluations),
            "successful_evaluations": len(evaluations),
            "failed_evaluations": len(request.evaluations) - len(evaluations),
            "average_score": sum(e.score for e in evaluations) / len(evaluations) if evaluations else 0,
            "misconceptions_found": sum(len(e.misconceptions_detected) for e in evaluations),
            "average_confidence": sum(e.agent_metadata.confidence_score for e in evaluations) / len(evaluations) if evaluations else 0
        }
        
        # Log analytics en background
        background_tasks.add_task(
            log_batch_analytics,
            batch_id,
            summary
        )
        
        # Convertir objetos Pydantic a dict para serialización segura
        evaluations_dicts = [e.dict() for e in evaluations]
        
        # Calcular estadísticas básicas para la respuesta (opcional)
        stats = {
            "total_evaluations": len(evaluations),
            "average_score": sum(e.score for e in evaluations) / len(evaluations) if evaluations else 0,
            "average_confidence": sum(e.agent_metadata.confidence_score for e in evaluations) / len(evaluations) if evaluations else 0,
        }
        
        response_payload = BatchEvaluationResponse(
            batch_id=batch_id,
            evaluations=evaluations,  # Mantener objetos para trazabilidad interna
            summary=summary,
            processing_time_ms=processing_time_ms
        ).dict()
        
        # Añadir claves adicionales esperadas por el frontend / pruebas
        response_payload.update({
            "processed": summary["successful_evaluations"],
            "failed": summary["failed_evaluations"],
            "results": evaluations_dicts,
            "statistics": stats,
        })
        
        return jsonable_encoder(response_payload)
        
    except Exception as e:
        logger.error("Batch evaluation error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error en evaluación por lotes: {str(e)}"
        )


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: str,
    service: AgenticEvaluationService = Depends(get_evaluation_service)
) -> EvaluationResponse:
    """
    Obtiene una evaluación específica por ID.
    """
    try:
        evaluation_dict = await service.get_evaluation_by_id(evaluation_id)
        if not evaluation_dict:
            raise HTTPException(
                status_code=404,
                detail=f"Evaluación {evaluation_id} no encontrada"
            )
        return EvaluationResponse(**evaluation_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get evaluation error", error=str(e), evaluation_id=evaluation_id)
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo evaluación: {str(e)}"
        )


@router.get("/user/{user_id}/history")
async def get_user_evaluation_history(
    user_id: str,
    limit: int = 20,
    service: AgenticEvaluationService = Depends(get_evaluation_service)
):
    """
    Obtiene el historial de evaluaciones de un usuario.
    """
    try:
        evaluations_list = await service.get_user_evaluation_history(
            user_id=user_id,
            limit=limit
        )
        evaluations_objs = [EvaluationResponse(**e) for e in evaluations_list]
        # Calcular estadísticas básicas
        stats = {
            "total_evaluations": len(evaluations_objs),
            "average_score": sum(e.score for e in evaluations_objs) / len(evaluations_objs) if evaluations_objs else 0,
            "average_confidence": sum(e.agent_metadata.confidence_score for e in evaluations_objs) / len(evaluations_objs) if evaluations_objs else 0,
        }
        return {
            "evaluations": evaluations_objs,
            "statistics": stats
        }
    except Exception as e:
        logger.error(
            "Get user history error",
            error=str(e),
            user_id=user_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo historial: {str(e)}"
        )


# Funciones auxiliares para background tasks
async def log_evaluation_analytics(
    evaluation: EvaluationResponse,
    request: EvaluationRequest
):
    """Log analytics de evaluación para métricas"""
    logger.info(
        "Evaluation analytics",
        evaluation_id=evaluation.evaluation_id,
        user_id=request.user_id,
        question_id=request.question_id,
        score=evaluation.score,
        misconceptions_count=len(evaluation.misconceptions_detected),
        confidence=evaluation.agent_metadata.confidence_score,
        reasoning_steps=len(evaluation.agent_metadata.reasoning_steps),
        tools_used=evaluation.agent_metadata.tools_used,
        processing_time_ms=evaluation.agent_metadata.processing_time_ms
    )


async def log_batch_analytics(batch_id: str, summary: dict):
    """Log analytics de evaluación por lotes"""
    logger.info(
        "Batch evaluation analytics",
        batch_id=batch_id,
        **summary
    ) 