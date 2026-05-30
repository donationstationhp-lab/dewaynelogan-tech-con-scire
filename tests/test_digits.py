"""Unit tests for suprememath.digits"""

import datetime
import math
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from suprememath.digits import (
    reduce, day_of_year, week_of_year,
    method_a, method_b, method_c, calculation_steps,
)


class TestReduce(unittest.TestCase):
    def test_single_digit_unchanged(self):
        for n in range(10):
            self.assertEqual(reduce(n), n)

    def test_two_digit(self):
        self.assertEqual(reduce(19), 1)
        self.assertEqual(reduce(29), 2)
        self.assertEqual(reduce(10), 1)

    def test_multi_step(self):
        self.assertEqual(reduce(999), 9)
        self.assertEqual(reduce(100), 1)

    def test_zero(self):
        self.assertEqual(reduce(0), 0)

    def test_negative_uses_abs(self):
        self.assertEqual(reduce(-29), reduce(29))

    def test_year_2026(self):
        self.assertEqual(reduce(2026), 1)  # 2+0+2+6=10→1


class TestDayAndWeekOfYear(unittest.TestCase):
    def test_jan1_is_day1(self):
        self.assertEqual(day_of_year(datetime.date(2026, 1, 1)), 1)

    def test_feb7_2026(self):
        self.assertEqual(day_of_year(datetime.date(2026, 2, 7)), 38)

    def test_week_of_year_jan1(self):
        self.assertEqual(week_of_year(datetime.date(2026, 1, 1)), 1)

    def test_week_of_year_is_ceil(self):
        # day 8 → ceil(8/7) = 2
        d = datetime.date(2026, 1, 8)
        self.assertEqual(day_of_year(d), 8)
        self.assertEqual(week_of_year(d), math.ceil(8 / 7))


class TestMethodA(unittest.TestCase):
    """Method A returns a Y·M·W·D address dict, not a single number."""

    def test_returns_dict_with_expected_keys(self):
        addr = method_a(datetime.date(2026, 2, 7))
        for k in ("Y", "M", "W", "D", "display"):
            self.assertIn(k, addr)

    def test_components_are_single_digits(self):
        addr = method_a(datetime.date(2026, 5, 29))
        for k in ("Y", "M", "W", "D"):
            self.assertGreaterEqual(addr[k], 0)
            self.assertLessEqual(addr[k], 9)

    def test_feb7_2026_address(self):
        # Y=reduce(2026)=1, M=reduce(2)=2, W=reduce(ceil(38/7)=6)=6, D=reduce(7)=7
        addr = method_a(datetime.date(2026, 2, 7))
        self.assertEqual(addr["Y"], 1)
        self.assertEqual(addr["M"], 2)
        self.assertEqual(addr["W"], reduce(math.ceil(38 / 7)))
        self.assertEqual(addr["D"], 7)

    def test_display_format(self):
        addr = method_a(datetime.date(2026, 2, 7))
        parts = addr["display"].split("·")
        self.assertEqual(len(parts), 4)
        for p in parts:
            self.assertTrue(p.isdigit())


class TestMethodB(unittest.TestCase):
    """Method B: sum all digits of YYYYMMDD, reduce."""

    def test_feb7_2026(self):
        # "20260207" → 2+0+2+6+0+2+0+7 = 19 → 1
        self.assertEqual(method_b(datetime.date(2026, 2, 7)), 1)

    def test_may29_2026(self):
        # "20260529" → 2+0+2+6+0+5+2+9 = 26 → 8
        self.assertEqual(method_b(datetime.date(2026, 5, 29)), 8)

    def test_result_is_single_digit(self):
        for month in range(1, 13):
            for day in (1, 15, 28):
                try:
                    d = datetime.date(2026, month, day)
                except ValueError:
                    continue
                r = method_b(d)
                self.assertGreaterEqual(r, 0)
                self.assertLessEqual(r, 9)


class TestMethodC(unittest.TestCase):
    """Method C: reduce(month_int + day_int + year_int)."""

    def test_feb7_2026(self):
        # 2 + 7 + 2026 = 2035 → 2+0+3+5=10 → 1
        self.assertEqual(method_c(datetime.date(2026, 2, 7)), 1)

    def test_may29_2026(self):
        # 5 + 29 + 2026 = 2060 → 8
        self.assertEqual(method_c(datetime.date(2026, 5, 29)), 8)

    def test_result_is_single_digit(self):
        for month in range(1, 13):
            for day in (1, 15, 28):
                try:
                    d = datetime.date(2026, month, day)
                except ValueError:
                    continue
                r = method_c(d)
                self.assertGreaterEqual(r, 0)
                self.assertLessEqual(r, 9)


class TestCalculationSteps(unittest.TestCase):
    def test_feb7_2026(self):
        d = datetime.date(2026, 2, 7)
        display, total, result = calculation_steps(d)
        self.assertEqual(total, 19)   # 2+7+2+0+2+6 (M+D+YYYY order)
        self.assertEqual(result, 1)
        self.assertIn("→", display)

    def test_result_equals_method_b(self):
        # calculation_steps and method_b must agree (sum is order-independent)
        for date_str in ("2026-02-07", "2026-05-29", "2026-12-31"):
            d = datetime.date.fromisoformat(date_str)
            _, _, result = calculation_steps(d)
            self.assertEqual(result, method_b(d))

    def test_no_arrow_when_already_single(self):
        d = datetime.date(2000, 1, 1)  # 1+1+2+0+0+0 = 4
        display, total, result = calculation_steps(d)
        self.assertEqual(total, result)
        self.assertNotIn("→", display)


if __name__ == "__main__":
    unittest.main()
