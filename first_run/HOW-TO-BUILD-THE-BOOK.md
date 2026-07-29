# How to Build the Question Bank Book — End to End

> **What this is:** the single master runbook for turning tagged sitting HTML into the
> final, print-ready `QUESTION-BANK-BOOK.html` — every script, in the exact order they
> must run, with what each one does, how to validate it, and the gotchas that have
> already bitten someone once. Written 2026-07-27 after auditing and running the whole
> pipeline end-to-end in one pass. If you're an AI picking up this repo cold, read this
> file before touching any script under `first_run/scripts/`.
>
> This file covers **assembly** (sitting HTML → chapter books → front/back matter → ToC
> → merged book → PDF). It does **not** cover how a sitting's HTML gets created and
> tagged in the first place (verbatim extraction, topic tagging, question splitting,
> examiner-comments handling, accuracy auditing) — that's a separate, earlier stage with
> its own dedicated docs: `_claude/skills/SKILL-question-bank-pipeline-overview.md` is
> the index for all of those; read it first if you're building a *new* sitting rather
> than reassembling the book from sittings that already exist.

---

## 0. Architecture at a glance

```
Layer 1                Layer 2                    Layer 3                  Layer 4
─────────               ─────────                   ─────────                ─────────
Sitting HTML   ──────▶  questions_index.json ────▶  34 chapter books ──┐
(parsed-from-pdf/,      (extract_questions.py,       (generate_all_       │
34 files, verbatim      mechanical/no-AI-judgment,   chapter_books.py,     │
source of truth)        BeautifulSoup)               generate_chapter_     │
                                          │                book.py, each    │
                                          └─▶ generate_qb_coverage_matrix.py│
                                              (Chapter-wise Sitting Summary)│
                                                       book.py)             ▼
                                                                    front-matter.html
                                                                    table-of-contents.html  ──▶  qb_merge.py  ──▶  QUESTION-BANK-BOOK.html
                                                                    back-matter.html                                  │
                                                                    (generate_qb_front_                               ▼
                                                                     back_matter.py,                        resolve_qb_toc_pages.py
                                                                     generate_qb_toc.py)                    (headless Chrome, real
                                                                                                              page numbers) ──▶ re-merge
                                                                                                                              │
                                                                                                                              ▼
                                                                                                                    Chrome print → PDF
```

- `generate_book_stats.py` — coverage statistics (`book_stats.json`), read from
  `questions_index.json` directly, independent of chapter-book rendering policy.
  **As of 2026-07-27, this is a required upstream step, not a side script**: Step 4
  (front matter) reads `book_stats.json` to render the "Book Coverage at a Glance"
  page, and hard-stops if the file is missing.
- `resolve_qb_toc_pages.py` — the only script that opens a real browser; everything
  else is pure Python/string manipulation.

---

## 1. Folder map

| Path | What's there |
|---|---|
| `first_run/source/` | Source PDFs only (never `.md`) for every in-scope sitting. Not read by anything in this guide — only relevant when *creating* a new sitting. |
| `first_run/output/parsed-from-pdf/` | **Layer 1.** All 34 in-scope sitting HTML files (`MTP_*.html`, `RTP_*.html`, `PYQ_*.html`) — verbatim, tagged, permanent source of truth. |
| `first_run/output/generated-from-script/` | **Layers 2–3.** `questions_index.json` + all 34 `*_Question_Book.html` chapter books (each now including its own Topic-wise Marks Mapping table, added 2026-07-28) + `book_stats.json`. Fully reproducible — never hand-edit anything here. |
| `first_run/output/` (root) | `front-matter.html`, `table-of-contents.html`, `chapter-coverage-matrix.html` (Chapter-wise Sitting Summary, added 2026-07-28), `back-matter.html`, `QUESTION-BANK-BOOK.html`, `vendor/` (fonts + paged.js polyfill), `How-to-Read-this-Book.md` (student-facing guide). |
| `first_run/schema/` | `book-style.json` (single source of truth for all colours/typography/page geometry), `book-style.css` (generated from it), `HTML-SCHEMA.md`. |
| `first_run/scripts/` | Every script below. |
| `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` | **External dependency, not under `first_run/`** (added 2026-07-28) — `qb_common.chapter_name_short_lookup()` / `topic_abbrev_lookup()` read this file directly for the coverage matrix's chapter-name column and every chapter's Topic-wise Marks Mapping table / per-question topic line. If this file's `chapter_name_short` or `topic_name_abbvtd` fields are ever renamed or restructured, those three render paths break — not just something under `first_run/`. |

