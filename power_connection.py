#!/usr/bin/env python3
"""power_connection.py — Numerological date calculator.

Calculates the power connection of a date through two paths:
  Path One  (Whole Year):      month + day + year → reduce
  Path Two  (Individual Digits): each digit separately → reduce

Both paths converge to a single born number whose intelligence
is then translated into its directive.

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
    Returns a dict with both paths, compound numbers, and the born result.
    """
    # Path One — whole year
    p1_raw      = month + day + year
    p1_compound = _digit_sum(p1_raw) if p1_raw > 99 else p1_raw
    p1_born     = reduce_to_single(p1_compound)

    # Path Two — individual digits
    all_digits  = [int(d) for d in f"{month}{day}{year}"]
    p2_raw      = sum(all_digits)
    p2_compound = p2_raw
    p2_born     = reduce_to_single(p2_compound)

    # Directive: decode each component
    directive = _build_directive(month, day, year, p1_raw, p1_compound, p2_raw, p2_compound, p1_born)

    return {
        "date":      {"month": month, "day": day, "year": year},
        "path_one":  {"raw": p1_raw,  "compound": p1_compound, "born": p1_born},
        "path_two":  {"raw": p2_raw,  "compound": p2_compound, "born": p2_born},
        "born":      p1_born,
        "directive": directive,
    }


def _build_directive(month, day, year, p1_raw, p1_compound, p2_raw, p2_compound, born):
    parts = []

    # Month and day
    m_name = _label(month)
    d_name = _label(day)
    parts.append(
        f"{month}/{day} — {m_name} powered refinement of/by/through {d_name}."
    )

    # Year decoded digit by digit
    year_digits = [int(d) for d in str(year)]
    year_phrase = " → ".join(f"{d}({_label(d)})" for d in year_digits)
    parts.append(
        f"{year} amplifies: {year_phrase}."
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
    d  = result["date"]
    p1 = result["path_one"]
    p2 = result["path_two"]

    print(f"\n{BAR}")
    print(f"  POWER CONNECTION  —  {d['month']}/{d['day']}/{d['year']}")
    print(BAR)

    print(f"\n  PATH ONE  (Whole Year)")
    print(f"    {d['month']} + {d['day']} + {d['year']} = {p1['raw']}")
    if p1['raw'] != p1['compound']:
        print(f"    {'  '.join(str(p1['raw']))} → {p1['compound']}")
    digits_c = " + ".join(str(x) for x in str(p1['compound']))
    print(f"    {digits_c} = {p1['born']}  [{_label(p1['born'])}]")

    print(f"\n  PATH TWO  (Individual Digits)")
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
