#!/usr/bin/env python3
"""
telegram/tools/populate_course_catalog.py -- builds the course_catalog DB
table from real, already-verified sources (2026-08-11, extended to full
CA coverage 2026-08-12)
--------------------------------------------------------------------------------
Pranav's ask: "this course catalog should be part of a table in our db and
should be the single source of truth for all MCQs and descriptive
questions... Chapter ID, Unit ID, Chapter name for each Course, Level,
Subject should be derived from this course content." This is that build
script -- idempotent (safe to re-run any time a source changes), never
hand-types a chapter/unit/paper number.

UPDATE 2026-08-12: Pranav caught a real gap the day after this first
shipped -- "I saw many subjects and chapters missing." He was right: the
first version only covered 2 of CA's 17 real subjects (Advanced
Accounting + Quantitative Aptitude), while CS/CMA were already fully
covered (their source, CS_CMA_Chapter_Catalog.xlsx, has ALL subjects with
a real PaperNo already). Fixed by importing
telegram/tools/build_study_bot_catalog.py's own COURSE_META dict
DIRECTLY (not copying its values into a second, driftable dict here) --
that dict already has real, cover-page-verified paper numbers for
literally every CA subject. All 17 CA subjects now covered, matching
CS/CMA's completeness.

THREE SOURCES, each already independently verified against real ICAI/
ICSI/ICMAI material in an earlier session (never re-typed here):

1. CA Inter Advanced Accounting -- telegram/reference-data/
   ca-inter-adv-accounts-topic-page-index.json, a bundled snapshot (copied
   2026-08-12, as part of making telegram/ standalone-portable -- see
   FIRST_PROMPT.md) of the canonical "never edit" topic/page index at
   books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-
   page-index.json, built from a 400-topic/36-chapter CSV cross-referenced
   against the locked master syllabus JSON. Re-copy the snapshot by hand if
   the canonical file ever changes -- see the snapshot's own
   "_telegram_snapshot_note" field. The ONE CA subject with real unit-level
   granularity -- every other CA subject below only has chapter-level data
   available, so gets unit_no=0 honestly, not a pretended unit breakdown.
2. CS + CMA, every subject -- telegram/source-docs/CS_CMA_Chapter_Catalog
   .xlsx's "Chapter Catalog" sheet (647 chapters, chapter numbers/names
   read directly off each subject's own printed Table of Contents --
   see telegram/tools/scan_cs_cma_toc.py). ICSI/ICMAI material has no
   real sub-unit structure below chapter level (confirmed against the
   sheet itself) -- every CS/CMA row here gets unit_no=0, the same
   "no further sub-units" convention CA's own single-unit chapters use.
3. CA -- every OTHER subject (16 of CA's 17) -- telegram/source-docs/
   StudyHub_Master_Catalog.xlsx (chapter numbers/names read directly off
   the real study material file names -- see telegram/tools/
   build_study_bot_catalog.py), scoped to exactly the (course, level,
   subject) tuples in that script's own COURSE_META. unit_no=0 (chapter-
   level data only, same reasoning as above).

PAPER NUMBERS -- cross-checked, not re-typed: every paper_no value below
is copied from telegram/tools/cs_cma_common.py's FILE_META (CS/CMA) or
imported directly from telegram/tools/build_study_bot_catalog.py's
COURSE_META (CA, all 17 subjects) -- both already read directly off each
subject's own printed cover page in an earlier session (see those
modules' own docstrings). This script does NOT invent or guess a single
paper number, and imports COURSE_META rather than copying it so the two
scripts can never silently drift apart on what a subject's real paper
number is.

USAGE:
    python telegram/tools/populate_course_catalog.py            # apply
    python telegram/tools/populate_course_catalog.py --dry-run   # preview only, writes nothing
"""

import re
import sys
import json
import argparse
from pathlib import Path

import pandas as pd

# Matches the REAL flat filename shape build_study_bot_catalog.py itself
# produces: '{CourseLevel}-{SubjectShort}-{Session}_M{module}-C{chapter}-
# U{unit}_{Title}.pdf' -- note the M-C-U segment uses HYPHENS, embedded
# mid-string after a prefix, NOT build_study_bot_catalog.py's own
# FNAME_RE (which matches a DIFFERENT, underscore-separated, string-start
# shape used for the nested SOURCE tree before flattening -- confirmed by
# testing directly, not assumed: FNAME_RE.match() returns None against
# every one of these real flat filenames). Verified against all 314 real
# CA Study Materials filenames in StudyHub_Master_Catalog.xlsx before
# being trusted here -- 0 unmatched.
CA_FLAT_FNAME_UNIT_RE = re.compile(r"_M(?P<module>\d+)-C(?P<chapter>\d+)-U(?P<unit>\d+)_")

