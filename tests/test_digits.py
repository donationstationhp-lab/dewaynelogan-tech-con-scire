"""Unit tests for suprememath.digits"""

import datetime
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from suprememath.digits import reduce, method_a, method_b, method_c, calculation_steps


class TestReduce(unittest.TestCase):
    def test_single_digit_unchanged(self):
        for n in range(10):
            self.assertEqual(reduce(n), n)

    def test_two_digit(self):
        self.assertEqual(reduce(19), 1)   # 1+9=10 → 1
        self.assertEqual(reduce(29), 2)   # 2+9=11 → 2
        self.assertEqual(reduce(10), 1)

    def test_multi_step(self):
        self.assertEqual(reduce(999), 9)  # 27 → 9
        self.assertEqual(reduce(100), 1)

    def test_zero(self):
        self.assertEqual(reduce(0), 0)

    def test_negative_uses_abs(self):
        self.assertEqual(reduce(-29), reduce(29))

    def test_year_2026(self):
        # 2+0+2+6 = 10 → 1
        self.assertEqual(reduce(2026), 1)


class TestMethodA(unittest.TestCase):
    # Reference from existing Notion daily entry: 2026-02-07 → 1
    def test_feb7_2026(self):
        # 2+7+2+0+2+6 = 19 → 1
        d = datetime.date(2026, 2, 7)
        self.assertEqual(method_a(d), 1)

    def test_may29_2026(self):
        # 5+2+9+2+0+2+6 = 26 → 8
        d = datetime.date(2026, 5, 29)
        self.assertEqual(method_a(d), 8)

    def test_jan1_2000(self):
        # 1+1+2+0+0+0 = 4
        d = datetime.date(2000, 1, 1)
        self.assertEqual(method_a(d), 4)


class TestMethodB(unittest.TestCase):
    def test_feb7_2026(self):
        # reduce(2) + reduce(7) + reduce(2026=10→1) = 2+7+1 = 10 → 1
        d = datetime.date(2026, 2, 7)
        self.assertEqual(method_b(d), 1)

    def test_result_is_single_digit(self):
        for month in range(1, 13):
            for day in (1, 15, 28):
                try:
                    d = datetime.date(2026, month, day)
                except ValueError:
                    continue
                self.assertLessEqual(method_b(d), 9)
                self.assertGreaterEqual(method_b(d), 0)


class TestMethodC(unittest.TestCase):
    def test_jan1(self):
        # Day 1 of year → 1
        self.assertEqual(method_c(datetime.date(2026, 1, 1)), 1)

    def test_feb7_2026(self):
        # Day 38 → 3+8=11 → 2
        self.assertEqual(method_c(datetime.date(2026, 2, 7)), 2)

    def test_result_is_single_digit(self):
        for yday in range(1, 367):
            from suprememath.digits import reduce as _r
            self.assertLessEqual(_r(yday), 9)


class TestCalculationSteps(unittest.TestCase):
    def test_feb7_2026(self):
        d = datetime.date(2026, 2, 7)
        display, total, result = calculation_steps(d)
        self.assertIn("19", display)
        self.assertEqual(total, 19)
        self.assertEqual(result, 1)
        self.assertIn("→", display)

    def test_no_arrow_when_already_single(self):
        # A date whose digit sum is already 0-9
        d = datetime.date(2000, 1, 1)  # 1+1+2+0+0+0 = 4
        display, total, result = calculation_steps(d)
        self.assertEqual(total, result)
        self.assertNotIn("→", display)

    def test_display_format(self):
        d = datetime.date(2026, 2, 7)
        display, _, _ = calculation_steps(d)
        # Should contain space-separated digits joined with +
        self.assertIn(" + ", display)
        self.assertIn("=", display)


if __name__ == "__main__":
    unittest.main()
