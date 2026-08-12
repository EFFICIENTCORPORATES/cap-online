# Course Catalog + Human-Readable MCQ IDs (built 2026-08-11)

Pranav's ask: the platform's Course→Level→Subject→Chapter→Unit taxonomy
should be **one single source of truth in the database**, and every
MCQ/descriptive question's chapter/unit tagging should be **derived from
it, not independently typed**. Plus: every question gets an additional
human-readable ID (`CA_L2_P01_C3_U4_00876`) alongside its existing
internal ID, for students to cross-reference.

## What was actually found before building anything

Investigated first, rather than assuming. Found **4 different, mutually
inconsistent MCQ ID schemes already in production**:

| File | Existing ID example |
|---|---|
| CA Inter Advanced Accounting | `CAI-P1-MTP-2025-01-S1-PI-Q1-a` |
| CA Foundation Quant Aptitude | `CA-FND-QUANTS-C1-Q001` |
| CMA Intermediate Law | `CMAI-P5-M12-FACULTY-2026-Q01-...` |
| CMA Foundation Law | `CMAF-P1-FACULTY-CS-ARUN-CHOUHAN-M1-Q01` |

Also found real, **already-verified** raw material to build the catalog
from, so nothing needed re-researching from scratch:
- `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` — the canonical, locked CA Inter Advanced Accounting chapter+unit+topic index.
- `telegram/source-docs/CS_CMA_Chapter_Catalog.xlsx`'s "Chapter Catalog" sheet — 647 real CS/CMA chapters, including `PaperNo`, read directly off each subject's own printed Table of Contents.
- `telegram/tools/cs_cma_common.py` / `build_study_bot_catalog.py` — paper numbers for every subject, read directly off real cover pages in an earlier session.
- `telegram/source-docs/StudyHub_Master_Catalog.xlsx` — CA Foundation Quantitative Aptitude's 18 real chapters.

## Locked decisions (all confirmed via AskUserQuestion, 2026-08-11)

1. **Course code is `CMA`, not `CO`** — matches every other reference to this course across the whole platform.
2. **CS level numbering**: CSEET=L1, Executive=L2, Professional=L3 (same graduated pattern CA/CMA already use).
3. **Paper numbers were cross-checked** against the already-verified sources above before being trusted (not re-typed) — see `populate_course_catalog.py`'s own docstring for the exact provenance of each one.
4. **The human_id is additive** — the existing internal ID (`mcq_id`/`book_id`) is never touched or replaced.
5. **Retrofit all existing questions now**, deterministically, via a Python script driven by the verified catalog — not just new content going forward.

## What was built

### `course_catalog` DB table (`schema.sql`)
One row per (course, level, paper, chapter, unit) — 701 rows. CS/CMA
chapters (no real ICSI/ICMAI sub-unit structure) use `unit_no=0`, the same
convention CA's own single-unit chapters already use.

### `telegram/tools/populate_course_catalog.py`
Rebuilds `course_catalog` from the 3 verified sources above. Full
replace each run (never a partial/incremental merge) — a fatal error on
any duplicate key, so a real data conflict can never silently overwrite
another. `--dry-run` previews without writing.

### `telegram/tools/generate_mcq_human_ids.py`
Retrofits `human_id` onto every question in all 6 real content files —
**the catalog is authoritative, never the question's own tag.** A real
mismatch was found and correctly resolved this way: CA Foundation Quant
Aptitude's MCQs all tag themselves `U1`, but the real ICAI material has no
sub-unit structure there at all — the catalog says `U0`, and that's what
went into all 625 of that subject's IDs (loudly reported, not silently
patched over). **Idempotent** — a record that already has a `human_id` is
never touched again; re-running after adding new questions only assigns
IDs to the new ones, so a previously-communicated ID never changes.

**Result**: **2,486 questions** across 6 files now carry both their
original internal ID and their new human-readable one, e.g.
`CMA_L2_P05_C12_U0_00001`.

### Admin Portal → Content → Course Catalog
New page (`/content/course-catalog`) — Course → Level → Subject dropdowns,
showing every chapter/unit for the selected subject, filterable,
paginated, exportable (CSV/Excel/HTML/PDF) — reuses the same shared
infrastructure as every other Analytics view.

