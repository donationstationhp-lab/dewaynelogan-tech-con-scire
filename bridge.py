#!/usr/bin/env python3
"""bridge.py — AXIOM Assessment Signal Verifier

Loads two AXIOM assessment files for the same organization,
compares every dimension, and surfaces signal moves — changes
in score and level between assessments.

Usage:
    python bridge.py                        # auto-selects two most recent
    python bridge.py FILE_A.json FILE_B.json
    python bridge.py --dimension 6         # focus on a single position
    python bridge.py --json                # machine-readable output
"""

import argparse
import json
import os
import sys
from glob import glob

ASSESSMENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assessments")

LEVEL_ORDER = {"Absent": 0, "Emerging": 1, "Established": 2, "Mature": 3}

# ── Loaders ───────────────────────────────────────────────────────────────────

def load(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def latest_two(directory: str) -> tuple:
    pattern = os.path.join(directory, "*.json")
    files = sorted(glob(pattern))
    if len(files) < 2:
        raise FileNotFoundError(
            f"Need at least 2 assessment files in {directory}; found {len(files)}."
        )
    return files[-2], files[-1]


# ── Comparison ────────────────────────────────────────────────────────────────

def compare_dimension(before: dict, after: dict) -> dict:
    delta = round(after["average"] - before["average"], 2)
    before_rank = LEVEL_ORDER[before["level"]]
    after_rank = LEVEL_ORDER[after["level"]]
    level_delta = after_rank - before_rank

    if level_delta > 0:
        direction = "UP"
    elif level_delta < 0:
        direction = "DOWN"
    elif delta > 0:
        direction = "GAIN"
    elif delta < 0:
        direction = "LOSS"
    else:
        direction = "FLAT"

    return {
        "position": before["position"],
        "name": before["name"],
        "before_score": before["average"],
        "after_score": after["average"],
        "delta": delta,
        "before_level": before["level"],
        "after_level": after["level"],
        "level_moved": level_delta != 0,
        "direction": direction,
    }


def build_diff(old: dict, new: dict) -> dict:
    old_by_pos = {d["position"]: d for d in old["dimensions"]}
    new_by_pos = {d["position"]: d for d in new["dimensions"]}

    moves = []
    for pos in sorted(old_by_pos):
        if pos in new_by_pos:
            moves.append(compare_dimension(old_by_pos[pos], new_by_pos[pos]))

    agg_delta = round(new["aggregate_score"] - old["aggregate_score"], 2)
    return {
        "organization": new["organization"],
        "before_file": old.get("_source", ""),
        "after_file": new.get("_source", ""),
        "before_timestamp": old["timestamp"],
        "after_timestamp": new["timestamp"],
        "aggregate_before": old["aggregate_score"],
        "aggregate_after": new["aggregate_score"],
        "aggregate_delta": agg_delta,
        "moves": moves,
        "signal_moves": [m for m in moves if m["level_moved"]],
        "score_moves": [m for m in moves if m["delta"] != 0 and not m["level_moved"]],
    }


# ── Output ────────────────────────────────────────────────────────────────────

ARROWS = {"UP": "↑", "DOWN": "↓", "GAIN": "+", "LOSS": "−", "FLAT": "·"}

def _level_tag(level: str) -> str:
    return f"[{level}]"


def print_diff(diff: dict, focus_position: int = None) -> None:
    sep = "─" * 66

    print(f"\n{sep}")
    print(f"  BRIDGE — Signal Verification")
    print(f"{sep}")
    print(f"  Organization : {diff['organization']}")
    print(f"  Before       : {diff['before_timestamp'][:19].replace('T', '  ')}")
    print(f"  After        : {diff['after_timestamp'][:19].replace('T', '  ')}")
    print(f"{sep}")

    moves = diff["moves"]
    if focus_position is not None:
        moves = [m for m in moves if m["position"] == focus_position]
        if not moves:
            print(f"  No data for position {focus_position}.")
            return

    print(f"  {'POS':<4} {'DIMENSION':<22} {'BEFORE':>7} {'AFTER':>7} {'DELTA':>7}  {'MOVE'}")
    print(f"  {'---':<4} {'---------':<22} {'------':>7} {'-----':>7} {'-----':>7}  {'----'}")

    for m in moves:
        arrow = ARROWS[m["direction"]]
        level_note = ""
        if m["level_moved"]:
            level_note = f"  {m['before_level']} → {m['after_level']}"
        delta_str = f"{'+' if m['delta'] > 0 else ''}{m['delta']:.2f}"
        print(
            f"  {m['position']:<4} {m['name']:<22} {m['before_score']:>7.2f} "
            f"{m['after_score']:>7.2f} {delta_str:>7}  {arrow}{level_note}"
        )

    print(sep)
    agg_delta = diff["aggregate_delta"]
    agg_str = f"{'+' if agg_delta > 0 else ''}{agg_delta:.2f}"
    print(
        f"  {'AGGREGATE':<26} {diff['aggregate_before']:>7.2f} "
        f"{diff['aggregate_after']:>7.2f} {agg_str:>7}"
    )
    print(sep)

    # Signal summary
    sigs = diff["signal_moves"]
    if sigs:
        print(f"\n  SIGNAL MOVES (level change):")
        for m in sigs:
            arrow = ARROWS[m["direction"]]
            print(
                f"    {arrow}  P{m['position']} {m['name']}: "
                f"{m['before_level']} → {m['after_level']}  "
                f"({m['before_score']:.2f} → {m['after_score']:.2f})"
            )
    else:
        print(f"\n  No level-change signal moves detected.")

    gains = [m for m in diff["score_moves"] if m["delta"] > 0]
    losses = [m for m in diff["score_moves"] if m["delta"] < 0]
    if gains:
        print(f"\n  SCORE GAINS (within level):")
        for m in gains:
            print(f"    +  P{m['position']} {m['name']}: {m['before_score']:.2f} → {m['after_score']:.2f}")
    if losses:
        print(f"\n  SCORE LOSSES (within level):")
        for m in losses:
            print(f"    −  P{m['position']} {m['name']}: {m['before_score']:.2f} → {m['after_score']:.2f}")

    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="AXIOM signal verifier")
    parser.add_argument("files", nargs="*", help="Two JSON assessment files (before, after)")
    parser.add_argument("--dimension", "-d", type=int, default=None,
                        help="Focus output on a single position (0–9)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON diff")
    args = parser.parse_args()

    if args.files:
        if len(args.files) != 2:
            print("Provide exactly two files, or none to auto-select the two most recent.")
            sys.exit(1)
        path_before, path_after = args.files
    else:
        path_before, path_after = latest_two(ASSESSMENTS_DIR)

    before = load(path_before)
    after = load(path_after)
    before["_source"] = os.path.basename(path_before)
    after["_source"] = os.path.basename(path_after)

    diff = build_diff(before, after)

    if args.json:
        print(json.dumps(diff, indent=2))
    else:
        print_diff(diff, focus_position=args.dimension)


if __name__ == "__main__":
    main()
