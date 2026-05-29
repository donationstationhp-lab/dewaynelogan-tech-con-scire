# Context for Claude — Supreme Mathematics Daily Reading Engine
*Transmittable briefing. Paste at the top of a new conversation to continue without loss.*

---

## Who I am and what we built

I am Dewayne Logan. In this session we built a Supreme Mathematics daily reading engine in Python, housed in a GitHub repository (`donationstationhp-lab/dewaynelogan-tech-con-scire`, branch `claude/artifact-link-reference-9Mt4v`). The engine is a CLI tool (`sm_daily.py`) backed by a standalone module (`suprememath/`) and an editable data file (`data/sm_lexicon.json`).

The work started from a React artifact I had built (a browser-based daily reading component). That artifact was the sealed reference. We rebuilt it in Python, correcting the mapping twice as the full system came into view.

---

## The sealed arithmetic

### Three methods

**Method A — address** (`Y·M·W·D`)
Not a single number. Four independent reductions:
- `Y = reduce(year)`
- `M = reduce(month_number)`
- `W = reduce(ceil(day_of_year / 7))`
- `D = reduce(day_of_month)`
Displayed as e.g. `1·5·4·2` for 2026-05-29.

**Method B — sum** (primary date cipher → becomes Attention)
Concatenate `YYYYMMDD` as a digit string, sum all digits, reduce.
2026-05-29 → `"20260529"` → 2+0+2+6+0+5+2+9 = 26 → **8**

**Method C — whole**
`reduce(month_int + day_int + year_int)`
2026-05-29 → 5 + 29 + 2026 = 2060 → **8**

`reduce(n)` is the standard digital root: sum digits of abs(n) until 0–9.

### The reading frame

```
now  →  Calculate (Method B)      →  Attention   "of"
     →  Decode (12-hour clock)    →  Intention   "by"
     →  Translate (Att + Int)     →  Purpose     "through"
     →  Converge (Att + Int + Pur)→  Resolution
```

- **Attention** = `method_b(date)` — the day's sealed cipher. Does not change within the day.
- **Intention** = `reduce(h12)` where `h12 = (hour % 12) or 12` — changes each hour.
- **Purpose** = `reduce(Attention + Intention)` — the resolution of the two.
- **Convergence** = `reduce(Attention + Intention + Purpose)` — when this equals 6 (Equality), the reading is "aligned."
- **Year Arc** = `reduce(year)` — the year's holding container. 2026 → 1 = Knowledge.

### The calculation display
For daily journal entries, digits are shown in M+D+YYYY order (matching existing hand-written entries). The sum is order-independent and equals Method B.
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

The `verb` field is sealed where present: 1 is *gained*, 7 is *given*. The `say` field holds the brief instruction for each seat. **Etymology lives only in the data file — no root judgment is baked into the logic.**

---

## The Fraction Calendar (parallel system, Notion)

A separate but related document in Notion ("Month/Day Fraction Calendar — Seed (Jan 1)") defines a parallel frame:
- **Received Attention of (Month)**
- **Gained Intention by (Day)**
- **Given Purpose through all being born to (Month + Day)**

This is a *different* system from the daily reading engine above. In that system, Purpose = reduce(month + day). In the engine, Purpose = reduce(Attention + Intention) where Attention is the full date cipher and Intention is the hour. Both are the user's own work; do not conflate them.

---

## The three prepositions (sealed)

These come directly from the artifact and are stored in `sm_lexicon.json` under `reading_labels`:
- Attention → **"of"** / operation: **Calculate**
- Intention → **"by"** / operation: **Decode**
- Purpose → **"through"** / operation: **Translate**

From the May 26 entry in Notion: *"Attention, Intention, Purpose, at root, are a stretching of consciousness toward the lights: ATTENTION (ad-tendere, stretch-toward), INTENTION (in-tendere, stretch-into), PURPOSE (pro-pōnere, place-forth)."*

---

## Moon phase (sealed)

- 8 phases — not 4. Source: fivepercenterlessons.com (sealed by the user 5/4/2026).
- Reference new moon: `2000-01-06 18:14 UTC` (sealed; not midnight).
- `days_to_full` field is included in the reading output.
- The 8 phases are: New, Waxing Crescent, First Quarter, Waxing Gibbous, Full, Waning Gibbous, Last Quarter, Waning Crescent.
- 8 phases = Position 8 (Build / Destroy). Doctrinally: *the moon is the body of Position 8 walked across the synodic cycle.*

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

62 tests pass. Run with: `python -m pytest tests/`

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
| Month/Day Fraction Calendar | `46e0a67ba3dd494fac5c1cec071123ca` | Parallel fraction system |
| Lunar Cycle Learning Thread | `35603691bd5e81a3a4d4fa3b27ca0975` | 13-month / 28-day study thread |

Daily entries live as child pages of the Journal with the title format `Month D, YYYY` (e.g. "May 29, 2026"). The `notion_sync.push()` function writes to the Journal by default. The user needs to set `NOTION_TOKEN` in their environment; `NOTION_PARENT_ID` defaults to the Journal page.

---

## The two-calendar system (sealed 5/26/2026)

From the May 26 Notion entry ("Two Reeds Named: Sun & Moon"):
- **Gregorian** (solar reed) — counted from the Door (January ← *Iānus*, doorway)
- **Roman** (lunar reed) — counted from Mars (March ← *Mārtius*, the elder year-head)

Both calendars produce a Method A address. The user is tracking both in parallel. The lunar 13-month / 28-day calendar is *known doctrinally but not yet walked operationally* — it is an open study thread, not yet implemented in the engine.

**SUN** ← PIE *sóh₂wl̥* — the burning one; rules the day and year.
**MOON** ← PIE *meh₁-* — to measure; root of moon, month, and measure itself.
**CALENDAR** ← *kalendae* ← *calāre* — to call out the new moon.

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

All corrections are now sealed in the codebase. 62 tests encode the correct arithmetic.

---

## Active branch

`claude/artifact-link-reference-9Mt4v` on `donationstationhp-lab/dewaynelogan-tech-con-scire`

Latest commit: `88f8195` — "Rebuild from sealed reference: correct all three methods and reading frame"

---

## Today's reading (at time of writing, 2026-05-29 13:00)

```
Address:    1·5·4·2   (Y·M·W·D)
Method B:   8         (Attention — date cipher)
Method C:   8

Attention:  8  Build / Destroy     "of"    Calculate
Intention:  1  Knowledge           "by"    Decode       (hour 13 → h12=1)
Purpose:    9  Birth               "through" Translate  (reduce 8+1)
Convergence: 9  Birth                                   (reduce 8+1+9=18→9)

Year Arc:   1  Knowledge           (2026)
Moon:       🌔 Waxing Gibbous  95.8%  ~2 days to full
```
