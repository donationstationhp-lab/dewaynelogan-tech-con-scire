#!/usr/bin/env python3
"""donation_station_web.py — Browser dashboard for Donation Station.

Run:
  python donation_station_web.py
  open http://localhost:5000
"""

from datetime import datetime, timezone
from flask import Flask, redirect, render_template_string, request, url_for
import donation_station as ds

app = Flask(__name__)

# ── Palette (matches paper form) ──────────────────────────────────────────────
TIER_COLORS = {
    "T": "#C4700E",  # amber
    "I": "#3B5AA0",  # indigo
    "E": "#1E7A4E",  # forest
    "R": "#A3442A",  # rust
}
STAGE_ORDER  = ["intake", "qc", "storage", "distributed"]
STAGE_LABELS = {"intake": "Intake", "qc": "QC", "storage": "Storage", "distributed": "Distributed"}

# ── Base template ─────────────────────────────────────────────────────────────
BASE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}Donation Station{% endblock %}</title>
<style>
:root {
  --bg:       #F8F5F0;
  --surface:  #FFFFFF;
  --text:     #1C1917;
  --mid:      #6B6560;
  --rule:     #E2DDD6;
  --nav:      #2C4B6E;
  --nav-text: #EEF2F7;
  --T: #C4700E; --I: #3B5AA0; --E: #1E7A4E; --R: #A3442A;
  --pass: #1E7A4E; --fail: #A3442A;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #141210; --surface: #1E1B17; --text: #F0EBE3;
    --mid: #A09890; --rule: #2E2A25; --nav: #1B2E44; --nav-text: #C8D4E0;
  }
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 14px;
       background: var(--bg); color: var(--text); min-height: 100vh; }
a { color: var(--nav); text-decoration: none; }
a:hover { text-decoration: underline; }

/* nav */
nav { background: var(--nav); color: var(--nav-text);
      padding: 0 24px; display: flex; align-items: center; gap: 0; height: 48px; }
.nav-brand { font-family: Georgia, serif; font-size: 16px; letter-spacing: 0.05em;
             color: var(--nav-text); margin-right: 32px; }
.nav-links { display: flex; gap: 0; height: 100%; }
.nav-links a { color: var(--nav-text); opacity: 0.75; font-size: 12px;
               letter-spacing: 0.08em; text-transform: uppercase;
               padding: 0 16px; display: flex; align-items: center;
               border-bottom: 2px solid transparent; }
.nav-links a:hover, .nav-links a.active { opacity: 1; text-decoration: none;
               border-bottom-color: var(--nav-text); }
.nav-right { margin-left: auto; }
.nav-right form { display: flex; gap: 0; }
.nav-right input { padding: 6px 12px; font-size: 12px; border: none;
                   background: rgba(255,255,255,0.12); color: var(--nav-text);
                   outline: none; width: 180px; }
.nav-right input::placeholder { color: rgba(255,255,255,0.45); }
.nav-right button { padding: 6px 12px; font-size: 11px; letter-spacing: 0.08em;
                    text-transform: uppercase; background: rgba(255,255,255,0.18);
                    color: var(--nav-text); border: none; cursor: pointer; }
.nav-right button:hover { background: rgba(255,255,255,0.28); }

/* page */
.page { max-width: 1000px; margin: 0 auto; padding: 28px 20px 60px; }
.page-title { font-family: Georgia, serif; font-size: 22px; font-weight: normal;
              margin-bottom: 24px; }

/* badges */
.badge { display: inline-block; font-size: 10px; font-weight: bold;
         letter-spacing: 0.1em; text-transform: uppercase;
         padding: 2px 8px; border-radius: 2px; }
