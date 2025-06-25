"""
Esquemas Pydantic para el Servicio Agéntico de Planificación
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class DifficultyLevel(str, Enum):
    """Niveles de dificultad"""
    BASICO = "básico"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"


class LearningStyle(str, Enum):
    """Estilos de aprendizaje"""
    VISUAL = "visual"
    AUDITIVO = "auditivo"
    KINESTESICO = "kinestésico"
    LECTOESCRITURA = "lectoescritura"
    MIXTO = "mixto"


class PlanStatus(str, Enum):
    """Estados del plan de aprendizaje"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ADAPTED = "adapted"


class LearningContext(BaseModel):
    """Contexto del estudiante para planificación"""
    current_level: DifficultyLevel = DifficultyLevel.BASICO
    previous_topics: List[str] = Field(default_factory=list)
    learning_style: LearningStyle = LearningStyle.MIXTO
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    available_days_per_week: int = Field(5, ge=1, le=7)
    minutes_per_session: int = Field(30, ge=10, le=180)
    preferred_time: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=lambda: {})


class CreatePlanRequest(BaseModel):
    """Request para crear un plan de aprendizaje"""
    user_id: str = Field(..., description="ID del estudiante")
    learning_goals: List[str] = Field(
        ..., min_items=1,
        description="Objetivos de aprendizaje"
    )
    time_available_hours: float = Field(
        ..., gt=0,
        description="Horas totales disponibles"
    )
    preferred_difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIO
    context: LearningContext
    deadline: Optional[date] = Field(
        None,
        description="Fecha límite para completar objetivos"
    )
    
    @field_validator('learning_goals')
    def validate_goals(cls, v):
        if not all(goal.strip() for goal in v):
            raise ValueError("Los objetivos no pueden estar vacíos")
        return [goal.strip() for goal in v]


class LearningPhase(BaseModel):
    """Fase de aprendizaje dentro del plan"""
    phase_id: int = Field(..., ge=1)
    name: str = Field(..., description="Nombre de la fase")
    atoms: List[str] = Field(..., description="IDs de átomos en esta fase")
    estimated_duration_minutes: int = Field(..., ge=0)
    objectives: List[str] = Field(default_factory=list)
    prerequisites_completed: bool = False
    difficulty_level: DifficultyLevel


class DailySession(BaseModel):
    """Sesión diaria de estudio"""
    day: int = Field(..., ge=1)
    date: Optional[date] = None
    atoms: List[str] = Field(
        ..., 
        description="Átomos nuevos a estudiar"
    )
    review_atoms: List[str] = Field(
        default_factory=list,
        description="Átomos para repasar"
    )
    estimated_time_minutes: int = Field(..., ge=0)
    session_type: str = Field(
        "mixed",
        description="Tipo: new_content, review, mixed"
    )


class LearningPath(BaseModel):
    """Ruta de aprendizaje completa"""
    total_atoms: int = Field(..., ge=0)
    estimated_time_hours: float = Field(..., ge=0)
    difficulty_progression: str = Field(
        ...,
        description="Tipo de progresión: gradual, accelerated, adaptive"
    )
    phases: List[LearningPhase]
    dependency_graph: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Grafo de dependencias entre átomos"
    )


class Schedule(BaseModel):
    """Calendario de estudio"""
    daily_sessions: List[DailySession]
    total_days: int = Field(..., ge=1)
    review_frequency: str = Field(
        "spaced",
        description="Frecuencia de repaso: daily, spaced, adaptive"
    )
    estimated_completion_date: Optional[date] = None


class AgentPlanningMetadata(BaseModel):
    """Metadatos del proceso de planificación agéntica"""
    reasoning_steps: List[str] = Field(
        ...,
        description="Pasos del workflow Plan-Execute-Observe-Reflect"
    )
    tools_used: List[str] = Field(
        ...,
        description="Herramientas utilizadas en la planificación"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confianza en el plan generado"
    )
    algorithms_applied: List[str] = Field(
        ...,
        description="Algoritmos pedagógicos aplicados"
    )
    iterations: int = Field(..., ge=1)
    processing_time_ms: int = Field(..., ge=0)
    adaptability_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Capacidad de adaptación del plan"
    )


