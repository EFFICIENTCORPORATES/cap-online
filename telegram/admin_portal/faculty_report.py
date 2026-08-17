"""
telegram/admin_portal/faculty_report.py -- Comprehensive Faculty Report
(2026-08-14, Pranav's ask: a full per-faculty, any-date-range report --
"He should first get the subjects and levels which are live... how many
MCQs and Descriptive question access do students have... which are the
most accessed chapters, practiced chapter... which Chapter has most MCQ
attempted, correct and time spent... Same should be there for all Subject
live for him across all courses... he should get to know about Students
performance... Last 7 days analysis... which student is doing which
chapters the most... which were the questions which were mostly made
wrong... All of these deterministic reports... need any commentary in
report, just raw facts, arranged properly with proper table headings.")

REVISED 2026-08-17 -- Level-wise segmentation + username-rollup identity
+ Day End Report + colorful PDF (Pranav's follow-up ask, confirmed via
AskUserQuestion): "Students of Each level... in case of CS Arun, we have
3 levels live... show the Report for each level separately." Two locked
decisions from that confirmation round:
  1. Student identity in Sections 3/4/5 is now the student's permanent
     1LAVYA username (student_profiles/students.lavya_username), with
     activity merged across every linked telegram_user_id (phone) --
     matching telegram/database/leaderboard_metrics.py's own "one
     identity, several phones" rollup, not a new mechanism. A student's
     linked chat_ids are still shown (comma-joined) so a faculty can
     still identify/message them -- just no longer the PRIMARY key.
  2. The whole report is now built once per (course, level) pair in the
     tenant's own content_scope (single combined document, level sections
     stacked inside -- Pranav's confirmed choice over separate files per
     level), reusing content_availability()'s existing source of that
     (course, level) list -- no new config.
--------------------------------------------------------------------------------
Six sections per level, every one a plain deterministic table (no
narrative text, no scoring/opinion) built straight from platform activity
logs:

  1. content_availability()   -- which (course, level, subject) this
                                  faculty's students can access, and how
                                  many MCQ/Descriptive questions exist for
                                  each -- a STATIC snapshot (not date-
                                  ranged; "how many questions exist" isn't
                                  a time-boxed fact). Reuses
                                  document_catalog.question_bank_rows(),
                                  the same 100%-accurate-by-construction
                                  human_id-derived counter the Course
                                  Catalog page already uses -- not a second
                                  counting method.
  2. chapter_stats()          -- per chapter within ONE (course, level):
                                  unique students (by username), MCQ
                                  shown/answered/correct/accuracy, time
                                  spent, descriptive views. Sorted
                                  most-practiced first.
  3. student_performance()    -- per STUDENT (by 1LAVYA username, every
                                  linked chat_id's activity merged): the
                                  same metrics, sorted most-active first.
  4. student_last7days()      -- per (student, day) for the real last 7
                                  UTC calendar days -- a FIXED window,
                                  independent of the report's own date
                                  range (this is "how are things going
                                  right now," not a slice of an arbitrary
                                  custom range).
  5. student_chapter_matrix() -- one row per (student, chapter) they've
                                  touched, ranked within that student's own
                                  activity (rank 1 = their most-practiced
                                  chapter) -- "which student is doing which
                                  chapters the most."
  6. question_difficulty()    -- per MCQ: how often answered, how often
                                  wrong, and the single most commonly
                                  chosen WRONG option (not just "wrong" in
                                  general) -- sorted worst-first. Filtered
                                  to >=2 real attempts so a single fluke
                                  answer doesn't show as "100% wrong."

Every function takes an open db connection (and, where relevant, the list
of bot_ids to scope to, plus an optional course/level filter) and returns
plain JSON-serializable Python -- same convention telegram/database/
analytics.py already follows. build_report() assembles one level-block per
(course, level) the tenant serves, each with all 6 sections, plus tenant/
range metadata into one dict; render_full_report_html()/build_report_pdf()/
build_report_xlsx() turn that into the three downloadable formats, and
send_report_email() emails the PDF version to the faculty.

TENANT VS BOT: a tenant (telegram/config/tenants.json) can map to more than
one bot process (telegram/config/bots.json) -- e.g. CA Pranav has two,
capranav-study + capranav-exam. This report is scoped to a TENANT, not one
bot, and pools activity across every bot linked to that tenant (via
_exam_bot_ids_for_tenant()/_all_bot_ids_for_tenant()) so "Faculty X's
report" always means everything that faculty's students did, not one bot's
slice of it. Sections 2-6 (all activity-log-derived) only query bots of
kind exam/unified (the only kinds that write exam_hub_mcq_attempts/
exam_hub_descriptive_events) -- a study-only bot contributes nothing to
those tables today, correctly excluded rather than silently double-counted
as zero.

DAY END REPORT (2026-08-17): no new mechanism -- "day end" is simply
build_report(conn, tenant_id, bots, start_date=today, end_date=today) using
the platform's existing UTC-calendar-day convention (same one
last_7_days_range() already uses). Exposed two ways: (1) a "Day End
(Today)" button on the Admin Portal's /reports/faculty page (app.py), and
(2) telegram/tools/generate_day_end_faculty_reports.py, a scheduled batch
script that generates + PDF-saves every real faculty's day-end report to
disk nightly -- see that script's own docstring.
"""

from __future__ import annotations

import io
import sys
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "branding"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import student_analytics  # noqa: E402 -- telegram/database/student_analytics.py, for _seconds_between()/the same 30-min-per-question time cap the student report already uses
import brand_kit  # noqa: E402
import cf_email  # noqa: E402 -- telegram/database/cf_email.py
import document_catalog  # noqa: E402 -- sibling module in admin_portal/
import faculty_master  # noqa: E402 -- sibling module in admin_portal/, telegram/admin_portal/faculty_master.py (2026-08-14)

from openpyxl import Workbook  # noqa: E402
from xhtml2pdf import pisa  # noqa: E402

TENANTS_PATH = REPO_ROOT / "telegram" / "config" / "tenants.json"
BOTS_PATH = REPO_ROOT / "telegram" / "config" / "bots.json"

