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


# ── Ecosystem logic ───────────────────────────────────────────────────────────

STRENGTH_THRESHOLD = 9.0


def calculate_pairwise_distances(reports: list) -> list:
    """Return all org pairs sorted by relational distance (sum of dim deltas)."""
    orgs = [
        (r["organization"], {d["position"]: d["average"] for d in r["dimensions"]})
        for r in reports
    ]
    pairs = []
    for i in range(len(orgs)):
        for j in range(i + 1, len(orgs)):
            name_a, dims_a = orgs[i]
            name_b, dims_b = orgs[j]
            distance = round(
                sum(abs(dims_a.get(p, 0) - dims_b.get(p, 0)) for p in range(10)), 2
            )
            pairs.append({"orgs": [name_a, name_b], "distance": distance})
    pairs.sort(key=lambda x: x["distance"])
    return pairs


def build_ecosystem_report(reports: list, source_files: list = None) -> dict:
    """Assemble an ecosystem report from a list of individual assessment reports."""
    org_names = [r["organization"] for r in reports]
    org_aggregates = [r["aggregate_score"] for r in reports]
    ecosystem_aggregate = round(sum(org_aggregates) / len(org_aggregates), 2)

    dim_analysis = []
    for pos in range(10):
        dim_name = DIMENSIONS[pos]["name"]
        scores = {}
        for r in reports:
            for d in r["dimensions"]:
                if d["position"] == pos:
                    scores[r["organization"]] = d["average"]
        values = list(scores.values())
        avg = round(sum(values) / len(values), 2)
        dim_analysis.append({
            "position": pos,
            "name": dim_name,
            "scores": scores,
            "average": avg,
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "level": get_category(avg),
            "uniform": len(set(values)) == 1,
        })

    strengths = [d for d in dim_analysis if d["min"] >= STRENGTH_THRESHOLD]
    vulnerabilities = []
    for d in dim_analysis:
        gaps = {org: score for org, score in d["scores"].items()
                if score < STRENGTH_THRESHOLD}
        if gaps:
            vulnerabilities.append({
                "position": d["position"],
                "name": d["name"],
                "gaps": gaps,
            })

    pairs = calculate_pairwise_distances(reports) if len(reports) > 1 else []

    return {
        "type": "ecosystem",
        "timestamp": datetime.now().isoformat(),
        "organization_count": len(reports),
        "organizations": org_names,
        "dimensions": dim_analysis,
        "ecosystem_aggregate": ecosystem_aggregate,
        "ecosystem_level": get_category(ecosystem_aggregate),
        "collective_strengths": strengths,
        "shared_vulnerabilities": vulnerabilities,
        "relational_map": {
            "closest": pairs[0] if pairs else None,
            "most_divergent": pairs[-1] if pairs else None,
            "all_pairs": pairs,
        },
        "source_files": source_files or [],
    }


def write_ecosystem_report(report: dict, directory: str) -> str:
    """Write the ecosystem report as a JSON file. Returns the file path written."""
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(directory, f"ecosystem_{timestamp}.json")
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    return filepath


