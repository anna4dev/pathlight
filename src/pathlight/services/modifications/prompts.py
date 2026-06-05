"""Prompt builders for modification generation."""

from __future__ import annotations

from pathlight.models import Lesson


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
1. Prefer **one** modification that addresses **all** conflicts in [Identified Learning Conflicts] when one coherent instructional routine can cover them.
2. **At most 2 modifications** for this phase. Use 2 only when conflicts need **clearly non-substitutable** strategies (e.g. a participation structure change vs. a comprehension scaffold that cannot be merged without watering one down).
3. **No redundant bundles:** Do not output two modifications where one’s `conflict_ref` is a subset of the other’s, or where both target the same primary access issue. Merge into one entry or drop the weaker one.
4. Each provided `conflict_type` must appear in **exactly one** modification’s `conflict_ref` across the whole array (full coverage: do not omit an input conflict; do not list the same type twice).
5. Independent practice should remain primarily independent when possible.
6. Modifications may change support level or response format, but must preserve the core learning goal.
7. `implementation_steps` must describe concrete teacher actions and align with **this phase’s Activity** (reference its task, format, grouping, or materials when relevant—not generic “lessons” or other phases).
8. `expected_outcome` should describe the likely instructional improvement for this phase only.

## Output Rules
1. Return all fields in English only.
2. **Hard cap: at most 2 modifications.** Default to **1** when a single merged plan suffices.
3. Avoid vague recommendations or generic encouragement.
4. `conflict_ref` values must **exactly** match the `conflict_type` values in [Identified Learning Conflicts]. Do not invent conflict types. Include only conflicts this modification actually addresses.
5. `iep_anchor` must list **exact** strings copied **only** from the `iep_anchor` fields in [Identified Learning Conflicts]. Do not paraphrase, summarize, or add quotes not present there.
6. Return [] if there is no meaningful modification or if there are no conflicts to address.
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
