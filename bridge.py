#!/usr/bin/env python3
"""
bridge.py — Con-Scire Bridge

Connects three knowledge systems:
  · AXIOM              organizational health across ten Decinary positions
  · Donation Station   item lifecycle (intake → qc → storage → distributed)
  · Power Connection   numerological reading of dates

A donation item's intake date yields a Power Connection born number.
That born number maps to a governing AXIOM dimension. The org's health
at that dimension is the relational reading for the item.

Each donation stage is governed by specific AXIOM positions:
  intake      → KNOWLEDGE (1)  + BORN (9)
  qc          → WISDOM (2)     + BUILD/DESTROY (8)
  storage     → CULTURED FREEDOM (4) + UNDERSTANDING (3)
  distributed → EQUALITY (6)   + CONSCIOUSNESS (7)

Usage:
  python bridge.py                          # stage health summary
  python bridge.py --station                # bridge all items
  python bridge.py --item DS-0001           # bridge one item
  python bridge.py --stage qc              # dimensions governing a stage
  python bridge.py --org <file.json>       # use a specific assessment
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from power_connection import (
    calculate as pc_calculate,
    SINGLE_MEANINGS,
    COMPOUND_MEANINGS,
)
from donation_station import _load as ds_load, STAGE_LABELS
from axiom import DIMENSIONS, get_category

# ── Mapping tables ────────────────────────────────────────────────────────────

# Power Connection born number → AXIOM position
BORN_TO_POSITION = {
    1:  1,   # Origin       → KNOWLEDGE
    2:  2,   # Wisdom       → WISDOM
    3:  3,   # Creation     → UNDERSTANDING
    4:  4,   # Foundation   → CULTURED FREEDOM
    5:  5,   # Power        → POWER REFINEMENT
    6:  6,   # Equality     → EQUALITY
    7:  7,   # Revelation   → CONSCIOUSNESS
    8:  8,   # Authority    → BUILD/DESTROY
    9:  0,   # Completion   → CIPHER/COMPLETION
    11: 7,   # Illumination → CONSCIOUSNESS (master)
    22: 4,   # Master Builder → CULTURED FREEDOM (master)
    33: 8,   # Master Teacher → BUILD/DESTROY (master)
}

# Donation stage → governing AXIOM positions
STAGE_TO_POSITIONS = {
    "intake":      [1, 9],   # who/what enters + new emergence
    "qc":          [2, 8],   # practical wisdom applied + discern what to keep or release
    "storage":     [4, 3],   # responsible stewardship + depth of care
    "distributed": [6, 7],   # equitable distribution + recipient awakening to agency
}

WIDTH = 70
BAR = "─" * WIDTH
DBAR = "═" * WIDTH

# ── Core bridge functions ─────────────────────────────────────────────────────


def map_born_to_position(born: int) -> int:
    """Map a Power Connection born number to its governing AXIOM position."""
    return BORN_TO_POSITION.get(born, born % 10)


def map_stage_to_positions(stage: str) -> list:
    """Return AXIOM positions governing a donation lifecycle stage."""
    return STAGE_TO_POSITIONS.get(stage, [])


def get_dimension_score(position: int, assessment: dict) -> dict | None:
    """Pull one dimension's data from an assessment by position number."""
    for dim in assessment.get("dimensions", []):
        if dim["position"] == position:
            return dim
    return None


def item_born_number(item: dict) -> int | None:
    """Derive the Power Connection born number from an item's intake timestamp."""
    history = item.get("history", [])
    intake_event = next((e for e in history if e.get("stage") == "intake"), None)
    if not intake_event:
        return None
    ts = intake_event.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        result = pc_calculate(dt.month, dt.day, dt.year)
        return result["born"]
    except (ValueError, KeyError):
        return None


def born_name(born: int | None) -> str | None:
    """Return the name for a born number from either single or compound meanings."""
    if born is None:
        return None
    entry = SINGLE_MEANINGS.get(born) or COMPOUND_MEANINGS.get(born)
    return entry[0] if entry else str(born)