# Same per-question time-spent ceiling the student report/leaderboard/
# "I'm Done" summary all already use (student_analytics.py's own constant)
# -- one abandoned-then-resumed question shouldn't blow up a chapter's or
# student's "time spent" total.
TIME_CAP_SECONDS = student_analytics.MAX_REASONABLE_SECONDS_PER_QUESTION

# A question answered only once or twice tells you nothing about whether
# it's genuinely confusing -- a single wrong guess would otherwise show as
# "100% wrong." Filters question_difficulty() to questions with at least
# this many real recorded answers before it's included at all.
MIN_ATTEMPTS_FOR_DIFFICULTY = 2


# ---------------------------------------------------------------------------
# Tenant / bot resolution
# ---------------------------------------------------------------------------
def _load_tenants() -> dict:
    data = json.loads(TENANTS_PATH.read_text(encoding="utf-8"))
    return {t["tenant_id"]: t for t in data["tenants"]}


def list_reportable_tenants(conn, bots: list) -> list:
    """Every tenant with at least one linked bot -- used to populate the
    report's tenant/faculty picker. Platform tenants (1lavya-studyhub/
    1lavya-examhub) are included too, sorted after real faculty tenants --
    a report against the flagship pool is a legitimate thing to want (e.g.
    "how is the shared 1LAVYA content doing overall"), just listed second.

    contact_email comes from the faculty_master DB table (2026-08-14),
    NOT tenants.json -- see that table's own schema.sql comment and
    telegram/admin_portal/faculty_master.py for why."""
    tenants = _load_tenants()
    bots_by_tenant = defaultdict(list)
    for b in bots:
        if b.get("tenant_id"):
            bots_by_tenant[b["tenant_id"]].append(b)

    out = []
    for tenant_id, t in tenants.items():
        linked = bots_by_tenant.get(tenant_id, [])
        if not linked:
            continue
        master = faculty_master.get_faculty_master(conn, tenant_id)
        out.append({
            "tenant_id": tenant_id,
            "display_name": t.get("display_name", tenant_id),
            "kind": t.get("kind"),
            "contact_email": master["contact_email"] if master else None,
            "bot_ids": [b["bot_id"] for b in linked],
        })
    out.sort(key=lambda r: (r["kind"] != "faculty", r["display_name"]))
    return out


def list_faculty_tenant_ids(conn, bots: list) -> list:
    """Just the real faculty tenants (kind=="faculty") with linked bots --
    e.g. ["capranav", "csarunchouhan"] today. Used by
    generate_day_end_faculty_reports.py so that script never needs its own
    copy of "what counts as a faculty" -- one definition, reused."""
    return [t["tenant_id"] for t in list_reportable_tenants(conn, bots) if t["kind"] == "faculty"]


def _exam_bot_ids_for_tenant(tenant_id: str, bots: list) -> list:
    """Only bots that actually write exam_hub_mcq_attempts/
    exam_hub_descriptive_events -- see module docstring."""
    return [b["bot_id"] for b in bots if b.get("tenant_id") == tenant_id and b["kind"] in ("exam", "unified")]


def _all_bot_ids_for_tenant(tenant_id: str, bots: list) -> list:
    return [b["bot_id"] for b in bots if b.get("tenant_id") == tenant_id]


# ---------------------------------------------------------------------------
# Section 1 -- content availability (static, not date-ranged)
# ---------------------------------------------------------------------------
def _content_scope_entries(conn, tenant: dict) -> list:
    scope = tenant.get("content_scope")
    if scope == "ALL":
        rows = conn.execute(
            "SELECT DISTINCT course, level, subject FROM course_catalog ORDER BY course, level, subject"
        ).fetchall()
        return [{"course": c, "level": l, "subject": s} for c, l, s in rows]
    return [{"course": e["course"], "level": e["level"], "subject": e["subject"]} for e in (scope or [])]


def _content_scope_levels(conn, tenant: dict) -> list:
    """Distinct (course, level) pairs this tenant serves, in first-seen
    order -- the report is built once per pair (see module docstring,
    2026-08-17). Reuses _content_scope_entries(), the same source
    content_availability() already reads -- no second scope mechanism."""
    seen = []
    for e in _content_scope_entries(conn, tenant):
        key = (e["course"], e["level"])
        if key not in seen:
            seen.append(key)
    return seen


def content_availability(conn, tenant: dict) -> list:
    out = []
    for entry in _content_scope_entries(conn, tenant):
        rows = document_catalog.question_bank_rows(conn, entry["course"], entry["level"], entry["subject"])
        mcq = sum(r["mcq_count"] for r in rows)
        desc = sum(r["descriptive_count"] for r in rows)
        covered = sum(1 for r in rows if r["mcq_count"] or r["descriptive_count"])
        out.append({
            "course": entry["course"], "level": entry["level"], "subject": entry["subject"],
            "chapters_total": len(rows), "chapters_with_content": covered,
            "mcq_count": mcq, "descriptive_count": desc, "total_count": mcq + desc,
        })
    out.sort(key=lambda r: r["total_count"], reverse=True)
    return out


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _date_where(column: str, start_date, end_date, params: list) -> list:
    clauses = []
    if start_date:
        clauses.append(f"date({column}) >= ?")
        params.append(start_date)
    if end_date:
        clauses.append(f"date({column}) <= ?")
        params.append(end_date)
    return clauses


def _scope_where(course, level, params: list) -> list:
    """course/level filter shared by every Section 2-6 query -- both
    exam_hub_mcq_attempts and exam_hub_descriptive_events already carry
    their own course/level columns per row (set at content-tagging time),
    so this is a plain equality filter, nothing new to compute."""
    clauses = []
    if course:
        clauses.append("course = ?")
        params.append(course)
    if level:
        clauses.append("level = ?")
        params.append(level)
    return clauses


def _seconds_capped(shown_at, ended_at):
    if not (shown_at and ended_at):
        return 0.0
    secs = student_analytics._seconds_between(shown_at, ended_at)
    return min(secs, TIME_CAP_SECONDS) if secs and secs >= 0 else 0.0


