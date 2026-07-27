# SKILL — Question Bank: Chapter Book Rendering (Layer 2 → Layer 3)

> **What this is:** how `first_run/scripts/generate_chapter_book.py` turns
> `questions_index.json` (Layer 2, one row per qblock — see
> `SKILL-question-bank-html-schema.md`) into one chapter's Question Book HTML (Layer 3),
> matching the quality bar of `books/question-bank/metadata-index/AS10_Question_Book.html`.
> `first_run/scripts/generate_all_chapter_books.py` (added 2026-07-26) batch-drives this
> function once per unique `final_chapter` found in the index — that's how all 34 books get
> (re)built in one command rather than one `generate_chapter_book.py` invocation per chapter.
> Both scripts read/write exclusively inside `first_run/output/generated-from-script/`.
>
> Read `SKILL-question-bank-topic-tagging.md` first (Final Chapter placement is decided
> there, at tagging time — this skill only renders what tagging already decided). Read
> `SKILL-question-bank-question-splitting.md` for why most questions arrive here already
> single-topic.
>
> **This skill also carries a live list of open design issues (§3) found during Pranav's
> first real-data review (2026-07-25, reviewing `AS02_Question_Book.html`). These are
> flagged, not resolved — do not silently "fix" them by picking a design unilaterally.
> Pranav is running a structured review pass and wants to decide all of them together once
> he's done reviewing.**

---

## 1. Current design (revised 2026-07-26 — MCQs removed, several new reader-facing fields added)

`generate_chapter_book.py <unitcode> <standard-label> <chapter-title> <output-filename>`
queries `questions_index.json` for:

- **`home`** — every row where `final_chapter == unitcode`.
- **`integrated`** — every row where `final_chapter != unitcode` but the target unit
  appears as one of the row's *secondary* `topics[]` tags (i.e. `topic_count > 1`, a
  genuinely connected multi-topic question homed elsewhere).

**MCQs are excluded from the rendered book entirely (2026-07-26 decision, Pranav)** —
`mcq`/`case-mcq` rows are filtered out of `home` before rendering (they still exist in
`questions_index.json`, just never queried into a chapter book). Sections are now:
- **Section I — Descriptive** (everything in `home` after MCQs are excluded).
- **Section II — Integrated** (rendered regardless of qtype).

