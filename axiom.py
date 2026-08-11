#!/usr/bin/env python3
"""
AXIOM — Decinary Diagnostic Tool

Assesses an organization or community across ten dimensions of the
Decinary Operating System (positions 0–9). Each dimension is scored
via three sub-questions on a 1–10 scale. Scores aggregate to a
categorical level and a single composite reading.

Usage:
    python axiom.py                          # single-assessor intake
    python axiom.py --multi                  # multi-assessor intake (averages N scorers)
    python axiom.py --compare a.json b.json  # compare two assessment files
"""

import argparse
import json
import os
import sys
from datetime import datetime

# ── Dimensions ────────────────────────────────────────────────────────────────

DIMENSIONS = [
    {
        "position": 0,
        "name": "CIPHER/COMPLETION",
        "theme": "wholeness, integration, return to source",
        "questions": [
            "How consistently does the organization complete the cycles it begins "
            "(projects, commitments, initiatives — started and closed)?",
            "How well does the organization integrate lessons from past work into "
            "current practice rather than repeating resolved errors?",
            "To what extent do members report a sense of wholeness and shared purpose "
            "within the organization — feeling part of something coherent?",
        ],
    },
    {
        "position": 1,
        "name": "KNOWLEDGE",
        "theme": "foundation, awareness, acknowledgment with self",
        "questions": [
            "How clearly does the organization understand its own history, founding "
            "principles, and the problem it was built to solve?",
            "To what degree do members demonstrate self-awareness of their individual "
            "roles, responsibilities, and personal development edges?",
            "How reliably does the organization document and preserve institutional "
            "knowledge — so it survives leadership transitions?",
        ],
    },
    {
        "position": 2,
        "name": "WISDOM",
        "theme": "action, practical application, expansion with family",
        "questions": [
            "How effectively does the organization translate accumulated knowledge "
            "into practical programs, services, or actions that produce results?",
            "To what degree has the organization expanded its reach and impact within "
            "its immediate community — the people closest to its core?",
            "How consistently does leadership apply learned wisdom to decision-making "
            "rather than defaulting to reactive or untested approaches?",
        ],
    },
    {
        "position": 3,
        "name": "UNDERSTANDING",
        "theme": "depth, gratitude, integration with friends",
        "questions": [
            "How deeply does the organization understand the lived experience and "
            "actual needs of the communities it serves — beyond surface data?",
            "To what degree does the organization express genuine gratitude and "
            "recognition toward its partners, allies, and collaborators?",
            "How well does the organization integrate feedback from peer organizations "
            "and allies into its own strategy and operations?",
        ],
    },
    {
        "position": 4,
        "name": "CULTURED FREEDOM",
        "theme": "embodiment, responsible stewardship with love",
        "questions": [
            "To what extent does the organization embody its stated values in daily "
            "operations — not just in mission language but in observable behavior?",
            "How responsibly does the organization steward its resources — financial, "
            "human, physical — without waste, exploitation, or neglect?",
            "How much genuine care is expressed in the organization's relationships "
            "with community members — treating people as whole human beings?",
        ],
    },
    {
        "position": 5,
        "name": "POWER REFINEMENT",
        "theme": "conscious resource allocation, truth with education",
        "questions": [
            "How consciously and equitably does the organization allocate its "
            "resources — directing power toward highest-leverage community needs?",
            "To what degree does the organization operate with transparency and "
            "truth in its internal and external communications?",
            "How robust are the organization's educational and capacity-building "
            "programs — developing knowledge in the people it serves?",
        ],
    },
    {
        "position": 6,
        "name": "EQUALITY",
        "theme": "balance, internal manifestation with training",
        "questions": [
            "How equitably are opportunities, recognition, and responsibilities "
            "distributed within the organization across roles and demographics?",
            "To what degree has the organization manifested its stated equity goals "
            "internally — in staff conditions, compensation, and culture?",
            "How effective are the organization's training and skill-development "
            "programs in raising the capacity of its people?",
        ],
    },
    {
        "position": 7,
        "name": "CONSCIOUSNESS",
        "theme": "divine creativity, illumination with skilled labor",
        "questions": [
            "How creatively does the organization approach problem-solving — "
            "generating new approaches rather than recycling standard templates?",
            "To what degree does the organization inspire and illuminate new "
            "thinking in its field — shifting how others see the problem?",
            "To what degree does the organization inspire the people it serves "
            "to see themselves differently — not just receive services, but "
            "awaken to their own agency?",
        ],
    },
    {
        "position": 8,
        "name": "BUILD/DESTROY",
        "theme": "transformation, collective elevation with social development",
        "questions": [
            "How effectively does the organization identify and dismantle "
            "dysfunctional internal patterns or structures that limit its impact?",
            "To what degree does the organization elevate the collective capacity "
            "of the community it serves — not just deliver services to it?",
            "How actively does the organization engage in broader social development "
            "work beyond its immediate programs — contributing to systemic change?",
        ],
    },
    {
        "position": 9,
        "name": "BORN",
        "theme": "relational renewal, emergence with economic development",
        "questions": [
            "How consistently does the organization renew and deepen its key "
            "relationships — preventing stagnation in its network?",
            "To what degree is the organization generating new initiatives, leaders, "
            "or approaches — evidence of emergence and forward motion?",
            "How effectively does the organization contribute to and participate in "
            "local economic development — building wealth within the community?",
        ],
    },
]

