#!/usr/bin/env python3
"""
look_ahead.py — Convergence window finder

Scans forward N days to find dates matching specific cognitive/SM criteria:
  · purpose position  — SM governing number (1-9)
  · self-determination stage  — 16-day cycle
  · ✦ aligned  — convergence = 6 (Equality)
  · ◈ triple  — purpose position = stage number
  · domain in frame
  · value governing

Usage:
  python look_ahead.py                          # 30-day summary
  python look_ahead.py --purpose 7              # days governed by Consciousness
  python look_ahead.py --stage 7                # days in Stage 7 (Commonality)
  python look_ahead.py --aligned                # ✦ aligned days only
  python look_ahead.py --triple                 # purpose position = stage number
  python look_ahead.py --purpose 7 --stage 7   # both filters
  python look_ahead.py --days 90 --aligned
  python look_ahead.py --date 2027-01-01 --days 365 --triple
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

SEP  = "─" * 66
DSEP = "═" * 66


def _load_bridge():
    path = os.path.join(BASE, "data", "cf_bridge.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _stage_for_date(date):
    doy = day_of_year(date)
    return ((doy - 1) % 16) + 1


def scan(start_date, n_days=30, filters=None, lexicon=None):
    """
    Scan n_days forward from start_date. Returns list of day dicts.

    filters keys (all optional):
      purpose   int 1-9       — SM purpose position
      stage     int 1-16      — self-determination stage
      aligned   bool          — only ✦ aligned days
      triple    bool          — only days where purpose_pos == stage_num
      domain    str           — partial name match
      value     str           — partial name match
    """
    if lexicon is None:
        lexicon = Lexicon(DEFAULT_LEXICON_PATH)
    if filters is None:
        filters = {}

    bridge  = _load_bridge()
    cf_data = cf.load()
    matches = []

    for i in range(n_days):
        date = start_date + datetime.timedelta(days=i)
        dt   = datetime.datetime(date.year, date.month, date.day, 12, 0)
        sm   = compute_daily(dt, lexicon)

        purpose_pos = sm["purpose"]["number"]
        stage_num   = _stage_for_date(date)
        conv        = sm["secondary"]["convergence"]
        aligned     = conv["aligned"]

        key          = str(purpose_pos)
        domain_id    = bridge["sm_to_domain"].get(key)
        value_id     = bridge["sm_to_value"].get(key)
        domain_entry = next((e for e in cf_data["domains"] if e["id"] == domain_id), None)
        value_entry  = next((e for e in cf_data["values"]  if e["id"] == value_id),  None)
        stage_entry  = next((s for s in cf_data["stages"]["items"] if s["number"] == stage_num), None)

        # Apply filters
        if filters.get("purpose") and purpose_pos != filters["purpose"]:
            continue
        if filters.get("stage") and stage_num != filters["stage"]:
            continue
        if filters.get("aligned") and not aligned:
            continue
        if filters.get("triple") and purpose_pos != stage_num:
            continue
        if filters.get("domain") and domain_entry:
            if filters["domain"].lower() not in domain_entry["name"].lower():
                continue
        if filters.get("value") and value_entry:
            if filters["value"].lower() not in value_entry["name"].lower():
                continue

        matches.append({
            "date":            str(date),
            "purpose_pos":     purpose_pos,
            "purpose_name":    sm["purpose"]["name"],
            "stage_num":       stage_num,
            "stage_name":      stage_entry["name"]        if stage_entry else None,
            "stage_etymology": stage_entry["etymology"]   if stage_entry else None,
            "stage_root":      stage_entry["root"]        if stage_entry else None,
            "aligned":         aligned,
            "convergence":     conv["number"],
            "domain":          domain_entry["name"]       if domain_entry else None,
            "value":           value_entry["name"]        if value_entry else None,
            "moon_emoji":      sm["moon"]["emoji"],
            "moon_phase":      sm["moon"]["phase"],
        })

    return matches


# ── Display ───────────────────────────────────────────────────────────────────

def print_matches(matches, start_date, n_days, filters):
    end_date  = start_date + datetime.timedelta(days=n_days - 1)
    start_str = start_date.strftime("%b %d")
    end_str   = end_date.strftime("%b %d, %Y")

    print(f"\n{DSEP}")
    print(f"  LOOK-AHEAD  ·  {start_str} – {end_str}  ·  {n_days} days")
    print(DSEP)

    parts = []
    if filters.get("purpose"): parts.append(f"purpose={filters['purpose']}")
    if filters.get("stage"):   parts.append(f"stage={filters['stage']}")
    if filters.get("aligned"): parts.append("✦ aligned")
    if filters.get("triple"):  parts.append("◈ triple (purpose = stage)")
    if filters.get("domain"):  parts.append(f"domain~{filters['domain']}")
    if filters.get("value"):   parts.append(f"value~{filters['value']}")
    if parts:
        print(f"\n  Filters: {', '.join(parts)}")

    if not matches:
        print(f"\n  No matching days in this window.\n")
        print(DSEP + "\n")
        return

    print(f"\n  {len(matches)} match{'es' if len(matches) != 1 else ''} found\n")
    print(f"  {SEP[2:]}")

    for m in matches:
        aligned_mark = "  ✦" if m["aligned"] else ""
        triple_mark  = "  ◈" if m["purpose_pos"] == m["stage_num"] else ""
        print(f"  {m['date']}  {m['moon_emoji']}  "
              f"P{m['purpose_pos']} {m['purpose_name']:<22}"
              f"  Stage {m['stage_num']:>2} · {m['stage_name']}"
              f"{aligned_mark}{triple_mark}")
        print(f"       Domain: {m['domain'] or '—':<25}  Value: {m['value'] or '—'}")
        if m["stage_etymology"]:
            print(f"       {m['stage_etymology']} — \"{m['stage_root']}\"")
        print(f"  {SEP[2:]}")

    print()
    print(f"  ◈ = triple alignment (purpose position = stage number)")
    print(f"  ✦ = aligned (convergence = 6 · Equality)")
    print(f"\n{DSEP}\n")


def print_summary(all_days, start_date, n_days):
    end_date  = start_date + datetime.timedelta(days=n_days - 1)
    start_str = start_date.strftime("%b %d")
    end_str   = end_date.strftime("%b %d, %Y")

    print(f"\n{DSEP}")
    print(f"  LOOK-AHEAD SUMMARY  ·  {start_str} – {end_str}  ·  {n_days} days")
    print(DSEP)

    aligned_days = [m for m in all_days if m["aligned"]]
    triple_days  = [m for m in all_days if m["purpose_pos"] == m["stage_num"]]
    both_days    = [m for m in all_days if m["aligned"] and m["purpose_pos"] == m["stage_num"]]

    purpose_counts = {}
    for m in all_days:
        k = (m["purpose_pos"], m["purpose_name"])
        purpose_counts[k] = purpose_counts.get(k, 0) + 1

    print(f"\n  ✦ Aligned days  ({len(aligned_days)} total)")
    for m in aligned_days:
        triple_mark = "  ◈" if m["purpose_pos"] == m["stage_num"] else ""
        print(f"    {m['date']}  {m['moon_emoji']}  "
              f"P{m['purpose_pos']} {m['purpose_name']:<22}"
              f"  Stage {m['stage_num']:>2} {m['stage_name']}{triple_mark}")

    print(f"\n  ◈ Triple alignments  ({len(triple_days)} total  ·  purpose = stage)")
    for m in triple_days:
        aligned_mark = "  ✦" if m["aligned"] else ""
        print(f"    {m['date']}  {m['moon_emoji']}  "
              f"P{m['purpose_pos']} {m['purpose_name']:<22}"
              f"  Stage {m['stage_num']:>2} {m['stage_name']}{aligned_mark}")

    if both_days:
        print(f"\n  ✦◈ Both (aligned + triple)  ({len(both_days)} total)")
        for m in both_days:
            print(f"    {m['date']}  P{m['purpose_pos']} {m['purpose_name']}  Stage {m['stage_num']} {m['stage_name']}")

    print(f"\n  Purpose distribution")
    for (pos, name), count in sorted(purpose_counts.items()):
        bar = "█" * count
        print(f"    P{pos} {name:<22}  {count:>2}  {bar}")

    print(f"\n{DSEP}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Look-Ahead — Convergence window finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python look_ahead.py\n"
            "  python look_ahead.py --purpose 7\n"
            "  python look_ahead.py --stage 7\n"
            "  python look_ahead.py --aligned\n"
            "  python look_ahead.py --triple\n"
            "  python look_ahead.py --purpose 7 --stage 7\n"
            "  python look_ahead.py --days 90 --aligned\n"
            "  python look_ahead.py --date 2027-01-01 --days 365 --triple"
        ),
    )
    parser.add_argument("--date",    metavar="YYYY-MM-DD", help="Start date (default: today)")
    parser.add_argument("--days",    type=int, default=30, metavar="N",    help="Days to scan (default: 30)")
    parser.add_argument("--purpose", type=int, metavar="1-9",              help="Filter by SM purpose position")
    parser.add_argument("--stage",   type=int, metavar="1-16",             help="Filter by self-determination stage")
    parser.add_argument("--aligned", action="store_true",                  help="Show only ✦ aligned days")
    parser.add_argument("--triple",  action="store_true",                  help="Show only ◈ triple alignments")
    parser.add_argument("--domain",  metavar="NAME",                       help="Filter by domain name (partial match)")
    parser.add_argument("--value",   metavar="NAME",                       help="Filter by value name (partial match)")
    parser.add_argument("--json",    action="store_true",                  help="Output raw JSON")
    args = parser.parse_args()

    if args.date:
        try:
            start_date = datetime.date.fromisoformat(args.date)
        except ValueError:
            print(f"Invalid date {args.date!r}. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        start_date = datetime.date.today()

    if args.purpose and not (1 <= args.purpose <= 9):
        print("`--purpose` must be 1-9.")
        sys.exit(1)
    if args.stage and not (1 <= args.stage <= 16):
        print("`--stage` must be 1-16.")
        sys.exit(1)

    filters = {
        "purpose": args.purpose,
        "stage":   args.stage,
        "aligned": args.aligned,
        "triple":  args.triple,
        "domain":  args.domain,
        "value":   args.value,
    }

    lexicon     = Lexicon(DEFAULT_LEXICON_PATH)
    has_filters = any([args.purpose, args.stage, args.aligned, args.triple, args.domain, args.value])

    if has_filters:
        matches = scan(start_date, args.days, filters, lexicon)
        if args.json:
            import json as _json
            print(_json.dumps(matches, indent=2))
        else:
            print_matches(matches, start_date, args.days, filters)
    else:
        all_days = scan(start_date, args.days, {}, lexicon)
        if args.json:
            import json as _json
            print(_json.dumps(all_days, indent=2))
        else:
            print_summary(all_days, start_date, args.days)


if __name__ == "__main__":
    main()