def today_utc_date() -> str:
    """The platform's one definition of "today" for date-ranged queries --
    a UTC calendar day, matching last_7_days_range() and every activity
    timestamp (db.now() itself is UTC). Used for the Day End Report so it
    means the same "today" everywhere it's read, not a separate local-time
    definition."""
    return datetime.now(timezone.utc).date().isoformat()


# ---------------------------------------------------------------------------
# Identity: username rollup (2026-08-17) -- every student in Sections 3-5
# is keyed by their permanent 1LAVYA username, with activity merged across
# every telegram_user_id (phone) linked to it, matching
# leaderboard_metrics.py's own "one identity, several phones" model. A
# student who has never touched a wallet-gated flow yet (no lavya_username
# set) still gets a stable per-chat_id fallback key so no row is ever
# silently dropped -- just never merged with anyone else's, correctly,
# since there's nothing yet to merge.
# ---------------------------------------------------------------------------
def _uid_identity_map(conn) -> dict:
    """telegram_user_id -> {"username": str, "display_name": str}.
    `username` is students.lavya_username when set, else a private
    per-chat_id placeholder (never shown to a faculty -- display_name
    always reads naturally either way). display_name prefers the
    student's own profile display_name (student_profiles, set via
    "profile" in any bot), then their Telegram first+last name, then their
    Telegram @handle, then a generic "Student {id}" -- same fallback order
    student report/leaderboard code already uses elsewhere."""
    rows = conn.execute(
        "SELECT s.telegram_user_id, s.lavya_username, s.first_name, s.last_name, s.username, sp.display_name "
        "FROM students s LEFT JOIN student_profiles sp ON sp.username = s.lavya_username"
    ).fetchall()
    out = {}
    for uid, lavya_username, first, last, tg_username, profile_display in rows:
        username = lavya_username or f"__unlinked_{uid}"
        name = (profile_display or "").strip() or " ".join(p for p in (first, last) if p).strip() \
            or tg_username or f"Student {uid}"
        out[uid] = {"username": username, "display_name": name}
    return out


def _identity_for(uid_map: dict, uid: int) -> dict:
    return uid_map.get(uid) or {"username": f"__unlinked_{uid}", "display_name": f"Student {uid}"}


# ---------------------------------------------------------------------------
# Section 2 -- chapter-wise practice, within ONE (course, level)
# ---------------------------------------------------------------------------
def chapter_stats(conn, bot_ids: list, start_date: str = None, end_date: str = None,
                   course: str = None, level: str = None, uid_map: dict = None) -> list:
    if not bot_ids:
        return []
    uid_map = uid_map if uid_map is not None else _uid_identity_map(conn)
    placeholders = ",".join("?" * len(bot_ids))

    mcq_params = list(bot_ids)
    mcq_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, mcq_params) \
        + _scope_where(course, level, mcq_params)
    mcq_rows = conn.execute(
        f"""SELECT chapter_slug, chapter_label, course, level, telegram_user_id, shown_at, answered_at, is_correct
            FROM exam_hub_mcq_attempts WHERE {' AND '.join(mcq_where)}""",
        mcq_params,
    ).fetchall()

    desc_params = list(bot_ids)
    desc_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, desc_params) \
        + _scope_where(course, level, desc_params)
    desc_rows = conn.execute(
        f"""SELECT chapter_slug, chapter_label, course, level, telegram_user_id, shown_at, answer_shown_at
            FROM exam_hub_descriptive_events WHERE {' AND '.join(desc_where)}""",
        desc_params,
    ).fetchall()

    def _blank(chapter_slug, chapter_label, course_, level_):
        return {
            "chapter_slug": chapter_slug, "chapter_label": chapter_label or chapter_slug, "course": course_, "level": level_,
            "mcq_shown": 0, "mcq_answered": 0, "mcq_correct": 0, "mcq_seconds": 0.0,
            "descriptive_shown": 0, "descriptive_seconds": 0.0, "usernames": set(),
        }

    by_chapter = {}
    for chapter_slug, chapter_label, c_, l_, uid, shown_at, answered_at, is_correct in mcq_rows:
        key = chapter_slug or "unknown"
        c = by_chapter.setdefault(key, _blank(key, chapter_label, c_, l_))
        c["mcq_shown"] += 1
        c["usernames"].add(_identity_for(uid_map, uid)["username"])
        if answered_at is not None:
            c["mcq_answered"] += 1
            c["mcq_seconds"] += _seconds_capped(shown_at, answered_at)
        if is_correct == 1:
            c["mcq_correct"] += 1

    for chapter_slug, chapter_label, c_, l_, uid, shown_at, answer_shown_at in desc_rows:
        key = chapter_slug or "unknown"
        c = by_chapter.setdefault(key, _blank(key, chapter_label, c_, l_))
        c["descriptive_shown"] += 1
        c["usernames"].add(_identity_for(uid_map, uid)["username"])
        c["descriptive_seconds"] += _seconds_capped(shown_at, answer_shown_at)

    out = []
    for c in by_chapter.values():
        out.append({
            "chapter_slug": c["chapter_slug"], "chapter_label": c["chapter_label"],
            "course": c["course"], "level": c["level"], "unique_students": len(c["usernames"]),
            "mcq_shown": c["mcq_shown"], "mcq_answered": c["mcq_answered"], "mcq_correct": c["mcq_correct"],
            "mcq_accuracy_pct": round(100 * c["mcq_correct"] / c["mcq_answered"], 1) if c["mcq_answered"] else None,
            "time_spent_minutes": round((c["mcq_seconds"] + c["descriptive_seconds"]) / 60, 1),
            "descriptive_shown": c["descriptive_shown"],
        })
    out.sort(key=lambda r: (r["mcq_shown"] + r["descriptive_shown"]), reverse=True)
    return out


