"""
telegram/tools/generate_predesigned_tests.py -- Pre-Designed Test catalog
generator (2026-08-16)
--------------------------------------------------------------------------------
Groups the REAL, already-loaded CA Inter Advanced Accounting question banks
(via exam_hub_bot.py's own QuestionBank/McqBank -- reused directly, never
re-parsed independently, so this can never drift from what the bot itself
actually serves) into one predesigned_tests row per real sitting -- see
telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md for the full design.

SITTING KEY: both sides of the corpus encode (exam_type, year, month, set)
consistently, verified against the real data before writing this script,
not assumed:
  - Descriptive src_text: "MTP May 2024 Set 1", "PYQ September 2025", etc.
  - MCQ mcq_id: "CAI-P1-MTP-2024-05-S1-PI-Q1-a" -- month IS encoded in the
    id (confirmed: MTP 2024 has BOTH -05- and -09- sittings with distinct
    real MCQs, i.e. May and September 2024 are genuinely different papers,
    not a single (exam_type, year, set) group as a first look at the
    year+set fields alone would have suggested).

RTP IS DELIBERATELY EXCLUDED. Confirmed by inspecting every real RTP
record (both MCQ and descriptive) before writing this script: RTP
questions carry no reliable stated marks on either side (marks_text is
unparseable/absent for descriptive; the `marks` field is empty for MCQ) --
consistent with RTP being revision material, not a scored real paper. A
₹1/10-marks charge and a "total marks" summary are both meaningless for a
0-marks test, so RTP sittings never become Predesigned Tests. This is the
concrete case the platform's own "gracefully deny, ask what else" UX rule
is for.

IDEMPOTENT / SAFE TO RE-RUN: always a full rebuild (DELETE + re-INSERT),
never a partial merge -- same discipline as populate_course_catalog.py.
Existing test_sessions/test_questions rows reference predesigned_tests by
catalog_key; a re-run that changes a sitting's marks/duration does NOT
retroactively change any already-started test (test_sessions freezes its
own total_marks/duration_minutes at Start Test time -- see exam_hub_bot.py).

Run: python telegram/tools/generate_predesigned_tests.py [--dry-run]
"""

import os
import re
import sys
import math
import argparse
from pathlib import Path
from collections import defaultdict

os.environ.setdefault("BOT_ID", "1lavya-examhub")

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
sys.path.insert(0, str(REPO_ROOT / "telegram" / "bots"))
import db as platform_db  # noqa: E402
import exam_hub_bot as bot  # noqa: E402 -- real, already-loaded question banks

COURSE, LEVEL, SUBJECT = "CA", "Inter", "Advanced Accounting"
MONTH_NUM_TO_NAME = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}
MONTH_NAME_TO_NUM = {v: k for k, v in MONTH_NUM_TO_NAME.items()}

_DESC_SRC_RE = re.compile(r"(MTP|RTP|PYQ)\s+([A-Za-z]+)\s+(\d{4})(?:\s+Set\s+(\d))?", re.IGNORECASE)
_MCQ_ID_RE = re.compile(r"-(MTP|RTP|PYQ)-(\d{4})-(\d{2})(?:-S(\d))?-")

TIME_PER_MARK_MINUTES = 1.8  # same ceil(marks * 1.8) convention the Question Bank Book pipeline already uses (see CLAUDE.md §6/§7)


def _sitting_key_from_descriptive(q: dict):
    m = _DESC_SRC_RE.search(q.get("src_text") or "")
    if not m:
        return None
    exam_type, month_name, year, set_no = m.groups()
    return (exam_type.upper(), year, month_name.title(), set_no)


def _sitting_key_from_mcq(q: dict):
    m = _MCQ_ID_RE.search(q.get("mcq_id") or "")
    if not m:
        return None
    exam_type, year, month_num, set_no = m.groups()
    month_name = MONTH_NUM_TO_NAME.get(month_num)
    return (exam_type.upper(), year, month_name, set_no)


def _parse_desc_marks(q: dict) -> int:
    m = re.search(r"(\d+)", q.get("marks_text") or "")
    return int(m.group(1)) if m else 0


