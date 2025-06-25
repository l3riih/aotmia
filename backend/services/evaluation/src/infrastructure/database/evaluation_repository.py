"""
Repositorio para persistencia de evaluaciones en PostgreSQL.
Maneja el almacenamiento y recuperación de evaluaciones educativas.
"""

import asyncpg
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
import logging
from ...core.config import get_settings
from ...core.logging import get_logger
from ...schemas import (
    EvaluationRequest,
    EvaluationResponse,
    FeedbackDetail,
    LearningProgress,
    AgentMetadata,
    Misconception
)
from sqlalchemy import MetaData, Table, Column, String, Float, DateTime, JSON, create_engine, inspect, PrimaryKeyConstraint
from sqlalchemy.ext.asyncio import create_async_engine
import uuid
import sqlalchemy as sa

logger = get_logger(__name__)
settings = get_settings()

# Definición de la tabla de evaluaciones con SQLAlchemy
metadata = sa.MetaData()

evaluations = sa.Table(
    'evaluations', metadata,
    sa.Column('evaluation_id', sa.String, primary_key=True),
    sa.Column('user_id', sa.String, nullable=False, index=True),
    sa.Column('question_id', sa.String, nullable=False, index=True),
    sa.Column('score', sa.Float, nullable=False),
    sa.Column('feedback', sa.JSON, nullable=False),
    sa.Column('misconceptions_detected', sa.JSON, default=[]),
    sa.Column('learning_progress', sa.JSON, nullable=False),
    sa.Column('agent_metadata', sa.JSON, nullable=False),
    sa.Column('key_concepts_understood', sa.JSON, default=[]),
    sa.Column('next_recommended_topics', sa.JSON, default=[]),
    sa.Column('estimated_time_to_mastery', sa.Integer, default=60),
    sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
)

class EvaluationRepository:
    """
    Gestiona la persistencia de las evaluaciones de estudiantes.
    """
    def __init__(self, database_url: str, pool_size: int = 10):
        if not database_url:
            raise ValueError("database_url cannot be empty")
        self._database_url = database_url  # Para SQLAlchemy
        # Para asyncpg necesitamos un DSN sin el sufijo +asyncpg
        if database_url.startswith("postgresql+asyncpg://"):
            self._dsn_asyncpg = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        else:
            self._dsn_asyncpg = database_url
        self._pool_size = pool_size
        self._engine = create_async_engine(database_url, pool_size=pool_size)
        self._db_pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Inicializa la conexión a la base de datos y crea la tabla si no existe."""
        if self._db_pool:
            return
        try:
            self._db_pool = await asyncpg.create_pool(
                dsn=self._dsn_asyncpg,
                min_size=1, # Start with 1 connection
                max_size=self._pool_size
            )
            async with self._engine.begin() as conn:
                await conn.run_sync(metadata.create_all)
            logger.info("Database pool connected and table 'evaluations' verified.")
        except Exception as e:
            logger.error("Failed to connect to the database", error=str(e))
            self._db_pool = None
            raise
    
    async def disconnect(self):
        """Cierra la conexión a la base de datos."""
        if self._db_pool:
            await self._db_pool.close()
            self._db_pool = None
            logger.info("Database pool disconnected.")

    async def save_evaluation(self, evaluation: EvaluationResponse, user_id: str, question_id: str) -> str:
        """Guarda una nueva evaluación en la base de datos."""
        if self._db_pool is None:
            await self.connect()
        
        async with self._engine.begin() as conn:
            query = evaluations.insert().values(
                evaluation_id=evaluation.evaluation_id,
                user_id=user_id,
                question_id=question_id,
                score=evaluation.score,
                feedback=evaluation.feedback.dict(),
                misconceptions_detected=[m.dict() for m in evaluation.misconceptions_detected],
                learning_progress=evaluation.learning_progress.dict(),
                agent_metadata=evaluation.agent_metadata.dict(),
                key_concepts_understood=evaluation.key_concepts_understood,
                next_recommended_topics=evaluation.next_recommended_topics,
                estimated_time_to_mastery=evaluation.estimated_time_to_mastery,
            )
            await conn.execute(query)
            logger.info("Saved evaluation to DB", evaluation_id=evaluation.evaluation_id)
            return evaluation.evaluation_id
    
    async def get_evaluation_by_id(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una evaluación por su ID."""
        if self._db_pool is None:
            await self.connect()

        async with self._engine.begin() as conn:
            query = evaluations.select().where(evaluations.c.evaluation_id == evaluation_id)
            result = await conn.execute(query)
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def get_user_evaluations(self, user_id: str, question_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene las últimas evaluaciones de un usuario (opcionalmente por pregunta)."""
        if self._db_pool is None:
            await self.connect()
        async with self._engine.begin() as conn:
            query = evaluations.select().where(evaluations.c.user_id == user_id)
            if question_id:
                query = query.where(evaluations.c.question_id == question_id)
            query = query.order_by(sa.desc(evaluations.c.created_at)).limit(limit)
            result = await conn.execute(query)
            rows = result.fetchall()
            return [dict(r._mapping) for r in rows]

    async def update_user_progress(self, user_id: str, atom_id: str, mastery_level: float):
        # Esta lógica puede ser más compleja y requerir su propia tabla,
        # por ahora es un placeholder.
        logger.info("Updating user progress (placeholder)", user_id=user_id, atom_id=atom_id, mastery=mastery_level)
        pass

# Instancia singleton
_evaluation_repository: Optional[EvaluationRepository] = None

async def get_repository() -> EvaluationRepository:
    """Función de dependencia para obtener la instancia del repositorio."""
    global _evaluation_repository
    if _evaluation_repository is None:
        db_url = settings.DATABASE_URL
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set.")
        _evaluation_repository = EvaluationRepository(db_url)
        await _evaluation_repository.connect()
    return _evaluation_repository 