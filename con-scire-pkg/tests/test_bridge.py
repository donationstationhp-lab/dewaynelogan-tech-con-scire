import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge import (
    pc_born,
    born_label,
    map_born_to_position,
    get_dim,
    item_born,
    bridge_item,
    stage_health,
    donor_born,
    bridge_donor,
    BORN_TO_POSITION,
    STAGE_TO_POSITIONS,
)


def _make_assessment(scores=None):
    scores = scores or {}
    return {
        "organization": "Test Org",
        "aggregate_score": 9.0,
        "aggregate_level": "Mature",
        "timestamp": "2026-08-17T00:00:00",
        "dimensions": [
            {
                "position": p,
                "name": f"DIM_{p}",
                "scores": [scores.get(p, 9.0)] * 3,
                "average": scores.get(p, 9.0),
                "level": "Mature",
            }
            for p in range(10)
        ],
    }


def _make_item(item_id="DS-0001", stage="intake", ts="2026-08-17T12:00:00Z"):
    return {
        "id": item_id,
        "name": "Test Item",
        "stage": stage,
        "history": [{"stage": "intake", "timestamp": ts}],
    }


class TestPcBorn(unittest.TestCase):
    def test_returns_integer(self):
        self.assertIsInstance(pc_born(8, 17, 2026), int)

    def test_valid_range(self):
        born = pc_born(1, 1, 2026)
        valid = set(range(1, 10)) | {11, 22, 33}
        self.assertIn(born, valid)

    def test_different_dates_produce_values(self):
        a = pc_born(1, 1, 2026)
        b = pc_born(7, 4, 2026)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)


class TestBornLabel(unittest.TestCase):
    def test_single_digits(self):
        self.assertEqual(born_label(1), "Origin")
        self.assertEqual(born_label(6), "Equality")
        self.assertEqual(born_label(9), "Completion")

    def test_master_numbers(self):
        self.assertEqual(born_label(11), "Illumination")
        self.assertEqual(born_label(22), "Master Builder")
        self.assertEqual(born_label(33), "Master Teacher")

    def test_none_returns_none(self):
        self.assertIsNone(born_label(None))

    def test_unknown_returns_string(self):
        self.assertIsNotNone(born_label(99))


class TestMapBornToPosition(unittest.TestCase):
    def test_completion_maps_to_cipher(self):
        self.assertEqual(map_born_to_position(9), 0)

    def test_illumination_maps_to_consciousness(self):
        self.assertEqual(map_born_to_position(11), 7)

    def test_master_builder_maps_to_cultured_freedom(self):
        self.assertEqual(map_born_to_position(22), 4)

    def test_master_teacher_maps_to_build_destroy(self):
        self.assertEqual(map_born_to_position(33), 8)

    def test_all_single_digits_valid(self):
        for n in range(1, 10):
            self.assertIn(map_born_to_position(n), range(10))

    def test_none_returns_none(self):
        self.assertIsNone(map_born_to_position(None))

    def test_fallback_to_modulo(self):
        self.assertEqual(map_born_to_position(15), 5)

    def test_nine_born_map_to_nine_distinct_positions(self):
        positions = {map_born_to_position(n) for n in range(1, 10)}
        self.assertEqual(len(positions), 9)


class TestGetDim(unittest.TestCase):
    def setUp(self):
        self.assessment = _make_assessment({6: 8.33})

    def test_found(self):
        d = get_dim(6, self.assessment)
        self.assertIsNotNone(d)
        self.assertAlmostEqual(d["average"], 8.33)

    def test_position_zero(self):
        self.assertIsNotNone(get_dim(0, self.assessment))

    def test_missing_returns_none(self):
        self.assertIsNone(get_dim(5, {"dimensions": []}))


class TestItemBorn(unittest.TestCase):
    def test_valid_date(self):
        born = item_born(_make_item(ts="2026-08-17T12:00:00Z"))
        self.assertIsNotNone(born)
        self.assertIsInstance(born, int)

    def test_valid_set(self):
        valid = set(range(1, 10)) | {11, 22, 33}
        self.assertIn(item_born(_make_item(ts="2026-01-15T00:00:00Z")), valid)

    def test_no_history(self):
        self.assertIsNone(item_born({**_make_item(), "history": []}))

    def test_no_intake_event(self):
        item = {
            **_make_item(), "stage": "qc",
            "history": [{"stage": "qc", "timestamp": "2026-08-17T12:00:00Z"}],
        }
        self.assertIsNone(item_born(item))

    def test_bad_timestamp(self):
        item = {**_make_item(), "history": [{"stage": "intake", "timestamp": "bad"}]}
        self.assertIsNone(item_born(item))


