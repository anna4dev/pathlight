"""Conflict detection service."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.pathlight.shared.utils import debug_json, debug_log
from . import prompts
from .schemas import LearningConflict

if TYPE_CHECKING:
    from src.pathlight.llm import JsonLLMClient
    from src.pathlight.models import Lesson, Student


class ConflictService:
    def __init__(self, llm: JsonLLMClient) -> None:
        self._llm = llm

    async def detect(
        self,
        student: Student,
        lesson: Lesson,
        phase_id: str,
    ) -> List[LearningConflict]:
        pair = prompts.prompts_for_phase(student, lesson, phase_id)
        if not pair:
            return []

        system_prompt, user_prompt = pair
        debug_log("DEBUG LLM system_prompt:", system_prompt)
        debug_log("DEBUG LLM user_prompt:", user_prompt)

        conflicts = await self._llm.fetch_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=list[LearningConflict],
        )

        debug_json(
            "DEBUG LLM OUTPUT:",
            [c.model_dump() for c in conflicts],
        )
        return conflicts
