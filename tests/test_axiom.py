"""Unit tests for axiom.py

Run with:
    pip install pytest
    pytest tests/
"""

import json
import os
import sys
import unittest

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import axiom


# ── get_category ──────────────────────────────────────────────────────────────

class TestGetCategory(unittest.TestCase):
    def test_absent_at_one(self):
        self.assertEqual(axiom.get_category(1.0), "Absent")

    def test_absent_at_three(self):
        self.assertEqual(axiom.get_category(3.0), "Absent")

    def test_absent_at_midpoint(self):
        self.assertEqual(axiom.get_category(2.5), "Absent")

    def test_emerging_at_four(self):
        self.assertEqual(axiom.get_category(4.0), "Emerging")

    def test_emerging_at_six(self):
        self.assertEqual(axiom.get_category(6.0), "Emerging")

    def test_emerging_at_midpoint(self):
        self.assertEqual(axiom.get_category(5.0), "Emerging")

    def test_established_at_seven(self):
        self.assertEqual(axiom.get_category(7.0), "Established")

    def test_established_at_eight(self):
        self.assertEqual(axiom.get_category(8.0), "Established")

    def test_established_at_midpoint(self):
        self.assertEqual(axiom.get_category(7.5), "Established")

    def test_mature_at_nine(self):
        self.assertEqual(axiom.get_category(9.0), "Mature")

    def test_mature_at_ten(self):
        self.assertEqual(axiom.get_category(10.0), "Mature")

    def test_mature_at_midpoint(self):
        self.assertEqual(axiom.get_category(9.5), "Mature")


# ── calculate_position_score ──────────────────────────────────────────────────

class TestCalculatePositionScore(unittest.TestCase):
    def test_uniform_scores(self):
        self.assertAlmostEqual(axiom.calculate_position_score([5.0, 5.0, 5.0]), 5.0)

    def test_known_average(self):
        self.assertAlmostEqual(axiom.calculate_position_score([6.0, 8.0, 10.0]), 8.0)

    def test_all_minimum(self):
        self.assertAlmostEqual(axiom.calculate_position_score([1.0, 1.0, 1.0]), 1.0)

    def test_all_maximum(self):
        self.assertAlmostEqual(axiom.calculate_position_score([10.0, 10.0, 10.0]), 10.0)

    def test_rounds_to_two_decimal_places(self):
        # 7 + 8 + 9 = 24 / 3 = 8.00 exactly
        result = axiom.calculate_position_score([7.0, 8.0, 9.0])
        self.assertAlmostEqual(result, 8.0, places=2)

    def test_non_integer_inputs(self):
        result = axiom.calculate_position_score([3.3, 6.6, 9.9])
        self.assertAlmostEqual(result, 6.6, places=2)

    def test_returns_float(self):
        result = axiom.calculate_position_score([5.0, 5.0, 5.0])
        self.assertIsInstance(result, float)


# ── calculate_aggregate ───────────────────────────────────────────────────────

class TestCalculateAggregate(unittest.TestCase):
    def test_uniform_scores(self):
        scores = [5.0] * 10
        self.assertAlmostEqual(axiom.calculate_aggregate(scores), 5.0)

    def test_known_average(self):
        # 0,2,4,6,8,10 pattern averaged over 10
        scores = [2.0, 4.0, 6.0, 8.0, 10.0, 2.0, 4.0, 6.0, 8.0, 10.0]
        self.assertAlmostEqual(axiom.calculate_aggregate(scores), 6.0)

    def test_all_minimum(self):
        self.assertAlmostEqual(axiom.calculate_aggregate([1.0] * 10), 1.0)

    def test_all_maximum(self):
        self.assertAlmostEqual(axiom.calculate_aggregate([10.0] * 10), 10.0)

    def test_rounds_to_two_decimal_places(self):
        result = axiom.calculate_aggregate([5.0] * 10)
        # Result should have at most 2 decimal places
        self.assertEqual(result, round(result, 2))


# ── find_top_gap ──────────────────────────────────────────────────────────────

