#!/usr/bin/env python3
"""
generate_book_stats.py -- computes the Question Bank Book's coverage
statistics (attempts covered, question counts, total marks) and writes
them as a machine-readable JSON file, entirely from questions_index.json
(Layer 2 -- the mechanical, no-AI-judgment extraction built by
extract_questions.py from every sitting's tagged HTML). No number in this
script is hand-typed; re-run it any time the underlying sittings change and
every figure updates itself.

WHY questions_index.json AND NOT THE 34 CHAPTER BOOK FILES
------------------------------------------------------------
generate_chapter_book.py was substantially rewritten since this pipeline's
last chapter-book regeneration (confirmed 2026-07-27: all 34
*_Question_Book.html files now dated one batch, 2026-07-26 20:2x-20:3x,
noticeably after this session's earlier merge work) -- MCQs are now
deliberately excluded from the rendered chapter books ("practise those on
the dedicated MCQ platform" per that script's own comment), and a richer
built-in self-notes/notebook-ref/tag/revision-phase block plus a
brand-header/footer and an error-register section were added per chapter.
That's a real, current policy about what gets PRINTED -- but this book's
STATISTICS should describe the underlying question corpus itself (every
sitting, every question type, including MCQs), not just whatever subset a
particular rendering policy currently chooses to typeset. Reading Layer 2
directly keeps this script's numbers stable and honest regardless of how
that rendering policy evolves -- and it explicitly reports the MCQ-vs-
rendered split (see "chapter_book_policy" in the output) so nobody reading
the stats page mistakes "questions in the corpus" for "questions printed
in the chapter books" -- they are two different, both true, numbers.

MARKS TOTAL -- WHY IT ISN'T JUST sum(marks)
------------------------------------------------
OR-alternative questions (e.g. "6(a) AS 24 theory OR 6(a) Amalgamation
problem") are stored as two separate rows sharing one data-alt-group, by
design (see CLAUDE.md section 6 / SKILL-question-bank-question-splitting.md)
-- a student only ever answers ONE of them, so summing both rows' marks
would overstate the paper's real total. This script reuses the exact
alt-group-dedup logic extract_questions.py already uses for its own
per-file sanity check (count each alt_group only once), applied globally
instead of per-file, to get one honest whole-book marks total.

USAGE
-----
    python generate_book_stats.py
        Prints a console summary and writes
        first_run/output/generated-from-script/book_stats.json

    python generate_book_stats.py --check
        Same, but does not write the file (dry run for a quick look).
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qb_common as qc  # noqa: E402

INDEX_PATH = qc.OUTPUT_DIR / "generated-from-script" / "questions_index.json"
STATS_OUT_PATH = qc.OUTPUT_DIR / "generated-from-script" / "book_stats.json"

MONTH_NAMES = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}

# qtypes that count as MCQ for the purposes of "how many questions are
# actually printed in the chapter books" -- matches generate_chapter_book.py's
# own filter (`row["qtype"] not in ("mcq", "case-mcq")` for its Descriptive
# section) exactly, so this script's "excluded from chapter books" figure
# can never silently drift out of sync with what that script really does.
MCQ_QTYPES = {"mcq", "case-mcq"}


def load_index() -> list:
    if not INDEX_PATH.exists():
        raise SystemExit(
            f"ERROR: {INDEX_PATH} not found -- run extract_questions.py first "
            "(it builds this file from the sitting HTML files)."
        )
    with INDEX_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def sitting_label(row: dict) -> str:
    ptype = row.get("paper_type") or ""
    month = MONTH_NAMES.get(row.get("exam_month"), row.get("exam_month") or "")
    year = row.get("exam_year") or ""
    label = f"{ptype} {month} {year}".strip()
    if row.get("set"):
        label += f" Set {row['set']}"
    return label


def dedup_marks_total(rows: list) -> int:
    """Sum every row's marks, EXCEPT for OR-alternative rows sharing a
    data-alt-group -- those are counted only once (the group's first-seen
    row), since a student only ever answers one alternative. Same logic as
    extract_questions.py's own per-file sanity check, applied book-wide."""
    total = 0
    seen_alt_groups = set()
    for row in rows:
        marks = row.get("marks") or 0
        ag = row.get("alt_group")
        if ag:
            key = (row["source_file"], ag)
            if key in seen_alt_groups:
                continue
            seen_alt_groups.add(key)
        total += marks
    return total


