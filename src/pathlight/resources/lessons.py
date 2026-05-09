"""Load lesson JSON from ``data/lessons/``."""

from __future__ import annotations

from pathlib import Path

from src.pathlight.models import Lesson

from .paths import data_dir


def lessons_dir() -> Path:
    return data_dir() / "lessons"


def get_lesson_path(lesson_id: str) -> Path:
    return lessons_dir() / f"{lesson_id}.json"


def list_lesson_ids() -> list[str]:
    """Basenames of ``*.json`` under ``data/lessons/`` (sorted)."""

    d = lessons_dir()
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def load_lesson(lesson_id: str) -> Lesson:
    path = get_lesson_path(lesson_id)
    if not path.exists():
        raise FileNotFoundError(f"Lesson {lesson_id} not found at {path}")
    with open(path, encoding="utf-8") as f:
        return Lesson.model_validate_json(f.read())
