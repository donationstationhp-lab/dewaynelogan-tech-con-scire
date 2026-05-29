"""
Push a daily Supreme Mathematics reading to Notion.

Required env vars:
  NOTION_TOKEN        — Notion integration token (secret_...)
  NOTION_PARENT_ID    — ID of the parent page to write into
                        (defaults to the Daily Mathematics Journal page)

The page format mirrors the hand-written daily entries already in the journal.
"""

from __future__ import annotations
import os
import datetime
from typing import Any

import requests

_NOTION_VERSION = "2022-06-28"
_API_BASE = "https://api.notion.com/v1"

# ID of "📅 Daily Mathematics Journal" — override with NOTION_PARENT_ID env var
_DEFAULT_PARENT_ID = "a49dfa85e41846e79080b811b9b21f3b"


# ── Block helpers ─────────────────────────────────────────────────────────────

def _rt(text: str, bold: bool = False) -> dict:
    ann = {"bold": bold} if bold else {}
    return {"type": "text", "text": {"content": text}, "annotations": ann}


def _h2(text: str) -> dict:
    return {"type": "heading_2", "heading_2": {"rich_text": [_rt(text)]}}


def _h3(text: str) -> dict:
    return {"type": "heading_3", "heading_3": {"rich_text": [_rt(text)]}}


def _bullet(text: str) -> dict:
    return {"type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [_rt(text)]}}


def _todo(text: str) -> dict:
    return {"type": "to_do", "to_do": {"rich_text": [_rt(text)], "checked": False}}


def _para(text: str, bold: bool = False) -> dict:
    return {"type": "paragraph", "paragraph": {"rich_text": [_rt(text, bold=bold)]}}


def _divider() -> dict:
    return {"type": "divider", "divider": {}}


# ── Page builder ──────────────────────────────────────────────────────────────

def _build_blocks(reading: dict[str, Any]) -> list[dict]:
    date_str  = reading["date"]
    calc_str  = reading["calculation"]
    cipher    = reading["cipher"]
    attention = reading["attention"]
    intention = reading["intention"]
    purpose   = reading["purpose"]
    moon      = reading["moon"]
    onion     = reading["onion_instruction"]
    year      = datetime.date.fromisoformat(date_str).year
    day       = datetime.date.fromisoformat(date_str).day
    month     = datetime.date.fromisoformat(date_str).month

    a_kw = attention["key_words"][0] if attention.get("key_words") else ""
    i_kw = intention["key_words"][0] if intention.get("key_words") else ""
    p_kw = purpose["key_words"][0]   if purpose.get("key_words")   else ""

    return [
        _h2("📊 Consciousness Calculation"),
        _bullet(f"Full Date: {date_str}"),
        _bullet(f"Calculation: {calc_str}"),
        _bullet(
            f"Date Vibration: {cipher['number']} = {cipher['name']}"
            + (f" ({a_kw.title()})" if a_kw else "")
        ),
        _divider(),
        _h2(f"🧅 Onion Instruction ({year})"),
        _para(onion, bold=True),
        _h3("Component Decode"),
        _bullet(
            f"Attention (Day {day}): "
            f"{attention['number']} = {attention['name']}"
            + (f" — {a_kw}" if a_kw else "")
        ),
        _bullet(
            f"Intention (Month {month}): "
            f"{intention['number']} = {intention['name']}"
            + (f" — {i_kw}" if i_kw else "")
        ),
        _bullet(
            f"Purpose (Year {year}): "
            f"{purpose['number']} = {purpose['name']}"
            + (f" — {p_kw}" if p_kw else "")
        ),
        _divider(),
        _h2("🌙 Moon Phase"),
        _bullet(
            f"{moon['emoji']} {moon['phase']} "
            f"({moon['illumination_pct']}% illuminated)"
        ),
        _divider(),
        _h2("📌 Planner (Inked Commitments)"),
        _todo("1 clear priority for the day (what must be real by tonight?)"),
        _todo("1 call or message that creates alignment"),
        _todo("1 system clean-up or proof-of-work artifact"),
        _divider(),
        _h2("📝 Reflections"),
        _para(""),
        _h2("🌱 Manifestations"),
        _para(""),
        _h2("👁️ Observations"),
        _para(""),
        _h2("📸 Daily Visual Documentation"),
        _para(
            "Upload images of today's whiteboard + proof of what got completed."
        ),
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def push(reading: dict[str, Any], token: str | None = None,
         parent_id: str | None = None) -> str:
    """
    Create a daily-entry page in Notion and return the new page URL.

    Args:
        reading:   dict returned by compute_daily()
        token:     Notion integration token; falls back to NOTION_TOKEN env var
        parent_id: Notion page ID for the parent page;
                   falls back to NOTION_PARENT_ID env var, then the default journal ID

    Raises:
        EnvironmentError: if no token is available
        requests.HTTPError: if the Notion API call fails
    """
    token = token or os.environ.get("NOTION_TOKEN", "")
    if not token:
        raise EnvironmentError(
            "No Notion token found. Set the NOTION_PARENT_ID env var or pass token=."
        )

    parent_id = (
        parent_id
        or os.environ.get("NOTION_PARENT_ID", "")
        or _DEFAULT_PARENT_ID
    )

    date = datetime.date.fromisoformat(reading["date"])
    title = date.strftime("%B %-d, %Y")  # e.g. "May 29, 2026"

    payload = {
        "parent": {"page_id": parent_id},
        "icon": {"type": "emoji", "emoji": "📐"},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        },
        "children": _build_blocks(reading),
    }

    resp = requests.post(
        f"{_API_BASE}/pages",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": _NOTION_VERSION,
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    resp.raise_for_status()
    page_id = resp.json()["id"].replace("-", "")
    return f"https://www.notion.so/{page_id}"
