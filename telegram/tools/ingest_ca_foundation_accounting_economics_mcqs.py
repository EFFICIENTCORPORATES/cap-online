#!/usr/bin/env python3
"""
telegram/tools/ingest_ca_foundation_accounting_economics_mcqs.py -- one-time
ingestion of the 2 new CA Foundation MCQ content sets (2026-08-12)
--------------------------------------------------------------------------------
Pranav added 2 raw staging folders:
  telegram/assets/exam_bot/CA Found Account Json/      (Accounting, 1,595 MCQs)
  telegram/assets/exam_bot/JSON CA Foundation Eco/      (Business Economics, 918 MCQs)

Both had real defects fixed BEFORE this script ran (not by this script --
see COURSE-CATALOG.md's "CA Foundation Accounting" entries for the full
story): 3 files had invalid JSON (unescaped LaTeX \\%, one stray ":="
typo) -- repaired in place, source folders now parse 100% clean.

This script does the actual INGESTION: merges each subject's many
scattered per-chapter/per-unit files into ONE clean, normalized,
subject-level file, per Pranav's confirmed convention (2026-08-12,
AskUserQuestion) -- one MCQ JSON + one Descriptive JSON per (course,
level, subject), never bundled across subjects or split across chapters.
Only the MCQ file is produced here (neither subject has descriptive
content yet).

WHY NO FUZZY TOPIC MATCHING WAS NEEDED: every source record already
carries a real, machine-parseable unit indicator once you look past the
schema drift -- `unit_code`/`unit`/`unitcode` values in 5+ different
literal formats ("M1-C1-U1", "Unit-1", "Unit 1", "unit-1-slug-suffix").
ONE regex (`_UNIT_NO_RE`) extracts the integer from all of them. No
per-question topic-keyword classification was built or needed -- the
data was always there, just inconsistently formatted.

CHAPTER/UNIT VALIDITY: every resolved (chapter_no, unit_no) is checked
against course_catalog -- a record whose source unit_code resolves to a
combination that ISN'T a real catalog row is not silently kept; it's
either remapped (single-unit chapters where the source subdivides
informally, e.g. Economics Ch.5/Ch.10 use internal "Unit 1-4" labels for
what course_catalog correctly treats as ONE real unit -- Business
Economics has no ICAI sub-unit split there) or flagged.

SOURCING/GENERATION TAGS: Pranav confirmed (2026-08-12) these specific 2
batches are self-authored practice MCQs based on ICAI Study Material
(his stated 70-80% self-sourcing plan) -- `generation_source` is set to
that exact description for every record in both files. `faculty_name`/
`faculty_id` are left null -- WHO specifically wrote them isn't something
this script can know or should guess; flagged as open in the run report.

USAGE:
    python telegram/tools/ingest_ca_foundation_accounting_economics_mcqs.py [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
ACC_SRC = REPO_ROOT / "telegram" / "assets" / "exam_bot" / "CA Found Account Json"
ECO_SRC = REPO_ROOT / "telegram" / "assets" / "exam_bot" / "JSON CA Foundation Eco"
ACC_OUT = REPO_ROOT / "telegram" / "assets" / "exam_bot" / "ca-foundation-accounting" / "mcq_questions_extracted.json"
ECO_OUT = REPO_ROOT / "telegram" / "assets" / "exam_bot" / "ca-foundation-business-economics" / "mcq_questions_extracted.json"

sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402

GENERATION_SOURCE = "Self-authored practice MCQ, based on ICAI Study Material (Pranav, 2026-08-12)"

_UNIT_NO_RE = re.compile(r"[Uu](?:nit)?[-\s]?(\d+)")


def _parse_unit_no(unit_code) -> int:
    if not unit_code:
        return None
    m = _UNIT_NO_RE.search(str(unit_code))
    return int(m.group(1)) if m else None


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _load_catalog(conn, course, level, subject):
    """{chapter_no: {"paper_no":..., "name":..., "units": {unit_no: unit_name or None}}}"""
    rows = conn.execute(
        "SELECT paper_no, chapter_no, chapter_name, unit_no, unit_name FROM course_catalog "
        "WHERE course=? AND level=? AND subject=? ORDER BY chapter_no, unit_no",
        (course, level, subject),
    ).fetchall()
    out = {}
    for paper_no, chapter_no, chapter_name, unit_no, unit_name in rows:
        entry = out.setdefault(chapter_no, {"paper_no": paper_no, "units": {}})
        entry["units"][unit_no] = unit_name or chapter_name
    return out


def _option_letter(options: dict, answer_text: str, options_is_list: bool, raw_options):
    """Resolve which lettered option matches the source's own 'correct'
    field -- found to vary by chapter, not one format: a full option-text
    value (most chapters), an already-correct letter (Ch.8), or a 0-indexed
    integer position into the original options list (Ch.9). Tries all
    three, in that order, before giving up."""
    if answer_text is None:
        return None
    # (a) already a valid letter key
    if isinstance(answer_text, str) and answer_text.strip().upper() in options:
        return answer_text.strip().upper()
    # (b) 0-indexed integer position into the ORIGINAL (pre-lettering) list
    if isinstance(answer_text, int) and options_is_list:
        letters = list(options.keys())
        if 0 <= answer_text < len(letters):
            return letters[answer_text]
        return None
    # (c) full option-text match
    norm_answer = str(answer_text).strip().casefold()
    for letter, text in options.items():
        if str(text).strip().casefold() == norm_answer:
            return letter
    return None


def _normalize_options(raw_options) -> dict:
    if isinstance(raw_options, dict):
        return {k: v for k, v in raw_options.items()}
    letters = "ABCDEFGH"
    return {letters[i]: v for i, v in enumerate(raw_options)}


def build_accounting(conn, report: list) -> list:
    catalog = _load_catalog(conn, "CA", "Foundation", "Accounting")
    out = []
    seq_by_chapter_unit = defaultdict(int)
    files = sorted(ACC_SRC.glob("Chapter */*.json"))
    for f in files:
        chapter_no = int(re.search(r"Chapter (\d+)", f.parent.name).group(1))
        data = json.loads(f.read_text(encoding="utf-8"))
        for r in data:
            # Real, found via the mcq_id-must-exist check below (not
            # inspection): one record (Chapter 2/Unit 6) has the key typo'd
            # as "mc_id" instead of "mcq_id" -- otherwise a normal, valid
            # record. Recovered, not discarded.
            if "mcq_id" not in r and "mc_id" in r:
                r["mcq_id"] = r.pop("mc_id")
                report.append(f"RECOVERED: {f.name} had 'mc_id' instead of 'mcq_id' (fixed) -- {r['mcq_id']}")
            if not r.get("mcq_id"):
                report.append(f"SKIPPED (no mcq_id, even after mc_id recovery): {f.name} question={r.get('question_html','')[:80]!r}")
                continue

            cat_entry = catalog.get(chapter_no)
            if cat_entry is None:
                report.append(f"SKIPPED (no catalog chapter {chapter_no}): {f.name} mcq_id={r.get('mcq_id')}")
                continue
            unit_no = _parse_unit_no(r.get("unitcode")) if r.get("unitcode") not in (None, "") else 0
            if unit_no is None or unit_no not in cat_entry["units"]:
                # Single-unit chapters store the chapter number itself as
                # unitcode (e.g. "Chapter 3") -- real unit is 0 in that case.
                unit_no = 0 if 0 in cat_entry["units"] else next(iter(cat_entry["units"]))
            seq_by_chapter_unit[(chapter_no, unit_no)] += 1
            r["chapter_slug"] = _slugify(cat_entry["units"][unit_no] or f"chapter-{chapter_no}")
            r["generation_source"] = GENERATION_SOURCE
            # Real, found by inspection: the SOURCE data claims
            # exam_type="MTP" on all 1,595 records, but source_kind already
            # (correctly) says "Study Material" and Pranav confirmed these
            # are self-authored practice MCQs, not from an actual ICAI MTP
            # paper -- "MTP" here would misrepresent provenance to a
            # student. Corrected to "PRACTICE", matching the exact
            # convention already established for CA Foundation Quantitative
            # Aptitude (the other self-authored batch already live).
            if r.get("exam_type") == "MTP":
                r["exam_type"] = "PRACTICE"
            out.append(r)
    return out


def build_economics(conn, report: list) -> list:
    catalog = _load_catalog(conn, "CA", "Foundation", "Business Economics")
    out = []
    seq_by_chapter_unit = defaultdict(int)
    files = sorted(ECO_SRC.glob("Chapter *.json"))
    for f in files:
        chapter_no = int(re.search(r"Chapter (\d+)", f.stem).group(1))
        data = json.loads(f.read_text(encoding="utf-8"))
        cat_entry = catalog.get(chapter_no)
        if cat_entry is None:
            report.append(f"SKIPPED (no catalog chapter {chapter_no}): entire {f.name} ({len(data)} records)")
            continue
        real_units = sorted(cat_entry["units"].keys())
        single_unit_chapter = real_units == [0]

        for r in data:
            raw_unit_field = r.get("unit_code") or r.get("unit")
            parsed_unit = _parse_unit_no(raw_unit_field)
            if single_unit_chapter:
                # Ch.5/Ch.10: source subdivides informally into its own
                # "Unit 1-4" labels, but course_catalog has no real ICAI
                # sub-unit split here -- everything maps to the one real unit.
                unit_no = 0
            elif parsed_unit is not None and parsed_unit in cat_entry["units"]:
                unit_no = parsed_unit
            else:
                report.append(f"UNRESOLVED unit for chapter {chapter_no}, raw unit field={raw_unit_field!r} "
                               f"(real units: {real_units}) -- question defaulted to unit {real_units[0]}, flag for review")
                unit_no = real_units[0]

            seq_by_chapter_unit[(chapter_no, unit_no)] += 1
            seq = seq_by_chapter_unit[(chapter_no, unit_no)]

            question_text = r.get("question") or r.get("question_text") or ""
            explanation = r.get("explanation") or ""
            chapter_name = cat_entry["units"][unit_no]

            raw_options = r.get("options") or r.get("Options")  # 1 record in Ch.5 has "Options" (capitalized) -- real typo, not a schema variant
            if raw_options is None:
                report.append(f"SKIPPED (no options field at all): chapter {chapter_no} unit_code={raw_unit_field!r} "
                               f"question={question_text[:80]!r}")
                continue
            options = _normalize_options(raw_options)
            # Explicit key-presence checks, NOT `a or b or c` -- Ch.9 uses a
            # 0-indexed integer answer, and 0 is falsy in Python, which
            # silently fell through to the next field entirely on the very
            # first real bug this script hit (found via the report output,
            # not by inspection).
            for field in ("answer", "correct_answer", "correct_option"):
                if field in r and r[field] is not None:
                    raw_answer = r[field]
                    break
            else:
                raw_answer = None
            letter = _option_letter(options, raw_answer, isinstance(raw_options, list), raw_options)
            if letter is None:
                report.append(f"UNRESOLVED answer letter: chapter {chapter_no} unit {unit_no} seq {seq} "
                               f"-- raw answer {raw_answer!r} didn't match any option text, flag for review")

            normalized = {
                "mcq_id": f"CA-FND-ECO-CH{chapter_no}-U{unit_no}-Q{seq:03d}",
                "course": "CA",
                "level": "Foundation",
                # "PRACTICE"/"2026" -- same convention as the Accounting
                # correction above and the existing CA Foundation
                # Quantitative Aptitude batch: self-authored, not from a
                # real ICAI exam sitting.
                "exam_type": "PRACTICE",
                "year": "2026",
                "set": None,
                "qno_text": None,
                "marks": 1,
                "difficulty": r.get("difficulty") or "Medium",
                "qtype": "direct-mcq",
                "case_ref": None,
                "case_facts_html": None,
                "question_html": f"<p>{question_text}</p>",
                "options": options,
                "correct_option": letter,
                "answer_html": (
                    f"<p><strong>Answer:</strong> "
                    f"{f'({letter}) ' if letter else ''}{options.get(letter, raw_answer)}.</p>"
                    + (f"<p>{explanation}</p>" if explanation else "")
                ),
                "chapter_slug": _slugify(chapter_name or f"chapter-{chapter_no}"),
                "chapter_label": f"Chapt {chapter_no}",
                "unitcode": f"Unit {unit_no}" if unit_no else None,
                "topic_text": r.get("topic") or None,
                "source_kind": "Study Material",
                "faculty_id": None,
                "faculty_name": None,
                "source_file": f.name,
                "source_document_hash": None,
                "publication_status": "Published",
                "validation_status": "Verified" if letter else "Needs Review",
                "generation_source": GENERATION_SOURCE,
            }
            out.append(normalized)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = platform_db.get_connection()
    report = []

    acc = build_accounting(conn, report)
    eco = build_economics(conn, report)

    print(f"Accounting: {len(acc)} MCQs normalized")
    print(f"Business Economics: {len(eco)} MCQs normalized")
    if report:
        print(f"\n{len(report)} item(s) flagged for review:")
        for line in report:
            print(f"  - {line}")

    needs_review = sum(1 for r in eco if r.get("validation_status") == "Needs Review")
    if needs_review:
        print(f"\n{needs_review} Economics record(s) marked 'Needs Review' (answer letter unresolved).")

    # Final preflight -- both files, same checks: no duplicate mcq_id
    # (would silently shadow via first-match-wins lookup, same class of
    # bug flagged in validate_content_json.py's own CORE_FIELDS contract),
    # and correct_option must be a real key in that record's own options.
    fatal = []
    for name, records in (("Accounting", acc), ("Business Economics", eco)):
        ids = [r["mcq_id"] for r in records]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            fatal.append(f"{name}: {len(dupes)} duplicate mcq_id(s): {sorted(dupes)[:5]}")
        bad_option = [r["mcq_id"] for r in records if r.get("correct_option") not in r.get("options", {})]
        if bad_option:
            fatal.append(f"{name}: {len(bad_option)} record(s) with correct_option not in options: {bad_option[:5]}")

    if fatal:
        print("\nFATAL preflight failures -- nothing written:")
        for f in fatal:
            print(f"  - {f}")
        sys.exit(1)
    print("\nPreflight OK: no duplicate mcq_ids, every correct_option is a real option key.")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return

    ACC_OUT.parent.mkdir(parents=True, exist_ok=True)
    ECO_OUT.parent.mkdir(parents=True, exist_ok=True)
    ACC_OUT.write_text(json.dumps(acc, indent=2, ensure_ascii=False), encoding="utf-8")
    ECO_OUT.write_text(json.dumps(eco, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {ACC_OUT}")
    print(f"Wrote {ECO_OUT}")


if __name__ == "__main__":
    main()
