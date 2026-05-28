"""MCP resource backing: paths and JSON loaders for students and lessons."""

from .lessons import (
    get_lesson_path,
    lessons_dir,
    list_lesson_ids,
    load_lesson,
)
from .gateway import (
    list_resource_catalog,
    read_resource_payload,
)
from .students import (
    get_student_path,
    list_student_ids,
    load_student,
    students_dir,
)

__all__ = [
    "get_lesson_path",
    "get_student_path",
    "lessons_dir",
    "list_lesson_ids",
    "list_student_ids",
    "list_resource_catalog",
    "load_lesson",
    "load_student",
    "read_resource_payload",
    "students_dir",
]
