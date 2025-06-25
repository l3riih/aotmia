import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for SQLAlchemy models."""

    pass


DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://atomia_user:atomia_password@localhost/atomia_dev",
)

# Echo set to False to reduce noise; change to True for debugging
engine = create_async_engine(DATABASE_URL, echo=False)

# Factory that creates new AsyncSession objects
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""

    async with AsyncSessionLocal() as session:
        yield session 