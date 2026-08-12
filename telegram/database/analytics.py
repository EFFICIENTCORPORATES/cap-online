"""
telegram/database/analytics.py -- shared query layer for every reporting
surface (2026-08-10, built same day as the platform DB itself)
-----------------------------------------------------------------------------
Single source of truth for "what does the platform DB actually say right
now" -- both telegram/tools/generate_dashboard.py (static snapshot, you
re-run it and open the file) and telegram/tools/dashboard_server.py (live,
Refresh-button version) call the SAME functions here instead of each having
its own copy of these queries. Same principle CLAUDE.md section 7 already
states for print/pagination CSS ("one JSON file is the only place geometry
numbers live") applied to analytics queries instead: a metric definition
changes here once, and both surfaces pick it up.

Every function takes an open db.get_connection() connection and returns
plain JSON-serializable Python (dicts/lists/ints/strings) -- never a raw
cursor/Row object -- so callers can json.dumps() the result directly.
"""

import sys
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import validate_content_json  # noqa: E402 -- must follow the sys.path.insert() above

TENANTS_PATH = Path(__file__).resolve().parents[1] / "config" / "tenants.json"

HEARTBEAT_STALE_AFTER_SECONDS = 360   # 3x the 120s heartbeat interval in db.py's schedule_heartbeat()
                                       # -- kept as the same literal manage_bots.py's own
                                       # HEARTBEAT_STALE_AFTER_SECONDS uses; if one changes, change both.


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts.endswith("Z") else datetime.fromisoformat(ts)


def fetch_heartbeats(conn, stale_after_seconds: int = HEARTBEAT_STALE_AFTER_SECONDS) -> dict:
    """{bot_id: {pid, last_heartbeat_at, age_seconds, online}} -- "online"
    means the heartbeat is fresh, regardless of whether the OS-level PID is
    still technically alive (see schema.sql's own note on why heartbeat
    freshness, not raw PID existence, is the trust signal here)."""
    rows = conn.execute("SELECT bot_id, pid, last_heartbeat_at FROM bot_heartbeats").fetchall()
    now = datetime.now(timezone.utc)
    out = {}
    for bot_id, pid, last in rows:
        try:
            last_dt = _parse_iso(last)
        except ValueError:
            continue
        age = (now - last_dt).total_seconds()
        out[bot_id] = {
            "pid": pid, "last_heartbeat_at": last, "age_seconds": age,
            "online": age < stale_after_seconds,
        }
    return out


def fetch_daily_activity(conn) -> dict:
    """{date_str: {bot_id: {"count": n, "users": [id, id, ...]}}} -- the
    shape generate_dashboard.py's/dashboard_server.py's JS needs to compute
    both message-volume bars and true distinct-visitor counts for any date
    range, client-side (a set union across days, not a sum of daily
    uniques -- see database/README.md)."""
    rows = conn.execute(
        "SELECT substr(created_at,1,10) AS d, bot_id, telegram_user_id FROM bot_interactions"
    ).fetchall()
    daily = defaultdict(lambda: defaultdict(lambda: {"count": 0, "users": set()}))
    for d, bot_id, user_id in rows:
        daily[d][bot_id]["count"] += 1
        daily[d][bot_id]["users"].add(user_id)
    return {
        d: {bot_id: {"count": v["count"], "users": sorted(v["users"])} for bot_id, v in bots.items()}
        for d, bots in daily.items()
    }


def fetch_unique_mcq_attempters(conn) -> int:
    """Distinct students, platform-wide, who have shown at least one MCQ --
    added 2026-08-11 to sit next to "Unique Visitors" and make the real
    difference between the two visible, not just explainable after the
    fact. Pranav's own observation: Student Breakdown showed 14+2=16
    students (a naive SUM across two bots -- but 2 of those students used
    BOTH bots, so the true unique count across bots was smaller than the
    sum) while Unique Visitors showed 32 (bot_interactions, ALL 8 bots --
    including Study Hub/MyFiles Hub -- and ANY interaction, not just MCQ
    attempts; confirmed separately that most of that gap, 18 of 33 total
    visitors at the time this was investigated, never attempted a single
    MCQ at all). Neither number was wrong -- they measure different
    populations. This is the third, unambiguous number: real unique
    MCQ-attempters, deduped across every bot."""
    row = conn.execute("SELECT COUNT(DISTINCT telegram_user_id) FROM exam_hub_mcq_attempts").fetchone()
    return row[0] if row else 0