.tier-T { background: color-mix(in srgb, var(--T) 14%, transparent); color: var(--T); }
.tier-I { background: color-mix(in srgb, var(--I) 14%, transparent); color: var(--I); }
.tier-E { background: color-mix(in srgb, var(--E) 14%, transparent); color: var(--E); }
.tier-R { background: color-mix(in srgb, var(--R) 14%, transparent); color: var(--R); }
.stage-intake      { background:#F0F0F0; color:#555; }
.stage-qc          { background:#FFF8E1; color:#8A6500; }
.stage-storage     { background:#E8EEF8; color:#2C4B6E; }
.stage-distributed { background:#E6F4EC; color:#1E7A4E; }

/* summary cards */
.summary { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px;
           margin-bottom: 28px; }
.card { background: var(--surface); border: 1px solid var(--rule);
        padding: 16px 18px; }
.card-num { font-family: Georgia, serif; font-size: 32px; line-height: 1;
            font-weight: bold; }
.card-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.12em;
              color: var(--mid); margin-top: 4px; }
.card-T .card-num { color: var(--T); }
.card-I .card-num { color: var(--I); }
.card-E .card-num { color: var(--E); }
.card-R .card-num { color: var(--R); }

/* table */
.tbl-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; background: var(--surface); }
th { font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em;
     color: var(--mid); padding: 10px 14px; text-align: left;
     border-bottom: 2px solid var(--text); white-space: nowrap;
     font-weight: normal; }
td { padding: 11px 14px; border-bottom: 1px solid var(--rule);
     vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: color-mix(in srgb, var(--nav) 4%, transparent); }
.td-name { font-weight: 500; }
.td-id   { font-family: 'Courier New', monospace; font-size: 12px;
           color: var(--mid); white-space: nowrap; }

/* item detail */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
               margin-bottom: 24px; }
.detail-box { background: var(--surface); border: 1px solid var(--rule);
              padding: 16px 18px; }
.detail-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.12em;
                color: var(--mid); margin-bottom: 4px; }
.detail-val { font-size: 15px; }
.timeline { display: flex; flex-direction: column; gap: 0; }
.tl-event { display: flex; gap: 16px; }
.tl-dot-col { display: flex; flex-direction: column; align-items: center; width: 36px; flex-shrink: 0; }
.tl-dot { width: 28px; height: 28px; background: var(--nav); color: #fff;
          display: flex; align-items: center; justify-content: center;
          font-family: Georgia, serif; font-size: 12px; font-weight: bold;
          flex-shrink: 0; }
.tl-line { flex: 1; width: 2px; background: var(--rule); margin: 2px 0; min-height: 16px; }
.tl-body { padding: 3px 0 20px; flex: 1; }
.tl-stage { font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
            font-weight: bold; color: var(--text); }
.tl-ts    { font-size: 11px; color: var(--mid); margin-bottom: 6px; }
.tl-row   { font-size: 12px; color: var(--mid); margin-top: 2px; }

/* power date */
.power-box { background: color-mix(in srgb, var(--nav) 6%, var(--surface));
             border: 1px solid var(--rule); padding: 14px 18px; margin-bottom: 24px; }
.power-title { font-size: 10px; text-transform: uppercase; letter-spacing: 0.14em;
               color: var(--mid); margin-bottom: 8px; }
.power-vals { display: flex; gap: 28px; }
.power-item { display: flex; flex-direction: column; gap: 2px; }
.power-num  { font-family: Georgia, serif; font-size: 22px; font-weight: bold;
              color: var(--nav); line-height: 1; }
.power-sub  { font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em;
              color: var(--mid); }

/* form */
.form-box { background: var(--surface); border: 1px solid var(--rule);
            padding: 24px 28px; max-width: 580px; }
.field { display: flex; flex-direction: column; gap: 5px; margin-bottom: 16px; }
.field label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.12em;
               color: var(--mid); }
.field input, .field select, .field textarea {
  padding: 8px 10px; border: 1px solid var(--rule); background: var(--bg);
  color: var(--text); font-size: 13px; font-family: inherit; outline: none; }
.field input:focus, .field select:focus, .field textarea:focus {
  border-color: var(--nav); }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.btn { padding: 9px 22px; background: var(--nav); color: #fff; border: none;
       cursor: pointer; font-size: 12px; letter-spacing: 0.1em;
       text-transform: uppercase; }
.btn:hover { opacity: 0.88; }
.btn-sm { padding: 5px 12px; font-size: 11px; }

/* report bars */
.bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.bar-label { width: 120px; font-size: 11px; text-transform: uppercase;
             letter-spacing: 0.08em; color: var(--mid); }
.bar-track { flex: 1; height: 14px; background: var(--rule); }
.bar-fill  { height: 100%; }
.bar-count { width: 32px; text-align: right; font-family: Georgia, serif;
             font-size: 14px; font-variant-numeric: tabular-nums; }

/* flash */
.flash { padding: 10px 16px; margin-bottom: 20px; font-size: 13px;
         background: color-mix(in srgb, var(--E) 12%, var(--surface));
         border-left: 3px solid var(--E); color: var(--text); }

