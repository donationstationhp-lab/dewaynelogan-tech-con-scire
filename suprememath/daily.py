"""
Core reading engine: maps a date to Attention / Intention / Purpose
plus the date-vibration cipher and moon phase.
"""

from __future__ import annotations
import datetime
from typing import Any

from .digits import reduce, method_a, method_b, method_c, calculation_steps
from .lexicon import Lexicon
from .moon import moon_phase as _moon_phase


def _position_record(n: int, lex: Lexicon) -> dict[str, Any]:
    entry = lex.get(n)
    return {"number": n, **entry}


def compute_daily(
    date: datetime.date,
    lex: Lexicon,
    *,
    cipher_method: str = "a",
) -> dict[str, Any]:
    """
    Compute the Supreme Mathematics reading for *date*.

    cipher_method controls which arithmetic is used for the Date Vibration:
      'a'  flat all-digit sum  (default; matches existing journal entries)
      'b'  component-wise reduce-then-sum
      'c'  day-of-year ordinal

    Returns a dict with keys:
      date, attention (month), intention (day),
      purpose (reduce(month+day) — born from both),
      year (reduce(year) — the year arc),
      cipher, moon, calculation (Method A display), methods (a/b/c results)
    """
    # Receive Attention OF the month | Gain Intention BY the day
    # Give Purpose through all being born to (Month + Day)
    attention_n = reduce(date.month)
    intention_n = reduce(date.day)
    purpose_n   = reduce(date.month + date.day)
    year_n      = reduce(date.year)

    _methods = {"a": method_a, "b": method_b, "c": method_c}
    if cipher_method not in _methods:
        raise ValueError(f"cipher_method must be 'a', 'b', or 'c'; got {cipher_method!r}")
    cipher_n = _methods[cipher_method](date)

    steps_str, _raw_sum, _reduced = calculation_steps(date)

    attention = _position_record(attention_n, lex)
    intention = _position_record(intention_n, lex)
    purpose   = _position_record(purpose_n,   lex)
    year      = _position_record(year_n,      lex)
    cipher    = _position_record(cipher_n,    lex)

    # "Attention + Intention = Year made clear" — the Onion uses the year arc
    onion = (
        f"{attention['name']} + {intention['name']} = "
        f"{year['name']} made clear."
    )

    return {
        "date": date.isoformat(),
        "attention":   attention,   # month
        "intention":   intention,   # day
        "purpose":     purpose,     # reduce(month + day) — born from both
        "year":        year,        # reduce(year) — the year arc
        "cipher":      cipher,
        "moon":        _moon_phase(date),
        "calculation": steps_str,
        "onion_instruction": onion,
        "methods": {
            "a": method_a(date),
            "b": method_b(date),
            "c": method_c(date),
        },
    }
