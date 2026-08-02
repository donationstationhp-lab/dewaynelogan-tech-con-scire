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

  # Lot tracking (Dart-style)
  python donation_station.py intake "Jacket" --lot LOT-0001
  python donation_station.py lot LOT-0001
  python donation_station.py lots

  # Location system (Target-style)
  python donation_station.py location add CL-A4 --zone clothing --capacity 20
  python donation_station.py location list
  python donation_station.py capacity

  # FIFO & pick lists (Target/Dart)
  python donation_station.py fifo
  python donation_station.py picklist
  python donation_station.py picklist --recipient "Matthew"

  # Labels
  python donation_station.py label DS-0001

  # Throughput & QC metrics (Dart-style)
  python donation_station.py metrics

  # Maintenance scheduling (Dart-style)
  python donation_station.py maintenance
  python donation_station.py maintain DS-0001 --due 2026-08-10 --by "Staff"
  python donation_station.py maintain DS-0001 --complete --notes "Zipper fixed" --by "Staff"

  # Perishables (Door to Door Organics-style)
  python donation_station.py intake "Apples" --category food --expiry 2026-08-05 --zone refrigerated --weight "10 lbs" --origin "Green Acres Farm"
  python donation_station.py expiring
  python donation_station.py expiring --days 5

  # Routes & delivery manifests (Door to Door Organics-style)
  python donation_station.py route add "North Loop" --description "North side residential stops"
  python donation_station.py route stop "North Loop" "Community Center" --address "123 Main St" --notes "Side door"
  python donation_station.py route list
  python donation_station.py manifest "North Loop"

  # Substitution notes on distribution
  python donation_station.py distribute DS-0001 "Recipient" --substitution "Swapped apples for pears"
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

try:
    import power_connection as _pc
except ImportError:
    _pc = None

# ── Storage ───────────────────────────────────────────────────────────────────

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         ".donation_station_data.json")

STAGES     = ("intake", "qc", "storage", "distributed")
CONDITIONS = ("good", "fair", "poor")
TEMP_ZONES = ("ambient", "refrigerated", "frozen")
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
            db = json.load(f)
        db.setdefault("next_lot", 1)
        db.setdefault("locations", {})
        db.setdefault("routes", {})
        return db
    return {"next_id": 1, "next_lot": 1, "items": {}, "locations": {}, "routes": {}}


def _save(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)


def _next_id(db):
    n  = db["next_id"]
    db["next_id"] += 1
    return f"DS-{n:04d}"


def _next_lot_id(db):
    n = db.get("next_lot", 1)
    db["next_lot"] = n + 1
    return f"LOT-{n:04d}"


# ── Core operations ───────────────────────────────────────────────────────────

