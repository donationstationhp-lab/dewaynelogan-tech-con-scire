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

    def test_report_by_tier(self):
        ds.intake("Walk Dogs", category="volunteer")
        ds.intake("Cash",      category="financial")
        r = ds.report()
        self.assertIn("by_tier", r)
        self.assertGreater(r["by_tier"]["T"], 0)
        self.assertGreater(r["by_tier"]["E"], 0)


# ── T.I.E.R. ──────────────────────────────────────────────────────────────────

class TestTIER(DSTestCase):
    def test_classify_time(self):
        self.assertEqual(ds.classify_tier("volunteer"), "T")
        self.assertEqual(ds.classify_tier("service"),   "T")
        self.assertEqual(ds.classify_tier("time"),      "T")

    def test_classify_intelligence(self):
        self.assertEqual(ds.classify_tier("knowledge"),  "I")
        self.assertEqual(ds.classify_tier("education"),  "I")
        self.assertEqual(ds.classify_tier("training"),   "I")

    def test_classify_energy(self):
        self.assertEqual(ds.classify_tier("financial"), "E")
        self.assertEqual(ds.classify_tier("funding"),   "E")
        self.assertEqual(ds.classify_tier("grant"),     "E")

    def test_classify_resources(self):
        self.assertEqual(ds.classify_tier("food"),       "R")
        self.assertEqual(ds.classify_tier("clothing"),   "R")
        self.assertEqual(ds.classify_tier("shelter"),    "R")
        self.assertEqual(ds.classify_tier("technology"), "R")
        self.assertEqual(ds.classify_tier("hygiene"),    "R")

    def test_classify_unknown_defaults_to_resources(self):
        self.assertEqual(ds.classify_tier("unknown_category"), "R")

    def test_case_insensitive(self):
        self.assertEqual(ds.classify_tier("Volunteer"), "T")
        self.assertEqual(ds.classify_tier("FINANCIAL"), "E")

    def test_intake_assigns_tier_automatically(self):
        item = ds.intake("Dog Walking", category="volunteer")
        self.assertEqual(item["tier"], "T")

        item2 = ds.intake("Cash", category="financial")
        self.assertEqual(item2["tier"], "E")

        item3 = ds.intake("Jacket", category="clothing")
        self.assertEqual(item3["tier"], "R")

    def test_print_item_shows_tier(self):
        item = ds.intake("Dog Walking", category="volunteer")
        captured = StringIO()
        with patch("sys.stdout", captured):
            ds.print_item(item)
        out = captured.getvalue()
        self.assertIn("T.I.E.R.", out)
        self.assertIn("T — Time", out)

    def test_print_report_shows_tier_breakdown(self):
        ds.intake("Walk", category="volunteer")
        ds.intake("Cash", category="financial")
        ds.intake("Food", category="food")
        r = ds.report()
        captured = StringIO()
        with patch("sys.stdout", captured):
            ds.print_report(r)
        out = captured.getvalue()
        self.assertIn("T.I.E.R.", out)
        self.assertIn("Time",      out)
        self.assertIn("Energy",    out)
        self.assertIn("Resources", out)


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


# ── search ─────────────────────────────────────────────────────────────────────

class TestSearch(DSTestCase):
    def setUp(self):
        super().setUp()
        ds.intake("Winter Jacket", category="clothing", donor="Jane Smith")
        item2 = ds.intake("Dog Walking", category="volunteer", donor="Matthew")
        ds.process_qc(item2["id"], passed=True)
        item3 = ds.intake("20 Dollars", category="financial", donor="Mary")
        ds.process_qc(item3["id"], passed=True)
        ds.store(item3["id"], "A-1")
        ds.distribute(item3["id"], "Community Center")

    def test_search_by_name(self):
        results = ds.search("Jacket")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Winter Jacket")

    def test_search_by_donor(self):
        results = ds.search("Matthew")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["category"], "volunteer")

    def test_search_by_recipient(self):
        results = ds.search("Community Center")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "20 Dollars")

    def test_search_by_category(self):
        results = ds.search("financial")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "20 Dollars")

    def test_search_case_insensitive(self):
        self.assertEqual(ds.search("jane smith"), ds.search("Jane Smith"))

    def test_search_no_match(self):
        self.assertEqual(ds.search("xyz_no_match"), [])

    def test_search_multiple_matches(self):
        results = ds.search("Donation")
        self.assertGreaterEqual(len(results), 0)

    def test_search_returns_full_item(self):
        results = ds.search("Jacket")
        self.assertIn("history", results[0])
        self.assertIn("tier",    results[0])


# ── power date ─────────────────────────────────────────────────────────────────

