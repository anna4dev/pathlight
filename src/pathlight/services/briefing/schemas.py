"""Structured LLM output: teacher-facing briefing."""

from typing import List

from pydantic import BaseModel


class PhaseBrief(BaseModel):
    phase_id: str
    phase_name: str
    risks: List[str]
    teacher_actions: List[str]
    materials_needed: List[str]
    monitoring_focus: List[str]


class PreClassBriefing(BaseModel):
    lesson_summary: str
    priority_concerns: List[str]
    preparation_checklist: List[str]
    phase_briefs: List[PhaseBrief]
