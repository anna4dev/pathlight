"""Register MCP prompts (append a module to ``_PROMPT_MODULES`` for each new prompt file)."""

from __future__ import annotations

import mcp.types as types

from src.pathlight.prompts import analyze_student_lesson

_PROMPT_MODULES = [
    analyze_student_lesson,
]


def list_mcp_prompts() -> list[types.Prompt]:
    return [m.mcp_prompt() for m in _PROMPT_MODULES]


def get_mcp_prompt_result(
    name: str,
    arguments: dict[str, str] | None,
) -> types.GetPromptResult:
    for mod in _PROMPT_MODULES:
        if mod.NAME == name:
            return mod.mcp_get_prompt_result(arguments)
    raise ValueError(f"Unknown prompt: {name}")
