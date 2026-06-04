#!/usr/bin/env python3
"""etymonline.py — search and explore word etymologies from etymonline.com

Commands:
  search <query>        Search for words matching a query
  look <word>           Look up a specific word's etymology
  explore <word>        Look up a word and follow related entries
  cache                 Manage local cache  (--list | --clear)

Global options:
  --offline   Use only cached results; no network requests
  --json      Output raw JSON instead of formatted text
  --no-cache  Skip cache and always fetch fresh from the network

Examples:
  python etymonline.py search serendipity
  python etymonline.py look galaxy
  python etymonline.py explore robot --depth 2
  python etymonline.py --offline look serendipity
  python etymonline.py cache --list
  python etymonline.py cache --clear
"""

import argparse
import hashlib
import json
import os
import sys
import textwrap
import time

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit(
        "Missing dependencies. Install with:\n"
        "  pip install requests beautifulsoup4"
    )

import notion

# ── Constants ─────────────────────────────────────────────────────────────────

BASE_URL  = "https://www.etymonline.com"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".etymonline_cache")
REQ_DELAY = 1.0   # polite delay between outbound requests (seconds)
WIDTH     = 72    # terminal output width

# ── Cache ─────────────────────────────────────────────────────────────────────

def _cache_path(key):
    return os.path.join(CACHE_DIR, key + ".json")


def cache_get(key):
    p = _cache_path(key)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None


def cache_set(key, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(key), "w") as f:
        json.dump(data, f, indent=2)


def cache_list():
    if not os.path.isdir(CACHE_DIR):
        return []
    return sorted(fn[:-5] for fn in os.listdir(CACHE_DIR) if fn.endswith(".json"))


def cache_clear():
    if not os.path.isdir(CACHE_DIR):
        return 0
    removed = 0
    for fn in os.listdir(CACHE_DIR):
        if fn.endswith(".json"):
            os.remove(os.path.join(CACHE_DIR, fn))
            removed += 1
    return removed


def _cache_key(prefix, text):
    digest = hashlib.sha1(text.lower().encode()).hexdigest()[:12]
    return f"{prefix}_{digest}"


# ── HTTP ──────────────────────────────────────────────────────────────────────

_last_req_time = 0.0


def fetch(url):
    global _last_req_time
    wait = REQ_DELAY - (time.time() - _last_req_time)
    if wait > 0:
        time.sleep(wait)
    resp = requests.get(
        url,
        timeout=15,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    resp.raise_for_status()
    _last_req_time = time.time()
    return resp.text


# ── Parsing ───────────────────────────────────────────────────────────────────

def _has_cls(tag, fragment):
    """True if any CSS class on `tag` contains `fragment` as a substring."""
    return any(fragment in c for c in tag.get("class", []))


def _strip_html(text):
    return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)


def _parse_next_data(html):
    """
    Primary parse path: extract entries from the Next.js __NEXT_DATA__ JSON
    embed that React SSR pages include.  Returns a list of entry dicts or
    None if the embed is absent / unusable.
    """
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script or not script.string:
        return None

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return None

    props = data.get("props", {}).get("pageProps", {})

    # The JSON structure differs between search results and individual word pages
    raw = (
        props.get("entries")
        or props.get("words")
        or props.get("searchResults")
        or props.get("results")
        or []
    )
    if not raw:
        return None

    entries = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        word = item.get("name") or item.get("word") or ""
        body = (
            item.get("meaning")
            or item.get("definition")
            or item.get("body")
            or ""
        )
        entries.append({"word": word, "etymology": _strip_html(body)})

    return entries if entries else None


