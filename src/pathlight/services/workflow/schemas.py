"""Structured outputs for end-to-end lesson adaptation workflow."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel
from pathlight.services.briefing.schemas import PreClassBriefing
from pathlight.services.conflicts.schemas import LearningConflict
from pathlight.services.modifications.schemas import StudentModification


class PhaseAdaptation(BaseModel):
    phase_id: str
    conflicts: List[LearningConflict]
    modifications: List[StudentModification]


class LessonAdaptation(BaseModel):
    student_id: str
    lesson_id: str
    phases: List[PhaseAdaptation]
    briefing: PreClassBriefing
