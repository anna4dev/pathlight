"""Tool handlers and registration (primitive + workflow)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import mcp.types as types

from src.pathlight.resources import load_lesson, load_student
from src.pathlight.services.briefing.schemas import PreClassBriefing
from src.pathlight.services.conflicts.schemas import LearningConflict
from src.pathlight.services.modifications.schemas import StudentModification
from src.pathlight.services.workflow.service import LessonAdaptationWorkflowService
from src.pathlight.services.briefing.service import BriefingService
from src.pathlight.services.conflicts.service import ConflictService
from src.pathlight.services.modifications.service import ModificationService
from src.pathlight.shared.serialization import to_text_content
from src.pathlight.tools.schemas import (
    schema_lesson_phase_conflicts,
    schema_student_lesson,
    schema_student_lesson_modifications,
    schema_student_lesson_phase,
)


@dataclass(frozen=True)
class ToolContext:
    conflict_service: ConflictService
    modification_service: ModificationService
    briefing_service: BriefingService
    workflow_service: LessonAdaptationWorkflowService


ToolHandler = Callable[[ToolContext, dict[str, Any]], Awaitable[list[types.TextContent]]]


async def _handle_detect_conflicts(ctx: ToolContext, args: dict[str, Any]) -> list[types.TextContent]:
    student = load_student(args["student_id"])
    lesson = load_lesson(args["lesson_id"])
    conflicts = await ctx.conflict_service.detect(student, lesson, args["phase_id"])
    return to_text_content(conflicts)


async def _handle_generate_modifications(ctx: ToolContext, args: dict[str, Any]) -> list[types.TextContent]:
    lesson = load_lesson(args["lesson_id"])
    conflicts = [LearningConflict.model_validate(item) for item in args["conflicts"]]
    modifications = await ctx.modification_service.generate(
        lesson=lesson,
        phase_id=args["phase_id"],
        conflicts=conflicts,
    )
    return to_text_content(modifications)


async def _handle_generate_pre_class_briefing(
    ctx: ToolContext,
    args: dict[str, Any],
) -> list[types.TextContent]:
    student = load_student(args["student_id"])
    lesson = load_lesson(args["lesson_id"])
    modifications = [StudentModification.model_validate(item) for item in args["modifications"]]
    briefing = await ctx.briefing_service.generate(student, lesson, modifications)
    return to_text_content(briefing)


async def _handle_generate_instructional_plan(
    ctx: ToolContext,
    args: dict[str, Any],
) -> list[types.TextContent]:
    student = load_student(args["student_id"])
    lesson = load_lesson(args["lesson_id"])
    result = await ctx.workflow_service.generate_instructional_plan(student, lesson)
    return to_text_content(result)


_TOOL_HANDLERS: dict[str, ToolHandler] = {
    "detect_conflicts": _handle_detect_conflicts,
    "generate_modifications": _handle_generate_modifications,
    "generate_pre_class_briefing": _handle_generate_pre_class_briefing,
    "generate_instructional_plan": _handle_generate_instructional_plan,
}


def build_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="detect_conflicts",
            description="Primitive: detect student-lesson conflicts for one phase",
            inputSchema=schema_student_lesson_phase(),
        ),
        types.Tool(
            name="generate_modifications",
            description="Primitive: generate modifications from provided conflicts",
            inputSchema=schema_lesson_phase_conflicts(),
        ),
        types.Tool(
            name="generate_pre_class_briefing",
            description="Primitive: generate briefing from provided modifications",
            inputSchema=schema_student_lesson_modifications(),
        ),
        types.Tool(
            name="generate_instructional_plan",
            description="Workflow: detect conflicts, generate modifications, and synthesize briefing",
            inputSchema=schema_student_lesson(),
        ),
    ]


async def dispatch_tool(
    ctx: ToolContext,
    name: str,
    arguments: dict[str, Any] | None,
) -> list[types.TextContent]:
    if not arguments:
        raise ValueError("Missing arguments")

    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")

    return await handler(ctx, arguments)
