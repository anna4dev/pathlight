"""Modification generation service (pure: conflicts -> modifications)."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from pathlight.services.conflicts.schemas import LearningConflict
from pathlight.shared.serialization import models_to_json_str
from pathlight.shared.utils import debug_json, debug_log
from . import prompts
from .schemas import StudentModification

if TYPE_CHECKING:
    from pathlight.llm import JsonLLMClient
    from pathlight.models import Lesson


class ModificationService:
    def __init__(self, llm: JsonLLMClient) -> None:
        self._llm = llm

    async def generate(
        self,
        lesson: Lesson,
        phase_id: str,
        conflicts: List[LearningConflict],
    ) -> List[StudentModification]:
        """Generate modifications for one phase from explicit conflicts."""
        phase_info = prompts.get_phase_activity(lesson, phase_id)
        if not phase_info or not conflicts:
            return []

        pid, activity = phase_info
        user_prompt = prompts.build_modification_user_prompt(
            phase_id=pid,
            activity=activity,
            conflicts_json=models_to_json_str(conflicts),
        )

        debug_log("DEBUG MODIFICATION SYSTEM PROMPT:", prompts.MODIFICATION_SYSTEM_PROMPT)
        debug_log("DEBUG MODIFICATION USER PROMPT:", user_prompt)

        modifications = await self._llm.fetch_json(
            system_prompt=prompts.MODIFICATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=list[StudentModification],
        )

        debug_json(
            "DEBUG MODIFICATIONS OUTPUT:",
            [m.model_dump() for m in modifications],
        )
        return modifications
