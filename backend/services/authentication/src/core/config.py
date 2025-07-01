"""
Configuración del Servicio de Autenticación
"""

import os
import secrets
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Configuración del servicio de autenticación"""
    
    # Servicio
    SERVICE_NAME: str = "authentication"
    SERVICE_VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8007
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
    
    # Redis Cache para sesiones
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 3  # DB separada para autenticación
    REDIS_TTL_SECONDS: int = 86400  # 24 horas
    
    @property
    def redis_url(self) -> str:
        """Construye la URL de Redis"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Clave secreta para JWT"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Claves RSA para firma (opcional, para usar RS256)
    JWT_PRIVATE_KEY: Optional[str] = None
    JWT_PUBLIC_KEY: Optional[str] = None
    
    # Password Configuration
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_HASH_ROUNDS: int = 12
    
    # Session Configuration
    MAX_SESSIONS_PER_USER: int = 5
    SESSION_TIMEOUT_MINUTES: int = 60 * 24  # 24 horas
    REMEMBER_ME_DAYS: int = 30
    
    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@atomia.edu"
    
    # Verification
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 2
    
    # Rate Limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_MINUTES: int = 15
    RATE_LIMIT_REGISTRATION_PER_IP_HOUR: int = 3
    RATE_LIMIT_PASSWORD_RESET_PER_EMAIL_HOUR: int = 2
    
    # Security
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://localhost:5555"
    ])
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5555"
    ])
    
    # Roles y Permisos
    DEFAULT_USER_ROLE: str = "student"
    ADMIN_EMAIL: Optional[str] = None
    
    # Feature Flags
    ENABLE_EMAIL_VERIFICATION: bool = True
    ENABLE_PASSWORD_RESET: bool = True
    ENABLE_REMEMBER_ME: bool = True
    ENABLE_MULTI_DEVICE_SESSIONS: bool = True
    ENABLE_SOCIAL_LOGIN: bool = False  # Para futuro
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Servicios dependientes
    GAMIFICATION_SERVICE_URL: str = "http://localhost:8006"
    
    # Validaciones
    @field_validator('JWT_SECRET_KEY')
    @classmethod
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY debe tener al menos 32 caracteres')
        return v
    
    @field_validator('PASSWORD_MIN_LENGTH')
    @classmethod
    def validate_password_length(cls, v):
        if v < 6:
            raise ValueError('PASSWORD_MIN_LENGTH debe ser al menos 6')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
    def get_password_policy(self) -> dict:
        """Obtiene la política de contraseñas"""
        return {
            "min_length": self.PASSWORD_MIN_LENGTH,
            "require_uppercase": self.PASSWORD_REQUIRE_UPPERCASE,
            "require_lowercase": self.PASSWORD_REQUIRE_LOWERCASE,
            "require_digits": self.PASSWORD_REQUIRE_DIGITS,
            "require_special": self.PASSWORD_REQUIRE_SPECIAL
        }
    
    def get_rate_limits(self) -> dict:
        """Obtiene configuración de rate limits"""
        return {
            "login_attempts": self.RATE_LIMIT_LOGIN_ATTEMPTS,
            "login_window_minutes": self.RATE_LIMIT_LOGIN_WINDOW_MINUTES,
            "registration_per_ip_hour": self.RATE_LIMIT_REGISTRATION_PER_IP_HOUR,
            "password_reset_per_email_hour": self.RATE_LIMIT_PASSWORD_RESET_PER_EMAIL_HOUR
        }


# Instancia global
_settings = None

def get_settings() -> Settings:
    """Obtiene la instancia singleton de configuración"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 