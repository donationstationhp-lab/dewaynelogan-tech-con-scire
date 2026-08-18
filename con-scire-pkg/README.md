# con-scire

*to know together*

Standalone bridge connecting AXIOM organizational health assessments with
Donation Station item lifecycle data through Power Connection numerology.

## What it does

A donation item's intake date yields a Power Connection born number. That born
number maps to a governing AXIOM dimension. The organization's health at that
dimension is the relational reading for the item.

Each lifecycle stage is governed by specific AXIOM positions:

| Stage | Governing Positions |
|---|---|
| intake | P1 KNOWLEDGE + P9 BORN |
| qc | P2 WISDOM + P8 BUILD/DESTROY |
| storage | P4 CULTURED FREEDOM + P3 UNDERSTANDING |
| distributed | P6 EQUALITY + P7 CONSCIOUSNESS |

## Usage

```
python bridge.py                               # stage health summary
python bridge.py --station                     # bridge all items
python bridge.py --item DS-0001                # one item
python bridge.py --stage distributed           # one stage
python bridge.py --org assessments/file.json   # specific AXIOM assessment
python bridge.py --api http://localhost:5000   # live Donation Station API
python bridge.py --data .donation_station_data.json
```

## Dependencies

Python 3.10+. No external packages required.

Reads AXIOM assessment JSON files (`assessments/` by default or `--org`).
Connects to Donation Station via local data file or live API (`--api`).
