"""Low-level helpers (JSON extraction, debug logging)."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


class LLMJsonParseError(Exception):
    """Failed to extract or parse JSON from an LLM response."""


def extract_json_string(text: str) -> str:
    """
    Extract a JSON object or array from LLM output.

    Supports ```json fences, generic ``` fences, or raw balanced { } / [ ].
    """

    if not text:
        raise LLMJsonParseError("LLM response is empty")

    text = text.strip()

    json_block = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    if json_block:
        return json_block.group(1).strip()

    generic_block = re.search(r"```\s*([\s\S]*?)\s*```", text)
    if generic_block:
        return generic_block.group(1).strip()

    start_idx = None
    for i, ch in enumerate(text):
        if ch in ("{", "["):
            start_idx = i
            break

    if start_idx is None:
        raise LLMJsonParseError(
            f"No JSON structure found.\n\nRAW RESPONSE:\n{text}"
        )

    opening = text[start_idx]
    closing = "}" if opening == "{" else "]"

    depth = 0
    in_string = False
    escape = False

    for i in range(start_idx, len(text)):
        ch = text[i]

        if escape:
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == opening:
            depth += 1
        elif ch == closing:
            depth -= 1
            if depth == 0:
                return text[start_idx : i + 1]

    raise LLMJsonParseError(
        f"Unbalanced JSON structure.\n\nRAW RESPONSE:\n{text}"
    )


def debug_log(title: str, body: str) -> None:
    """Write debug output to stderr (matches prior engine behavior)."""

    sys.stderr.write(f"{title}\n{body}\n\n")
    sys.stderr.flush()


def debug_json(title: str, payload: Any) -> None:
    """Pretty-print JSON debug output."""

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    debug_log(title, text)
