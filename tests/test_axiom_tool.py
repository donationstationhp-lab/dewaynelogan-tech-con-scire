"""Unit tests for axiom_tool.py

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

import axiom_tool as tool

_VALID_ENTRIES = [{"position": p, "scores": [7, 7, 7]} for p in range(10)]


class TestToolSchemas(unittest.TestCase):
    def test_all_tools_have_required_fields(self):
        for spec in tool.TOOLS:
            self.assertIn("name", spec)
            self.assertIn("description", spec)
            self.assertIn("input_schema", spec)

    def test_every_tool_has_a_handler(self):
        names = {spec["name"] for spec in tool.TOOLS}
        self.assertEqual(names, set(tool._HANDLERS))


class TestDispatchGetDimensions(unittest.TestCase):
    def test_returns_ten_dimensions(self):
        outcome = tool.dispatch("axiom_get_dimensions", {})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(len(outcome["content"]["dimensions"]), 10)


class TestDispatchScoreAssessment(unittest.TestCase):
    def test_success(self):
        outcome = tool.dispatch("axiom_score_assessment", {
            "organization": "Acme Co",
            "dimension_scores": _VALID_ENTRIES,
        })
        self.assertFalse(outcome["is_error"])
        report = outcome["content"]
        self.assertEqual(report["organization"], "Acme Co")
        self.assertEqual(len(report["dimensions"]), 10)
        self.assertEqual(report["aggregate_score"], 7.0)
        self.assertIn("top_gap", report)
        self.assertNotIn("saved_to", report)

    @patch("axiom_tool.ax.write_report")
    def test_save_writes_report(self, mock_write):
        mock_write.return_value = "assessments/Acme_Co_20260101_000000.json"
        outcome = tool.dispatch("axiom_score_assessment", {
            "organization": "Acme Co",
            "dimension_scores": _VALID_ENTRIES,
            "save": True,
        })
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["saved_to"], mock_write.return_value)
        mock_write.assert_called_once()

    def test_missing_organization_is_input_error(self):
        outcome = tool.dispatch("axiom_score_assessment", {"dimension_scores": _VALID_ENTRIES})
        self.assertTrue(outcome["is_error"])
        self.assertIn("organization", outcome["content"])

    def test_wrong_dimension_count_is_input_error(self):
        outcome = tool.dispatch("axiom_score_assessment", {
            "organization": "Acme Co",
            "dimension_scores": _VALID_ENTRIES[:9],
        })
        self.assertTrue(outcome["is_error"])

    def test_duplicate_position_is_input_error(self):
        entries = [{"position": 0, "scores": [5, 5, 5]}] * 10
        outcome = tool.dispatch("axiom_score_assessment", {
            "organization": "Acme Co",
            "dimension_scores": entries,
        })
        self.assertTrue(outcome["is_error"])
        self.assertIn("Duplicate", outcome["content"])

    def test_invalid_position_is_input_error(self):
        entries = [dict(e) for e in _VALID_ENTRIES]
        entries[0] = {"position": 99, "scores": [5, 5, 5]}
        outcome = tool.dispatch("axiom_score_assessment", {
            "organization": "Acme Co",
            "dimension_scores": entries,
        })
        self.assertTrue(outcome["is_error"])

    def test_score_out_of_range_is_input_error(self):
        entries = [dict(e) for e in _VALID_ENTRIES]
        entries[0] = {"position": 0, "scores": [5, 5, 11]}
        outcome = tool.dispatch("axiom_score_assessment", {
            "organization": "Acme Co",
            "dimension_scores": entries,
        })
        self.assertTrue(outcome["is_error"])

    def test_wrong_number_of_scores_is_input_error(self):
        entries = [dict(e) for e in _VALID_ENTRIES]
        entries[0] = {"position": 0, "scores": [5, 5]}
        outcome = tool.dispatch("axiom_score_assessment", {
            "organization": "Acme Co",
            "dimension_scores": entries,
        })
        self.assertTrue(outcome["is_error"])


class TestDispatchUnknown(unittest.TestCase):
    def test_unknown_tool_name(self):
        outcome = tool.dispatch("not_a_real_tool", {})
        self.assertTrue(outcome["is_error"])


if __name__ == "__main__":
    unittest.main()
