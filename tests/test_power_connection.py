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
        # Path One: 5+6+2026=2037 → 2+0+3+7=12 → 1+2=3
        self.assertEqual(r["path_one"]["raw"],      2037)
        self.assertEqual(r["path_one"]["compound"], 12)
        self.assertEqual(r["path_one"]["born"],     3)
        # Path Two: 5+6+2+0+2+6=21 → 2+1=3
        self.assertEqual(r["path_two"]["raw"],      21)
        self.assertEqual(r["path_two"]["compound"], 21)
        self.assertEqual(r["path_two"]["born"],     3)
        # Both paths born to 3
        self.assertEqual(r["born"], 3)

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
        for key in ("date", "path_one", "path_two", "born", "directive"):
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

    def test_output_contains_both_paths(self):
        r = pc.calculate(5, 6, 2026)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_result(r)
        out = captured.getvalue()
        self.assertIn("PATH ONE", out)
        self.assertIn("PATH TWO", out)

    def test_output_contains_directive(self):
        r = pc.calculate(5, 6, 2026)
        captured = StringIO()
        with patch("sys.stdout", captured):
            pc.print_result(r)
        self.assertIn("DIRECTIVE", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
