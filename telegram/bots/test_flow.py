"""
telegram/bots/test_flow.py -- Test Mode: Pre-Designed Tests (2026-08-16)
--------------------------------------------------------------------------------
See telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md for the full design.
Scope, confirmed with Pranav: **Pre-Designed Tests only** (real MTP/PYQ
sittings, reused as-is) -- no Student Customised Test in this build. Real
content exists ONLY for CA Inter Advanced Accounting today
(telegram/tools/generate_predesigned_tests.py) -- any other course/level/
subject a student asks for is met with an honest "not available yet" and a
menu of what to do instead, never a dead end or a silent empty list.

SAME MODULE SHAPE as profile_flow.py/report_flow.py/mcq_issue_flow.py: a
standalone flow with its own callback-data prefixes, state tracked partly in
context.user_data (for the picker, which is fine to lose on a restart -- a
student just re-triggers "test") and partly (everything that MUST survive a
restart) in the database directly -- see _get_active_test() below, which is
the ONLY source of truth for "does this student have a test in progress,"
never context.user_data.

HOST-MODULE INJECTION, deliberate: this module never `import`s
exam_hub_bot.py (avoids a circular import, since exam_hub_bot.py imports
this module) and never re-implements its HTML-rendering/PDF/message-
splitting helpers (a real maintenance-burden risk if duplicated) -- instead,
every entry point takes a `host` parameter, which the caller passes as its
own module object (`sys.modules[__name__]` from exam_hub_bot.py). `host` is
expected to expose: `.bank` (QuestionBank), `.mcq_bank` (McqBank),
`.html_to_telegram_text`, `.send_long_message`, `.html_to_pdf_bytes`,
`.TENANT_ID`. Same pattern mcq_issue_flow.py already established for its own
"deliberate non-dependency" on the host bot's question-lookup internals.

CALLBACK_DATA NAMESPACING: `testflow:<action>` for the picker/summary
(Course -> Level -> Subject -> sitting -> confirm), `tnav:<action>` for
in-test navigation (next/prev/palette/submit), `topt:<letter>` for
selecting an MCQ option, `tgo:<seq_no>` for a palette jump, `tupload:<seq_no>`
for picking which descriptive question an upload is for. All index-based
where the underlying value could be long (Telegram's 64-byte callback_data
limit -- the exact bug class this platform has hit and fixed 3+ times
already; test_id is NEVER embedded in callback_data, always resolved via
_get_active_test()).
"""

import os
import re
import sys
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402
import wallet  # noqa: E402
import identity  # noqa: E402
import academic_profiles  # noqa: E402 -- telegram/database/academic_profiles.py, multi-course profiles (2026-08-16)

logger = logging.getLogger(__name__)

TRIGGER_PHRASES = {"test", "take a test", "practice test", "mock test", "start test"}
UPLOAD_TRIGGER_PHRASES = {"upload"}
DONE_UPLOAD_PHRASES = {"done"}

UPLOADS_ROOT = REPO_ROOT / "telegram" / "assets" / "exam_bot" / "Tests" / "uploads"

# --- context.user_data keys (picker state only -- fine to lose on restart) ---
UD_PICKER_COURSES = "testflow_courses"
UD_PICKER_LEVELS = "testflow_levels"
UD_PICKER_SUBJECTS = "testflow_subjects"
UD_PICKER_SITTINGS = "testflow_sittings"  # list of catalog_keys
UD_PICKER_COURSE = "testflow_picked_course"
UD_PICKER_LEVEL = "testflow_picked_level"
UD_PICKER_CATALOG_KEY = "testflow_picked_catalog_key"
UD_AWAITING_UPLOAD_PICK = "testflow_awaiting_upload_pick"   # bool -- "upload" was typed, waiting for a seq_no choice
UD_UPLOAD_SEQ = "testflow_upload_seq"                        # int or None -- actively collecting pages for this seq_no
UD_UPLOAD_PAGE_COUNTER = "testflow_upload_page_counter"
UD_PICKER_TIER_MARKS = "testflow_picked_tier_marks"           # int -- the chosen size tier's target marks (2026-08-16)

# --- Size tiers (2026-08-16, Pranav's explicit ask: "we should not have the
# mandatory 100 marks test, instead we should have 3 options... 20/50/100
# marks") -- offered per real sitting, never a mandatory full-paper size.
# A tier at or above the sitting's own total collapses to "Full Paper" (no
# point offering a phantom 100-mark option on a 62-mark paper) -- see
# _tier_options() below. Split 30:70 MCQ:Descriptive when building a
# tier's actual question subset -- the SAME ratio Pranav already confirmed
# for the (still unbuilt) Custom Test's own marks-assembly, reused here
# rather than inventing a second, competing ratio decision.
SIZE_TIERS = [20, 50, 100]
TIER_MCQ_SHARE = 0.3


def matches_trigger(text: str) -> bool:
    return text.strip().lower() in TRIGGER_PHRASES


def is_awaiting_upload_pick(context) -> bool:
    return bool(context.user_data.get(UD_AWAITING_UPLOAD_PICK))


def is_collecting_upload(context) -> bool:
    return context.user_data.get(UD_UPLOAD_SEQ) is not None


# ---------------------------------------------------------------------------
# ACTIVITY LOG -- added 2026-08-16, Pranav's ask: capture every point of
# possible data during a test, timestamped, so at most 60 seconds of
# activity is ever unaccounted for even if the student's phone dies
# mid-test, and so understanding can later be analyzed at topic/subtopic
# granularity. See schema.sql's own test_activity_log comment for the full
# design reasoning (append-only event log underneath the current-state
# tables, same pattern wallet_ledger/report_flow_events already use).
# ---------------------------------------------------------------------------

def _log_activity(conn, test_id: str, seq_no, action_type: str, detail: str = None):
    platform_db.execute_with_retry(
        conn,
        "INSERT INTO test_activity_log (test_id, seq_no, action_type, detail, occurred_at) VALUES (?,?,?,?,?)",
        (test_id, seq_no, action_type, detail, platform_db.now()),
    )


HEARTBEAT_INTERVAL_SECONDS = 60  # Pranav's explicit ask: lose at most 60s of "what was the student doing" data


def _heartbeat_job_name(test_id: str) -> str:
    return f"test_heartbeat:{test_id}"


def _schedule_heartbeat_check(context, test_id: str, seq_no: int):
    """Self-terminating by design: each firing re-checks whether seq_no is
    STILL the question being shown (test_sessions.current_seq_no) before
    logging anything or rescheduling itself. The moment the student
    navigates away, the next stale firing (if any is still pending) simply
    finds a mismatch and stops -- no explicit cross-navigation cancellation
    needed, and a new call from wherever the question actually changes
    starts a fresh chain for the new seq_no."""
    if not context.job_queue:
        return
    context.job_queue.run_once(
        _heartbeat_job_callback, when=HEARTBEAT_INTERVAL_SECONDS,
        name=_heartbeat_job_name(test_id), data={"test_id": test_id, "seq_no": seq_no},
    )


async def _heartbeat_job_callback(context):
    test_id = context.job.data["test_id"]
    seq_no = context.job.data["seq_no"]
    conn = platform_db.get_connection()
    row = conn.execute("SELECT status, current_seq_no FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()
    if not row or row[0] != "in_progress" or row[1] != seq_no:
        return  # test ended, or the student has moved to a different question -- this chain stops here
    _log_activity(conn, test_id, seq_no, "no_activity_heartbeat")
    _schedule_heartbeat_check(context, test_id, seq_no)


def _mark_question_viewed(context, conn, test_id: str, seq_no: int):
    """Called from every code path that actually shows a question to the
    student (start, next/prev, palette jump) -- updates current_seq_no
    (both the exact-point-resume marker and what the heartbeat checks
    against), logs the view, and (re)starts the heartbeat chain for the
    new question."""
    platform_db.execute_with_retry(conn, "UPDATE test_sessions SET current_seq_no=? WHERE test_id=?", (seq_no, test_id))
    _log_activity(conn, test_id, seq_no, "question_viewed")
    _schedule_heartbeat_check(context, test_id, seq_no)


# ---------------------------------------------------------------------------
# DB-SOURCED TRUTH -- never context.user_data for anything that must survive
# a restart (roadmap's own explicit rule, §7).
# ---------------------------------------------------------------------------

def _get_active_test(conn, telegram_user_id: int):
    return conn.execute(
        "SELECT * FROM test_sessions WHERE telegram_user_id=? AND status='in_progress' ORDER BY started_at DESC LIMIT 1",
        (telegram_user_id,),
    ).fetchone()


def _row_to_dict(cursor_row, conn):
    """sqlite3 rows are tuples by default in this codebase's connections
    (db.py's get_connection() never sets row_factory) -- fetch column names
    explicitly rather than assuming a Row object."""
    if cursor_row is None:
        return None
    cols = [d[0] for d in conn.execute("SELECT * FROM test_sessions LIMIT 0").description]
    return dict(zip(cols, cursor_row))


# ---------------------------------------------------------------------------
# PICKER: Course -> Level -> Subject -> sitting -> summary/confirm
# ---------------------------------------------------------------------------

def _available_courses(conn):
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT course FROM predesigned_tests WHERE active=1 ORDER BY course"
    ).fetchall()]


