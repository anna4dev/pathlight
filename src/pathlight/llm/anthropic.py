"""Anthropic Claude client for JSON-validated completions."""

from __future__ import annotations

import json
import os
import sys
from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import TypeAdapter, ValidationError

from pathlight.shared.utils import LLMJsonParseError, extract_json_string
from .exceptions import LLMResponseValidationError

T = TypeVar("T")

# Claude 3.5 Sonnet (and similar) API output limit for completions.
_ANTHROPIC_JSON_MAX_OUTPUT_TOKENS = 8192


class AnthropicClient:
    def __init__(self) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        # stderr only: stdout is the MCP JSON-RPC channel under stdio transport.
        print(
            f"--- DEBUG: ANTHROPIC_API_KEY is "
            f"{'SET' if self.api_key else 'NOT SET'} ---",
            file=sys.stderr,
        )
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None
        self.model = "claude-3-5-sonnet-20241022"

    async def fetch_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.2,
    ) -> str:
        if not self.client:
            raise RuntimeError("Missing ANTHROPIC_API_KEY")

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            if not response.content:
                raise RuntimeError("Empty LLM response")

            content_blocks = [
                block.text for block in response.content if hasattr(block, "text")
            ]
            content = "\n".join(content_blocks).strip()
            if not content:
                raise RuntimeError("Empty text response")
            return content

        except Exception as e:
            raise RuntimeError(f"Anthropic request failed: {str(e)}") from e

    async def fetch_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        max_tokens: int = 8192,
    ) -> T:
        json_system = f"""
        {system_prompt}

        CRITICAL:
        - Return valid JSON only
        - Do not use markdown
        - Do not wrap with ```json
        - No explanation text
        - No comments
        - No trailing text
        """.strip()

        doubled = min(max_tokens * 2, _ANTHROPIC_JSON_MAX_OUTPUT_TOKENS)
        attempt_tokens = (max_tokens, doubled) if doubled > max_tokens else (max_tokens,)

        last_err: json.JSONDecodeError | None = None
        raw_text = ""
        json_str = ""

        for budget in attempt_tokens:
            raw_text = await self.fetch_text(
                system_prompt=json_system,
                user_prompt=user_prompt,
                max_tokens=budget,
                temperature=0.1,
            )
            json_str = extract_json_string(raw_text)
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError as e:
                last_err = e
                continue
            try:
                return TypeAdapter(schema).validate_python(parsed)
            except ValidationError as e:
                raise LLMResponseValidationError.from_validation(e, parsed) from e

        raise LLMJsonParseError(
            f"Failed to parse JSON after retries.\n\nERROR:\n{last_err}\n\n"
            f"RAW RESPONSE:\n{raw_text}\n\nEXTRACTED JSON:\n{json_str}"
        ) from last_err
