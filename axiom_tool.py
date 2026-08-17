"""axiom_tool.py — Claude tool-use wrapper for axiom.py

Exposes AXIOM's ten-dimension Decinary diagnostic as Anthropic Messages
API tool definitions (TOOLS) plus a dispatch() function, so a Claude
agent can drive the assessment through tool_use content blocks instead
of the interactive CLI prompt loop.

The CLI's `run_assessment()` is interactive (30 stdin prompts) and has
no tool-shaped equivalent; the wrapper instead accepts scores an agent
has already gathered (e.g. by asking the user each sub-question itself)
and hands them to axiom.py's scoring/report functions directly.
"""

import axiom as ax

_DIMENSIONS_BY_POSITION = {d["position"]: d for d in ax.DIMENSIONS}

TOOLS = [
    {
        "name": "axiom_get_dimensions",
        "description": (
            "List AXIOM's ten Decinary diagnostic dimensions (positions "
            "0-9), each with its name, theme, and the three 1-10 "
            "sub-questions used to score it. Call this before "
            "axiom_score_assessment to see what to ask the user."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "axiom_score_assessment",
        "description": (
            "Score an AXIOM assessment for an organization from "
            "already-collected 1-10 sub-question answers (one triple of "
            "scores per dimension). Returns each dimension's average and "
            "level, the overall aggregate score/level, and the "
            "lowest-scoring dimension (top gap) to prioritize."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "organization": {
                    "type": "string",
                    "description": "Name of the organization being assessed.",
                },
                "dimension_scores": {
                    "type": "array",
                    "description": (
                        "One entry per dimension — all 10 positions 0-9, "
                        "each exactly once — with its three 1-10 sub-scores."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "position": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 9,
                            },
                            "scores": {
                                "type": "array",
                                "items": {
                                    "type": "number",
                                    "minimum": 1,
                                    "maximum": 10,
                                },
                                "minItems": 3,
                                "maxItems": 3,
                            },
                        },
                        "required": ["position", "scores"],
                    },
                    "minItems": 10,
                    "maxItems": 10,
                },
                "save": {
                    "type": "boolean",
                    "description": "Write the report as a JSON file under assessments/.",
                    "default": False,
                },
            },
            "required": ["organization", "dimension_scores"],
        },
    },
]


class ToolError(Exception):
    """A tool_input validation error, reported back to the caller (not raised)."""


def _is_plain_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _axiom_get_dimensions(tool_input):
    return {"dimensions": ax.DIMENSIONS}


def _axiom_score_assessment(tool_input):
    org = (tool_input.get("organization") or "").strip()
    if not org:
        raise ToolError("`organization` is required and must be a non-empty string.")

    entries = tool_input.get("dimension_scores")
    if not isinstance(entries, list) or len(entries) != 10:
        raise ToolError("`dimension_scores` must contain exactly 10 entries, one per dimension.")

    seen_positions = set()
    results = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ToolError("Each `dimension_scores` entry must be an object with `position` and `scores`.")

        position = entry.get("position")
        if isinstance(position, bool) or position not in _DIMENSIONS_BY_POSITION:
            raise ToolError(f"Invalid `position` {position!r}; must be an integer 0-9.")
        if position in seen_positions:
            raise ToolError(f"Duplicate `position` {position} in `dimension_scores`.")
        seen_positions.add(position)

        scores = entry.get("scores")
        if not isinstance(scores, list) or len(scores) != 3:
            raise ToolError(f"Position {position}: `scores` must be a list of exactly 3 numbers.")
        for s in scores:
            if not _is_plain_number(s) or not (1 <= s <= 10):
                raise ToolError(f"Position {position}: each score must be a number between 1 and 10.")

        dim = _DIMENSIONS_BY_POSITION[position]
        avg = ax.calculate_position_score(scores)
        results.append({
            "position": position,
            "name": dim["name"],
            "scores": scores,
            "average": avg,
            "level": ax.get_category(avg),
        })

    results.sort(key=lambda r: r["position"])
    report = ax.build_report(org, results)

    if tool_input.get("save"):
        report["saved_to"] = ax.write_report(report, "assessments")

    return report


_HANDLERS = {
    "axiom_get_dimensions": _axiom_get_dimensions,
    "axiom_score_assessment": _axiom_score_assessment,
}


def dispatch(name, tool_input):
    """
    Run the tool named `name` with Claude's parsed tool_input dict.

    Returns {"is_error": False, "content": <json-serializable result>} on
    success, or {"is_error": True, "content": "<message>"} on failure.
    Never raises: unknown tools, bad input, and filesystem failures while
    saving a report are all caught and reported as an error result.
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"is_error": True, "content": f"Unknown tool: {name!r}"}

    try:
        return {"is_error": False, "content": handler(tool_input or {})}
    except ToolError as exc:
        return {"is_error": True, "content": str(exc)}
    except OSError as exc:
        return {"is_error": True, "content": f"Could not write report: {exc}"}