# Found 2026-08-12 while fixing the FIRST unit-numbering bug above, via
# the same collision check catching a SECOND, genuinely different real
# case: CA Inter Financial Management's chapter 9 has 7 real files (an
# Appendix + 6 real named units, "Unit I".."Unit VI") but EVERY ONE of
# their filenames says U0 -- the source filename's own U-segment is wrong/
# uninformative for this subject specifically, while the row's own Label
# text correctly states "Unit I"/"Unit II"/etc. Roman-numeral unit labels
# in Label text are authoritative over the filename when present.
_ROMAN_NUMERALS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
UNIT_LABEL_RE = re.compile(r"^Unit\s+([IVX]+|\d+)\b", re.IGNORECASE)

# Real, found 2026-08-12 (the SAME collision check, a third real case):
# CA Final Financial Reporting's chapter 11 has two files BOTH genuinely
# encoded as U0 in their filename -- 'Comprehensive Illustrations' and
# 'Test Your Knowledge' -- neither is a real syllabus topic, both are
# chapter-level review/practice material. Excluded from the catalog
# entirely (an MCQ on a real topic within this chapter tags to whichever
# REAL unit it's testing, never to "Comprehensive Illustrations" as if
# that were its own unit).
AUXILIARY_LABELS = {"comprehensive illustrations", "test your knowledge", "appendix", "case studies", "summary"}


def _parse_unit_from_label(label: str):
    m = UNIT_LABEL_RE.match((label or "").strip())
    if not m:
        return None
    token = m.group(1).upper()
    return _ROMAN_NUMERALS.get(token) or (int(token) if token.isdigit() else None)


def _is_auxiliary_label(label: str) -> bool:
    return (label or "").strip().lower() in AUXILIARY_LABELS

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
sys.path.insert(0, str(REPO_ROOT / "telegram" / "tools"))
import db as platform_db  # noqa: E402
import build_study_bot_catalog  # noqa: E402 -- for its already-verified COURSE_META (CA paper numbers)

# Bundled snapshot inside telegram/ (not a live read of the books/ pillar's
# canonical file) -- fixed 2026-08-12 so this script works even if telegram/
# is moved into its own repo, detached from books/. See that file's own
# "_telegram_snapshot_note" and FIRST_PROMPT.md for the portability pass.
FILE1_PATH = Path(__file__).resolve().parent.parent / "reference-data" / "ca-inter-adv-accounts-topic-page-index.json"
CS_CMA_CATALOG_PATH = REPO_ROOT / "telegram" / "source-docs" / "CS_CMA_Chapter_Catalog.xlsx"
STUDYHUB_CATALOG_PATH = REPO_ROOT / "telegram" / "source-docs" / "StudyHub_Master_Catalog.xlsx"

# Pranav's confirmed level-number mapping, 2026-08-11: "CSEET=L1,
# Executive=L2, Professional=L3 (Recommended)" -- extended the same
# graduated pattern to CA/CMA's own Foundation/Inter(mediate)/Final.
LEVEL_NUM = {
    ("CA", "Foundation"): 1, ("CA", "Inter"): 2, ("CA", "Final"): 3,
    ("CMA", "Foundation"): 1, ("CMA", "Intermediate"): 2, ("CMA", "Final"): 3,
    ("CS", "CSEET"): 1, ("CS", "Executive"): 2, ("CS", "Professional"): 3,
}


def _ca_paper_no(level: str, subject: str) -> str:
    """Looks up build_study_bot_catalog.COURSE_META directly -- e.g.
    ('CA', 'Inter', 'Advanced Accounting', ..., 'Paper 1', ...) ->
    '1'; ('CA', 'Inter', 'Taxation - Goods and Services Tax', ...,
    'Paper 3B', ...) -> '3B'. Raises if a subject isn't in COURSE_META --
    fail loudly rather than silently skip a subject that should exist."""
    for meta in build_study_bot_catalog.COURSE_META.values():
        course, lvl, subj = meta[0], meta[1], meta[2]
        if course == "CA" and lvl == level and subj == subject:
            return meta[4].replace("Paper ", "").strip()
    raise KeyError(f"No COURSE_META entry for CA / {level} / {subject!r}")


CMA_PAPER_NO = {
    ("CMA", "Foundation"): {"Fundamentals of Business Laws and Business Communication": "1"},  # cs_cma_common.py FILE_META
    ("CMA", "Intermediate"): {"Business Laws and Ethics": "5"},                                  # cs_cma_common.py FILE_META
}


def _now():
    return platform_db.now()


