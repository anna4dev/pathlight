"""Strict output contract for the v1 teacher deliverable (Shape A).

This is the canonical artifact schema. Claude drafts content; the structure is
enforced here so the final deliverable does not depend on free-form prose.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChecklistItem(BaseModel):
    action: str
    # Source reference to a grounding IEP item, e.g. "acc_01 (p.18)".
    # Optional: some before-class actions are general logistics.
    accommodation_ref: Optional[str] = None


class ScaffoldedQuestion(BaseModel):
    # Must reference a real lesson question id, e.g. "q1".
    question_id: str
    original: str
    scaffolded: str


class AccommodationReminder(BaseModel):
    label: str
    # Source reference, e.g. "acc_01 (p.18)".
    source: Optional[str] = None


class PhasePlan(BaseModel):
    phase_id: str
    teacher_actions: List[str] = Field(default_factory=list)
    scaffolded_questions: List[ScaffoldedQuestion] = Field(default_factory=list)
    accommodation_reminders: List[AccommodationReminder] = Field(default_factory=list)


class TeacherDeliverable(BaseModel):
    student_id: str
    lesson_id: str
    before_class_checklist: List[ChecklistItem] = Field(default_factory=list)
    by_phase: List[PhasePlan] = Field(default_factory=list)
