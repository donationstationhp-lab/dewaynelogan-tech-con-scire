"""Unit tests for power_connection_tool.py

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

import power_connection_tool as tool


class TestToolSchemas(unittest.TestCase):
    def test_every_tool_has_a_handler(self):
        names = {spec["name"] for spec in tool.TOOLS}
        self.assertEqual(names, set(tool._HANDLERS))


class TestDispatchCalculate(unittest.TestCase):
    @patch("power_connection_tool.pc.calculate")
    def test_success(self, mock_calc):
        mock_calc.return_value = {"born": 8}
        outcome = tool.dispatch("power_connection_calculate", {"month": 5, "day": 6, "year": 2026})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["born"], 8)
        mock_calc.assert_called_once_with(5, 6, 2026)

    def test_missing_field_is_input_error(self):
        outcome = tool.dispatch("power_connection_calculate", {"month": 5, "day": 6})
        self.assertTrue(outcome["is_error"])
        self.assertIn("year", outcome["content"])

    def test_month_out_of_range_is_input_error(self):
        outcome = tool.dispatch("power_connection_calculate", {"month": 13, "day": 1, "year": 2026})
        self.assertTrue(outcome["is_error"])

    def test_day_out_of_range_is_input_error(self):
        outcome = tool.dispatch("power_connection_calculate", {"month": 1, "day": 32, "year": 2026})
        self.assertTrue(outcome["is_error"])

    def test_non_positive_year_is_input_error(self):
        outcome = tool.dispatch("power_connection_calculate", {"month": 1, "day": 1, "year": 0})
        self.assertTrue(outcome["is_error"])

    def test_non_integer_field_is_input_error(self):
        outcome = tool.dispatch("power_connection_calculate", {"month": "May", "day": 6, "year": 2026})
        self.assertTrue(outcome["is_error"])


class TestDispatchMarkDate(unittest.TestCase):
    @patch("power_connection_tool.pc.mark_date")
    def test_success(self, mock_mark):
        mock_mark.return_value = ({"date": "5/6/2026"}, {"born": 8})
        outcome = tool.dispatch("power_connection_mark_date", {
            "month": 5, "day": 6, "year": 2026, "note": "Proceed",
        })
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["mark"]["date"], "5/6/2026")
        mock_mark.assert_called_once_with(5, 6, 2026, "Proceed")

    def test_invalid_date_is_input_error(self):
        outcome = tool.dispatch("power_connection_mark_date", {"month": 5, "day": 40, "year": 2026})
        self.assertTrue(outcome["is_error"])


class TestDispatchListMarks(unittest.TestCase):
    @patch("power_connection_tool.pc.marks_load")
    def test_success(self, mock_load):
        mock_load.return_value = [{"date": "5/6/2026"}]
        outcome = tool.dispatch("power_connection_list_marks", {})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(len(outcome["content"]["marks"]), 1)


class TestDispatchUnknown(unittest.TestCase):
    def test_unknown_tool_name(self):
        outcome = tool.dispatch("not_a_real_tool", {})
        self.assertTrue(outcome["is_error"])


if __name__ == "__main__":
    unittest.main()
