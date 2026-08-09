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
option + correct/incorrect) is logged to a local SQLite DB (see DB_PATH
below) for analytics -- which student saw/attempted which question, and how
they did. See README_Bot2_ExamHub.md for the full DB schema.

SETUP (do this before running):
1. pip install python-telegram-bot beautifulsoup4 xhtml2pdf --break-system-packages
2. Set JSON_PATH / MCQ_JSON_PATH / DB_PATH below if your layout differs.
3. Set BOT_TOKEN below (or the TELEGRAM_EXAM_BOT_TOKEN environment variable, recommended).
4. Run: python exam_hub_bot.py
   Keep the terminal/laptop running for the bot to stay online.
"""

import os
import re
import io
import json
import random
import logging
import sqlite3
import threading

from datetime import datetime, timezone

from bs4 import BeautifulSoup
from xhtml2pdf import pisa

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------------------------------------------------------------------------
# CONFIG — edit these lines for your setup
# ---------------------------------------------------------------------------
JSON_PATH = r"D:\EffCorp_Projects\cap-online\telegram\assets\exam_bot\book_questions_extracted.json"       # descriptive questions
MCQ_JSON_PATH = r"D:\EffCorp_Projects\cap-online\telegram\assets\exam_bot\mcq_questions_extracted.json"    # MCQ questions (see telegram/tools/build_exam_bot_mcq_export.py)
DB_PATH = r"D:\EffCorp_Projects\cap-online\telegram\assets\exam_bot\Exam_Bot.db"                            # activity/analytics log
BOT_TOKEN = os.environ.get("TELEGRAM_EXAM_BOT_TOKEN", "PASTE_YOUR_BOTFATHER_TOKEN_HERE")

MIX_LABEL = "\U0001F500 Mix (All)"
ALL_CHAPTERS_LABEL = "\U0001F4DA All Chapters"

# Course -> ordered list of Levels. Shown in full up front (per Pranav's
# instruction, 2026-08-08) even though only one combination currently has
# question data -- see AVAILABLE_DATA below.
COURSES = {
    "CA": ["Foundation", "Inter", "Final"],
    "CS": ["Foundation", "Executive", "Professional"],
    "CMA": ["Foundation", "Inter", "Final"],
}

# (course, level) pairs that currently have real question data (descriptive
# and/or MCQ) behind them. Every other Course/Level combination is still
# shown in the menu -- selecting one just returns a "not available yet"
# message instead of the Descriptive/MCQ mode picker. Extend this set as
# more question banks get built for other courses/levels.
AVAILABLE_DATA = {("CA", "Inter")}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DATABASE — activity / analytics logging
# ---------------------------------------------------------------------------
# One SQLite file, four tables:
#   students                     -- one row per Telegram user
#   bot_sessions                 -- one row per /start (or "Start Over"),
#                                    tracks the course/level/mode funnel
#   descriptive_question_events  -- one row per descriptive question shown,
#                                    updated in place when the answer is
#                                    revealed / a PDF is requested
#   mcq_attempts                 -- one row per MCQ shown, updated in place
#                                    with the student's selected option and
#                                    whether it was correct, once answered
#
# Writes are serialized behind DB_LOCK -- python-telegram-bot's async
# handlers all run on one event loop for a bot this size, but the lock is
# cheap insurance against any accidental concurrent access.
DB_LOCK = threading.Lock()
DB_CONN = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db():
    global DB_CONN
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DB_CONN = sqlite3.connect(DB_PATH, check_same_thread=False)
    with DB_LOCK:
        DB_CONN.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                telegram_user_id INTEGER PRIMARY KEY,
                username         TEXT,
                first_name       TEXT,
                last_name        TEXT,
                first_seen_at    TEXT NOT NULL,
                last_seen_at     TEXT NOT NULL,
                session_count    INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS bot_sessions (
                session_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id  INTEGER NOT NULL,
                started_at        TEXT NOT NULL,
                course            TEXT,
                level             TEXT,
                mode              TEXT,
                FOREIGN KEY (telegram_user_id) REFERENCES students(telegram_user_id)
            );

            CREATE TABLE IF NOT EXISTS descriptive_question_events (
                event_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id  INTEGER NOT NULL,
                session_id        INTEGER,
                book_id           TEXT NOT NULL,
                course            TEXT,
                level             TEXT,
                exam_type         TEXT,
                year              TEXT,
                chapter_slug      TEXT,
                chapter_label     TEXT,
                qno_text          TEXT,
                marks_text        TEXT,
                shown_at          TEXT NOT NULL,
                answer_shown_at   TEXT,
                pdf_requested_at  TEXT,
                FOREIGN KEY (telegram_user_id) REFERENCES students(telegram_user_id),
                FOREIGN KEY (session_id) REFERENCES bot_sessions(session_id)
            );

            CREATE TABLE IF NOT EXISTS mcq_attempts (
                attempt_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id  INTEGER NOT NULL,
                session_id        INTEGER,
                mcq_id            TEXT NOT NULL,
                course            TEXT,
                level             TEXT,
                exam_type         TEXT,
                year              TEXT,
                chapter_slug      TEXT,
                chapter_label     TEXT,
                qno_text          TEXT,
                marks             INTEGER,
                difficulty        TEXT,
                correct_option    TEXT NOT NULL,
                selected_option   TEXT,
                is_correct        INTEGER,
                shown_at          TEXT NOT NULL,
                answered_at       TEXT,
                FOREIGN KEY (telegram_user_id) REFERENCES students(telegram_user_id),
                FOREIGN KEY (session_id) REFERENCES bot_sessions(session_id)
            );

            CREATE INDEX IF NOT EXISTS idx_desc_events_user    ON descriptive_question_events(telegram_user_id);
            CREATE INDEX IF NOT EXISTS idx_desc_events_book    ON descriptive_question_events(book_id);
            CREATE INDEX IF NOT EXISTS idx_mcq_attempts_user   ON mcq_attempts(telegram_user_id);
            CREATE INDEX IF NOT EXISTS idx_mcq_attempts_mcq    ON mcq_attempts(mcq_id);
            CREATE INDEX IF NOT EXISTS idx_mcq_attempts_chapter ON mcq_attempts(chapter_slug);
            """
        )
        DB_CONN.commit()
    logger.info(f"DB ready at {DB_PATH}")


