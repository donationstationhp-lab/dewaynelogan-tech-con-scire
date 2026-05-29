"""Moon-phase utility. 8 phases (sealed: not 4). No external dependencies."""

from __future__ import annotations
import datetime
import math

# Reference new moon: 2000-01-06 18:14 UTC (sealed)
_KNOWN_NEW_MOON_UTC = datetime.datetime(2000, 1, 6, 18, 14, 0,
                                        tzinfo=datetime.timezone.utc)
_SYNODIC_DAYS = 29.530588853

# 8 phases (from fivepercenterlessons.com; sealed)
_PHASES = [
    (0.0625,  "New",              "🌑"),
    (0.1875,  "Waxing Crescent",  "🌒"),
    (0.3125,  "First Quarter",    "🌓"),
    (0.4375,  "Waxing Gibbous",   "🌔"),
    (0.5625,  "Full",             "🌕"),
    (0.6875,  "Waning Gibbous",   "🌖"),
    (0.8125,  "Last Quarter",     "🌗"),
    (0.9375,  "Waning Crescent",  "🌘"),
    (1.0,     "New",              "🌑"),
]


def moon_phase(when: datetime.date | datetime.datetime) -> dict:
    """
    Return the approximate moon phase for a given date or datetime.

    Keys: phase (str), emoji (str), illumination_pct (float),
          phase_fraction (float), days_to_full (float)
    """
    if isinstance(when, datetime.datetime):
        if when.tzinfo is None:
            dt_utc = when.replace(tzinfo=datetime.timezone.utc)
        else:
            dt_utc = when.astimezone(datetime.timezone.utc)
    else:
        dt_utc = datetime.datetime(when.year, when.month, when.day,
                                   tzinfo=datetime.timezone.utc)

    elapsed = (dt_utc - _KNOWN_NEW_MOON_UTC).total_seconds() / 86400.0
    age = (elapsed % _SYNODIC_DAYS + _SYNODIC_DAYS) % _SYNODIC_DAYS
    frac = age / _SYNODIC_DAYS  # 0.0 = new, 0.5 = full

    for threshold, name, emoji in _PHASES:
        if frac < threshold:
            break

    illum = round(50.0 * (1.0 - math.cos(2.0 * math.pi * frac)), 1)
    days_to_full = (_SYNODIC_DAYS / 2 - age + _SYNODIC_DAYS) % _SYNODIC_DAYS

    return {
        "phase": name,
        "emoji": emoji,
        "illumination_pct": illum,
        "phase_fraction": round(frac, 4),
        "days_to_full": round(days_to_full, 2),
    }
