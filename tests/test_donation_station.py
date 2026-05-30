"""Unit tests for donation_station.py

Run with:
  pytest tests/test_donation_station.py
"""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import donation_station as ds


class DSTestCase(unittest.TestCase):
    def setUp(self):
        self._orig = ds.DATA_FILE
        self._tmp  = tempfile.mktemp(suffix=".json")
        ds.DATA_FILE = self._tmp

    def tearDown(self):
        ds.DATA_FILE = self._orig
        if os.path.exists(self._tmp):
            os.remove(self._tmp)


# ── intake ─────────────────────────────────────────────────────────────────────

class TestIntake(DSTestCase):
    def test_creates_item(self):
        item = ds.intake("Blanket", "household", "good", "John", "nice blanket")
        self.assertEqual(item["name"],      "Blanket")
        self.assertEqual(item["category"],  "household")
        self.assertEqual(item["condition"], "good")
        self.assertEqual(item["donor"],     "John")
        self.assertEqual(item["stage"],     "intake")

    def test_id_format(self):
        item = ds.intake("Shoes")
        self.assertTrue(item["id"].startswith("DS-"))
        self.assertEqual(len(item["id"]), 7)   # DS-XXXX

    def test_ids_increment(self):
        a = ds.intake("Item A")
        b = ds.intake("Item B")
        self.assertNotEqual(a["id"], b["id"])
        num_a = int(a["id"].split("-")[1])
        num_b = int(b["id"].split("-")[1])
        self.assertEqual(num_b, num_a + 1)

    def test_history_has_intake_event(self):
        item = ds.intake("Coat", notes="warm coat")
        self.assertEqual(len(item["history"]), 1)
        self.assertEqual(item["history"][0]["stage"], "intake")
        self.assertEqual(item["history"][0]["notes"], "warm coat")

    def test_persists_to_disk(self):
        item = ds.intake("Boots")
        db   = ds._load()
        self.assertIn(item["id"], db["items"])


# ── QC ─────────────────────────────────────────────────────────────────────────

class TestQC(DSTestCase):
    def setUp(self):
        super().setUp()
        self.item = ds.intake("Jacket")

    def test_qc_pass(self):
        item = ds.process_qc(self.item["id"], passed=True, by="Staff")
        self.assertEqual(item["stage"], "qc")
        qc = item["history"][-1]
        self.assertTrue(qc["passed"])
        self.assertEqual(qc["by"], "Staff")

    def test_qc_fail_flags_maintenance(self):
        item = ds.process_qc(self.item["id"], passed=False,
                             maintenance="Needs zipper repair")
        self.assertEqual(item["maintenance_needed"], "Needs zipper repair")

    def test_qc_wrong_stage_raises(self):
        ds.process_qc(self.item["id"], passed=True)
        with self.assertRaises(ValueError):
            ds.process_qc(self.item["id"], passed=True)

    def test_qc_unknown_id_raises(self):
        with self.assertRaises(KeyError):
            ds.process_qc("DS-9999", passed=True)

    def test_history_grows(self):
        item = ds.process_qc(self.item["id"], passed=True)
        self.assertEqual(len(item["history"]), 2)
        self.assertEqual(item["history"][1]["stage"], "qc")


# ── storage ────────────────────────────────────────────────────────────────────

class TestStore(DSTestCase):
    def setUp(self):
        super().setUp()
        item = ds.intake("Shirt")
        self.item = ds.process_qc(item["id"], passed=True)

    def test_store_assigns_location(self):
        item = ds.store(self.item["id"], "A-1")
        self.assertEqual(item["stage"],    "storage")
        self.assertEqual(item["location"], "A-1")

    def test_store_wrong_stage_raises(self):
        item2 = ds.intake("Pants")
        with self.assertRaises(ValueError):
            ds.store(item2["id"], "A-2")

    def test_store_failed_qc_raises(self):
        item2 = ds.intake("Torn Jeans")
        ds.process_qc(item2["id"], passed=False, maintenance="Needs patch")
        with self.assertRaises(ValueError):
            ds.store(item2["id"], "C-5")

    def test_store_history_event(self):
        item = ds.store(self.item["id"], "B-3")
        storage_event = item["history"][-1]
        self.assertEqual(storage_event["stage"],    "storage")
        self.assertEqual(storage_event["location"], "B-3")