def intake(name, category="general", condition="good", donor="", notes="", by="", lot="",
           expiry_date="", temp_zone="ambient", weight="", origin=""):
    db      = _load()
    item_id = _next_id(db)
    tier    = classify_tier(category)
    ts      = _now()
    if not lot:
        lot = _next_lot_id(db)
    if temp_zone and temp_zone not in TEMP_ZONES:
        raise ValueError(f"temp_zone must be one of: {', '.join(TEMP_ZONES)}")
    item = {
        "id":        item_id,
        "lot":       lot,
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
    if expiry_date:
        item["expiry_date"] = expiry_date
    if temp_zone and temp_zone != "ambient":
        item["temp_zone"] = temp_zone
    elif temp_zone == "ambient":
        item["temp_zone"] = "ambient"
    if weight:
        item["weight"] = weight
    if origin:
        item["origin"] = origin
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
    loc_data = db.get("locations", {}).get(location)
    if loc_data and loc_data.get("temp_zone") and item.get("temp_zone"):
        loc_zone  = loc_data["temp_zone"]
        item_zone = item["temp_zone"]
        if loc_zone != item_zone:
            raise ValueError(
                f"Temperature zone mismatch: item requires '{item_zone}' "
                f"but location {location} is '{loc_zone}'."
            )
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
    if location in db.get("locations", {}):
        db["locations"][location]["count"] = db["locations"][location].get("count", 0) + 1
    _save(db)
    return item


def distribute(item_id, recipient, by="", notes="", substitution=""):
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
    if substitution:
        event["substitution"] = substitution
    loc = item.get("location")
    item["history"].append(event)
    item["stage"]     = "distributed"
    item["recipient"] = recipient
    if loc and loc in db.get("locations", {}):
        db["locations"][loc]["count"] = max(0, db["locations"][loc].get("count", 1) - 1)
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


# ── Lot tracking (Dart) ──────────────────────────────────────────────────────

def lot_info(lot_id):
    db    = _load()
    items = [i for i in db["items"].values() if i.get("lot") == lot_id]
    if not items:
        raise KeyError(f"Lot '{lot_id}' not found.")
    return items


def lots_list():
    db   = _load()
    seen = {}
    for item in db["items"].values():
        lot = item.get("lot", "")
        if lot not in seen:
            seen[lot] = {"lot": lot, "count": 0, "stages": {}}
        seen[lot]["count"] += 1
        s = item["stage"]
        seen[lot]["stages"][s] = seen[lot]["stages"].get(s, 0) + 1
    return sorted(seen.values(), key=lambda x: x["lot"])


# ── Location system (Target) ──────────────────────────────────────────────────

def add_location(code, zone="", capacity=0, description="", temp_zone=""):
    db = _load()
    if temp_zone and temp_zone not in TEMP_ZONES:
        raise ValueError(f"temp_zone must be one of: {', '.join(TEMP_ZONES)}")
    loc = {
        "code":        code,
        "zone":        zone,
        "capacity":    capacity,
        "description": description,
        "count":       0,
    }
    if temp_zone:
        loc["temp_zone"] = temp_zone
    db["locations"][code] = loc
    _save(db)
    return db["locations"][code]


def list_locations():
    db = _load()
    return list(db.get("locations", {}).values())


def capacity_report():
    db   = _load()
    locs = list(db.get("locations", {}).values())
    items = list(db["items"].values())
    actual = {}
    for item in items:
        if item["stage"] == "storage" and item.get("location"):
            actual[item["location"]] = actual.get(item["location"], 0) + 1
    for loc in locs:
        loc["actual"] = actual.get(loc["code"], loc.get("count", 0))
    return locs


# ── FIFO & pick lists (Target/Dart) ──────────────────────────────────────────

def fifo_list():
    """Storage items sorted expiry-first (perishables soonest), then intake-date FIFO."""
    items = list_items("storage")

    def _intake_ts(item):
        ev = next((e for e in item["history"] if e["stage"] == "intake"), {})
        return ev.get("timestamp", "")

    def _sort_key(item):
        expiry = item.get("expiry_date", "")
        if expiry:
            return (0, expiry, _intake_ts(item))
        return (1, "", _intake_ts(item))

    return sorted(items, key=_sort_key)


def expiring(days=2):
    """Return storage items expiring within *days* days, with urgency flags."""
    items = list_items("storage")
    now   = datetime.now(timezone.utc)
    result = []
    for item in items:
        expiry = item.get("expiry_date", "")
        if not expiry:
            continue
        try:
            exp_dt    = datetime.strptime(expiry, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_left = (exp_dt.date() - now.date()).days
        except ValueError:
            continue
        if days_left <= days:
            if days_left < 0:
                urgency = "expired"
            elif days_left == 0:
                urgency = "critical"
            elif days_left == 1:
                urgency = "warning"
            else:
                urgency = "watch"
            result.append({**item, "_days_left": days_left, "_urgency": urgency})
    return sorted(result, key=lambda x: x["expiry_date"])


def pick_list(recipient=""):
    """Generate a pick list from storage items (expiry-first FIFO order)."""
    items = fifo_list()
    picks = []
    for i, item in enumerate(items, 1):
        ev = next((e for e in item["history"] if e["stage"] == "intake"), {})
        picks.append({
            "pick":      i,
            "id":        item["id"],
            "lot":       item.get("lot", ""),
            "name":      item["name"],
            "location":  item.get("location", "—"),
            "tier":      item.get("tier", "R"),
            "category":  item.get("category", ""),
            "intake_ts": ev.get("timestamp", "")[:10],
            "expiry":    item.get("expiry_date", ""),
            "temp_zone": item.get("temp_zone", "ambient"),
        })
    return {"recipient": recipient, "picks": picks, "total": len(picks)}


# ── Routes & manifests (Door to Door Organics) ───────────────────────────────

def add_route(name, description=""):
    db = _load()
    if name in db["routes"]:
        raise ValueError(f"Route '{name}' already exists.")
    db["routes"][name] = {"name": name, "description": description, "stops": []}
    _save(db)
    return db["routes"][name]


def add_route_stop(route_name, recipient, address="", notes=""):
    db = _load()
    if route_name not in db["routes"]:
        raise KeyError(f"Route '{route_name}' not found.")
    stop = {"recipient": recipient, "address": address, "notes": notes}
    db["routes"][route_name]["stops"].append(stop)
    _save(db)
    return db["routes"][route_name]


def list_routes():
    db = _load()
    return list(db.get("routes", {}).values())


def generate_manifest(route_name):
    db = _load()
    if route_name not in db.get("routes", {}):
        raise KeyError(f"Route '{route_name}' not found.")
    route   = db["routes"][route_name]
    items   = fifo_list()
    now     = datetime.now(timezone.utc)

    urgent, cold, normal = [], [], []
    for item in items:
        expiry = item.get("expiry_date", "")
        zone   = item.get("temp_zone", "ambient")
        if expiry:
            try:
                days_left = (datetime.strptime(expiry, "%Y-%m-%d").replace(tzinfo=timezone.utc).date()
                             - now.date()).days
            except ValueError:
                days_left = 999
            item = {**item, "_days_left": days_left,
                    "_urgency": "expired" if days_left < 0
                                else "critical" if days_left == 0
                                else "warning" if days_left == 1
                                else "watch"}
            urgent.append(item)
        elif zone in ("refrigerated", "frozen"):
            cold.append(item)
        else:
            normal.append(item)

    return {
        "route":        route_name,
        "description":  route.get("description", ""),
        "stops":        route.get("stops", []),
        "urgent":       urgent,
        "cold":         cold,
        "normal":       normal,
        "generated_at": _now(),
    }


# ── Throughput & QC metrics (Dart) ───────────────────────────────────────────

def metrics():
    db    = _load()
    items = list(db["items"].values())
    now   = datetime.now(timezone.utc)

    def _parse(ts):
        try:
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except Exception:
            return None

    def _intake_dt(item):
        ev = next((e for e in item["history"] if e["stage"] == "intake"), {})
        return _parse(ev.get("timestamp", ""))

    counts_today  = sum(1 for i in items if (d := _intake_dt(i)) and d.date() == now.date())
    counts_7d     = sum(1 for i in items if (d := _intake_dt(i)) and (now - d).days <= 7)
    counts_30d    = sum(1 for i in items if (d := _intake_dt(i)) and (now - d).days <= 30)

    stage_pairs = [("intake", "qc"), ("qc", "storage"), ("storage", "distributed")]
    velocity    = {}
    for s1, s2 in stage_pairs:
        deltas = []
        for item in items:
            t1 = next((_parse(e["timestamp"]) for e in item["history"] if e["stage"] == s1), None)
            t2 = next((_parse(e["timestamp"]) for e in item["history"] if e["stage"] == s2), None)
            if t1 and t2:
                deltas.append((t2 - t1).total_seconds() / 3600)
        velocity[f"{s1}→{s2}"] = round(sum(deltas) / len(deltas), 1) if deltas else None

    qc_events = [e for i in items for e in i["history"] if e["stage"] == "qc"]
    by_cat    = {}
    for item in items:
        qc = next((e for e in item["history"] if e["stage"] == "qc"), None)
        if qc:
            cat = item.get("category", "general")
            if cat not in by_cat:
                by_cat[cat] = {"pass": 0, "fail": 0}
            if qc.get("passed"):
                by_cat[cat]["pass"] += 1
            else:
                by_cat[cat]["fail"] += 1

    total_pass = sum(v["pass"] for v in by_cat.values())
    total_fail = sum(v["fail"] for v in by_cat.values())
    total_qc   = total_pass + total_fail

    maint_items = [i for i in items if i.get("maintenance_needed") and i["stage"] != "distributed"]
    overdue     = []
    for item in maint_items:
        due = item.get("maintenance_due")
        if due and due < now.strftime("%Y-%m-%d"):
            overdue.append(item)

    return {
        "throughput": {
            "today":   counts_today,
            "7_days":  counts_7d,
            "30_days": counts_30d,
        },
        "velocity": velocity,
        "qc": {
            "total":      total_qc,
            "pass":       total_pass,
            "fail":       total_fail,
            "pass_rate":  round(total_pass / total_qc * 100) if total_qc else 0,
            "by_category": by_cat,
        },
        "maintenance": {
            "pending": len(maint_items),
            "overdue": len(overdue),
        },
    }


# ── Maintenance scheduling (Dart) ─────────────────────────────────────────────

def maintenance_list():
    db = _load()
    return [i for i in db["items"].values()
            if i.get("maintenance_needed") and i["stage"] != "distributed"]


def schedule_maintenance(item_id, due="", by=""):
    db   = _load()
    item = _get_item(db, item_id)
    if not item.get("maintenance_needed"):
        raise ValueError(f"{item_id} has no maintenance flagged.")
    item["maintenance_due"] = due
    item["maintenance_assigned_to"] = by
    _save(db)
    return item


def complete_maintenance(item_id, notes="", by=""):
    db   = _load()
    item = _get_item(db, item_id)
    if not item.get("maintenance_needed"):
        raise ValueError(f"{item_id} has no maintenance flagged.")
    event = {
        "stage":     "qc",
        "timestamp": _now(),
        "by":        by,
        "passed":    True,
        "notes":     notes or "Maintenance completed.",
        "maintenance": item["maintenance_needed"],
    }
    item["history"].append(event)
    item["stage"]              = "qc"
    item["maintenance_needed"] = None
    item.pop("maintenance_due", None)
    item.pop("maintenance_assigned_to", None)
    _save(db)
    return item


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
            "Temp Zone":        item.get("temp_zone", ""),
            "Expiry Date":      item.get("expiry_date", ""),
            "Weight":           item.get("weight", ""),
            "Origin":           item.get("origin", ""),
            "Date Received":    intake.get("timestamp", "")[:10],
            "Date Distributed": dist.get("timestamp", "")[:10],
            "Received By":      intake.get("by", ""),
            "Distributed By":   dist.get("by", ""),
            "Substitution":     dist.get("substitution", ""),
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
        if event.get("substitution"):
            lines.append(f"       Substitution: {event['substitution']}")
    if event.get("notes"):
        lines.append(f"       Notes: {event['notes']}")
    return "\n".join(lines)


def _urgency_flag(item):
    """Return an urgency string for an item with expiry_date, or empty string."""
    expiry = item.get("expiry_date", "")
    if not expiry:
        return ""
    try:
        days_left = (datetime.strptime(expiry, "%Y-%m-%d").replace(tzinfo=timezone.utc).date()
                     - datetime.now(timezone.utc).date()).days
    except ValueError:
        return ""
    if days_left < 0:
        return " !! EXPIRED"
    if days_left == 0:
        return " !! EXPIRES TODAY"
    if days_left == 1:
        return " ! expires tomorrow"
    return f" (expires in {days_left}d)"


def print_item(item, header="ITEM"):
    tier      = item.get("tier") or classify_tier(item.get("category", "general"))
    tier_name = TIER_LABELS.get(tier, tier)
    print(f"\n{BAR}")
    print(f"  {header}  —  {item['id']}  |  {item['name']}")
    print(f"  Category: {item['category']}  |  T.I.E.R.: {tier} — {tier_name}"
          + (f"  |  Condition: {item['condition']}" if item.get('condition') else ""))
    print(f"  Lot: {item.get('lot', '—')}  |  Donor: {item.get('donor', '—')}  |  Stage: {STAGE_LABELS.get(item['stage'], item['stage'].upper())}")
    if item.get("location"):
        print(f"  Location: {item['location']}")
    if item.get("temp_zone") or item.get("expiry_date") or item.get("weight") or item.get("origin"):
        parts = []
        if item.get("temp_zone"):
            parts.append(f"Temp: {item['temp_zone']}")
        if item.get("expiry_date"):
            parts.append(f"Expiry: {item['expiry_date']}{_urgency_flag(item)}")
        if item.get("weight"):
            parts.append(f"Weight: {item['weight']}")
        if item.get("origin"):
            parts.append(f"Origin: {item['origin']}")
        print("  " + "  |  ".join(parts))
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


def print_label(item):
    tier      = item.get("tier") or classify_tier(item.get("category", "general"))
    tier_name = TIER_LABELS.get(tier, tier)
    ev_intake = next((e for e in item["history"] if e["stage"] == "intake"), {})
    lw = 46
    sep = "─" * lw
    print(f"\n┌{sep}┐")
    print(f"│  {'Item ID':<10}  {item['id']:<12}  {'Lot':<6}  {item.get('lot','—'):<10}│")
    print(f"│  {sep[:lw-2]}  │".replace("│  ─" * 23, f"│  {sep}  │"))
    print(f"│  {item['name'][:lw-2]:<{lw-2}}│")
    print(f"│  T.I.E.R.: {tier} — {tier_name:<{lw-14}}│")
    print(f"│  Category: {item.get('category',''):<16}  Condition: {item.get('condition',''):<6}│")
    if item.get("location"):
        print(f"│  Location: {item['location']:<{lw-12}}│")
    print(f"│  Intake: {ev_intake.get('timestamp','')[:10]:<12}  By: {ev_intake.get('by','—'):<{lw-26}}│")
    print(f"│  Donor: {item.get('donor','—')[:lw-9]:<{lw-9}}│")
    print(f"└{sep}┘")


def print_picklist(pl):
    recipient = pl.get("recipient") or "All"
    print(f"\n{BAR}")
    print(f"  PICK LIST  —  {recipient}")
    print(f"  {len(pl['picks'])} item(s)  |  perishables first, then FIFO")
    print(BAR)
    if not pl["picks"]:
        print("  No items in storage.\n")
        return
    print(f"\n  {'#':<4}  {'ID':<10}  {'LOT':<10}  {'LOCATION':<14}  {'EXPIRY':<12}  {'ZONE':<12}  NAME")
    print(f"  {'─'*4}  {'─'*10}  {'─'*10}  {'─'*14}  {'─'*12}  {'─'*12}  {'─'*20}")
    for p in pl["picks"]:
        print(f"  {p['pick']:<4}  {p['id']:<10}  {p['lot']:<10}  {p['location']:<14}  "
              f"{p['expiry'] or '—':<12}  {p['temp_zone']:<12}  {p['name'][:24]}")
    print()


def print_expiring(items, days):
    URGENCY_LABEL = {
        "expired":  "!! EXPIRED",
        "critical": "!! TODAY",
        "warning":  "!  TOMORROW",
        "watch":    "   SOON",
    }
    print(f"\n{BAR}")
    print(f"  EXPIRING — items expiring within {days} day(s)")
    print(BAR)
    if not items:
        print(f"  No items expiring within {days} day(s).\n")
        return
    print(f"\n  {'ID':<10}  {'NAME':<24}  {'EXPIRY':<12}  {'ZONE':<12}  {'LOCATION':<14}  STATUS")
    print(f"  {'─'*10}  {'─'*24}  {'─'*12}  {'─'*12}  {'─'*14}  {'─'*12}")
    for item in items:
        urgency = URGENCY_LABEL.get(item.get("_urgency", "watch"), "")
        print(f"  {item['id']:<10}  {item['name'][:24]:<24}  {item.get('expiry_date',''):<12}  "
              f"{item.get('temp_zone','ambient'):<12}  {item.get('location','—'):<14}  {urgency}")
    print()


def print_manifest(manifest):
    print(f"\n{BAR}")
    print(f"  DELIVERY MANIFEST  —  {manifest['route']}")
    if manifest.get("description"):
        print(f"  {manifest['description']}")
    print(f"  Generated: {manifest['generated_at'][:16].replace('T','  ')}")
    print(BAR)

    stops = manifest.get("stops", [])
    if stops:
        print(f"\n  STOPS ({len(stops)}):")
        for i, stop in enumerate(stops, 1):
            print(f"    {i}. {stop['recipient']}")
            if stop.get("address"):
                print(f"       {stop['address']}")
            if stop.get("notes"):
                print(f"       Note: {stop['notes']}")

    for section, label in [("urgent", "PERISHABLES / URGENT"), ("cold", "COLD CHAIN"), ("normal", "AMBIENT / DRY")]:
        items = manifest.get(section, [])
        if not items:
            continue
        print(f"\n  {label}  ({len(items)} item(s))")
        print(f"  {'─'*66}")
        for item in items:
            urgency = item.get("_urgency", "")
            flag    = {"expired": "!! EXPIRED", "critical": "!! TODAY",
                       "warning": "!  TOMORROW", "watch": "   SOON"}.get(urgency, "")
            expiry  = f"  exp:{item['expiry_date']}" if item.get("expiry_date") else ""
            print(f"    {item['id']}  {item['name'][:30]:<30}  {item.get('location','—'):<12}  {flag}{expiry}")
    print()


def print_locations(locs):
    if not locs:
        print("  No locations defined. Add with: donation_station.py location add <code>\n")
        return
    print(f"\n{BAR}")
    print(f"  {'CODE':<16}  {'ZONE':<14}  {'CURRENT':>8}  {'CAPACITY':>9}  {'FILL':>6}  DESCRIPTION")
    print(BAR)
    for loc in sorted(locs, key=lambda x: x["code"]):
        cap   = loc.get("capacity", 0)
        cur   = loc.get("actual", loc.get("count", 0))
        fill  = f"{int(cur/cap*100)}%" if cap else "—"
        bar   = ("█" * int(cur / cap * 10) if cap else "") + ("░" * (10 - int(cur/cap*10)) if cap else "")
        print(f"  {loc['code']:<16}  {loc.get('zone',''):<14}  {cur:>8}  {cap:>9}  {fill:>6}  {loc.get('description','')}")
    print()


def print_metrics(m):
    t  = m["throughput"]
    v  = m["velocity"]
    qc = m["qc"]
    mn = m["maintenance"]
    print(f"\n{BAR}")
    print(f"  METRICS  —  THROUGHPUT & QUALITY")
    print(BAR)
    print(f"\n  Throughput")
    print(f"    Today:      {t['today']:>4}")
    print(f"    Last 7d:    {t['7_days']:>4}")
    print(f"    Last 30d:   {t['30_days']:>4}")
    print(f"\n  Stage Velocity (avg hours)")
    for label, val in v.items():
        display = f"{val}h" if val is not None else "—"
        print(f"    {label:<24}  {display}")
    print(f"\n  QC Performance")
    print(f"    Overall pass rate:  {qc['pass_rate']}%  ({qc['pass']}/{qc['total']})")
    if qc["by_category"]:
        print(f"\n    By Category:")
        for cat, vals in sorted(qc["by_category"].items()):
            total = vals["pass"] + vals["fail"]
            rate  = int(vals["pass"] / total * 100) if total else 0
            bar   = "█" * (rate // 10)
            print(f"      {cat:<20}  {vals['pass']:>3}/{total:<3}  {rate:>3}%  {bar}")
    print(f"\n  Maintenance")
    print(f"    Pending:  {mn['pending']}")
    if mn["overdue"]:
        print(f"    Overdue:  {mn['overdue']}  ← action needed")
    print()


def print_lots(lots):
    if not lots:
        print("  No lots recorded.\n")
        return
    print(f"\n{BAR}")
    print(f"  {'LOT':<12}  {'ITEMS':>6}  STAGE BREAKDOWN")
    print(BAR)
    for lot in lots:
        stages = "  ".join(f"{s}:{n}" for s, n in lot["stages"].items())
        print(f"  {lot['lot']:<12}  {lot['count']:>6}  {stages}")
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
            p.add_argument("--lot",       default="")
            p.add_argument("--expiry",    default="", dest="expiry_date",
                           metavar="YYYY-MM-DD", help="expiry date for perishables")
            p.add_argument("--zone",      default="ambient", choices=TEMP_ZONES,
                           dest="temp_zone", help="temperature zone")
            p.add_argument("--weight",    default="", help="weight (e.g. '5 lbs')")
            p.add_argument("--origin",    default="", help="farm or supplier origin")
            a    = p.parse_args(rest)
            item = intake(a.name, a.category, a.condition, a.donor, a.notes, a.by, a.lot,
                          a.expiry_date, a.temp_zone, a.weight, a.origin)
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
            p.add_argument("--by",           default="")
            p.add_argument("--notes",        default="")
            p.add_argument("--substitution", default="",
                           help="substitution note (item swapped for another)")
            a    = p.parse_args(rest)
            item = distribute(a.item_id, a.recipient, a.by, a.notes, a.substitution)
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

        elif cmd == "lot":
            if not rest:
                lots = lots_list()
                if use_json:
                    print(json.dumps(lots, indent=2))
                else:
                    print_lots(lots)
            else:
                items = lot_info(rest[0])
                if use_json:
                    print(json.dumps(items, indent=2))
                else:
                    print(f"\n  Lot {rest[0]}  —  {len(items)} item(s)")
                    print_list(items)

        elif cmd == "lots":
            lots = lots_list()
            if use_json:
                print(json.dumps(lots, indent=2))
            else:
                print_lots(lots)

        elif cmd == "location":
            if not rest:
                sys.exit("Usage: donation_station.py location add <code> | list")
            sub = rest[0]
            if sub == "add":
                p = argparse.ArgumentParser(prog="donation_station location add")
                p.add_argument("code")
                p.add_argument("--zone",        default="")
                p.add_argument("--capacity",    type=int, default=0)
                p.add_argument("--description", default="")
                p.add_argument("--temp-zone",   default="", dest="temp_zone",
                               choices=list(TEMP_ZONES) + [""],
                               help="temperature zone for perishable storage")
                a   = p.parse_args(rest[1:])
                loc = add_location(a.code, a.zone, a.capacity, a.description, a.temp_zone)
                if use_json:
                    print(json.dumps(loc, indent=2))
                else:
                    tz_note = f", temp_zone={loc['temp_zone']}" if loc.get("temp_zone") else ""
                    print(f"  Location {loc['code']} added  (zone={loc['zone']}, capacity={loc['capacity']}{tz_note})")
            elif sub == "list":
                locs = list_locations()
                if use_json:
                    print(json.dumps(locs, indent=2))
                else:
                    print_locations(locs)
            else:
                sys.exit(f"Unknown location sub-command '{sub}'. Use: add | list")

        elif cmd == "capacity":
            locs = capacity_report()
            if use_json:
                print(json.dumps(locs, indent=2))
            else:
                print_locations(locs)

        elif cmd == "fifo":
            items = fifo_list()
            if use_json:
                print(json.dumps(items, indent=2))
            else:
                if not items:
                    print("  No items in storage.")
                else:
                    print(f"\n  FIFO — {len(items)} item(s) in storage (oldest first)\n")
                    print_list(items)

        elif cmd == "picklist":
            p = argparse.ArgumentParser(prog="donation_station picklist")
            p.add_argument("--recipient", default="")
            a  = p.parse_args(rest)
            pl = pick_list(a.recipient)
            if use_json:
                print(json.dumps(pl, indent=2))
            else:
                print_picklist(pl)

        elif cmd == "label":
            if not rest:
                sys.exit("Usage: donation_station.py label <item-id>")
            item = get_status(rest[0])
            if use_json:
                print(json.dumps(item, indent=2))
            else:
                print_label(item)

        elif cmd == "metrics":
            m = metrics()
            if use_json:
                print(json.dumps(m, indent=2))
            else:
                print_metrics(m)

        elif cmd == "maintenance":
            items = maintenance_list()
            if use_json:
                print(json.dumps(items, indent=2))
            else:
                if not items:
                    print("  No maintenance pending.\n")
                else:
                    print(f"\n  {len(items)} item(s) pending maintenance:\n")
                    for item in items:
                        due  = item.get("maintenance_due", "—")
                        asgn = item.get("maintenance_assigned_to", "—")
                        print(f"  {item['id']}  {item['name'][:28]:<28}  Due: {due:<12}  Assigned: {asgn}")
                        print(f"           {item.get('maintenance_needed','')}")
                    print()

        elif cmd == "maintain":
            p = argparse.ArgumentParser(prog="donation_station maintain")
            p.add_argument("item_id")
            p.add_argument("--due",      default="")
            p.add_argument("--by",       default="")
            p.add_argument("--complete", action="store_true")
            p.add_argument("--notes",    default="")
            a = p.parse_args(rest)
            if a.complete:
                item = complete_maintenance(a.item_id, a.notes, a.by)
            else:
                item = schedule_maintenance(a.item_id, a.due, a.by)
            if use_json:
                print(json.dumps(item, indent=2))
            else:
                if a.complete:
                    print(f"  {a.item_id} maintenance complete. Stage: qc (ready to store).")
                else:
                    print(f"  {a.item_id} maintenance scheduled. Due: {a.due or '—'}  Assigned: {a.by or '—'}")

        elif cmd == "export":
            p = argparse.ArgumentParser(prog="donation_station export")
            p.add_argument("--out", default=None, help="output file path")
            a        = p.parse_args(rest)
            path, n  = export(a.out)
            if use_json:
                print(json.dumps({"path": path, "count": n}))
            else:
                print(f"  Exported {n} item(s) → {path}")

        elif cmd == "expiring":
            p = argparse.ArgumentParser(prog="donation_station expiring")
            p.add_argument("--days", type=int, default=2,
                           help="show items expiring within this many days (default 2)")
            a     = p.parse_args(rest)
            items = expiring(a.days)
            if use_json:
                print(json.dumps(items, indent=2))
            else:
                print_expiring(items, a.days)

        elif cmd == "route":
            if not rest:
                sys.exit("Usage: donation_station.py route add <name> | stop <name> <recipient> | list")
            sub = rest[0]
            if sub == "add":
                p = argparse.ArgumentParser(prog="donation_station route add")
                p.add_argument("name")
                p.add_argument("--description", default="")
                a     = p.parse_args(rest[1:])
                route = add_route(a.name, a.description)
                if use_json:
                    print(json.dumps(route, indent=2))
                else:
                    print(f"  Route '{route['name']}' created.")
            elif sub == "stop":
                p = argparse.ArgumentParser(prog="donation_station route stop")
                p.add_argument("route_name")
                p.add_argument("recipient")
                p.add_argument("--address", default="")
                p.add_argument("--notes",   default="")
                a     = p.parse_args(rest[1:])
                route = add_route_stop(a.route_name, a.recipient, a.address, a.notes)
                if use_json:
                    print(json.dumps(route, indent=2))
                else:
                    print(f"  Stop '{a.recipient}' added to route '{a.route_name}'.")
            elif sub == "list":
                routes = list_routes()
                if use_json:
                    print(json.dumps(routes, indent=2))
                else:
                    if not routes:
                        print("  No routes defined.\n")
                    else:
                        print(f"\n{BAR}")
                        print(f"  ROUTES")
                        print(BAR)
                        for r in routes:
                            print(f"  {r['name']:<20}  {len(r.get('stops',[]))} stop(s)  {r.get('description','')}")
                        print()
            else:
                sys.exit(f"Unknown route sub-command '{sub}'. Use: add | stop | list")

        elif cmd == "manifest":
            if not rest:
                sys.exit("Usage: donation_station.py manifest <route-name>")
            manifest = generate_manifest(rest[0])
            if use_json:
                print(json.dumps(manifest, indent=2))
            else:
                print_manifest(manifest)

        else:
            sys.exit(f"Unknown command '{cmd}'. Run without arguments for usage.")

    except (KeyError, ValueError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
