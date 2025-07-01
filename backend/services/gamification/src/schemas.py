"""
Esquemas Pydantic para el Servicio de Gamificación y Adherencia
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid


# ===== ENUMS =====

class AchievementType(str, Enum):
    """Tipos de logros"""
    PROGRESS = "progress"
    CONSISTENCY = "consistency"
    MASTERY = "mastery"
    SOCIAL = "social"
    SPECIAL = "special"
    HIDDEN = "hidden"

class StreakType(str, Enum):
    """Tipos de rachas"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class ChallengeType(str, Enum):
    """Tipos de desafíos"""
    DAILY = "daily"
    WEEKLY = "weekly"
    SPECIAL = "special"
    COMMUNITY = "community"

class NotificationType(str, Enum):
    """Tipos de notificaciones"""
    ACHIEVEMENT = "achievement"
    STREAK_REMINDER = "streak_reminder"
    CHALLENGE = "challenge"
    COMEBACK = "comeback"
    MILESTONE = "milestone"
    SOCIAL = "social"

class UserLevel(str, Enum):
    """Niveles de usuario"""
    BEGINNER = "beginner"
    EXPLORER = "explorer"
    SCHOLAR = "scholar"
    EXPERT = "expert"
    MASTER = "master"
    SAGE = "sage"


# ===== MODELOS BASE =====

class Achievement(BaseModel):
    """Modelo para logros"""
    id: str = Field(..., description="ID único del logro")
    name: str = Field(..., description="Nombre del logro")
    description: str = Field(..., description="Descripción del logro")
    type: AchievementType = Field(..., description="Tipo de logro")
    icon: str = Field(..., description="Icono del logro")
    points: int = Field(..., ge=0, description="Puntos otorgados")
    rarity: str = Field(default="common", description="Rareza del logro")
    criteria: Dict[str, Any] = Field(..., description="Criterios para desbloquear")
    is_hidden: bool = Field(default=False, description="Si es un logro oculto")
    category: Optional[str] = Field(None, description="Categoría del logro")
    
    class Config:
        from_attributes = True

class UserAchievement(BaseModel):
    """Logro desbloqueado por un usuario"""
    user_id: str = Field(..., description="ID del usuario")
    achievement_id: str = Field(..., description="ID del logro")
    achievement: Achievement = Field(..., description="Datos del logro")
    unlocked_at: datetime = Field(..., description="Fecha de desbloqueo")
    progress: float = Field(default=1.0, ge=0.0, le=1.0, description="Progreso del logro")
    
    class Config:
        from_attributes = True

class UserProgress(BaseModel):
    """Progreso general del usuario en gamificación"""
    user_id: str = Field(..., description="ID del usuario")
    total_points: int = Field(default=0, ge=0, description="Puntos totales")
    current_level: UserLevel = Field(default=UserLevel.BEGINNER, description="Nivel actual")
    level_progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progreso en el nivel")
    points_to_next_level: int = Field(default=100, ge=0, description="Puntos para el siguiente nivel")
    
    # Estadísticas de actividad
    days_active: int = Field(default=0, ge=0, description="Días activos totales")
    atoms_completed: int = Field(default=0, ge=0, description="Átomos completados")
    questions_answered: int = Field(default=0, ge=0, description="Preguntas respondidas")
    correct_answers: int = Field(default=0, ge=0, description="Respuestas correctas")
    
    # Rachas
    current_daily_streak: int = Field(default=0, ge=0, description="Racha diaria actual")
    longest_daily_streak: int = Field(default=0, ge=0, description="Racha diaria más larga")
    current_weekly_streak: int = Field(default=0, ge=0, description="Racha semanal actual")
    
    # Fechas importantes
    first_activity: Optional[datetime] = Field(None, description="Primera actividad")
    last_activity: Optional[datetime] = Field(None, description="Última actividad")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class Challenge(BaseModel):
    """Modelo para desafíos"""
    id: str = Field(..., description="ID único del desafío")
    name: str = Field(..., description="Nombre del desafío")
    description: str = Field(..., description="Descripción del desafío")
    type: ChallengeType = Field(..., description="Tipo de desafío")
    difficulty: str = Field(..., description="Dificultad del desafío")
    
    # Objetivo y criterios
    target_value: int = Field(..., ge=1, description="Valor objetivo")
    target_metric: str = Field(..., description="Métrica objetivo (atoms, points, etc.)")
    
    # Recompensas
    points_reward: int = Field(..., ge=0, description="Puntos de recompensa")
    achievement_reward: Optional[str] = Field(None, description="Logro de recompensa")
    
    # Timing
    duration_days: int = Field(..., ge=1, description="Duración en días")
    start_date: Optional[date] = Field(None, description="Fecha de inicio")
    end_date: Optional[date] = Field(None, description="Fecha de fin")
    
    # Metadata
    is_active: bool = Field(default=True, description="Si está activo")
    is_global: bool = Field(default=False, description="Si es global para todos")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class UserChallenge(BaseModel):
    """Desafío asignado a un usuario"""
    user_id: str = Field(..., description="ID del usuario")
    challenge_id: str = Field(..., description="ID del desafío")
    challenge: Challenge = Field(..., description="Datos del desafío")
    
    # Progreso
    current_value: int = Field(default=0, ge=0, description="Valor actual")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=1.0, description="Porcentaje de progreso")
    is_completed: bool = Field(default=False, description="Si está completado")
    completed_at: Optional[datetime] = Field(None, description="Fecha de completado")
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Fecha de expiración")
    
    class Config:
        from_attributes = True