# ── distribution ───────────────────────────────────────────────────────────────

class TestDistribute(DSTestCase):
    def setUp(self):
        super().setUp()
        item = ds.intake("Towels")
        item = ds.process_qc(item["id"], passed=True)
        self.item = ds.store(item["id"], "D-1")

    def test_distribute_sets_recipient(self):
        item = ds.distribute(self.item["id"], "Food Bank")
        self.assertEqual(item["stage"],     "distributed")
        self.assertEqual(item["recipient"], "Food Bank")

    def test_distribute_wrong_stage_raises(self):
        item2 = ds.intake("Hat")
        with self.assertRaises(ValueError):
            ds.distribute(item2["id"], "Shelter")

    def test_distribute_history_event(self):
        item = ds.distribute(self.item["id"], "Shelter")
        dist_event = item["history"][-1]
        self.assertEqual(dist_event["stage"],     "distributed")
        self.assertEqual(dist_event["recipient"], "Shelter")

    def test_full_lifecycle_history_length(self):
        item = ds.distribute(self.item["id"], "Clinic")
        self.assertEqual(len(item["history"]), 4)
        stages = [e["stage"] for e in item["history"]]
        self.assertEqual(stages, ["intake", "qc", "storage", "distributed"])


# ── list & report ──────────────────────────────────────────────────────────────

class TestListAndReport(DSTestCase):
    def setUp(self):
        super().setUp()
        ds.intake("Item A", category="clothing")
        item2 = ds.intake("Item B", category="food")
        ds.process_qc(item2["id"], passed=True)

    def test_list_all(self):
        items = ds.list_items()
        self.assertEqual(len(items), 2)

    def test_list_by_stage(self):
        intake_items = ds.list_items("intake")
        self.assertEqual(len(intake_items), 1)
        self.assertEqual(intake_items[0]["name"], "Item A")

        qc_items = ds.list_items("qc")
        self.assertEqual(len(qc_items), 1)
        self.assertEqual(qc_items[0]["name"], "Item B")

    def test_report_totals(self):
        r = ds.report()
        self.assertEqual(r["total"], 2)
        self.assertEqual(r["by_stage"]["intake"], 1)
        self.assertEqual(r["by_stage"]["qc"],     1)

    def test_report_by_category(self):
        r = ds.report()
        self.assertIn("clothing", r["by_category"])
        self.assertIn("food",     r["by_category"])

    def test_report_maintenance_pending(self):
        item3 = ds.intake("Broken Radio", category="electronics")
        ds.process_qc(item3["id"], passed=False, maintenance="Needs new battery")
        r = ds.report()
        self.assertEqual(r["maintenance_pending"], 1)


# ── output ─────────────────────────────────────────────────────────────────────

class TestOutput(DSTestCase):
    def test_print_item_shows_id_and_name(self):
        item = ds.intake("Pillow")
        captured = StringIO()
        with patch("sys.stdout", captured):
            ds.print_item(item)
        out = captured.getvalue()
        self.assertIn(item["id"],   out)
        self.assertIn("Pillow",     out)
        self.assertIn("INTAKE",     out)

    def test_print_list_shows_all_items(self):
        ds.intake("Scarf")
        ds.intake("Gloves")
        items    = ds.list_items()
        captured = StringIO()
        with patch("sys.stdout", captured):
            ds.print_list(items)
        out = captured.getvalue()
        self.assertIn("Scarf",  out)
        self.assertIn("Gloves", out)

    def test_print_report_shows_total(self):
        ds.intake("Cup")
        r        = ds.report()
        captured = StringIO()
        with patch("sys.stdout", captured):
            ds.print_report(r)
        self.assertIn("Total items", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