def _available_levels(conn, course):
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT level FROM predesigned_tests WHERE active=1 AND course=? ORDER BY level", (course,)
    ).fetchall()]


def _available_subjects(conn, course, level):
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT subject FROM predesigned_tests WHERE active=1 AND course=? AND level=? ORDER BY subject",
        (course, level),
    ).fetchall()]


def _sittings_for(conn, course, level, subject):
    return conn.execute(
        "SELECT catalog_key, title, total_marks, duration_minutes, mcq_count, descriptive_count "
        "FROM predesigned_tests WHERE active=1 AND course=? AND level=? AND subject=? "
        "ORDER BY year DESC, month DESC, set_no",
        (course, level, subject),
    ).fetchall()


def _not_available_text_and_markup(what: str):
    text = (
        f"\U0001F615 Tests aren't available for {what} yet — only CA Inter Advanced Accounting has "
        f"ready-made tests right now. What would you like to do instead?"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F4DD Try CA Inter Advanced Accounting", callback_data="testflow:jump_advacc")],
        [InlineKeyboardButton("\U0001F519 Back to practice mode", callback_data="restart")],
    ])
    return text, markup


async def start_test_flow(update, context, bot_id: str, host):
    """Entry point -- the "test"/"take a test" text trigger. If the student
    already has a test in progress, resumes it instead of starting a new
    picker (never two concurrent tests)."""
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    user = update.effective_user
    telegram_user_id = user.id

    active = _get_active_test(conn, telegram_user_id)
    if active:
        await update.message.reply_text(
            "\U0001F4CB You already have a test in progress — picking up where you left off."
        )
        await _show_current_question(update.message, context, active[0], host)
        return

    courses = _available_courses(conn)
    if not courses:
        # Should never happen in practice (the catalog generator has run),
        # but never crash/dead-end if it somehow does.
        await update.message.reply_text(
            "\U0001F615 No tests are available on this platform yet — check back soon!"
        )
        return

    if len(courses) == 1:
        context.user_data[UD_PICKER_COURSE] = courses[0]
        await _show_level_picker(update.message, context, conn, courses[0])
        return

    # 2026-08-16: same profile-based pre-fill as exam_hub_bot.py's
    # resolve_entry() -- if the student's saved Course/Level (see
    # academic_profiles.py) narrows this down to exactly ONE course that
    # actually has real Test Mode content, skip the Course picker rather
    # than re-asking what's already on file. With 2+ still-usable matches
    # (or none), falls straight through to the existing picker below
    # unchanged -- Test Mode's real content is CA Inter Advanced
    # Accounting only today (see module docstring), so this mostly matters
    # once more courses/levels exist here.
    username, _ = identity.ensure_wallet_identity(conn, user)
    context.user_data["lavya_username"] = username  # read by _show_level_picker() one step down
    profile_courses = {p["course"] for p in academic_profiles.list_profiles(conn, username)} & set(courses)
    if len(profile_courses) == 1:
        course = next(iter(profile_courses))
        context.user_data[UD_PICKER_COURSE] = course
        await _show_level_picker(update.message, context, conn, course)
        return

    context.user_data[UD_PICKER_COURSES] = courses
    rows = [[InlineKeyboardButton(c, callback_data=f"testflow:course:{i}")] for i, c in enumerate(courses)]
    await update.message.reply_text("\U0001F4DD Which course?", reply_markup=InlineKeyboardMarkup(rows))


async def _show_level_picker(message_or_query, context, conn, course, edit=False):
    levels = _available_levels(conn, course)
    if len(levels) == 1:
        context.user_data[UD_PICKER_LEVEL] = levels[0]
        await _show_subject_picker(message_or_query, context, conn, course, levels[0], edit=edit)
        return

    # 2026-08-16: same profile-based pre-fill reasoning as start_test_flow()'s
    # own Course-level check above, one step down.
    username = context.user_data.get("lavya_username")
    if username:
        profile_levels = {
            p["level"] for p in academic_profiles.list_profiles(conn, username) if p["course"] == course
        } & set(levels)
        if len(profile_levels) == 1:
            level = next(iter(profile_levels))
            context.user_data[UD_PICKER_LEVEL] = level
            await _show_subject_picker(message_or_query, context, conn, course, level, edit=edit)
            return

    context.user_data[UD_PICKER_LEVELS] = levels
    rows = [[InlineKeyboardButton(lv, callback_data=f"testflow:level:{i}")] for i, lv in enumerate(levels)]
    text = f"\U0001F4DD {course} — which level?"
    markup = InlineKeyboardMarkup(rows)
    if edit:
        await message_or_query.edit_message_text(text, reply_markup=markup)
    else:
        await message_or_query.reply_text(text, reply_markup=markup)


async def _show_subject_picker(message_or_query, context, conn, course, level, edit=False):
    subjects = _available_subjects(conn, course, level)
    if len(subjects) == 1:
        await _show_sitting_picker(message_or_query, context, conn, course, level, subjects[0], edit=edit)
        return
    context.user_data[UD_PICKER_SUBJECTS] = subjects
    rows = [[InlineKeyboardButton(s, callback_data=f"testflow:subject:{i}")] for i, s in enumerate(subjects)]
    text = f"\U0001F4DD {course} {level} — which subject?"
    markup = InlineKeyboardMarkup(rows)
    if edit:
        await message_or_query.edit_message_text(text, reply_markup=markup)
    else:
        await message_or_query.reply_text(text, reply_markup=markup)


async def _show_sitting_picker(message_or_query, context, conn, course, level, subject, edit=False):
    sittings = _sittings_for(conn, course, level, subject)
    if not sittings:
        text, markup = _not_available_text_and_markup(f"{course} {level} {subject}")
        if edit:
            await message_or_query.edit_message_text(text, reply_markup=markup)
        else:
            await message_or_query.reply_text(text, reply_markup=markup)
        return

    context.user_data[UD_PICKER_SITTINGS] = [s[0] for s in sittings]  # catalog_keys, index-addressed
    rows = []
    for i, (catalog_key, title, total_marks, duration_minutes, mcq_count, descriptive_count) in enumerate(sittings):
        label = f"{title} — {total_marks} marks (~{duration_minutes} min)"
        rows.append([InlineKeyboardButton(label, callback_data=f"testflow:sitting:{i}")])
    text = f"\U0001F4DD {course} {level} {subject} — pick a test:"
    markup = InlineKeyboardMarkup(rows)
    if edit:
        await message_or_query.edit_message_text(text, reply_markup=markup)
    else:
        await message_or_query.reply_text(text, reply_markup=markup)


def _tier_options(total_marks: int):
    """Returns [(label, target_marks), ...] -- a tier at or above the
    sitting's own total collapses to one 'Full Paper' option instead of a
    phantom '100 marks' on, say, a 62-mark paper. Never more than
    len(SIZE_TIERS) options, per Pranav's explicit '3 options' ask."""
    options = []
    for t in SIZE_TIERS:
        if t >= total_marks:
            options.append((f"Full Paper ({total_marks} marks)", total_marks))
            break
        options.append((f"{t} marks", t))
    return options


