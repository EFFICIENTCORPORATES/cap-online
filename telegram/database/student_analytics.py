"""
telegram/database/student_analytics.py -- per-student report analytics
(2026-08-11, Phase 2 of the branding-kit -> report-pipeline -> leaderboard
-> admin-portal roadmap)
--------------------------------------------------------------------------------
Everything telegram/tools/generate_student_report.py needs to build one
student's performance report: total questions practiced, accuracy, time per
question, chapter-wise breakdown, and time spent on the bot. All queries
are PLATFORM-WIDE for the given telegram_user_id (Pranav's explicit
2026-08-10 call: milestones and stats are per-student across every bot they
use, not per-bot) -- never filtered by bot_id.

`criteria` (an optional `since` date OR an optional `last_n` count, never
both) scopes the QUESTION-level stats (counts, accuracy, chapter-wise) --
"time on bot"/session stats are always all-time regardless of `criteria`,
since a session is a holistic engagement unit that doesn't cleanly slice by
"the last N questions." Documented, not hidden -- the report itself states
this plainly rather than silently mixing scopes.

"Time spent on bot" deliberately does NOT come from an explicit session-end
timestamp (see schema.sql's own note on why that design was rejected before
shipping -- it would count idle gaps between sessions as active time).
Instead, each session's real span is MAX(activity timestamp) - started_at,
computed from the actual mcq_attempts/descriptive_events rows tied to that
session_id -- never wider than what real recorded activity actually spans.
A session with zero recorded activity (e.g. the student only saw a menu and
left) contributes 0 seconds, which is honest, not a gap to paper over.
"""

from datetime import datetime, timezone

# Any single question's shown->answered gap above this is treated as "the
# student stepped away and came back," not real thinking time -- capped
# (not excluded) at this ceiling when averaging, so one abandoned-then-
# resumed question doesn't dominate the whole average. 30 minutes is a
# generous, deliberately-loose ceiling -- real answering time for even a
# hard question is minutes, not tens of minutes.
MAX_REASONABLE_SECONDS_PER_QUESTION = 30 * 60


def _seconds_between(a: str, b: str) -> float:
    """b - a, in seconds. Both are ISO timestamps as stored by db.py's now()."""
    def parse(ts):
        return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts.endswith("Z") else datetime.fromisoformat(ts)
    dt_a, dt_b = parse(a), parse(b)
    if dt_a.tzinfo is None:
        dt_a = dt_a.replace(tzinfo=timezone.utc)
    if dt_b.tzinfo is None:
        dt_b = dt_b.replace(tzinfo=timezone.utc)
    return (dt_b - dt_a).total_seconds()


def _mcq_attempt_ids_for_criteria(conn, telegram_user_id: int, since: str = None, last_n: int = None) -> list:
    """Returns the exact set of attempt_ids in scope -- every other query
    below filters against this same set, so "last 100 questions" means the
    same 100 questions everywhere in the report, not three slightly
    different slices from three separately-filtered queries."""
    if last_n:
        rows = conn.execute(
            "SELECT attempt_id FROM exam_hub_mcq_attempts WHERE telegram_user_id=? "
            "ORDER BY shown_at DESC LIMIT ?",
            (telegram_user_id, last_n),
        ).fetchall()
    elif since:
        rows = conn.execute(
            "SELECT attempt_id FROM exam_hub_mcq_attempts WHERE telegram_user_id=? AND shown_at >= ?",
            (telegram_user_id, since),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT attempt_id FROM exam_hub_mcq_attempts WHERE telegram_user_id=?",
            (telegram_user_id,),
        ).fetchall()
    return [r[0] for r in rows]