# ---------------------------------------------------------------------------
# Section 3 -- student-wise performance, by username (every linked phone
# merged), within ONE (course, level)
# ---------------------------------------------------------------------------
def student_performance(conn, bot_ids: list, start_date: str = None, end_date: str = None,
                         course: str = None, level: str = None, uid_map: dict = None) -> list:
    if not bot_ids:
        return []
    uid_map = uid_map if uid_map is not None else _uid_identity_map(conn)
    placeholders = ",".join("?" * len(bot_ids))

    def _blank():
        return {"mcq_shown": 0, "mcq_answered": 0, "mcq_correct": 0, "descriptive_shown": 0,
                "seconds": 0.0, "last_active_at": None, "chat_ids": set(), "display_name": None}

    def _bump_last_active(rec, *timestamps):
        candidates = [t for t in ([rec["last_active_at"]] + list(timestamps)) if t]
        rec["last_active_at"] = max(candidates) if candidates else None

    mcq_params = list(bot_ids)
    mcq_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, mcq_params) \
        + _scope_where(course, level, mcq_params)
    mcq_rows = conn.execute(
        f"""SELECT telegram_user_id, shown_at, answered_at, is_correct
            FROM exam_hub_mcq_attempts WHERE {' AND '.join(mcq_where)}""",
        mcq_params,
    ).fetchall()

    desc_params = list(bot_ids)
    desc_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, desc_params) \
        + _scope_where(course, level, desc_params)
    desc_rows = conn.execute(
        f"""SELECT telegram_user_id, shown_at, answer_shown_at
            FROM exam_hub_descriptive_events WHERE {' AND '.join(desc_where)}""",
        desc_params,
    ).fetchall()

    by_student = {}
    for uid, shown_at, answered_at, is_correct in mcq_rows:
        ident = _identity_for(uid_map, uid)
        s = by_student.setdefault(ident["username"], _blank())
        s["display_name"] = ident["display_name"]
        s["chat_ids"].add(uid)
        s["mcq_shown"] += 1
        _bump_last_active(s, shown_at, answered_at)
        if answered_at is not None:
            s["mcq_answered"] += 1
            s["seconds"] += _seconds_capped(shown_at, answered_at)
        if is_correct == 1:
            s["mcq_correct"] += 1

    for uid, shown_at, answer_shown_at in desc_rows:
        ident = _identity_for(uid_map, uid)
        s = by_student.setdefault(ident["username"], _blank())
        s["display_name"] = ident["display_name"]
        s["chat_ids"].add(uid)
        s["descriptive_shown"] += 1
        _bump_last_active(s, shown_at, answer_shown_at)
        s["seconds"] += _seconds_capped(shown_at, answer_shown_at)

    out = []
    for username, s in by_student.items():
        out.append({
            "username": username, "display_name": s["display_name"] or username,
            "chat_ids": sorted(s["chat_ids"]),
            "mcq_shown": s["mcq_shown"], "mcq_answered": s["mcq_answered"], "mcq_correct": s["mcq_correct"],
            "accuracy_pct": round(100 * s["mcq_correct"] / s["mcq_answered"], 1) if s["mcq_answered"] else None,
            "descriptive_shown": s["descriptive_shown"],
            "time_spent_minutes": round(s["seconds"] / 60, 1),
            "last_active_at": s["last_active_at"],
        })
    out.sort(key=lambda r: (r["mcq_shown"] + r["descriptive_shown"]), reverse=True)
    return out


# ---------------------------------------------------------------------------
# Section 4 -- last 7 real UTC calendar days, student-wise (a fixed window,
# independent of the report's own chosen date range -- see module
# docstring), within ONE (course, level)
# ---------------------------------------------------------------------------
def last_7_days_range() -> tuple:
    today = datetime.now(timezone.utc).date()
    return (today - timedelta(days=6)).isoformat(), today.isoformat()


def student_last7days(conn, bot_ids: list, course: str = None, level: str = None, uid_map: dict = None) -> list:
    if not bot_ids:
        return []
    uid_map = uid_map if uid_map is not None else _uid_identity_map(conn)
    start, end = last_7_days_range()
    placeholders = ",".join("?" * len(bot_ids))

    mcq_params = list(bot_ids) + [start, end]
    mcq_scope = _scope_where(course, level, mcq_params)
    mcq_rows = conn.execute(
        f"""SELECT telegram_user_id, date(shown_at) AS d, shown_at, answered_at, is_correct
            FROM exam_hub_mcq_attempts
            WHERE bot_id IN ({placeholders}) AND date(shown_at) BETWEEN ? AND ?
            {' AND ' + ' AND '.join(mcq_scope) if mcq_scope else ''}""",
        mcq_params,
    ).fetchall()
    desc_params = list(bot_ids) + [start, end]
    desc_scope = _scope_where(course, level, desc_params)
    desc_rows = conn.execute(
        f"""SELECT telegram_user_id, date(shown_at) AS d, shown_at, answer_shown_at
            FROM exam_hub_descriptive_events
            WHERE bot_id IN ({placeholders}) AND date(shown_at) BETWEEN ? AND ?
            {' AND ' + ' AND '.join(desc_scope) if desc_scope else ''}""",
        desc_params,
    ).fetchall()

    def _blank(username, d):
        return {"username": username, "date": d, "mcq_shown": 0, "mcq_answered": 0,
                "mcq_correct": 0, "descriptive_shown": 0, "seconds": 0.0, "display_name": None, "chat_ids": set()}

    by_key = {}
    for uid, d, shown_at, answered_at, is_correct in mcq_rows:
        ident = _identity_for(uid_map, uid)
        r = by_key.setdefault((ident["username"], d), _blank(ident["username"], d))
        r["display_name"] = ident["display_name"]
        r["chat_ids"].add(uid)
        r["mcq_shown"] += 1
        if answered_at is not None:
            r["mcq_answered"] += 1
            r["seconds"] += _seconds_capped(shown_at, answered_at)
        if is_correct == 1:
            r["mcq_correct"] += 1
    for uid, d, shown_at, answer_shown_at in desc_rows:
        ident = _identity_for(uid_map, uid)
        r = by_key.setdefault((ident["username"], d), _blank(ident["username"], d))
        r["display_name"] = ident["display_name"]
        r["chat_ids"].add(uid)
        r["descriptive_shown"] += 1
        r["seconds"] += _seconds_capped(shown_at, answer_shown_at)

    out = []
    for r in by_key.values():
        out.append({
            "username": r["username"], "display_name": r["display_name"] or r["username"],
            "chat_ids": sorted(r["chat_ids"]),
            "date": r["date"], "mcq_shown": r["mcq_shown"], "mcq_answered": r["mcq_answered"], "mcq_correct": r["mcq_correct"],
            "accuracy_pct": round(100 * r["mcq_correct"] / r["mcq_answered"], 1) if r["mcq_answered"] else None,
            "descriptive_shown": r["descriptive_shown"], "time_spent_minutes": round(r["seconds"] / 60, 1),
        })
    out.sort(key=lambda r: (r["display_name"], r["date"]))
    return out


