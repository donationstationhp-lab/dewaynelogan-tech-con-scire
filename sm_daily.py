#!/usr/bin/env python3
"""sm_daily.py — Supreme Mathematics daily reading

Usage:
  python sm_daily.py                         # now
  python sm_daily.py --date 2026-05-29       # that date, current hour
  python sm_daily.py --hour 14               # today at 14:00
  python sm_daily.py --date 2026-05-29 --hour 9
  python sm_daily.py --notion                # push to Notion
  python sm_daily.py --json                  # raw JSON output

Primary frame — Founder's Month/Day Fraction Calendar
  (Notion 46e0a67b-a3dd-494f-ac5c-1cec071123ca):
  Received Attention of  (Month)
  Gained   Intention by  (Day)
  Given    Purpose through all being born to (Month + Day)

Secondary lens — Method B + 12-hour clock:
  A  Y·M·W·D  address
  B  reduce(sum of YYYYMMDD digits) — date cipher
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
except ImportError as exc:
    sys.exit(f"Import error: {exc}\nRun from the project root directory.")

WIDTH = 72
BAR   = "─" * WIDTH
HALF  = "─" * (WIDTH // 2)


def _wrap(text: str, indent: int = 5) -> str:
    return textwrap.fill(
        text, width=WIDTH,
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
    )


def _compound_tag(seat: dict) -> str:
    if seat.get("compound"):
        return f"  [compound: {seat['raw']} → {seat['number']}]"
    return ""


def print_reading(reading: dict) -> None:
    dt      = datetime.date.fromisoformat(reading["date"])
    weekday = dt.strftime("%A")
    title   = f"{dt.strftime('%B')} {dt.day}, {dt.year}"
    time    = reading.get("time", "")

    att  = reading["attention"]
    itn  = reading["intention"]
    pur  = reading["purpose"]
    sec  = reading["secondary"]
    yr   = reading["year_arc"]
    addr = reading["address"]
    moon = reading["moon"]
    mths = reading["methods"]
    srcs = reading["sources"]

    print(f"\n{BAR}")
    print(f"  Supreme Mathematics — {weekday}, {title}  {time}")
    print(BAR)

    # ── Moon ──────────────────────────────────────────────────────────────────
    to_full = moon.get("days_to_full", 0)
    to_full_str = ("full now" if to_full < 0.5
                   else f"{round(to_full)} {'day' if round(to_full)==1 else 'days'} to full")
    print(f"\n  {moon['emoji']} {moon['phase']}  ·  "
          f"{moon['illumination_pct']}% illuminated  ·  {to_full_str}")
    if moon.get("note"):
        print(f"     {moon['note']}")

    # ── Primary: Fraction Calendar ────────────────────────────────────────────
    print(f"\n{BAR}")
    print(f"  FRACTION CALENDAR  ·  Received · Gained · Given")
    print(f"  {srcs['fraction_calendar']['name']}")
    print(BAR)

    for seat in (att, itn, pur):
        compound_tag = _compound_tag(seat)
        print(f"\n  {seat['liturgy']}")
        print(f"   {seat['number']:>2}  {seat['name']}{compound_tag}")
        if seat.get("pie_root"):
            print(f"       {seat['pie_root']}")
        if seat.get("say"):
            print(_wrap(seat["say"], indent=6))

    # ── Secondary lens ────────────────────────────────────────────────────────
    print(f"\n{HALF}")
    print(f"  Secondary lens  ·  Method B + 12-hour clock")
    print(HALF)

    print(f"\n  {'Method A':12}  {'Method B':12}  {'Method C':12}")
    print(f"  {addr['display']:12}  {mths['b']:<12}  {mths['c']:<12}")
    print(f"  {'Y·M·W·D':12}  {'YYYYMMDD':12}  {'M+D+Y':12}")
    print(f"\n  Cipher: {reading['calculation']}")

    h   = sec["hour"]
    s_a = sec["attention"]
    s_p = sec["purpose"]
    s_c = sec["convergence"]
    aligned_tag = "  ← aligned" if s_c["aligned"] else ""

    print(f"\n  Hour {time} → h12={h['h12']}"
          f":  {h['number']}  {h['name']}")
    print(f"  Date cipher (B)   :  {s_a['number']}  {s_a['name']}")
    print(f"  Cipher purpose    :  {s_p['number']}  {s_p['name']}")
    print(f"  Convergence       :  {s_c['number']}  {s_c['name']}{aligned_tag}")

    # ── Year arc ──────────────────────────────────────────────────────────────
    print(f"\n{BAR}")
    print(f"  Year Arc  {yr['number']} — {yr['name']}  ({dt.year})")

    # ── Sources ───────────────────────────────────────────────────────────────
    print(f"\n  Sources:")
    for key, src in srcs.items():
        print(f"    {src['name']}")
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
                   help="Hour 0–23 (default: current hour)")
    p.add_argument("--notion", action="store_true",
                   help="Push reading to Notion")
    p.add_argument("--json",   action="store_true",
                   help="Output raw JSON")
    p.add_argument("--lexicon", metavar="PATH",
                   help="Path to a custom lexicon JSON file")
    return p


def main() -> None:
    args = build_parser().parse_args()
    now  = datetime.datetime.now()

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

    dt = datetime.datetime(d.year, d.month, d.day, hour)

    lexicon_path = args.lexicon or DEFAULT_LEXICON_PATH
    try:
        lex = Lexicon(lexicon_path)
    except FileNotFoundError:
        sys.exit(f"Lexicon file not found: {lexicon_path}")

    reading = compute_daily(dt, lex)

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
