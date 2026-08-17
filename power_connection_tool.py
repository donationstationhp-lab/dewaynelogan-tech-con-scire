"""power_connection_tool.py — Claude tool-use wrapper for power_connection.py

Exposes the numerological date calculator (root / path one / path two /
born, plus marking dates) as Anthropic Messages API tool definitions
(TOOLS) and a dispatch() function.
"""

import power_connection as pc

TOOLS = [
    {
        "name": "power_connection_calculate",
        "description": (
            "Run the Power Connection numerological calculation for a "
            "month/day/year: the Root (month expressed through day), Path "
            "One (root + year as whole numbers) and Path Two (every digit "
            "summed individually), and the final 'born' number with its "
            "directive interpretation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "integer", "minimum": 1, "maximum": 12},
                "day": {"type": "integer", "minimum": 1, "maximum": 31},
                "year": {"type": "integer", "minimum": 1},
            },
            "required": ["month", "day", "year"],
        },
    },
    {
        "name": "power_connection_mark_date",
        "description": (
            "Calculate a date's Power Connection result and save it as a "
            "marked date (persisted locally) with an optional note, for "
            "later recall via power_connection_list_marks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "integer", "minimum": 1, "maximum": 12},
                "day": {"type": "integer", "minimum": 1, "maximum": 31},
                "year": {"type": "integer", "minimum": 1},
                "note": {
                    "type": "string",
                    "description": "Optional note describing why this date was marked.",
                    "default": "",
                },
            },
            "required": ["month", "day", "year"],
        },
    },
    {
        "name": "power_connection_list_marks",
        "description": "List every previously marked date, with its root, born number, and note.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


class ToolError(Exception):
    """A tool_input validation error, reported back to the caller (not raised)."""


def _validate_mdy(tool_input):
    month, day, year = tool_input.get("month"), tool_input.get("day"), tool_input.get("year")
    for name, value in (("month", month), ("day", day), ("year", year)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ToolError(f"`{name}` is required and must be an integer.")
    if not (1 <= month <= 12):
        raise ToolError("`month` must be between 1 and 12.")
    if not (1 <= day <= 31):
        raise ToolError("`day` must be between 1 and 31.")
    if year < 1:
        raise ToolError("`year` must be a positive integer.")
    return month, day, year


def _power_connection_calculate(tool_input):
    month, day, year = _validate_mdy(tool_input)
    return pc.calculate(month, day, year)


def _power_connection_mark_date(tool_input):
    month, day, year = _validate_mdy(tool_input)
    note = tool_input.get("note", "")
    entry, result = pc.mark_date(month, day, year, note)
    return {"mark": entry, "result": result}


def _power_connection_list_marks(tool_input):
    return {"marks": pc.marks_load()}


_HANDLERS = {
    "power_connection_calculate": _power_connection_calculate,
    "power_connection_mark_date": _power_connection_mark_date,
    "power_connection_list_marks": _power_connection_list_marks,
}


def dispatch(name, tool_input):
    """
    Run the tool named `name` with Claude's parsed tool_input dict.

    Returns {"is_error": False, "content": <json-serializable result>} on
    success, or {"is_error": True, "content": "<message>"} on failure.
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"is_error": True, "content": f"Unknown tool: {name!r}"}

    try:
        return {"is_error": False, "content": handler(tool_input or {})}
    except ToolError as exc:
        return {"is_error": True, "content": str(exc)}
    except OSError as exc:
        return {"is_error": True, "content": f"Could not save mark: {exc}"}