# ---------------------------------------------------------------------------
# Section 5 -- student x chapter matrix ("which student is doing which
# chapters the most"), ranked within each student's own activity, by
# username (every linked phone merged), within ONE (course, level)
# ---------------------------------------------------------------------------
def student_chapter_matrix(conn, bot_ids: list, start_date: str = None, end_date: str = None,
                            course: str = None, level: str = None, uid_map: dict = None) -> list:
    if not bot_ids:
        return []
    uid_map = uid_map if uid_map is not None else _uid_identity_map(conn)
    placeholders = ",".join("?" * len(bot_ids))

    mcq_params = list(bot_ids)
    mcq_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, mcq_params) \
        + _scope_where(course, level, mcq_params)
    mcq_rows = conn.execute(
        f"""SELECT telegram_user_id, chapter_slug, chapter_label, is_correct
            FROM exam_hub_mcq_attempts WHERE {' AND '.join(mcq_where)}""",
        mcq_params,
    ).fetchall()

    desc_params = list(bot_ids)
    desc_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, desc_params) \
        + _scope_where(course, level, desc_params)
    desc_rows = conn.execute(
        f"""SELECT telegram_user_id, chapter_slug, chapter_label
            FROM exam_hub_descriptive_events WHERE {' AND '.join(desc_where)}""",
        desc_params,
    ).fetchall()

    def _blank(username, chapter_slug, chapter_label):
        return {"username": username, "chapter_slug": chapter_slug, "chapter_label": chapter_label or chapter_slug,
                "mcq_attempted": 0, "mcq_correct": 0, "descriptive_shown": 0, "display_name": None, "chat_ids": set()}

    by_student_chapter = {}
    for uid, chapter_slug, chapter_label, is_correct in mcq_rows:
        ident = _identity_for(uid_map, uid)
        key = (ident["username"], chapter_slug or "unknown")
        c = by_student_chapter.setdefault(key, _blank(ident["username"], key[1], chapter_label))
        c["display_name"] = ident["display_name"]
        c["chat_ids"].add(uid)
        c["mcq_attempted"] += 1
        if is_correct == 1:
            c["mcq_correct"] += 1
    for uid, chapter_slug, chapter_label in desc_rows:
        ident = _identity_for(uid_map, uid)
        key = (ident["username"], chapter_slug or "unknown")
        c = by_student_chapter.setdefault(key, _blank(ident["username"], key[1], chapter_label))
        c["display_name"] = ident["display_name"]
        c["chat_ids"].add(uid)
        c["descriptive_shown"] += 1

    per_student = defaultdict(list)
    for c in by_student_chapter.values():
        c["accuracy_pct"] = round(100 * c["mcq_correct"] / c["mcq_attempted"], 1) if c["mcq_attempted"] else None
        c["display_name"] = c["display_name"] or c["username"]
        c["chat_ids"] = sorted(c["chat_ids"])
        per_student[c["username"]].append(c)

    out = []
    for chapters in per_student.values():
        chapters.sort(key=lambda c: c["mcq_attempted"] + c["descriptive_shown"], reverse=True)
        for rank, c in enumerate(chapters, start=1):
            c["rank_for_student"] = rank
            out.append(c)
    out.sort(key=lambda c: (c["display_name"], c["rank_for_student"]))
    return out


# ---------------------------------------------------------------------------
# Section 6 -- question-wise difficulty: which MCQs are most often wrong,
# and what students chose instead of the right answer, within ONE
# (course, level)
# ---------------------------------------------------------------------------
def question_difficulty(conn, bot_ids: list, start_date: str = None, end_date: str = None,
                         course: str = None, level: str = None,
                         min_attempts: int = MIN_ATTEMPTS_FOR_DIFFICULTY, limit: int = None) -> list:
    if not bot_ids:
        return []
    placeholders = ",".join("?" * len(bot_ids))
    params = list(bot_ids)
    where = [f"bot_id IN ({placeholders})", "answered_at IS NOT NULL"] + _date_where("shown_at", start_date, end_date, params) \
        + _scope_where(course, level, params)
    rows = conn.execute(
        f"""SELECT mcq_id, human_id, chapter_label, course, level, correct_option, selected_option, is_correct
            FROM exam_hub_mcq_attempts WHERE {' AND '.join(where)}""",
        params,
    ).fetchall()

    by_q = {}
    for mcq_id, human_id, chapter_label, course_, level_, correct_option, selected_option, is_correct in rows:
        q = by_q.setdefault(mcq_id, {
            "mcq_id": mcq_id, "human_id": human_id, "chapter_label": chapter_label, "course": course_, "level": level_,
            "correct_option": correct_option, "times_answered": 0, "times_wrong": 0, "wrong_option_counts": defaultdict(int),
        })
        if human_id and not q["human_id"]:
            q["human_id"] = human_id
        q["times_answered"] += 1
        if is_correct != 1:
            q["times_wrong"] += 1
            if selected_option:
                q["wrong_option_counts"][selected_option] += 1

    out = []
    for q in by_q.values():
        if q["times_answered"] < min_attempts:
            continue
        top_wrong_option, top_wrong_count = max(q["wrong_option_counts"].items(), key=lambda kv: kv[1], default=(None, 0))
        out.append({
            "mcq_id": q["mcq_id"], "human_id": q["human_id"] or q["mcq_id"], "chapter_label": q["chapter_label"],
            "course": q["course"], "level": q["level"], "correct_option": q["correct_option"],
            "times_answered": q["times_answered"], "times_wrong": q["times_wrong"],
            "wrong_pct": round(100 * q["times_wrong"] / q["times_answered"], 1),
            "most_common_wrong_option": top_wrong_option, "most_common_wrong_option_count": top_wrong_count,
        })
    out.sort(key=lambda r: (r["times_wrong"], r["wrong_pct"]), reverse=True)
    return out[:limit] if limit else out


