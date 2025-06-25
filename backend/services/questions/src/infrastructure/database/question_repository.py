"""
Repositorio para la base de datos de preguntas (PostgreSQL).
"""
from typing import List
import structlog
from sqlalchemy import (
    create_engine, Table, Column, String, Text, DateTime, MetaData, Integer, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

from ....src.schemas import Question

logger = structlog.get_logger(__name__)

metadata = MetaData()
questions_table = Table(
    'questions',
    metadata,
    Column('question_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('atom_id', String, nullable=False, index=True),
    Column('question_text', Text, nullable=False),
    Column('question_type', String, nullable=False),
    Column('difficulty_level', String, nullable=False),
    Column('options', JSON),
    Column('correct_answer', Text),
    Column('explanation', Text),
    Column('author_agent_id', String),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('version', Integer, default=1),
)

class PostgresQuestionRepository:
    """
    Repositorio para la gestión de preguntas en PostgreSQL.
    """

    def __init__(self, database_url: str):
        try:
            self.engine = create_async_engine(database_url, echo=False)
            self.async_session = sessionmaker(
                self.engine, expire_on_commit=False, class_=AsyncSession
            )
            # Crear la tabla si no existe
            sync_engine = create_engine(database_url)
            metadata.create_all(sync_engine)
            logger.info("PostgresQuestionRepository initialized", db_url=database_url)
        except Exception as e:
            logger.error("Failed to initialize PostgresQuestionRepository", error=str(e))
            raise

    async def save_many(self, questions: List[Question]) -> None:
        """
        Guarda una lista de preguntas en la base de datos.
        """
        if not questions:
            return

        async with self.async_session() as session:
            try:
                session.add_all(questions)
                await session.commit()
                logger.info("Successfully saved questions", count=len(questions))
            except Exception as e:
                await session.rollback()
                logger.error("Failed to save questions", error=str(e))
                raise

    async def close_connection(self):
        """Cierra el pool de conexiones del motor."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection pool closed.") 