async def _show_tier_picker(message_or_query, context, conn, catalog_key, edit=True):
    row = conn.execute("SELECT title, total_marks FROM predesigned_tests WHERE catalog_key=?", (catalog_key,)).fetchone()
    title, total_marks = row
    options = _tier_options(total_marks)
    context.user_data["testflow_tier_options"] = [m for _, m in options]
    rows = [[InlineKeyboardButton(label, callback_data=f"testflow:tier:{i}")] for i, (label, _) in enumerate(options)]
    text = f"\U0001F4DD <b>{title}</b> — how long a test?"
    markup = InlineKeyboardMarkup(rows)
    if edit:
        await message_or_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    else:
        await message_or_query.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


def _build_subset_questions(mcq_qs: list, desc_qs: list, target_marks: int):
    """Splits target_marks 30:70 between MCQ:Descriptive (the same ratio
    already confirmed for Custom Test's own marks-assembly -- reused here
    rather than inventing a second, competing ratio), then takes the
    largest PREFIX of each pool (in the sitting's own original order) that
    doesn't exceed its sub-target. Deterministic -- the same tier on the
    same sitting always yields the same subset, never randomized, so 'the
    20-mark version of MTP May 2026 Set 1' is a stable, well-defined thing.
    Any marks left over after both prefixes run out of room (a pool ran
    dry before its sub-target) are reallocated to the OTHER pool -- never
    silently under-delivers a tier's target if the content exists to fill it.

    Returns (mcq_subset, desc_subset, actual_total_marks) -- actual_total
    is often slightly UNDER target_marks (can't split a single question to
    hit an exact number) and this is expected, not a bug."""
    def take_prefix(qs, target, marks_fn):
        selected, total = [], 0
        for q in qs:
            m = marks_fn(q)
            if total + m <= target:
                selected.append(q)
                total += m
            else:
                break
        return selected, total

    mcq_marks_fn = lambda q: q.get("marks") or 0  # noqa: E731
    desc_marks_fn = _parse_desc_marks

    mcq_target = round(target_marks * TIER_MCQ_SHARE)
    desc_target = target_marks - mcq_target

    mcq_selected, mcq_total = take_prefix(mcq_qs, mcq_target, mcq_marks_fn)
    desc_selected, desc_total = take_prefix(desc_qs, desc_target, desc_marks_fn)

    leftover = target_marks - mcq_total - desc_total
    if leftover > 0:
        more_desc, more_total = take_prefix(desc_qs[len(desc_selected):], leftover, desc_marks_fn)
        desc_selected += more_desc
        desc_total += more_total
        leftover -= more_total
    if leftover > 0:
        more_mcq, more_total = take_prefix(mcq_qs[len(mcq_selected):], leftover, mcq_marks_fn)
        mcq_selected += more_mcq
        mcq_total += more_total

    return mcq_selected, desc_selected, mcq_total + desc_total


def _summary_text_and_markup(conn, catalog_key, tier_marks, username, tenant_id, host):
    row = conn.execute("SELECT title FROM predesigned_tests WHERE catalog_key=?", (catalog_key,)).fetchone()
    title = row[0]

    mcq_qs = _mcqs_for_catalog(host, catalog_key)
    desc_qs = _descs_for_catalog(host, catalog_key)
    mcq_subset, desc_subset, total_marks = _build_subset_questions(mcq_qs, desc_qs, tier_marks)
    mcq_count, descriptive_count = len(mcq_subset), len(desc_subset)
    mcq_marks = sum(q.get("marks") or 0 for q in mcq_subset)
    descriptive_marks = total_marks - mcq_marks
    duration_minutes = max(10, int(total_marks * 1.8 + 0.999))

    cost_credits = total_marks * wallet.RATE_TEST_CREDIT_PER_MARK
    balance = wallet.get_balance(conn, username)

    lines = [
        f"\U0001F4DD <b>{title}</b> — {tier_marks}-mark version",
        f"Total: {total_marks} marks (~{duration_minutes} minutes)",
        f"MCQs: {mcq_count} ({mcq_marks} marks) | Descriptive: {descriptive_count} ({descriptive_marks} marks)",
        "",
        f"Starting this test uses <b>{cost_credits} credits</b> from your balance "
        f"(you currently have {balance}).",
        "",
        "Once started: MCQ answers are hidden until you submit or time runs out. "
        "You can skip and come back to any question. Descriptive answers are "
        "submitted by uploading a photo of your written answer, question by question.",
    ]
    if balance < cost_credits:
        lines.append("")
        lines.append("⚠️ Your balance isn't enough for this test right now.")
        rows = [
            [InlineKeyboardButton("\U0001F4B3 Recharge Wallet", callback_data="walletrc:start")],
            [InlineKeyboardButton("\U0001F519 Back to practice mode", callback_data="restart")],
        ]
    else:
        rows = [
            [InlineKeyboardButton("\U0001F3C1 Start Test", callback_data="testflow:confirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="restart")],
        ]
    return "\n".join(lines), InlineKeyboardMarkup(rows)


# ---------------------------------------------------------------------------
# STARTING A TEST
# ---------------------------------------------------------------------------

def _new_test_id(telegram_user_id: int) -> str:
    """Millisecond precision, not seconds -- a real collision risk found
    while testing (2026-08-16): two Start-Test calls for the same student
    within the same second (e.g. rapid back-to-back test attempts, or a
    duplicate webhook update) would otherwise generate the exact same
    test_id and fail on test_sessions' PRIMARY KEY."""
    return f"T-{telegram_user_id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}"


async def _start_test(update_or_query, context, conn, telegram_user_id, bot_id, catalog_key, tier_marks, host, is_callback):
    # GUARD -- 2026-08-16 (found via independent code review): the roadmap's
    # own rule ("only one active test at a time, never silently create a
    # second concurrent session") was enforced at start_test_flow()'s "test"
    # text-trigger entry point but NOT here, at the actual state-changing
    # action -- so a double-tap on "Start Test" (ordinary impatient-user
    # behavior, not an exotic race) could run this whole function twice,
    # debiting the wallet twice and opening two test_sessions for the same
    # student, with the first one silently orphaned (_get_active_test()
    # always returns the most recent). This is the real chokepoint every
    # path into a new test funnels through, so the check belongs here, not
    # just at the one call site that happens to exist today.
    active = _get_active_test(conn, telegram_user_id)
    if active:
        text = "\U0001F4CB You already have a test in progress — picking up where you left off."
        if is_callback:
            await update_or_query.edit_message_text(text)
        else:
            await update_or_query.message.reply_text(text)
        await _show_current_question(update_or_query, context, active[0], host)
        return

    user = update_or_query.from_user if is_callback else update_or_query.effective_user
    username, _ = identity.ensure_wallet_identity(conn, user)

    mcq_qs = _mcqs_for_catalog(host, catalog_key)
    desc_qs = _descs_for_catalog(host, catalog_key)
    mcq_qs, desc_qs, total_marks = _build_subset_questions(mcq_qs, desc_qs, tier_marks)
    mcq_count, descriptive_count = len(mcq_qs), len(desc_qs)
    duration_minutes = max(10, int(total_marks * 1.8 + 0.999))

    test_id = _new_test_id(telegram_user_id)
    ok, new_balance, already_applied = wallet.debit_for_test(conn, username, host.TENANT_ID, test_id, total_marks)
    if not ok:
        text = "⚠️ Your balance isn't enough to start this test."
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F4B3 Recharge Wallet", callback_data="walletrc:start")]])
        if is_callback:
            await update_or_query.edit_message_text(text, reply_markup=markup)
        else:
            await update_or_query.message.reply_text(text, reply_markup=markup)
        return

    now_dt = datetime.now(timezone.utc)
    started_at = now_dt.isoformat(timespec="seconds")
    expires_at = (now_dt + timedelta(minutes=duration_minutes)).isoformat(timespec="seconds")

    platform_db.execute_with_retry(
        conn,
        "INSERT INTO test_sessions (test_id, bot_id, telegram_user_id, username, catalog_key, total_marks, "
        "mcq_count, descriptive_count, duration_minutes, started_at, expires_at, status) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,'in_progress')",
        (test_id, bot_id, telegram_user_id, username, catalog_key, total_marks, mcq_count, descriptive_count,
         duration_minutes, started_at, expires_at),
    )

    seq_no = 1
    for q in mcq_qs:
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO test_questions (test_id, seq_no, qtype, source_id, human_id, marks, status, chapter_slug, topic_text) "
            "VALUES (?,?,'mcq',?,?,?,'pending',?,?)",
            (test_id, seq_no, q.get("mcq_id"), q.get("human_id"), q.get("marks") or 0,
             q.get("chapter_slug"), q.get("topic_text")),
        )
        seq_no += 1
    for q in desc_qs:
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO test_questions (test_id, seq_no, qtype, source_id, human_id, marks, status, chapter_slug, topic_text) "
            "VALUES (?,?,'descriptive',?,?,?,'not_uploaded',?,?)",
            (test_id, seq_no, q.get("book_id"), q.get("human_id"), _parse_desc_marks(q),
             q.get("chapter_slug"), q.get("topic_text")),
        )
        seq_no += 1

    platform_db.execute_with_retry(conn, "UPDATE test_sessions SET current_seq_no=1 WHERE test_id=?", (test_id,))
    _log_activity(conn, test_id, None, "test_started", f"catalog_key={catalog_key} tier_marks={tier_marks} actual_marks={total_marks}")
    _schedule_test_timers(context, test_id, expires_at)

    intro = (
        f"\U0001F3C1 <b>Test started!</b> You have <b>{duration_minutes} minutes</b>.\n"
        f"{mcq_count} MCQs + {descriptive_count} descriptive questions, {total_marks} marks total.\n\n"
        f"MCQ answers are hidden until you submit. Type <code>upload</code> anytime to submit a "
        f"descriptive answer. Use \U0001F3C1 Submit Test when you're done, or it auto-submits at time-up."
    )
    chat_id = (update_or_query.message.chat_id if is_callback else update_or_query.message.chat_id)
    if is_callback:
        await update_or_query.edit_message_text(intro, parse_mode=ParseMode.HTML)
    else:
        await update_or_query.message.reply_text(intro, parse_mode=ParseMode.HTML)

    await _show_question_by_chat(context, chat_id, conn, test_id, 1, host)


