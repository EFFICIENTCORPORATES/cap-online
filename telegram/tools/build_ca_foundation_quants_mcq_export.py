"""
Combine the CA Foundation Quantitative Aptitude per-chapter MCQ files into
one bot-ready JSON.
------------------------------------------------------------------------
Source: telegram/assets/exam_bot/ca-foundation-quantitative-aptitude/
Chapt N.json -- one file per chapter, already in the platform's standard
MCQ record shape (mcq_id, course, level, exam_type, year, question_html,
options, correct_option, answer_html, chapter_slug, chapter_label,
unitcode, topic_text, source_kind, faculty_id, faculty_name, ...).

As of 2026-08-11: chapters 1-14, 16, 17 (16 files, 625 records) -- chapter
15 doesn't exist yet (not an error, just not provided), and chapter 18
("Chapt 18.json", Index Numbers) uses a completely different, non-bot-ready
shape (no question_html/options-dict/correct_option/answer_html at all --
just {chapter, title, exercise_mcqs: [{question, options: ["a) ...", ...],
answer: "a"}]}, no explanations). This script SKIPS any file that doesn't
parse into the expected record shape (logs it, doesn't crash) rather than
guessing at a conversion -- Chapter 18 needs either a real conversion pass
(including authoring genuine explanations, since none exist in the source)
or a reshaped source file before it can be included.

This script:
  1. Reads all "Chapt N.json" files in chapter-number order (1, 2, ..., 18
     -- not lexical order, which would put Chapter 10 before Chapter 2),
     skipping any chapter number that doesn't exist and any file that
     isn't a flat list of MCQ-shaped records.
  2. Standardizes every mcq_id to one uniform pattern:
     CA-FND-QUANTS-C{chapter}-Q{qno} -- fixes:
       - Chapters 1-12 used subject code "MATH"; chapters 13-14/16/17 used
         "MATH" or "STAT" with an extra "-U<n>-" segment no chapter's
         FINAL id should carry (e.g. CAI-FND-STAT-C14-U1-Q001, also note
         the stray extra "I" in "CAI").
       - "MATH"/"STAT" -> "QUANTS", to match the short subject code Study
         Hub's own catalog already uses for this whole paper (see
         telegram/tools/build_study_bot_catalog.py's COURSE_META,
         "ca-found-quants-..." / short label "Quants") -- one subject-code
         convention shared across bots instead of several.
  3. Normalizes "unitcode" to always carry the "M1-" module prefix
     (chapters 14/16/17 arrived as bare "C14-U1" instead of "M1-C14-U1",
     inconsistent with chapters 1-13's own already-M1-prefixed values).
     Not read by any bot code -- purely for consistency/future use.
  4. Adds a "subject": "Quantitative Aptitude" field to every record
     (inserted right after "level"). Not read by any bot code today --
     this is purely for future course/subject/chapter grouping (e.g. a
     dashboard summary) -- adding it now costs nothing and avoids having
     to backfill it later.
  5. Writes the combined, chapter-ordered list to
     mcq_questions_extracted.json in that same folder -- matching the
     filename convention every other bank in this repo already uses
     (telegram/assets/exam_bot/mcq_questions_extracted.json,
     telegram/assets/exam_bot/faculty/csarunchouhan/mcq_questions_extracted.json).

Re-run whenever a source "Chapt N.json" file changes or a new chapter is
added -- this script always reads fresh and overwrites its output in
full; nothing in the output is hand-patched.

Usage: python telegram/tools/build_ca_foundation_quants_mcq_export.py
"""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

SOURCE_DIR = os.path.join(
    REPO_ROOT, "telegram", "assets", "exam_bot", "ca-foundation-quantitative-aptitude"
)
OUTPUT_PATH = os.path.join(SOURCE_DIR, "mcq_questions_extracted.json")

CHAPTER_NUM_RE = re.compile(r"Chapt\s*(\d+)", re.IGNORECASE)
# Covers every id shape seen so far: CA-FND-MATH-C1-Q001 (ch 1-12),
# CA-FND-MATH-C13-U1-Q001 (ch 13), CAI-FND-STAT-C14-U1-Q001 (ch 14/16/17).
OLD_ID_RE = re.compile(r"^CAI?-FND-(?:MATH|STAT)-C(\d+)(?:-U\d+)?-Q(\d+)$")

SUBJECT_LABEL = "Quantitative Aptitude"


def chapter_num(filename: str) -> int:
    m = CHAPTER_NUM_RE.search(filename)
    if not m:
        raise ValueError(f"Can't find a chapter number in filename: {filename}")
    return int(m.group(1))


def standardize_id(mcq_id: str) -> str:
    m = OLD_ID_RE.match(mcq_id)
    if not m:
        raise ValueError(f"mcq_id doesn't match any known pattern: {mcq_id!r}")
    chap, qno = m.group(1), m.group(2)
    return f"CA-FND-QUANTS-C{chap}-Q{qno}"


def normalize_unitcode(unitcode):
    if isinstance(unitcode, str) and unitcode and not unitcode.startswith("M"):
        return f"M1-{unitcode}"
    return unitcode


def with_subject(record: dict) -> dict:
    """Return a copy of record with 'subject' inserted right after 'level'."""
    out = {}
    for k, v in record.items():
        out[k] = v
        if k == "level":
            out["subject"] = SUBJECT_LABEL
    if "subject" not in out:  # defensive: only if a record has no "level" key at all
        out["subject"] = SUBJECT_LABEL
    return out


def main():
    files = sorted(
        glob.glob(os.path.join(SOURCE_DIR, "Chapt *.json")),
        key=lambda p: chapter_num(os.path.basename(p)),
    )
    if not files:
        raise SystemExit(f"No 'Chapt *.json' files found in {SOURCE_DIR}")

    combined = []
    per_file_counts = []
    skipped = []
    for path in files:
        fn = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            rows = json.load(f)

        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict) or "mcq_id" not in rows[0]:
            skipped.append((fn, "not a flat list of MCQ-shaped records (needs conversion first)"))
            continue

        try:
            for r in rows:
                r["mcq_id"] = standardize_id(r["mcq_id"])
                r["unitcode"] = normalize_unitcode(r.get("unitcode"))
                r = with_subject(r)
                combined.append(r)
        except ValueError as e:
            skipped.append((fn, str(e)))
            continue

        per_file_counts.append((fn, len(rows)))

    ids = [r["mcq_id"] for r in combined]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"Duplicate mcq_ids after standardization -- aborting, nothing written: {dupes}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"Combined {len(per_file_counts)} chapter files ({sum(c for _, c in per_file_counts)} records) "
          f"into {OUTPUT_PATH}")
    for fn, c in per_file_counts:
        print(f"    {fn}: {c}")
    if skipped:
        print(f"\nSkipped {len(skipped)} file(s) -- not included in the output, needs attention:")
        for fn, reason in skipped:
            print(f"    {fn}: {reason}")


if __name__ == "__main__":
    main()