---

## 2. One-time prerequisites

- **Python packages:** `beautifulsoup4` (Layer 1→2 extraction) and `websocket-client`
  (`pip install websocket-client` — required by `resolve_qb_toc_pages.py`, which drives
  Chrome directly over the DevTools Protocol; not needed for anything else).
- **Chrome or Edge installed** at one of the paths in `resolve_qb_toc_pages.py`'s
  `CHROME_CANDIDATES` list. Edit that list if it's installed somewhere else.
- **`first_run/output/vendor/`** must contain `paged.polyfill.js` and `gfonts-local.css`
  (and the `fonts/` folder `gfonts-local.css` points at) — `qb_merge.py` hard-stops with
  a clear error if either is missing, rather than silently producing an unpaginated book.
- All scripts are run from `first_run/scripts/` (they resolve every path relative to
  their own file location, so `cd` there first).

---

## 3. The build, step by step

Run these **in this exact order**. Every step is safe to re-run from scratch (nothing
is patched incrementally except step 7, which is designed to be re-run).

### Step 1 — Extract questions from sitting HTML (only if a sitting changed)
```
python extract_questions.py
```
Reads every file in `output/parsed-from-pdf/`, writes
`output/generated-from-script/questions_index.json`. Purely mechanical (BeautifulSoup),
no AI judgment — it reads what the HTML already says. **Before running this**, grep every
sitting file for `data-part="[^"]*"` values and confirm they're only `"I"`/`"II"` — a
free-text drift here has broken extraction silently once before (see
`SKILL-question-bank-html-schema.md`).

**Skip this step** if you're only re-rendering chapter books after a
`generate_chapter_book.py` change — `questions_index.json` doesn't need rebuilding just
because the *rendering* changed.

### Step 2 — Generate all 34 chapter books
```
python generate_all_chapter_books.py
```
Queries `questions_index.json` for every unique `final_chapter`, writes one
`*_Question_Book.html` per chapter into `output/generated-from-script/`. MCQs are
deliberately excluded from these files (see §7). `LEGACY-*` `final_chapter` values
(pre-syllabus-change topics, see CLAUDE.md §6) are skipped and reported by name/count
— confirmed no chapter book is silently generated for one. Every chapter file now also
includes its own **Topic-wise Marks Mapping** table (added 2026-07-28, see §6) right
after the intro notes, before Section I — built automatically, no separate step.
Prints a per-chapter descriptive/integrated count — sanity-check that no chapter shows
0 descriptive rows unexpectedly.

### Step 2.5 — Chapter-wise Sitting Summary (whole-book coverage matrix)
```
python generate_qb_coverage_matrix.py
```
Writes `output/chapter-coverage-matrix.html` — three pages (MTP/RTP/PYQ), each a
marks-coverage matrix of every chapter × exam session, with a Total column. See §6 for
the full design (why 3 pages, why RTP shows question count not marks). Depends only on
`questions_index.json` (Step 1) and `qb_merge.py`'s `CHAPTERS` tuple — safe to run any
time after Step 1, independent of Steps 2–3.

### Step 3 — Coverage statistics (required — front matter now reads this file)
```
python generate_book_stats.py
```
Writes `output/generated-from-script/book_stats.json` and prints a console summary
(sittings covered, question counts, marks totals, examiner-comment vs author-note
counts). Reads `questions_index.json` directly, not the chapter books — see that
script's own docstring for why (chapter-book rendering policy, like excluding MCQs, is
a separate, evolving decision from what the underlying corpus actually contains).

**No longer optional as of 2026-07-27**: Step 4 now builds a "Book Coverage at a
Glance" front-matter page (stat tiles + sittings list + a few honest caveats, e.g. why
RTP sittings show 0 marks) directly from `book_stats.json`. If this file is missing or
stale, `generate_qb_front_back_matter.py` hard-stops with a clear error rather than
silently building a front matter with no stats page.

### Step 4 — Front matter and back matter
```
python generate_qb_front_back_matter.py
```
Writes `output/front-matter.html` (title page, copyright & disclaimers, dedication, How
to Read This Book, **Book Coverage at a Glance**) and `output/back-matter.html` (about
the author, closing note). Both are real standalone HTML files — open either directly
in a browser to review before merging. Every number on the coverage page is read live
from `book_stats.json` at generation time — never hand-typed — so re-running Step 3
after adding sittings and then this step keeps the page honest automatically.

