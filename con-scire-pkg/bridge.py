#!/usr/bin/env python3
"""
bridge.py — Con-Scire  (to know together)

Standalone bridge connecting three knowledge systems:
  · AXIOM              organizational health across ten Decinary positions
  · Donation Station   item lifecycle (intake → qc → storage → distributed)
  · Power Connection   numerological reading of dates (embedded)

A donation item's intake date yields a Power Connection born number.
That born number maps to a governing AXIOM dimension. The organization's
health at that dimension is the relational reading for the item.

Stage governance:
  intake      → P1 KNOWLEDGE        + P9 BORN
  qc          → P2 WISDOM           + P8 BUILD/DESTROY
  storage     → P4 CULTURED FREEDOM + P3 UNDERSTANDING
  distributed → P6 EQUALITY         + P7 CONSCIOUSNESS

Usage:
  python bridge.py                               # stage health summary
  python bridge.py --station                     # bridge all items
  python bridge.py --item DS-0001                # one item
  python bridge.py --stage distributed           # one stage
  python bridge.py --org assessments/file.json   # specific assessment
  python bridge.py --api http://localhost:5000   # live Donation Station API
  python bridge.py --data .donation_station_data.json
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime

# ── Embedded numerology (Power Connection) ────────────────────────────────────

SINGLE_MEANINGS = {
    1: "Origin", 2: "Wisdom", 3: "Creation", 4: "Foundation",
    5: "Power", 6: "Equality", 7: "Revelation", 8: "Authority", 9: "Completion",
}
MASTER_MEANINGS = {11: "Illumination", 22: "Master Builder", 33: "Master Teacher"}
MASTER_NUMBERS = {11, 22, 33}


def _reduce(n):
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def pc_born(month, day, year):
    """Return the Power Connection born number (Path One) for a date."""
    raw = month + day + year
    compound = sum(int(d) for d in str(raw)) if raw > 99 else raw
    return _reduce(compound)


def born_label(born):
    """Return the name for a born number."""
    if born is None:
        return None
    return MASTER_MEANINGS.get(born) or SINGLE_MEANINGS.get(born, str(born))


# ── Mapping tables ────────────────────────────────────────────────────────────

BORN_TO_POSITION = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
    6: 6, 7: 7, 8: 8, 9: 0,
    11: 7, 22: 4, 33: 8,
}

STAGE_TO_POSITIONS = {
    "intake":      [1, 9],
    "qc":          [2, 8],
    "storage":     [4, 3],
    "distributed": [6, 7],
}

STAGE_LABELS = {
    "intake": "INTAKE", "qc": "QUALITY CONTROL",
    "storage": "STORAGE", "distributed": "DISTRIBUTED",
}

WIDTH = 70
BAR = "─" * WIDTH
DBAR = "═" * WIDTH

# ── Data loading ──────────────────────────────────────────────────────────────


def load_assessment(path):
    with open(path) as f:
        return json.load(f)


def load_latest_assessment(org_name="Donation Station HP", assessments_dir="assessments"):
    """Load the most recent AXIOM assessment for an org from a local directory."""
    if not os.path.isdir(assessments_dir):
        return None
    safe = "".join(c if c.isalnum() else "_" for c in org_name)
    matching = sorted(
        [
            f for f in os.listdir(assessments_dir)
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


def load_items_from_api(base_url):
    """Load items from a running Donation Station HP API."""
    url = base_url.rstrip("/") + "/items"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


def load_items_from_file(path):
    """Load items from a local donation_station data JSON file."""
    with open(path) as f:
        data = json.load(f)
    return list(data.get("items", {}).values())


# ── Core bridge functions ─────────────────────────────────────────────────────


def map_born_to_position(born):
    """Map a Power Connection born number to its governing AXIOM position."""
    if born is None:
        return None
    return BORN_TO_POSITION.get(born, born % 10)


def get_dim(position, assessment):
    """Pull one dimension's data from an assessment by position number."""
    for d in assessment.get("dimensions", []):
        if d["position"] == position:
            return d
    return None


def item_born(item):
    """Derive the Power Connection born number from an item's intake timestamp."""
    history = item.get("history", [])
    intake = next((e for e in history if e.get("stage") == "intake"), None)
    if not intake:
        return None
    ts = intake.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return pc_born(dt.month, dt.day, dt.year)
    except (ValueError, KeyError):
        return None


def bridge_item(item, assessment):
    """
    Produce a bridge reading for one item:
    intake date → born number → AXIOM position → org health at that dimension.
    """
    b = item_born(item)
    gov_pos = map_born_to_position(b)
    gov_dim = get_dim(gov_pos, assessment) if gov_pos is not None else None
    stage = item.get("stage", "")
    stage_dims = [
        d for d in [get_dim(p, assessment) for p in STAGE_TO_POSITIONS.get(stage, [])]
        if d
    ]
    return {
        "item_id": item.get("id") or item.get("itemId", "?"),
        "name": item.get("name", ""),
        "stage": stage,
        "born": b,
        "born_name": born_label(b),
        "governing_position": gov_pos,
        "governing_dimension": gov_dim,
        "stage_dimensions": stage_dims,
    }


