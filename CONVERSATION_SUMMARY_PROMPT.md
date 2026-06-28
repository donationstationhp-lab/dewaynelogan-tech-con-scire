# Conversation Summary Prompt
*Paste this at the top of any past conversation transcript to extract documentation status.*

---

## Prompt

You are auditing a past conversation about the **Supreme Mathematics Daily Reading Engine** (repo: `donationstationhp-lab/dewaynelogan-tech-con-scire`). Your job is to extract two things:

1. **What has been documented** — decisions, implementations, corrections, sealed rules, and data that were committed or recorded in `CONTEXT_FOR_CLAUDE.md`, the codebase, or Notion during this conversation.

2. **What still needs documentation** — open threads, unresolved questions, mid-conversation discoveries, or decisions made verbally that were never written into a file, a commit message, or `CONTEXT_FOR_CLAUDE.md`.

---

### Format your response as follows:

---

#### DOCUMENTED (sealed / committed / recorded)

For each item:
- **What:** one-sentence description of the decision, rule, or implementation
- **Where:** file path, commit SHA (if visible), or Notion page name/ID
- **Status:** `sealed` | `committed` | `in-progress`

---

#### NEEDS DOCUMENTATION (open / verbal only / not yet written)

For each item:
- **What:** one-sentence description of what was discovered or decided
- **Why it matters:** how it affects the engine, lexicon, moon calc, Fraction Calendar, or Notion sync
- **Suggested home:** where it should be recorded (e.g., `CONTEXT_FOR_CLAUDE.md`, `data/sm_lexicon.json`, `suprememath/daily.py` docstring, Notion page, new file)

---

#### OPEN QUESTIONS (unresolved as of this conversation's end)

For each item:
- **Question:** what remains unclear or undecided
- **Context:** what was said about it
- **Blocking:** does this block any existing feature? (yes / no / partial)

---

#### CORRECTIONS MADE (things that were wrong and fixed)

For each item:
- **Error:** what was incorrect
- **Fix:** what replaced it
- **Sealed:** yes / no

---

### Key vocabulary to watch for in the transcript

Use these terms to identify relevant passages:

| Term | Meaning |
|------|---------|
| Fraction Calendar | Primary reading frame: Attention = month, Intention = raw day, Purpose = unreduced M+D |
| compound-not-collapsed | Multi-digit sums shown unreduced; SM position is a secondary lookup |
| Method A / B / C | Secondary arithmetic lens (labeled, not primary) |
| sealed | A decision the user explicitly froze — do not change without being asked |
| DKL_LOOP | 7-step etymological reasoning protocol |
| Lexicon | `data/sm_lexicon.json` — user's own SM cipher, not the standard Five Percent list |
| Steward | Role with authority over doctrinal (moon/calendar) interpretation |
| held-in-study | An open thread acknowledged but not yet implemented operationally |
| notion_sync | `suprememath/notion_sync.py` — pushes daily readings to Notion |
| CONTEXT_FOR_CLAUDE.md | The transmittable session briefing file |

---

### Output rules

- Be specific. Vague entries like "discussed moon phases" are not useful. Write: "User sealed Third Quarter (not Last Quarter) as the correct phase name — `suprememath/moon.py` line ~42."
- If you cannot find where something was committed or saved, mark it `NEEDS DOCUMENTATION`.
- If a decision contradicts `CONTEXT_FOR_CLAUDE.md` as you know it, flag it under `CORRECTIONS MADE` and note whether it was resolved.
- Do not invent or infer decisions not present in the transcript.
- Keep each bullet to 1–2 sentences.
