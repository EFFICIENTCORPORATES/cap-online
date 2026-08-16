"""
1Lavya Exam Hub Bot (Bot 2)
----------------------------
Drill-down exam practice bot, Mode-first as of the 2026-08-12/13 rewrite
(see /CLAUDE.md section 11's last several dated entries for the full
"why" behind every decision below -- this is the short version):

  Mode (Descriptive / MCQ)
    -> Course (CA / CS / CMA)
      -> Level (per course, e.g. Foundation / Inter / Final)
        -> Subject (e.g. CA Foundation: Accounting / Business Economics /
           Quantitative Aptitude -- added 2026-08-13, previously MISSING
           entirely, which silently merged every subject's chapters into
           one undifferentiated list)
          -> Exam Type (MTP / RTP / PYQ / Mix)
            -> Year (or Mix - all years)
              -> Chapter (or All Chapters)
                Descriptive: -> Shows a question -> "Show Answer?" ->
                  answer (text) + PDF download
                MCQ: -> Shows a question + up to 4 options as buttons ->
                  student taps an option -> immediately shown correct/
                  incorrect, the correct answer, its explanation, and a
                  "Report Issue in MCQ" button -> Next Question /
                  Chapter List / I'm Done (a real today's-summary +
                  report offer, not just a reset)

EVERY step above is auto-skipped when only one real option exists, and
every option list is derived LIVE from what's actually loaded (never a
hand-maintained "show everything, gate later" list) -- a student never
taps into a dead end. See resolve_entry()'s own docstring for the
cascade mechanics.

CONTENT POOL, standing rule (2026-08-13): every question on the platform
-- 1LAVYA-authored or faculty-sourced -- is part of THIS bot's pool, no
exceptions (a faculty's own bot stays separately, narrowly scoped via
their own tenants.json content_scope). Provenance is tracked via
_content_owner (inferred from each content file's own path), never via
withholding content here.

Every question record resolves a real (course, level, subject) triple
and a globally-unique, student-facing human_id (shown on-screen, first
line of every question) via course_catalog -- see
_resolve_course_level_subject()'s own docstring.

Every question shown, answer reveal, PDF request, and MCQ attempt (selected
option + correct/incorrect) is logged to the shared platform database (see
telegram/database/db.py, telegram/database/schema.sql's exam_hub_* tables)
for analytics -- which student saw/attempted which question, and how they
did. See README_Bot2_ExamHub.md for the full DB schema.

SETUP (do this before running):
1. pip install python-telegram-bot[job-queue] beautifulsoup4 xhtml2pdf python-dotenv --break-system-packages
2. BOT-ID-AWARE (tenant-aware since 2026-08-10; refactored onto the master
   bot mapping same day) -- see telegram/config/bots.json / bots.README.md.
   Set BOT_ID before launching (defaults to "1lavya-examhub", today's
   original behavior; also accepts the older TENANT_ID name as a fallback
   for single-bot tenants, e.g. "csarunchouhan"). BOT_ID selects a bots.json
   row (which token/script); that row's tenant_id selects a
   telegram/config/tenants.json row -- JSON_PATH/MCQ_JSON_PATH (each a LIST
   of files as of 2026-08-11, merged at load time -- see
   _load_and_merge_json_sources()) come from that row's exam_content.
3. Faculty bot tokens resolve via the env var named in their bots.json
   `bot_token_env` field -- put the real value in telegram/.env (gitignored).
   This script loads telegram/.env automatically.
4. Run: python exam_hub_bot.py
   Keep the terminal/laptop running for the bot to stay online. Or use
   telegram/tools/manage_bots.py to start every `active` bot in bots.json
   at once.
"""

import os
import re
import io
import sys
import json
import random
import logging

from pathlib import Path

from bs4 import BeautifulSoup
from xhtml2pdf import pisa
from dotenv import load_dotenv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402 -- must follow the sys.path.insert() above
import student_analytics  # noqa: E402 -- telegram/database/student_analytics.py, for the "I'm Done" today-summary (2026-08-13)
import report_flow  # noqa: E402 -- telegram/bots/report_flow.py, the 20-question milestone report pipeline (2026-08-11)
import profile_flow  # noqa: E402 -- telegram/bots/profile_flow.py, the "profile"/"change profile" identity flow (2026-08-11)
import mcq_issue_flow  # noqa: E402 -- telegram/bots/mcq_issue_flow.py, the "Report Issue in MCQ" flow (2026-08-13)
import wallet  # noqa: E402 -- telegram/database/wallet.py, the credit-wallet ledger (2026-08-15/16)
import identity  # noqa: E402 -- telegram/database/identity.py, auto-provisioned wallet identity (2026-08-16)
import test_flow  # noqa: E402 -- telegram/bots/test_flow.py, Test Mode / Pre-Designed Tests (2026-08-16)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]   # telegram/bots/exam_hub_bot.py -> repo root
TENANTS_PATH = REPO_ROOT / "telegram" / "config" / "tenants.json"
BOTS_PATH = REPO_ROOT / "telegram" / "config" / "bots.json"

load_dotenv(REPO_ROOT / "telegram" / ".env")   # secrets (faculty bot tokens) live here, gitignored


def load_bot(bot_id: str, bots_path: Path) -> dict:
    """Same contract as study_hub_bot.py's load_bot() -- see that file's
    docstring. Duplicated rather than imported so this script stays
    runnable standalone; the copies are small and kept identical."""
    data = json.loads(bots_path.read_text(encoding="utf-8"))
    for b in data["bots"]:
        if b["bot_id"] == bot_id:
            return b
    known = [b["bot_id"] for b in data["bots"]]
    raise SystemExit(f"Unknown BOT_ID '{bot_id}' -- no matching entry in {bots_path}. Known bot_ids: {known}")


def load_tenant(tenant_id: str, tenants_path: Path) -> dict:
    """Same contract as study_hub_bot.py's load_tenant() -- see that file's
    docstring."""
    data = json.loads(tenants_path.read_text(encoding="utf-8"))
    for t in data["tenants"]:
        if t["tenant_id"] == tenant_id:
            return t
    known = [t["tenant_id"] for t in data["tenants"]]
    raise SystemExit(
        f"Unknown tenant_id '{tenant_id}' (from bots.json's BOT_ID entry) -- no matching entry in {tenants_path}. "
        f"Known tenant_ids: {known}"
    )


BOT_ID = os.environ.get("BOT_ID") or os.environ.get("TENANT_ID", "1lavya-examhub")
BOT_CONFIG = load_bot(BOT_ID, BOTS_PATH)
TENANT_ID = BOT_CONFIG["tenant_id"]
TENANT = load_tenant(TENANT_ID, TENANTS_PATH)
BOT_TOKEN = os.environ.get(BOT_CONFIG.get("bot_token_env") or "", "") or None

def _resolve_content_paths(value):
    """exam_content.descriptive_json / .mcq_json may be a single relative
    path (the original shape, every tenant before 2026-08-11) or a list of
    them (added 2026-08-11 so a tenant's flagship auto-generated bank and
    a separately-owned, separately-regenerated subject batch -- e.g. CA
    Foundation Quantitative Aptitude, built by its own
    build_ca_foundation_quants_mcq_export.py -- can be merged at LOAD time
    without either file's own regeneration script ever clobbering the
    other). Returns a list of absolute path strings, or None if unset."""
    if not value:
        return None
    paths = value if isinstance(value, list) else [value]
    return [str(REPO_ROOT / p) for p in paths]


_exam_content = TENANT.get("exam_content", {})
JSON_PATH = _resolve_content_paths(_exam_content.get("descriptive_json"))
MCQ_JSON_PATH = _resolve_content_paths(_exam_content.get("mcq_json"))

# 1LAVYA's own flagship bots carry no branding footer; every white-label
# faculty bot gets a one-line "Powered by 1LAVYA" signature -- but ONLY on
# an actual answer (send_answer/handle_mcq_answer) or a PDF (send_pdf), per
# Pranav's 2026-08-10 instruction. Never on menus, a question being asked,
# or any other plain communication -- deliberately used at only 3 call
# sites in this file; don't add more without checking that instruction.
# Two variants because this bot mixes ParseMode.MARKDOWN (menus, in
# button_router) and ParseMode.HTML (question/answer text, via
# send_long_message) -- an HTML tag inside a MARKDOWN-parsed message (or
# vice versa) renders as literal text instead of formatting, so using the
# wrong one is a real, visible bug, not just a style nit.
_IS_FACULTY = TENANT.get("kind") == "faculty"
BRAND_FOOTER_MD = "\n\n_Powered by 1LAVYA_" if _IS_FACULTY else ""
BRAND_FOOTER_HTML = "\n\n<i>Powered by 1LAVYA</i>" if _IS_FACULTY else ""


def with_brand_md(text: str) -> str:
    return f"{text}{BRAND_FOOTER_MD}"


def with_brand_html(text: str) -> str:
    return f"{text}{BRAND_FOOTER_HTML}"


MIX_LABEL = "\U0001F500 Mix (All)"
ALL_CHAPTERS_LABEL = "\U0001F4DA All Chapters"