def _mcqs_for_catalog(host, catalog_key):
    row = _catalog_row(host, catalog_key)
    return [q for q in host.mcq_bank.questions if _mcq_matches(q, row)]


def _descs_for_catalog(host, catalog_key):
    row = _catalog_row(host, catalog_key)
    return [q for q in host.bank.questions if _desc_matches(q, row)]


_CATALOG_ROW_CACHE = {}


def _catalog_row(host, catalog_key):
    if catalog_key in _CATALOG_ROW_CACHE:
        return _CATALOG_ROW_CACHE[catalog_key]
    conn = platform_db.get_connection()
    row = conn.execute(
        "SELECT course, level, subject, exam_type, year, month, set_no FROM predesigned_tests WHERE catalog_key=?",
        (catalog_key,),
    ).fetchone()
    conn.close()
    _CATALOG_ROW_CACHE[catalog_key] = row
    return row


_MONTH_NUM_TO_NAME = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}
_MCQ_ID_RE = re.compile(r"-(MTP|RTP|PYQ)-(\d{4})-(\d{2})(?:-S(\d))?-")
_DESC_SRC_RE = re.compile(r"(MTP|RTP|PYQ)\s+([A-Za-z]+)\s+(\d{4})(?:\s+Set\s+(\d))?", re.IGNORECASE)


def _mcq_matches(q, catrow):
    course, level, subject, exam_type, year, month, set_no = catrow
    if q.get("_course") != course or q.get("_level") != level or q.get("_subject") != subject:
        return False
    m = _MCQ_ID_RE.search(q.get("mcq_id") or "")
    if not m:
        return False
    et, yr, mo, sn = m.groups()
    return et.upper() == exam_type and yr == year and _MONTH_NUM_TO_NAME.get(mo) == month and (sn or None) == (set_no or None)


def _desc_matches(q, catrow):
    course, level, subject, exam_type, year, month, set_no = catrow
    if q.get("_course") != course or q.get("_level") != level or q.get("_subject") != subject:
        return False
    m = _DESC_SRC_RE.search(q.get("src_text") or "")
    if not m:
        return False
    et, mo, yr, sn = m.groups()
    return et.upper() == exam_type and yr == year and mo.title() == month and (sn or None) == (set_no or None)


def _parse_desc_marks(q) -> int:
    m = re.search(r"(\d+)", q.get("marks_text") or "")
    return int(m.group(1)) if m else 0


# ---------------------------------------------------------------------------
# QUESTION RENDERING / NAVIGATION
# ---------------------------------------------------------------------------

