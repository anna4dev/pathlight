"""Load student IEP JSON from ``data/students/``."""

from __future__ import annotations

from pathlib import Path

from src.pathlight.models import Student

from .paths import data_dir


def students_dir() -> Path:
    return data_dir() / "students"


def get_student_path(student_id: str) -> Path:
    return students_dir() / f"{student_id}.json"


def list_student_ids() -> list[str]:
    """Basenames of ``*.json`` under ``data/students/`` (sorted)."""

    d = students_dir()
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def load_student(student_id: str) -> Student:
    path = get_student_path(student_id)
    if not path.exists():
        raise FileNotFoundError(f"Student {student_id} not found at {path}")
    with open(path, encoding="utf-8") as f:
        return Student.model_validate_json(f.read())