def _parse_html(html):
    """
    Fallback HTML parse path.  etymonline uses hashed CSS class names
    (e.g. 'word__deftext--2b9Rq') so we match on stable class-name prefixes.
    """
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen = set()

    # Each entry lives in a container div/section with a "word__" class
    containers = soup.find_all(
        lambda t: t.name in ("section", "div", "article")
        and (_has_cls(t, "word__deflist") or _has_cls(t, "word__col"))
    )
    if not containers:
        # Broad fallback: any <section> that contains a word-name element
        containers = [
            s for s in soup.find_all("section")
            if s.find(lambda t: _has_cls(t, "word__name"))
        ]

    for el in containers:
        name_el = el.find(lambda t: _has_cls(t, "word__name"))
        if not name_el:
            continue
        word = name_el.get_text(" ", strip=True)
        if not word or word in seen:
            continue
        seen.add(word)

        text_el = el.find(lambda t: _has_cls(t, "word__deftext"))
        etymology = text_el.get_text(" ", strip=True) if text_el else ""
        entries.append({"word": word, "etymology": etymology})

    return entries


def parse_entries(html):
    """Try Next.js JSON embed first; fall back to HTML scraping."""
    return _parse_next_data(html) or _parse_html(html)


def parse_related(html, exclude=""):
    """Return a de-duplicated list of word slugs linked from a word page."""
    soup = BeautifulSoup(html, "html.parser")
    seen, words = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/word/"):
            w = href[6:].split("?")[0].strip("/")
            if w and w != exclude and w not in seen:
                seen.add(w)
                words.append(w)
    return words


# ── Core operations ───────────────────────────────────────────────────────────

def search(query, offline=False, no_cache=False):
    """
    Search etymonline.com for `query`.
    Returns (list[entry_dict], from_cache_bool).
    """
    key = _cache_key("search", query)
    if not no_cache:
        cached = cache_get(key)
        if cached is not None:
            return cached, True

    if offline:
        return [], False

    url = f"{BASE_URL}/search?q={requests.utils.quote(query)}"
    html = fetch(url)
    entries = parse_entries(html)
    cache_set(key, entries)
    return entries, False


def lookup(word, offline=False, no_cache=False):
    """
    Fetch the etymology page for `word`.
    Returns (result_dict, from_cache_bool).
    result_dict keys: word, entries, related
    """
    key = _cache_key("word", word)
    if not no_cache:
        cached = cache_get(key)
        if cached is not None:
            return cached, True

    if offline:
        return {"word": word, "entries": [], "related": []}, False

    url = f"{BASE_URL}/word/{requests.utils.quote(word)}"
    html = fetch(url)
    entries = parse_entries(html)
    related = parse_related(html, exclude=word)[:15]
    result = {"word": word, "entries": entries, "related": related}
    cache_set(key, result)
    return result, False


def explore(word, depth=1, offline=False, no_cache=False):
    """
    Look up `word`, then (when depth > 0) also fetch the first few related
    words so the caller can display a richer picture.
    Returns an ordered dict  {word: result_dict, ...}.
    """
    root, _ = lookup(word, offline=offline, no_cache=no_cache)
    explored = {word: root}

    if depth > 0:
        for rel in root.get("related", [])[:3]:
            if rel not in explored:
                result, _ = lookup(rel, offline=offline, no_cache=no_cache)
                explored[rel] = result

    return explored


# ── DKL_LOOP — Etymological Reasoning Engine ─────────────────────────────────

# Seven-step protocol: D-K-[E|L]-W-S-N-C
# v.A (Equality): step 3 = EQUALITY — weigh variables, catch flattening
# v.B (Leading):  step 3 = LEADING  — draw the sequence forward

_LOOP_STEPS_A = [
    ("D", "DEPTH",    '*dʰewbʰ-* "to hollow, to dig"'),
    ("K", "KNOWLEDGE",'*gno-* "to recognize"'),
    ("E", "EQUALITY", '*aik-* "to be master of, to possess"'),
    ("W", "WISDOM",   '*weid-* "to see"'),
    ("S", "SOURCE",   '*s(w)e-* "one\'s own"'),
    ("N", "NOW",      '*nu-* "now, at this moment"'),
    ("C", "CONTAINER",'*kel-* "to cover, to hold"'),
]

