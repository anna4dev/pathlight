"""Prompt builders for modification generation."""

from __future__ import annotations

from src.pathlight.models import Lesson


MODIFICATION_SYSTEM_PROMPT = """
## Role
Differentiated Instruction Specialist.

## Task
Generate instructional modifications that reduce the identified learning conflicts within the lesson phase.

Return a JSON array only.

## JSON Schema
[
{
    "phase_id": "string",
    "conflict_ref": [
        "string"
    ],
    "modification_strategy": "string",
    "implementation_steps": [
        "string"
    ],
    "expected_outcome": "string",
    "iep_anchor": [
        "string"
    ],
}
]

## Instructional Principles
- Preserve the lesson’s intended learning goal and academic rigor.
- Avoid supports requiring continuous adult prompting, individualized facilitation, or separate instructional workflows.
- Improve instructional accessibility without lowering expectations.
- Modifications may adjust task format, scaffolding, or response mode to improve access.

## Pedagogical Grounding
Ground modifications in evidence-based practices such as:
- Universal Design for Learning (UDL)
- scaffolded instruction
- guided practice
- multimodal representation
- executive functioning supports
- structured participation
- comprehension scaffolds

## Reasoning Rules
1. Merge overlapping instructional supports into unified routines whenever possible, while preserving distinct instructional conflict dimensions.
2. A single modification may address multiple related conflicts.
3. Independent practice should remain primarily independent when possible.
4. Modifications may change support level or response format, but should preserve the core learning goal.
5. implementation_steps must describe concrete teacher actions.
6. expected_outcome should describe the likely instructional improvement.
7. Prefer modifications within the existing activity structure.

## Output Rules
1. Return all fields in English only.
2. Average expected output is 1-3 modifications.
3. Avoid vague recommendations or generic encouragement.
4. conflict_ref values must exactly match the provided conflict_type values.
5. iep_anchor must directly quote related IEP evidence.
6. Return [] if no meaningful modification exists.
""".strip()


def build_modification_user_prompt(
    *,
    phase_id: str,
    activity: str,
    conflicts_json: str,
) -> str:
    return f"""
    [Lesson Phase]

    Phase ID:
    {phase_id}

    Activity:
    {activity}

    [Identified Learning Conflicts]

    {conflicts_json}
    """.strip()


def get_phase_activity(
    lesson: Lesson,
    phase_id: str,
) -> tuple[str, str] | None:
    target = next(
        (p for p in lesson.phases if p.phase_id == phase_id),
        None,
    )

    if not target:
        return None

    return target.phase_id, target.activity
