from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.models.learning_atom import LearningAtom
from backend.services.atomization.src.schemas import LearningAtomCreate


async def create_atom(session: AsyncSession, data: LearningAtomCreate) -> LearningAtom:
    atom = LearningAtom(
        title=data.title,
        content=data.content,
        difficulty_level=data.difficulty_level,
        prerequisites=data.prerequisites,
    )
    session.add(atom)
    await session.commit()
    await session.refresh(atom)
    return atom


async def list_atoms(session: AsyncSession, limit: int = 100) -> List[LearningAtom]:
    stmt = select(LearningAtom).limit(limit)
    result = await session.execute(stmt)
 