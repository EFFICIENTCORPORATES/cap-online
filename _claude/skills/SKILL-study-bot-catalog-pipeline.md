# SKILL — Telegram Study Hub Bot: Catalog Pipeline

> **What this is:** `telegram/bots/study_hub_bot.py` (Pillar 6) is a free Telegram bot that
> sends CA Foundation/Inter/Final study-material PDFs to students, either via a guided
> Course → Level → Subject → Chapter menu or free-text fuzzy search. It has no database —
> an Excel file is its entire catalog/search index, read into memory at startup, and it
> serves PDFs from one flat folder. This skill documents the pipeline that produces that
> Excel file and that flat folder from the original nested ICAI study-material PDFs — built
> 2026-08-07. Read this before touching anything under `telegram/assets/study_bot_flat/`,
> `telegram/source-docs/1Lavya_Study_Hub_File_Mapping.xlsx`, or `telegram/tools/`.

---

## 1. The problem this solves

ICAI ships its study material as PDFs nested `<course>/Module N/M{module}_C{chapter}_
U{unit}_ <Chapter Title>.pdf` — Pranav collected 17 course-subject folders (CA Foundation
×4, CA Inter ×8 paper-sections, CA Final ×5) under `telegram/assets/study_bot/`, 380 PDFs
total, each with an ICAI-authored `.md` sibling from an earlier conversion pass. The bot,
however, needs:
- **One flat folder** (`os.path.join(FILES_FOLDER, filename)` — no subfolder concept).
- **Globally unique filenames** — but ICAI's own naming collides: `M1_C0_U1_ Initial
  Pages.pdf` alone appears 12 times across different courses (every course's Module 1 has
  its own "Initial Pages" cover file). Flattened naively, later copies silently overwrite
  earlier ones.
- **A populated Excel catalog** (`FileName, Course, Level, Subject, ModuleOrGroup,
  ChapterNo, ChapterName, Keywords`) — the original template shipped with only 3 example
  rows; nothing had ever been built against the 380 real files.
- **No `.md` files** — the bot only ever sends PDFs; the siblings were dead weight.

Doing this by hand (rename 380 files, type 380 Excel rows) is exactly the kind of
mechanical, error-prone job Pranav asked to be done by **script**, not manually — see
§4 for the two scripts that do it.

## 2. Non-negotiable: verify before trusting any filename

Pranav's explicit instruction (2026-08-07): *"this will be the last time we will be
checking it... accuracy shall be required."* ICAI's filenames are the input, not a
guaranteed-correct one — so **every filename's stated chapter title was checked against
the PDF's own first-page text** before it was used to build anything, using
`pypdf` text extraction + `rapidfuzz` fuzzy scoring (`telegram/tools/
scan_study_bot_source.py`). This is the same "flag uncertainty, never guess silently"
discipline the Question Bank pipeline uses (`SKILL-question-bank-verbatim-extraction.md`)
applied to a different corpus.

**Result of the one-time verification pass**: 380/380 PDFs had extractable, non-empty
text (nothing scanned/blank). Only expected structural files (Initial Pages, Section
overview/crossword-puzzle supplements) scored low against a fuzzy title match — because
they're front matter, not because anything was wrong. Three **real** problems were found
and fixed by actually reading the flagged PDFs:
- `ca-found-accounts-may26-corrigendum.pdf` — no `M_C_U_` prefix at all (a standalone
  erratum sheet, not a chapter). Given an explicit override.
- `M2_C14_U1_ Untitled.pdf` / `M2_C14_U2_ Untitled.pdf` (CA Final Advanced Auditing) — the
  filename's title field was literally the word "Untitled". Reading page 1 showed these
  are Chapter 14 Units 1–2, "Special Features of Audit of Banks" / "...of Non-Banking
  Financial Companies (NBFCs)".
- `M1_C0_U0_ Unit I Statistical Description of Data.pdf` / `...Unit I Measures of Central
  Tendency.pdf` (CA Foundation Quantitative Aptitude) — filename's module/chapter were
  both `0` (uninformative). Page 1 showed printed chapter numbers "13CHAPTER" and "14"
  respectively — these are real Chapters 13 and 14, not "Unit I" of chapter 0.

All three corrections are recorded, with the reasoning above, in `TITLE_OVERRIDES` at the
top of `build_study_bot_catalog.py` — **not** silently baked into the output with no
trace. If ICAI ever re-ships a corrected version of one of these files, that override
table is the first place to check whether it's still needed.

Subject/paper full names (`Course/Level/Subject` columns) were **not** guessed either —
every one of the 17 subjects' official paper name and number was read directly off that
subject's own "Initial Pages" cover PDF (e.g. confirmed "Paper 3, Section – A:
Income-tax Law", not assumed as "Income Tax"). See `COURSE_META` in the same script.

## 3. Naming convention (locked, per Pranav's choice 2026-08-07)

Flat filename: `{Course}{Level}-{SubjectShort}-{Session}_{M{n}-C{n}-U{n}}_{ShortTitle}.pdf`

```
CAInter-AdvAcc-May26_M1-C4-U2_AS3CashFlowStatement.pdf
CAFinal-FinReporting-May26_M2-C10-U0_AssessmentOfTrusts.pdf
CAFoundation-Accounts-May26_M1-C7-U1_FinalAccountsOfNonManufacturing.pdf
```

- **Course-Level-Subject-Session prefix** — so the file is self-identifying without
  opening it (Pranav's explicit requirement).
- **`M{module}-C{chapter}-U{unit}`** — ICAI's own chapter/unit numbering, kept in the same
  `M{n}-C{n}-U{n}` shape already used as the taxonomy ID convention elsewhere in this repo
  (`books/concept-book/syllabus-engine/...`, the Question Bank pipeline) — deliberate
  consistency, not a coincidence.
- **Short title** — a CamelCase abbreviation of the (verified, corrected) chapter title,
  capped at 35 characters, word-boundary-safe (`short_title()` in the build script). The
  **full, untruncated** title always lives in the Excel's `ChapterName` column — that's
  what students actually see (menu button label, PDF caption); the filename is just a
  stable, short, on-disk identifier. Typical final length: 45–77 characters, well inside
  any filesystem limit.
- Global uniqueness is asserted by the build script (hard-fails if it ever produces a
  collision) — never assume it silently held.

## 4. The two scripts (run in order)

```
telegram/assets/study_bot/  (nested, ICAI-original — DELETED 2026-08-07 after verification;
                              re-source from ICAI if this pipeline needs to run again from
                              scratch, e.g. a new session's PDFs)
   │
   ▼  telegram/tools/scan_study_bot_source.py   (read-only; re-run any time source PDFs change)
   │     - parses every M_C_U filename, extracts first-page text via pypdf,
   │       fuzzy-scores filename vs. real content
   │     - writes telegram/tools/_reports/source_scan.csv + .json for review
   │     - THIS is the step that must be re-run and re-reviewed if ICAI ever
   │       reships a subject with renamed/renumbered files
   ▼
telegram/tools/build_study_bot_catalog.py        (writes; safe to re-run any time)
   │     - COURSE_META: course-slug -> verified (Course, Level, Subject, Session)
   │     - TITLE_OVERRIDES: the 3 corrections from §2
   │     - copies every PDF into telegram/assets/study_bot_flat/ under its new name
   │     - writes telegram/source-docs/1Lavya_Study_Hub_File_Mapping.xlsx
   │       (2 sheets: "Read Me First" + "File Mapping", matching the schema
   │       study_hub_bot.py's Catalog class expects)
   ▼
telegram/assets/study_bot_flat/*.pdf  +  telegram/source-docs/1Lavya_Study_Hub_File_Mapping.xlsx
   (what study_hub_bot.py actually reads at startup)
```

**Both scripts are idempotent** — `build_study_bot_catalog.py` wipes and regenerates
`study_bot_flat/` and the Excel from scratch every run. **Never hand-edit either output**
(rename a file in the flat folder, or edit a row in the Excel directly) — the two will
silently drift apart. Fix the source (a title in `TITLE_OVERRIDES`, a new PDF added to
the nested tree if it still exists, a `COURSE_META` entry for a new subject) and re-run.

**The nested source tree no longer exists in this repo** (deleted once the flat copy was
verified complete — Pranav's explicit call, "delete the older version to avoid
duplication"). If new PDFs need to be added later (a new subject, a new session), drop
them into a same-shaped nested tree, run `scan_study_bot_source.py` first to verify them
the same way, then run `build_study_bot_catalog.py` — it will pick up anything under
`telegram/assets/study_bot/` if that folder is recreated, and merges cleanly with
whatever's already in `COURSE_META`/`TITLE_OVERRIDES`.

## 5. Credentials

The bot's Telegram token lives in `telegram/creds.txt` (gitignored — see `.gitignore`'s
"Secrets / credentials" section, added 2026-08-07 alongside `desktop.ini`), in
`Name: <BotUsername>` / `Bot Token: <token>` blocks, one per bot (Study Hub / Exam Hub /
MyFiles Hub all share this one file). `study_hub_bot.py` parses its own token out of that
file at import time (`load_token_from_creds()`), falling back to nothing (a clear
`SystemExit` at startup, not a silent failure) if neither the file nor the
`TELEGRAM_STUDY_BOT_TOKEN` env var provides one. **The token is never hardcoded in the
script** — an earlier version had a live token as the `os.environ.get(...)` fallback
default, which is exactly the kind of thing that ends up in git history the first time
someone runs `git add -A`; don't reintroduce that pattern.

## 6. Telegram `callback_data` has its own 64-byte limit — unrelated to filesystem limits

Found the hard way (Pranav tested the live bot, searched "Inventories", got
`telegram.error.BadRequest: Button_data_invalid`) right after this pipeline shipped.
The flat filenames in §3 are comfortably short for a *filesystem* (45–82 chars), but
`InlineKeyboardButton(callback_data=...)` has its own, much stricter cap: **64 bytes**,
enforced by Telegram itself, independent of anything about the file. The bot's original
code built every menu/search-result button's `callback_data` out of the literal
`FileName` (`f"file:{filename}"`) — 192 of the 380 generated filenames overflow that once
the `file:` prefix is added. The same bug independently existed for the **Subject**
picker too: `f"subject:{course}:{level}:{subject_name}"` overflows for any subject whose
full name is long (e.g. "Advanced Auditing, Assurance & Professional Ethics" — 23 of 380
rows), so Browse would have failed on that step even for someone who never used
free-text search.

**Fix** (in `study_hub_bot.py`, not the catalog pipeline itself — the Excel/flat-folder
outputs didn't need to change): `Catalog.load()` now resets the DataFrame to a
contiguous `0..N-1` index, and every callback that used to embed a `FileName` or a
`Subject` string now embeds that row's small integer index instead
(`Catalog.chapters()` attaches it as `row_id`; `Catalog.search_text()` returns
`(score, row_id, row_dict)`; `Catalog.get_row_by_id()` resolves it back). The Subject
picker uses the subject's position in `subjects(course, level)`'s list instead of its
name. Verified afterward by generating every possible `callback_data` string across the
full browse tree (401 of them) plus several free-text queries — max is now 23 bytes,
nowhere close to the limit, regardless of how long a filename or subject name is.

**Lesson for any future catalog change**: this ceiling has nothing to do with filenames,
paths, or Excel — it's specific to what gets put in a Telegram inline button's
`callback_data`. Never put a variable-length human-readable string there; use a stable
short id (int index, hash, whatever) and resolve it via the catalog, every time.

**Second bug, same incident**: even after the fix above, Pranav reported searching
"Inventories" still didn't show the CA Inter Advanced Accounting result ("Accounting
Standard 2 Valuation of Inventory"). Root cause was unrelated to callback_data: **21
chapters** score ≥60 against "Inventories" (the topic legitimately recurs across
Foundation/Inter/Final — same shape as the Cash Flow duplicate in §7), but
`TOP_N_SUGGESTIONS` was `3`. Two exact-title matches ("Inventories" in both CA Final and
CA Foundation, score 100) took 2 of the 3 slots; the AdvAcc chapter scored 72.7 in a
five-way tie for the last slot and lost it purely to sort-order luck, not relevance.
Fixed by raising `TOP_N_SUGGESTIONS` to `8` (covers every row scoring ≥65 for this real
query) and adding **Level** to each result's button label (`ChapterName — Level
Subject`) so a student can tell same-titled results at different levels apart, which the
label couldn't do before (it only showed Subject).

## 7. What deliberately is NOT solved here

- **CS / CMA content** — the bot's README always described CA/CS/CMA, but only CA
  material has ever existed on disk. Adding CS/CMA later is just new `COURSE_META`
  entries once those PDFs exist in the same nested-tree shape.
- **Cross-listed chapters** — some topics genuinely appear twice under different subjects
  because ICAI's own study material repeats them (e.g. Cash Flow Statement is both its own
  AS-3 chapter, `M1-C4-U2`, and again inside the "Financial Statements of Companies"
  chapter, `M3-C11-U2`, of CA Inter Advanced Accounting) — confirmed correct by reading
  both PDFs, not a tagging bug. A free-text search for "cash flow" will legitimately
  return both. This mirrors the exact same M1-C4-U2 vs. M3-C11-U2 duplicate-chapter
  situation already documented in `CLAUDE.md` §6's 2026-08-07 entry for the Question Bank
  pipeline — same two ICAI-real codes, same reasoning, independently encountered here.
- **`desktop.ini` clutter** — Windows folder-view metadata files were scattered across the
  repo (54 of them just inside the old nested `study_bot/` tree). Added a blanket
  `desktop.ini` rule to `.gitignore` as a side effect of this work; not otherwise cleaned
  up.
