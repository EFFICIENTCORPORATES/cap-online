# SKILL — Study Hub Bot: Unified 3-Category, 3-Course Architecture

> **What this is:** on 2026-08-08, Pranav restructured `telegram/assets/` from separate
> per-course flat folders into `telegram/assets/study_bot/{Study Materials, Exam
> Materials, Revision Material}/` and populated it with all of CA + CS + CMA content —
> 1,026 Study Materials files (380 CA + 646 CS/CMA) and 58 Exam Materials files (CA Inter
> Advanced Accounting only, so far). This skill documents the catalog-unification layer
> and the bot rewrite that followed. Read `SKILL-study-bot-catalog-pipeline.md` (CA) and
> `SKILL-cs-cma-toc-pipeline.md` (CS/CMA) first — this is the layer *above* both of them,
> not a replacement.

---

## 1. The folder structure this targets

```
telegram/assets/study_bot/
├── Study Materials/     1,026 PDFs -- one per chapter, all three courses mixed together
├── Exam Materials/         58 PDFs -- MTP/PYQ/RTP papers (CA Inter AdvAcc only, so far)
└── Revision Material/       0 PDFs -- not populated yet
```

All three are **flat** (no subfolders) — same reasoning as the original CA-only
`study_bot_flat/` folder this superseded: Telegram's bot API sends a file by path, and a
flat layout with self-describing filenames is simplest to keep in sync with a generated
catalog. `telegram/assets/backup pdfs/` holds the original CS/CMA consolidated PDFs +
their once-flat `cs_cma_flat/` output — a backup from the restructuring, not read by
anything; leave it alone unless asked.

## 2. One master catalog, built from three sources

`telegram/tools/build_master_catalog.py` produces
`telegram/source-docs/StudyHub_Master_Catalog.xlsx` (sheet `Catalog`) — the **only** file
the bot itself reads. It merges:

1. **CA Study Materials** — `1Lavya_Study_Hub_File_Mapping.xlsx` (built by
   `build_study_bot_catalog.py`), remapped into the unified schema.
2. **CS/CMA Study Materials** — `CS_CMA_Chapter_Catalog.xlsx` (built by
   `build_cs_cma_catalog.py` + `split_cs_cma_pdfs.py --execute`), same remapping. Rows
   with no real page range (e.g. the ESG "merged lesson" — see
   `SKILL-cs-cma-toc-pipeline.md` §4) are dropped here, since there is no file for them.
3. **Exam Materials** — **parsed directly from filenames**, no upstream Excel. The
   existing naming convention already encodes everything needed:
   `{CourseLevel}-{SubjectShort}-{MTP|PYQ|RTP}-{Session}[-SetN]-{Q|Ans}.pdf`, or
   `{CourseLevel}-{SubjectShort}-PYQ_Examiner_Comments-{Session}.pdf`. Three regexes
   handle the three shapes (`MTP_RE`, `PYQ_EC_RE`, `SIMPLE_RE`); an unmatched filename is
   reported loudly, never silently dropped. `CourseLevel` (e.g. `CAInter`) is split back
   into `(Course, Level)` via a small hardcoded 9-entry table (`COURSELEVEL_PREFIXES`) —
   one entry per `{course}{level_code}` combination already used by the two Study
   Materials build scripts, so it stays consistent automatically. `SubjectShort` (e.g.
   `AdvAcc`) is resolved to its full Subject name (`Advanced Accounting`) by matching the
   same `<CourseLevel>-<SubjectShort>` prefix against the already-loaded Study Materials
   rows' own filenames — no separate subject-name table to maintain.
4. **Revision Material** — currently empty; `load_revision_rows()` has generic best-effort
   handling (same prefix-splitting as Exam Materials) ready for whenever it's populated,
   so this script shouldn't need touching again just because files appear there.

**Self-cross-checking, every run**: `cross_check_against_disk()` verifies every catalog
row has a matching file in its category folder, *and* every real file has a matching
catalog row, in both directions, for all three categories. Any mismatch is printed
loudly — the script never silently drops a file or fabricates a row.

