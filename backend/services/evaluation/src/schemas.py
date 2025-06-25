"""
Esquemas Pydantic para el Servicio Agéntico de Evaluación
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class DifficultyLevel(str, Enum):
    """Niveles de dificultad para evaluaciones"""
    BASICO = "básico"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"


class EvaluationType(str, Enum):
    """Tipos de evaluación soportados"""
    OPEN_ENDED = "open_ended"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    PRACTICAL = "practical"


class EvaluationContext(BaseModel):
    """Contexto adicional para la evaluación"""
    previous_attempts: Optional[int] = 0
    learning_path: Optional[str] = None
    time_spent_seconds: Optional[int] = None
    atom_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=lambda: {})


class EvaluationRequest(BaseModel):
    """Request para evaluación agéntica de respuesta"""
    question_id: str = Field(..., description="ID de la pregunta")
    question_text: str = Field(..., description="Texto completo de la pregunta")
    student_answer: str = Field(..., description="Respuesta del estudiante")
    expected_concepts: List[str] = Field(
        default_factory=list,
        description="Conceptos esperados en la respuesta"
    )
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIO
    evaluation_type: EvaluationType = EvaluationType.OPEN_ENDED
    user_id: str = Field(..., description="ID del estudiante")
    context: Optional[EvaluationContext] = None
    rubric: Optional[Dict[str, Any]] = Field(
        None,
        description="Rúbrica específica de evaluación"
    )
    
    @field_validator('student_answer')
    def validate_answer_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("La respuesta del estudiante no puede estar vacía")
        return v.strip()


class FeedbackDetail(BaseModel):
    """Detalle estructurado del feedback"""
    strengths: List[str] = Field(
        default_factory=list,
        description="Aspectos positivos identificados"
    )
    improvements: List[str] = Field(
        default_factory=list,
        description="Áreas de mejora"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Sugerencias específicas de estudio"
    )
    examples: Optional[List[str]] = Field(
        None,
        description="Ejemplos para clarificar conceptos"
    )


class Misconception(BaseModel):
    """Concepto erróneo detectado"""
    concept: str = Field(..., description="Concepto mal entendido")
    description: str = Field(..., description="Descripción del error")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severidad del error")
    correction: str = Field(..., description="Corrección sugerida")


class LearningProgress(BaseModel):
    """Progreso de aprendizaje del estudiante"""
    current_mastery: float = Field(
        ..., ge=0.0, le=1.0,
        description="Nivel actual de dominio del concepto"
    )
    improvement: float = Field(
        ..., ge=-1.0, le=1.0,
        description="Mejora desde la última evaluación"
    )
    trend: str = Field(
        ..., 
        description="Tendencia: improving, stable, declining"
    )
    confidence_level: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confianza del agente en la evaluación"
    )


class AgentMetadata(BaseModel):
    """Metadatos del proceso de razonamiento agéntico"""
    reasoning_steps: List[str] = Field(
        ...,
        description="Pasos del workflow Plan-Execute-Observe-Reflect"
    )
    tools_used: List[str] = Field(
        ...,
        description="Herramientas educativas utilizadas"
    )
    iterations: int = Field(..., ge=1, description="Iteraciones del agente")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confianza en la evaluación"
    )
    reasoning_quality: float = Field(
        ..., ge=0.0, le=1.0,
        description="Calidad del razonamiento"
    )
    processing_time_ms: int = Field(..., description="Tiempo de procesamiento")


class EvaluationResponse(BaseModel):
    """Respuesta de evaluación agéntica"""
    evaluation_id: str = Field(..., description="ID único de la evaluación")
    score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Puntuación normalizada"
    )
    feedback: FeedbackDetail
    misconceptions_detected: List[Misconception] = Field(
        default_factory=list,
        description="Conceptos erróneos identificados"
    )
    learning_progress: LearningProgress
    agent_metadata: AgentMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Campos adicionales para análisis
    key_concepts_understood: List[str] = Field(
        default_factory=list,
        description="Conceptos clave que el estudiante comprende"
    )
    next_recommended_topics: List[str] = Field(
        default_factory=list,
        description="Temas recomendados para estudiar"
    )
    estimated_time_to_mastery: Optional[int] = Field(
        None,
        description="Tiempo estimado en minutos para dominar el concepto"
    )


class BatchEvaluationRequest(BaseModel):
    """Request para evaluación de múltiples respuestas"""
    evaluations: List[EvaluationRequest]
    batch_context: Optional[Dict[str, Any]] = None


class BatchEvaluationResponse(BaseModel):
    """Respuesta de evaluación por lotes"""
    batch_id: str
    evaluations: List[EvaluationResponse]
    summary: Dict[str, Any]
    processing_time_ms: int


class HealthResponse(BaseModel):
    """Respuesta del health check"""
    status: str = "healthy"
    service: str = "evaluation"
    version: str = "2.0.0"
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "agentic_reasoning": True,
        "misconception_detection": True,
        "adaptive_feedback": True,
        "batch_evaluation": True
    })


class AgenticCapabilitiesResponse(BaseModel):
    """Respuesta sobre capacidades agénticas del servicio"""
    service: str = "evaluation"
    workflow: str = "Plan-Execute-Observe-Reflect"
    tools_available: List[str] = Field(default_factory=lambda: [
        "analyze_student_response",
        "detect_misconceptions",
        "generate_constructive_feedback",
        "calculate_learning_progress"
    ])
    supported_evaluation_types: List[str] = Field(
        default_factory=lambda: [e.value for e in EvaluationType]
    )
    pedagogical_principles: List[str] = Field(default_factory=lambda: [
        "Evaluación Formativa",
        "Scaffolding Adaptativo",
        "Zona de Desarrollo Próximo",
        "Metacognición"
    ])
    llm_integration: bool = True
    max_reasoning_iterations: int = 10 