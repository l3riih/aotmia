from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DifficultyLevel(str, Enum):
    """Niveles de dificultad para átomos de aprendizaje"""
    BASICO = "básico"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"


class LearningAtomBase(BaseModel):
    title: str
    content: str
    difficulty_level: DifficultyLevel
    prerequisites: List[UUID] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    estimated_time_minutes: Optional[int] = None
    tags: List[str] = Field(default_factory=list)


class LearningAtomCreate(LearningAtomBase):
    pass


class LearningAtomRead(LearningAtomBase):
    id: UUID
    created_at: datetime
    version: int = 1
    status: str = "active"
    
    # Metadatos agénticos
    created_by_agent: bool = False
    agent_reasoning_quality: Optional[float] = None
    tools_used_count: Optional[int] = None
    iteration_count: Optional[int] = None

    class Config:
        from_attributes = True


class AtomizationRequest(BaseModel):
    """Request para atomización agéntica de contenido"""
    content: str = Field(..., description="Contenido educativo a atomizar")
    objectives: Optional[str] = Field(None, description="Objetivos de aprendizaje del curso")
    difficulty_level: str = Field("intermedio", description="Nivel de dificultad: básico, intermedio, avanzado")
    user_id: Optional[str] = Field(None, description="ID del usuario para contexto personalizado")
    context: Optional[Dict[str, Any]] = Field(default_factory=lambda: {}, description="Contexto adicional")


class AgenticAtomizationResponse(BaseModel):
    """Respuesta de atomización agéntica"""
    atoms: List[LearningAtomRead]
    agent_metadata: Dict[str, Any] = Field(default_factory=lambda: {})
    reasoning_steps: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    iterations: int = 0
    quality_score: float = 0.0


class AtomizationTaskRequest(BaseModel):
    """Request para el sistema agéntico"""
    query: str
    user_id: Optional[str] = None
    task_type: str = "ATOMIZATION"
    context: Dict[str, Any] = Field(default_factory=lambda: {}) 