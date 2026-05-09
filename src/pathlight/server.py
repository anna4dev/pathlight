import asyncio
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from src.pathlight.llm.groq import GroqClient
from src.pathlight.prompts import get_mcp_prompt_result, list_mcp_prompts
from src.pathlight.resources import list_lesson_ids, list_student_ids, load_lesson, load_student
from src.pathlight.services.briefing.service import BriefingService
from src.pathlight.services.conflicts.service import ConflictService
from src.pathlight.services.modifications.service import ModificationService
from src.pathlight.services.workflow.service import LessonAdaptationWorkflowService
from src.pathlight.tools import ToolContext, build_tools, dispatch_tool

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
    resources = []

    for s_id in list_student_ids():
        resources.append(
            types.Resource(
                uri=f"student://{s_id}/full",
                name=f"Student Profile: {s_id}",
                mimeType="application/json",
            )
        )

    for l_id in list_lesson_ids():
        resources.append(
            types.Resource(
                uri=f"lesson://{l_id}/full",
                name=f"Lesson Plan: {l_id}",
                mimeType="application/json",
            )
        )

    return resources


@server.read_resource()
async def handle_read_resource(uri: Any) -> str:
    uri_str = str(uri)

    if uri_str.startswith("student://"):
        student_id = uri_str.split("/")[2]
        return load_student(student_id).model_dump_json()
    if uri_str.startswith("lesson://"):
        lesson_id = uri_str.split("/")[2]
        return load_lesson(lesson_id).model_dump_json()

    raise ValueError(f"Unknown resource: {uri}")


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


if __name__ == "__main__":
    asyncio.run(main())
