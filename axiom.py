#!/usr/bin/env python3
"""
AXIOM — Decinary Diagnostic Tool

Assesses an organization or community across ten dimensions of the
Decinary Operating System (positions 0–9). Each dimension is scored
via three sub-questions on a 1–10 scale. Scores aggregate to a
categorical level and a single composite reading.

Usage:
    python axiom.py
"""

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


def make_safe_name(org_name: str) -> str:
    """Return a filesystem-safe version of an organization name."""
    return "".join(c if c.isalnum() else "_" for c in org_name)


def build_report(org_name: str, results: list) -> dict:
    """Assemble the full assessment report dictionary."""
    position_averages = [r["average"] for r in results]
    aggregate = calculate_aggregate(position_averages)
    gap = find_top_gap(results)
    return {
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
    }


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
    gap = report["top_gap"]
    print(
        f"\n  TOP GAP  →  Position {gap['position']}: {gap['name']}"
    )
    print(
        f"             Score {gap['score']:.2f} — {gap['level']}"
    )
    print(f"\n  Action: Prioritize investment in {gap['name']} before")
    print(f"          scaling other dimensions.\n")

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


def run_assessment(assessments_dir: str = "assessments") -> None:
    """Interactive CLI assessment loop."""
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

    print(f"\n  Assessing: {org_name}")
    print(f"  You will answer 3 questions per dimension (30 total).")
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

    report = build_report(org_name, results)

    # Terminal output
    print_report(report)

    # File output
    filepath = write_report(report, assessments_dir)
    print(f"  Report saved → {filepath}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_assessment()
