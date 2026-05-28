"""Resource catalog and read handlers for MCP resource URIs."""

from __future__ import annotations

import json
import re
from typing import Any

import mcp.types as types

from src.pathlight.models import Lesson, Student
from src.pathlight.resources.lessons import list_lesson_ids, load_lesson
from src.pathlight.resources.students import list_student_ids, load_student


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return value or "item"


def _student_plaafp_id(index: int, domain: str) -> str:
    return f"{index}_{_slug(domain)}"


def _lesson_question_id(index: int) -> str:
    return f"q{index}"


def _lesson_formative_checks_with_ids(lesson: Lesson) -> list[dict[str, Any]]:
    return [
        {"question_id": _lesson_question_id(i + 1), **item.model_dump()}
        for i, item in enumerate(lesson.formative_checks)
    ]


def _find_formative_check_by_id(lesson: Lesson, question_id: str) -> dict[str, Any] | None:
    for i, item in enumerate(lesson.formative_checks, start=1):
        current_id = _lesson_question_id(i)
        if current_id == question_id:
            return {"question_id": current_id, **item.model_dump()}
    return None


def _student_instructional_core_payload(student: Student) -> dict[str, Any]:
    return {
        "student_id": student.id,
        "profile": {
            "full_name": student.profile.full_name,
            "grade": student.profile.grade,
            "disability_categories": student.profile.disability_categories,
            "primary_language": student.profile.primary_language,
            "english_learner": student.profile.english_learner,
            "assistive_tech_required": student.profile.assistive_tech_required,
            "placement": student.profile.placement,
        },
        "plaafp": [item.model_dump() for item in student.plaafp],
        "goals": [item.model_dump() for item in student.goals],
        "accommodations": [item.model_dump() for item in student.accommodations],
    }


def _lesson_phase_scope_payload(lesson: Lesson, phase_id: str) -> dict[str, Any]:
    phase = next((item for item in lesson.phases if item.phase_id == phase_id), None)
    if not phase:
        raise ValueError(f"Unknown phase id '{phase_id}' for lesson '{lesson.id}'")

    return {
        "lesson_id": lesson.id,
        "overview": lesson.overview.model_dump(),
        "objectives": [item.model_dump() for item in lesson.objectives],
        "phase": phase.model_dump(),
        "materials": lesson.materials,
        "formative_checks": _lesson_formative_checks_with_ids(lesson),
    }


def _lesson_overview_payload(lesson: Lesson) -> dict[str, Any]:
    total_duration_minutes = sum(phase.duration_minutes for phase in lesson.phases)
    objective_summary = " ".join(objective.statement for objective in lesson.objectives)

    return {
        "lesson_id": lesson.id,
        "grade": lesson.overview.grade,
        "subject": "ELA",
        "unit_topic": {
            "unit": lesson.overview.unit,
            "topic": lesson.overview.title,
        },
        "duration_minutes": total_duration_minutes,
        "instructional_objective_summary": objective_summary,
        "raw_overview": lesson.overview.model_dump(),
    }


def _list_student_resources(student_id: str) -> list[types.Resource]:
    student = load_student(student_id)

    resources: list[types.Resource] = [
        types.Resource(uri=f"student://{student_id}/full", name=f"Student Full Profile: {student_id}", mimeType="application/json"),
        types.Resource(uri=f"student://{student_id}/profile", name=f"Student Profile: {student_id}", mimeType="application/json"),
        types.Resource(uri=f"student://{student_id}/plaafp", name=f"Student PLAAFP: {student_id}", mimeType="application/json"),
        types.Resource(uri=f"student://{student_id}/goals", name=f"Student Goals: {student_id}", mimeType="application/json"),
        types.Resource(uri=f"student://{student_id}/accommodations", name=f"Student Accommodations: {student_id}", mimeType="application/json"),
        types.Resource(uri=f"student://{student_id}/services", name=f"Student Services: {student_id}", mimeType="application/json"),
        types.Resource(uri=f"student://{student_id}/assessment_accommodations", name=f"Student Assessment Accommodations: {student_id}", mimeType="application/json"),
        types.Resource(uri=f"student://{student_id}/key_dates", name=f"Student Key Dates: {student_id}", mimeType="application/json"),
        types.Resource(uri=f"student://{student_id}/scopes/instructional_core", name=f"Student Instructional Scope: {student_id}", mimeType="application/json"),
    ]

    for goal in student.goals:
        resources.append(
            types.Resource(
                uri=f"student://{student_id}/goals/{goal.id}",
                name=f"Student Goal {goal.id}: {student_id}",
                mimeType="application/json",
            )
        )

    for accommodation in student.accommodations:
        resources.append(
            types.Resource(
                uri=f"student://{student_id}/accommodations/{accommodation.id}",
                name=f"Student Accommodation {accommodation.id}: {student_id}",
                mimeType="application/json",
            )
        )

    for i, plaafp in enumerate(student.plaafp, start=1):
        section_id = _student_plaafp_id(i, plaafp.domain)
        resources.append(
            types.Resource(
                uri=f"student://{student_id}/plaafp/{section_id}",
                name=f"Student PLAAFP {section_id}: {student_id}",
                mimeType="application/json",
            )
        )

    return resources