def fetch_bot_summary(conn) -> dict:
    """Bot-wise usage summary, all-time -- the "on demand summary of usage
    metrics, bot-wise" Pranav asked for 2026-08-10, delivered as a dashboard
    view (his choice) rather than a Telegram command. One dict per bot_id
    that has ANY row in ANY table below (a configured-but-never-run bot
    simply doesn't appear -- not shown as all-zeroes, so an empty platform
    doesn't look like a broken one).

    Deliberately all-time, not date-ranged (unlike fetch_daily_activity,
    which the chart already ranges client-side) -- this is a "how is each
    bot doing overall" view, not a trend view. Re-add range filtering here
    later if that turns out to be wanted; not built speculatively."""
    summary = defaultdict(lambda: {
        "total_interactions": 0, "unique_users": 0, "first_seen_at": None, "last_seen_at": None,
        "study_hub": None, "exam_hub": None,
    })

    # --- generic interaction volume (every bot writes here) ---
    for bot_id, count, users, first, last in conn.execute(
        "SELECT bot_id, COUNT(*), COUNT(DISTINCT telegram_user_id), MIN(created_at), MAX(created_at) "
        "FROM bot_interactions GROUP BY bot_id"
    ).fetchall():
        summary[bot_id]["total_interactions"] = count
        summary[bot_id]["unique_users"] = users
        summary[bot_id]["first_seen_at"] = first
        summary[bot_id]["last_seen_at"] = last

    # --- Study Hub: downloads + search behavior ---
    for bot_id, event_type, count in conn.execute(
        "SELECT bot_id, event_type, COUNT(*) FROM study_hub_events GROUP BY bot_id, event_type"
    ).fetchall():
        sh = summary[bot_id]["study_hub"] or {"file_download": 0, "search_query": 0, "search_no_match": 0}
        sh[event_type] = count
        summary[bot_id]["study_hub"] = sh

    # --- Exam Hub: sessions, MCQ attempts + accuracy, descriptive views ---
    for bot_id, count in conn.execute(
        "SELECT bot_id, COUNT(*) FROM exam_hub_sessions GROUP BY bot_id"
    ).fetchall():
        eh = summary[bot_id]["exam_hub"] or _blank_exam_hub()
        eh["sessions"] = count
        summary[bot_id]["exam_hub"] = eh

    for bot_id, shown, answered, correct in conn.execute(
        "SELECT bot_id, COUNT(*), COUNT(answered_at), "
        "SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) FROM exam_hub_mcq_attempts GROUP BY bot_id"
    ).fetchall():
        eh = summary[bot_id]["exam_hub"] or _blank_exam_hub()
        eh["mcq_shown"] = shown
        eh["mcq_answered"] = answered
        eh["mcq_correct"] = correct or 0
        eh["mcq_accuracy_pct"] = round(100 * (correct or 0) / answered, 1) if answered else None
        summary[bot_id]["exam_hub"] = eh

    for bot_id, shown, answer_shown, pdf_requested in conn.execute(
        "SELECT bot_id, COUNT(*), COUNT(answer_shown_at), COUNT(pdf_requested_at) "
        "FROM exam_hub_descriptive_events GROUP BY bot_id"
    ).fetchall():
        eh = summary[bot_id]["exam_hub"] or _blank_exam_hub()
        eh["descriptive_shown"] = shown
        eh["descriptive_answer_viewed"] = answer_shown
        eh["descriptive_pdf_requested"] = pdf_requested
        summary[bot_id]["exam_hub"] = eh

    return dict(summary)