# ---------------------------------------------------------------------------
# One level-block: all 6 sections, scoped to ONE (course, level) pair,
# plus a scorecard summary (unique students / MCQs shown / avg accuracy /
# time spent) computed from Section 3's own totals -- never a separate
# count, so the scorecard can never disagree with the table beneath it.
# ---------------------------------------------------------------------------
def build_level_report(conn, tenant: dict, course: str, level: str, exam_bot_ids: list,
                        start_date: str, end_date: str, uid_map: dict) -> dict:
    subjects = sorted({e["subject"] for e in _content_scope_entries(conn, tenant)
                        if e["course"] == course and e["level"] == level})
    content = [r for r in content_availability(conn, tenant) if r["course"] == course and r["level"] == level]
    students = student_performance(conn, exam_bot_ids, start_date, end_date, course=course, level=level, uid_map=uid_map)

    total_mcq_shown = sum(r["mcq_shown"] for r in students)
    total_mcq_answered = sum(r["mcq_answered"] for r in students)
    total_mcq_correct = sum(r["mcq_correct"] for r in students)
    total_time = round(sum(r["time_spent_minutes"] for r in students), 1)
    avg_accuracy = round(100 * total_mcq_correct / total_mcq_answered, 1) if total_mcq_answered else None

    return {
        "course": course, "level": level, "subjects": subjects,
        "content_availability": content,
        "chapter_stats": chapter_stats(conn, exam_bot_ids, start_date, end_date, course=course, level=level, uid_map=uid_map),
        "student_performance": students,
        "last_7_days_rows": student_last7days(conn, exam_bot_ids, course=course, level=level, uid_map=uid_map),
        "student_chapter_matrix": student_chapter_matrix(conn, exam_bot_ids, start_date, end_date, course=course, level=level, uid_map=uid_map),
        "question_difficulty": question_difficulty(conn, exam_bot_ids, start_date, end_date, course=course, level=level),
        "scorecard": {
            "unique_students": len(students),
            "total_mcq_shown": total_mcq_shown,
            "total_mcq_answered": total_mcq_answered,
            "avg_accuracy_pct": avg_accuracy,
            "total_time_minutes": total_time,
        },
    }


# ---------------------------------------------------------------------------
# Combined report -- one level-block per (course, level) this tenant serves
# ---------------------------------------------------------------------------
def build_report(conn, tenant_id: str, bots: list, start_date: str = None, end_date: str = None) -> dict:
    tenants = _load_tenants()
    tenant = tenants.get(tenant_id)
    if not tenant:
        raise ValueError(f"Unknown tenant_id {tenant_id!r}")

    exam_bot_ids = _exam_bot_ids_for_tenant(tenant_id, bots)
    all_bot_ids = _all_bot_ids_for_tenant(tenant_id, bots)
    l7_start, l7_end = last_7_days_range()
    range_label = f"{start_date or '…'} to {end_date or '…'}" if (start_date or end_date) else "All-time"
    master = faculty_master.get_faculty_master(conn, tenant_id)
    uid_map = _uid_identity_map(conn)

    level_pairs = _content_scope_levels(conn, tenant)
    levels = [
        build_level_report(conn, tenant, course, level, exam_bot_ids, start_date, end_date, uid_map)
        for course, level in level_pairs
    ]

    return {
        "tenant_id": tenant_id,
        "display_name": tenant.get("display_name", tenant_id),
        "kind": tenant.get("kind"),
        "contact_email": master["contact_email"] if master else None,
        "bot_ids": all_bot_ids,
        "exam_bot_ids": exam_bot_ids,
        "range_label": range_label,
        "start_date": start_date,
        "end_date": end_date,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "last_7_days": {"start": l7_start, "end": l7_end},
        "levels": levels,
    }


# ---------------------------------------------------------------------------
# Rendering -- one branded, colorful HTML source, reused for the "download
# as HTML" button (served as-is) and "download as PDF" (the same HTML
# through xhtml2pdf) -- same discipline exporters.py's
# render_printable_table() already follows, applied to a multi-level,
# multi-section document. Colorful by design (2026-08-17, Pranav: "Make
# sure pdf is colorful and easy to understand") -- navy/gold brand banners
# per level, a 4-tile scorecard per level, colored accuracy/wrong-%
# badges (green/amber/red by threshold), alternating row bands. All of it
# is plain inline CSS (xhtml2pdf has weak support for CSS custom
# properties / :nth-child / flexbox -- see CLAUDE.md section 7 and this
# module's own history) -- no gradients, no external assets beyond the
# already-embedded brand_kit logo.
# ---------------------------------------------------------------------------
def _fmt(v):
    return "—" if v is None else v


def _pct_badge(pct, good_high: bool = True):
    """A colored chip for a percentage value. good_high=True means a
    HIGHER number is good (accuracy); False means a HIGHER number is bad
    (wrong %) -- same three-color thresholds either way, just which end
    is green vs red flips."""
    if pct is None:
        return '<span style="color:#999;">—</span>'
    score = pct if good_high else (100 - pct)
    color = "#1e8449" if score >= 70 else ("#b7791f" if score >= 40 else "#c0392b")
    return (f'<span style="display:inline-block; padding:2px 9px; border-radius:10px; '
            f'background:{color}; color:#ffffff; font-weight:bold; font-size:10.5px;">{pct}%</span>')


def _chat_ids_cell(ids):
    if not ids:
        return "—"
    return ", ".join(str(i) for i in ids)


