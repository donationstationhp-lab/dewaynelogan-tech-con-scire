#!/usr/bin/env python3
"""sm_daily.py — Supreme Mathematics daily reading

Usage:
  python sm_daily.py                         # now
  python sm_daily.py --date 2026-05-29       # that date, current hour
  python sm_daily.py --hour 14               # today at 14:00
  python sm_daily.py --date 2026-05-29 --hour 9
  python sm_daily.py --notion                # push to Notion
  python sm_daily.py --json                  # raw JSON output

Reading frame:
  Attention = Method B (date cipher)       — Calculate  "of"
  Intention = reduce(12-hour clock)        — Decode     "by"
  Purpose   = reduce(Attention+Intention)  — Translate  "through"
  Convergence = reduce(A+I+P)

Methods:
  A  Y·M·W·D  address (year · month · week-of-year · day-of-month)
  B  reduce(sum of YYYYMMDD digits)  — primary cipher / Attention
  C  reduce(month + day + year as integers)

Environment variables (for --notion):
  NOTION_TOKEN       Notion integration token  (required)
  NOTION_PARENT_ID   Parent page ID (defaults to Daily Mathematics Journal)
"""

import argparse
import datetime
import json
import sys
import textwrap

try:
    from suprememath import Lexicon, compute_daily, DEFAULT_LEXICON_PATH
    from suprememath.digits import reduce
except ImportError as exc:
    sys.exit(f"Import error: {exc}\nRun from the project root directory.")

WIDTH = 72
BAR   = "─" * WIDTH
HALF  = "─" * (WIDTH // 2)


def _wrap(text: str, indent: int = 4) -> str:
    return textwrap.fill(
        text, width=WIDTH,
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
    )


def print_reading(reading: dict, lex: Lexicon) -> None:
    dt      = datetime.date.fromisoformat(reading["date"])
    weekday = dt.strftime("%A")
    title   = dt.strftime("%B %-d, %Y")
    time    = reading.get("time", "")

    att  = reading["attention"]
    itn  = reading["intention"]
    pur  = reading["purpose"]
    conv = reading["convergence"]
    yr   = reading["year_arc"]
    addr = reading["address"]
    moon = reading["moon"]
    mths = reading["methods"]

    print(f"\n{BAR}")
    print(f"  Supreme Mathematics — {weekday}, {title}  {time}")
    print(BAR)

    # ── Moon ──────────────────────────────────────────────────────────────────
    to_full = moon.get("days_to_full", 0)
    to_full_str = ("full now" if to_full < 0.5
                   else f"{round(to_full)} {'day' if round(to_full)==1 else 'days'} to full")
    print(f"\n  {moon['emoji']} {moon['phase']}  ·  "
          f"{moon['illumination_pct']}% illuminated  ·  {to_full_str}")

    # ── Method strip ─────────────────────────────────────────────────────────
    print(f"\n  {'Method A':12}  {'Method B':12}  {'Method C':12}")
    print(f"  {'A · address':12}  {'B · sum':12}  {'C · whole':12}")
    print(f"  {addr['display']:12}  {mths['b']:<12}  {mths['c']:<12}")
    print(f"  {'Y·M·W·D':12}  {'(YYYYMMDD)':12}  {'(M+D+Y)':12}")

    # ── Calculation ───────────────────────────────────────────────────────────
    print(f"\n  {reading['calculation']}")

    # ── Three seats ───────────────────────────────────────────────────────────
    print(f"\n  {HALF}")
    for prep_key, op_key, rec in (
        ("attention_prep", "attention_op", att),
        ("intention_prep", "intention_op", itn),
        ("purpose_prep",   "purpose_op",   pur),
    ):
        prep = lex.label(prep_key)
        op   = lex.label(op_key)
        verb = rec.get("verb", "")
        verb_str = f"  · {verb}" if verb else ""
        print(f"\n  {op}  ·  {prep}")
        print(f"  {rec['number']:>2}  {rec['name']}{verb_str}")
        print(f"     {rec.get('pie_root','')}")
        if rec.get("say"):
            print(_wrap(rec["say"], indent=5))

    # ── Convergence ───────────────────────────────────────────────────────────
    print(f"\n  {HALF}")
    aligned = "  aligned" if conv["number"] == 6 else ""
    print(f"\n  {att['number']} + {itn['number']} + {pur['number']} → "
          f"{conv['number']}  {conv['name']}{aligned}")
    print(f"  {reading['onion_instruction']}")

    # ── Year arc ──────────────────────────────────────────────────────────────
    print(f"\n  Year Arc  {yr['number']} — {yr['name']}  ({dt.year})")
    print()
    print(BAR)
    print("  The lexicon is a proposal. Calculation and address are sealed;")
    print("  translation stays in your hands — edit a root and the day re-reads.\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sm_daily",
        description="Supreme Mathematics daily reading engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--date",   metavar="YYYY-MM-DD",
                   help="Date to read (default: today)")
    p.add_argument("--hour",   metavar="H", type=int,
                   help="Hour 0–23 to use for Intention (default: current hour)")
    p.add_argument("--notion", action="store_true",
                   help="Push reading to Notion")
    p.add_argument("--json",   action="store_true",
                   help="Output raw JSON")
    p.add_argument("--lexicon", metavar="PATH",
                   help="Path to a custom lexicon JSON file")
    return p


def main() -> None:
    args   = build_parser().parse_args()
    now    = datetime.datetime.now()

    # Build the datetime to read
    if args.date:
        try:
            d = datetime.date.fromisoformat(args.date)
        except ValueError:
            sys.exit(f"Invalid date {args.date!r}. Use YYYY-MM-DD format.")
    else:
        d = now.date()

    hour = args.hour if args.hour is not None else now.hour
    if not 0 <= hour <= 23:
        sys.exit(f"--hour must be 0–23, got {hour}")

    dt = datetime.datetime(d.year, d.month, d.day, hour, now.minute)

    # Lexicon
    lexicon_path = args.lexicon or DEFAULT_LEXICON_PATH
    try:
        lex = Lexicon(lexicon_path)
    except FileNotFoundError:
        sys.exit(f"Lexicon file not found: {lexicon_path}")

    reading = compute_daily(dt, lex)

    if args.json:
        print(json.dumps(reading, indent=2))
        return

    print_reading(reading, lex)

    if args.notion:
        try:
            from suprememath.notion_sync import push
            url = push(reading)
            print(f"  ✓ Notion page created: {url}\n")
        except EnvironmentError as exc:
            sys.exit(str(exc))
        except Exception as exc:
            sys.exit(f"Notion error: {exc}")


if __name__ == "__main__":
    main()