/* empty */
.empty { color: var(--mid); font-size: 13px; padding: 24px 0; }

/* urgency chips */
.urg-expired  { display:inline-block;padding:2px 8px;font-size:10px;font-weight:bold;
                letter-spacing:.1em;text-transform:uppercase;background:#A3442A;color:#fff; }
.urg-critical { display:inline-block;padding:2px 8px;font-size:10px;font-weight:bold;
                letter-spacing:.1em;text-transform:uppercase;background:#C4700E;color:#fff; }
.urg-warning  { display:inline-block;padding:2px 8px;font-size:10px;font-weight:bold;
                letter-spacing:.1em;text-transform:uppercase;background:#8A6500;color:#fff; }
.urg-watch    { display:inline-block;padding:2px 8px;font-size:10px;
                letter-spacing:.08em;text-transform:uppercase;
                background:var(--rule);color:var(--mid); }

/* temp zone pill */
.zone-refrigerated { color:#2C4B6E; font-weight:500; }
.zone-frozen       { color:#1E7A4E; font-weight:500; }
.zone-ambient      { color:var(--mid); }
</style>
</head>
<body>
<nav>
  <span class="nav-brand">Donation Station</span>
  <div class="nav-links">
    <a href="{{ url_for('index') }}"    class="{{ 'active' if active=='home' }}">Items</a>
    <a href="{{ url_for('new_item') }}" class="{{ 'active' if active=='new' }}">+ Intake</a>
    <a href="{{ url_for('expiring_view') }}" class="{{ 'active' if active=='expiring' }}"
       style="{% if expiring_count %}color:#E07820{% endif %}">
      Expiring{% if expiring_count %} ({{ expiring_count }}){% endif %}
    </a>
    <a href="{{ url_for('report') }}"   class="{{ 'active' if active=='report' }}">Report</a>
  </div>
  <div class="nav-right">
    <form action="{{ url_for('search_view') }}" method="get">
      <input name="q" placeholder="Search items…" value="{{ q or '' }}">
      <button type="submit">Go</button>
    </form>
  </div>
</nav>
<div class="page">
  {% if flash %}<div class="flash">{{ flash }}</div>{% endif %}
  {% block content %}{% endblock %}
</div>
</body>
</html>"""

# ── Index ─────────────────────────────────────────────────────────────────────
INDEX = BASE.replace("{% block content %}{% endblock %}", """{% block content %}
<div class="summary">
  {% for letter, name in [('T','Time'),('I','Intelligence'),('E','Energy'),('R','Resources')] %}
  <div class="card card-{{ letter }}">
    <div class="card-num">{{ by_tier[letter] }}</div>
    <div class="card-label">{{ letter }} — {{ name }}</div>
  </div>
  {% endfor %}
</div>
{% if stage_filter and stage_filter != 'all' %}
<p style="margin-bottom:14px;font-size:12px;color:var(--mid)">
  Showing: <strong>{{ stage_filter }}</strong> &nbsp;
  <a href="{{ url_for('index') }}">clear filter</a>
</p>
{% endif %}
<div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
  {% for s in ['all','intake','qc','storage','distributed'] %}
  <a href="{{ url_for('index', stage=s) }}"
     style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;
            padding:4px 12px;border:1px solid var(--rule);
            background:{{ 'var(--nav)' if stage_filter==s else 'var(--surface)' }};
            color:{{ '#fff' if stage_filter==s else 'var(--mid)' }}">
    {{ s }}
  </a>
  {% endfor %}
</div>
<div class="tbl-wrap">
<table>
  <thead><tr>
    <th>ID</th><th>Name</th><th>T.I.E.R.</th><th>Category</th>
    <th>Donor</th><th>Stage</th><th>Expiry</th><th>Power Born</th>
  </tr></thead>
  <tbody>
  {% for item in items %}
  {% set urgency = urgency_map.get(item.id, '') %}
  <tr>
    <td class="td-id"><a href="{{ url_for('item_detail', item_id=item.id) }}">{{ item.id }}</a></td>
    <td class="td-name"><a href="{{ url_for('item_detail', item_id=item.id) }}">{{ item.name }}</a></td>
    <td><span class="badge tier-{{ item.tier }}">{{ item.tier }}</span></td>
    <td style="color:var(--mid);font-size:12px">{{ item.category }}</td>
    <td style="color:var(--mid);font-size:12px">{{ item.donor or '—' }}</td>
    <td><span class="badge stage-{{ item.stage }}">{{ item.stage }}</span></td>
    <td style="font-size:12px">
      {% if item.get('expiry_date') %}
        {{ item.expiry_date }}
        {% if urgency %}<span class="urg-{{ urgency }}">{{ urgency }}</span>{% endif %}
      {% else %}—{% endif %}
    </td>
    <td style="font-family:Georgia,serif;font-size:13px;color:var(--nav)">
      {% if item.power_date %}{{ item.power_date.born }} [{{ item.power_date.born_name }}]{% else %}—{% endif %}
    </td>
  </tr>
  {% else %}
  <tr><td colspan="8" class="empty">No items found.</td></tr>
  {% endfor %}
  </tbody>
</table>
</div>
{% endblock %}""")

# ── Detail ────────────────────────────────────────────────────────────────────
DETAIL = BASE.replace("{% block title %}Donation Station{% endblock %}",
                      "{% block title %}{{ item.id }} — Donation Station{% endblock %}"
                      ).replace("{% block content %}{% endblock %}", """{% block content %}
<div style="margin-bottom:16px">
  <a href="{{ url_for('index') }}" style="font-size:12px;color:var(--mid)">← All items</a>
</div>
<h1 class="page-title">{{ item.name }}</h1>
<div class="detail-grid">
  <div class="detail-box">
    <div class="detail-label">Item ID</div>
    <div class="detail-val" style="font-family:monospace">{{ item.id }}</div>
  </div>
  <div class="detail-box">
    <div class="detail-label">T.I.E.R.</div>
    <div class="detail-val">
      <span class="badge tier-{{ item.tier }}">{{ item.tier }}</span>
      <span style="margin-left:8px;font-size:13px">{{ tier_names[item.tier] }}</span>
    </div>
  </div>
  <div class="detail-box">
    <div class="detail-label">Category</div>
    <div class="detail-val">{{ item.category }}</div>
  </div>
  <div class="detail-box">
    <div class="detail-label">Condition</div>
    <div class="detail-val">{{ item.condition }}</div>
  </div>
  <div class="detail-box">
    <div class="detail-label">Donor</div>
    <div class="detail-val">{{ item.donor or '—' }}</div>
  </div>
  <div class="detail-box">
    <div class="detail-label">Stage</div>
    <div class="detail-val">
      <span class="badge stage-{{ item.stage }}">{{ item.stage }}</span>
    </div>
  </div>
  {% if item.recipient %}
  <div class="detail-box">
    <div class="detail-label">Recipient</div>
    <div class="detail-val">{{ item.recipient }}</div>
  </div>
  {% endif %}
  {% if item.location %}
  <div class="detail-box">
    <div class="detail-label">Location</div>
    <div class="detail-val">{{ item.location }}</div>
  </div>
  {% endif %}
  {% if item.get('temp_zone') %}
  <div class="detail-box">
    <div class="detail-label">Temperature Zone</div>
    <div class="detail-val"><span class="zone-{{ item.temp_zone }}">{{ item.temp_zone }}</span></div>
  </div>
  {% endif %}
  {% if item.get('expiry_date') %}
  <div class="detail-box">
    <div class="detail-label">Expiry Date</div>
    <div class="detail-val">
      {{ item.expiry_date }}
      {% if urgency %}<span class="urg-{{ urgency }}" style="margin-left:8px">{{ urgency }}</span>{% endif %}
    </div>
  </div>
  {% endif %}
  {% if item.get('weight') %}
  <div class="detail-box">
    <div class="detail-label">Weight</div>
    <div class="detail-val">{{ item.weight }}</div>
  </div>
  {% endif %}
  {% if item.get('origin') %}
  <div class="detail-box">
    <div class="detail-label">Origin</div>
    <div class="detail-val">{{ item.origin }}</div>
  </div>
  {% endif %}
</div>
{% if item.power_date %}
<div class="power-box">
  <div class="power-title">Power Connection — Intake Date</div>
  <div class="power-vals">
    <div class="power-item">
      <div class="power-num">{{ item.power_date.root }}</div>
      <div class="power-sub">Root</div>
    </div>
    <div class="power-item" style="color:var(--mid);align-self:center;font-size:18px">→</div>
    <div class="power-item">
      <div class="power-num">{{ item.power_date.root_born }}</div>
      <div class="power-sub">Root Born</div>
    </div>
    <div class="power-item" style="color:var(--mid);align-self:center;font-size:18px;margin:0 8px">|</div>
    <div class="power-item">
      <div class="power-num">{{ item.power_date.born }}</div>
      <div class="power-sub">Born</div>
    </div>
    <div class="power-item">
      <div class="power-num" style="font-size:16px;padding-top:4px">{{ item.power_date.born_name }}</div>
      <div class="power-sub">Name</div>
    </div>
  </div>
</div>
{% endif %}
<h2 style="font-family:Georgia,serif;font-size:16px;font-weight:normal;margin-bottom:16px">History</h2>
<div class="timeline">
{% for event in item.history %}
<div class="tl-event">
  <div class="tl-dot-col">
    <div class="tl-dot">{{ loop.index }}</div>
    {% if not loop.last %}<div class="tl-line"></div>{% endif %}
  </div>
  <div class="tl-body">
    <div class="tl-stage">{{ event.stage }}</div>
    <div class="tl-ts">{{ event.timestamp[:16].replace('T','  ') }}</div>
    {% if event.by %}<div class="tl-row">By: {{ event.by }}</div>{% endif %}
    {% if event.stage == 'qc' %}
      <div class="tl-row" style="color:{{ 'var(--pass)' if event.passed else 'var(--fail)' }}">
        Result: {{ 'PASS' if event.passed else 'FAIL' }}
      </div>
      {% if event.maintenance %}<div class="tl-row">Maintenance: {{ event.maintenance }}</div>{% endif %}
    {% endif %}
    {% if event.location %}<div class="tl-row">Location: {{ event.location }}</div>{% endif %}
    {% if event.recipient %}<div class="tl-row">Recipient: {{ event.recipient }}</div>{% endif %}
    {% if event.get('substitution') %}<div class="tl-row" style="color:var(--T)">Substitution: {{ event.substitution }}</div>{% endif %}
    {% if event.notes %}<div class="tl-row">Notes: {{ event.notes }}</div>{% endif %}
  </div>
</div>
{% endfor %}
</div>
{% endblock %}""")

# ── New intake form ───────────────────────────────────────────────────────────
NEW = BASE.replace("{% block content %}{% endblock %}", """{% block content %}
<h1 class="page-title">New Intake</h1>
<div class="form-box">
  <form method="post">
    <div class="field">
      <label>Item Name *</label>
      <input name="name" required autofocus>
    </div>
    <div class="row2">
      <div class="field">
        <label>Category</label>
        <select name="category">
          {% for cat in categories %}<option value="{{ cat }}">{{ cat }}</option>{% endfor %}
        </select>
      </div>
      <div class="field">
        <label>Condition</label>
        <select name="condition">
          <option>good</option><option>fair</option><option>poor</option>
        </select>
      </div>
    </div>
    <div class="row2">
      <div class="field">
        <label>Donor</label>
        <input name="donor">
      </div>
      <div class="field">
        <label>Received By</label>
        <input name="by">
      </div>
    </div>
    <div class="field">
      <label>Notes</label>
      <input name="notes">
    </div>
    <div style="margin:20px 0 10px;padding-top:16px;border-top:1px solid var(--rule)">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:var(--mid);margin-bottom:14px">
        Perishable Details (optional)
      </div>
    </div>
    <div class="row2">
      <div class="field">
        <label>Expiry Date</label>
        <input name="expiry_date" type="date" placeholder="YYYY-MM-DD">
      </div>
      <div class="field">
        <label>Temperature Zone</label>
        <select name="temp_zone">
          <option value="ambient">Ambient (dry / shelf-stable)</option>
          <option value="refrigerated">Refrigerated</option>
          <option value="frozen">Frozen</option>
        </select>
      </div>
    </div>
    <div class="row2">
      <div class="field">
        <label>Weight</label>
        <input name="weight" placeholder="e.g. 5 lbs">
      </div>
      <div class="field">
        <label>Origin / Supplier</label>
        <input name="origin" placeholder="e.g. Green Acres Farm">
      </div>
    </div>
    <button type="submit" class="btn">Log Intake</button>
  </form>
</div>
{% endblock %}""")

# ── Report ────────────────────────────────────────────────────────────────────
REPORT = BASE.replace("{% block content %}{% endblock %}", """{% block content %}
<h1 class="page-title">Report</h1>
<h2 style="font-family:Georgia,serif;font-size:15px;font-weight:normal;
           margin-bottom:14px;color:var(--mid)">T.I.E.R. Breakdown</h2>
{% set tier_max = [by_tier.T, by_tier.I, by_tier.E, by_tier.R] | max or 1 %}
{% for letter, name, color in [('T','Time','var(--T)'),('I','Intelligence','var(--I)'),
                                ('E','Energy','var(--E)'),('R','Resources','var(--R)')] %}
<div class="bar-row">
  <div class="bar-label">{{ letter }} — {{ name }}</div>
  <div class="bar-track">
    <div class="bar-fill" style="width:{{ (by_tier[letter] / tier_max * 100)|int }}%;background:{{ color }}"></div>
  </div>
  <div class="bar-count">{{ by_tier[letter] }}</div>
</div>
{% endfor %}
<div style="margin-top:28px;margin-bottom:14px">
<h2 style="font-family:Georgia,serif;font-size:15px;font-weight:normal;color:var(--mid)">By Stage</h2>
</div>
{% set stage_max = [by_stage.intake, by_stage.qc, by_stage.storage, by_stage.distributed] | max or 1 %}
{% for s, label in [('intake','Intake'),('qc','Quality Control'),('storage','Storage'),('distributed','Distributed')] %}
<div class="bar-row">
  <div class="bar-label" style="width:140px">{{ label }}</div>
  <div class="bar-track">
    <div class="bar-fill" style="width:{{ (by_stage[s] / stage_max * 100)|int }}%;background:var(--nav)"></div>
  </div>
  <div class="bar-count">{{ by_stage[s] }}</div>
</div>
{% endfor %}
<div style="margin-top:28px;margin-bottom:14px">
<h2 style="font-family:Georgia,serif;font-size:15px;font-weight:normal;color:var(--mid)">
  Total Items: {{ total }}
  {% if maintenance_pending %}
    &nbsp;·&nbsp; <span style="color:var(--fail)">{{ maintenance_pending }} maintenance pending</span>
  {% endif %}
</h2>
</div>
{% endblock %}""")

# ── Search ────────────────────────────────────────────────────────────────────
SEARCH = BASE.replace("{% block content %}{% endblock %}", """{% block content %}
<h1 class="page-title">Search: "{{ q }}"</h1>
<div class="tbl-wrap">
<table>
  <thead><tr>
    <th>ID</th><th>Name</th><th>T.I.E.R.</th><th>Category</th>
    <th>Donor</th><th>Stage</th>
  </tr></thead>
  <tbody>
  {% for item in items %}
  <tr>
    <td class="td-id"><a href="{{ url_for('item_detail', item_id=item.id) }}">{{ item.id }}</a></td>
    <td class="td-name"><a href="{{ url_for('item_detail', item_id=item.id) }}">{{ item.name }}</a></td>
    <td><span class="badge tier-{{ item.tier }}">{{ item.tier }}</span></td>
    <td style="color:var(--mid);font-size:12px">{{ item.category }}</td>
    <td style="color:var(--mid);font-size:12px">{{ item.donor or '—' }}</td>
    <td><span class="badge stage-{{ item.stage }}">{{ item.stage }}</span></td>
  </tr>
  {% else %}
  <tr><td colspan="6" class="empty">No items matched "{{ q }}".</td></tr>
  {% endfor %}
  </tbody>
</table>
</div>
{% endblock %}""")

# ── Expiring ──────────────────────────────────────────────────────────────────
EXPIRING = BASE.replace("{% block content %}{% endblock %}", """{% block content %}
<h1 class="page-title">Expiring Items</h1>
<p style="font-size:12px;color:var(--mid);margin-bottom:20px">
  Showing items in storage expiring within
  <strong>{{ days }}</strong> day(s).
  &nbsp;<a href="?days=1">1d</a> &nbsp;<a href="?days=2">2d</a>
  &nbsp;<a href="?days=5">5d</a> &nbsp;<a href="?days=14">14d</a>
</p>
<div class="tbl-wrap">
<table>
  <thead><tr>
    <th>ID</th><th>Name</th><th>Expiry</th><th>Zone</th>
    <th>Location</th><th>Weight</th><th>Origin</th><th>Urgency</th>
  </tr></thead>
  <tbody>
  {% for item in items %}
  <tr>
    <td class="td-id"><a href="{{ url_for('item_detail', item_id=item.id) }}">{{ item.id }}</a></td>
    <td class="td-name"><a href="{{ url_for('item_detail', item_id=item.id) }}">{{ item.name }}</a></td>
    <td style="font-variant-numeric:tabular-nums">{{ item.expiry_date }}</td>
    <td><span class="zone-{{ item.get('temp_zone','ambient') }}">{{ item.get('temp_zone','ambient') }}</span></td>
    <td style="color:var(--mid);font-size:12px">{{ item.get('location','—') }}</td>
    <td style="color:var(--mid);font-size:12px">{{ item.get('weight','—') }}</td>
    <td style="color:var(--mid);font-size:12px">{{ item.get('origin','—') }}</td>
    <td><span class="urg-{{ item._urgency }}">{{ item._urgency }}</span></td>
  </tr>
  {% else %}
  <tr><td colspan="8" class="empty">No items expiring within {{ days }} day(s).</td></tr>
  {% endfor %}
  </tbody>
</table>
</div>
{% endblock %}""")

TIER_NAMES = {"T": "Time", "I": "Intelligence", "E": "Energy", "R": "Resources"}
CATEGORIES = sorted(ds.TIER_MAP.keys())


# ── Helpers ───────────────────────────────────────────────────────────────────

def _urgency_for(item):
    """Return urgency string for an item with expiry_date, or empty string."""
    expiry = item.get("expiry_date", "")
    if not expiry:
        return ""
    try:
        days_left = (datetime.strptime(expiry, "%Y-%m-%d").replace(tzinfo=timezone.utc).date()
                     - datetime.now(timezone.utc).date()).days
    except ValueError:
        return ""
    if days_left < 0:
        return "expired"
    if days_left == 0:
        return "critical"
    if days_left == 1:
        return "warning"
    return "watch"


def _global_ctx():
    """Values shared across every rendered template."""
    urgent = ds.expiring(days=2)
    return {"expiring_count": len(urgent)}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    stage   = request.args.get("stage", "all")
    items   = ds.list_items(stage)
    r       = ds.report()
    urgency_map = {item["id"]: _urgency_for(item) for item in items}
    return render_template_string(INDEX,
        items=items, by_tier=r["by_tier"], stage_filter=stage,
        urgency_map=urgency_map,
        active="home", flash=request.args.get("flash"), q=None,
        **_global_ctx())


@app.route("/item/<item_id>")
def item_detail(item_id):
    try:
        item = ds.get_status(item_id)
    except KeyError:
        return redirect(url_for("index", flash=f"Item {item_id} not found."))
    urgency = _urgency_for(item)
    return render_template_string(DETAIL,
        item=item, tier_names=TIER_NAMES, urgency=urgency,
        active="home", flash=None, q=None,
        **_global_ctx())


@app.route("/new", methods=["GET", "POST"])
def new_item():
    if request.method == "POST":
        f = request.form
        item = ds.intake(
            name=f["name"].strip(),
            category=f.get("category", "general"),
            condition=f.get("condition", "good"),
            donor=f.get("donor", "").strip(),
            notes=f.get("notes", "").strip(),
            by=f.get("by", "").strip(),
            expiry_date=f.get("expiry_date", "").strip(),
            temp_zone=f.get("temp_zone", "ambient"),
            weight=f.get("weight", "").strip(),
            origin=f.get("origin", "").strip(),
        )
        return redirect(url_for("item_detail", item_id=item["id"]))
    return render_template_string(NEW,
        categories=CATEGORIES, active="new", flash=None, q=None,
        **_global_ctx())


@app.route("/expiring")
def expiring_view():
    days  = int(request.args.get("days", 2))
    items = ds.expiring(days=days)
    return render_template_string(EXPIRING,
        items=items, days=days, active="expiring", flash=None, q=None,
        **_global_ctx())


@app.route("/report")
def report():
    r = ds.report()
    return render_template_string(REPORT, active="report", flash=None, q=None,
        total=r["total"], by_tier=r["by_tier"], by_stage=r["by_stage"],
        maintenance_pending=r["maintenance_pending"],
        **_global_ctx())


@app.route("/search")
def search_view():
    q     = request.args.get("q", "").strip()
    items = ds.search(q) if q else []
    return render_template_string(SEARCH,
        items=items, q=q, active=None, flash=None,
        **_global_ctx())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
