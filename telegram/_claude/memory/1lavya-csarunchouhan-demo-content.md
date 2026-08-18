---
name: 1lavya-csarunchouhan-demo-content
description: "CS Arun Chouhan's live exam content has grown from a 20-MCQ demo to 1,025 MCQs (Foundation+Intermediate merged) + 47 descriptive — see the 2026-08-10 update below for current counts and the merge-tool architecture; the original QA finding (his source docx sometimes marks the WRONG option as correct) still applies to any future extraction"
metadata: 
  node_type: memory
  type: project
  originSessionId: eff70d38-31a6-4cc7-baf2-a93b1aa25479
  modified: 2026-08-10T15:03:36.183Z
---

**SUPERSEDED BY THE 2026-08-10 UPDATE AT THE BOTTOM OF THIS FILE** — the
counts below (20 MCQs, 5 descriptive) describe the original 2026-08-09 demo
batch only. Read the update first if you just need current state; the
original section is kept for the still-relevant QA finding about his source
docx files.

---

Built 2026-08-10, extends [[1lavya-study-hub-tenant-aware-live]] and
[[1lavya-tenant-schema-artifacts]]. Files:
`telegram/assets/exam_bot/faculty/csarunchouhan/mcq_questions_extracted.json` (20 MCQs)
and `.../book_questions_extracted.json` (5 descriptive) — both loaded live by
`telegram/bots/faculty_bot.py`/`exam_hub_bot.py` for `TENANT_ID=csarunchouhan`.

**Content**: 10 MCQs CMA Foundation (Module 1, Constitutional Law — from his own
"10 Most Important Questions" table, cross-checked against his Answer Key table) + 10
MCQs CMA Intermediate (Companies Act 2013, Module 12, incorporation topics — from
`IncorporationOfCompany_50MCQs_June2026.docx`) + 5 descriptive CMA Intermediate
(Companies Act 2013 — corporate veil, OPC incorporation, prospectus misstatement
liability, red herring prospectus, deposits from members). Verified end-to-end via
simulated callback-flow tests (no live Telegram needed) before being called done.

**Important, reusable finding — his `IncorporationOfCompany_50MCQs_June2026.docx`
(and likely his other CMA Inter MCQ docx files, unverified) has a real error rate**:
that file marks a "✓ CORRECT ANSWER" on each question, but cross-checking the marked
option against the question's own explanation paragraph (not just trusting the
checkmark) found **5 of ~16 questions inspected had a real problem**: 2 with the
checkmark simply on the wrong option (the explanation described a different option
entirely), 1 with an outdated numeric rule (OPC residency "182 days" — superseded by
120 days per a 2021 amendment) that would have contradicted this same tenant's own
already-published descriptive answer, and 1 with a likely-outdated small-company
threshold (probably superseded by a 2022 amendment). **All 5 were excluded, not
"corrected and used"** — full detail in `mcq_questions_extracted.json`'s own
`_source_note`.

**Applies to any future extraction from his remaining ~355 un-extracted MCQs**: never
trust a "✓ CORRECT ANSWER" / answer-key marker in his source files without
cross-checking it against that same question's own explanation text (where one
exists) and independently verifying the underlying legal fact — especially for any
numeric threshold, time period, or monetary limit, which are the categories most
likely to have been amended since the document was written.

---

**Update 2026-08-10, later same day — content grew to 1,025 MCQs + 47
descriptive, a real drift bug found+fixed, and a merge tool now exists.**

A concurrent session (not this one — see CLAUDE.md section 2's multi-agent
note) built `telegram/assets/faculty/csarunchouhan-cma-inter-law/
convert_inter_law_mcqs.py`, a deterministic converter for 14 real MCQ docx
papers (Companies Act + labour-law modules, CMA Intermediate) — 650/650
records extracted clean (0 exclusions, 0 answer mismatches, 0 missing
explanations per its own report), and it writes DIRECTLY to the tenant's
shared bot-facing file.

Checking this on Pranav's request surfaced a real live bug: **the running
bot process didn't know the file had changed underneath it.** JSON is
load-once-at-startup (see [[1lavya-platform-backend-built]]) — the converter
overwrote the file at 19:10, the bot process (started 18:16) kept serving
its stale 20-question in-memory snapshot until manually restarted. Same for
the descriptive file (47 on disk, 5 in memory). Validated the new content
two independent ways (the converter's own report + `validate_content_json.py`,
see [[1lavya-reporting-roadmap-decisions]]) before restarting to deploy.

Also found: the 650 new MCQs were 100% CMA Intermediate — the pre-existing
375-question Foundation file (`csarunchouhan-cma-found-law/
cma_foundation_law_faculty_mcqs.json`, flagged unmerged since 2026-08-09)
was still sitting completely un-wired, so `AVAILABLE_DATA` for this tenant
showed Intermediate only — a Foundation student would have gotten zero
MCQs. Inspected before merging: **all 375 Foundation records are
self-labeled `publication_status: "draft"` with zero real explanations**
(bare `"(B)"` answers, no reasoning) — materially lower quality than the
Intermediate set. Flagged explicitly; Pranav chose to merge as-is now,
explanations to follow later without needing a re-merge.