# 2026-08-12: content_scope is now consumed as a (course, level, subject)
# allow-list (SCOPE_TRIPLES, defined after the banks load below) rather
# than the old course->levels dict -- see "COURSE/LEVEL/SUBJECT
# RESOLUTION" further down for why, and CLAUDE.md/FIRST_PROMPT.md's
# 2026-08-12 entries for the flow-order decision this replaced (Mode is
# now asked FIRST, then Course/Level/Subject are derived from real
# content + this allow-list, never a hand-maintained "show every course
# even empty ones" list -- Pranav's explicit choice).

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DATABASE — activity / analytics logging
# ---------------------------------------------------------------------------
# Migrated 2026-08-10 onto the SHARED platform database (see
# telegram/database/db.py, schema.sql) -- this used to be its own separate
# per-tenant SQLite file (students/bot_sessions/descriptive_question_events/
# mcq_attempts). Same function names/signatures as before on purpose (every
# call site below is unchanged) -- only what's underneath them moved: the
# `students` table is now the ONE shared table every bot writes to (the
# 2026-08-09 "centralized account model" decision, which this bot's own
# students table had been the one holdout from); bot_sessions/
# descriptive_question_events/mcq_attempts are now exam_hub_sessions/
# exam_hub_descriptive_events/exam_hub_mcq_attempts, each with a bot_id
# column so every "exam" bot shares one table set (see schema.sql's own
# "shared table per bot kind" note). platform_db.execute_with_retry()
# replaces the old DB_LOCK -- retry-with-backoff is the right tool now that
# multiple bot PROCESSES (not just threads) write to the same file.
DB_CONN = platform_db.get_connection()
platform_db.init_schema(DB_CONN)


def db_upsert_student(user):
    platform_db.upsert_student(DB_CONN, user)
    platform_db.log_interaction(DB_CONN, BOT_ID, user.id, "start")


# ---------------------------------------------------------------------------
# WALLET -- billing rollout, 2026-08-16 (see
# telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md §0/§9 for the full
# decision trail). MUST be called AFTER db_upsert_student(user) -- both
# identity.ensure_wallet_identity() and wallet.grant_signup_bonus() below
# read/write the `students` row db_upsert_student() just created/updated.
# ---------------------------------------------------------------------------

def db_ensure_wallet(user):
    """Auto-provisions this student's wallet identity (their Telegram
    @username if valid/unclaimed, else a tg{id} placeholder -- see
    identity.py's own docstring for why) and grants the one-time signup
    bonus if they've never received one before (platform-wide -- the grant
    is keyed by username, not bot_id, so whichever 1LAVYA bot a student
    touches first is the one that grants it). Returns a welcome-bonus
    message to show the student, or None if they'd already been granted
    one (i.e. this isn't their genuine first-ever interaction) -- callers
    append this to whatever they're already about to send, never send it
    as a separate message."""
    username, _ = identity.ensure_wallet_identity(DB_CONN, user)
    _, already_granted = wallet.grant_signup_bonus(DB_CONN, username, "platform")
    if already_granted:
        return None
    return wallet.build_signup_grant_message()


def _out_of_balance_text() -> str:
    """Shown instead of a question when a student's balance can't cover
    it. Deliberately never mentions money/rupees (Pranav's explicit rule,
    2026-08-15/16) -- and deliberately doesn't promise a working recharge
    flow yet, since wallet_flow.py (the actual top-up conversation) isn't
    built as of this writing -- see roadmap §0.2. Update this once it is."""
    return (
        "\U0001F6D1 You've used up your free access for now. "
        "Recharging your balance is coming very soon — check back shortly, "
        "or type <code>profile</code> to see your account."
    )


def db_start_session(user_id) -> int:
    now = platform_db.now()
    platform_db.execute_with_retry(
        DB_CONN,
        "INSERT INTO exam_hub_sessions (bot_id, telegram_user_id, started_at) VALUES (?,?,?)",
        (BOT_ID, user_id, now),
    )
    return DB_CONN.execute("SELECT last_insert_rowid()").fetchone()[0]


def db_update_session(session_id, **fields):
    if not session_id or not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [session_id]
    platform_db.execute_with_retry(DB_CONN, f"UPDATE exam_hub_sessions SET {cols} WHERE session_id=?", values)


