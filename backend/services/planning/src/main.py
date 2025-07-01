"""
Servicio de Planificación Adaptativa para Atomia
"""

import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from typing import Dict, Any, List

# Configurar logging básico
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida del servicio"""
    logger.info("📚 Starting Atomia Planning Service")
    yield
    logger.info("🛑 Shutting down Atomia Planning Service")

app = FastAPI(
    title="Atomia - Planning Service",
    description="Servicio de planificación adaptativa de aprendizaje con IA",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check
@app.get("/health")
async def health_check():
    """Health check del servicio de planificación"""
    return {
        "service": "planning",
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "adaptive_planning": True,
            "spaced_repetition": True,
            "personalized_paths": True,
            "difficulty_adjustment": True,
            "progress_tracking": True,
            "knowledge_graph": True
        }
    }

# Endpoint raíz
@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Atomia Planning Service",
        "version": "2.0.0",
        "description": "Servicio de planificación adaptativa de aprendizaje",
        "status": "operational"
    }

# Endpoints de planificación
@app.post("/api/v1/plans/generate/{user_id}")
async def generate_learning_plan(user_id: str, subject: str = "general"):
    """Generar un plan de aprendizaje personalizado"""
    return {
        "plan_id": f"plan_{user_id}_{subject}",
        "user_id": user_id,
        "subject": subject,
        "status": "generated",
        "atoms": [
            {
                "id": "atom_1",
                "title": "Conceptos Básicos",
                "difficulty": "beginner",
                "estimated_time": 30,
                "prerequisites": []
            },
            {
                "id": "atom_2", 
                "title": "Aplicación Práctica",
                "difficulty": "intermediate",
                "estimated_time": 45,
                "prerequisites": ["atom_1"]
            }
        ],
        "total_estimated_time": 75,
        "created_at": "2024-01-25T16:00:00Z"
    }

@app.get("/api/v1/plans/{plan_id}")
async def get_learning_plan(plan_id: str):
    """Obtener un plan de aprendizaje específico"""
    return {
        "plan_id": plan_id,
        "status": "active",
        "progress": {
            "completed_atoms": 1,
            "total_atoms": 5,
            "completion_percentage": 20
        },
        "next_review": "2024-01-26T10:00:00Z"
    }

@app.put("/api/v1/plans/{plan_id}/progress")
async def update_progress(plan_id: str, progress_data: Dict[str, Any]):
    """Actualizar progreso del plan"""
    return {
        "plan_id": plan_id,
        "updated": True,
        "new_progress": progress_data.get("completion", 0),
        "adaptations_made": [
            "Adjusted difficulty based on performance",
            "Rescheduled review sessions"
        ]
    }

@app.get("/api/v1/users/{user_id}/next-atoms")
async def get_next_atoms(user_id: str, limit: int = 3):
    """Obtener próximos átomos recomendados para el usuario"""
    return {
        "user_id": user_id,
        "recommended_atoms": [
            {
                "id": "atom_next_1",
                "title": "Siguiente Concepto",
                "priority": "high",
                "reason": "Builds on recently mastered concepts"
            },
            {
                "id": "atom_review_1",
                "title": "Repaso Importante",
                "priority": "medium", 
                "reason": "Due for spaced repetition review"
            }
        ]
    }

@app.post("/api/v1/plans/{plan_id}/adapt")
async def adapt_plan(plan_id: str, adaptation_data: Dict[str, Any]):
    """Adaptar plan basado en rendimiento del usuario"""
    return {
        "plan_id": plan_id,
        "adapted": True,
        "changes": [
            "Increased difficulty for mathematics section",
            "Added extra practice exercises",
            "Adjusted review schedule"
        ],
        "reasoning": "User showing strong performance, ready for more challenge"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 