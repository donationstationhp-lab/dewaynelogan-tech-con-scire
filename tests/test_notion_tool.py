"""Unit tests for notion_tool.py

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

import notion_tool as tool


class TestToolSchemas(unittest.TestCase):
    def test_every_tool_has_a_handler(self):
        names = {spec["name"] for spec in tool.TOOLS}
        self.assertEqual(names, set(tool._HANDLERS))


class TestDispatchSaveEntry(unittest.TestCase):
    @patch("notion_tool.nt.save_entry")
    def test_success(self, mock_save):
        mock_save.return_value = {"id": "page-123"}
        outcome = tool.dispatch("notion_save_entry", {
            "word": "robot", "etymology": "from Czech robota", "related": ["automaton"],
        })
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["notion_page_id"], "page-123")
        mock_save.assert_called_once_with("robot", "from Czech robota", related=["automaton"])

    def test_missing_word_is_input_error(self):
        outcome = tool.dispatch("notion_save_entry", {})
        self.assertTrue(outcome["is_error"])

    @patch("notion_tool.nt.save_entry")
    def test_missing_credentials_is_reported_as_error(self, mock_save):
        mock_save.side_effect = EnvironmentError("NOTION_TOKEN is not set.")
        outcome = tool.dispatch("notion_save_entry", {"word": "robot"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("NOTION_TOKEN", outcome["content"])

    @patch("notion_tool.nt.save_entry")
    def test_http_error_is_reported_as_error(self, mock_save):
        mock_save.side_effect = requests.HTTPError("400 Bad Request")
        outcome = tool.dispatch("notion_save_entry", {"word": "robot"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("Notion error", outcome["content"])


class TestDispatchSaveEntries(unittest.TestCase):
    @patch("notion_tool.nt.save_entries")
    def test_success(self, mock_save):
        mock_save.return_value = 2
        outcome = tool.dispatch("notion_save_entries", {
            "entries": [{"word": "robot"}, {"word": "automaton"}],
        })
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["saved"], 2)

    def test_empty_entries_is_input_error(self):
        outcome = tool.dispatch("notion_save_entries", {"entries": []})
        self.assertTrue(outcome["is_error"])

    def test_entry_missing_word_is_input_error(self):
        outcome = tool.dispatch("notion_save_entries", {"entries": [{"etymology": "x"}]})
        self.assertTrue(outcome["is_error"])


class TestDispatchUnknown(unittest.TestCase):
    def test_unknown_tool_name(self):
        outcome = tool.dispatch("not_a_real_tool", {})
        self.assertTrue(outcome["is_error"])


if __name__ == "__main__":
    unittest.main()