class TestFindTopGap(unittest.TestCase):
    def _make_results(self, averages):
        return [
            {"position": i, "name": f"DIM{i}", "average": avg, "level": "Emerging"}
            for i, avg in enumerate(averages)
        ]

    def test_identifies_lowest(self):
        results = self._make_results([7.0, 3.0, 8.0, 6.0, 9.0, 5.0, 7.0, 8.0, 6.0, 9.0])
        gap = axiom.find_top_gap(results)
        self.assertEqual(gap["position"], 1)

    def test_identifies_last_position_as_lowest(self):
        results = self._make_results([8.0] * 9 + [1.0])
        gap = axiom.find_top_gap(results)
        self.assertEqual(gap["position"], 9)

    def test_identifies_first_position_as_lowest(self):
        results = self._make_results([1.0] + [8.0] * 9)
        gap = axiom.find_top_gap(results)
        self.assertEqual(gap["position"], 0)

    def test_returns_first_on_tie(self):
        results = self._make_results([3.0, 3.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0])
        gap = axiom.find_top_gap(results)
        self.assertEqual(gap["position"], 0)

    def test_returns_full_dict(self):
        results = self._make_results([5.0, 2.0, 9.0])
        gap = axiom.find_top_gap(results)
        self.assertIn("position", gap)
        self.assertIn("name", gap)
        self.assertIn("average", gap)


# ── make_safe_name ────────────────────────────────────────────────────────────

class TestMakeSafeName(unittest.TestCase):
    def test_alphanumeric_unchanged(self):
        self.assertEqual(axiom.make_safe_name("DonationStation"), "DonationStation")

    def test_spaces_replaced_with_underscore(self):
        self.assertEqual(axiom.make_safe_name("Donation Station"), "Donation_Station")

    def test_special_chars_replaced(self):
        self.assertEqual(axiom.make_safe_name("Org & Co."), "Org___Co_")

    def test_numbers_preserved(self):
        self.assertEqual(axiom.make_safe_name("Org123"), "Org123")

    def test_empty_string(self):
        self.assertEqual(axiom.make_safe_name(""), "")

    def test_only_special_chars(self):
        result = axiom.make_safe_name("!@#")
        self.assertEqual(result, "___")

    def test_hyphen_replaced(self):
        self.assertEqual(axiom.make_safe_name("My-Org"), "My_Org")


# ── build_report ──────────────────────────────────────────────────────────────

class TestBuildReport(unittest.TestCase):
    def _make_results(self, averages=None):
        if averages is None:
            averages = [5.0] * 10
        return [
            {
                "position": i,
                "name": f"DIM{i}",
                "scores": [avg, avg, avg],
                "average": avg,
                "level": axiom.get_category(avg),
            }
            for i, avg in enumerate(averages)
        ]

    def test_organization_name_preserved(self):
        report = axiom.build_report("Test Org", self._make_results())
        self.assertEqual(report["organization"], "Test Org")

    def test_timestamp_present(self):
        report = axiom.build_report("Test Org", self._make_results())
        self.assertIn("timestamp", report)

    def test_ten_dimensions_in_report(self):
        report = axiom.build_report("Test Org", self._make_results())
        self.assertEqual(len(report["dimensions"]), 10)

    def test_aggregate_score_correct(self):
        results = self._make_results([5.0] * 10)
        report = axiom.build_report("Test Org", results)
        self.assertAlmostEqual(report["aggregate_score"], 5.0)

    def test_aggregate_level_correct(self):
        results = self._make_results([5.0] * 10)
        report = axiom.build_report("Test Org", results)
        self.assertEqual(report["aggregate_level"], "Emerging")

    def test_top_gap_identified_correctly(self):
        averages = [7.0] * 10
        averages[4] = 1.5  # position 4 is the gap
        results = self._make_results(averages)
        report = axiom.build_report("Test Org", results)
        self.assertEqual(report["top_gap"]["position"], 4)

    def test_top_gap_has_required_fields(self):
        report = axiom.build_report("Test Org", self._make_results())
        gap = report["top_gap"]
        self.assertIn("position", gap)
        self.assertIn("name", gap)
        self.assertIn("score", gap)
        self.assertIn("level", gap)

    def test_mixed_levels_aggregate(self):
        # 5 dims at 2.0 (Absent) + 5 dims at 9.0 (Mature) → avg 5.5 (Emerging)
        averages = [2.0] * 5 + [9.0] * 5
        results = self._make_results(averages)
        report = axiom.build_report("Test Org", results)
        self.assertAlmostEqual(report["aggregate_score"], 5.5)
        self.assertEqual(report["aggregate_level"], "Emerging")


