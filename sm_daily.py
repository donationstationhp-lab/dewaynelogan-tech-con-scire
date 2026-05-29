#!/usr/bin/env python3
"""sm_daily.py — Supreme Mathematics daily reading

Usage:
  python sm_daily.py                         # today's reading
  python sm_daily.py --date 2026-05-29       # specific date
  python sm_daily.py --notion                # also push to Notion
  python sm_daily.py --json                  # output raw JSON
  python sm_daily.py --method b              # use Method B for Date Vibration

Methods for Date Vibration cipher:
  a  flat: all digits of MONTH+DAY+YEAR concatenated, summed, reduced  (default)
  b  component: reduce(month) + reduce(day) + reduce(year), then reduce
  c  ordinal: reduce the day-of-year number (1–366)

Environment variables (for --notion):
  NOTION_TOKEN       Notion integration token  (required)
  NOTION_PARENT_ID   Parent page ID to write into  (optional; defaults to
                     the Daily Mathematics Journal page)
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
BAR = "─" * WIDTH


def _wrap(text: str, indent: int = 4) -> str:
    return textwrap.fill(
        text, width=WIDTH,
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
    )


def print_reading(reading: dict) -> None:
    date    = datetime.date.fromisoformat(reading["date"])
    weekday = date.strftime("%A")
    title   = date.strftime("%B %-d, %Y")

    att  = reading["attention"]
    itn  = reading["intention"]
    pur  = reading["purpose"]
    yr   = reading["year"]
    cph  = reading["cipher"]
    moon = reading["moon"]

    print(f"\n{BAR}")
    print(f"  Supreme Mathematics — {weekday}, {title}")
    print(BAR)

    # ── Consciousness Calculation ─────────────────────────────────────────────
    print("\n  📊 Consciousness Calculation")
    print(f"     {reading['calculation']}")
    print(f"     {reading['reading_labels']['cipher']}: "
          f"{cph['number']} = {cph['name']}")

    # ── Onion Instruction ─────────────────────────────────────────────────────
    print(f"\n  🧅 Onion Instruction ({date.year})")
    print(_wrap(reading["onion_instruction"], indent=5))
    print()
    print(f"     Component Decode:")

    def _decode_line(label: str, source: str, n: int, name: str) -> str:
        return f"  {label:<22}  {source:<20}  {n} = {name}"

    month_src = f"Month {date.month} → {reduce(date.month)}"
    day_src   = f"Day {date.day} → {reduce(date.day)}"
    born_src  = f"M{date.month}+D{date.day} → {reduce(date.month+date.day)}"
    year_src  = f"Year {date.year} → {reduce(date.year)}"

    print("    " + _decode_line(
        reading["reading_labels"]["attention"], month_src, att["number"], att["name"]))
    print("    " + _decode_line(
        reading["reading_labels"]["intention"], day_src,   itn["number"], itn["name"]))
    print("    " + _decode_line(
        reading["reading_labels"]["purpose"],   born_src,  pur["number"], pur["name"]))
    print("    " + _decode_line(
        "Year Arc",                             year_src,  yr["number"],  yr["name"]))

    # ── Instructions ─────────────────────────────────────────────────────────
    print(f"\n  {BAR[:WIDTH//2]}")
    for label_key, rec in (
        ("attention", att),
        ("intention", itn),
        ("purpose",   pur),
        ("year_arc",  yr),
    ):
        label = reading["reading_labels"][label_key]
        print(f"\n  {label}  ·  {rec['number']} – {rec['name']}")
        if rec.get("instruction"):
            print(_wrap(rec["instruction"]))
        if rec.get("pie_root"):
            print(f"     PIE: {rec['pie_root']}")

    # ── Moon ──────────────────────────────────────────────────────────────────
    print(f"\n  {BAR[:WIDTH//2]}")
    print(f"\n  🌙 Moon Phase: {moon['emoji']} {moon['phase']} "
          f"({moon['illumination_pct']}% illuminated)\n")
    print(BAR + "\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sm_daily",
        description="Supreme Mathematics daily reading engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--date",   metavar="YYYY-MM-DD",
                   help="Date to read (default: today)")
    p.add_argument("--method", choices=["a", "b", "c"], default="a",
                   help="Date Vibration cipher method (default: a)")
    p.add_argument("--notion", action="store_true",
                   help="Push reading to Notion")
    p.add_argument("--json",   action="store_true",
                   help="Output raw JSON")
    p.add_argument("--lexicon", metavar="PATH",
                   help="Path to a custom lexicon JSON file")
    return p


def main() -> None:
    args = build_parser().parse_args()

    # Date
    if args.date:
        try:
            date = datetime.date.fromisoformat(args.date)
        except ValueError:
            sys.exit(f"Invalid date {args.date!r}. Use YYYY-MM-DD format.")
    else:
        date = datetime.date.today()

    # Lexicon
    lexicon_path = args.lexicon or DEFAULT_LEXICON_PATH
    try:
        lex = Lexicon(lexicon_path)
    except FileNotFoundError:
        sys.exit(f"Lexicon file not found: {lexicon_path}")

    # Compute
    reading = compute_daily(date, lex, cipher_method=args.method)

    # Attach labels for display convenience
    reading["reading_labels"] = {
        "attention": lex.label_attention,
        "intention": lex.label_intention,
        "purpose":   lex.label_purpose,
        "cipher":    lex.label_cipher,
        "year_arc":  "Year Arc",
    }

    if args.json:
        print(json.dumps(reading, indent=2))
        return

    print_reading(reading)

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
