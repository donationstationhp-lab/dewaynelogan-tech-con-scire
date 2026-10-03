#!/usr/bin/env python3
"""
unified_daily.py — Unified daily reading

Bridges the Supreme Mathematics daily reading with:
  · Cognitive process functions activated by today's purpose position
  · Mathematical/logical domain in frame
  · Core value governing the day
  · Self-determination stage (16-day cycle through the year)
  · AXIOM organizational health at the governing dimension (if assessment available)

Usage:
  python unified_daily.py
  python unified_daily.py --date 2026-10-07
  python unified_daily.py --hour 9
  python unified_daily.py --json
  python unified_daily.py --org assessments/Donation_Station_HP_20260916_113000.json
"""

import argparse
import datetime
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

from suprememath import Lexicon, compute_daily, DEFAULT_LEXICON_PATH
from suprememath.digits import day_of_year
import cognitive_functions as cf
import axiom as ax
import bridge as br
import daily_log as dl


def _load_bridge():
    path = os.path.join(BASE, "data", "cf_bridge.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_cf():
    return cf.load()


def _load_assessment(path=None):
    if path:
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)
    return br.load_latest_assessment("Donation Station HP")


def _stage_for_date(date):
    doy = day_of_year(date)
    return ((doy - 1) % 16) + 1


def compute_unified(dt, lexicon=None, assessment_path=None):
    """
    Compute the full unified daily reading for *dt*.

    Returns a dict with all frames:
      sm          — Supreme Mathematics reading
      process     — activated cognitive process functions (from purpose position)
      domain      — mathematical/logical domain in frame
      value       — core value governing the day
      stage       — self-determination stage (16-day cycle)
      axiom       — AXIOM dimension health (None if no assessment available)
    """
    if lexicon is None:
        lexicon = Lexicon(DEFAULT_LEXICON_PATH)

    sm = compute_daily(dt, lexicon)
    bridge = _load_bridge()
    cf_data = _load_cf()

    purpose_pos = sm["purpose"]["number"]
    key = str(purpose_pos)

    # Process functions
    process_ids = bridge["sm_to_process"].get(key, [])
    process_entries = [
        e for e in cf_data["process"] if e["id"] in process_ids
    ]
    # preserve order from bridge
    process_entries = sorted(process_entries, key=lambda e: process_ids.index(e["id"]))

    # Domain
    domain_id = bridge["sm_to_domain"].get(key)
    domain_entry = next((e for e in cf_data["domains"] if e["id"] == domain_id), None)

    # Value
    value_id = bridge["sm_to_value"].get(key)
    value_entry = next((e for e in cf_data["values"] if e["id"] == value_id), None)

    # Self-determination stage
    date = dt.date() if isinstance(dt, datetime.datetime) else dt
    stage_num = _stage_for_date(date)
    stage_entry = next((s for s in cf_data["stages"]["items"] if s["number"] == stage_num), None)

    # AXIOM health
    axiom_reading = None
    assessment = _load_assessment(assessment_path)
    if assessment:
        dim = br.get_dimension_score(purpose_pos, assessment)
        if dim:
            axiom_reading = {
                "organization": assessment.get("organization", ""),
                "aggregate_score": assessment.get("aggregate_score"),
                "aggregate_level": assessment.get("aggregate_level"),
                "dimension": dim,
                "signal": br._signal(dim["average"]),
            }

    return {
        "sm":      sm,
        "process": process_entries,
        "domain":  domain_entry,
        "value":   value_entry,
        "stage":   stage_entry,
        "axiom":   axiom_reading,
    }


# ── Terminal output ───────────────────────────────────────────────────────────

SEP  = "─" * 66
DSEP = "═" * 66


