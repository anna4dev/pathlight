"""MCP prompt: Claude-first IEP-grounded lesson adaptation (Shape A)."""

from __future__ import annotations

import mcp.types as types

NAME = "analyze_student_lesson"
DESCRIPTION = (
    "Draft an IEP-grounded, teacher-usable lesson adaptation for one student and one "
    "lesson. Claude reasons directly over MCP resources (Shape A)."
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


def _build_prompt_text(student_id: str, lesson_id: str) -> str:
    return f"""\
You are helping a teacher adapt one lesson for one student with an IEP.
You are the reasoning engine. The MCP server only provides grounded context;
do all instructional reasoning yourself. Do not call any server-side
"generate_*" workflow tools.

Target:
- student_id: {student_id}
- lesson_id: {lesson_id}

## Step 1 — Read context first (scoped MCP resources)
Read these resources before reasoning:
- `student://{student_id}/scopes/instructional_core`
  (profile teaching context, PLAAFP, goals, accommodations)
- `lesson://{lesson_id}/overview` (grade, duration, objective summary)
- `lesson://{lesson_id}/phases` (to enumerate phase ids)
Then, for each phase id, read the cross-resource slice:
- `student://{student_id}/scopes/lesson/{lesson_id}/phase/<phase_id>`
  (phase + formative questions + the student's instructional core in one read)
Use `lesson://{lesson_id}/questions/<qN>` if you need a specific question verbatim.

## Step 2 — Draft a structured deliverable (not prose)
Produce a single JSON draft with this shape:
{{
  "student_id": "{student_id}",
  "lesson_id": "{lesson_id}",
  "before_class_checklist": [
    {{"action": "...", "accommodation_ref": "acc_xx (p.NN)"}}
  ],
  "by_phase": [
    {{
      "phase_id": "...",
      "teacher_actions": ["..."],
      "scaffolded_questions": [
        {{"question_id": "qN", "original": "...", "scaffolded": "..."}}
      ],
      "accommodation_reminders": [
        {{"label": "...", "source": "acc_xx (p.NN)"}}
      ]
    }}
  ]
}}

## Step 3 — Self-validate before finalizing
Before presenting the draft, verify and fix:
- Grounding: every action/reminder traces to a real IEP item (goal/PLAAFP/accommodation id).
- Accommodation coverage: required accommodations from instructional_core are represented.
- Lesson-question references: each scaffolded_questions item cites a real `question_id`.
- No unsupported output: do not invent materials, accommodations, or questions absent from the resources.
If any check fails, revise that section and re-check.

## Step 4 — Render the canonical artifact
Once the draft passes self-validation, call the `render_teacher_artifact` tool
with the JSON draft as arguments. This validates the draft against the v1
output contract and returns a deterministic markdown checklist. Present that
rendered markdown to the teacher as the final deliverable; do not hand-format
your own version of the checklist.

## Step 5 — Human-in-the-loop
Treat the output as a draft. The teacher may edit, reject, or ask you to
regenerate only one section (e.g. one phase's actions, or the checklist).
When regenerating a section, keep all accepted sections unchanged and
re-render via `render_teacher_artifact`.
"""


def mcp_get_prompt_result(arguments: dict[str, str] | None) -> types.GetPromptResult:
    if not arguments:
        raise ValueError("Missing arguments")

    s_id = arguments["student_id"]
    l_id = arguments["lesson_id"]

    return types.GetPromptResult(
        description=f"Claude-first lesson adaptation for lesson {l_id} and student {s_id}",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=_build_prompt_text(s_id, l_id)),
            )
        ],
    )