class Notification(BaseModel):
    """Modelo para notificaciones"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único")
    user_id: str = Field(..., description="ID del usuario")
    type: NotificationType = Field(..., description="Tipo de notificación")
    
    # Contenido
    title: str = Field(..., description="Título de la notificación")
    message: str = Field(..., description="Mensaje de la notificación")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")
    
    # Estado
    is_read: bool = Field(default=False, description="Si fue leída")
    is_sent: bool = Field(default=False, description="Si fue enviada")
    
    # Timing
    scheduled_for: Optional[datetime] = Field(None, description="Programada para")
    sent_at: Optional[datetime] = Field(None, description="Enviada en")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


# ===== REQUESTS =====

class PointsEventRequest(BaseModel):
    """Request para registrar un evento de puntos"""
    user_id: str = Field(..., description="ID del usuario")
    event_type: str = Field(..., description="Tipo de evento")
    points: int = Field(..., ge=0, description="Puntos a otorgar")
    difficulty: Optional[str] = Field(None, description="Dificultad del contenido")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional")

class ActivityEventRequest(BaseModel):
    """Request para registrar actividad del usuario"""
    user_id: str = Field(..., description="ID del usuario")
    activity_type: str = Field(..., description="Tipo de actividad")
    atom_id: Optional[str] = Field(None, description="ID del átomo")
    question_id: Optional[str] = Field(None, description="ID de la pregunta")
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score obtenido")
    time_spent: Optional[int] = Field(None, ge=0, description="Tiempo gastado en segundos")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional")

class CreateChallengeRequest(BaseModel):
    """Request para crear un desafío"""
    name: str = Field(..., description="Nombre del desafío")
    description: str = Field(..., description="Descripción del desafío")
    type: ChallengeType = Field(..., description="Tipo de desafío")
    difficulty: str = Field(..., description="Dificultad")
    target_value: int = Field(..., ge=1, description="Valor objetivo")
    target_metric: str = Field(..., description="Métrica objetivo")
    points_reward: int = Field(..., ge=0, description="Puntos de recompensa")
    duration_days: int = Field(..., ge=1, le=30, description="Duración en días")
    is_global: bool = Field(default=False, description="Si es global")

class SendNotificationRequest(BaseModel):
    """Request para enviar notificación"""
    user_id: str = Field(..., description="ID del usuario")
    type: NotificationType = Field(..., description="Tipo de notificación")
    title: str = Field(..., description="Título")
    message: str = Field(..., description="Mensaje")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")
    scheduled_for: Optional[datetime] = Field(None, description="Programar para")


# ===== RESPONSES =====

class PointsEventResponse(BaseModel):
    """Response para evento de puntos"""
    success: bool = Field(..., description="Si fue exitoso")
    points_awarded: int = Field(..., description="Puntos otorgados")
    total_points: int = Field(..., description="Puntos totales del usuario")
    level_up: bool = Field(default=False, description="Si subió de nivel")
    new_level: Optional[UserLevel] = Field(None, description="Nuevo nivel si subió")
    achievements_unlocked: List[Achievement] = Field(default_factory=list, description="Logros desbloqueados")

class LeaderboardEntry(BaseModel):
    """Entrada en leaderboard"""
    user_id: str = Field(..., description="ID del usuario")
    username: Optional[str] = Field(None, description="Nombre de usuario")
    points: int = Field(..., description="Puntos")
    level: UserLevel = Field(..., description="Nivel")
    position: int = Field(..., description="Posición en el ranking")

class LeaderboardResponse(BaseModel):
    """Response del leaderboard"""
    type: str = Field(..., description="Tipo de leaderboard")
    entries: List[LeaderboardEntry] = Field(..., description="Entradas")
    user_position: Optional[int] = Field(None, description="Posición del usuario solicitante")
    total_users: int = Field(..., description="Total de usuarios")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EngagementAnalytics(BaseModel):
    """Analytics de engagement del usuario"""
    user_id: str = Field(..., description="ID del usuario")
    engagement_score: float = Field(..., ge=0.0, le=1.0, description="Score de engagement")
    churn_risk: float = Field(..., ge=0.0, le=1.0, description="Riesgo de abandono")
    predicted_activity: str = Field(..., description="Actividad predicha")
    recommendations: List[str] = Field(default_factory=list, description="Recomendaciones")
    last_activity: Optional[datetime] = Field(None, description="Última actividad")
    activity_trend: str = Field(..., description="Tendencia de actividad")

class HealthResponse(BaseModel):
    """Response de health check"""
    status: str = Field(..., description="Estado del servicio")
    service: str = Field(..., description="Nombre del servicio")
    version: str = Field(..., description="Versión")
    features: Dict[str, bool] = Field(..., description="Features habilitadas") 