def build_rows(dry_run: bool = False):
    descs = [q for q in bot.bank.questions if q["_course"] == COURSE and q["_level"] == LEVEL and q["_subject"] == SUBJECT]
    mcqs = [q for q in bot.mcq_bank.questions if q["_course"] == COURSE and q["_level"] == LEVEL and q["_subject"] == SUBJECT]

    desc_groups = defaultdict(list)
    unmatched_desc = 0
    for q in descs:
        key = _sitting_key_from_descriptive(q)
        if key:
            desc_groups[key].append(q)
        else:
            unmatched_desc += 1

    mcq_groups = defaultdict(list)
    unmatched_mcq = 0
    for q in mcqs:
        key = _sitting_key_from_mcq(q)
        if key:
            mcq_groups[key].append(q)
        else:
            unmatched_mcq += 1

    if unmatched_desc or unmatched_mcq:
        print(f"WARNING: {unmatched_desc} descriptive / {unmatched_mcq} MCQ records didn't match the sitting-key "
              f"pattern and are excluded from every Predesigned Test -- check src_text/mcq_id formatting if this "
              f"number is ever nonzero and unexpected.")

    all_keys = set(desc_groups) | set(mcq_groups)
    rows = []
    skipped_rtp = 0
    skipped_zero_marks = 0

    for key in sorted(all_keys):
        exam_type, year, month, set_no = key
        if exam_type == "RTP":
            skipped_rtp += 1
            continue

        desc_qs = desc_groups.get(key, [])
        mcq_qs = mcq_groups.get(key, [])
        descriptive_marks = sum(_parse_desc_marks(q) for q in desc_qs)
        mcq_marks = sum(q.get("marks") or 0 for q in mcq_qs)
        total_marks = descriptive_marks + mcq_marks

        if total_marks <= 0:
            skipped_zero_marks += 1
            continue

        set_label = f"-S{set_no}" if set_no else ""
        catalog_key = f"CA-Inter-AdvAcc-{exam_type}-{year}-{MONTH_NAME_TO_NUM.get(month, '00')}{set_label}"
        title_parts = [exam_type, month or "", year] + ([f"Set {set_no}"] if set_no else [])
        title = " ".join(p for p in title_parts if p)

        rows.append({
            "catalog_key": catalog_key,
            "course": COURSE, "level": LEVEL, "subject": SUBJECT,
            "exam_type": exam_type, "year": year, "month": month, "set_no": set_no,
            "title": title,
            "total_marks": total_marks,
            "duration_minutes": max(10, math.ceil(total_marks * TIME_PER_MARK_MINUTES)),
            "mcq_count": len(mcq_qs), "mcq_marks": mcq_marks,
            "descriptive_count": len(desc_qs), "descriptive_marks": descriptive_marks,
        })

    print(f"Built {len(rows)} Predesigned Test row(s) -- skipped {skipped_rtp} RTP sitting(s) "
          f"(no reliable marks, by design) and {skipped_zero_marks} zero-marks sitting(s).")
    for r in rows:
        print(f"  {r['catalog_key']:40s} {r['title']:28s} {r['total_marks']:3d} marks "
              f"({r['mcq_count']} MCQ / {r['descriptive_count']} descriptive), {r['duration_minutes']} min")

    if dry_run:
        print("\n--dry-run: not writing to the database.")
        return rows

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    now = platform_db.now()
    conn.execute("DELETE FROM predesigned_tests")
    for r in rows:
        conn.execute(
            "INSERT INTO predesigned_tests (catalog_key, course, level, subject, exam_type, year, month, set_no, "
            "title, total_marks, duration_minutes, mcq_count, mcq_marks, descriptive_count, descriptive_marks, "
            "active, generated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?)",
            (r["catalog_key"], r["course"], r["level"], r["subject"], r["exam_type"], r["year"], r["month"], r["set_no"],
             r["title"], r["total_marks"], r["duration_minutes"], r["mcq_count"], r["mcq_marks"],
             r["descriptive_count"], r["descriptive_marks"], now),
        )
    conn.commit()
    conn.close()
    print(f"\nWrote {len(rows)} rows to predesigned_tests.")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    build_rows(dry_run=args.dry_run)
