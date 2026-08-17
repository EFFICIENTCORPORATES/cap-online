"""
telegram/database/access_requests.py -- self-service "extra level in the
same course" approval workflow (2026-08-16)
--------------------------------------------------------------------------------
Built for the faculty/manager-testing scenario Pranav described: a normal
student holds at most ONE level per course via self-service
(academic_profiles.py), but someone wanting a SECOND level in a course they
already have (e.g. already "CA Inter", now also wants "CA Foundation" and
"CA Final" to test the bot across all three) requests it instead. Pranav's
exact spec: "this will be sent for approval... in backend this should move
into an auto approval... within 10 seconds the response should be given as
this is approved by admin." Open to ANY student (his confirmed choice,
2026-08-16) -- there's no separate faculty/manager identity on this
platform today to gate it on, so this is a general "extra course access"
request mechanism that happens to be exactly what a tester needs too.

NO REAL HUMAN REVIEW YET -- every request is auto-approved by a delayed
background job (~10s, see bots/profile_flow.py's
_schedule_auto_approval_job()) rather than a person actually looking at it.
The request row + resolved_by='auto' marker are real and permanent, so
switching to genuine manual review later (an admin portal action that calls
approve_request()/reject_request() itself, or leaves resolved_by NULL/an
admin username) needs no data-model change, just wiring a UI to functions
that already exist here.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402
import academic_profiles  # noqa: E402

AUTO_APPROVE_DELAY_SECONDS = 10


def create_request(conn, username: str, telegram_user_id: int, bot_id: str, course: str, level: str) -> int:
    now = db.now()
    db.execute_with_retry(
        conn,
        "INSERT INTO access_requests (username, telegram_user_id, bot_id, course, level, status, requested_at) "
        "VALUES (?,?,?,?,?,'pending',?)",
        (username, telegram_user_id, bot_id, course, level, now),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_request(conn, request_id: int):
    row = conn.execute(
        "SELECT request_id, username, telegram_user_id, bot_id, course, level, status "
        "FROM access_requests WHERE request_id=?",
        (request_id,),
    ).fetchone()
    if not row:
        return None
    return {"request_id": row[0], "username": row[1], "telegram_user_id": row[2], "bot_id": row[3],
            "course": row[4], "level": row[5], "status": row[6]}


def approve_request(conn, request_id: int, resolved_by: str = "auto"):
    """Flips a pending request to approved and creates the real academic
    profile via academic_profiles.add_profile() (deliberately bypassing
    that module's has_course() gate -- this IS the approved exception to
    it). Idempotent -- a request that's already resolved (approved or
    rejected, e.g. a re-armed job firing again after a restart, see
    rearm_pending_requests() below) is left untouched and this returns
    None, so a duplicate approval attempt can never double-create a
    profile or crash. Returns the resolved request dict on a real
    transition, None otherwise."""
    row = conn.execute(
        "SELECT request_id, username, telegram_user_id, bot_id, course, level, status "
        "FROM access_requests WHERE request_id=?",
        (request_id,),
    ).fetchone()
    if not row or row[6] != "pending":
        return None
    request_id, username, telegram_user_id, bot_id, course, level, _ = row
    now = db.now()
    db.execute_with_retry(
        conn, "UPDATE access_requests SET status='approved', resolved_at=?, resolved_by=? WHERE request_id=?",
        (now, resolved_by, request_id),
    )
    academic_profiles.add_profile(conn, username, course, level)
    return {"request_id": request_id, "username": username, "telegram_user_id": telegram_user_id,
            "bot_id": bot_id, "course": course, "level": level}


def pending_requests(conn) -> list:
    """Every still-open request -- used at bot startup to re-arm the
    delayed-approval job for anything that was pending when the process
    last stopped (job_queue jobs don't survive a restart, same reasoning
    as every other delayed job on this platform -- see wallet_flow.py's
    rearm_pending_recharge_jobs() and test_flow.py's twin for the pattern
    this mirrors)."""
    rows = conn.execute(
        "SELECT request_id, username, telegram_user_id, bot_id, course, level, requested_at "
        "FROM access_requests WHERE status='pending'"
    ).fetchall()
    return [
        {"request_id": r[0], "username": r[1], "telegram_user_id": r[2], "bot_id": r[3],
         "course": r[4], "level": r[5], "requested_at": r[6]}
        for r in rows
    ]
