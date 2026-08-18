#!/usr/bin/env python3
"""
telegram/tools/smoke_test_course_catalog.py -- smoke test for the course
catalog + human-readable MCQ ID pipeline (2026-08-11)
--------------------------------------------------------------------------------
Covers populate_course_catalog.py (real DB writes, re-run against the
real platform.db -- rebuild is idempotent/full-replace by design, so
re-running this test is always safe) and generate_mcq_human_ids.py
(re-run against the real content JSON files -- MUST be a true no-op on a
second run, since every question already has a human_id after the first
real run; this test verifies that idempotency directly, not just asserts
it).

USAGE:
    python telegram/tools/smoke_test_course_catalog.py
"""

import re
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))

import db as platform_db  # noqa: E402
import populate_course_catalog as pop  # noqa: E402
import generate_mcq_human_ids as gen  # noqa: E402

failures = []


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(label)


def main():
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    print("\n--- Step 1: course_catalog population ---")
    row_count = conn.execute("SELECT COUNT(*) FROM course_catalog").fetchone()[0]
    check("course_catalog has real rows", row_count > 0, f"got {row_count}")
    check("course_catalog has all 3 sources", row_count >= 700, f"got {row_count}")

    # No duplicate keys (the population script itself refuses to write
    # duplicates -- this re-confirms the DB actually reflects that).
    # Includes session (2026-08-18) to match idx_course_catalog_key's real
    # widened definition -- a subject with >1 live ICAI edition (GST is
    # the first) legitimately has the SAME (chapter,unit) twice, once per
    # session, and that is correct, not a duplicate. See
    # populate_course_catalog.py's module docstring.
    dupes = conn.execute(
        "SELECT course, level, paper_no, chapter_no, unit_no, session, COUNT(*) c "
        "FROM course_catalog GROUP BY course, level, paper_no, chapter_no, unit_no, session HAVING c > 1"
    ).fetchall()
    check("no duplicate (course,level,paper,chapter,unit,session) keys", len(dupes) == 0, str(dupes[:3]))

    # A subject with >1 live edition must have exactly one row per
    # (chapter,unit) PER session (real ICAI content, not a partial/missing
    # edition) -- GST-specific regression guard for the 2026-08-18 fix.
    gst_sessions = conn.execute(
        "SELECT session, COUNT(*) FROM course_catalog "
        "WHERE course='CA' AND level='Inter' AND subject='Taxation - Goods and Services Tax' "
        "GROUP BY session ORDER BY session"
    ).fetchall()
    check("GST has exactly 2 editions (May26, May27), 15 chapters each",
          gst_sessions == [("May26", 15), ("May27", 15)], str(gst_sessions))
    gst_subject_count = conn.execute(
        "SELECT COUNT(DISTINCT subject) FROM course_catalog WHERE course='CA' AND level='Inter' "
        "AND subject LIKE 'Taxation - Goods%'"
    ).fetchone()[0]
    check("GST is ONE subject, not split by edition (Pranav's 2026-08-18 call)",
          gst_subject_count == 1, f"got {gst_subject_count} distinct subject(s)")

    # Cross-check specific real, independently-confirmed facts.
    row = conn.execute(
        "SELECT chapter_name_short FROM course_catalog WHERE course='CA' AND level='Inter' AND chapter_no=7 AND unit_no=3"
    ).fetchone()
    check("CA Inter Adv Acc chapter 7 unit 3 is AS-11 (matches real MCQ content)",
          row is not None and row[0] == "AS-11", str(row))

    row = conn.execute(
        "SELECT chapter_name FROM course_catalog WHERE course='CMA' AND level='Intermediate' AND paper_no='5' AND chapter_no=12"
    ).fetchone()
    check("CMA Intermediate Paper 5 chapter 12 is Companies Act, 2013",
          row is not None and row[0] == "Companies Act, 2013", str(row))

    row = conn.execute(
        "SELECT chapter_name FROM course_catalog WHERE course='CA' AND level='Foundation' AND subject='Quantitative Aptitude' AND chapter_no=1"
    ).fetchone()
    check("CA Foundation Quant Aptitude chapter 1 is Ratio and Proportion...",
          row is not None and "Ratio and Proportion" in row[0], str(row))

    print("\n--- Step 1b: full CA coverage (regression for the 2026-08-12 gap) ---")
    # Pranav caught this: the first version only covered 2 of CA's 17 real
    # subjects. Assert all 17 are present now, matching CS/CMA's completeness.
    ca_subjects = conn.execute(
        "SELECT DISTINCT level, subject FROM course_catalog WHERE course='CA'"
    ).fetchall()
    check("all 17 real CA subjects are present", len(ca_subjects) == 17, f"got {len(ca_subjects)}: {ca_subjects}")
    check("CA Final has real subjects (was completely empty before the fix)",
          any(lvl == "Final" for lvl, _ in ca_subjects))

    # The 3 specific real edge cases found while fixing this -- each its
    # own permanent regression guard, not just "no crash."
    rows = conn.execute(
        "SELECT unit_no, unit_name FROM course_catalog WHERE course='CA' AND level='Inter' "
        "AND subject='Financial Management' AND chapter_no=9 ORDER BY unit_no"
    ).fetchall()
    check("CA Inter Financial Management ch.9: 6 real units parsed from Label text (Unit I..VI), not filename U0",
          [r[0] for r in rows] == [1, 2, 3, 4, 5, 6], str(rows))

    rows = conn.execute(
        "SELECT unit_no FROM course_catalog WHERE course='CA' AND level='Final' "
        "AND subject='Advanced Auditing, Assurance & Professional Ethics' AND chapter_no=14 ORDER BY unit_no"
    ).fetchall()
    check("CA Final Advanced Auditing ch.14: real U1/U2 preserved (Banks / NBFCs), not collapsed to one U0",
          [r[0] for r in rows] == [1, 2], str(rows))

    row = conn.execute(
        "SELECT COUNT(*) FROM course_catalog WHERE course='CA' AND level='Final' "
        "AND subject='Financial Reporting' AND chapter_no=11"
    ).fetchone()
    check("CA Final Financial Reporting ch.11: auxiliary files excluded (6 real units, not 8)", row[0] == 6, str(row))

    # Real, found 2026-08-12 -- a 4th edge case, same collision check, this
    # time triggered by adding 3 new "Other Laws" PDFs: CA Inter Corporate
    # and Other Laws' printed chapter numbering restarts at Module 4
    # (Chapter 1/2/3 for General Clauses Act/Interpretation of Statutes/
    # FEMA 1999) -- same numbers Module 1 already uses. Offset to continue
    # the subject's existing sequence (13/14/15) instead of colliding.
    # Scoped to session='May27' (2026-08-18: this subject gained a second
    # live edition, May26 -- see the module-wide session checks below for
    # that) so this specific offset check stays a stable, single-edition
    # assertion rather than silently doubling.
    rows = conn.execute(
        "SELECT chapter_no, chapter_name FROM course_catalog WHERE course='CA' AND level='Inter' "
        "AND subject='Corporate and Other Laws' AND session='May27' AND chapter_no IN (13, 14, 15) "
        "ORDER BY chapter_no"
    ).fetchall()
    check("CA Inter Corporate and Other Laws: Module 4's 3 chapters offset to 13/14/15, not colliding with Module 1's 1/2/3",
          [r[1] for r in rows] == ["The General Clauses Act, 1897", "Interpretation of Statutes",
                                    "The Foreign Exchange Management Act, 1999"], str(rows))
    # 2026-08-18: this subject now has 2 live ICAI editions (May26, May27,
    # same GST-style dual-edition situation) -- 15 chapters each, one
    # Subject entry (not duplicated), matching study_hub_bot.py's
    # editions_for()/"ed:" drill-down design.
    law_sessions = conn.execute(
        "SELECT session, COUNT(*) FROM course_catalog WHERE course='CA' AND level='Inter' "
        "AND subject='Corporate and Other Laws' GROUP BY session ORDER BY session"
    ).fetchall()
    check("CA Inter Corporate and Other Laws: 15 real chapters total (12 Company Law + 3 Other Laws), "
          "2 editions (May26, May27)",
          law_sessions == [("May26", 15), ("May27", 15)], str(law_sessions))

    # Real, found 2026-08-12 (later same day): Pranav asked whether the new
    # CA Foundation Accounting MCQ set's chapters 8-11 (NPO Financial
    # Statements / Incomplete Records / Partnership & LLP Accounts / Company
    # Accounts) matched the real ICAI syllabus. They did -- confirmed against
    # https://www.icai.org/post/19138, ICAI's own real Study Material PDFs
    # downloaded and added -- but course_catalog itself had never had those
    # 4 chapters at all (it stopped at chapter 7, Module 1). Not a collision
    # this time (Module 2 continues 8-11 sequentially, no restart) -- a
    # genuine coverage gap, same class of bug as the earlier CA-coverage fix.
    rows = conn.execute(
        "SELECT DISTINCT chapter_no FROM course_catalog WHERE course='CA' AND level='Foundation' "
        "AND subject='Accounting' ORDER BY chapter_no"
    ).fetchall()
    check("CA Foundation Accounting: all 11 real chapters present (was capped at 7)",
          [r[0] for r in rows] == list(range(1, 12)), str(rows))
    rows = conn.execute(
        "SELECT unit_no FROM course_catalog WHERE course='CA' AND level='Foundation' "
        "AND subject='Accounting' AND chapter_no=10 ORDER BY unit_no"
    ).fetchall()
    check("CA Foundation Accounting ch.10 (Partnership and LLP Accounts): 7 real units (6 + Annexure II)",
          [r[0] for r in rows] == [1, 2, 3, 4, 5, 6, 7], str(rows))
    rows = conn.execute(
        "SELECT unit_no FROM course_catalog WHERE course='CA' AND level='Foundation' "
        "AND subject='Accounting' AND chapter_no=11 ORDER BY unit_no"
    ).fetchall()
    check("CA Foundation Accounting ch.11 (Company Accounts): 6 real units",
          [r[0] for r in rows] == [1, 2, 3, 4, 5, 6], str(rows))

    print("\n--- Step 2: dry-run population never writes ---")
    before = conn.execute("SELECT MAX(updated_at) FROM course_catalog").fetchone()[0]
    import subprocess
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "populate_course_catalog.py"), "--dry-run"],
        capture_output=True, text=True,
    )
    check("dry-run exits cleanly", result.returncode == 0, result.stderr[-500:] if result.returncode else "")
    after = conn.execute("SELECT MAX(updated_at) FROM course_catalog").fetchone()[0]
    check("dry-run does not change updated_at (writes nothing)", before == after)

    print("\n--- Step 3: human_id format + coverage on real content files ---")
    HUMAN_ID_RE = re.compile(r"^(CA|CS|CMA)_L[123]_P\w{1,3}_C\d+_U\d+_\d{5}$")
    for src in gen.CONTENT_SOURCES:
        if not src["path"].exists():
            continue
        _, records = gen._load(src["path"])
        missing = [r.get(src["id_field"]) for r in records if not r.get("human_id")]
        check(f"{src['path'].name} ({src['course']}/{src['level']}): every record has a human_id",
              len(missing) == 0, f"{len(missing)} missing, e.g. {missing[:3]}")
        bad_format = [r["human_id"] for r in records if r.get("human_id") and not HUMAN_ID_RE.match(r["human_id"])]
        check(f"{src['path'].name}: every human_id matches the expected format",
              len(bad_format) == 0, f"{bad_format[:3]}")
        ids = [r["human_id"] for r in records if r.get("human_id")]
        check(f"{src['path'].name}: every human_id is unique within the file",
              len(ids) == len(set(ids)), f"{len(ids)} ids, {len(set(ids))} unique")
        # Every id's course/level_num must match its own source's expected values.
        expected_course = src["course"]
        mismatched = [i for i in ids if not i.startswith(f"{expected_course}_L")]
        check(f"{src['path'].name}: every human_id starts with the correct course code",
              len(mismatched) == 0, f"{mismatched[:3]}")

    print("\n--- Step 4: generator is idempotent (a second real run changes nothing) ---")
    # Snapshot every file's human_ids, run for real again, confirm byte-identical human_id assignment.
    snapshots = {}
    for src in gen.CONTENT_SOURCES:
        if not src["path"].exists():
            continue
        _, records = gen._load(src["path"])
        snapshots[str(src["path"])] = [r.get("human_id") for r in records]

    result = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "generate_mcq_human_ids.py")],
                             capture_output=True, text=True)
    check("second real run exits cleanly", result.returncode == 0, result.stderr[-500:] if result.returncode else "")
    check("second real run assigns exactly 0 new ids (fully idempotent)",
          "Total newly assigned: 0" in result.stdout, result.stdout[-300:])

    for src in gen.CONTENT_SOURCES:
        if not src["path"].exists():
            continue
        _, records = gen._load(src["path"])
        after_ids = [r.get("human_id") for r in records]
        check(f"{src['path'].name}: human_ids unchanged after a second run",
              after_ids == snapshots[str(src["path"])])

    print("\n--- Step 5: merged faculty file (regenerated) carries human_id through ---")
    merged_path = Path("telegram/assets/exam_bot/faculty/csarunchouhan/mcq_questions_extracted.json")
    if merged_path.exists():
        data = json.loads(merged_path.read_text(encoding="utf-8"))
        records = data["questions"] if isinstance(data, dict) and "questions" in data else data
        missing = sum(1 for r in records if not r.get("human_id"))
        check("merged csarunchouhan MCQ file: every record has a human_id", missing == 0, f"{missing} missing")

    print("\n--- Step 6: content validator still clean (no regression from these changes) ---")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import validate_content_json as v
    reports = v.validate_all()
    total_errors = sum(len([i for i in r["issues"] if i["severity"] == "ERROR"]) for r in reports)
    total_warnings = sum(len([i for i in r["issues"] if i["severity"] == "WARNING"]) for r in reports)
    check("0 content validation errors platform-wide", total_errors == 0, f"got {total_errors}")
    check("0 content validation warnings platform-wide", total_warnings == 0, f"got {total_warnings}")

    print(f"\n{'='*70}")
    if failures:
        print(f"{len(failures)} check(s) FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
