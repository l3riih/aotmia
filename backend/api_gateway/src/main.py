"""
API Gateway Agéntico Principal para Atomia
"""

import httpx
import structlog
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import time
import uuid

# Configuración de logging estructurado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configuración de servicios
SERVICE_URLS = {
    "atomization": "http://localhost:8001",
    "llm_orchestrator": "http://localhost:8002", 
    "evaluation": "http://localhost:8003",
    "planning": "http://localhost:8004",
    "questions": "http://localhost:8005",
    "gamification": "http://localhost:8006"
}

# Cliente HTTP global para reutilización
class ServiceClient:
    def __init__(self):
        self.clients: Dict[str, httpx.AsyncClient] = {}
    
    async def get_client(self, service_name: str) -> httpx.AsyncClient:
        if service_name not in self.clients:
            self.clients[service_name] = httpx.AsyncClient(
                base_url=SERVICE_URLS[service_name],
                timeout=30.0,
                follow_redirects=True
            )
        return self.clients[service_name]
    
    async def close_all(self):
        for client in self.clients.values():
            await client.aclose()

service_client = ServiceClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("🚀 Starting Atomia API Gateway")
    yield
    logger.info("🛑 Shutting down Atomia API Gateway")
    await service_client.close_all()

app = FastAPI(
    title="Atomia API Gateway Agéntico",
    description="Gateway principal para el Agente de IA Educativo con capacidades agénticas avanzadas",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # En producción, especificar hosts exactos
)

# Middleware para agregar request ID y timing
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Añade contexto y métricas a cada request"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Agregar headers de contexto
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    # Calcular tiempo de procesamiento
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        "Request processed",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response

# ===== ENDPOINTS DE SALUD =====

@app.get("/health", tags=["Health"])
async def gateway_health():
    """Health check del gateway y todos los servicios"""
    services_health = {}
    overall_healthy = True
    
    for service_name, url in SERVICE_URLS.items():
        try:
            client = await service_client.get_client(service_name)
            response = await client.get("/health", timeout=5.0)
            services_health[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": url,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            services_health[service_name] = {
                "status": "unreachable",
                "url": url,
                "error": str(e)
            }
            overall_healthy = False
    
    return {
        "gateway": "healthy",
        "services": services_health,
        "overall_status": "healthy" if overall_healthy else "degraded",
        "timestamp": time.time()
    }

# ===== PROXY AGÉNTICO =====

@app.post("/api/agent/process", tags=["Agentic"])
async def process_educational_task(request: Dict[str, Any]):
    """
    Procesa una tarea educativa usando el sistema agéntico completo.
    
    Workflow Plan-Execute-Observe-Reflect implementado en llm_orchestrator.
    """
    try:
        logger.info("Processing agentic task", task_type=request.get("task_type", "unknown"))
        
        client = await service_client.get_client("llm_orchestrator")
        response = await client.post("/agent/process", json=request)
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Agentic task completed", 
                       iterations=result.get("iterations", 0),
                       reasoning_steps=len(result.get("reasoning_steps", [])))
            return result
        else:
            logger.error("Agentic service error", status=response.status_code)
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except httpx.TimeoutException:
        logger.error("Agentic task timeout")
        raise HTTPException(status_code=504, detail="Timeout procesando tarea agéntica")
    except Exception as e:
        logger.error("Agentic task error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error en procesamiento agéntico: {str(e)}")

@app.get("/api/agent/memory/search", tags=["Agentic"])
async def search_agent_memory(query: str, user_id: Optional[str] = None, limit: int = 5):
    """Busca en la memoria semántica del agente"""
    try:
        client = await service_client.get_client("llm_orchestrator")
        params = {"query": query, "limit": limit}
        if user_id:
            params["user_id"] = user_id
            
        response = await client.get("/agent/memory/search", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error("Memory search error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error en búsqueda de memoria: {str(e)}")

# ===== PROXY A SERVICIOS =====

@app.api_route("/api/atomization/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Atomization"])
async def proxy_atomization(path: str, request: Request):
    """Proxy al servicio de atomización"""
    return await proxy_to_service("atomization", path, request)

@app.api_route("/api/evaluation/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Evaluation"])
async def proxy_evaluation(path: str, request: Request):
    """Proxy al servicio de evaluación"""
    return await proxy_to_service("evaluation", path, request)

@app.api_route("/api/planning/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Planning"])
async def proxy_planning(path: str, request: Request):
    """Proxy al servicio de planificación"""
    return await proxy_to_service("planning", path, request)

@app.api_route("/api/questions/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Questions"])
async def proxy_questions(path: str, request: Request):
    """Proxy al servicio de preguntas"""
    return await proxy_to_service("questions", path, request)