### Step 5 — Table of Contents (blank page numbers)
```
python generate_qb_toc.py
```
Writes `output/table-of-contents.html` from `qb_merge.py`'s own `CHAPTERS` tuple — one
row per chapter, chapter label, study-material cross-reference code, and an **empty**
`<span class="qb-toc-page">`. Always a full-file rewrite, never a patch — this is what
makes the ToC immune to the duplication bug described in §7. **Always run this before
Step 6**, even if you think the ToC hasn't changed — Step 7 requires the page-number
spans to start empty; re-running this script resets them.

### Step 6 — First merge pass
```
python qb_merge.py
```
Stitches `front-matter.html` → `table-of-contents.html` → `chapter-coverage-matrix.html`
→ all 34 chapters (teaching-sequence order, per the `CHAPTERS` tuple) → `back-matter.html`
into one file,
`output/QUESTION-BANK-BOOK.html`. Fixes the `id="AS02-NNN"` collision bug at merge time
(harmless no-op now that `generate_chapter_book.py` generates correct per-chapter ids
directly — see §7), inlines fonts (CORS workaround, see §7), and verifies all 34
chapters share byte-identical embedded `<style>` before taking a single copy of it.
`--force` proceeds past an "orphaned file in output/" warning; never overrides a
genuinely missing chapter file.

At this point the merged book exists but every ToC page number is still blank — that's
expected, not a bug.

### Step 7 — Resolve real page numbers and re-merge
```
python resolve_qb_toc_pages.py --remerge
```
Launches headless Chrome, opens the Step 6 output, waits for paged.js pagination to
stabilize (up to 180s — a 307-page book takes real time, this is not a hang), reads the
real page number for each chapter's anchor via `data-page-number` on its
`.pagedjs_page` container (`target-counter()` is confirmed broken in this vendored
paged.js version), patches `table-of-contents.html` with the real numbers, then
automatically re-runs `qb_merge.py --force` so the final `QUESTION-BANK-BOOK.html`
has correct page numbers baked in. This is the only step that needs a real browser.

**Validate after this step:**
```python
import re
data = open("output/QUESTION-BANK-BOOK.html", encoding="utf-8").read()
assert not re.findall(r'<span class="qb-toc-page"[^>]*>(\s*)</span>', data), "blank ToC pages remain"
assert data.count("build-info") == 0 and data.count("Extraction note") == 0
assert data.count('class="qb-student-notes"') == 0  # the old merge-time duplicate strip must never actually render
```
Also worth an HTMLParser pass (unclosed tags, duplicate ids) — see the validation
snippet used throughout this pipeline's history, no special library needed beyond the
stdlib.

### Step 8 — PDF (manual, final step)
Open `QUESTION-BANK-BOOK.html` in Chrome directly (not headless). Wait for paged.js to
finish repainting — a 34-chapter book visibly takes longer than any single section, that
is expected. Then `Ctrl+P` → **Save as PDF**, with **Background graphics** enabled (the
running header/footer and colour-coded boxes depend on it).

---

## 4. Regenerating after a change — what actually needs re-running

| You changed... | Re-run from step... |
|---|---|
| A sitting's tagged HTML (`parsed-from-pdf/*.html`) | 1, then 2, 2.5, 3, then 4–7 |
| `generate_chapter_book.py` (rendering logic/fields, incl. the Topic-wise Marks Mapping table) | 2 |
| `generate_qb_coverage_matrix.py` (Chapter-wise Sitting Summary logic) | 2.5 |
| `book-style.json` (colours/typography/page geometry) | 2 (chapter books share this indirectly via `qb_common.py`), then 4–7 |
| `generate_qb_front_back_matter.py` content, or the Book Coverage page (i.e. just re-adding sittings without changing rendering) | 3, then 4, then 5–7 (page count shifts, so ToC page numbers must be re-resolved) |
| `qb_merge.py`'s `CHAPTERS` tuple (order/labels) | 5, then 6–7 |
| Only re-running the merge with no upstream changes | 6–7 is sufficient |

**Note:** Step 4 (front/back matter) now reads Step 3's output (`book_stats.json`) for
the Book Coverage page — always run 3 before 4, not just after a sitting change but any
time you're unsure whether `book_stats.json` is current.

**Rule of thumb:** anything that can change the merged book's total page count means
Step 5 (reset ToC to blank) and Step 7 (re-resolve) must both run again — an already-
patched ToC file will NOT get overwritten correctly by Step 7 alone (its regex only
matches empty `<span>` tags; see §7).

