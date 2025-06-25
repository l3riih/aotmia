"""
Servicio de Atomización Agéntico
Microservicio que atomiza contenido educativo usando agentes de IA con razonamiento avanzado
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import structlog
import uvicorn
from typing import List

from .api.v1.router import router as api_v1_router
from .core.config import get_settings
from .core.logging import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()

# Settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Atomia - Servicio de Atomización Agéntico",
    description="Microservicio que atomiza contenido educativo usando agentes de IA con capacidades de razonamiento Plan-Execute-Observe-Reflect",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
            "pedagogical_validation": True
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Servicio de Atomización Agéntico - Atomia",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_config=None  # Use structlog config
    ) 