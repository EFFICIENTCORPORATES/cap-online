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
--------------------------------------------------------------------------------
Six sections, every one a plain deterministic table (no narrative text,
no scoring/opinion) built straight from platform activity logs:

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
  2. chapter_stats()          -- per chapter, across every subject/course
                                  this faculty's bot(s) serve: unique
                                  students, MCQ shown/answered/correct/
                                  accuracy, time spent, descriptive views.
                                  Sorted most-practiced first.
  3. student_performance()    -- per student (chat ID): the same metrics,
                                  platform-activity-log derived, sorted
                                  most-active first.
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
of bot_ids to scope to) and returns plain JSON-serializable Python -- same
convention telegram/database/analytics.py already follows. build_report()
is the one function callers actually need; it assembles all six sections
plus tenant/range metadata into one dict, which render_full_report_html()/
build_report_pdf()/build_report_xlsx() then turn into the three downloadable
formats, and send_report_email() emails the PDF version to the faculty.

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


def _seconds_capped(shown_at, ended_at):
    if not (shown_at and ended_at):
        return 0.0
    secs = student_analytics._seconds_between(shown_at, ended_at)
    return min(secs, TIME_CAP_SECONDS) if secs and secs >= 0 else 0.0


def _student_display_names(conn) -> dict:
    rows = conn.execute("SELECT telegram_user_id, first_name, last_name, username FROM students").fetchall()
    out = {}
    for uid, first, last, username in rows:
        name = " ".join(p for p in (first, last) if p).strip()
        out[uid] = name or username or f"Student {uid}"
    return out


# ---------------------------------------------------------------------------
# Section 2 -- chapter-wise practice, across every subject/course this
# faculty's bots serve
# ---------------------------------------------------------------------------
def chapter_stats(conn, bot_ids: list, start_date: str = None, end_date: str = None) -> list:
    if not bot_ids:
        return []
    placeholders = ",".join("?" * len(bot_ids))

    mcq_params = list(bot_ids)
    mcq_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, mcq_params)
    mcq_rows = conn.execute(
        f"""SELECT chapter_slug, chapter_label, course, level, telegram_user_id, shown_at, answered_at, is_correct
            FROM exam_hub_mcq_attempts WHERE {' AND '.join(mcq_where)}""",
        mcq_params,
    ).fetchall()

    desc_params = list(bot_ids)
    desc_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, desc_params)
    desc_rows = conn.execute(
        f"""SELECT chapter_slug, chapter_label, course, level, telegram_user_id, shown_at, answer_shown_at
            FROM exam_hub_descriptive_events WHERE {' AND '.join(desc_where)}""",
        desc_params,
    ).fetchall()

    def _blank(chapter_slug, chapter_label, course, level):
        return {
            "chapter_slug": chapter_slug, "chapter_label": chapter_label or chapter_slug, "course": course, "level": level,
            "mcq_shown": 0, "mcq_answered": 0, "mcq_correct": 0, "mcq_seconds": 0.0,
            "descriptive_shown": 0, "descriptive_seconds": 0.0, "students": set(),
        }

    by_chapter = {}
    for chapter_slug, chapter_label, course, level, uid, shown_at, answered_at, is_correct in mcq_rows:
        key = chapter_slug or "unknown"
        c = by_chapter.setdefault(key, _blank(key, chapter_label, course, level))
        c["mcq_shown"] += 1
        c["students"].add(uid)
        if answered_at is not None:
            c["mcq_answered"] += 1
            c["mcq_seconds"] += _seconds_capped(shown_at, answered_at)
        if is_correct == 1:
            c["mcq_correct"] += 1

    for chapter_slug, chapter_label, course, level, uid, shown_at, answer_shown_at in desc_rows:
        key = chapter_slug or "unknown"
        c = by_chapter.setdefault(key, _blank(key, chapter_label, course, level))
        c["descriptive_shown"] += 1
        c["students"].add(uid)
        c["descriptive_seconds"] += _seconds_capped(shown_at, answer_shown_at)

    out = []
    for c in by_chapter.values():
        out.append({
            "chapter_slug": c["chapter_slug"], "chapter_label": c["chapter_label"],
            "course": c["course"], "level": c["level"], "unique_students": len(c["students"]),
            "mcq_shown": c["mcq_shown"], "mcq_answered": c["mcq_answered"], "mcq_correct": c["mcq_correct"],
            "mcq_accuracy_pct": round(100 * c["mcq_correct"] / c["mcq_answered"], 1) if c["mcq_answered"] else None,
            "time_spent_minutes": round((c["mcq_seconds"] + c["descriptive_seconds"]) / 60, 1),
            "descriptive_shown": c["descriptive_shown"],
        })
    out.sort(key=lambda r: (r["mcq_shown"] + r["descriptive_shown"]), reverse=True)
    return out