_LOOP_STEPS_B = [
    ("D", "DEPTH",   '*dʰewbʰ-* "to hollow, to dig"'),
    ("K", "KNOWLEDGE",'*gno-* "to recognize"'),
    ("L", "LEADING", '*deuk-* "to draw, to lead forth"'),
    ("W", "WISDOM",  '*weid-* "to see"'),
    ("S", "SOURCE",  '*s(w)e-* "one\'s own"'),
    ("N", "NOW",     '*nu-* "now, at this moment"'),
    ("C", "CONTAINER",'*kel-* "to cover, to hold"'),
]


def run_dkl_loop(word, variant="b", offline=False, no_cache=False):
    """
    Run the DKL_LOOP protocol on a word using fetched etymology data.
    Returns (list[(letter, name, root, text)], from_cache).
    """
    result, from_cache = lookup(word, offline=offline, no_cache=no_cache)
    entries  = result.get("entries", [])
    related  = result.get("related", [])
    schema   = _LOOP_STEPS_A if variant == "a" else _LOOP_STEPS_B

    # Build body text for each step from the etymology data
    bodies = []

    # Step 1 — DEPTH: non-surface layer of the first entry
    depth = entries[0].get("etymology", "") if entries else ""
    bodies.append(depth if depth else "(no etymology found)")

    # Step 2 — KNOWLEDGE: all distinct senses, each on its own terms
    known_lines = []
    for e in entries:
        etym = e.get("etymology", "")
        if etym:
            known_lines.append(f"{e.get('word', word)}: {etym[:200]}")
    bodies.append("\n".join(known_lines) if known_lines else "(no data)")

    # Step 3 — variant-specific
    if variant == "a":
        # EQUALITY: enumerate distinct senses; refuse to collapse them
        senses = [e.get("word", "") for e in entries if e.get("word")]
        if len(senses) > 1:
            eq = ("Distinct senses: " + " | ".join(senses[:6]) +
                  "\nEach weighted on its own terms — not interchangeable tokens.")
        elif senses:
            eq = f"Single attested sense: {senses[0]}"
        else:
            eq = "(no senses identified)"
        bodies.append(eq)
    else:
        # LEADING: which direction does the root point?
        if related:
            bodies.append("Sequence points toward: " + ", ".join(related[:5]))
        else:
            bodies.append("(no related words found — root may be a terminus)")

    # Step 4 — WISDOM: what the depth + step-3 together reveal
    if entries:
        etym0 = entries[0].get("etymology", "")
        wisdom = etym0[:300] + ("…" if len(etym0) > 300 else "")
    else:
        wisdom = "(no etymology to synthesize)"
    bodies.append(wisdom if wisdom else "(no etymology to synthesize)")

    # Step 5 — SOURCE: authorship verification
    src = f"Etymology: etymonline.com · Word queried: '{word}'"
    if from_cache:
        src += "  [from cache]"
    bodies.append(src)

    # Step 6 — NOW: present action
    if related:
        bodies.append(f"Immediate move: run `explore {word}` or look up '{related[0]}' next.")
    else:
        bodies.append(f"Immediate move: run `look {word}` with --no-cache for a fresh trace.")

    # Step 7 — CONTAINER: where the result is stored
    cache_key = _cache_key("word", word)
    bodies.append(f"Stored at: {_cache_path(cache_key)}")

    steps = [(letter, name, root, body)
             for (letter, name, root), body in zip(schema, bodies)]
    return steps, from_cache


# ── Formatted output ──────────────────────────────────────────────────────────

BAR = "─" * WIDTH


def _wrap(text, indent=4):
    return textwrap.fill(
        text, width=WIDTH,
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
    )


