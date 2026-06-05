"""Semantic validation for the teacher deliverable (Phase 5).

Pydantic (`TeacherDeliverable`) is the *first* gate: shape, required sections,
no unknown keys, strict types. These checks are the *second* gate: they verify
the draft is grounded in the actual student IEP and lesson, beyond mere shape.

All checks are deterministic and pure (no LLM). The result is a structured
report so Claude can self-correct only the failing sections, or surface the
issues to the teacher.

Categories (see README "Validation Contract" / ARCHITECTURE Layer 3):
- IEP grounding: accommodation references resolve to real accommodation ids
- accommodation coverage: every IEP accommodation is represented in the plan
- lesson-question references: scaffolded questions cite real lesson question ids
- unsupported output: phase ids / question ids not present in the lesson
"""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel

from pathlight.models import Lesson, Student
from pathlight.schemas.deliverable import TeacherDeliverable

ERROR = "error"
WARNING = "warning"

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_PAGE_RE = re.compile(r"p\.?\s*(\d+)", re.IGNORECASE)


class ValidationIssue(BaseModel):
    code: str
    severity: str  # "error" | "warning"
    location: str  # dotted path into the deliverable, e.g. "by_phase[0].phase_id"
    message: str
    found: Optional[str] = None
    expected: Optional[List[str]] = None


class ValidationReport(BaseModel):
    ok: bool  # True only when there are no error-severity issues
    error_count: int
    warning_count: int
    issues: List[ValidationIssue]


def _ref_tokens(ref: str) -> list[str]:
    return _TOKEN_RE.findall(ref or "")


def _ref_page(ref: str) -> int | None:
    match = _PAGE_RE.search(ref or "")
    return int(match.group(1)) if match else None


def _question_text_by_id(lesson: Lesson) -> dict[str, str]:
    # Mirrors the `qN` convention used by the resource gateway.
    return {f"q{i}": fc.question for i, fc in enumerate(lesson.formative_checks, start=1)}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _check_ref_grounding(
    ref: str,
    location: str,
    known_accommodations: dict[str, int | None],
    issues: list[ValidationIssue],
) -> set[str]:
    """Validate one accommodation reference string; return matched ids."""
    tokens = _ref_tokens(ref)
    matched = {token for token in tokens if token in known_accommodations}
    if not matched:
        issues.append(
            ValidationIssue(
                code="ungrounded_accommodation_ref",
                severity=ERROR,
                location=location,
                message=(
                    f"Reference {ref!r} does not cite any real accommodation id."
                ),
                found=ref,
                expected=sorted(known_accommodations),
            )
        )
        return set()

    page = _ref_page(ref)
    for acc_id in matched:
        source_page = known_accommodations.get(acc_id)
        if page is not None and source_page is not None and page != source_page:
            issues.append(
                ValidationIssue(
                    code="accommodation_page_mismatch",
                    severity=WARNING,
                    location=location,
                    message=(
                        f"Reference cites p.{page} but accommodation {acc_id} "
                        f"is on p.{source_page}."
                    ),
                    found=ref,
                    expected=[f"{acc_id} (p.{source_page})"],
                )
            )
    return matched


def validate_deliverable(
    deliverable: TeacherDeliverable,
    student: Student,
    lesson: Lesson,
) -> ValidationReport:
    issues: list[ValidationIssue] = []

    known_accommodations: dict[str, int | None] = {
        acc.id: acc.source_page for acc in student.accommodations
    }
    valid_phase_ids = {phase.phase_id for phase in lesson.phases}
    question_text_by_id = _question_text_by_id(lesson)

    referenced_accommodations: set[str] = set()

    # Before-class checklist: grounding of optional accommodation refs.
    for i, item in enumerate(deliverable.before_class_checklist):
        if item.accommodation_ref:
            referenced_accommodations |= _check_ref_grounding(
                item.accommodation_ref,
                f"before_class_checklist[{i}].accommodation_ref",
                known_accommodations,
                issues,
            )

    # Per-phase checks.
    for p, phase in enumerate(deliverable.by_phase):
        if phase.phase_id not in valid_phase_ids:
            issues.append(
                ValidationIssue(
                    code="unknown_phase_id",
                    severity=ERROR,
                    location=f"by_phase[{p}].phase_id",
                    message=f"Phase id {phase.phase_id!r} is not in the lesson.",
                    found=phase.phase_id,
                    expected=sorted(valid_phase_ids),
                )
            )

        for q, question in enumerate(phase.scaffolded_questions):
            loc = f"by_phase[{p}].scaffolded_questions[{q}]"
            if question.question_id not in question_text_by_id:
                issues.append(
                    ValidationIssue(
                        code="unknown_question_id",
                        severity=ERROR,
                        location=f"{loc}.question_id",
                        message=(
                            f"Question id {question.question_id!r} is not in the lesson."
                        ),
                        found=question.question_id,
                        expected=sorted(question_text_by_id),
                    )
                )
            elif _normalize(question.original) != _normalize(
                question_text_by_id[question.question_id]
            ):
                issues.append(
                    ValidationIssue(
                        code="question_text_mismatch",
                        severity=WARNING,
                        location=f"{loc}.original",
                        message=(
                            f"`original` does not match the lesson text for "
                            f"{question.question_id}."
                        ),
                        found=question.original,
                        expected=[question_text_by_id[question.question_id]],
                    )
                )

        for r, reminder in enumerate(phase.accommodation_reminders):
            if reminder.source:
                referenced_accommodations |= _check_ref_grounding(
                    reminder.source,
                    f"by_phase[{p}].accommodation_reminders[{r}].source",
                    known_accommodations,
                    issues,
                )

    # Accommodation coverage: advisory, not blocking (not every accommodation
    # necessarily applies to a single lesson).
    uncovered = sorted(set(known_accommodations) - referenced_accommodations)
    if uncovered:
        issues.append(
            ValidationIssue(
                code="uncovered_accommodations",
                severity=WARNING,
                location="before_class_checklist / by_phase[*].accommodation_reminders",
                message=(
                    "Some IEP accommodations are not referenced anywhere in the plan."
                ),
                expected=uncovered,
            )
        )

    error_count = sum(1 for issue in issues if issue.severity == ERROR)
    warning_count = sum(1 for issue in issues if issue.severity == WARNING)
    return ValidationReport(
        ok=error_count == 0,
        error_count=error_count,
        warning_count=warning_count,
        issues=issues,
    )
