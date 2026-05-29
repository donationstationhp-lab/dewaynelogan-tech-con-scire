"""
Core reading engine — maps a datetime to Attention · Intention · Purpose.

  now  →  Calculate (Method B)   →  Attention   "of"
       →  Decode (12-hour clock) →  Intention   "by"
       →  Translate (A + I)      →  Purpose     "through"
       →  Converge (A + I + P)   →  Resolution

Attention  = method_b(date)          — the day's sealed cipher
Intention  = reduce(hour_12)         — the hour; changes each hour
Purpose    = reduce(attention + intention)
Convergence = reduce(attention + intention + purpose)
"""

from __future__ import annotations
import datetime
from typing import Any

from .digits import reduce, method_a, method_b, method_c, calculation_steps
from .lexicon import Lexicon
from .moon import moon_phase as _moon_phase


def _rec(n: int, lex: Lexicon) -> dict[str, Any]:
    return {"number": n, **lex.get(n)}


def compute_daily(
    dt: datetime.datetime | datetime.date,
    lex: Lexicon,
) -> dict[str, Any]:
    """
    Compute the Supreme Mathematics reading for *dt*.

    Accepts a datetime (time-aware reading) or a date (intention uses
    midnight / hour 0, which reduces to 12 on the 12-hour clock).

    Returns a dict with keys:
      datetime, date, time,
      attention (method_b), intention (reduce of 12-hr hour),
      purpose (reduce of att+int), convergence (reduce of att+int+pur),
      address (method_a Y·M·W·D), year_arc (reduce of year),
      moon, calculation (display string), onion_instruction,
      methods {a: display_str, b: int, c: int}
    """
    if isinstance(dt, datetime.datetime):
        date = dt.date()
        hour = dt.hour
    else:
        date = dt
        hour = 0

    h12 = (hour % 12) or 12

    attention_n   = method_b(date)
    intention_n   = reduce(h12)
    purpose_n     = reduce(attention_n + intention_n)
    convergence_n = reduce(attention_n + intention_n + purpose_n)
    year_n        = reduce(date.year)

    addr      = method_a(date)
    steps_str, _, _ = calculation_steps(date)

    att  = _rec(attention_n,   lex)
    itn  = _rec(intention_n,   lex)
    pur  = _rec(purpose_n,     lex)
    conv = _rec(convergence_n, lex)
    yr   = _rec(year_n,        lex)

    onion = (
        f"{att['name']} · {itn['name']} "
        f"→ {pur['name']} born, resolved in {conv['name']}."
    )

    return {
        "datetime":          dt.isoformat() if isinstance(dt, datetime.datetime) else date.isoformat(),
        "date":              date.isoformat(),
        "time":              f"{hour:02d}:{0:02d}",
        "attention":         att,
        "intention":         itn,
        "purpose":           pur,
        "convergence":       conv,
        "year_arc":          yr,
        "address":           addr,
        "moon":              _moon_phase(dt),
        "calculation":       steps_str,
        "onion_instruction": onion,
        "methods": {
            "a": addr["display"],
            "b": method_b(date),
            "c": method_c(date),
        },
    }