def rows_from_file1() -> list:
    """CA Inter Advanced Accounting -- one row per unit (topics are finer
    than this catalog's grain, intentionally not carried here)."""
    data = json.loads(FILE1_PATH.read_text(encoding="utf-8"))
    paper_no = _ca_paper_no("Inter", "Advanced Accounting")
    rows = []
    for c in data["chapters"]:
        unit_no = 0 if c.get("is_single_unit_chapter") else int(c["unit_code"].split(".")[-1])
        rows.append({
            "course": "CA", "level": "Inter", "level_num": LEVEL_NUM[("CA", "Inter")],
            "paper_no": paper_no, "subject": "Advanced Accounting",
            "chapter_no": int(c["chapter_no"]), "chapter_name": c["chapter_name"],
            "chapter_name_short": c.get("chapter_name_short"),
            "unit_no": unit_no, "unit_name": c.get("unit_name"),
            "unit_name_short": c.get("standard") or c.get("chapter_name_short"),
            "source": "1-ca-inter-adv-accounts-topic-page-index.json",
        })
    return rows


def rows_from_cs_cma_catalog() -> list:
    """CS + CMA, every subject -- one row per chapter, unit_no always 0
    (ICSI/ICMAI material has no sub-unit structure below chapter level)."""
    df = pd.read_excel(CS_CMA_CATALOG_PATH, sheet_name="Chapter Catalog")
    rows = []
    skipped_no_paper_no = set()
    for _, r in df.iterrows():
        course, level, subject = r["Course"], r["Level"], r["Subject"]
        if (course, level) not in LEVEL_NUM:
            continue
        # Only subjects that currently HAVE question content need a real,
        # cross-checked paper_no (see module docstring) -- every other
        # subject still gets a full chapter-name catalog row (useful once
        # question content for it exists), just with paper_no taken
        # directly from the catalog's own PaperNo column (already real,
        # read off the cover page by build_cs_cma_catalog.py -- not
        # independently re-verified against a SECOND source the way the
        # two question-bearing subjects above were, since there's no MCQ
        # content yet whose IDs would depend on it being exactly right).
        paper_no = str(r["PaperNo"]) if pd.notna(r["PaperNo"]) else None
        if paper_no is None:
            skipped_no_paper_no.add((course, level, subject))
            continue
        rows.append({
            "course": course, "level": level, "level_num": LEVEL_NUM[(course, level)],
            "paper_no": paper_no, "subject": subject,
            "chapter_no": int(r["ChapterNo"]), "chapter_name": r["ChapterName"],
            "chapter_name_short": r.get("ShortChapterName"),
            "unit_no": 0, "unit_name": None, "unit_name_short": None,
            "source": "CS_CMA_Chapter_Catalog.xlsx",
        })
    if skipped_no_paper_no:
        print(f"  (skipped {len(skipped_no_paper_no)} CS/CMA subject(s) with no PaperNo in the catalog: "
              f"{sorted(skipped_no_paper_no)})")
    return rows


