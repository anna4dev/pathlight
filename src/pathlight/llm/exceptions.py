"""LLM response validation errors (shared by JSON clients)."""

from pydantic import ValidationError


class LLMResponseValidationError(Exception):
    """Parsed JSON failed Pydantic validation."""

    @classmethod
    def from_validation(
        cls,
        err: ValidationError,
        parsed: object,
    ) -> "LLMResponseValidationError":
        import json

        return cls(
            "Response schema validation failed.\n\n"
            f"ERROR:\n{err}\n\n"
            f"PARSED DATA:\n{json.dumps(parsed, indent=2, ensure_ascii=False)}"
        )
