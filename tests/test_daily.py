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
                    "secondary", "year_arc", "address", "moon",
                    "calculation", "methods", "sources"):
            self.assertIn(key, r, f"Missing key: {key}")

    def test_each_primary_seat_has_number_and_name(self):
        r = _r("2026-02-07")
        for slot in ("attention", "intention", "purpose"):
            self.assertIn("number", r[slot], slot)
            self.assertIn("name",   r[slot], slot)

    # ── Primary Attention = month ─────────────────────────────────────────────

    def test_attention_raw_is_month(self):
        r = _r("2026-02-07")   # month=2
        self.assertEqual(r["attention"]["raw"], 2)

    def test_attention_position_is_reduced_month(self):
        r = _r("2026-02-07")
        self.assertEqual(r["attention"]["number"], reduce(2))

    def test_attention_may(self):
        r = _r("2026-05-29")   # month=5 → reduce(5)=5
        self.assertEqual(r["attention"]["raw"], 5)
        self.assertEqual(r["attention"]["number"], 5)

    def test_attention_verb_received(self):
        r = _r("2026-05-29")
        self.assertEqual(r["attention"]["verb"], "Received")

    def test_attention_prep_of(self):
        r = _r("2026-05-29")
        self.assertEqual(r["attention"]["prep"], "of")

    def test_attention_liturgy_contains_month_name(self):
        r = _r("2026-05-29")
        self.assertIn("Received Attention of", r["attention"]["liturgy"])
        self.assertIn("May", r["attention"]["liturgy"])
        self.assertIn("5", r["attention"]["liturgy"])

    # ── Primary Intention = day (raw, unreduced) ──────────────────────────────

    def test_intention_raw_is_day(self):
        r = _r("2026-05-29")   # day=29
        self.assertEqual(r["intention"]["raw"], 29)

    def test_intention_position_is_reduced_day(self):
        r = _r("2026-05-29")
        self.assertEqual(r["intention"]["number"], reduce(29))  # 2+9=11→2 → 2

    def test_intention_compound_when_day_multi_digit(self):
        r = _r("2026-05-29")   # day=29, reduce(29)=2 — compound
        self.assertTrue(r["intention"]["compound"])

    def test_intention_not_compound_for_single_digit_day(self):
        r = _r("2026-02-07")   # day=7, reduce(7)=7 — not compound
        self.assertFalse(r["intention"]["compound"])

    def test_intention_verb_gained(self):
        r = _r("2026-05-29")
        self.assertEqual(r["intention"]["verb"], "Gained")

    def test_intention_prep_by(self):
        r = _r("2026-05-29")
        self.assertEqual(r["intention"]["prep"], "by")

    def test_intention_liturgy_contains_day(self):
        r = _r("2026-05-29")
        self.assertIn("Gained Intention by", r["intention"]["liturgy"])
        self.assertIn("29", r["intention"]["liturgy"])

    # ── Primary Purpose = month + day UNREDUCED ───────────────────────────────

    def test_purpose_raw_is_unreduced_sum(self):
        r = _r("2026-05-29")   # 5 + 29 = 34 (not reduced)
        self.assertEqual(r["purpose"]["raw"], 34)

    def test_purpose_position_is_reduced_sum(self):
        r = _r("2026-05-29")
        self.assertEqual(r["purpose"]["number"], reduce(34))  # 3+4=7

    def test_purpose_compound_when_sum_multi_digit(self):
        r = _r("2026-05-29")   # 34 != 7 — compound
        self.assertTrue(r["purpose"]["compound"])

    def test_purpose_not_compound_when_sum_single_digit(self):
        r = _r("2026-01-01")   # 1+1=2, reduce(2)=2 — not compound
        self.assertFalse(r["purpose"]["compound"])

    def test_purpose_verb_given(self):
        r = _r("2026-05-29")
        self.assertEqual(r["purpose"]["verb"], "Given")

    def test_purpose_prep_through(self):
        r = _r("2026-05-29")
        self.assertEqual(r["purpose"]["prep"], "through")

    def test_purpose_liturgy_format(self):
        r = _r("2026-05-29")   # 5 + 29 = 34
        liturgy = r["purpose"]["liturgy"]
        self.assertIn("Given Purpose through all being born to", liturgy)
        self.assertIn("5", liturgy)
        self.assertIn("29", liturgy)
        self.assertIn("34", liturgy)

    def test_purpose_carries_month_and_day(self):
        r = _r("2026-05-29")
        self.assertEqual(r["purpose"]["month"], 5)
        self.assertEqual(r["purpose"]["day"],   29)

    # ── Secondary lens ────────────────────────────────────────────────────────

    def test_secondary_present(self):
        r = _r("2026-05-29")
        self.assertIn("secondary", r)
        for key in ("hour", "attention", "purpose", "convergence"):
            self.assertIn(key, r["secondary"])

    def test_secondary_attention_is_method_b(self):
        r = _r("2026-05-29")
        self.assertEqual(
            r["secondary"]["attention"]["number"],
            method_b(datetime.date(2026, 5, 29)),
        )

    def test_secondary_h12_at_1pm(self):
        r = _r("2026-05-29", hour=13)
        self.assertEqual(r["secondary"]["hour"]["h12"], 1)
        self.assertEqual(r["secondary"]["hour"]["number"], reduce(1))

    def test_secondary_h12_at_midnight_is_12_reduced(self):
        # hour=0, h12 = (0%12) or 12 = 12, reduce(12)=3
        r = _r("2026-05-29", hour=0)
        self.assertEqual(r["secondary"]["hour"]["h12"], 12)
        self.assertEqual(r["secondary"]["hour"]["number"], reduce(12))

    def test_secondary_h12_at_noon_is_12_reduced(self):
        # hour=12, h12 = (12%12) or 12 = 12, reduce(12)=3
        r = _r("2026-05-29", hour=12)
        self.assertEqual(r["secondary"]["hour"]["h12"], 12)
        self.assertEqual(r["secondary"]["hour"]["number"], 3)

    def test_secondary_convergence_formula(self):
        r = _r("2026-05-29", hour=10)
        s = r["secondary"]
        mb   = s["attention"]["number"]
        h    = s["hour"]["number"]
        pur  = s["purpose"]["number"]
        self.assertEqual(s["convergence"]["number"], reduce(mb + h + pur))

    def test_secondary_aligned_when_convergence_6(self):
        # Find a day + hour where convergence = 6
        # date=2026-02-07 → method_b=1; h12=13%12=1→reduce(1)=1
        # pur=reduce(1+1)=2; conv=reduce(1+1+2)=4 → not aligned
        # Just verify the flag is correct (bool)
        r = _r("2026-05-29", hour=9)
        s = r["secondary"]
        self.assertIsInstance(s["convergence"]["aligned"], bool)
        self.assertEqual(s["convergence"]["aligned"], s["convergence"]["number"] == 6)

    # ── Address (Method A) ────────────────────────────────────────────────────

    def test_address_has_required_keys(self):
        r = _r("2026-02-07")
        for k in ("Y", "M", "W", "D", "display"):
            self.assertIn(k, r["address"])

    def test_methods_dict(self):
        r = _r("2026-05-29")
        self.assertIsInstance(r["methods"]["a"], str)
        self.assertIsInstance(r["methods"]["b"], int)
        self.assertIsInstance(r["methods"]["c"], int)

    def test_methods_b_equals_method_b(self):
        r = _r("2026-05-29")
        self.assertEqual(r["methods"]["b"], method_b(datetime.date(2026, 5, 29)))

    def test_methods_c_equals_method_c(self):
        r = _r("2026-05-29")
        self.assertEqual(r["methods"]["c"], method_c(datetime.date(2026, 5, 29)))

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

    # ── Sources ───────────────────────────────────────────────────────────────

    def test_sources_present(self):
        r = _r("2026-05-29")
        self.assertIn("fraction_calendar", r["sources"])
        self.assertIn("lunar_thread", r["sources"])

    def test_sources_have_notion_ids(self):
        r = _r("2026-05-29")
        self.assertIn("notion_id", r["sources"]["fraction_calendar"])
        self.assertIn("notion_id", r["sources"]["lunar_thread"])

    # ── Lexicon names match the sealed cipher ─────────────────────────────────

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

    # ── Date passthrough ──────────────────────────────────────────────────────

    def test_date_preserved(self):
        r = _r("2026-05-29")
        self.assertEqual(r["date"], "2026-05-29")

    def test_accepts_date_object(self):
        r = compute_daily(datetime.date(2026, 5, 29), _LEXICON)
        self.assertEqual(r["date"], "2026-05-29")

    # ── Spot-check known reading (May 29, 2026) ───────────────────────────────

    def test_may29_attention_is_may(self):
        r = _r("2026-05-29")
        self.assertEqual(r["attention"]["raw"], 5)
        self.assertEqual(r["attention"]["number"], 5)  # reduce(5)=5

    def test_may29_intention_is_29(self):
        r = _r("2026-05-29")
        self.assertEqual(r["intention"]["raw"], 29)
        self.assertEqual(r["intention"]["number"], 2)  # reduce(29)=2+9=11→2

    def test_may29_purpose_is_34(self):
        r = _r("2026-05-29")
        self.assertEqual(r["purpose"]["raw"], 34)      # 5+29 unreduced
        self.assertEqual(r["purpose"]["number"], 7)    # reduce(34)=3+4=7

    def test_october_attention_raw_and_position(self):
        # month=10, raw=10, position=reduce(10)=1 (Knowledge) — raw != position
        r = _r("2026-10-15")
        self.assertEqual(r["attention"]["raw"], 10)
        self.assertEqual(r["attention"]["number"], 1)
        self.assertIn("October", r["attention"]["liturgy"])
        self.assertIn("10", r["attention"]["liturgy"])

    def test_october_purpose_compound(self):
        # month=10, day=15, raw=25, reduce(25)=7
        r = _r("2026-10-15")
        self.assertEqual(r["purpose"]["raw"], 25)
        self.assertEqual(r["purpose"]["number"], 7)
        self.assertTrue(r["purpose"]["compound"])


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

    def test_third_quarter_not_last_quarter(self):
        from suprememath.moon import _PHASES
        names = [name for _, name, _ in _PHASES]
        self.assertIn("Third Quarter", names)
        self.assertNotIn("Last Quarter", names)

    def test_doctrinal_note_in_return(self):
        from suprememath.moon import moon_phase
        m = moon_phase(datetime.date(2026, 5, 29))
        self.assertIn("note", m)
        self.assertIn("synodic", m["note"])


if __name__ == "__main__":
    unittest.main()
