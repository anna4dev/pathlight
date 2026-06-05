"""MCP prompt templates (client-facing), separate from LLM prompts under services/."""

from pathlight.prompts.registry import get_mcp_prompt_result, list_mcp_prompts

__all__ = ["get_mcp_prompt_result", "list_mcp_prompts"]
