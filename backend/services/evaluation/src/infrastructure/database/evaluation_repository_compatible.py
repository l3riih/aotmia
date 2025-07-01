"""
Repositorio compatible para persistencia de evaluaciones en PostgreSQL.
Compatible con la tabla existente de evaluations.
"""

from typing import Dict, Any, Optional, List
import asyncio
import structlog
from datetime import datetime
from sqlalchemy import MetaData, Table, Column, String, Float, DateTime, JSON, Integer, select, insert, update as sa_update, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker as _sm

from ...schemas import EvaluationResponse

logger = structlog.get_logger()

# Definir la tabla usando la estructura existente (sin atom_id)
metadata = MetaData()

evaluations_table = Table(
    "evaluations",
    metadata,
    Column("evaluation_id", String, primary_key=True),
    Column("user_id", String, nullable=False, index=True),
    Column("question_id", String, nullable=False, index=True),
    Column("score", Float, nullable=False),
    Column("feedback", JSON, nullable=False),
    Column("misconceptions_detected", JSON, default=[]),
    Column("learning_progress", JSON, nullable=False),
    Column("agent_metadata", JSON, nullable=False),
    Column("key_concepts_understood", JSON, default=[]),
    Column("next_recommended_topics", JSON, default=[]),
    Column("estimated_time_to_mastery", Integer, default=60),
    Column("created_at", DateTime, default=datetime.utcnow),
)

