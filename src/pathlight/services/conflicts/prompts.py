"""Prompt builders for conflict detection."""

from __future__ import annotations

from src.pathlight.models import Lesson, Student


def build_plaafp_context(student: Student) -> list[str]:
    """Flatten PLAAFP into instructional barrier context."""

    context: list[str] = []

    for p in student.plaafp:
        sections = []

        if p.current_levels and p.current_levels != "N/A":
            sections.append(
                f"""
                CURRENT LEVELS:
                {p.current_levels}
                """.strip()
            )

        if p.disability_impact and p.disability_impact != "N/A":
            sections.append(
                f"""
                DISABILITY IMPACT:
                {p.disability_impact}
                """.strip()
            )

        if sections:
            context.append(
                f"""
                DOMAIN: {p.domain}

                {chr(10).join(sections)}
                """.strip()
            )

    return context


CONFLICT_SYSTEM_PROMPT = """
## Role
Special Education Instructional Accessibility Evaluator.

## Task
Identify instructional conflicts between:
- the CURRENT lesson phase demands
- the student's documented learning barriers

Return a JSON array only.

## JSON Schema
[
{
    "phase_id": "string",
    "conflict_type": "modality_access|cognitive_load|behavioral_regulation_stamina|response_demand|participation_structure|task_independence",
    "evidence": "string",
    "severity": "low|medium|high",
    "iep_anchor": "string"
}
]

## Conflict Definition
- Instructional Demand vs. Student Barrier mismatch.
- A conflict should reflect a meaningful accessibility barrier, not a general preference, comfort, or engagement style.
- Dimensions: Modality, Cognitive Load, Behavioral Regulation/Stamina, Response Demand, Participation Structure, Task Independence.
- Results: Disengagement, shutdown, avoidance, comprehension breakdown, reduced independence, inability to sustain participation.

## Reasoning Rules
1. Logic: [Demand] vs [Functional Barrier] → [Dimension] → [Result].
2. Never use disability impact summaries when direct classroom evidence exists. Use disability summaries only when no direct instructional evidence exists.
3. Merge overlapping conflicts sharing same root instructional barrier.
4. Evidence must explicitly connect:
   - the lesson phase demand
   - the student barrier
5. Evidence and iep_anchor should describe observable instructional breakdowns tied to the lesson demand.
6. Only identify participation_structure conflicts when the lesson phase explicitly depends on group participation, peer interaction, or collaborative structures.

## Output Rules
1. All output must be in English.
2. Average expected output is 1-3 conflicts.
3. Each conflict must represent one primary instructional dimension only. Do not combine multiple dimensions into a single conflict_type.
4. Select the MOST instructionally relevant IEP quote supporting the conflict.
5. Avoid broad disability summaries when a more specific instructional barrier exists.
6. `iep_anchor` must be an EXACT quote from the IEP. Do NOT summarize or paraphrase `iep_anchor`. Do NOT invent IEP content.
7. Do NOT mention accommodations, supports, or solutions.
8. Return [] if no meaningful conflict exists.
""".strip()


def build_conflict_user_prompt(
    *,
    phase_id: str,
    activity: str,
    plaafp_context: list[str],
) -> str:
    return f"""
    [Lesson Phase]

    Phase ID:
    {phase_id}

    Activity:
    {activity}

    [Relevant Instructional Barriers]

    {chr(10).join(plaafp_context)}
    """.strip()


def prompts_for_phase(
    student: Student,
    lesson: Lesson,
    phase_id: str,
) -> tuple[str, str] | None:
    """Return (system, user) prompts for a lesson phase."""

    target_phase = next(
        (p for p in lesson.phases if p.phase_id == phase_id),
        None,
    )

    if not target_phase:
        return None

    plaafp_context = build_plaafp_context(student)

    user_prompt = build_conflict_user_prompt(
        phase_id=target_phase.phase_id,
        activity=target_phase.activity,
        plaafp_context=plaafp_context,
    )

    return CONFLICT_SYSTEM_PROMPT, user_prompt