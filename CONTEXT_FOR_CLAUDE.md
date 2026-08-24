# Context for Claude — Supreme Mathematics Daily Reading Engine
*Transmittable briefing. Paste at the top of a new conversation to continue without loss.*

---

## Who I am and what we built

I am Dewayne Logan. In this session we built a Supreme Mathematics daily reading engine in Python, housed in a GitHub repository (`donationstationhp-lab/dewaynelogan-tech-con-scire`, branch `claude/artifact-link-reference-9Mt4v`). The engine is a CLI tool (`sm_daily.py`) backed by a standalone module (`suprememath/`) and an editable data file (`data/sm_lexicon.json`).

The work started from a React artifact I had built (a browser-based daily reading component). That artifact was the sealed reference. We rebuilt it in Python, correcting the mapping twice as the full system came into view. The primary frame is the Founder's Month/Day Fraction Calendar.

---

## The PRIMARY reading frame — Founder's Month/Day Fraction Calendar

**Source of truth:** Notion page `46e0a67b-a3dd-494f-ac5c-1cec071123ca`
("Month/Day Fraction Calendar — Seed (Jan 1)")

```
Received Attention of  (Month)
Gained   Intention by  (Day)
Given    Purpose through all being born to (Month + Day)
```

- **Attention** = month number as its SM position (January = 1 = Knowledge)
- **Intention** = raw day number — NOT pre-reduced (Day 29 is carried as 29)
- **Purpose**   = Month + Day, **UNREDUCED** — "compound-not-collapsed"
  Rendered as: `Given Purpose through all being born to (5 + 29 = 34)`

SM position = `reduce(raw)` — e.g., Day 29 → reduce(29) = 2 (Wisdom).
When raw ≠ position, the `compound` flag is True and the display shows both: `[compound: 29 → 2]`.

### Verbs (sealed)
- **Received** — on the Attention / Month seat
- **Gained**   — on the Intention / Day seat
- **Given**    — on the Purpose seat

These are fixed, not read from the lexicon.

---

## The SECONDARY lens — Method B + 12-hour clock

Method A/B/C and the hour-based reading are a **secondary, labeled lens** only. They are not the primary frame.

### Three arithmetic methods

**Method A — address** (`Y·M·W·D`)
Not a single number. Four independent reductions:
- `Y = reduce(year)`
- `M = reduce(month_number)`
- `W = reduce(ceil(day_of_year / 7))`
- `D = reduce(day_of_month)`
Displayed as e.g. `1·5·4·2` for 2026-05-29.

**Method B — date cipher** (secondary Attention)
Concatenate `YYYYMMDD` as a digit string, sum all digits, reduce.
2026-05-29 → `"20260529"` → 2+0+2+6+0+5+2+9 = 26 → **8**

**Method C — whole**
`reduce(month_int + day_int + year_int)`
2026-05-29 → 5 + 29 + 2026 = 2060 → **8**

`reduce(n)` is the standard digital root: sum digits of abs(n) until 0–9.

### Secondary reading frame

```
method_b(date)              → secondary Attention  (date cipher)
reduce(12-hour clock)       → secondary Intention  (hour cipher)
reduce(sec_att + sec_int)   → secondary Purpose
reduce(att + int + pur)     → Convergence — "aligned" when = 6
```

The `secondary` key in the `compute_daily()` return dict holds this frame.

### The calculation display
For daily journal entries, digits are shown in M+D+YYYY order (matching hand-written entries). The sum is order-independent and equals Method B.
Example: 2026-02-07 → `2 + 7 + 2 + 0 + 2 + 6 = 19 → 1`

---

## The user's own cipher (sealed in `data/sm_lexicon.json`)

This is the user's own reading, not the generic Five Percent Nation list. Do not substitute standard SM names without being asked.

| # | Name | PIE root | Verb |
|---|------|----------|------|
| 0 | Completion | com-plēre — to fill together | |
| 1 | Knowledge | *ǵneh₃-* — to know | gained |
| 2 | Wisdom | *weid-* — to see | |
| 3 | Understanding | *(inter/under)-stā-* — to stand between | |
| 4 | Cultured Freedom | *kʷel-* — to turn, to till | |
| 5 | Powered Refinement | re- + finis — back to the fine | |
| 6 | Equality | *aequus* — level, even | |
| 7 | Consciousness | com-scīre — to know-with | given |
| 8 | Build / Destroy | de-struere — to un-pile | |
| 9 | Birth | *bʰer-* — to bear, to carry | |

The `verb` field in the lexicon is sealed where present: 1 is *gained*, 7 is *given*. The `say` field holds the brief instruction for each seat. **Etymology lives only in the data file — no root judgment is baked into the logic.**

The fixed seat verbs (Received / Gained / Given) are NOT from the lexicon — they are baked into `compute_daily()` and sealed by the Fraction Calendar.

---

## The Fraction Calendar vs. the secondary lens (sealed distinction)

The Fraction Calendar is a *different* system from the secondary Method B frame:

| | Fraction Calendar (primary) | Secondary lens |
|---|---|---|
| Attention | month number | Method B (YYYYMMDD digit sum) |
| Intention | raw day number | reduce(12-hour clock) |
| Purpose | reduce(month + day) | reduce(sec_att + sec_int) |
| Sum display | unreduced M+D | reduced |

Both are the user's own work; do not conflate them.

---

## Moon phase (sealed)

- 8 phases — not 4. Source: fivepercenterlessons.com (sealed by the user 5/4/2026).
- Reference new moon: `2000-01-06 18:14 UTC` (sealed; not midnight).
- `days_to_full` field is included in the reading output.
- The 8 phases are: New, Waxing Crescent, First Quarter, Waxing Gibbous, Full, Waning Gibbous, **Third Quarter** (not "Last Quarter"), Waning Crescent.
- The synodic (~29.53 day) calc is outer/astronomical only.
- Doctrinal cycle: 28-day/13-month, held-in-study, not yet tracked operationally. 29.53-vs-28 reconciliation is an open task.
- Moon phases are NOT mapped to SM positions here — reserved for lineage-trained Stewards.
- Superseding source: `fivepercenterlessons.com/moon-phases/` (confirmed by the Founder 2026-05-04).
- Notion source: Lunar Cycle Learning Thread `35603691-bd5e-81a3-a4d4-fa3b27ca0975`.

---

## The two-calendar system (sealed 5/26/2026)

From the May 26 Notion entry ("Two Reeds Named: Sun & Moon"):
- **Gregorian** (solar reed) — counted from the Door (January ← *Iānus*, doorway)
- **Roman** (lunar reed) — counted from Mars (March ← *Mārtius*, the elder year-head)

Both calendars produce a Method A address. The lunar 13-month / 28-day calendar is *known doctrinally but not yet walked operationally* — it is an open study thread, not yet implemented in the engine.

**SUN** ← PIE *sóh₂wl̥* — the burning one; rules the day and year.
**MOON** ← PIE *meh₁-* — to measure; root of moon, month, and measure itself.
**CALENDAR** ← *kalendae* ← *calāre* — to call out the new moon.

---

## Project structure

```
dewaynelogan-tech-con-scire/
  sm_daily.py               CLI entry point
  suprememath/
    __init__.py
    digits.py               reduce(), day_of_year(), week_of_year(),
                            method_a() → address dict,
                            method_b() → int,
                            method_c() → int,
                            calculation_steps() → display string
    lexicon.py              Lexicon class — loads sm_lexicon.json at runtime
    moon.py                 moon_phase(date|datetime) → dict
    daily.py                compute_daily(datetime, Lexicon) → reading dict
    notion_sync.py          push(reading) → Notion page URL
  data/
    sm_lexicon.json         EDITABLE — all names, roots, verbs, say instructions
  tests/
    test_digits.py
    test_lexicon.py
    test_daily.py
  etymonline.py             Separate tool — etymology lookup from etymonline.com
```

112 tests pass. Run with: `python -m pytest tests/`

---

## compute_daily() return structure

```python
{
    "date":       "2026-05-29",
    "time":       "13:00",

    # PRIMARY — Fraction Calendar
    "attention":  {
        "verb": "Received", "prep": "of",
        "raw": 5,            # month number
        "number": 5,         # reduce(month)
        "name": "Powered Refinement",
        "pie_root": "...", "say": "...",
        "liturgy": "Received Attention of (May = 5)",
    },
    "intention":  {
        "verb": "Gained", "prep": "by",
        "raw": 29,           # day number (unreduced)
        "number": 2,         # reduce(29)
        "compound": True,    # 29 != 2
        "name": "Wisdom",
        "pie_root": "...", "say": "...",
        "liturgy": "Gained Intention by (29)",
    },
    "purpose":    {
        "verb": "Given", "prep": "through",
        "raw": 34,           # month + day, UNREDUCED
        "month": 5, "day": 29,
        "number": 7,         # reduce(34)
        "compound": True,    # 34 != 7
        "name": "Consciousness",
        "pie_root": "...", "say": "...",
        "liturgy": "Given Purpose through all being born to (5 + 29 = 34)",
    },

    # SECONDARY — Method B + 12-hour clock (labeled lens)
    "secondary":  {
        "label": "Method B + 12-hour clock (secondary lens)",
        "hour":        {"h12": 1, "number": 1, "name": "Knowledge"},
        "attention":   {"number": 8, "name": "Build / Destroy"},
        "purpose":     {"number": 9, "name": "Birth"},
        "convergence": {"number": 9, "name": "Birth", "aligned": False},
    },

    # SUPPORTING
    "year_arc":   {"number": 1, "name": "Knowledge", "year": 2026, ...},
    "address":    {"Y": 1, "M": 5, "W": 4, "D": 2, "display": "1·5·4·2"},
    "moon":       {"phase": "Waxing Gibbous", "emoji": "🌔", ...},
    "calculation": "5 + 2+9 + 2+0+2+6 = 26 → 8",
    "methods":    {"a": "1·5·4·2", "b": 8, "c": 8},
    "sources":    {
        "fraction_calendar": {
            "name": "Founder's Month/Day Fraction Calendar",
            "notion_id": "46e0a67ba3dd494fac5c1cec071123ca",
        },
        "lunar_thread": {
            "name": "Lunar Cycle Learning Thread",
            "notion_id": "35603691bd5e81a3a4d4fa3b27ca0975",
        },
    },
}
```