---

## 5. Known gotchas and fixed incidents (read before assuming something is broken)

- **ToC duplication bug (fixed).** An earlier version patched a growing `<div>` with a
  non-greedy regex that stopped at the wrong closing tag, so re-running it left stale
  rows behind (67 entries instead of 34, confirmed once). Fixed by making the ToC file
  fully script-owned and always a full rewrite (Step 5) — there is never leftover
  content to accidentally preserve.

- **Student-notes duplication (found and fixed 2026-07-27).** `qb_common.py` used to
  inject its own compact "Your Notes" / "Notebook Page No." strip into every question at
  merge time (`inject_student_notes()`). Once `generate_chapter_book.py` grew its own,
  richer built-in Student Self Notes / Notebook Ref / Tag / Revision Phase block per
  question, calling both would print duplicate fields on every single question. The
  merge-time call is now disabled (`page_shell()` no longer calls
  `inject_student_notes()`) — the function is left defined, not deleted, in case a
  future chapter-book redesign drops its own version again and the merge-time fallback
  is needed. **If you ever see two "notes" sections stacked on one question, this is the
  first thing to check.**

- **`id="AS02-NNN"` bug (fixed at the source, 2026-07-26).** `generate_chapter_book.py`
  used to hardcode `AS02-` as the id prefix for every chapter regardless of which
  chapter it actually was. Fixed directly in that script (a `chapter_slug` parameter now
  flows into every qblock's id). `qb_merge.py`'s `rewrite_qblock_ids()` workaround is
  now a harmless no-op for freshly-regenerated chapters — left in place as a safety net,
  not removed.

- **CORS blocks font `<link>` under `file://`.** paged.js re-fetches every linked
  stylesheet via XHR to analyze its rules; Chrome blocks that under `file://` origin,
  and the failure is *silent* — no console dialog, `.pagedjs_page` count just never
  leaves zero. Fixed by inlining `gfonts-local.css`'s content directly into the merged
  document's own `<style>` block (`qb_merge.py`'s `build_merged_html()`), rewriting its
  relative `font/...` paths to `vendor/font/...` since the inlined CSS now resolves
  relative to the merged document's location, not its original file's.

- **Flex containers don't fragment predictably across a page break.** The title page's
  `min-height` was originally 220mm — 6mm taller than the 214mm content-box height
  available, which silently scattered its children (author name, credential line) onto
  a *later* page instead of visibly overflowing where it would have been obvious. Fixed
  by keeping `min-height` safely under the real content-box height, plus
  `break-inside: avoid` as a second line of defence.

- **`.qblock` itself is deliberately NOT in the `break-inside: avoid` list.** It
  originally was — measured directly against real output, 93% of content pages held
  exactly one qblock with ~29% of the page wasted, because a large container breaking
  as a whole (rather than at its natural internal boundaries) jumps entirely to the next
  page the moment it doesn't fit. Fixed by scoping `break-inside: avoid` to the smaller
  pieces inside a qblock (`.question`, `.answer-block`, `.mistakes`, etc.) instead.

- **File-path percent-encoding (fixed 2026-07-27).** `resolve_qb_toc_pages.py` builds a
  `file://` URL and passes it straight into an HTTP request to Chrome's DevTools
  endpoint. A raw space in the path (any repo clone sitting under a directory with a
  space in its name, e.g. `.../Other computers/...`) makes Python's `http.client` reject
  the request outright (`URL can't contain control characters`). Fixed by
  percent-encoding the URL (`urllib.parse.quote(file_url, safe=":/")`) before use — safe
  regardless of whether the path has a space or not, so no environment-specific
  workaround was needed.

- **MCQs are deliberately excluded from every chapter book** (2026-07-26, Pranav's
  decision) — they need continuous, fast, repeated drilling, better served by a
  dedicated MCQ platform than a slow-read book. They still exist in `questions_index.json`
  and the sitting HTML; `generate_book_stats.py` explicitly reports both the full-corpus
  and rendered-in-book counts so nobody confuses the two.

- **A chapter's "Integrated" section can legitimately be empty**, and a question can
  legitimately appear in *two* chapters' books (once as home, once as a cross-reference
  under another chapter's Integrated section) — both are by-design consequences of the
  independent-question-splitting rule, not bugs. See
  `SKILL-question-bank-question-splitting.md`.

