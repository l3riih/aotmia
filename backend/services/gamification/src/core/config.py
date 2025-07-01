"""
Configuración del Servicio Agéntico de Gamificación
"""

import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuración del servicio de gamificación"""
    
    # Servicio
    SERVICE_NAME: str = "gamification"
    SERVICE_VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8006
    WORKERS: int = 1
    RELOAD: bool = False
    
    # Base de Datos PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "atomia_dev"
    POSTGRES_USER: str = "atomia_user"
    POSTGRES_PASSWORD: str = "atomia_password"
    
    @property
    def postgres_url(self) -> str:
        """Construye la URL de PostgreSQL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2  # DB separada para gamificación
    REDIS_TTL_SECONDS: int = 3600
    
    @property
    def redis_url(self) -> str:
        """Construye la URL de Redis"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Servicios dependientes
    LLM_ORCHESTRATOR_URL: str = "http://localhost:8002"
    EVALUATION_SERVICE_URL: str = "http://localhost:8003"
    PLANNING_SERVICE_URL: str = "http://localhost:8004"
    
    # Configuración de Gamificación
    POINTS_MULTIPLIERS: Dict[str, float] = Field(default_factory=lambda: {
        "basic": 1.0,
        "intermediate": 1.5,
        "advanced": 2.0
    })
    
    STREAK_THRESHOLDS: Dict[str, int] = Field(default_factory=lambda: {
        "daily_min": 3,
        "weekly_min": 2,
        "monthly_min": 8
    })
    
    LEVEL_PROGRESSION: Dict[str, int] = Field(default_factory=lambda: {
        "beginner": 0,
        "explorer": 100,
        "scholar": 500,
        "expert": 1500,
        "master": 3000,
        "sage": 6000
    })
    
    # Configuración de Logros
    ACHIEVEMENT_TYPES: List[str] = Field(default_factory=lambda: [
        "progress",
        "consistency",
        "mastery",
        "social",
        "special",
        "hidden"
    ])
    
    # Configuración de Notificaciones
    NOTIFICATION_WINDOWS: Dict[str, int] = Field(default_factory=lambda: {
        "optimal_study_time": 30,  # minutos antes/después
        "streak_reminder": 60,     # minutos antes de perder racha
        "comeback_delay": 1440     # minutos (24h) para notificación de regreso
    })
    
    # Configuración de Desafíos
    CHALLENGE_DURATION_DAYS: Dict[str, int] = Field(default_factory=lambda: {
        "daily": 1,
        "weekly": 7,
        "special": 3
    })
    
    # Algoritmos de Engagement
    INTERMITTENT_REWARD_RATE: float = 0.3  # 30% probabilidad de recompensa extra
    FLOW_STATE_THRESHOLD: float = 0.8      # Umbral para detectar estado de flujo
    CHURN_PREDICTION_THRESHOLD: float = 0.7 # Umbral para predicción de abandono
    
    # Configuración de Leaderboards
    LEADERBOARD_SIZES: Dict[str, int] = Field(default_factory=lambda: {
        "global": 100,
        "friends": 20,
        "weekly": 50
    })
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5555"
    ])
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Feature Flags
    ENABLE_SOCIAL_FEATURES: bool = True
    ENABLE_PUSH_NOTIFICATIONS: bool = True
    ENABLE_ADAPTIVE_CHALLENGES: bool = True
    ENABLE_BEHAVIORAL_ANALYTICS: bool = True
    ENABLE_AI_RECOMMENDATIONS: bool = True
    
    # Límites y Seguridad
    MAX_POINTS_PER_DAY: int = 1000
    MAX_ACHIEVEMENTS_PER_USER: int = 500
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instancia global
_settings = None

def get_settings() -> Settings:
    """Obtiene la instancia singleton de configuración"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 