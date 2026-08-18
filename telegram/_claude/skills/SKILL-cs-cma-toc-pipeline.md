# SKILL — CS / CMA Chapter-Catalog Pipeline (ToC Extraction)

> **What this is:** Pillar 6's Study Hub bot is being extended to CS (Company Secretary)
> and CMA (Cost & Management Accountant) content, in `telegram/assets/{CS Exce, CS Prof,
> CS EET, CMA Final, CMA Found Study mat, CMA Inter Study Mat}/`. Unlike ICAI's CA material
> (see `SKILL-study-bot-catalog-pipeline.md`), ICSI and ICMAI ship **one consolidated PDF
> per subject** — every chapter of a ~300-1300 page book in a single file, no per-chapter
> split, no usable embedded bookmarks (checked: 47 of 50 files have zero PDF outline
> entries). Built 2026-08-08. Read this before touching `telegram/tools/scan_cs_cma_toc.py`,
> `build_cs_cma_catalog.py`, `cs_cma_common.py`, or
> `telegram/source-docs/CS_CMA_Chapter_Catalog.xlsx`.

---

## 1. The problem, and why it's harder than the CA pipeline

There is no per-chapter file to trust or verify — chapter boundaries have to be **derived
from each PDF's own printed Table of Contents**, and then "printed page N" has to be
reverse-engineered into "actual PDF page M", since the two are offset by however many
un-numbered/roman-numeral front-matter pages precede printed page 1. Pranav's explicit
instruction (2026-08-08): use the ToC to bifurcate into chapter-wise page ranges, and
capture **both** the printed page range and the actual PDF page range in the catalog,
"because our Python code will only understand the page of the PDF and not the printed
page." This skill is Stage 1 (extraction + verification) and Stage 2 (Excel catalog) of
that; **splitting the PDFs into actual per-chapter files is a separate, not-yet-built next
stage** — see §6.

## 2. Course/Level/Subject metadata — read from each cover page, not guessed

`cs_cma_common.py`'s `FILE_META` table has one entry per PDF (50 total), each read
directly off that file's own cover/syllabus page — ICMAI: `"FINAL / Paper 18 / Corporate
Financial Reporting"`; ICSI: `"(i) / TITLE / GROUP N / PAPER N / EXECUTIVE PROGRAMME"`.
Same discipline as the CA pipeline's `COURSE_META`. One real nuance found this way: **CMA
Intermediate's "Paper 7" is one syllabus paper split across two study-note volumes** —
Direct Taxation and Indirect Taxation — kept distinct as `7A`/`7B` in `PaperNo`, the same
pattern already used for CA Inter's Paper 3A/3B GST/Income-tax split.

## 3. Two publisher formats, two parsers, one shared 64-page/650-chapter batch

`scan_cs_cma_toc.py` auto-detects which parser to use per file (`publisher_of()` in
`cs_cma_common.py`, based on folder):

**ICMAI (23 files: CMA Final/Foundation/Intermediate)** — a "Contents as per Syllabus"
page (or several) gives explicit printed page **ranges** per `Module N. Title NN-NN` and
`SECTION X: Title NN-NN` line — no end-page inference needed, unlike ICSI. Two real
format variants found and handled:
- A handful of files use `Module N **:** Title` (colon) instead of `Module N**.** Title`
  (period) — `ICMAI_MODULE_RE` accepts either.
- **7 of the 23 files** render their ToC table **column-by-column, not row-by-row** — every
  heading on a page comes first (with no inline page range), then *all* of that page's
  page-range values are dumped together at the end, in the same order the headings
  appeared. `parse_icmai_toc_grouped_ranges()` is the fallback for this: collect all
  headings in document order, all standalone `NN-NN` range lines in document order, zip
  them positionally. Only invoked when the primary (inline) parser finds zero modules on
  a file, and only trusted if heading-count equals range-count.

