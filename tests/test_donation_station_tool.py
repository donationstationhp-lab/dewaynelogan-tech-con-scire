"""Unit tests for donation_station_tool.py

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

import donation_station_tool as tool


class TestToolSchemas(unittest.TestCase):
    def test_every_tool_has_a_handler(self):
        names = {spec["name"] for spec in tool.TOOLS}
        self.assertEqual(names, set(tool._HANDLERS))


class TestDispatchIntake(unittest.TestCase):
    @patch("donation_station_tool.ds.intake")
    def test_success(self, mock_intake):
        mock_intake.return_value = {"id": "DS-0001"}
        outcome = tool.dispatch("donation_station_intake", {"name": "Winter Jacket"})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["id"], "DS-0001")
        mock_intake.assert_called_once_with(
            "Winter Jacket", category="general", condition="good", donor="", notes="", by="",
            expiry_date="", temp_zone="ambient", weight="", origin="",
        )

    def test_missing_name_is_input_error(self):
        outcome = tool.dispatch("donation_station_intake", {})
        self.assertTrue(outcome["is_error"])

    def test_invalid_condition_is_input_error(self):
        outcome = tool.dispatch("donation_station_intake", {"name": "Jacket", "condition": "pristine"})
        self.assertTrue(outcome["is_error"])

    def test_invalid_temp_zone_is_input_error(self):
        outcome = tool.dispatch("donation_station_intake", {"name": "Fish", "temp_zone": "warm"})
        self.assertTrue(outcome["is_error"])

    @patch("donation_station_tool.ds.intake")
    def test_perishable_fields_passed_through(self, mock_intake):
        mock_intake.return_value = {"id": "DS-0002"}
        tool.dispatch("donation_station_intake", {
            "name": "Apples", "category": "food",
            "expiry_date": "2026-12-31", "temp_zone": "refrigerated",
            "weight": "5 lbs", "origin": "Green Acres Farm",
        })
        mock_intake.assert_called_once_with(
            "Apples", category="food", condition="good", donor="", notes="", by="",
            expiry_date="2026-12-31", temp_zone="refrigerated",
            weight="5 lbs", origin="Green Acres Farm",
        )

    def test_food_without_expiry_is_reported_as_error_not_raised(self):
        outcome = tool.dispatch("donation_station_intake", {"name": "Apples", "category": "food"})
        self.assertTrue(outcome["is_error"])
        self.assertIn("expiry_date", outcome["content"])

    def test_food_with_null_expiry_is_reported_as_error_not_raised(self):
        # A JSON null for a present-but-unset optional field (as opposed to
        # an omitted key) must not crash the perishable-category check.
        outcome = tool.dispatch(
            "donation_station_intake",
            {"name": "Apples", "category": "food", "expiry_date": None},
        )
        self.assertTrue(outcome["is_error"])
        self.assertIn("expiry_date", outcome["content"])


class TestDispatchProcessQc(unittest.TestCase):
    @patch("donation_station_tool.ds.process_qc")
    def test_success(self, mock_qc):
        mock_qc.return_value = {"id": "DS-0001", "stage": "qc"}
        outcome = tool.dispatch("donation_station_process_qc", {"item_id": "DS-0001", "passed": True})
        self.assertFalse(outcome["is_error"])
        mock_qc.assert_called_once_with("DS-0001", True, by="", notes="", maintenance="")

    def test_missing_passed_is_input_error(self):
        outcome = tool.dispatch("donation_station_process_qc", {"item_id": "DS-0001"})
        self.assertTrue(outcome["is_error"])

    @patch("donation_station_tool.ds.process_qc")
    def test_unknown_item_is_reported_as_error(self, mock_qc):
        mock_qc.side_effect = KeyError("Item 'DS-9999' not found.")
        outcome = tool.dispatch("donation_station_process_qc", {"item_id": "DS-9999", "passed": True})
        self.assertTrue(outcome["is_error"])

    @patch("donation_station_tool.ds.process_qc")
    def test_wrong_stage_is_reported_as_error(self, mock_qc):
        mock_qc.side_effect = ValueError("DS-0001 is at stage 'qc', expected 'intake'.")
        outcome = tool.dispatch("donation_station_process_qc", {"item_id": "DS-0001", "passed": True})
        self.assertTrue(outcome["is_error"])
        self.assertIn("expected 'intake'", outcome["content"])


class TestDispatchStore(unittest.TestCase):
    @patch("donation_station_tool.ds.store")
    def test_success(self, mock_store):
        mock_store.return_value = {"id": "DS-0001", "stage": "storage"}
        outcome = tool.dispatch("donation_station_store", {"item_id": "DS-0001", "location": "B-3"})
        self.assertFalse(outcome["is_error"])
        mock_store.assert_called_once_with("DS-0001", "B-3", by="", notes="")

    def test_missing_location_is_input_error(self):
        outcome = tool.dispatch("donation_station_store", {"item_id": "DS-0001"})
        self.assertTrue(outcome["is_error"])


class TestDispatchDistribute(unittest.TestCase):
    @patch("donation_station_tool.ds.distribute")
    def test_success(self, mock_dist):
        mock_dist.return_value = {"id": "DS-0001", "stage": "distributed"}
        outcome = tool.dispatch("donation_station_distribute", {
            "item_id": "DS-0001", "recipient": "Community Center",
        })
        self.assertFalse(outcome["is_error"])
        mock_dist.assert_called_once_with("DS-0001", "Community Center", by="", notes="")


class TestDispatchGetStatus(unittest.TestCase):
    @patch("donation_station_tool.ds.get_status")
    def test_success(self, mock_status):
        mock_status.return_value = {"id": "DS-0001"}
        outcome = tool.dispatch("donation_station_get_status", {"item_id": "DS-0001"})
        self.assertFalse(outcome["is_error"])

    @patch("donation_station_tool.ds.get_status")
    def test_unknown_item_is_reported_as_error(self, mock_status):
        mock_status.side_effect = KeyError("Item 'DS-9999' not found.")
        outcome = tool.dispatch("donation_station_get_status", {"item_id": "DS-9999"})
        self.assertTrue(outcome["is_error"])


class TestDispatchListItems(unittest.TestCase):
    @patch("donation_station_tool.ds.list_items")
    def test_default_all(self, mock_list):
        mock_list.return_value = [{"id": "DS-0001"}]
        outcome = tool.dispatch("donation_station_list_items", {})
        self.assertFalse(outcome["is_error"])
        mock_list.assert_called_once_with("all")

    def test_invalid_stage_is_input_error(self):
        outcome = tool.dispatch("donation_station_list_items", {"stage": "shipped"})
        self.assertTrue(outcome["is_error"])


class TestDispatchReport(unittest.TestCase):
    @patch("donation_station_tool.ds.report")
    def test_success(self, mock_report):
        mock_report.return_value = {"total": 5}
        outcome = tool.dispatch("donation_station_report", {})
        self.assertFalse(outcome["is_error"])
        self.assertEqual(outcome["content"]["total"], 5)


class TestDispatchUnknown(unittest.TestCase):
    def test_unknown_tool_name(self):
        outcome = tool.dispatch("not_a_real_tool", {})
        self.assertTrue(outcome["is_error"])


if __name__ == "__main__":
    unittest.main()
