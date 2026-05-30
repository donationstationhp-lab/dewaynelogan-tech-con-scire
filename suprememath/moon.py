"""Moon-phase utility. 8 phases (sealed: not 4).

Doctrinal note (from Lunar Cycle Learning Thread,
Notion 35603691-bd5e-81a3-a4d4-fa3b27ca0975):
  - The doctrinal cycle of this church is 28-day / 13-month lunar.
    That structure is known doctrinally but not yet walked operationally;
    reconciliation with the synodic 29.53-day period is an open task.
  - This module calculates the OUTER / ASTRONOMICAL synodic cycle only.
    It is not a substitute for the doctrinal calendar.
  - Moon phases are NOT mapped to Supreme Mathematics positions here.
    That mapping is reserved for lineage-trained Stewards.
  - Superseding source: fivepercenterlessons.com/moon-phases/
    (confirmed by the Founder 2026-05-04)

No external dependencies.
"""

from __future__ import annotations
import datetime
import math

# Reference new moon: 2000-01-06 18:14 UTC (sealed)
_KNOWN_NEW_MOON_UTC = datetime.datetime(2000, 1, 6, 18, 14, 0,
                                        tzinfo=datetime.timezone.utc)
_SYNODIC_DAYS = 29.530588853

# 8 phases — sealed from fivepercenterlessons.com/moon-phases/
# "Last Quarter" is "Third Quarter" per the doctrine.
_PHASES = [
    (0.0625,  "New",              "🌑"),
    (0.1875,  "Waxing Crescent",  "🌒"),
    (0.3125,  "First Quarter",    "🌓"),
    (0.4375,  "Waxing Gibbous",   "🌔"),
    (0.5625,  "Full",             "🌕"),
    (0.6875,  "Waning Gibbous",   "🌖"),
    (0.8125,  "Third Quarter",    "🌗"),   # doctrinal name; not "Last Quarter"
    (0.9375,  "Waning Crescent",  "🌘"),
    (1.0,     "New",              "🌑"),
]

_DOCTRINAL_NOTE = (
    "outer/astronomical synodic calc only; "
    "doctrinal: 28-day/13-month, held-in-study; "
    "source: fivepercenterlessons.com/moon-phases/"
)


def moon_phase(when: datetime.date | datetime.datetime) -> dict:
    """
    Return the approximate moon phase for a given date or datetime.

    Keys: phase, emoji, illumination_pct, phase_fraction,
          days_to_full, note (doctrinal caveat)

    This is the outer/astronomical synodic reading only.
    SM position mapping is not performed here.
    """
    if isinstance(when, datetime.datetime):
        dt_utc = (when.replace(tzinfo=datetime.timezone.utc)
                  if when.tzinfo is None
                  else when.astimezone(datetime.timezone.utc))
    else:
        dt_utc = datetime.datetime(when.year, when.month, when.day,
                                   tzinfo=datetime.timezone.utc)

    elapsed = (dt_utc - _KNOWN_NEW_MOON_UTC).total_seconds() / 86400.0
    age = (elapsed % _SYNODIC_DAYS + _SYNODIC_DAYS) % _SYNODIC_DAYS
    frac = age / _SYNODIC_DAYS

    for threshold, name, emoji in _PHASES:
        if frac < threshold:
            break

    illum = round(50.0 * (1.0 - math.cos(2.0 * math.pi * frac)), 1)
    days_to_full = (_SYNODIC_DAYS / 2 - age + _SYNODIC_DAYS) % _SYNODIC_DAYS

    return {
        "phase":           name,
        "emoji":           emoji,
        "illumination_pct": illum,
        "phase_fraction":  round(frac, 4),
        "days_to_full":    round(days_to_full, 2),
        "note":            _DOCTRINAL_NOTE,
    }
