# Conversation Summary Prompt
*Paste this at the start of any conversation transcript to extract documentation status.*

---

You are auditing the conversation transcript that follows this prompt. Your job is to extract two things:

1. **What has been documented** — decisions, rules, implementations, or data that were explicitly written into a file, committed to code, saved somewhere, or stated as final and sealed during this conversation.

2. **What still needs documentation** — anything discovered, decided, or agreed upon verbally during the conversation that was never written into a file, saved, or confirmed as recorded somewhere.

Read the entire transcript below, then respond using this exact format:

---

### DOCUMENTED
*(Things that were written, saved, committed, or sealed)*

For each item:
- **What:** One sentence describing the decision, rule, or implementation.
- **Where:** Where it was saved — file name, commit, page title, or system (e.g. "committed to repo", "saved in Notion", "written to config file").
- **Status:** `sealed` / `committed` / `saved` / `in-progress`

---

### NEEDS DOCUMENTATION
*(Things said or decided but never written down)*

For each item:
- **What:** One sentence describing what was discovered or decided.
- **Why it matters:** How it affects the project or future work.
- **Suggested home:** Where it should be recorded (e.g. a README, a config file, a notes page, a specific file in the project).

---

### OPEN QUESTIONS
*(Things that came up but were not resolved)*

For each item:
- **Question:** What remains unclear or undecided.
- **Context:** What was said about it in the conversation.
- **Blocking:** Does this block anything? (yes / no / partial)

---

### CORRECTIONS MADE
*(Things that started wrong and were fixed during the conversation)*

For each item:
- **Error:** What was incorrect at the start.
- **Fix:** What replaced it.
- **Recorded:** Was the fix written somewhere, or just stated verbally? (yes / no)

---

### Output rules
- Be specific. "Discussed moon phases" is not useful. Write exactly what was decided and where it ended up.
- If you cannot find where something was saved or committed, put it under NEEDS DOCUMENTATION.
- Do not invent or infer anything not present in the transcript.
- Keep each bullet to 1–2 sentences.
- If a section has nothing to report, write "None identified."

---
*(Paste the conversation transcript below this line)*
