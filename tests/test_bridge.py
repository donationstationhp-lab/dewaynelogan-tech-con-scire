import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge import (
    map_born_to_position,
    map_stage_to_positions,
    get_dimension_score,
    item_born_number,
    bridge_item,
    stage_health,
    born_name,
    BORN_TO_POSITION,
    STAGE_TO_POSITIONS,
)


def _make_assessment(scores=None):
    """Build a minimal assessment dict with optional per-position scores."""
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
        "category": "general",
        "condition": "good",
        "stage": stage,
        "history": [{"stage": "intake", "timestamp": ts}],
    }


class TestMapBornToPosition(unittest.TestCase):
    def test_origin_maps_to_knowledge(self):
        self.assertEqual(map_born_to_position(1), 1)

    def test_wisdom_maps_to_wisdom(self):
        self.assertEqual(map_born_to_position(2), 2)

    def test_equality_maps_to_equality(self):
        self.assertEqual(map_born_to_position(6), 6)

    def test_completion_maps_to_cipher(self):
        self.assertEqual(map_born_to_position(9), 0)

    def test_master_illumination_maps_to_consciousness(self):
        self.assertEqual(map_born_to_position(11), 7)

    def test_master_builder_maps_to_cultured_freedom(self):
        self.assertEqual(map_born_to_position(22), 4)

    def test_master_teacher_maps_to_build_destroy(self):
        self.assertEqual(map_born_to_position(33), 8)

    def test_all_single_digits_yield_valid_positions(self):
        for n in range(1, 10):
            pos = map_born_to_position(n)
            self.assertIn(pos, range(10), f"born={n} gave invalid position {pos}")

    def test_all_master_numbers_yield_valid_positions(self):
        for n in (11, 22, 33):
            pos = map_born_to_position(n)
            self.assertIn(pos, range(10))

    def test_unknown_falls_back_to_modulo(self):
        self.assertEqual(map_born_to_position(15), 5)
        self.assertEqual(map_born_to_position(17), 7)

    def test_every_single_digit_in_table(self):
        for n in range(1, 10):
            self.assertIn(n, BORN_TO_POSITION)


class TestMapStageToPositions(unittest.TestCase):
    def test_all_four_stages_return_positions(self):
        for stage in ("intake", "qc", "storage", "distributed"):
            positions = map_stage_to_positions(stage)
            self.assertIsInstance(positions, list)
            self.assertGreater(len(positions), 0, f"stage={stage} returned no positions")

    def test_unknown_stage_returns_empty(self):
        self.assertEqual(map_stage_to_positions("unknown"), [])
        self.assertEqual(map_stage_to_positions(""), [])

    def test_distributed_governs_equality_and_consciousness(self):
        positions = map_stage_to_positions("distributed")
        self.assertIn(6, positions)
        self.assertIn(7, positions)

    def test_storage_governs_cultured_freedom(self):
        self.assertIn(4, map_stage_to_positions("storage"))

    def test_qc_governs_wisdom(self):
        self.assertIn(2, map_stage_to_positions("qc"))

    def test_intake_governs_knowledge(self):
        self.assertIn(1, map_stage_to_positions("intake"))

    def test_all_positions_in_table_are_valid(self):
        for stage, positions in STAGE_TO_POSITIONS.items():
            for pos in positions:
                self.assertIn(pos, range(10))


class TestGetDimensionScore(unittest.TestCase):
    def setUp(self):
        self.assessment = _make_assessment({0: 10.0, 6: 8.33})

    def test_found_by_position(self):
        dim = get_dimension_score(6, self.assessment)
        self.assertIsNotNone(dim)
        self.assertAlmostEqual(dim["average"], 8.33)

    def test_position_zero_found(self):
        dim = get_dimension_score(0, self.assessment)
        self.assertIsNotNone(dim)
        self.assertEqual(dim["average"], 10.0)

    def test_missing_position_returns_none(self):
        empty = {"dimensions": []}
        self.assertIsNone(get_dimension_score(5, empty))

    def test_returns_dict_with_expected_keys(self):
        dim = get_dimension_score(0, self.assessment)
        self.assertIn("position", dim)
        self.assertIn("average", dim)
        self.assertIn("level", dim)


class TestBornName(unittest.TestCase):
    def test_single_digit_names(self):
        self.assertEqual(born_name(1), "Origin")
        self.assertEqual(born_name(6), "Equality")
        self.assertEqual(born_name(9), "Completion")

    def test_master_number_names(self):
        self.assertEqual(born_name(11), "Illumination")
        self.assertEqual(born_name(22), "Master Builder")
        self.assertEqual(born_name(33), "Master Teacher")

    def test_none_returns_none(self):
        self.assertIsNone(born_name(None))

    def test_unknown_number_returns_string(self):
        result = born_name(99)
        self.assertIsNotNone(result)


