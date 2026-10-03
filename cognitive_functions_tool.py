"""cognitive_functions_tool.py — Claude tool-use wrapper for cognitive_functions.py

Exposes the four-layer cognitive function framework as Anthropic Messages API
tool definitions (TOOLS) plus a dispatch() function.

Layers:
  process  — 18 mental operations
  values   — 5 core values
  stages   — 16 self-determination stages with etymologies
  domains  — 6 mathematical/logical domains
"""

import cognitive_functions as cf

_data = cf.load()

TOOLS = [
    {
        "name": "cognitive_function_lookup",
        "description": (
            "Look up a cognitive function by name or number across all four "
            "layers: process operations (1–18), core values, self-determination "
            "stages (1–16 with etymologies), and mathematical/logical domains. "
            "Returns all matching entries with their category, number/id, name, "
            "and etymology where applicable."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "description": (
                        "A name fragment (e.g. 'focusing', 'neophyte', 'integrity', 'logic') "
                        "or a number (1–18 for process, 1–16 for stages, 1–6 for domains/values)."
                    ),
                    "oneOf": [
                        {"type": "string", "minLength": 1},
                        {"type": "integer", "minimum": 1},
                    ],
                },
                "category": {
                    "description": "Limit search to one layer: 'process', 'values', 'stages', or 'domains'.",
                    "type": "string",
                    "enum": ["process", "values", "stages", "domains"],
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "cognitive_function_list",
        "description": (
            "List all cognitive function entries, optionally filtered to one "
            "layer: process (18 mental operations), values (5 core values), "
            "stages (16 self-determination stages with etymologies), or "
            "domains (6 mathematical/logical domains)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "description": "Layer to list. Omit to return all four layers.",
                    "type": "string",
                    "enum": ["process", "values", "stages", "domains"],
                },
            },
        },
    },
]


class ToolError(Exception):
    pass


def _cognitive_function_lookup(tool_input):
    query = tool_input.get("query")
    if query is None:
        raise ToolError("`query` is required.")
    results = cf.lookup(_data, query)
    category = tool_input.get("category")
    if category:
        results = [(c, e) for c, e in results if c == category]
    if not results:
        raise ToolError(
            f"No match for {query!r}"
            + (f" in category '{category}'" if category else "")
            + ". Try a different name or number."
        )
    return [{"category": c, "entry": e} for c, e in results]


def _cognitive_function_list(tool_input):
    category = tool_input.get("category")
    if category:
        return {category: cf._items(_data, category)}
    return {
        cat: cf._items(_data, cat)
        for cat in cf.CATEGORIES
    }


_HANDLERS = {
    "cognitive_function_lookup": _cognitive_function_lookup,
    "cognitive_function_list":   _cognitive_function_list,
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
