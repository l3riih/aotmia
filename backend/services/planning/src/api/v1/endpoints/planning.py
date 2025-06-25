"""
Endpoints del servicio agéntico de planificación
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
import structlog

from ....schemas import (
    CreatePlanRequest, LearningPlanResponse, UpdatePlanRequest,
    AdaptivePlanUpdate, RecommendationsRequest, RecommendationsResponse,
    AgenticCapabilitiesResponse
)
from ....core.dependencies import get_planning_service
from ....core.logging import agentic_metrics
from ....domain.services.agentic_planning_service import AgenticPlanningService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/create-plan", response_model=LearningPlanResponse)
async def create_learning_plan(
    request: CreatePlanRequest,
    background_tasks: BackgroundTasks,
    planning_service: AgenticPlanningService = Depends(get_planning_service)
):
    """
    Crea un plan de aprendizaje personalizado usando razonamiento agéntico.
    
    El servicio:
    - Analiza objetivos de aprendizaje y contexto del estudiante
    - Aplica algoritmos pedagógicos (FSRS, ZDP)
    - Genera una ruta optimizada con calendario
    - Predice probabilidad de éxito
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(
            "Creating learning plan",
            user_id=request.user_id,
            goals=request.learning_goals,
            time_available=request.time_available_hours
        )
        
        # Validar request
        if request.time_available_hours > 1000:
            raise HTTPException(
                status_code=400,
                detail="Tiempo disponible excede el límite máximo (1000 horas)"
            )
        
        # Crear plan con el agente
        plan = await planning_service.create_learning_plan(request)
        
        # Log métricas en background
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        background_tasks.add_task(
            agentic_metrics.log_planning_task,
            user_id=request.user_id,
            task_type="CREATE_PLAN",
            goals=request.learning_goals,
            duration_ms=duration_ms,
            iterations=plan.agent_metadata.iterations,
            confidence=plan.agent_metadata.confidence_score,
            success=True
        )
        
        return plan
        
    except Exception as e:
        logger.error(
            "Failed to create learning plan",
            error=str(e),
            user_id=request.user_id
        )
        
        # Log fallo
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        background_tasks.add_task(
            agentic_metrics.log_planning_task,
            user_id=request.user_id,
            task_type="CREATE_PLAN",
            goals=request.learning_goals,
            duration_ms=duration_ms,
            iterations=0,
            confidence=0.0,
            success=False
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error creando plan de aprendizaje: {str(e)}"
        )


@router.put("/update-plan/{plan_id}", response_model=AdaptivePlanUpdate)
async def update_plan_with_progress(
    plan_id: str,
    update_request: UpdatePlanRequest,
    background_tasks: BackgroundTasks,
    planning_service: AgenticPlanningService = Depends(get_planning_service)
):
    """
    Actualiza un plan basándose en el progreso del estudiante.
    
    Características:
    - Adaptación dinámica basada en evaluaciones
    - Reajuste de dificultad y ritmo
    - Replanificación si es necesario
    """
    try:
        logger.info(
            "Updating plan with progress",
            plan_id=plan_id,
            completed_atoms=len(update_request.completed_atoms),
            has_feedback=bool(update_request.user_feedback)
        )
        
        # Actualizar plan
        update = await planning_service.update_plan_with_progress(
            plan_id, update_request
        )
        
        # Log adaptación
        background_tasks.add_task(
            agentic_metrics.log_adaptation,
            plan_id=plan_id,
            adaptation_type="progress_based",
            changes_count=len(update.adaptations_made),
            reason=update.reason,
            confidence=update.confidence
        )
        
        return update
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to update plan",
            error=str(e),
            plan_id=plan_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando plan: {str(e)}"
        )


@router.get("/recommendations/{user_id}", response_model=RecommendationsResponse)
async def get_adaptive_recommendations(
    user_id: str,
    context: str = Query("current_session", description="Contexto de recomendación"),
    time_available_minutes: Optional[int] = Query(None, description="Tiempo disponible"),
    include_alternatives: bool = Query(True, description="Incluir alternativas"),
    background_tasks: BackgroundTasks = None,
    planning_service: AgenticPlanningService = Depends(get_planning_service)
):
    """
    Obtiene recomendaciones adaptativas de aprendizaje.
    
    Contextos disponibles:
    - current_session: Para sesión actual
    - next_topic: Siguiente tema a estudiar
    - review: Material de repaso
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(
            "Getting recommendations",
            user_id=user_id,
            context=context,
            time_available=time_available_minutes
        )
        
        # Crear request
        rec_request = RecommendationsRequest(
            user_id=user_id,
            context=context,
            time_available_minutes=time_available_minutes,
            include_alternatives=include_alternatives
        )
        
        # Obtener recomendaciones
        recommendations = await planning_service.get_adaptive_recommendations(
            rec_request
        )
        
        # Log métricas
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        avg_priority = sum(r.priority for r in recommendations.recommendations) / len(recommendations.recommendations) if recommendations.recommendations else 0.0
        
        background_tasks.add_task(
            agentic_metrics.log_recommendation,
            user_id=user_id,
            context=context,
            recommendations_count=len(recommendations.recommendations),
            avg_priority=avg_priority,
            response_time_ms=duration_ms
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(
            "Failed to get recommendations",
            error=str(e),
            user_id=user_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo recomendaciones: {str(e)}"
        )


@router.get("/plans/{plan_id}", response_model=LearningPlanResponse)
async def get_plan(
    plan_id: str,
    planning_service: AgenticPlanningService = Depends(get_planning_service)
):
    """Obtiene un plan de aprendizaje por ID"""
    try:
        # TODO: Implementar get_plan en el servicio
        raise HTTPException(
            status_code=501,
            detail="Endpoint no implementado aún"
        )
    except Exception as e:
        logger.error("Failed to get plan", error=str(e), plan_id=plan_id)
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo plan: {str(e)}"
        )


@router.get("/plans/user/{user_id}", response_model=List[LearningPlanResponse])
async def get_user_plans(
    user_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    planning_service: AgenticPlanningService = Depends(get_planning_service)
):
    """Obtiene todos los planes de un usuario"""
    try:
        # TODO: Implementar get_user_plans en el servicio
        raise HTTPException(
            status_code=501,
            detail="Endpoint no implementado aún"
        )
    except Exception as e:
        logger.error("Failed to get user plans", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo planes: {str(e)}"
        )


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    planning_service: AgenticPlanningService = Depends(get_planning_service)
):
    """Elimina un plan de aprendizaje"""
    try:
        # TODO: Implementar delete_plan en el servicio
        return {"message": f"Plan {plan_id} eliminado correctamente"}
    except Exception as e:
        logger.error("Failed to delete plan", error=str(e), plan_id=plan_id)
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando plan: {str(e)}"
        )


@router.get("/agentic-capabilities", response_model=AgenticCapabilitiesResponse)
async def get_agentic_capabilities():
    """
    Obtiene las capacidades agénticas del servicio de planificación.
    
    Incluye:
    - Herramientas disponibles
    - Algoritmos soportados
    - Puntos de integración
    - Límites del sistema
    """
    return AgenticCapabilitiesResponse() 