def db_log_descriptive_shown(user_id, session_id, q, course, level, exam_type, year,
                              chapter_slug, chapter_label) -> int:
    now = platform_db.now()
    platform_db.execute_with_retry(
        DB_CONN,
        """INSERT INTO exam_hub_descriptive_events
           (bot_id, telegram_user_id, session_id, book_id, course, level, exam_type, year,
            chapter_slug, chapter_label, qno_text, marks_text, shown_at, content_owner, human_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (BOT_ID, user_id, session_id, q.get("book_id"), course, level, exam_type, year,
         chapter_slug, chapter_label, q.get("qno_text"), q.get("marks_text"), now,
         q.get("_content_owner"), q.get("human_id")),
    )
    # Capture the new row's id BEFORE log_interaction()'s own INSERT runs --
    # last_insert_rowid() is connection-global, not table-specific, so
    # calling it after a second, unrelated insert returns THAT row's id
    # instead (a real bug caught by testing, not just inspection).
    event_id = DB_CONN.execute("SELECT last_insert_rowid()").fetchone()[0]
    platform_db.log_interaction(DB_CONN, BOT_ID, user_id, "descriptive_question_shown")
    return event_id


def db_log_descriptive_answer_shown(event_id):
    if not event_id:
        return
    platform_db.execute_with_retry(
        DB_CONN, "UPDATE exam_hub_descriptive_events SET answer_shown_at=? WHERE event_id=?",
        (platform_db.now(), event_id),
    )


def db_log_descriptive_pdf(event_id):
    if not event_id:
        return
    platform_db.execute_with_retry(
        DB_CONN, "UPDATE exam_hub_descriptive_events SET pdf_requested_at=? WHERE event_id=?",
        (platform_db.now(), event_id),
    )


def db_log_mcq_shown(user_id, session_id, q, course, level) -> int:
    now = platform_db.now()
    platform_db.execute_with_retry(
        DB_CONN,
        """INSERT INTO exam_hub_mcq_attempts
           (bot_id, telegram_user_id, session_id, mcq_id, course, level, exam_type, year,
            chapter_slug, chapter_label, qno_text, marks, difficulty, correct_option, shown_at,
            content_owner, human_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (BOT_ID, user_id, session_id, q.get("mcq_id"), course, level, q.get("exam_type"), q.get("year"),
         q.get("chapter_slug"), q.get("chapter_label"), q.get("qno_text"), q.get("marks"),
         q.get("difficulty"), q.get("correct_option"), now,
         q.get("_content_owner"), q.get("human_id")),
    )
    # Same "capture before log_interaction's own insert" reasoning as
    # db_log_descriptive_shown above.
    attempt_id = DB_CONN.execute("SELECT last_insert_rowid()").fetchone()[0]
    platform_db.log_interaction(DB_CONN, BOT_ID, user_id, "mcq_shown")
    return attempt_id


def db_log_mcq_answered(attempt_id, selected_option, is_correct):
    if not attempt_id:
        return
    platform_db.execute_with_retry(
        DB_CONN, "UPDATE exam_hub_mcq_attempts SET selected_option=?, is_correct=?, answered_at=? WHERE attempt_id=?",
        (selected_option, 1 if is_correct else 0, platform_db.now(), attempt_id),
    )


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------
_FACULTY_PATH_RE = re.compile(r"[/\\]faculty[/\\]([^/\\]+)[/\\]")


def _infer_content_owner(path: str) -> str:
    """Which tenant a content file's questions were sourced/generated by --
    added 2026-08-13 per Pranav's standing rule ("everything becomes part
    of the flagship bot, there is just the key tagging that will identify
    actually sourced by and generated by"). Inferred purely from the
    file's own path convention -- no per-record field needed, no schema
    change to any content file: anything under a `.../faculty/<tenant_id>/`
    folder is that tenant's own sourced content; everything else (the
    flagship's own auto-generated/ingested batches) is "1lavya". Matches
    the SAME convention this platform already documented (but never wired
    up) in schema.sql's own "content-ownership tagging" comment."""
    m = _FACULTY_PATH_RE.search(str(path))
    return m.group(1) if m else "1lavya"


def _load_and_merge_json_sources(json_paths, id_field, kind_label, logger):
    """Shared by QuestionBank/McqBank below: read every path in json_paths
    (already a list, or None), concatenate their records, and warn (never
    crash) if the same id_field value shows up in more than one source --
    get_by_book_id()/get_by_id() are first-match-wins, so a real collision
    would silently shadow one source's record with another's rather than
    erroring, exactly the bug class validate_content_json.py's own
    duplicate-id check exists to catch on a single file; this is that same
    check applied across merged files. Also tags every record with
    `_content_owner` (see _infer_content_owner() above) -- purely
    informational provenance, never a visibility/access filter (that's
    still SCOPE_TRIPLES/content_scope's job, unaffected by this)."""
    if not json_paths:
        logger.warning(f"{kind_label}: no content configured for this tenant -- starting empty.")
        return []
    combined = []
    seen_ids = set()
    for path in json_paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "questions" in data:
            data = data["questions"]
        dupes = {r.get(id_field) for r in data if r.get(id_field) in seen_ids}
        if dupes:
            logger.warning(f"{kind_label}: {len(dupes)} {id_field}(s) from {path} collide with an "
                            f"earlier source and will be shadowed: {sorted(dupes)}")
        seen_ids.update(r.get(id_field) for r in data)
        owner = _infer_content_owner(path)
        for r in data:
            r["_content_owner"] = owner
        combined.extend(data)
        logger.info(f"{kind_label}: loaded {len(data)} record(s) from {path}")
    return combined


# ---------------------------------------------------------------------------
# COURSE/LEVEL/SUBJECT RESOLUTION -- added 2026-08-12
# ---------------------------------------------------------------------------
# Every question record resolves to a real (course, level, subject) triple,
# derived from the platform's own course_catalog DB table (see
# database/schema.sql) via human_id -- never hand-typed per content file.
# This replaced two real gaps found the same day: (1) 2 of 3 CA Foundation
# content files (Accounting, Business Economics) never had an explicit
# "subject" field at all -- only Quantitative Aptitude did; (2) the
# flagship's descriptive bank (book_questions_extracted.json) has no
# course/level field on ANY record (its schema predates multi-course
# support) and used to rely on a "no course/level field always matches"
# hack -- correct only because this platform had exactly one course/level/
# subject in scope when that was written, and silently wrong the moment a
# second one existed. human_id (already on every MCQ record and most
# descriptive records) encodes course/level_num/paper_no
# (e.g. "CA_L1_P04_C1_U1_00001") -- joining that back to course_catalog is
# the SAME mechanism the platform already uses for chapter/unit naming
# (see COURSE-CATALOG.md), just applied one level up. Validated 2026-08-12
# against every real record across every tenant's content: 0 unresolved
# ("Unknown") records.
_HUMAN_ID_RE = re.compile(r"^([A-Z]+)_L(\d+)_P(\d+[A-Z]?)_C(\d+)_U(\d+)_(\d+)$")


def _build_catalog_lookup(conn) -> dict:
    """(course, level_num, paper_no) -> (level_name, subject), from every
    distinct row in course_catalog. Built once at bot startup -- the table
    is small (~1000 rows) and static within a process's lifetime."""
    rows = conn.execute(
        "SELECT DISTINCT course, level_num, paper_no, level, subject FROM course_catalog"
    ).fetchall()
    return {(course, str(level_num), paper_no): (level, subject) for course, level_num, paper_no, level, subject in rows}


def _build_chapter_catalog_lookup(conn) -> dict:
    """(course, level_num, paper_no, chapter_no, unit_no) -> a real chapter/
    unit name (short form preferred), for the Chapter-label disambiguation
    pass below."""
    rows = conn.execute(
        "SELECT course, level_num, paper_no, chapter_no, unit_no, chapter_name_short, chapter_name FROM course_catalog"
    ).fetchall()
    lookup = {}
    for course, level_num, paper_no, chapter_no, unit_no, name_short, name in rows:
        lookup[(course, str(level_num), paper_no, str(chapter_no), str(unit_no))] = name_short or name
    return lookup


_CATALOG_LOOKUP = _build_catalog_lookup(DB_CONN)
_CHAPTER_CATALOG_LOOKUP = _build_chapter_catalog_lookup(DB_CONN)


def _resolve_course_level_subject(q: dict) -> tuple:
    """Returns (course, level, subject) for a question record -- explicit
    fields win where present; anything missing/None is derived from
    human_id via _CATALOG_LOOKUP. Falls back to "Unknown" only if
    human_id is missing/unparseable or the catalog has no matching row (a
    real content-authoring gap -- logged loudly, never silently guessed
    past, same discipline as every other null-handling fix in this file)."""
    course, level, subject = q.get("course"), q.get("level"), q.get("subject")
    if course and level and subject:
        return course, level, subject

    m = _HUMAN_ID_RE.match(q.get("human_id") or "")
    if not m:
        return course or "Unknown", level or "Unknown", subject or "Unknown"

    hid_course, level_num, paper_no = m.group(1), m.group(2), m.group(3).lstrip("0") or "0"
    looked_up = _CATALOG_LOOKUP.get((hid_course, level_num, paper_no))
    if not looked_up:
        logger.warning(
            f"No course_catalog match for human_id {q.get('human_id')!r} "
            f"(course={hid_course}, level_num={level_num}, paper_no={paper_no}) -- "
            f"this record's course/level/subject will show as 'Unknown'."
        )
        return course or hid_course, level or "Unknown", subject or "Unknown"

    catalog_level, catalog_subject = looked_up
    return course or hid_course, level or catalog_level, subject or catalog_subject


def _disambiguate_chapter_labels(questions: list) -> None:
    """Second resolution pass, added 2026-08-13 -- runs AFTER course/level/
    subject are resolved. Within each (course, level, subject) group, if
    the same `chapter_label` string is shared by more than one distinct
    `chapter_slug`, the Chapter picker shows identical-looking buttons
    that actually lead to different question sets (confirmed live: CA
    Foundation Accounting/Business Economics were ingested with a bare
    "Chapt N"/"Chapt. N" label carrying no Unit distinction -- e.g.
    "Chapt 1" shared by 7 genuinely different units, "Chapt 7" by 4 --
    exactly Pranav's report, "many chapters are simply coming repeated").

    Resolves ONLY the colliding groups -- a label that's already unique
    (the flagship's "AS 11: ..." style labels, CMA's real per-chapter Act
    names) is never touched, so already-good labels don't get a
    redundant/worse suffix. Disambiguates by appending the real chapter/
    unit name from course_catalog (via human_id ->
    (course, level_num, paper_no, chapter_no, unit_no), the SAME join
    mechanism _resolve_course_level_subject uses) -- falling back to a
    title-cased chapter_slug if even that lookup fails, so a label is
    NEVER left silently ambiguous either way.

    Sets q["_chapter_label"] on every record -- QuestionBank/McqBank's
    chapters() methods must read that, never the raw `chapter_label`
    field, from here on."""
    groups = {}  # (course, level, subject, raw_label) -> set of chapter_slug
    for q in questions:
        raw_label = q.get("chapter_label") or (q.get("chapter_slug") or "unknown")
        key = (q["_course"], q["_level"], q["_subject"], raw_label)
        groups.setdefault(key, set()).add(q.get("chapter_slug") or "unknown")

    ambiguous_keys = {k for k, slugs in groups.items() if len(slugs) > 1}

    for q in questions:
        raw_label = q.get("chapter_label") or (q.get("chapter_slug") or "unknown")
        key = (q["_course"], q["_level"], q["_subject"], raw_label)
        if key not in ambiguous_keys:
            q["_chapter_label"] = raw_label
            continue

        m = _HUMAN_ID_RE.match(q.get("human_id") or "")
        catalog_name = None
        if m:
            hid_course, level_num, paper_no = m.group(1), m.group(2), m.group(3).lstrip("0") or "0"
            chapter_no, unit_no = m.group(4), m.group(5)
            catalog_name = _CHAPTER_CATALOG_LOOKUP.get((hid_course, level_num, paper_no, chapter_no, unit_no))
        if not catalog_name:
            catalog_name = (q.get("chapter_slug") or "unknown").replace("-", " ").title()
        q["_chapter_label"] = f"{raw_label}: {catalog_name}"


class QuestionBank:
    """Descriptive questions (book_questions_extracted.json)."""

    def __init__(self, json_paths):
        self.json_paths = json_paths
        self.questions = []
        self.load()

    def load(self):
        self.questions = _load_and_merge_json_sources(self.json_paths, "book_id", "QuestionBank", logger)
        for q in self.questions:
            # An explicit "exam_type"/"year" field (added 2026-08-10 for
            # faculty practice content) always wins; pattern-detection from
            # src_text is the original fallback for records that don't have
            # those fields (the flagship's real MTP/RTP/PYQ data).
            q["_exam_type"] = q.get("exam_type") or self._detect_exam_type(q.get("src_text", ""))
            q["_year"] = q.get("year") or self._detect_year(q.get("src_text", ""))
            q["_course"], q["_level"], q["_subject"] = _resolve_course_level_subject(q)
        _disambiguate_chapter_labels(self.questions)

    @staticmethod
    def _detect_exam_type(src_text: str) -> str:
        src = (src_text or "").upper()
        if "MTP" in src:
            return "MTP"
        if "RTP" in src:
            return "RTP"
        if "PYQ" in src or "PAST" in src:
            return "PYQ"
        if "PRACTICE" in src:
            return "PRACTICE"
        return "OTHER"

    @staticmethod
    def _detect_year(src_text: str) -> str:
        m = re.search(r"(20\d{2})", src_text or "")
        return m.group(1) if m else "Unknown"

    def courses(self):
        return sorted({q["_course"] for q in self.questions})

    def levels(self, course):
        return sorted({q["_level"] for q in self.questions if q["_course"] == course})

    def subjects(self, course, level):
        return sorted({q["_subject"] for q in self.questions if q["_course"] == course and q["_level"] == level})

    def exam_types(self, course, level, subject):
        return sorted({q["_exam_type"] for q in self._by_scope(course, level, subject)})

    def years(self, exam_type, course, level, subject):
        pool = self._by_scope(course, level, subject)
        subset = pool if exam_type == "MIX" else [q for q in pool if q["_exam_type"] == exam_type]
        return sorted({q["_year"] for q in subset})

    def chapters(self, exam_type, year, course, level, subject):
        subset = self._filter(exam_type, year, course, level, subject)
        seen = {}
        for q in subset:
            # `.get(key, default)` only substitutes when the key is ABSENT --
            # a record with an explicit `"chapter_slug": null` (real, seen in
            # faculty content) still returns None, not the default. `or` is
            # what's actually needed here (see McqBank's twin methods below
            # for the concrete crash this exact mistake caused 2026-08-10).
            # `_chapter_label` (not the raw `chapter_label` field) -- see
            # _disambiguate_chapter_labels()'s own docstring for why.
            slug = q.get("chapter_slug") or "unknown"
            label = q["_chapter_label"]
            seen[slug] = label
        return sorted(seen.items(), key=lambda kv: kv[1])

    def _by_scope(self, course, level, subject):
        """course/level/subject are always resolved real values by this
        point in the flow (Mode -> Course -> Level -> Subject is fully
        settled, auto-skipped or explicitly chosen, before any exam-type/
        year/chapter query ever runs) -- strict equality, no None-means-
        no-filter fallback needed (unlike the pre-2026-08-12 version)."""
        return [q for q in self.questions if q["_course"] == course and q["_level"] == level and q["_subject"] == subject]

    def _filter(self, exam_type, year, course, level, subject):
        subset = self._by_scope(course, level, subject)
        if exam_type != "MIX":
            subset = [q for q in subset if q["_exam_type"] == exam_type]
        if year != "MIX":
            subset = [q for q in subset if q["_year"] == year]
        return subset

    def filter_questions(self, exam_type, year, chapter_slug, course, level, subject):
        subset = self._filter(exam_type, year, course, level, subject)
        if chapter_slug != "ALL":
            # Normalized the same way chapters() above synthesizes "unknown"
            # for a null chapter_slug -- see McqBank's twin fix, same date,
            # same reasoning.
            subset = [q for q in subset if (q.get("chapter_slug") or "unknown") == chapter_slug]
        return subset

    def get_by_book_id(self, book_id):
        for q in self.questions:
            if q.get("book_id") == book_id:
                return q
        return None


class McqBank:
    """MCQ questions. May be loaded from more than one source file (see
    _resolve_content_paths()/_load_and_merge_json_sources() above) -- e.g.
    the flagship's auto-generated CA-Inter bank
    (telegram/tools/build_exam_bot_mcq_export.py) plus a separately-owned
    subject batch like CA Foundation Quantitative Aptitude
    (telegram/tools/build_ca_foundation_quants_mcq_export.py), merged here
    at load time so neither file's own regeneration script ever clobbers
    the other. exam_type/year are already explicit top-level fields on
    every record (unlike the descriptive bank), no pattern-detection
    needed."""

    def __init__(self, json_paths):
        self.json_paths = json_paths
        self.questions = []
        self.load()

    def load(self):
        self.questions = _load_and_merge_json_sources(self.json_paths, "mcq_id", "McqBank", logger)
        for q in self.questions:
            q["_course"], q["_level"], q["_subject"] = _resolve_course_level_subject(q)
        _disambiguate_chapter_labels(self.questions)

    def courses(self):
        return sorted({q["_course"] for q in self.questions})

    def levels(self, course):
        return sorted({q["_level"] for q in self.questions if q["_course"] == course})

    def subjects(self, course, level):
        return sorted({q["_subject"] for q in self.questions if q["_course"] == course and q["_level"] == level})

    def _by_scope(self, course, level, subject):
        return [q for q in self.questions if q["_course"] == course and q["_level"] == level and q["_subject"] == subject]

    def exam_types(self, course, level, subject):
        # BUG FIXED 2026-08-10: `.get("exam_type", "OTHER")` only substitutes
        # "OTHER" when the key is missing entirely -- a record with an
        # EXPLICIT `"year": null` (real, present in 375 merged CMA Foundation
        # records) still returns None from `.get("year", "Unknown")` below,
        # since the key IS present. That None became an InlineKeyboardButton's
        # `text`, which Telegram's API rejects outright ("Can't parse
        # inlinekeyboardbutton: can't find field text") -- the edit_message_text
        # call throws, the menu never updates, and to a student it looks
        # exactly like "pressing the button does nothing." `or` (not
        # `.get(key, default)`) is the fix everywhere a field might be
        # explicitly null, not just absent -- applied to every sibling method
        # below too, defensively, since more faculty JSON will have the same
        # heterogeneity going forward.
        return sorted({q.get("exam_type") or "OTHER" for q in self._by_scope(course, level, subject)})

    def years(self, exam_type, course, level, subject):
        pool = self._by_scope(course, level, subject)
        subset = pool if exam_type == "MIX" else [q for q in pool if q.get("exam_type") == exam_type]
        return sorted({q.get("year") or "Unknown" for q in subset})

    def chapters(self, exam_type, year, course, level, subject):
        subset = self._filter(exam_type, year, course, level, subject)
        seen = {}
        for q in subset:
            # `_chapter_label` (not the raw `chapter_label` field) -- see
            # _disambiguate_chapter_labels()'s own docstring for why.
            slug = q.get("chapter_slug") or "unknown"
            label = q["_chapter_label"]
            seen[slug] = label
        return sorted(seen.items(), key=lambda kv: kv[1])

    def _filter(self, exam_type, year, course, level, subject):
        # Must normalize the SAME way years()/exam_types()/chapters() above
        # do (`or`, not raw `.get()`) -- otherwise a student picking the
        # "Unknown"/"OTHER" bucket those methods synthesized for a
        # null-valued record would match zero records here (comparing the
        # synthesized label against the raw None never matches), silently
        # showing an empty chapter/question list instead of the bug above's
        # loud crash. Same root cause, different failure mode -- fixed
        # together 2026-08-10.
        subset = self._by_scope(course, level, subject)
        if exam_type != "MIX":
            subset = [q for q in subset if (q.get("exam_type") or "OTHER") == exam_type]
        if year != "MIX":
            subset = [q for q in subset if (q.get("year") or "Unknown") == year]
        return subset

    def filter_questions(self, exam_type, year, chapter_slug, course, level, subject):
        subset = self._filter(exam_type, year, course, level, subject)
        if chapter_slug != "ALL":
            subset = [q for q in subset if (q.get("chapter_slug") or "unknown") == chapter_slug]
        return subset

    def get_by_id(self, mcq_id):
        for q in self.questions:
            if q.get("mcq_id") == mcq_id:
                return q
        return None


bank = QuestionBank(JSON_PATH)
mcq_bank = McqBank(MCQ_JSON_PATH)


def _mode_bank(mode):
    return bank if mode == "descriptive" else mcq_bank


# tenants.json's content_scope, consumed as a (course, level, subject)
# allow-list. None = unrestricted (the flagship's "ALL" scope) -- a scoped
# (faculty) tenant's bot never shows a course/level/subject outside this
# set, even if the underlying merged JSON technically contains it (e.g. a
# faculty's exam_content currently pointing at a shared flagship file).
if TENANT["content_scope"] == "ALL":
    SCOPE_TRIPLES = None
else:
    SCOPE_TRIPLES = {(s["course"], s["level"], s["subject"]) for s in TENANT["content_scope"]}


def _scope_allows_course(course):
    return SCOPE_TRIPLES is None or any(c == course for c, _l, _s in SCOPE_TRIPLES)


def _scope_allows_level(course, level):
    return SCOPE_TRIPLES is None or any(c == course and l == level for c, l, _s in SCOPE_TRIPLES)


def _scope_allows_subject(course, level, subject):
    return SCOPE_TRIPLES is None or (course, level, subject) in SCOPE_TRIPLES


def _available_modes():
    """Which of Descriptive/MCQ have ANY real, in-scope content for this
    tenant -- computed from real data + SCOPE_TRIPLES, never hand-
    maintained (see this file's 2026-08-12 flow rewrite)."""
    modes = []
    for m in ("descriptive", "mcq"):
        courses = [c for c in _mode_bank(m).courses() if _scope_allows_course(c)]
        if courses:
            modes.append(m)
    return modes


logger.info(
    f"Tenant '{TENANT_ID}': available modes = {_available_modes()}, "
    f"descriptive courses = {[c for c in bank.courses() if _scope_allows_course(c)]}, "
    f"mcq courses = {[c for c in mcq_bank.courses() if _scope_allows_course(c)]}"
)

# ---------------------------------------------------------------------------
# HTML HELPERS
# ---------------------------------------------------------------------------
TELEGRAM_ALLOWED_TAGS = {"b", "strong", "i", "em", "u", "s", "code", "pre", "a"}


def html_to_telegram_text(html: str) -> str:
    """Convert arbitrary question/answer HTML into Telegram-safe HTML text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["p", "div", "br", "li"]):
        tag.insert_after("\n")

    for tag in soup.find_all(True):
        if tag.name not in TELEGRAM_ALLOWED_TAGS:
            tag.unwrap()

    text = str(soup)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

# Telegram's hard cap is 4096 chars; keep a safety margin below it
TELEGRAM_MESSAGE_LIMIT = 4000


def split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list:
    """Split long text into chunks Telegram will accept, preferring to break
    on paragraph/line boundaries so we don't cut in the middle of a word
    (or, as much as possible, in the middle of an HTML tag)."""
    if len(text) <= limit:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > limit:
        split_at = remaining.rfind("\n\n", 0, limit)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at == -1 or split_at == 0:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


async def send_long_message(context, chat_id, text, reply_markup=None):
    """Send text as one message, or split across several if it's over
    Telegram's limit. Only the LAST chunk gets the reply_markup (buttons).
    If a chunk's HTML gets malformed by the split, fall back to plain text
    rather than crashing."""
    chunks = split_message(text)
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        markup = reply_markup if is_last else None
        try:
            await context.bot.send_message(
                chat_id=chat_id, text=chunk, parse_mode=ParseMode.HTML, reply_markup=markup
            )
        except Exception as e:
            logger.warning(f"HTML parse failed on chunk {i}, retrying as plain text: {e}")
            await context.bot.send_message(chat_id=chat_id, text=chunk, reply_markup=markup)


def prepare_text_for_pdf(html: str) -> str:
    """
    xhtml2pdf's underlying PDF engine (reportlab) has a confirmed bug: the ₹
    (Rupee) symbol fails to render even with an embedded Unicode font that
    contains the glyph. Substitute ₹ with "Rs." for PDF output only.
    """
    if not html:
        return html
    return html.replace("\u20b9", "Rs. ")


def html_to_pdf_bytes(title: str, meta_lines: list, question_html: str, answer_html: str) -> bytes:
    """Render question+answer HTML into a simple styled PDF, return raw bytes."""

    question_html = prepare_text_for_pdf(question_html)
    answer_html = prepare_text_for_pdf(answer_html)
    meta_lines = [prepare_text_for_pdf(m) for m in meta_lines]

    meta_html = "".join(f"<p style='color:#555;font-size:11px;margin:2px 0;'>{m}</p>" for m in meta_lines)
    full_html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Helvetica, Arial, sans-serif; font-size: 13px; color: #222; }}
        h2 {{ color: #1F4E78; margin-bottom: 4px; }}
        .section-title {{ color: #1F4E78; font-weight: bold; margin-top: 18px; border-bottom: 1px solid #ccc; }}
    </style>
    </head>
    <body>
        <h2>{title}</h2>
        {meta_html}
        <div class="section-title">Question</div>
        {question_html or ""}
        <div class="section-title">Answer</div>
        {answer_html or ""}
    </body>
    </html>
    """
    buffer = io.BytesIO()
    pisa.CreatePDF(full_html, dest=buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# MENU BUILDERS
# ---------------------------------------------------------------------------
# No brand footer on any menu/question screen below -- per Pranav's
# 2026-08-10 instruction, "Powered by 1LAVYA" only appears when delivering
# an answer (send_answer/handle_mcq_answer) or a PDF (send_pdf). Menus,
# questions being asked, and other plain communication stay unbranded.
def build_mode_menu(modes):
    keyboard = []
    if "descriptive" in modes:
        keyboard.append([InlineKeyboardButton("\U0001F4DD Descriptive", callback_data="mode:descriptive")])
    if "mcq" in modes:
        keyboard.append([InlineKeyboardButton("✅ MCQ", callback_data="mode:mcq")])
    opening = TENANT.get("welcome_message") or "*Welcome to 1Lavya Exam Hub* \U0001F4DD"
    text = f"{opening}\n\nWhat would you like to practice?"
    return text, InlineKeyboardMarkup(keyboard)


def _label(mode):
    return "Descriptive" if mode == "descriptive" else "MCQ"


def build_course_menu(mode, courses):
    keyboard = [[InlineKeyboardButton(c, callback_data=f"course:{c}")] for c in courses]
    return f"Mode: *{_label(mode)}*\nSelect your *Course*:", InlineKeyboardMarkup(keyboard)


def build_level_menu(mode, course, levels):
    keyboard = [[InlineKeyboardButton(lvl, callback_data=f"level:{lvl}")] for lvl in levels]
    return f"Mode: *{_label(mode)}* | Course: *{course}*\nSelect your *Level*:", InlineKeyboardMarkup(keyboard)


def build_subject_menu(mode, course, level, subjects):
    # Index-based callback_data, not the literal subject name -- subject
    # names (e.g. "Fundamentals of Business Laws and Business
    # Communication") can exceed Telegram's 64-byte callback_data limit on
    # their own, the exact bug class fixed for Chapter buttons earlier
    # today (see the "year" action's own comment). Resolved back via
    # context.user_data["subject_options"], stashed by resolve_entry().
    keyboard = [[InlineKeyboardButton(s, callback_data=f"subject:{i}")] for i, s in enumerate(subjects)]
    text = f"Mode: *{_label(mode)}* | Course: *{course}* | Level: *{level}*\nSelect your *Subject*:"
    return text, InlineKeyboardMarkup(keyboard)


def build_type_menu(mode, course, level, subject):
    exam_types = _mode_bank(mode).exam_types(course, level, subject)
    keyboard = [[InlineKeyboardButton(et, callback_data=f"type:{et}")] for et in exam_types]
    keyboard.append([InlineKeyboardButton(MIX_LABEL, callback_data="type:MIX")])
    text = (
        f"Mode: *{_label(mode)}* | Course: *{course}* | Level: *{level}* | Subject: *{subject}*\n"
        f"Select *Exam Type*:"
    )
    return text, InlineKeyboardMarkup(keyboard)


def build_no_content_gate(mode=None, course=None, level=None):
    parts = []
    if mode:
        parts.append(f"Mode: *{_label(mode)}*")
    if course:
        parts.append(f"Course: *{course}*")
    if level:
        parts.append(f"Level: *{level}*")
    header = (" | ".join(parts) + "\n\n") if parts else ""
    keyboard = [[InlineKeyboardButton("\U0001F519 Start Over", callback_data="restart")]]
    text = f"{header}\U0001F6A7 No questions available for this selection yet. We will shortly have more!"
    return text, InlineKeyboardMarkup(keyboard)


def resolve_entry(context, mode=None, course=None, level=None, subject=None):
    """Central cascade for the Exam Hub flow (rewritten 2026-08-12, Mode-
    first per Pranav's explicit choice): Mode -> Course -> Level ->
    Subject -> Exam Type. Given however much of the first 4 is already
    decided, returns (text, markup, updates) for the NEXT screen --
    auto-skipping any step that has exactly one real, in-scope option, so
    a narrowly-scoped faculty bot (or any step that only ever has one
    answer) never shows a picker with nothing to pick. Course/Level/
    Subject are derived from REAL content (never a hand-maintained "show
    every course, even empty ones, gate later" list) -- the explicit UX
    choice behind this rewrite: a student never taps into a dead end.

    `updates` are the additional context.user_data keys this call
    resolved by auto-skip; callers merge them in (and mirror into
    db_update_session) themselves. Reused for BOTH the initial /start
    screen and every mid-flow button tap (mode/course/level/subject
    actions in button_router) -- one cascade, not the pre-2026-08-12
    code's two separately-maintained auto-skip implementations (entry
    screen vs. button_router's "course" branch)."""
    updates = {}

    if mode is None:
        modes = _available_modes()
        if not modes:
            return (*build_no_content_gate(), updates)
        if len(modes) > 1:
            return (*build_mode_menu(modes), updates)
        mode = modes[0]
        updates["mode"] = mode

    bank_obj = _mode_bank(mode)

    if course is None:
        courses = [c for c in bank_obj.courses() if _scope_allows_course(c)]
        if not courses:
            return (*build_no_content_gate(mode), updates)
        if len(courses) > 1:
            return (*build_course_menu(mode, courses), updates)
        course = courses[0]
        updates["course"] = course

    if level is None:
        levels = [lv for lv in bank_obj.levels(course) if _scope_allows_level(course, lv)]
        if not levels:
            return (*build_no_content_gate(mode, course), updates)
        if len(levels) > 1:
            return (*build_level_menu(mode, course, levels), updates)
        level = levels[0]
        updates["level"] = level

    if subject is None:
        subjects = [s for s in bank_obj.subjects(course, level) if _scope_allows_subject(course, level, s)]
        if not subjects:
            return (*build_no_content_gate(mode, course, level), updates)
        if len(subjects) > 1:
            context.user_data["subject_options"] = subjects
            return (*build_subject_menu(mode, course, level, subjects), updates)
        subject = subjects[0]
        updates["subject"] = subject

    return (*build_type_menu(mode, course, level, subject), updates)


# ---------------------------------------------------------------------------
# HANDLERS
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    db_upsert_student(user)
    welcome_bonus_text = db_ensure_wallet(user)
    context.user_data["session_id"] = db_start_session(user.id)

    text, markup, updates = resolve_entry(context)
    if updates:
        context.user_data.update(updates)
        db_update_session(context.user_data["session_id"], **updates)
    if welcome_bonus_text:
        # Sent as its own message, ahead of the menu, so it's never lost in
        # (or made to look like part of) the Markdown-formatted menu text.
        await update.message.reply_text(welcome_bonus_text, parse_mode=ParseMode.HTML)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


def _session_expired_markup():
    return InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F519 Start Over", callback_data="restart")]])


async def _require_state(query, context, *keys):
    """Read back a set of prior-step selections from context.user_data, or
    edit the message with a "session expired" prompt and return None if any
    is missing. context.user_data is in-memory only (no persistence
    backend configured) -- it doesn't survive a bot restart, but a stale
    inline keyboard from before the restart can still be tapped afterward.
    BUG FIXED 2026-08-12: the "year"/"chapter" actions used to read
    context.user_data["exam_type"] (and ["year"]) directly -- a KeyError on
    a stale tap raised an unhandled exception AFTER query.answer() already
    fired, so the student saw the loading spinner clear and then nothing:
    no error, no menu update, indistinguishable from the bot being broken.
    Confirmed live in capranav-exam.log/csarunchouhan.log
    ("KeyError: 'exam_type'"). Every handler that reads a prior step's
    value back out of user_data should go through this instead of a raw
    dict index."""
    missing = [k for k in keys if context.user_data.get(k) is None]
    if missing:
        await query.edit_message_text(
            "⚠️ Your session has expired (the bot may have restarted). Please start over.",
            reply_markup=_session_expired_markup(),
        )
        return None
    return {k: context.user_data[k] for k in keys}


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    action = data.split(":")[0]
    session_id = context.user_data.get("session_id")

    if action == "restart":
        context.user_data.clear()
        user = query.from_user
        db_upsert_student(user)
        welcome_bonus_text = db_ensure_wallet(user)  # no-op/None for a real restart; covers the rare case this is somehow their first-ever interaction
        context.user_data["session_id"] = db_start_session(user.id)
        text, markup, updates = resolve_entry(context)
        if updates:
            context.user_data.update(updates)
            db_update_session(context.user_data["session_id"], **updates)
        if welcome_bonus_text:
            await context.bot.send_message(chat_id=query.message.chat_id, text=welcome_bonus_text, parse_mode=ParseMode.HTML)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
        return

    if action == "mode":
        mode = data.split(":", 1)[1]  # "descriptive" or "mcq"
        text, markup, updates = resolve_entry(context, mode=mode)
        context.user_data["mode"] = mode
        context.user_data.update(updates)
        db_update_session(session_id, mode=mode, **updates)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    elif action == "course":
        course = data.split(":", 1)[1]
        state = await _require_state(query, context, "mode")
        if state is None:
            return
        text, markup, updates = resolve_entry(context, mode=state["mode"], course=course)
        context.user_data["course"] = course
        context.user_data.update(updates)
        db_update_session(session_id, course=course, **updates)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    elif action == "level":
        level = data.split(":", 1)[1]
        state = await _require_state(query, context, "mode", "course")
        if state is None:
            return
        text, markup, updates = resolve_entry(context, mode=state["mode"], course=state["course"], level=level)
        context.user_data["level"] = level
        context.user_data.update(updates)
        db_update_session(session_id, level=level, **updates)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    elif action == "subject":
        raw = data.split(":", 1)[1]
        state = await _require_state(query, context, "mode", "course", "level")
        if state is None:
            return
        options = context.user_data.get("subject_options") or []
        try:
            subject = options[int(raw)]
        except (ValueError, IndexError):
            await query.edit_message_text(
                "⚠️ Your session has expired (the bot may have restarted). Please start over.",
                reply_markup=_session_expired_markup(),
            )
            return
        text, markup, _updates = resolve_entry(
            context, mode=state["mode"], course=state["course"], level=state["level"], subject=subject
        )
        context.user_data["subject"] = subject
        db_update_session(session_id, subject=subject)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    elif action == "type":
        exam_type = data.split(":", 1)[1]
        context.user_data["exam_type"] = exam_type
        state = await _require_state(query, context, "mode", "course", "level", "subject")
        if state is None:
            return
        mode, course, level, subject = state["mode"], state["course"], state["level"], state["subject"]
        years = _mode_bank(mode).years(exam_type, course, level, subject)
        keyboard = [[InlineKeyboardButton(y, callback_data=f"year:{y}")] for y in years]
        keyboard.append([InlineKeyboardButton(MIX_LABEL, callback_data="year:MIX")])
        await query.edit_message_text(
            f"Type: *{exam_type}*\nSelect *Year*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "year":
        year = data.split(":", 1)[1]
        context.user_data["year"] = year
        state = await _require_state(query, context, "exam_type", "mode", "course", "level", "subject")
        if state is None:
            return
        exam_type = state["exam_type"]
        mode, course, level, subject = state["mode"], state["course"], state["level"], state["subject"]
        chapters = _mode_bank(mode).chapters(exam_type, year, course, level, subject)
        # Telegram's callback_data has a hard 64-BYTE limit. Some content
        # sources slugify the full chapter/unit name (e.g. "the-process-of-
        # budget-making-sources-of-revenue-expenditure-management-and-
        # management-of-public-debt") -- well over 64 bytes on its own.
        # BUG FIXED 2026-08-12: putting that raw slug straight into
        # "chapter:{slug}" made Telegram reject the whole edit_message_text
        # call (BadRequest: Button_data_invalid) for EVERY chapter button
        # whenever even one slug in the list was too long -- confirmed live
        # in 1lavya-examhub.log, and it's exactly the step right after
        # picking Year, matching the "selecting anything gives no response"
        # report. Fix: carry a small integer index in callback_data instead
        # (same fix already applied to Study Hub's buttons for this exact
        # bug class -- see CLAUDE.md section 8) and resolve it back via
        # context.user_data, never the raw slug string.
        context.user_data["chapter_slugs"] = [slug for slug, _label in chapters]
        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"chapter:{i}")]
            for i, (slug, label) in enumerate(chapters)
        ]
        keyboard.append([InlineKeyboardButton(ALL_CHAPTERS_LABEL, callback_data="chapter:ALL")])
        await query.edit_message_text(
            f"Type: *{exam_type}* | Year: *{year}*\nSelect *Chapter*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "chapter":
        raw = data.split(":", 1)[1]
        if raw == "ALL":
            chapter_slug = "ALL"
        else:
            slugs = context.user_data.get("chapter_slugs") or []
            try:
                chapter_slug = slugs[int(raw)]
            except (ValueError, IndexError):
                await query.edit_message_text(
                    "⚠️ Your session has expired (the bot may have restarted). Please start over.",
                    reply_markup=_session_expired_markup(),
                )
                return
        context.user_data["chapter_slug"] = chapter_slug
        state = await _require_state(query, context, "exam_type", "year", "mode", "course", "level", "subject")
        if state is None:
            return
        exam_type, year = state["exam_type"], state["year"]
        mode, course, level, subject = state["mode"], state["course"], state["level"], state["subject"]
        bank_obj = _mode_bank(mode)

        matches = bank_obj.filter_questions(exam_type, year, chapter_slug, course, level, subject)
        if not matches:
            await query.edit_message_text("No questions found for that selection. Use /start to try again.")
            return

        id_field = "book_id" if mode == "descriptive" else "mcq_id"
        ids = [q[id_field] for q in matches]
        random.shuffle(ids)
        context.user_data["queue"] = ids
        context.user_data["queue_pos"] = 0

        if mode == "descriptive":
            await send_question(query, context)
        else:
            await send_mcq(query, context)

    elif action == "answer":
        book_id = data.split(":", 1)[1]
        await send_answer(query, context, book_id)

    elif action == "pdf":
        book_id = data.split(":", 1)[1]
        await send_pdf(query, context, book_id)

    elif action == "next":
        mode = context.user_data.get("mode")
        if mode == "mcq":
            await send_mcq(query, context)
        else:
            await send_question(query, context)

    elif action == "mcqopt":
        _, mcq_id, letter = data.split(":", 2)
        await handle_mcq_answer(query, context, mcq_id, letter)

    elif action == "reportissue":
        # Added 2026-08-13. Only button_router has access to the current
        # question's course/level/subject/chapter (stashed by
        # handle_mcq_answer) -- mcq_issue_flow.py deliberately never looks
        # a question up itself, see that module's own docstring.
        info = context.user_data.get("current_mcq_report_ctx")
        if not info:
            await query.edit_message_text(
                "⚠️ Your session has expired (the bot may have restarted). Please start over.",
                reply_markup=_session_expired_markup(),
            )
            return
        return_markup = InlineKeyboardMarkup(next_step_rows(context, include_next=True))
        await mcq_issue_flow.start_issue_report(
            query, context, BOT_ID,
            mcq_id=info["mcq_id"], human_id=info.get("human_id"), course=info["course"], level=info["level"],
            subject=info["subject"],
            chapter_slug=info["chapter_slug"], chapter_label=info["chapter_label"],
            return_markup=return_markup,
        )

    elif action == "imdone":
        await show_today_summary(query, context)


def next_step_rows(context, include_next=True, extra_rows=None):
    """The 3-way choice shown after a question is answered (or after the
    queue runs out, with include_next=False since there's nothing left to
    advance to): keep going, back up one level to the Chapter list to pick
    a different chapter/exam-type set, or end the session entirely.
    "Back to Chapter List" reuses the existing "year" action unchanged --
    context.user_data["exam_type"]/["year"] are already set from earlier
    in this session, so re-invoking it just recomputes and re-shows the
    same chapter list the student picked from, exactly like Study Hub's
    "Download more" button reuses its own prior screen.

    Returns raw button ROWS (a list of one-button lists), not a wrapped
    InlineKeyboardMarkup, so a caller with its own extra button (e.g.
    send_answer's "Get as PDF") can pass it via extra_rows and get one
    combined keyboard rather than stitching two separately.

    BUG FIXED 2026-08-13: "I'm Done" used to carry the SAME bare `restart`
    callback_data as "Start Over" -- meaning it silently reset straight
    back to the Mode picker, no summary ever shown. Now carries its own
    `imdone` action (see button_router's own branch, which shows a quick
    today's-summary + the on-demand report offer, Pranav's explicit ask)."""
    year = context.user_data.get("year")
    exam_type = context.user_data.get("exam_type")
    back_cb = "restart" if (year is None or exam_type is None) else f"year:{year}"
    rows = list(extra_rows or [])
    if include_next:
        rows.append([InlineKeyboardButton("⏭ Next Question", callback_data="next")])
    rows.append([InlineKeyboardButton("\U0001F519 Back to Chapter List", callback_data=back_cb)])
    rows.append([InlineKeyboardButton("\U0001F3C1 I'm Done", callback_data="imdone")])
    return rows


async def show_today_summary(query, context):
    """Shown when the student taps "I'm Done" -- added 2026-08-13, Pranav's
    ask. A quick "how did today go" snapshot (student_analytics.
    fetch_today_summary(), platform-wide/UTC-day, distinct from the full
    report's always-all-time numbers), then offers the SAME on-demand
    report flow already built in report_flow.py -- reusing its existing
    "report:ondemand_yes"/"report:ondemand_no" callback branches directly
    (already registered in main() below), zero new report-delivery code
    needed here. Setting report_flow_bot_id ourselves (normally done by
    report_flow.start_report_flow_on_demand()/maybe_trigger_report_milestone(),
    neither of which runs on this path) is the one thing this function
    must do for that reuse to work correctly later in the conversation."""
    conn = platform_db.get_connection()
    summary = student_analytics.fetch_today_summary(conn, query.from_user.id)
    mins, secs = divmod(summary["time_spent_today_seconds"], 60)
    time_str = f"{mins}m {secs}s" if mins else f"{secs}s"

    text = (
        f"\U0001F4CA *Today's Summary*\n\n"
        f"MCQs attempted: *{summary['mcq_shown']}*\n"
        f"MCQs answered: *{summary['mcq_answered']}*\n"
        f"Correct answers: *{summary['mcq_correct']}*\n"
        f"Descriptive questions viewed: *{summary['descriptive_shown']}*\n"
        f"Time spent today: *{time_str}*\n\n"
        f"Would you like a complete performance report (accuracy, chapter-wise "
        f"breakdown, time spent) sent to you?"
    )
    context.user_data["report_flow_bot_id"] = BOT_ID
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="report:ondemand_yes"),
         InlineKeyboardButton("No", callback_data="report:ondemand_no")],
        [InlineKeyboardButton("\U0001F519 Start Over", callback_data="restart")],
    ]
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))


