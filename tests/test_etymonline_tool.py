"""Unit tests for etymonline_tool.py

Run with:
  pip install pytest
  pytest tests/
"""

import os
import sys
import unittest
from unittest.mock import patch

import requests

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import etymonline_tool as tool

# ── Tool schema ───────────────────────────────────────────────────────────────

class TestToolSchemas(unittest.TestCase):
    def test_all_tools_have_required_fields(self):
        for spec in tool.TOOLS:
            self.assertIn("name", spec)
            self.assertIn("description", spec)
            self.assertIn("input_schema", spec)
            self.assertEqual(spec["input_schema"]["type"], "object")
            self.assertIn("properties", spec["input_schema"])

    def test_names_are_unique(self):
        names = [spec["name"] for spec in tool.TOOLS]
        self.assertEqual(len(names), len(set(names)))

    def test_every_tool_has_a_handler(self):
        names = {spec["name"] for spec in tool.TOOLS}
        self.assertEqual(names, set(tool._HANDLERS))

    def test_required_fields_are_declared_properties(self):
        for spec in tool.TOOLS:
            schema = spec["input_schema"]
            for field in schema.get("required", []):
                self.assertIn(field, schema["properties"])


# ── dispatch(): unknown tool ─────────────────────────────────────────────────

class TestDispatchUnknown(unittest.TestCase):
    def test_unknown_tool_name(self):
        outcome = tool.dispatch("not_a_real_tool", {})
        self.assertTrue(outcome["is_error"])
        self.assertIn("Unknown tool", outcome["content"])


# ── dispatch(): etymonline_search ────────────────────────────────────────────

class TestDispatchSearch(unittest.TestCase):
    @patch("etymonline_tool.ety.search")
    def test_success(self, mock_search):
        mock_search.return_value = ([{"word": "galaxy", "etymology": "..."}], False)
        outcome = tool.dispatch("etymonline_search", {"query": "galaxy"})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["query"], "galaxy")
        self.assertEqual(len(outcome["content"]["entries"]), 1)
        self.assertFalse(outcome["content"]["from_cache"])
        mock_search.assert_called_once_with("galaxy", offline=False, no_cache=False)

    @patch("etymonline_tool.ety.search")
    def test_passes_offline_and_no_cache_flags(self, mock_search):
        mock_search.return_value = ([], True)
        tool.dispatch("etymonline_search", {"query": "x", "offline": True, "no_cache": True})
        mock_search.assert_called_once_with("x", offline=True, no_cache=True)

    def test_missing_query_is_input_error(self):
        outcome = tool.dispatch("etymonline_search", {})
        self.assertTrue(outcome["is_error"])
        self.assertIn("query", outcome["content"])

    def test_blank_query_is_input_error(self):
        outcome = tool.dispatch("etymonline_search", {"query": "   "})
        self.assertTrue(outcome["is_error"])


# ── dispatch(): etymonline_look ──────────────────────────────────────────────

class TestDispatchLook(unittest.TestCase):
    @patch("etymonline_tool.ety.lookup")
    def test_success(self, mock_lookup):
        mock_lookup.return_value = (
            {"word": "robot", "entries": [{"word": "robot (n.)", "etymology": "..."}],
             "related": ["automaton"]},
            True,
        )
        outcome = tool.dispatch("etymonline_look", {"word": "robot"})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["word"], "robot")
        self.assertEqual(outcome["content"]["related"], ["automaton"])
        self.assertTrue(outcome["content"]["from_cache"])

    def test_missing_word_is_input_error(self):
        outcome = tool.dispatch("etymonline_look", {})
        self.assertTrue(outcome["is_error"])
        self.assertIn("word", outcome["content"])


# ── dispatch(): etymonline_explore ───────────────────────────────────────────

