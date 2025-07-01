"""
Repositorio para persistencia de evaluaciones en PostgreSQL.
Maneja el almacenamiento y recuperación de evaluaciones educativas.
"""

from typing import Dict, Any, Optional, List
import asyncio
import structlog
from datetime import datetime
from sqlalchemy import MetaData, Table, Column, String, Float, DateTime, JSON, Integer
from sqlalchemy import insert, update as sa_update, select, delete as sa_delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker as _sm

from ...schemas import EvaluationResponse

logger = structlog.get_logger()

metadata = MetaData()

# Tabla de evaluaciones
evaluations_table = Table(
    "evaluations",
    metadata,
    Column("evaluation_id", String, primary_key=True),
    Column("user_id", String, nullable=False, index=True),
    Column("question_id", String, nullable=False, index=True),
    Column("atom_id", String, nullable=True, index=True),
    Column("score", Float, nullable=False),
    Column("evaluation_data", JSON, nullable=False),  # objeto completo de la evaluación
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Tabla de progreso de usuario
user_progress_table = Table(
    "user_progress",
    metadata,
    Column("user_id", String, primary_key=True),
    Column("atom_id", String, primary_key=True),
    Column("mastery_level", Float, default=0.0),
    Column("total_attempts", Integer, default=0),
    Column("correct_attempts", Integer, default=0),
    Column("last_evaluation_id", String, nullable=True),
    Column("last_updated", DateTime, default=datetime.utcnow),
)

class PostgresEvaluationRepository:
    """
    Repositorio para la gestión de datos de evaluación en PostgreSQL.
    - Guarda evaluaciones de respuestas de usuarios
    - Rastrea el progreso de aprendizaje por átomo
    - Proporciona métricas de rendimiento
    """

    async def _init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    def __init__(self, database_url: str):
        try:
            self.engine: AsyncEngine = create_async_engine(database_url, echo=False, future=True)
            self.async_session: _sm[AsyncSession] = _sm(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
            self._init_task = asyncio.create_task(self._init_db())
            logger.info("PostgresEvaluationRepository initialized", db_url=database_url)
        except Exception as e:
            logger.error("Failed to initialize PostgresEvaluationRepository", error=str(e))
            raise

    async def save_evaluation(self, evaluation: EvaluationResponse, user_id: str, question_id: str, atom_id: Optional[str] = None) -> str:
        """Guarda una nueva evaluación en la base de datos."""
        await self._init_task
        async with self.async_session() as session:
            stmt = insert(evaluations_table).values(
                evaluation_id=evaluation.evaluation_id,
                user_id=user_id,
                question_id=question_id,
                atom_id=atom_id,
                score=evaluation.score,
                evaluation_data=evaluation.model_dump(mode='json'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("Evaluation saved", evaluation_id=evaluation.evaluation_id, user_id=user_id)
            return evaluation.evaluation_id

    async def get_evaluation_by_id(self, evaluation_id: str) -> Optional[EvaluationResponse]:
        """Obtiene una evaluación por su ID."""
        await self._init_task
        async with self.async_session() as session:
            stmt = select(evaluations_table).where(evaluations_table.c.evaluation_id == evaluation_id)
            result = await session.execute(stmt)
            row = result.fetchone()
            if not row:
                return None
            record = dict(row._mapping)
            return EvaluationResponse(**record["evaluation_data"])

    async def get_user_evaluations(self, user_id: str, question_id: Optional[str] = None, atom_id: Optional[str] = None, limit: int = 20) -> List[EvaluationResponse]:
        """Obtiene las últimas evaluaciones de un usuario."""
        await self._init_task
        async with self.async_session() as session:
            stmt = select(evaluations_table).where(evaluations_table.c.user_id == user_id)
            
            if question_id:
                stmt = stmt.where(evaluations_table.c.question_id == question_id)
            if atom_id:
                stmt = stmt.where(evaluations_table.c.atom_id == atom_id)
                
            stmt = stmt.order_by(evaluations_table.c.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            evaluations = []
            for row in rows:
                record = dict(row._mapping)
                evaluations.append(EvaluationResponse(**record["evaluation_data"]))
            return evaluations

    async def update_user_progress(self, user_id: str, atom_id: str, evaluation_id: str, correct: bool, score: float):
        """Actualiza el progreso del usuario para un átomo específico."""
        await self._init_task
        async with self.async_session() as session:
            # Buscar progreso existente
            stmt = select(user_progress_table).where(
                user_progress_table.c.user_id == user_id,
                user_progress_table.c.atom_id == atom_id
            )
            result = await session.execute(stmt)
            existing = result.fetchone()
            
            if existing:
                # Actualizar progreso existente
                record = dict(existing._mapping)
                new_total = record["total_attempts"] + 1
                new_correct = record["correct_attempts"] + (1 if correct else 0)
                new_mastery = min(new_correct / new_total, 1.0) if new_total > 0 else 0.0
                
                # Aplicar factor de recencia - evaluaciones más recientes pesan más
                new_mastery = (record["mastery_level"] * 0.7) + (score * 0.3)
                new_mastery = max(0.0, min(1.0, new_mastery))
                
                update_stmt = sa_update(user_progress_table).where(
                    user_progress_table.c.user_id == user_id,
                    user_progress_table.c.atom_id == atom_id
                ).values(
                    mastery_level=new_mastery,
                    total_attempts=new_total,
                    correct_attempts=new_correct,
                    last_evaluation_id=evaluation_id,
                    last_updated=datetime.utcnow()
                )
                await session.execute(update_stmt)
            else:
                # Crear nuevo registro de progreso
                mastery_level = score  # Primera evaluación define el nivel inicial
                insert_stmt = insert(user_progress_table).values(
                    user_id=user_id,
                    atom_id=atom_id,
                    mastery_level=mastery_level,
                    total_attempts=1,
                    correct_attempts=1 if correct else 0,
                    last_evaluation_id=evaluation_id,
                    last_updated=datetime.utcnow()
                )
                await session.execute(insert_stmt)
            
            await session.commit()
            logger.info("User progress updated", user_id=user_id, atom_id=atom_id, score=score)

    async def get_user_progress(self, user_id: str, atom_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene el progreso de un usuario."""
        await self._init_task
        async with self.async_session() as session:
            stmt = select(user_progress_table).where(user_progress_table.c.user_id == user_id)
            
            if atom_id:
                stmt = stmt.where(user_progress_table.c.atom_id == atom_id)
                
            stmt = stmt.order_by(user_progress_table.c.last_updated.desc())
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows]

    async def get_mastery_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de dominio del usuario."""
        await self._init_task
        async with self.async_session() as session:
            # Contar total de átomos
            total_stmt = select(user_progress_table.c.atom_id).where(user_progress_table.c.user_id == user_id)
            total_result = await session.execute(total_stmt)
            total_atoms = len(total_result.fetchall())
            
            # Contar átomos dominados (mastery >= 0.8)
            mastered_stmt = select(user_progress_table.c.atom_id).where(
                user_progress_table.c.user_id == user_id,
                user_progress_table.c.mastery_level >= 0.8
            )
            mastered_result = await session.execute(mastered_stmt)
            mastered_atoms = len(mastered_result.fetchall())
            
            # Promedio de dominio
            avg_stmt = select(user_progress_table.c.mastery_level).where(user_progress_table.c.user_id == user_id)
            avg_result = await session.execute(avg_stmt)
            mastery_levels = [row[0] for row in avg_result.fetchall()]
            avg_mastery = sum(mastery_levels) / len(mastery_levels) if mastery_levels else 0.0
            
            return {
                "total_atoms": total_atoms,
                "mastered_atoms": mastered_atoms,
                "mastery_percentage": (mastered_atoms / total_atoms * 100) if total_atoms > 0 else 0.0,
                "average_mastery": avg_mastery,
                "atoms_in_progress": total_atoms - mastered_atoms
            }

    async def get_evaluation_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de evaluaciones."""
        await self._init_task
        async with self.async_session() as session:
            # Total de evaluaciones
            total_stmt = select(evaluations_table.c.evaluation_id)
            total_result = await session.execute(total_stmt)
            total_evaluations = len(total_result.fetchall())
            
            # Promedio de scores
            score_stmt = select(evaluations_table.c.score)
            score_result = await session.execute(score_stmt)
            scores = [row[0] for row in score_result.fetchall()]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Usuarios únicos
            users_stmt = select(evaluations_table.c.user_id).distinct()
            users_result = await session.execute(users_stmt)
            unique_users = len(users_result.fetchall())
            
            return {
                "total_evaluations": total_evaluations,
                "average_score": avg_score,
                "unique_users": unique_users,
                "evaluations_per_user": total_evaluations / unique_users if unique_users > 0 else 0.0
            } 