Each row renders as one `.qblock` card, in order: `qmeta` line (source paper · question
number · marks · **Approx Time** [marks × 1.8 min, rounded up; RTP-no-marks → "10–20
minutes"] · topic, written in full as `{unitcode with underscores} : {standard —
title} / ICAI Study Mat Topic No : {subtopicref}`, joined with `+` when a row has more
than one tagged topic), the question (with any `case_facts_html` prepended inline), the
answer, a Common Student Mistakes box **colour-coded by provenance** (tan/orange
`.mistakes.icai` for a real quoted ICAI Examiner's Comment, pale pink `.mistakes.synth`
for an Author's Note — colours now match `book-style.json`'s `examiner_comment_*` /
`synthesized_comment_*` values, closing the gap where both used to render identically),
a blank **Student Self Notes** box, a **Notebook Ref No** field, a freeform **My Tag**
field, and a **Revision Phase 1/2/3** tick-box line. The old per-question
**Extraction Note** and the file-level **Build Info** footer are no longer rendered at
all (removed at Pranav's request — student-facing text, not engineering plumbing; the
underlying data is still in `questions_index.json` for anyone auditing the pipeline).
Every chapter book also opens with a small `.brand-header` and closes with a
`.brand-footer` (Pranav Bhaiya / Newton of Accounts / AIR 1-1-5 / Kahaan-Koncept-Karma),
and ends with a blank, dotted-line **"Sanjeevani Booti 2: Error Register"** page
(`.error-register`, `page-break-before:always`) with two sections — Concepts I Forgot /
Mistakes I Repeated More Than Twice. The book title (`<h1>` and `<title>`) is now just
`{standard_label} — {chapter_title}`, no "Question Book" suffix.

See `first_run/output/How-to-Read-this-Book.md` (new, 2026-07-26) for the reader-facing
explanation of every colour/field above — written so a student understands *why* each
small thing exists, not just what it is. Point students there rather than re-explaining
these conventions inline anywhere else.

Regenerated for all 34 chapters via `generate_all_chapter_books.py`, validated clean (0
unclosed tags, 0 NUL bytes, 0 backticks, 0 placeholders, 0 duplicate IDs) after this
revision.

**Bug fixed this revision:** `topic_label()` previously only displayed the tag matching
the *current* chapter, so a connected multi-topic question shown in a secondary
chapter's Integrated section silently hid its other tagged topic(s) — found via
`AS16_Question_Book.html`'s MTP_May2026_Set2 Q8 entry, which showed "AS 16" only despite
also testing AS 10. Fixed by rendering every tagged topic on the row, joined together
(see the full-format description above); confirmed fixed by re-checking that same row
after regeneration.

**Still open / not part of this revision:** OP/PP recurring-question tags (duplicate
detection still designed, not built — see `SKILL-question-bank-duplicate-detection.md`)
and a short-chapter-name field for the topic-tag display (needs Pranav's input to draft
36 names before it can replace the full title currently used). Both are documented as
"coming in a future edition" in `How-to-Read-this-Book.md` rather than silently absent.

## 2. A chapter's Section III being empty is expected, not a bug

Because independent multi-topic questions are split into single-topic records at
*extraction* time (see the splitting skill), Section III only ever catches the rarer
*connected* case. A chapter with zero Integrated questions across the whole pilot batch
(true for AS 2 as of 2026-07-25) is a legitimate finding — state it plainly in the book's
own scope note (as `AS02_Question_Book.html` does), don't treat it as an extraction gap.

## 3. Open issues from Pranav's first real-data review (2026-07-25)

**§3.1, 3.2, and 3.3 below were RESOLVED (design finalized) on 2026-07-26 — see
`SKILL-question-bank-phase1-definition-of-done.md` §2 for the locked rule (one home
chapter per cluster = latest-taught touched standard, shown under a new "(b) Integrated
with Other Standards" sub-heading, with a cross-reference-only pointer in every other
touched chapter; case-scenario narratives rendered once per cluster, nested, never
duplicated per MCQ). Implementation in `extract_questions.py` /
`generate_chapter_book.py` is not yet built — the design is settled, the code isn't.
§3.4 (theory/practical) is also resolved: fold into the accuracy-audit pass per the same
skill §3, then surface in rendering. Kept below for the historical context of how each was
found.**

### 3.1 Case-scenario narrative repeated verbatim across every sibling MCQ

A single case scenario with 4 dependent MCQs currently has its full narrative embedded
inline in **all 4** rendered qblocks (`case_facts_html` is duplicated per row in
`questions_index.json` itself, then rendered once per qblock). Pranav's objection: the
source PDF states the scenario once, with 4 questions beneath it — repeating it 4x in the
generated book wastes space, and print has a real cost. **Needs a design decision**:
render the scenario once per case-scenario group with the sibling MCQs listed beneath it
(changes the qblock grouping logic, not just a CSS tweak), vs. some other de-duplication
approach. Not yet decided.

### 3.2 Case-scenario clusters that span multiple chapters

Found in `PYQ_Jan2026.html`: one case scenario (the "P Limited" cluster) has Q1–Q3
individually testing AS 11 and Q4 individually testing AS 2. Each individual MCQ is
correctly tagged single-topic on its own (per the normal splitting convention — this is
*not* the same bug as a connected question needing multiple topic tags). The open question
is what happens **at the cluster level**: Pranav's view is that a case-scenario cluster
whose sibling questions collectively span two chapters should be treated as a group,
homed under whichever standard is taught **later** in `teaching_sequence` (same
directional logic as the existing Final Chapter rule for connected questions — see the
tagging skill §4), and shown there under a new **"MCQ — Integrated with Other AS"**
bucket, distinct from ordinary single-AS MCQs — rather than the AS 2 chapter showing Q4 as
an ordinary Section I entry as it does today.

**Not yet decided:** does the earlier-taught chapter (AS 2 here) show this cluster at all
(e.g. cross-referenced under its own "Integrated" bucket), or does it disappear from that
chapter's book entirely? Is this decided per-cluster or does each individual MCQ need a
new `data-cluster-id`-type attribute so extraction can detect "this MCQ's siblings, under
the same `data-case-ref`, tag a different `unitcode`" mechanically rather than by manual
review? This needs a schema change (probably in `SKILL-question-bank-html-schema.md`'s
case-scenario section and/or a new field in `questions_index.json`), not just a rendering
change — flagging here first since it was surfaced during rendering review.

### 3.3 Sections I and II need the same Single-AS vs. Integrated split that Section III implies

Directly follows from 3.2: whatever rule ends up governing "does this MCQ cluster/question
count as Integrated," Sections I (MCQs) and II (Descriptive) currently show **every** `home`
row in one flat list regardless of `topic_count` — there's no sub-split for a `home` row
that is itself a connected multi-topic question tagged secondary-elsewhere. Once 3.2 is
resolved, the generator needs equivalent Single-AS/Integrated sub-buckets inside a
chapter's own Sections I and II, not only as the separate Section III.

### 3.4 Theoretical vs. Practical — already tagged in Layer 1, not yet surfaced

`data-qtype` on descriptive qblocks already carries `theory` vs `practical` (confirmed
present across all 5 sitting files, e.g. `RTP_May2026.html` has 12 `theory` + 7
`practical` records) — **this is not a new tagging layer to build**, it already exists.
What's missing: (a) it isn't surfaced in the chapter book's `qmeta` display or as a
queryable field anywhere downstream, and (b) the existing tags haven't had a dedicated
review pass. Pranav's proposed heuristic for that review: a question that is verbose/
text-driven with few or no numbers is likely `theory`; still requires human judgment,
not a fully mechanical reclassification — flag disagreements rather than silently
overriding the existing `data-qtype` value.

## 4. Style reference

Inline `<style>` block, no external stylesheet (this differs from the sitting-HTML schema,
which is meant to eventually share a generated `book-style.css` per CLAUDE.md §7 — the
chapter-book generator hasn't been reconciled with that single-source-of-truth styling
architecture yet; today its CSS lives directly in the Python script's `STYLE` constant).
Class names deliberately mirror `AS10_Question_Book.html`: `.qblock`, `.qmeta`, `.badge`,
`.question`, `.answer-block`, `.mistakes`, `.extraction-note`, `.na`, `.note`.