def fetch_student_report_data(conn, telegram_user_id: int, since: str = None, last_n: int = None) -> dict:
    """The one function generate_student_report.py calls. `since` (an ISO
    date/timestamp string) and `last_n` (an integer) are mutually exclusive
    -- pass at most one; neither means "all-time." Returns a plain dict,
    JSON-serializable, ready to feed straight into the HTML template."""
    if since and last_n:
        raise ValueError("Pass at most one of since/last_n, not both.")

    student_row = conn.execute(
        "SELECT username, first_name, last_name, email, mobile_number FROM students WHERE telegram_user_id=?",
        (telegram_user_id,),
    ).fetchone()
    if not student_row:
        raise ValueError(f"No student row for telegram_user_id={telegram_user_id}.")
    username, first_name, last_name, email, mobile_number = student_row

    attempt_ids = _mcq_attempt_ids_for_criteria(conn, telegram_user_id, since, last_n)
    if attempt_ids:
        placeholders = ",".join("?" * len(attempt_ids))
        mcq_rows = conn.execute(
            f"SELECT chapter_slug, chapter_label, shown_at, answered_at, is_correct "
            f"FROM exam_hub_mcq_attempts WHERE attempt_id IN ({placeholders})",
            attempt_ids,
        ).fetchall()
    else:
        mcq_rows = []

    desc_where = "telegram_user_id=?"
    desc_params = [telegram_user_id]
    if since:
        desc_where += " AND shown_at >= ?"
        desc_params.append(since)
    # last_n is a QUESTION (MCQ) concept per the original ask's own wording
    # ("last 100 questions") -- descriptive views aren't scoped by it, only
    # by since/all-time. Documented, not silently assumed.
    desc_rows = conn.execute(
        f"SELECT chapter_slug, chapter_label FROM exam_hub_descriptive_events WHERE {desc_where}",
        desc_params,
    ).fetchall()

    # --- totals ---
    mcq_shown = len(mcq_rows)
    mcq_answered = sum(1 for r in mcq_rows if r[3] is not None)
    mcq_correct = sum(1 for r in mcq_rows if r[4] == 1)
    mcq_accuracy_pct = round(100 * mcq_correct / mcq_answered, 1) if mcq_answered else None

    per_question_seconds = []
    for _, _, shown_at, answered_at, _ in mcq_rows:
        if shown_at and answered_at:
            secs = _seconds_between(shown_at, answered_at)
            if secs >= 0:
                per_question_seconds.append(min(secs, MAX_REASONABLE_SECONDS_PER_QUESTION))
    avg_seconds_per_mcq = round(sum(per_question_seconds) / len(per_question_seconds), 1) if per_question_seconds else None

    # --- chapter-wise ---
    by_chapter = {}
    for chapter_slug, chapter_label, shown_at, answered_at, is_correct in mcq_rows:
        key = chapter_slug or "unknown"
        c = by_chapter.setdefault(key, {"chapter_label": chapter_label or key, "mcq_shown": 0, "mcq_answered": 0,
                                         "mcq_correct": 0, "descriptive_shown": 0})
        c["mcq_shown"] += 1
        if answered_at is not None:
            c["mcq_answered"] += 1
        if is_correct == 1:
            c["mcq_correct"] += 1
    for chapter_slug, chapter_label in desc_rows:
        key = chapter_slug or "unknown"
        c = by_chapter.setdefault(key, {"chapter_label": chapter_label or key, "mcq_shown": 0, "mcq_answered": 0,
                                         "mcq_correct": 0, "descriptive_shown": 0})
        c["descriptive_shown"] += 1

    chapter_list = []
    for c in by_chapter.values():
        c["accuracy_pct"] = round(100 * c["mcq_correct"] / c["mcq_answered"], 1) if c["mcq_answered"] else None
        c["total_questions"] = c["mcq_shown"] + c["descriptive_shown"]
        chapter_list.append(c)
    chapter_list.sort(key=lambda c: c["total_questions"], reverse=True)

    # --- time on bot (always all-time, see module docstring) ---
    sessions = conn.execute(
        "SELECT session_id, started_at FROM exam_hub_sessions WHERE telegram_user_id=?",
        (telegram_user_id,),
    ).fetchall()
    last_activity_by_session = {}
    for session_id, ts in conn.execute(
        """
        SELECT session_id, MAX(ts) FROM (
            SELECT session_id, shown_at AS ts FROM exam_hub_mcq_attempts WHERE telegram_user_id=? AND session_id IS NOT NULL
            UNION ALL
            SELECT session_id, answered_at AS ts FROM exam_hub_mcq_attempts WHERE telegram_user_id=? AND session_id IS NOT NULL AND answered_at IS NOT NULL
            UNION ALL
            SELECT session_id, shown_at AS ts FROM exam_hub_descriptive_events WHERE telegram_user_id=? AND session_id IS NOT NULL
            UNION ALL
            SELECT session_id, answer_shown_at AS ts FROM exam_hub_descriptive_events WHERE telegram_user_id=? AND session_id IS NOT NULL AND answer_shown_at IS NOT NULL
        ) GROUP BY session_id
        """,
        (telegram_user_id, telegram_user_id, telegram_user_id, telegram_user_id),
    ).fetchall():
        last_activity_by_session[session_id] = ts

    total_time_on_bot_seconds = 0
    sessions_with_activity = 0
    for session_id, started_at in sessions:
        last_activity = last_activity_by_session.get(session_id)
        if last_activity:
            span = _seconds_between(started_at, last_activity)
            if span > 0:
                total_time_on_bot_seconds += span
                sessions_with_activity += 1

    all_activity_timestamps = [r[2] for r in mcq_rows if r[2]] + [r[3] for r in mcq_rows if r[3]]
    first_activity = min(all_activity_timestamps) if all_activity_timestamps else None
    last_activity_overall = max(all_activity_timestamps) if all_activity_timestamps else None

    if last_n:
        criteria_label = f"Last {last_n} MCQ questions"
    elif since:
        criteria_label = f"Since {since}"
    else:
        criteria_label = "All-time"

    return {
        "telegram_user_id": telegram_user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "mobile_number": mobile_number,
        "criteria_label": criteria_label,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "totals": {
            "mcq_shown": mcq_shown,
            "mcq_answered": mcq_answered,
            "mcq_correct": mcq_correct,
            "mcq_accuracy_pct": mcq_accuracy_pct,
            "descriptive_shown": len(desc_rows),
            "avg_seconds_per_mcq": avg_seconds_per_mcq,
            "total_sessions": len(sessions),
            "sessions_with_activity": sessions_with_activity,
            "total_time_on_bot_seconds": round(total_time_on_bot_seconds),
        },
        "by_chapter": chapter_list,
        "date_range": {"first_activity": first_activity, "last_activity": last_activity_overall},
    }