@app.api_route("/api/gamification/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Gamification"])
async def proxy_gamification(path: str, request: Request):
    """Proxy al servicio de gamificación"""
    return await proxy_to_service("gamification", path, request)

async def proxy_to_service(service_name: str, path: str, request: Request):
    """
    Función genérica para hacer proxy a cualquier servicio
    """
    try:
        client = await service_client.get_client(service_name)
        
        # Obtener el cuerpo de la request si existe
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Hacer la request al servicio
        response = await client.request(
            method=request.method,
            url=f"/api/v1/{path}",
            content=body,
            headers={
                key: value for key, value in request.headers.items()
                if key.lower() not in ["host", "content-length"]
            },
            params=request.query_params
        )
        
        # Retornar la respuesta
        return JSONResponse(
            content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            status_code=response.status_code,
            headers={
                key: value for key, value in response.headers.items()
                if key.lower() not in ["content-length", "content-encoding", "transfer-encoding"]
            }
        )
        
    except httpx.TimeoutException:
        logger.error("Service timeout", service=service_name, path=path)
        raise HTTPException(status_code=504, detail=f"Timeout en servicio {service_name}")
    except httpx.ConnectError:
        logger.error("Service unreachable", service=service_name, path=path)
        raise HTTPException(status_code=503, detail=f"Servicio {service_name} no disponible")
    except Exception as e:
        logger.error("Proxy error", service=service_name, path=path, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error en proxy a {service_name}: {str(e)}")

# ===== ENDPOINTS ESPECIALES =====

@app.get("/api/services", tags=["Services"])
async def list_services():
    """Lista todos los servicios disponibles y sus capacidades"""
    services_info = {}
    
    for service_name, url in SERVICE_URLS.items():
        try:
            client = await service_client.get_client(service_name)
            
            # Intentar obtener información del servicio
            try:
                response = await client.get("/", timeout=5.0)
                info = response.json() if response.status_code == 200 else {"status": "unknown"}
            except:
                info = {"status": "basic"}
            
            services_info[service_name] = {
                "url": url,
                "status": "available",
                "info": info
            }
        except Exception as e:
            services_info[service_name] = {
                "url": url,
                "status": "unavailable",
                "error": str(e)
            }
    
    return {
        "gateway": {
            "name": "Atomia API Gateway",
            "version": "2.0.0",
            "features": [
                "Agentic routing",
                "Service discovery",
                "Health monitoring",
                "Request tracing",
                "Load balancing"
            ]
        },
        "services": services_info
    }

@app.get("/api/capabilities", tags=["Capabilities"])
async def get_system_capabilities():
    """Obtiene las capacidades completas del sistema agéntico"""
    try:
        # Obtener capacidades del orquestador agéntico
        client = await service_client.get_client("llm_orchestrator")
        orchestrator_response = await client.get("/", timeout=10.0)
        orchestrator_info = orchestrator_response.json() if orchestrator_response.status_code == 200 else {}
        
        return {
            "system": "Atomia - Agente de IA Educativo",
            "architecture": "Microservicios Agénticos",
            "core_capabilities": {
                "agentic_reasoning": True,
                "workflow": "Plan-Execute-Observe-Reflect",
                "memory_system": "Multi-level (Short-term, Long-term, Semantic)",
                "pedagogical_principles": [
                    "Microaprendizaje (Skinner)",
                    "Repetición Espaciada",
                    "Aprendizaje Activo",
                    "Refuerzo Intermitente"
                ]
            },
            "services": {
                "atomization": "Descomposición inteligente de contenido",
                "evaluation": "Evaluación agéntica con detección de misconceptions",
                "planning": "Planificación adaptativa de rutas de aprendizaje",
                "questions": "Generación agéntica de preguntas educativas",
                "llm_orchestrator": "Sistema agéntico central con razonamiento",
                "gamification": "Sistema de adherencia y motivación"
            },
            "orchestrator": orchestrator_info,
            "gateway_features": [
                "Routing agéntico",
                "Monitoreo de salud",
                "Trazabilidad de requests",
                "Manejo de errores resiliente",
                "Balanceador de carga básico"
            ]
        }
        
    except Exception as e:
        logger.error("Error getting system capabilities", error=str(e))
        return {
            "system": "Atomia - Agente de IA Educativo",
            "status": "partial_info",
            "error": str(e)
        }

# Endpoint raíz
@app.get("/", tags=["Root"])
async def root():
    """Información básica del gateway"""
    return {
        "service": "Atomia API Gateway",
        "version": "2.0.0", 
        "description": "Gateway agéntico para sistema educativo de IA",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "services": "/api/services", 
            "capabilities": "/api/capabilities",
            "docs": "/api/docs",
            "agentic": "/api/agent/*",
            "microservices": "/api/{service}/*"
        }
    } 