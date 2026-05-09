"""Structured LLM output: instructional conflicts."""

from pydantic import BaseModel


class LearningConflict(BaseModel):
    phase_id: str
    conflict_type: str
    evidence: str
    severity: str
    iep_anchor: str