# ── Scoring logic ─────────────────────────────────────────────────────────────

def get_category(score: float) -> str:
    """Map a numeric score (1–10) to a categorical level."""
    if score <= 3:
        return "Absent"
    elif score <= 6:
        return "Emerging"
    elif score <= 8:
        return "Established"
    else:
        return "Mature"


def calculate_position_score(sub_scores: list) -> float:
    """Return the average of a list of sub-scores, rounded to 2 decimal places."""
    return round(sum(sub_scores) / len(sub_scores), 2)


def calculate_aggregate(position_averages: list) -> float:
    """Return the aggregate score across all position averages."""
    return round(sum(position_averages) / len(position_averages), 2)


def find_top_gap(results: list) -> dict:
    """Return the dimension result with the lowest average score."""
    return min(results, key=lambda r: r["average"])


def scores_are_uniform(results: list) -> bool:
    """Return True if all dimension averages are equal."""
    averages = [r["average"] for r in results]
    return len(set(averages)) == 1


def make_safe_name(org_name: str) -> str:
    """Return a filesystem-safe version of an organization name."""
    return "".join(c if c.isalnum() else "_" for c in org_name)


def build_report(org_name: str, results: list, assessors: list = None) -> dict:
    """Assemble the full assessment report dictionary."""
    position_averages = [r["average"] for r in results]
    aggregate = calculate_aggregate(position_averages)
    gap = find_top_gap(results)
    report = {
        "organization": org_name,
        "timestamp": datetime.now().isoformat(),
        "dimensions": results,
        "aggregate_score": aggregate,
        "aggregate_level": get_category(aggregate),
        "top_gap": {
            "position": gap["position"],
            "name": gap["name"],
            "score": gap["average"],
            "level": gap["level"],
        },
        "uniform": scores_are_uniform(results),
    }
    if assessors:
        report["assessors"] = assessors
        report["assessor_count"] = len(assessors)
    return report