---

## CLI usage

```bash
python sm_daily.py                        # now
python sm_daily.py --date 2026-05-29      # that date at current hour
python sm_daily.py --hour 9               # today at 09:00
python sm_daily.py --date 2026-05-29 --hour 9
python sm_daily.py --json                 # raw JSON
python sm_daily.py --notion               # push to Notion (needs NOTION_TOKEN env var)
python sm_daily.py --lexicon my_lex.json  # swap in a custom lexicon
```

---

## Notion workspace

The user has an active Notion workspace with Supreme Mathematics content. Relevant pages:

| Page | Notion ID | Notes |
|------|-----------|-------|
| Daily Mathematics Journal | `a49dfa85e41846e79080b811b9b21f3b` | Parent for daily entries |
| Supreme Mathematics — Collection | `c3ae0c2d3d4a4c4c85322b09b23873b7` | Reference hub |
| Supreme Mathematics Reference | `b5ff9a45427b4833ba7e8675d1f78278` | Full reference guide |
| Month/Day Fraction Calendar | `46e0a67ba3dd494fac5c1cec071123ca` | **PRIMARY spec source** |
| Lunar Cycle Learning Thread | `35603691bd5e81a3a4d4fa3b27ca0975` | Moon spec + 13-month study |

Daily entries live as child pages of the Journal with the title format `Month D, YYYY` (e.g. "May 29, 2026"). The `notion_sync.push()` function writes to the Journal by default. The user needs to set `NOTION_TOKEN` in their environment; `NOTION_PARENT_ID` defaults to the Journal page.

---

## Today's reading (2026-05-29 13:00)

```
PRIMARY — Fraction Calendar
─────────────────────────────────────────────────
Received Attention of (May = 5)
  5  Powered Refinement

Gained Intention by (29)
  2  Wisdom         [compound: 29 → 2]

Given Purpose through all being born to (5 + 29 = 34)
  7  Consciousness  [compound: 34 → 7]

SECONDARY — Method B + 12-hr clock
─────────────────────────────────────────────────
Address:        1·5·4·2   (Y·M·W·D)
Method B:       8         (date cipher)
Method C:       8
Hour 13 → h12=1: 1 Knowledge
Cipher purpose:  9 Birth
Convergence:     9 Birth

Year Arc:  1  Knowledge  (2026)
Moon:      🌔 Waxing Gibbous  95.8%  ~2 days to full
```

---

## Project tools

| Tool | File | Purpose |
|------|------|---------|
| Conversation summary prompt | `CONVERSATION_SUMMARY_PROMPT.md` | Paste at the top of any past conversation transcript to audit what was documented vs. what still needs to be written down. Works on any conversation, not just SM sessions. |

---

## Active branch

`claude/artifact-link-reference-9Mt4v` on `donationstationhp-lab/dewaynelogan-tech-con-scire`

---

## What the session discovered and corrected

1. **First pass** — Methods A/B/C were guessed without the reference. Attention/Intention/Purpose were mapped to month/day/year.

2. **First correction** — User pointed to the Fraction Calendar in Notion: Attention ← month, Intention ← day, Purpose ← reduce(month+day). Applied.

3. **Second correction (full reference received)** — User pasted the full React artifact. Revealed:
   - Attention = method_b (full date cipher), not month
   - Intention = reduce(12-hour clock), not day
   - Purpose = reduce(Attention + Intention)
   - Method A is an address, not a flat number
   - Method B = YYYYMMDD digit sum
   - Method C = reduce(month + day + year as integers)
   - SM names are the user's own cipher (7 = Consciousness, 0 = Completion, etc.)
   - Moon reference = 18:14 UTC, not midnight

4. **Third correction (5-part instruction set, 2026-05-29)** — User re-established the Fraction Calendar as the PRIMARY frame:
   - Received Attention = month; Gained Intention = raw day; Given Purpose = unreduced M+D
   - Compound-not-collapsed: multi-digit sums shown unreduced with SM position as secondary lookup
   - Fixed verbs: Received / Gained / Given baked into daily.py (not from lexicon)
   - Moon: "Last Quarter" renamed "Third Quarter"; synodic calc labeled outer/astronomical only; doctrinal 28-day/13-month cycle held-in-study; no SM position mapping
   - Sources cited explicitly in return dict: fraction_calendar + lunar_thread Notion IDs
   - Method A/B/C relegated to secondary labeled lens

All corrections are now sealed in the codebase. 112 tests encode the correct arithmetic.