def _list_lesson_resources(lesson_id: str) -> list[types.Resource]:
    lesson = load_lesson(lesson_id)

    resources: list[types.Resource] = [
        types.Resource(uri=f"lesson://{lesson_id}/full", name=f"Lesson Full Plan: {lesson_id}", mimeType="application/json"),
        types.Resource(uri=f"lesson://{lesson_id}/overview", name=f"Lesson Overview: {lesson_id}", mimeType="application/json"),
        types.Resource(uri=f"lesson://{lesson_id}/objectives", name=f"Lesson Objectives: {lesson_id}", mimeType="application/json"),
        types.Resource(uri=f"lesson://{lesson_id}/key_terms", name=f"Lesson Key Terms: {lesson_id}", mimeType="application/json"),
        types.Resource(uri=f"lesson://{lesson_id}/phases", name=f"Lesson Phases: {lesson_id}", mimeType="application/json"),
        types.Resource(uri=f"lesson://{lesson_id}/materials", name=f"Lesson Materials: {lesson_id}", mimeType="application/json"),
        types.Resource(uri=f"lesson://{lesson_id}/formative_checks", name=f"Lesson Formative Checks: {lesson_id}", mimeType="application/json"),
    ]

    for phase in lesson.phases:
        resources.append(
            types.Resource(
                uri=f"lesson://{lesson_id}/phases/{phase.phase_id}",
                name=f"Lesson Phase {phase.phase_id}: {lesson_id}",
                mimeType="application/json",
            )
        )
        resources.append(
            types.Resource(
                uri=f"lesson://{lesson_id}/scopes/phase/{phase.phase_id}",
                name=f"Lesson Scoped Context {phase.phase_id}: {lesson_id}",
                mimeType="application/json",
            )
        )

    for i, _ in enumerate(lesson.formative_checks, start=1):
        question_id = _lesson_question_id(i)
        resources.append(
            types.Resource(
                uri=f"lesson://{lesson_id}/questions/{question_id}",
                name=f"Lesson Question {question_id}: {lesson_id}",
                mimeType="application/json",
            )
        )

    return resources


def list_resource_catalog() -> list[types.Resource]:
    resources: list[types.Resource] = []
    for student_id in list_student_ids():
        resources.extend(_list_student_resources(student_id))
    for lesson_id in list_lesson_ids():
        resources.extend(_list_lesson_resources(lesson_id))
    return resources


