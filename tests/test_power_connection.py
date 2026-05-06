"""Unit tests for power_connection.py

Run with:
  pytest tests/test_power_connection.py
"""

import json
import sys
import os
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import power_connection as pc


class TestReduceToSingle(unittest.TestCase):
    def test_already_single(self):
        self.assertEqual(pc.reduce_to_single(7), 7)

    def test_double_digit(self):
        self.assertEqual(pc.reduce_to_single(21), 3)   # 2+1=3
        self.assertEqual(pc.reduce_to_single(12), 3)   # 1+2=3

    def test_large_number(self):
        # 2037 → 2+0+3+7=12 → 1+2=3
        self.assertEqual(pc.reduce_to_single(2037), 3)

    def test_master_number_preserved(self):
        self.assertEqual(pc.reduce_to_single(11), 11)
        self.assertEqual(pc.reduce_to_single(22), 22)
        self.assertEqual(pc.reduce_to_single(33), 33)

    def test_single_digit_boundaries(self):
        for n in range(1, 10):
            self.assertEqual(pc.reduce_to_single(n), n)


class TestCalculate(unittest.TestCase):
    def test_date_5_6_2026(self):
        r = pc.calculate(5, 6, 2026)
        # Step 1 — Root: 5+6=11 (master number, preserved)
        self.assertEqual(r["root"]["raw"],  11)
        self.assertEqual(r["root"]["born"], 11)
        # Step 2 — Path One: 5+6+2026=2037 → 2+0+3+7=12 → 1+2=3
        self.assertEqual(r["path_one"]["raw"],      2037)
        self.assertEqual(r["path_one"]["compound"], 12)
        self.assertEqual(r["path_one"]["born"],     3)
        # Step 3 — Path Two: 5+6+2+0+2+6=21 → 2+1=3
        self.assertEqual(r["path_two"]["raw"],      21)
        self.assertEqual(r["path_two"]["compound"], 21)
        self.assertEqual(r["path_two"]["born"],     3)
        # Both paths born to 3
        self.assertEqual(r["born"], 3)

    def test_root_raw_is_month_plus_day(self):
        r = pc.calculate(3, 8, 2025)
        self.assertEqual(r["root"]["raw"], 3 + 8)

    def test_root_born_reduces(self):
        # month=9, day=9 → 18 → 1+8=9
        r = pc.calculate(9, 9, 2020)
        self.assertEqual(r["root"]["raw"],  18)
        self.assertEqual(r["root"]["born"], 9)

    def test_root_master_number_preserved(self):
        # month=2, day=9 → 11 (master)
        r = pc.calculate(2, 9, 2024)
        self.assertEqual(r["root"]["born"], 11)

    def test_born_number_matches_path_one(self):
        r = pc.calculate(1, 1, 2024)
        self.assertEqual(r["born"], r["path_one"]["born"])

    def test_directive_is_list_of_strings(self):
        r = pc.calculate(5, 6, 2026)
        self.assertIsInstance(r["directive"], list)
        self.assertTrue(all(isinstance(s, str) for s in r["directive"]))

    def test_directive_references_born_number(self):
        r = pc.calculate(5, 6, 2026)
        combined = " ".join(r["directive"])
        self.assertIn("3", combined)

    def test_result_structure(self):
        r = pc.calculate(5, 6, 2026)
        for key in ("date", "root", "path_one", "path_two", "born", "directive"):
            self.assertIn(key, r)

    def test_date_stored_correctly(self):
        r = pc.calculate(5, 6, 2026)
        self.assertEqual(r["date"], {"month": 5, "day": 6, "year": 2026})


class TestLabelAndMeanings(unittest.TestCase):
    def test_all_single_digits_have_meanings(self):
        for n in range(1, 10):
            self.assertIn(n, pc.SINGLE_MEANINGS)

    def test_compound_12_in_meanings(self):
        self.assertIn(12, pc.COMPOUND_MEANINGS)

    def test_compound_21_in_meanings(self):
        self.assertIn(21, pc.COMPOUND_MEANINGS)

    def test_label_five_is_power(self):
        self.assertEqual(pc._label(5), "Power")

    def test_label_six_is_equality(self):
        self.assertEqual(pc._label(6), "Equality")

    def test_label_three_is_creation(self):
        self.assertEqual(pc._label(3), "Creation")

    def test_label_two_is_wisdom(self):
        self.assertEqual(pc._label(2), "Wisdom")


