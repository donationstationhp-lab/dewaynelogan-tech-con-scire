"""Unit tests for tools.py — the unified Claude tool-use registry.

Run with:
  pip install pytest
  pytest tests/
"""

import os
import sys
import unittest
from unittest.mock import patch

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import axiom_tool
import donation_station_tool
import etymonline_tool
import notion_tool
import power_connection_tool
import suprememath_tool
import tools


class TestRegistry(unittest.TestCase):
    def test_combines_every_module(self):
        expected = sum(len(m.TOOLS) for m in (
            etymonline_tool, axiom_tool, power_connection_tool,
            donation_station_tool, suprememath_tool, notion_tool,
        ))
        self.assertEqual(len(tools.TOOLS), expected)

    def test_no_duplicate_names(self):
        names = [spec["name"] for spec in tools.TOOLS]
        self.assertEqual(len(names), len(set(names)))

    def test_every_module_tool_is_present(self):
        registered = {spec["name"] for spec in tools.TOOLS}
        for mod in (etymonline_tool, axiom_tool, power_connection_tool,
                    donation_station_tool, suprememath_tool, notion_tool):
            for spec in mod.TOOLS:
                self.assertIn(spec["name"], registered)


class TestDispatchRouting(unittest.TestCase):
    def test_unknown_tool(self):
        outcome = tools.dispatch("not_a_real_tool", {})
        self.assertTrue(outcome["is_error"])
        self.assertIn("Unknown tool", outcome["content"])

    def test_routes_axiom_tool_to_axiom_module(self):
        outcome = tools.dispatch("axiom_get_dimensions", {})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(len(outcome["content"]["dimensions"]), 10)

    @patch("power_connection_tool.pc.calculate")
    def test_routes_power_connection_tool_to_its_module(self, mock_calc):
        mock_calc.return_value = {"born": 8}
        outcome = tools.dispatch("power_connection_calculate", {"month": 5, "day": 6, "year": 2026})
        self.assertFalse(outcome["is_error"])
        mock_calc.assert_called_once_with(5, 6, 2026)

    @patch("donation_station_tool.ds.report")
    def test_routes_donation_station_tool_to_its_module(self, mock_report):
        mock_report.return_value = {"total": 3}
        outcome = tools.dispatch("donation_station_report", {})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["total"], 3)

    @patch("etymonline_tool.ety.search")
    def test_routes_etymonline_tool_to_its_module(self, mock_search):
        mock_search.return_value = ([], False)
        outcome = tools.dispatch("etymonline_search", {"query": "galaxy"})
        self.assertFalse(outcome["is_error"])


if __name__ == "__main__":
    unittest.main()
