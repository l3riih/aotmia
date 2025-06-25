"""
Punto de entrada para el Servicio Agéntico de Generación de Preguntas
"""
import uvicorn
from fastapi import FastAPI
from ..core.config import settings
from .api.v1.router import router as api_v1_router

app = FastAPI(
    title="Atomia - Question Generation Service",
    version="1.0.0",
    description="Servicio para generar preguntas educativas usando agentes de IA."
)

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    ) 