- **A single chapter's coverage table can blow past print width too, not just the
  whole-book one (found and fixed 2026-07-28).** The Topic-wise Marks Mapping table's
  first draft combined MTP+PYQ+RTP sessions into one table per chapter — fine for a
  thin chapter, but AS 2 (tested in nearly every sitting) produced **22 columns**, the
  same print-width failure the whole-book matrix was designed to avoid, just
  rediscovered one level deeper than expected. Fixed by splitting the per-chapter table
  into up to 3 mini-tables (MTP/PYQ marks, RTP count) too — `generate_chapter_book.py`'s
  `_topic_subtable()`. **If a future chapter table looks unexpectedly wide, this is the
  first thing to check** — don't assume "a single chapter" is automatically narrow.

- **Topic-wise Marks Mapping showed the same chapter name on every row (found and
  fixed 2026-07-28).** `extract_questions.py`'s `extract_topics()` only captured
  `data-title` (the chapter-level title, identical for every question in that
  chapter) from each sitting HTML's topic-tag span — it never captured
  `data-subtopictitle`, which was already present on essentially every tag with a
  genuinely topic-specific description (confirmed by direct grep against real
  sitting files before touching any code). Fixed by capturing `subtopictitle` in
  extraction, and by `qb_common.abbreviated_topic_label()`, which prefers file 1's
  new `topic_name_abbvtd` (matched via `topic_no` for chapters using that plain-
  integer tagging convention, e.g. Framework) and falls back to `subtopictitle`
  otherwise — never the chapter-level `title`. **If a future chapter shows a
  repeated label again, check whether a topic-tag's `subtopicref` format changed
  in a way `abbreviated_topic_label()` doesn't yet handle**, don't assume the bug
  is back in the same place.

- **Page-break blank space after long tables/answers (found and fixed 2026-07-28,
  same root cause as the .qblock fix above, one level deeper).** Pranav sent real
  screenshots: a long accounting table or a whole worked answer jumping wholesale
  to the next page, leaving the remainder of the current page blank. Cause: `table`
  and `.answer-block` were both still in the `break-inside: avoid` list in
  `qb_common.print_layer_css()` — exactly the same "large container can't fit
  remaining space, jumps whole" failure the `.qblock` fix (2026-07-26) already
  solved once, just rediscovered on the next container down. Fixed by removing
  both from that list; a `<table>` with proper `<thead>`/`<tbody>` (already
  required by the schema) only ever splits between complete rows, never mid-row,
  and paged.js repeats the header on the continuation page — this is normal,
  correct print-table behaviour, not a new risk. **Not yet visually re-verified
  with a screenshot** (Pranav asked to skip that step for now) — if blank-space
  complaints continue after this fix, that verification is the first thing to
  actually do, not re-guess the CSS.

- **A CSS comment containing markdown-style backtick-quoting broke the file's own
  0-backticks validation rule (found and fixed 2026-07-28).** Writing the
  page-break fix above, the explanatory comment used `` `table` ``/`` `.answer-block` ``
  as inline-code-style quoting — harmless in isolation, but every sitting/merged
  file in this pipeline is validated with a hard "0 backticks anywhere" rule (it
  exists to catch rupee-sign OCR corruption, see `SKILL-question-bank-verbatim-
  extraction.md`). A backtick in a *comment* still trips that check. Rephrased
  without backticks. **Any future prose added to `qb_common.py`'s CSS comments —
  or anywhere else in this pipeline — must avoid literal backtick characters
  entirely**, not just in student-facing content.

---

## 6. Feature status

- **OP/PP recurring-question tags — explicitly OUT OF SCOPE for this (first) edition**
  (Pranav, 2026-07-28), not just "not yet built." Marks which sitting is the original
  version of a repeated/near-identical question vs. a later practice repeat. Design
  exists (`SKILL-question-bank-duplicate-detection.md`, ≥90% text-similarity rule) but
  is deliberately deferred to a dedicated post-launch effort once the full 34-sitting
  corpus exists — don't build this for edition 1 even if it looks quick partway
  through a sitting build.
