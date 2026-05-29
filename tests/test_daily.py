"""Unit tests for suprememath.daily"""

import datetime
import sys
import os
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from suprememath.lexicon import Lexicon
from suprememath.daily import compute_daily
from suprememath.digits import reduce

_LEXICON = Lexicon(Path(__file__).parent.parent / "data" / "sm_lexicon.json")


class TestComputeDaily(unittest.TestCase):
    def _reading(self, date_str, method="a"):
        return compute_daily(datetime.date.fromisoformat(date_str), _LEXICON,
                             cipher_method=method)

    # ── Structure ─────────────────────────────────────────────────────────────

    def test_required_keys_present(self):
        r = self._reading("2026-02-07")
        for key in ("date", "attention", "intention", "purpose", "year",
                    "cipher", "moon", "calculation", "onion_instruction", "methods"):
            self.assertIn(key, r, f"Missing key: {key}")

    def test_each_position_has_number_and_name(self):
        r = self._reading("2026-02-07")
        for slot in ("attention", "intention", "purpose", "year", "cipher"):
            self.assertIn("number", r[slot])
            self.assertIn("name",   r[slot])

    # ── Arithmetic (reference date: 2026-02-07) ───────────────────────────────

    def test_attention_is_reduced_month(self):
        # Month 2 → 2  (Receive Attention OF the month)
        r = self._reading("2026-02-07")
        self.assertEqual(r["attention"]["number"], reduce(2))

    def test_intention_is_reduced_day(self):
        # Day 7 → 7  (Gain Intention BY the day)
        r = self._reading("2026-02-07")
        self.assertEqual(r["intention"]["number"], reduce(7))

    def test_purpose_is_reduce_month_plus_day(self):
        # Purpose = reduce(month + day) = reduce(2 + 7) = reduce(9) = 9 = Born
        r = self._reading("2026-02-07")
        self.assertEqual(r["purpose"]["number"], reduce(2 + 7))
        self.assertEqual(r["purpose"]["number"], 9)

    def test_year_is_reduced_year(self):
        # Year arc: 2026 → 2+0+2+6=10 → 1 = Knowledge
        r = self._reading("2026-02-07")
        self.assertEqual(r["year"]["number"], reduce(2026))
        self.assertEqual(r["year"]["number"], 1)

    def test_cipher_method_a(self):
        # 2+7+2+0+2+6 = 19 → 1
        r = self._reading("2026-02-07", method="a")
        self.assertEqual(r["cipher"]["number"], 1)

    def test_cipher_method_b(self):
        r = self._reading("2026-02-07", method="b")
        # reduce(2)+reduce(7)+reduce(2026) = 2+7+1=10 → 1
        self.assertEqual(r["cipher"]["number"], 1)

    def test_cipher_method_c(self):
        # Feb 7 is day 38 → 3+8=11 → 2
        r = self._reading("2026-02-07", method="c")
        self.assertEqual(r["cipher"]["number"], 2)

    def test_invalid_method_raises(self):
        with self.assertRaises(ValueError):
            self._reading("2026-02-07", method="x")

    # ── Moon ─────────────────────────────────────────────────────────────────

    def test_moon_keys_present(self):
        r = self._reading("2026-02-07")
        for key in ("phase", "emoji", "illumination_pct", "phase_fraction"):
            self.assertIn(key, r["moon"])

    def test_moon_illumination_range(self):
        for date_str in ("2026-01-01", "2026-06-15", "2026-12-31"):
            r = self._reading(date_str)
            self.assertGreaterEqual(r["moon"]["illumination_pct"], 0.0)
            self.assertLessEqual(r["moon"]["illumination_pct"], 100.0)

    # ── Onion instruction ────────────────────────────────────────────────────

    def test_onion_instruction_includes_names(self):
        # Onion = "{attention} + {intention} = {year} made clear."
        r = self._reading("2026-02-07")
        onion = r["onion_instruction"]
        self.assertIn(r["attention"]["name"], onion)
        self.assertIn(r["intention"]["name"], onion)
        self.assertIn(r["year"]["name"],      onion)

    def test_onion_attention_precedes_intention(self):
        r = self._reading("2026-02-07")
        onion = r["onion_instruction"]
        att_pos = onion.index(r["attention"]["name"])
        itn_pos = onion.index(r["intention"]["name"])
        self.assertLess(att_pos, itn_pos)

    # ── Methods dict ─────────────────────────────────────────────────────────

    def test_methods_dict_has_all_three(self):
        r = self._reading("2026-05-29")
        self.assertIn("a", r["methods"])
        self.assertIn("b", r["methods"])
        self.assertIn("c", r["methods"])

    def test_methods_dict_values_are_single_digits(self):
        r = self._reading("2026-05-29")
        for v in r["methods"].values():
            self.assertGreaterEqual(v, 0)
            self.assertLessEqual(v, 9)

    # ── Date passthrough ──────────────────────────────────────────────────────

    def test_date_preserved_in_output(self):
        r = self._reading("2026-05-29")
        self.assertEqual(r["date"], "2026-05-29")


class TestMoonPhaseStandalone(unittest.TestCase):
    def test_known_new_moon(self):
        from suprememath.moon import moon_phase
        # 2000-01-06 is the reference new moon
        m = moon_phase(datetime.date(2000, 1, 6))
        self.assertEqual(m["phase"], "New Moon")
        self.assertLess(m["illumination_pct"], 5.0)

    def test_approximate_full_moon(self):
        from suprememath.moon import moon_phase, _SYNODIC_DAYS, _KNOWN_NEW_MOON
        import math
        # Half a synodic period after reference = full moon
        half_period = int(_SYNODIC_DAYS / 2)
        d = _KNOWN_NEW_MOON + datetime.timedelta(days=half_period)
        m = moon_phase(d)
        self.assertIn("Full", m["phase"])


if __name__ == "__main__":
    unittest.main()