def fetch_today_summary(conn, telegram_user_id: int) -> dict:
    """Lightweight "how did today go" snapshot -- added 2026-08-13 for the
    "I'm Done" button (exam_hub_bot.py), distinct from
    fetch_student_report_data()'s full report (whose "time on bot" is
    deliberately ALWAYS all-time, see that function's own docstring).
    "Today" is a UTC calendar day (matches every timestamp in this schema,
    which is stored in UTC via db.py's now()) -- platform-wide, same
    centralized-account reasoning as everything else in this module.

    "Time spent today" here is a deliberately SIMPLER metric than the full
    report's session-span one: the sum of each individual question's
    shown->answered (MCQ) / shown->answer_shown (descriptive) gap, for
    only today's questions, capped at MAX_REASONABLE_SECONDS_PER_QUESTION
    per question (same cap the full report uses) -- good enough for a
    quick same-session summary, not a slice of the full report's own
    number (which counts idle-session gaps differently -- see that
    function's docstring for why the two are intentionally not the same
    computation)."""
    mcq_rows = conn.execute(
        "SELECT shown_at, answered_at, is_correct FROM exam_hub_mcq_attempts "
        "WHERE telegram_user_id=? AND date(shown_at)=date('now')",
        (telegram_user_id,),
    ).fetchall()
    desc_rows = conn.execute(
        "SELECT shown_at, answer_shown_at FROM exam_hub_descriptive_events "
        "WHERE telegram_user_id=? AND date(shown_at)=date('now')",
        (telegram_user_id,),
    ).fetchall()

    mcq_shown = len(mcq_rows)
    mcq_answered = sum(1 for _, a, _ in mcq_rows if a is not None)
    mcq_correct = sum(1 for _, _, c in mcq_rows if c == 1)
    descriptive_shown = len(desc_rows)

    seconds = []
    for shown_at, answered_at, _ in mcq_rows:
        if shown_at and answered_at:
            secs = _seconds_between(shown_at, answered_at)
            if secs >= 0:
                seconds.append(min(secs, MAX_REASONABLE_SECONDS_PER_QUESTION))
    for shown_at, answer_shown_at in desc_rows:
        if shown_at and answer_shown_at:
            secs = _seconds_between(shown_at, answer_shown_at)
            if secs >= 0:
                seconds.append(min(secs, MAX_REASONABLE_SECONDS_PER_QUESTION))

    return {
        "mcq_shown": mcq_shown,
        "mcq_answered": mcq_answered,
        "mcq_correct": mcq_correct,
        "descriptive_shown": descriptive_shown,
        "questions_attempted_today": mcq_shown + descriptive_shown,
        "time_spent_today_seconds": round(sum(seconds)),
    }


def platform_wide_mcq_answered_count(conn, telegram_user_id: int) -> int:
    """Used by the 20-question milestone trigger -- platform-wide, all
    bots, all time, ANSWERED (not just shown) MCQs. A dedicated small
    function rather than callers hand-rolling this exact query, so the
    milestone definition lives in one place."""
    row = conn.execute(
        "SELECT COUNT(*) FROM exam_hub_mcq_attempts WHERE telegram_user_id=? AND answered_at IS NOT NULL",
        (telegram_user_id,),
    ).fetchone()
    return row[0] if row else 0