class TestDispatchExplore(unittest.TestCase):
    @patch("etymonline_tool.ety.explore")
    def test_success_default_depth(self, mock_explore):
        mock_explore.return_value = {"robot": {"word": "robot", "entries": [], "related": []}}
        outcome = tool.dispatch("etymonline_explore", {"word": "robot"})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["root"], "robot")
        mock_explore.assert_called_once_with("robot", depth=1, offline=False, no_cache=False)

    @patch("etymonline_tool.ety.explore")
    def test_custom_depth_is_passed_through(self, mock_explore):
        mock_explore.return_value = {}
        tool.dispatch("etymonline_explore", {"word": "robot", "depth": 3})
        mock_explore.assert_called_once_with("robot", depth=3, offline=False, no_cache=False)

    def test_depth_out_of_range_is_input_error(self):
        outcome = tool.dispatch("etymonline_explore", {"word": "robot", "depth": 99})
        self.assertTrue(outcome["is_error"])
        self.assertIn("depth", outcome["content"])

    def test_depth_zero_is_input_error(self):
        outcome = tool.dispatch("etymonline_explore", {"word": "robot", "depth": 0})
        self.assertTrue(outcome["is_error"])

    def test_non_integer_depth_is_input_error(self):
        outcome = tool.dispatch("etymonline_explore", {"word": "robot", "depth": "two"})
        self.assertTrue(outcome["is_error"])

    def test_bool_depth_is_input_error(self):
        # bool is a subclass of int in Python — must not sneak past the check.
        outcome = tool.dispatch("etymonline_explore", {"word": "robot", "depth": True})
        self.assertTrue(outcome["is_error"])


# ── dispatch(): etymonline_dkl_loop ──────────────────────────────────────────

class TestDispatchDklLoop(unittest.TestCase):
    @patch("etymonline_tool.ety.run_dkl_loop")
    def test_success_default_variant(self, mock_loop):
        mock_loop.return_value = (
            [("D", "DEPTH", "*root*", "body text")],
            False,
        )
        outcome = tool.dispatch("etymonline_dkl_loop", {"word": "galaxy"})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["variant"], "b")
        self.assertEqual(len(outcome["content"]["steps"]), 1)
        self.assertEqual(outcome["content"]["steps"][0]["step"], "D")
        mock_loop.assert_called_once_with("galaxy", variant="b", offline=False, no_cache=False)

    @patch("etymonline_tool.ety.run_dkl_loop")
    def test_variant_a_is_passed_through(self, mock_loop):
        mock_loop.return_value = ([], False)
        tool.dispatch("etymonline_dkl_loop", {"word": "galaxy", "variant": "a"})
        mock_loop.assert_called_once_with("galaxy", variant="a", offline=False, no_cache=False)

    def test_invalid_variant_is_input_error(self):
        outcome = tool.dispatch("etymonline_dkl_loop", {"word": "galaxy", "variant": "c"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("variant", outcome["content"])


# ── dispatch(): network/HTTP error mapping ───────────────────────────────────

class TestDispatchNetworkErrors(unittest.TestCase):
    @patch("etymonline_tool.ety.lookup")
    def test_http_error(self, mock_lookup):
        mock_lookup.side_effect = requests.HTTPError("500 Server Error")
        outcome = tool.dispatch("etymonline_look", {"word": "robot"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("HTTP error", outcome["content"])

    @patch("etymonline_tool.ety.lookup")
    def test_connection_error(self, mock_lookup):
        mock_lookup.side_effect = requests.ConnectionError()
        outcome = tool.dispatch("etymonline_look", {"word": "robot"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("Network error", outcome["content"])

    @patch("etymonline_tool.ety.lookup")
    def test_timeout(self, mock_lookup):
        mock_lookup.side_effect = requests.Timeout()
        outcome = tool.dispatch("etymonline_look", {"word": "robot"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("timed out", outcome["content"])

    @patch("etymonline_tool.ety.lookup")
    def test_too_many_redirects(self, mock_lookup):
        mock_lookup.side_effect = requests.TooManyRedirects()
        outcome = tool.dispatch("etymonline_look", {"word": "robot"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("redirects", outcome["content"])


if __name__ == "__main__":
    unittest.main()
