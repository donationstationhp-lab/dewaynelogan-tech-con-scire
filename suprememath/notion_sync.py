"""
Push a daily Supreme Mathematics reading to Notion.

Required env vars:
  NOTION_TOKEN        — Notion integration token (secret_...)
  NOTION_PARENT_ID    — ID of the parent page to write into
                        (defaults to the Daily Mathematics Journal page)

Sources of record:
  Fraction Calendar — Notion 46e0a67b-a3dd-494f-ac5c-1cec071123ca
  Lunar Thread      — Notion 35603691-bd5e-81a3-a4d4-fa3b27ca0975
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
    attention = reading["attention"]
    intention = reading["intention"]
    purpose   = reading["purpose"]
    secondary = reading["secondary"]
    year_arc  = reading["year_arc"]
    moon      = reading["moon"]
    mths      = reading["methods"]
    calc      = reading["calculation"]
    srcs      = reading["sources"]

    date_obj  = datetime.date.fromisoformat(date_str)
    year      = date_obj.year

    sec_att  = secondary["attention"]
    sec_h    = secondary["hour"]
    sec_pur  = secondary["purpose"]
    sec_conv = secondary["convergence"]

    def _compound(seat: dict) -> str:
        if seat.get("compound"):
            return f"  [compound: {seat['raw']} → {seat['number']}]"
        return ""

    return [
        # ── Fraction Calendar (primary) ───────────────────────────────────────
        _h2("Fraction Calendar  ·  Received · Gained · Given"),
        _bullet(srcs["fraction_calendar"]["name"]),
        _divider(),
        _para(attention["liturgy"], bold=True),
        _bullet(
            f"{attention['number']}  {attention['name']}"
            + _compound(attention)
        ),
        _bullet(attention.get("pie_root", "")),
        _para(intention["liturgy"], bold=True),
        _bullet(
            f"{intention['number']}  {intention['name']}"
            + _compound(intention)
        ),
        _bullet(intention.get("pie_root", "")),
        _para(purpose["liturgy"], bold=True),
        _bullet(
            f"{purpose['number']}  {purpose['name']}"
            + _compound(purpose)
        ),
        _bullet(purpose.get("pie_root", "")),
        _divider(),
        # ── Secondary lens ────────────────────────────────────────────────────
        _h2("Secondary Lens  ·  Method B + 12-hour clock"),
        _bullet(f"Method A (address):  {mths['a']}"),
        _bullet(f"Method B (YYYYMMDD): {mths['b']}  {sec_att['name']}"),
        _bullet(f"Method C (M+D+Y):    {mths['c']}"),
        _bullet(f"Cipher: {calc}"),
        _bullet(
            f"Hour → h12={sec_h['h12']}:  "
            f"{sec_h['number']}  {sec_h['name']}"
        ),
        _bullet(
            f"Cipher purpose:  "
            f"{sec_pur['number']}  {sec_pur['name']}"
        ),
        _bullet(
            f"Convergence:  "
            f"{sec_conv['number']}  {sec_conv['name']}"
            + ("  ← aligned" if sec_conv["aligned"] else "")
        ),
        _divider(),
        # ── Moon ──────────────────────────────────────────────────────────────
        _h2("Moon"),
        _bullet(
            f"{moon['emoji']} {moon['phase']} "
            f"({moon['illumination_pct']}% illuminated, "
            f"{round(moon['days_to_full'], 1)} days to full)"
        ),
        _bullet(moon.get("note", "")),
        _divider(),
        # ── Year arc ──────────────────────────────────────────────────────────
        _h2(f"Year Arc  ·  {year}"),
        _bullet(
            f"{year_arc['number']}  {year_arc['name']} — {year_arc.get('pie_root', '')}"
        ),
        _divider(),
        # ── Sources ───────────────────────────────────────────────────────────
        _h2("Sources"),
        _bullet(srcs["fraction_calendar"]["name"]),
        _bullet(srcs["lunar_thread"]["name"]),
        _divider(),
        # ── Planner / Journal ─────────────────────────────────────────────────
        _h2("Planner (Inked Commitments)"),
        _todo("1 clear priority for the day (what must be real by tonight?)"),
        _todo("1 call or message that creates alignment"),
        _todo("1 system clean-up or proof-of-work artifact"),
        _divider(),
        _h2("Reflections"),
        _para(""),
        _h2("Manifestations"),
        _para(""),
        _h2("Observations"),
        _para(""),
        _h2("Daily Visual Documentation"),
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
            "No Notion token found. Set the NOTION_TOKEN env var or pass token=."
        )

    parent_id = (
        parent_id
        or os.environ.get("NOTION_PARENT_ID", "")
        or _DEFAULT_PARENT_ID
    )

    date  = datetime.date.fromisoformat(reading["date"])
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
