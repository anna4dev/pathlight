"""Structured LLM output: per-conflict modifications."""

from typing import List

from pydantic import BaseModel


class StudentModification(BaseModel):
    phase_id: str
    conflict_ref: List[str]
    modification_strategy: str
    implementation_steps: List[str]
    expected_outcome: str
    iep_anchor: List[str]
