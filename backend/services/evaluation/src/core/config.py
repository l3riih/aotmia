"""
Configuración del Servicio Agéntico de Evaluación
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración del servicio"""
    
    # Servicio
    SERVICE_NAME: str = "evaluation"
    SERVICE_VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    WORKERS: int = 1
    RELOAD: bool = False
    
    # LLM Orchestrator
    LLM_ORCHESTRATOR_URL: str = "http://localhost:8002"
    LLM_ORCHESTRATOR_TIMEOUT: int = 30
    LLM_ORCHESTRATOR_MAX_RETRIES: int = 3
    
    # Base de Datos
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 10
    DATABASE_POOL_MAX_OVERFLOW: int = 20
    
    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "atomia_dev"
    POSTGRES_USER: str = "atomia_user"
    POSTGRES_PASSWORD: str = "atomia_password"
    
    @property
    def postgres_url(self) -> str:
        """Construye la URL de PostgreSQL a partir de los parámetros"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None
    REDIS_TTL_SECONDS: int = 3600  # 1 hora
    ENABLE_CACHE: bool = True
    
    @property
    def redis_url_computed(self) -> str:
        """Construye la URL de Redis a partir de los parámetros"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    # Configuración Agéntica
    MAX_REASONING_ITERATIONS: int = 10
    MIN_REASONING_CONFIDENCE: float = 0.7
    EVALUATION_CONFIDENCE_THRESHOLD: float = 0.8
    ENABLE_MISCONCEPTION_DETECTION: bool = True
    ENABLE_ADAPTIVE_FEEDBACK: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json o console
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # Métricas
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9003
    
    # Development
    DEBUG: bool = False
    TESTING: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instancia global de configuración
settings = Settings() 

def get_settings() -> Settings:
    """Obtiene la instancia de configuración"""
    return settings 