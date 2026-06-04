"""Shape A strict output contracts and deterministic artifact rendering."""

from src.pathlight.schemas.deliverable import (
    AccommodationReminder,
    ChecklistItem,
    PhasePlan,
    ScaffoldedQuestion,
    TeacherDeliverable,
)
from src.pathlight.schemas.rendering import render_teacher_markdown
from src.pathlight.schemas.validation import (
    ValidationIssue,
    ValidationReport,
    validate_deliverable,
)

__all__ = [
    "AccommodationReminder",
    "ChecklistItem",
    "PhasePlan",
    "ScaffoldedQuestion",
    "TeacherDeliverable",
    "ValidationIssue",
    "ValidationReport",
    "render_teacher_markdown",
    "validate_deliverable",
]