def print_unified(reading):
    sm      = reading["sm"]
    process = reading["process"]
    domain  = reading["domain"]
    value   = reading["value"]
    stage   = reading["stage"]
    axiom   = reading["axiom"]

    date_str = sm["date"]
    time_str = sm["time"]
    moon     = sm["moon"]

    print(f"\n{DSEP}")
    print(f"  UNIFIED DAILY READING  ·  {date_str}  {time_str}")
    print(DSEP)

    # ── SM Primary ───────────────────────────────────────────────────────────
    print(f"\n  {'FRACTION CALENDAR'}")
    print(f"  {SEP[2:]}")

    att = sm["attention"]
    itn = sm["intention"]
    pur = sm["purpose"]

    print(f"  {att['liturgy']}")
    cmp = f"  [compound: {itn['raw']} → {itn['number']}]" if itn.get("compound") else ""
    print(f"    {att['number']} — {att['name']}")
    print()
    print(f"  {itn['liturgy']}{cmp}")
    print(f"    {itn['number']} — {itn['name']}")
    print()
    pur_cmp = f"  [compound: {pur['raw']} → {pur['number']}]" if pur.get("compound") else ""
    print(f"  {pur['liturgy']}{pur_cmp}")
    print(f"    {pur['number']} — {pur['name']}  ←  governing position")

    # ── SM Secondary ─────────────────────────────────────────────────────────
    sec  = sm["secondary"]
    conv = sec["convergence"]
    aligned = "  ✦ aligned" if conv["aligned"] else ""
    print(f"\n  SECONDARY LENS  (Method B + 12-hr clock)")
    print(f"  {SEP[2:]}")
    print(f"  Date cipher (B): {sec['attention']['number']} — {sec['attention']['name']}")
    print(f"  Convergence:     {conv['number']} — {conv['name']}{aligned}")
    print(f"  Address:         {sm['methods']['a']}")

    # ── Year Arc + Moon ───────────────────────────────────────────────────────
    ya = sm["year_arc"]
    print(f"\n  Year Arc {ya['year']}:  {ya['number']} — {ya['name']}")
    print(f"  Moon:            {moon['emoji']} {moon['phase']}  ({moon['illumination_pct']:.1f}% illuminated)")

    # ── Cognitive Bridge ─────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print(f"  COGNITIVE BRIDGE  (Purpose {pur['number']} — {pur['name']})")
    print(SEP)

    print(f"\n  Process Functions Activated")
    for p in process:
        print(f"    · {p['name']}")

    if domain:
        print(f"\n  Domain in Frame    →  {domain['name']}")

    if value:
        note = f"  ({value['note']})" if value.get("note") else ""
        print(f"  Value Governing    →  {value['name']}{note}")

    if stage:
        print(f"\n  Self-Determination Stage  {stage['number']}/16")
        print(f"    {stage['name']}  ·  {stage['etymology']} — \"{stage['root']}\"")
        print(f"    {stage['description']}")

    # ── AXIOM ─────────────────────────────────────────────────────────────────
    if axiom:
        dim = axiom["dimension"]
        sig = axiom["signal"] or ""
        print(f"\n{SEP}")
        print(f"  AXIOM  ·  {axiom['organization']}")
        print(SEP)
        print(f"  Governing P{dim['position']}: {dim['name']}")
        print(f"  Score: {dim['average']:.2f}  [{dim['level']}]  {sig}")
        print(f"  Theme: {next((d['theme'] for d in ax.DIMENSIONS if d['position'] == dim['position']), '')}")
        print(f"  Aggregate: {axiom['aggregate_score']}  [{axiom['aggregate_level']}]")
    else:
        print(f"\n  AXIOM  ·  no assessment loaded  (pass --org <file.json> to include)")

    print(f"\n{DSEP}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Unified Daily Reading — SM + Cognitive Functions + AXIOM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python unified_daily.py\n"
            "  python unified_daily.py --date 2026-10-07\n"
            "  python unified_daily.py --hour 9\n"
            "  python unified_daily.py --org assessments/Donation_Station_HP_20260916_113000.json\n"
            "  python unified_daily.py --json"
        ),
    )
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="Date to read (default: today)")
    parser.add_argument("--hour", type=int, metavar="0-23", help="Hour 0-23 (default: now)")
    parser.add_argument("--org",  metavar="FILE", help="AXIOM assessment JSON file")
    parser.add_argument("--json",    action="store_true", help="Output raw JSON")
    parser.add_argument("--log",     action="store_true", help="Append this reading to the daily log")
    parser.add_argument("--reflect", metavar="TEXT",      help="Add a one-line reflection (implies --log)")
    args = parser.parse_args()

    now = datetime.datetime.now()

    if args.date:
        try:
            d = datetime.date.fromisoformat(args.date)
        except ValueError:
            print(f"Invalid date {args.date!r}. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        d = now.date()

    hour = args.hour if args.hour is not None else now.hour
    if not (0 <= hour <= 23):
        print("`--hour` must be 0-23.")
        sys.exit(1)

    dt = datetime.datetime(d.year, d.month, d.day, hour, now.minute)

    reading = compute_unified(dt, assessment_path=args.org)

    if args.json:
        print(json.dumps(reading, indent=2, default=str))
    else:
        print_unified(reading)

    if args.log or args.reflect:
        entry, is_new = dl.append_entry(reading, reflection=args.reflect)
        status = "logged" if is_new else "updated"
        aligned = "  ✦ aligned" if entry["aligned"] else ""
        print(f"  → {status} {entry['date']}  ·  "
              f"Purpose {entry['purpose_pos']} — {entry['purpose']}"
              f"  ·  Stage {entry['stage_num']}{aligned}\n")


if __name__ == "__main__":
    main()