def bridge_item(item: dict, assessment: dict) -> dict:
    """
    Produce a bridge reading for one item:
    intake date → born number → AXIOM position → org health at that dimension.
    """
    b = item_born_number(item)
    governing_position = map_born_to_position(b) if b is not None else None
    governing_dim = (
        get_dimension_score(governing_position, assessment)
        if governing_position is not None
        else None
    )
    stage_positions = map_stage_to_positions(item.get("stage", ""))
    stage_dims = [d for d in [get_dimension_score(p, assessment) for p in stage_positions] if d]

    return {
        "item_id": item["id"],
        "name": item["name"],
        "stage": item.get("stage"),
        "born": b,
        "born_name": born_name(b),
        "governing_position": governing_position,
        "governing_dimension": governing_dim,
        "stage_dimensions": stage_dims,
    }


def stage_health(stage: str, assessment: dict) -> list:
    """Return health scores for AXIOM dimensions governing a donation stage."""
    positions = map_stage_to_positions(stage)
    return [d for d in [get_dimension_score(p, assessment) for p in positions] if d]


def load_latest_assessment(
    org_name: str, assessments_dir: str = "assessments"
) -> dict | None:
    """Load the most recent AXIOM assessment for an org by name."""
    if not os.path.isdir(assessments_dir):
        return None
    safe = "".join(c if c.isalnum() else "_" for c in org_name)
    matching = sorted(
        [
            f
            for f in os.listdir(assessments_dir)
            if f.startswith(safe)
            and f.endswith(".json")
            and not f.startswith("ecosystem_")
        ],
        reverse=True,
    )
    if not matching:
        return None
    with open(os.path.join(assessments_dir, matching[0])) as f:
        return json.load(f)