def _blank_exam_hub() -> dict:
    return {
        "sessions": 0,
        "mcq_shown": 0, "mcq_answered": 0, "mcq_correct": 0, "mcq_accuracy_pct": None,
        "descriptive_shown": 0, "descriptive_answer_viewed": 0, "descriptive_pdf_requested": 0,
    }


def fetch_content_health() -> list:
    """The Content Health view's data -- a live re-run of
    telegram/tools/validate_content_json.py's validate_all() on every call
    (added 2026-08-10, per Pranav's ask: "core fields are consistent...
    validations triggered through that admin port"). Deliberately not
    cached -- a content file can change between two dashboard loads (a
    faculty's new docx conversion, a hand-edit), and this is meant to be
    the trustworthy "is it safe right now" answer, not a stale one. No
    `conn` argument -- unlike every other fetch_* here, this reads JSON
    files directly, not the platform DB."""
    return validate_content_json.validate_all()


def fetch_student_breakdown_by_bot(conn, bot_ids: list) -> dict:
    """{bot_id: [{telegram_user_id, display_name, attempted, answered,
    correct, wrong, accuracy_pct}, ...]} for every bot_id in `bot_ids` --
    added 2026-08-11, Pranav's ask: "a dropdown of bot name and based on
    that it will show me CHAT ID wise no of questions attempted, answered
    and correct and wrong." Only bots with MCQ data show up meaningfully
    (a study/myfiles/dashboard/watcher bot_id just gets an empty list --
    not an error, there's genuinely nothing to show)."""
    out = {}
    for bot_id in bot_ids:
        rows = conn.execute(
            """
            SELECT a.telegram_user_id,
                   COALESCE(s.first_name || ' ' || COALESCE(s.last_name, ''), s.username, 'Student ' || a.telegram_user_id) AS display_name,
                   COUNT(*) AS attempted,
                   SUM(CASE WHEN a.answered_at IS NOT NULL THEN 1 ELSE 0 END) AS answered,
                   SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) AS correct
            FROM exam_hub_mcq_attempts a
            LEFT JOIN students s ON s.telegram_user_id = a.telegram_user_id
            WHERE a.bot_id = ?
            GROUP BY a.telegram_user_id
            ORDER BY attempted DESC
            """,
            (bot_id,),
        ).fetchall()
        out[bot_id] = [
            {
                "telegram_user_id": r[0],
                "display_name": (r[1] or "").strip() or f"Student {r[0]}",
                "attempted": r[2],
                "answered": r[3],
                "correct": r[4],
                "wrong": r[3] - r[4],
                "accuracy_pct": round(100 * r[4] / r[3], 1) if r[3] else None,
            }
            for r in rows
        ]
    return out


