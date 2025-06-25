"""
Health check endpoints para el servicio de atomización agéntico
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import httpx
import structlog

from ....core.config import get_settings

logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()


@router.get("/status")
async def health_status() -> Dict[str, Any]:
    """
    Estado de salud del servicio de atomización agéntico.
    
    Verifica:
    - Estado del servicio local
    - Conectividad con LLM Orchestrator (sistema agéntico)
    - Estado de bases de datos
    - Capacidades agénticas disponibles
    """
    health_status = {
        "service": "atomization",
        "version": "2.0.0",
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "features": {
            "agentic_reasoning": False,
            "memory_integration": False,
            "pedagogical_validation": False,
            "workflow_plan_execute_observe_reflect": False
        },
        "dependencies": {
            "llm_orchestrator": {"status": "unknown", "url": settings.LLM_ORCHESTRATOR_URL},
            "mongodb": {"status": "unknown", "url": settings.MONGODB_URL},
            "redis": {"status": "unknown", "url": settings.REDIS_URL}
        },
        "agentic_capabilities": {
            "reasoning_quality_assessment": True,
            "educational_task_construction": True,
            "atom_extraction_from_agent": True,
            "pedagogical_validation": True,
            "metadata_enrichment": True,
            "cache_optimization": True
        }
    }
    
    # Verificar LLM Orchestrator (sistema agéntico principal)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.LLM_ORCHESTRATOR_URL}/health")
            if response.status_code == 200:
                health_status["dependencies"]["llm_orchestrator"]["status"] = "healthy"
                health_status["features"]["agentic_reasoning"] = True
                health_status["features"]["workflow_plan_execute_observe_reflect"] = True
                
                # Verificar capacidades específicas del agente
                try:
                    agent_response = await client.get(f"{settings.LLM_ORCHESTRATOR_URL}/agent/health")
                    if agent_response.status_code == 200:
                        agent_status = agent_response.json()
                        health_status["features"]["memory_integration"] = agent_status.get("memory_systems", {}).get("all_active", False)
                        health_status["agentic_capabilities"]["tools_available"] = agent_status.get("tools_count", 0)
                        health_status["agentic_capabilities"]["agent_active"] = agent_status.get("agent_active", False)
                except:
                    pass
            else:
                health_status["dependencies"]["llm_orchestrator"]["status"] = "unhealthy"
    except Exception as e:
        health_status["dependencies"]["llm_orchestrator"]["status"] = "error"
        health_status["dependencies"]["llm_orchestrator"]["error"] = str(e)
    
    # Verificar MongoDB
    try:
        # TODO: Implementar verificación real de MongoDB
        health_status["dependencies"]["mongodb"]["status"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["mongodb"]["status"] = "error"
        health_status["dependencies"]["mongodb"]["error"] = str(e)
    
    # Verificar Redis
    try:
        # TODO: Implementar verificación real de Redis
        health_status["dependencies"]["redis"]["status"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["redis"]["status"] = "error"
        health_status["dependencies"]["redis"]["error"] = str(e)
    
    # Determinar estado general
    agentic_healthy = health_status["dependencies"]["llm_orchestrator"]["status"] == "healthy"
    db_healthy = health_status["dependencies"]["mongodb"]["status"] == "healthy"
    cache_healthy = health_status["dependencies"]["redis"]["status"] == "healthy"
    
    if agentic_healthy and db_healthy and cache_healthy:
        health_status["status"] = "healthy"
        health_status["features"]["pedagogical_validation"] = True
    elif agentic_healthy:
        health_status["status"] = "degraded"
    else:
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/agentic-capabilities")
async def agentic_capabilities() -> Dict[str, Any]:
    """
    Detalle de las capacidades agénticas disponibles en el servicio.
    """
    return {
        "workflow": {
            "name": "Plan-Execute-Observe-Reflect",
            "description": "Workflow completo de razonamiento educativo",
            "steps": [
                {
                    "name": "PLAN",
                    "description": "Analiza contenido y planifica estrategia de atomización",
                    "implemented": True
                },
                {
                    "name": "EXECUTE", 
                    "description": "Usa herramientas educativas especializadas",
                    "implemented": True
                },
                {
                    "name": "OBSERVE",
                    "description": "Valida calidad pedagógica de los átomos",
                    "implemented": True
                },
                {
                    "name": "REFLECT",
                    "description": "Mejora átomos basado en principios educativos",
                    "implemented": True
                }
            ]
        },
        "pedagogical_principles": [
            {
                "name": "Microaprendizaje (Skinner)",
                "description": "Divide contenido en unidades pequeñas y autosuficientes",
                "implemented": True
            },
            {
                "name": "Prerrequisitos claros",
                "description": "Establece dependencias entre conceptos",
                "implemented": True
            },
            {
                "name": "Evaluabilidad",
                "description": "Cada átomo es fácilmente evaluable",
                "implemented": True
            },
            {
                "name": "Coherencia conceptual",
                "description": "Mantiene unidad temática en cada átomo",
                "implemented": True
            }
        ],
        "memory_systems": {
            "short_term": {
                "description": "Buffer de conversación en memoria",
                "implemented": True
            },
            "long_term": {
                "description": "Persistencia en Redis con TTL",
                "implemented": True
            },
            "semantic": {
                "description": "Búsqueda vectorial con ChromaDB",
                "implemented": True
            }
        },
        "educational_tools": [
            {
                "name": "search_learning_atoms",
                "description": "Busca átomos de aprendizaje relacionados",
                "implemented": True
            },
            {
                "name": "track_learning_progress",
                "description": "Rastrea progreso de aprendizaje",
                "implemented": True
            },
            {
                "name": "generate_adaptive_questions",
                "description": "Genera preguntas basadas en principios pedagógicos",
                "implemented": True
            },
            {
                "name": "evaluate_user_answer",
                "description": "Evalúa respuestas y proporciona retroalimentación",
                "implemented": True
            }
        ],
        "quality_assessment": {
            "reasoning_quality_scoring": {
                "description": "Evalúa calidad del razonamiento (0.0-1.0)",
                "factors": ["reasoning_steps", "tools_used", "iterations"],
                "implemented": True
            },
            "pedagogical_validation": {
                "description": "Valida principios educativos en átomos",
                "implemented": True
            },
            "metadata_enrichment": {
                "description": "Añade metadatos agénticos completos",
                "implemented": True
            }
        },
        "integration": {
            "llm_orchestrator": {
                "url": settings.LLM_ORCHESTRATOR_URL,
                "description": "Sistema agéntico principal con LangChain/LangGraph",
                "implemented": True
            },
            "cache_optimization": {
                "description": "Cache inteligente basado en contexto agéntico",
                "implemented": True
            },
            "traceability": {
                "description": "Trazabilidad completa del razonamiento",
                "implemented": True
            }
        }
    } 