def db_upsert_student(user):
    now = _now()
    with DB_LOCK:
        row = DB_CONN.execute(
            "SELECT telegram_user_id FROM students WHERE telegram_user_id=?", (user.id,)
        ).fetchone()
        if row:
            DB_CONN.execute(
                "UPDATE students SET username=?, first_name=?, last_name=?, last_seen_at=?, "
                "session_count=session_count+1 WHERE telegram_user_id=?",
                (user.username, user.first_name, user.last_name, now, user.id),
            )
        else:
            DB_CONN.execute(
                "INSERT INTO students (telegram_user_id, username, first_name, last_name, "
                "first_seen_at, last_seen_at, session_count) VALUES (?,?,?,?,?,?,1)",
                (user.id, user.username, user.first_name, user.last_name, now, now),
            )
        DB_CONN.commit()


def db_start_session(user_id) -> int:
    now = _now()
    with DB_LOCK:
        cur = DB_CONN.execute(
            "INSERT INTO bot_sessions (telegram_user_id, started_at) VALUES (?, ?)",
            (user_id, now),
        )
        DB_CONN.commit()
        return cur.lastrowid


def db_update_session(session_id, **fields):
    if not session_id or not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [session_id]
    with DB_LOCK:
        DB_CONN.execute(f"UPDATE bot_sessions SET {cols} WHERE session_id=?", values)
        DB_CONN.commit()


