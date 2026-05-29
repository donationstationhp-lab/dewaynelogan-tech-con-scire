"""Unit tests for suprememath.daily"""

import datetime
import sys
import os
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from suprememath.lexicon import Lexicon
from suprememath.daily import compute_daily
from suprememath.digits import reduce, method_b, method_c

_LEXICON = Lexicon(Path(__file__).parent.parent / "data" / "sm_lexicon.json")


def _r(date_str: str, hour: int = 9) -> dict:
    dt = datetime.datetime.fromisoformat(date_str).replace(hour=hour)
    return compute_daily(dt, _LEXICON)


class TestComputeDaily(unittest.TestCase):

    # ── Structure ─────────────────────────────────────────────────────────────

    def test_required_keys_present(self):
        r = _r("2026-02-07")
        for key in ("date", "time", "attention", "intention", "purpose",
                    "convergence", "year_arc", "address", "moon",
                    "calculation", "onion_instruction", "methods"):
            self.assertIn(key, r, f"Missing key: {key}")

    def test_each_seat_has_number_and_name(self):
        r = _r("2026-02-07")
        for slot in ("attention", "intention", "purpose", "convergence", "year_arc"):
            self.assertIn("number", r[slot], slot)
            self.assertIn("name",   r[slot], slot)

    # ── Attention = method_b(date) ────────────────────────────────────────────

    def test_attention_is_method_b(self):
        r = _r("2026-02-07")
        self.assertEqual(r["attention"]["number"], method_b(datetime.date(2026, 2, 7)))

    def test_attention_feb7_2026(self):
        # "20260207" → 19 → 1
        r = _r("2026-02-07")
        self.assertEqual(r["attention"]["number"], 1)

    def test_attention_may29_2026(self):
        # "20260529" → 26 → 8
        r = _r("2026-05-29")
        self.assertEqual(r["attention"]["number"], 8)

    # ── Intention = reduce(12-hour clock) ────────────────────────────────────

    def test_intention_at_9am(self):
        r = _r("2026-02-07", hour=9)
        self.assertEqual(r["intention"]["number"], 9)

    def test_intention_at_1pm_is_1(self):
        # 13 % 12 = 1
        r = _r("2026-02-07", hour=13)
        self.assertEqual(r["intention"]["number"], 1)

    def test_intention_at_noon_is_12_reduced(self):
        # hour=12, h12 = (12 % 12) or 12 = 12, reduce(12) = 3
        r = _r("2026-02-07", hour=12)
        self.assertEqual(r["intention"]["number"], reduce(12))
        self.assertEqual(r["intention"]["number"], 3)

    def test_intention_at_midnight_is_12_reduced(self):
        # hour=0, h12 = (0 % 12) or 12 = 12, reduce(12) = 3
        r = _r("2026-02-07", hour=0)
        self.assertEqual(r["intention"]["number"], 3)

    # ── Purpose = reduce(attention + intention) ───────────────────────────────

    def test_purpose_formula(self):
        r = _r("2026-02-07", hour=9)
        att = r["attention"]["number"]
        itn = r["intention"]["number"]
        self.assertEqual(r["purpose"]["number"], reduce(att + itn))

    # ── Convergence = reduce(A + I + P) ──────────────────────────────────────

    def test_convergence_formula(self):
        r = _r("2026-05-29", hour=10)
        att  = r["attention"]["number"]
        itn  = r["intention"]["number"]
        pur  = r["purpose"]["number"]
        self.assertEqual(r["convergence"]["number"], reduce(att + itn + pur))

    # ── Address (Method A) ────────────────────────────────────────────────────

    def test_address_has_four_components(self):
        r = _r("2026-02-07")
        for k in ("Y", "M", "W", "D", "display"):
            self.assertIn(k, r["address"])

    def test_methods_dict(self):
        r = _r("2026-05-29")
        self.assertIsInstance(r["methods"]["a"], str)  # address string "Y·M·W·D"
        self.assertIsInstance(r["methods"]["b"], int)
        self.assertIsInstance(r["methods"]["c"], int)

    # ── Year arc ──────────────────────────────────────────────────────────────

    def test_year_arc_is_reduced_year(self):
        r = _r("2026-02-07")
        self.assertEqual(r["year_arc"]["number"], reduce(2026))
        self.assertEqual(r["year_arc"]["number"], 1)

    # ── Moon ─────────────────────────────────────────────────────────────────

    def test_moon_keys_present(self):
        r = _r("2026-02-07")
        for key in ("phase", "emoji", "illumination_pct", "phase_fraction", "days_to_full"):
            self.assertIn(key, r["moon"])

    def test_moon_illumination_range(self):
        for ds in ("2026-01-01", "2026-06-15", "2026-12-31"):
            r = _r(ds)
            self.assertGreaterEqual(r["moon"]["illumination_pct"], 0.0)
            self.assertLessEqual(r["moon"]["illumination_pct"], 100.0)

    # ── Lexicon names match the artifact ─────────────────────────────────────

    def test_position_7_is_consciousness(self):
        self.assertEqual(_LEXICON.name(7), "Consciousness")

    def test_position_7_verb_is_given(self):
        self.assertEqual(_LEXICON.verb(7), "given")

    def test_position_1_verb_is_gained(self):
        self.assertEqual(_LEXICON.verb(1), "gained")

    def test_position_0_is_completion(self):
        self.assertEqual(_LEXICON.name(0), "Completion")

    def test_position_9_is_birth(self):
        self.assertEqual(_LEXICON.name(9), "Birth")

    # ── Onion instruction ────────────────────────────────────────────────────

    def test_onion_includes_attention_and_intention(self):
        r = _r("2026-02-07", hour=9)
        onion = r["onion_instruction"]
        self.assertIn(r["attention"]["name"], onion)
        self.assertIn(r["intention"]["name"], onion)

    # ── Date passthrough ──────────────────────────────────────────────────────

    def test_date_preserved(self):
        r = _r("2026-05-29")
        self.assertEqual(r["date"], "2026-05-29")

    # ── Date-only input ───────────────────────────────────────────────────────

    def test_accepts_date_object(self):
        r = compute_daily(datetime.date(2026, 5, 29), _LEXICON)
        self.assertEqual(r["date"], "2026-05-29")


class TestMoonPhase(unittest.TestCase):
    def test_known_new_moon(self):
        from suprememath.moon import moon_phase
        m = moon_phase(datetime.datetime(2000, 1, 6, 18, 14, 0))
        self.assertEqual(m["phase"], "New")
        self.assertLess(m["illumination_pct"], 2.0)

    def test_approximate_full_moon(self):
        from suprememath.moon import moon_phase, _SYNODIC_DAYS, _KNOWN_NEW_MOON_UTC
        half = datetime.timedelta(days=_SYNODIC_DAYS / 2)
        m = moon_phase(_KNOWN_NEW_MOON_UTC + half)
        self.assertIn("Full", m["phase"])

    def test_days_to_full_present(self):
        from suprememath.moon import moon_phase
        m = moon_phase(datetime.date(2026, 5, 29))
        self.assertIn("days_to_full", m)


if __name__ == "__main__":
    unittest.main()