def print_ecosystem_report(report: dict) -> None:
    """Print the ecosystem report to the terminal."""
    sep = "═" * 70
    thin = "─" * 70

    print(f"\n{sep}")
    print(f"  AXIOM ECOSYSTEM REPORT")
    print(f"  {report['organization_count']} organizations  ·  "
          f"{report['timestamp'][:10]}")
    print(f"{sep}")

    for org in report["organizations"]:
        agg = next(
            (r["aggregate_score"] for r in [report] if False), None
        )
        # pull from source data embedded in dimension scores
        org_agg = round(
            sum(d["scores"].get(org, 0) for d in report["dimensions"]) /
            len(report["dimensions"]), 2
        )
        level = get_category(org_agg)
        print(f"  · {org:<40} {org_agg:>6.2f}  {level}")

    print(f"{thin}")
    print(f"  {'ECOSYSTEM AGGREGATE':<44} {report['ecosystem_aggregate']:>6.2f}"
          f"  {report['ecosystem_level']}")
    print(f"{sep}")

    print(f"\n  {'POS':<4} {'DIMENSION':<22} {'AVG':>6}  {'MIN':>6}  {'MAX':>6}  VAR")
    print(f"  {'---':<4} {'---------':<22} {'---':>6}  {'---':>6}  {'---':>6}  ---")
    for d in report["dimensions"]:
        spread = round(d["max"] - d["min"], 2)
        var_mark = f"{spread:+.2f}" if spread > 0 else "─"
        print(
            f"  {d['position']:<4} {d['name']:<22} {d['average']:>6.2f}  "
            f"{d['min']:>6.2f}  {d['max']:>6.2f}  {var_mark}"
        )
    print(f"{sep}")

    strengths = report["collective_strengths"]
    vulns = report["shared_vulnerabilities"]

    print(f"\n  COLLECTIVE STRENGTHS  (all orgs ≥ {STRENGTH_THRESHOLD:.0f}.0)")
    if strengths:
        for s in strengths:
            print(f"    · Position {s['position']}: {s['name']}")
    else:
        print(f"    None — variance exists across all dimensions")

    print(f"\n  SHARED VULNERABILITIES  (any org < {STRENGTH_THRESHOLD:.0f}.0)")
    if vulns:
        for v in vulns:
            for org, score in v["gaps"].items():
                print(f"    · Position {v['position']}: {v['name']}"
                      f" — {org} at {score:.2f}")
    else:
        print(f"    None — all organizations above threshold on every dimension")

    rm = report["relational_map"]
    if rm["closest"] or rm["most_divergent"]:
        print(f"\n  RELATIONAL MAP")
        if rm["closest"]:
            c = rm["closest"]
            print(f"    Closest      →  {c['orgs'][0]}  ↔  {c['orgs'][1]}"
                  f"  (distance {c['distance']:.2f})")
        if rm["most_divergent"] and rm["most_divergent"] != rm["closest"]:
            d = rm["most_divergent"]
            print(f"    Most divergent →  {d['orgs'][0]}  ↔  {d['orgs'][1]}"
                  f"  (distance {d['distance']:.2f})")
    print()


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


def run_ecosystem(files: list = None, assessments_dir: str = "assessments") -> None:
    """Load reports and produce an ecosystem reading.

    If files is empty/None, discovers all non-ecosystem assessment JSONs
    in assessments_dir. Otherwise uses the specified file paths.
    """
    if files:
        paths = files
    else:
        if not os.path.isdir(assessments_dir):
            print(f"No assessments directory found at '{assessments_dir}'.")
            print("Run an assessment first, or specify files explicitly.")
            sys.exit(1)
        paths = sorted(
            os.path.join(assessments_dir, f)
            for f in os.listdir(assessments_dir)
            if f.endswith(".json") and not f.startswith("ecosystem_")
        )
        if not paths:
            print(f"No assessment files found in '{assessments_dir}'.")
            sys.exit(1)

    reports = []
    for path in paths:
        if not os.path.exists(path):
            print(f"File not found: {path}")
            sys.exit(1)
        with open(path) as f:
            data = json.load(f)
        if data.get("type") == "ecosystem":
            print(f"Skipping ecosystem file: {path}")
            continue
        reports.append(data)

    if len(reports) < 2:
        print("Ecosystem requires at least 2 organization assessments.")
        sys.exit(1)

    report = build_ecosystem_report(reports, source_files=paths)
    print_ecosystem_report(report)
    filepath = write_ecosystem_report(report, assessments_dir)
    print(f"  Ecosystem report saved → {filepath}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AXIOM — Decinary Diagnostic Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python axiom.py\n"
            "  python axiom.py --multi\n"
            "  python axiom.py --compare assessments/OrgA.json assessments/OrgB.json\n"
            "  python axiom.py --ecosystem\n"
            "  python axiom.py --ecosystem assessments/OrgA.json assessments/OrgB.json"
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
    parser.add_argument(
        "--ecosystem",
        nargs="*",
        metavar="FILE",
        help=(
            "Ecosystem mode: no args = all files in assessments/, "
            "or specify individual JSON files"
        ),
    )
    args = parser.parse_args()

    if args.compare:
        run_comparison(args.compare[0], args.compare[1])
    elif args.ecosystem is not None:
        run_ecosystem(files=args.ecosystem if args.ecosystem else None)
    elif args.multi:
        run_multi_assessment()
    else:
        run_assessment()


if __name__ == "__main__":
    main()
