#!/usr/bin/env python3
"""
gen_year.py — Year cognitive calendar

Computes all 365 daily readings for a given year and surfaces patterns:
  · ✦ aligned days  (convergence = 6 · Equality)
  · ◈ triple alignments  (purpose position = stage number)
  · Purpose position distribution across the year
  · Stage cycle: which months complete a full 16-stage pass
  · Dominant values and domains by month

Usage:
  python gen_year.py                        # current year summary
  python gen_year.py --year 2027            # 2027 summary
  python gen_year.py --year 2027 --aligned  # list all ✦ aligned days
  python gen_year.py --year 2027 --triples  # list all ◈ triple days
  python gen_year.py --year 2027 --month 3  # March detail
  python gen_year.py --year 2027 --json     # full data to stdout
  python gen_year.py --year 2027 --out year_2027.json
"""

import argparse
import datetime
import json
import os
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))

from suprememath import Lexicon, compute_daily, DEFAULT_LEXICON_PATH
from suprememath.digits import day_of_year
import cognitive_functions as cf

SEP  = "─" * 66
DSEP = "═" * 66

MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _load_bridge():
    path = os.path.join(BASE, "data", "cf_bridge.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _stage_for_date(date):
    doy = day_of_year(date)
    return ((doy - 1) % 16) + 1


def generate_year(year, lexicon=None, quiet=False):
    """
    Compute a day dict for every day in year.
    Returns a list of 365 (or 366) dicts, one per calendar day.
    """
    if lexicon is None:
        lexicon = Lexicon(DEFAULT_LEXICON_PATH)

    bridge  = _load_bridge()
    cf_data = cf.load()
    days    = []

    start = datetime.date(year, 1, 1)
    end   = datetime.date(year, 12, 31)
    total = (end - start).days + 1

    d = start
    while d <= end:
        if not quiet:
            pct = int(((d - start).days + 1) / total * 40)
            bar = "█" * pct + "░" * (40 - pct)
            print(f"\r  [{bar}] {(d - start).days + 1}/{total}  {d}", end="", flush=True, file=sys.stderr)

        dt  = datetime.datetime(d.year, d.month, d.day, 12, 0)
        sm  = compute_daily(dt, lexicon)

        purpose_pos = sm["purpose"]["number"]
        stage_num   = _stage_for_date(d)
        conv        = sm["secondary"]["convergence"]

        key          = str(purpose_pos)
        domain_id    = bridge["sm_to_domain"].get(key)
        value_id     = bridge["sm_to_value"].get(key)
        domain_entry = next((e for e in cf_data["domains"] if e["id"] == domain_id), None)
        value_entry  = next((e for e in cf_data["values"]  if e["id"] == value_id),  None)
        stage_entry  = next((s for s in cf_data["stages"]["items"] if s["number"] == stage_num), None)

        days.append({
            "date":         str(d),
            "doy":          (d - start).days + 1,
            "month":        d.month,
            "month_name":   MONTHS[d.month],
            "purpose_pos":  purpose_pos,
            "purpose_name": sm["purpose"]["name"],
            "stage_num":    stage_num,
            "stage_name":   stage_entry["name"] if stage_entry else None,
            "aligned":      conv["aligned"],
            "convergence":  conv["number"],
            "domain":       domain_entry["name"] if domain_entry else None,
            "value":        value_entry["name"]  if value_entry  else None,
            "moon_emoji":   sm["moon"]["emoji"],
            "moon_phase":   sm["moon"]["phase"],
        })

        d += datetime.timedelta(days=1)

    if not quiet:
        print(file=sys.stderr)  # newline after progress bar

    return days


# ── Display ───────────────────────────────────────────────────────────────────

def print_year_summary(days, year):
    total        = len(days)
    aligned_days = [d for d in days if d["aligned"]]
    triple_days  = [d for d in days if d["purpose_pos"] == d["stage_num"]]
    both_days    = [d for d in days if d["aligned"] and d["purpose_pos"] == d["stage_num"]]

    purpose_counts = Counter(
        f"P{d['purpose_pos']} {d['purpose_name']}" for d in days
    )
    value_counts  = Counter(d["value"]  for d in days if d["value"])
    domain_counts = Counter(d["domain"] for d in days if d["domain"])
    moon_counts   = Counter(d["moon_phase"] for d in days)

    print(f"\n{DSEP}")
    print(f"  YEAR CALENDAR  ·  {year}  ·  {total} days")
    print(DSEP)

    print(f"\n  ✦ Aligned days  ({len(aligned_days)} total  ·  {len(aligned_days)/total*100:.1f}%)")
    for d in aligned_days:
        triple_mark = "  ◈" if d["purpose_pos"] == d["stage_num"] else ""
        print(f"    {d['date']}  {d['moon_emoji']}  "
              f"P{d['purpose_pos']} {d['purpose_name']:<22}"
              f"  Stage {d['stage_num']:>2} {d['stage_name']}{triple_mark}")

    print(f"\n  ◈ Triple alignments  ({len(triple_days)} total  ·  {len(triple_days)/total*100:.1f}%)")
    for d in triple_days:
        aligned_mark = "  ✦" if d["aligned"] else ""
        print(f"    {d['date']}  {d['moon_emoji']}  "
              f"P{d['purpose_pos']} {d['purpose_name']:<22}"
              f"  Stage {d['stage_num']:>2} {d['stage_name']}{aligned_mark}")

    if both_days:
        print(f"\n  ✦◈ Both  ({len(both_days)} total — rarest convergence)")
        for d in both_days:
            print(f"    {d['date']}  P{d['purpose_pos']} {d['purpose_name']}  Stage {d['stage_num']} {d['stage_name']}")

    print(f"\n  Purpose distribution")
    for label, count in sorted(purpose_counts.items()):
        bar = "█" * (count // 2)
        print(f"    {label:<30}  {count:>3}  {bar}")

    print(f"\n  Values governing")
    for label, count in value_counts.most_common():
        bar = "█" * (count // 3)
        print(f"    {label:<30}  {count:>3}  {bar}")

    print(f"\n  Domains in frame")
    for label, count in domain_counts.most_common():
        bar = "█" * (count // 3)
        print(f"    {label:<30}  {count:>3}  {bar}")

    print(f"\n  Stage cycle — full 16-stage passes complete at:")
    completions = [d["date"] for d in days if d["stage_num"] == 16]
    for dt_str in completions:
        print(f"    {dt_str}")

    print(f"\n  Moon phases")
    for phase, count in moon_counts.most_common():
        print(f"    {phase:<28}  {count:>3}")

    print(f"\n{DSEP}\n")


def print_aligned(days, year):
    aligned = [d for d in days if d["aligned"]]
    print(f"\n{DSEP}")
    print(f"  ✦ ALIGNED DAYS  ·  {year}  ·  {len(aligned)} total")
    print(DSEP)
    for d in aligned:
        triple_mark = "  ◈" if d["purpose_pos"] == d["stage_num"] else ""
        print(f"  {d['date']}  {d['moon_emoji']}  "
              f"P{d['purpose_pos']} {d['purpose_name']:<22}"
              f"  Stage {d['stage_num']:>2} {d['stage_name']:<18}"
              f"  {d['domain']}{triple_mark}")
    print(f"\n{DSEP}\n")


def print_triples(days, year):
    triples = [d for d in days if d["purpose_pos"] == d["stage_num"]]
    print(f"\n{DSEP}")
    print(f"  ◈ TRIPLE ALIGNMENTS  ·  {year}  ·  {len(triples)} total")
    print(DSEP)
    for d in triples:
        aligned_mark = "  ✦" if d["aligned"] else ""
        print(f"  {d['date']}  {d['moon_emoji']}  "
              f"P{d['purpose_pos']} {d['purpose_name']:<22}"
              f"  Stage {d['stage_num']:>2} {d['stage_name']:<18}"
              f"  {d['value']}{aligned_mark}")
    print(f"\n{DSEP}\n")


def write_annual_export(days, year, log_entries=None, path=None):
    """
    Write a human-readable annual summary document — the year-end heirloom record.
    Incorporates any reflections from the daily log for that year.
    """
    from collections import Counter as _Counter

    total        = len(days)
    aligned_days = [d for d in days if d["aligned"]]
    triple_days  = [d for d in days if d["purpose_pos"] == d["stage_num"]]
    both_days    = [d for d in days if d["aligned"] and d["purpose_pos"] == d["stage_num"]]

    purpose_counts = _Counter(f"P{d['purpose_pos']} {d['purpose_name']}" for d in days)
    value_counts   = _Counter(d["value"]  for d in days if d["value"])
    domain_counts  = _Counter(d["domain"] for d in days if d["domain"])

    year_log = []
    if log_entries:
        year_str = str(year)
        year_log = [e for e in log_entries if e.get("date", "").startswith(year_str)]

    generated = datetime.date.today().isoformat()
    W = 70
    BAR = "═" * W
    SEP = "─" * W

    lines = []
    lines += [
        BAR,
        f"  CON-SCIRE ANNUAL SUMMARY",
        f"  {year}",
        BAR,
        f"",
        f"  Generated:   {generated}",
        f"  Days:        {total}",
        f"  Aligned (✦): {len(aligned_days)}  ({len(aligned_days)/total*100:.1f}%)",
        f"  Triple  (◈): {len(triple_days)}  ({len(triple_days)/total*100:.1f}%)",
        f"  Both   (✦◈): {len(both_days)}  (rarest convergence)",
        f"",
    ]

    # Aligned days
    lines += [SEP, f"  ✦ ALIGNED DAYS  ({len(aligned_days)} total)", SEP]
    for d in aligned_days:
        tm = "  ◈" if d["purpose_pos"] == d["stage_num"] else ""
        lines.append(f"  {d['date']}  {d['moon_emoji']}  "
                     f"P{d['purpose_pos']} {d['purpose_name']:<22}"
                     f"  Stage {d['stage_num']:>2} {d['stage_name']}{tm}")
    lines.append("")

    # Triple alignments
    lines += [SEP, f"  ◈ TRIPLE ALIGNMENTS  ({len(triple_days)} total  ·  purpose = stage)", SEP]
    for d in triple_days:
        am = "  ✦" if d["aligned"] else ""
        lines.append(f"  {d['date']}  {d['moon_emoji']}  "
                     f"P{d['purpose_pos']} {d['purpose_name']:<22}"
                     f"  Stage {d['stage_num']:>2} {d['stage_name']}{am}")
    lines.append("")

    # Purpose distribution
    lines += [SEP, f"  PURPOSE DISTRIBUTION", SEP]
    for label, count in sorted(purpose_counts.items()):
        bar = "█" * (count // 2)
        lines.append(f"  {label:<30}  {count:>3}  {bar}")
    lines.append("")

    # Values and domains
    lines += [SEP, f"  VALUES GOVERNING", SEP]
    for label, count in value_counts.most_common():
        lines.append(f"  {label:<30}  {count:>3}")
    lines.append("")

    lines += [SEP, f"  DOMAINS IN FRAME", SEP]
    for label, count in domain_counts.most_common():
        lines.append(f"  {label:<30}  {count:>3}")
    lines.append("")

    # Stage cycle completions
    completions = [d["date"] for d in days if d["stage_num"] == 16]
    lines += [SEP, f"  STAGE CYCLE COMPLETIONS  ({len(completions)} full passes)", SEP]
    for dt_str in completions:
        lines.append(f"  {dt_str}")
    lines.append("")

    # Reflections from this year
    if year_log:
        reflected = [e for e in year_log if e.get("reflection")]
        lines += [SEP, f"  REFLECTIONS  ({len(reflected)} recorded  ·  {len(year_log)} entries)", SEP]
        for e in sorted(reflected, key=lambda x: x["date"]):
            aligned_mark = "  ✦" if e.get("aligned") else ""
            lines.append(f"")
            lines.append(f"  {e['date']}  P{e['purpose_pos']} {e.get('purpose',''):<22}"
                         f"  Stage {e['stage_num']:>2} {e.get('stage_name', '')}{aligned_mark}")
            lines.append(f"  Domain: {e.get('domain','—')}  ·  Value: {e.get('value','—')}")
            lines.append(f"    \"{e['reflection']}\"")
        if not reflected:
            lines.append(f"  None recorded for {year}.")
        lines.append("")

    lines += [BAR, f"  End of {year} — Con-Scire Annual Record", BAR, ""]

    content = "\n".join(lines)

    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print(content)

    return content


def print_month(days, month, year):
    month_days = [d for d in days if d["month"] == month]
    label = MONTHS[month]
    print(f"\n{DSEP}")
    print(f"  {label.upper()}  {year}  ·  {len(month_days)} days")
    print(DSEP)
    print()
    for d in month_days:
        aligned_mark = "  ✦" if d["aligned"] else ""
        triple_mark  = "  ◈" if d["purpose_pos"] == d["stage_num"] else ""
        print(f"  {d['date']}  {d['moon_emoji']}  "
              f"P{d['purpose_pos']} {d['purpose_name']:<22}"
              f"  St{d['stage_num']:>2} {d['stage_name']:<18}"
              f"  {d['domain'] or '—'}{aligned_mark}{triple_mark}")
    print(f"\n{DSEP}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Year Cognitive Calendar — SM + Cognitive Functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python gen_year.py\n"
            "  python gen_year.py --year 2027\n"
            "  python gen_year.py --year 2027 --aligned\n"
            "  python gen_year.py --year 2027 --triples\n"
            "  python gen_year.py --year 2027 --month 3\n"
            "  python gen_year.py --year 2027 --json\n"
            "  python gen_year.py --year 2027 --out year_2027.json\n"
            "  python gen_year.py --year 2026 --export annual_2026.txt"
        ),
    )
    parser.add_argument("--year",    type=int, metavar="YYYY",  help="Year to generate (default: current year)")
    parser.add_argument("--aligned", action="store_true",       help="List all ✦ aligned days")
    parser.add_argument("--triples", action="store_true",       help="List all ◈ triple alignments")
    parser.add_argument("--month",   type=int, metavar="1-12",  help="Show one month in detail")
    parser.add_argument("--json",    action="store_true",       help="Output full data as JSON to stdout")
    parser.add_argument("--out",     metavar="FILE",            help="Write full data JSON to file")
    parser.add_argument("--export",  metavar="FILE",            help="Write human-readable annual summary document")
    parser.add_argument("--log",     metavar="FILE",            help="Daily log JSON to include reflections in export")
    args = parser.parse_args()

    year = args.year or datetime.date.today().year

    if args.month and not (1 <= args.month <= 12):
        print("`--month` must be 1-12.")
        sys.exit(1)

    lexicon = Lexicon(DEFAULT_LEXICON_PATH)

    print(f"  Generating {year} calendar…", file=sys.stderr)
    days = generate_year(year, lexicon, quiet=args.json)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(days, f, indent=2, ensure_ascii=False)
        print(f"  Written {len(days)} days → {args.out}")
        return

    if args.json:
        print(json.dumps(days, indent=2))
        return

    if args.export:
        import daily_log as dl
        log_path    = args.log or dl.DEFAULT_LOG
        log_entries = dl.load_log(log_path)
        write_annual_export(days, year, log_entries=log_entries, path=args.export)
        print(f"  Annual export written → {args.export}", file=sys.stderr)
        return

    if args.aligned:
        print_aligned(days, year)
    elif args.triples:
        print_triples(days, year)
    elif args.month:
        print_month(days, args.month, year)
    else:
        print_year_summary(days, year)


if __name__ == "__main__":
    main()
