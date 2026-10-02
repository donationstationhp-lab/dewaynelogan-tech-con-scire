import json, math
from datetime import date

YEAR = 2030
YEAR_ARC = 5  # reduce(2+0+3+0)=5

CIPHER = {
    1: ("Knowledge",          "*ǵneh₃-* — to know",                     "Track the trail. Attend to what can be learned."),
    2: ("Wisdom",             "*weid-* — to see",                         "Let seeing become the means; act on what was shown."),
    3: ("Understanding",      "*(inter/under)-stā-* — to stand between",  "Stand on the common ground beneath the two."),
    4: ("Cultured Freedom",   "*kʷel-* — to turn, to till",               "Work the freedom. Till it; it is freedom only once made."),
    5: ("Powered Refinement", "re- + finis — back to the fine",           "Refine by force held steady; bring it back to fineness."),
    6: ("Equality",           "*aequus* — level, even",                   "Bring the distinct to par. Pair without flattening."),
    7: ("Consciousness",      "com-scīre — to know-with",                 "Know with another. This seat is given, not gotten."),
    8: ("Build / Destroy",    "de-struere — to un-pile",                  "Tear down what was piled wrong; raise it true."),
    9: ("Birth",              "*bʰer-* — to bear, to carry",              "Bear it forth. Carry the made thing into being."),
}

MONTH_NAMES = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
               7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}
MONTH_DAYS  = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}

# Reference: New Moon Jan 4, 2030
REF_NEW = date(2030, 1, 4)
SYNODIC  = 29.53

def reduce(n):
    n = int(n)
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def mb(month, day):
    return reduce(sum(int(c) for c in f"2030{month:02d}{day:02d}"))

def method_a(attention, day):
    third = reduce(attention + math.ceil((day - 2) / 7))
    return (YEAR_ARC, attention, third, reduce(day))

def moon(month, day):
    age = (date(2030, month, day) - REF_NEW).days % SYNODIC
    illum = (1 - math.cos(2 * math.pi * age / SYNODIC)) / 2 * 100
    dtf = 14.765 - age if age <= 14.765 else 14.765 + SYNODIC - age
    dtf_r = round(dtf)
    if age < 1.5:
        em, ph = "🌑", "New"
    elif age < 7.38:
        em, ph = "🌒", "Waxing Crescent"
    elif age < 8.38:
        em, ph = "🌓", "First Quarter"
    elif age < 14.765:
        em, ph = "🌔", "Waxing Gibbous"
    elif age < 16.0:
        em, ph = "🌕", "Full"
    elif age < 22.15:
        em, ph = "🌖", "Waning Gibbous"
    elif age < 23.15:
        em, ph = "🌗", "Third Quarter"
    else:
        em, ph = "🌘", "Waning Crescent"
    if ph == "Full":
        return f"{em} Full ({illum:.1f}% illuminated, full now)"
    elif age < 14.765:
        return f"{em} {ph} ({illum:.1f}% illuminated, ~{dtf_r} days to full)"
    else:
        return f"{em} {ph} ({illum:.1f}% illuminated, {dtf_r} days to next full)"

def cipher_line(n, raw=None):
    nm, et, ap = CIPHER[n]
    cmp = f" [compound: {raw} → {n}]" if raw and raw > 9 else ""
    return f"{n} — {nm}{cmp} · _{et}_\n\n> {ap}"

def page(month, day):
    mn       = MONTH_NAMES[month]
    attention = reduce(month)
    purp_raw  = attention + day
    purp_red  = reduce(purp_raw)
    ma        = method_a(attention, day)
    MB        = mb(month, day)
    mb_hour   = reduce(MB + 1)
    conv      = reduce(2 * mb_hour)
    conv_str  = f"{conv} — {CIPHER[conv][0]}"
    if conv == 6:
        conv_str += " ✦ aligned"
    yr_etym   = CIPHER[YEAR_ARC][1]

    content = f"""\
## Fraction Calendar · Received · Gained · Given
Founder's Month/Day Fraction Calendar

---

**Received Attention of ({mn} = {attention})**

{cipher_line(attention)}

---

**Gained Intention by ({day})**

{cipher_line(reduce(day), day)}

---

**Given Purpose through all being born to ({attention} + {day} = {purp_raw})**

{cipher_line(purp_red, purp_raw)}

---

## Secondary Lens · Method B + 12-hour clock

- Method A (address): {ma[0]}·{ma[1]}·{ma[2]}·{ma[3]}
- Method B (YYYYMMDD): {MB} — {CIPHER[MB][0]}
- Hour (12-hr): 1 — Knowledge
- Purpose (MB+Hour): {mb_hour} — {CIPHER[mb_hour][0]}
- Convergence (all three): {conv_str}

---

## \U0001f319 Moon

{moon(month, day)}
outer/astronomical synodic calc only — doctrinal: 28-day/13-month, held-in-study

---

## Year Arc · 2030

{YEAR_ARC} — {CIPHER[YEAR_ARC][0]} ({yr_etym})

---

## Sources

- Founder's Month/Day Fraction Calendar
- Lunar Cycle Learning Thread

---

## Planner (Inked Commitments)

- [ ] 1 clear priority for the day
- [ ] 1 call or message to return
- [ ] 1 system clean-up or put-away

---

## Reflections

## Manifestations

## Observations

## Daily Visual Documentation

Upload images of today's whiteboard + proof of what got completed."""

    return {"icon": "\U0001f4d0", "properties": {"title": f"{mn} {day}, 2030"}, "content": content}

BASE = "/tmp/claude-0/-home-user-dewaynelogan-tech-con-scire/6c971680-bba7-5e2b-a3fb-6dd7d1e50ca9/scratchpad"

for m in range(1, 13):
    days = MONTH_DAYS[m]
    abbr = MONTH_NAMES[m][:3].lower()
    if days == 31:
        batches = [(1,16),(17,31)]
    elif days == 30:
        batches = [(1,15),(16,30)]
    else:  # 28
        batches = [(1,14),(15,28)]
    for bn,(s,e) in enumerate(batches,1):
        pages = [page(m,d) for d in range(s,e+1)]
        path = f"{BASE}/{abbr}2030_batch{bn}.json"
        with open(path,'w',encoding='utf-8') as f:
            json.dump(pages, f, ensure_ascii=False)
        print(f"  {abbr}2030_batch{bn}.json  ({len(pages)} pages)")

print("Done. 365 pages across 24 files.")
