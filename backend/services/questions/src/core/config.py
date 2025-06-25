"""
Configuración del Servicio Agéntico de Generación de Preguntas
"""
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configuración del servicio de preguntas"""
    
    # Servicio
    SERVICE_NAME: str = "questions"
    SERVICE_PORT: int = Field(8005, env="SERVICE_PORT")
    
    # Base de datos
    DATABASE_URL: str = Field(
        "postgresql://user:password@localhost/atomia_questions",
        description="URL de la base de datos PostgreSQL para preguntas"
    )
    
    # LLM Orchestrator
    LLM_ORCHESTRATOR_URL: str = Field(
        "http://localhost:8002",
        description="URL del orquestrador agéntico"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 