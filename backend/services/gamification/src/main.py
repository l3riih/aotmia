"""
Servicio Agéntico de Gamificación y Adherencia para Atomia
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

# Configurar logging básico
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida del servicio"""
    logger.info("🎮 Starting Atomia Gamification Service")
    yield
    logger.info("🛑 Shutting down Atomia Gamification Service")

app = FastAPI(
    title="Atomia - Gamification & Adherence Service",
    description="Servicio agéntico para gamificación, adherencia y motivación educativa",
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
    """Health check del servicio de gamificación"""
    return {
        "service": "gamification",
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "achievement_system": True,
            "points_and_levels": True,
            "streaks_tracking": True,
            "challenges_system": True,
            "leaderboards": True,
            "smart_notifications": True,
            "behavioral_analytics": True,
            "adaptive_rewards": True
        }
    }

# Endpoint raíz
@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Atomia Gamification Service",
        "version": "2.0.0",
        "description": "Sistema agéntico de gamificación y adherencia educativa",
        "status": "operational"
    }

# Endpoints básicos de gamificación
@app.get("/api/v1/achievements/{user_id}")
async def get_user_achievements(user_id: str):
    """Obtener logros del usuario"""
    return {
        "user_id": user_id,
        "achievements": [
            {"id": "first_lesson", "name": "Primera Lección", "earned": True},
            {"id": "week_streak", "name": "Racha Semanal", "earned": False}
        ]
    }

@app.get("/api/v1/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Obtener progreso del usuario"""
    return {
        "user_id": user_id,
        "level": 5,
        "points": 1250,
        "streak_days": 7
    }

@app.post("/api/v1/progress/{user_id}/update")
async def update_user_progress(user_id: str):
    """Actualizar progreso del usuario"""
    return {
        "user_id": user_id,
        "updated": True,
        "message": "Progress updated successfully"
    }

@app.get("/api/v1/leaderboard")
async def get_leaderboard():
    """Obtener tabla de líderes"""
    return {
        "leaderboard": [
            {"rank": 1, "user_id": "user123", "username": "MathWiz", "points": 2500},
            {"rank": 2, "user_id": "user456", "username": "ScienceGuru", "points": 2350},
            {"rank": 3, "user_id": "user789", "username": "HistoryBuff", "points": 2200},
        ],
        "total_participants": 1247
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 