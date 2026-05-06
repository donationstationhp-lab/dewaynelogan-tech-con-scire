#!/usr/bin/env python3
"""power_connection.py — Numerological date calculator.

Three steps, in order:
  1. The Root:  month expresses through day → the date's foundation
  2. Path One   (Whole Year):       root + year → reduce
  3. Path Two   (Individual Digits): each digit separately → reduce

Every month expresses itself through a day to form a date.
That date (month + day) is the root. The year then amplifies
the intelligence of the root. Both full calculations are
birthed from that understanding.

Usage:
  python power_connection.py              # today's date
  python power_connection.py 5 6 2026    # month day year
  python power_connection.py --json 5 6 2026

  python power_connection.py mark 7 2 2026 "Proceed with project"
  python power_connection.py marks        # list all marked dates
"""

import argparse
import json
import os
import sys
from datetime import date

MARKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".power_marks.json")

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

    Step 1 — Root: month expresses through day; this is the date's foundation.
    Step 2 — Path One: the year amplifies the root (whole year method).
    Step 3 — Path Two: the year amplifies the root (individual digit method).
    """
    # Step 1 — Root: month expressing through day forms the date
    root_raw  = month + day
    root_born = reduce_to_single(root_raw)

    # Step 2 — Path One: root + year as whole numbers, then reduced
    p1_raw      = month + day + year
    p1_compound = _digit_sum(p1_raw) if p1_raw > 99 else p1_raw
    p1_born     = reduce_to_single(p1_compound)

    # Step 3 — Path Two: every individual digit summed, then reduced
    all_digits  = [int(d) for d in f"{month}{day}{year}"]
    p2_raw      = sum(all_digits)
    p2_compound = p2_raw
    p2_born     = reduce_to_single(p2_compound)

    directive = _build_directive(month, day, year, root_raw, root_born,
                                 p1_raw, p1_compound, p2_raw, p2_compound, p1_born)

    return {
        "date":     {"month": month, "day": day, "year": year},
        "root":     {"raw": root_raw, "born": root_born},
        "path_one": {"raw": p1_raw,  "compound": p1_compound, "born": p1_born},
        "path_two": {"raw": p2_raw,  "compound": p2_compound, "born": p2_born},
        "born":     p1_born,
        "directive": directive,
    }


def _build_directive(month, day, year,
                     root_raw, root_born,
                     p1_raw, p1_compound,
                     p2_raw, p2_compound, born):
    parts = []

    # The root: month expresses through day
    m_name = _label(month)
    d_name = _label(day)
    root_label = ""
    if root_raw in COMPOUND_MEANINGS:
        root_label = f" [{COMPOUND_MEANINGS[root_raw][0]}]"
    elif root_raw in SINGLE_MEANINGS:
        root_label = f" [{SINGLE_MEANINGS[root_raw][0]}]"
    parts.append(
        f"{month} ({m_name}) expresses itself through {day} ({d_name})"
        f" to form the date. The root is born to {root_raw}{root_label}."
    )

    # Year amplifies the intelligence of the date (the root)
    year_digits = [int(d) for d in str(year)]
    year_phrase = " → ".join(f"{d}({_label(d)})" for d in year_digits)
    parts.append(
        f"{year} amplifies the intelligence of the date: {year_phrase}."
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
    rt  = result["root"]
    p1  = result["path_one"]
    p2  = result["path_two"]

    print(f"\n{BAR}")
    print(f"  POWER CONNECTION  —  {d['month']}/{d['day']}/{d['year']}")
    print(BAR)

    # ── Step 1: The Root — month expresses through day ────────────────────────
    root_raw  = rt["raw"]
    root_born = rt["born"]
    root_label = ""
    if root_raw in COMPOUND_MEANINGS:
        root_label = f"  [{COMPOUND_MEANINGS[root_raw][0]}]"
    elif root_raw in SINGLE_MEANINGS:
        root_label = f"  [{SINGLE_MEANINGS[root_raw][0]}]"

    print(f"\n  STEP 1  —  The Root  (Month expresses through Day)")
    print(f"    {d['month']} [{_label(d['month'])}]  expresses through"
          f"  {d['day']} [{_label(d['day'])}]")
    print(f"    {d['month']} + {d['day']} = {root_raw}{root_label}")
    if root_raw != root_born:
        digits_root = " + ".join(str(x) for x in str(root_raw))
        print(f"    {digits_root} = {root_born}  [{_label(root_born)}]")

    print(f"\n  {'─' * (WIDTH - 2)}")
    print(f"  The year amplifies the intelligence of the date.")
    print(f"  Born into the full calculations:\n")

    # ── Step 2: Path One — year amplifies the root (whole year) ───────────────
    print(f"  STEP 2  —  Path One  (Year amplifies — Whole Numbers)")
    print(f"    {d['month']} + {d['day']} + {d['year']} = {p1['raw']}")
    if p1['raw'] != p1['compound']:
        spaced = "  ".join(str(p1['raw']))
        print(f"    {spaced} → {p1['compound']}")
    digits_c = " + ".join(str(x) for x in str(p1['compound']))
    print(f"    {digits_c} = {p1['born']}  [{_label(p1['born'])}]")

    # ── Step 3: Path Two — year amplifies the root (individual digits) ─────────
    print(f"\n  STEP 3  —  Path Two  (Year amplifies — Individual Digits)")
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


# ── Marks ─────────────────────────────────────────────────────────────────────

def marks_load():
    if os.path.exists(MARKS_FILE):
        with open(MARKS_FILE) as f:
            return json.load(f)
    return []


def marks_save(marks):
    with open(MARKS_FILE, "w") as f:
        json.dump(marks, f, indent=2)


def mark_date(month, day, year, note=""):
    result  = calculate(month, day, year)
    marks   = marks_load()
    entry   = {
        "date":      f"{month}/{day}/{year}",
        "note":      note,
        "root":      result["root"]["raw"],
        "root_born": result["root"]["born"],
        "born":      result["born"],
        "born_name": SINGLE_MEANINGS.get(result["born"], ("", ""))[0],
    }
    marks.append(entry)
    marks_save(marks)
    return entry, result


def print_mark(entry, result):
    print(f"\n{BAR}")
    print(f"  MARKED  —  {entry['date']}")
    if entry["note"]:
        print(f"  {entry['note']}")
    print(BAR)
    print_result(result)
    print(f"  Marked: {entry['date']}  |  Root: {entry['root']} → {entry['root_born']}"
          f"  |  Born: {entry['born']} [{entry['born_name']}]\n")


def print_marks_list():
    marks = marks_load()
    if not marks:
        print("No marked dates.")
        return
    print(f"\n{BAR}")
    print(f"  MARKED DATES")
    print(BAR)
    for m in marks:
        note = f"  —  {m['note']}" if m.get("note") else ""
        print(f"\n  {m['date']}{note}")
        print(f"    Root: {m['root']} → {m['root_born']} [{_label(m['root_born'])}]"
              f"    Born: {m['born']} [{m.get('born_name', _label(m['born']))}]")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    argv = sys.argv[1:]

    # mark / marks are detected before handing off to argparse
    if argv and argv[0] == "marks":
        print_marks_list()
        return

    use_json = "--json" in argv
    if use_json:
        argv = [a for a in argv if a != "--json"]

    if argv and argv[0] == "mark":
        rest = argv[1:]
        if len(rest) < 3:
            sys.exit("Usage: power_connection.py mark <month> <day> <year> [note]")
        try:
            month, day, year = int(rest[0]), int(rest[1]), int(rest[2])
        except ValueError:
            sys.exit("month, day, and year must be integers.")
        note = " ".join(rest[3:])
        entry, result = mark_date(month, day, year, note)
        if use_json:
            print(json.dumps({"mark": entry, "result": result}, indent=2))
        else:
            print_mark(entry, result)
        return

    # default: calculate a date
    try:
        if len(argv) >= 3:
            month, day, year = int(argv[0]), int(argv[1]), int(argv[2])
        else:
            today = date.today()
            month, day, year = today.month, today.day, today.year
    except ValueError:
        sys.exit("Usage: power_connection.py [month day year]")

    if not (1 <= month <= 12):
        sys.exit("Month must be between 1 and 12.")
    if not (1 <= day <= 31):
        sys.exit("Day must be between 1 and 31.")
    if year < 1:
        sys.exit("Year must be a positive integer.")

    result = calculate(month, day, year)

    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print_result(result)


if __name__ == "__main__":
    main()