## Verified

- `smoke_test_course_catalog.py` (new): **39 checks**, including real
  cross-checks against independently-known facts (CA Inter chapter 7 unit
  3 = AS-11, CMA Intermediate paper 5 chapter 12 = Companies Act 2013),
  dry-run-never-writes, format/uniqueness of every human_id, and —
  critically — **a real second full run confirmed to assign exactly 0 new
  IDs** (true idempotency, not just claimed).
- `smoke_test_admin_portal.py`: grew to **72 checks** with the new Course
  Catalog route's coverage (including a 400 when course/level/subject
  params are missing on export).
- Content validator re-run clean: **0 errors, 0 warnings** platform-wide
  (also fixed the pre-existing "year" warning — see below).
- All affected bots (`1lavya-examhub`, `capranav-exam`, `csarunchouhan`,
  `1lavya-admin-portal`) restarted; `health_check.py` shows no new issues.

## Also fixed this session: the "year" field warning

Root cause: converting Arun's CMA Foundation Law content into JSON, the
`--year` argument was never passed to `convert_faculty_mcq_docx.py` — all
375 records got `year: null`, while the sibling CMA Intermediate Law file
(converted correctly) used `year: "2026"`. Fixed at the source
(`cma_foundation_law_faculty_mcqs.json`), re-merged, re-validated: 0
warnings platform-wide.

## Real gap found + fixed the next day (2026-08-12)

Pranav checked the live Admin Portal himself and caught a real, correct
issue: *"I saw many subjects and chapters missing."* He was right — the
first version only covered 2 of CA's 17 real subjects (Advanced
Accounting + Quantitative Aptitude); CA Final had **zero** subjects at
all. CS/CMA were always fully covered (their source already has every
subject with a real `PaperNo`) — the gap was CA-specific.

**Root cause**: `rows_from_studyhub_catalog()` was hand-scoped to just
Quantitative Aptitude instead of every CA subject `build_study_bot_catalog.py`'s
own already-verified `COURSE_META` dict covers. Fixed by importing
`COURSE_META` **directly** (not copying its values into a second dict
that could drift) and iterating all 17 CA subjects.

**Fixing this surfaced two more real, previously-invisible bugs** — both
caught by the catalog's own duplicate-key collision check doing exactly
its job, not by inspection:

1. **CA Final Advanced Auditing's chapter 14 is genuinely two units**
   ("Special Features of Audit of Banks" / "...of NBFCs") sharing one
   chapter number. An initial blanket "every StudyHub-sourced subject is
   single-unit" assumption collapsed them into a fabricated collision.
   Fixed: the real unit number is now parsed from each file's own
   embedded `M{module}-C{chapter}-U{unit}` filename segment (verified
   against all 314 real CA Study Material filenames before being
   trusted — 0 unmatched) instead of being assumed.
