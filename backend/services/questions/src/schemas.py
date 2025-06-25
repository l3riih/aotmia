"""
Esquemas Pydantic para el Servicio Agéntico de Generación de Preguntas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid

class QuestionType(str, Enum):
    """Tipos de preguntas que se pueden generar"""
    OPEN_ENDED = "open_ended"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"

class DifficultyLevel(str, Enum):
    """Niveles de dificultad para las preguntas"""
    BASICO = "básico"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"

class Question(BaseModel):
    """Modelo base para una pregunta generada"""
    question_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    atom_id: str
    question_text: str
    question_type: QuestionType
    difficulty_level: DifficultyLevel
    options: Optional[List[Dict[str, Any]]] = None  # Para opción múltiple
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    author_agent_id: str = "AtomiaQuestioner-v1"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    class Config:
        from_attributes = True

class QuestionGenerationRequest(BaseModel):
    """Request para generar una o más preguntas para un átomo"""
    atom_id: str = Field(..., description="ID del átomo de aprendizaje")
    atom_content: str = Field(..., description="Contenido del átomo")
    question_types: List[QuestionType] = Field(
        [QuestionType.OPEN_ENDED],
        description="Tipos de preguntas a generar"
    )
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIO
    num_questions: int = Field(1, ge=1, le=5)
    user_id: Optional[str] = None

class GeneratedQuestion(BaseModel):
    """Sub-modelo para la respuesta de una pregunta generada"""
    question_text: str
    question_type: QuestionType
    options: Optional[List[Dict[str, Any]]] = None
    correct_answer: str
    explanation: str

class QuestionGenerationResponse(BaseModel):
    """Respuesta del servicio con las preguntas generadas"""
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    atom_id: str
    generated_questions: List[GeneratedQuestion]
    agent_metadata: Dict[str, Any] = Field(default_factory=dict) 