"""tools.py — unified Claude tool-use registry for this repository.

Combines every <module>_tool.py's TOOLS list and dispatch() function into
one master TOOLS list and one dispatch(name, tool_input), so a single
Claude agent can be handed every tool in the repo — etymonline, axiom,
power_connection, donation_station, suprememath, and notion — through
one servicing surface instead of wiring each module in separately.

Usage with the Anthropic SDK:

    import anthropic
    from tools import TOOLS, dispatch

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=TOOLS,
        messages=[{"role": "user", "content": "..."}],
    )

    for block in response.content:
        if block.type == "tool_use":
            outcome = dispatch(block.name, block.input)
            ...  # send back as a tool_result content block
"""

import axiom_tool
import donation_station_tool
import etymonline_tool
import notion_tool
import power_connection_tool
import suprememath_tool

_MODULES = [
    etymonline_tool,
    axiom_tool,
    power_connection_tool,
    donation_station_tool,
    suprememath_tool,
    notion_tool,
]

TOOLS = []
_DISPATCH_BY_NAME = {}

for _mod in _MODULES:
    for _spec in _mod.TOOLS:
        _name = _spec["name"]
        if _name in _DISPATCH_BY_NAME:
            raise RuntimeError(
                f"Duplicate tool name {_name!r} — check {_mod.__name__} against "
                "the other registered tool modules."
            )
        _DISPATCH_BY_NAME[_name] = _mod.dispatch
        TOOLS.append(_spec)


def dispatch(name, tool_input):
    """
    Run the tool named `name`, from any registered module, with Claude's
    parsed tool_input dict.

    Returns {"is_error": False, "content": <json-serializable result>} on
    success, or {"is_error": True, "content": "<message>"} on failure —
    the shape a tool_result content block's "content"/"is_error" fields
    expect. Routes to the owning module's own dispatch(), so each
    module's error handling (input validation, network/HTTP failures,
    domain errors) applies unchanged.
    """
    handler = _DISPATCH_BY_NAME.get(name)
    if handler is None:
        return {"is_error": True, "content": f"Unknown tool: {name!r}"}
    return handler(name, tool_input)
