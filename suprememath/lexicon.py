"""Loads and queries the editable Supreme Mathematics position lexicon."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any


class Lexicon:
    """
    Thin wrapper around sm_lexicon.json.
    All meaning lives in the data file — this class only loads and indexes.
    """

    def __init__(self, path: str | Path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self._positions: dict[int, dict[str, Any]] = {
            int(k): v for k, v in data["positions"].items()
        }
        self._labels: dict[str, str] = data.get("reading_labels", {})
        self._raw = data

    # ── Position queries ──────────────────────────────────────────────────────

    def get(self, n: int) -> dict[str, Any]:
        """Return the full position dict for digit n (0–9)."""
        if n not in self._positions:
            raise KeyError(f"No lexicon entry for position {n}")
        return dict(self._positions[n])

    def name(self, n: int) -> str:
        return self._positions[n]["name"]

    def pie_root(self, n: int) -> str:
        return self._positions[n].get("pie_root", "")

    def verb(self, n: int) -> str:
        """Sealed verb of reception for this seat (e.g. 'gained', 'given')."""
        return self._positions[n].get("verb", "")

    def say(self, n: int) -> str:
        """Brief sealed instruction for this seat."""
        return self._positions[n].get("say", "")

    def instruction(self, n: int) -> str:
        """Alias for say()."""
        return self.say(n)

    # ── Reading labels ────────────────────────────────────────────────────────

    @property
    def label_attention(self) -> str:
        return self._labels.get("attention", "Attention")

    @property
    def label_intention(self) -> str:
        return self._labels.get("intention", "Intention")

    @property
    def label_purpose(self) -> str:
        return self._labels.get("purpose", "Purpose")

    @property
    def label_convergence(self) -> str:
        return self._labels.get("convergence", "Convergence")

    @property
    def label_cipher(self) -> str:
        return self._labels.get("cipher", "Date Vibration")

    def label(self, key: str) -> str:
        return self._labels.get(key, key.replace("_", " ").title())

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def positions(self) -> dict[int, dict[str, Any]]:
        return dict(self._positions)

    def __repr__(self) -> str:
        return f"Lexicon({len(self._positions)} positions)"