class TestDigitSum(unittest.TestCase):
    def test_digit_sum_2026(self):
        self.assertEqual(pc._digit_sum(2026), 10)   # 2+0+2+6

    def test_digit_sum_2037(self):
        self.assertEqual(pc._digit_sum(2037), 12)   # 2+0+3+7


class TestPrintResult(unittest.TestCase):
    def test_output_contains_date(self):
        r = pc.calculate(5, 6, 2026)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_result(r)
        out = captured.getvalue()
        self.assertIn("5/6/2026", out)
        self.assertIn("3", out)
        self.assertIn("Creation", out)

    def test_output_step_1_appears_before_paths(self):
        r = pc.calculate(5, 6, 2026)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_result(r)
        out = captured.getvalue()
        step1_pos = out.index("STEP 1")
        step2_pos = out.index("STEP 2")
        step3_pos = out.index("STEP 3")
        self.assertLess(step1_pos, step2_pos)
        self.assertLess(step2_pos, step3_pos)

    def test_output_root_shown(self):
        r = pc.calculate(5, 6, 2026)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_result(r)
        out = captured.getvalue()
        self.assertIn("The Root", out)
        self.assertIn("expresses through", out)
        self.assertIn("11", out)        # 5+6=11
        self.assertIn("Illumination", out)

    def test_output_year_amplifies_language(self):
        r = pc.calculate(5, 6, 2026)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_result(r)
        self.assertIn("amplifies the intelligence of the date", captured.getvalue())

    def test_output_born_into_label(self):
        r = pc.calculate(5, 6, 2026)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_result(r)
        self.assertIn("Born into the full calculations", captured.getvalue())

    def test_output_contains_directive(self):
        r = pc.calculate(5, 6, 2026)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_result(r)
        self.assertIn("DIRECTIVE", captured.getvalue())


class TestMarks(unittest.TestCase):
    def setUp(self):
        self._orig = pc.MARKS_FILE
        import tempfile
        self._tmp = tempfile.mktemp(suffix=".json")
        pc.MARKS_FILE = self._tmp

    def tearDown(self):
        pc.MARKS_FILE = self._orig
        if os.path.exists(self._tmp):
            os.remove(self._tmp)

    def test_mark_date_creates_entry(self):
        entry, result = pc.mark_date(7, 2, 2026, "Proceed with project")
        self.assertEqual(entry["date"], "7/2/2026")
        self.assertEqual(entry["note"], "Proceed with project")
        self.assertEqual(entry["born"], 1)
        self.assertEqual(entry["born_name"], "Origin")

    def test_mark_date_persists(self):
        pc.mark_date(7, 2, 2026, "Proceed with project")
        marks = pc.marks_load()
        self.assertEqual(len(marks), 1)
        self.assertEqual(marks[0]["date"], "7/2/2026")

    def test_mark_root_recorded(self):
        entry, _ = pc.mark_date(7, 2, 2026, "")
        self.assertEqual(entry["root"],      9)
        self.assertEqual(entry["root_born"], 9)

    def test_multiple_marks(self):
        pc.mark_date(7, 2, 2026, "First")
        pc.mark_date(5, 6, 2026, "Second")
        marks = pc.marks_load()
        self.assertEqual(len(marks), 2)
        self.assertEqual(marks[1]["date"], "5/6/2026")

    def test_marks_load_empty_when_no_file(self):
        self.assertEqual(pc.marks_load(), [])

    def test_print_mark_contains_note(self):
        entry, result = pc.mark_date(7, 2, 2026, "Proceed with project")
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_mark(entry, result)
        self.assertIn("Proceed with project", captured.getvalue())
        self.assertIn("7/2/2026", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
