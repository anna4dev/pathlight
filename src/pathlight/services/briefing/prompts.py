"""Prompt builders for pre-class briefing."""

from __future__ import annotations

from src.pathlight.shared.serialization import models_to_json_str
from src.pathlight.models import Lesson, Student

BRIEFING_SYSTEM_PROMPT = """
## Role
Special education instructional coordinator.

## Task
Generate a concise teacher-facing pre-class instructional briefing based on the lesson modifications.

Return a JSON object only.

## JSON Schema
{
    "lesson_summary": "string",

    "priority_concerns": [
        "string"
    ],

    "preparation_checklist": [
        "string"
    ],

    "phase_briefs": [
        {
            "phase_id": "string",

            "phase_name": "string",

            "risks": [
                "string"
            ],

            "teacher_actions": [
                "string"
            ],

            "materials_needed": [
                "string"
            ],

            "monitoring_focus": [
                "string"
            ]
        }
    ]
}

## Briefing Principles
- Prioritize actionable, realistic classroom guidance.
- Do not infer additional instructional concerns from the lesson content itself. Only use explicitly identified conflicts and modifications.
- Focus on instructional access risks and teacher decision-making.
- Translate instructional conflicts into teacher-friendly classroom concerns rather than repeating taxonomy labels.
- Preserve lesson rigor and instructional intent.
- Ground supports in the specific lesson content and objectives.

## Operational Guidance
1. teacher_actions must describe concrete classroom actions.
2. Convert strategies into practical teacher cues or classroom artifacts.
3. monitoring_focus must describe observable student behaviors or risk indicators.
4. preparation_checklist should only include materials or logistical preparation needed before class.
5. materials_needed should describe realistic classroom supports or artifacts.

## Output Rules
1. Return all fields in English only.
2. Maximum 3 priority concerns. Maximum 3 teacher actions per phase. Maximum 3 monitoring focus items.
3. Avoid generic summaries or repeated modifications. Prefer high-impact supports only.
4. Keep guidance concise, operational, and concise teacher-facing language.
5. Prioritize instructional clarity over completeness. Avoid repeating materials or supports across sections.
""".strip()


def build_briefing_user_prompt(
    *,
    student: Student,
    lesson: Lesson,
    modifications_json: str,
) -> str:
    return f"""
[Student]

Name:
{student.profile.full_name}

Grade:
{student.profile.grade}

[Lesson]

Title:
{lesson.overview.title}

Objectives:
{models_to_json_str(lesson.objectives)}

Materials:
{models_to_json_str(lesson.materials)}

[Instructional Modifications]

{modifications_json}
""".strip()