def _time_remaining_text(expires_at_iso: str) -> str:
    expires = datetime.fromisoformat(expires_at_iso)
    remaining = expires - datetime.now(timezone.utc)
    minutes = max(0, int(remaining.total_seconds() // 60))
    return f"{minutes} min left" if minutes > 0 else "time's up"


def _nav_keyboard(test_id, seq_no, total_questions, extra_rows=None):
    rows = []
    nav_row = []
    if seq_no > 1:
        nav_row.append(InlineKeyboardButton("◀ Prev", callback_data="tnav:prev"))
    if seq_no < total_questions:
        nav_row.append(InlineKeyboardButton("Next ▶", callback_data="tnav:next"))
    if nav_row:
        rows.append(nav_row)
    if extra_rows:
        rows.extend(extra_rows)
    rows.append([InlineKeyboardButton("\U0001F4CB Question List", callback_data="tnav:palette")])
    rows.append([InlineKeyboardButton("\U0001F3C1 Submit Test", callback_data="tnav:submit")])
    return InlineKeyboardMarkup(rows)


async def _show_question_by_chat(context, chat_id, conn, test_id, seq_no, host):
    """Sends a fresh message (not an edit) -- used for Next/Prev navigation
    and after starting a test, so the question history stays scrollable in
    the chat rather than being overwritten in place."""
    _mark_question_viewed(context, conn, test_id, seq_no)
    text, markup = _render_question(conn, test_id, seq_no, host)
    await host.send_long_message(context, chat_id, text, reply_markup=markup)


async def _show_current_question(message_or_query, context, test_id, host):
    """2026-08-16, Pranav's ask: resume from the EXACT question the
    student was last looking at (current_seq_no), not just 'the first
    unanswered one' -- if they'd navigated ahead to review something
    before a dropped connection, resuming should put them back exactly
    there, not silently jump them somewhere else."""
    conn = platform_db.get_connection()
    row = conn.execute("SELECT status, expires_at, current_seq_no FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()
    if not row or row[0] != "in_progress":
        return
    seq_no = row[2] or _first_unanswered_or_first(conn, test_id)
    chat_id = message_or_query.chat_id if hasattr(message_or_query, "chat_id") else message_or_query.message.chat_id
    await _show_question_by_chat(context, chat_id, conn, test_id, seq_no, host)


def _first_unanswered_or_first(conn, test_id):
    row = conn.execute(
        "SELECT seq_no FROM test_questions WHERE test_id=? AND status IN ('pending','not_uploaded') ORDER BY seq_no LIMIT 1",
        (test_id,),
    ).fetchone()
    if row:
        return row[0]
    row = conn.execute("SELECT MIN(seq_no) FROM test_questions WHERE test_id=?", (test_id,)).fetchone()
    return row[0] or 1


def _render_question(conn, test_id, seq_no, host):
    tq = conn.execute(
        "SELECT qtype, source_id, human_id, marks, status FROM test_questions WHERE test_id=? AND seq_no=?",
        (test_id, seq_no),
    ).fetchone()
    total = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=?", (test_id,)).fetchone()[0]
    expires_at = conn.execute("SELECT expires_at FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()[0]
    qtype, source_id, human_id, marks, status = tq
    time_line = f"⏱ {_time_remaining_text(expires_at)} | Q{seq_no}/{total} | {marks} marks"

    if qtype == "mcq":
        q = host.mcq_bank.get_by_id(source_id)
        if not q:
            return f"{time_line}\n\n(Question unavailable.)", _nav_keyboard(test_id, seq_no, total)
        body_parts = []
        if q.get("case_facts_html"):
            body_parts.append("<b>Case:</b>\n" + host.html_to_telegram_text(q["case_facts_html"]))
        body_parts.append(host.html_to_telegram_text(q.get("question_html", "")))
        options = q.get("options", {})
        option_lines = "\n".join(f"<b>{letter}.</b> {host.html_to_telegram_text(t).strip()}" for letter, t in sorted(options.items()))
        body_parts.append(option_lines)
        answer_line = ""
        opt_row = conn.execute("SELECT selected_option FROM test_mcq_answers WHERE test_id=? AND seq_no=?", (test_id, seq_no)).fetchone()
        if opt_row and opt_row[0]:
            answer_line = f"\n\n<i>Your answer: {opt_row[0]} (hidden/locked in until the test ends)</i>"
        text = f"{time_line}\n\U0001F194 {human_id or source_id}\n\n" + "\n\n".join(body_parts) + answer_line
        opt_row_buttons = [InlineKeyboardButton(letter, callback_data=f"topt:{letter}") for letter in sorted(options)]
        extra = [opt_row_buttons] if opt_row_buttons else None
        return text, _nav_keyboard(test_id, seq_no, total, extra_rows=extra)

    q = host.bank.get_by_book_id(source_id)
    if not q:
        return f"{time_line}\n\n(Question unavailable.)", _nav_keyboard(test_id, seq_no, total)
    question_text = host.html_to_telegram_text(q.get("question_html", ""))
    if status == "uploaded":
        upload_status = "✅ Uploaded"
    elif status == "skipped":
        upload_status = "⏭ Passed (you can still upload before submitting)"
    else:
        upload_status = "❌ Not uploaded yet"
    text = (
        f"{time_line}\n\U0001F194 {human_id or source_id}\n\n{question_text}\n\n"
        f'<i>{upload_status} — type "upload" to submit your written answer for this question.</i>'
    )
    return text, _nav_keyboard(test_id, seq_no, total)


# ---------------------------------------------------------------------------
# CALLBACK ROUTING
# ---------------------------------------------------------------------------

async def test_flow_callback(update, context, bot_id: str, host):
    query = update.callback_query
    data = query.data
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    telegram_user_id = query.from_user.id

    if data.startswith("testflow:"):
        await _handle_picker_callback(query, context, conn, data, bot_id, host)
        return

    active = _get_active_test(conn, telegram_user_id)
    if not active:
        await query.edit_message_text("⚠️ This test has ended or expired. Type <code>test</code> to start a new one.", parse_mode=ParseMode.HTML)
        return
    cols = [d[0] for d in conn.execute("SELECT * FROM test_sessions LIMIT 0").description]
    session = dict(zip(cols, active))
    test_id = session["test_id"]

    if data.startswith("tnav:"):
        action = data.split(":", 1)[1]
        await _handle_nav(query, context, conn, test_id, action, host)
    elif data.startswith("topt:"):
        letter = data.split(":", 1)[1]
        await _handle_option_select(query, context, conn, test_id, letter, host)
    elif data.startswith("tgo:"):
        seq_no = int(data.split(":", 1)[1])
        _mark_question_viewed(context, conn, test_id, seq_no)
        text, markup = _render_question(conn, test_id, seq_no, host)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif data.startswith("tupload:"):
        await _handle_tupload_callback(query, context, conn, test_id, data, host)
    elif data.startswith("tgrace:"):
        await _handle_grace_callback(query, context, conn, test_id, data, host)


async def _handle_tupload_callback(query, context, conn, test_id, data, host):
    parts = data.split(":")
    seq_no = int(parts[1])

    if len(parts) == 2:
        # Initial pick from the question list. If this question already has
        # uploaded pages, don't silently accept more on top -- ask first
        # (real gap Pranav found by testing: the bot used to just start
        # accepting new photos with no warning at all).
        existing_pages = conn.execute(
            "SELECT COUNT(*) FROM test_uploads WHERE test_id=? AND seq_no=?", (test_id, seq_no)
        ).fetchone()[0]
        if existing_pages > 0:
            await query.edit_message_text(
                f"You've already uploaded {existing_pages} page(s) for Q{seq_no}. What would you like to do?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("\U0001F504 Overwrite (start fresh)", callback_data=f"tupload:{seq_no}:overwrite")],
                    [InlineKeyboardButton("➕ Add more pages", callback_data=f"tupload:{seq_no}:append")],
                ]),
            )
            return
        await _begin_upload_collection(query, context, seq_no, start_page=0)
        return

    # len(parts) == 3 -- the overwrite/append choice was just made.
    mode = parts[2]
    if mode == "overwrite":
        rows = conn.execute("SELECT file_path FROM test_uploads WHERE test_id=? AND seq_no=?", (test_id, seq_no)).fetchall()
        for (file_path,) in rows:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass
        platform_db.execute_with_retry(conn, "DELETE FROM test_uploads WHERE test_id=? AND seq_no=?", (test_id, seq_no))
        platform_db.execute_with_retry(conn, "UPDATE test_questions SET status='not_uploaded' WHERE test_id=? AND seq_no=?", (test_id, seq_no))
        _log_activity(conn, test_id, seq_no, "upload_overwrite_chosen", f"discarded_pages={len(rows)}")
        await _begin_upload_collection(query, context, seq_no, start_page=0)
    else:  # append
        max_page = conn.execute("SELECT COALESCE(MAX(page_no), 0) FROM test_uploads WHERE test_id=? AND seq_no=?", (test_id, seq_no)).fetchone()[0]
        _log_activity(conn, test_id, seq_no, "upload_append_chosen", f"existing_pages={max_page}")
        await _begin_upload_collection(query, context, seq_no, start_page=max_page)


async def _begin_upload_collection(query, context, seq_no, start_page: int):
    context.user_data[UD_UPLOAD_SEQ] = seq_no
    context.user_data[UD_UPLOAD_PAGE_COUNTER] = start_page
    context.user_data[UD_AWAITING_UPLOAD_PICK] = False
    await query.edit_message_text(
        f"\U0001F4F7 Send photo(s) of your answer for Q{seq_no} now — one at a time. "
        f'Type "done" when finished with this question, or "pass" if you don\'t want to answer it.',
    )


async def _handle_picker_callback(query, context, conn, data, bot_id, host):
    parts = data.split(":")
    action = parts[1]

    if action == "course":
        idx = int(parts[2])
        course = context.user_data.get(UD_PICKER_COURSES, [])[idx]
        context.user_data[UD_PICKER_COURSE] = course
        await _show_level_picker(query, context, conn, course, edit=True)
    elif action == "level":
        idx = int(parts[2])
        level = context.user_data.get(UD_PICKER_LEVELS, [])[idx]
        context.user_data[UD_PICKER_LEVEL] = level
        course = context.user_data[UD_PICKER_COURSE]
        await _show_subject_picker(query, context, conn, course, level, edit=True)
    elif action == "subject":
        idx = int(parts[2])
        subject = context.user_data.get(UD_PICKER_SUBJECTS, [])[idx]
        course = context.user_data[UD_PICKER_COURSE]
        level = context.user_data[UD_PICKER_LEVEL]
        await _show_sitting_picker(query, context, conn, course, level, subject, edit=True)
    elif action == "sitting":
        idx = int(parts[2])
        catalog_key = context.user_data.get(UD_PICKER_SITTINGS, [])[idx]
        context.user_data[UD_PICKER_CATALOG_KEY] = catalog_key
        await _show_tier_picker(query, context, conn, catalog_key, edit=True)
    elif action == "tier":
        idx = int(parts[2])
        tier_marks = context.user_data.get("testflow_tier_options", [])[idx]
        context.user_data[UD_PICKER_TIER_MARKS] = tier_marks
        catalog_key = context.user_data.get(UD_PICKER_CATALOG_KEY)
        user = query.from_user
        username, _ = identity.ensure_wallet_identity(conn, user)
        text, markup = _summary_text_and_markup(conn, catalog_key, tier_marks, username, host.TENANT_ID, host)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "confirm":
        catalog_key = context.user_data.get(UD_PICKER_CATALOG_KEY)
        tier_marks = context.user_data.get(UD_PICKER_TIER_MARKS)
        if not catalog_key or not tier_marks:
            await query.edit_message_text("⚠️ Something went wrong — type <code>test</code> to start again.", parse_mode=ParseMode.HTML)
            return
        await _start_test(query, context, conn, query.from_user.id, bot_id, catalog_key, tier_marks, host, is_callback=True)
    elif action == "jump_advacc":
        courses = _available_courses(conn)
        context.user_data[UD_PICKER_COURSES] = courses
        if "CA" in courses:
            context.user_data[UD_PICKER_COURSE] = "CA"
            await _show_level_picker(query, context, conn, "CA", edit=True)


async def _handle_nav(query, context, conn, test_id, action, host):
    total = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=?", (test_id,)).fetchone()[0]
    current = _current_seq_no(query, context, conn, test_id)

    if action == "next" and current < total:
        _mark_question_viewed(context, conn, test_id, current + 1)
        text, markup = _render_question(conn, test_id, current + 1, host)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "prev" and current > 1:
        _mark_question_viewed(context, conn, test_id, current - 1)
        text, markup = _render_question(conn, test_id, current - 1, host)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "palette":
        text, markup = _render_palette(conn, test_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "submit":
        # 2026-08-16, Pranav's ask: show a summary before actually
        # submitting, not submit immediately on the first tap.
        _log_activity(conn, test_id, None, "submit_confirmation_shown")
        text, markup = _submit_confirmation_text_and_markup(conn, test_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif action == "submit_confirm":
        await _submit_test(query, context, conn, test_id, host, auto=False)
    elif action == "submit_cancel":
        current = _first_unanswered_or_first(conn, test_id)
        _mark_question_viewed(context, conn, test_id, current)
        text, markup = _render_question(conn, test_id, current, host)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


def _submit_confirmation_text_and_markup(conn, test_id):
    mcq_total = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=? AND qtype='mcq'", (test_id,)).fetchone()[0]
    mcq_answered = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=? AND qtype='mcq' AND status='answered'", (test_id,)).fetchone()[0]
    desc_total = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=? AND qtype='descriptive'", (test_id,)).fetchone()[0]
    desc_uploaded = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=? AND qtype='descriptive' AND status='uploaded'", (test_id,)).fetchone()[0]
    desc_skipped = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=? AND qtype='descriptive' AND status='skipped'", (test_id,)).fetchone()[0]
    desc_missing = desc_total - desc_uploaded - desc_skipped

    lines = ["\U0001F4CB <b>Ready to submit?</b>", ""]
    if mcq_total > 0:
        lines.append(f"MCQs: <b>{mcq_answered}/{mcq_total} answered</b> ({mcq_total - mcq_answered} left blank)")
    if desc_total > 0:
        lines.append(f"Descriptive: <b>{desc_uploaded}/{desc_total} uploaded</b>"
                      + (f", {desc_skipped} passed" if desc_skipped else "")
                      + (f", {desc_missing} not yet uploaded" if desc_missing else ""))
    lines.append("")
    lines.append("Once submitted, you can't go back and change anything.")

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm & Submit", callback_data="tnav:submit_confirm")],
        [InlineKeyboardButton("◀ Go Back (keep working)", callback_data="tnav:submit_cancel")],
    ])
    return "\n".join(lines), markup


def _current_seq_no(query, context, conn, test_id):
    """Parsed back out of the message being edited isn't reliable across
    edits -- instead, re-derive from the message text's own 'Q{n}/{total}'
    marker, which _render_question() always writes. Falls back to the first
    pending question if parsing fails for any reason."""
    text = query.message.text or ""
    m = re.search(r"Q(\d+)/\d+", text)
    if m:
        return int(m.group(1))
    return _first_unanswered_or_first(conn, test_id)


def _render_palette(conn, test_id):
    rows_data = conn.execute(
        "SELECT seq_no, qtype, status FROM test_questions WHERE test_id=? ORDER BY seq_no", (test_id,)
    ).fetchall()
    rows = []
    current_row = []
    for seq_no, qtype, status in rows_data:
        if status in ("answered", "uploaded"):
            icon = "✅"
        elif status == "skipped":
            icon = "⚪"
        else:
            icon = "\U0001F7E1" if qtype == "mcq" else "\U0001F4DD"
        current_row.append(InlineKeyboardButton(f"{icon}{seq_no}", callback_data=f"tgo:{seq_no}"))
        if len(current_row) == 5:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([InlineKeyboardButton("\U0001F3C1 Submit Test", callback_data="tnav:submit")])
    text = "\U0001F4CB <b>Question List</b>\n✅ done ⚪ skipped \U0001F7E1 MCQ pending \U0001F4DD descriptive pending\nTap a number to jump there."
    return text, InlineKeyboardMarkup(rows)


async def _handle_option_select(query, context, conn, test_id, letter, host):
    seq_no = _current_seq_no(query, context, conn, test_id)
    now = platform_db.now()
    existing = conn.execute("SELECT selected_option FROM test_mcq_answers WHERE test_id=? AND seq_no=?", (test_id, seq_no)).fetchone()
    if existing:
        previous_option = existing[0]
        platform_db.execute_with_retry(
            conn, "UPDATE test_mcq_answers SET selected_option=?, answered_at=? WHERE test_id=? AND seq_no=?",
            (letter, now, test_id, seq_no),
        )
        # 2026-08-16, Pranav's ask: distinguish a first pick from a later
        # CHANGE of mind -- both matter for understanding how confident a
        # student actually was, not just what they ended up with.
        if previous_option != letter:
            _log_activity(conn, test_id, seq_no, "mcq_option_changed", f"from={previous_option} to={letter}")
    else:
        platform_db.execute_with_retry(
            conn, "INSERT INTO test_mcq_answers (test_id, seq_no, selected_option, answered_at) VALUES (?,?,?,?)",
            (test_id, seq_no, letter, now),
        )
        _log_activity(conn, test_id, seq_no, "mcq_option_selected", f"option={letter}")
    platform_db.execute_with_retry(
        conn, "UPDATE test_questions SET status='answered' WHERE test_id=? AND seq_no=?", (test_id, seq_no),
    )
    text, markup = _render_question(conn, test_id, seq_no, host)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


# ---------------------------------------------------------------------------
# SUBMISSION / SCORING
# ---------------------------------------------------------------------------

async def _submit_test(update_or_query, context, conn, test_id, host, auto: bool):
    tqs = conn.execute("SELECT seq_no, qtype, source_id, marks FROM test_questions WHERE test_id=?", (test_id,)).fetchall()
    mcq_score = 0
    mcq_max = 0
    for seq_no, qtype, source_id, marks in tqs:
        if qtype != "mcq":
            continue
        mcq_max += marks
        ans = conn.execute("SELECT selected_option FROM test_mcq_answers WHERE test_id=? AND seq_no=?", (test_id, seq_no)).fetchone()
        q = host.mcq_bank.get_by_id(source_id)
        if ans and ans[0] and q and ans[0] == q.get("correct_option"):
            mcq_score += marks
        if not ans:
            platform_db.execute_with_retry(conn, "UPDATE test_questions SET status='skipped' WHERE test_id=? AND seq_no=?", (test_id, seq_no))

    # 2026-08-16: a question with real uploaded pages counts as uploaded at
    # submission time EVEN IF "done" was never typed (e.g. time ran out
    # mid-upload) -- nothing is actually lost, since every photo is saved
    # to disk/DB the instant it's sent, not batched behind "done". This is
    # what makes the grace-period question moot from a data-safety
    # standpoint: reconcile any question with real pages but a stale
    # 'not_uploaded' status before counting.
    platform_db.execute_with_retry(
        conn,
        "UPDATE test_questions SET status='uploaded' WHERE test_id=? AND qtype='descriptive' AND status='not_uploaded' "
        "AND seq_no IN (SELECT DISTINCT seq_no FROM test_uploads WHERE test_id=?)",
        (test_id, test_id),
    )

    descriptive_count = sum(1 for _, qtype, _, _ in tqs if qtype == "descriptive")
    uploaded_count = conn.execute(
        "SELECT COUNT(*) FROM test_questions WHERE test_id=? AND qtype='descriptive' AND status='uploaded'", (test_id,)
    ).fetchone()[0]

    now = platform_db.now()
    platform_db.execute_with_retry(
        conn,
        "UPDATE test_sessions SET status='submitted', submitted_at=?, mcq_score=?, mcq_max=? WHERE test_id=?",
        (now, mcq_score, mcq_max, test_id),
    )
    _log_activity(conn, test_id, None, "test_submitted", f"auto={auto} mcq_score={mcq_score}/{mcq_max} descriptive_uploaded={uploaded_count}/{descriptive_count}")
    _cancel_test_timers(context, test_id)

    lines = ["\U0001F3C1 <b>Test submitted!</b>"]
    if auto:
        lines[0] = "⏰ <b>Time's up — your test was auto-submitted.</b>"
    if mcq_max > 0:
        lines.append(f"MCQ score: <b>{mcq_score}/{mcq_max}</b>")
    if descriptive_count > 0:
        lines.append(f"Descriptive: {uploaded_count}/{descriptive_count} question(s) uploaded — saved safely.")
        lines.append("Evaluation for descriptive answers isn't available yet — coming in a future update.")
    lines.append("\nType <code>test</code> anytime to take another one.")
    text = "\n".join(lines)

    chat_id = update_or_query.message.chat_id
    if hasattr(update_or_query, "edit_message_text"):
        try:
            await update_or_query.edit_message_text(text, parse_mode=ParseMode.HTML)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# TIMERS -- expiry, reminders, and the interactive grace-period offer, all
# surviving a restart via rearm_pending_test_jobs() at startup. Added/
# expanded 2026-08-16 per Pranav's real manual-testing feedback: reminders
# didn't exist at all before, and time-up used to hard-submit immediately
# with no grace whatsoever.
# ---------------------------------------------------------------------------

REMINDER_MINUTES_BEFORE = [5, 3]     # Pranav's explicit ask
GRACE_OPTIONS_MINUTES = [2, 3, 5]    # offered once; student picks at most one
GRACE_TIMEOUT_SECONDS = 60           # how long to wait for a response to the grace offer before submitting anyway


def _expiry_job_name(test_id):
    return f"test_expiry:{test_id}"


def _reminder_job_name(test_id, minutes_before):
    return f"test_reminder:{test_id}:{minutes_before}"


def _grace_timeout_job_name(test_id):
    return f"test_grace_timeout:{test_id}"


def _schedule_test_timers(context, test_id, expires_at_iso):
    """Schedules the expiry job AND both reminder jobs. A reminder whose
    fire-time has already passed (e.g. re-arming a short-remaining test
    after a restart) is simply skipped, never scheduled with a negative
    delay."""
    if not context.job_queue:
        return
    now = datetime.now(timezone.utc)
    expires_dt = datetime.fromisoformat(expires_at_iso)
    delay = max(1, (expires_dt - now).total_seconds())
    context.job_queue.run_once(_expiry_job_callback, when=delay, name=_expiry_job_name(test_id), data={"test_id": test_id})

    for minutes_before in REMINDER_MINUTES_BEFORE:
        fire_at = expires_dt - timedelta(minutes=minutes_before)
        reminder_delay = (fire_at - now).total_seconds()
        if reminder_delay > 0:
            context.job_queue.run_once(
                _reminder_job_callback, when=reminder_delay, name=_reminder_job_name(test_id, minutes_before),
                data={"test_id": test_id, "minutes_before": minutes_before},
            )


def _cancel_test_timers(context, test_id):
    """Cancels every job class this test might have pending -- expiry,
    both reminders, the grace-timeout fallback, and the heartbeat chain --
    called whenever a test ends for any reason (manual submit, grace choice
    made, etc.) so nothing fires against an already-finished test. The
    heartbeat is self-limiting even without this (it checks status='in_progress'
    before rescheduling itself), but explicitly cancelling it here avoids
    one wasted no-op firing after a test ends."""
    if not context.job_queue:
        return
    names = [_expiry_job_name(test_id), _grace_timeout_job_name(test_id), _heartbeat_job_name(test_id)]
    names += [_reminder_job_name(test_id, m) for m in REMINDER_MINUTES_BEFORE]
    for name in names:
        for job in context.job_queue.get_jobs_by_name(name):
            job.schedule_removal()


async def _reminder_job_callback(context):
    test_id = context.job.data["test_id"]
    minutes_before = context.job.data["minutes_before"]
    conn = platform_db.get_connection()
    row = conn.execute("SELECT status, telegram_user_id FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()
    if not row or row[0] != "in_progress":
        return
    _log_activity(conn, test_id, None, "reminder_sent", f"minutes_before={minutes_before}")
    await context.bot.send_message(chat_id=row[1], text=f"⏰ {minutes_before} minute(s) left in your test!")


async def _expiry_job_callback(context):
    """Fires at the nominal time limit. The FIRST time this fires for a
    test, it doesn't submit -- it offers the student a one-time choice of
    a few extra minutes (Pranav's explicit ask, 2026-08-16). If they've
    already been offered (this is a re-fire at an extended deadline, or a
    stray duplicate), it submits for real -- the offer is never repeated."""
    test_id = context.job.data["test_id"]
    conn = platform_db.get_connection()
    row = conn.execute("SELECT status, telegram_user_id, grace_offered_at FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()
    if not row or row[0] != "in_progress":
        return
    telegram_user_id, grace_offered_at = row[1], row[2]

    if grace_offered_at is None:
        now = platform_db.now()
        platform_db.execute_with_retry(conn, "UPDATE test_sessions SET grace_offered_at=? WHERE test_id=?", (now, test_id))
        _log_activity(conn, test_id, None, "grace_offered")
        option_row = [InlineKeyboardButton(f"+{m} min", callback_data=f"tgrace:{m}") for m in GRACE_OPTIONS_MINUTES]
        markup = InlineKeyboardMarkup([option_row, [InlineKeyboardButton("Submit now", callback_data="tgrace:submit")]])
        await context.bot.send_message(
            chat_id=telegram_user_id,
            text="⏰ Time's up! Need a few extra minutes to finish? This can only be offered once.",
            reply_markup=markup,
        )
        if context.job_queue:
            context.job_queue.run_once(
                _grace_timeout_job_callback, when=GRACE_TIMEOUT_SECONDS,
                name=_grace_timeout_job_name(test_id), data={"test_id": test_id},
            )
        return

    await _finalize_submit(context, conn, test_id)


async def _grace_timeout_job_callback(context):
    """No response to the grace offer within GRACE_TIMEOUT_SECONDS --
    treated as an implicit 'no', submits for real."""
    test_id = context.job.data["test_id"]
    conn = platform_db.get_connection()
    row = conn.execute("SELECT status FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()
    if not row or row[0] != "in_progress":
        return
    await _finalize_submit(context, conn, test_id)


async def _handle_grace_callback(query, context, conn, test_id, data, host):
    choice = data.split(":", 1)[1]
    _log_activity(conn, test_id, None, "grace_chosen", f"choice={choice}")
    if context.job_queue:
        for job in context.job_queue.get_jobs_by_name(_grace_timeout_job_name(test_id)):
            job.schedule_removal()

    if choice == "submit":
        await query.edit_message_text("Submitting now...")
        await _finalize_submit(context, conn, test_id)
        return

    minutes = int(choice)
    new_expiry = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    platform_db.execute_with_retry(
        conn, "UPDATE test_sessions SET expires_at=?, grace_requested_minutes=? WHERE test_id=?",
        (new_expiry.isoformat(timespec="seconds"), minutes, test_id),
    )
    if context.job_queue:
        context.job_queue.run_once(
            _expiry_job_callback, when=minutes * 60, name=_expiry_job_name(test_id), data={"test_id": test_id},
        )
    await query.edit_message_text(f"✅ You have {minutes} more minute(s). Good luck!")


async def _finalize_submit(context, conn, test_id):
    """Shared by the grace-timeout path and the 'already offered, this is
    the real deadline' expiry path -- both end up here to actually call
    _submit_test() with a synthetic query object (no real callback query
    exists when a job_queue job, not a button tap, is what triggers this)."""
    row = conn.execute("SELECT telegram_user_id FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()
    if not row:
        return
    telegram_user_id = row[0]

    class _FakeQuery:
        def __init__(self, chat_id):
            self.message = _FakeMsg(chat_id)

        async def edit_message_text(self, *a, **k):
            raise NotImplementedError  # forces the send_message fallback in _submit_test

    class _FakeMsg:
        def __init__(self, chat_id):
            self.chat_id = chat_id

    host = context.application.bot_data.get("test_flow_host")
    if host is None:
        logger.warning(f"test_flow: finalize-submit fired for {test_id} but no host module registered -- cannot auto-submit correctly.")
        return
    await _submit_test(_FakeQuery(telegram_user_id), context, conn, test_id, host, auto=True)


def rearm_pending_test_jobs(application, host):
    """Called once at bot startup. Sweeps every in_progress test_sessions
    row: already past expiry with the grace offer already shown (or
    overdue either way) -> finalize immediately; already past expiry but
    never offered grace yet -> re-arm the expiry job so the offer still
    happens correctly; still valid -> re-arm expiry + reminder jobs
    (job_queue jobs don't survive a process restart, same reasoning
    already established for the wallet recharge polling design and the
    platform's other job_queue users)."""
    application.bot_data["test_flow_host"] = host
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    rows = conn.execute("SELECT test_id, expires_at, grace_offered_at, current_seq_no FROM test_sessions WHERE status='in_progress'").fetchall()
    now = datetime.now(timezone.utc)
    rearmed, finalized = 0, 0
    for test_id, expires_at, grace_offered_at, current_seq_no in rows:
        if datetime.fromisoformat(expires_at) <= now:
            if grace_offered_at is not None:
                application.job_queue.run_once(_grace_timeout_job_callback, when=1, name=_grace_timeout_job_name(test_id), data={"test_id": test_id})
            else:
                application.job_queue.run_once(_expiry_job_callback, when=1, name=_expiry_job_name(test_id), data={"test_id": test_id})
            finalized += 1
        else:
            delay = (datetime.fromisoformat(expires_at) - now).total_seconds()
            application.job_queue.run_once(_expiry_job_callback, when=delay, name=_expiry_job_name(test_id), data={"test_id": test_id})
            for minutes_before in REMINDER_MINUTES_BEFORE:
                fire_at = datetime.fromisoformat(expires_at) - timedelta(minutes=minutes_before)
                reminder_delay = (fire_at - now).total_seconds()
                if reminder_delay > 0:
                    application.job_queue.run_once(
                        _reminder_job_callback, when=reminder_delay, name=_reminder_job_name(test_id, minutes_before),
                        data={"test_id": test_id, "minutes_before": minutes_before},
                    )
            # Re-arm the no-activity heartbeat chain too (2026-08-16) -- it
            # doesn't survive a restart any more than the other jobs do.
            if current_seq_no:
                application.job_queue.run_once(
                    _heartbeat_job_callback, when=HEARTBEAT_INTERVAL_SECONDS, name=_heartbeat_job_name(test_id),
                    data={"test_id": test_id, "seq_no": current_seq_no},
                )
            rearmed += 1
    if rearmed or finalized:
        logger.info(f"test_flow: startup sweep -- re-armed {rearmed} in-progress test(s), finalizing {finalized} already-expired test(s).")


# ---------------------------------------------------------------------------
# UPLOAD COLLECTION (text + photo/document handling)
# ---------------------------------------------------------------------------

def matches_upload_trigger(text: str) -> bool:
    return text.strip().lower() in UPLOAD_TRIGGER_PHRASES


async def start_upload_pick(update, context, host):
    conn = platform_db.get_connection()
    active = _get_active_test(conn, update.effective_user.id)
    if not active:
        await update.message.reply_text("You don't have a test in progress right now. Type <code>test</code> to start one.", parse_mode=ParseMode.HTML)
        return
    cols = [d[0] for d in conn.execute("SELECT * FROM test_sessions LIMIT 0").description]
    session = dict(zip(cols, active))
    test_id = session["test_id"]
    descs = conn.execute(
        "SELECT seq_no, human_id, status FROM test_questions WHERE test_id=? AND qtype='descriptive' ORDER BY seq_no", (test_id,)
    ).fetchall()
    if not descs:
        await update.message.reply_text("This test has no descriptive questions to upload an answer for.")
        return
    rows = []
    for seq_no, human_id, status in descs:
        icon = "✅" if status == "uploaded" else "❌"
        rows.append([InlineKeyboardButton(f"{icon} Q{seq_no} ({human_id or ''})", callback_data=f"tupload:{seq_no}")])
    context.user_data[UD_AWAITING_UPLOAD_PICK] = True
    await update.message.reply_text("Which question is this answer for?", reply_markup=InlineKeyboardMarkup(rows))


PASS_UPLOAD_PHRASES = {"pass"}


async def handle_upload_text_input(update, context, host) -> bool:
    """Returns True if the message was consumed. Handles 'done' (finish
    this question, keeping whatever was uploaded) and 'pass' (2026-08-16,
    Pranav's ask: an explicit way to decline a descriptive question rather
    than leaving no fallback for "I don't want to upload this") while
    actively collecting pages for a question."""
    text = (update.message.text or "").strip().lower()
    if not is_collecting_upload(context):
        return False

    seq_no = context.user_data.get(UD_UPLOAD_SEQ)

    if text in PASS_UPLOAD_PHRASES:
        context.user_data.pop(UD_UPLOAD_SEQ, None)
        context.user_data.pop(UD_UPLOAD_PAGE_COUNTER, None)
        conn = platform_db.get_connection()
        active = _get_active_test(conn, update.effective_user.id)
        if active:
            cols = [d[0] for d in conn.execute("SELECT * FROM test_sessions LIMIT 0").description]
            test_id = dict(zip(cols, active))["test_id"]
            platform_db.execute_with_retry(conn, "UPDATE test_questions SET status='skipped' WHERE test_id=? AND seq_no=?", (test_id, seq_no))
            _log_activity(conn, test_id, seq_no, "question_passed")
            await update.message.reply_text(f'Q{seq_no} marked as passed — you can still come back to it later by typing "upload" again before you submit.')
        return True

    if text in DONE_UPLOAD_PHRASES:
        context.user_data.pop(UD_UPLOAD_SEQ, None)
        context.user_data.pop(UD_UPLOAD_PAGE_COUNTER, None)
        conn = platform_db.get_connection()
        active = _get_active_test(conn, update.effective_user.id)
        if active:
            cols = [d[0] for d in conn.execute("SELECT * FROM test_sessions LIMIT 0").description]
            test_id = dict(zip(cols, active))["test_id"]
            page_count = conn.execute("SELECT COUNT(*) FROM test_uploads WHERE test_id=? AND seq_no=?", (test_id, seq_no)).fetchone()[0]
            if page_count > 0:
                platform_db.execute_with_retry(conn, "UPDATE test_questions SET status='uploaded' WHERE test_id=? AND seq_no=?", (test_id, seq_no))
                _log_activity(conn, test_id, seq_no, "upload_done", f"page_count={page_count}")
                await update.message.reply_text(f'✅ Saved {page_count} page(s) for Q{seq_no}. Type "test" to continue, or "upload" for another question.')
            else:
                await update.message.reply_text(f'No pages were received for Q{seq_no} — nothing saved. Type "upload" to try again, or "pass" if you don\'t want to answer it.')
        return True

    return False


async def handle_upload_photo_or_document(update, context, host) -> bool:
    """Returns True if this message was a photo/document consumed by an
    active upload-collection state, False otherwise (caller should ignore
    or handle it some other way)."""
    seq_no = context.user_data.get(UD_UPLOAD_SEQ)
    if seq_no is None:
        return False

    conn = platform_db.get_connection()
    active = _get_active_test(conn, update.effective_user.id)
    if not active:
        await update.message.reply_text("This test has ended — the upload wasn't saved.")
        context.user_data.pop(UD_UPLOAD_SEQ, None)
        return True
    cols = [d[0] for d in conn.execute("SELECT * FROM test_sessions LIMIT 0").description]
    test_id = dict(zip(cols, active))["test_id"]

    file_obj = None
    mime_type = "image/jpeg"
    if update.message.photo:
        file_obj = await update.message.photo[-1].get_file()
    elif update.message.document:
        file_obj = await update.message.document.get_file()
        mime_type = update.message.document.mime_type or "application/octet-stream"
    else:
        return False

    page_no = context.user_data.get(UD_UPLOAD_PAGE_COUNTER, 0) + 1
    context.user_data[UD_UPLOAD_PAGE_COUNTER] = page_no

    dest_dir = UPLOADS_ROOT / test_id / str(seq_no)
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = ".pdf" if "pdf" in mime_type else ".jpg"
    dest_path = dest_dir / f"{page_no}{ext}"
    await file_obj.download_to_drive(custom_path=str(dest_path))

    platform_db.execute_with_retry(
        conn,
        "INSERT INTO test_uploads (test_id, seq_no, page_no, file_path, telegram_file_id, mime_type, uploaded_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (test_id, seq_no, page_no, str(dest_path), file_obj.file_id, mime_type, platform_db.now()),
    )
    _log_activity(conn, test_id, seq_no, "upload_page_added", f"page_no={page_no} mime_type={mime_type}")
    await update.message.reply_text(f'\U0001F4C4 Page {page_no} saved for Q{seq_no}. Send another page, or type "done" to finish this question.')
    return True
