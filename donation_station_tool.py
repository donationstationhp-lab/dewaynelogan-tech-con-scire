"""donation_station_tool.py — Claude tool-use wrapper for donation_station.py

Exposes the donation lifecycle (intake -> qc -> storage -> distributed)
as Anthropic Messages API tool definitions (TOOLS) plus a dispatch()
function, one tool per stage transition plus status/list/report.
"""

import donation_station as ds

TOOLS = [
    {
        "name": "donation_station_intake",
        "description": "Log a newly donated item and start its lifecycle at the 'intake' stage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Item name, e.g. 'Winter Jacket'."},
                "category": {"type": "string", "default": "general"},
                "condition": {
                    "type": "string",
                    "enum": list(ds.CONDITIONS),
                    "default": "good",
                },
                "donor": {"type": "string", "default": ""},
                "notes": {"type": "string", "default": ""},
                "by": {"type": "string", "description": "Operator logging the intake.", "default": ""},
            },
            "required": ["name"],
        },
    },
    {
        "name": "donation_station_process_qc",
        "description": (
            "Record quality-control inspection results for an item currently at "
            "the 'intake' stage, advancing it to 'qc'. A failed inspection "
            "flags the item for maintenance and blocks it from being stored "
            "until a passing inspection is recorded."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "e.g. 'DS-0001'."},
                "passed": {"type": "boolean"},
                "by": {"type": "string", "default": ""},
                "notes": {"type": "string", "default": ""},
                "maintenance": {
                    "type": "string",
                    "description": "Maintenance needed, if `passed` is false.",
                    "default": "",
                },
            },
            "required": ["item_id", "passed"],
        },
    },
    {
        "name": "donation_station_store",
        "description": (
            "Assign an inventory location to an item that has passed QC, "
            "advancing it from 'qc' to 'storage'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "location": {"type": "string", "description": "e.g. 'B-3'."},
                "by": {"type": "string", "default": ""},
                "notes": {"type": "string", "default": ""},
            },
            "required": ["item_id", "location"],
        },
    },
    {
        "name": "donation_station_distribute",
        "description": "Send a stored item to its recipient, advancing it from 'storage' to 'distributed'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "recipient": {"type": "string"},
                "by": {"type": "string", "default": ""},
                "notes": {"type": "string", "default": ""},
            },
            "required": ["item_id", "recipient"],
        },
    },
    {
        "name": "donation_station_get_status",
        "description": "Get an item's current stage and full history by ID.",
        "input_schema": {
            "type": "object",
            "properties": {"item_id": {"type": "string"}},
            "required": ["item_id"],
        },
    },
    {
        "name": "donation_station_list_items",
        "description": "List donation items, optionally filtered to a single lifecycle stage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "enum": list(ds.STAGES) + ["all"],
                    "default": "all",
                },
            },
        },
    },
    {
        "name": "donation_station_report",
        "description": "Summarize all items: totals by stage, by category, and maintenance pending.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


class ToolError(Exception):
    """A tool_input validation error, reported back to the caller (not raised)."""


def _require_str(tool_input, key):
    value = (tool_input.get(key) or "").strip() if isinstance(tool_input.get(key), str) else ""
    if not value:
        raise ToolError(f"`{key}` is required and must be a non-empty string.")
    return value


def _donation_station_intake(tool_input):
    name = _require_str(tool_input, "name")
    condition = tool_input.get("condition", "good")
    if condition not in ds.CONDITIONS:
        raise ToolError(f"`condition` must be one of {list(ds.CONDITIONS)}.")
    return ds.intake(
        name,
        category=tool_input.get("category", "general"),
        condition=condition,
        donor=tool_input.get("donor", ""),
        notes=tool_input.get("notes", ""),
        by=tool_input.get("by", ""),
    )


def _donation_station_process_qc(tool_input):
    item_id = _require_str(tool_input, "item_id")
    passed = tool_input.get("passed")
    if not isinstance(passed, bool):
        raise ToolError("`passed` is required and must be a boolean.")
    return ds.process_qc(
        item_id,
        passed,
        by=tool_input.get("by", ""),
        notes=tool_input.get("notes", ""),
        maintenance=tool_input.get("maintenance", ""),
    )


def _donation_station_store(tool_input):
    item_id = _require_str(tool_input, "item_id")
    location = _require_str(tool_input, "location")
    return ds.store(item_id, location, by=tool_input.get("by", ""), notes=tool_input.get("notes", ""))


def _donation_station_distribute(tool_input):
    item_id = _require_str(tool_input, "item_id")
    recipient = _require_str(tool_input, "recipient")
    return ds.distribute(item_id, recipient, by=tool_input.get("by", ""), notes=tool_input.get("notes", ""))


def _donation_station_get_status(tool_input):
    item_id = _require_str(tool_input, "item_id")
    return ds.get_status(item_id)


def _donation_station_list_items(tool_input):
    stage = tool_input.get("stage", "all")
    if stage not in ds.STAGES and stage != "all":
        raise ToolError(f"`stage` must be one of {list(ds.STAGES) + ['all']}.")
    return {"items": ds.list_items(stage)}


def _donation_station_report(tool_input):
    return ds.report()


_HANDLERS = {
    "donation_station_intake": _donation_station_intake,
    "donation_station_process_qc": _donation_station_process_qc,
    "donation_station_store": _donation_station_store,
    "donation_station_distribute": _donation_station_distribute,
    "donation_station_get_status": _donation_station_get_status,
    "donation_station_list_items": _donation_station_list_items,
    "donation_station_report": _donation_station_report,
}


def dispatch(name, tool_input):
    """
    Run the tool named `name` with Claude's parsed tool_input dict.

    Returns {"is_error": False, "content": <json-serializable result>} on
    success, or {"is_error": True, "content": "<message>"} on failure.
    Unknown item IDs and out-of-order stage transitions (both raised by
    donation_station.py as KeyError/ValueError) are caught and reported
    as error results rather than propagating.
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"is_error": True, "content": f"Unknown tool: {name!r}"}

    try:
        return {"is_error": False, "content": handler(tool_input or {})}
    except ToolError as exc:
        return {"is_error": True, "content": str(exc)}
    except (KeyError, ValueError) as exc:
        return {"is_error": True, "content": str(exc)}
