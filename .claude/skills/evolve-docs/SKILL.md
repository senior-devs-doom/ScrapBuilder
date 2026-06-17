---
name: evolve-docs
description: Capture what this session learned back into the project docs so the next session is faster. Invoke at the end of EVERY ScrapBuilder session (building, fixing, or even just exploring) before signing off. Updates JOURNAL.md always, and CASES.md / TOOLS.md / METHODOLOGY.md when an approach changed.
---

# evolve-docs

The mechanism that makes ScrapBuilder compound. Memory lives in docs, not in the chat.
If a lesson isn't written down here, it didn't happen. **Run this before ending any session.**

## Surgical-edit rule (apply to every change)
Edits must be precise and small; the brain stays sharp by *replacing*, not *accreting*:
- **Find the home first.** Grep the topic. Edit in place; never open a second section for
  a topic that already exists.
- **One fact, one home.** A given fact lives in exactly one doc; everywhere else links.
- **Net-neutral by default.** When you add lines, cut or merge so the doc doesn't grow.
- **Promote/refine over add.** Tighten an existing archetype/gotcha before adding new.
- **JOURNAL is the only append-only doc.** Everything else is edit-in-place.

---

## EVOLVE checklist — tick every box before closing the session

☐ **1. JOURNAL appended.**
   Add a dated entry to [JOURNAL.md](../../../docs/JOURNAL.md) using its template:
   target, archetype, tier, what you did, **Reflect** (what was brute-forced, what
   was available but unused, what the next agent does faster), open risks, rough cost.
   Newest at top. Keep it laconic.

☐ **2. CASES updated (if site taught you something).**
   Edit [CASES.md](../../../docs/CASES.md) with the abstracted pattern only:
   - New archetype → add lettered section with Tells + Playbook.
   - Refined archetype → edit in place, not append.
   - New gotcha → add to "Cross-cutting gotchas."
   - Promote theoretical → confirmed once seen in the wild.
   **CASES must be site-name-free.** No domain names, vendor product names, or
   site-specific Polish/foreign terms. Only generic patterns.

☐ **3. Grep for site-specific leakage in non-JOURNAL docs.**
   Run: `grep -rniE "(filter[A-Z]|\.pl/|\.com/[a-z]+-[a-z]+)" CLAUDE.md README.md docs/ --include="*.md" --exclude="JOURNAL.md"`
   Fix any hit that names a real URL path or product-specific term outside JOURNAL.

☐ **4. TOOLS updated (if tooling changed).**
   Edit [TOOLS.md](../../../docs/TOOLS.md) if a library worked better, a probe is
   worth keeping, or a tier boundary should be redrawn.

☐ **5. MANIFEST + README status lines updated.**
   [docs/MANIFEST.md](../../../docs/MANIFEST.md) and [README.md](../../../README.md)
   each have a **Status:** line. Update session number and any changed constraint.

☐ **6. ENVIRONMENT.md still accurate.**
   Read [docs/ENVIRONMENT.md](../../../docs/ENVIRONMENT.md). Confirm Python version,
   venv path, install command, and `run.bat` invocation match reality. Fix anything stale.

☐ **7. Net-neutral check.**
   For each doc you touched: did it grow? If yes, cut an equal amount of stale or
   redundant wording. The brain should not get longer session over session.

☐ **8. Methodology or CLAUDE.md changed (only if process itself shifted).**
   High-stakes; note why in the journal entry. Update the builder cycle line in
   CLAUDE.md if a step was added/removed. Check build-scraper/SKILL.md matches.

---

## Model note (validated Session 4)
Routine EVOLVE on normal builds is safe on a cheaper model — judgment is pre-encoded here.
Two tendencies to police on cheaper models: (1) **verbosity** — enforce one-screen rule;
(2) **accrete-vs-edit** — make it edit in place, not append duplicates.
Keep "process changes" (METHODOLOGY/CLAUDE edits) on a stronger model or under review.
