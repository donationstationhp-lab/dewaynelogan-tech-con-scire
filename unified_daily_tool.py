"""unified_daily_tool.py — Claude tool-use wrapper for unified_daily.py

Exposes the unified daily reading (SM + cognitive functions + AXIOM bridge)
as an Anthropic Messages API tool definition plus a dispatch() function.
"""

import datetime
import unified_daily as ud
from suprememath import Lexicon, DEFAULT_LEXICON_PATH

TOOLS = [
    {
        "name": "unified_daily_reading",
        "description": (
            "Compute the full unified daily reading for a date and hour: "
            "Supreme Mathematics Fraction Calendar (primary frame), "
            "secondary Method B lens, cognitive process functions activated "
            "by today's purpose position, mathematical domain in frame, "
            "core value governing the day, self-determination stage "
            "(16-day cycle), and optional AXIOM organizational health at "
            "the governing dimension."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date as YYYY-MM-DD. Defaults to today.",
                },
                "hour": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 23,
                    "description": "Hour 0-23. Defaults to current hour.",
                },
                "assessment_path": {
                    "type": "string",
                    "description": "Path to an AXIOM assessment JSON file to include organizational health.",
                },
            },
        },
    },
]


class ToolError(Exception):
    pass


def _unified_daily_reading(tool_input):
    now = datetime.datetime.now()

    date_str = tool_input.get("date")
    if date_str:
        try:
            d = datetime.date.fromisoformat(date_str)
        except ValueError:
            raise ToolError(f"Invalid `date` {date_str!r}; use YYYY-MM-DD.")
    else:
        d = now.date()

    hour = tool_input.get("hour", now.hour)
    if not isinstance(hour, int) or isinstance(hour, bool) or not (0 <= hour <= 23):
        raise ToolError("`hour` must be an integer 0-23.")

    dt = datetime.datetime(d.year, d.month, d.day, hour, now.minute)
    lexicon = Lexicon(DEFAULT_LEXICON_PATH)

    return ud.compute_unified(
        dt,
        lexicon=lexicon,
        assessment_path=tool_input.get("assessment_path"),
    )


_HANDLERS = {
    "unified_daily_reading": _unified_daily_reading,
}


def dispatch(name, tool_input):
    """
    Run the tool named `name` with Claude's parsed tool_input dict.

    Returns {"is_error": False, "content": <result>} on success,
    or {"is_error": True, "content": "<message>"} on failure.
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"is_error": True, "content": f"Unknown tool: {name!r}"}
    try:
        return {"is_error": False, "content": handler(tool_input or {})}
    except ToolError as exc:
        return {"is_error": True, "content": str(exc)}
    except Exception as exc:
        return {"is_error": True, "content": f"Error: {exc}"}