def _render_table(headers: list, rows: list, colors: dict, cell_renderers: dict = None) -> str:
    cell_renderers = cell_renderers or {}
    navy = colors["navy"]
    head = "".join(
        f'<th style="text-align:left; padding:7px 8px; font-size:10px; text-transform:uppercase; '
        f'color:#ffffff;">{h}</th>'
        for h in headers
    )
    if not rows:
        body = (f'<tr><td colspan="{len(headers)}" style="padding:12px; color:#888; text-align:center; font-size:11px;">'
                 f'No data for this period.</td></tr>')
    else:
        body_parts = []
        for i, row in enumerate(rows):
            bg = "#f4f6fb" if i % 2 else "#ffffff"
            cells = "".join(
                f'<td style="padding:5px 8px; border-bottom:1px solid #e6e6e6; font-size:11px;">'
                f'{cell_renderers[j](v) if j in cell_renderers else _fmt(v)}</td>'
                for j, v in enumerate(row)
            )
            body_parts.append(f'<tr style="background-color:{bg};">{cells}</tr>')
        body = "".join(body_parts)
    return (f'<table style="width:100%; border-collapse:collapse; margin-bottom:22px;">'
            f'<thead><tr style="background-color:{navy};">{head}</tr></thead><tbody>{body}</tbody></table>')


def _level_banner_html(level_block: dict, colors: dict) -> str:
    navy, gold = colors["navy"], colors["gold"]
    subj = ", ".join(level_block["subjects"]) or "—"
    sc = level_block["scorecard"]
    tiles = [
        ("Unique Students", sc["unique_students"]),
        ("MCQs Shown", sc["total_mcq_shown"]),
        ("Avg Accuracy", f'{sc["avg_accuracy_pct"]}%' if sc["avg_accuracy_pct"] is not None else "—"),
        ("Time Spent", f'{sc["total_time_minutes"]} min'),
    ]
    tile_bgs = ["#eaf1fb", "#fdf3e2", "#eaf1fb", "#fdf3e2"]
    tiles_html = "".join(
        f'<td style="text-align:center; padding:12px 6px; background-color:{tile_bgs[i]}; border-radius:6px;">'
        f'<div style="font-size:19px; font-weight:bold; color:{navy};">{v}</div>'
        f'<div style="font-size:9px; color:#777; text-transform:uppercase;">{label}</div></td>'
        for i, (label, v) in enumerate(tiles)
    )
    return f"""
<table style="width:100%; border-collapse:collapse; margin:28px 0 6px;"><tr>
  <td style="background-color:{navy}; padding:11px 16px; border-radius:6px;">
    <span style="color:#ffffff; font-size:15px; font-weight:bold;">LEVEL: {level_block['course']} — {level_block['level']}</span>
    <span style="color:{gold}; font-size:11px; margin-left:12px;">{subj}</span>
  </td>
</tr></table>
<table style="width:100%; border-collapse:separate; border-spacing:6px 0; margin-bottom:16px;"><tr>{tiles_html}</tr></table>
""".strip()


def _level_sections(level_block: dict, l7_start: str = "", l7_end: str = "") -> list:
    l7_rows = level_block["last_7_days_rows"]
    return [
        ("1. Content Availability", ["Subject", "Chapters w/ Content", "Chapters Total", "MCQ Count", "Descriptive Count", "Total Questions"],
         [[r["subject"], r["chapters_with_content"], r["chapters_total"], r["mcq_count"], r["descriptive_count"], r["total_count"]]
          for r in level_block["content_availability"]], {}),
        ("2. Chapter-wise Practice", ["Chapter", "Unique Students", "MCQ Shown", "MCQ Answered", "MCQ Correct",
                                       "Accuracy", "Time Spent (min)", "Descriptive Viewed"],
         [[r["chapter_label"], r["unique_students"], r["mcq_shown"], r["mcq_answered"], r["mcq_correct"],
           r["mcq_accuracy_pct"], r["time_spent_minutes"], r["descriptive_shown"]] for r in level_block["chapter_stats"]],
         {5: _pct_badge}),
        ("3. Student Performance", ["1LAVYA Username", "Student", "Chat ID(s)", "MCQ Shown", "MCQ Answered", "MCQ Correct",
                                      "Accuracy", "Descriptive Viewed", "Time Spent (min)", "Last Active"],
         [[r["username"], r["display_name"], _chat_ids_cell(r["chat_ids"]), r["mcq_shown"], r["mcq_answered"], r["mcq_correct"],
           r["accuracy_pct"], r["descriptive_shown"], r["time_spent_minutes"],
           (r["last_active_at"] or "—")[:19].replace("T", " ")] for r in level_block["student_performance"]],
         {6: _pct_badge}),
        (f"4. Last 7 Days Activity, Student-wise ({l7_start} to {l7_end})",
         ["Date", "1LAVYA Username", "Student", "MCQ Shown", "MCQ Answered", "MCQ Correct", "Accuracy", "Descriptive Viewed", "Time Spent (min)"],
         [[r["date"], r["username"], r["display_name"], r["mcq_shown"], r["mcq_answered"], r["mcq_correct"],
           r["accuracy_pct"], r["descriptive_shown"], r["time_spent_minutes"]] for r in l7_rows],
         {6: _pct_badge}),
        ("5. Student × Chapter Matrix", ["Student", "1LAVYA Username", "Rank (within student's own activity)", "Chapter",
                                           "MCQ Attempted", "MCQ Correct", "Accuracy", "Descriptive Viewed"],
         [[r["display_name"], r["username"], r["rank_for_student"], r["chapter_label"],
           r["mcq_attempted"], r["mcq_correct"], r["accuracy_pct"], r["descriptive_shown"]]
          for r in level_block["student_chapter_matrix"]], {6: _pct_badge}),
        ("6. Question-wise Difficulty (min. 2 real attempts)",
         ["Question ID", "Chapter", "Times Answered", "Times Wrong", "Wrong %", "Correct Option",
          "Most Common Wrong Option", "Chose It (count)"],
         [[r["human_id"], r["chapter_label"], r["times_answered"], r["times_wrong"], r["wrong_pct"],
           r["correct_option"], r["most_common_wrong_option"], r["most_common_wrong_option_count"]]
          for r in level_block["question_difficulty"]],
         {4: lambda v: _pct_badge(v, good_high=False)}),
    ]