def print_entries(entries, header):
    print(f"\n{BAR}")
    print(f"  {header}")
    print(BAR)
    if not entries:
        print("  (no entries found)\n")
        return
    for e in entries:
        print(f"\n  {e.get('word', '(unknown)')}")
        etym = e.get("etymology", "")
        if etym:
            print(_wrap(etym))
    print()


def print_lookup(result):
    word    = result.get("word", "")
    entries = result.get("entries", [])
    related = result.get("related", [])

    print_entries(entries, f"Etymology of: {word}")

    if related:
        print("  " + "─" * (WIDTH - 2))
        rel_line = "  Related: " + ", ".join(related[:10])
        print(textwrap.fill(rel_line, width=WIDTH, subsequent_indent="    "))
        print()


def print_dkl_loop(word, steps, variant="b", from_cache=False):
    variant_label = "v.A — Equality" if variant == "a" else "v.B — Leading"
    cache_note = "  [cached]" if from_cache else ""
    print(f"\n{BAR}")
    print(f"  DKL_LOOP {variant_label}{cache_note}")
    print(f"  Input: {word}")
    print(BAR)
    for i, (letter, name, root, body) in enumerate(steps, 1):
        print(f"\n  STEP {i} — {letter} — {name}  [{root}]")
        for line in body.split("\n"):
            if line.strip():
                print(_wrap(line))
    print()


def print_explore(explored):
    root_word = next(iter(explored))
    print_lookup(explored[root_word])

    others = {k: v for k, v in explored.items() if k != root_word}
    if not others:
        return

    print(BAR)
    print("  Explored related entries:")
    print(BAR)
    for word, result in others.items():
        entries = result.get("entries", [])
        if not entries:
            continue
        e = entries[0]
        print(f"\n  {e.get('word', word)}")
        etym = e.get("etymology", "")
        if etym:
            snippet = etym[:300] + ("…" if len(etym) > 300 else "")
            print(_wrap(snippet))
    print()


# ── Notion helpers ───────────────────────────────────────────────────────────

def _notion_save_entries(entries):
    """Save a flat list of entry dicts to Notion; prints status."""
    try:
        n = notion.save_entries(entries)
        print(f"  [notion] Saved {n} entr{'y' if n == 1 else 'ies'} to Notion.")
    except (EnvironmentError, requests.HTTPError) as exc:
        print(f"  [notion] Warning: could not save to Notion — {exc}", file=sys.stderr)


def _notion_save_lookup(result):
    """Save a single lookup result (word + its entries) to Notion."""
    word    = (result.get("word") or "").replace("  [cached]", "").strip()
    entries = result.get("entries", [])
    related = result.get("related", [])
    if not entries:
        print("  [notion] Nothing to save (no entries).", file=sys.stderr)
        return
    # Merge all entry etymologies under the word's canonical name.
    combined = " | ".join(
        e.get("etymology", "") for e in entries if e.get("etymology")
    )
    try:
        notion.save_entry(word, combined, related=related)
        print(f"  [notion] Saved '{word}' to Notion.")
    except (EnvironmentError, requests.HTTPError) as exc:
        print(f"  [notion] Warning: could not save to Notion — {exc}", file=sys.stderr)