class CompatibleEvaluationRepository:
    """
    Repositorio compatible con la tabla existente de evaluations.
    Funciona con la estructura actual sin modificar el esquema.
    """

    async def _init_db(self):
        """No necesitamos crear tablas, ya existen"""
        # Solo verificamos que la conexión funciona
        async with self.engine.begin() as conn:
            await conn.execute(select(1))

    def __init__(self, database_url: str):
        try:
            self.engine: AsyncEngine = create_async_engine(database_url, echo=False, future=True)
            self.async_session: _sm[AsyncSession] = _sm(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
            self._init_task = asyncio.create_task(self._init_db())
            logger.info("CompatibleEvaluationRepository initialized", db_url=database_url)
        except Exception as e:
            logger.error("Failed to initialize CompatibleEvaluationRepository", error=str(e))
            raise

    async def save_evaluation(self, evaluation: EvaluationResponse, user_id: str, question_id: str) -> str:
        """Guarda una nueva evaluación usando la estructura existente"""
        await self._init_task
        async with self.async_session() as session:
            stmt = insert(evaluations_table).values(
                evaluation_id=evaluation.evaluation_id,
                user_id=user_id,
                question_id=question_id,
                score=evaluation.score,
                feedback=evaluation.feedback.model_dump(mode='json'),
                misconceptions_detected=[m.model_dump(mode='json') for m in evaluation.misconceptions_detected],
                learning_progress=evaluation.learning_progress.model_dump(mode='json'),
                agent_metadata=evaluation.agent_metadata.model_dump(mode='json'),
                key_concepts_understood=evaluation.key_concepts_understood,
                next_recommended_topics=evaluation.next_recommended_topics,
                estimated_time_to_mastery=evaluation.estimated_time_to_mastery,
                created_at=datetime.utcnow(),
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("Evaluation saved (compatible)", evaluation_id=evaluation.evaluation_id, user_id=user_id)
            return evaluation.evaluation_id

    async def get_evaluation_by_id(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una evaluación por su ID"""
        await self._init_task
        async with self.async_session() as session:
            stmt = select(evaluations_table).where(evaluations_table.c.evaluation_id == evaluation_id)
            result = await session.execute(stmt)
            row = result.fetchone()
            if not row:
                return None
            return dict(row._mapping)

    async def get_user_evaluations(self, user_id: str, question_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene las últimas evaluaciones de un usuario"""
        await self._init_task
        async with self.async_session() as session:
            stmt = select(evaluations_table).where(evaluations_table.c.user_id == user_id)
            
            if question_id:
                stmt = stmt.where(evaluations_table.c.question_id == question_id)
                
            stmt = stmt.order_by(evaluations_table.c.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows]

    async def get_user_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """Obtiene un resumen del progreso del usuario basado en evaluaciones"""
        await self._init_task
        async with self.async_session() as session:
            # Obtener todas las evaluaciones del usuario
            stmt = select(evaluations_table).where(evaluations_table.c.user_id == user_id)
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            if not rows:
                return {
                    "total_evaluations": 0,
                    "average_score": 0.0,
                    "concepts_mastered": [],
                    "recent_topics": [],
                    "improvement_trend": "no_data"
                }
            
            evaluations = [dict(row._mapping) for row in rows]
            
            # Calcular estadísticas
            total_evaluations = len(evaluations)
            average_score = sum(e["score"] for e in evaluations) / total_evaluations
            
            # Extraer conceptos entendidos
            all_concepts = []
            for eval_data in evaluations:
                concepts = eval_data.get("key_concepts_understood", [])
                all_concepts.extend(concepts)
            
            # Conceptos únicos con frecuencia > 1 (dominados)
            concept_counts = {}
            for concept in all_concepts:
                concept_counts[concept] = concept_counts.get(concept, 0) + 1
            
            concepts_mastered = [concept for concept, count in concept_counts.items() if count > 1]
            
            # Últimos temas recomendados
            recent_evaluations = sorted(evaluations, key=lambda x: x["created_at"], reverse=True)[:5]
            recent_topics = []
            for eval_data in recent_evaluations:
                topics = eval_data.get("next_recommended_topics", [])
                recent_topics.extend(topics)
            
            # Tendencia de mejora (últimas 5 vs anteriores)
            if len(evaluations) >= 5:
                recent_scores = [e["score"] for e in recent_evaluations]
                older_scores = [e["score"] for e in evaluations[:-5]] if len(evaluations) > 5 else []
                
                if older_scores:
                    recent_avg = sum(recent_scores) / len(recent_scores)
                    older_avg = sum(older_scores) / len(older_scores)
                    
                    if recent_avg > older_avg + 0.1:
                        improvement_trend = "improving"
                    elif recent_avg < older_avg - 0.1:
                        improvement_trend = "declining"
                    else:
                        improvement_trend = "stable"
                else:
                    improvement_trend = "insufficient_data"
            else:
                improvement_trend = "insufficient_data"
            
            return {
                "total_evaluations": total_evaluations,
                "average_score": round(average_score, 3),
                "concepts_mastered": list(set(concepts_mastered)),
                "recent_topics": list(set(recent_topics))[:10],  # Top 10 únicos
                "improvement_trend": improvement_trend,
                "last_evaluation_date": recent_evaluations[0]["created_at"].isoformat() if recent_evaluations else None
            }

    async def get_evaluation_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de evaluaciones"""
        await self._init_task
        async with self.async_session() as session:
            # Contar total de evaluaciones
            total_stmt = select(evaluations_table.c.evaluation_id)
            total_result = await session.execute(total_stmt)
            total_evaluations = len(total_result.fetchall())
            
            if total_evaluations == 0:
                return {
                    "total_evaluations": 0,
                    "average_score": 0.0,
                    "unique_users": 0,
                    "evaluations_per_user": 0.0
                }
            
            # Obtener todos los scores
            score_stmt = select(evaluations_table.c.score)
            score_result = await session.execute(score_stmt)
            scores = [row[0] for row in score_result.fetchall()]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Contar usuarios únicos
            users_stmt = select(evaluations_table.c.user_id).distinct()
            users_result = await session.execute(users_stmt)
            unique_users = len(users_result.fetchall())
            
            return {
                "total_evaluations": total_evaluations,
                "average_score": round(avg_score, 3),
                "unique_users": unique_users,
                "evaluations_per_user": round(total_evaluations / unique_users, 2) if unique_users > 0 else 0.0
            }

    async def search_evaluations_by_concept(self, concept: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca evaluaciones que contengan un concepto específico"""
        await self._init_task
        async with self.async_session() as session:
            # Usar sintaxis PostgreSQL correcta para buscar en arrays JSON
            # Convertir a texto y buscar usando LIKE
            stmt = select(evaluations_table).where(
                text("key_concepts_understood::text LIKE :concept")
            ).params(concept=f'%"{concept}"%').limit(limit)
            
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows] 