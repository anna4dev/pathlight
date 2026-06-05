"""Tool handlers and registration.

Shape A keeps Claude as the reasoning engine; the server-side LLM workflow
tools below (conflict / modification / briefing / instructional-plan) are
legacy experiments. They are NOT registered by default and are gated behind
the ``PATHLIGHT_ENABLE_LEGACY_TOOLS`` environment flag.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import mcp.types as types

from pathlight.resources import load_lesson, load_student
from pathlight.resources.gateway import read_resource_payload
from pathlight.schemas import (
    TeacherDeliverable,
    render_teacher_markdown,
    validate_deliverable,
)
from pathlight.services.briefing.schemas import PreClassBriefing
from pathlight.services.conflicts.schemas import LearningConflict
from pathlight.services.modifications.schemas import StudentModification
from pathlight.services.workflow.service import LessonAdaptationWorkflowService
from pathlight.services.briefing.service import BriefingService
from pathlight.services.conflicts.service import ConflictService
from pathlight.services.modifications.service import ModificationService
from pathlight.shared.serialization import to_text_content
from pathlight.tools.schemas import (
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


async def _handle_get_instructional_context(
    ctx: ToolContext,
    args: dict[str, Any],
) -> list[types.TextContent]:
    # Deterministic, no LLM. Claude Desktop does not auto-read MCP *resources*
    # in its tool loop, so this tool delivers the same scoped slice that backs
    # `student://{id}/scopes/lesson/{lid}/phase/{pid}`, letting Claude pull the
    # real IEP/lesson content (accommodation labels, phase, questions) before
    # drafting. Reuses the resource reader to guarantee parity.
    uri = (
        f"student://{args['student_id']}/scopes/lesson/"
        f"{args['lesson_id']}/phase/{args['phase_id']}"
    )
    return [types.TextContent(type="text", text=read_resource_payload(uri))]


async def _handle_validate_teacher_artifact(
    ctx: ToolContext,
    args: dict[str, Any],
) -> list[types.TextContent]:
    # Deterministic, no LLM. First gate: schema (strict Pydantic). Second gate:
    # semantic grounding against the real student IEP + lesson.
    deliverable = TeacherDeliverable.model_validate(args)
    student = load_student(deliverable.student_id)
    lesson = load_lesson(deliverable.lesson_id)
    report = validate_deliverable(deliverable, student, lesson)
    return to_text_content(report.model_dump())


async def _handle_render_teacher_artifact(
    ctx: ToolContext,
    args: dict[str, Any],
) -> list[types.TextContent]:
    # Deterministic, no LLM: validate the draft against the contract, then render.
    deliverable = TeacherDeliverable.model_validate(args)
    rendered = render_teacher_markdown(deliverable)
    return to_text_content(
        {
            "deliverable": deliverable.model_dump(),
            "rendered_markdown": rendered,
        }
    )


# Shape A tools are deterministic (no server-side LLM) and always registered.
_SHAPE_A_TOOL_HANDLERS: dict[str, ToolHandler] = {
    "get_instructional_context": _handle_get_instructional_context,
    "validate_teacher_artifact": _handle_validate_teacher_artifact,
    "render_teacher_artifact": _handle_render_teacher_artifact,
}


# All handlers below belong to the legacy server-side LLM workflow.
_LEGACY_TOOL_HANDLERS: dict[str, ToolHandler] = {
    "detect_conflicts": _handle_detect_conflicts,
    "generate_modifications": _handle_generate_modifications,
    "generate_pre_class_briefing": _handle_generate_pre_class_briefing,
    "generate_instructional_plan": _handle_generate_instructional_plan,
}

_LEGACY_TOOLS_FLAG = "PATHLIGHT_ENABLE_LEGACY_TOOLS"


def legacy_tools_enabled() -> bool:
    return os.environ.get(_LEGACY_TOOLS_FLAG, "").strip().lower() in {"1", "true", "yes", "on"}


def _shape_a_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_instructional_context",
            description=(
                "Fetch the grounded context for one student + lesson + phase in a "
                "single read: lesson overview, the requested phase, formative "
                "questions (with stable question ids), and the student's "
                "instructional core (profile, PLAAFP, goals, accommodations with "
                "real labels and source pages). Call this FIRST and base the draft "
                "on the returned content; do not invent accommodation text."
            ),
            inputSchema=schema_student_lesson_phase(),
        ),
        types.Tool(
            name="validate_teacher_artifact",
            description=(
                "Validate a teacher deliverable draft beyond schema: checks IEP "
                "grounding (accommodation refs resolve to real ids), accommodation "
                "coverage, lesson-question references, and unsupported phase/question "
                "ids. Returns a structured report ({ok, error_count, warning_count, "
                "issues[]}). Call this in the self-validation step and fix every "
                "error before rendering."
            ),
            inputSchema=TeacherDeliverable.model_json_schema(),
        ),
        types.Tool(
            name="render_teacher_artifact",
            description=(
                "Validate a teacher deliverable draft against the v1 output contract "
                "and return both the canonical JSON and a deterministic markdown "
                "checklist. Call this after drafting and self-validating in the "
                "`analyze_student_lesson` prompt to produce the final artifact."
            ),
            inputSchema=TeacherDeliverable.model_json_schema(),
        ),
    ]


def _legacy_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="detect_conflicts",
            description="[legacy] Server-side: detect student-lesson conflicts for one phase",
            inputSchema=schema_student_lesson_phase(),
        ),
        types.Tool(
            name="generate_modifications",
            description="[legacy] Server-side: generate modifications from provided conflicts",
            inputSchema=schema_lesson_phase_conflicts(),
        ),
        types.Tool(
            name="generate_pre_class_briefing",
            description="[legacy] Server-side: generate briefing from provided modifications",
            inputSchema=schema_student_lesson_modifications(),
        ),
        types.Tool(
            name="generate_instructional_plan",
            description=(
                "[legacy] Server-side workflow: detect conflicts, generate modifications, "
                "and synthesize briefing. Disabled by default in Shape A; prefer the "
                "`analyze_student_lesson` prompt with Claude-driven reasoning over MCP resources."
            ),
            inputSchema=schema_student_lesson(),
        ),
    ]


def build_tools() -> list[types.Tool]:
    # Shape A default path is resource + prompt driven; Claude reasons directly,
    # then calls the deterministic renderer to finalize the artifact. Legacy
    # server-side workflow tools are only surfaced when explicitly enabled.
    tools: list[types.Tool] = list(_shape_a_tools())
    if legacy_tools_enabled():
        tools.extend(_legacy_tools())
    return tools


async def dispatch_tool(
    ctx: ToolContext,
    name: str,
    arguments: dict[str, Any] | None,
) -> list[types.TextContent]:
    if not arguments:
        raise ValueError("Missing arguments")

    shape_a_handler = _SHAPE_A_TOOL_HANDLERS.get(name)
    if shape_a_handler is not None:
        return await shape_a_handler(ctx, arguments)

    handler = _LEGACY_TOOL_HANDLERS.get(name)
    if handler is not None:
        if not legacy_tools_enabled():
            raise ValueError(
                f"Tool '{name}' is a legacy server-side workflow tool, disabled in Shape A. "
                f"Set {_LEGACY_TOOLS_FLAG}=1 to enable it for experiments."
            )
        return await handler(ctx, arguments)

    raise ValueError(f"Unknown tool: {name}")
