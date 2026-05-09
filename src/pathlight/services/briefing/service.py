"""Pre-class briefing service (pure: modifications -> briefing)."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.pathlight.services.modifications.schemas import StudentModification
from src.pathlight.shared.serialization import models_to_json_str
from src.pathlight.shared.utils import debug_json, debug_log
from . import prompts
from .schemas import PreClassBriefing

if TYPE_CHECKING:
    from src.pathlight.llm import JsonLLMClient
    from src.pathlight.models import Lesson, Student


class BriefingService:
    def __init__(self, llm: JsonLLMClient) -> None:
        self._llm = llm

    async def generate(
        self,
        student: Student,
        lesson: Lesson,
        modifications: List[StudentModification],
    ) -> PreClassBriefing:
        user_prompt = prompts.build_briefing_user_prompt(
            student=student,
            lesson=lesson,
            modifications_json=models_to_json_str(modifications),
        )

        debug_log("DEBUG BRIEFING SYSTEM PROMPT:", prompts.BRIEFING_SYSTEM_PROMPT)
        debug_log("DEBUG BRIEFING USER PROMPT:", user_prompt)

        briefing = await self._llm.fetch_json(
            system_prompt=prompts.BRIEFING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=PreClassBriefing,
        )

        debug_json("DEBUG BRIEFING OUTPUT:", briefing.model_dump())
        return briefing
