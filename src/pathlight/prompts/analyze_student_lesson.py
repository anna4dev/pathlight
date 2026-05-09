"""MCP prompt: end-to-end student × lesson accessibility workflow."""

from __future__ import annotations

import mcp.types as types

NAME = "analyze_student_lesson"
DESCRIPTION = (
    "Analyze conflicts and produce adapted lesson guidance for one student and one lesson"
)

PROMPT_ARGUMENTS: list[types.PromptArgument] = [
    types.PromptArgument(
        name="student_id",
        description="Student JSON file stem under data/students/",
        required=True,
    ),
    types.PromptArgument(
        name="lesson_id",
        description="Lesson JSON file stem under data/lessons/",
        required=True,
    ),
]


def mcp_prompt() -> types.Prompt:
    return types.Prompt(name=NAME, description=DESCRIPTION, arguments=PROMPT_ARGUMENTS)


def mcp_get_prompt_result(arguments: dict[str, str] | None) -> types.GetPromptResult:
    if not arguments:
        raise ValueError("Missing arguments")

    s_id = arguments["student_id"]
    l_id = arguments["lesson_id"]

    text = (
        "Use workflow tool `generate_instructional_plan` with the ids below.\n"
        f"- student_id: {s_id}\n"
        f"- lesson_id: {l_id}\n\n"
        "If needed, you may call primitive tools manually in this order:\n"
        "1) detect_conflicts (per phase)\n"
        "2) generate_modifications (per phase, with explicit conflicts payload)\n"
        "3) generate_pre_class_briefing (with aggregated modifications)\n"
    )

    return types.GetPromptResult(
        description=(
            f"Lesson adaptation workflow for lesson {l_id} and student {s_id}"
        ),
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=text),
            )
        ],
    )