def write_report(report: dict, directory: str) -> str:
    """Write the report as a JSON file. Returns the file path written."""
    os.makedirs(directory, exist_ok=True)
    safe_name = make_safe_name(report["organization"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.json"
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    return filepath


# ── Terminal output ───────────────────────────────────────────────────────────

def print_report(report: dict) -> None:
    """Print the assessment results to the terminal."""
    sep = "─" * 62
    print(f"\n{sep}")
    print(f"  AXIOM ASSESSMENT RESULTS")
    print(f"{sep}")
    print(f"  Organization : {report['organization']}")
    print(f"  Assessed     : {report['timestamp'][:19].replace('T', '  ')}")
    if report.get("assessor_count", 1) > 1:
        names = ", ".join(report.get("assessors", []))
        print(f"  Assessors    : {report['assessor_count']}  ({names})")
    print(f"{sep}")
    print(f"  {'POS':<4} {'DIMENSION':<25} {'SCORE':>6}  {'LEVEL'}")
    print(f"  {'---':<4} {'---------':<25} {'-----':>6}  {'-----'}")
    for dim in report["dimensions"]:
        print(
            f"  {dim['position']:<4} {dim['name']:<25} {dim['average']:>6.2f}  {dim['level']}"
        )
    print(f"{sep}")
    print(
        f"  {'AGGREGATE':<29} {report['aggregate_score']:>6.2f}  {report['aggregate_level']}"
    )
    print(f"{sep}")

    if report.get("uniform"):
        print(f"\n  All dimensions scored equally — no gap identified.\n")
    else:
        gap = report["top_gap"]
        print(f"\n  TOP GAP  →  Position {gap['position']}: {gap['name']}")
        print(f"             Score {gap['score']:.2f} — {gap['level']}")
        print(f"\n  Action: Prioritize investment in {gap['name']} before")
        print(f"          scaling other dimensions.\n")


def print_comparison(report_a: dict, report_b: dict) -> None:
    """Print a side-by-side comparison of two assessment reports."""
    sep = "─" * 70
    name_a = report_a["organization"]
    name_b = report_b["organization"]
    date_a = report_a["timestamp"][:10]
    date_b = report_b["timestamp"][:10]

    print(f"\n{sep}")
    print(f"  AXIOM COMPARISON")
    print(f"{sep}")
    print(f"  A: {name_a:<36} {date_a}")
    print(f"  B: {name_b:<36} {date_b}")
    print(f"{sep}")
    print(f"  {'POS':<4} {'DIMENSION':<22} {'SCORE A':>7}  {'SCORE B':>7}  {'DELTA':>7}  {'MOVE'}")
    print(f"  {'---':<4} {'---------':<22} {'-------':>7}  {'-------':>7}  {'-----':>7}  {'----'}")

    dims_a = {d["position"]: d for d in report_a["dimensions"]}
    dims_b = {d["position"]: d for d in report_b["dimensions"]}
    deltas = []

    for pos in range(10):
        da = dims_a.get(pos)
        db = dims_b.get(pos)
        if not da or not db:
            continue
        delta = round(db["average"] - da["average"], 2)
        deltas.append((pos, da["name"], delta))
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "─")
        print(
            f"  {pos:<4} {da['name']:<22} {da['average']:>7.2f}  {db['average']:>7.2f}  "
            f"{delta:>+7.2f}  {arrow}"
        )

    agg_a = report_a["aggregate_score"]
    agg_b = report_b["aggregate_score"]
    agg_delta = round(agg_b - agg_a, 2)
    agg_arrow = "▲" if agg_delta > 0 else ("▼" if agg_delta < 0 else "─")
    print(f"{sep}")
    print(
        f"  {'AGGREGATE':<26} {agg_a:>7.2f}  {agg_b:>7.2f}  "
        f"{agg_delta:>+7.2f}  {agg_arrow}"
    )
    print(f"{sep}")

    gains = [(pos, name, d) for pos, name, d in deltas if d > 0]
    losses = [(pos, name, d) for pos, name, d in deltas if d < 0]

    if gains:
        best = max(gains, key=lambda x: x[2])
        print(f"\n  LARGEST GAIN  →  Position {best[0]}: {best[1]}  ({best[2]:+.2f})")
    if losses:
        worst = min(losses, key=lambda x: x[2])
        print(f"  LARGEST DROP  →  Position {worst[0]}: {worst[1]}  ({worst[2]:+.2f})")
    if not gains and not losses:
        print(f"\n  No movement between assessments.")
    print()


# ── CLI intake ────────────────────────────────────────────────────────────────

def prompt_score(question: str, sub_num: int) -> float:
    """Prompt the user for a single 1–10 sub-question score."""
    while True:
        try:
            raw = input(f"    [{sub_num}/3] {question}\n           Score (1–10): ").strip()
            value = float(raw)
            if 1.0 <= value <= 10.0:
                return value
            print("           Enter a number between 1 and 10.")
        except ValueError:
            print("           Enter a number between 1 and 10.")
        except (EOFError, KeyboardInterrupt):
            print("\nAssessment cancelled.")
            sys.exit(0)


def _collect_scores(org_name: str, assessor_label: str = "") -> list:
    """Walk through all ten dimensions and collect scores. Returns results list."""
    label = f" ({assessor_label})" if assessor_label else ""
    print(f"\n  Assessing: {org_name}{label}")
    print(f"  Answer 3 questions per dimension (30 total).")
    print(f"  Score each question from 1 (lowest) to 10 (highest).\n")

    results = []
    for dim in DIMENSIONS:
        print(f"\n  ── Position {dim['position']}: {dim['name']} ──")
        print(f"     Theme: {dim['theme']}\n")
        sub_scores = []
        for i, question in enumerate(dim["questions"], start=1):
            score = prompt_score(question, i)
            sub_scores.append(score)
        avg = calculate_position_score(sub_scores)
        level = get_category(avg)
        results.append(
            {
                "position": dim["position"],
                "name": dim["name"],
                "scores": sub_scores,
                "average": avg,
                "level": level,
            }
        )
        print(f"     → {dim['name']}: {avg:.2f}  [{level}]")
    return results


def run_assessment(assessments_dir: str = "assessments") -> None:
    """Single-assessor interactive CLI."""
    print("\n" + "=" * 62)
    print("  AXIOM — Decinary Diagnostic Tool")
    print("  Ten dimensions. Honest numbers. Actionable gaps.")
    print("=" * 62)

    try:
        org_name = input("\n  Organization being assessed: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAssessment cancelled.")
        sys.exit(0)

    if not org_name:
        print("Organization name cannot be blank.")
        sys.exit(1)

    results = _collect_scores(org_name)
    report = build_report(org_name, results)
    print_report(report)
    filepath = write_report(report, assessments_dir)
    print(f"  Report saved → {filepath}\n")


def run_multi_assessment(assessments_dir: str = "assessments") -> None:
    """Multi-assessor interactive CLI — averages scores across N scorers."""
    print("\n" + "=" * 62)
    print("  AXIOM — Decinary Diagnostic Tool  [Multi-Assessor]")
    print("  Scores averaged across all assessors.")
    print("=" * 62)

    try:
        org_name = input("\n  Organization being assessed: ").strip()
        if not org_name:
            print("Organization name cannot be blank.")
            sys.exit(1)

        raw = input("  Number of assessors (2–10): ").strip()
        n = int(raw)
        if not 2 <= n <= 10:
            print("  Enter a number between 2 and 10.")
            sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAssessment cancelled.")
        sys.exit(0)
    except ValueError:
        print("  Enter a valid number.")
        sys.exit(1)

    all_results = []
    assessor_names = []
    for i in range(1, n + 1):
        try:
            name = input(f"\n  Assessor {i} name: ").strip() or f"Assessor {i}"
        except (EOFError, KeyboardInterrupt):
            print("\nAssessment cancelled.")
            sys.exit(0)
        assessor_names.append(name)
        print(f"\n{'─' * 62}")
        print(f"  Scoring by: {name}")
        print(f"{'─' * 62}")
        results = _collect_scores(org_name, assessor_label=name)
        all_results.append(results)

    # Average sub-scores across all assessors per dimension per question
    averaged_results = []
    for dim_idx, dim in enumerate(DIMENSIONS):
        averaged_sub_scores = []
        for q_idx in range(3):
            avg_score = round(
                sum(all_results[a][dim_idx]["scores"][q_idx] for a in range(n)) / n, 2
            )
            averaged_sub_scores.append(avg_score)
        avg = calculate_position_score(averaged_sub_scores)
        level = get_category(avg)
        averaged_results.append(
            {
                "position": dim["position"],
                "name": dim["name"],
                "scores": averaged_sub_scores,
                "average": avg,
                "level": level,
            }
        )

    report = build_report(org_name, averaged_results, assessors=assessor_names)
    print_report(report)
    filepath = write_report(report, assessments_dir)
    print(f"  Report saved → {filepath}\n")


def run_comparison(path_a: str, path_b: str) -> None:
    """Load two JSON reports and print a comparison."""
    for path in (path_a, path_b):
        if not os.path.exists(path):
            print(f"File not found: {path}")
            sys.exit(1)
    with open(path_a) as f:
        report_a = json.load(f)
    with open(path_b) as f:
        report_b = json.load(f)
    print_comparison(report_a, report_b)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AXIOM — Decinary Diagnostic Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python axiom.py\n"
            "  python axiom.py --multi\n"
            "  python axiom.py --compare assessments/OrgA.json assessments/OrgB.json"
        ),
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Multi-assessor mode: average scores from N scorers",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("FILE_A", "FILE_B"),
        help="Compare two saved assessment JSON files",
    )
    args = parser.parse_args()

    if args.compare:
        run_comparison(args.compare[0], args.compare[1])
    elif args.multi:
        run_multi_assessment()
    else:
        run_assessment()


if __name__ == "__main__":
    main()
