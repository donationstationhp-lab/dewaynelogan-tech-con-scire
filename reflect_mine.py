#!/usr/bin/env python3
"""
reflect_mine.py — Reflection pattern miner

Reads the daily log and surfaces correlations between the day's cognitive
frame (purpose, stage, value, domain) and the quality of reflections.

Over time this builds a personal epistemology: which conditions produce
the most generative thought. It works with any number of entries and
shows confidence indicators so sparse patterns are never mistaken for
settled ones.

Usage:
  python reflect_mine.py                   # full mining report
  python reflect_mine.py --by purpose      # group reflections by purpose position
  python reflect_mine.py --by stage        # group by stage
  python reflect_mine.py --by value        # group by governing value
  python reflect_mine.py --by domain       # group by domain in frame
  python reflect_mine.py --score           # entries ranked by reflection richness
  python reflect_mine.py --show            # list all entries that have reflections
  python reflect_mine.py --log FILE        # use alternate log file
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_LOG = os.path.join(BASE, ".daily_log.json")

SEP  = "─" * 66
DSEP = "═" * 66

# Words that signal generative depth
DEPTH_MARKERS   = {"realized", "discovered", "understood", "learned", "saw", "noticed",
                   "recognized", "connected", "clarity", "clear", "insight", "understood",
                   "revealed", "emerged", "opened", "shifted", "deepened"}
ACTION_MARKERS  = {"did", "made", "built", "wrote", "started", "completed", "decided",
                   "moved", "created", "finished", "shipped", "pushed", "called"}
STRUGGLE_MARKERS = {"hard", "difficult", "challenging", "struggled", "wrestled",
                    "resisted", "blocked", "stuck", "heavy", "slow"}
JOY_MARKERS     = {"flow", "aligned", "resonant", "easy", "good", "clear",
                   "yes", "open", "light", "free", "moved", "alive"}

# Minimum entries before a correlation is considered meaningful
CONFIDENCE_THRESHOLDS = {
    "emerging":    3,
    "provisional": 10,
    "established": 25,
    "reliable":    50,
}


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_reflection(text):
    """
    Return a richness score for a reflection string.
    Components:
      · word count         (up to 30 points at 30 words)
      · depth markers      (5 pts each, max 20)
      · action markers     (3 pts each, max 12)
      · struggle markers   (4 pts each, max 8)
      · joy markers        (3 pts each, max 9)
    Max possible: ~79 — normalized to 0-10 scale.
    """
    if not text:
        return 0.0

    words  = text.lower().split()
    w_set  = set(words)
    n_words = len(words)

    length_score   = min(n_words, 30)
    depth_score    = min(len(w_set & DEPTH_MARKERS)   * 5, 20)
    action_score   = min(len(w_set & ACTION_MARKERS)  * 3, 12)
    struggle_score = min(len(w_set & STRUGGLE_MARKERS) * 4, 8)
    joy_score      = min(len(w_set & JOY_MARKERS)     * 3, 9)

    raw = length_score + depth_score + action_score + struggle_score + joy_score
    return round(raw / 7.9, 2)   # normalize to ~0-10


def confidence_label(n):
    """Return a confidence label based on sample size."""
    if n >= CONFIDENCE_THRESHOLDS["reliable"]:    return "reliable"
    if n >= CONFIDENCE_THRESHOLDS["established"]: return "established"
    if n >= CONFIDENCE_THRESHOLDS["provisional"]: return "provisional"
    if n >= CONFIDENCE_THRESHOLDS["emerging"]:    return "emerging"
    return "sparse"


def confidence_bar(n, max_n=50):
    filled = min(int(n / max_n * 10), 10)
    return "▓" * filled + "░" * (10 - filled)


# ── Analysis ──────────────────────────────────────────────────────────────────

def load_log(path=None):
    p = path or DEFAULT_LOG
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def scored_entries(entries):
    """Return entries enriched with reflection_score."""
    result = []
    for e in entries:
        e2 = dict(e)
        e2["reflection_score"] = score_reflection(e.get("reflection") or "")
        e2["has_reflection"]   = bool(e.get("reflection"))
        result.append(e2)
    return result


def mine_by_dimension(entries, dim_key, dim_label):
    """
    Group entries by a dimension (purpose_pos, stage_num, value, domain)
    and compute: count, reflection rate, avg score, best reflection.

    Returns list of group dicts sorted by avg_score desc.
    """
    groups = defaultdict(list)
    for e in entries:
        k = e.get(dim_key)
        if k is not None:
            groups[k].append(e)

    results = []
    for key, group in groups.items():
        reflected  = [e for e in group if e["has_reflection"]]
        scores     = [e["reflection_score"] for e in reflected]
        avg_score  = round(sum(scores) / len(scores), 2) if scores else 0.0
        best       = max(reflected, key=lambda e: e["reflection_score"]) if reflected else None

        results.append({
            "key":          key,
            "total":        len(group),
            "reflected":    len(reflected),
            "rate":         round(len(reflected) / len(group), 2) if group else 0.0,
            "avg_score":    avg_score,
            "best":         best,
            "confidence":   confidence_label(len(reflected)),
        })

    return sorted(results, key=lambda x: (x["avg_score"], x["rate"]), reverse=True)


def correlate_aligned(entries):
    """Compare reflection richness on ✦ aligned vs. non-aligned days."""
    aligned     = [e for e in entries if e.get("aligned")]
    not_aligned = [e for e in entries if not e.get("aligned")]

    def stats(group):
        reflected = [e for e in group if e["has_reflection"]]
        scores    = [e["reflection_score"] for e in reflected]
        return {
            "total":     len(group),
            "reflected": len(reflected),
            "rate":      round(len(reflected) / len(group), 2) if group else 0.0,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        }

    return {
        "aligned":     stats(aligned),
        "not_aligned": stats(not_aligned),
    }


# ── Display ───────────────────────────────────────────────────────────────────

def _star(score):
    """Convert 0-10 score to star rating."""
    filled = max(0, min(5, round(score / 2)))
    return "★" * filled + "☆" * (5 - filled)


def print_mining_report(entries):
    se     = scored_entries(entries)
    total  = len(se)
    has_r  = [e for e in se if e["has_reflection"]]
    no_r   = [e for e in se if not e["has_reflection"]]

    print(f"\n{DSEP}")
    print(f"  REFLECTION MINER  ·  {total} entries  ·  {len(has_r)} with reflections")
    print(DSEP)

    if total == 0:
        print(f"\n  No entries. Run: python unified_daily.py --log\n")
        print(DSEP + "\n")
        return

    # Readiness indicators
    print(f"\n  Data readiness")
    for label, threshold in CONFIDENCE_THRESHOLDS.items():
        bar  = confidence_bar(len(has_r), threshold)
        need = max(0, threshold - len(has_r))
        note = f"  ← {need} more reflections" if need > 0 else "  ✓"
        print(f"    {label:<14}  {bar}  {len(has_r):>3}/{threshold}{note}")

    # Aligned correlation
    print(f"\n  ✦ Aligned day correlation")
    corr = correlate_aligned(se)
    for label, stats in [("✦ aligned", corr["aligned"]), ("non-aligned", corr["not_aligned"])]:
        if stats["total"] > 0:
            print(f"    {label:<14}  {stats['total']:>3} days  "
                  f"{stats['reflected']:>2} reflected ({stats['rate']*100:.0f}%)  "
                  f"avg score {stats['avg_score']:.1f}")

    # Top patterns by purpose
    print(f"\n  Purpose positions  (by reflection richness)")
    groups = mine_by_dimension(se, "purpose_pos", "purpose")
    for g in groups[:5]:
        purpose_name = next((e["purpose"] for e in se if e.get("purpose_pos") == g["key"]), str(g["key"]))
        conf = f"[{g['confidence']}]" if g["confidence"] != "reliable" else ""
        print(f"    P{g['key']} {purpose_name:<22}  "
              f"{g['reflected']}/{g['total']} reflected  "
              f"score {g['avg_score']:.1f}  {conf}")

    # Top patterns by stage
    print(f"\n  Self-determination stages  (by reflection richness)")
    groups = mine_by_dimension(se, "stage_num", "stage")
    for g in groups[:5]:
        stage_name = next((e.get("stage_name", "") for e in se if e.get("stage_num") == g["key"]), "")
        conf = f"[{g['confidence']}]" if g["confidence"] != "reliable" else ""
        print(f"    St{g['key']:>2} {stage_name:<20}  "
              f"{g['reflected']}/{g['total']} reflected  "
              f"score {g['avg_score']:.1f}  {conf}")

    # Top patterns by value
    print(f"\n  Governing values  (by reflection richness)")
    groups = mine_by_dimension(se, "value", "value")
    for g in groups:
        conf = f"[{g['confidence']}]" if g["confidence"] != "reliable" else ""
        print(f"    {str(g['key']):<30}  "
              f"{g['reflected']}/{g['total']} reflected  "
              f"score {g['avg_score']:.1f}  {conf}")

    # Best reflections
    best = sorted(has_r, key=lambda e: e["reflection_score"], reverse=True)[:3]
    if best:
        print(f"\n  Highest-scored reflections")
        for e in best:
            stars = _star(e["reflection_score"])
            print(f"    {e['date']}  P{e['purpose_pos']} St{e['stage_num']}  "
                  f"{stars}  {e['reflection_score']:.1f}")
            print(f"      ↳ {e['reflection']}")

    # Emerging patterns (narrative)
    print(f"\n  Emerging observations  [{confidence_label(len(has_r))} data]")
    if len(has_r) == 0:
        print(f"    No reflections yet. Add one: python unified_daily.py --reflect \"...\"")
    elif len(has_r) < CONFIDENCE_THRESHOLDS["emerging"]:
        print(f"    {len(has_r)} reflection(s) recorded. Patterns surface at 3+.")
        for e in has_r:
            print(f"    · {e['date']}  P{e['purpose_pos']} St{e['stage_num']}  "
                  f"score {e['reflection_score']:.1f}  — {e['reflection'][:60]}…" if len(e['reflection']) > 60
                  else f"    · {e['date']}  P{e['purpose_pos']} St{e['stage_num']}  "
                  f"score {e['reflection_score']:.1f}  — {e['reflection']}")
    else:
        # Enough data for observations
        by_purpose = mine_by_dimension(se, "purpose_pos", "purpose")
        by_stage   = mine_by_dimension(se, "stage_num",   "stage")
        top_p = by_purpose[0] if by_purpose else None
        top_s = by_stage[0]   if by_stage   else None
        if top_p and top_p["reflected"] >= 2:
            pname = next((e["purpose"] for e in se if e.get("purpose_pos") == top_p["key"]), str(top_p["key"]))
            print(f"    · P{top_p['key']} {pname} produces the richest reflections so far "
                  f"(avg {top_p['avg_score']:.1f})")
        if top_s and top_s["reflected"] >= 2:
            sname = next((e.get("stage_name", "") for e in se if e.get("stage_num") == top_s["key"]), "")
            print(f"    · Stage {top_s['key']} {sname} is most generative by stage "
                  f"(avg {top_s['avg_score']:.1f})")
        aligned_c = corr["aligned"]
        not_al_c  = corr["not_aligned"]
        if aligned_c["total"] >= 2 and not_al_c["total"] >= 2:
            if aligned_c["avg_score"] > not_al_c["avg_score"]:
                print(f"    · ✦ Aligned days yield richer reflections "
                      f"({aligned_c['avg_score']:.1f} vs {not_al_c['avg_score']:.1f})")
            else:
                print(f"    · Non-aligned days are currently more reflective "
                      f"({not_al_c['avg_score']:.1f} vs {aligned_c['avg_score']:.1f})")

    print(f"\n{DSEP}\n")


def print_by_dimension(entries, dim):
    se = scored_entries(entries)
    dim_map = {
        "purpose": ("purpose_pos", "purpose",    "Purpose Positions"),
        "stage":   ("stage_num",   "stage_name", "Self-Determination Stages"),
        "value":   ("value",       "value",      "Governing Values"),
        "domain":  ("domain",      "domain",     "Domains in Frame"),
    }
    dim_key, name_key, label = dim_map[dim]

    groups_data = defaultdict(list)
    for e in se:
        k = e.get(dim_key)
        if k is not None:
            groups_data[k].append(e)

    print(f"\n{DSEP}")
    print(f"  REFLECTIONS BY {label.upper()}  ·  {len(se)} entries")
    print(DSEP)

    for key in sorted(groups_data.keys(), key=lambda k: str(k)):
        group     = groups_data[key]
        reflected = [e for e in group if e["has_reflection"]]
        name      = next((e.get(name_key, "") for e in group if e.get(name_key)), "")
        heading   = f"P{key} {name}" if dim == "purpose" else (
                    f"Stage {key} · {name}" if dim == "stage" else str(key))

        print(f"\n  {heading}")
        print(f"  {SEP[2:]}")
        print(f"  {len(group)} day(s)  ·  {len(reflected)} reflection(s)")

        if not reflected:
            print(f"  No reflections recorded.")
        else:
            for e in sorted(reflected, key=lambda e: e["reflection_score"], reverse=True):
                stars = _star(e["reflection_score"])
                print(f"  {e['date']}  {stars}  {e['reflection_score']:.1f}")
                print(f"    ↳ {e['reflection']}")

    print(f"\n{DSEP}\n")


def print_scored(entries):
    se      = scored_entries(entries)
    has_r   = [e for e in se if e["has_reflection"]]
    no_r    = [e for e in se if not e["has_reflection"]]
    ranked  = sorted(has_r, key=lambda e: e["reflection_score"], reverse=True)

    print(f"\n{DSEP}")
    print(f"  REFLECTION SCORES  ·  {len(has_r)} entries ranked")
    print(DSEP)

    if not ranked:
        print(f"\n  No reflections yet.")
        print(f"  Add one: python unified_daily.py --reflect \"...\"\n")
        print(DSEP + "\n")
        return

    print(f"\n  {'Date':<13}  {'P':<2}  {'St':<3}  {'Score':<6}  {'Stars':<5}  Reflection")
    print(f"  {SEP[2:]}")
    for e in ranked:
        stars = _star(e["reflection_score"])
        trunc = e["reflection"][:55] + "…" if len(e["reflection"]) > 55 else e["reflection"]
        print(f"  {e['date']:<13}  P{e['purpose_pos']:<2}  {e['stage_num']:>2}     "
              f"{e['reflection_score']:<6.1f}  {stars}  {trunc}")

    if no_r:
        print(f"\n  {len(no_r)} day(s) with no reflection recorded.")

    scores = [e["reflection_score"] for e in has_r]
    print(f"\n  Range: {min(scores):.1f} – {max(scores):.1f}  ·  "
          f"Mean: {sum(scores)/len(scores):.1f}  ·  "
          f"Median: {sorted(scores)[len(scores)//2]:.1f}")

    print(f"\n{DSEP}\n")


def print_show(entries):
    se    = scored_entries(entries)
    has_r = [e for e in se if e["has_reflection"]]

    print(f"\n{DSEP}")
    print(f"  ALL REFLECTIONS  ·  {len(has_r)} recorded  ·  {len(se)} total entries")
    print(DSEP)

    if not has_r:
        print(f"\n  None yet. Add one: python unified_daily.py --reflect \"...\"\n")
        print(DSEP + "\n")
        return

    for e in sorted(has_r, key=lambda e: e["date"], reverse=True):
        aligned_mark = "  ✦" if e.get("aligned") else ""
        stars = _star(e["reflection_score"])
        print(f"\n  {e['date']}  P{e['purpose_pos']} {e.get('purpose', ''):<22}"
              f"  St{e['stage_num']:>2} {e.get('stage_name', '')}{aligned_mark}")
        print(f"  {stars}  {e['reflection_score']:.1f}  —  {e.get('domain', '')}  ·  {e.get('value', '')}")
        print(f"    ↳ {e['reflection']}")
        print(f"  {SEP[2:]}")

    print()


def write_log_export(entries, path=None):
    """
    Write a human-readable narrative archive of the full daily log —
    the living record of how attention, intelligence, and energy were invested.
    Every entry is included; reflections are given prominence.
    """
    se       = scored_entries(entries)
    has_r    = [e for e in se if e["has_reflection"]]
    W        = 70
    BAR      = "═" * W
    SEP      = "─" * W
    generated = __import__("datetime").date.today().isoformat()

    lines = []
    lines += [
        BAR,
        f"  CON-SCIRE DAILY LOG — NARRATIVE ARCHIVE",
        BAR,
        f"",
        f"  Generated:    {generated}",
        f"  Total entries: {len(se)}",
        f"  Reflections:   {len(has_r)}",
        f"",
        f'  "Each entry is a dated artifact of how intelligence, energy,',
        f'   and attention were invested on that day."',
        f"",
        BAR,
        f"",
    ]

    # Full chronological record
    for e in sorted(se, key=lambda x: x["date"]):
        aligned_mark = "  ✦ ALIGNED" if e.get("aligned") else ""
        triple_mark  = "  ◈ TRIPLE"  if e.get("purpose_pos") == e.get("stage_num") else ""
        lines.append(f"  {e['date']}  {e.get('moon_emoji','')}  "
                     f"P{e['purpose_pos']} {e.get('purpose',''):<22}"
                     f"  Stage {e.get('stage_num',''):>2}{aligned_mark}{triple_mark}")
        lines.append(f"  Domain: {e.get('domain','—'):<28}  Value: {e.get('value','—')}")
        if e["has_reflection"]:
            stars = _star(e["reflection_score"])
            lines.append(f"  {stars}  [{e['reflection_score']:.1f}]  \"{e['reflection']}\"")
        lines.append(f"  {SEP}")
        lines.append("")

    # Pattern summary
    by_purpose = mine_by_dimension(se, "purpose_pos", "purpose")
    by_stage   = mine_by_dimension(se, "stage_num",   "stage")
    by_value   = mine_by_dimension(se, "value",       "value")

    lines += [BAR, f"  PATTERNS  ·  {confidence_label(len(has_r)).upper()} DATA", BAR, ""]

    lines.append(f"  Purpose positions by reflection richness:")
    for g in by_purpose:
        if g["reflected"] == 0:
            continue
        pname = next((e.get("purpose","") for e in se if e.get("purpose_pos") == g["key"]), "")
        lines.append(f"    P{g['key']} {pname:<22}  {g['reflected']}/{g['total']}  "
                     f"avg {g['avg_score']:.1f}  [{g['confidence']}]")
    lines.append("")

    lines.append(f"  Stages by reflection richness:")
    for g in by_stage:
        if g["reflected"] == 0:
            continue
        sname = next((e.get("stage_name","") for e in se if e.get("stage_num") == g["key"]), "")
        lines.append(f"    Stage {g['key']:>2} {sname:<20}  {g['reflected']}/{g['total']}  "
                     f"avg {g['avg_score']:.1f}  [{g['confidence']}]")
    lines.append("")

    lines.append(f"  Values when reflections were written:")
    for g in by_value:
        if g["reflected"] == 0:
            continue
        lines.append(f"    {str(g['key']):<30}  {g['reflected']}/{g['total']}  "
                     f"avg {g['avg_score']:.1f}  [{g['confidence']}]")
    lines.append("")

    # Readiness
    lines += [SEP, "  DATA READINESS", SEP]
    for label, threshold in CONFIDENCE_THRESHOLDS.items():
        need = max(0, threshold - len(has_r))
        note = f"← {need} more" if need > 0 else "✓ reached"
        lines.append(f"  {label:<14}  {len(has_r):>3}/{threshold:<4}  {note}")
    lines.append("")

    lines += [BAR, f"  End of archive — {generated}", BAR, ""]

    content = "\n".join(lines)

    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print(content)

    return content


def main():
    parser = argparse.ArgumentParser(
        description="Reflection Miner — pattern analysis of daily log reflections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python reflect_mine.py\n"
            "  python reflect_mine.py --by purpose\n"
            "  python reflect_mine.py --by stage\n"
            "  python reflect_mine.py --by value\n"
            "  python reflect_mine.py --by domain\n"
            "  python reflect_mine.py --score\n"
            "  python reflect_mine.py --show\n"
            "  python reflect_mine.py --export log_archive.txt\n"
            "  python reflect_mine.py --log /path/to/log.json"
        ),
    )
    parser.add_argument("--by",     metavar="DIMENSION",
                        choices=["purpose", "stage", "value", "domain"],
                        help="Group reflections by purpose, stage, value, or domain")
    parser.add_argument("--score",  action="store_true", help="Rank all reflections by richness score")
    parser.add_argument("--show",   action="store_true", help="List all entries that have reflections")
    parser.add_argument("--export", metavar="FILE",      help="Write narrative archive to file")
    parser.add_argument("--log",    metavar="FILE",      help=f"Alternate log file (default: {DEFAULT_LOG})")
    args = parser.parse_args()

    entries = load_log(args.log)

    if args.export:
        write_log_export(entries, path=args.export)
        print(f"  Archive written → {args.export}")
    elif args.by:
        print_by_dimension(entries, args.by)
    elif args.score:
        print_scored(entries)
    elif args.show:
        print_show(entries)
    else:
        print_mining_report(entries)


if __name__ == "__main__":
    main()