def db_log_descriptive_shown(user_id, session_id, q, course, level, exam_type, year,
                              chapter_slug, chapter_label) -> int:
    now = _now()
    with DB_LOCK:
        cur = DB_CONN.execute(
            """INSERT INTO descriptive_question_events
               (telegram_user_id, session_id, book_id, course, level, exam_type, year,
                chapter_slug, chapter_label, qno_text, marks_text, shown_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, session_id, q.get("book_id"), course, level, exam_type, year,
             chapter_slug, chapter_label, q.get("qno_text"), q.get("marks_text"), now),
        )
        DB_CONN.commit()
        return cur.lastrowid


def db_log_descriptive_answer_shown(event_id):
    if not event_id:
        return
    with DB_LOCK:
        DB_CONN.execute(
            "UPDATE descriptive_question_events SET answer_shown_at=? WHERE event_id=?",
            (_now(), event_id),
        )
        DB_CONN.commit()


def db_log_descriptive_pdf(event_id):
    if not event_id:
        return
    with DB_LOCK:
        DB_CONN.execute(
            "UPDATE descriptive_question_events SET pdf_requested_at=? WHERE event_id=?",
            (_now(), event_id),
        )
        DB_CONN.commit()


def db_log_mcq_shown(user_id, session_id, q, course, level) -> int:
    now = _now()
    with DB_LOCK:
        cur = DB_CONN.execute(
            """INSERT INTO mcq_attempts
               (telegram_user_id, session_id, mcq_id, course, level, exam_type, year,
                chapter_slug, chapter_label, qno_text, marks, difficulty, correct_option, shown_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, session_id, q.get("mcq_id"), course, level, q.get("exam_type"), q.get("year"),
             q.get("chapter_slug"), q.get("chapter_label"), q.get("qno_text"), q.get("marks"),
             q.get("difficulty"), q.get("correct_option"), now),
        )
        DB_CONN.commit()
        return cur.lastrowid