Re-run order after any source change: whichever of `build_study_bot_catalog.py` /
`build_cs_cma_catalog.py` (+`split_cs_cma_pdfs.py --execute`) produced the change, **then**
`build_master_catalog.py` last, since it reads the other two catalogs' output.

## 3. Unified catalog schema

One row per file, same columns regardless of category (blank where not applicable):
`Category, Course, Level, Subject, Label, ShortLabel, ChapterNo, PaperType, Session,
SetLabel, DocType, Keywords, FileName`. Study/Revision rows use `ChapterNo`+`Label`
(chapter number + name); Exam rows use `PaperType`+`Session`+`SetLabel`+`DocType` instead
and leave `ChapterNo` blank. This lets the bot's `Catalog` class use one `pandas`
DataFrame and one set of filter-by-column helper methods for everything, rather than
branching on category throughout.

## 4. Bot browse-tree redesign

`study_hub_bot.py`'s menu is now **Category → Course → Level → Subject → (Chapter |
Paper Type → file)**:
- **Category first** (not Course), because it's a one-time top-level choice matching how
  the folders are physically organized, and it avoids forcing every single subject
  through an always-mostly-empty Category submenu (Exam Materials only has content for
  one subject today; Revision Material has none) — see §5 for the empty-category UX.
- Courses/Levels/Subjects/Paper-Types shown at each step are **computed dynamically**
  from whatever the catalog actually contains for the categories/courses chosen so far
  (`courses_for_category()`, `levels_for()`, `subjects_for()`, `paper_types_for()`) — the
  bot never hardcodes "CA has Foundation/Inter/Final"; if CS/CMA/a new course/a new level
  gets added to the catalog, the menu grows automatically with zero code changes.
- **Exam Materials gets one extra step (Paper Type)** before the flat file list, because
  a single subject can have 30+ exam files (multiple sessions × sets × Q/Ans) — grouping
  by MTP/PYQ/RTP first keeps each screen manageable. Study/Revision Materials skip
  straight from Subject to a flat chapter list, same as the original CA-only bot.

## 5. Empty-category handling (Revision Material today, generically)

`courses_for_category()` on a category with zero rows returns `[]`. `browse_callback`'s
`cat` branch checks for this and shows *"No {category} available yet — check back
soon!"* with a Back button, instead of rendering an empty (and confusing) course-picker
keyboard. This needed no special-casing beyond that one check — the same code path will
start working normally the moment `build_master_catalog.py` finds real files under
`Revision Material/` on some future run.

## 6. The 64-byte `callback_data` lesson, applied one level deeper

Same discipline as `SKILL-study-bot-catalog-pipeline.md` §6 (which documents the incident
that taught this the hard way) — extended to the new Category and Paper-Type dimensions:
`Category` is passed as `cat_idx` (its index into the fixed `CATEGORIES` list), never the
literal string; `Subject` stays index-based as before; `PaperType`/`Course`/`Level` are
safe as literal strings only because they're short, fixed-vocabulary values (`MTP`,
`CA`, `Inter`, ...) — never do this for anything free-text or user-authored. Verified
end-to-end for real: generating every possible `callback_data` string across the entire
current browse tree (1,172 of them) gives a max of 25 bytes.

## 7. Known gaps, honestly

- **Exam Materials covers exactly one subject** (CA Inter Advanced Accounting) — the
  pipeline is generic (any file following the naming convention gets catalogued
  automatically), but no other subject's MTP/PYQ/RTP papers have been sourced into
  `Exam Materials/` yet.
- **Revision Material is empty.** The bot and catalog both handle this gracefully, but
  there's no content to serve there yet, and its eventual file-naming convention is
  unknown — `load_revision_rows()`'s generic handling is a best guess, not a designed
  spec; revisit it once real files exist and a real naming convention is chosen.
- **`telegram/assets/backup pdfs/`** is not part of the served catalog and was not
  audited as part of this work (it's a backup, presumably safe to eventually delete once
  Pranav confirms `Study Materials/` is trusted as complete, but that's his call).
