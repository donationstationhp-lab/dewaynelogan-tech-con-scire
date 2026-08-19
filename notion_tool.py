"""notion_tool.py — Claude tool-use wrapper for notion.py

Exposes the generic Notion save helpers (used by etymonline entries and
elsewhere) as Anthropic Messages API tool definitions (TOOLS) plus a
dispatch() function. Requires the NOTION_TOKEN and NOTION_DATABASE_ID
environment variables — see notion.py's module docstring for the
expected database schema.
"""

import requests

import notion as nt

TOOLS = [
    {
        "name": "notion_save_entry",
        "description": (
            "Save a single word/etymology entry as a new row in the "
            "configured Notion database. Requires the NOTION_TOKEN and "
            "NOTION_DATABASE_ID environment variables."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "word": {"type": "string"},
                "etymology": {"type": "string", "default": ""},
                "related": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Related words, saved as a comma-separated list (first 10 used).",
                },
            },
            "required": ["word"],
        },
    },
    {
        "name": "notion_save_entries",
        "description": (
            "Save a batch of word/etymology entries as new rows in the "
            "configured Notion database, one row per entry. Requires the "
            "NOTION_TOKEN and NOTION_DATABASE_ID environment variables."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "word": {"type": "string"},
                            "etymology": {"type": "string", "default": ""},
                        },
                        "required": ["word"],
                    },
                    "minItems": 1,
                },
                "related": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Related words applied to every saved entry (first 10 used).",
                },
            },
            "required": ["entries"],
        },
    },
]


class ToolError(Exception):
    """A tool_input validation error, reported back to the caller (not raised)."""


def _notion_save_entry(tool_input):
    word = (tool_input.get("word") or "").strip()
    if not word:
        raise ToolError("`word` is required and must be a non-empty string.")
    resp = nt.save_entry(
        word,
        tool_input.get("etymology", ""),
        related=tool_input.get("related"),
    )
    return {"saved": True, "notion_page_id": resp.get("id")}


def _notion_save_entries(tool_input):
    entries = tool_input.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ToolError("`entries` is required and must be a non-empty list.")
    for entry in entries:
        if not isinstance(entry, dict) or not (entry.get("word") or "").strip():
            raise ToolError("Every entry must be an object with a non-empty `word`.")
    saved = nt.save_entries(entries, related=tool_input.get("related"))
    return {"saved": saved}


_HANDLERS = {
    "notion_save_entry": _notion_save_entry,
    "notion_save_entries": _notion_save_entries,
}


def dispatch(name, tool_input):
    """
    Run the tool named `name` with Claude's parsed tool_input dict.

    Returns {"is_error": False, "content": <json-serializable result>} on
    success, or {"is_error": True, "content": "<message>"} on failure.
    Missing Notion credentials (EnvironmentError) and Notion API failures
    (requests.HTTPError) are caught and reported as error results.
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"is_error": True, "content": f"Unknown tool: {name!r}"}

    try:
        return {"is_error": False, "content": handler(tool_input or {})}
    except ToolError as exc:
        return {"is_error": True, "content": str(exc)}
    except requests.HTTPError as exc:
        # Must be checked before EnvironmentError: requests exceptions
        # subclass OSError/EnvironmentError, so the broader clause would
        # otherwise swallow HTTP failures before they reach this branch.
        return {"is_error": True, "content": f"Notion error: {exc}"}
    except EnvironmentError as exc:
        return {"is_error": True, "content": str(exc)}