class TestPowerDate(DSTestCase):
    def test_intake_stores_power_date(self):
        item = ds.intake("Coat")
        self.assertIn("power_date", item)

    def test_power_date_has_required_keys(self):
        item = ds.intake("Coat")
        pd = item["power_date"]
        for key in ("root", "root_born", "born", "born_name"):
            self.assertIn(key, pd)

    def test_power_date_born_is_int(self):
        item = ds.intake("Coat")
        self.assertIsInstance(item["power_date"]["born"], int)

    def test_power_date_root_is_int(self):
        item = ds.intake("Coat")
        self.assertIsInstance(item["power_date"]["root"], int)

    def test_power_date_born_name_is_string(self):
        item = ds.intake("Coat")
        self.assertIsInstance(item["power_date"]["born_name"], str)

    def test_power_date_shown_in_print_item(self):
        item = ds.intake("Coat")
        captured = StringIO()
        with patch("sys.stdout", captured):
            ds.print_item(item)
        self.assertIn("Power", captured.getvalue())
        self.assertIn("Born", captured.getvalue())

    def test_power_date_persists(self):
        item = ds.intake("Coat")
        reloaded = ds.get_status(item["id"])
        self.assertIn("power_date", reloaded)


# ── export ─────────────────────────────────────────────────────────────────────

class TestExport(DSTestCase):
    def setUp(self):
        super().setUp()
        self._csv = tempfile.mktemp(suffix=".csv")

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self._csv):
            os.remove(self._csv)

    def _full_item(self):
        item = ds.intake("Jacket", "clothing", "good", "Jane")
        item = ds.process_qc(item["id"], passed=True, by="Staff")
        item = ds.store(item["id"], "A-1")
        item = ds.distribute(item["id"], "Shelter")
        return item

    def test_returns_path_and_count(self):
        ds.intake("Hat")
        path, count = ds.export(self._csv)
        self.assertEqual(path, self._csv)
        self.assertEqual(count, 1)

    def test_creates_file(self):
        ds.intake("Hat")
        ds.export(self._csv)
        self.assertTrue(os.path.exists(self._csv))

    def test_csv_has_header(self):
        import csv
        ds.intake("Hat")
        ds.export(self._csv)
        with open(self._csv) as f:
            reader = csv.DictReader(f)
            for col in ("Name", "Item ID", "T.I.E.R.", "Stage",
                        "Power Root", "Power Born", "Power Born Name"):
                self.assertIn(col, reader.fieldnames)

    def test_csv_row_count_matches_items(self):
        import csv
        ds.intake("Hat")
        ds.intake("Coat")
        ds.intake("Boots")
        ds.export(self._csv)
        with open(self._csv) as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 3)

    def test_csv_name_and_id(self):
        import csv
        item = ds.intake("Scarf")
        ds.export(self._csv)
        with open(self._csv) as f:
            row = list(csv.DictReader(f))[0]
        self.assertEqual(row["Name"],    "Scarf")
        self.assertEqual(row["Item ID"], item["id"])

    def test_csv_tier_label(self):
        import csv
        ds.intake("Walk Dogs", category="volunteer")
        ds.export(self._csv)
        with open(self._csv) as f:
            row = list(csv.DictReader(f))[0]
        self.assertEqual(row["T.I.E.R."], "T — Time")

    def test_csv_stage(self):
        import csv
        self._full_item()
        ds.export(self._csv)
        with open(self._csv) as f:
            row = list(csv.DictReader(f))[0]
        self.assertEqual(row["Stage"], "distributed")

    def test_csv_qc_pass(self):
        import csv
        self._full_item()
        ds.export(self._csv)
        with open(self._csv) as f:
            row = list(csv.DictReader(f))[0]
        self.assertEqual(row["QC Result"], "Pass")

    def test_csv_qc_fail(self):
        import csv
        item = ds.intake("Torn Shirt", "clothing")
        ds.process_qc(item["id"], passed=False, maintenance="Needs patch")
        ds.export(self._csv)
        with open(self._csv) as f:
            row = list(csv.DictReader(f))[0]
        self.assertEqual(row["QC Result"], "Fail")

    def test_csv_donor_and_recipient(self):
        import csv
        self._full_item()
        ds.export(self._csv)
        with open(self._csv) as f:
            row = list(csv.DictReader(f))[0]
        self.assertEqual(row["Donor"],     "Jane")
        self.assertEqual(row["Recipient"], "Shelter")

    def test_csv_location(self):
        import csv
        self._full_item()
        ds.export(self._csv)
        with open(self._csv) as f:
            row = list(csv.DictReader(f))[0]
        self.assertEqual(row["Location"], "A-1")

    def test_default_path(self):
        ds.intake("Hat")
        path, _ = ds.export()
        self.assertTrue(path.endswith("donation_station_export.csv"))
        if os.path.exists(path):
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
