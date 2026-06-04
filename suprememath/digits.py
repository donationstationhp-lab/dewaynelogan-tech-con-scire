"""
Digit-reduction and date arithmetic for Supreme Mathematics readings.

Three methods (matching the sealed reference):

  Method A — address  Y·M·W·D
    Four independent reductions; returns a dict + display string, not a
    single number.  Y = reduce(year), M = reduce(month),
    W = reduce(ceil(day_of_year / 7)), D = reduce(day_of_month).

  Method B — sum  (primary date cipher; used for Attention)
    Concatenate YYYY MM DD as a digit string, sum all digits, reduce.
    Example: 2026-05-29 → "20260529" → 2+0+2+6+0+5+2+9 = 26 → 8

  Method C — whole
    Sum month, day, and year as raw integers, then reduce.
    Example: 5 + 29 + 2026 = 2060 → 2+0+6+0 = 8
"""

from __future__ import annotations
import datetime
import math


def reduce(n: int) -> int:
    """Digital root: sum digits of abs(n) until result is 0–9."""
    n = abs(n)
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n


def day_of_year(date: datetime.date) -> int:
    """Return the 1-based day-of-year (1–366)."""
    return date.timetuple().tm_yday


def week_of_year(date: datetime.date) -> int:
    """Return the week number within the year (ceil of day_of_year / 7)."""
    return math.ceil(day_of_year(date) / 7)


def method_a(date: datetime.date) -> dict:
    """
    Address method: return Y·M·W·D — four independent reduced coordinates.

    Returns a dict with keys Y, M, W, D (ints) and 'display' (str "Y·M·W·D").
    """
    y = reduce(date.year)
    m = reduce(date.month)
    w = reduce(week_of_year(date))
    d = reduce(date.day)
    return {"Y": y, "M": m, "W": w, "D": d, "display": f"{y}·{m}·{w}·{d}"}


def method_b(date: datetime.date) -> int:
    """Sum: concatenate YYYYMMDD digits, sum, reduce. Primary date cipher."""
    raw = f"{date.year}{date.month:02d}{date.day:02d}"
    return reduce(sum(int(c) for c in raw))


def method_c(date: datetime.date) -> int:
    """Whole: reduce(month_int + day_int + year_int)."""
    return reduce(date.month + date.day + date.year)


def calculation_steps(date: datetime.date) -> tuple[str, int, int]:
    """
    Return (display_string, raw_sum, reduced) for the date cipher (Method B).

    Display shows digits in M+D+YYYY order to match existing journal entries;
    the sum is order-independent and equals method_b(date).
    Example: 2026-02-07 → "2 + 7 + 2 + 0 + 2 + 6 = 19 → 1"
    """
    raw = str(date.month) + str(date.day) + str(date.year)
    digits = [int(c) for c in raw]
    total = sum(digits)
    result = reduce(total)
    parts = " + ".join(str(d) for d in digits)
    display = f"{parts} = {total}" + (f" → {result}" if total != result else "")
    return display, total, result
