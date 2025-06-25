from backend.shared.database import Base
from .learning_atom import LearningAtom

__all__ = ["Base", "LearningAtom"]

target_metadata = Base.metadata 