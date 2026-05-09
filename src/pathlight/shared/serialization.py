"""Serialize Pydantic models and other structures for prompts and tools."""

from __future__ import annotations

import json
from typing import Any
import mcp.types as types


def models_to_json_str(data: Any) -> str:
    """
    Convert model instance(s) to a pretty-printed JSON string for LLM prompts.

    Accepts a single model with ``model_dump``, a list of such models, or plain data.
    """

    if isinstance(data, list):
        payload = [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in data
        ]
    elif hasattr(data, "model_dump"):
        payload = data.model_dump()
    else:
        payload = data

    return json.dumps(payload, indent=2, ensure_ascii=False)

def to_text_content(data) -> list[types.TextContent]:

    if isinstance(data, list):
        payload = [
            item.model_dump()
            if hasattr(item, "model_dump")
            else item
            for item in data
        ]

    elif hasattr(data, "model_dump"):
        payload = data.model_dump()

    else:
        payload = data

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                payload,
                ensure_ascii=False,
                indent=2
            )
        )
    ]