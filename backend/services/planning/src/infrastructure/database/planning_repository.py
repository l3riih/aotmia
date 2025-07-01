"""
Repositorio para interactuar con la base de datos de planificación (PostgreSQL).
"""

from typing import List, Optional, Dict, Any
import asyncio
import structlog
from datetime import datetime
from sqlalchemy import text, MetaData, Table, Column, String, JSON, Float, DateTime, Integer
from sqlalchemy import insert, update as sa_update, select, delete as sa_delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker as _sm

from ...schemas import LearningPlanResponse

logger = structlog.get_logger()

# Umbral para considerar un átomo como dominado
MASTERY_THRESHOLD = 0.8

metadata = MetaData()

learning_plans_table = Table(
    "learning_plans",
    metadata,
    Column("plan_id", String, primary_key=True),
    Column("user_id", String, nullable=False, index=True),
    Column("status", String, default="draft"),
    Column("plan_json", JSON, nullable=False),  # objeto completo del plan
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

user_progress_table = Table(
    "user_progress",
    metadata,
    Column("user_id", String, primary_key=True),
    Column("atom_id", String, primary_key=True),
    Column("mastery_level", Float, default=0.0),
    Column("last_review", DateTime, default=datetime.utcnow),
)

class PostgresPlanningRepository:
    """
    Repositorio para la gestión de datos de planificación en PostgreSQL.
    - Lee el progreso del usuario para informar nuevos planes.
    - Guarda los planes de aprendizaje generados.
    """

    async def _init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    def __init__(self, database_url: str):
        try:
            self.engine: AsyncEngine = create_async_engine(database_url, echo=False, future=True)
            self.async_session: _sm[AsyncSession] = _sm(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
            self._init_task = asyncio.create_task(self._init_db())
            logger.info("PostgresPlanningRepository initialized", db_url=database_url)
        except Exception as e:
            logger.error("Failed to initialize PostgresPlanningRepository", error=str(e))
            raise

    async def get_mastered_atom_ids(self, user_id: str) -> List[str]:
        """
        Obtiene los IDs de los átomos que un usuario ya ha dominado.
        """
        query = text("""
            SELECT atom_id FROM user_progress
            WHERE user_id = :user_id AND mastery_level >= :threshold
        """)
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    query, {"user_id": user_id, "threshold": MASTERY_THRESHOLD}
                )
                mastered_ids = [row[0] for row in result.fetchall()]
                logger.info(
                    "Fetched mastered atoms for user",
                    user_id=user_id,
                    count=len(mastered_ids)
                )
                return mastered_ids
        except Exception as e:
            logger.error(
                "Failed to fetch mastered atoms",
                error=str(e),
                user_id=user_id
            )
            return []

    async def save(self, plan: LearningPlanResponse) -> None:
        await self._init_task
        async with self.async_session() as session:
            stmt = insert(learning_plans_table).values(
                plan_id=plan.plan_id,
                user_id=plan.user_id,
                status=plan.status.value if hasattr(plan.status, "value") else str(plan.status),
                plan_json=plan.model_dump(mode='json'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("Plan saved", plan_id=plan.plan_id)

    async def get(self, plan_id: str) -> Optional[LearningPlanResponse]:
        await self._init_task
        async with self.async_session() as session:
            stmt = select(learning_plans_table).where(learning_plans_table.c.plan_id == plan_id)
            result = await session.execute(stmt)
            row = result.fetchone()
            if not row:
        return None
            record = dict(row._mapping)
            return LearningPlanResponse(**record["plan_json"])

    async def update(self, plan: LearningPlanResponse) -> None:
        await self._init_task
        async with self.async_session() as session:
            stmt = sa_update(learning_plans_table).where(learning_plans_table.c.plan_id == plan.plan_id).values(
                status=plan.status.value if hasattr(plan.status, "value") else str(plan.status),
                plan_json=plan.model_dump(mode='json'),
                updated_at=datetime.utcnow(),
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("Plan updated", plan_id=plan.plan_id)

    async def delete(self, plan_id: str) -> bool:
        await self._init_task
        async with self.async_session() as session:
            stmt = sa_delete(learning_plans_table).where(learning_plans_table.c.plan_id == plan_id)
            result = await session.execute(stmt)
            await session.commit()
            deleted = result.rowcount is not None and result.rowcount > 0
            if deleted:
                logger.info("Plan deleted", plan_id=plan_id)
            return deleted
    
    async def get_user_plans(self, user_id: str, limit: int = 10, offset: int = 0) -> List[LearningPlanResponse]:
        await self._init_task
        async with self.async_session() as session:
            stmt = (
                select(learning_plans_table)
                .where(learning_plans_table.c.user_id == user_id)
                .limit(limit)
                .offset(offset)
                .order_by(learning_plans_table.c.created_at.desc())
            )
            result = await session.execute(stmt)
            rows = result.fetchall()
            plans: List[LearningPlanResponse] = []
            for row in rows:
                record = dict(row._mapping)
                plans.append(LearningPlanResponse(**record["plan_json"]))
            return plans
    
    async def get_active_plans_count(self) -> int:
        """Obtiene el número de planes activos"""
        await self._init_task
        async with self.async_session() as session:
            stmt = select(learning_plans_table.c.plan_id).where(learning_plans_table.c.status == "active")
            result = await session.execute(stmt)
            return len(result.fetchall())
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del repositorio"""
        await self._init_task
        async with self.async_session() as session:
            total = await session.execute(select(learning_plans_table.c.plan_id))
            total_plans = len(total.fetchall())
            active = await session.execute(select(learning_plans_table.c.plan_id).where(learning_plans_table.c.status == "active"))
            active_plans = len(active.fetchall())
            completed = await session.execute(select(learning_plans_table.c.plan_id).where(learning_plans_table.c.status == "completed"))
            adapted = await session.execute(select(learning_plans_table.c.plan_id).where(learning_plans_table.c.status == "adapted"))
        return {
            "total_plans": total_plans,
            "active_plans": active_plans,
                "completed_plans": len(completed.fetchall()),
                "adapted_plans": len(adapted.fetchall()),
        } 