def distinct_question_number_count(rows: list) -> int:
    """How many questions were printed in the original papers, BEFORE this
    pipeline's independent-sub-part splitting turned e.g. one "Q6(a)+(b)"
    into two separate rows, and before OR-alternatives duplicated a slot
    into two rows. Groups by (sitting, the question's real printed number)
    -- parent_qno when a row is a split sub-part, qno otherwise -- so
    "Q6(a)" and "Q6(b)" collapse back into one "Q6", and an OR-alternative
    pair collapses into the one question slot it actually is."""
    seen = set()
    for row in rows:
        real_qno = row.get("parent_qno") or row.get("qno")
        seen.add((row["source_file"], real_qno))
    return len(seen)


def build_stats(rows: list) -> dict:
    sittings = sorted(set(r["source_file"] for r in rows))

    per_sitting = {}
    sittings_without_marks = []
    for sf in sittings:
        sitting_rows = [r for r in rows if r["source_file"] == sf]
        rep = sitting_rows[0]
        has_marks = any(r.get("marks") is not None for r in sitting_rows)
        if not has_marks:
            sittings_without_marks.append(sitting_label(rep))
        per_sitting[sf] = {
            "label": sitting_label(rep),
            "total_marks_of_paper": rep.get("total_marks"),
            "records_in_corpus": len(sitting_rows),
            "distinct_questions": distinct_question_number_count(sitting_rows),
            "marks_covered_here": dedup_marks_total(sitting_rows),
            "has_marks_in_source": has_marks,
        }

    qtype_counts = Counter(r.get("qtype") for r in rows)
    part_counts = Counter(r.get("part") for r in rows)
    mcq_rows = [r for r in rows if r.get("qtype") in MCQ_QTYPES]
    non_mcq_rows = [r for r in rows if r.get("qtype") not in MCQ_QTYPES]

    difficulty_counts = Counter(r.get("difficulty") for r in rows)

    real_comment_count = sum(
        1 for r in rows
        if r.get("examiner_comment") and r["examiner_comment"].get("comment_source") == "icai"
    )
    synthesized_note_count = sum(
        1 for r in rows
        if r.get("examiner_comment") and r["examiner_comment"].get("comment_source") != "icai"
    )

    # LEGACY-* final_chapter values mark pre-syllabus-change topics with no
    # real chapter in the current 36-chapter taxonomy (Pranav, 2026-07-28,
    # see CLAUDE.md §6) -- excluded from "chapters touched" since they don't
    # represent a real syllabus chapter, but counted separately below so the
    # exclusion is visible in the stats rather than silently invisible.
    all_chapters_touched = set(r.get("final_chapter") for r in rows if r.get("final_chapter"))
    legacy_chapters = sorted(c for c in all_chapters_touched if c.startswith("LEGACY-"))
    chapters_touched = sorted(c for c in all_chapters_touched if not c.startswith("LEGACY-"))
    legacy_rows = [r for r in rows if (r.get("final_chapter") or "").startswith("LEGACY-")]

    return {
        "generated_from": str(INDEX_PATH.relative_to(qc.FIRST_RUN)),
        "sittings": {
            "count": len(sittings),
            "list": [per_sitting[sf]["label"] for sf in sittings],
            "per_sitting": per_sitting,
        },
        "questions": {
            "total_records_including_parts_and_subparts": len(rows),
            "distinct_question_numbers_as_printed": distinct_question_number_count(rows),
            "by_qtype": dict(qtype_counts),
            "by_part": dict(part_counts),
            "by_difficulty": dict(difficulty_counts),
        },
        "marks": {
            "total_marks_covered_book_wide": dedup_marks_total(rows),
            "note": "OR-alternative rows (data-alt-group) counted once, "
                    "not twice, since a student only ever answers one. "
                    "RTP sittings contribute 0 to this total -- ICAI's own "
                    "RTP documents carry no per-question marks breakdown "
                    "(no answer key with marks is published for RTPs), not "
                    "a tagging gap -- see sittings_without_marks_in_source. "
                    "Each MTP/PYQ sitting sums to 114, not the paper's "
                    "nominal 100 -- verified (2026-07-27) this is expected, "
                    "not an error: Part II offers a 'answer any N of the "
                    "remaining M' choice (Q1-Q5 required marks = 70, but "
                    "Q1-Q6 are all shown = 84), and this book deliberately "
                    "includes every optional question so a student can "
                    "practice all of them, not just the ones one particular "
                    "sitting required. 30 (Part I) + 84 (Part II, all "
                    "options shown) = 114 consistently across all 7 "
                    "MTP/PYQ sittings checked.",
            "sittings_without_marks_in_source": sittings_without_marks,
        },
        "chapters_touched_count": len(chapters_touched),
        "legacy_pre_syllabus_topics": {
            "note": "Records tagged LEGACY-* test topics from before a syllabus "
                    "change (e.g. Hire Purchase, Departmental Accounts) that don't "
                    "exist in the current 36-chapter taxonomy at all. Kept in the "
                    "sitting HTML/questions_index.json for a complete record, but "
                    "excluded from chapter books and from chapters_touched_count "
                    "above -- Pranav's decision, 2026-07-28.",
            "distinct_legacy_topics": len(legacy_chapters),
            "legacy_topic_codes": legacy_chapters,
            "records_excluded": len(legacy_rows),
        },
        "mistake_notes": {
            "real_icai_examiner_comments": real_comment_count,
            "author_synthesized_notes": synthesized_note_count,
        },
        "chapter_book_policy": {
            "note": "generate_chapter_book.py (as of 2026-07-26) deliberately "
                    "excludes MCQs from the printed chapter books -- they "
                    "live on the separate MCQ platform instead. Figures below "
                    "show what that means against the numbers above.",
            "mcq_records_in_corpus": len(mcq_rows),
            "non_mcq_records_in_corpus": len(non_mcq_rows),
        },
    }


