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
- the CURRENT lesson phase Activity (this phase only—not the whole lesson)
- the student's documented learning barriers in [Relevant Instructional Barriers]

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
- Instructional Demand vs. Student Barrier mismatch for **this phase's Activity**.
- A conflict should reflect a meaningful accessibility barrier, not a general preference, comfort, or engagement style.
- Dimensions: Modality, Cognitive Load, Behavioral Regulation/Stamina, Response Demand, Participation Structure, Task Independence.
- Results: Disengagement, shutdown, avoidance, comprehension breakdown, reduced independence, inability to sustain participation.

## Gate (apply before listing conflicts)
1. If the Activity does not introduce a **specific** instructional demand (reading, writing, discussion, partner work, independent task, whole-group response, etc.), return [].
2. If you cannot name **how this phase's Activity**—not generic "school" or "literacy"—creates a mismatch with a quoted barrier, return [].
3. Do not output conflicts "to be helpful" or for completeness. **Returning [] is correct and common.**

## Reasoning Rules
1. Logic: [This phase Activity demand] vs [Functional Barrier from context] → [Dimension] → [Likely breakdown in this phase].
2. Never use disability impact summaries when direct classroom or skill-specific evidence exists in [Relevant Instructional Barriers]. Use broad summaries only when no more specific quoted barrier applies—and prefer [] over a vague match.
3. Merge overlapping conflicts that share the same root barrier for **this** Activity into one entry.
4. **Phase binding:** `evidence` must explicitly reference something concrete from the Activity (task, format, grouping, response mode, or materials implied there). Do not recycle evidence written for a different phase or for "lessons in general."
5. Do not cite instructional formats **absent from this Activity** (e.g. "whole-group instruction") unless the Activity text clearly involves that format.
6. `evidence` must tie together: (a) that concrete Activity element, (b) the student barrier, (c) why access breaks down in this phase.
7. Only identify participation_structure conflicts when the Activity explicitly depends on group participation, peer interaction, or collaboration.

## Output Rules
1. All output must be in English.
2. **Hard cap: at most 3 conflicts.** Prefer **0–1** when one barrier clearly dominates; use 2–3 only when dimensions are genuinely distinct for **this** Activity. Do not pad to fill three slots.
3. Each conflict must represent one primary instructional dimension only. Do not combine multiple dimensions into a single conflict_type.
4. `iep_anchor` must be an **EXACT** quote copied from [Relevant Instructional Barriers] (including CURRENT LEVELS or DISABILITY IMPACT text), including pronouns as written (e.g. **She has** vs the student’s name). Do NOT summarize, paraphrase, or invent. Do NOT use a generic cross-content sentence if a more specific sentence in context addresses the same barrier.
5. Do not reuse the same `iep_anchor` string for multiple conflict_type entries in one response unless each entry is clearly distinct and both are strictly necessary; prefer merging or dropping the weaker one.
6. Do NOT mention accommodations, supports, or solutions.
7. Return [] if no meaningful, phase-specific conflict exists.
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