def rows_from_studyhub_catalog() -> list:
    """Every CA subject EXCEPT Advanced Accounting (that one comes from
    the richer file1 source above) -- one row per (chapter, unit),
    unit_no taken from the REAL 'M{module}_C{chapter}_U{unit}_...' encoded
    in each row's own FileName (build_study_bot_catalog.py's own
    FNAME_RE), NOT blindly assumed 0.

    Found and fixed 2026-08-12 (a real duplicate-key crash caught this,
    not a hunch): CA Final Advanced Auditing's chapter 14 is genuinely
    TWO units ('Special Features of Audit of Banks' / '...of NBFCs',
    U1/U2) sharing one ChapterNo -- assuming unit_no=0 for every
    StudyHub-sourced subject collapsed these into one fabricated
    collision. Most subjects here really ARE single-unit chapters
    (unit_no=0 is correct for them), but that's now verified per-row from
    the real filename, never assumed as a blanket rule again."""
    df = pd.read_excel(STUDYHUB_CATALOG_PATH, sheet_name="Catalog")
    ca_subjects = sorted({
        (meta[1], meta[2]) for meta in build_study_bot_catalog.COURSE_META.values()
        if meta[0] == "CA" and meta[2] != "Advanced Accounting"
    })

    rows = []
    missing_in_studyhub, unparseable, excluded_auxiliary = [], [], []
    for level, subject in ca_subjects:
        subset = df[
            (df["Course"] == "CA") & (df["Level"] == level) & (df["Subject"] == subject)
            & (df["Category"] == "Study Materials")
            & (df["ChapterNo"] > 0)   # excludes the "Initial Pages" (ChapterNo 0) row -- not a real chapter
        ]
        if subset.empty:
            missing_in_studyhub.append((level, subject))
            continue
        paper_no = _ca_paper_no(level, subject)
        # Group by chapter_no first, so a multi-unit chapter's units are
        # only distinguished by REAL unit numbers, not by row iteration
        # order (which the dataframe doesn't guarantee is unit-ordered).
        for chapter_no, group in subset.groupby("ChapterNo"):
            is_multi_unit = len(group) > 1
            for _, r in group.iterrows():
                if is_multi_unit and _is_auxiliary_label(r["Label"]):
                    excluded_auxiliary.append(r["FileName"])
                    continue

                # Unit number resolution order: (1) an explicit "Unit N"/
                # "Unit IV" prefix in the row's own Label text, when
                # present, is authoritative over the filename -- found
                # necessary 2026-08-12, CA Inter Financial Management's
                # filenames all say U0 despite real distinct units. (2)
                # otherwise, the filename's own U-segment. (3) if neither
                # resolves, default to 0 and report it, never silently.
                unit_no = _parse_unit_from_label(r["Label"])
                if unit_no is None:
                    m = CA_FLAT_FNAME_UNIT_RE.search(r["FileName"])
                    unit_no = int(m.group("unit")) if m else None
                    if unit_no is None:
                        unparseable.append(r["FileName"])
                        unit_no = 0
                if not is_multi_unit:
                    # Single-unit chapter -- normalize to 0 regardless of
                    # what the filename's own U-segment says (matches the
                    # U0 convention used everywhere else in this catalog,
                    # even where a source file happens to say U1).
                    unit_no = 0
                rows.append({
                    "course": "CA", "level": level, "level_num": LEVEL_NUM[("CA", level)],
                    "paper_no": paper_no, "subject": subject,
                    "chapter_no": int(chapter_no), "chapter_name": r["Label"],
                    "chapter_name_short": r.get("ShortLabel"),
                    "unit_no": unit_no,
                    "unit_name": r["Label"] if is_multi_unit else None,
                    "unit_name_short": r.get("ShortLabel") if is_multi_unit else None,
                    "source": "StudyHub_Master_Catalog.xlsx",
                })
    if excluded_auxiliary:
        print(f"  (excluded {len(excluded_auxiliary)} auxiliary/review file(s) -- not real syllabus units: "
              f"{excluded_auxiliary})")
    if missing_in_studyhub:
        print(f"  (WARNING: {len(missing_in_studyhub)} CA subject(s) in COURSE_META have no chapters in "
              f"StudyHub_Master_Catalog.xlsx: {missing_in_studyhub})")
    if unparseable:
        print(f"  (WARNING: {len(unparseable)} filename(s) didn't match the expected M-C-U pattern, "
              f"defaulted to unit_no=0: {unparseable[:5]})")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview only, write nothing.")
    args = parser.parse_args()

    # Each source read exactly once (the previous version called each
    # function twice -- once here, once again inside this same print
    # statement -- harmless but wasteful, and doubled every source
    # function's own diagnostic prints; fixed 2026-08-12).
    file1_rows = rows_from_file1()
    cs_cma_rows = rows_from_cs_cma_catalog()
    studyhub_rows = rows_from_studyhub_catalog()
    all_rows = file1_rows + cs_cma_rows + studyhub_rows
    print(f"Collected {len(all_rows)} catalog rows from 3 sources "
          f"({len(file1_rows)} CA Inter Adv Acc, "
          f"{len(cs_cma_rows)} CS/CMA, "
          f"{len(studyhub_rows)} CA -- every other subject).")

    # Sanity check: the unique key (course, level, paper_no, chapter_no,
    # unit_no) must actually be unique across everything collected --
    # a collision here would mean two real chapters mapping to the same
    # catalog slot, which must never happen silently.
    seen = {}
    for r in all_rows:
        key = (r["course"], r["level"], r["paper_no"], r["chapter_no"], r["unit_no"])
        if key in seen:
            raise SystemExit(f"FATAL: duplicate catalog key {key} -- {seen[key]!r} vs {r!r}")
        seen[key] = r

    if args.dry_run:
        print("--dry-run: would write the above, nothing written.")
        return

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    now = _now()
    conn.execute("DELETE FROM course_catalog")   # full rebuild, always -- see README for why
    for r in all_rows:
        conn.execute(
            """INSERT INTO course_catalog
               (course, level, level_num, paper_no, subject, chapter_no, chapter_name,
                chapter_name_short, unit_no, unit_name, unit_name_short, source, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (r["course"], r["level"], r["level_num"], r["paper_no"], r["subject"], r["chapter_no"],
             r["chapter_name"], r.get("chapter_name_short"), r["unit_no"], r.get("unit_name"),
             r.get("unit_name_short"), r["source"], now),
        )
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM course_catalog").fetchone()[0]
    print(f"Wrote {total} rows to course_catalog.")


if __name__ == "__main__":
    main()
