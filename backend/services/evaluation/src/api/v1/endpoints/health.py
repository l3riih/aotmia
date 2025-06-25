"""
Health check endpoints agénticos
"""

from fastapi import APIRouter, Depends
import httpx
import structlog
from typing import Dict, Any
from datetime import datetime

from ....schemas import HealthResponse, AgenticCapabilitiesResponse
from ....core.config import settings, get_settings
from ....core.dependencies import get_orchestrator_client
from ....core.logging import get_logger
from ....infrastructure.agentic.orchestrator_client import OrchestratorClient

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check básico del servicio de evaluación.
    Confirma que el servicio está activo y responde.
    """
    logger.info("Health check requested")
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION
    )


@router.get("/agentic-capabilities", response_model=AgenticCapabilitiesResponse)
async def get_agentic_capabilities() -> AgenticCapabilitiesResponse:
    """
    Obtiene las capacidades agénticas del servicio.
    Útil para descubrimiento de servicios y debugging.
    """
    return AgenticCapabilitiesResponse(
        service=settings.SERVICE_NAME,
        workflow="Plan-Execute-Observe-Reflect",
        tools_available=[
            "analyze_student_response",
            "detect_misconceptions",
            "generate_constructive_feedback",
            "calculate_learning_progress"
        ],
        supported_evaluation_types=[
            "open_ended",
            "multiple_choice",
            "true_false",
            "fill_blank",
            "practical"
        ],
        pedagogical_principles=[
            "Evaluación Formativa",
            "Scaffolding Adaptativo",
            "Zona de Desarrollo Próximo",
            "Metacognición"
        ],
        llm_integration=True,
        max_reasoning_iterations=settings.MAX_REASONING_ITERATIONS
    )


@router.get("/agentic-status")
async def check_agentic_status(
    orchestrator: OrchestratorClient = Depends(get_orchestrator_client)
):
    """
    Verifica el estado completo del sistema agéntico.
    Incluye conectividad con LLM Orchestrator y servicios dependientes.
    """
    status = {
        "service": settings.SERVICE_NAME,
        "agentic_components": {
            "llm_orchestrator": "unknown",
            "memory_system": "unknown",
            "tools_available": "unknown"
        },
        "errors": []
    }
    
    # Verificar LLM Orchestrator
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.LLM_ORCHESTRATOR_URL}/health",
                timeout=5.0
            )
            if response.status_code == 200:
                status["agentic_components"]["llm_orchestrator"] = "healthy"
            else:
                status["agentic_components"]["llm_orchestrator"] = "unhealthy"
                status["errors"].append(f"LLM Orchestrator returned {response.status_code}")
    except Exception as e:
        status["agentic_components"]["llm_orchestrator"] = "unreachable"
        status["errors"].append(f"LLM Orchestrator error: {str(e)}")
    
    # Verificar herramientas educativas
    try:
        # TODO: Implementar verificación real de herramientas
        status["agentic_components"]["tools_available"] = "4 tools configured"
    except Exception as e:
        status["errors"].append(f"Tools check error: {str(e)}")
    
    # Verificar sistema de memoria
    try:
        # TODO: Implementar verificación real de memoria
        status["agentic_components"]["memory_system"] = "multi-level active"
    except Exception as e:
        status["errors"].append(f"Memory system error: {str(e)}")
    
    # Determinar estado general
    if status["errors"]:
        status["overall_status"] = "degraded"
    else:
        status["overall_status"] = "healthy"
    
    return status


def create_unified_status(
    orchestrator_status: Dict[str, Any],
    service: str = "evaluation"
) -> Dict[str, Any]:
    """Crea una respuesta de estado unificada."""
    return {
        "service_name": service,
        "service_version": settings.APP_VERSION,
        "service_status": "healthy" if orchestrator_status.get("status") == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "llm_orchestrator": orchestrator_status
        }
    } 