def fetch_faculty_report(conn, bot_ids: list) -> dict:
    """{bot_id: [{telegram_user_id, display_name, total_attempted,
    total_correct, accuracy_pct, chapters: [{chapter_slug, chapter_label,
    mcq_attempted, mcq_correct, accuracy_pct, descriptive_shown}, ...]}]}
    -- added 2026-08-11 (Phase 3 of the roadmap), Pranav's ask: "a Faculty
    specific report, where we will give student wise, chapter wise
    analysis which will help faculty to identify which students are doing
    good." Same per-chat-id granularity as fetch_student_breakdown_by_bot
    above (not per-username) -- a student practicing from two phones shows
    as two separate rows here today, same known limitation that table
    already has; see telegram/PROFILE-SYSTEM.md for the username-linking
    layer this could be upgraded to aggregate through later.

    Sorted by total_attempted descending within each bot -- "who's
    actually engaging" is the first useful signal before accuracy is even
    meaningful (a 100%-accuracy student on 2 questions tells a faculty
    much less than an 80%-accuracy student on 200)."""
    out = {}
    for bot_id in bot_ids:
        mcq_rows = conn.execute(
            """
            SELECT a.telegram_user_id,
                   COALESCE(s.first_name || ' ' || COALESCE(s.last_name, ''), s.username, 'Student ' || a.telegram_user_id) AS display_name,
                   a.chapter_slug, a.chapter_label,
                   COUNT(*) AS mcq_attempted,
                   SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) AS mcq_correct
            FROM exam_hub_mcq_attempts a
            LEFT JOIN students s ON s.telegram_user_id = a.telegram_user_id
            WHERE a.bot_id = ? AND a.answered_at IS NOT NULL
            GROUP BY a.telegram_user_id, a.chapter_slug
            """,
            (bot_id,),
        ).fetchall()
        desc_rows = conn.execute(
            """
            SELECT telegram_user_id, chapter_slug, chapter_label, COUNT(*)
            FROM exam_hub_descriptive_events WHERE bot_id = ?
            GROUP BY telegram_user_id, chapter_slug
            """,
            (bot_id,),
        ).fetchall()

        students = {}
        for uid, display_name, chapter_slug, chapter_label, attempted, correct in mcq_rows:
            student = students.setdefault(uid, {"telegram_user_id": uid, "display_name": display_name, "chapters": {}})
            key = chapter_slug or "unknown"
            ch = student["chapters"].setdefault(key, {
                "chapter_slug": key, "chapter_label": chapter_label or key,
                "mcq_attempted": 0, "mcq_correct": 0, "descriptive_shown": 0,
            })
            ch["mcq_attempted"] += attempted
            ch["mcq_correct"] += correct or 0

        for uid, chapter_slug, chapter_label, shown in desc_rows:
            student = students.setdefault(uid, {"telegram_user_id": uid, "display_name": f"Student {uid}", "chapters": {}})
            key = chapter_slug or "unknown"
            ch = student["chapters"].setdefault(key, {
                "chapter_slug": key, "chapter_label": chapter_label or key,
                "mcq_attempted": 0, "mcq_correct": 0, "descriptive_shown": 0,
            })
            ch["descriptive_shown"] += shown

        rows_out = []
        for student in students.values():
            chapters = list(student["chapters"].values())
            for c in chapters:
                c["accuracy_pct"] = round(100 * c["mcq_correct"] / c["mcq_attempted"], 1) if c["mcq_attempted"] else None
            chapters.sort(key=lambda c: c["mcq_attempted"] + c["descriptive_shown"], reverse=True)

            total_attempted = sum(c["mcq_attempted"] for c in chapters)
            total_correct = sum(c["mcq_correct"] for c in chapters)
            rows_out.append({
                "telegram_user_id": student["telegram_user_id"],
                "display_name": student["display_name"],
                "total_attempted": total_attempted,
                "total_correct": total_correct,
                "accuracy_pct": round(100 * total_correct / total_attempted, 1) if total_attempted else None,
                "chapters": chapters,
            })
        rows_out.sort(key=lambda r: r["total_attempted"], reverse=True)
        out[bot_id] = rows_out
    return out


