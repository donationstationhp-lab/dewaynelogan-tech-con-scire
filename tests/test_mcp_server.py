"""Unit tests for mcp_server.py

Run with:
  pip install pytest mcp
  pytest tests/
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mcp.types as types

import mcp_server as srv
import tools


class TestListTools(unittest.IsolatedAsyncioTestCase):
    async def test_mirrors_tools_registry(self):
        listed = await srv.list_tools()
        self.assertEqual(len(listed), len(tools.TOOLS))
        for spec, tool in zip(tools.TOOLS, listed):
            self.assertEqual(tool.name, spec["name"])
            self.assertEqual(tool.description, spec["description"])
            self.assertEqual(tool.inputSchema, spec["input_schema"])

    async def test_returns_mcp_tool_instances(self):
        listed = await srv.list_tools()
        self.assertTrue(all(isinstance(t, types.Tool) for t in listed))


class TestCallTool(unittest.IsolatedAsyncioTestCase):
    @patch("mcp_server.tools.dispatch")
    async def test_success_dict_content_is_json_encoded(self, mock_dispatch):
        mock_dispatch.return_value = {"is_error": False, "content": {"born": 8}}
        result = await srv.call_tool("power_connection_calculate", {"month": 5, "day": 6, "year": 2026})
        self.assertFalse(result.isError)
        self.assertEqual(json.loads(result.content[0].text), {"born": 8})
        mock_dispatch.assert_called_once_with(
            "power_connection_calculate", {"month": 5, "day": 6, "year": 2026},
        )

    @patch("mcp_server.tools.dispatch")
    async def test_error_string_content_passed_through_unencoded(self, mock_dispatch):
        mock_dispatch.return_value = {"is_error": True, "content": "`year` is required."}
        result = await srv.call_tool("power_connection_calculate", {"month": 5, "day": 6})
        self.assertTrue(result.isError)
        self.assertEqual(result.content[0].text, "`year` is required.")

    @patch("mcp_server.tools.dispatch")
    async def test_none_arguments_becomes_empty_dict(self, mock_dispatch):
        mock_dispatch.return_value = {"is_error": False, "content": {}}
        await srv.call_tool("axiom_get_dimensions", None)
        mock_dispatch.assert_called_once_with("axiom_get_dimensions", {})

    async def test_unknown_tool_routes_through_real_dispatch(self):
        result = await srv.call_tool("not_a_real_tool", {})
        self.assertTrue(result.isError)
        self.assertIn("Unknown tool", result.content[0].text)


class TestRealProtocol(unittest.IsolatedAsyncioTestCase):
    """End-to-end sanity check over the actual MCP client/server protocol."""

    @patch("mcp_server.tools.dispatch")
    async def test_list_and_call_over_memory_transport(self, mock_dispatch):
        from mcp.shared.memory import create_connected_server_and_client_session

        mock_dispatch.return_value = {"is_error": False, "content": {"ok": True}}

        async with create_connected_server_and_client_session(srv.server) as client:
            listed = await client.list_tools()
            self.assertEqual(len(listed.tools), len(tools.TOOLS))

            result = await client.call_tool("axiom_get_dimensions", {})
            self.assertFalse(result.isError)
            self.assertEqual(json.loads(result.content[0].text), {"ok": True})


if __name__ == "__main__":
    unittest.main()