def read_resource_payload(uri: Any) -> str:
    uri_str = str(uri)

    if uri_str.startswith("student://"):
        path = uri_str.removeprefix("student://")
        parts = [part for part in path.split("/") if part]
        if len(parts) < 2:
            raise ValueError(f"Invalid student resource URI: {uri}")

        student_id = parts[0]
        section = parts[1]
        student = load_student(student_id)

        if section == "full":
            if len(parts) != 2:
                raise ValueError(f"Invalid student full URI: {uri}")
            return student.model_dump_json()
        if section == "profile":
            if len(parts) != 2:
                raise ValueError(f"Invalid student profile URI: {uri}")
            return student.profile.model_dump_json()
        if section == "plaafp":
            if len(parts) == 2:
                return _json_dump([item.model_dump() for item in student.plaafp])
            if len(parts) == 3:
                target_id = parts[2]
                for i, item in enumerate(student.plaafp, start=1):
                    if _student_plaafp_id(i, item.domain) == target_id:
                        return item.model_dump_json()
                raise ValueError(f"Unknown PLAAFP id '{target_id}' for student '{student_id}'")
            raise ValueError(f"Invalid student plaafp URI: {uri}")
        if section == "goals":
            if len(parts) == 2:
                return _json_dump([item.model_dump() for item in student.goals])
            if len(parts) == 3:
                target_id = parts[2]
                for item in student.goals:
                    if item.id == target_id:
                        return item.model_dump_json()
                raise ValueError(f"Unknown goal id '{target_id}' for student '{student_id}'")
            raise ValueError(f"Invalid student goals URI: {uri}")
        if section == "accommodations":
            if len(parts) == 2:
                return _json_dump([item.model_dump() for item in student.accommodations])
            if len(parts) == 3:
                target_id = parts[2]
                for item in student.accommodations:
                    if item.id == target_id:
                        return item.model_dump_json()
                raise ValueError(
                    f"Unknown accommodation id '{target_id}' for student '{student_id}'"
                )
            raise ValueError(f"Invalid student accommodations URI: {uri}")
        if section == "services":
            if len(parts) != 2:
                raise ValueError(f"Invalid student services URI: {uri}")
            return _json_dump([item.model_dump() for item in student.services])
        if section == "assessment_accommodations":
            if len(parts) != 2:
                raise ValueError(f"Invalid student assessment_accommodations URI: {uri}")
            return _json_dump([item.model_dump() for item in student.assessment_accommodations])
        if section == "key_dates":
            if len(parts) != 2:
                raise ValueError(f"Invalid student key_dates URI: {uri}")
            return student.key_dates.model_dump_json()
        if section == "scopes":
            if len(parts) == 3 and parts[2] == "instructional_core":
                return _json_dump(_student_instructional_core_payload(student))
            raise ValueError(f"Unknown student scope in URI: {uri}")
        raise ValueError(f"Unknown student section '{section}' in URI: {uri}")

    if uri_str.startswith("lesson://"):
        path = uri_str.removeprefix("lesson://")
        parts = [part for part in path.split("/") if part]
        if len(parts) < 2:
            raise ValueError(f"Invalid lesson resource URI: {uri}")

        lesson_id = parts[0]
        section = parts[1]
        lesson = load_lesson(lesson_id)

        if section == "full":
            if len(parts) != 2:
                raise ValueError(f"Invalid lesson full URI: {uri}")
            return lesson.model_dump_json()
        if section == "overview":
            if len(parts) != 2:
                raise ValueError(f"Invalid lesson overview URI: {uri}")
            return _json_dump(_lesson_overview_payload(lesson))
        if section == "objectives":
            if len(parts) != 2:
                raise ValueError(f"Invalid lesson objectives URI: {uri}")
            return _json_dump([item.model_dump() for item in lesson.objectives])
        if section == "key_terms":
            if len(parts) != 2:
                raise ValueError(f"Invalid lesson key_terms URI: {uri}")
            return _json_dump([item.model_dump() for item in lesson.key_term])
        if section == "phases":
            if len(parts) == 2:
                return _json_dump([item.model_dump() for item in lesson.phases])
            if len(parts) == 3:
                target_id = parts[2]
                for item in lesson.phases:
                    if item.phase_id == target_id:
                        return item.model_dump_json()
                raise ValueError(f"Unknown phase id '{target_id}' for lesson '{lesson_id}'")
            raise ValueError(f"Invalid lesson phases URI: {uri}")
        if section == "materials":
            if len(parts) != 2:
                raise ValueError(f"Invalid lesson materials URI: {uri}")
            return _json_dump(lesson.materials)
        if section == "formative_checks":
            if len(parts) != 2:
                raise ValueError(f"Invalid lesson formative_checks URI: {uri}")
            return _json_dump(_lesson_formative_checks_with_ids(lesson))
        if section == "questions":
            if len(parts) != 3:
                raise ValueError(f"Invalid lesson questions URI: {uri}")
            question_id = parts[2]
            payload = _find_formative_check_by_id(lesson, question_id)
            if not payload:
                raise ValueError(f"Unknown question id '{question_id}' for lesson '{lesson_id}'")
            return _json_dump(payload)
        if section == "scopes":
            if len(parts) == 4 and parts[2] == "phase":
                phase_id = parts[3]
                return _json_dump(_lesson_phase_scope_payload(lesson, phase_id))
            raise ValueError(f"Unknown lesson scope in URI: {uri}")
        raise ValueError(f"Unknown lesson section '{section}' in URI: {uri}")

    raise ValueError(f"Unknown resource: {uri}")
