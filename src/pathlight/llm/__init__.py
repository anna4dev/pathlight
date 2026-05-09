"""LLM client implementations and protocol."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class JsonLLMClient(Protocol):
    """Minimal contract for structured JSON completion used by domain services."""

    async def fetch_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        max_tokens: int = 2048,
    ) -> T:
        ...


__all__ = ["JsonLLMClient", "T"]