class LearningPlanResponse(BaseModel):
    """Respuesta con plan de aprendizaje completo"""
    plan_id: str = Field(..., description="ID único del plan")
    user_id: str
    status: PlanStatus = PlanStatus.DRAFT
    learning_path: LearningPath
    schedule: Schedule
    agent_metadata: AgentPlanningMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Métricas predictivas
    predicted_success_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="Probabilidad de éxito predicha"
    )
    estimated_mastery_level: float = Field(
        ..., ge=0.0, le=1.0,
        description="Nivel de dominio estimado al completar"
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Factores de riesgo identificados"
    )


class UpdatePlanRequest(BaseModel):
    """Request para actualizar un plan basado en progreso"""
    completed_atoms: List[str] = Field(default_factory=list)
    evaluation_results: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Resultados de evaluación por átomo"
    )
    user_feedback: Optional[str] = None
    time_spent_minutes: Dict[str, int] = Field(
        default_factory=dict,
        description="Tiempo real gastado por átomo"
    )
    request_replanning: bool = Field(
        False,
        description="Solicitar replanificación completa"
    )


class AdaptivePlanUpdate(BaseModel):
    """Actualización adaptativa del plan"""
    plan_id: str
    adaptations_made: List[str] = Field(
        ...,
        description="Lista de adaptaciones realizadas"
    )
    new_schedule: Optional[Schedule] = None
    removed_atoms: List[str] = Field(default_factory=list)
    added_atoms: List[str] = Field(default_factory=list)
    difficulty_adjustments: Dict[str, str] = Field(
        default_factory=dict,
        description="Ajustes de dificultad por fase"
    )
    reason: str = Field(..., description="Razón de las adaptaciones")
    confidence: float = Field(..., ge=0.0, le=1.0)


class RecommendationsRequest(BaseModel):
    """Request para obtener recomendaciones"""
    user_id: str
    context: str = Field(
        "current_session",
        description="Contexto: current_session, next_topic, review"
    )
    time_available_minutes: Optional[int] = None
    include_alternatives: bool = True


class LearningRecommendation(BaseModel):
    """Recomendación de aprendizaje"""
    recommendation_id: str
    atom_ids: List[str]
    recommendation_type: str = Field(
        ...,
        description="Tipo: new_content, review, practice, challenge"
    )
    estimated_time_minutes: int
    rationale: str = Field(..., description="Explicación de la recomendación")
    priority: float = Field(..., ge=0.0, le=1.0)
    expected_benefit: str
    prerequisites_met: bool = True


class RecommendationsResponse(BaseModel):
    """Respuesta con recomendaciones adaptativas"""
    user_id: str
    recommendations: List[LearningRecommendation]
    current_mastery_snapshot: Dict[str, float] = Field(
        ...,
        description="Estado actual de dominio por tema"
    )
    suggested_next_steps: List[str]
    agent_reasoning: List[str]


class HealthResponse(BaseModel):
    """Respuesta del health check"""
    status: str = "healthy"
    service: str = "planning"
    version: str = "2.0.0"
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "agentic_reasoning": True,
        "adaptive_planning": True,
        "spaced_repetition": True,
        "predictive_modeling": True,
        "multi_algorithm": True
    })


class AgenticCapabilitiesResponse(BaseModel):
    """Capacidades agénticas del servicio"""
    service: str = "planning"
    workflow: str = "Plan-Execute-Observe-Reflect"
    tools_available: List[str] = Field(default_factory=lambda: [
        "analyze_learning_state",
        "generate_learning_path",
        "optimize_spaced_repetition",
        "predict_learning_outcomes",
        "detect_learning_gaps"
    ])
    algorithms_supported: List[str] = Field(default_factory=lambda: [
        "FSRS",
        "Zona de Desarrollo Próximo",
        "Curva de Aprendizaje",
        "Exploración-Explotación"
    ])
    integration_points: List[str] = Field(default_factory=lambda: [
        "atomization_service",
        "evaluation_service",
        "questions_service",
        "gamification_service"
    ])
    max_planning_iterations: int = 15 