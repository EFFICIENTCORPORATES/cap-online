"""
telegram/database/academic_profiles.py -- multi-course academic profiles
(2026-08-16)
--------------------------------------------------------------------------------
Built for multi-course support (Pranav's ask: a student may genuinely be
preparing for more than one course/level simultaneously -- CS Final + CA
Inter + CMA Foundation is a normal real-world case, each with its OWN
target exam attempt). See schema.sql's own comment on
student_academic_profiles for the full design/reasoning.

LOCKED RULE (Pranav, 2026-08-16): a student can self-service add profiles
for as many DIFFERENT courses as they like, but at most ONE level per
course via self-service. A SECOND level within a course they already have
is the faculty/manager-testing scenario and must go through
access_requests.py instead -- has_course() below is the check every caller
uses to decide which path applies; this module's own add_profile() does
NOT enforce that gate itself (it's a plain upsert), by design, so
access_requests.approve_request() can call it directly once a request is
approved without re-triggering the same gate it already passed.

IDENTITY: everything here is keyed by `username` (student_profiles), same
as wallet.py -- a student's academic profiles follow them across every
linked chat_id/phone, never per-device.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402


def list_profiles(conn, username: str) -> list:
    """Every academic profile this username holds, oldest first (so "the
    first one they ever added" reads first in any list/picker)."""
    rows = conn.execute(
        "SELECT profile_id, course, level, exam_attempt, created_at, updated_at "
        "FROM student_academic_profiles WHERE username=? ORDER BY created_at",
        (username,),
    ).fetchall()
    return [
        {"profile_id": r[0], "course": r[1], "level": r[2], "exam_attempt": r[3],
         "created_at": r[4], "updated_at": r[5]}
        for r in rows
    ]


def get_profile(conn, profile_id: int):
    row = conn.execute(
        "SELECT profile_id, username, course, level, exam_attempt FROM student_academic_profiles WHERE profile_id=?",
        (profile_id,),
    ).fetchone()
    if not row:
        return None
    return {"profile_id": row[0], "username": row[1], "course": row[2], "level": row[3], "exam_attempt": row[4]}


def has_course(conn, username: str, course: str) -> bool:
    """True if this username already has ANY level saved for this course.
    The gate every add-flow call site checks BEFORE calling add_profile()
    directly -- if this is True and the level being added is a DIFFERENT
    one than what's already on file, route through access_requests.py
    instead of calling add_profile() here."""
    row = conn.execute(
        "SELECT 1 FROM student_academic_profiles WHERE username=? AND course=? LIMIT 1",
        (username, course),
    ).fetchone()
    return row is not None


def add_profile(conn, username: str, course: str, level: str, exam_attempt: str = None) -> int:
    """Plain upsert -- inserts a new (username, course, level) profile, or
    (if that exact course+level already exists) updates its exam_attempt
    and returns the existing profile_id unchanged otherwise. Does NOT
    enforce the has_course() gate -- callers (profile_flow.py's self-
    service add, access_requests.approve_request() once a request clears)
    are responsible for deciding whether this call is even allowed."""
    now = db.now()
    existing = conn.execute(
        "SELECT profile_id FROM student_academic_profiles WHERE username=? AND course=? AND level=?",
        (username, course, level),
    ).fetchone()
    if existing:
        if exam_attempt is not None:
            db.execute_with_retry(
                conn, "UPDATE student_academic_profiles SET exam_attempt=?, updated_at=? WHERE profile_id=?",
                (exam_attempt, now, existing[0]),
            )
        return existing[0]
    db.execute_with_retry(
        conn,
        "INSERT INTO student_academic_profiles (username, course, level, exam_attempt, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?)",
        (username, course, level, exam_attempt, now, now),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_exam_attempt(conn, profile_id: int, exam_attempt: str):
    db.execute_with_retry(
        conn, "UPDATE student_academic_profiles SET exam_attempt=?, updated_at=? WHERE profile_id=?",
        (exam_attempt, db.now(), profile_id),
    )


def remove_profile(conn, profile_id: int):
    db.execute_with_retry(conn, "DELETE FROM student_academic_profiles WHERE profile_id=?", (profile_id,))
