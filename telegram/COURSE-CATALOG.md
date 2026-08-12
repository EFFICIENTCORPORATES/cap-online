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

## What's genuinely left to do

1. **Extend the catalog to more subjects** as new question content is
   built — today it only covers the 3 subjects that actually HAVE
   question content (CA Inter Adv Accounting, CA Foundation Quant
   Aptitude, CMA Foundation + Intermediate Law). Any new subject's real
   chapter/unit numbers need the same verified-source treatment before
   `populate_course_catalog.py` can include it.
2. **Question Catalog editing** (metadata-only, per the earlier confirmed
   scope) — still not built; Course Catalog today is view-only.
3. Everything already tracked in `telegram/admin_portal/README.md`'s own
   "not built yet" list (Masters editing, Faculty/New Bot addition,
   Leaderboard edits, Users & Access/RBAC) is unaffected by this work —
   still pending, same order as before.
