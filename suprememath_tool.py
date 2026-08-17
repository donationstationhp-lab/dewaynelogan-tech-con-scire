"""suprememath_tool.py — Claude tool-use wrapper for the suprememath package

Exposes the Supreme Mathematics daily-reading engine (Fraction Calendar
primary frame + Method B/12-hour secondary lens + moon phase) and its
optional Notion push as Anthropic Messages API tool definitions (TOOLS)
plus a dispatch() function.
"""

import datetime

import requests

from suprememath import Lexicon, compute_daily, DEFAULT_LEXICON_PATH

_DATE_PROP = {
    "type": "string",
    "description": "Date to read, as YYYY-MM-DD. Defaults to today.",
}
_HOUR_PROP = {
    "type": "integer",
    "description": "Hour 0-23 to read. Defaults to the current hour.",
    "minimum": 0,
    "maximum": 23,
}
_LEXICON_PROP = {
    "type": "string",
    "description": "Path to a custom lexicon JSON file. Defaults to the built-in lexicon.",
}

TOOLS = [
    {
        "name": "suprememath_daily_reading",
        "description": (
            "Compute the Supreme Mathematics reading for a date/hour: the "
            "primary Fraction Calendar frame (Attention/Intention/Purpose "
            "from month/day), the secondary Method B + 12-hour-clock lens, "
            "the year arc, moon phase, and the sealed A/B/C date-cipher "
            "methods."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": _DATE_PROP,
                "hour": _HOUR_PROP,
                "lexicon_path": _LEXICON_PROP,
            },
        },
    },
    {
        "name": "suprememath_push_to_notion",
        "description": (
            "Compute the Supreme Mathematics reading for a date/hour and "
            "push it as a new page to the Daily Mathematics Journal in "
            "Notion. Requires the NOTION_TOKEN environment variable (and "
            "optionally NOTION_PARENT_ID) to be set. Returns the reading "
            "plus the created page's URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": _DATE_PROP,
                "hour": _HOUR_PROP,
                "lexicon_path": _LEXICON_PROP,
                "parent_id": {
                    "type": "string",
                    "description": "Notion parent page ID to write into. Defaults to NOTION_PARENT_ID env var, then the Daily Mathematics Journal.",
                },
            },
        },
    },
]


class ToolError(Exception):
    """A tool_input validation error, reported back to the caller (not raised)."""


def _resolve_datetime(tool_input):
    now = datetime.datetime.now()

    date_str = tool_input.get("date")
    if date_str:
        try:
            d = datetime.date.fromisoformat(date_str)
        except ValueError:
            raise ToolError(f"Invalid `date` {date_str!r}; use YYYY-MM-DD format.")
    else:
        d = now.date()

    hour = tool_input.get("hour", now.hour)
    if isinstance(hour, bool) or not isinstance(hour, int) or not (0 <= hour <= 23):
        raise ToolError("`hour` must be an integer between 0 and 23.")

    return datetime.datetime(d.year, d.month, d.day, hour, now.minute)


def _load_lexicon(tool_input):
    path = tool_input.get("lexicon_path") or DEFAULT_LEXICON_PATH
    try:
        return Lexicon(path)
    except FileNotFoundError:
        raise ToolError(f"Lexicon file not found: {path}")


def _suprememath_daily_reading(tool_input):
    dt = _resolve_datetime(tool_input)
    lex = _load_lexicon(tool_input)
    return compute_daily(dt, lex)


def _suprememath_push_to_notion(tool_input):
    dt = _resolve_datetime(tool_input)
    lex = _load_lexicon(tool_input)
    reading = compute_daily(dt, lex)

    from suprememath.notion_sync import push
    url = push(reading, parent_id=tool_input.get("parent_id"))
    return {"reading": reading, "notion_url": url}


_HANDLERS = {
    "suprememath_daily_reading": _suprememath_daily_reading,
    "suprememath_push_to_notion": _suprememath_push_to_notion,
}


def dispatch(name, tool_input):
    """
    Run the tool named `name` with Claude's parsed tool_input dict.

    Returns {"is_error": False, "content": <json-serializable result>} on
    success, or {"is_error": True, "content": "<message>"} on failure.
    Missing Notion credentials and Notion API failures are caught and
    reported as error results rather than propagating.
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