2. **CA Inter Financial Management's chapter 9 has 6 real named units
   ("Unit I" through "Unit VI") plus an Appendix, but every one of their
   filenames says `U0`** — the filename's own unit segment is simply
   wrong for this subject. Fixed: a chapter's Label text ("Unit IV
   Management of Receivables") is now checked FIRST for an explicit
   "Unit N" prefix (roman or arabic numeral) and used as authoritative
   over the filename when present. The Appendix, and two similar
   chapter-level review files in Financial Reporting ("Comprehensive
   Illustrations", "Test Your Knowledge"), are correctly excluded
   entirely — genuine chapter-level review material, not real syllabus
   topics an MCQ would ever be tagged to as its own unit.

**Result**: **957 catalog rows** (up from 701), all 17 real CA subjects
present, CA Final populated for the first time. The human_id generator
re-run confirmed **fully idempotent** against this larger catalog — 0
new IDs assigned, since no new question content was added, only catalog
coverage. 5 new permanent regression checks added to
`smoke_test_course_catalog.py` for these exact 3 cases (full CA subject
count, the two real multi-unit chapters resolving correctly, and the
auxiliary-file exclusion) — this exact bug class can't silently
reappear. Visually re-verified: CA Final Financial Reporting (previously
completely empty) now shows its real 46-row structure, multi-unit
chapters intact.

**Also verified same day**: the "375 warnings" fix from the day before
is still fully clean — confirmed fresh, live, in all four places (the
raw validator, the old `:8787` dashboard's API, the new Admin Portal's
Content Health page, and every bot's own log file) — 0 errors, 0
warnings everywhere, right now, not just at the time it was originally
fixed.

## 4 document/question catalogues added to the Admin Portal (2026-08-12)

Pranav's ask: the existing Course Catalog page (chapter/unit taxonomy only)
should become the live **Study Materials** catalogue, read from
`telegram/source-docs/knowledge_base_documents.json`; plus 3 more
catalogues under the same Course/Level/Subject picker -- **Exam
Materials**, **Revision Material**, and a **Question Bank** catalogue
(chapter-level MCQ + Descriptive counts per subject/level/course). Also
asked to check whether 3 PDFs he'd just added to the Study Materials
folder (CA Inter Law, "Other Laws" part -- General Clauses Act,
Interpretation of Statutes, FEMA 1999) were showing up anywhere.

**They weren't.** `knowledge_base_documents.json` is generated (by
`tools/build_knowledge_base_catalog.py`) from `1Lavya_Study_Hub_File_
Mapping.xlsx`, not by scanning the folder directly -- the 3 new PDFs
existed on disk but had never been added to that source Excel, so no
downstream catalog (the JSON, `StudyHub_Master_Catalog.xlsx`, or
`course_catalog`) knew about them. Fixed at the root: added 3 rows to
`1Lavya_Study_Hub_File_Mapping.xlsx` with chapter titles verified by
reading each PDF's own first pages (`The General Clauses Act, 1897` /
`Interpretation of Statutes` / `The Foreign Exchange Management Act,
1999`), then re-ran the full downstream chain in order --
`build_master_catalog.py` -> `populate_course_catalog.py` ->
`build_knowledge_base_catalog.py` -- so every catalog derived from that
Excel picks the 3 files up, not just the one the request happened to
mention.

**A second real bug surfaced immediately, caught by `populate_course_
catalog.py`'s own duplicate-key check**: CA Inter Corporate and Other
Laws' printed chapter numbering genuinely restarts at Module 4 ("Other
Laws" -- Chapter 1/2/3) even though Module 1 already uses Chapter 1/2/3 for
"Preliminary"/etc. Verified this is the ONLY CA subject with this pattern
(checked all 17) before writing a fix -- added a small, explicit,
documented offset table (`CHAPTER_NO_MODULE_OFFSET`, same style as the
existing `TITLE_OVERRIDES`/`AUXILIARY_LABELS` overrides) so Module 4's
local 1/2/3 continue the subject's existing sequence as 13/14/15 instead
of colliding. `course_catalog` grew from 957 to 960 rows.

**Built `telegram/admin_portal/document_catalog.py`** -- the query layer
for the 3 new document-level catalogues (Study/Exam/Revision Material,
plus Question Bank) on top of `course_catalog`'s existing chapter
taxonomy:
- **Study Materials** / **Revision Material**: course_catalog chapters,
  each matched to its real document(s) from `knowledge_base_documents.json`
  at CHAPTER granularity (not unit -- avoids re-deriving the same
  multi-unit-chapter special cases `populate_course_catalog.py` already
  handles, a second driftable time). Shows file name(s), page count, and
  an Available/Missing (or "not sourced yet" for Revision Material, which
  is honestly empty everywhere -- the folder has no files yet) status.
- **Exam Materials**: a flat listing (exam papers aren't chapter-
  addressable), grouped by paper type/session/set. Today only CA Inter
  Advanced Accounting has any (58 files) -- every other course/level/
  subject shows an explicit "not sourced yet" message, not a silent empty
  table. Sourcing official CS/CMA exam papers from ICAI/ICSI/ICMAI's own
  websites was raised and explicitly deferred (Pranav's choice, asked via
  AskUserQuestion) to its own separate, scoped task.
