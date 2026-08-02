#!/usr/bin/env python3
"""donation_station.py — Donation Station lifecycle management system.

Every donated item moves through four stages in order:
  1. intake      — item is received and logged
  2. qc          — item is inspected for quality; maintenance flagged if needed
  3. storage     — item is assigned a location in inventory
  4. distributed — item is sent to its recipient

Each stage is recorded with a timestamp, operator, and notes.
The full history of every item is preserved.

Usage:
  python donation_station.py intake "Winter Jacket" --category clothing --condition good --donor "Jane Smith"
  python donation_station.py process DS-0001 --pass --by "Staff" --notes "Clean, no repairs needed"
  python donation_station.py process DS-0001 --fail --maintenance "Needs zipper repair"
  python donation_station.py store DS-0001 B-3 --notes "Shelf 3, bin 2"
  python donation_station.py distribute DS-0001 "Community Center" --notes "Delivered Tuesday"

  python donation_station.py status DS-0001
  python donation_station.py list
  python donation_station.py list --stage qc
  python donation_station.py search "Jane"
  python donation_station.py report
  python donation_station.py export
  python donation_station.py export --out /path/to/file.csv
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

try:
    import power_connection as _pc
except ImportError:
    _pc = None

# ── Storage ───────────────────────────────────────────────────────────────────

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         ".donation_station_data.json")

STAGES    = ("intake", "qc", "storage", "distributed")
CONDITIONS = ("good", "fair", "poor")
WIDTH     = 70
BAR       = "─" * WIDTH

# ── T.I.E.R. classification ───────────────────────────────────────────────────
#
#   T — Time        : volunteer hours, presence, effort, service
#   I — Intelligence: knowledge, skills, education, planning, strategy
#   E — Energy      : financial, currency, funding — concentrated transferable energy
#   R — Resources   : physical things that meet tangible needs
#
TIER_LABELS = {
    "T": "Time",
    "I": "Intelligence",
    "E": "Energy",
    "R": "Resources",
}

TIER_MAP = {
    # T — Time
    "volunteer":   "T",
    "service":     "T",
    "time":        "T",
    # I — Intelligence
    "knowledge":     "I",
    "education":     "I",
    "skills":        "I",
    "training":      "I",
    "planning":      "I",
    "information":   "I",
    "strategy":      "I",
    "data":          "I",
    "study":         "I",
    "study session": "I",
    "workshop":      "I",
    "mentorship":    "I",
    "coaching":      "I",
    # E — Energy
    "financial":   "E",
    "money":       "E",
    "currency":    "E",
    "funding":     "E",
    "grant":       "E",
    # R — Resources (default for physical goods)
    "food":        "R",
    "clothing":    "R",
    "shelter":     "R",
    "technology":  "R",
    "hygiene":     "R",
    "household":   "R",
    "electronics": "R",
    "tools":       "R",
    "equipment":   "R",
    "general":     "R",
}


def classify_tier(category):
    """Return the T.I.E.R. letter for a given category. Defaults to R."""
    return TIER_MAP.get(category.lower().strip(), "R")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _power_date(timestamp):
    """Return power connection data for a YYYY-MM-DDTHH:MM:SSZ timestamp."""
    if _pc is None:
        return None
    y, m, d = (int(p) for p in timestamp[:10].split("-"))
    r = _pc.calculate(m, d, y)
    return {
        "root":      r["root"]["raw"],
        "root_born": r["root"]["born"],
        "born":      r["born"],
        "born_name": _pc.SINGLE_MEANINGS.get(r["born"], ("", ""))[0],
    }


def _load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"next_id": 1, "items": {}}


def _save(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)


def _next_id(db):
    n  = db["next_id"]
    db["next_id"] += 1
    return f"DS-{n:04d}"


# ── Core operations ───────────────────────────────────────────────────────────

def intake(name, category="general", condition="good", donor="", notes="", by=""):
    db      = _load()
    item_id = _next_id(db)
    tier    = classify_tier(category)
    ts      = _now()
    item = {
        "id":        item_id,
        "name":      name,
        "category":  category,
        "tier":      tier,
        "condition": condition,
        "donor":     donor,
        "stage":     "intake",
        "history":   [
            {
                "stage":     "intake",
                "timestamp": ts,
                "by":        by,
                "notes":     notes,
            }
        ],
    }
    pd = _power_date(ts)
    if pd:
        item["power_date"] = pd
    db["items"][item_id] = item
    _save(db)
    return item


def process_qc(item_id, passed, by="", notes="", maintenance=""):
    db   = _load()
    item = _get_item(db, item_id)
    if item["stage"] != "intake":
        raise ValueError(f"{item_id} is at stage '{item['stage']}', expected 'intake'.")
    event = {
        "stage":        "qc",
        "timestamp":    _now(),
        "by":           by,
        "passed":       passed,
        "notes":        notes,
        "maintenance":  maintenance,
    }
    item["history"].append(event)
    item["stage"] = "qc"
    if not passed:
        item["maintenance_needed"] = maintenance or "unspecified"
    _save(db)
    return item


def store(item_id, location, by="", notes=""):
    db   = _load()
    item = _get_item(db, item_id)
    if item["stage"] != "qc":
        raise ValueError(f"{item_id} is at stage '{item['stage']}', expected 'qc'.")
    qc_event = next((e for e in reversed(item["history"]) if e["stage"] == "qc"), None)
    if qc_event and not qc_event.get("passed", True):
        raise ValueError(f"{item_id} did not pass QC. Complete maintenance before storing.")
    event = {
        "stage":     "storage",
        "timestamp": _now(),
        "location":  location,
        "by":        by,
        "notes":     notes,
    }
    item["history"].append(event)
    item["stage"]    = "storage"
    item["location"] = location
    _save(db)
    return item


def distribute(item_id, recipient, by="", notes=""):
    db   = _load()
    item = _get_item(db, item_id)
    if item["stage"] != "storage":
        raise ValueError(f"{item_id} is at stage '{item['stage']}', expected 'storage'.")
    event = {
        "stage":     "distributed",
        "timestamp": _now(),
        "recipient": recipient,
        "by":        by,
        "notes":     notes,
    }
    item["history"].append(event)
    item["stage"]     = "distributed"
    item["recipient"] = recipient
    _save(db)
    return item


def get_status(item_id):
    db = _load()
    return _get_item(db, item_id)


def list_items(stage=None):
    db = _load()
    items = list(db["items"].values())
    if stage and stage != "all":
        items = [i for i in items if i["stage"] == stage]
    return items


def search(query):
    db = _load()
    q  = query.lower().strip()
    results = []
    for item in db["items"].values():
        haystack = " ".join(filter(None, [
            item["name"],
            item.get("donor", ""),
            item.get("recipient", ""),
            item.get("category", ""),
            item.get("location", ""),
        ] + [e.get("notes", "") for e in item["history"]])).lower()
        if q in haystack:
            results.append(item)
    return results


def report():
    db    = _load()
    items = list(db["items"].values())
    total = len(items)
    by_stage    = {s: 0 for s in STAGES}
    by_category = {}
    by_tier     = {"T": 0, "I": 0, "E": 0, "R": 0}
    maintenance_pending = 0
    for item in items:
        by_stage[item["stage"]] = by_stage.get(item["stage"], 0) + 1
        cat = item.get("category", "general")
        by_category[cat] = by_category.get(cat, 0) + 1
        tier = item.get("tier") or classify_tier(cat)
        by_tier[tier] = by_tier.get(tier, 0) + 1
        if item.get("maintenance_needed") and item["stage"] != "distributed":
            maintenance_pending += 1
    return {
        "total":               total,
        "by_stage":            by_stage,
        "by_category":         by_category,
        "by_tier":             by_tier,
        "maintenance_pending": maintenance_pending,
    }


def export(path=None):
    import csv
    db    = _load()
    items = list(db["items"].values())

    TIER_NAMES = {"T": "T — Time", "I": "I — Intelligence",
                  "E": "E — Energy", "R": "R — Resources"}

    rows = []
    for item in items:
        def _ev(stage):
            return next((e for e in item["history"] if e["stage"] == stage), {})
        intake = _ev("intake")
        qc     = _ev("qc")
        dist   = _ev("distributed")
        tier   = item.get("tier") or classify_tier(item.get("category", "general"))
        pd = item.get("power_date", {})
        rows.append({
            "Name":             item["name"],
            "Item ID":          item["id"],
            "T.I.E.R.":        TIER_NAMES.get(tier, tier),
            "Category":         item.get("category", ""),
            "Condition":        item.get("condition", ""),
            "Stage":            item["stage"],
            "Donor":            item.get("donor", ""),
            "Recipient":        item.get("recipient", ""),
            "Location":         item.get("location", ""),
            "Date Received":    intake.get("timestamp", "")[:10],
            "Date Distributed": dist.get("timestamp", "")[:10],
            "Received By":      intake.get("by", ""),
            "Distributed By":   dist.get("by", ""),
            "QC Result":        "Pass" if qc.get("passed") else ("Fail" if qc else ""),
            "Power Root":       pd.get("root", ""),
            "Power Born":       pd.get("born", ""),
            "Power Born Name":  pd.get("born_name", ""),
            "Notes":            intake.get("notes", ""),
        })

    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "donation_station_export.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    return path, len(rows)


def _get_item(db, item_id):
    item = db["items"].get(item_id)
    if not item:
        raise KeyError(f"Item '{item_id}' not found.")
    return item


# ── Output ────────────────────────────────────────────────────────────────────

STAGE_LABELS = {
    "intake":      "INTAKE",
    "qc":          "QUALITY CONTROL",
    "storage":     "STORAGE",
    "distributed": "DISTRIBUTED",
}

STAGE_ICONS = {
    "intake":      "[1]",
    "qc":          "[2]",
    "storage":     "[3]",
    "distributed": "[4]",
}


def _fmt_event(event):
    s     = event["stage"]
    ts    = event.get("timestamp", "")[:16].replace("T", "  ")
    label = STAGE_LABELS.get(s, s.upper())
    icon  = STAGE_ICONS.get(s, "   ")
    lines = [f"  {icon}  {label}  —  {ts}"]
    if event.get("by"):
        lines.append(f"       By: {event['by']}")
    if s == "qc":
        result = "PASSED" if event.get("passed") else "FAILED"
        lines.append(f"       Result: {result}")
        if event.get("maintenance"):
            lines.append(f"       Maintenance: {event['maintenance']}")
    if s == "storage":
        lines.append(f"       Location: {event.get('location', '')}")
    if s == "distributed":
        lines.append(f"       Recipient: {event.get('recipient', '')}")
    if event.get("notes"):
        lines.append(f"       Notes: {event['notes']}")
    return "\n".join(lines)


def print_item(item, header="ITEM"):
    tier      = item.get("tier") or classify_tier(item.get("category", "general"))
    tier_name = TIER_LABELS.get(tier, tier)
    print(f"\n{BAR}")
    print(f"  {header}  —  {item['id']}  |  {item['name']}")
    print(f"  Category: {item['category']}  |  T.I.E.R.: {tier} — {tier_name}"
          + (f"  |  Condition: {item['condition']}" if item.get('condition') else ""))
    print(f"  Donor: {item.get('donor', '—')}  |  Stage: {STAGE_LABELS.get(item['stage'], item['stage'].upper())}")
    if item.get("location"):
        print(f"  Location: {item['location']}")
    if item.get("maintenance_needed"):
        print(f"  Maintenance: {item['maintenance_needed']}")
    if item.get("power_date"):
        pd = item["power_date"]
        print(f"  Power: Root {pd['root']} → {pd['root_born']}  |  Born {pd['born']} [{pd['born_name']}]")
    print(BAR)
    print()
    for event in item["history"]:
        print(_fmt_event(event))
        print()


def print_list(items):
    if not items:
        print("  No items found.")
        return
    print(f"\n{BAR}")
    print(f"  {'ID':<10}  {'NAME':<22}  {'TIER':<16}  {'STAGE':<14}  {'CATEGORY'}")
    print(BAR)
    for item in items:
        stage     = STAGE_LABELS.get(item["stage"], item["stage"])[:13]
        tier      = item.get("tier") or classify_tier(item.get("category", "general"))
        tier_name = TIER_LABELS.get(tier, tier)
        tier_col  = f"{tier} — {tier_name}"
        print(f"  {item['id']:<10}  {item['name'][:22]:<22}  {tier_col:<16}  {stage:<14}  {item.get('category','')}")
    print()


def print_report(r):
    print(f"\n{BAR}")
    print(f"  DONATION STATION  —  REPORT")
    print(BAR)
    print(f"\n  Total items:  {r['total']}")

    print(f"\n  T.I.E.R. Breakdown:")
    for letter in ("T", "I", "E", "R"):
        count     = r["by_tier"].get(letter, 0)
        tier_name = TIER_LABELS[letter]
        bar       = "█" * count
        print(f"    {letter} — {tier_name:<14}  {count:>4}  {bar}")

    print(f"\n  By Stage:")
    for stage in STAGES:
        count = r["by_stage"].get(stage, 0)
        bar   = "█" * count
        print(f"    {STAGE_LABELS[stage]:<16}  {count:>4}  {bar}")

    if r["by_category"]:
        print(f"\n  By Category:")
        for cat, count in sorted(r["by_category"].items(), key=lambda x: -x[1]):
            tier      = classify_tier(cat)
            tier_name = TIER_LABELS.get(tier, tier)
            print(f"    {cat:<20}  {count}  [{tier} — {tier_name}]")

    if r["maintenance_pending"]:
        print(f"\n  Maintenance pending:  {r['maintenance_pending']}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    argv = sys.argv[1:]
    use_json = "--json" in argv
    if use_json:
        argv = [a for a in argv if a != "--json"]

    if not argv:
        print(__doc__)
        return

    cmd  = argv[0]
    rest = argv[1:]

    try:
        if cmd == "intake":
            p = argparse.ArgumentParser(prog="donation_station intake")
            p.add_argument("name")
            p.add_argument("--category",  default="general")
            p.add_argument("--condition", default="good", choices=CONDITIONS)
            p.add_argument("--donor",     default="")
            p.add_argument("--notes",     default="")
            p.add_argument("--by",        default="")
            a    = p.parse_args(rest)
            item = intake(a.name, a.category, a.condition, a.donor, a.notes, a.by)
            if use_json:
                print(json.dumps(item, indent=2))
            else:
                print_item(item, "INTAKE RECEIVED")

        elif cmd == "process":
            p = argparse.ArgumentParser(prog="donation_station process")
            p.add_argument("item_id")
            grp = p.add_mutually_exclusive_group(required=True)
            grp.add_argument("--pass",  dest="passed", action="store_true")
            grp.add_argument("--fail",  dest="passed", action="store_false")
            p.add_argument("--by",          default="")
            p.add_argument("--notes",       default="")
            p.add_argument("--maintenance", default="")
            a    = p.parse_args(rest)
            item = process_qc(a.item_id, a.passed, a.by, a.notes, a.maintenance)
            if use_json:
                print(json.dumps(item, indent=2))
            else:
                print_item(item, "QC PROCESSED")

        elif cmd == "store":
            p = argparse.ArgumentParser(prog="donation_station store")
            p.add_argument("item_id")
            p.add_argument("location")
            p.add_argument("--by",    default="")
            p.add_argument("--notes", default="")
            a    = p.parse_args(rest)
            item = store(a.item_id, a.location, a.by, a.notes)
            if use_json:
                print(json.dumps(item, indent=2))
            else:
                print_item(item, "STORED")

        elif cmd == "distribute":
            p = argparse.ArgumentParser(prog="donation_station distribute")
            p.add_argument("item_id")
            p.add_argument("recipient")
            p.add_argument("--by",    default="")
            p.add_argument("--notes", default="")
            a    = p.parse_args(rest)
            item = distribute(a.item_id, a.recipient, a.by, a.notes)
            if use_json:
                print(json.dumps(item, indent=2))
            else:
                print_item(item, "DISTRIBUTED")

        elif cmd == "status":
            if not rest:
                sys.exit("Usage: donation_station.py status <item-id>")
            item = get_status(rest[0])
            if use_json:
                print(json.dumps(item, indent=2))
            else:
                print_item(item, "STATUS")

        elif cmd == "list":
            p = argparse.ArgumentParser(prog="donation_station list")
            p.add_argument("--stage", default="all",
                           choices=list(STAGES) + ["all"])
            a     = p.parse_args(rest)
            items = list_items(a.stage)
            if use_json:
                print(json.dumps(items, indent=2))
            else:
                print_list(items)

        elif cmd == "report":
            r = report()
            if use_json:
                print(json.dumps(r, indent=2))
            else:
                print_report(r)

        elif cmd == "search":
            if not rest:
                sys.exit("Usage: donation_station.py search <query>")
            results = search(" ".join(rest))
            if use_json:
                print(json.dumps(results, indent=2))
            else:
                if not results:
                    print(f"  No items matched '{' '.join(rest)}'.")
                else:
                    print_list(results)

        elif cmd == "export":
            p = argparse.ArgumentParser(prog="donation_station export")
            p.add_argument("--out", default=None, help="output file path")
            a        = p.parse_args(rest)
            path, n  = export(a.out)
            if use_json:
                print(json.dumps({"path": path, "count": n}))
            else:
                print(f"  Exported {n} item(s) → {path}")

        else:
            sys.exit(f"Unknown command '{cmd}'. Run without arguments for usage.")

    except (KeyError, ValueError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
