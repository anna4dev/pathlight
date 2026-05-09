"""Reusable JSON Schema fragments for MCP tool ``inputSchema``."""

from __future__ import annotations

from typing import Any

_STUDENT_ID: dict[str, Any] = {
    "type": "string",
    "description": "e.g., 35110GST",
}

_LESSON_ID: dict[str, Any] = {
    "type": "string",
    "description": "e.g., community",
}

_PHASE_ID: dict[str, Any] = {
    "type": "string",
    "description": "Lesson phase id, e.g., during_reading",
}

_CONFLICT_ITEM: dict[str, Any] = {
    "type": "object",
    "properties": {
        "phase_id": {"type": "string"},
        "conflict_type": {"type": "string"},
        "evidence": {"type": "string"},
        "severity": {"type": "string"},
        "iep_anchor": {"type": "string"},
    },
    "required": ["phase_id", "conflict_type", "evidence", "severity", "iep_anchor"],
}

_MODIFICATION_ITEM: dict[str, Any] = {
    "type": "object",
    "properties": {
        "phase_id": {"type": "string"},
        "conflict_ref": {"type": "array", "items": {"type": "string"}},
        "modification_strategy": {"type": "string"},
        "implementation_steps": {"type": "array", "items": {"type": "string"}},
        "expected_outcome": {"type": "string"},
        "iep_anchor": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "phase_id",
        "conflict_ref",
        "modification_strategy",
        "implementation_steps",
        "expected_outcome",
        "iep_anchor",
    ],
}


def object_schema(*, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required}


def schema_student_lesson_phase() -> dict[str, Any]:
    return object_schema(
        properties={
            "student_id": _STUDENT_ID,
            "lesson_id": _LESSON_ID,
            "phase_id": _PHASE_ID,
        },
        required=["student_id", "lesson_id", "phase_id"],
    )


def schema_lesson_phase_conflicts() -> dict[str, Any]:
    return object_schema(
        properties={
            "lesson_id": _LESSON_ID,
            "phase_id": _PHASE_ID,
            "conflicts": {"type": "array", "items": _CONFLICT_ITEM},
        },
        required=["lesson_id", "phase_id", "conflicts"],
    )


def schema_student_lesson_modifications() -> dict[str, Any]:
    return object_schema(
        properties={
            "student_id": _STUDENT_ID,
            "lesson_id": _LESSON_ID,
            "modifications": {"type": "array", "items": _MODIFICATION_ITEM},
        },
        required=["student_id", "lesson_id", "modifications"],
    )


def schema_student_lesson() -> dict[str, Any]:
    return object_schema(
        properties={"student_id": _STUDENT_ID, "lesson_id": _LESSON_ID},
        required=["student_id", "lesson_id"],
    )