# ── write_report ──────────────────────────────────────────────────────────────

class TestWriteReport(unittest.TestCase):
    def _make_report(self, org="TestOrg"):
        return {
            "organization": org,
            "timestamp": "2024-01-01T00:00:00",
            "dimensions": [],
            "aggregate_score": 5.0,
            "aggregate_level": "Emerging",
            "top_gap": {"position": 0, "name": "DIM0", "score": 5.0, "level": "Emerging"},
        }

    def test_file_is_created(self, ):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = axiom.write_report(self._make_report(), tmpdir)
            self.assertTrue(os.path.exists(filepath))

    def test_file_contains_valid_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = axiom.write_report(self._make_report(), tmpdir)
            with open(filepath) as f:
                data = json.load(f)
            self.assertEqual(data["organization"], "TestOrg")

    def test_filename_contains_safe_org_name(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = axiom.write_report(self._make_report("My Org"), tmpdir)
            self.assertIn("My_Org", os.path.basename(filepath))

    def test_directory_created_if_missing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "nested", "assessments")
            filepath = axiom.write_report(self._make_report(), new_dir)
            self.assertTrue(os.path.exists(filepath))

    def test_returns_filepath_string(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = axiom.write_report(self._make_report(), tmpdir)
            self.assertIsInstance(result, str)

    def test_file_ends_with_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = axiom.write_report(self._make_report(), tmpdir)
            self.assertTrue(filepath.endswith(".json"))


# ── DIMENSIONS constant ───────────────────────────────────────────────────────

class TestDimensions(unittest.TestCase):
    def test_exactly_ten_dimensions(self):
        self.assertEqual(len(axiom.DIMENSIONS), 10)

    def test_positions_zero_through_nine(self):
        positions = [d["position"] for d in axiom.DIMENSIONS]
        self.assertEqual(positions, list(range(10)))

    def test_each_dimension_has_three_questions(self):
        for dim in axiom.DIMENSIONS:
            self.assertEqual(
                len(dim["questions"]),
                3,
                msg=f"Position {dim['position']} ({dim['name']}) has "
                    f"{len(dim['questions'])} questions, expected 3",
            )

    def test_required_fields_present(self):
        for dim in axiom.DIMENSIONS:
            for field in ("position", "name", "theme", "questions"):
                self.assertIn(
                    field,
                    dim,
                    msg=f"Position {dim.get('position', '?')} missing field '{field}'",
                )

    def test_names_match_decinary(self):
        expected_names = [
            "CIPHER/COMPLETION",
            "KNOWLEDGE",
            "WISDOM",
            "UNDERSTANDING",
            "CULTURED FREEDOM",
            "POWER REFINEMENT",
            "EQUALITY",
            "CONSCIOUSNESS",
            "BUILD/DESTROY",
            "BORN",
        ]
        actual_names = [d["name"] for d in axiom.DIMENSIONS]
        self.assertEqual(actual_names, expected_names)

    def test_questions_are_non_empty_strings(self):
        for dim in axiom.DIMENSIONS:
            for q in dim["questions"]:
                self.assertIsInstance(q, str)
                self.assertGreater(len(q.strip()), 0)


# ── Integration: score pipeline ───────────────────────────────────────────────

class TestScoringPipeline(unittest.TestCase):
    """End-to-end test of the score calculation chain without I/O."""

    def test_full_pipeline_all_fives(self):
        results = []
        for dim in axiom.DIMENSIONS:
            sub_scores = [5.0, 5.0, 5.0]
            avg = axiom.calculate_position_score(sub_scores)
            level = axiom.get_category(avg)
            results.append(
                {"position": dim["position"], "name": dim["name"],
                 "scores": sub_scores, "average": avg, "level": level}
            )
        report = axiom.build_report("Pipeline Test Org", results)
        self.assertAlmostEqual(report["aggregate_score"], 5.0)
        self.assertEqual(report["aggregate_level"], "Emerging")

    def test_full_pipeline_high_scores(self):
        results = []
        for dim in axiom.DIMENSIONS:
            sub_scores = [9.0, 10.0, 9.5]
            avg = axiom.calculate_position_score(sub_scores)
            level = axiom.get_category(avg)
            results.append(
                {"position": dim["position"], "name": dim["name"],
                 "scores": sub_scores, "average": avg, "level": level}
            )
        report = axiom.build_report("Pipeline Test Org", results)
        self.assertEqual(report["aggregate_level"], "Mature")

    def test_full_pipeline_low_scores(self):
        results = []
        for dim in axiom.DIMENSIONS:
            sub_scores = [1.0, 2.0, 1.5]
            avg = axiom.calculate_position_score(sub_scores)
            level = axiom.get_category(avg)
            results.append(
                {"position": dim["position"], "name": dim["name"],
                 "scores": sub_scores, "average": avg, "level": level}
            )
        report = axiom.build_report("Pipeline Test Org", results)
        self.assertEqual(report["aggregate_level"], "Absent")

    def test_gap_matches_lowest_dimension(self):
        averages = [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 2.0]
        results = [
            {
                "position": i,
                "name": axiom.DIMENSIONS[i]["name"],
                "scores": [avg, avg, avg],
                "average": avg,
                "level": axiom.get_category(avg),
            }
            for i, avg in enumerate(averages)
        ]
        report = axiom.build_report("Gap Test", results)
        self.assertEqual(report["top_gap"]["position"], 9)
        self.assertEqual(report["top_gap"]["name"], "BORN")


# ── scores_are_uniform ───────────────────────────────────────────────────────

class TestScoresAreUniform(unittest.TestCase):
    def _make_results(self, averages):
        return [{"position": i, "name": f"D{i}", "average": avg, "level": "Emerging"}
                for i, avg in enumerate(averages)]

    def test_all_equal_returns_true(self):
        self.assertTrue(axiom.scores_are_uniform(self._make_results([10.0] * 10)))

    def test_one_different_returns_false(self):
        avgs = [10.0] * 10
        avgs[5] = 9.0
        self.assertFalse(axiom.scores_are_uniform(self._make_results(avgs)))

    def test_all_different_returns_false(self):
        self.assertFalse(axiom.scores_are_uniform(self._make_results(list(range(1, 11)))))

    def test_single_item_returns_true(self):
        self.assertTrue(axiom.scores_are_uniform(self._make_results([7.0])))


# ── build_report uniform flag ─────────────────────────────────────────────────

class TestBuildReportUniformFlag(unittest.TestCase):
    def _make_results(self, avg):
        return [
            {"position": i, "name": f"D{i}", "scores": [avg]*3,
             "average": avg, "level": axiom.get_category(avg)}
            for i in range(10)
        ]

    def test_uniform_true_when_all_equal(self):
        report = axiom.build_report("Org", self._make_results(10.0))
        self.assertTrue(report["uniform"])

    def test_uniform_false_when_mixed(self):
        results = self._make_results(7.0)
        results[3]["average"] = 4.0
        report = axiom.build_report("Org", results)
        self.assertFalse(report["uniform"])

    def test_assessors_stored_when_provided(self):
        results = self._make_results(8.0)
        report = axiom.build_report("Org", results, assessors=["Alice", "Bob"])
        self.assertEqual(report["assessors"], ["Alice", "Bob"])
        self.assertEqual(report["assessor_count"], 2)

    def test_no_assessors_key_when_omitted(self):
        results = self._make_results(8.0)
        report = axiom.build_report("Org", results)
        self.assertNotIn("assessors", report)
        self.assertNotIn("assessor_count", report)


# ── print_report uniform output ───────────────────────────────────────────────

class TestPrintReportUniform(unittest.TestCase):
    """Verify print_report suppresses gap action when scores are uniform."""

    def _make_uniform_report(self):
        results = [
            {"position": i, "name": f"D{i}", "scores": [10.0]*3,
             "average": 10.0, "level": "Mature"}
            for i in range(10)
        ]
        return axiom.build_report("Test Org", results)

    def _make_varied_report(self):
        avgs = [7.0] * 10
        avgs[5] = 2.0
        results = [
            {"position": i, "name": f"D{i}", "scores": [a]*3,
             "average": a, "level": axiom.get_category(a)}
            for i, a in enumerate(avgs)
        ]
        return axiom.build_report("Test Org", results)

    def test_uniform_report_prints_no_gap_message(self):
        import io
        from contextlib import redirect_stdout
        report = self._make_uniform_report()
        buf = io.StringIO()
        with redirect_stdout(buf):
            axiom.print_report(report)
        output = buf.getvalue()
        self.assertIn("no gap identified", output.lower())
        self.assertNotIn("TOP GAP", output)

    def test_varied_report_prints_top_gap(self):
        import io
        from contextlib import redirect_stdout
        report = self._make_varied_report()
        buf = io.StringIO()
        with redirect_stdout(buf):
            axiom.print_report(report)
        output = buf.getvalue()
        self.assertIn("TOP GAP", output)


# ── print_comparison ──────────────────────────────────────────────────────────

class TestPrintComparison(unittest.TestCase):
    def _make_report(self, org, averages):
        results = [
            {"position": i, "name": axiom.DIMENSIONS[i]["name"],
             "scores": [a]*3, "average": a, "level": axiom.get_category(a)}
            for i, a in enumerate(averages)
        ]
        return axiom.build_report(org, results)

    def test_comparison_runs_without_error(self):
        import io
        from contextlib import redirect_stdout
        a = self._make_report("Org A", [7.0] * 10)
        b = self._make_report("Org B", [8.0] * 10)
        buf = io.StringIO()
        with redirect_stdout(buf):
            axiom.print_comparison(a, b)
        output = buf.getvalue()
        self.assertIn("Org A", output)
        self.assertIn("Org B", output)

    def test_comparison_shows_delta(self):
        import io
        from contextlib import redirect_stdout
        a = self._make_report("Org A", [5.0] * 10)
        b = self._make_report("Org B", [8.0] * 10)
        buf = io.StringIO()
        with redirect_stdout(buf):
            axiom.print_comparison(a, b)
        output = buf.getvalue()
        self.assertIn("+3.00", output)

    def test_comparison_identifies_largest_gain(self):
        import io
        from contextlib import redirect_stdout
        avgs_a = [5.0] * 10
        avgs_b = [5.0] * 10
        avgs_b[3] = 9.0  # big gain at position 3
        a = self._make_report("Org A", avgs_a)
        b = self._make_report("Org B", avgs_b)
        buf = io.StringIO()
        with redirect_stdout(buf):
            axiom.print_comparison(a, b)
        output = buf.getvalue()
        self.assertIn("LARGEST GAIN", output)
        self.assertIn("UNDERSTANDING", output)

    def test_comparison_identifies_largest_drop(self):
        import io
        from contextlib import redirect_stdout
        avgs_a = [8.0] * 10
        avgs_b = [8.0] * 10
        avgs_b[7] = 3.0  # big drop at position 7
        a = self._make_report("Org A", avgs_a)
        b = self._make_report("Org B", avgs_b)
        buf = io.StringIO()
        with redirect_stdout(buf):
            axiom.print_comparison(a, b)
        output = buf.getvalue()
        self.assertIn("LARGEST DROP", output)
        self.assertIn("CONSCIOUSNESS", output)

    def test_no_movement_message_when_identical(self):
        import io
        from contextlib import redirect_stdout
        a = self._make_report("Org A", [7.0] * 10)
        b = self._make_report("Org B", [7.0] * 10)
        buf = io.StringIO()
        with redirect_stdout(buf):
            axiom.print_comparison(a, b)
        output = buf.getvalue()
        self.assertIn("No movement", output)


# ── run_comparison file loading ───────────────────────────────────────────────

class TestRunComparison(unittest.TestCase):
    def _write_report(self, path, org, averages):
        results = [
            {"position": i, "name": axiom.DIMENSIONS[i]["name"],
             "scores": [a]*3, "average": a, "level": axiom.get_category(a)}
            for i, a in enumerate(averages)
        ]
        report = axiom.build_report(org, results)
        with open(path, "w") as f:
            json.dump(report, f)

    def test_compare_two_files(self):
        import io
        import tempfile
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmpdir:
            path_a = os.path.join(tmpdir, "a.json")
            path_b = os.path.join(tmpdir, "b.json")
            self._write_report(path_a, "Org A", [5.0] * 10)
            self._write_report(path_b, "Org B", [8.0] * 10)
            buf = io.StringIO()
            with redirect_stdout(buf):
                axiom.run_comparison(path_a, path_b)
            output = buf.getvalue()
            self.assertIn("Org A", output)
            self.assertIn("Org B", output)

    def test_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            axiom.run_comparison("/nonexistent/a.json", "/nonexistent/b.json")


if __name__ == "__main__":
    unittest.main()
