"""
Core reading engine.

PRIMARY frame — Founder's Month/Day Fraction Calendar
  (Notion 46e0a67b-a3dd-494f-ac5c-1cec071123ca):

  Received Attention of  (Month)
  Gained   Intention by  (Day)
  Given    Purpose through all being born to (Month + Day)

  Month and Day are carried as raw values; SM position = reduce(raw).
  The Purpose sum (Month + Day) is UNREDUCED — "compound-not-collapsed."

SECONDARY frame — Method B date cipher + 12-hour clock (labeled lens only):

  method_b(date)            → date cipher
  reduce(12-hour hour)      → hour cipher
  reduce(cipher + hour)     → hour purpose
  reduce(c + h + hp)        → convergence

Sources:
  Fraction Calendar — Notion 46e0a67b-a3dd-494f-ac5c-1cec071123ca
  Lunar Thread      — Notion 35603691-bd5e-81a3-a4d4-fa3b27ca0975
"""

from __future__ import annotations
import calendar
import datetime
from typing import Any

from .digits import reduce, method_a, method_b, method_c, calculation_steps
from .lexicon import Lexicon
from .moon import moon_phase as _moon_phase

_SOURCES: dict[str, dict[str, str]] = {
    "fraction_calendar": {
        "name":      "Founder's Month/Day Fraction Calendar",
        "notion_id": "46e0a67ba3dd494fac5c1cec071123ca",
    },
    "lunar_thread": {
        "name":      "Lunar Cycle Learning Thread",
        "notion_id": "35603691bd5e81a3a4d4fa3b27ca0975",
    },
}


def _seat(position: int, lex: Lexicon) -> dict[str, Any]:
    entry = lex.get(position)
    return {
        "number":   position,
        "name":     entry["name"],
        "pie_root": entry.get("pie_root", ""),
        "say":      entry.get("say", ""),
    }


def compute_daily(
    dt: datetime.datetime | datetime.date,
    lex: Lexicon,
) -> dict[str, Any]:
    """
    Compute the Supreme Mathematics reading for *dt*.

    Returns a dict with:
      date, time,
      attention / intention / purpose  (primary Fraction Calendar frame),
      secondary  (Method B + 12-hour clock lens),
      year_arc, address, moon, calculation,
      methods {a, b, c}, sources
    """
    if isinstance(dt, datetime.datetime):
        date = dt.date()
        hour = dt.hour
    else:
        date = dt
        hour = 0

    month = date.month
    day   = date.day
    year  = date.year
    month_name = calendar.month_name[month]  # "May"

    # ── Primary: Fraction Calendar ────────────────────────────────────────────
    att_pos = reduce(month)
    itn_pos = reduce(day)
    pur_raw = month + day        # UNREDUCED — compound-not-collapsed
    pur_pos = reduce(pur_raw)

    attention = {
        **_seat(att_pos, lex),
        "verb":    "Received",
        "prep":    "of",
        "raw":     month,
        "liturgy": f"Received Attention of ({month_name} = {month})",
    }
    intention = {
        **_seat(itn_pos, lex),
        "verb":     "Gained",
        "prep":     "by",
        "raw":      day,
        "compound": day != itn_pos,
        "liturgy":  f"Gained Intention by ({day})",
    }
    purpose = {
        **_seat(pur_pos, lex),
        "verb":     "Given",
        "prep":     "through",
        "raw":      pur_raw,
        "month":    month,
        "day":      day,
        "compound": pur_raw != pur_pos,
        "liturgy": (
            f"Given Purpose through all being born to "
            f"({month} + {day} = {pur_raw})"
        ),
    }

    # ── Secondary: Method B + 12-hour clock ──────────────────────────────────
    h12     = (hour % 12) or 12
    mb      = method_b(date)
    mb_itn  = reduce(h12)
    mb_pur  = reduce(mb + mb_itn)
    mb_conv = reduce(mb + mb_itn + mb_pur)

    secondary = {
        "label": "Method B + 12-hour clock (secondary lens)",
        "hour": {
            "h12":    h12,
            "number": mb_itn,
            "name":   lex.name(mb_itn),
        },
        "attention": {
            "number": mb,
            "name":   lex.name(mb),
        },
        "purpose": {
            "number": mb_pur,
            "name":   lex.name(mb_pur),
        },
        "convergence": {
            "number":  mb_conv,
            "name":    lex.name(mb_conv),
            "aligned": mb_conv == 6,
        },
    }

    # ── Supporting ────────────────────────────────────────────────────────────
    year_pos = reduce(year)
    year_arc = {**_seat(year_pos, lex), "year": year}
    addr     = method_a(date)
    steps_str, _, _ = calculation_steps(date)

    return {
        "date":        date.isoformat(),
        "time":        f"{hour:02d}:00",
        "attention":   attention,
        "intention":   intention,
        "purpose":     purpose,
        "secondary":   secondary,
        "year_arc":    year_arc,
        "address":     addr,
        "moon":        _moon_phase(dt),
        "calculation": steps_str,
        "methods": {
            "a": addr["display"],
            "b": mb,
            "c": method_c(date),
        },
        "sources": _SOURCES,
    }