**New tool, not a hand-edit**: `telegram/tools/merge_faculty_mcq_sources.py`
— the real root cause was architectural (two independent per-level
converters both writing toward one shared file, no merge step, so whichever
runs last silently clobbers the other), not just "a file needed updating."
Reads a tenant's configured source list (`MCQ_SOURCES` dict in the script),
fails loudly on any `mcq_id` collision across sources, writes the combined
file, re-validates its own output. **Operational rule, easy to forget**: if
`convert_inter_law_mcqs.py` (or any future per-level converter that writes
directly to the shared tenant file) is re-run, **re-run this merge script
immediately after**, or the other source's content silently vanishes from
the live file again.

**Current live state for csarunchouhan**: 1,025 MCQs (650 Intermediate +
375 Foundation), 47 descriptive (Companies Act), `AVAILABLE_DATA =
{('CMA','Foundation'), ('CMA','Intermediate')}`. Bot restarted and verified
serving this. Still ~355 of his ~1,380-question total corpus un-extracted
(non-MCQ reference sheets deliberately excluded, per the converter session's
own note).

**Update 2026-08-10, later still — the merge exposed a real crash bug in
`exam_hub_bot.py` itself, now fixed.** Tapping Exam Type "FACULTY_PRACTICE"
gave no response — root cause was `McqBank.years()`'s `q.get("year",
"Unknown")`: `dict.get(key, default)` only substitutes when the key is
ABSENT, not when it's present with an explicit `null` (true for all 375
Foundation records' `year` field). `None` became an `InlineKeyboardButton`'s
`text`, which Telegram's API rejects outright. Fixed every sibling
`.get(field, default)` call in both `McqBank`/`QuestionBank` (`exam_types()`,
`years()`, `chapters()`, `_filter()`'s comparisons, the MCQ meta line) to
`q.get(field) or default` instead — verified directly against the exact
reproduction path (`years('FACULTY_PRACTICE','CMA','Foundation')` now
correctly returns `['Unknown']`, `filter_questions(...)` finds all 375
records under that bucket). **Lesson for next time**: when a validator flags
"missing recommended field, bot falls back to a generic value" (as
`validate_content_json.py` did for these exact 375 records right before the
merge), actually exercise that fallback code path before trusting the claim
— "falls back safely" and "is coded to fall back safely" turned out to be
two different things here.

**Update 2026-08-10, later still — a second real bug, this one pre-dating
the merge entirely.** All 650 Intermediate MCQs had `question_html:
"<p></p>"` — genuinely blank, students saw options with no question.
Root-caused in the real source docx: `convert_inter_law_mcqs.py` assumed
the question stem was inline with `"Q<n>."`, but these particular files put
`"Q1. [topic]"` on its own paragraph and the actual question text on the
NEXT paragraph — a shape the parser's loop had no branch for, so it
silently dropped that paragraph. Fixed the parser (append any pre-option
paragraph to the question text instead of discarding), re-ran the
converter (0/650 blank after), re-ran the merge (converter always clobbers
the shared tenant file, re-merge is mandatory every time it runs), and this
time **verified via directly simulating `send_mcq()`'s own rendering logic
against a random sample of real records**, not just checking JSON in
isolation.

**The more important fix**: `validate_content_json.py`'s `_is_present()`
now strips HTML tags before checking blankness, so `"<p></p>"` is correctly
treated as empty everywhere. Before this, a field could be "structurally
present" (non-empty string) while being completely void of real content,
and the validator said "0 errors" both times this happened. **Both bugs
this session — the null-vs-missing crash and this one — came from the same
root habit: trusting a structural check ("0 errors," "0 issues") without
exercising the actual rendered output.** Don't repeat that shortcut on this
tenant's content, or any other faculty's, going forward.

**Update 2026-08-10, later still — a THIRD real bug, this one leaking the
correct answer to students.** 50 records (all from
`Factories_Act_50_MCQs_June2026 (1).docx`) showed a checkmark against the
right option inline, before the student answered. `convert_inter_law_mcqs.py`
already stripped an inline "✓ CORRECT ANSWER" marker (this docx set predates
FACULTY-MCQ-TEMPLATE.md's answer-key-only convention), but its regex
required the word "ANSWER" — this one file used the shorter "✓ CORRECT."
Scanned all 14 source files for every distinct marker phrase actually used
(exactly two exist) before fixing, rather than special-casing the one file.
Fixed the regex to make "ANSWER" optional; re-ran, re-merged, re-validated,
restarted, and verified via direct rendering simulation against all 50
previously-affected records specifically (0 leaks) plus a broader sample.

Also added a permanent defense: `validate_content_json.py` now ERRORs on
any checkmark character in `options`/`question_html` (never `answer_html`,
which is supposed to reveal the answer) — this exact leak class can't pass
silently again for this or any future faculty's content.

**Three real bugs found in this one tenant's pipeline in a single session**
(null-vs-missing crash, blank questions, leaked answers) — all three had
already passed some "0 issues" structural check before a live report caught
them. If more of Arun's ~355 remaining un-extracted questions get converted
later, budget for an actual rendering spot-check as a real step, not an
afterthought.
