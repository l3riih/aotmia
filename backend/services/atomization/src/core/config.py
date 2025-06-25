"""
Configuración del servicio de atomización agéntico
"""

import os
from typing import List
from functools import lru_cache


class Settings:
    """Configuración del servicio de atomización"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Atomia Atomization Service"
    VERSION: str = "2.0.0"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8000",
        "http://localhost:5555" # Origen para el frontend de Flutter Web
    ]
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "atomia_atomization")
    
    # LLM Orchestrator (Sistema Agéntico)
    LLM_ORCHESTRATOR_URL: str = os.getenv("LLM_ORCHESTRATOR_URL", "http://localhost:8002")
    
    # Neo4j Graph Database
    NEO4J_URI: str = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "atomia-dev-pass")
    
    # Redis (Cache)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Cache settings
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # Agent settings
    AGENT_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_TIMEOUT_SECONDS", "60"))
    AGENT_MAX_RETRIES: int = int(os.getenv("AGENT_MAX_RETRIES", "3"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Development
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 