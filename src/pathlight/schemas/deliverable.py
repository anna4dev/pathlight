"""Strict output contract for the v1 teacher deliverable (Shape A).

This is the canonical artifact schema. Claude drafts content; the structure is
enforced here so the final deliverable does not depend on free-form prose.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Base for the v1 deliverable contract.

    Strict on both axes: ``extra="forbid"`` rejects unknown/misspelled keys
    instead of silently dropping them, and ``strict=True`` disables lax type
    coercion (e.g. an int will not be coerced into a string field). Combined
    with required (non-defaulted) sections below, an omitted structural
    section errors rather than becoming ``[]``. Emptiness is a *semantic*
    concern handled by the Phase 5 validation suite, not by the schema.
    """

    model_config = ConfigDict(extra="forbid", strict=True)


class ChecklistItem(ContractModel):
    action: str
    # Source reference to a grounding IEP item, e.g. "acc_01 (p.18)".
    # Optional leaf: some before-class actions are general logistics.
    accommodation_ref: Optional[str] = None


class ScaffoldedQuestion(ContractModel):
    # Must reference a real lesson question id, e.g. "q1".
    question_id: str
    original: str
    scaffolded: str


class AccommodationReminder(ContractModel):
    label: str
    # Source reference, e.g. "acc_01 (p.18)".
    source: Optional[str] = None


class PhasePlan(ContractModel):
    phase_id: str
    teacher_actions: List[str]
    scaffolded_questions: List[ScaffoldedQuestion]
    accommodation_reminders: List[AccommodationReminder]


class TeacherDeliverable(ContractModel):
    student_id: str
    lesson_id: str
    before_class_checklist: List[ChecklistItem]
    by_phase: List[PhasePlan]
