"""
Router principal para la API v1 del servicio de gamificación
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()

api_router = APIRouter()

# Achievements endpoints
@api_router.get("/achievements/{user_id}")
async def get_user_achievements(user_id: str):
    """Obtener logros del usuario"""
    return {
        "user_id": user_id,
        "achievements": [
            {
                "id": "first_lesson",
                "name": "Primera Lección",
                "description": "Completaste tu primera lección",
                "icon": "🎓", 
                "earned": True,
                "earned_at": "2024-01-15T10:30:00Z",
                "points": 50
            },
            {
                "id": "week_streak", 
                "name": "Racha Semanal",
                "description": "Estudia 7 días consecutivos",
                "icon": "🔥",
                "earned": False,
                "progress": 4,
                "total": 7,
                "points": 200
            },
            {
                "id": "atom_master",
                "name": "Maestro de Átomos", 
                "description": "Domina 10 átomos de aprendizaje",
                "icon": "⚛️",
                "earned": True,
                "earned_at": "2024-01-20T14:15:00Z",
                "points": 300
            }
        ],
        "total_earned": 2,
        "total_available": 25
    }

@api_router.post("/achievements/{user_id}/check")
async def check_achievements(user_id: str):
    """Verificar nuevos logros para el usuario"""
    return {
        "user_id": user_id,
        "new_achievements": [
            {
                "id": "quiz_master",
                "name": "Maestro del Quiz",
                "description": "Responde correctamente 20 preguntas seguidas",
                "icon": "🧠",
                "points": 150
            }
        ],
        "checked_at": "2024-01-25T16:45:00Z"
    }

# Progress endpoints
@api_router.get("/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Obtener progreso detallado del usuario"""
    return {
        "user_id": user_id,
        "level": 5,
        "current_points": 1250,
        "points_to_next_level": 250,
        "total_points_earned": 1250,
        "streak": {
            "current_days": 7,
            "longest_streak": 12,
            "streak_type": "daily_study"
        },
        "stats": {
            "lessons_completed": 24,
            "atoms_mastered": 18,
            "quizzes_taken": 31,
            "perfect_scores": 8,
            "study_time_minutes": 1440
        },
        "next_milestone": {
            "level": 6,
            "reward": "Nuevo avatar disponible",
            "points_needed": 250
        }
    }

@api_router.post("/progress/{user_id}/update")
async def update_user_progress(user_id: str, progress_data: Dict[str, Any]):
    """Actualizar progreso del usuario"""
    return {
        "user_id": user_id,
        "updated": True,
        "points_awarded": progress_data.get("points", 0),
        "new_level": progress_data.get("new_level"),
        "achievements_unlocked": progress_data.get("achievements", [])
    }

# Streaks endpoints  
@api_router.get("/streaks/{user_id}")
async def get_user_streaks(user_id: str):
    """Obtener rachas del usuario"""
    return {
        "user_id": user_id,
        "active_streaks": [
            {
                "type": "daily_study",
                "current_count": 7,
                "best_count": 12,
                "last_activity": "2024-01-25T18:30:00Z"
            },
            {
                "type": "perfect_quiz",
                "current_count": 3,
                "best_count": 5,
                "last_activity": "2024-01-25T17:15:00Z"
            }
        ],
        "streak_rewards": [
            {"days": 7, "reward": "Bonus 50 puntos", "claimed": True},
            {"days": 14, "reward": "Avatar especial", "claimed": False}
        ]
    }

# Challenges endpoints
@api_router.get("/challenges/{user_id}")
async def get_user_challenges(user_id: str):
    """Obtener desafíos del usuario"""
    return {
        "user_id": user_id,
        "active_challenges": [
            {
                "id": "math_week",
                "name": "Semana de Matemáticas",
                "description": "Completa 10 lecciones de matemáticas esta semana",
                "progress": 6,
                "target": 10,
                "reward": "500 puntos + insignia matemática",
                "expires_at": "2024-01-28T23:59:59Z"
            }
        ],
        "completed_challenges": [
            {
                "id": "first_week",
                "name": "Primera Semana",
                "completed_at": "2024-01-22T12:00:00Z",
                "reward_claimed": True
            }
        ]
    }

# Leaderboard endpoints
@api_router.get("/leaderboard")
async def get_leaderboard(period: str = "weekly", limit: int = 10):
    """Obtener tabla de líderes"""
    return {
        "period": period,
        "leaderboard": [
            {"rank": 1, "user_id": "user123", "username": "MathWiz", "points": 2500},
            {"rank": 2, "user_id": "user456", "username": "ScienceGuru", "points": 2350},
            {"rank": 3, "user_id": "user789", "username": "HistoryBuff", "points": 2200},
        ],
        "user_rank": 15,
        "total_participants": 1247
    }

# Notifications endpoints
@api_router.get("/notifications/{user_id}")
async def get_notifications(user_id: str):
    """Obtener notificaciones de gamificación"""
    return {
        "user_id": user_id,
        "notifications": [
            {
                "id": "notif_001",
                "type": "achievement",
                "title": "¡Nuevo logro desbloqueado!",
                "message": "Has ganado la insignia 'Maestro de Átomos'",
                "icon": "⚛️",
                "created_at": "2024-01-25T14:15:00Z",
                "read": False
            },
            {
                "id": "notif_002", 
                "type": "streak_reminder",
                "title": "¡Mantén tu racha!",
                "message": "Llevas 7 días seguidos, ¡no lo pierdas!",
                "icon": "🔥",
                "created_at": "2024-01-25T20:00:00Z",
                "read": True
            }
        ]
    }

# Rewards endpoints
@api_router.get("/rewards/{user_id}")
async def get_available_rewards(user_id: str):
    """Obtener recompensas disponibles"""
    return {
        "user_id": user_id,
        "available_rewards": [
            {
                "id": "avatar_science",
                "name": "Avatar Científico",
                "description": "Un avatar con bata de laboratorio",
                "cost": 500,
                "type": "avatar",
                "unlocked": True
            },
            {
                "id": "theme_dark",
                "name": "Tema Oscuro",
                "description": "Activa el modo oscuro premium",
                "cost": 300,
                "type": "theme", 
                "unlocked": True
            }
        ],
        "user_points": 1250
    }

@api_router.post("/rewards/{user_id}/redeem/{reward_id}")
async def redeem_reward(user_id: str, reward_id: str):
    """Canjear una recompensa"""
    return {
        "user_id": user_id,
        "reward_id": reward_id,
        "success": True,
        "points_spent": 300,
        "remaining_points": 950,
        "message": "¡Recompensa canjeada exitosamente!"
    } 