#!/usr/bin/env python3
"""mcp_server.py — MCP server exposing every tool in tools.py.

Every tool registered in tools.TOOLS (etymonline, axiom,
power_connection, donation_station, suprememath, notion) becomes
available to any MCP client — Claude Desktop, Claude Code, etc. — with
its existing name/description/input_schema unchanged. Each call is
routed through tools.dispatch(), so the same error handling used by the
Anthropic tool-use wrapper applies here too: dispatch()'s "is_error"
flag maps directly onto MCP's CallToolResult.is_error.

Usage:
  python mcp_server.py

Point an MCP client at this script over stdio, e.g. in Claude Desktop's
claude_desktop_config.json:

  {
    "mcpServers": {
      "repo-tools": {
        "command": "python",
        "args": ["/absolute/path/to/mcp_server.py"]
      }
    }
  }
"""

import asyncio
import json

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.types import (
    CallToolRequest,
    CallToolRequestParams,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    PaginatedRequestParams,
    TextContent,
    Tool,
)

import tools

server = Server("repo-tools")


async def list_tools() -> list[Tool]:
    return [
        Tool(
            name=spec["name"],
            description=spec["description"],
            input_schema=spec["input_schema"],
        )
        for spec in tools.TOOLS
    ]


async def call_tool(name: str, arguments: dict) -> CallToolResult:
    outcome = tools.dispatch(name, arguments or {})
    content = outcome["content"]
    text = content if isinstance(content, str) else json.dumps(content, indent=2)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        is_error=outcome["is_error"],
    )


async def _handle_list_tools(ctx, params: PaginatedRequestParams) -> ListToolsResult:
    return ListToolsResult(tools=await list_tools())


async def _handle_call_tool(ctx, params: CallToolRequestParams) -> CallToolResult:
    return await call_tool(params.name, dict(params.arguments or {}))


server.add_request_handler("tools/list", PaginatedRequestParams, _handle_list_tools)
server.add_request_handler("tools/call", CallToolRequestParams, _handle_call_tool)


async def _run():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
