#!/usr/bin/env python3
"""power_connection.py — Numerological date calculator.

Three steps, in order:
  1. Day Calculation:  month + day → understand the day's intelligence
  2. Path One         (Whole Year):       month + day + year → reduce
  3. Path Two         (Individual Digits): each digit separately → reduce

The day is understood first. The user is then birthed into
both full calculations, which converge to a single born number.

Usage:
  python power_connection.py              # today's date
  python power_connection.py 5 6 2026    # month day year
  python power_connection.py --json 5 6 2026
"""

import argparse
import json
import sys
from datetime import date

# ── Number intelligence ────────────────────────────────────────────────────────

SINGLE_MEANINGS = {
    1: ("Origin",      "The initiating force. Singular will that begins all things."),
    2: ("Wisdom",      "Intelligence that knows it needs its counterpart. Partnership."),
    3: ("Creation",    "Expression. Communication. The point where thought becomes word."),
    4: ("Foundation",  "Structure. The frame upon which all else is built."),
    5: ("Power",       "Directed force moving through a process to refine it."),
    6: ("Equality",    "Balance as the measuring rod. The law that governs how power operates."),
    7: ("Revelation",  "Depth. The intelligence that surfaces what is hidden."),
    8: ("Authority",   "Abundance in flow. The infinite cycle of giving and receiving."),
    9: ("Completion",  "Universal wisdom. Everything fulfilled, nothing wasted."),
}

COMPOUND_MEANINGS = {
    10: ("New Cycle",       "Origin reborn. The circle closed and opened again."),
    11: ("Illumination",    "Master number. Light amplified beyond ordinary measure."),
    12: ("Suspension",      "Completion through pause. Wisdom earned by seeing from a new angle."),
    21: ("Fulfillment",     "The world turning in full cycle. Everything arriving in right order."),
    22: ("Master Builder",  "Master number. Vision translated into lasting structure."),
    33: ("Master Teacher",  "Master number. Creation in service of the whole."),
}

NUMBER_LABELS = {
    1: "Origin",    2: "Wisdom",     3: "Creation",  4: "Foundation",
    5: "Power",     6: "Equality",   7: "Revelation", 8: "Authority",
    9: "Completion",
}

WIDTH = 68
BAR   = "─" * WIDTH


def _label(n):
    return NUMBER_LABELS.get(n, str(n))


# ── Reduction ─────────────────────────────────────────────────────────────────

def reduce_to_single(n, master_numbers=(11, 22, 33)):
    """Reduce n by digit-sum until single digit or a master number."""
    while n > 9 and n not in master_numbers:
        n = sum(int(d) for d in str(n))
    return n


def _digit_sum(n):
    return sum(int(d) for d in str(n))


# ── Core calculation ───────────────────────────────────────────────────────────

def calculate(month, day, year):
    """
    Returns a dict containing all three steps and the born result.
    Step 1 — Day Calculation — must be understood before steps 2 & 3.
    """
    # Step 1 — Day: month + day, reduced
    day_raw      = month + day
    day_born     = reduce_to_single(day_raw)

    # Step 2 — Path One: whole year added together, then reduced
    p1_raw      = month + day + year
    p1_compound = _digit_sum(p1_raw) if p1_raw > 99 else p1_raw
    p1_born     = reduce_to_single(p1_compound)

    # Step 3 — Path Two: every individual digit summed, then reduced
    all_digits  = [int(d) for d in f"{month}{day}{year}"]
    p2_raw      = sum(all_digits)
    p2_compound = p2_raw
    p2_born     = reduce_to_single(p2_compound)

    directive = _build_directive(month, day, year, day_raw, day_born,
                                 p1_raw, p1_compound, p2_raw, p2_compound, p1_born)

    return {
        "date":      {"month": month, "day": day, "year": year},
        "day_calc":  {"raw": day_raw, "born": day_born},
        "path_one":  {"raw": p1_raw,  "compound": p1_compound, "born": p1_born},
        "path_two":  {"raw": p2_raw,  "compound": p2_compound, "born": p2_born},
        "born":      p1_born,
        "directive": directive,
    }


