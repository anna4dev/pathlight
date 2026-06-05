"""Workflow orchestration service (explicitly owns multi-step pipeline)."""

from __future__ import annotations

from pathlight.services.briefing.service import BriefingService
from pathlight.services.conflicts.service import ConflictService
from pathlight.services.modifications.service import ModificationService
from pathlight.services.workflow.schemas import LessonAdaptation, PhaseAdaptation
from pathlight.models import Lesson, Student


class LessonAdaptationWorkflowService:
    def __init__(
        self,
        conflict_service: ConflictService,
        modification_service: ModificationService,
        briefing_service: BriefingService,
    ) -> None:
        self._conflict_service = conflict_service
        self._modification_service = modification_service
        self._briefing_service = briefing_service

    async def generate_instructional_plan(
        self,
        student: Student,
        lesson: Lesson,
    ) -> LessonAdaptation:
        phase_outputs: list[PhaseAdaptation] = []
        all_modifications = []

        for phase in lesson.phases:
            conflicts = await self._conflict_service.detect(student, lesson, phase.phase_id)
            modifications = await self._modification_service.generate(
                lesson=lesson,
                phase_id=phase.phase_id,
                conflicts=conflicts,
            )
            all_modifications.extend(modifications)
            phase_outputs.append(
                PhaseAdaptation(
                    phase_id=phase.phase_id,
                    conflicts=conflicts,
                    modifications=modifications,
                )
            )

        briefing = await self._briefing_service.generate(
            student=student,
            lesson=lesson,
            modifications=all_modifications,
        )

        return LessonAdaptation(
            student_id=student.id,
            lesson_id=lesson.id,
            phases=phase_outputs,
            briefing=briefing,
        )
