"""
Digit-reduction and date arithmetic for Supreme Mathematics readings.

Three methods for deriving a single digit from a calendar date:

  Method A — flat (primary, matches existing daily-journal format):
    Concatenate month, day, and 4-digit year as individual digits;
    sum them all; reduce to a single digit (0–9).
    Example: 2026-02-07 → digits 2,7,2,0,2,6 → sum 19 → reduce → 1

  Method B — component:
    Independently reduce month, day, and 4-digit year each to a single
    digit, then sum and reduce those three results.
    Example: reduce(2) + reduce(7) + reduce(2026) = 2+7+1 = 10 → 1

  Method C — ordinal:
    Reduce the day-of-year number (1–366).
    Example: 2026-02-07 is day 38 → 3+8=11 → 2
"""

from __future__ import annotations
import datetime


def reduce(n: int) -> int:
    """Digital root: sum the digits of abs(n) until the result is 0–9."""
    n = abs(n)
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n


def method_a(date: datetime.date) -> int:
    """Flat all-digit sum: concat month+day+year digits, sum, reduce."""
    raw = str(date.month) + str(date.day) + str(date.year)
    return reduce(sum(int(c) for c in raw))


def method_b(date: datetime.date) -> int:
    """Component sum: reduce each of month, day, year; sum; reduce."""
    return reduce(reduce(date.month) + reduce(date.day) + reduce(date.year))


def method_c(date: datetime.date) -> int:
    """Ordinal: reduce the day-of-year (1–366)."""
    return reduce(date.timetuple().tm_yday)


def calculation_steps(date: datetime.date) -> tuple[str, int, int]:
    """
    Return (display_string, raw_sum, reduced) for Method A.

    display_string matches the format used in existing daily journal entries,
    e.g. "2 + 7 + 2 + 0 + 2 + 6 = 19 → 1"
    """
    raw = str(date.month) + str(date.day) + str(date.year)
    digits = [int(c) for c in raw]
    total = sum(digits)
    result = reduce(total)
    parts = " + ".join(str(d) for d in digits)
    if total != result:
        display = f"{parts} = {total} → {result}"
    else:
        display = f"{parts} = {result}"
    return display, total, result
