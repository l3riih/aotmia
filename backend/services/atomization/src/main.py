"""
Servicio de Atomización Agéntica - Atomia

Este servicio maneja la atomización de contenido educativo usando:
- Pipeline modular de 7 pasos (Parse → Chunk → Atomize → Relate → Validate → Store → Index)
- Agentes de IA con capacidades de razonamiento avanzado
- Soporte para múltiples formatos (PDF, DOCX, TXT, HTML, MD)
- Interfaz web para monitoreo y gestión
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import structlog
import uvicorn
from typing import List

from .api.v1.router import router as api_v1_router
from .domain.web_interface.dashboard import router as dashboard_router
from .core.config import get_settings
from .core.logging import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()

# Settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Atomia - Servicio de Atomización Agéntica",
    description="""
    Sistema de atomización educativa que convierte documentos largos en átomos de aprendizaje coherentes.
    
    ## Características Principales
    
    - **Pipeline de 7 Pasos**: Parse → Chunk → Atomize → Relate → Validate → Store → Index
    - **Múltiples Formatos**: PDF, DOCX, TXT, HTML, Markdown
    - **Agentes de IA**: Razonamiento educativo avanzado con LangChain + LangGraph
    - **Resolución de Dependencias**: Mantiene coherencia conceptual entre chunks
    - **Validación Pedagógica**: Asegura calidad educativa de los átomos
    - **Interfaz Web**: Dashboard para monitoreo y gestión
    
    ## Endpoints Principales
    
    - `/api/v1/pipeline/process` - Procesamiento completo de documentos
    - `/api/v1/atomization/atomize` - Atomización simple (legacy)
    - `/dashboard/` - Interfaz web de gestión
    """,
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/dashboard")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "atomization",
        "version": "2.0.0",
        "features": {
            "agentic_reasoning": True,
            "memory_integration": True,
            "pedagogical_validation": True,
            "pipeline_processing": True,
            "multi_format_support": True,
            "web_interface": True
        }
    }

@app.get("/")
async def root():
    """Redirige al dashboard principal."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard/")

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    """Inicialización del servicio."""
    logger.info("🚀 Atomia Atomization Service starting up")
    logger.info("📊 Dashboard available at /dashboard/")
    logger.info("📚 API documentation at /api/docs")
    logger.info("🔧 Pipeline endpoint at /api/v1/pipeline/process")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar el servicio."""
    logger.info("🛑 Atomia Atomization Service shutting down")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_config=None  # Use structlog config
    ) 