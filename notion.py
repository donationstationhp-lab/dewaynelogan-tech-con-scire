"""notion.py — save etymonline lookup results to a Notion database.

Required environment variables:
  NOTION_TOKEN        Your Notion integration secret (starts with "secret_")
  NOTION_DATABASE_ID  The ID of the target database (32-char hex or URL form)

The target database must have these properties (exact names, matching types):
  Word              Title
  Etymology         Text
  Related Words     Text
  Date Looked Up    Date

To create the integration and obtain a token:
  https://www.notion.so/my-integrations

To share your database with the integration, open the database in Notion,
click "..." → "Add connections" and select your integration.
"""

import datetime
import os

import requests

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Notion rich_text blocks cap out at 2 000 characters each.
_MAX_TEXT = 2000


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def get_credentials():
    """Read NOTION_TOKEN and NOTION_DATABASE_ID from the environment."""
    token = os.environ.get("NOTION_TOKEN", "").strip()
    db_id = os.environ.get("NOTION_DATABASE_ID", "").strip()
    if not token:
        raise EnvironmentError(
            "NOTION_TOKEN is not set. "
            "Export your Notion integration secret before using --notion."
        )
    if not db_id:
        raise EnvironmentError(
            "NOTION_DATABASE_ID is not set. "
            "Export the target database ID before using --notion."
        )
    return token, db_id


def save_entry(word, etymology, related=None, *, token=None, database_id=None):
    """Create one row in the Notion database for a single word.

    Returns the raw Notion API response dict.
    Raises requests.HTTPError on API errors.
    """
    if token is None or database_id is None:
        token, database_id = get_credentials()

    related_str = ", ".join(related[:10]) if related else ""
    etym_text = (etymology or "")[:_MAX_TEXT]

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Word": {
                "title": [{"text": {"content": word}}]
            },
            "Etymology": {
                "rich_text": [{"text": {"content": etym_text}}]
            },
            "Related Words": {
                "rich_text": [{"text": {"content": related_str}}]
            },
            "Date Looked Up": {
                "date": {"start": datetime.date.today().isoformat()}
            },
        },
    }

    resp = requests.post(
        f"{NOTION_API_URL}/pages",
        headers=_headers(token),
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def save_entries(entries, related=None, *, token=None, database_id=None):
    """Create one Notion row per entry dict in `entries`.

    Each entry dict must have at least a "word" key; "etymology" is optional.
    Returns the number of rows successfully created.
    """
    if token is None or database_id is None:
        token, database_id = get_credentials()

    saved = 0
    for entry in entries:
        word = (entry.get("word") or "").strip()
        if not word:
            continue
        etymology = entry.get("etymology", "")
        save_entry(word, etymology, related=related,
                   token=token, database_id=database_id)
        saved += 1
    return saved