def _build_directive(month, day, year,
                     day_raw, day_born,
                     p1_raw, p1_compound,
                     p2_raw, p2_compound, born):
    parts = []

    # Day foundation
    m_name = _label(month)
    d_name = _label(day)
    day_label = ""
    if day_raw in COMPOUND_MEANINGS:
        day_label = f" [{COMPOUND_MEANINGS[day_raw][0]}]"
    elif day_raw in SINGLE_MEANINGS:
        day_label = f" [{SINGLE_MEANINGS[day_raw][0]}]"
    parts.append(
        f"{month}/{day} — {m_name} powered refinement of/by/through {d_name}."
        f" The day is born to {day_raw}{day_label}."
    )

    # Year amplifies
    year_digits = [int(d) for d in str(year)]
    year_phrase = " → ".join(f"{d}({_label(d)})" for d in year_digits)
    parts.append(
        f"{year} amplifies the day's intelligence: {year_phrase}."
    )

    # Compound interpretations
    if p1_compound in COMPOUND_MEANINGS:
        name, desc = COMPOUND_MEANINGS[p1_compound]
        parts.append(f"Path One compound {p1_compound} — {name}: {desc}")
    if p2_compound != p1_compound and p2_compound in COMPOUND_MEANINGS:
        name, desc = COMPOUND_MEANINGS[p2_compound]
        parts.append(f"Path Two compound {p2_compound} — {name}: {desc}")

    # Born number
    if born in SINGLE_MEANINGS:
        name, desc = SINGLE_MEANINGS[born]
        parts.append(f"Born to {born} — {name}: {desc}")

    return parts


# ── Output ────────────────────────────────────────────────────────────────────

def _wrap(text, indent=2):
    import textwrap
    return textwrap.fill(text, width=WIDTH,
                         initial_indent=" " * indent,
                         subsequent_indent=" " * indent)


def print_result(result):
    d   = result["date"]
    dc  = result["day_calc"]
    p1  = result["path_one"]
    p2  = result["path_two"]

    print(f"\n{BAR}")
    print(f"  POWER CONNECTION  —  {d['month']}/{d['day']}/{d['year']}")
    print(BAR)

    # ── Step 1: understand the day ────────────────────────────────────────────
    day_raw   = dc["raw"]
    day_born  = dc["born"]
    day_label = ""
    if day_raw in COMPOUND_MEANINGS:
        day_label = f"  [{COMPOUND_MEANINGS[day_raw][0]}]"
    elif day_raw in SINGLE_MEANINGS:
        day_label = f"  [{SINGLE_MEANINGS[day_raw][0]}]"

    print(f"\n  STEP 1  —  Understand the Day")
    print(f"    {d['month']} + {d['day']} = {day_raw}{day_label}")
    if day_raw != day_born:
        digits_day = " + ".join(str(x) for x in str(day_raw))
        print(f"    {digits_day} = {day_born}  [{_label(day_born)}]")

    print(f"\n  {'─' * (WIDTH - 2)}")
    print(f"  Born into the full calculations:\n")

    # ── Step 2: Path One ──────────────────────────────────────────────────────
    print(f"  STEP 2  —  Path One  (Whole Year)")
    print(f"    {d['month']} + {d['day']} + {d['year']} = {p1['raw']}")
    if p1['raw'] != p1['compound']:
        spaced = "  ".join(str(p1['raw']))
        print(f"    {spaced} → {p1['compound']}")
    digits_c = " + ".join(str(x) for x in str(p1['compound']))
    print(f"    {digits_c} = {p1['born']}  [{_label(p1['born'])}]")

    # ── Step 3: Path Two ──────────────────────────────────────────────────────
    print(f"\n  STEP 3  —  Path Two  (Individual Digits)")
    digits_shown = " + ".join(
        str(x) for x in [int(c) for c in f"{d['month']}{d['day']}{d['year']}"]
    )
    print(f"    {digits_shown} = {p2['compound']}")
    digits_b = " + ".join(str(x) for x in str(p2['compound']))
    print(f"    {digits_b} = {p2['born']}  [{_label(p2['born'])}]")

    print(f"\n{BAR}")
    print(f"  BORN  →  {result['born']}  [{_label(result['born'])}]")
    print(BAR)

    print(f"\n  DIRECTIVE\n")
    for line in result["directive"]:
        print(_wrap(line))
        print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(
        prog="power_connection",
        description="Calculate the power connection of a date.",
    )
    p.add_argument("month", nargs="?", type=int, help="Month (1-12)")
    p.add_argument("day",   nargs="?", type=int, help="Day (1-31)")
    p.add_argument("year",  nargs="?", type=int, help="Year (e.g. 2026)")
    p.add_argument("--json", action="store_true", help="Output raw JSON")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.month and args.day and args.year:
        month, day, year = args.month, args.day, args.year
    else:
        today = date.today()
        month, day, year = today.month, today.day, today.year

    if not (1 <= month <= 12):
        sys.exit("Month must be between 1 and 12.")
    if not (1 <= day <= 31):
        sys.exit("Day must be between 1 and 31.")
    if year < 1:
        sys.exit("Year must be a positive integer.")

    result = calculate(month, day, year)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_result(result)


if __name__ == "__main__":
    main()