class TestItemBornNumber(unittest.TestCase):
    def test_known_date_yields_integer(self):
        item = _make_item(ts="2026-08-17T12:00:00Z")
        born = item_born_number(item)
        self.assertIsNotNone(born)
        self.assertIsInstance(born, int)

    def test_born_is_single_digit_or_master(self):
        item = _make_item(ts="2026-01-15T00:00:00Z")
        born = item_born_number(item)
        valid = set(range(1, 10)) | {11, 22, 33}
        self.assertIn(born, valid)

    def test_no_history_returns_none(self):
        item = {**_make_item(), "history": []}
        self.assertIsNone(item_born_number(item))

    def test_no_intake_event_returns_none(self):
        item = {
            **_make_item(),
            "stage": "qc",
            "history": [{"stage": "qc", "timestamp": "2026-08-17T12:00:00Z"}],
        }
        self.assertIsNone(item_born_number(item))

    def test_bad_timestamp_returns_none(self):
        item = {**_make_item(), "history": [{"stage": "intake", "timestamp": "not-a-date"}]}
        self.assertIsNone(item_born_number(item))

    def test_different_dates_may_yield_different_born(self):
        item_a = _make_item(ts="2026-01-01T00:00:00Z")
        item_b = _make_item(ts="2026-07-04T00:00:00Z")
        born_a = item_born_number(item_a)
        born_b = item_born_number(item_b)
        # Both should be valid; they may or may not differ
        self.assertIsNotNone(born_a)
        self.assertIsNotNone(born_b)


class TestBridgeItem(unittest.TestCase):
    def setUp(self):
        self.assessment = _make_assessment()

    def test_returns_all_expected_keys(self):
        item = _make_item()
        reading = bridge_item(item, self.assessment)
        for key in ("item_id", "name", "stage", "born", "born_name",
                    "governing_position", "governing_dimension", "stage_dimensions"):
            self.assertIn(key, reading)

    def test_item_id_matches(self):
        item = _make_item(item_id="DS-9999")
        reading = bridge_item(item, self.assessment)
        self.assertEqual(reading["item_id"], "DS-9999")

    def test_born_number_present_for_item_with_intake(self):
        item = _make_item(ts="2026-08-17T12:00:00Z")
        reading = bridge_item(item, self.assessment)
        self.assertIsNotNone(reading["born"])
        self.assertIsNotNone(reading["governing_dimension"])

    def test_no_intake_yields_none_born(self):
        item = {**_make_item(), "history": []}
        reading = bridge_item(item, self.assessment)
        self.assertIsNone(reading["born"])
        self.assertIsNone(reading["governing_position"])
        self.assertIsNone(reading["governing_dimension"])

    def test_stage_dimensions_populated(self):
        item = _make_item(stage="distributed")
        reading = bridge_item(item, self.assessment)
        self.assertGreater(len(reading["stage_dimensions"]), 0)

    def test_distributed_stage_includes_equality_dimension(self):
        item = _make_item(stage="distributed")
        reading = bridge_item(item, self.assessment)
        positions = [d["position"] for d in reading["stage_dimensions"]]
        self.assertIn(6, positions)

    def test_governing_dimension_position_matches_born_map(self):
        item = _make_item(ts="2026-08-17T12:00:00Z")
        reading = bridge_item(item, self.assessment)
        if reading["born"] is not None:
            expected_pos = map_born_to_position(reading["born"])
            self.assertEqual(reading["governing_position"], expected_pos)


class TestStageHealth(unittest.TestCase):
    def setUp(self):
        self.assessment = _make_assessment({
            1: 9.0, 2: 7.5, 3: 6.0, 4: 8.0,
            5: 5.0, 6: 8.33, 7: 10.0, 8: 9.0, 9: 10.0,
        })

    def test_all_stages_return_non_empty(self):
        for stage in ("intake", "qc", "storage", "distributed"):
            dims = stage_health(stage, self.assessment)
            self.assertGreater(len(dims), 0, f"stage={stage} returned no dimensions")

    def test_distributed_returns_equality_and_consciousness(self):
        dims = stage_health("distributed", self.assessment)
        positions = {d["position"] for d in dims}
        self.assertIn(6, positions)
        self.assertIn(7, positions)

    def test_qc_returns_wisdom_and_build_destroy(self):
        dims = stage_health("qc", self.assessment)
        positions = {d["position"] for d in dims}
        self.assertIn(2, positions)
        self.assertIn(8, positions)

    def test_unknown_stage_returns_empty(self):
        dims = stage_health("unknown", self.assessment)
        self.assertEqual(dims, [])

    def test_scores_match_assessment(self):
        dims = stage_health("distributed", self.assessment)
        equality_dim = next((d for d in dims if d["position"] == 6), None)
        self.assertIsNotNone(equality_dim)
        self.assertAlmostEqual(equality_dim["average"], 8.33)


class TestMappingCoverage(unittest.TestCase):
    def test_all_nine_born_numbers_map_to_distinct_positions(self):
        positions = {map_born_to_position(n) for n in range(1, 10)}
        # Nine born numbers, each should map to a valid position
        self.assertEqual(len(positions), 9)

    def test_all_four_stages_covered(self):
        for stage in ("intake", "qc", "storage", "distributed"):
            self.assertIn(stage, STAGE_TO_POSITIONS)

    def test_every_axiom_position_0_to_9_is_reachable(self):
        # Every AXIOM position (0-9) should be reachable from some born number or stage
        reachable = set()
        for n in range(1, 10):
            reachable.add(map_born_to_position(n))
        for positions in STAGE_TO_POSITIONS.values():
            reachable.update(positions)
        for pos in range(10):
            self.assertIn(pos, reachable, f"AXIOM position {pos} is unreachable")


if __name__ == "__main__":
    unittest.main()
