"""look_ahead_tool.py — Claude tool-use wrapper for look_ahead.py

Exposes the convergence window finder as an Anthropic Messages API tool
definition plus a dispatch() function.
"""

import datetime
import look_ahead as la
from suprememath import Lexicon, DEFAULT_LEXICON_PATH

TOOLS = [
    {
        "name": "look_ahead",
        "description": (
            "Scan forward N days to find dates matching specific cognitive/SM criteria: "
            "SM purpose position (1-9), self-determination stage (1-16), "
            "✦ aligned days (convergence = 6 · Equality), "
            "◈ triple alignments (purpose position = stage number), "
            "domain in frame, or governing value. "
            "Returns a list of matching dates each with full cognitive frame."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Start date as YYYY-MM-DD. Defaults to today.",
                },
                "days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 365,
                    "description": "Days to scan forward. Default 30.",
                },
                "purpose": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 9,
                    "description": "Return only days governed by this SM purpose position.",
                },
                "stage": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 16,
                    "description": "Return only days in this self-determination stage.",
                },
                "aligned": {
                    "type": "boolean",
                    "description": "If true, return only ✦ aligned days (convergence = 6).",
                },
                "triple": {
                    "type": "boolean",
                    "description": "If true, return only ◈ triple days (purpose position = stage number).",
                },
                "domain": {
                    "type": "string",
                    "description": "Filter by domain name — partial match (e.g. 'logic', 'relationships').",
                },
                "value": {
                    "type": "string",
                    "description": "Filter by value name — partial match (e.g. 'dignity', 'integrity').",
                },
            },
        },
    },
]


class ToolError(Exception):
    pass


def _look_ahead(tool_input):
    date_str = tool_input.get("date")
    if date_str:
        try:
            start_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            raise ToolError(f"Invalid `date` {date_str!r}; use YYYY-MM-DD.")
    else:
        start_date = datetime.date.today()

    days = tool_input.get("days", 30)
    if not isinstance(days, int) or isinstance(days, bool) or not (1 <= days <= 365):
        raise ToolError("`days` must be an integer 1-365.")

    purpose = tool_input.get("purpose")
    if purpose is not None and not (1 <= purpose <= 9):
        raise ToolError("`purpose` must be 1-9.")

    stage = tool_input.get("stage")
    if stage is not None and not (1 <= stage <= 16):
        raise ToolError("`stage` must be 1-16.")

    filters = {
        "purpose": purpose,
        "stage":   stage,
        "aligned": tool_input.get("aligned", False),
        "triple":  tool_input.get("triple", False),
        "domain":  tool_input.get("domain"),
        "value":   tool_input.get("value"),
    }

    lexicon = Lexicon(DEFAULT_LEXICON_PATH)
    return la.scan(start_date, days, filters, lexicon)


_HANDLERS = {
    "look_ahead": _look_ahead,
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
