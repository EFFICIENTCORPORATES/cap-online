# Project Log — cap-online

A running status note. Newest entries at the top. One short block per session.

---

## 2026-07-28 (cont'd, 4) — Question Bank Book: full print-cost reduction pass implemented, 819 → 688 pages

Pranav gave the go-ahead to implement the punch list from the previous entry, plus new
points: a new `topic_name_abbvtd` field he added to
`books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`,
a redesigned Error Register (one shared 6-page/3-double-sided-sheet appendix instead of
34 per-chapter pages), and dropping the redundant chapter-name repeat on every
question's topic line. Explicitly asked to skip visual (screenshot) verification for
now and just document + hand over the final path.

**All implemented, pipeline rebuilt and re-validated after every change:**

1. **Topic-wise Marks Mapping bug, root cause confirmed and fixed.**
   `extract_questions.py`'s `extract_topics()` now also captures `data-subtopictitle`
   (was already present on the source tags, just never read). New
   `qb_common.abbreviated_topic_label()` prefers file 1's `topic_name_abbvtd` (matched
   via `topic_no` for the plain-integer tagging convention, e.g. Framework's "7",
   "7/9/11") and falls back to `subtopictitle` otherwise. Spot-checked on the Framework
   chapter: rows now read "6 — Fundamental Accounting Assumptions",
   "7/9/11 — Qual. Char. Fin Stmts / Elements of Financial Statements / Capital
   Maintenance", etc. — no longer the same chapter title repeated on every row.
2. **Per-question topic line no longer repeats the chapter name** — same
   `abbreviated_topic_label()`, used in `topic_full_label()` too. Shows just
   `Topic {ref}: {name}`.
3. **Empty Descriptive/Integrated sections omitted entirely** — no heading, no "no
   questions" placeholder, when a section has zero rows (`render_section()`).
