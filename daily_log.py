#!/usr/bin/env python3
"""
daily_log.py — Daily reading log

Records each unified daily reading as a durable entry. Accumulates
patterns over time: recurring purpose positions, stage distribution,
aligned days (✦ convergence = 6), AXIOM health trends.

Usage:
  python daily_log.py --show              # last 14 entries
  python daily_log.py --show --all        # full history
  python daily_log.py --reflect "text"    # add reflection to today's entry
  python daily_log.py --patterns          # show recurring patterns
  python daily_log.py --aligned           # show all ✦ aligned days
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import date as date_type

DEFAULT_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           ".daily_log.json")

SEP  = "─" * 66
DSEP = "═" * 66


# ── I/O ───────────────────────────────────────────────────────────────────────

def load_log(path=None):
    p = path or DEFAULT_LOG
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_log(entries, path=None):
    p = path or DEFAULT_LOG
    with open(p, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


# ── Entry construction ────────────────────────────────────────────────────────

def entry_from_reading(reading, reflection=None):
    """Build a log entry dict from a compute_unified() result."""
    sm    = reading["sm"]
    stage = reading["stage"]
    dom   = reading["domain"]
    val   = reading["value"]
    axiom = reading["axiom"]
    sec   = sm["secondary"]
    conv  = sec["convergence"]

    return {
        "date":          sm["date"],
        "time":          sm["time"],
        "attention_pos": sm["attention"]["number"],
        "attention":     sm["attention"]["name"],
        "intention_pos": sm["intention"]["number"],
        "intention":     sm["intention"]["name"],
        "purpose_pos":   sm["purpose"]["number"],
        "purpose":       sm["purpose"]["name"],
        "aligned":       conv["aligned"],
        "convergence":   conv["number"],
        "address":       sm["methods"]["a"],
        "stage_num":     stage["number"] if stage else None,
        "stage_name":    stage["name"]   if stage else None,
        "domain":        dom["name"]     if dom   else None,
        "value":         val["name"]     if val   else None,
        "moon_phase":    sm["moon"]["phase"],
        "moon_emoji":    sm["moon"]["emoji"],
        "axiom_dim":     axiom["dimension"]["name"]    if axiom else None,
        "axiom_score":   axiom["dimension"]["average"] if axiom else None,
        "axiom_level":   axiom["dimension"]["level"]   if axiom else None,
        "reflection":    reflection,
    }


def append_entry(reading, reflection=None, path=None):
    """
    Append (or update today's existing) entry to the log.
    Returns the entry written and whether it was new (True) or updated (False).
    """
    entries = load_log(path)
    new_entry = entry_from_reading(reading, reflection)
    today = new_entry["date"]

    for i, e in enumerate(entries):
        if e["date"] == today:
            # Update existing entry; preserve prior reflection if none given
            if reflection is None and e.get("reflection"):
                new_entry["reflection"] = e["reflection"]
            entries[i] = new_entry
            save_log(entries, path)
            return new_entry, False

    entries.append(new_entry)
    save_log(entries, path)
    return new_entry, True


def add_reflection(text, date_str=None, path=None):
    """Add or replace the reflection on an existing entry (default: today)."""
    entries = load_log(path)
    target = date_str or str(date_type.today())
    for e in entries:
        if e["date"] == target:
            e["reflection"] = text
            save_log(entries, path)
            return e
    return None


# ── Display ───────────────────────────────────────────────────────────────────

def _fmt_entry(e, verbose=False):
    aligned = "  ✦" if e.get("aligned") else ""
    stage_str = (f"Stage {e['stage_num']:>2}/{16}  {e['stage_name']}"
                 if e.get("stage_num") else "")
    axiom_str = (f"  ·  P{e['axiom_dim'].split()[0] if e.get('axiom_dim') else ''}"
                 f":{e.get('axiom_score', ''):.1f} {e.get('axiom_level', '')}"
                 if e.get("axiom_score") is not None else "")

    lines = []
    lines.append(
        f"  {e['date']}  {e['moon_emoji']}  "
        f"{e['purpose_pos']} — {e['purpose']:<22}{aligned}"
    )
    if verbose:
        lines.append(
            f"    {e['attention_pos']}·{e['intention_pos']}·{e['purpose_pos']}"
            f"  addr {e['address']}"
            f"  conv {e['convergence']}"
        )
        lines.append(f"    {stage_str}  ·  {e.get('domain', '')}  ·  {e.get('value', '')}{axiom_str}")
    if e.get("reflection"):
        lines.append(f"    ↳ {e['reflection']}")
    return "\n".join(lines)


def print_log(entries, n=14, verbose=False):
    shown = entries[-n:] if n else entries
    if not shown:
        print("\n  No entries yet. Run: python unified_daily.py --log\n")
        return
    print(f"\n{DSEP}")
    print(f"  DAILY LOG  ·  {len(entries)} total  ·  showing {len(shown)}")
    print(DSEP)
    for e in reversed(shown):
        print(_fmt_entry(e, verbose=verbose))
        print(f"  {SEP[2:]}")
    print()


def print_patterns(entries):
    if not entries:
        print("\n  No entries to analyze.\n")
        return

    purpose_counts  = Counter(f"{e['purpose_pos']} — {e['purpose']}" for e in entries)
    stage_counts    = Counter(f"{e['stage_num']:>2}. {e['stage_name']}" for e in entries if e.get("stage_num"))
    value_counts    = Counter(e["value"] for e in entries if e.get("value"))
    domain_counts   = Counter(e["domain"] for e in entries if e.get("domain"))
    aligned_days    = [e["date"] for e in entries if e.get("aligned")]
    moon_counts     = Counter(e["moon_phase"] for e in entries)

    print(f"\n{DSEP}")
    print(f"  PATTERNS  ·  {len(entries)} entries")
    print(DSEP)

    print(f"\n  Purpose Positions")
    for label, count in purpose_counts.most_common():
        bar = "█" * count
        print(f"    {label:<30}  {count:>3}  {bar}")

    print(f"\n  Self-Determination Stages")
    for label, count in stage_counts.most_common(5):
        bar = "█" * count
        print(f"    {label:<30}  {count:>3}  {bar}")

    print(f"\n  Values Governing")
    for label, count in value_counts.most_common():
        print(f"    {label:<30}  {count:>3}")

    print(f"\n  Domains in Frame")
    for label, count in domain_counts.most_common():
        print(f"    {label:<30}  {count:>3}")

    print(f"\n  ✦ Aligned Days  ({len(aligned_days)} total)")
    for d in aligned_days[-10:]:
        print(f"    {d}")

    print(f"\n  Moon Phases")
    for ph, count in moon_counts.most_common():
        print(f"    {ph:<22}  {count:>3}")

    print()


def print_aligned(entries):
    aligned = [e for e in entries if e.get("aligned")]
    print(f"\n{SEP}")
    print(f"  ✦ ALIGNED DAYS  (convergence = 6 · Equality)  ·  {len(aligned)} total")
    print(SEP)
    if not aligned:
        print("  None recorded yet.")
    for e in aligned:
        print(_fmt_entry(e, verbose=True))
        print(f"  {SEP[2:]}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Daily log — view history and patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python daily_log.py --show\n"
            "  python daily_log.py --show --all\n"
            "  python daily_log.py --reflect \"Cultured Freedom day — tilled the backlog\"\n"
            "  python daily_log.py --patterns\n"
            "  python daily_log.py --aligned"
        ),
    )
    parser.add_argument("--show",    action="store_true", help="Show recent entries (default: last 14)")
    parser.add_argument("--all",     action="store_true", help="Show all entries with --show")
    parser.add_argument("--verbose", action="store_true", help="Show full detail per entry")
    parser.add_argument("--reflect", metavar="TEXT",      help="Add reflection to today's entry")
    parser.add_argument("--date",    metavar="YYYY-MM-DD",help="Target date for --reflect (default: today)")
    parser.add_argument("--patterns",action="store_true", help="Show recurring patterns across all entries")
    parser.add_argument("--aligned", action="store_true", help="Show all ✦ aligned days")
    parser.add_argument("--log",     metavar="FILE",      help=f"Path to log file (default: {DEFAULT_LOG})")
    args = parser.parse_args()

    log_path = args.log or DEFAULT_LOG
    entries  = load_log(log_path)

    if args.reflect:
        entry = add_reflection(args.reflect, date_str=args.date, path=log_path)
        if entry:
            print(f"\n  Reflection saved for {entry['date']}:")
            print(f"  ↳ {entry['reflection']}\n")
        else:
            target = args.date or str(date_type.today())
            print(f"\n  No entry found for {target}. Run the unified reading first:\n"
                  f"  python unified_daily.py --log\n")
            sys.exit(1)
    elif args.patterns:
        print_patterns(entries)
    elif args.aligned:
        print_aligned(entries)
    elif args.show or not any([args.reflect, args.patterns, args.aligned]):
        n = 0 if args.all else 14
        print_log(entries, n=n, verbose=args.verbose)
    else:
        print_log(entries, verbose=args.verbose)


if __name__ == "__main__":
    main()
