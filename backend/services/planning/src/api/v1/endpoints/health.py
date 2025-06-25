"""
Health check endpoints del servicio de planificación
"""

from fastapi import APIRouter, HTTPException
import structlog
from datetime import datetime

from ....schemas import HealthResponse
from ....core.config import settings
from ....core.dependencies import check_dependencies_health

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check del servicio de planificación.
    
    Verifica:
    - Estado del servicio
    - Dependencias externas
    - Features habilitados
    """
    try:
        # Verificar dependencias
        dependencies = await check_dependencies_health()
        
        # Determinar estado general
        all_healthy = all(dependencies.values())
        
        if not all_healthy:
            logger.warning(
                "Service degraded",
                dependencies=dependencies
            )
            
            # Si el orquestador no está disponible, el servicio está degradado
            if not dependencies["orchestrator"]:
                raise HTTPException(
                    status_code=503,
                    detail="Servicio degradado: Orquestador agéntico no disponible"
                )
        
        return HealthResponse(
            status="healthy" if all_healthy else "degraded",
            service=settings.SERVICE_NAME,
            version=settings.SERVICE_VERSION,
            features={
                "agentic_reasoning": dependencies["orchestrator"],
                "adaptive_planning": True,
                "spaced_repetition": True,
                "predictive_modeling": settings.ENABLE_PREDICTIVE_MODELING,
                "multi_algorithm": settings.ENABLE_MULTI_ALGORITHM_PLANNING
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/readiness")
async def readiness_check():
    """
    Readiness check para Kubernetes.
    
    Verifica si el servicio está listo para recibir tráfico.
    """
    try:
        dependencies = await check_dependencies_health()
        
        # Para estar "ready", necesitamos al menos el orquestador
        if not dependencies["orchestrator"]:
            raise HTTPException(
                status_code=503,
                detail="Service not ready: Orchestrator unavailable"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": dependencies
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check failed: {str(e)}"
        )


@router.get("/liveness")
async def liveness_check():
    """
    Liveness check para Kubernetes.
    
    Verifica si el servicio está vivo y respondiendo.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION
    } 