def fetch_student_master(conn, bots: list) -> list:
    """One row per student in the `students` table -- contact info plus
    which faculty/course(s) they've actually studied, derived from REAL
    recorded activity (not a bot's full possible content_scope, which
    would overstate what they've actually touched). Added 2026-08-11,
    Pranav's ask: "Student ID, Name, Number, Email... which Courses,
    Subject, Faculty he is studying or he is doing self study" -- "so that
    we can cater him properly as per his needs."

    A student who has only ever used a platform bot (1lavya-studyhub/
    1lavya-examhub) shows as "Self Study" -- no dedicated faculty. A
    student can legitimately show MULTIPLE faculties/courses if they've
    used more than one bot (e.g. a test account touching both a faculty's
    bot and the flagship)."""
    bot_meta = {b["bot_id"]: b for b in bots}
    tenants_data = json.loads(TENANTS_PATH.read_text(encoding="utf-8"))
    tenant_meta = {t["tenant_id"]: t for t in tenants_data["tenants"]}

    students = conn.execute(
        "SELECT telegram_user_id, username, first_name, last_name, email, mobile_number, "
        "first_seen_at, last_seen_at FROM students ORDER BY last_seen_at DESC"
    ).fetchall()

    # Real (student, bot, course, level, subject) activity -- union across
    # every table that carries course/level, so "what they study" reflects
    # what they've actually touched, not a bot's full possible scope.
    activity_rows = conn.execute(
        """
        SELECT telegram_user_id, bot_id, course, level, subject FROM study_hub_events WHERE course IS NOT NULL AND course != ''
        UNION
        SELECT telegram_user_id, bot_id, course, level, NULL FROM exam_hub_sessions WHERE course IS NOT NULL AND course != ''
        UNION
        SELECT telegram_user_id, bot_id, course, level, NULL FROM exam_hub_mcq_attempts WHERE course IS NOT NULL AND course != ''
        UNION
        SELECT telegram_user_id, bot_id, course, level, NULL FROM exam_hub_descriptive_events WHERE course IS NOT NULL AND course != ''
        """
    ).fetchall()

    activity_by_student = defaultdict(list)
    for uid, bot_id, course, level, subject in activity_rows:
        activity_by_student[uid].append((bot_id, course, level, subject))

    out = []
    for uid, username, first_name, last_name, email, mobile, first_seen, last_seen in students:
        name = " ".join(p for p in (first_name, last_name) if p).strip() or username or f"Student {uid}"
        faculty_labels = set()
        # Keyed by (course, level) so the SAME course+level seen with and
        # without a subject (study_hub_events carries subject, the exam_hub
        # tables don't) collapses into one entry -- prefer the more
        # specific (subject-bearing) version rather than showing both.
        course_key_to_subject = {}
        for bot_id, course, level, subject in activity_by_student.get(uid, []):
            bot = bot_meta.get(bot_id)
            tenant_id = bot.get("tenant_id") if bot else None
            tenant = tenant_meta.get(tenant_id) if tenant_id else None
            if tenant and tenant.get("kind") == "faculty":
                faculty_labels.add(tenant["display_name"])
            else:
                faculty_labels.add("Self Study (1LAVYA Shared Pool)")
            key = (course or "Unknown", level)
            if key not in course_key_to_subject or (subject and not course_key_to_subject[key]):
                course_key_to_subject[key] = subject

        course_labels = set()
        for (course, level), subject in course_key_to_subject.items():
            label = course
            if level:
                label += f" {level}"
            if subject:
                label += f" ({subject})"
            course_labels.add(label)

        out.append({
            "telegram_user_id": uid,
            "display_name": name,
            "username": username,
            "email": email,
            "mobile_number": mobile,
            "faculty": sorted(faculty_labels) or ["No activity yet"],
            "courses": sorted(course_labels) or ["No activity yet"],
            "first_seen_at": first_seen,
            "last_seen_at": last_seen,
        })
    return out


def fetch_all(conn, bots: list) -> dict:
    """Everything one API response / one static HTML build needs, in one
    call -- what both generate_dashboard.py's main() and
    dashboard_server.py's /api/data handler actually call."""
    bot_meta = {
        b["bot_id"]: {"kind": b["kind"], "tenant_id": b.get("tenant_id"), "display_name": b["display_name"],
                       "status": b.get("status", "unknown")}
        for b in bots
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bots": bot_meta,
        "heartbeats": fetch_heartbeats(conn),
        "daily": fetch_daily_activity(conn),
        "summary": fetch_bot_summary(conn),
        "content_health": fetch_content_health(),
        "student_breakdown": fetch_student_breakdown_by_bot(conn, [b["bot_id"] for b in bots if b["kind"] in ("exam", "unified")]),
        "faculty_report": fetch_faculty_report(conn, [b["bot_id"] for b in bots if b["kind"] in ("exam", "unified")]),
        "student_master": fetch_student_master(conn, bots),
        "unique_mcq_attempters": fetch_unique_mcq_attempters(conn),
    }
