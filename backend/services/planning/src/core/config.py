"""
Configuración del Servicio Agéntico de Planificación
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, Any, Optional


class Settings(BaseSettings):
    """Configuración del servicio de planificación"""
    
    # Servicio
    SERVICE_NAME: str = "planning"
    SERVICE_VERSION: str = "2.0.0"
    SERVICE_PORT: int = Field(8004, env="SERVICE_PORT")
    
    # Agéntico
    LLM_ORCHESTRATOR_URL: str = Field(
        "http://localhost:8002",
        description="URL del orquestador agéntico"
    )
    
    # Servicios dependientes
    ATOMIZATION_SERVICE_URL: str = Field(
        "http://localhost:8001",
        description="URL del servicio de atomización"
    )
    EVALUATION_SERVICE_URL: str = Field(
        "http://localhost:8003", 
        description="URL del servicio de evaluación"
    )
    
    # Base de datos
    DATABASE_URL: str = Field(
        "postgresql://user:password@localhost/atomia_planning",
        description="URL de la base de datos PostgreSQL"
    )
    
    NEO4J_URI: str = Field(
        "neo4j://localhost:7687",
        description="URI para la base de datos de grafos Neo4j"
    )
    NEO4J_USER: str = Field("neo4j", description="Usuario para Neo4j")
    NEO4J_PASSWORD: str = Field("password", description="Contraseña para Neo4j")
    
    # Cache
    REDIS_URL: str = Field("redis://localhost:6379/1", env="REDIS_URL")
    CACHE_TTL_SECONDS: int = Field(3600, description="TTL del cache en segundos")
    
    # Algoritmos pedagógicos
    FSRS_DEFAULT_PARAMETERS: Dict[str, Any] = Field(
        default_factory=lambda: {
            "w": [0.4, 0.6, 2.4, 5.8],  # Pesos por defecto FSRS
            "request_retention": 0.9,    # Retención objetivo
            "maximum_interval": 365      # Intervalo máximo en días
        }
    )
    
    ZDP_DIFFICULTY_WINDOW: float = Field(
        0.2,
        description="Ventana de dificultad para Zona de Desarrollo Próximo"
    )
    
    EXPLORATION_EXPLOITATION_RATIO: float = Field(
        0.3,
        description="Ratio de exploración vs explotación (0.3 = 30% exploración)"
    )
    
    # Configuración agéntica
    MAX_PLANNING_ITERATIONS: int = Field(
        15,
        description="Máximo de iteraciones del agente planificador"
    )
    MIN_CONFIDENCE_THRESHOLD: float = Field(
        0.75,
        description="Umbral mínimo de confianza para planes"
    )
    ENABLE_ADAPTIVE_REPLANNING: bool = Field(
        True,
        description="Habilitar replanificación adaptativa automática"
    )
    ENABLE_PREDICTIVE_MODELING: bool = Field(
        True,
        description="Habilitar modelado predictivo de resultados"
    )
    
    # Planificación
    DEFAULT_SESSION_DURATION_MINUTES: int = Field(
        30,
        description="Duración por defecto de sesiones de estudio"
    )
    MAX_DAILY_STUDY_HOURS: int = Field(
        4,
        description="Máximo de horas de estudio diarias recomendadas"
    )
    REVIEW_TO_NEW_CONTENT_RATIO: float = Field(
        0.3,
        description="Ratio de contenido de repaso vs nuevo (0.3 = 30% repaso)"
    )
    
    # Recomendaciones
    MAX_RECOMMENDATIONS_PER_REQUEST: int = Field(
        5,
        description="Máximo de recomendaciones por solicitud"
    )
    RECOMMENDATION_CACHE_MINUTES: int = Field(
        30,
        description="Minutos de cache para recomendaciones"
    )
    
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("json", env="LOG_FORMAT")
    
    # Monitoreo
    ENABLE_METRICS: bool = Field(True, description="Habilitar métricas Prometheus")
    METRICS_PORT: int = Field(9094, description="Puerto para métricas")
    
    # Feature flags
    ENABLE_MULTI_ALGORITHM_PLANNING: bool = Field(
        True,
        description="Usar múltiples algoritmos en paralelo"
    )
    ENABLE_SOCIAL_LEARNING_FEATURES: bool = Field(
        False,
        description="Habilitar características de aprendizaje social"
    )
    ENABLE_GAMIFICATION_INTEGRATION: bool = Field(
        True,
        description="Integrar con servicio de gamificación"
    )
    
    # Límites de seguridad
    MAX_ATOMS_PER_PLAN: int = Field(
        500,
        description="Máximo de átomos en un plan"
    )
    MAX_PLAN_DURATION_DAYS: int = Field(
        365,
        description="Duración máxima de un plan en días"
    )
    
    # Performance
    REQUEST_TIMEOUT_SECONDS: int = Field(30, description="Timeout para requests HTTP")
    DB_CONNECTION_POOL_SIZE: int = Field(10, description="Tamaño del pool de conexiones DB")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def get_fsrs_params(self) -> Dict[str, Any]:
        """Obtiene parámetros FSRS con valores por defecto"""
        return self.FSRS_DEFAULT_PARAMETERS.copy()
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Obtiene todos los feature flags activos"""
        return {
            "multi_algorithm": self.ENABLE_MULTI_ALGORITHM_PLANNING,
            "social_learning": self.ENABLE_SOCIAL_LEARNING_FEATURES,
            "gamification": self.ENABLE_GAMIFICATION_INTEGRATION,
            "adaptive_replanning": self.ENABLE_ADAPTIVE_REPLANNING,
            "predictive_modeling": self.ENABLE_PREDICTIVE_MODELING
        }
    
    def get_algorithm_config(self) -> Dict[str, Any]:
        """Obtiene configuración de algoritmos pedagógicos"""
        return {
            "fsrs": self.get_fsrs_params(),
            "zdp": {
                "difficulty_window": self.ZDP_DIFFICULTY_WINDOW
            },
            "exploration_exploitation": {
                "ratio": self.EXPLORATION_EXPLOITATION_RATIO
            }
        }


# Instancia global de configuración
settings = Settings() 