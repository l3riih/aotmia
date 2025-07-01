"""
FastAPI Application - Servicio Agéntico de Evaluación
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog
import os

from .core.config import settings
from .core.logging import configure_logging
from .api.v1.router import api_router

# Configurar logging
configure_logging()
logger = structlog.get_logger()

# Crear aplicación FastAPI
app = FastAPI(
    title=f"Atomia - {settings.SERVICE_NAME.capitalize()} Service",
    description="Servicio Agéntico de Evaluación con capacidades de razonamiento educativo avanzado",
    version=settings.SERVICE_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Incluir routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Montar métricas Prometheus
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.on_event("startup")
async def startup_event():
    """Inicialización del servicio"""
    logger.info(
        "Starting agentic evaluation service",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        port=settings.PORT
    )
    
    # Inicializar cache Redis si está habilitado
    from .core.dependencies import get_cache_service
    cache_service = get_cache_service()
    if cache_service:
        await cache_service.initialize()
    
    # Verificar conectividad con LLM Orchestrator
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.LLM_ORCHESTRATOR_URL}/health")
            if response.status_code == 200:
                logger.info("LLM Orchestrator connection verified")
            else:
                logger.warning(
                    "LLM Orchestrator health check failed",
                    status_code=response.status_code
                )
    except Exception as e:
        logger.error("Failed to connect to LLM Orchestrator", error=str(e))

    # Ejecutar migraciones Alembic (upgrade head)
    try:
        from alembic import command, config as alembic_config
        alembic_cfg = alembic_config.Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        # Asegurarse de que Alembic conozca la ruta de migrations y la URL
        migrations_path = os.path.join(os.path.dirname(__file__), "..", "migrations")
        alembic_cfg.set_main_option("script_location", migrations_path)
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL or settings.postgres_url)
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations applied")
    except Exception as mig_err:
        logger.warning("Failed to apply Alembic migrations", error=str(mig_err))


@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar el servicio"""
    logger.info("Shutting down agentic evaluation service")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "operational",
        "features": {
            "agentic_reasoning": True,
            "misconception_detection": settings.ENABLE_MISCONCEPTION_DETECTION,
            "adaptive_feedback": settings.ENABLE_ADAPTIVE_FEEDBACK,
            "workflow": "Plan-Execute-Observe-Reflect"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=1,  # Force single worker for development
        log_level=settings.LOG_LEVEL.lower()
    ) 