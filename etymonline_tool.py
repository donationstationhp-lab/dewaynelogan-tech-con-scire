"""etymonline_tool.py — Claude tool-use wrapper for etymonline.py

Exposes etymonline's search / look / explore / DKL_LOOP operations as
Anthropic Messages API tool definitions (TOOLS), plus a dispatch()
function that runs a tool call by name and returns a tool_result-shaped
dict — so a Claude agent can drive etymonline.py through tool_use content
blocks instead of the CLI.

Usage with the Anthropic SDK:

    import anthropic
    from etymonline_tool import TOOLS, dispatch

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=TOOLS,
        messages=[{"role": "user", "content": "Where does 'serendipity' come from?"}],
    )

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            outcome = dispatch(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(outcome["content"]),
                "is_error": outcome["is_error"],
            })
"""

import requests

import etymonline as ety

# ── Shared input-schema fragments ───────────────────────────────────────────

_OFFLINE_PROP = {
    "type": "boolean",
    "description": "Use only cached results; make no network requests.",
    "default": False,
}

_NO_CACHE_PROP = {
    "type": "boolean",
    "description": "Skip the cache and always fetch fresh from the network.",
    "default": False,
}

_WORD_PROP = {
    "type": "string",
    "description": "The exact word to look up, e.g. 'galaxy'.",
}

# ── Tool definitions ─────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "etymonline_search",
        "description": (
            "Search etymonline.com for words matching a free-text query. "
            "Returns a list of matching entries, each with a word and its "
            "etymology text. Use this to find candidate words before "
            "looking one up in detail with etymonline_look."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms, e.g. 'serendipity' or 'origin of robot'.",
                },
                "offline": _OFFLINE_PROP,
                "no_cache": _NO_CACHE_PROP,
            },
            "required": ["query"],
        },
    },
    {
        "name": "etymonline_look",
        "description": (
            "Look up a single word's etymology on etymonline.com. Returns "
            "the word's entries (etymology text for each sense) and a list "
            "of related word slugs linked from its page."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "word": _WORD_PROP,
                "offline": _OFFLINE_PROP,
                "no_cache": _NO_CACHE_PROP,
            },
            "required": ["word"],
        },
    },
    {
        "name": "etymonline_explore",
        "description": (
            "Look up a word, then follow its related words in a "
            "breadth-first search up to `depth` hops, building out a small "
            "etymological neighborhood. Capped at 15 words total, 3 "
            "branches followed per hop."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "word": _WORD_PROP,
                "depth": {
                    "type": "integer",
                    "description": "Number of hops to follow from the root word.",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 5,
                },
                "offline": _OFFLINE_PROP,
                "no_cache": _NO_CACHE_PROP,
            },
            "required": ["word"],
        },
    },
    {
        "name": "etymonline_dkl_loop",
        "description": (
            "Run the DKL_LOOP seven-step etymological reasoning protocol on "
            "a word (Depth, Knowledge, Equality-or-Leading, Wisdom, Source, "
            "Now, Container), grounded in that word's fetched etymology "
            "data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "word": _WORD_PROP,
                "variant": {
                    "type": "string",
                    "enum": ["a", "b"],
                    "description": (
                        "a = Equality (weigh and separate distinct senses); "
                        "b = Leading (direction/strategy toward related words)."
                    ),
                    "default": "b",
                },
                "offline": _OFFLINE_PROP,
                "no_cache": _NO_CACHE_PROP,
            },
            "required": ["word"],
        },
    },
]

_MAX_EXPLORE_DEPTH = 5


class ToolError(Exception):
    """A tool_input validation error, reported back to the caller (not raised)."""


def _bool(tool_input, key, default=False):
    return bool(tool_input.get(key, default))


def _require_word(tool_input, key="word"):
    word = (tool_input.get(key) or "").strip()
    if not word:
        raise ToolError(f"`{key}` is required and must be a non-empty string.")
    return word


def _etymonline_search(tool_input):
    query = (tool_input.get("query") or "").strip()
    if not query:
        raise ToolError("`query` is required and must be a non-empty string.")
    entries, from_cache = ety.search(
        query,
        offline=_bool(tool_input, "offline"),
        no_cache=_bool(tool_input, "no_cache"),
    )
    return {"query": query, "entries": entries, "from_cache": from_cache}


def _etymonline_look(tool_input):
    word = _require_word(tool_input)
    result, from_cache = ety.lookup(
        word,
        offline=_bool(tool_input, "offline"),
        no_cache=_bool(tool_input, "no_cache"),
    )
    return dict(result, from_cache=from_cache)


def _etymonline_explore(tool_input):
    word = _require_word(tool_input)
    depth = tool_input.get("depth", 1)
    if isinstance(depth, bool) or not isinstance(depth, int) or not (1 <= depth <= _MAX_EXPLORE_DEPTH):
        raise ToolError(f"`depth` must be an integer between 1 and {_MAX_EXPLORE_DEPTH}.")
    explored = ety.explore(
        word,
        depth=depth,
        offline=_bool(tool_input, "offline"),
        no_cache=_bool(tool_input, "no_cache"),
    )
    return {"root": word, "explored": explored}


def _etymonline_dkl_loop(tool_input):
    word = _require_word(tool_input)
    variant = tool_input.get("variant", "b")
    if variant not in ("a", "b"):
        raise ToolError("`variant` must be 'a' or 'b'.")
    steps, from_cache = ety.run_dkl_loop(
        word,
        variant=variant,
        offline=_bool(tool_input, "offline"),
        no_cache=_bool(tool_input, "no_cache"),
    )
    return {
        "word": word,
        "variant": variant,
        "from_cache": from_cache,
        "steps": [
            {"step": letter, "name": name, "root": root, "body": body}
            for letter, name, root, body in steps
        ],
    }


_HANDLERS = {
    "etymonline_search": _etymonline_search,
    "etymonline_look": _etymonline_look,
    "etymonline_explore": _etymonline_explore,
    "etymonline_dkl_loop": _etymonline_dkl_loop,
}


def dispatch(name, tool_input):
    """
    Run the tool named `name` with Claude's parsed tool_input dict.

    Returns {"is_error": False, "content": <json-serializable result>} on
    success, or {"is_error": True, "content": "<message>"} on failure — the
    shape a tool_result content block's "content"/"is_error" fields expect.
    Never raises: unknown tools, bad input, and network/HTTP failures are
    all caught and reported as an error result instead.
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"is_error": True, "content": f"Unknown tool: {name!r}"}

    try:
        return {"is_error": False, "content": handler(tool_input or {})}
    except ToolError as exc:
        return {"is_error": True, "content": str(exc)}
    except requests.HTTPError as exc:
        return {"is_error": True, "content": f"HTTP error: {exc}"}
    except requests.TooManyRedirects:
        return {
            "is_error": True,
            "content": "Too many redirects. The site may have moved or be blocking requests.",
        }
    except requests.ConnectionError:
        return {
            "is_error": True,
            "content": "Network error. Check your connection or pass offline=true.",
        }
    except requests.Timeout:
        return {
            "is_error": True,
            "content": "Request timed out. Try again or pass offline=true.",
        }