class TestBridgeItem(unittest.TestCase):
    def setUp(self):
        self.assessment = _make_assessment()

    def test_all_keys_present(self):
        reading = bridge_item(_make_item(), self.assessment)
        for key in ("item_id", "name", "stage", "born", "born_name",
                    "governing_position", "governing_dimension", "stage_dimensions"):
            self.assertIn(key, reading)

    def test_item_id_matches(self):
        self.assertEqual(bridge_item(_make_item(item_id="DS-9999"), self.assessment)["item_id"], "DS-9999")

    def test_born_present_with_intake(self):
        reading = bridge_item(_make_item(ts="2026-08-17T12:00:00Z"), self.assessment)
        self.assertIsNotNone(reading["born"])
        self.assertIsNotNone(reading["governing_dimension"])

    def test_no_intake_yields_none_born(self):
        reading = bridge_item({**_make_item(), "history": []}, self.assessment)
        self.assertIsNone(reading["born"])
        self.assertIsNone(reading["governing_dimension"])

    def test_distributed_includes_equality(self):
        positions = [d["position"] for d in bridge_item(_make_item(stage="distributed"), self.assessment)["stage_dimensions"]]
        self.assertIn(6, positions)

    def test_governing_position_consistent_with_born(self):
        reading = bridge_item(_make_item(ts="2026-08-17T12:00:00Z"), self.assessment)
        if reading["born"] is not None:
            self.assertEqual(reading["governing_position"], map_born_to_position(reading["born"]))


class TestStageHealth(unittest.TestCase):
    def setUp(self):
        self.assessment = _make_assessment({6: 8.33, 7: 10.0})

    def test_all_stages_non_empty(self):
        for stage in ("intake", "qc", "storage", "distributed"):
            self.assertGreater(len(stage_health(stage, self.assessment)), 0)

    def test_distributed_has_equality_and_consciousness(self):
        positions = {d["position"] for d in stage_health("distributed", self.assessment)}
        self.assertIn(6, positions)
        self.assertIn(7, positions)

    def test_qc_has_wisdom_and_build_destroy(self):
        positions = {d["position"] for d in stage_health("qc", self.assessment)}
        self.assertIn(2, positions)
        self.assertIn(8, positions)

    def test_unknown_stage_empty(self):
        self.assertEqual(stage_health("unknown", self.assessment), [])

    def test_scores_match_assessment(self):
        dims = stage_health("distributed", self.assessment)
        eq = next((d for d in dims if d["position"] == 6), None)
        self.assertAlmostEqual(eq["average"], 8.33)


def _make_donor(donor_id="D-0001", name="Test Donor", donation_date="2026-08-17"):
    return {"id": donor_id, "name": name, "donation_date": donation_date}


class TestDonorBorn(unittest.TestCase):
    def test_valid_date_yields_integer(self):
        born = donor_born(_make_donor(donation_date="2026-08-17"))
        self.assertIsNotNone(born)
        self.assertIsInstance(born, int)

    def test_born_in_valid_set(self):
        valid = set(range(1, 10)) | {11, 22, 33}
        self.assertIn(donor_born(_make_donor(donation_date="2026-01-15")), valid)

    def test_missing_date_returns_none(self):
        self.assertIsNone(donor_born({"id": "D-0001", "name": "No Date"}))

    def test_bad_date_returns_none(self):
        self.assertIsNone(donor_born(_make_donor(donation_date="not-a-date")))

    def test_iso_with_time_component(self):
        born = donor_born(_make_donor(donation_date="2026-08-17T14:30:00Z"))
        self.assertIsNotNone(born)

    def test_camel_case_field(self):
        donor = {"id": "D-0001", "donationDate": "2026-08-17"}
        self.assertIsNotNone(donor_born(donor))


class TestBridgeDonor(unittest.TestCase):
    def setUp(self):
        self.assessment = _make_assessment()

    def test_all_keys_present(self):
        reading = bridge_donor(_make_donor(), self.assessment)
        for key in ("donor_id", "name", "donation_date", "born", "born_name",
                    "governing_position", "governing_dimension"):
            self.assertIn(key, reading)

    def test_donor_id_matches(self):
        reading = bridge_donor(_make_donor(donor_id="D-9999"), self.assessment)
        self.assertEqual(reading["donor_id"], "D-9999")

    def test_born_present_with_date(self):
        reading = bridge_donor(_make_donor(donation_date="2026-08-17"), self.assessment)
        self.assertIsNotNone(reading["born"])
        self.assertIsNotNone(reading["governing_dimension"])

    def test_no_date_yields_none_born(self):
        reading = bridge_donor({"id": "D-0001", "name": "No Date"}, self.assessment)
        self.assertIsNone(reading["born"])
        self.assertIsNone(reading["governing_dimension"])

    def test_governing_position_consistent_with_born(self):
        reading = bridge_donor(_make_donor(donation_date="2026-08-17"), self.assessment)
        if reading["born"] is not None:
            self.assertEqual(reading["governing_position"], map_born_to_position(reading["born"]))


class TestMappingCoverage(unittest.TestCase):
    def test_all_four_stages_covered(self):
        for s in ("intake", "qc", "storage", "distributed"):
            self.assertIn(s, STAGE_TO_POSITIONS)

    def test_every_axiom_position_reachable(self):
        reachable = set()
        for n in range(1, 10):
            reachable.add(map_born_to_position(n))
        for positions in STAGE_TO_POSITIONS.values():
            reachable.update(positions)
        for pos in range(10):
            self.assertIn(pos, reachable, f"Position {pos} unreachable")


if __name__ == "__main__":
    unittest.main()
