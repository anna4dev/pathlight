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

## Step 1 — Fetch grounded context first (tool calls)
First, discover the lesson's phases: call `get_instructional_context` with only
- `student_id={student_id}`, `lesson_id={lesson_id}` (omit `phase_id`)
This returns the lesson overview, the list of available `phase_ids`, and the
student's instructional core.

Then, for each phase you will plan, call `get_instructional_context` again with
- `student_id={student_id}`, `lesson_id={lesson_id}`, `phase_id=<one of the phase_ids>`
This returns that phase, its formative questions (with stable `question_id`s),
and the student's instructional core — including the **real accommodation labels
and source pages** (e.g. acc_01 = "Repeat directions; copy of teacher's notes").

Base every action, scaffold, and reminder on this returned content. Do NOT
invent accommodation text or infer it from ids alone: a checklist item must
reflect what the accommodation actually says.

(The same data is also available as MCP resources, e.g.
`student://{student_id}/scopes/lesson/{lesson_id}/phase/<phase_id>`, if you
attach them manually, but the tool is the reliable path for autonomous reasoning.)

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

The contract is strict: include every key shown above, even when a section is
empty (use `[]`), and do not add keys that are not in this shape. Omitting a
section or introducing an extra/misspelled key will fail validation.

## Step 3 — Validate before finalizing
Call the `validate_teacher_artifact` tool with your JSON draft. It runs
deterministic semantic checks and returns
`{{ok, error_count, warning_count, issues[]}}`, where each issue has a
`code`, `severity`, `location`, and `message`:
- Grounding: every `accommodation_ref` / `source` resolves to a real accommodation id.
- Accommodation coverage: IEP accommodations are represented in the plan.
- Lesson-question references: each `scaffolded_questions.question_id` is a real lesson question.
- Unsupported output: no invented phase ids or question ids.
Fix every `error` issue (revise only the failing `location`) and re-run the
tool until `ok` is true. Treat `warning` issues as advice; resolve or
consciously keep them.

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
