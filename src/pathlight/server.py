import asyncio
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from pathlight.llm.groq import GroqClient
from pathlight.prompts import get_mcp_prompt_result, list_mcp_prompts
from pathlight.resources.gateway import list_resource_catalog, read_resource_payload
from pathlight.services.briefing.service import BriefingService
from pathlight.services.conflicts.service import ConflictService
from pathlight.services.modifications.service import ModificationService
from pathlight.services.workflow.service import LessonAdaptationWorkflowService
from pathlight.tools import ToolContext, build_tools, dispatch_tool

server = Server("pathlight")

_llm = GroqClient()
_conflict_service = ConflictService(_llm)
_modification_service = ModificationService(_llm)
_briefing_service = BriefingService(_llm)
_workflow_service = LessonAdaptationWorkflowService(
    conflict_service=_conflict_service,
    modification_service=_modification_service,
    briefing_service=_briefing_service,
)

_TOOL_CTX = ToolContext(
    conflict_service=_conflict_service,
    modification_service=_modification_service,
    briefing_service=_briefing_service,
    workflow_service=_workflow_service,
)


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return list_resource_catalog()


@server.read_resource()
async def handle_read_resource(uri: Any) -> str:
    return read_resource_payload(uri)


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return build_tools()


@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict | None,
) -> list[types.TextContent]:
    try:
        return await dispatch_tool(_TOOL_CTX, name, arguments)
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return list_mcp_prompts()


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    return get_mcp_prompt_result(name, arguments)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="pathlight",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def run() -> None:
    """Synchronous entry point for the ``pathlight`` console script."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