def db_log_mcq_answered(attempt_id, selected_option, is_correct):
    if not attempt_id:
        return
    with DB_LOCK:
        DB_CONN.execute(
            "UPDATE mcq_attempts SET selected_option=?, is_correct=?, answered_at=? WHERE attempt_id=?",
            (selected_option, 1 if is_correct else 0, _now(), attempt_id),
        )
        DB_CONN.commit()


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------
class QuestionBank:
    """Descriptive questions (book_questions_extracted.json)."""

    def __init__(self, json_path: str):
        self.json_path = json_path
        self.questions = []
        self.load()

    def load(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "questions" in data:
            data = data["questions"]
        self.questions = data
        for q in self.questions:
            q["_exam_type"] = self._detect_exam_type(q.get("src_text", ""))
            q["_year"] = self._detect_year(q.get("src_text", ""))
        logger.info(f"Loaded {len(self.questions)} descriptive questions from {self.json_path}")

    @staticmethod
    def _detect_exam_type(src_text: str) -> str:
        src = (src_text or "").upper()
        if "MTP" in src:
            return "MTP"
        if "RTP" in src:
            return "RTP"
        if "PYQ" in src or "PAST" in src:
            return "PYQ"
        return "OTHER"

    @staticmethod
    def _detect_year(src_text: str) -> str:
        m = re.search(r"(20\d{2})", src_text or "")
        return m.group(1) if m else "Unknown"

    def exam_types(self):
        return sorted({q["_exam_type"] for q in self.questions})

    def years(self, exam_type):
        subset = self.questions if exam_type == "MIX" else [
            q for q in self.questions if q["_exam_type"] == exam_type
        ]
        return sorted({q["_year"] for q in subset})

    def chapters(self, exam_type, year):
        subset = self._filter(exam_type, year)
        seen = {}
        for q in subset:
            slug = q.get("chapter_slug", "unknown")
            label = q.get("chapter_label", slug)
            seen[slug] = label
        return sorted(seen.items(), key=lambda kv: kv[1])

    def _filter(self, exam_type, year):
        subset = self.questions
        if exam_type != "MIX":
            subset = [q for q in subset if q["_exam_type"] == exam_type]
        if year != "MIX":
            subset = [q for q in subset if q["_year"] == year]
        return subset

    def filter_questions(self, exam_type, year, chapter_slug):
        subset = self._filter(exam_type, year)
        if chapter_slug != "ALL":
            subset = [q for q in subset if q.get("chapter_slug") == chapter_slug]
        return subset

    def get_by_book_id(self, book_id):
        for q in self.questions:
            if q.get("book_id") == book_id:
                return q
        return None


class McqBank:
    """MCQ questions (mcq_questions_extracted.json — see
    telegram/tools/build_exam_bot_mcq_export.py). exam_type/year are already
    explicit top-level fields here (unlike the descriptive bank), no
    pattern-detection needed."""

    def __init__(self, json_path: str):
        self.json_path = json_path
        self.questions = []
        self.load()

    def load(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "questions" in data:
            data = data["questions"]
        self.questions = data
        logger.info(f"Loaded {len(self.questions)} MCQ questions from {self.json_path}")

    def exam_types(self):
        return sorted({q.get("exam_type", "OTHER") for q in self.questions})

    def years(self, exam_type):
        subset = self.questions if exam_type == "MIX" else [
            q for q in self.questions if q.get("exam_type") == exam_type
        ]
        return sorted({q.get("year", "Unknown") for q in subset})

    def chapters(self, exam_type, year):
        subset = self._filter(exam_type, year)
        seen = {}
        for q in subset:
            slug = q.get("chapter_slug", "unknown")
            label = q.get("chapter_label", slug)
            seen[slug] = label
        return sorted(seen.items(), key=lambda kv: kv[1])

    def _filter(self, exam_type, year):
        subset = self.questions
        if exam_type != "MIX":
            subset = [q for q in subset if q.get("exam_type") == exam_type]
        if year != "MIX":
            subset = [q for q in subset if q.get("year") == year]
        return subset

    def filter_questions(self, exam_type, year, chapter_slug):
        subset = self._filter(exam_type, year)
        if chapter_slug != "ALL":
            subset = [q for q in subset if q.get("chapter_slug") == chapter_slug]
        return subset

    def get_by_id(self, mcq_id):
        for q in self.questions:
            if q.get("mcq_id") == mcq_id:
                return q
        return None


bank = QuestionBank(JSON_PATH)
mcq_bank = McqBank(MCQ_JSON_PATH)

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
def build_course_menu():
    keyboard = [[InlineKeyboardButton(c, callback_data=f"course:{c}")] for c in COURSES]
    text = "*Welcome to 1Lavya Exam Hub* \U0001F4DD\n\nSelect your *Course*:"
    return text, InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------------
# HANDLERS
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    db_upsert_student(user)
    context.user_data["session_id"] = db_start_session(user.id)

    text, markup = build_course_menu()
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
        text, markup = build_course_menu()
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
        return

    if action == "course":
        course = data.split(":", 1)[1]
        context.user_data["course"] = course
        db_update_session(session_id, course=course)
        levels = COURSES.get(course, [])
        keyboard = [[InlineKeyboardButton(lvl, callback_data=f"level:{lvl}")] for lvl in levels]
        await query.edit_message_text(
            f"Course: *{course}*\nSelect your *Level*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "level":
        level = data.split(":", 1)[1]
        context.user_data["level"] = level
        course = context.user_data.get("course")
        db_update_session(session_id, level=level)

        if (course, level) not in AVAILABLE_DATA:
            keyboard = [[InlineKeyboardButton("\U0001F519 Start Over", callback_data="restart")]]
            await query.edit_message_text(
                f"Course: *{course}* | Level: *{level}*\n\n"
                f"\U0001F6A7 Currently there are no questions for this Level. "
                f"We will shortly have questions on these as well!",
                parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

        keyboard = [
            [InlineKeyboardButton("\U0001F4DD Descriptive", callback_data="mode:descriptive")],
            [InlineKeyboardButton("\u2705 MCQ", callback_data="mode:mcq")],
        ]
        await query.edit_message_text(
            f"Course: *{course}* | Level: *{level}*\nWhat would you like to practice?",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "mode":
        mode = data.split(":", 1)[1]  # "descriptive" or "mcq"
        context.user_data["mode"] = mode
        db_update_session(session_id, mode=mode)
        bank_obj = bank if mode == "descriptive" else mcq_bank
        exam_types = bank_obj.exam_types()
        keyboard = [[InlineKeyboardButton(et, callback_data=f"type:{et}")] for et in exam_types]
        keyboard.append([InlineKeyboardButton(MIX_LABEL, callback_data="type:MIX")])
        label = "Descriptive" if mode == "descriptive" else "MCQ"
        await query.edit_message_text(
            f"Mode: *{label}*\nSelect *Exam Type*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "type":
        exam_type = data.split(":", 1)[1]
        context.user_data["exam_type"] = exam_type
        mode = context.user_data.get("mode")
        bank_obj = bank if mode == "descriptive" else mcq_bank
        years = bank_obj.years(exam_type)
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
        bank_obj = bank if mode == "descriptive" else mcq_bank
        chapters = bank_obj.chapters(exam_type, year)
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
        bank_obj = bank if mode == "descriptive" else mcq_bank

        matches = bank_obj.filter_questions(exam_type, year, chapter_slug)
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


# ---------------------------------------------------------------------------
# DESCRIPTIVE FLOW
# ---------------------------------------------------------------------------
async def send_question(query, context):
    queue = context.user_data.get("queue", [])
    pos = context.user_data.get("queue_pos", 0)

    if pos >= len(queue):
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\u2705 You've gone through all questions in this selection. Use /start to pick another set.",
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

    keyboard = [
        [InlineKeyboardButton("\U0001F4C4 Get as PDF", callback_data=f"pdf:{book_id}")],
        [InlineKeyboardButton("\u23ED Next Question", callback_data="next")],
    ]

    await send_long_message(
        context,
        query.message.chat_id,
        f"<b>Answer:</b>\n\n{answer_text}{note_block}",
        reply_markup=InlineKeyboardMarkup(keyboard),
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
        caption="Here's your question + answer as a PDF.",
    )


# ---------------------------------------------------------------------------
# MCQ FLOW
# ---------------------------------------------------------------------------
async def send_mcq(query, context):
    queue = context.user_data.get("queue", [])
    pos = context.user_data.get("queue_pos", 0)

    if pos >= len(queue):
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\u2705 You've gone through all MCQs in this selection. Use /start to pick another set.",
        )
        return

    mcq_id = queue[pos]
    context.user_data["queue_pos"] = pos + 1
    q = mcq_bank.get_by_id(mcq_id)

    meta = (
        f"\U0001F4C4 {q.get('exam_type','')} {q.get('year','')} | {q.get('qno_text','')}\n"
        f"\U0001F3F7 {q.get('topic_text','')}\n"
        f"Marks: {q.get('marks','')} | Difficulty: {q.get('difficulty','')}"
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

    keyboard = [[InlineKeyboardButton("\u23ED Next Question", callback_data="next")]]
    result_text = f"{icon}\nCorrect Answer: <b>({correct})</b>\n\n{explanation}"

    await send_long_message(
        context, query.message.chat_id, result_text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


def main():
    if BOT_TOKEN == "PASTE_YOUR_BOTFATHER_TOKEN_HERE":
        raise SystemExit(
            "Set your bot token first: either edit BOT_TOKEN in this file, "
            "or set the TELEGRAM_EXAM_BOT_TOKEN environment variable."
        )

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_router))

    logger.info("1Lavya Exam Hub Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