# ---------------------------------------------------------------------------
# Section 3 -- student-wise performance
# ---------------------------------------------------------------------------
def student_performance(conn, bot_ids: list, start_date: str = None, end_date: str = None) -> list:
    if not bot_ids:
        return []
    names = _student_display_names(conn)
    placeholders = ",".join("?" * len(bot_ids))

    def _blank():
        return {"mcq_shown": 0, "mcq_answered": 0, "mcq_correct": 0, "descriptive_shown": 0, "seconds": 0.0, "last_active_at": None}

    def _bump_last_active(rec, *timestamps):
        candidates = [t for t in ([rec["last_active_at"]] + list(timestamps)) if t]
        rec["last_active_at"] = max(candidates) if candidates else None

    mcq_params = list(bot_ids)
    mcq_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, mcq_params)
    mcq_rows = conn.execute(
        f"""SELECT telegram_user_id, shown_at, answered_at, is_correct
            FROM exam_hub_mcq_attempts WHERE {' AND '.join(mcq_where)}""",
        mcq_params,
    ).fetchall()

    desc_params = list(bot_ids)
    desc_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, desc_params)
    desc_rows = conn.execute(
        f"""SELECT telegram_user_id, shown_at, answer_shown_at
            FROM exam_hub_descriptive_events WHERE {' AND '.join(desc_where)}""",
        desc_params,
    ).fetchall()

    by_student = {}
    for uid, shown_at, answered_at, is_correct in mcq_rows:
        s = by_student.setdefault(uid, _blank())
        s["mcq_shown"] += 1
        _bump_last_active(s, shown_at, answered_at)
        if answered_at is not None:
            s["mcq_answered"] += 1
            s["seconds"] += _seconds_capped(shown_at, answered_at)
        if is_correct == 1:
            s["mcq_correct"] += 1

    for uid, shown_at, answer_shown_at in desc_rows:
        s = by_student.setdefault(uid, _blank())
        s["descriptive_shown"] += 1
        _bump_last_active(s, shown_at, answer_shown_at)
        s["seconds"] += _seconds_capped(shown_at, answer_shown_at)

    out = []
    for uid, s in by_student.items():
        out.append({
            "telegram_user_id": uid, "display_name": names.get(uid, f"Student {uid}"),
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
# independent of the report's own chosen date range -- see module docstring)
# ---------------------------------------------------------------------------
def last_7_days_range() -> tuple:
    today = datetime.now(timezone.utc).date()
    return (today - timedelta(days=6)).isoformat(), today.isoformat()


def student_last7days(conn, bot_ids: list) -> list:
    if not bot_ids:
        return []
    start, end = last_7_days_range()
    names = _student_display_names(conn)
    placeholders = ",".join("?" * len(bot_ids))

    mcq_rows = conn.execute(
        f"""SELECT telegram_user_id, date(shown_at) AS d, shown_at, answered_at, is_correct
            FROM exam_hub_mcq_attempts
            WHERE bot_id IN ({placeholders}) AND date(shown_at) BETWEEN ? AND ?""",
        list(bot_ids) + [start, end],
    ).fetchall()
    desc_rows = conn.execute(
        f"""SELECT telegram_user_id, date(shown_at) AS d, shown_at, answer_shown_at
            FROM exam_hub_descriptive_events
            WHERE bot_id IN ({placeholders}) AND date(shown_at) BETWEEN ? AND ?""",
        list(bot_ids) + [start, end],
    ).fetchall()

    def _blank(uid, d):
        return {"telegram_user_id": uid, "date": d, "mcq_shown": 0, "mcq_answered": 0,
                "mcq_correct": 0, "descriptive_shown": 0, "seconds": 0.0}

    by_key = {}
    for uid, d, shown_at, answered_at, is_correct in mcq_rows:
        r = by_key.setdefault((uid, d), _blank(uid, d))
        r["mcq_shown"] += 1
        if answered_at is not None:
            r["mcq_answered"] += 1
            r["seconds"] += _seconds_capped(shown_at, answered_at)
        if is_correct == 1:
            r["mcq_correct"] += 1
    for uid, d, shown_at, answer_shown_at in desc_rows:
        r = by_key.setdefault((uid, d), _blank(uid, d))
        r["descriptive_shown"] += 1
        r["seconds"] += _seconds_capped(shown_at, answer_shown_at)

    out = []
    for r in by_key.values():
        out.append({
            "telegram_user_id": r["telegram_user_id"],
            "display_name": names.get(r["telegram_user_id"], f"Student {r['telegram_user_id']}"),
            "date": r["date"], "mcq_shown": r["mcq_shown"], "mcq_answered": r["mcq_answered"], "mcq_correct": r["mcq_correct"],
            "accuracy_pct": round(100 * r["mcq_correct"] / r["mcq_answered"], 1) if r["mcq_answered"] else None,
            "descriptive_shown": r["descriptive_shown"], "time_spent_minutes": round(r["seconds"] / 60, 1),
        })
    out.sort(key=lambda r: (r["display_name"], r["date"]))
    return out


# ---------------------------------------------------------------------------
# Section 5 -- student x chapter matrix ("which student is doing which
# chapters the most"), ranked within each student's own activity
# ---------------------------------------------------------------------------
def student_chapter_matrix(conn, bot_ids: list, start_date: str = None, end_date: str = None) -> list:
    if not bot_ids:
        return []
    names = _student_display_names(conn)
    placeholders = ",".join("?" * len(bot_ids))

    mcq_params = list(bot_ids)
    mcq_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, mcq_params)
    mcq_rows = conn.execute(
        f"""SELECT telegram_user_id, chapter_slug, chapter_label, is_correct
            FROM exam_hub_mcq_attempts WHERE {' AND '.join(mcq_where)}""",
        mcq_params,
    ).fetchall()

    desc_params = list(bot_ids)
    desc_where = [f"bot_id IN ({placeholders})"] + _date_where("shown_at", start_date, end_date, desc_params)
    desc_rows = conn.execute(
        f"""SELECT telegram_user_id, chapter_slug, chapter_label
            FROM exam_hub_descriptive_events WHERE {' AND '.join(desc_where)}""",
        desc_params,
    ).fetchall()

    def _blank(uid, chapter_slug, chapter_label):
        return {"telegram_user_id": uid, "chapter_slug": chapter_slug, "chapter_label": chapter_label or chapter_slug,
                "mcq_attempted": 0, "mcq_correct": 0, "descriptive_shown": 0}

    by_student_chapter = {}
    for uid, chapter_slug, chapter_label, is_correct in mcq_rows:
        key = (uid, chapter_slug or "unknown")
        c = by_student_chapter.setdefault(key, _blank(uid, key[1], chapter_label))
        c["mcq_attempted"] += 1
        if is_correct == 1:
            c["mcq_correct"] += 1
    for uid, chapter_slug, chapter_label in desc_rows:
        key = (uid, chapter_slug or "unknown")
        c = by_student_chapter.setdefault(key, _blank(uid, key[1], chapter_label))
        c["descriptive_shown"] += 1

    per_student = defaultdict(list)
    for c in by_student_chapter.values():
        c["accuracy_pct"] = round(100 * c["mcq_correct"] / c["mcq_attempted"], 1) if c["mcq_attempted"] else None
        c["display_name"] = names.get(c["telegram_user_id"], f"Student {c['telegram_user_id']}")
        per_student[c["telegram_user_id"]].append(c)

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
# and what students chose instead of the right answer
# ---------------------------------------------------------------------------
def question_difficulty(conn, bot_ids: list, start_date: str = None, end_date: str = None,
                         min_attempts: int = MIN_ATTEMPTS_FOR_DIFFICULTY, limit: int = None) -> list:
    if not bot_ids:
        return []
    placeholders = ",".join("?" * len(bot_ids))
    params = list(bot_ids)
    where = [f"bot_id IN ({placeholders})", "answered_at IS NOT NULL"] + _date_where("shown_at", start_date, end_date, params)
    rows = conn.execute(
        f"""SELECT mcq_id, human_id, chapter_label, course, level, correct_option, selected_option, is_correct
            FROM exam_hub_mcq_attempts WHERE {' AND '.join(where)}""",
        params,
    ).fetchall()

    by_q = {}
    for mcq_id, human_id, chapter_label, course, level, correct_option, selected_option, is_correct in rows:
        q = by_q.setdefault(mcq_id, {
            "mcq_id": mcq_id, "human_id": human_id, "chapter_label": chapter_label, "course": course, "level": level,
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
# Combined report
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
        "content_availability": content_availability(conn, tenant),
        "chapter_stats": chapter_stats(conn, exam_bot_ids, start_date, end_date),
        "student_performance": student_performance(conn, exam_bot_ids, start_date, end_date),
        "last_7_days": {"start": l7_start, "end": l7_end, "rows": student_last7days(conn, exam_bot_ids)},
        "student_chapter_matrix": student_chapter_matrix(conn, exam_bot_ids, start_date, end_date),
        "question_difficulty": question_difficulty(conn, exam_bot_ids, start_date, end_date),
    }


# ---------------------------------------------------------------------------
# Rendering -- one branded HTML source, reused for the "download as HTML"
# button (served as-is) and "download as PDF" (the same HTML through
# xhtml2pdf) -- same discipline exporters.py's render_printable_table()
# already follows, applied to a multi-section document instead of one
# table.
# ---------------------------------------------------------------------------
def _fmt(v):
    return "—" if v is None else v


def _render_table(headers: list, rows: list, colors: dict) -> str:
    navy, ink = colors["navy"], colors["ink"]
    head = "".join(
        f'<th style="text-align:left; padding:6px 8px; border-bottom:2px solid {navy}; font-size:10px; '
        f'text-transform:uppercase; color:{ink};">{h}</th>'
        for h in headers
    )
    body = "".join(
        "<tr>" + "".join(
            f'<td style="padding:5px 8px; border-bottom:1px solid #e2e2e2; font-size:11px;">{_fmt(v)}</td>' for v in row
        ) + "</tr>"
        for row in rows
    )
    if not rows:
        body = (f'<tr><td colspan="{len(headers)}" style="padding:12px; color:#888; text-align:center; font-size:11px;">'
                 f'No data for this period.</td></tr>')
    return f'<table style="width:100%; border-collapse:collapse; margin-bottom:22px;"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def _report_sections(data: dict) -> list:
    l7 = data["last_7_days"]
    return [
        ("1. Content Availability -- Subjects & Levels Live",
         ["Course", "Level", "Subject", "Chapters w/ Content", "Chapters Total", "MCQ Count", "Descriptive Count", "Total Questions"],
         [[r["course"], r["level"], r["subject"], r["chapters_with_content"], r["chapters_total"],
           r["mcq_count"], r["descriptive_count"], r["total_count"]] for r in data["content_availability"]]),
        ("2. Chapter-wise Practice -- Most Accessed / Practiced Chapters",
         ["Chapter", "Course", "Level", "Unique Students", "MCQ Shown", "MCQ Answered", "MCQ Correct",
          "MCQ Accuracy %", "Time Spent (min)", "Descriptive Viewed"],
         [[r["chapter_label"], r["course"], r["level"], r["unique_students"], r["mcq_shown"], r["mcq_answered"],
           r["mcq_correct"], r["mcq_accuracy_pct"], r["time_spent_minutes"], r["descriptive_shown"]] for r in data["chapter_stats"]]),
        ("3. Student Performance -- All Students",
         ["Chat ID", "Student", "MCQ Shown", "MCQ Answered", "MCQ Correct", "Accuracy %",
          "Descriptive Viewed", "Time Spent (min)", "Last Active"],
         [[r["telegram_user_id"], r["display_name"], r["mcq_shown"], r["mcq_answered"], r["mcq_correct"],
           r["accuracy_pct"], r["descriptive_shown"], r["time_spent_minutes"],
           (r["last_active_at"] or "—")[:19].replace("T", " ")] for r in data["student_performance"]]),
        (f"4. Last 7 Days Activity, Student-wise ({l7['start']} to {l7['end']})",
         ["Date", "Chat ID", "Student", "MCQ Shown", "MCQ Answered", "MCQ Correct", "Accuracy %",
          "Descriptive Viewed", "Time Spent (min)"],
         [[r["date"], r["telegram_user_id"], r["display_name"], r["mcq_shown"], r["mcq_answered"], r["mcq_correct"],
           r["accuracy_pct"], r["descriptive_shown"], r["time_spent_minutes"]] for r in l7["rows"]]),
        ("5. Student x Chapter Matrix -- Which Chapters Each Student Practices Most",
         ["Student", "Chat ID", "Rank (within this student's own activity)", "Chapter", "MCQ Attempted",
          "MCQ Correct", "Accuracy %", "Descriptive Viewed"],
         [[r["display_name"], r["telegram_user_id"], r["rank_for_student"], r["chapter_label"],
           r["mcq_attempted"], r["mcq_correct"], r["accuracy_pct"], r["descriptive_shown"]] for r in data["student_chapter_matrix"]]),
        ("6. Question-wise Difficulty -- Most Wrongly Answered MCQs (min. 2 attempts)",
         ["Question ID", "Chapter", "Course", "Level", "Times Answered", "Times Wrong", "Wrong %",
          "Correct Option", "Most Common Wrong Option Chosen", "Chose It (count)"],
         [[r["human_id"], r["chapter_label"], r["course"], r["level"], r["times_answered"], r["times_wrong"],
           r["wrong_pct"], r["correct_option"], r["most_common_wrong_option"], r["most_common_wrong_option_count"]]
          for r in data["question_difficulty"]]),
    ]


def render_full_report_html(data: dict) -> str:
    c = brand_kit.colors()
    body_html = ""
    for title, headers, rows in _report_sections(data):
        body_html += f'<h2 style="color:{c["navy"]}; font-size:14px; margin:22px 0 8px; font-family:Arial,Helvetica,sans-serif;">{title}</h2>'
        body_html += _render_table(headers, rows, c)

    subtitle = f"{data['display_name']} &middot; {data['range_label']}"
    return f"""<html><head><meta charset="utf-8"><title>Faculty Report -- {data['display_name']}</title></head>
<body style="font-family:Arial,Helvetica,sans-serif; color:{c['ink']}; margin:24px;">
{brand_kit.render_header_html("Comprehensive Faculty Report", subtitle)}
<p style="font-size:10.5px; color:#888;">Bots covered: {', '.join(data['bot_ids']) or '—'} &middot; Report generated {data['generated_at'][:19].replace('T', ' ')} UTC</p>
<p style="font-size:10px; color:#999;">All figures below are raw, deterministic counts read directly from platform activity logs -- no estimation, scoring, or commentary.</p>
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
    for title, headers, rows in _report_sections(data):
        # Excel sheet names cap at 31 chars and can't start with a number
        # in some strict readers -- strip the leading "N. " section number
        # and truncate, keeping the sheet tab legible.
        sheet_name = title.split(" -- ")[0].split(". ", 1)[-1][:31]
        ws = wb.create_sheet(title=sheet_name)
        ws.append(headers)
        for row in rows:
            ws.append(["" if v is None else v for v in row])
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
    return f"""
<div style="font-family:Arial,Helvetica,sans-serif; max-width:600px; margin:0 auto; padding:24px; color:{c['ink']};">
  <div style="font-size:20px; font-weight:bold; color:{c['navy']}; font-family:Georgia,'Times New Roman',serif;">{brand_kit.BRAND_NAME}</div>
  <div style="font-size:10px; color:{c['gold']}; text-transform:uppercase; margin-bottom:20px;">{brand_kit.TAGLINE}</div>
  <p style="font-size:14px; line-height:1.6;">Hi {data['display_name']},</p>
  <p style="font-size:14px; line-height:1.6;">
    Attached is your comprehensive bot performance report for <b>{data['range_label']}</b> -- content availability
    across every subject/level live for you, chapter-wise practice, student-wise performance, the last 7 days'
    student-wise activity, a student &times; chapter breakdown, and a question-wise difficulty analysis (which
    MCQs students get wrong most often, and what they chose instead of the right answer).
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
