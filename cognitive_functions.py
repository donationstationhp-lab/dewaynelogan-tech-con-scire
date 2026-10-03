#!/usr/bin/env python3
"""
cognitive_functions.py — Lookup and display cognitive function entries.

Four layers:
  process  — 18 mental operations (Focusing, Labeling, Analyzing …)
  values   — 5 core values (INTEGRITY, DIGNITY, DISCERNMENT …)
  stages   — 16 self-determination stages with etymologies (Neophyte → Anoint)
  domains  — 6 mathematical/logical domains (Quantity, Logic/Proof …)

Usage:
  python cognitive_functions.py --list
  python cognitive_functions.py --list --category stages
  python cognitive_functions.py --lookup "focusing"
  python cognitive_functions.py --lookup "neophyte"
  python cognitive_functions.py --lookup 7
  python cognitive_functions.py --lookup "integrity"
  python cognitive_functions.py --lookup "logic"
"""

import argparse
import json
import os
import sys

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "cognitive_functions.json")

CATEGORIES = ("process", "values", "stages", "domains")


def load(path=None):
    with open(path or DEFAULT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _norm(s):
    return s.lower().replace("/", " ").replace("-", " ").replace("_", " ").strip()


def _items(data, category):
    if category == "stages":
        return data["stages"]["items"]
    return data[category]


def lookup(data, query):
    """
    Find an entry across all four layers.
    query: an integer (stage number or process/value/domain id) or a string (name).
    Returns list of (category, entry) tuples — multiple matches possible.
    """
    results = []

    # numeric query
    if isinstance(query, int) or (isinstance(query, str) and query.strip().lstrip("-").isdigit()):
        n = int(query)
        for cat in CATEGORIES:
            for item in _items(data, cat):
                key = item.get("number") or item.get("id")
                if key == n:
                    results.append((cat, item))
        return results

    # string query
    q = _norm(query)
    for cat in CATEGORIES:
        for item in _items(data, cat):
            name = _norm(item["name"])
            if q == name or name.startswith(q) or q in name:
                results.append((cat, item))
    return results


def format_entry(category, entry):
    lines = []
    if category == "stages":
        lines.append(f"Stage {entry['number']:>2}: {entry['name']}")
        lines.append(f"  Category : Build Self-Determination")
        lines.append(f"  Etymology: {entry['etymology']} — \"{entry['root']}\"")
        lines.append(f"  Meaning  : {entry['description']}")
    elif category == "values":
        note = f"  ({entry['note']})" if entry.get("note") else ""
        lines.append(f"Value {entry['id']}: {entry['name']}{note}")
        lines.append(f"  Category : Core Values")
    elif category == "process":
        lines.append(f"Process {entry['id']:>2}: {entry['name']}")
        lines.append(f"  Category : Cognitive Process Functions")
    elif category == "domains":
        lines.append(f"Domain {entry['id']}: {entry['name']}")
        lines.append(f"  Category : Mathematical/Logical Domains")
    return "\n".join(lines)


def print_list(data, category=None):
    sep = "─" * 62
    cats = [category] if category else CATEGORIES
    for cat in cats:
        if cat == "stages":
            header = f"BUILD SELF-DETERMINATION  ({len(data['stages']['items'])} stages)"
        else:
            header = cat.upper()
        print(f"\n{sep}")
        print(f"  {header}")
        print(sep)
        for item in _items(data, cat):
            if cat == "stages":
                etym = f"  ← {item['etymology']} \"{item['root']}\""
                print(f"  {item['number']:>2}. {item['name']:<24}{etym}")
            elif cat == "values":
                note = f"  ({item['note']})" if item.get("note") else ""
                print(f"  {item['id']}. {item['name']}{note}")
            elif cat == "process":
                print(f"  {item['id']:>2}. {item['name']}")
            elif cat == "domains":
                print(f"  {item['id']}. {item['name']}")
    print()


def print_entry(category, entry):
    sep = "─" * 62
    print(f"\n{sep}")
    print(f"  {format_entry(category, entry)}")
    print(sep)


def main():
    parser = argparse.ArgumentParser(
        description="Cognitive Functions — lookup and list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cognitive_functions.py --list\n"
            "  python cognitive_functions.py --list --category stages\n"
            "  python cognitive_functions.py --lookup focusing\n"
            "  python cognitive_functions.py --lookup neophyte\n"
            "  python cognitive_functions.py --lookup 7\n"
            "  python cognitive_functions.py --lookup integrity\n"
            "  python cognitive_functions.py --lookup logic"
        ),
    )
    parser.add_argument("--list", action="store_true", help="List all entries")
    parser.add_argument(
        "--category",
        choices=CATEGORIES,
        help="Limit --list or --lookup to one category",
    )
    parser.add_argument(
        "--lookup",
        metavar="NAME_OR_NUM",
        help="Look up a function by name or number",
    )
    parser.add_argument(
        "--data",
        metavar="FILE",
        help=f"Path to cognitive_functions.json (default: {DEFAULT_PATH})",
    )
    args = parser.parse_args()

    try:
        data = load(args.data)
    except FileNotFoundError as e:
        print(f"Data file not found: {e}")
        sys.exit(1)

    if args.lookup:
        results = lookup(data, args.lookup)
        if args.category:
            results = [(c, e) for c, e in results if c == args.category]
        if not results:
            print(f"No match for {args.lookup!r}.")
            sys.exit(1)
        for cat, entry in results:
            print_entry(cat, entry)
    elif args.list:
        print_list(data, args.category)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