- **Short chapter/unit names** — some chapter titles are long (e.g. AS 5's full title);
  a future edition should shorten these in the topic tag once a shortlist is drafted
  with Pranav's input. Still not built.
- **Chapter-wise Sitting Summary and per-chapter Topic-wise Summary — built 2026-07-28**
  (Pranav's request, once the full 34-sitting corpus existed). Chapter-wise Sitting
  Summary: `generate_qb_coverage_matrix.py` → `output/chapter-coverage-matrix.html`,
  three pages (MTP/RTP/PYQ), each a marks-coverage matrix of chapter × exam session
  (one column per session, Set 1 + Set 2 collapsed; RTP shows question count, not
  marks, since ICAI's RTP documents carry no per-question marks key) with a Total
  column. Per-chapter Topic-wise Summary: built into `generate_chapter_book.py`
  (`build_topic_summary()`/`_topic_subtable()`), one table set per chapter, right after
  the intro notes and before Section I, split the same way (MTP/PYQ marks, RTP count)
  for the same print-width reason — see the gotcha above. Both are pure derivations
  from `questions_index.json`, reusing shared helpers in `qb_common.py`
  (`sessions_for()`, `dedup_marks_sum()`, `dedup_count()`, `session_label()`) so the
  two features' arithmetic can never drift apart. Formalizes the pattern Pranav
  already hand-built for the AS10 pilot in `AS10_Question_Reference.html`.

OP/PP and short chapter names are named honestly as "coming in a future edition" in the
book's own front matter — don't silently build around their absence elsewhere.

### Print-cost reduction pass (2026-07-28, Pranav's review) — 819 → 688 pages

Pranav reviewed the merged 819-page book for print cost and sent a punch list, all
implemented in one pass:

- **Empty Descriptive/Integrated sections are omitted entirely** (`generate_chapter_book.py`'s
  `render_section()`) — no heading, no intro sentence, no "no questions" placeholder,
  when a section has zero rows. The "an empty Section II is normal, not a bug" context
  now lives once in front matter instead of being restated per chapter.
- **The per-box "Written by the author, not ICAI..." / "Real ICAI Examiner's Comment..."
  provenance sentence no longer repeats on every Author's Note/Examiner's Comment box**
  (~500+ instances) — stated once in front matter's How to Read This Book colour key.
- **The 3-line student-fields block (Notebook Ref / My Tag / Revision Phase) is now one
  line**: `My NB Page No ___  My Tag ___  Revision Phase [ ]1 [ ]2 [ ]3`. The "e.g.
  Last-day Revision..." My Tag suggestions moved into front matter, stated once.
- **The Error Register is now ONE shared 6-page appendix at the back of the book** (3
  double-sided sheets — `generate_qb_front_back_matter.build_error_register_pages()`),
  replacing a dedicated full page per chapter (34 pages). A "Chapter / Topic" column
  lets one shared register hold entries from any chapter. `generate_chapter_book.py`
  no longer emits any `.error-register` content at all.
- **Per-question topic line no longer repeats the chapter name** (e.g. "AS 10 —
  Property, Plant and Equipment") — the chapter is already the whole file's own title
  and the ToC entry. Now shows only `Topic {ref}: {abbreviated/specific name}`, via
  `qb_common.abbreviated_topic_label()` — see the gotcha above for exactly how that
  label is chosen and why the old version was actually a display bug, not just verbose.
- **Coverage-matrix chapter column uses file 1's `chapter_name_short`** (not a
  from-title string-split heuristic) plus CSS wrapping (`max-width` + `overflow-wrap`,
  no more `white-space: nowrap`) for names still long after abbreviation (Framework's
  short name is barely shorter than its full name) — both the abbreviation *and* the
  wrap fallback Pranav asked for are applied together, not one or the other.
- **Page-break blank-space fix** — see the gotcha above (`table`/`.answer-block` removed
  from `break-inside: avoid`).
- **Margins checked, not changed**: already at a documented 6mm floor (cut from 20mm in
  an earlier pass), flagged there as near the physical limit most consumer printers can
  handle without clipping. Reducing further wasn't done — a real print-safety tradeoff,
  not an oversight.

**Result**: 819 → **688 pages** (131 pages, ~16%), all from removing genuine repetition
and fixing real bugs — no content was cut to get there. Full pipeline re-run and
re-validated after every change (0 unclosed tags, 0 duplicate ids, 0 NUL bytes, 0
backticks).

---

## 7. Quick reference — full command sequence, copy-pasteable

```bash
cd first_run/scripts

# Only if a sitting's HTML changed:
python extract_questions.py

python generate_all_chapter_books.py
python generate_qb_coverage_matrix.py    # Chapter-wise Sitting Summary
python generate_book_stats.py            # required -- front matter reads this
python generate_qb_front_back_matter.py
python generate_qb_toc.py
python qb_merge.py
python resolve_qb_toc_pages.py --remerge

# Then, manually: open output/QUESTION-BANK-BOOK.html in Chrome,
# wait for pagination to finish, Ctrl+P -> Save as PDF (Background graphics ON).
```
