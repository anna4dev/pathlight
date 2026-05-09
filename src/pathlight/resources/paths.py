"""Filesystem layout for bundled JSON data (repo `data/` directory)."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Repository root (contains ``data/``, ``src/``).

    Resolved from ``pathlight/resources/paths.py`` → ``.../src/pathlight/resources`` → four parents up.
    """

    return Path(__file__).resolve().parent.parent.parent.parent


def data_dir() -> Path:
    return repo_root() / "data"
