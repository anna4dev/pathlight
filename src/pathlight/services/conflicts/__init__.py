"""Conflict detection between lesson phases and IEP barriers."""

from .schemas import LearningConflict
from .service import ConflictService

__all__ = ["ConflictService", "LearningConflict"]