def _notion_save_explore(explored):
    """Save every word in an explore result to Notion."""
    saved = 0
    try:
        for word, result in explored.items():
            entries = result.get("entries", [])
            related = result.get("related", [])
            combined = " | ".join(
                e.get("etymology", "") for e in entries if e.get("etymology")
            )
            notion.save_entry(word, combined, related=related)
            saved += 1
        print(f"  [notion] Saved {saved} word{'s' if saved != 1 else ''} to Notion.")
    except (EnvironmentError, requests.HTTPError) as exc:
        print(f"  [notion] Warning: could not save to Notion — {exc}", file=sys.stderr)


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(
        prog="etymonline",
        description="Search and explore word etymologies from etymonline.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--offline",  action="store_true",
                   help="Use only cached results; no network requests")
    p.add_argument("--json",     action="store_true",
                   help="Output raw JSON")
    p.add_argument("--no-cache", action="store_true", dest="no_cache",
                   help="Skip cache; always fetch fresh")
    p.add_argument("--notion",   action="store_true",
                   help="Save results to Notion (requires NOTION_TOKEN and "
                        "NOTION_DATABASE_ID env vars)")

    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="Search for words matching a query")
    s.add_argument("query", nargs="+", help="Search terms")

    lk = sub.add_parser("look", help="Look up a specific word")
    lk.add_argument("word")

    ex = sub.add_parser("explore", help="Look up a word and follow related entries")
    ex.add_argument("word")
    ex.add_argument("--depth", type=int, default=1, metavar="N",
                    help="Hops to follow from the root word (default: 1)")

    ca = sub.add_parser("cache", help="Manage the local cache")
    ca.add_argument("--list",  action="store_true", help="List cached entries")
    ca.add_argument("--clear", action="store_true", help="Delete all cached entries")

    lp = sub.add_parser("loop",
        help="Run the DKL_LOOP 7-step etymological reasoning protocol on a word")
    lp.add_argument("word")
    lp.add_argument("--variant", choices=["a", "b"], default="b",
                    help="v.A=Equality (weigh/evaluate), v.B=Leading (direct/strategy) [default: b]")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.cmd == "search":
            query = " ".join(args.query)
            results, from_cache = search(query, offline=args.offline,
                                         no_cache=args.no_cache)
            if args.offline and not results:
                sys.exit(f"No cached results for '{query}'. Re-run without --offline.")
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                n   = len(results)
                lbl = f"Search: {query!r}  ({n} entr{'y' if n == 1 else 'ies'})"
                if from_cache:
                    lbl += "  [cached]"
                print_entries(results, lbl)
            if args.notion:
                _notion_save_entries(results)

        elif args.cmd == "look":
            result, from_cache = lookup(args.word, offline=args.offline,
                                        no_cache=args.no_cache)
            if args.offline and not result["entries"]:
                sys.exit(f"No cached entry for '{args.word}'. Re-run without --offline.")
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                if from_cache:
                    result = dict(result, word=result["word"] + "  [cached]")
                print_lookup(result)
            if args.notion:
                _notion_save_lookup(result)

        elif args.cmd == "explore":
            explored = explore(args.word, depth=args.depth,
                               offline=args.offline, no_cache=args.no_cache)
            if args.json:
                print(json.dumps(explored, indent=2))
            else:
                print_explore(explored)
            if args.notion:
                _notion_save_explore(explored)

        elif args.cmd == "loop":
            steps, from_cache = run_dkl_loop(
                args.word, variant=args.variant,
                offline=args.offline, no_cache=args.no_cache,
            )
            if args.json:
                print(json.dumps(
                    [{"step": l, "name": n, "root": r, "body": b}
                     for l, n, r, b in steps],
                    indent=2,
                ))
            else:
                print_dkl_loop(args.word, steps, variant=args.variant,
                                from_cache=from_cache)

        elif args.cmd == "cache":
            if args.clear:
                n = cache_clear()
                print(f"Cleared {n} cached entr{'y' if n == 1 else 'ies'} from {CACHE_DIR}")
            else:
                keys = cache_list()
                if not keys:
                    print(f"Cache is empty.  ({CACHE_DIR})")
                else:
                    print(f"{len(keys)} cached entr{'y' if len(keys) == 1 else 'ies'} "
                          f"in {CACHE_DIR}:")
                    for k in keys:
                        print(f"  {k}")

    except requests.HTTPError as exc:
        sys.exit(f"HTTP error: {exc}")
    except requests.ConnectionError:
        sys.exit("Network error. Check your connection or use --offline.")
    except requests.Timeout:
        sys.exit("Request timed out. Try again or use --offline.")
    except KeyboardInterrupt:
        sys.exit("\nInterrupted.")


if __name__ == "__main__":
    main()
