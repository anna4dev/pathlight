"""Deterministic renderer: TeacherDeliverable -> teacher-facing markdown checklist.

The rendering is pure and order-preserving so the same deliverable always
produces the same artifact (easy diffing, regression testing, reproducibility).
"""

from __future__ import annotations

from pathlight.schemas.deliverable import TeacherDeliverable


def _ref_suffix(ref: str | None) -> str:
    return f"  ({ref})" if ref else ""


def render_teacher_markdown(deliverable: TeacherDeliverable) -> str:
    lines: list[str] = []
    lines.append("# Teacher Lesson Adaptation")
    lines.append("")
    lines.append(f"- Student: {deliverable.student_id}")
    lines.append(f"- Lesson: {deliverable.lesson_id}")
    lines.append("")

    lines.append("## Before Class")
    if deliverable.before_class_checklist:
        for item in deliverable.before_class_checklist:
            lines.append(f"- [ ] {item.action}{_ref_suffix(item.accommodation_ref)}")
    else:
        lines.append("- (none)")
    lines.append("")

    for phase in deliverable.by_phase:
        lines.append(f"## Phase: {phase.phase_id}")

        lines.append("Teacher actions:")
        if phase.teacher_actions:
            for action in phase.teacher_actions:
                lines.append(f"- {action}")
        else:
            lines.append("- (none)")

        if phase.scaffolded_questions:
            lines.append("Scaffolded questions:")
            for question in phase.scaffolded_questions:
                lines.append(f"- [{question.question_id}] {question.original}")
                lines.append(f"  -> {question.scaffolded}")

        if phase.accommodation_reminders:
            lines.append("Accommodation reminders:")
            for reminder in phase.accommodation_reminders:
                lines.append(f"- {reminder.label}{_ref_suffix(reminder.source)}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
