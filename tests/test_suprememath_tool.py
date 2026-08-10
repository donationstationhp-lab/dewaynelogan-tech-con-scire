"""Unit tests for suprememath_tool.py

Run with:
  pip install pytest
  pytest tests/
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import suprememath_tool as tool


class TestToolSchemas(unittest.TestCase):
    def test_every_tool_has_a_handler(self):
        names = {spec["name"] for spec in tool.TOOLS}
        self.assertEqual(names, set(tool._HANDLERS))


class TestDispatchDailyReading(unittest.TestCase):
    @patch("suprememath_tool.compute_daily")
    @patch("suprememath_tool.Lexicon")
    def test_success_defaults(self, mock_lexicon_cls, mock_compute):
        mock_compute.return_value = {"date": "2026-05-06"}
        outcome = tool.dispatch("suprememath_daily_reading", {})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["date"], "2026-05-06")
        mock_lexicon_cls.assert_called_once_with(tool.DEFAULT_LEXICON_PATH)

    @patch("suprememath_tool.compute_daily")
    @patch("suprememath_tool.Lexicon")
    def test_explicit_date_and_hour(self, mock_lexicon_cls, mock_compute):
        mock_compute.return_value = {"date": "2026-05-06"}
        outcome = tool.dispatch("suprememath_daily_reading", {"date": "2026-05-06", "hour": 9})
        self.assertFalse(outcome["is_error"])
        called_dt = mock_compute.call_args[0][0]
        self.assertEqual((called_dt.year, called_dt.month, called_dt.day, called_dt.hour), (2026, 5, 6, 9))

    def test_invalid_date_is_input_error(self):
        outcome = tool.dispatch("suprememath_daily_reading", {"date": "not-a-date"})
        self.assertTrue(outcome["is_error"])

    def test_hour_out_of_range_is_input_error(self):
        outcome = tool.dispatch("suprememath_daily_reading", {"hour": 24})
        self.assertTrue(outcome["is_error"])

    @patch("suprememath_tool.Lexicon")
    def test_missing_lexicon_file_is_input_error(self, mock_lexicon_cls):
        mock_lexicon_cls.side_effect = FileNotFoundError()
        outcome = tool.dispatch("suprememath_daily_reading", {"lexicon_path": "/nope.json"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("Lexicon file not found", outcome["content"])


class TestDispatchPushToNotion(unittest.TestCase):
    @patch("suprememath.notion_sync.push")
    @patch("suprememath_tool.compute_daily")
    @patch("suprememath_tool.Lexicon")
    def test_success(self, mock_lexicon_cls, mock_compute, mock_push):
        mock_compute.return_value = {"date": "2026-05-06"}
        mock_push.return_value = "https://www.notion.so/abc123"
        outcome = tool.dispatch("suprememath_push_to_notion", {})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["notion_url"], "https://www.notion.so/abc123")
        self.assertEqual(outcome["content"]["reading"]["date"], "2026-05-06")

    @patch("suprememath.notion_sync.push")
    @patch("suprememath_tool.compute_daily")
    @patch("suprememath_tool.Lexicon")
    def test_missing_token_is_reported_as_error(self, mock_lexicon_cls, mock_compute, mock_push):
        mock_compute.return_value = {"date": "2026-05-06"}
        mock_push.side_effect = EnvironmentError("No Notion token found.")
        outcome = tool.dispatch("suprememath_push_to_notion", {})
        self.assertTrue(outcome["is_error"])
        self.assertIn("No Notion token found", outcome["content"])

    @patch("suprememath.notion_sync.push")
    @patch("suprememath_tool.compute_daily")
    @patch("suprememath_tool.Lexicon")
    def test_http_error_is_reported_as_error(self, mock_lexicon_cls, mock_compute, mock_push):
        mock_compute.return_value = {"date": "2026-05-06"}
        mock_push.side_effect = requests.HTTPError("500 Server Error")
        outcome = tool.dispatch("suprememath_push_to_notion", {})
        self.assertTrue(outcome["is_error"])
        self.assertIn("Notion error", outcome["content"])


class TestDispatchUnknown(unittest.TestCase):
    def test_unknown_tool_name(self):
        outcome = tool.dispatch("not_a_real_tool", {})
        self.assertTrue(outcome["is_error"])


if __name__ == "__main__":
    unittest.main()