**ICSI (27 files: CS Executive/Professional/CSEET)** — a "CONTENTS" section lists each
`LESSON N` header + title, followed by that lesson's own detailed subtopic list (each
ending in a printed page number) — a lesson's start page is the **first** page number
after its header; its end page is the **next** lesson's start minus 1 (or a `TEST PAPERS
NNN` sentinel minus 1 for the last lesson, if present). Two real bugs found and fixed here:
- **Sub-heading bleed-through**: lines like `"SECTION I: THE...CODE, 2020"` (a sub-Act
  citation within one lesson) end in a 4-digit year that looks exactly like a trailing
  page number. Fixed by skipping any candidate line whose text-before-the-number ends in
  a comma (real page-number lines are space-separated, never comma-separated) plus an
  explicit `SECTION\s+[IVXLCM]+:` skip.
- **`^`/`$` regex anchors applied to a whole multi-line page string instead of per-line**
  (twice, independently, in two different functions) silently made `.findall()`/`.search()`
  never match — the practical symptom was the ToC-page-window detector never terminating
  early (always hitting its 90-page safety cap) and, worse, a lesson's own **later body
  chapter opening** (which restates the same `"LESSON N" + TITLE` heading) bleeding into
  the parsed ToC as spurious duplicate/corrupted entries. Fixed by matching per stripped
  line everywhere, and by making the parser explicitly ignore any `LESSON N` header whose
  number was already captured (idempotent against this exact bleed-through, not just the
  window-sizing symptom).

## 4. Verification: content-matching, with two confirmed real-typo overrides

Same discipline as the CA pipeline: **every computed PDF page range is verified**, not
trusted from arithmetic alone. `detect_offset()` fuzzy-matches (rapidfuzz `partial_ratio`)
first/middle/last chapter titles against real page text in a search window to find the
printed→PDF page offset per file, then every single chapter's title is re-checked against
its own computed opening page (with a small local re-search if the first attempt scores
< 70, to absorb an occasional divider-page shift). 647 chapters extracted across 50 files;
**a random 12-row independent spot-check (re-reading the actual PDF page fresh, outside
the pipeline's own self-reported scores) confirmed every one correct**, including
cross-checking the printed page number visible in each page's own running header.

Two rows needed an explicit, documented correction rather than trusting the source
verbatim — both in `build_cs_cma_catalog.py`'s override tables, never applied silently:
- **`TITLE_OVERRIDES`**: CMA Final "Cost and Mgmt Audit.pdf" chapters 15–16 have genuine
  typos in ICMAI's *own* printed ToC ("Operatinal", "Diefferent") — confirmed by reading
  the actual chapter-opening page, which spells both correctly. The catalog uses the
  corrected spelling; the row's Notes column says exactly why.
- **`MERGED_NO_CONTENT`**: CS Professional's ESG book's own ToC states Lesson 6 "has been
  merged with Lesson 3" — it genuinely has no standalone page range. Listed in the catalog
  with a Notes explanation instead of a fabricated range.

## 5. The Excel catalog

`telegram/source-docs/CS_CMA_Chapter_Catalog.xlsx` — generated by `build_cs_cma_catalog.py`
from `telegram/tools/_reports/cs_cma_toc_scan.json` (itself generated by
`scan_cs_cma_toc.py`; re-run that first if source PDFs change). Both scripts are
idempotent — never hand-edit the Excel, fix the override tables or parsers and re-run.
Key columns: `PrintedPageStart/End` (as a human reads it in the book) vs.
`PDFPageStart/End_1indexed` (1-indexed, as any PDF viewer shows it — **subtract 1 for
pypdf's 0-indexed `reader.pages[]`**), `ChapterName` (full) vs. `ShortChapterName`
(≤35-char, Telegram-button-width, same `short_title()` abbreviation scheme as the CA
pipeline), `SourceFile` (which consolidated PDF these pages still live inside — nothing
has been split out yet), `FinalPDFFileName` (the planned name once a chapter *is* split:
`{Course}{LevelCode}-{SubjectShort}_{Code}_{ShortTitle}.pdf`, e.g.
`CMAInter-CostAcc_M1_IntroductionToCostAccounting.pdf` — `M`-prefix codes for ICMAI
Modules, `L`-prefix for ICSI Lessons), and `Notes` (only non-empty for the 3 rows above —
read it before trusting a flagged row).

## 6. Explicitly NOT done yet (scope, locked 2026-08-08)

Pranav's instruction was **"make this complete Excel file first"** — deliberately staged
before any actual PDF splitting. Not built yet, and not to be built without asking:
- A `split_cs_cma_pdfs.py`-equivalent that actually writes one PDF per chapter into a flat
  `telegram/assets/study_bot_flat/`-style folder using this catalog's page ranges (pypdf
  `PdfWriter`, straightforward once the catalog is signed off on).
- Wiring the resulting flat PDFs + a File-Mapping-shaped catalog into `study_hub_bot.py`
  itself (currently only serves CA content — see `SKILL-study-bot-catalog-pipeline.md`).
- CS/CMA `.md` sibling files, `desktop.ini` cleanup, `.gitignore` review for the new
  `telegram/assets/{CS *, CMA *}/` folders — not yet audited the way the CA `study_bot/`
  tree was.
