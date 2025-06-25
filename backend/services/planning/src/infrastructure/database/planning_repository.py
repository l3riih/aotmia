"""
Repositorio para interactuar con la base de datos de planificación (PostgreSQL).
"""

from typing import List, Optional, Dict, Any
import asyncio
import structlog
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ...schemas import LearningPlanResponse

logger = structlog.get_logger()

# Umbral para considerar un átomo como dominado
MASTERY_THRESHOLD = 0.8

class PostgresPlanningRepository:
    """
    Repositorio para la gestión de datos de planificación en PostgreSQL.
    - Lee el progreso del usuario para informar nuevos planes.
    - Guarda los planes de aprendizaje generados.
    """

    def __init__(self, database_url: str):
        try:
            self.engine = create_async_engine(database_url, echo=False)
            self.async_session = sessionmaker(
                self.engine, expire_on_commit=False, class_=AsyncSession
            )
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
        """Guarda un plan de aprendizaje. (No implementado)"""
        # TODO: Implementar la lógica para guardar el objeto del plan
        # en una tabla 'learning_plans'.
        logger.warning("Save plan not implemented", plan_id=plan.plan_id)
        pass

    async def get(self, plan_id: str) -> Optional[LearningPlanResponse]:
        """Obtiene un plan por ID. (No implementado)"""
        # TODO: Implementar la lógica para obtener un plan.
        logger.warning("Get plan not implemented", plan_id=plan_id)
        return None

    async def update(self, plan: LearningPlanResponse) -> None:
        """Actualiza un plan existente. (No implementado)"""
        # TODO: Implementar la lógica para actualizar un plan.
        logger.warning("Update plan not implemented", plan_id=plan.plan_id)
        pass

    async def close_connection(self):
        """Cierra el pool de conexiones del motor."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection pool closed.")

    async def delete(self, plan_id: str) -> bool:
        """Elimina un plan"""
        try:
            if plan_id in self._plans:
                del self._plans[plan_id]
                logger.info("Plan deleted", plan_id=plan_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete plan", error=str(e), plan_id=plan_id)
            raise
    
    async def get_user_plans(
        self, 
        user_id: str, 
        limit: int = 10,
        offset: int = 0
    ) -> List[LearningPlanResponse]:
        """Obtiene todos los planes de un usuario"""
        try:
            # Simular latencia de DB
            await asyncio.sleep(0.1)
            
            # Filtrar planes por usuario
            user_plans = [
                plan for plan in self._plans.values()
                if plan.user_id == user_id
            ]
            
            # Ordenar por fecha de creación (más reciente primero)
            user_plans.sort(key=lambda p: p.created_at, reverse=True)
            
            # Aplicar paginación
            return user_plans[offset:offset + limit]
            
        except Exception as e:
            logger.error(
                "Failed to get user plans",
                error=str(e),
                user_id=user_id
            )
            raise
    
    async def get_active_plans_count(self) -> int:
        """Obtiene el número de planes activos"""
        return sum(
            1 for plan in self._plans.values()
            if plan.status == "active"
        )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del repositorio"""
        total_plans = len(self._plans)
        active_plans = await self.get_active_plans_count()
        
        return {
            "total_plans": total_plans,
            "active_plans": active_plans,
            "completed_plans": sum(
                1 for plan in self._plans.values()
                if plan.status == "completed"
            ),
            "adapted_plans": sum(
                1 for plan in self._plans.values()
                if plan.status == "adapted"
            )
        } 