4. **Repeated per-box provenance sentence removed** (~500+ Author's
   Note/Examiner's Comment boxes) — the explanation now lives once in front matter's
   How to Read This Book colour key.
5. **3-line student-fields block collapsed to 1 line**, renamed "My Notebook Ref No" →
   "My NB Page No"; the My Tag suggestion examples moved into front matter (stated
   once, not per question). "Student Self Notes" (the 2-line writing box) was
   correctly kept — a first draft of this edit accidentally deleted it entirely,
   caught and fixed in the same pass before it reached the pipeline.
6. **Error Register redesigned**: `generate_chapter_book.py` no longer emits any
   `.error-register` content per chapter (was 34 full pages). New
   `generate_qb_front_back_matter.build_error_register_pages()` builds ONE shared
   6-page appendix (3 double-sided sheets, alternating "Concepts I Forgot"/"Mistakes I
   Repeated More Than Twice") with a "Chapter/Topic" column so one register serves the
   whole book, appended at the very end of back matter.
7. **Coverage-matrix chapter column** now uses file 1's existing `chapter_name_short`
   field (via a new `qb_common.chapter_name_short_lookup()`) instead of an ad hoc
   string-split, plus CSS wrapping (`max-width`/`overflow-wrap`, `white-space: nowrap`
   removed) as a fallback for names still long after abbreviation (Framework's short
   name barely shortens the full one) — both fixes applied together as Pranav asked.
8. **Page-break blank-space bug fixed**: `table` and `.answer-block` removed from
   `qb_common.print_layer_css()`'s `break-inside: avoid` list — the exact same
   "large container jumps whole, leaves the rest of the page blank" failure the
   `.qblock` fix (2026-07-26) already solved once, rediscovered one container level
   deeper after Pranav sent real screenshots. A table with proper thead/tbody already
   only splits between whole rows, so this is safe, not a new risk.
9. **Margins checked, left unchanged** — already at a documented 6mm floor (cut from
   20mm previously), flagged as near the physical print-safety limit; explained to
   Pranav rather than reduced further.

**Two real mistakes caught and fixed within this same pass, before they reached the
pipeline**: (a) the student-fields collapse first draft deleted the separate "Student
Self Notes" writing box entirely, not just the 3 metadata lines — restored; (b) the
new CSS comment explaining fix #8 used markdown-style backtick-quoting
(`` `table` ``/`` `.answer-block` ``), which tripped this pipeline's own hard
"0 backticks anywhere" validation rule — reworded without backticks.

**Result**: full pipeline re-run (extract → chapter books → coverage matrix → stats →
front/back matter → ToC → merge → resolve) end-to-end. **688 pages**, down from 819
(131 pages / ~16%, all from removing genuine repetition and fixing real bugs, no
content cut). Validated: 0 unclosed tags (full `html.parser` pass), 0 duplicate ids,
0 NUL bytes, 0 backticks, 0 blank ToC pages.

**Not done this pass, by Pranav's explicit request**: visual/screenshot verification of
the page-break fix and the coverage-matrix wrapping. A PDF was generated via headless
Chrome (proving pagination completes and is stable at 688 pages) but not visually
reviewed page-by-page. If blank-space complaints continue after this fix, that
verification is the first real next step, not re-guessing the CSS further.

Final book: `first_run/output/QUESTION-BANK-BOOK.html`. Full detail in
`first_run/HOW-TO-BUILD-THE-BOOK.md`'s "Print-cost reduction pass" section and its two
new gotchas, and `CLAUDE.md` §6.

---

## 2026-07-28 (cont'd, 3) — Question Bank Book: Pranav's print-review punch list (recorded, NOT yet actioned — he's still reviewing)

Pranav is reviewing the 819-page merged book and sent a first batch of review points,
explicitly asking to record them and hold off implementing until he says go (he's
still reviewing, more points likely to follow). Recorded here verbatim/summarized so
nothing is lost; **none of these are implemented yet**.

1. **Empty sections should be omitted entirely, not printed as "No questions..."** —
   e.g. an empty "II. Integrated Questions" section currently still prints its heading
   + intro sentence + the honest-finding note. Only render a section when it has rows.
2. **Remove the per-box "Written by the author, not ICAI..." provenance line** — stated
   once already in front matter (How to Read This Book / Book Coverage), repeating it
   under every single Author's Note box is redundant. Drop the repeated line, keep the
   once-stated explanation in front matter.
3. **Collapse the 3-line student-fields block into 1 line**, and rename "My Notebook
   Ref No" → "My NB Page No": `My NB Page No ______  My Tag ______  Revision Phase 1 2 3`
   — currently 3 separate `<div>` lines per question. Also move the "e.g. Last-day
   Revision, Not Important..." explainer for My Tag into front matter (state once, not
   per question).
4. **Chapter-Wise Sitting Summary table: chapter-name column too wide** — long names
   like "Framework for Preparation and Presentation of Financial Statements" push the
   table past the page margin. Needs a smaller font and/or wrapping for the chapter
   column.
5. **Real print flow problem: wasted blank space after each question, answer restarts
   on a fresh page** — needs investigation into why content isn't flowing continuously
   (likely `break-inside: avoid` on `.answer-block`/`table` forcing a jump to the next
   page when the remaining space on the current page is too short, rather than letting
   a long table split across the break). Needs actual visual verification (screenshot),
   not just CSS reasoning — same lesson CLAUDE.md §7 already states.
6. **Real bug, root cause confirmed this session (see above)**: the new Topic-wise
   Marks Mapping table shows the same chapter-level title repeated on every row
   instead of each row's actual topic name. Cause: `extract_questions.py`'s
   `extract_topics()` (line 53) only captures `data-title` (chapter-level, same for
   every question in that chapter) from each sitting HTML's `topic-tag` span — it never
   captures `data-subtopictitle`, which already exists on the source tags with correct,
   specific per-topic text (confirmed present and accurate via direct grep against
   `MTP_May2023_Set1.html`). Fix: capture `data-subtopictitle` in `extract_topics()`,
   re-run `extract_questions.py`, and use it (not `title`) for the table's row label in
   `generate_chapter_book.py`'s `subtopic_key()`. Not a data-quality problem — the
   sitting HTML tagging itself is fine; only the extraction script drops a field that
   was always there.

**Also asked for**: genuine page-count-reduction ideas (separate from the fixes above,
which are also page-saving as a side effect). Ideas given in-conversation, not yet
written up as a durable doc — revisit and formalize once Pranav finishes this review
pass and gives the go-ahead to implement.

---

## 2026-07-28 (cont'd, 2) — Question Bank Book: Chapter-wise Sitting Summary + per-chapter Topic-wise Summary built (819 pages)

Pranav's request, once the 34-sitting corpus was complete: a whole-book "which chapter
matters most" marks-coverage table near the front, and a per-chapter "which topic
within this chapter matters most" table at the start of each chapter. OP/PP explicitly
confirmed out of scope for this edition (not deferred-but-maybe — a firm decision, see
the previous entry).

**Built:**
- Three new shared helpers in `qb_common.py` (`session_label()`, `dedup_marks_sum()`,
  `dedup_count()`, `sessions_for()`) so both new features and any future one share
  identical marks-aggregation logic — no risk of two tables disagreeing on a number.
- `generate_qb_coverage_matrix.py` (new script) → `output/chapter-coverage-matrix.html`:
  3 pages (MTP/RTP/PYQ), each a chapter × exam-session marks matrix, one column per
  session (an MTP session's Set 1 + Set 2 combine into one column), Total column at the
  end. RTP pages show question **count**, not marks — ICAI's RTP documents carry no
  per-question marks key, confirmed already known from `book_stats.json`. Wired into
  `qb_merge.py`'s `BOOK_ORDER`, right after the ToC.
- `generate_chapter_book.py`: a Topic-wise Marks Mapping table added to every chapter,
  right after the intro notes. **Real finding, fixed same session**: the first combined
  draft (one table, all paper types together) produced 22 columns for AS 2 — the exact
  print-width problem the whole-book matrix exists to avoid, rediscovered one level
  deeper than expected (a "single chapter" isn't automatically narrow if it's tested in
  nearly every sitting). Fixed by splitting into up to 3 mini-tables per chapter
  (MTP/PYQ marks, RTP count), same pattern as the whole-book version.

**Validated**: all 34 regenerated chapter books + the new coverage-matrix page pass a
full `html.parser` structural pass (0 errors) and a duplicate-id check (corrected to
properly anchor the regex after an earlier false-positive from `data-target-id=`
matching a naive `id="..."` pattern). Full pipeline re-run end-to-end (stats → coverage
matrix → front/back matter → ToC → merge → resolve): **819 pages** (up from 796),
38 merged sections (was 37).

Both features and the OP/PP-out-of-scope decision are documented in
`first_run/HOW-TO-BUILD-THE-BOOK.md` §5/§6 and `CLAUDE.md` §6.

---

## 2026-07-28 (cont'd) — Question Bank Book: all 34 sittings built, full pipeline rebuilt (796 pages)

Completed the scaling work the previous entry left in progress: all 24 remaining
sittings are now built and independently validated (structural checks re-run by the
orchestrating session on every file, not just trusted from each agent's self-report —
two real defects were caught this way: a stray backtick in `PYQ_Nov2023.html`'s
extraction-note, fixed directly; and my own validation script's false-positive
duplicate-id count, caused by an unanchored regex matching `data-target-id="..."`
as if it were `id="..."` — the actual merged book has 0 real duplicate ids, confirmed
with a corrected regex plus a full `html.parser` structural pass, 0 errors).

**Blocker resolved mid-session**: the account's monthly Claude spend limit that paused
the previous entry's batch reset partway through — confirmed by a live retry, not
assumed. Two further spend-limit hits occurred later in the same session; in every
case, the agent's `Write` call had already completed before the process was killed,
so the file survived regardless — this pattern (write to disk as early as possible,
refine in place) is now baked into every sitting-build agent's instructions going
forward, per Pranav's explicit request.

**Real finding, confirmed at scale**: 47 question records across 13 distinct
pre-syllabus-change topics (Hire Purchase, Departmental Accounts, Incomplete Records,
Insurance Claims for Loss of Stock, Redemption of Debentures/Preference Shares, Profit
Prior to Incorporation, Bonus Shares, Managerial Remuneration, Issue of Debentures,
Rights Issue) were tagged `LEGACY-*` across the older 2023 sittings. Fixed
`generate_all_chapter_books.py` and `generate_book_stats.py` to explicitly skip/report
these rather than silently including them or crashing — confirmed working: pipeline
run shows "Skipped 47 LEGACY records across 13 topics" and generates exactly 34
legitimate chapter books, no stray `LEGACY_Question_Book.html` file.

**Full pipeline rebuilt end-to-end** with all 34 sittings:
`extract_questions.py` (831 total question records, 897 counting case-scenario nodes)
→ `generate_all_chapter_books.py` (34 chapter books, incl. AS 1 and AS 27 now finally
covered — both previously the only two genuinely untouched chapters) →
`generate_book_stats.py` → `generate_qb_front_back_matter.py` → `generate_qb_toc.py`
→ `qb_merge.py` → `resolve_qb_toc_pages.py --remerge`. Final `QUESTION-BANK-BOOK.html`:
**796 pages** (up from 308 with the 10-sitting pilot), all 34 chapters' ToC page
numbers correctly resolved. Corpus totals: 437 distinct question numbers as originally
printed, 3,096 total marks covered, 68 real ICAI Examiner's Comments matched (up from
24) + 763 synthesized Author's Notes.

**Next**: build the two summary-table features locked in earlier this session
(Chapter-wise Sitting Summary, per-chapter Topic-wise Summary — see the previous
entry and `CLAUDE.md` §6) now that the full 34-sitting corpus finally exists, which
was the explicit precondition for starting that work.

---

## 2026-07-28 — Question Bank Book: scaling to all 34 sittings (in progress, paused on account spend limit); OP/PP scoped out of edition 1; two new summary-table features locked in

Pranav asked to build all 24 remaining in-scope sittings (from `first_run/pending/`
PDFs + `first_run/output/pending-pdf-parsed-clean/` MD aids), using the same
parallel-background-agent-per-sitting pattern this session established, batched ~5 at
a time with independent re-validation after each batch (both the agent's own
self-check and a second structural check run by the orchestrating session before
trusting the result).

**Progress at pause: 14 of 24 built and independently validated** — MTP Jan2025
Set1/Set2, PYQ Jan2025, RTP Jan2025, PYQ May2023, MTP May2023 Set1/Set2, MTP May2024
Set1/Set2, PYQ May2024, RTP May2024, MTP May2025 Set2, PYQ May2025, RTP May2025. **1
never written** (MTP May2025 Set1 — its agent died before the Write call ran). **9 not
yet started**: MTP Nov2023 Set1/Set2, PYQ Nov2023, MTP Sep2024 Set1/Set2, PYQ Sep2024,
RTP Sep2024, MTP Sep2025 Set1/Set2.

**Real finding, now a locked rule**: several 2023-vintage sittings test topics from
before a syllabus change, absent from the current 36-chapter taxonomy entirely (Hire
Purchase, Departmental Accounts, Incomplete Records, Insurance Claims for Loss of
Stock, Redemption of Debentures/Preference Shares, Profit Prior to Incorporation,
Bonus Shares, Managerial Remuneration). Tagged `LEGACY-{SLUG}` + `data-issue="topic-
legacy-not-in-current-syllabus"`; Pranav's call: keep them in the sitting record for
completeness, exclude from generated chapter books entirely (no appendix this
edition). Full detail: `CLAUDE.md` §6.

**Blocker (paused here, not a pipeline bug)**: batch 3's remaining agents all failed
mid-work on the account's **monthly Claude spend limit**. 4 of those 5 agents'
`Write` calls had already completed before the API error killed them, so their files
survived and were independently validated anyway — confirms the per-sitting
save-as-you-go approach is robust to a mid-batch failure. Resume once the daily/
monthly usage allowance is confirmed available again.

**Two scope decisions, both Pranav's call, both documented in full in `CLAUDE.md` §6**:
1. **OP/PP recurring-question detection is explicitly OUT of this edition's scope**
   (not just "still not built") — deferred to a dedicated post-launch effort once the
   full 34-sitting corpus exists, since the ≥90%-similarity comparison is O(n²) over
   the whole corpus and running it against a partial corpus now would mean redoing it
   later for nothing.
2. **Two new locked-in features, not yet built**: a whole-book **Chapter-wise Sitting
   Summary** (marks-coverage matrix, one column per exam session not per individual
   paper/set, split into 3 pages — MTP/RTP/PYQ — for print width, each with a
   row-summed Total column) near the front matter, and a narrower **per-chapter
   Topic-wise Summary** at the start of each chapter book (formalizing the exact
   pattern Pranav already hand-built for the AS10 pilot in
   `AS10_Question_Reference.html`). Both are pure `questions_index.json` derivations,
   no new tagging needed — build both only after all 34 sittings are in, for the same
   reason as the OP/PP deferral.

---

## 2026-07-27 (cont'd, 4) — Question Bank Book: wired book_stats.json into the actual front matter as a "Book Coverage at a Glance" page

Pranav's ask, after reviewing what `generate_book_stats.py` computes: don't leave it
sitting unused in `book_stats.json` — bake it into the book itself. Also asked to
confirm (not just recall) that color-coding, headers/footers, and student-notes boxes
are genuinely script-generated, not manually patched — verified directly by grepping
`generate_chapter_book.py`/`qb_common.py` before answering (they are: `.mistakes
icai`/`.mistakes synth` per-question, static `.brand-header`/`.brand-footer` plus a
separate print running-header/footer via `position: running()`, and
`.self-notes`/`.notebook-ref`/`.revision-phase` all rendered inline in
`render_qblock()`).

**Implemented:**
- `generate_qb_front_back_matter.py` now reads `output/generated-from-script/
  book_stats.json` (hard error if missing/stale — never silently builds a front matter
  without it) and renders a new "Book Coverage at a Glance" front-matter page: 6 stat
  tiles (sittings covered, distinct questions, question records incl. split parts,
  chapters touched of 36, total marks, real ICAI examiner's comments), the full sittings
  list, and 3 honest caveat notes (why MTP/PYQ sittings sum to 114 not 100, why RTP
  shows 0 marks, how many mistake notes are synthesized vs real). Every number is read
  live at generation time, never hand-typed.
- New CSS (`.qb-stats-grid`/`.qb-stat-tile`/`.qb-stats-sittings`) added to
  `qb_common.front_back_css()` so `qb_merge.py` picks it up automatically for the merged
  book too — one shared definition, not duplicated.
- `generate_book_stats.py` is now a **required** upstream step (Step 3), not an
  optional/informational one — `HOW-TO-BUILD-THE-BOOK.md` updated throughout (step
  descriptions, the "what needs re-running" table, the architecture note, the
  copy-paste command block) to reflect the new Step 3 → Step 4 dependency.

**Ran the full pipeline end-to-end to confirm it actually works**: `generate_book_stats.py`
→ `generate_qb_front_back_matter.py` → `generate_qb_toc.py` → `qb_merge.py` →
`resolve_qb_toc_pages.py --remerge`. Book grew from 307 to **308 pages** (exactly the one
new front-matter page, as expected). Validated: all prior checks still pass (0 blank ToC
pages, 0 build-info/extraction-note leftovers, 0 duplicate student-notes strips), plus new
checks confirming the stats page and its 6 tiles are present in the final merged
`QUESTION-BANK-BOOK.html`.

---

## 2026-07-27 (cont'd, 3) — CLAUDE.md reconciled: fixed stale/contradictory statements, documented the multi-agent reality, added Claude_V2.md to the read order

Pranav's ask: "document all of your skills, understanding into the claude.md file... make
sure even a fresh git repo pull will give all the context to that new AI after reading
claude.md and claude_v2.md... don't repeat things and ensure things are not contradictory."

Read `Claude_V2.md` in full (690 lines) first — confirmed it's entirely Strategy-Book
(Pillar 1) specific, zero overlap with Question Bank content, so nothing there needed
touching. All the actual staleness was in `CLAUDE.md` §6, left behind by today's rapid
pace of work:
- Two "still not built" statements about the whole-book merge script were now flatly
  false (it's built and proven — see the previous entry). Annotated both in place as
  historical rather than deleting them, and added the real current-state entry at the
  end of §6.
- The "unconfirmed origin" note about `QUESTION-BANK-BOOK.html`/`front-matter.html`/
  `back-matter.html`/`vendor/` was stale — their origin (the Codex session) is now
  confirmed and documented.
- §3's `first_run/` folder-table row hadn't been updated since the merge/ToC/stats
  scripts were added — now lists all of them and points to the new
  `HOW-TO-BUILD-THE-BOOK.md`.
- Added an explicit "this repo has multiple concurrent AI sessions" callout to §2
  (working rules) — this has caused real confusion and even a git-history divergence
  requiring a manual merge (see the 2026-07-27 entry further down) — worth stating
  plainly rather than leaving future sessions to piece it together from scattered
  mentions.
- Added `Claude_V2.md` to §1's mandatory read order (conditional on the task touching
  the Strategy Book, same pattern as the existing `content/README.md` conditional entry)
  — it was previously only cited deep in §7, easy to miss on a fresh clone.

Ran `tools/health_check.py` and `tools/file_index.py` afterward — same 16 pre-existing,
unrelated failures as before this session started (stale `EXPECTED_DIRS`, bridge-course
NUL bytes, undocumented `capranav_com/`), nothing new introduced.

---

## 2026-07-27 (cont'd, 2) — Question Bank Book: took full ownership of the whole-book pipeline, audited every file, ran it end-to-end, wrote the master runbook

Pranav's ask: "take full control of the entire book and entire flow," go through every
file the parallel agent had built, fix small bugs directly, only pause on major issues,
and produce one final MD file documenting the whole build end-to-end.

**Audit findings:**
- The student-notes duplication risk flagged in the previous session (my per-question
  fields in `generate_chapter_book.py` vs. `qb_common.py`'s `inject_student_notes()`)
  had **already been found and fixed** by the parallel agent — `page_shell()` no longer
  calls that function, confirmed by grepping the merged book (0 occurrences of the old
  strip's text, all of my new fields present and correct, `build-info`/`Extraction note`
  both at 0). No action needed there, just verified.
- **Real gap found and fixed**: `qb_common.front_back_css()` already defined `.qb-howto`
  and `.qb-legend-*` CSS classes, but no page anywhere in the actual HTML used them — a
  "How to Read This Book" legend page was designed (CSS existed) but never actually
  written into `front-matter.html`. Added the page (condensed from the existing
  `first_run/output/How-to-Read-this-Book.md`), plus 3 more legend swatches
  (`qb-legend-answer`/`qb-legend-case`/`qb-legend-flagged`) alongside the 2 that already
  existed (`qb-legend-examiner`/`qb-legend-author`) so all five colour-coded box types
  get a swatch, not just two.
- **Real bug found and fixed**: `resolve_qb_toc_pages.py` builds a `file://` URL and
  passes it unencoded into an HTTP request to Chrome's DevTools endpoint — a raw space
  in the repo's path (this clone sits under `.../Other computers/...`) makes
  `http.client` reject the request outright. Fixed with `urllib.parse.quote(file_url,
  safe=":/")` before use; safe regardless of whether a given path has a space in it.

**Ran the full pipeline end-to-end** for the first time in one continuous pass:
`generate_all_chapter_books.py` → `generate_book_stats.py` →
`generate_qb_front_back_matter.py` → `generate_qb_toc.py` → `qb_merge.py` →
`resolve_qb_toc_pages.py --remerge` (had to `pip install websocket-client` first, not
previously installed in this environment). Final `QUESTION-BANK-BOOK.html`: **307 pages**,
all 34 ToC page numbers correctly resolved and baked in, validated clean (0 unclosed
tags, 0 duplicate ids, 0 NUL bytes, 0 backticks, 0 placeholders, 0 leftover build-info/
extraction-note text, 0 duplicate student-notes strips).

**New file**: `first_run/HOW-TO-BUILD-THE-BOOK.md` — the master end-to-end runbook
Pranav asked for: architecture diagram, folder map, prerequisites, the exact 7-step
command sequence (extract → chapter books → stats → front/back matter → ToC → merge →
resolve-and-remerge → manual PDF export), a "what needs re-running after X changes"
table, every fixed-incident gotcha in one place, and the still-open items (OP/PP tags,
short chapter names). `SKILL-question-bank-pipeline-overview.md` updated to point to it
and to describe the now-complete merge/ToC/front-back-matter stages instead of
describing them as future work.

---

## 2026-07-27 (cont'd) — Question Bank Book: Dedication added, How-to-Use removed (superseded by How-to-Read-this-Book.md), ToC split into its own file

Pranav's follow-up after reviewing the front matter and the stats script:

1. **Dedication page added.** Reused the Strategy Book's exact dedication (same real people: parents, sister, CA Deepak Pandey, CA Mukul Bhatt, CA Praveen Sharma, CA Gurpreet Singh & Rahul Bhutani) rather than inventing a different one, since Pranav didn't ask for a different dedication when given the choice. New `.qb-dedication-block`/`.qb-ded-*` CSS in `qb_common.front_back_css()`, ported from the Strategy Book's own rules onto this book's CSS variable names.
2. **"How to Use This Book" removed from front matter.** The other session's `How-to-Read-this-Book.md` is more comprehensive and already describes the current (post-redesign) book shape accurately — mine was still describing the old 3-section MCQ/Descriptive/Integrated structure, now stale anyway. Removed rather than kept as a second, competing copy.
3. **Table of Contents split into its own file**, `first_run/output/table-of-contents.html`, generated by a rewritten `generate_qb_toc.py` -- confirmed directly for Pranav: **the ToC is 100% script-derived, not hand-typed.** Every row's chapter order, label, and study-material code comes straight from `qb_merge.py`'s `CHAPTERS` tuple; the only thing not computed at generation time is the page number, which can't be known until the book is actually paginated -- `resolve_qb_toc_pages.py` fills that in afterward from a real headless-Chrome pass. Rewriting this as a fully-owned, always-regenerated-from-scratch file also permanently closes the class of bug from the previous "patch an existing div" approach (the ToC-duplication bug fixed earlier this week) -- there's no longer any existing content for a bad patch to leave behind.
4. Moved `wrap_page()` (the shared standalone-HTML-file shell) into `qb_common.py` so all three front-matter-shaped files (front-matter.html, back-matter.html, table-of-contents.html) share one copy instead of two independently hand-kept ones.
5. **Disabled the merge-time `inject_student_notes()` overlay** in `qb_common.page_shell()` -- the 34 chapter files (redesigned outside this session, see the 2026-07-27 entry above) now have their own richer, built-in self-notes/notebook-ref/tag/revision-phase block per question. Calling both would have printed the exact kind of duplication Pranav asked to avoid elsewhere this same conversation. Function left defined, not deleted, in case a future chapter-book redesign drops its own version again.

Re-merged and verified clean: 305 pages (down from 368, mostly because the redesigned chapter files no longer include MCQs), 0 duplicate ids, dedication renders correctly on its own page, ToC starts immediately after with all 34 real page numbers resolved.

**Still not reconciled (flagged, not fixed this pass)**: the chapter-print CSS overrides (`print_layer_css()`'s `chapter_print_*` font-size rules) don't yet cover the new chapter classes (`.self-notes`, `.brand-header`, `.brand-footer`, `.error-register`), so those render at their original (larger) size; and the redesigned per-question content is tall enough with its own new fields that some pages show the same kind of trailing whitespace the earlier page-break fix addressed for the old shape -- would need the same break-inside review applied to the new elements.

---

## 2026-07-27 — Book stats script built; discovered the 34 chapter files were substantially redesigned outside this session

Two things this session, in order:

**1. Discovered `generate_chapter_book.py` and all 34 chapter files were regenerated/redesigned outside this conversation** (files dated 2026-07-26 ~20:2x-20:3x, after this session's earlier merge work that day). Real, confirmed changes: MCQs are now deliberately excluded from the printed chapter books (they're described as living on "the dedicated MCQ platform" instead -- only Descriptive + Integrated sections remain); the old `id="AS02-NNN"` bug is fixed at the source now (ids are correctly per-chapter, e.g. `M2C5U2-001`); a richer built-in self-notes/notebook-ref/tag-placeholder/revision-phase block was added per question (overlapping with, and now superseding, the simpler one-line strip this session had injected at merge time); a per-chapter brand-header/footer and a back-of-chapter "Sanjeevani Booti 2: Error Register" section were added. **Not yet reconciled with the merge pipeline** (`qb_merge.py`/`qb_common.py` still assume the old shape in places -- e.g. the now-redundant `inject_student_notes()` merge-time overlay, and the chapter_print_* font overrides don't yet cover the new `.self-notes`/`.brand-header`/`.error-register` classes) -- flagged to Pranav directly rather than guessed at; the previously-delivered `QUESTION-BANK-BOOK.html` is stale against this and needs a full re-merge once the reconciliation approach is agreed.

**2. Built `first_run/scripts/generate_book_stats.py`** (Pranav's request: a script-driven book-coverage summary — attempts covered, question counts including parts/sub-parts, total marks). Reads `questions_index.json` (Layer 2) directly rather than the 34 chapter files, deliberately: chapter-book rendering policy (MCQs in/out) can keep changing, but the underlying question corpus is stable, so the stats describe the corpus with the current rendering policy called out as a separate, explicit fact rather than baked into the numbers.

Ran it and checked every surprising number against the raw data before trusting it, rather than reporting them as-is:
- **275 total question records** (already parts/sub-parts-inclusive, since independent splitting happens at extraction) across the 10 known sittings; **165 distinct question numbers as originally printed** (collapsing split sub-parts and OR-alternative pairs back to their real printed number).
- **"Easy" for all 275 rows on the difficulty field** — checked topic_count distribution directly (272 rows touch exactly 1 topic, 3 touch 2), confirmed this is a real consequence of the splitting design, not a computation bug; the difficulty label currently carries near-zero signal.
- **RTP sittings show 0 marks** — confirmed by grepping the raw sitting HTML: RTP files genuinely have zero `data-marks` attributes anywhere (ICAI's RTP documents don't publish a marks-weighted answer key), matching an already-documented, expected behavior from 2026-07-26's log, not new data loss.
- **Each MTP/PYQ sitting sums to 114 marks, not the nominal 100** — traced to Part II's "answer any N of the remaining M" choice structure: the book deliberately includes every optional question shown (Q1-Q6, 84 marks) rather than only the subset (Q1-Q5, 70 marks) one specific sitting required, so a student can practice all of them. Verified consistent (30 + 84 = 114) across all 7 MTP/PYQ sittings, confirming it's structural, not a one-off tagging error.

Every one of those four "this looks wrong" moments turned out to be either already-documented expected behavior or a real, traceable structural fact -- none were left unexplained in the script's own output (each has an inline NOTE in both the console summary and the written `book_stats.json`).

**Not yet done**: wiring these stats into an actual front-matter page (Pranav asked to confirm the script works first, before deciding where in the book's flow to place it) -- `book_stats.json` is written to `first_run/output/generated-from-script/` for now, nothing reads it yet.

---

## 2026-07-26 (cont'd, 8) — Question Bank Book: chapter-book reader-experience overhaul (MCQs removed, Integrated-topic bug fixed, several new student-facing fields)

Pranav sent a 16-point review of the rendered chapter books; asked for feedback/plan first (delivered), then to implement all "straightforward" items and report what's left.

**Implemented in `generate_chapter_book.py`, all 34 books regenerated and re-validated clean (0 unclosed tags/NUL/backticks/placeholders/duplicate IDs):**
- MCQs removed from the book entirely (still in sitting HTML + `questions_index.json`, just not rendered) — sections renumbered to I. Descriptive, II. Integrated.
- Fixed a real bug: `topic_label()` used to show only the current chapter's tag on an Integrated-section row, hiding the question's other tested standard (found via `AS16_Question_Book.html`'s MTP_May2026_Set2 Q8 — showed "AS 16" only despite also testing AS 10). Now shows every tagged topic.
- Topic tags now render in full (`M1_C2_U0 : Framework for Preparation and Presentation of Financial Statements / ICAI Study Mat Topic No : 7/9/11`) instead of the old compressed `Framework (7/9/11)`.
- Examiner's Comment (tan/orange) vs Author's Note (pale pink) now actually colour-differ, matching `book-style.json` — previously both rendered in one flat colour despite the front-matter legend promising a distinction.
- New "Approx Time" field (`ceil(marks × 1.8)` minutes, computed at generation time; RTP with no stated marks shows a "10–20 minutes" range).
- Removed from rendered output (data still in JSON): per-question Extraction Note, file-level Build Info footer.
- New per-question fields: blank Student Self Notes box, My Notebook Ref No, freeform My Tag, Revision Phase 1/2/3 tick-boxes.
- New chapter-end blank page: "Sanjeevani Booti 2: Error Register" (dotted lines, 40% opacity, two sections).
- New static header/footer branding (Pranav Bhaiya / Newton of Accounts / AIR 1-1-5 / Kahaan-Koncept-Karma) on each standalone chapter file — **not** the same as a print running-header-on-every-physical-page, which belongs to the other agent's merge/pagination scripts (`qb_merge.py`/`qb_common.py`) and isn't wired up there yet.
- Title simplified to `{Standard} — {Chapter}`, no "Question Book" suffix.
- New `first_run/output/How-to-Read-this-Book.md` — student-facing guide to every colour/field and why it exists; each chapter book's "how this is organised" note now points here.

**Explicitly parked (need more design or Pranav's input, not built this pass):** OP/PP recurring-question tags (duplicate-detection design exists, never built) and a short-chapter-name field for the topic-index taxonomy (needs Pranav to help draft ~36 short names). Both named honestly as "coming in a future edition" in the new guide.

**Flag for the parallel agent running the whole-book merge**: this pass changed the DOM/CSS inside each chapter book — removed `.extraction-note` and `.build-info` divs, added `.self-notes`/`.notebook-ref`/`.tag-placeholder`/`.revision-phase`/`.error-register` (the last has `page-break-before:always`), changed `.mistakes` to need an `.icai`/`.synth` subclass for colour. If `qb_merge.py`/`qb_common.py` has any CSS or structural assumptions keyed to the old markup (e.g. selectors targeting `.extraction-note`/`.build-info`, or page-count math from the earlier print-cost pass), it should be re-checked against the regenerated files before the next merged-book build.

---

## 2026-07-26 (cont'd, 7) — Question Bank Book: ToC-duplication bug fixed, study-material cross-reference added, page-break waste cut, student-notes strip added

Pranav's review of the merged book (388 pages, from the print-cost pass) surfaced four things in one message. All four addressed:

1. **Real bug: Table of Contents was duplicating on re-runs.** Root cause: `generate_qb_toc.py`'s patch regex used a non-greedy `(.*?)(</div>)` to find the ToC list div's closing tag -- correct only while that div was still empty. Once it held 34 nested `<div class="qb-toc-entry">` rows, the lazy match stopped at row 1's own `</div>` instead of the list's real closing tag, so every re-run replaced only row 1 and left the old rows sitting there, growing by ~33 stale rows each time (confirmed: 67 entries in the file Pranav flagged, exactly 34 fresh + 33 leftover). Fixed with balanced-`<div>`-tag counting instead of regex (`_find_matching_close()`), verified idempotent by running it 3 times in a row and confirming the count stays at 34.

2. **Chapter <-> study-material cross-reference, added.** Each of the 34 `CHAPTERS` entries in `qb_merge.py` now carries a 4th field, `study_material_ref` (e.g. `"M2-C5-U1"`), sourced from `1-ca-inter-adv-accounts-topic-page-index.json`'s `unique_chapter_id` -- deliberately NOT `metadata-index/topic-index.json` (which already correctly drives each *question's* own subtopic tag like "AS 2 (1.4)", untouched) since that file only covers 32/36 chapters and documents itself as secondary to file 1 for chapter-level IDs. Shows as a small chip next to every ToC entry and as a one-line "Study Material Reference: M2-C5-U1" banner at the top of each chapter.

3. **Page-break waste, measured and fixed.** Pranav's instinct that "each question starting from a new page" was wasteful was checked against real data, not assumed: 312 of 334 content pages (93%) held exactly 1 qblock, averaging 282px of ~960px (29%) unused per page. Cause: `break-inside: avoid` was set on the whole `.qblock` container, so any question too tall for the remaining space on a page jumped ENTIRELY to the next page rather than just the part that didn't fit. Fixed by moving `break-inside: avoid` down to the smaller indivisible pieces inside a qblock (`.question`, `.answer-block`, `.mistakes`, `.extraction-note`, `table`, `.note`, `.case-facts`, `.empty-section` -- confirmed these are real sibling `<div>`s, not guessed) and removing it from `.qblock` itself, so a page break can now fall between a question's own Question/Answer/Notes sections instead of only between different questions. Cut 388 -> 361 pages on its own.

4. **Student self-notes + notebook-page-reference strip, added to every question.** A compact one-line strip ("Your Notes: ______ Practiced in Notebook — Page No.: ____") injected after each qblock's content via `qb_common.inject_student_notes()`, using the same balanced-div-counting technique as the ToC fix (a qblock's real closing tag is not the first `</div>` inside it either). Applied only at merge time -- the 34 source chapter files (screen-review copies) are untouched, this only exists in the print-ready merged book, which is the only place a student would actually write in it. Kept deliberately compact (single line, not a ruled box) given the same-day cost-cutting effort: added only ~7 pages across all 278 questions.

**Net page count after all four fixes: 368** (was 388 before this round; 707 before the whole print-cost pass started). Re-verified structurally clean each time (0 duplicate ids, 0 NUL, 0 backticks, single `<style>`/script) and visually via headless-Chrome screenshots of the ToC and an AS 2 chapter page.

**Not yet done, flagged for a decision, not executed:** nothing outstanding from this round -- all four of Pranav's points were addressed. Still open from earlier: whether to extend the em-dash humanization pass to the 34 chapter files' own content (their own `<h1>`s still have em-dashes), and OP/PP duplicate detection.

---

## 2026-07-26 (cont'd, 6) — Question Bank Book: print-cost reduction (margins + font size), 707 → 388 pages

Pranav asked to shrink margins to "nearly zero" and reduce font size, explicitly for printing cost (page count is the direct cost driver). Both changes went into `first_run/schema/book-style.json` (the single source of truth) and are consumed additively by `qb_common.py`'s `print_layer_css()` — the 34 chapter files' own embedded style is still never touched, this is a merge-time-only override layered on top, same discipline as everything else in this pipeline.

- **Margins**: `page_geometry_for_future_print_stage` cut from 20mm to 6mm on every side — near the practical floor for a home/office printer (many can't guarantee edge printing below ~4-5mm without clipping; true 0mm was avoided for that reason, flagged in a code comment so it's an easy one-line change if Pranav confirms his actual print method can go tighter).
- **Font size**: new `chapter_print_*` fields added to `book-style.json` (body 9pt, h1 15pt, h2 12pt, table 7.5pt, small text 7pt) plus tightened `.qblock` margin/padding — applied only inside `.qb-book-content` (higher specificity than the chapter files' own bare-tag rules, no `!important` needed).
- **Result**: 707 → **388 pages** (~45% cut). Re-verified structurally clean (0 duplicate ids — a first check falsely flagged 34 "duplicates" that turned out to be a regex matching `data-target-id="..."` as if it were `id="..."`, not real; a boundary-safe regex confirmed the true count is 0) and visually via headless-Chrome screenshots (title page and an AS 2 chapter page both still legible at the smaller size).

**Also discovered and adapted to, mid-task, not caused by this session's own work**: sometime between this morning's working merge and this afternoon, the 34 chapter files were moved from `first_run/output/` directly into a new `first_run/output/generated-from-script/` subfolder and regenerated fresh (confirmed by mtimes — content shape/style unchanged, same known `id="AS02-NNN"` bug still present), and the 10 sitting-level files similarly moved into `first_run/output/parsed-from-pdf/`. `qb_merge.py`'s file-existence check caught this immediately (all 34 chapters suddenly "missing") rather than silently merging stale content. Fixed `qb_common.load_chapter_html()` and `qb_merge.py`'s validation to check both the old flat location and the new subfolder, so the pipeline keeps working regardless of which layout is current — worth telling Pranav this reorganization happened, since it wasn't this session's doing and it's unclear if it was intentional or another concurrent process.

**Output** (unchanged path): `first_run/output/QUESTION-BANK-BOOK.html` — 388 pages, same Chrome → Save as PDF workflow.

---

## 2026-07-26 (cont'd, 5) — Question Bank Book: front/back matter, whole-book merge, ToC with real page numbers — full pipeline working end-to-end

Pranav assigned a new deliverable on top of the 34 already-generated chapter files ("the main content is done"): front/back matter, a chapter merge order, and one final single HTML mergeable into a print-ready PDF via Chrome — same "Save as PDF" workflow already proven on the Strategy Book.

**Built, all in `first_run/scripts/`:**
- `qb_common.py` — shared helpers: fixes the real `id="AS02-NNN"` bug (every chapter file hardcodes this id prefix regardless of its actual chapter — confirmed directly, fixed at merge time via slug-prefix rewriting, chapter source files never touched); the print/pagination CSS layer (page geometry literally templated from `book-style.json`, since `@page` doesn't resolve `var()`); front/back-matter-only CSS (title page, copyright page, ToC, author bio).
- `generate_qb_front_back_matter.py` — writes `front-matter.html` (title page, copyright & disclaimers, How to Use This Book, ToC placeholder) and `back-matter.html` (About the Author, closing note) as standalone reviewable files.
- `qb_merge.py` — the whole-book assembler. `CHAPTERS` tuple = 34 chapters in teaching sequence (cross-referenced against `1-ca-inter-adv-accounts-topic-page-index.json`'s `teaching_sequence`; confirmed the 34-vs-36 gap is two deliberate syllabus-pair collapses, not missing content — Financial Statements' two units share one file, and pre-Ind-AS "AS 14" **is** "Amalgamation of Companies" so that pairing shares one file too, confirmed straight from that file's own `<title>`).
- `generate_qb_toc.py` + `resolve_qb_toc_pages.py` — same two-pass pattern as the Strategy Book's ToC (`target-counter()` is confirmed broken in this vendored paged.js; real page numbers come from polling `data-page-number` via a headless-Chrome CDP pass after a first blank-ToC merge, then re-merging).

**Two real bugs found and fixed, both invisible without headless-Chrome verification (reading the code/output alone would have missed both):**
1. Pagination silently never started (0 `.pagedjs_page` elements, no console dialog, no crash) — root cause was `<link rel="stylesheet" href="vendor/gfonts-local.css">` in the merged file's `<head>`: paged.js internally re-fetches every linked stylesheet via XHR to analyze it, and Chrome blocks that XHR under `file://` origin (CORS: "Access to XMLHttpRequest ... blocked by CORS policy"), throwing an uncaught promise rejection that halted initialization before any page ever rendered. Fixed by inlining the font CSS text directly into the merged `<style>` block instead of linking it (with its `url(fonts/...)` paths rewritten to `url(vendor/fonts/...)`, since inlined relative URLs resolve against the *document's* location, not the original CSS file's).
2. The title page's author-name/credential line was rendering on a *different, much later physical page* than the rest of the title page — traced via `getBoundingClientRect()` (not visible from a DOM-only check) to `.qb-title-page`'s `min-height: 220mm` exceeding the actual per-page content-box height (`254mm - 20mm - 20mm = 214mm`, from `book-style.json`): a `display:flex; justify-content:space-between` container that overflows a page boundary doesn't fragment predictably, so its children scattered across pages instead of visibly overflowing where the bug would have been obvious. Fixed: `min-height: 190mm` (safely under the 214mm ceiling) plus `break-inside: avoid` as a second line of defence.

**Verified clean after both fixes** (headless Chrome, real-time `.pagedjs_page`-count polling until stable — no `--dump-dom`/timed-capture shortcuts, per the Strategy Book's established discipline): **707 pages**, 0 duplicate `id` attributes (319 total, verified with a boundary-safe regex after an initial loose regex falsely flagged 34 — those were `data-target-id="..."` substring matches, not real duplicates), exactly one `<style>` block and one `paged.polyfill.js` reference, 0 NUL bytes, 0 backticks, 0 leftover placeholder markers, all 34 ToC entries resolved to real ascending page numbers (7 through 674). Screenshotted the title page, ToC, and an AS 2 chapter-opening page directly (not just DOM-checked) to confirm the visual fix.

**Flagged, not changed:** the 34 chapter files' own content (headings, question text) still contains em-dashes in places — e.g. `AS02_Question_Book.html`'s own `<h1>` reads "AS 2 — Valuation of Inventories: Question Book." Left untouched deliberately, since Pranav said this content is done and out of scope for this task; new content this session (book title, chapter labels in the running header/ToC, all front/back-matter prose) was written without em-dashes from the start, matching the Strategy Book's cleanup discipline. Worth a decision from Pranav on whether the same humanization pass should eventually extend to the 34 chapter files.

**Output:** `first_run/output/QUESTION-BANK-BOOK.html` — open in Chrome, wait for pagination to finish (a 707-page document takes noticeably longer to settle than any single chapter), then Ctrl+P → Save as PDF with Background graphics enabled.

---

## 2026-07-26 (cont'd, 4) — Phase 2 complete: 5 more sittings built, full 34-chapter Question Bank Book generated

Built the 5 sittings Pranav named (completing the Jan 2026 exam cycle + starting Sep 2025): `MTP_Jan2026_Set1.html`, `MTP_Jan2026_Set2.html`, `RTP_Jan2026.html`, `PYQ_Sep2025.html`, `RTP_Sep2025.html` — all read from raw source PDFs, tagged, split, and validated against the same schema as the original 5, at the Phase 2 relaxed accuracy bar (§0 of the Phase 1 skill: correct transcription and topic tagging, MCQ letters verified against source, but not the exhaustive re-derivation depth Phase 1's audit applied). PYQ_Sep2025 has a real ICAI Examiner's Comments document — folded in 13 verbatim real comments (labelled "Examiner's Comment") alongside synthesized ones (labelled "Author's Note"), the first sitting since PYQ_Jan2026 to exercise that distinction.

**Two accuracy-relevant things surfaced and fixed along the way:**
- Resolved a genuinely unresolved flag from Phase 1: `MTP_Jan2026_Set1.html` Q15's lease-rent MCQ (dealer/operating lease, 20% margin on cost) had been left flagged `unverified-arithmetic` because the simple pro-rata computation didn't reproduce the answer key. Building `RTP_Jan2026.html` turned up the *identical* question with one extra detail in its narrative ("3-year **operating** lease") that the MTP version's shorter restatement omitted — this revealed the actual mechanism (recover cost+margin in proportion to output consumed during the lease, out of the machine's full economic-life output, not a flat 3-year spread). Went back and fixed the MTP file's explanation with the same resolved logic.
- Found and fixed a real `unitCode` inconsistency: Branch Accounting was tagged `M3-C15-U0` in some files and `M3-C15-U1` in others; Framework similarly `M1-C2-U0` vs `M1-C2-U1`. Per CLAUDE.md's locked U0/U1 migration, both are single-unit chapters that must always use U0 — left un-caught, this would have silently split each into two separate "chapters" at book-generation time. Fixed across all affected files before generating books.

**Also caught mid-build:** `extract_questions.py`'s file-discovery briefly re-ingested a previously generated chapter book as if it were an 11th sitting (same bug pattern as before, from a stray filename not matching the `_Question_Book.html` exclusion at the time it was written) — already covered by the existing exclusion filter from the last fix, no recurrence.

**Built `first_run/scripts/generate_all_chapter_books.py`** — a batch driver that reads every unique `final_chapter` out of `questions_index.json` and calls the existing `generate_chapter_book.build_book()` for each, with a naming scheme matching the AS10 reference sample's style (`AS02_Question_Book.html`, `AS16_Question_Book.html`, ... `CashFlowStatement_Question_Book.html`, `Buyback_Question_Book.html`, etc. for the non-AS-numbered chapters).

**Result:** 275 rows extracted across all 10 sittings (30 Part I marks + 88 raw/84 deduped Part II marks per marked paper, consistently — RTPs correctly show 0/0/0 since they print no marks). **34 chapters touched — essentially the entire 36-chapter syllabus** (only 2 chapters, AS 1 and AS 27, remain thin at 2 questions each; genuinely zero-coverage chapters from the original per-question audit are now gone). All 34 generated chapter books validated structurally clean (0 unclosed tags, 0 NUL, 0 backticks, 0 duplicate IDs). Two chapters (AS 10, AS 16) now have real, non-empty Section III "Integrated" content for the first time in this pilot, from genuinely connected multi-topic questions found across the 10 sittings.

**Not done in this phase** (per Pranav's explicit "keep parked" instruction from earlier): the whole-book merge/"sewing" script, OP/PP duplicate-detection implementation, and any of the parked UX items (answer-hide toggle, mobile/print CSS, filter bar, etc.). Several likely-recurring (OP/PP) questions were spotted and noted in extraction-notes during this build (the P/Q/R Ltd. AS 18 scenario across 3 sittings; the Anshul manufacturers AS 2 scenario across 2; the Alfa/Jay Ltd. reconstruction scenario within the same MTP series; the Mansi Ltd./Akash Ltd. AS 19 sale-leaseback across 2 RTPs) but not formally merged, since duplicate detection remains a separate, not-yet-built workstream.

---

## 2026-07-26 (cont'd, 3) — Phase 1 closed out; accuracy bar relaxed for descriptives; moving to Phase 2 (scale to more sittings)

After the MCQ audit found 6 real errors, Pranav deliberately relaxed the remaining bar rather than asking for the same depth on all 69 descriptive rows: "we need not be 100% accurate... first edition... just skim through and let's close this." Ran a fast automated red-flag skim (hedge phrases, placeholder text, suspiciously short answers) across all 69 descriptive rows — zero automated flags, one manual catch during spot-reading: `MTP_May2026_Set1.html`'s Q6(a) alt-2 (amalgamation purchase consideration) had literal leftover placeholder text ("see working note...", a stray "...") sitting inside a real answer table, previously flagged `needs-visual-check`/`ocr-garbled`. Recomputed the missing share-count derivation from the given exchange ratios, confirmed it reconciles exactly to the already-stated rupee totals, and marked the row `verified`.

**Also implemented, per Pranav's instructions**: renamed the rendered Mistakes box from generic wording to **"Examiner's Comment"** (real ICAI sittings) vs. **"Author's Note"** (synthesized, with an explicit "may not apply in every case" caveat) — a display-layer change in `generate_chapter_book.py`, not a change to the underlying `data-comment-source` enum. Added a reader-facing disclaimer (top and bottom of every chapter book) acknowledging first-edition status and inviting error reports by email — **placeholder email address in the script (`ERROR_REPORT_EMAIL`), needs Pranav's real address before any real distribution**. Rewrote the book's front-matter to be student-facing (moved script/JSON/folder-path references into a small "Build info" footer, per the already-accepted Phase 1 §4 item). Documented the bar relaxation in `SKILL-question-bank-phase1-definition-of-done.md` §0 (new) so it isn't lost/re-litigated on the next sitting.

`AS02_Question_Book.html` regenerated against the new template and re-validated clean.

**Next**: Pranav asked to move to "Phase 2" — build 5 more sitting HTML files through the full pipeline (source PDF → tagged sitting HTML → extraction → chapter books) and produce the complete chapter-wise Question Bank across all resulting chapters, not just AS 2. This is a substantially larger undertaking than anything done so far (roughly re-doing the full sitting-authoring effort 5 more times, then generating N chapter books instead of 1) — scope/sitting-selection to be confirmed before starting.

---

## 2026-07-26 (cont'd, 2) — Full MCQ accuracy audit (Phase 1 §1) completed for all 5 pilot sittings

Executed the accuracy-audit gate from `SKILL-question-bank-phase1-definition-of-done.md` §1 against all 67 MCQ rows across the 5 sitting files (the other 69 descriptive rows are not yet done — see below). Independently re-derived the arithmetic for every MCQ carrying a Claude-authored explanation (50 of 67; the other 17 are genuinely bare-letter with no explanation, matching source, no risk). Consulted `books/concept-book/raw_icai_study_materials/` (Pranav's explicit authorization) to resolve conceptual doubts against three different standards' actual rule text (AS 18 related-party aggregation through a controlled subsidiary; AS 23 equity-method dividend treatment; AS 25 interim-period cost/gain/estimate-change treatment, cross-checked against a near-identical worked illustration in the AS 25 study material itself).

**Found and fixed, beyond the original 2 (AS02-005/006):**
- `MTP_May2026_Set2.html` Q7 (AS 16 borrowing-cost suspension): the case narrative's stated "3 months" standstill doesn't reconcile to the official answer letter — only a 4-month reading does. Flagged as a source-wording ambiguity (`data-issue="source-inconsistency"`) rather than silently picking one reading, per the verbatim-extraction skill's "flag, don't fix" doctrine.
- `MTP_May2026_Set2.html` Q15 (AS 18 related party): final letter was already right, but the stated method (diluting an indirect holding through a subsidiary as 60%×20%=12%) is not how AS 18 aggregates control-based holdings — verified against the AS 18 study material and corrected to the proper full (non-diluted) aggregation.
- `PYQ_Jan2026.html` Q7 (AS 23 equity method): explanation was self-contradictory (called the same dividend "pre-acquisition" then "post-acquisition" in one sentence) and never showed real numbers; the attached Mistakes note claimed the dividend "should be added, not deducted" — backward. Rewrote with the full verified calculation (₹26,00,000).
- `PYQ_Jan2026.html` Q12 (cash flow): the written formula literally computed to ₹20,30,000 while claiming to justify ₹23,00,000, hedged with "= per source figure" — a real tell that the reconciliation was never actually completed. Re-derived properly (interest reclassified to financing, added back before removing) and cross-checked against Q13/Q14's dependent figures.
- `PYQ_May2026.html` Q10 (AS 25 interim reporting): previously bare answer-letter only, no explanation at all, on a question where three plausible sign conventions are easy to get wrong (confirmed by getting it wrong myself twice before checking source) — added a fully verified explanation after cross-referencing the AS 25 study material's own near-identical worked illustration.
- `RTP_May2026.html` Q2 (AS 19 lease PV computation): could **not** be independently re-derived — the discount/implicit rate needed for the calculation is not present anywhere in the extracted source text. Flagged honestly (`data-issue="unverified-arithmetic"`) rather than assumed correct just because the letter matches the source answer key.

**Confirmed correct (no change needed) after independent re-derivation:** the remaining ~44 authored MCQ explanations, including several cross-checked against the AS 18/AS 23/Amalgamation study materials for genuinely tricky theory points (G Limited associate-via-board-representation despite only 12% holding; External Reconstruction vs. Absorption vs. Amalgamation terminology; Amalgamation Adjustment Reserve = statutory reserves only).

Also caught and fixed 2 stray literal backticks introduced by this session's own edits (violates the repo's no-backtick/UTF-8 discipline) — from markdown-style code spans in extraction-note prose, switched to `<code>` tags.

**Not yet done, and substantially larger in scope per row:** the 69 descriptive-answer rows (full worked solutions — journals, balance sheets, ledger accounts) have not been arithmetic-audited yet. Flagged to Pranav as the next chunk of Phase 1 §1; pacing/priority to be confirmed before continuing.

---

## 2026-07-26 (cont'd) — Phase 1 scope finalized and locked

After the accuracy incident below, Pranav cut off further open-ended review discussion and finalized scope: "whatever is parked for later, keep it parked... I just want that this book HTML should have accuracy at all cost... genuinely high value [improvements] are only to be considered." Wrote the locked checklist to `_claude/skills/SKILL-question-bank-phase1-definition-of-done.md` — the reusable Definition of Done for scaling past the AS 2 pilot to the remaining ~35 chapters and ~12+ sittings. Locked scope:

1. **Accuracy audit (top priority, gate before anything else)** — re-derive every AI-authored explanation's arithmetic across all 5 sittings against source figures; consult `books/concept-book/raw_icai_study_materials/` (per-unit ICAI study material MD, Pranav explicitly authorized this as the reference to resolve conceptual doubt) whenever the correct rule itself, not just the arithmetic, is uncertain.
2. **Cross-chapter cluster classification, finalized design** — one home chapter per case-scenario cluster/connected question (latest-taught touched standard), shown there under a new "(b) Integrated with Other Standards" sub-heading; every other touched chapter gets a cross-reference pointer only, never duplicated full content. This one rule resolves the earlier-logged case-scenario-duplication issue, the cross-chapter-cluster-homing issue, and the Single-AS/Integrated sub-bucket issue together. Design locked; `extract_questions.py`/`generate_chapter_book.py` implementation not yet built.
3. **Theory/practical** — folded into the accuracy-audit pass (already tagged at Layer 1, just needs a sanity check + surfacing), not a separate workstream.
4. **Two external-review suggestions accepted as genuinely high value**: strip build/engineering plumbing from student-facing text; fix the Mistakes-box voice so MTP/RTP synthesized comments don't falsely claim "many examinees" behavior on papers that never had real candidates (reframed as a correctness fix, not a tone preference). Bonus near-free item: render the topic tag's existing `data-subtopictitle`.
5. **Everything else explicitly parked**: answer-hide toggle, concept recap, revision scaffolding, mobile/print CSS, filter bar, OP/PP badge, Q11/Q12 cross-pointer.

Execution order locked: full accuracy audit first, then the combined cluster/sub-bucket/theory-practical/voice-fix regeneration, then re-validate AS 2 as the Phase 1 proof before scaling.

---

## 2026-07-26 — Real accuracy incident: two backward AS 2 explanations found via external AI review of AS02_Question_Book.html

Pranav ran the AS02 book past another AI for review and relayed its findings rather than accepting them at face value: "Dont accept everyting blindly... evaluate all against our Main goal... main is to make life of student easier and to ensure 100% accuracy at all cost." Independently re-verified every claim from source before acting.

**Confirmed, fixed:** `PYQ_Jan2026.html` Q4 and `PYQ_May2026.html` Q6 (both AS 2 MCQs) had explanations where the arithmetic actually computed to the *distractor* option, not the letter the qblock claimed — and the attached synthesized "Common Student Mistakes" note branded the *correct* method as the student error, exactly backward. Traced root cause by reading the actual source PDFs: both ICAI "Suggested Answers" documents give only a bare letter (`4. (B)`, `6. (B)`) with zero working — meaning the explanations were never transcribed, they were authored by Claude while building these files directly (2026-07-24 session), and the `extraction-note` on both falsely claimed "Verbatim... Confidence: high" for reasoning that was never in the source. Fixed both explanations with correct AS 2 reasoning (fixed-overhead absorption at the *actual* production rate when actual exceeds normal capacity; raw-material write-down to replacement cost when the finished goods it feeds are expected to sell below cost), corrected the mistakes-notes, and rewrote the extraction-notes to honestly distinguish source-verbatim (letter/options) from Claude-authored (explanation).

**Also fixed for consistency, not correctness:** the 4 sibling AS 2 MCQs in `MTP_May2026_Set2.html` (Q10–13) had the same "verbatim... high confidence" mislabeling on Claude-authored explanations, even though re-deriving their arithmetic independently confirmed all 4 were already correct. Relabeled honestly rather than left as-is, since the metadata claim was still false regardless of whether the content happened to be right.

**Bug also caught mid-fix:** `extract_questions.py`'s file-discovery (`os.listdir(OUTPUT_DIR) if f.endswith(".html")`) was sweeping up generated chapter-book outputs (`AS02_Question_Book.html`) as if they were a 6th sitting, double-counting those 7 rows (136 → 143). Fixed by excluding `*_Question_Book.html` from the glob — will matter more once more chapter books accumulate in the same folder.

**Flagged as a systemic risk, not fully resolved:** found on 2 of ~13 AS 2 MCQs checked so far — since ICAI MCQ answer keys are routinely bare-letter-only, most authored explanations across all 5 sittings carry the same unverified-arithmetic risk. Recommended a full audit pass (re-derive every MCQ explanation's arithmetic against its own source figures) before scaling past the pilot; not yet scheduled. New skill section added: `SKILL-question-bank-verbatim-extraction.md` §6, plus a new `data-issue="answer-key-letter-only"` vocabulary value in the html-schema skill.

**Evaluated, not blindly accepted, the same reviewer's 12 UX/structure suggestions** (case-scenario dedup — already tracked as our own issue 1; subtopic-title surfacing — cheap, data already exists via `data-subtopictitle`; engineering-plumbing-in-student-view removal; mobile CSS; print CSS tied to CLAUDE.md §7's existing page-break architecture; MTP/RTP "examinees" voice being factually wrong since those papers never had real candidates; etc.) — see chat for the full per-item verdict, not duplicated here since most are pending design decisions, not facts to persist.

---

## 2026-07-25 — Pipeline proven end-to-end: extraction script + first real chapter book (AS 2)

Pranav asked to prove the whole pipeline actually works: "For all the extracted HTML File, I want you to complete the entire pending actions... I want to see from you being able to give me a 'Proper well formatted HTML file for the AS02 Chapter'." Built and ran both remaining scripts against the 5 real pilot sitting files (no synthetic test data).

**`first_run/scripts/extract_questions.py`** (Layer 1 → Layer 2, BeautifulSoup, mechanical only — no AI re-judgment): walks every sitting HTML in `first_run/output/`, emits one row per qblock into `first_run/output/questions_index.json`. Ran clean: **136 rows from 5 files** (MTP Set1: 28, MTP Set2: 27, PYQ Jan2026: 27, PYQ May2026: 28, RTP: 26). Built-in marks sanity check (Part I total 30, Part II raw vs alt-group-deduped total 84, across the 4 files that carry marks; RTP correctly shows 0/0/0 since it prints none).

**Caught before extraction, via a pre-flight `grep -o 'data-part="[^"]*"' | sort -u` across all 5 files**: `MTP_May2026_Set1.html` (the oldest file, built before the `"I"`/`"II"` data-part convention was settled) still had free-text values (`"Part I - Case Scenario I"`, `"Part I - MCQs"`, `"Part II"`). Fixed with a targeted regex pass (18 lines), re-validated 0 errors. This is exactly the cross-session schema drift the extraction script's Part-I/Part-II bucketing logic depends on being clean — worth re-running that same grep sanity check before extracting after any future file is added or edited.

**`first_run/scripts/generate_chapter_book.py`** (Layer 2 → Layer 3, plain Python/f-strings, no AI): takes a unitcode + labels, queries `questions_index.json`, partitions into Section I (MCQ/case-mcq), II (descriptive, single-topic = the norm post-splitting), III (integrated — `topic_count > 1` and the target unit is a secondary tag), renders inline-CSS HTML matching the `AS10_Question_Book.html` quality bar (qmeta line, case-facts embedded inline, answer block, Common-Student-Mistakes box **with an explicit real-ICAI-vs-synthesized provenance line per entry** — a discipline the AS10 hand-built sample predates and doesn't have, added here since our schema already tracks it losslessly in `examiner_comment.comment_source`).

Ran it for AS 2 (Valuation of Inventories, `M2-C5-U1`) → `first_run/output/AS02_Question_Book.html`: **6 MCQs + 1 descriptive + 0 integrated = 7 questions**, matching the record set already hand-confirmed by ad-hoc query. Validated: 0 unclosed tags (the 2 "errors" HTMLParser reported were a validator artifact from self-closing `<br/>` synthetic end-tag events, not real defects — confirmed by grep, no `</br>` exists anywhere), 0 NUL bytes, 0 backticks, correct `&#8377;` rupee entities, 0 placeholder phrases, 0 duplicate IDs. Read the full rendered output — case scenarios correctly embedded per-MCQ (the exact bug Pranav flagged earlier in this project as the "major issue" with the original external-AI output), verbatim accounting tables intact, synthesized-mistakes provenance correctly labelled throughout (no real ICAI comment exists for any of these 7 — all synthesized per `examiner-comments-writing-skill.md`).

**Honest finding surfaced by the run itself, documented in the book's own scope note**: Section III (Integrated) is genuinely empty for AS 2 across this 5-file pilot — 0 records exist where AS2 is a secondary tag on a connected multi-topic question. This is the expected shape of the independent-vs-connected splitting design (most multi-topic-looking questions get split into single-topic records at extraction time), not a pipeline gap — but it means the AS10 hand-built sample's 3-section structure won't always have content in all 3 sections for every chapter, which future chapter-book runs should expect and state plainly rather than treat as a bug to chase.

Also deleted `first_run/output/TODO.md` — confirmed stale (pre-build planning notes for RTP referencing an abandoned `M1-C4-U2`/`M3-C11-U2` unit-code confusion that was resolved differently in the final schema).

**Next**: this is the first chapter book against real data — scale the same `generate_chapter_book.py` call to the remaining 35 chapters once enough sittings are tagged (still only 5 of ~17+ sittings exist at all); OP/PP duplicate detection and a whole-book merge script are still designed-not-built.

---

## 2026-07-24 (cont'd, 3) — Remaining 3 pilot sittings built directly (MTP Set 2, PYQ May2026, PYQ Jan2026)

Pranav decided not to hand the revised prompts to the external AI for the remaining 3 sittings ("I dont know they will again create a mess") and asked Claude to build them directly instead, against the schema/skills already established from the MTP Set 1 and RTP rebuilds — "minimum token possible... best possible output." All 3 built end-to-end: source PDFs extracted via pypdf, read in full, classified question-by-question (independent-split vs connected vs OR-alternative), tagged against `topic-index.json` with `data-final-chapter`, and validated with the same Python script used for the first two files.

**MTP May 2026 Set 2** (13+14-page Q/Ans PDFs) — 27 qblocks + 3 case scenarios. One judgment call worth recording: Q6(a) bundles two Framework sub-questions ((i) qualitative characteristics, (ii) capital maintenance calc) under one 4-mark heading with no individual mark split shown in the source — kept as one record rather than inventing a split, since both map to the same syllabus unit anyway.

**PYQ May 2026** (44-page Ans PDF, both Q&A embedded per the PYQ sourcing decision) — 28 qblocks + 3 case scenarios. One genuine ambiguity flagged rather than guessed: Q5(a)'s mark value is not printed in the extracted source text (only Q5(b)'s "10 Marks" is) — inferred as 4 (14 total pattern minus 10) and marked `data-issue="marks-mismatch"` rather than stated as confirmed fact.

**PYQ Jan 2026** (45-page Ans PDF) — the pilot's one sitting with a real ICAI Examiner's Comments document (`Paper1-ExaminerComments-Jan2026.md`). Matched all 6 real comments to their corresponding Part II sub-questions (Q1a/b/c, Q2, Q3a/b, Q4, Q5, Q6a-alt1, Q6b, Q6c — 11 of 12 Part II records), leaving only Q6(a)'s AS 19 lease alternative synthesized since the real comment for Q6(a) discusses only the AS 24 disclosure alternative content, not the lease computation — confirmed by actually reading what the comment describes rather than assuming one comment covers both OR-branches.

**Caught and fixed a self-introduced schema bug during this build**: all 11 real-comment blocks in the Jan 2026 file were first written with the citation string stuffed into `data-comment-source` (e.g. `data-comment-source="ICAI Examiner's Comment — Jan 2026, paraphrased"`) and the `synthesized` CSS class left on by copy-paste, instead of the clean enum `data-comment-source="icai"` plus the citation in `data-source`, per the schema. Caught by grepping the output for the enum values immediately after the validation pass reported "0 errors" (structural validation doesn't check semantic correctness of attribute values) — a reminder that automated validation catches malformed HTML, not wrong values in well-formed attributes. Fixed with a targeted regex pass; re-validated: 11 `icai` + 16 `synthesized` = 27, matching the 27 qblocks exactly.

All three files validated identically to the first two: 0 unclosed tags, 0 backticks, 0 placeholder phrases, all IDs unique, all case-scenario references resolve, marks arithmetic consistent (Part I 30, Part II 84 after alt-group dedup across all three files).

**All 5 pilot sittings are now built and validated against the current schema**: MTP Set 1, MTP Set 2, RTP May2026, PYQ May2026, PYQ Jan2026. Next: the HTML→JSON extraction script, duplicate-detection (OP/PP) implementation, and difficulty-computation step, per the six `SKILL-question-bank-*.md` skills — none of these are built yet, only designed.

---

## 2026-07-24 (cont'd, 2) — RTP May 2026 rebuilt against the revised schema

Extended the same-day schema revision (previous entry below) to the second pilot file.
`first_run/output/RTP_May2026.html` had been generated under the *old* schema and, on
inspection, was far worse than the MTP file had been: nearly every Part II answer (16 of
20 questions) was placeholder/meta-descriptive text ("see source", "as printed in source",
"full data in source") with **zero real content**, zero topic tagging throughout, and the
document metadata claimed `"Total Marks: NA"` while individual questions carried invented
marks values (4, 6, 8, 14, etc.) that do not exist anywhere in the source PDF — the RTP
genuinely prints no marks per question at all, so those numbers were fabricated by the
earlier AI, not merely omitted.

Extracted the full 48-page source PDF and rebuilt the file end-to-end: real Case Scenario
node (the AS 16 borrowing-cost scenario behind Q1's four MCQ sub-parts), verbatim content
for every one of the 20 original questions, correct MCQ answers cross-checked against the
source answer key (**and one genuine error caught and fixed**: Q4's answer was recorded as
"(a)" in the old file; the source's own suggested-answer section plainly states "4. (b)"),
topic tags against `topic-index.json` for all 26 resulting records, and `data-marks`
omitted throughout rather than invented (documented in the Part II section header so this
isn't mistaken for an oversight). Applied the independent/connected sub-part rule from the
new question-splitting skill: Q9 (three unrelated post-balance-sheet events bundled under
one number) and Q17 (two unrelated AS 29 fact patterns) split into independent records;
Q15 (three progressively-building sub-parts, the third explicitly referencing "the above")
and Q20 (Euro-denominated branch accounts feeding a converted trial balance) correctly kept
as single connected records — a real worked example of both branches of the rule.

Also caught, independently of the splitting/tagging work: Q10 is printed in the source
under the heading "AS 7 Construction Contracts" but its actual content (Y Limited
constructing its own factory) is a self-constructed-PPE-plus-borrowing-cost problem, AS 10
+ AS 16, not AS 7 at all — exactly the header-mismatch failure mode already anticipated and
warned against in the RTP prompt's specific notes, now confirmed as a real, not just
theoretical, risk. Tagged from actual content, flagged the header mismatch in the
extraction-note rather than tagging blindly from the printed heading. One further source
typo was caught and corrected with a flagged note (an evident stray-zero OCR/typo artifact
in one journal-entry credit figure in Q19, internally inconsistent with the same entry's
debit side and with the same figure used correctly elsewhere in the same scheme).

Validated identically to the MTP file: 0 unclosed HTML tags, 0 backticks, 0 leftover
placeholder phrases, all 27 IDs (26 qblocks + 1 case scenario) unique, case-scenario
reference resolves.

**Both pilot sittings reviewed under the revised schema are now MTP May 2026 Set 1 and
RTP May 2026.** Remaining: MTP Set 2, PYQ May 2026, PYQ Jan 2026 still need first-time
generation via the revised prompts.

---

## 2026-07-24 (cont'd) — Question Bank schema revision: case scenarios, marks tagging, question splitting, Final Chapter, six new skill files

Continuing the same-day MTP Set 1 review (previous entry below), Pranav flagged two more
structural gaps by inspecting the rectified file directly: (1) Case Scenario MCQs'
shared narratives were captured nowhere at all — the questions referenced facts
("the Company", specific rupee figures, dates) that appeared in no visible node, an
extraction blunder neither the original AI nor Claude's first-pass fix had caught; (2)
marks, paper facets (MTP/RTP/PYQ, month, year, set), and difficulty needed to be
independently machine-queryable, not embedded in display strings like `"MTP May 2026 Set 1"`
or `"14 (7+7)"`.

Fixed the case-scenario gap immediately (added `.case-scenario` nodes + `data-case-ref`
for all three scenarios in the pilot file). For the rest, Pranav also forwarded an
external AI's independent schema-review document and asked for honest evaluation, not
blanket acceptance — most of it was sound (paper-level facets, structured MCQ options,
deterministic composite IDs, structured review-flag attributes) and was adopted; two
specific recommendations were rejected with reasoning (a parallel topic-ID namespace that
would recreate the U0/U1 ID-scheme fight already fixed once; diluting the synthesized
examiner-comment voice, which reverses `examiner-comments-writing-skill.md`'s explicit
design choice — voice fidelity + provenance metadata was always the intended
misattribution safeguard, not a diluted voice).

**New locked decision (Pranav):** multi-part descriptive questions get classified
independent (unrelated sub-parts, just bundled under one question number — the common
case, confirmed by checking every multi-part question in the pilot file) vs. connected
(one continuous fact pattern). Independent sub-parts split into separate Question Bank
records, each single-topic; connected questions stay one record. Paired with a new
`data-final-chapter` concept — every question/fragment's designated home chapter in the
assembled book, computed from `teaching_sequence` (pulled fresh from
`books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`).
Also confirmed: Easy/Medium/Hard difficulty (by count of distinct topics tagged: ≤2/3–5/
>5) will be computed in the Python `questions.json` step, never hand-authored in HTML —
Pranav's own call, for the same one-place-to-change-the-logic reason already governing
the rest of the pipeline's two-layer (HTML source / JSON computed) architecture.

Rebuilt `MTP_May2026_Set1.html` end-to-end against the new schema: split the four
multi-part Part II questions into 13 independent records (one, Q6's part (a), also needed
`data-alt-group` handling for its OR-alternative), added paper-level facets on `<body>`,
converted all 15 MCQs' options to structured `<ol><li data-opt>` lists, fixed 54 leftover
stray-backtick rupee signs the earlier review had missed, fixed an arrow-in-cell
(`1,50,000 → 8,50,000`) table anti-pattern into separate before/after columns, and added
`data-final-chapter`/`data-confidence`/`data-review-status`/`data-comment-source` across
all 28 resulting qblocks. Validated with a Python script: 0 unclosed HTML tags, 0
backticks, 0 leftover placeholder phrases, all 31 IDs (28 qblocks + 3 case scenarios)
unique, all case-scenario references resolve, marks arithmetic correct (Part I = 30, Part
II = 84 across 6 distinct questions after alt-group deduplication, i.e. 6×14 — matching
the paper's "compulsory Q1 + best 4 of remaining 5" structure).

Wrote six new skill files at `_claude/skills/SKILL-question-bank-*.md`
(`pipeline-overview`, `html-schema`, `topic-tagging`, `question-splitting`,
`examiner-comments`, `duplicate-detection`) plus `verbatim-extraction` (seven total),
per Pranav's explicit request that all of today's Question Bank learnings be captured as
durable, self-contained documentation usable "by anyone using a clone of git... with
whatever AI they want" — `pipeline-overview` is the front-matter index pointing to the
rest. Updated `first_run/schema/HTML-SCHEMA.md` (the operative generation spec) and
`first_run/prompts/GENERATE-SITTING-HTML-PROMPTS.md` (all 3 prompts) to match, including
switching the prompts' source-of-truth instruction from the `.md` conversions to the
original PDFs directly (per the new `verbatim-extraction` skill's #1 rule) and adding an
explicit "count questions against the paper's own stated structure" instruction, aimed
directly at the missing-Q6 failure mode from earlier today.

**Not yet done:** `RTP_May2026.html` (generated under the old schema) needs re-review/
rebuild against the new one. `MTP_May2026_Set2.html`, `PYQ_May2026.html`,
`PYQ_Jan2026.html` still need first-time generation with the revised prompts. The
HTML→JSON extraction script, the duplicate-detection (OP/PP) implementation, and the
difficulty-computation step are all still unbuilt — designed in the new skills, not yet
coded.

---

## 2026-07-24 — MTP May 2026 Set 1: reviewed and rectified the first pilot AI output against the source PDF

Pranav ran Prompt 1 through his external AI and got `first_run/output/MTP_May2026_Set1.html`. He asked for a review against the **PDF** (not the MD conversion), and rectification of anything wrong.

**Found it badly non-compliant with `HTML-SCHEMA.md` and the prompt's own rules**, extracted both source PDFs (`CAInter-AdvAcc-MTP-May2026-Set1-Q.pdf`, `-Ans.pdf`) via `pypdf` to verify line by line:
- **Zero chapter/topic tagging** on all 20 questions (`<span class="na">Not tagged yet</span>` everywhere) despite the prompt requiring it.
- **Part II (descriptive, 70 of 100 marks) was not verbatim** — placeholder/meta-descriptive text like "(full text as in source)" and "as in source answers (verbatim, OCR-normalized)" stood in for actual content.
- **Question 6 of the source paper (14 marks — AS 24/Amalgamation alternative + AS 1 + AS 17) was missing entirely** — the AI only produced Q1–Q5 of Part II's 6 printed questions, silently dropping one full question worth 14 marks.
- **Two mark totals were wrong**: Q2 shown as 12 (source: 7+7=14), Q5 shown as 16 (source: 10+4=14) — the overall 30+70=100 happened to still check out only by coincidental cancellation.
- Examiner comments were thin one-liners, not following `examiner-comments-writing-skill.md`'s required quantifier/failure-mode/citation/consequence structure.
- Positives that did hold up: all 15 Part I MCQ answers verified correct against the PDF; `.author-comment` placeholders correctly present/empty throughout.

**Rectified directly** rather than re-prompting the external AI: rebuilt all 21 question blocks (added the missing Q6 as `id="Q21"`) with genuine verbatim question/answer text transcribed from the PDF extraction, tagged every question against `topic-index.json`'s taxonomy (flagging the one AS 1 tag as pointing to a chapter/unit not yet individually indexed, rather than fabricating detail), fixed the two mark totals, rewrote every examiner comment in the skill's actual voice, and fixed the "Printed paper instructions" placeholder with the real verbatim instructions. Also flagged (not silently corrected) one internal inconsistency found in the source answer PDF itself — Falgun Ltd.'s Note 1 Share Capital block prints figures for a different company size than the trial balance — left in as printed with an extraction-note pointing it out for Pranav's judgment call. Verified the final file has zero unclosed HTML tags and correct marks arithmetic (Part I 30 + Part II compulsory Q1 14 + best 4-of-5 optional = 70 = 100 total; file now shows all 6 printed Part II questions summing to 84, matching how MTP answer keys conventionally print solutions for every optional question).

**Not yet done:** `RTP_May2026.html` (already generated, not yet reviewed) still pending; the stray empty `first_run/output/TODO.md` is still unexplained/uninvestigated.

---

## 2026-07-23 — Strategy book: em-dash pass across all student-visible content

Pranav flagged that heavy em-dash use across the book reads as an AI-writing tell, and asked for a pass to humanize it. Scoped to actual book content only (Bucket 0–6, AI Section, Emergency, Personal Pages, front matter's real prose, Author's Journey) — explicitly not MASTER.md's internal working-draft/status notes, which aren't student-visible.

**Real scope, checked before starting:** 529 em-dashes in MASTER.md, but only 417 were prose (the other 112 are `Strategy N — Title` / `BUCKET N — Name` structural heading separators the parser's regex depends on to detect section boundaries — confirmed via the renderer that these never even survive into the rendered HTML as literal dash characters, since the tokenizer splits them into separate number/title fields). Plus 25 in front-matter.html and 41 in authors-journey.html (both hand-authored, edited directly, never regenerated).

**Went through every instance by hand, not a blind find-replace** — a mechanical substitution would break grammar constantly (some dashes need a comma, some a period splitting into two sentences, some a colon, some parentheses, depending on what the sentence is actually doing). Worked bucket by bucket: Routing → Bucket 0 → ... → Personal Pages, then both hand-authored files. A few of the period-splits (e.g. "Don't overthink the sequence. This default beats a blank page every time.") land closer to the book's intended "older brother, blunt" voice than the original single long sentence did anyway.

Also fixed the `<title>` tag em-dash (shared across all generator output, one-line fix in `build_page()`) and the Table of Contents' own `Bucket N — Label` format in `generate_toc.py` (that one was my own code, no parser dependency, fixed for full consistency).

**Left alone, deliberately:**
- Heading separators (`Strategy N — Title`, `BUCKET N — Name`, `TRACK A — ...`) — structural convention, not a prose tell, and some are parser-regex-load-bearing.
- Two table-placeholder dashes in the backward-planning calendars (`Exams start  —  —  01-05-2027`) — these mean "no value," same as a spreadsheet blank cell, not a written dash.
- One literal quoted exam-answer example (`"Computation of Total Income — Mr. X"`) — showing exact text a student would write on their answer sheet; a real accounting convention, not prose style.

**Verified, not assumed:** re-ran the full merge + ToC-resolve pipeline afterward — stable at 92 pages, same page numbers as before the edit (confirms the punctuation changes didn't meaningfully shift line-wrapping), and grepped the final merged book's body content for `—` to confirm only the three intentional exemption categories above remain.

Also caught and fixed a newly-stale `component-index` health-check failure (MASTER.md's content changed enough to trip the checksum) by re-running `tools/generate_component_index.py`.

---

## 2026-07-23 — first_run/ pilot workspace built: schema, style JSON, 3 external-AI prompts

Pranav reviewed `Claude_V2.md`'s paged.js/single-source-of-truth learnings (from the concurrent Strategy Book session) and asked for the same discipline in the Question Bank pipeline: font-size/spacing/margins controlled from exactly one JSON, never hardcoded per file. Distilled those learnings into new **CLAUDE.md section 7** (7 numbered lessons: JSON-driven geometry, `@page` not resolving `var()`, `break-inside:avoid` for page-break safety, local font vendoring, `position:running()` for repeating headers, merge-script gotchas, screenshot-based verification).

Also reconsidered and simplified the pipeline: **Parsed MD is not a required gate** (tagging works fine from Raw MD directly; cleanup can happen once, per-question, at first-read time instead of upfront for whole sittings that might not even get used) and **sitting-level records should embed full question+answer content directly** rather than staying a lean pointer-only index (this reverses part of yesterday's `TAGGING-SCHEMA.md` decision — for good reason: the one careful AI read of messy OCR content should never be thrown away and redone later). Also: MTP_Jan2025.json bundling both Sets into one file is inconsistent with the one-Set-per-100-mark-file convention used everywhere since — needs splitting (not done this session, flagged).

Further refined (after Pranav pushed back and asked for independent evaluation rather than agreement): moved from "embed HTML directly as JSON string values" to **"AI writes a standalone HTML file per sitting; a script extracts JSON from it mechanically."** Concrete reason this is better, not just different: embedding dense HTML (nested tables, quoted attributes, rupee signs) as JSON string values asks a model to get two escaping disciplines right at once, and smaller models are exactly the kind of thing that gets this wrong — a single bad escape corrupts the *entire* file. Plain HTML has no such compounding failure mode.

**Built `first_run/` (new temporary top-level folder, documented in CLAUDE.md §3 and README.md, zero new health_check failures introduced):**
- `source/` — copies of the 5-sitting pilot's 7 raw MD files + `Paper1-ExaminerComments-Jan2026.md`.
- `schema/book-style.json` + `generate_style_css.py` + generated `book-style.css` — the single source of truth for every font-size/spacing/colour/margin value; every sitting HTML links to the one generated stylesheet rather than hardcoding anything.
- `schema/HTML-SCHEMA.md` — the exact per-question HTML structure (`.qblock`, `.qmeta`, `.question`, `.answer-block`, `.topics`/`.topic-tag`, `.examiner-comment` with a mandatory `data-source` provenance attribute, `.author-comment` — always present, always empty, always hidden, a placeholder for Pranav's own future notes — and `.extraction-note`).
- `prompts/GENERATE-SITTING-HTML-PROMPTS.md` — 3 full, self-contained prompts (MTP/RTP/PYQ) for an external AI to read the raw sources directly and write real HTML files into `first_run/output/` (never just display content) — PYQ's prompt explicitly handles the split (Jan 2026 has a real ICAI Examiner's Comments doc to match against; May 2026 doesn't and gets synthesized notes per `examiner-comments-writing-skill.md`, embedded in the prompt).

**Pilot scope confirmed by Pranav:** MTP May 2026 Set 1 + Set 2, RTP May 2026, PYQ May 2026, and PYQ Jan 2026 (deliberately included out-of-batch specifically to test the real-comment-matching path) — 5 sittings, run through to a full chapter-book proof before scaling to the remaining ~30+.

**Waiting on:** Pranav running the 3 prompts (5 times total) via his other AI model(s). Next session resumes with reviewing the 5 HTML outputs, then building the HTML→JSON extraction script against real data.

---

## 2026-07-23 — Question Bank: U0 migration completed (topic-index.json + 4 tagged sittings)

Follow-up to the canonical topic/page-index JSON built earlier today (see entry below). Pranav confirmed: migrate everything to `U0` for the 7 single-unit chapters (Intro to AS, Framework, Applicability, Buyback, Amalgamation, Internal Reconstruction, Branch Accounting), reversing yesterday's `U1` choice.

Migrated in one pass: `topic-index.json` (7 `unitCode` fields + their `"unit": 1`→`0` companions) and all 4 already-tagged sitting JSONs (`MTP_Jan2025.json`, `MTP_May2024_Set1.json`, `PYQ_Jan2026.json`, `RTP_May2026.json` — 28 `unitCode` occurrences total). Re-validated every file as parseable JSON afterward; grepped for stray `U1` references and confirmed zero remain for these 7 chapters anywhere in tagging data. Deliberately left `topic-index.json`'s `sourceFile` fields alone (e.g. `"M1_C1_U1_ Introduction....pdf"`) — those are real filenames on disk under `raw_icai_study_materials/`, not our tagging convention.

Updated `TAGGING-SCHEMA.md` and `CLAUDE.md` §6 to mark the migration done (was previously flagged "not yet done, waiting on Pranav").

**Everything is now consistent**: `U0` + hyphens, matching the master syllabus JSON, the new canonical topic/page index, `topic-index.json`, and all 4 tagged sittings. Clear to proceed with Phase 1 (parsing + tagging the remaining ~34 sittings) without a looming ID-scheme cleanup hanging over it.

---

## 2026-07-23 — Strategy book: Table of Contents built, real page numbers verified working

Pranav wanted a Python script to generate the Table of Contents as its own file, added to the merge order like any other section — good instinct, and exactly how it's built. The hard part was always going to be page numbers: nobody can know what page Bucket 3 starts on until paged.js has actually laid out the whole merged book.

**First approach (didn't work, confirmed properly rather than given up on early):** CSS `target-counter()` — the standards-based way to ask "what page did this element land on." Looked promising (paged.js's CSS parser accepted the syntax, `getComputedStyle` showed it rewritten into an internal counter reference) but never actually resolved to a rendered number, across several syntax variants tried. Confirmed via paged.js's own GitHub issues this is a known, still-open bug (#145, "TOC page number always zero") — not a mistake in usage. One variant (`url(#fragment)` as a literal target) crashed pagination entirely and is now flagged in the code to never retry.

**What actually works:** paged.js stamps a real `data-page-number` attribute on every physical page container it creates. Built `tools/resolve_toc_pages.py` — drives its own headless Chrome instance over the DevTools Protocol (`websocket-client`, pip-installed), polls for genuine real-time pagination stability (reusing the section-15 lesson from yesterday — a fixed timer is not a reliable completion signal for a document this size), looks up which page each section's anchor lands on, and bakes the real number into `toc.html` as plain static text. Two-pass build: merge once (blank numbers) → resolve → merge again (correct numbers). `--remerge` flag chains the last two steps automatically.

**Verified, not assumed:** ran the full 3-command pipeline, then independently re-checked all 12 baked-in numbers against a fresh real-time pagination pass of the final book — every one matched exactly (routing→11 ... authors-journey→89, out of 92 total pages).

**Supporting changes:** `strategy_book_parser.py`'s `_h1()` now writes `id="{slug}"` on every section heading (bucket banners and generic H1s) — these are what the ToC and resolver both anchor to; `tools/generate_toc.py` imports `BOOK_ORDER` directly from the merge script rather than keeping a second list (order changes propagate automatically) and reuses `SECTION_META`'s already-correct labels rather than re-deriving display names. Front-matter.html and authors-journey.html both needed small hand-patches (anchor id, and — for front-matter specifically, since it supplies the merge's shared stylesheet — the new `.toc-entry`/`.toc-page` CSS) added surgically, never through the generator, per the standing hazard logged yesterday.

Full investigation and the working pipeline documented in Claude_V2.md section 16. Ran `health_check.py`/`file_index.py` — same 16 pre-existing failures, nothing new.

---

## 2026-07-23 — Canonical topic/page-number JSON built, U0/U1 decision reversed

Pranav shared `books/concept-book/syllabus-engine/data/CA INTER ADV ACCOUNTS - For Adarsh.csv` (400 topics, all 36 chapters incl. AS 1 and AS 27, real ICAI page numbers) and asked whether to convert it to JSON. Validated first: 0 duplicate topic IDs, 0 blank fields, spot-checked AS 10 against existing hand-built data — matched exactly. Test-converted before committing to anything.

Built `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` — the new canonical topic-number + page-number source. Cross-joined 1:1 against the locked master syllabus JSON (file 0) by `unique_chapter_id` (zero unmatched either direction), pulling in `teaching_sequence`/`chapter_name_short`/`marks_distinct_attempt_count`; added `standard`/`standard_title` (parsed from unit name) and `is_single_unit_chapter`.

**Decision reversed:** the CSV (and file 0) both use `U0` for the 7 single-unit chapters; Pranav confirmed switching from the `U1` convention chosen in yesterday's `TAGGING-SCHEMA.md` to `U0` ("no further units" reads more sensibly), and to keep hyphens (not the CSV's underscores) for IDs. `topic-index.json` and the 4 already-tagged sitting JSONs still use `U1` — **not yet migrated**, flagged as pending.

Also reviewed 3 more AS10 sample files Pranav added (`AS10_Question_Bank.json`, `AS10_Question_Reference.html`, `MTP_Jan2026.json`) — confirmed the two-layer book architecture (lean per-sitting tagging vs. derived per-chapter book JSON with embedded content), and that `MTP_Jan2026.json` is new untagged content needing to be folded into Layer 1.

Updated `TAGGING-SCHEMA.md` and `CLAUDE.md` §6 with all of this.

---

## 2026-07-23 — authors-journey.html: caught a second content-loss mistake, rewrote in third person

Pranav asked to check whether `authors-journey.html` was complete. Reading it showed the plain `[STRUCTURE ONLY]` placeholder — but per `project_log.md`'s own entry from 2026-07-22 ("Author's Journey + front-matter Category B sections complete"), the parallel session had already fully written this section (5-phase first-person narrative, real facts from the author profile, 4 quotes, photo placeholders). **My own blanket regeneration loop the previous session (run twice, for the book-order change and the font fix) silently overwrote it back to placeholder** — I'd protected `front-matter.html` specifically because I already knew it carried hand-authored content, but didn't realize this file did too, and didn't check before regenerating.

**Checked for recovery, found none:** MASTER.md never had the content (same gap as front-matter), the merged `FULL-BOOK.html` had already been regenerated by the time I looked, and a stray backup copy noticed in an earlier file listing no longer existed. Unlike the front-matter incident, there was no diff sitting in conversation context to restore from — the actual prose was gone for good.

**Resolution:** Pranav asked for the section to be rewritten in third person ("About the Author" style) rather than the original first-person plan. Read `books/about-author/Pranav_Pratik_Tulshyan_Master_Profile_Journey.md` (the real source document — far more detailed than the summary in the old log entry) and wrote a full third-person narrative covering the same ground: the demo-class Socrates story setup, Foundation 2014–15 (the teacher's rank-vs-pass philosophy, the PCO booth call, the 19 Jan 2015 AIR 1 result), Intermediate 2015–16 (handwritten summary system, the 25 April 2015 earthquake and the AIR-1-to-85%-target reframe, the Nepal Blockade, the Auditing Pronouncements story, the 1 Feb 2016 AIR 1 result), a "Why He Teaches" bridge (EY, CA Final AIR 5, IOCL, the coding/Efficient Corporates detour, the decision to teach CA Inter Accounts specifically), and the Socrates-story loop close. ~1,673 words. Added the missing `.journey-close`/`.photo-ph`/`.ph-caption`/`.story-vignette` CSS locally in this file (kept self-contained, not dependent on merge order). Verified it actually paginates correctly (2 pages, no errors) before re-merging — did **not** re-run the generator on any file, only the merge script, to avoid repeating the exact same mistake a third time.

**Standing risk, now stated more broadly (see also Claude_V2.md §14.2):** at least two build/ files (front-matter, authors-journey) have carried hand-authored content invisible to MASTER.md and at risk from any blanket regeneration. There may be others not yet discovered. Until this is resolved by porting real content back into MASTER.md as the source of truth, **never run `strategy_book_parser.py --section all` without first diffing every affected file against a fresh regen** — not just the ones already known to be hand-edited.

---

## 2026-07-22 — Strategy book: FULL-BOOK.html finalized (87 pages, verified stable) + a major false-alarm debugging lesson

Pranav gave the exact book order to merge (front-matter, routing, bucket-0..6, ai-section, emergency, personal-pages, authors-journey — "cover" deliberately dropped) and asked for a final, properly print-ready `FULL-BOOK.html` with "no margin or page issues."

**Checked front-matter.html was in sync first** (it carries hand-authored content from a concurrent session, per the standing hazard logged this morning) — geometry, footer fix, and structure were all already correct; no changes needed there.

**Updated `BOOK_ORDER` in `tools/strategy_book_merge.py`** to match exactly, regenerated the other 13 sections individually (still deliberately not touching front-matter.html directly via the generator), hand-patched only front-matter.html's font-loading `<link>` tag, and re-merged.

**Then hit a serious-looking problem:** repeated headless-Chrome checks of the identical merged file gave wildly different page counts (4, 7, 10, 22, 262) — looked like real pagination corruption. Spent real effort chasing two plausible causes (an empty `.blank-page` div confusing paged.js's fragmentation; Google Fonts loading over the network racing against paged.js's layout pass) — vendored all fonts locally either way (`design/templates/vendor/fonts/*.woff2` + `gfonts-local.css`, replacing the `@import` from fonts.googleapis.com) since it's a legitimate improvement regardless, but **instability persisted through both fixes**.

**Root cause, confirmed properly rather than guessed:** `--dump-dom`/`--virtual-time-budget` simply capture Chrome's headless state at an arbitrary, non-deterministic point — for a small file this coincides closely enough with paged.js actually finishing, but for this ~200KB/13-section merged book, paged.js needs several real seconds of wall-clock CPU time to converge, and every prior capture in this session was catching it mid-render. Installed `websocket-client` via pip (flagged, same low-risk pattern as the other concurrent session's `pypdf` install today) and drove Chrome directly over the DevTools Protocol, polling `document.querySelectorAll('.pagedjs_page').length` every 3 **real** seconds with no virtual-time involved at all. Result: **87 pages, stable from the very first check through 120 continuous real seconds** — confirmed genuinely complete, not a snapshot. Separately confirmed the actual rendered text ends exactly at the book's true final line ("End of Master Draft...") — nothing silently truncated.

**Documented as Claude_V2.md §15** — a standing rule for future sessions: never trust a single `--dump-dom`/`--screenshot` capture's page count for the *full merged book* (only for small single-section files, where it's fine). Poll for real-time stability instead, or just do what the human workflow already does — open it in a foreground tab and wait until it visibly stops changing before printing.

**Final state delivered:** `books/strategy-book/design/templates/build/FULL-BOOK.html`, 87 pages, verified stable, front-matter in sync, fonts vendored locally, correct book order. Ran `health_check.py`/`file_index.py` — same 16 pre-existing failures, nothing new.

---

## 2026-07-22 — Question Bank Book: locked in the end-goal + two new content layers

Pranav showed the target deliverable: `books/question-bank/metadata-index/AS10_Question_Book.html`, a hand-built student-facing "go-to book for practice" for AS 10 (~58 questions, official answers, topic tags, Common Student Mistakes, confidence flags). This reframed the whole Question Bank effort — tagging isn't the end product, it's infrastructure for one HTML book per chapter.

**Two strategic decisions confirmed by Pranav (see CLAUDE.md §6 for full detail):** (1) tag every sitting comprehensively once for every chapter, never re-scan chapter-by-chapter; (2) render chapter books with a reusable generator script, not hand-assembled HTML.

**New work this session:**
- Pranav sourced 6 real ICAI "Examiners' Comments on the Performance of the Examinees" PDFs (Jan2025/May2024/Sep2024/May2025/Sep2025/Jan2026) — converted, sliced to Paper 1 section (`Raw_PDF_.../examiner-comments-paper1/`). Analysed all 6 and wrote `metadata-index/examiner-comments-writing-skill.md` — a style guide for writing ICAI-voiced "Common Student Mistakes" for every question outside those 6 sittings, with a strict real-vs-synthesized provenance tag.
- Added Pranav's OP/PP recurring-question rule (90%-similarity-on-numbers-stripped text; earliest sitting = OP, rest = PP) to `TAGGING-SCHEMA.md`, alongside the `commonMistakes` schema.
- Deliberately did NOT retrofit the 4 already-tagged sitting JSONs — new shape applies going forward only.

**Blocked on:** Pranav is going to share more `AS10_*` sample files (`AS10_Question_Reference.html`, `question-book-implementation-plan.md`, `AS10_Question_Bank.json`) to reconcile our schema before the generator script gets built and Phase 1 (parse+tag remaining ~34 sittings) resumes at scale.

---

## 2026-07-22 — Strategy book: Author's Journey + front-matter Category B sections complete

**`authors-journey.html`** — fully written (was a CSS-only shell):
- Added CSS for `.journey-close` (gold left-border close block) and `.photo-ph` (picture gallery placeholders with handwritten-style `.ph-caption` in Kalam font)
- Full first-person narrative in 5 phases: Foundation 2014–15, Intermediate 2015–16, February 1 2016 result, Why I'm Here, the Socrates close
- All key facts from the master profile used: PCO booth call (80 seconds, 3rd ranker), earthquake April 25 2015 (11:56 AM, Cost Accounting / Overhead chapter), 25–30 days lost, 85% mental reframe, Nepal Blockade, Auditing Pronouncements 5-mark question, dates (Jan 19 2015 CPT, Feb 1 2016 IPCC)
- Four key quotes placed as `blockquote.anon-bq`: "I am not guaranteeing the result. I am guaranteeing the work." / the rank feeling quote / "What you do not revise the day before the exam..." / "Be stubborn about your goals. Be flexible about your methods."
- Socrates loop closes the section in `.journey-close` block
- Four `.photo-ph` placeholders for picture gallery (real photos needed from Pranav)

**`front-matter.html`** — all Category B sections written:
- Added CSS for `.story-vignette` (left border, non-italic vignette block) and `.dedication-block` (centered, spacious)
- **Dedication:** left as `[AUTHOR TO CONFIRM]` — Pranav must write this personally
- **The Socrates Story:** written as a brief plain-prose vignette (7 short paragraphs), no moral stated, no explanation — sits alone as intended
- **About This Book:** full prose from the bullet outlines — what it is, what it isn't, the implementation-layer differentiator, the gyaan warning
- **About the Author:** two-paragraph credential block — AIR 1 CPT+IPCC, EY, IOCL, VC Gurukul; pointer to the journey at the back
- **How to Read This Book:** prose version — bucket navigation, Bucket 0 is daily, [ALL]/[RANK] markers, Emergency Section independence, groups note
- Table of Contents remains `[AUTO-GENERATED]`

**What's left in the book:**
- Cover: Pranav getting it built elsewhere
- Dedication: Pranav's personal text
- Picture Gallery photos: real CPT/IPCC notebooks etc.
- Table of Contents: auto-generated at final assembly

---

## 2026-07-22 — Strategy book front-matter: Blank Page, Title Page, Copyright done

Completed three of the four Category A sections in `books/strategy-book/design/templates/build/front-matter.html`. Emergency section was already fully written (6 steps + 10-day schedule + "what not to do") in a prior context window — confirmed complete, no further work needed.

**What changed in front-matter.html:**
- Removed the `<h1>FRONT MATTER</h1>` editorial heading and the three `<h3 class="subsection-heading">Page N</h3>` structural markers for pages 1–3.
- Added CSS for three new layout classes: `.blank-page`, `.title-page` (with sub-elements `.tp-series`, `.tp-title`, `.tp-rule`, `.tp-author`, `.tp-credential`, `.tp-publisher`), and `.copyright-page` (with `.copy-year`).
- **Page 1 — Blank Page:** genuinely empty `<div class="blank-page"></div>` with `break-after: page`.
- **Page 2 — Title Page:** flex column layout (top/center/bottom zones); title "The Comprehensive CA Intermediate Exam Preparation Guide"; author "CA Pranav Pratik Tulshyan"; credential "AIR 1 (Foundation) · AIR 1 (Intermediate)"; publisher "VC Gurukul · Noida". Gold rule between title and author block.
- **Page 3 — Copyright & Disclaimers:** copyright line + no-reproduction notice + ICAI-requirements disclaimer + strategy-results disclaimer + publication year. Padded from top 60mm (verso positioning convention).
- Pages 4 onwards (Dedication, Socrates Story, About This Book, About the Author, How to Read, ToC) left as `[STRUCTURE ONLY]` — Category B/C, need Pranav's input.

---

## 2026-07-22 — Strategy book: whole-book merge script (`strategy_book_merge.py`)

Continuation of the same-day paged.js work. Pranav wanted independent per-section HTML files (already true — `strategy_book_parser.py` outputs one per bucket) plus one Python script to stitch them into a single whole-book file for continuous pagination/page numbers, with an explicit tuple of paths/slugs controlling merge order rather than relying on filenames.

**Two things checked before building, both verified rather than assumed:**
- Diffed the embedded `<style>` block across 4 different generated files (`bucket-0`, `ai-section`, `cover`, `authors-journey`) — byte-identical. Confirms consolidating to one shared stylesheet in the merged file is lossless, since per-section color/label are always inline styles, never baked into the CSS.
- Found a real bug while checking mergeability: every strategy heading gets `id="s{number}"`, and the number restarts at 1 in every bucket (confirmed `bucket-0.html` and `bucket-1.html` both have `id="s1"`, `id="s2"`...) — would collide into duplicate/invalid ids the moment two sections share one document.

**Also fixed in passing:** `"THE AUTHOR'S JOURNEY — CPT & IPCC"` had no `SECTION_META` entry, so it fell through to a generic fallback — output filename `section.html` (meaningless, collision-prone) and a mangled running-header label ("The Author'S Journey — Cpt & Ipcc" from Python's naive `.title()`). Added a proper entry; now generates as `authors-journey.html` with the correct label.

**Built `tools/strategy_book_merge.py`:** takes `BOOK_ORDER` (an explicit tuple of section slugs, editable in one place, not derived from filenames) or a `--order` CLI override; extracts each section's body-only content (drops the per-file paged.js `<script>` tag, kept exactly once in the output); rewrites `id="sN"` → `id="{slug}-sN"`; wraps each section in a `.book-section` div with `break-before: right` (recto-start, added only at merge time — lone section files don't need it); writes into the same `build/` folder as `vendor/paged.polyfill.js` so the existing relative script path keeps working. Validates in both directions before merging: any listed slug with no file = hard error; any file in `build/` not listed = hard error (downgradeable to a warning via `--force`) — protects against a section silently vanishing from the final book. Also checks CSS is still byte-identical across all sections being merged (hard error if not, `--force` to override) and warns if `MASTER.md` is newer than the build files being merged (stale-build hint).

**Verified with headless Chrome, not just read from the code:** ran `--dump-dom` on the merged 14-section `FULL-BOOK.html` (193,698 chars) — confirmed running-header color switches correctly at each section boundary (all 10 distinct bucket/section colors found in the rendered DOM, in the right places), single `<style>`/`<script>` survived the merge, ids properly disambiguated (`bucket-0-s1` and `bucket-1-s1` both present, distinctly). Also tested the validation logic directly: missing-slug hard error, orphaned-file hard error, and `--force` correctly downgrading the orphan case to a warning.

Documented all of this as durable learnings in **Claude_V2.md §13** (paged.js running-element mechanism, why `@page` can't be trusted with `var()`, the print-media export gap, and the full list of merge-script gotchas) so a future session doesn't have to re-derive any of it.

Ran `tools/health_check.py` + `tools/file_index.py` after adding the new script and build artifact — same 16 pre-existing failures as this morning's entry, nothing new introduced.

---

## 2026-07-22 — Question Bank: PYQ pipeline simplified to Answers-only, coverage extended to 2021

Pranav noticed PYQ "Suggested Answers" PDFs already contain both question and answer text, and are printed (not scanned) — unlike the separate PYQ Question-only PDFs, which always convert blank. Decision: PYQ sourcing now targets only the Suggested Answers document per sitting (same single-document shape as RTP); Question-only PDFs are dead weight.

**Work done:**
- Moved the 4 existing PYQ Question-only PDF/MD pairs (Jan2025, Jan2026, May2024, May2026) to new `Raw_PDF_Question_Bank_CA_Inter_Accounts/deprecated-pyq-question-files/`.
- Converted 6 newly-sourced PYQ Answer PDFs to `.md`: May 2026 (fills a previously-missing sitting) plus 5 older sittings never in the repo before — Dec 2021, May 2022, Nov 2022, May 2023, Nov 2023 (last two were AES-encrypted, empty-password decrypt worked). Used `pypdf` directly (MarkItDown isn't installed in this sandbox) — same plain-text-extraction contract, logged as such.
- Updated `conversion_log.txt` and `question_bank_index.csv` to match current folder reality.
- Built `books/question-bank/question_bank_index_by_attempt.csv` (new) — one row per exam sitting (not per file) with PDF/MD/Parsed/JSON status columns; more useful than the per-file CSV for pipeline-status questions. Updated `CLAUDE.md` section 6 accordingly.

**Result:** PYQ coverage now spans **Dec 2021 – May 2026** (was May 2024 – May 2026) — real progress toward the README's 7–10 yr goal. MTP/RTP still only May 2023 – May 2026.

**Note:** installed `pypdf` + `cryptography` via pip into the sandbox Python (not into the repo/venv) to do the conversions — flagging since it's an environment change, though a low-risk, easily-redone one.

---

## 2026-07-22 — Strategy book: paged.js wired in, page geometry config-driven

Pranav asked how to write the strategy book's HTML so page size/margins can change anytime with no manual re-editing and no overflow risk. Diagnosed a real bug in the existing `tools/strategy_book_parser.py` output: each section was one giant `.page-shell` div with `position:absolute` header/edge-tab/footer — correct-looking for exactly one physical page, but silently broken the moment Chrome sliced a tall bucket into multiple PDF pages (header/footer/edge-tab would only appear once per bucket file, not repeated per page).

**Work done:**
- `books/strategy-book/design/page-geometry.json` (new) — single source of truth for trim/margins.
- `tools/strategy_book_parser.py` — `get_css()` now templates both the `:root` CSS vars and the literal `@page` rule from that one JSON (`@page` doesn't reliably resolve `var()`, so both are substituted from the same source at generation time, never hand-duplicated). Removed the `.page-shell` fixed-div-per-file pattern entirely; content is now one continuous flow. Header/edge-tab/journey-strip are defined once per section via `position: running(name)` + `@page { @top-center/@bottom-center/@right-middle { content: element(name); } }` (edge tab only on `@page :right`) — paged.js auto-repeats them on every generated physical page. Added `break-inside: avoid` on every component (was missing) and `print-color-adjust: exact` (was missing entirely — bucket colours would've printed white).
- Vendored `paged.js` locally at `design/templates/vendor/paged.polyfill.js` (downloaded, MIT license) rather than a CDN, consistent with the offline-safe pattern already used for fonts/images elsewhere in this repo.
- Regenerated all sections (`python tools/strategy_book_parser.py --section all`) — 14 files now, including `cover.html`, `bucket-1.html`, `bucket-2.html`, `bucket-6.html` which MASTER.md had content for but nothing had generated yet.
- Verified with headless Chrome `--dump-dom`: pagination and running-element repetition are confirmed genuinely working (running header found on 4+ generated pages, edge tab on 3+, journey strip on 4+ for `bucket-0.html`).
- **Found and documented a real gap:** the existing `chrome --print-to-pdf` CLI recipe (`_claude/skills/SKILL-html-to-pdf.md`) does NOT work on paged.js output — produces a near-empty ~1KB PDF, because paged.js's paginated view is hidden under print media unless the caller forces screen-media emulation first (which plain Chrome CLI flags cannot do; normally requires Puppeteer). Added a new §9 to that skill file documenting this, with the working manual fallback (open in Chrome → Ctrl+P → Save as PDF) and what a Node+Puppeteer automated path would need. **Node/npm are not installed on this machine** — flagged, not installed without asking first.
- Ran `tools/health_check.py` + `tools/file_index.py` per repo rule. Health check's 16 failures are all pre-existing, unrelated to this work (missing `syllabus-engine`/`question-bank` subfolders, NUL bytes in unrelated `bridge-course/base-studymaterials/*.md` files, `capranav_com/` undocumented in CLAUDE.md) — not touched this session, flagged for Pranav.

**Known trade-off, not yet solved:** `.bucket-banner` (bucket opener colour banner) no longer bleeds to the full trim edge — the old negative-margin trick escaped `.page-shell`'s padding, which no longer exists. True full-bleed under `@page`-margin pagination needs a dedicated zero-margin named page; open item.

**Next lever:** if Pranav wants one-command PDF regeneration back, that needs Node + Puppeteer installed — ask before adding. Otherwise the manual Ctrl+P → Save as PDF path works today with zero new tooling.

---

## 2026-07-22 — Question Bank Book: full-focus audit + tagging schema + 3 sittings tagged

Pranav asked to shift full focus to the Question Bank Book (`books/question-bank/`). Ran a 3-way audit (question-bank folder, concept-book/syllabus taxonomy, mcq-platform for competing schemes) and wrote it up in **CLAUDE.md section 6** (new) — corrected two stale path entries in section 3 (`syllabus-engine/` and `question-bank/` both actually live nested under `books/concept-book/` and `books/` respectively, not at repo root as previously documented).

**Key findings:** raw PDFs converted (54/55) but only 3 of ~55 files had gone through the clean HTML-table parse; only 1 of ~17 exam sittings (MTP Jan 2025) had questions tagged to syllabus topics; three overlapping chapter/topic ID schemes exist in the repo (concept-book bracket tags, the "locked" master syllabus JSON, and `topic-index.json`) with a `U0`-vs-`U1` mismatch for 7 single-unit chapters between the master JSON and everything else.

**Work done:**
- `books/question-bank/metadata-index/TAGGING-SCHEMA.md` (new) — locks in `topic-index.json`'s `unitCode`+`subtopicRef` scheme (not the master JSON's IDs) as the tagging target, documents the U0/U1 reconciliation table, and switches to a **lean index** going forward (question/answer content stays in `Parsed_PDF_.../`, tagging files only point at it via `mdAnchor` — no more full-HTML duplication like the `MTP_Jan2025.json` pilot did).
- Tagged all 3 already-parsed pilot sittings end-to-end: `MTP_May2024_Set1.json`, `PYQ_Jan2026.json`, `RTP_May2026.json` (new files in `metadata-index/`) — 4 of ~17 sittings now tagged, up from 1.
- Extended `topic-index.json` from 22 to **32 of 36** syllabus units — added stub entries (heading lists only, not full descriptions) for AS16, AS28, AS18, AS5, AS24, AS7, AS22, AS25, AS15, AS17 as they came up in the 3 sittings. Only AS 1 and AS 27 remain untouched by any tagged question.
- All new/edited JSON validated (`python -c "import json; json.load(...)"`).

**Explicitly NOT done (flagged, Pranav to decide):** `books/question-bank/README.md` still describes the abandoned `pyq/mtp/rtp/solutions/` layout; `tools/health_check.py`'s `EXPECTED_DIRS` still checks for a top-level `question-bank/` that doesn't exist (pre-existing false-flag, not touched this session).

**Next lever:** parsing the remaining ~52 raw conversions into the clean `Parsed_PDF_.../` format is now the bottleneck — tagging itself is fast once a sitting is parsed.

---

## 2026-07-20 (latest) — Phase 1 extraction fully delegated (MTP/RTP/PYQ/ICAI-Practice); Batch 1 book pivot

**Continuation of the same session — read the two entries below first if picking this up cold.**

**Pivot:** Pranav asked to finish the Batch 1 (10-unit) Question Bank Book first, before starting Batch 2/3 Phase 0. Since Phase 1 (question extraction) is naturally per-source-paper not per-chapter, decided (Pranav's call) to **extract every question from every source paper once now**, then tag against Batch 1's keyword index only — non-Batch-1 matches wait for Batch 2/3's indexes later. This avoids re-scanning the same source papers three times.

**Delegation across tools, per Pranav's request:**

- Wrote `phase1-mtp-prompts.md` (5 prompts, 18 MTP attempts/36 files), `phase1-rtp-prompts.md` (3 prompts, 7 RTP files), `phase1-pyq-prompts.md` (3 prompts, 7 PYQ attempts incl. the null-Q/null-Ans edge cases) — for Pranav to run through Gemini/Copilot/Blackbox. **Not yet run as of this entry.**
- ICAI-Practice compilation (scanned, 101+111 pages) was assigned to me directly since it needed OCR. Built and verified an OCR pipeline (PyMuPDF + pytesseract, see the entry below for the snippet) and OCR'd both PDFs successfully.
- **I hand-extracted Model Test Papers 1–4's questions myself** (reading the OCR text directly) — written to `books/question-bank/metadata-index/icai-practice-extraction/icai_practice_MTP{1,2,3,4}_Q_extracted.json`. Partway through MTP5, Pranav pointed out that once OCR is done, structuring plain OCR text into JSON is mechanically identical to what the other three tools are doing for MTP/RTP/PYQ — no longer needs a premium model. **Correct call — I agreed and stopped doing it by hand.**
- Copied `icai_practice_Q_ocr.txt` / `icai_practice_Ans_ocr.txt` (the full OCR dumps) into the repo at `books/question-bank/metadata-index/icai-practice-extraction/` so Tier 2 tools can actually read them (they'd been sitting in Claude's own scratchpad temp dir, inaccessible to VS Code extensions). Wrote `phase1-icai-practice-prompts.md` (2 prompts: extract MTP5-8, then match answers for all 8 papers against the Ans OCR text, using my MTP1-4 files as the format reference). **Not yet run.**

**Lesson for future sessions:** OCR (image→text) is genuinely Tier 1/mechanical and fine to do myself via Tesseract. But *structuring* OCR'd text into schema'd JSON is Tier 2 work like any other source file — don't keep doing that by hand past the first paper or two once the OCR output is confirmed clean; write the prompt and hand it off. Recognize this pivot point earlier next time instead of grinding through several papers first.

**Current state:** all four Phase 1 prompt sets (MTP, RTP, PYQ, ICAI-Practice) are written and ready. Nothing to do until Pranav runs them and brings back outputs. Next real work is reviewing/merging those 8 batches of JSON, then Phase 2 (tagging against Batch 1's `topic-keyword-index.json`), then Phases 3–8 to produce the finished Batch 1 book.

---

## 2026-07-20 (later) — Phase 0 Batch 1 complete: topic-keyword-index.json (10/36 units)

**Continuation of the AS2/AS10 audit session (see the entry below this one for full background — read that first if this is your first time picking up the Question Bank Book work).**

**What happened this session:**
- Rebatched Phase 0 to Chapters 1–4 / 5–9 / 10–15 (10/17/9 units, replacing the earlier 17/13/6 split) — AS 2 and AS 10 now sit in Batch 2, not Batch 1.
- Verified Tesseract 5.5.0 install and built a working OCR pipeline: **PyMuPDF (`fitz`) + `pytesseract`**, no Poppler needed — simpler than the originally-planned `pdf2image` route. Confirmed end-to-end against the ICAI-Practice compilation.
- Wrote `books/question-bank/metadata-index/phase0-batch1-prompts.md` — 10 fully-instantiated Phase 0 prompts (real file paths, real topic scaffolds pulled from the taxonomy JSON), one per Batch 1 unit, ready to paste into Gemini/Copilot/Blackbox.
- **Ran all 10 prompts and completed the full Tier 3 review + merge cycle.** `books/question-bank/metadata-index/topic-keyword-index.json` now has **10/36 units, 114 topics**: M1-C1-U0 (Intro to AS), M1-C2-U0 (Framework), M1-C3-U0 (Applicability), M1-C4-U1 (AS1), M1-C4-U2 (AS3 Cash Flow), M1-C4-U3 (AS17 Segment Reporting), M1-C4-U4 (AS18 Related Party), M1-C4-U5 (AS20 EPS), M1-C4-U6 (AS24 Discontinuing Ops), M1-C4-U7 (AS25 Interim Reporting).

**Batch 1 is fully done.** Every Tier 2 draft was checked line-by-line against its actual source `.md`, not rubber-stamped. Patterns worth knowing before doing Batch 2/3:
- **Almost every unit's Tier 2 draft omitted the unit's own "Illustrations + Test Your Knowledge" section** as a topic bucket — even though this is usually the single richest source of realistic exam-style numerical/scenario questions. Added as a `*`-suffixed unnumbered bucket (e.g. `M1-C4-U5-T5.13*`) in every case. **Expect this same gap in Batch 2/3 outputs — check for it every time, don't assume a Tier 2 tool will remember to include it.**
- Some tools explicitly stated they only read part of a long source file (AS 17's tool said "read lines 1 to 500" of a 1010-line file) — when that happens, the *numbered* topics it did cover are usually still accurate, but the unread tail (illustrations/TYK) needs a separate read-and-add pass.
- Dense definitional/threshold sections (AS 18's `T4.6`, the MSME/SMC thresholds in `M1-C3-U0-T2`) came back essentially error-free even under heavy scrutiny — the Tier 2 tools are reliable on this kind of content when given the exact file path + topic scaffold, per the prompt design in `phase0-batch1-prompts.md`. The failure mode is *omission* (missing sub-rules, missing whole sections), not *fabrication* — no hallucinated facts were found across all 10 units.
- One prompt output arrived as an exact duplicate of an earlier prompt's output (Prompt 9 first came back identical to Prompt 7) — flagged to Pranav, he re-ran it and got a valid distinct result. If this happens again, don't merge the duplicate; ask for a re-run.

**Immediate next steps:**
1. Batch 2 (Chapters 5–9, 17 units — includes AS 2 and AS 10, which already have deep familiarity from the original audits) is next. Per Pranav's decision, wait for **all 17** Batch 2 units' Phase 0 keyword drafts before starting Phase 1 (question extraction) on any of them, including AS 2/AS 10 — don't fast-track those two ahead of their batch-mates.
2. Need a new `phase0-batch2-prompts.md` analogous to the Batch 1 one, with real file paths + topic scaffolds for all 17 Batch 2 units.
3. The two flagged AS 10 audit gaps (PYQ May 2026, ICAI-Practice MTP 6–8) from the earlier session are still open and lower priority than the Question Bank Book pipeline work.

---

## 2026-07-20 — AS2/AS10 question-bank audits + Question Bank Book project kicked off

**Read this entry first if you're picking up the "Question Bank Book" work on a fresh clone/session — it explains exactly where things stand and what to do next.**

**What exists now:**
- `books/question-bank/metadata-index/AS2_Question_Reference.html` and `AS10_Question_Reference.html` — accuracy-audited, topic-tagged references of every genuine question found in the MTP/RTP/PYQ/ICAI-Practice question bank for AS 2 (Valuation of Inventories) and AS 10 (Property, Plant & Equipment) respectively. Each has a topic-wise marks-weightage summary plus MCQ/Descriptive/Integrated detail tables with page refs (Q and Ans located independently, never inferred from each other), marks, concepts tested, and "Common Student Mistakes." **AS10's audit has two known gaps, clearly flagged inside the file itself: PYQ May 2026 (scanned PDF, no Ans doc exists) and ICAI-Practice Model Test Papers 6–8 were never audited.**
- `books/question-bank/metadata-index/topic-index.json` — a reusable index of ICAI base-material unit structure (currently has full/accurate numbered sub-topic breakdowns only for AS 2 and AS 10, built by directly reading each unit's source `.md`/`.pdf` — not guessed). Superseded in spirit by the newer `topic-keyword-index.json` planned in Phase 0 below, but still useful as-is.
- `_claude/skills/SKILL-question-bank-summary-making.md` — the accuracy-first methodology for auditing a chapter's questions across the question bank (source-of-truth locations, false-positive traps like FIFO-for-investments-vs-inventory, independent Q/Ans page verification rule, speed-vs-accuracy tradeoff handling, marks-aggregation rules). Load this before doing any further chapter audits.
- `books/question-bank/metadata-index/question-book-implementation-plan.md` — the actual build plan for turning these audits into a full **"Question Bank Book"**: one flowing per-chapter document (Q.N → metadata → question → answer → rubric → common mistakes), topic-ordered, with OP/PP duplicate-question linking and per-question time estimates. Read this file in full before doing any Question Bank Book work — it has the phase breakdown, tier assignments (Python / cheap model / Claude), ready-to-paste prompts for Phase 0 and Phase 1, and the Tesseract OCR install steps.
- `books/concept-book/syllabus-engine/data/0-ca-inter-adv-accounts-subtopics-marks-weightage.json` — pre-existing, NOT built this session, but central to the plan: canonical `M{module}-C{chapter}-U{unit}-T{topic}` IDs for all 36 units across the syllabus's 15 ICAI chapters. Confirmed by cross-checking against a direct read of the AS2/AS10 source units that its numbering is accurate.

**Key decisions made with Pranav this session (don't re-litigate these):**
- The "Question Bank Book" per chapter will have: Q.N sequence → metadata (MCQ-Direct/MCQ-Scenario/Descriptive, attempt, Q.No in that attempt, marks, estimated time = marks×1.8 min, topic tags in the `M-C-U-T` format, comprehensive-question flag for ≥3 distinct topic tags) → question → official answer → "Important Computational Steps" (rubric, author-inferred since ICAI doesn't publish official step-marks — will later drive AI-based grading of student answers, so this stays Claude-only, never delegated to a cheap model) → "Common Student Mistakes."
- Missing marks: apply an ICAI-typical default (2 marks is near-universal for MCQs) but always label it `"Author Guessed"`, never silently presented as ICAI's own figure.
- Duplicate/near-identical questions across attempts get an **OP** (original, earliest attempt) / **PP** ("Practice Perfect", later near-duplicates ≥95% text-similar after stripping numbers) tagging system — PP entries carry a pointer back to their OP.
- Ordering within a chapter's book follows the ICAI syllabus's own topic sequence, not the order questions happened to appear across exam attempts.
- Cost-control architecture (Pranav's framing, agreed): **Tier 1 fully deterministic → Python** (written by GitHub Copilot/Gemini in VS Code, not Claude); **Tier 2, 40–90% deterministic → cheap/free model** (Blackbox/Copilot/Gemini in VS Code, but the *prompt* is always authored by Claude); **Tier 3, creative/high-stakes/review → Claude directly**. OCR for scanned PDFs uses Tesseract (a dedicated tool), not an LLM at all.
- Phase 0 (building one single master `topic-keyword-index.json` covering all 36 units, so cross-chapter tagging for integrated questions works cleanly) runs **before** any further chapter's question extraction, in 3 batches by ICAI chapter number: **Batch 1 = Chapters 1–5 (17 units)**, **Batch 2 = Chapters 6–10 (13 units)**, **Batch 3 = Chapters 11–15 (6 units)** — note this split is workload-uneven (Batch 1 is ~3x Batch 3), which was flagged to Pranav and accepted as-is.

**Immediate next steps (in order):**
1. Build `books/question-bank/metadata-index/topic-keyword-index.json` for Batch 1 (Chapters 1–5) — the Phase 0 prompt is in `question-book-implementation-plan.md`, run once per unit via Gemini/Copilot, Claude reviews the drafts before merging (AS2/AS10 already have deep source familiarity from the audits, so those two units should be fast).
2. Once Phase 0 Batch 1 is done, Phase 1 (question+answer extraction) can start for the Batch 1 chapters — or, per Pranav's earlier framing, interleave so the AS2/AS10 book doesn't wait on all 17 Batch-1 units' keyword indexes to finish first (this specific interleaving question was raised but not yet finally answered — ask Pranav to confirm before assuming).
3. Separately, and lower priority: finish the two flagged AS10 audit gaps (PYQ May 2026, ICAI-Practice MTP 6–8) if a complete AS10 reference is needed before the Question Bank Book work reaches AS10.

---

## 2026-06-22 — CA Foundation strategy slides + HTML-to-PDF skill

Created `books/strategy-book/working/exam-strategyFoundation.html` (7-slide interactive dark-background presentation with beat-wise JS animation engine for CA Foundation Sep 2026 batch). Generated `exam-strategyFoundation-print.html` (static print copy, mm/pt sizing, all content visible) and `exam-strategyFoundation.pdf` (7 pages, 150 KB, A4 landscape) via Chrome headless.

Converted `books/concept-book/chapters/seq04-as02-valuation-of-inventories.html` to PDF (16 pages, 595 KB, A4 portrait). Added `print-color-adjust: exact` to source `*` rule; used Edge + `--virtual-time-budget=15000` because Chrome headless failed silently on Google Fonts.

Created `_claude/skills/SKILL-html-to-pdf.md` — full 8-section skill with two worked examples (slides vs. chapter), documenting the Chrome-vs-Edge decision, `--virtual-time-budget` flag, `--no-margins` usage, and the "no separate print file needed when source already has @media print" pattern.

---

## 2026-06-22 - Parsed question-bank pilot created

Created ooks/question-bank/Parsed_PDF_Question_Bank_CA_Inter_Accounts/ with one parsed MTP, one parsed RTP, one parsed PYQ, and a README. Outputs remain .md files with HTML table blocks for ruled accounting layouts. Ran python tools/health_check.py (17 pre-existing failures remain) and python tools/file_index.py (417 files indexed).

---

## 2026-06-22 - Question-bank markdown parseability sampling

Inspected ooks/question-bank/README.md, question_bank_index.csv, and sampled MTP/RTP/PYQ markdown files under ooks/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/. Confirmed raw OCR markdown is parseable with a custom rule-based parser, but needs cleanup rules for page numbers, table fragments, front-matter announcements, and embedded suggested answers in RTP files.

---

## 2026-06-22 - Orientation read: CLAUDE.md + project context reviewed

Read AGENTS.md, README.md, CLAUDE.md, and the _claude/memory/ context to understand the cap-online ecosystem. Ran python tools/health_check.py; it reported existing missing expected folders, NUL-byte text files in bridge-course/question-bank sources, and undocumented top-level capranav_com/. No content files changed beyond this log note.

---

## 2026-06-19 — AS02.dc.html animation: 4 fixes applied + local React bundled

Applied all 4 agreed fixes to `books/concept-book/characters/animations/AS02.dc.html`:

1. **Narrator position**: `top:332` → `bottom:90` (subtitle band, no longer overlaps characters)
2. **Pranav walk animation**: Added `asEnter` keyframe (slide in from right); changed his Scene 4 beat pose from `'walk'` (bounce) to `'enter'`
3. **Jump-to-scene menu**: `≡` button top-left opens an overlay listing all 12 scenes; click to jump; ESC or click-away to close; click-to-advance blocked while menu is open
4. **Local React**: Downloaded React 18.3.1 UMD as `react.min.js` + `react-dom.min.js` into animations folder; added `<script>` tags before `support.js` in all 3 `.dc.html` files (AS02, universe-intro, Character Universe) — zero CDN dependency at runtime

All changes committed locally. Pranav to `git push origin main` from his machine.

---

## 2026-06-17 — AS 2 Concept Book chapter: HTML print version complete

Created `books/concept-book/chapters/seq04-as02-valuation-of-inventories.html` — print-ready A4 HTML for the AS 2 Concept Book chapter. Self-contained file (Google Fonts CDN, all CSS inline).

Design: 7 pages — (1) cover (navy gradient, watermark AS2, gold-orange accent bar, badges), (2) story "Godown Ka Hisaab", (3–5) Layer 2 concept notes [AS2-1.2] to [AS2-1.15], (6) Illustration Guide, (7) TYK Guide + Layer 3. Color system: Story = orange border on warm cream; Kaam Ki Baat = green border on mint; Story Reference = purple border on lavender; Exam Note = red border on light red; Layer 3 = dark navy background with orange numbered circles. Print: @page A4, position:fixed header/footer repeating on each printed page. Fonts: Poppins (headings/badges), Merriweather (story prose), Lato (body).

All 4 Kaam Ki Baat boxes, 3 Story References, and Exam Notes from the MD chapter are fully reproduced in the HTML.

---

## 2026-06-17 — final-deliverables: 02A and 03A light versions created

Continuation session (context exhausted in previous turn). Tasks from previous session pending were:

1. `final-deliverables/02A-batch-day-wise-planner-light.md` — lighter version of 02. Stripped Kahaani/Koncept/Karma narrative from Day Focus column; removed Notes column. Kept all 97 rows, 6 phase headers, chapter tests, ITD tests, holiday markers. Day Focus is now just topic/subtopic name (e.g. "Why AS exist; ASB formation; 8-step standard setting; benefits and limitations"). Phase summary table retained at bottom.

2. `final-deliverables/03A-bridge-course-skeleton-light.md` — lighter version of 03. Removed all Kahaani narration (story beats, dialogues, Arjun/bus scenes). Kept: time budget tables for both sessions, Kahaani slot with just the anchor concept (blood report metaphor / why rules exist), full Koncept topic list in sequence, all Karma items (MCQ topics + illustration details), Layer 3 one-liners, vision close content list. 1.5 hrs × 2 session format maintained.

3. `final-deliverables/` folder documented in CLAUDE.md section 3 and README.md (folder map + Where things are table). This was overdue from when the folder was created last session.

4. `file_index.py` run: 326 files. `generate_component_index.py` run (regenerated). `health_check.py`: 22 pre-existing failures — 12 missing gitignored/local folders, 9 NUL-byte OCR files from last session's base-studymaterials, 1 component-index CRLF/LF hash mismatch (systematic tooling bug — generator hashes text, health_check hashes raw bytes on Windows). No new failures from this session's work.

---

## 2026-06-15 — teaching_sequence.md: ALL 10 chapters complete

Multi-session task concluded. Built `books/bridge-course/teaching_sequence.md` — 7-column table (CA Level | Chapter No. | Unit No. + Unit Name | Topic/SubTopic ID | Topic Name | Page No. | One-Line Summary) from all 10 base-studymaterial OCR files.

This session (continuation): CA Inter Chapter 2 (24 rows) + CA Inter Chapter 3 (9 rows) appended.

- Ch3 sections: 1 (Status of AS), 2 (Applicability intro), 2.1 (MSME/Large criteria, effective 1 Apr 2024), 2.1-Illus (Example 1), 2.3 (Companies), 2.3.1 (20 AS in entirety), 2.3.2 (SMC exemptions), UNTSMRY, TYK (ranking: 2.1 \ 1)
- Full file: header + Foundation Units 1–7 + Inter Ch1 (16 rows) + Inter Ch2 (24 rows) + Inter Ch3 (9 rows)
- `file_index.py` run (116 files); `health_check.py` 15 pre-existing failures only (same as before — not caused by this work)

---

## 2026-06-15 — Bridge Course Topics to cover.md — full final rewrite completed

Continuation session (prior context was exhausted mid-task). Wrote the complete final version of `books/bridge-course/Topics to cover.md` covering ALL source chapters:
- Foundation Ch1 Units 1–7: every numbered sub-topic, all illustrations with concept-test note, Summary, TYK with sub-topic IDs
- Inter Ch1 (Intro to AS): all 14 sections including 8-step process, IFRS components, carve outs/ins, Ind AS roadmap for all 4 entity categories
- Inter Ch2 (Framework): all 11 sections — 8 elements of the Framework, 7 user groups, 3 fundamental assumptions, 4 qualitative characteristics + sub-qualities, 5 elements (formal definitions), 4 measurement bases, all 3 capital maintenance concepts; all illustrations/examples with concept-test notes
- Inter Ch3 (Applicability): Status, 3-question test, ICDS (10 standards), MSME vs Large entity revised criteria (Aug 2024), SMC vs Non-SMC exemptions; all MCQs with sub-topic IDs, case scenarios
- Ran `file_index.py` (116 files); `health_check.py` shows 15 pre-existing failures only (no new issues)

---

## 2026-06-15 — Bridge Course Layer 2 revision map written

Created `books/bridge-course/Topics to cover.md` — point-wise, topic-wise raw concept summary of all source chapters:

- **CA Foundation Ch1 Units 1, 2, 5, 6, 7:** 6-step accounting cycle, evolution (Egypt → Pacioli), objectives, functions, book-keeping vs accounting, sub-fields, users, disciplines; all 12 GAAPs with key pointer each; 3 Fundamental Assumptions; Accounting Policies (selection + change); 4 Valuation Bases + Accounting Estimates; AS objectives, benefits, limitations, ASB process (8 steps), 3 sets of standards, AS 1-29 full list, key Ind AS list
- **CA Inter Ch1:** GAAP at Inter depth, IFRS/IASB, Convergence vs Adoption, Ind AS, Carve-outs, Phase-wise Roadmap
- **CA Inter Ch2:** Framework (objectives, users, 4 qualitative characteristics with sub-qualities), 5 elements with formal definitions, 2 recognition criteria, 4 measurement bases, Financial vs Physical Capital Maintenance
- **CA Inter Ch3:** Status of AS, 3-question applicability test, Companies Act Sec 129/133/143, non-corporate applicability, CA's professional responsibility
- Purpose: "Layer 2 skeleton" — Pranav Sir will insert story anchors and concept teaching between these raw topics
- `file_index.py` run (116 files: 106 text, 10 local); `health_check.py` has 15 pre-existing failures (9 NUL-byte files in base-studymaterials, 5 missing gitignored folders, component-index stale) — none caused by today's work

---

## 2026-06-15 — Bridge Course master teaching document complete

Rewrote `books/bridge-course/bridge-story.md` into a full structured teaching guide:

- **3-class × 1-hour structure** with story, chapter maps, cliffhangers
- **Class 1 (Foundation):** Going Concern, Money Measurement, Matching, Consistency, Conservatism, Materiality, Accounting Policies, Valuation Bases, Why AS exist — all with blood-report / Byju's / Arjun story thread
- **Class 2 (Inter Ch 1):** GAAP, AS-setting process (ASB), IFRS/IASB, Convergence vs Adoption, Ind AS, Carve-outs, Roadmap
- **Class 3 (Inter Ch 2 + 3):** Framework (4 qualitative characteristics), Elements (formal definitions), Recognition criteria, Capital Maintenance, 3-Question Test, Companies Act Sec 129/133/143, CA's responsibility
- Every class ends with a story cliffhanger except Class 3 (which is a resolution)
- AI fear not resolved — one paragraph: focus on studies, conversation for later
- Ran `file_index.py` (updated); `generate_component_index.py` (regenerated)
- `health_check.py` has 13 pre-existing failures (NUL bytes in base-studymaterials files from cross-mount edit, 5 missing gitignored folders, component-index stale) — none caused by today's work

---

## 2026-06-14 — Bridge course story written

Created `books/bridge-course/bridge-story.md` — a Chapter 0-style Hinglish dialogue story bridging CA Foundation → CA Inter. Same characters (Arjun + Pranav Bhaiya), same narrative style. Covers:

- Foundation concept recap (Entity, Dual Aspect, Accrual, Matching, Going Concern, Consistency, Conservatism)
- Why Accounting Standards exist (the 5-accountants-5-profits problem)
- What Accounting Standards are and how ICAI formulates them
- AS vs Ind AS vs IFRS — India's convergence journey
- Framework for financial statements (Reliable, Relevant, Comparable, Understandable)

Setting: Arjun receives his Foundation result (passed), calls Pranav Bhaiya, conversation bridges him into the Inter level. Content is ICAI curriculum-accurate throughout.

---

## 2026-06-13 — Working tree cleanup: 4-block atomic commit plan completed

Resumed from previous context (session ran out). Committed remaining 2 blocks:

- **Block 3** (`a6b3e18`): CLAUDE.md + content/README.md — documented `productions/` folder in both files
- **Block 4** (this entry): file-index regeneration + project log

**Sep26-strategy relocation** (done in prior session, committed as Block 1):
All 14 old paths under `books/strategy-book/video-presentations/sep26-strategy/` moved to `content/productions/sep26-strategy/deck/`. Git detected renames correctly.

**Pending decision (Pranav):** `content/assets/green-screen/book-cover-image-base-64.txt` — 573KB base64-encoded PNG. Used by `book-promo.html` for self-containment. Per "no binary files in git" rule, recommend adding to `.gitignore`. If Pranav wants it committed, can do so explicitly.

**Pending tasks:**
- Add `--input` flag to `tools/strategy_book_parser.py` so it can process `CA-Inter-90-Days-Strategy.md` (currently defaults to MASTER.md only)
- Generate 90-day book HTML → PDF once `--input` flag added

---

## 2026-06-11 — AI section expanded + parser table support added

**MASTER.md — THE AI SECTION:** Added 3 new sub-sections after the existing 7 use-cases:
- **TOOL PICKER** — markdown table: 10 rows mapping task → best tool → why (NotebookLM, Claude, Perplexity, ChatGPT, Sarvam/Gemini, KIMI)
- **OUTPUT FORMAT** — HTML vs MD vs PDF guidance with ready-to-use prompts; explains token cost of scanned PDFs
- **TOKEN MINIMIZATION** — 6 numbered habits for free-plan users + PRANAV'S TIP (compact MD summary habit)

**Parser (`tools/strategy_book_parser.py`) — markdown table support added:**
- Tokenizer: detects `|`-prefixed lines, parses header/separator/data rows → `{'type': 'table'}` token
- Renderer: `_table()` method → `<table class="content-table">` with thead/tbody
- `_component_body()`: table token wired in (tables inside components work too)
- CSS: `.content-table` / `.table-wrap` — zebra-striped, uppercase headers, border-collapse

Verified: parser renders AI section cleanly; all 7 checks pass (content-table, NotebookLM, headings, HOW TO DO THIS, PRANAV'S TIP, handwritten class, file size 20KB). health_check green (47/47, MD5: 5805c527).

---

## 2026-06-11 — CA-Inter-90-Days-Strategy.md fully rewritten, HTML-synced

Complete rewrite of `books/strategy-book/working/CA-Inter-90-Days-Strategy.md`.
Now fully in sync with the sep26-strategy HTML slide deck and standalone as an
independent book.

**Structure:** FRONT MATTER (Title, Copyright, Dedication, Socrates Story, About
the Author, About This Book, How to Read) → ROUTING PAGE → BUCKET 3 (Phase 1:
Build Your Arsenal, 18 strategies) → BUCKET 4 (Phase 2: Delivery Mode, 10
strategies) → BUCKET 5 (The 15 Days, 17 strategies) → BUCKET 0 (Daily
Foundation, 13 strategies + Discipline Bridge) → PERSONAL PAGES → AUTHOR'S STORY.

**Sync gaps closed vs slides:**
- Booti 3: "Paste It Where You Live" → "The Visual Vault" (Flowcharts / Tables
  & Formats / Skeletons / Dates·Rates·Limits / Mnemonics); paste-it is now the
  usage rule, not the name
- Level 1 gate: 3-check system (Boundary written + Layer 1&2 documented + 3
  Bootis) → LEVEL 1 CLEARED → NO NEW MATERIAL
- Mock Analysis Protocol: routing decision tree (recall-fail → Visual Vault;
  didn't-know-in-Boundary → Golden Nuggets; outside Boundary → decide)
- Discipline Bridge: before Bucket 0 — "CA is game of PREPARATION not talent"
  + Atomic Habits framing
- Student Toolkit promise (20+ tools, comment guarantee)
- "ON GROUND Strategies" / "No Gyaan Baazi" language in About This Book
- North Star escalates to 3× per day in Bucket 4
- Layer 3 size: "10–40 pages per subject"
- Gamify frame: Level 1 / Final Boss (tied to Level 1 CLEARED milestone)

**Parser compliance:** Section headings map to existing SECTION_META keys
(BUCKET 3/4/5/0, FRONT MATTER, ROUTING PAGE, PERSONAL PAGES). 58 strategy
headings. 48 component markers. Health check clean.

**Stats:** ~1520 lines. Gallery skipped (per Pranav). About Author added.

---

## 2026-06-11 — Book-promo silent slide (book-promo.html) + CTA bug confirmed fixed

- **CTA stray `</div>` bug**: confirmed already fixed on disk (Pranav's edit); his local `node --check slides-part4.js` passes. Deck is now **29 slides** — Pranav added Mock Analysis Protocol (24B), Discipline Bridge (24C), and a Manifest line on the CTA; deck README still says 27 (update pending).
- **New: `books/strategy-book/video-presentations/sep26-strategy/book-promo.html`** — standalone silent promo slide for the Complete Strategy Book PDF (end of Sep-26 video, no voiceover). Floating 3D A4 book cover (dark, brand blue/green edge, gold accents, shine sweep, float + floor-shadow animation) with Pranav's photo **chroma-keyed from green-screen** (`content/assets/green-screen/Book-cover-green.png` → transparent cutout, embedded base64 — file ~386 KB, fully self-contained). Right panel: LAUNCHING SOON badge, facts (90+ strategies, **20+ frameworks** — actual count 23, Pranav chose the safe number, 30+ Pranav's Tips, 7 buckets, 3 Bootis, 17 exam-day strategies, fill-in pages), CTA "For **Jan 27 & May 27** attempts" (Pranav confirmed; original brief said Jan 26) + PRE-BOOK NOW / Early Bird / UP TO 30% OFF / link in description. 1920×1080 stage, auto-scales to window.
- **Note**: the base64-embedded image makes this HTML a ~386 KB blob in git — Pranav to decide: commit as-is or gitignore it.
- Sandbox health_check: known stale-mount false flags (slides.js, parser, video-brief) + **component-index STALE (MASTER.md changed: 86bb07d8 → efdc37ad)** — Pranav to run `python tools/generate_component_index.py` + health_check locally. file_index regenerated (200 files).

## 2026-06-09 — reconcile Pranav's edits + new spaces (Session: setup, cont.)

- Confirmed Pranav's build-out: strategy-book `sources/ design/ working/ video-presentations/`, new tools (`generate_component_index.py`, `strategy_book_parser.py`), component-index MD5 check in health_check, segment-library + standup material in `preparations/`, all motivation images moved to `obs-setup/assets/` (content/motivation now a daily-quote media library, kept).
- Fixed typo `sources/extermal` → `sources/external`; added `.txt` to Report 4 & 5 (external strategy research from YouTube etc.).
- New top-level **`student-toolkit/`** (separate from telegram bots) — moved `Exam Preparation date calculator.xlsx` there.
- Dedupe: removed 6 redundant strategy copies from `_claude/` (book is single source of truth); concept-book material stays in `_claude/` until it gets its own home.
- Placed syllabus master `CA-Inter-Adv-Accounts-Syllabus-TEACHER-COPY.xlsx` → `syllabus-engine/data/` (4 sheets: chapter categorize, topics+subtopics w/ unique topic IDs, combined syllabus, ICAI topics).
- Registered `student-toolkit` in CLAUDE.md + health_check EXPECTED_DIRS.
- health_check encoding guard flagged sandbox-corrupted reads of `strategy_book_parser.py` (NULs) and `slides.js` (truncated) — disk copies intact; commit from Pranav's machine. Component-index stale → run `generate_component_index.py`.

## 2026-06-11 — Deck: Mock Analysis Protocol + Discipline bridge slides (Pranav's 2nd pass)

- **New slide "Mock Analysis Protocol"** (after Mock Window): analysis TURANT mock ke baad (khud ya siblings/friend se checkwao) + routing — knew-but-no-recall → Visual Vault · didn't-know-but-in-Boundary → Golden Nuggets · chapter-not-in-Boundary → decide; if added → must also go in Layer 3 + revision material.
- **New slide "Discipline bridge"** (cushion before Bucket 0, was abrupt): "Tough? Impossible?" → "CA is a game of PREPARATION, not talent" → discipline ≠ quick motivation / week's josh / Monday flame → unwavering commitment → ATOMIC HABITS, 21 din = habit, "buffer aaj bhi hai. Go."
- Deck now 29 slides. Fixed stray `</div>` in CTA (from Pranav's manual edit; wording kept). Pranav's wording edits this pass retained: "This entire PPT discussion — FREE PDF", manifest line, "Exam ke 15 days ki strategy".
- Clarified for Pranav: "Error Register ka ek full pass" = one complete start-to-finish sweep of every logged error before exams.
- Commit still Pranav-side (sandbox stale-view issue).

---

## 2026-06-11 — Deck review tweaks (Pranav's pass) + commit deferred to Pranav

- Pranav reviewed full deck. Changes: visible **"↺ RESET" button** on Subject Slider Board (R key kept as backup); **Booti 3 renamed "The Visual Vault"** (Pranav picked from options) — contents now Flowcharts / Tables & Formats / Skeletons / Dates·Rates·Limits / Mnemonics, paste-it-where-you-live kept as the usage rule; AI slide synced ("printable visual sheets — Visual Vault ke liye"); **15 JULY slide now gates LEVEL 1 CLEARED on 3 checks** — Boundary written (har subject/chapter) + Anchor Material & Layer 1–2 ready/documented (physical ya digital) + 3 Bootis — then "Tab — aur sirf tab — LEVEL 1 CLEARED".
- Pranav edits this session: "ON GROUND Strategies" wording, Layer 3 "Around 10-40 pages", toolkit line "This is where I'll help".
- **OPEN: Booti 3 rename in `CA-Inter-90-Days-Strategy.md`** (book still says "Paste It Where You Live") — Pranav to decide.
- **Git: NOT committed from sandbox** — sandbox mount serves stale/truncated views of files edited this session; a sandbox commit would store corrupted blobs. Pranav commits from his machine (`git add -A && git commit`). His local health_check is the authoritative check this session.

## 2026-06-11 — Fixes: .handwritten class + 90-day book AUTHOR SAYS rename + MASTER trailing space

**Fix 1:** `tools/strategy_book_parser.py` PRANAV'S TIP renderer — `comp-body` → `comp-body handwritten` (`.handwritten` CSS was orphaned after AUTHOR SAYS removal; this wires it back in).
**Fix 2:** `CA-Inter-90-Days-Strategy.md` — all 10 `> **AUTHOR SAYS:**` → `> **PRANAV'S TIP:**` (90-day guide had not been updated in the earlier rename pass).
**Cleanup:** MASTER.md line 1 trailing space (test artifact from staleness-test) removed. Component index regenerated (clean MD5: `86bb07d8`). All health checks green (46/46, encodings OK, index in sync).

---

## 2026-06-11 — AUTHOR SAYS → PRANAV'S TIP rename + component index automation

**MASTER.md:** All 30 occurrences of `> **AUTHOR SAYS:**` renamed to `> **PRANAV'S TIP:**` (branding — student reads Pranav's name on every tip block). PT total now 33 (30 former AS + 3 original PT), IF = 22.

**Reference code system designed and implemented:**
- `ASG.B.S` = All Strategy, Bucket B, strategy S (e.g., `ASG.0.4` = Move Your Body)
- `RSG.B.S` = Rank Strategy (e.g., `RSG.3.11` = Rate Your Chapters; only 2 RANK strategies exist, both in B3)
- `IF.B.S` / `PT.B.S` = component inside that strategy
- Bucket 6 → `6A` (Track A, passed) and `6B` (Track B, failed/retaking)
- Emergency → `E`

**New tool: `tools/generate_component_index.py`** — auto-generates MASTER-component-index.md from MASTER.md. Writes MD5 of MASTER.md into index header. Run after any MASTER.md edit.

**health_check.py updated:** Check 5 added — compares stored MD5 in index to current MASTER.md; fails with regeneration instructions if stale.

**strategy_book_parser.py updated:** Removed `AUTHOR SAYS` from COMPONENT_MARKERS; `PRANAV'S TIP` handler (`.pran-tip` CSS class) already existed and handles all PT blocks.

All checks green (46/46 folders, encodings clean, component index in sync, MD5: `86bb07d8`).

---

## 2026-06-11 — Sep-26 video slide deck COMPLETE: all 27 slides (Phases 1–4)

- Major restructure per Pranav after first-3-slides review: **15th July** (not 25th) = B4 start/Level-Up/No-New-Material date (Pranav's buffer choice; exact 45-days-before-1-Sep is 18 Jul — flagged, he chose 15th; slides say "45+ days"). Exams 1–12 Sep. Bilingual headings everywhere (EN + Devanagari). Brand chrome = DISC blue/green; bucket colours from design-spec; gold = Bootis only.
- **Phase 1**: slide chrome in engine (bilingual header + live days chip, footer journey strip w/ proportional buckets + B0 band, watermark "CA Pranav P Tulshyan"), Gita Shlok opener (2.47), Reality Check title, Bucket Analysis proportional timeline (B1 8% / B2 34% / B3 22% / B4 16% / B5 7% / B6 13%; markers AAJ · 15 JULY pulsing · 1 SEP · 12 SEP; B0 band beneath). Approved by Pranav.
- **Phases 2–4** (new files, additive architecture): `js/slides-part2/3/4.js` (SLIDES.push), `js/engine-extras.js`, `css/parts.css`. Slides: interactive **Subject Slider Board** (6 draggable markers on bucket-gradient tracks, B4 goal line at 64%, LEVEL 1 CLEARED badge when all ≥ B4, R = reset, tap-to-jump), Mission (live days-to-15-July), Roadmap TOC, North Star (21 hours, 1×/day), Boundary + 3-question filter + NOTHING ELSE stamp, **Implementation Framework + STUDENT TOOLKIT badge** (20+ tools, comment promise), 3-Layer Architecture (fixes layers-before-explained hiccup), Drive setup, Physical vs Digital (red flash), Booti intro + 3 Booti slides (gold, field-by-field; footer booti-tracker slots fill ①②③), AI (violet, memory-machine framing), Group Decision (comfort-first formula), 15 JULY deadline (LEVEL 1 CLEARED + NO NEW MATERIAL flash), Bucket 4 rules (North Star 3×/day), Layer 3 A/B/C (60/30/10), Mock Window (min 1/max 2, deadline live-computed = exam−10 = 22 AUG), Bucket 0 tick-list, CTA ("No Gyaan Baazi. ON GROUND Strategies." — Pranav's wording).
- Verified: node --check all new JS, 27 slides, all step sequences sequential, mock date computes 22 AUG. **Known sandbox issue:** the Cowork sandbox mount pins stale sizes for re-written files (slides.js etc.) → health_check run in-sandbox false-flags UTF-8 on them; files verified complete/valid on Windows side and Pranav's local health_check runs green. New-file architecture (part files) chosen partly for this reason.
- README (deck) updated: full file map, R key, wording-edit guide. Commit locally; Pranav pushes.

---

## 2026-06-11 — Sep-26 video slide deck: engine + first 3 slides

- New folder `books/strategy-book/video-presentations/sep26-strategy/` — HTML/CSS/JS deck for the Sep-26 strategy video (per `working/video-brief-sep26-strategy.md`). Multi-file: `index.html`, `css/theme.css` (B3 #E8A13D / B4 #E07A2F tokens, dark/light themes, 1920×1080 scaled stage, reveal animations), `css/slides.css`, `js/engine.js` (vanilla-JS: →/Space/click step reveals, ←, F fullscreen, H HUD), `js/slides.js` (content-as-data, edit text without touching engine), `README.md`.
- Built slides 1–3 for Pranav's look-and-feel approval: Hook ("83 days" — **live-computed** from EXAM_DATE 2026-09-01), Pain Mirror (NEW slide approved by Pranav — 4 Hinglish pain lines + closer), Positioning ("Yeh video kya NAHI hai"). 15 slides remain (18 total).
- Decisions locked with Pranav: pain-mirror slide added; days counter auto-calculated; folder location under strategy-book. **Slide 4 redesigned per Pranav**: timeline Today → 25th July → 1st Sep; first half = fix boundary + finalize 3 Bootis, second half = pure revision & practice (to build next).
- `books/strategy-book/README.md` updated (video-presentations/ in layout + file table). Verified: node --check clean, 3 slides / 12 reveal steps, days calc = 83. health_check green (46/46); file_index 91 files. Commit locally; Pranav pushes.

---

## 2026-06-10 — Staleness check + component index corrected

Checked 6 files for staleness and contradictions: CLAUDE.md (current), README.md (current), content/README.md (current), project_log.md (current), MASTER-component-index.md (stale — fixed), CA-Inter-Book-Full-Structure.md (superseded — marked archived).

**MASTER-component-index.md corrections:**
- Added `IF = IMPLEMENTATION FRAMEWORK` to key + IF column to per-section table (B0:3, B1:2, B2:6, B3:4, B4:3, B5:3, B6:1 = 22 content blocks)
- AS counts corrected: B0 6→7, B2 9→10, B3 5→6, B4 0→2, B5 2→3 (total 20→30)
- WA counts corrected: B1 2→1, B2 1→0 (total 1 WARNING at B1 S10)
- B3 tag notation corrected: "10×[ALL], 1×[RANK], 1×[ALL], 1×[RANK]" → "11×[ALL], 2×[RANK]"
- PRANAV'S TIP corrected: 4→3 (B1 S6, B1 S10, B4 S1)
- Total strategies corrected: 94→91; [ALL] 90→89; [RANK] 4→2 (B3 S11, B3 S13)

**CA-Inter-Book-Full-Structure.md:** Added ARCHIVED DRAFT header — this file diverged from MASTER.md before the 2026-06-10 normalization pass. It is reference-only; all active work is in MASTER.md.

---

## 2026-06-10 — New file: CA-Inter-90-Days-Strategy.md (website PDF mini-book)

Created `books/strategy-book/working/CA-Inter-90-Days-Strategy.md` — complete standalone 90-day strategy book for the website PDF. Parser-compatible with `tools/strategy_book_parser.py`.

Structure: Socrates Story (STRUCTURE ONLY) → About This Book (STRUCTURE ONLY) → Routing Page → First 45 Days (Strategies 1–17: boundary, Physical vs Digital, 3 Layers, 3 Sanjeevani Bootis, revision strategies) → Next 45 Days (Strategies 1–10: Layer 3 build, No New Material, mocks, error register) → Exam: The 15 Days (Strategies 1–17: kit/logistics, reading time, hall mechanics, between-papers) → Bucket 0 — The Daily Foundation (all 13 strategies, at end) → Personal Pages (Why I Am Doing CA, Dream Marksheet, Vision Board, My Boundary, My Notes) → Author's Journey + Gallery (STRUCTURE ONLY).

Key: "21 Hours Before Exam" throughout · PRANAV'S TIP components included in Physical vs Digital and Layer 2/Layer 3 strategies · cross-refs to MASTER.md noted via [REF: …] tags · parser note at end flagging new SECTION_META slugs required (FIRST 45 DAYS, NEXT 45 DAYS, EXAM: THE 15 DAYS, THE SOCRATES STORY).

health_check green (46/46); file_index 85 files.

---

## 2026-06-10 — MASTER.md: 23 Implementation Frameworks added across all 7 Buckets

Major session — comprehensive framework layer added to the Strategy Book:

- **New parser tag `IMPLEMENTATION FRAMEWORK`** added to file header (front-cover countable element).
- **About This Book** updated: added differentiator line about implementation plans for each strategy.
- **Bucket 0**: Wake Anchor Rule (sleep), 2-Minute Park Protocol (emotions + "scientifically proven" note without names), 4-Part Target Rule (daily targets).
- **Bucket 1**: Full 2-Role Rule rewrite in Pranav's plain-language style (Understanding vs Boundary); A/B/C Classification Formula (W = avg marks, ≥5=A, ≥2=B, else C) with VC Gurukul channel reference; 3-Condition Removal Rule for boundary.
- **Bucket 2**: Layer Lock Rule (zero Layer 2 during classes); 3-Question Class Filter (what to write); 25-5 Rhythm (active recall — no scientist names); 3-Item Buddy Agenda (study buddy calls); full Sanjeevani Booti 2 Error Register format (3 entry types + 5-field error format); MCQ Quota by Category (30/15/8 with VC Gurukul platform reference).
- **Bucket 3**: Compression Time Test (Layer 2 quality check); 3-Gate Revision Standard (Notes + Test + Error); Author Says on 7-subject IPCC spacing; 3-Day Triage Protocol (recovery); Action Matrix (chapter rating → action trigger).
- **Bucket 4**: 4-Type Layer 3 Filter (only 4 content types allowed); Author Says on mnemonic pairing (Audit disaster story); Layer 3 reading time updated to 30–40 min; Decision Tree (new material vs boundary gap); Mock Sequence Rule + Author Says (sister checking immediately).
- **Bucket 5**: 4-Step Reading Time Protocol (15-min sequence); MCQ-first rationale rewritten in Pranav's style + Author Says (watch on desk); Every-5 OMR cross-check; 4-Line Fallback Protocol (never leave blank); CA Inter Time Budget (1.8 min/mark table).
- **Between Papers**: COMPLETELY REWRITTEN — Pranav's 20–22 hr study approach: 2 hrs same day + 16 hrs next day + 4 hrs exam morning. Remove completed subject materials immediately after exam.
- **Bucket 6**: 3-Column Look-Back Table (honest review after exams).
- Memory saved: `project_ca_inter_basics.md` + `feedback_ca_inter_book_rules.md`.
- Total: 23 IMPLEMENTATION FRAMEWORK blocks, 30 AUTHOR SAYS blocks, 91 strategies.
- health_check green (46/46); file_index 84 files.

---

## 2026-06-10 — MASTER.md: 7 new concepts added + PRANAV'S TIP parser component

- Added **Strategy 13 — Make It a Game** to Bucket 0 (gamify concept: learning as levels, exam as Final Boss, Princess ko bachana hai).
- Added **PRANAV'S TIP for Google Drive subfolder structure** to B1 S6 (Layer 1 / Layer 2 / Layer 3 subfolders per subject).
- Added **Strategy 10 — Physical vs Digital** to Bucket 1: what must be physical (Layer 3 always physical), what is digital, WARNING for never-digital-as-primary, PRANAV'S TIP for cloud backup + YouTube Unlisted for heavy files.
- Enhanced **Error Register format** in B2 S15 with new PRANAV'S TIP block (5 specific fields: where is Q, where is solution, what was asked, where messed up, why messed up).
- Added **Strategy 18 — The Golden Nuggets Register** to Bucket 2 (distinct from Error Register; collects per-chapter: important concepts + exam tips + examiner tricks while watching revision videos).
- Added **North Star Question framing** ("21 Hours Before Exam") to Bucket 4 intro, before Strategy 1.
- Added **Layer 3 default A→B→C sequence** as PRANAV'S TIP inside B4 Strategy 1 Build Layer 3.
- Added **PRANAV'S TIP** to `COMPONENT_MARKERS` in `tools/strategy_book_parser.py` + renderer + CSS class `.pran-tip`.
- Updated `MASTER-component-index.md`: new key PT, updated strategy counts (B0:13, B1:10, B2:18), added new strategy rows.
- health_check green (46/46); file_index 83 files.

---

## 2026-06-10 — Video planning: Sep 2026 strategy video brief

- Planning discussion for a YouTube video targeting CA Inter Sep 2026 students ("exactly what to do in the next 40 days").
- Decided format: face-to-camera primary, slides only for data-heavy blocks (timelines, templates, checklists).
- Content scope: Bucket 3-to-4 transition. Core: Boundary fixation, 3-Layer material framework, three "Sanjeevani Bootis" (Golden Nuggets register, Error Register, Paste-It-Where-You-Live), AI usage for memory, post-25th-July phase. Bucket 0 compressed to 90 seconds at end. Bucket 5 deferred to separate video.
- Positioning: "Big Brother, not topper, not faculty" — no planners, no motivation, raw strategies only.
- Created `books/strategy-book/working/video-brief-sep26-strategy.md` — full run-of-show + 6 critical flags + open decisions table for Pranav.
- health_check green (46/46); file_index 83 files.

---

## 2026-06-10 — Strategy Book: md_to_html.py converter + Bucket 0 HTML output

- Built `books/strategy-book/design/templates/md_to_html.py` — state-machine line-by-line parser that converts MASTER.md → print-ready B5 HTML implementing design-spec.md visual system. Self-contained CSS (Archivo/Source Sans 3/Kalam, Google Fonts), embedded in output HTML.
- Handles all 10 component types (AUTHOR SAYS, HOW TO DO THIS, RANK ONLY, END GOAL, STARTING LATE? BARE MINIMUM, WARNING, DIAGRAM, FILL-IN, CHECKLIST — END OF BUCKET, EXAMPLE), strategy headings (number circle + title + ALL/RANK badge), non-strategy H3s, code/template blocks, checklists (`- [ ]` + ★), anonymous blockquotes, inline REF/STRUCTURE ONLY/AUTHOR TO CONFIRM tags.
- Generated `books/strategy-book/design/templates/build/bucket-0.html` (B5 Slate theme, 26KB, 564 lines). Component counts verified against MASTER-component-index: 5 Author Says, 3 HOW TO, 1 RANK ONLY, 1 DIAGRAM, 12 strategy headings. `build/` is gitignored per existing .gitignore rule.
- Known limitation: indented continuation lines of list items (e.g., `>   move on...` below a `> - list item`) are rendered as a separate `<p>` rather than joined to the list item. Text content is preserved; only visual grouping differs.
- CLI flags: `--section "BUCKET 0"`, `--section all`, `--list-sections`, `--output <path>`.
- health_check green (46/46); file_index regenerated (76 files). Commit locally; Pranav pushes.

---

## 2026-06-10 — Strategy Book MASTER: formatting normalization pass + component index

- **Normalization pass** on `books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md` (FORMATTING ONLY — zero content/wording changed). Objective: make every recurring component machine-parseable for the HTML build pipeline.
- Key changes made (counts): 20 AUTHOR SAYS → blockquotes · 12 HOW TO DO THIS → blockquotes (inline variants had text moved below marker) · 4 STARTING LATE? BARE MINIMUM → convention-compliant blockquotes · 6 END GOAL → blockquotes with `- [ ]` checkbox items (replacing □ in code blocks) · 8 RANK ONLY → blockquotes (inline ★ [RANK] within [ALL] strategies) · 2 DIAGRAM markers added (Routing Flowchart, Posture & Eye Exercise) · 5 FILL-IN markers added in Personal Pages section.
- **Heading fixes:** `# ROUTING PAGE — WHERE ARE YOU...` split into H1 + H2 · `### Priorities from today...` and `### Your Bucket 0 Daily Tick` and `### Understand this before any class strategy.` all converted to ALL-CAPS non-strategy H3 (no tag) · All Bucket 5 and Bucket 6 `**Strategy N — ...**` bold headings promoted to `### Strategy N — ...` with `---` after each · Added missing `---` after Bucket 2 Strategies 6, 7, 8.
- **Created** `books/strategy-book/working/MASTER-component-index.md` — per-section table, global summary (88 strategies total: 84 × [ALL], 4 × [RANK]), FILL-IN inventory, DIAGRAM inventory, 10 NEEDS HUMAN DECISION items, 3 UNTAGGED recurring patterns (code-fenced structured content, inline REF tags, STRUCTURE ONLY blocks).
- health_check green (46/46); file_index regenerated (74 files). Commit locally; Pranav pushes.

---

## 2026-06-10 — Strategy Book: subject-wise routing, repeat-attempt check, tick-list end-goals

- MASTER edits (`working/CA-Inter-Strategy-Book-MASTER.md`): Routing page now leads with the **subject-by-subject** principle (run buckets per subject, even for both-groups students) + a **repeat/multiple-attempt self-check** (per subject: 70%+ → Bucket 3, 50–70% → Bucket 2, <50% → fresh start Bucket 1/0).
- **All bucket "End Goals" converted to tick-lists** (□/★); folded the old separate end-of-bucket checklists in (one checklist per bucket). **Bucket 0** got a **Daily Tick** habit-tracker instead. Bucket 1 list includes a **FIXED (not new) single Gmail + phone number** for all study/digital activity.
- Bucket 0 also: "better late than never" line + Indian pure-veg budget diet examples. Voice kept to the Raj-Shamani/older-brother spec throughout.
- **Consistency pass:** reconciled `sources/summary-strategy-book-memory.md` — fixed the two stale lines (separate-closing-checklist format; "feedback-collection / no further changes" status) and appended a dated **UPDATE — current state (2026-06-10)** section cataloguing everything added across recent sessions. README is a file-manifest, still accurate (design/ entry already present). No contradictions found across the doc set.
- health_check green; file_index regenerated. Commit locally; Pranav pushes. (Sandbox git index keeps corrupting on this mount — rebuild with `git reset` before committing; one Cowork session at a time.)

## 2026-06-10 — Strategy Book design system: spec v1 locked

- Created `books/strategy-book/design/design-spec.md` — the visual design source of truth. Decisions locked by Pranav: **full-colour interior, B5 (7"×10") trim, diagram ownership decided per-diagram later, spec-only for now (no sample chapter yet)**.
- Spec covers: bucket colour system (B0 slate → B5 maroon, B6 sky, AI violet, Emergency signal-red with full red edge strip; gold reserved for RANK); **stepped right-edge bleed tabs** (9 slots → closed-book fore-edge index, Pranav's idea); footer **journey strip** ("you are here" mini-timeline on every page, B0 segment always half-filled); 2-page bucket-opener spread (End Goal + ranker line + grey Bare-Minimum box + mini-TOC); fixed component library (How to Do This checklist box = signature, Author Says in Kalam handwritten font with avatar, RANK gold border, warning strips, fill-in workbook forms); typography (Archivo/Source Sans 3/Kalam/Noto Serif Devanagari); **11-diagram Excalidraw inventory** prioritised (routing flowchart #1, 3-layer funnel #2…) — .excalidraw JSON committed, PNG exports local-only; production = HTML + paged.js → B5+bleed PDF.
- `books/strategy-book/README.md` updated (design/ in folder map + file table). health_check green (46/46, encodings clean, CLAUDE.md current); file_index 73 files. Commit locally; Pranav pushes.
- Next step when Pranav triggers build: CSS tokens + one sample section (Bucket 5 recommended) → print review → roll out.

## 2026-06-09 — Verification pass + git recovery

- Ran `tools/health_check.py` (green: 46/46 dirs, README links resolve, UTF-8/NUL clean, CLAUDE.md current) and `tools/file_index.py` (regenerated `_claude/artifacts/file-index.md`, 72 files). No structural fixes needed.
- Strategy Book confirmed fully committed on Pranav's machine (MASTER, Full-Structure, README, all sources — verified against HEAD).
- **Git incident logged for future-proofing:** two concurrent Cowork sessions/app hitting `.git` at once corrupted the index (stale `.git/index.lock`, "bad signature/index corrupt", and a sandbox view that showed the whole repo staged as deleted). No data lost — fixed by removing the lock + `git reset` to rebuild the index from HEAD. **Rule going forward: one Cowork session at a time on this repo.**

## 2026-06-09 — Strategy Book MASTER: harvested from 5 external ranker/faculty reports

- Reviewed the 5 `books/strategy-book/sources/extermal/` reports (YouTube ranker + faculty compilations). ~70% was CA Final (articleship/IBS/CFA/placement) — filtered as out-of-scope; deduped heavy repetition. Harvested 5 Inter-relevant items into `working/CA-Inter-Strategy-Book-MASTER.md`:
  - **Bucket 5 — new Strategy 1 "Your Exam Kit & Logistics"** (scout centre; TWO identical calculators; 3–4 same-brand black pens; 3–4 hall-ticket copies; stapler/scale/pencils; night-before pack; reach 1hr early; loose clothing; light meal + nimbu-paani/glucose). Renumbered Bucket 5 → 1–17. Folded submission mechanics (tick attempted-question boxes, OMR domino alignment, "1+2" supplement count, pen-cap-off, last-10-min review) into "Presentation & Submission" (Strat 11).
  - **Bucket 2** — Pause-and-Solve (Undivided-Attention, esp. recorded lectures); study-buddy fixed-call + Author Says (Teach-a-Friend → "and Keep a Study Buddy"); own-the-technical-keywords (theory mnemonics strat).
  - **Bucket 3** — Hinglish/Hindi revision notes (Build Layer 2); exam answer stays English.
- **Resolved morning-theory-vs-practical conflict** per Pranav: flipped Bucket 3 "Match Subject to Your Energy" → theory in your most productive window (morning OR night), practical sums when low/sleepy.
- **Excluded:** all CA-Final content; "lucky break" chapter-gambling; "reject notes/master from source"; rigid 12–14h & Pomodoro mandates; pure motivation/anecdote.
- health_check green; file_index 72. NOTE: project_log + summary-memory show signs of a **concurrent session/app** (a "Batch Operations" entry appeared that this session didn't write; summary-memory locked EPERM). Layer-3 fix still pending in canonical summary-memory. Commit locally; Pranav pushes.

## 2026-06-09 — Batch Operations system rebuilt + Standup Teaching philosophy doc

- Created `preparations/standup-teaching.md` — working philosophy doc for "Standup Teaching" (Pranav's named teaching style blending deep concept teaching with clean, anchored comedy). Not in books yet; flagged for future `books/about-author/` entry.
- Rebuilt `preparations/cainter-batch-operations.html` (replacing old `cainter-batch_operations_daily.html` which had a fixed daily quote+verse+insta routine). Key changes:
  - **Segment Library** (19 types): 6 Opening segments (Motivational Quote, Gita Shlok, Mahabharata/Epic Story, Personal IPCC Story, Standup Moment, Exam War Story) + 13 Mid-class segments (Insta Comedy Feed, Insta Motivation, Spiritual Reels, AI Tool Update, ICAI Updates, Financial News Brief, Mental Side of CA, CV & Career Reality, Famous CA/Finance Stories, Accounting in the News, Myth vs Reality in CA, YT Shorts Comment React, Student Doubt Discussion). Replaces the previous fixed daily routine.
  - **Week Planner tab**: Sun planning — pick Opening + Mid-class segment per day for 6 days. Saved to localStorage.
  - **Daily Ops tab**: Simplified checklist (fewer items, segment-aware). localStorage persistence per date — resets daily, survives refresh.
  - **Quote/Verse banks**: Added "Mark used" toggle per item, saved to localStorage — prevents repetition.
  - **Class structure**: Updated to 2.5 hr / 150 min flow, batch stats card (100 classes, 240 hrs, 4 months).
  - Removed: Sunday prep load for 6 separate daily items (now weekly Segment Library planning instead).
- README.md updated: preparations/ folder map expanded, "Where things are" table updated.
- Commit locally; Pranav pushes.

## 2026-06-09 — Strategy Book MASTER: harvested missing strategies + reverse-planning

- Compared MASTER vs Full-Structure vs original General-Exam-Systems; harvested everything missing into **MASTER** (the canonical working draft). All edits in `books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md`.
- **Bucket 1 restructured:** new Strategy 3 *Pick Your Anchor Book*; new Strategy 4 *Plan Backward From Exam Day* (industry hours + reverse-planning calendar for RANK and a separate PASS/exemption chart + one-group-or-two decision merged in); 3-Question Filter + Golden Rule box added to *Fix Your Boundary*. Renumbered to 1–9 (old standalone Both-Groups removed, folded into Strat 4).
- **Reverse-planning dates:** kept Pranav's round-number durations (4/21/45; 185/231/308/461) but **recomputed the calendar dates** — his table didn't tie out (second-rev start is 24-02-2027 not 17-03; Scenario A start 23-08-2026 not 28-10). PASS chart: exam-anchored back end fixed, second revision 45→39 days, classes+first-rev −30% (≈1295h) → starts 23-10-2026/21-09/29-07/12-04. **Flagged to Pranav** in case his dates used a different assumption (e.g. study-days only).
- **Other harvests:** Chapter Rating [RANK] (Exam-Relevant A/B/C + Recall + Simulation, Hinglish, Bucket 3); Paste-It-Where-You-Live (Bucket 3, GST-in-hallway Author Says); Amalgamation 5-times rule [RANK] (Bucket 3, exception only); 15-min Reading-Time strategy (Bucket 5 Strat 6, anecdote softened — dropped the 'not allowed' claim); Revision Marathons (Bucket 4); Dual-coding tip + Write-by-hand 'worse to worst' Author Says (Bucket 2); target-driven-not-hours + Pain Choice + diet (Bucket 0); AI teacher-first caution (AI Section); 'no motivation, gamified journey, warna time chala jayega' positioning (About This Book).
- **Dropped per Pranav:** Five-Year Rule, Articleship Discipline.
- **Layer 3 corrected** to one thin BOUND notebook per subject (spiral-bound A4 ok) — u