def stage_health(stage, assessment):
    """Return health scores for AXIOM dimensions governing a donation stage."""
    return [
        d for d in [get_dim(p, assessment) for p in STAGE_TO_POSITIONS.get(stage, [])]
        if d
    ]


# ── Output ────────────────────────────────────────────────────────────────────


def _signal(score):
    if score > 8:   return "OPTIMAL"
    if score > 6:   return "STABLE"
    if score > 3:   return "WATCH"
    return "CRITICAL"


def print_item_reading(reading, org_name):
    label = STAGE_LABELS.get(reading["stage"], (reading["stage"] or "").upper())
    print(f"\n{BAR}")
    print(f"  {reading['item_id']}  —  {reading['name']}")
    print(f"  Stage: {label}")
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


def print_stage_summary(assessment, org_name):
    print(f"\n{BAR}")
    print(f"  STAGE HEALTH  —  {org_name}")
    print(f"  Aggregate: {assessment.get('aggregate_score')}  [{assessment.get('aggregate_level')}]")
    print(BAR)
    for stage in ("intake", "qc", "storage", "distributed"):
        dims = stage_health(stage, assessment)
        scores = [d["average"] for d in dims]
        if scores:
            avg = round(sum(scores) / len(scores), 2)
            names = "  +  ".join(f"P{d['position']}:{d['name']}" for d in dims)
            print(f"  {STAGE_LABELS[stage]:<18}  {avg:.2f}  {_signal(avg)}  ({names})")
    print()


def print_station_bridge(items, assessment, org_name):
    print(f"\n{DBAR}")
    print(f"  CON-SCIRE  —  {org_name}")
    print(f"  {assessment.get('timestamp','')[:10]}  ·  Aggregate: {assessment.get('aggregate_score')}  [{assessment.get('aggregate_level')}]")
    print(DBAR)
    if not items:
        print(f"\n  No items found.\n")
    else:
        for item in items:
            print_item_reading(bridge_item(item, assessment), org_name)
    print(BAR)
    print(f"  STAGE HEALTH")
    print(BAR)
    for stage in ("intake", "qc", "storage", "distributed"):
        dims = stage_health(stage, assessment)
        scores = [d["average"] for d in dims]
        if scores:
            avg = round(sum(scores) / len(scores), 2)
            names = "  +  ".join(f"P{d['position']}:{d['name']}" for d in dims)
            print(f"  {STAGE_LABELS[stage]:<18}  {avg:.2f}  {_signal(avg)}  ({names})")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Con-Scire — to know together",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python bridge.py\n"
            "  python bridge.py --station\n"
            "  python bridge.py --item DS-0001\n"
            "  python bridge.py --stage distributed\n"
            "  python bridge.py --api http://localhost:5000\n"
            "  python bridge.py --org assessments/Donation_Station_HP.json"
        ),
    )
    parser.add_argument("--org", metavar="FILE", help="AXIOM assessment JSON")
    parser.add_argument("--station", action="store_true", help="Bridge all items")
    parser.add_argument("--item", metavar="ID", help="Bridge one item by ID")
    parser.add_argument(
        "--stage", metavar="STAGE",
        choices=list(STAGE_TO_POSITIONS),
        help="Show AXIOM dimensions governing a lifecycle stage",
    )
    parser.add_argument("--api", metavar="URL", help="Donation Station HP API base URL")
    parser.add_argument("--data", metavar="FILE", help="Local donation station data JSON")
    args = parser.parse_args()

    if args.org:
        assessment = load_assessment(args.org)
    else:
        assessment = load_latest_assessment()
        if not assessment:
            print("No assessment found. Pass --org <file.json> or run AXIOM first.")
            sys.exit(1)
    org_name = assessment.get("organization", "Unknown")

    items = []
    if args.api:
        try:
            items = load_items_from_api(args.api)
        except Exception as e:
            print(f"API error: {e}")
            sys.exit(1)
    elif args.data:
        items = load_items_from_file(args.data)
    else:
        default_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            ".donation_station_data.json",
        )
        if os.path.exists(default_data):
            items = load_items_from_file(default_data)

    if args.station:
        print_station_bridge(items, assessment, org_name)
    elif args.item:
        item = next(
            (i for i in items if i.get("id") == args.item or i.get("itemId") == args.item),
            None,
        )
        if not item:
            print(f"Item '{args.item}' not found.")
            sys.exit(1)
        print(f"\n{DBAR}")
        print(f"  CON-SCIRE  —  {org_name}")
        print(DBAR)
        print_item_reading(bridge_item(item, assessment), org_name)
    elif args.stage:
        dims = stage_health(args.stage, assessment)
        label = STAGE_LABELS.get(args.stage, args.stage.upper())
        print(f"\n{BAR}")
        print(f"  {label}  —  {org_name}")
        print(BAR)
        for d in dims:
            print(f"  P{d['position']}  {d['name']:<22}  {d['average']:.2f}  [{d['level']}]  {_signal(d['average'])}")
        print()
    else:
        print_stage_summary(assessment, org_name)
        if items:
            print(f"  {len(items)} item(s) found. Run --station to bridge all.\n")


if __name__ == "__main__":
    main()