- **Question Bank**: MCQ + Descriptive counts per chapter, computed
  directly from every real question's own `human_id` (which already
  encodes course/level/paper/chapter/unit) -- 100% accurate by
  construction, not a maintained/estimated count.

**Wired into the Admin Portal** as a 5-tab strip on the existing
`/content/course-catalog` page (Study Materials / Exam Materials /
Revision Material / Question Bank / Chapter Taxonomy -- the last one is
the original view, kept, not replaced), all sharing the same Course ->
Level -> Subject dropdowns via a `catalogue` query param, each with the
same pagination/filter/CSV/Excel/HTML/PDF export every other Admin Portal
table already has.

**A third real bug found while testing Pranav's own example URL**
(`?course=CA&level=Inter&subject=Accounting` -- the real CA Inter subject
is "Advanced Accounting", "Accounting" is a CA Foundation subject only):
an invalid course/level/subject in the URL was silently querying a value
with zero matching rows and rendering an unexplained empty "No chapters
match" table. Fixed -- an unrecognized course/level/subject in the URL now
falls back to the first real option instead.

**Verified**: `smoke_test_course_catalog.py` gained 2 new regression
checks for the Module-4 offset fix (still all-pass, including the
original 39). `smoke_test_admin_portal.py` gained ~15 new checks for the
4 new tabs, the Corporate and Other Laws collision fix, honest-empty
states, and the invalid-subject fallback (grew to 87 checks, all passing).
Content validator: still 0 errors/0 warnings. Visually verified via
headless-Edge screenshots (Study Materials, Question Bank, Exam Materials
tabs all render correctly with real data). `1lavya-admin-portal` and
`1lavya-studyhub` (the bot that actually serves these files to students)
both restarted and confirmed loading the updated catalog (`"Loaded 1087
rows from master catalog (1029 Study, 58 Exam, 0 Revision)"`).
`health_check.py`: same 16 pre-existing failures, nothing new.

## CA Foundation Accounting: 4 missing chapters found + real ICAI PDFs sourced (2026-08-12, later same day)

Pranav asked (in the context of reviewing 2 newly-added MCQ content sets)
whether the chapter names in a new CA Foundation Accounting MCQ set
matched our master syllabus, or deviated. Checked chapter-by-chapter and
topic-by-topic against `course_catalog` and the real Study Material PDF
filenames on disk: **Chapters 1-7 matched exactly** (unit-for-unit), but
the new MCQ set also had **Chapters 8-11** (Financial Statements of
Not-for-Profit Organisations / Accounts from Incomplete Records /
Partnership and LLP Accounts / Company Accounts) that didn't exist
anywhere in our systems — no `course_catalog` rows, no source PDFs.

Rather than guess whether these 4 chapters were real syllabus or
off-syllabus content, asked Pranav for the official ICAI syllabus link.
He provided **https://www.icai.org/post/19138** — fetched and confirmed:
**all 11 chapters, including the exact same 6-unit split for both Ch.10
and Ch.11, are real and match ICAI's own published syllabus exactly.**
The gap was in our own data, not a deviation in the new content — the
new MCQ set was actually more complete than `course_catalog`.