# ---------------------------------------------------------------------------
# DESCRIPTIVE FLOW
# ---------------------------------------------------------------------------
async def send_question(query, context):
    queue = context.user_data.get("queue", [])
    pos = context.user_data.get("queue_pos", 0)

    if pos >= len(queue):
        # No brand footer -- this is plain communication, not an answer/PDF.
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\u2705 You've gone through all questions in this selection.",
            reply_markup=InlineKeyboardMarkup(next_step_rows(context, include_next=False)),
        )
        return

    book_id = queue[pos]
    context.user_data["queue_pos"] = pos + 1
    q = bank.get_by_book_id(book_id)

    # WALLET -- billing rollout, 2026-08-16. Debited on every question
    # SHOWN (matches how mcq_debit already works, and Pranav's literal
    # instruction: "deducted with every MCQ or Descriptive questions
    # interacted by the students"), before any content is sent. No
    # idempotency_key here on purpose -- unlike a Test Mode charge or a
    # recharge, a genuine repeat VIEW of a question (navigating back to it)
    # is intended to debit again each time, not be protected against.
    username, _ = identity.ensure_wallet_identity(DB_CONN, query.from_user)
    ok, _, _ = wallet.debit(DB_CONN, username, TENANT_ID, "descriptive_debit", wallet.RATE_DESCRIPTIVE_CREDIT, reference=book_id)
    if not ok:
        await context.bot.send_message(
            chat_id=query.message.chat_id, text=_out_of_balance_text(), parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(next_step_rows(context, include_next=False)),
        )
        return

    # ID line shows human_id -- the platform's globally-unique, human-
    # readable question identifier (see COURSE-CATALOG.md) -- rather than
    # the internal book_id, so a student can actually reference "which
    # question" this is (to a faculty, in a support email, etc.). Falls
    # back to book_id only for the rare record with no human_id yet.
    meta = (
        f"\U0001F194 {q.get('human_id') or q.get('book_id','')}\n"
        f"\U0001F4C4 {q.get('src_text','')} | {q.get('qno_text','')}\n"
        f"\U0001F3F7 {q.get('topic_text','')}\n"
        f"{q.get('marks_text','')} | {q.get('approx_time_text','')}"
    )
    question_text = html_to_telegram_text(q.get("question_html", ""))

    keyboard = [
        [InlineKeyboardButton("\U0001F441 Show Answer", callback_data=f"answer:{book_id}")],
        [InlineKeyboardButton("\u23ED Next Question", callback_data="next")],
    ]

    event_id = db_log_descriptive_shown(
        query.from_user.id, context.user_data.get("session_id"), q,
        context.user_data.get("course"), context.user_data.get("level"),
        context.user_data.get("exam_type"), context.user_data.get("year"),
        q.get("chapter_slug"), q.get("chapter_label"),
    )
    context.user_data["current_descriptive_event_id"] = event_id

    # No brand footer -- this is the question being asked, never branded
    # (only the answer, in send_answer() below, carries it).
    text = f"{meta}\n\n{question_text}"
    await send_long_message(
        context, query.message.chat_id, text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_answer(query, context, book_id):
    q = bank.get_by_book_id(book_id)
    if not q:
        await query.answer("Question not found.", show_alert=True)
        return

    db_log_descriptive_answer_shown(context.user_data.get("current_descriptive_event_id"))

    answer_text = html_to_telegram_text(q.get("answer_html", ""))
    note = q.get("mistake_text")
    note_block = f"\n\n\u26A0\uFE0F <b>Note:</b> {note}" if note else ""

    rows = next_step_rows(
        context, include_next=True,
        extra_rows=[[InlineKeyboardButton("\U0001F4C4 Get as PDF", callback_data=f"pdf:{book_id}")]],
    )

    await send_long_message(
        context,
        query.message.chat_id,
        with_brand_html(f"<b>Answer:</b>\n\n{answer_text}{note_block}"),
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def send_pdf(query, context, book_id):
    q = bank.get_by_book_id(book_id)
    if not q:
        await query.answer("Question not found.", show_alert=True)
        return

    db_log_descriptive_pdf(context.user_data.get("current_descriptive_event_id"))

    title = f"{q.get('_chapter_label') or q.get('chapter_label','')} — {q.get('qno_text','')}"
    meta_lines = [
        f"Source: {q.get('src_text','')}",
        f"Topic: {q.get('topic_text','')}",
        f"{q.get('marks_text','')} | {q.get('approx_time_text','')}",
    ]
    pdf_bytes = html_to_pdf_bytes(
        title, meta_lines, q.get("question_html", ""), q.get("answer_html", "")
    )

    filename = f"{q.get('book_id', 'question')}.pdf"
    await context.bot.send_document(
        chat_id=query.message.chat_id,
        document=pdf_bytes,
        filename=filename,
        caption=with_brand_md("Here's your question + answer as a PDF."),
        parse_mode=ParseMode.MARKDOWN,
    )


# ---------------------------------------------------------------------------
# MCQ FLOW
# ---------------------------------------------------------------------------
async def send_mcq(query, context):
    queue = context.user_data.get("queue", [])
    pos = context.user_data.get("queue_pos", 0)

    if pos >= len(queue):
        # No brand footer -- plain communication, not an answer/PDF.
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\u2705 You've gone through all MCQs in this selection.",
            reply_markup=InlineKeyboardMarkup(next_step_rows(context, include_next=False)),
        )
        return

    mcq_id = queue[pos]
    context.user_data["queue_pos"] = pos + 1
    q = mcq_bank.get_by_id(mcq_id)

    # WALLET -- billing rollout, 2026-08-16, same shape as send_question()'s
    # own debit above -- see that comment for the full reasoning.
    username, _ = identity.ensure_wallet_identity(DB_CONN, query.from_user)
    ok, _, _ = wallet.debit(DB_CONN, username, TENANT_ID, "mcq_debit", wallet.RATE_MCQ_CREDIT, reference=mcq_id)
    if not ok:
        await context.bot.send_message(
            chat_id=query.message.chat_id, text=_out_of_balance_text(), parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(next_step_rows(context, include_next=False)),
        )
        return

    # `or ''` not `.get(key, '')` -- an explicit `null` (present on every one
    # of the 375 merged CMA Foundation records' "year"/"difficulty" fields)
    # would otherwise render as the literal word "None" in the message. Same
    # root cause as the button-crash fix above, different (cosmetic, not
    # crashing) symptom.
    # ID line shows human_id -- see send_question()'s own comment on why
    # (globally-unique, human-readable question identifier -- see
    # COURSE-CATALOG.md -- shown so a student can actually reference
    # "which question" this is). Falls back to the internal mcq_id only
    # for the rare record with no human_id yet.
    meta = (
        f"\U0001F194 {q.get('human_id') or q.get('mcq_id','')}\n"
        f"\U0001F4C4 {q.get('exam_type') or ''} {q.get('year') or ''} | {q.get('qno_text') or ''}\n"
        f"\U0001F3F7 {q.get('topic_text') or ''}\n"
        f"Marks: {q.get('marks') or ''} | Difficulty: {q.get('difficulty') or ''}"
    )

    body_parts = []
    if q.get("case_facts_html"):
        body_parts.append("<b>Case:</b>\n" + html_to_telegram_text(q["case_facts_html"]))
    body_parts.append(html_to_telegram_text(q.get("question_html", "")))

    options = q.get("options", {})
    option_lines = "\n".join(
        f"<b>{letter}.</b> {html_to_telegram_text(text).strip()}"
        for letter, text in sorted(options.items())
    )
    body_parts.append(option_lines)

    question_text = "\n\n".join(body_parts)

    keyboard = [[
        InlineKeyboardButton(letter, callback_data=f"mcqopt:{mcq_id}:{letter}")
        for letter in sorted(options)
    ]]

    attempt_id = db_log_mcq_shown(
        query.from_user.id, context.user_data.get("session_id"), q,
        context.user_data.get("course"), context.user_data.get("level"),
    )
    context.user_data["current_mcq_attempt_id"] = attempt_id

    # No brand footer -- this is the question being asked, never branded
    # (only the result, in handle_mcq_answer() below, carries it).
    text = f"{meta}\n\n{question_text}"
    await send_long_message(
        context, query.message.chat_id, text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_mcq_answer(query, context, mcq_id, letter):
    q = mcq_bank.get_by_id(mcq_id)
    if not q:
        await query.answer("Question not found.", show_alert=True)
        return

    correct = q.get("correct_option")
    is_correct = letter == correct

    attempt_id = context.user_data.get("current_mcq_attempt_id")
    db_log_mcq_answered(attempt_id, letter, is_correct)

    await query.answer(
        "\u2705 Correct!" if is_correct else f"\u274C Incorrect (Correct: {correct})",
    )

    # Remove the option buttons so the same question can't be re-answered.
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    icon = "\u2705 <b>Correct!</b>" if is_correct else f"\u274C <b>Incorrect</b> — you selected ({letter})"
    explanation = html_to_telegram_text(q.get("answer_html", ""))

    result_text = with_brand_html(f"{icon}\nCorrect Answer: <b>({correct})</b>\n\n{explanation}")

    # Stashed so the "reportissue" action (in button_router below) knows
    # which question is being flagged without needing mcq_id embedded in
    # its own button's callback_data -- see mcq_issue_flow.py's own
    # "DELIBERATE NON-DEPENDENCY" note for why that module never looks the
    # question up itself. `_course`/`_level`/`_subject`/`_chapter_label`
    # are already resolved on `q` at load time (see McqBank.load()).
    context.user_data["current_mcq_report_ctx"] = {
        "mcq_id": mcq_id, "human_id": q.get("human_id"), "course": q.get("_course"), "level": q.get("_level"),
        "subject": q.get("_subject"),
        "chapter_slug": q.get("chapter_slug"), "chapter_label": q.get("_chapter_label") or q.get("chapter_label"),
    }

    rows = next_step_rows(
        context, include_next=True,
        extra_rows=[[InlineKeyboardButton("\U0001F6A9 Report Issue in MCQ", callback_data="reportissue")]],
    )
    await send_long_message(
        context, query.message.chat_id, result_text,
        reply_markup=InlineKeyboardMarkup(rows),
    )

    # 2026-08-11: platform-wide 20-question report milestone -- see
    # report_flow.py's own docstring. No-ops unless this answer is exactly
    # the student's 20th platform-wide AND they've never been prompted
    # before, so this is safe to call unconditionally on every answer.
    await report_flow.maybe_trigger_report_milestone(query, context, query.from_user.id, BOT_ID)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This bot has no general free-text intent handling yet (that's
    separate, not-yet-scheduled roadmap scope -- see the big 2026-08-11
    roadmap's "conversational upgrades" item, not part of this phase).
    Free text here means one of: (1) mid-profile-flow input (display name,
    username, email, mobile, etc. -- checked FIRST so a profile edit in
    progress is never accidentally swallowed by the trigger-phrase check
    below), (2) the "profile"/"change profile" trigger phrase itself, or
    (3) a reply to the report flow's mobile/email prompt -- the original,
    only case this router handled before 2026-08-11, or (4) a reply to
    the "Report Issue in MCQ" description prompt (2026-08-13) -- checked
    FIRST of all, same "most specific active state first" discipline, so
    a student mid-way through describing a wrong-answer report never has
    their message swallowed by anything else. Anything else is silently
    ignored rather than guessed at."""
    text = (update.message.text or "").strip()
    # 2026-08-16: Test Mode's own upload-collection state, checked FIRST of
    # all -- a student actively uploading pages for a descriptive question
    # (typing "done" to finish) must never have that text swallowed by
    # anything else, same "most specific active state first" discipline
    # every other check below already follows.
    if test_flow.is_collecting_upload(context):
        if await test_flow.handle_upload_text_input(update, context, sys.modules[__name__]):
            return
    if mcq_issue_flow.is_awaiting_text_input(context):
        if await mcq_issue_flow.handle_issue_text_input(update, context):
            return
    if profile_flow.is_awaiting_text_input(context):
        if await profile_flow.handle_profile_text_input(update, context):
            return
    if profile_flow.matches_trigger(text):
        await profile_flow.start_profile_flow(update, context)
        return
    # Test Mode's own triggers -- "test"/"take a test"/etc. to start/resume
    # a test, "upload" to submit a descriptive answer while one is active.
    if test_flow.matches_trigger(text):
        await test_flow.start_test_flow(update, context, BOT_ID, sys.modules[__name__])
        return
    if test_flow.matches_upload_trigger(text):
        await test_flow.start_upload_pick(update, context, sys.modules[__name__])
        return
    # report_flow's own on-demand trigger ("report"/"analysis"/"email"/
    # "mail") -- guarded by `not is_awaiting_text_input` so a genuine
    # mid-flow mobile/email reply is never mistaken for the trigger phrase
    # itself (see report_flow.py's own docstring on this exact risk class).
    if report_flow.matches_trigger(text) and not report_flow.is_awaiting_text_input(context):
        await report_flow.start_report_flow_on_demand(update, context, BOT_ID)
        return
    await report_flow.handle_contact_text_input(update, context)


def main():
    if not BOT_TOKEN:
        env_name = BOT_CONFIG.get("bot_token_env")
        raise SystemExit(
            f"No bot token found for bot_id '{BOT_ID}'. "
            f"Set the {env_name} variable in telegram/.env "
            f"(see telegram/config/bots.README.md)."
        )

    app = Application.builder().token(BOT_TOKEN).build()
    platform_db.schedule_heartbeat(app, BOT_ID)

    app.add_handler(CommandHandler("start", start))
    # 2026-08-11: button_router now needs an explicit pattern -- it used to
    # have none (matched every callback), which was harmless only because
    # nothing else claimed any callback_data. The moment a second handler
    # (report_flow's, below) needs its own prefixes, an unrestricted
    # first-registered handler would silently swallow them: button_router
    # would run, find no matching `if action == ...` branch for "report"/
    # "reportconfirm", do nothing, and python-telegram-bot would still
    # count the update as handled -- report_flow_callback would never even
    # be invoked. Exactly the class of bug already found once this session
    # (2026-08-10, faculty_bot.py's "next"/"restart" callback pattern) --
    # scoping this explicitly now instead of relying on "nothing else
    # collides yet."
    app.add_handler(CallbackQueryHandler(
        button_router,
        pattern=r"^(course|level|mode|subject|type|year|chapter|answer|pdf|next|mcqopt|restart|reportissue|imdone)(:|$)",
    ))
    app.add_handler(CallbackQueryHandler(report_flow.report_flow_callback, pattern=r"^(report|reportconfirm):"))
    app.add_handler(CallbackQueryHandler(profile_flow.profile_flow_callback, pattern=r"^(profile|profileconfirm):"))
    # 2026-08-13: mcq_issue_flow's own callbacks ("issuecat:<i>", bare
    # "issuecancel") -- registered separately, same "explicit pattern per
    # module" discipline as report_flow/profile_flow above.
    app.add_handler(CallbackQueryHandler(mcq_issue_flow.mcq_issue_flow_callback, pattern=r"^(issuecat|issuecancel)(:|$)"))
    # 2026-08-16: Test Mode's own callback prefixes -- same "explicit
    # pattern per module" discipline as every flow above (the callback-
    # pattern-collision bug class this platform has hit 3+ times already).
    app.add_handler(CallbackQueryHandler(_test_flow_callback_wrapper, pattern=r"^(testflow|tnav|topt|tgo|tupload)(:|$)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    # Photo/document uploads -- only meaningful during Test Mode's upload
    # collection; test_flow.handle_upload_photo_or_document() is a no-op
    # (returns False) when no upload is actively being collected, so this
    # handler is safe to register unconditionally.
    app.add_handler(MessageHandler((filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND, _upload_router))

    # Sweep any in-progress tests from before this restart and re-arm their
    # expiry jobs -- job_queue jobs do NOT survive a process restart (same
    # reasoning already established for every other scheduled job on this
    # platform). Must happen AFTER the Application (and its job_queue) is
    # built, before run_polling() starts serving real traffic.
    test_flow.rearm_pending_test_jobs(app, sys.modules[__name__])

    logger.info(f"Exam Hub Bot starting for bot_id '{BOT_ID}' (tenant '{TENANT_ID}', {TENANT['display_name']})...")
    app.run_polling()


async def _test_flow_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_flow.test_flow_callback(update, context, BOT_ID, sys.modules[__name__])


async def _upload_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_flow.handle_upload_photo_or_document(update, context, sys.modules[__name__])


if __name__ == "__main__":
    main()
