"""
1Lavya Exam Hub Bot (Bot 2)
----------------------------
Drill-down exam practice bot:
  Course (CA / CS / CMA)
    -> Level (per course, e.g. Foundation / Inter / Final)
      -> [if no question data yet for that Course+Level: say so, offer restart]
      -> Mode (Descriptive / MCQ)
        Descriptive:
          Exam Type (MTP / RTP / PYQ / Mix)
            -> Year (or Mix - all years)
              -> Chapter (or All Chapters)
                -> Shows a question -> "Show Answer?" -> answer (text) + PDF download
        MCQ:
          Exam Type (MTP / RTP / PYQ / Mix)
            -> Year (or Mix - all years)
              -> Chapter (or All Chapters)
                -> Shows a question + up to 4 options as buttons
                  -> student taps an option -> immediately shown correct/incorrect,
                     the correct answer, and its explanation -> "Next Question"

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
   telegram/config/tenants.json row (JSON_PATH/MCQ_JSON_PATH/Course-Level
   menu all come from there).
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
import report_flow  # noqa: E402 -- telegram/bots/report_flow.py, the 20-question milestone report pipeline (2026-08-11)
import profile_flow  # noqa: E402 -- telegram/bots/profile_flow.py, the "profile"/"change profile" identity flow (2026-08-11)

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

# Course -> ordered list of Levels, shown in the menu. "ALL" scope
# (1LAVYA's flagship) keeps every course/level visible up front even
# where no question data exists yet (per Pranav's instruction,
# 2026-08-08) -- AVAILABLE_DATA below still gates entry into a
# combination with no real content. A scoped (faculty) tenant only ever
# sees the courses/levels its own content_scope licenses -- showing e.g.
# "CA Foundation" on a Law-only faculty's bot would be actively wrong,
# not just incomplete.
if TENANT["content_scope"] == "ALL":
    COURSES = {
        "CA": ["Foundation", "Inter", "Final"],
        "CS": ["Foundation", "Executive", "Professional"],
        "CMA": ["Foundation", "Inter", "Final"],
    }
else:
    COURSES = {}
    for _s in TENANT["content_scope"]:
        COURSES.setdefault(_s["course"], [])
        if _s["level"] not in COURSES[_s["course"]]:
            COURSES[_s["course"]].append(_s["level"])

# (course, level) pairs that actually have question data behind them --
# computed from whatever's really in the loaded banks (see bank/mcq_bank
# below) rather than hand-maintained, so this can never drift out of sync
# with the data itself. A course/level not in here still shows in the
# menu (for "ALL" scope) but resolves to a "not available yet" message.
AVAILABLE_DATA = set()

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
            chapter_slug, chapter_label, qno_text, marks_text, shown_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (BOT_ID, user_id, session_id, q.get("book_id"), course, level, exam_type, year,
         chapter_slug, chapter_label, q.get("qno_text"), q.get("marks_text"), now),
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
            chapter_slug, chapter_label, qno_text, marks, difficulty, correct_option, shown_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (BOT_ID, user_id, session_id, q.get("mcq_id"), course, level, q.get("exam_type"), q.get("year"),
         q.get("chapter_slug"), q.get("chapter_label"), q.get("qno_text"), q.get("marks"),
         q.get("difficulty"), q.get("correct_option"), now),
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
def _load_and_merge_json_sources(json_paths, id_field, kind_label, logger):
    """Shared by QuestionBank/McqBank below: read every path in json_paths
    (already a list, or None), concatenate their records, and warn (never
    crash) if the same id_field value shows up in more than one source --
    get_by_book_id()/get_by_id() are first-match-wins, so a real collision
    would silently shadow one source's record with another's rather than
    erroring, exactly the bug class validate_content_json.py's own
    duplicate-id check exists to catch on a single file; this is that same
    check applied across merged files."""
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
        combined.extend(data)
        logger.info(f"{kind_label}: loaded {len(data)} record(s) from {path}")
    return combined


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

    def exam_types(self, course=None, level=None):
        return sorted({q["_exam_type"] for q in self._by_course_level(course, level)})

    def years(self, exam_type, course=None, level=None):
        pool = self._by_course_level(course, level)
        subset = pool if exam_type == "MIX" else [q for q in pool if q["_exam_type"] == exam_type]
        return sorted({q["_year"] for q in subset})

    def chapters(self, exam_type, year, course=None, level=None):
        subset = self._filter(exam_type, year, course, level)
        seen = {}
        for q in subset:
            # `.get(key, default)` only substitutes when the key is ABSENT --
            # a record with an explicit `"chapter_slug": null` (real, seen in
            # faculty content) still returns None, not the default. `or` is
            # what's actually needed here (see McqBank's twin methods below
            # for the concrete crash this exact mistake caused 2026-08-10).
            slug = q.get("chapter_slug") or "unknown"
            label = q.get("chapter_label") or slug
            seen[slug] = label
        return sorted(seen.items(), key=lambda kv: kv[1])

    def _by_course_level(self, course, level):
        """A record with no "course"/"level" field (the flagship's original
        schema) always matches -- only records that DO carry those fields
        (faculty practice content spanning more than one course/level) get
        filtered. Prevents a Foundation student from ever seeing an
        Intermediate-only question, or vice versa, within the same bank."""
        subset = self.questions
        if course:
            subset = [q for q in subset if q.get("course") in (None, course)]
        if level:
            subset = [q for q in subset if q.get("level") in (None, level)]
        return subset

    def _filter(self, exam_type, year, course=None, level=None):
        subset = self._by_course_level(course, level)
        if exam_type != "MIX":
            subset = [q for q in subset if q["_exam_type"] == exam_type]
        if year != "MIX":
            subset = [q for q in subset if q["_year"] == year]
        return subset

    def filter_questions(self, exam_type, year, chapter_slug, course=None, level=None):
        subset = self._filter(exam_type, year, course, level)
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

    def _by_course_level(self, course, level):
        subset = self.questions
        if course:
            subset = [q for q in subset if q.get("course") in (None, course)]
        if level:
            subset = [q for q in subset if q.get("level") in (None, level)]
        return subset

    def exam_types(self, course=None, level=None):
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
        return sorted({q.get("exam_type") or "OTHER" for q in self._by_course_level(course, level)})

    def years(self, exam_type, course=None, level=None):
        pool = self._by_course_level(course, level)
        subset = pool if exam_type == "MIX" else [q for q in pool if q.get("exam_type") == exam_type]
        return sorted({q.get("year") or "Unknown" for q in subset})

    def chapters(self, exam_type, year, course=None, level=None):
        subset = self._filter(exam_type, year, course, level)
        seen = {}
        for q in subset:
            slug = q.get("chapter_slug") or "unknown"
            label = q.get("chapter_label") or slug
            seen[slug] = label
        return sorted(seen.items(), key=lambda kv: kv[1])

    def _filter(self, exam_type, year, course=None, level=None):
        # Must normalize the SAME way years()/exam_types()/chapters() above
        # do (`or`, not raw `.get()`) -- otherwise a student picking the
        # "Unknown"/"OTHER" bucket those methods synthesized for a
        # null-valued record would match zero records here (comparing the
        # synthesized label against the raw None never matches), silently
        # showing an empty chapter/question list instead of the bug above's
        # loud crash. Same root cause, different failure mode -- fixed
        # together 2026-08-10.
        subset = self._by_course_level(course, level)
        if exam_type != "MIX":
            subset = [q for q in subset if (q.get("exam_type") or "OTHER") == exam_type]
        if year != "MIX":
            subset = [q for q in subset if (q.get("year") or "Unknown") == year]
        return subset

    def filter_questions(self, exam_type, year, chapter_slug, course=None, level=None):
        subset = self._filter(exam_type, year, course, level)
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

# Computed from real loaded data (see COURSES's docstring-comment above for
# why this replaced a hand-maintained constant).
AVAILABLE_DATA = set()
for _q in mcq_bank.questions:
    if _q.get("course") and _q.get("level"):
        AVAILABLE_DATA.add((_q["course"], _q["level"]))
for _q in bank.questions:
    if _q.get("course") and _q.get("level"):
        AVAILABLE_DATA.add((_q["course"], _q["level"]))
logger.info(f"Tenant '{TENANT_ID}': AVAILABLE_DATA = {AVAILABLE_DATA}")

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
def build_course_menu():
    keyboard = [[InlineKeyboardButton(c, callback_data=f"course:{c}")] for c in COURSES]
    opening = TENANT.get("welcome_message") or "*Welcome to 1Lavya Exam Hub* \U0001F4DD"
    text = f"{opening}\n\nSelect your *Course*:"
    return text, InlineKeyboardMarkup(keyboard)


def build_level_menu(course):
    levels = COURSES.get(course, [])
    keyboard = [[InlineKeyboardButton(lvl, callback_data=f"level:{lvl}")] for lvl in levels]
    return f"Course: *{course}*\nSelect your *Level*:", InlineKeyboardMarkup(keyboard)


def build_mode_menu_or_gate(course, level):
    """The screen shown once Course+Level are both settled -- either the
    Descriptive/MCQ picker, or the "nothing here yet" gate, exactly what
    the old "level" branch used to render inline. Factored out so it can
    be reached either from a real Level tap OR from the auto-skip cascade
    in entry_screen_and_updates()/the "course" branch below."""
    if (course, level) not in AVAILABLE_DATA:
        keyboard = [[InlineKeyboardButton("\U0001F519 Start Over", callback_data="restart")]]
        text = (
            f"Course: *{course}* | Level: *{level}*\n\n"
            f"\U0001F6A7 Currently there are no questions for this Level. "
            f"We will shortly have questions on these as well!"
        )
        return text, InlineKeyboardMarkup(keyboard)
    keyboard = [
        [InlineKeyboardButton("\U0001F4DD Descriptive", callback_data="mode:descriptive")],
        [InlineKeyboardButton("✅ MCQ", callback_data="mode:mcq")],
    ]
    text = f"Course: *{course}* | Level: *{level}*\nWhat would you like to practice?"
    return text, InlineKeyboardMarkup(keyboard)


def entry_screen_and_updates():
    """What a student should see immediately after /start or "Start Over" --
    auto-skipping the Course and/or Level picker when this tenant's
    content_scope leaves only one real option at that step (persisted in
    telegram/config/tenants.json, so this is stable across restarts and
    every session -- nothing here is per-student/session state). Returns
    (text, markup, user_data_updates) -- callers must merge updates into
    context.user_data (and mirror into db_update_session) before the
    course/level get used anywhere else."""
    courses = list(COURSES.keys())
    if len(courses) != 1:
        text, markup = build_course_menu()
        return text, markup, {}
    course = courses[0]
    levels = COURSES[course]
    if len(levels) != 1:
        text, markup = build_level_menu(course)
        return text, markup, {"course": course}
    level = levels[0]
    text, markup = build_mode_menu_or_gate(course, level)
    return text, markup, {"course": course, "level": level}


# ---------------------------------------------------------------------------
# HANDLERS
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    db_upsert_student(user)
    context.user_data["session_id"] = db_start_session(user.id)

    text, markup, updates = entry_screen_and_updates()
    if updates:
        context.user_data.update(updates)
        db_update_session(context.user_data["session_id"], **updates)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


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
        context.user_data["session_id"] = db_start_session(user.id)
        text, markup, updates = entry_screen_and_updates()
        if updates:
            context.user_data.update(updates)
            db_update_session(context.user_data["session_id"], **updates)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
        return

    if action == "course":
        course = data.split(":", 1)[1]
        context.user_data["course"] = course
        db_update_session(session_id, course=course)
        levels = COURSES.get(course, [])
        if len(levels) == 1:
            # Only one Level under this course -- skip straight to the
            # Descriptive/MCQ picker (or the "nothing here yet" gate).
            level = levels[0]
            context.user_data["level"] = level
            db_update_session(session_id, level=level)
            text, markup = build_mode_menu_or_gate(course, level)
            await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
            return
        text, markup = build_level_menu(course)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    elif action == "level":
        level = data.split(":", 1)[1]
        context.user_data["level"] = level
        course = context.user_data.get("course")
        db_update_session(session_id, level=level)
        text, markup = build_mode_menu_or_gate(course, level)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    elif action == "mode":
        mode = data.split(":", 1)[1]  # "descriptive" or "mcq"
        context.user_data["mode"] = mode
        db_update_session(session_id, mode=mode)
        course = context.user_data.get("course")
        level = context.user_data.get("level")
        bank_obj = bank if mode == "descriptive" else mcq_bank
        label = "Descriptive" if mode == "descriptive" else "MCQ"
        exam_types = bank_obj.exam_types(course, level)

        # (course, level) has SOME content (the AVAILABLE_DATA gate above
        # already confirmed that), but this specific mode may still have
        # none -- e.g. a tenant with MCQs for one level and Descriptive for
        # another. Say so plainly rather than showing an Exam Type picker
        # that leads nowhere.
        if not exam_types:
            keyboard = [[InlineKeyboardButton("\U0001F519 Start Over", callback_data="restart")]]
            await query.edit_message_text(
                f"Course: *{course}* | Level: *{level}*\n\n"
                f"\U0001F6A7 No *{label}* questions for this Level yet. Try the other practice mode, "
                f"or check back soon!",
                parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

        keyboard = [[InlineKeyboardButton(et, callback_data=f"type:{et}")] for et in exam_types]
        keyboard.append([InlineKeyboardButton(MIX_LABEL, callback_data="type:MIX")])
        await query.edit_message_text(
            f"Mode: *{label}*\nSelect *Exam Type*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "type":
        exam_type = data.split(":", 1)[1]
        context.user_data["exam_type"] = exam_type
        mode = context.user_data.get("mode")
        course = context.user_data.get("course")
        level = context.user_data.get("level")
        bank_obj = bank if mode == "descriptive" else mcq_bank
        years = bank_obj.years(exam_type, course, level)
        keyboard = [[InlineKeyboardButton(y, callback_data=f"year:{y}")] for y in years]
        keyboard.append([InlineKeyboardButton(MIX_LABEL, callback_data="year:MIX")])
        await query.edit_message_text(
            f"Type: *{exam_type}*\nSelect *Year*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "year":
        year = data.split(":", 1)[1]
        context.user_data["year"] = year
        exam_type = context.user_data["exam_type"]
        mode = context.user_data.get("mode")
        course = context.user_data.get("course")
        level = context.user_data.get("level")
        bank_obj = bank if mode == "descriptive" else mcq_bank
        chapters = bank_obj.chapters(exam_type, year, course, level)
        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"chapter:{slug}")]
            for slug, label in chapters
        ]
        keyboard.append([InlineKeyboardButton(ALL_CHAPTERS_LABEL, callback_data="chapter:ALL")])
        await query.edit_message_text(
            f"Type: *{exam_type}* | Year: *{year}*\nSelect *Chapter*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "chapter":
        chapter_slug = data.split(":", 1)[1]
        context.user_data["chapter_slug"] = chapter_slug
        exam_type = context.user_data["exam_type"]
        year = context.user_data["year"]
        mode = context.user_data.get("mode")
        course = context.user_data.get("course")
        level = context.user_data.get("level")
        bank_obj = bank if mode == "descriptive" else mcq_bank

        matches = bank_obj.filter_questions(exam_type, year, chapter_slug, course, level)
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
    combined keyboard rather than stitching two separately."""
    year = context.user_data.get("year")
    exam_type = context.user_data.get("exam_type")
    back_cb = "restart" if (year is None or exam_type is None) else f"year:{year}"
    rows = list(extra_rows or [])
    if include_next:
        rows.append([InlineKeyboardButton("⏭ Next Question", callback_data="next")])
    rows.append([InlineKeyboardButton("\U0001F519 Back to Chapter List", callback_data=back_cb)])
    rows.append([InlineKeyboardButton("\U0001F3C1 I'm Done", callback_data="restart")])
    return rows


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

    meta = (
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

    title = f"{q.get('chapter_label','')} — {q.get('qno_text','')}"
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

    # `or ''` not `.get(key, '')` -- an explicit `null` (present on every one
    # of the 375 merged CMA Foundation records' "year"/"difficulty" fields)
    # would otherwise render as the literal word "None" in the message. Same
    # root cause as the button-crash fix above, different (cosmetic, not
    # crashing) symptom.
    meta = (
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

    await send_long_message(
        context, query.message.chat_id, result_text,
        reply_markup=InlineKeyboardMarkup(next_step_rows(context, include_next=True)),
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
    only case this router handled before 2026-08-11. Anything else is
    silently ignored rather than guessed at."""
    text = (update.message.text or "").strip()
    if profile_flow.is_awaiting_text_input(context):
        if await profile_flow.handle_profile_text_input(update, context):
            return
    if profile_flow.matches_trigger(text):
        await profile_flow.start_profile_flow(update, context)
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
        pattern=r"^(course|level|mode|type|year|chapter|answer|pdf|next|mcqopt|restart)(:|$)",
    ))
    app.add_handler(CallbackQueryHandler(report_flow.report_flow_callback, pattern=r"^(report|reportconfirm):"))
    app.add_handler(CallbackQueryHandler(profile_flow.profile_flow_callback, pattern=r"^(profile|profileconfirm):"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    logger.info(f"Exam Hub Bot starting for bot_id '{BOT_ID}' (tenant '{TENANT_ID}', {TENANT['display_name']})...")
    app.run_polling()


if __name__ == "__main__":
    main()