def render_full_report_html(data: dict) -> str:
    c = brand_kit.colors()
    l7_start, l7_end = data["last_7_days"]["start"], data["last_7_days"]["end"]
    body_html = ""
    for level_block in data["levels"]:
        body_html += _level_banner_html(level_block, c)
        for title, headers, rows, cell_renderers in _level_sections(level_block, l7_start, l7_end):
            body_html += f'<h3 style="color:{c["navy"]}; font-size:12.5px; margin:16px 0 6px; font-family:Arial,Helvetica,sans-serif;">{title}</h3>'
            body_html += _render_table(headers, rows, c, cell_renderers)
    if not data["levels"]:
        body_html = '<p style="color:#888;">This tenant has no content_scope entries -- nothing to report.</p>'

    subtitle = f"{data['display_name']} &middot; {data['range_label']}"
    return f"""<html><head><meta charset="utf-8"><title>Faculty Report -- {data['display_name']}</title></head>
<body style="font-family:Arial,Helvetica,sans-serif; color:{c['ink']}; margin:24px;">
{brand_kit.render_header_html("Comprehensive Faculty Report", subtitle)}
<p style="font-size:10.5px; color:#888;">Bots covered: {', '.join(data['bot_ids']) or '—'} &middot; Report generated {data['generated_at'][:19].replace('T', ' ')} UTC &middot; Last-7-Days window: {data['last_7_days']['start']} to {data['last_7_days']['end']}</p>
<p style="font-size:10px; color:#999;">All figures below are raw, deterministic counts read directly from platform activity logs -- no estimation, scoring, or commentary. Students are identified by their permanent 1LAVYA username; activity from every phone/chat linked to that username is merged into one row.</p>
{body_html}
{brand_kit.render_footer_html()}
</body></html>"""


def build_report_pdf(data: dict) -> bytes:
    html = render_full_report_html(data)
    buf = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buf)
    if result.err:
        raise RuntimeError(f"Faculty report PDF generation failed with {result.err} error(s) for tenant_id={data['tenant_id']}.")
    return buf.getvalue()


def build_report_xlsx(data: dict) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    l7_start, l7_end = data["last_7_days"]["start"], data["last_7_days"]["end"]
    for level_block in data["levels"]:
        level_prefix = f"{level_block['course']}-{level_block['level']}"[:8]
        for title, headers, rows, _ in _level_sections(level_block, l7_start, l7_end):
            # Excel sheet names cap at 31 chars and can't start with a number
            # in some strict readers -- strip the leading "N. " section
            # number, prefix with a short level code so sheets across
            # multiple levels don't collide, then truncate.
            section_name = title.split(" (")[0].split(". ", 1)[-1]
            sheet_name = f"{level_prefix}-{section_name}"[:31]
            ws = wb.create_sheet(title=sheet_name)
            ws.append(headers)
            for row in rows:
                ws.append(["" if v is None else v for v in row])
    if not wb.sheetnames:
        wb.create_sheet(title="No Content Scope")
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Email delivery -- same Cloudflare Email Service backend as the student
# report pipeline (telegram/database/report_delivery.py / cf_email.py),
# sent from the Admin Portal's own dedicated address (1lavya-admin-portal's
# from_email in bots.json) since this is an admin-triggered send, not a
# bot-triggered one -- same "honest label" precedent
# analytics_students_send_report() already established.
# ---------------------------------------------------------------------------
def resolve_admin_portal_from_address() -> tuple:
    try:
        data = json.loads(BOTS_PATH.read_text(encoding="utf-8"))
        for b in data.get("bots", []):
            if b.get("bot_id") == "1lavya-admin-portal":
                return b.get("from_email") or "reports@1lavya.com", b.get("display_name") or "1LAVYA"
    except Exception:
        pass
    return "reports@1lavya.com", "1LAVYA"


def build_report_email_html(data: dict) -> str:
    c = brand_kit.colors()
    level_list = ", ".join(f"{lv['course']} {lv['level']}" for lv in data["levels"]) or "—"
    return f"""
<div style="font-family:Arial,Helvetica,sans-serif; max-width:600px; margin:0 auto; padding:24px; color:{c['ink']};">
  <div style="font-size:20px; font-weight:bold; color:{c['navy']}; font-family:Georgia,'Times New Roman',serif;">{brand_kit.BRAND_NAME}</div>
  <div style="font-size:10px; color:{c['gold']}; text-transform:uppercase; margin-bottom:20px;">{brand_kit.TAGLINE}</div>
  <p style="font-size:14px; line-height:1.6;">Hi {data['display_name']},</p>
  <p style="font-size:14px; line-height:1.6;">
    Attached is your comprehensive bot performance report for <b>{data['range_label']}</b> — broken out
    separately for every level live for you ({level_list}): content availability, chapter-wise practice,
    student-wise performance, the last 7 days' student-wise activity, a student &times; chapter breakdown,
    and a question-wise difficulty analysis (which MCQs students get wrong most often, and what they chose
    instead of the right answer).
  </p>
  {brand_kit.render_email_footer_html("1LAVYA Admin Portal")}
</div>
""".strip()


def send_report_email(to_email: str, data: dict, pdf_bytes: bytes) -> None:
    """Raises on failure -- the caller (app.py's route) is responsible for
    catching, logging to faculty_report_deliveries, and flashing the
    failure rather than silently pretending it sent."""
    from_email, from_name = resolve_admin_portal_from_address()
    html_body = build_report_email_html(data)
    cf_email.send_email(
        from_email=from_email,
        from_name=from_name,
        to_email=to_email,
        subject=f"{brand_kit.BRAND_NAME} Faculty Report -- {data['display_name']} ({data['range_label']})",
        html_body=html_body,
        attachments=[{
            "filename": f"1LAVYA_Faculty_Report_{data['tenant_id']}.pdf",
            "content_bytes": pdf_bytes,
            "content_type": "application/pdf",
        }],
    )


def log_report_delivery(conn, tenant_id: str, range_label: str, delivered_to: str, status: str, error_detail: str = None) -> None:
    import db as platform_db
    platform_db.execute_with_retry(
        conn,
        """INSERT INTO faculty_report_deliveries
           (tenant_id, generated_at, range_label, delivered_to, status, error_detail)
           VALUES (?,?,?,?,?,?)""",
        (tenant_id, platform_db.now(), range_label, delivered_to, status, error_detail),
    )
