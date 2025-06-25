"""
Servicio Agéntico de Planificación - FastAPI Application
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog
import time

from .api.v1.router import api_router
from .core.config import settings
from .core.logging import setup_logging

# Configurar logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    # Startup
    logger.info(
        "Starting Planning Service",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        port=settings.SERVICE_PORT
    )
    
    # Inicializar conexiones y recursos
    try:
        # TODO: Inicializar conexión a base de datos
        # TODO: Inicializar clientes de servicios
        # TODO: Inicializar algoritmos pedagógicos
        logger.info("All resources initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize resources", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Planning Service")
    # TODO: Cerrar conexiones y limpiar recursos


# Crear aplicación FastAPI
app = FastAPI(
    title="Atomia - Servicio Agéntico de Planificación",
    description="""
    Servicio de planificación adaptativa que crea rutas de aprendizaje personalizadas
    usando razonamiento agéntico y algoritmos pedagógicos avanzados.
    
    ## Características
    
    * 🧠 **Workflow Plan-Execute-Observe-Reflect**: Razonamiento agéntico completo
    * 📊 **Algoritmos Pedagógicos**: FSRS, ZDP, Exploración-Explotación
    * 🎯 **Personalización Extrema**: Planes adaptados a cada estudiante
    * 🔄 **Adaptación Dinámica**: Ajuste continuo basado en progreso
    * 📈 **Predicción de Resultados**: Modelado predictivo de éxito
    """,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log todas las requests con métricas de tiempo"""
    start_time = time.time()
    
    # Generar request ID
    request_id = request.headers.get("X-Request-ID", "no-id")
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        request_id=request_id
    )
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=int(duration * 1000),
            request_id=request_id
        )
        
        # Agregar headers de respuesta
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}"
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=int(duration * 1000),
            request_id=request_id
        )
        raise

# Incluir routers
app.include_router(api_router, prefix="/api/v1")

# Health check en raíz
@app.get("/", tags=["Health"])
async def root():
    """Health check básico en la raíz"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "healthy",
        "message": "Atomia Planning Service - Agentic Learning Path Optimization"
    }

# Endpoint de métricas Prometheus
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Endpoint de información del servicio
@app.get("/info", tags=["Service Info"])
async def service_info():
    """Información detallada del servicio"""
    return {
        "service": {
            "name": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "description": "Agentic Planning Service for Personalized Learning"
        },
        "features": settings.get_feature_flags(),
        "algorithms": {
            "enabled": list(settings.get_algorithm_config().keys()),
            "config": settings.get_algorithm_config()
        },
        "integrations": {
            "llm_orchestrator": settings.LLM_ORCHESTRATOR_URL,
            "atomization_service": settings.ATOMIZATION_SERVICE_URL,
            "evaluation_service": settings.EVALUATION_SERVICE_URL
        },
        "limits": {
            "max_atoms_per_plan": settings.MAX_ATOMS_PER_PLAN,
            "max_plan_duration_days": settings.MAX_PLAN_DURATION_DAYS,
            "max_planning_iterations": settings.MAX_PLANNING_ITERATIONS
        }
    }

# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__
    )
    
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "path": request.url.path,
        "request_id": request.headers.get("X-Request-ID", "no-id")
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True,
        log_config=None  # Usamos structlog
    ) 