def load_assessment_file(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ── Output ────────────────────────────────────────────────────────────────────


def _signal(score: float) -> str:
    cat = get_category(score)
    return {
        "Absent": "CRITICAL",
        "Emerging": "WATCH",
        "Established": "STABLE",
        "Mature": "OPTIMAL",
    }[cat]


def print_item_reading(reading: dict, org_name: str) -> None:
    stage_label = STAGE_LABELS.get(reading["stage"], (reading["stage"] or "").upper())
    print(f"\n{BAR}")
    print(f"  {reading['item_id']}  —  {reading['name']}")
    print(f"  Stage: {stage_label}")
    print(BAR)

    if reading["born"] is not None:
        print(f"\n  Power Reading  →  Born {reading['born']}  [{reading['born_name']}]")
        gd = reading["governing_dimension"]
        if gd:
            sig = _signal(gd["average"])
            print(f"  Governing  →  Position {gd['position']}: {gd['name']}")
            print(f"  {org_name}: {gd['average']:.2f}  [{gd['level']}]  {sig}")
    else:
        print(f"\n  Power Reading  →  unavailable (no intake timestamp)")

    if reading["stage_dimensions"]:
        print(f"\n  Stage Dimensions  ({reading['stage']})")
        for d in reading["stage_dimensions"]:
            sig = _signal(d["average"])
            print(f"    P{d['position']}  {d['name']:<22}  {d['average']:.2f}  [{d['level']}]  {sig}")
    print()


def print_stage_query(stage: str, assessment: dict, org_name: str) -> None:
    label = STAGE_LABELS.get(stage, stage.upper())
    print(f"\n{BAR}")
    print(f"  {label}  —  Governing Dimensions  ({org_name})")
    print(BAR)
    dims = stage_health(stage, assessment)
    for d in dims:
        sig = _signal(d["average"])
        print(f"  P{d['position']}  {d['name']:<22}  {d['average']:.2f}  [{d['level']}]  {sig}")
    print()


def print_stage_summary(assessment: dict, org_name: str) -> None:
    print(f"\n{BAR}")
    print(f"  STAGE HEALTH  —  {org_name}")
    print(f"  Aggregate: {assessment.get('aggregate_score')}  [{assessment.get('aggregate_level')}]")
    print(BAR)
    for stage in ("intake", "qc", "storage", "distributed"):
        dims = stage_health(stage, assessment)
        label = STAGE_LABELS.get(stage, stage.upper())
        scores = [d["average"] for d in dims]
        if scores:
            avg = round(sum(scores) / len(scores), 2)
            sig = _signal(avg)
            names = "  +  ".join(f"P{d['position']}:{d['name']}" for d in dims)
            print(f"  {label:<18}  {avg:.2f}  {sig}  ({names})")
    print()


def print_station_bridge(items: list, assessment: dict, org_name: str) -> None:
    org_agg = assessment.get("aggregate_score", 0)
    org_level = assessment.get("aggregate_level", "")
    assessed = assessment.get("timestamp", "")[:10]

    print(f"\n{DBAR}")
    print(f"  CON-SCIRE BRIDGE  —  {org_name}")
    print(f"  Assessment: {assessed}  |  Aggregate: {org_agg}  [{org_level}]")
    print(f"{DBAR}")

    if not items:
        print(f"\n  No items in Donation Station.\n")
    else:
        for item in items:
            reading = bridge_item(item, assessment)
            print_item_reading(reading, org_name)

    print(f"{BAR}")
    print(f"  STAGE HEALTH SUMMARY")
    print(BAR)
    for stage in ("intake", "qc", "storage", "distributed"):
        dims = stage_health(stage, assessment)
        label = STAGE_LABELS.get(stage, stage.upper())
        scores = [d["average"] for d in dims]
        if scores:
            avg = round(sum(scores) / len(scores), 2)
            sig = _signal(avg)
            names = "  +  ".join(f"P{d['position']}:{d['name']}" for d in dims)
            print(f"  {label:<18}  {avg:.2f}  {sig}  ({names})")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Con-Scire Bridge — AXIOM × Donation Station × Power Connection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python bridge.py\n"
            "  python bridge.py --station\n"
            "  python bridge.py --item DS-0001\n"
            "  python bridge.py --stage distributed\n"
            "  python bridge.py --org assessments/Donation_Station_HP_20260811_224113.json"
        ),
    )
    parser.add_argument(
        "--org",
        metavar="FILE",
        help="Path to AXIOM assessment JSON (default: latest Donation Station HP)",
    )
    parser.add_argument(
        "--station",
        action="store_true",
        help="Bridge all items in Donation Station to org health",
    )
    parser.add_argument(
        "--item",
        metavar="ITEM_ID",
        help="Bridge a single item by ID",
    )
    parser.add_argument(
        "--stage",
        metavar="STAGE",
        choices=["intake", "qc", "storage", "distributed"],
        help="Show AXIOM dimensions governing a lifecycle stage",
    )
    args = parser.parse_args()

    if args.org:
        assessment = load_assessment_file(args.org)
    else:
        assessment = load_latest_assessment("Donation Station HP")
        if not assessment:
            print("No Donation Station HP assessment found. Run: python axiom.py")
            sys.exit(1)

    org_name = assessment.get("organization", "Unknown")
    db = ds_load()
    items = list(db["items"].values())

    if args.station:
        print_station_bridge(items, assessment, org_name)
    elif args.item:
        item = db["items"].get(args.item)
        if not item:
            print(f"Item '{args.item}' not found.")
            sys.exit(1)
        reading = bridge_item(item, assessment)
        print(f"\n{DBAR}")
        print(f"  CON-SCIRE BRIDGE  —  {org_name}")
        print(f"{DBAR}")
        print_item_reading(reading, org_name)
    elif args.stage:
        print_stage_query(args.stage, assessment, org_name)
    else:
        print_stage_summary(assessment, org_name)
        if items:
            print(f"  {len(items)} item(s) in Donation Station.")
            print(f"  Run --station to bridge all items, or --item <ID> for one.\n")


if __name__ == "__main__":
    main()
