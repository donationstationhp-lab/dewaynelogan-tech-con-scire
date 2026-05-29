"""Moon-phase utility using synodic period arithmetic. No external dependencies."""

from __future__ import annotations
import datetime
import math

# Reference new moon: January 6, 2000 (astronomically verified)
_KNOWN_NEW_MOON = datetime.date(2000, 1, 6)
_SYNODIC_DAYS = 29.530588853

_PHASES = [
    (0.0625,  "New Moon",        "🌑"),
    (0.1875,  "Waxing Crescent", "🌒"),
    (0.3125,  "First Quarter",   "🌓"),
    (0.4375,  "Waxing Gibbous",  "🌔"),
    (0.5625,  "Full Moon",       "🌕"),
    (0.6875,  "Waning Gibbous",  "🌖"),
    (0.8125,  "Last Quarter",    "🌗"),
    (0.9375,  "Waning Crescent", "🌘"),
    (1.0,     "New Moon",        "🌑"),
]


def moon_phase(date: datetime.date) -> dict:
    """
    Return the approximate moon phase for a given date.

    Keys: phase (str), emoji (str), illumination_pct (float), phase_fraction (float)
    """
    days_since = (date - _KNOWN_NEW_MOON).days
    frac = (days_since % _SYNODIC_DAYS) / _SYNODIC_DAYS  # 0.0 = new, 0.5 = full

    for threshold, name, emoji in _PHASES:
        if frac < threshold:
            break

    # Illumination: 0 % at new moon, 100 % at full moon
    illumination = round(50.0 * (1.0 - math.cos(2.0 * math.pi * frac)), 1)

    return {
        "phase": name,
        "emoji": emoji,
        "illumination_pct": illumination,
        "phase_fraction": round(frac, 4),
    }