def print_summary(stats: dict) -> None:
    q = stats["questions"]
    m = stats["marks"]
    s = stats["sittings"]
    cbp = stats["chapter_book_policy"]
    mn = stats["mistake_notes"]

    print("=" * 70)
    print("QUESTION BANK BOOK -- COVERAGE STATISTICS")
    print("=" * 70)
    print(f"\nSittings covered: {s['count']}")
    for label in s["list"]:
        print(f"  - {label}")

    print(f"\nTotal question records (including every split part/sub-part): "
          f"{q['total_records_including_parts_and_subparts']}")
    print(f"Distinct question numbers as originally printed: "
          f"{q['distinct_question_numbers_as_printed']}")

    print("\nBy question type:")
    for k, v in q["by_qtype"].items():
        print(f"  {k}: {v}")

    print("\nBy paper part:")
    for k, v in q["by_part"].items():
        print(f"  Part {k}: {v}")

    print("\nBy difficulty (topic-count based):")
    for k, v in q["by_difficulty"].items():
        print(f"  {k}: {v}")
    if set(q["by_difficulty"]) == {"Easy"}:
        print("  NOTE: every row shows 'Easy' because the independent-"
              "sub-part-splitting design (CLAUDE.md section 6) means "
              "almost every row is genuinely single-topic after splitting "
              "(272 of 275 rows touch exactly 1 topic, 3 touch 2) -- not a "
              "bug, just means this difficulty label carries close to no "
              "signal right now with today's splitting policy.")

    print(f"\nTotal marks covered book-wide (OR-alternatives counted once): "
          f"{m['total_marks_covered_book_wide']}")
    print("  NOTE: MTP/PYQ sittings each sum to 114, not the nominal 100 -- "
          "expected, not a bug: Part II offers 'answer any N of the "
          "remaining M', and this book includes every optional question "
          "shown (Q1-Q6, 84 marks) rather than just the subset (Q1-Q5, 70 "
          "marks) one particular sitting required.")
    if m["sittings_without_marks_in_source"]:
        print("  NOTE: these sittings contribute 0 to that total -- ICAI's "
              "own source has no per-question marks for them (RTPs are "
              "published without a marks-weighted answer key), not a "
              "tagging gap:")
        for label in m["sittings_without_marks_in_source"]:
            print(f"    - {label}")

    print(f"\nChapters touched: {stats['chapters_touched_count']}")

    print(f"\nMistake notes: {mn['real_icai_examiner_comments']} real ICAI "
          f"Examiner's Comments, {mn['author_synthesized_notes']} "
          f"Author's Notes")

    print(f"\nChapter-book rendering policy note: {cbp['note']}")
    print(f"  MCQ records (not printed in chapter books): {cbp['mcq_records_in_corpus']}")
    print(f"  Non-MCQ records (printed in chapter books): {cbp['non_mcq_records_in_corpus']}")

    print("\nPer-sitting breakdown:")
    for sf, row in s["per_sitting"].items():
        print(f"  {row['label']:32s} | records: {row['records_in_corpus']:3d} "
              f"| distinct Qs: {row['distinct_questions']:3d} "
              f"| marks: {row['marks_covered_here']:3d} "
              f"| paper total marks: {row['total_marks_of_paper']}")
    print("=" * 70)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                     help="Print the summary without writing book_stats.json.")
    args = ap.parse_args()

    rows = load_index()
    stats = build_stats(rows)
    print_summary(stats)

    if args.check:
        print(f"\n(--check: not writing {STATS_OUT_PATH})")
        return

    STATS_OUT_PATH.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWritten: {STATS_OUT_PATH}")


if __name__ == "__main__":
    main()