Found the real download links for all 15 missing PDFs directly on that
same ICAI page (`resource.cdn.icai.org`), downloaded and verified each
(real PDF, correct page counts, first-page title text matches the
expected chapter/unit name in every case), and added them to the Study
Materials folder using the exact same naming convention already in use
(`CAFoundation-Accounts-May26_M2-C{n}-U{n}_{Title}.pdf` — Module 2, per
ICAI's own module split). Added 15 rows to `1Lavya_Study_Hub_File_
Mapping.xlsx` (chapter/unit names taken directly from each PDF's own
first page, not guessed), then re-ran the full downstream chain —
`build_master_catalog.py` -> `populate_course_catalog.py` ->
`build_knowledge_base_catalog.py`. No chapter-number collision this time
(ICAI's own Module 2 continues the sequence 8-11, no restart) —
`course_catalog` grew cleanly from 960 to 975 rows.

Chapter 10's Annexure II (LLP financial statement formats — not a real
numbered unit) was kept as its own catalogued row (unit 7), matching the
same precedent already set for Chapter 7's Annexure-I.

**Verified**: 3 new permanent regression checks in `smoke_test_course_
catalog.py` (all 11 chapters present, ch.10's 7 units, ch.11's 6 units)
— all passing alongside the full existing suite. Content validator still
0/0. `1lavya-studyhub` (the bot that actually serves these files) and
`1lavya-admin-portal` both restarted, confirmed loading "1102 rows from
master catalog (1044 Study, 58 Exam, 0 Revision)" — the 15 new chapters
are live for real students immediately. `health_check.py`: same 16
pre-existing failures, nothing new.

**Separately flagged, not yet resolved**: the new MCQ content itself
(both CA Foundation Accounting and CA Foundation Business Economics) has
3 files that are invalid JSON (unescaped LaTeX `\%`), inconsistent
schemas across files within the same subject, and Economics' `subject`
field says "Economics" instead of "Business Economics" — see the earlier
"What's genuinely left to do" list below; none of that content has been
fixed/ingested yet, only the underlying chapter taxonomy gap is closed.

## CA Foundation Accounting + Business Economics MCQs: fixed, normalized, and made live (2026-08-12, later still)

Pranav asked to finish the job: get both new MCQ content sets in sync and
live in `1lavya-examhub`. Built `telegram/tools/ingest_ca_foundation_
accounting_economics_mcqs.py` -- a one-time ingestion script (full
reasoning in its own docstring) that:

1. **Repaired the 3 invalid-JSON files** found earlier: unescaped LaTeX
   `\%` in 2 Accounting files, plus a genuinely different defect found
   only once repair was attempted on the 3rd (Economics Ch.2) -- a stray
   `":="` typo (`"explanation":="..."` instead of `"explanation": "..."`).
2. **Merged both subjects' many scattered per-chapter/per-unit files**
   into 2 clean, subject-level files -- `telegram/assets/exam_bot/
   ca-foundation-accounting/mcq_questions_extracted.json` (1,595 MCQs) and
   `.../ca-foundation-business-economics/mcq_questions_extracted.json`
   (918 MCQs) -- per Pranav's confirmed convention (one MCQ + one
   Descriptive JSON per course/level/subject, never bundled).
3. **Resolved every question's real chapter/unit** WITHOUT fuzzy topic
   matching: every source record already carried a real unit indicator
   once you looked past the schema drift (`unit_code`/`unit`/`unitcode`
   in 5+ literal formats -- `"M1-C1-U1"`, `"Unit-1"`, `"Unit 1"`,
   `"unit-1-slug-suffix"`) -- one regex extracted the integer from all of
   them. Every resolved (chapter, unit) was cross-checked against
   `course_catalog`; Economics' Ch.5/Ch.10 (which have no real ICAI
   sub-unit split) correctly collapse the source's own informal "Unit
   1-4" labels into the one real unit.

**4 more real defects found and fixed during this pass**, each caught by
a preflight check failing loudly, not by inspection:
- A record's answer field being resolved via `a or b or c` chaining hit
  Python's falsy-zero bug -- Ch.9's `correct_answer: 0` (a valid
  0-indexed answer) was silently treated as absent. Fixed with explicit
  key-presence checks.
- Answer format turned out to vary BY CHAPTER, not be one convention:
  full option text (most chapters), an already-correct letter (Ch.8), or
  a 0-indexed integer list position (Ch.9) -- all three now handled.
- One Accounting record had its key typo'd as `mc_id` instead of
  `mcq_id` -- recovered, not discarded.
- One Economics record (Ch.5) had `"Options"` (capitalized) instead of
  `"options"` -- handled defensively.
- **The source data's own `exam_type: "MTP"` on all 1,595 Accounting
  records was corrected to `"PRACTICE"`** -- these are self-authored
  practice MCQs based on ICAI Study Material (Pranav's own description),
  not from a real ICAI Mock Test Paper; labeling them "MTP" would have
  misrepresented their provenance to a student. Matches the exact
  convention already established for the CA Foundation Quantitative
  Aptitude batch. Economics (which had no exam_type/year at all) got the
  same `"PRACTICE"`/`"2026"` treatment for consistency.

**Sourcing/generation tags**: every record in both files carries
`generation_source: "Self-authored practice MCQ, based on ICAI Study
Material (Pranav, 2026-08-12)"` -- Pranav's own stated description of how
this specific batch was created, not a guess. `faculty_name`/`faculty_id`
are left `null` -- WHO specifically authored them isn't something this
script could know, flagged as still open below.

**Human-readable IDs**: extended `generate_mcq_human_ids.py` with a new
resolver, `_resolve_by_chapter_slug()` -- since the ingestion script
already set every record's `chapter_slug` to the exact slugified real
`course_catalog` name, matching on that directly was both simpler and
more reliable than re-deriving chapter/unit from a source tag a second
time. All 2,513 new records got a real `human_id`
(`CA_L1_P01_C{n}_U{n}_{seq}` for Accounting, `CA_L1_P04_...` for
Economics) on the first real run; a second run confirmed fully
idempotent (0 newly assigned).

**Made live**: added both files to `1lavya-examhub`'s
`exam_content.mcq_json` list in `tenants.json` (same pattern as the
existing CA Foundation Quant Aptitude entry). Restarted `1lavya-examhub`
-- confirmed via its own startup log loading both files cleanly (1,595 +
918 records, 0 errors). Restarted `1lavya-admin-portal` -- the Question
Bank catalogue tab now shows real, correct per-chapter MCQ counts for
both subjects (verified the displayed numbers sum to 1,595 and 918
exactly, and via a live screenshot).

**Verified**: a full preflight pass added to the ingestion script itself
(no duplicate `mcq_id`, every `correct_option` is a real key in that
record's own `options`) passes clean on every run. Content validator:
0 errors, 0 warnings on both new files. `smoke_test_course_catalog.py`
and `smoke_test_admin_portal.py` both still fully pass. `health_check.py`:
same 16 pre-existing failures, nothing new.

**Still genuinely open**, named honestly, not silently dropped:
- `faculty_name`/`faculty_id` are null on all 2,513 new records --
  needs Pranav's input on who to attribute them to.
- Formal duplicate-question detection (OP/PP-style) was not run against
  this new content -- still the same explicitly-deferred, not-yet-built
  system referenced throughout this document.
- "Student tags" (a separate tagging concept Pranav described, distinct
  from chapter/topic tagging) was not built -- flagged, not started.
- Descriptive content for both subjects doesn't exist yet -- only the
  MCQ file was ingested for each, since that's all that was sourced.

## What's genuinely left to do

1. **Extend the human_id/Question Bank catalogue to more subjects** as new
   question content is built — `generate_mcq_human_ids.py` only tags
   content in its own `CONTENT_SOURCES` list today (CA Inter Adv
   Accounting, CA Foundation Quant Aptitude, CMA Foundation + Intermediate
   Law). The Course Catalog's chapter/unit taxonomy itself (all 4
   catalogue tabs' left-hand chapter column) now covers every CA/CS/CMA
   subject with real content on disk, per the 2026-08-12 CA-coverage fix
   above — this remaining gap is specifically the Question Bank tab's
   MCQ/Descriptive counts, which stay 0 for any subject with no tagged
   question content yet, honestly.
2. **Source official CS/CMA exam papers from ICAI/ICSI/ICMAI's own
   websites** — raised 2026-08-12, explicitly deferred as its own separate
   task (Pranav's choice). Today's Exam Materials catalogue only has CA
   Inter Advanced Accounting (58 files); every CS/CMA subject shows an
   honest "not sourced yet" row, not a silent gap.
3. **Question Catalog editing** (metadata-only, per the earlier confirmed
   scope) — still not built; all 5 Course Catalog tabs today are view-only.
4. Everything already tracked in `telegram/admin_portal/README.md`'s own
   "not built yet" list (Masters editing, Faculty/New Bot addition,
   Leaderboard edits, Users & Access/RBAC) is unaffected by this work —
   still pending, same order as before.
