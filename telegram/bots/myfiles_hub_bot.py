"""
1Lavya MyFiles Hub Bot (Bot 3)
-------------------------------
- Email OTP authentication (new/existing user)
- Free-form TAGGING, not a folder hierarchy: each student owns their own tag
  list (create/rename/delete anytime), picks up to MAX_TAGS_PER_FILE tags per
  upload from a multi-select keyboard, and a file can carry several tags at
  once -- there is no fixed Category/Subject/Level/Chapter structure
- Upload files, photos, or links; multiple sent together are buffered briefly,
  then the bot asks whether they all share the same tags (applies one tag set
  to all) or should be sent one at a time
- Per-user folder on disk, named by Telegram chat_id
- SQLite database (users, otps, files, tags, file_tags, activity_log) --
  safe for concurrent access
- Retrieval is tag-based: pick one or more tags, choose ALL (AND) or ANY (OR)
  to combine them, then browse/send/request-deletion of the matching files
- Bulk download auto-splits into ~45MB zip parts (Telegram's cap is 50MB)
- Per-student stats (file count / size, grouped by tag)
- Soft delete: files are hidden, never actually removed from disk -- deleting
  is a deliberate, separate menu action gated behind an emailed OTP
- Every login, upload, retrieval, and delete is recorded in activity_log

SETUP (do this before running):
1. pip install python-telegram-bot[job-queue] python-dotenv --break-system-packages
   (sqlite3, smtplib, zipfile, secrets are all in the Python standard library)
2. Copy telegram/.env.example to telegram/.env (gitignored -- never commit
   it) and fill in TELEGRAM_MYFILES_BOT_TOKEN, MYFILES_SMTP_EMAIL,
   MYFILES_SMTP_PASSWORD there. This script loads telegram/.env
   automatically at startup -- no shell exports needed for local runs.
3. BASE_STORAGE_PATH/DB_PATH below are auto-derived from this script's own
   location (REPO_ROOT) -- no manual editing needed even if this repo is
   cloned/moved elsewhere, as long as telegram/ keeps its folder shape.
4. Run: python myfiles_hub_bot.py
   Keep the terminal/laptop running for the bot to stay online.

NOTE ON "existing vs new user" / email verification:
   This script treats ANY email address as valid to register on first use
   (there's no pre-existing student list to check against). If you already
   have a master list of enrolled student emails, tell your developer to
   plug that check in at the marked "# TODO: validate against enrolled
   student list" line, so only pre-approved emails can register.
"""

import os
import re
import sys
import asyncio
import sqlite3
import secrets
import smtplib
import zipfile
import logging
from pathlib import Path
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# CONFIG — edit these for your setup
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]   # telegram/bots/myfiles_hub_bot.py -> repo root
load_dotenv(REPO_ROOT / "telegram" / ".env")      # secrets live in telegram/.env (gitignored)

# Heartbeat only (added 2026-08-10) -- this bot is NOT part of the BOT_ID/
# bots.json/shared-DB migration (its own users/otps/files/tags/activity_log
# stay exactly where they are, see telegram/database/schema.sql's own note
# on why). It still writes a heartbeat to the shared platform DB, purely so
# telegram/tools/manage_bots.py and the analytics dashboard can show it
# online/offline alongside every other bot -- see main() below.
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402 -- must follow the sys.path.insert() above
import log_rotation  # noqa: E402 -- telegram/database/log_rotation.py, Layer 1 of the log-rotation policy (2026-08-18)
import rate_limiter  # noqa: E402 -- telegram/bots/rate_limiter.py, per-user flood/abuse controls (2026-08-24, SECURITY.md Phase 1) -- same directory (telegram/bots/), no extra sys.path needed
import input_guard  # noqa: E402 -- telegram/bots/input_guard.py, free-text sanitization + upload validation (2026-08-24, SECURITY.md Phase 1)
import activity_logger  # noqa: E402 -- telegram/bots/activity_logger.py, the fine-grained activity log + correlation IDs (2026-08-17) -- writes to the SHARED platform.db like send_heartbeat() already does, even though this bot's own primary data stays in its separate myfiles_hub.db
MYFILES_BOT_ID = "1lavya-myfileshub"   # must match telegram/config/bots.json's entry

BOT_TOKEN = os.environ.get("TELEGRAM_MYFILES_BOT_TOKEN", "PASTE_YOUR_BOTFATHER_TOKEN_HERE")
# Derived from REPO_ROOT (set above from this script's own location) so the
# bot keeps working unmodified if this repo -- or just telegram/ -- is
# cloned/moved to a different path or computer. Was hardcoded to this
# session's own D:\EffCorp_Projects\cap-online\... path until 2026-08-12;
# fixed as part of the telegram/ portability pass -- see FIRST_PROMPT.md.
BASE_STORAGE_PATH = str(REPO_ROOT / "telegram" / "assets" / "myfiles_bot" / "uploads")  # per-user folders created here
DB_PATH = str(REPO_ROOT / "telegram" / "assets" / "myfiles_bot" / "myfiles_hub.db")     # SQLite database file

# SMTP settings for sending OTP emails (e.g. a Gmail account with an "App Password")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.environ.get("MYFILES_SMTP_EMAIL", "PASTE_YOUR_SENDING_EMAIL_HERE")
SMTP_PASSWORD = os.environ.get("MYFILES_SMTP_PASSWORD", "PASTE_YOUR_GMAIL_APP_PASSWORD_HERE")

OTP_VALID_MINUTES = 10
TELEGRAM_SAFE_LIMIT_MB = 45  # keep under Telegram's 50MB hard cap
BATCH_DEBOUNCE_SECONDS = 1.5  # how long to wait for more files before asking about tagging
MAX_TAGS_PER_FILE = 5  # cap on how many tags a student can assign to one upload

# Every new student gets these to start with -- fully theirs from that point on
# (rename/delete/add freely). Purely a convenience seed, not a fixed taxonomy.
STARTER_TAGS = [
    "Study Material", "Practice/Exam Material",
    "Accounting", "Costing", "Taxation", "Law", "Audit",
]

# BUG FIXED 2026-08-18: this used to write to its OWN separate file
# (assets/myfiles_bot/myfiles_hub.log, next to DB_PATH) via an explicit
# FileHandler, on TOP OF manage_bots.py's own OS-level stdout/stderr
# capture of this same StreamHandler's output into
# database/run/logs/1lavya-myfileshub.log -- two full copies of every log
# line, in two different locations, neither one ever read by the Admin
# Portal's Bot-wise Logs viewer (confirmed: it only ever reads
# manage_bots.LOG_DIR / f"{bot_id}.log"). Found while auditing every
# process's logging setup for LOGGING-ARCHITECTURE.md's rotation policy --
# the stray copy was already 12.5MB, pure waste. Consolidated onto the
# SAME bounded, rotated handler every other bot now uses, writing to the
# ONE path that's actually read.
logging.basicConfig(
    format=activity_logger.LOG_FORMAT_WITH_CORRELATION,
    level=logging.INFO,
    handlers=log_rotation.build_handlers(MYFILES_BOT_ID),
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # 2026-08-17: see LOGGING-ARCHITECTURE.md §6
activity_logger.install_correlation_filter()
logger = logging.getLogger(__name__)

# Conversation states
(
    AUTH_MENU, AUTH_EMAIL, AUTH_OTP, PROFILE_NAME,
    MAIN_MENU,
    UPLOAD_WAIT_ITEM, UPLOAD_TAG_SELECT, UPLOAD_TAG_CREATE,
    RETRIEVE_TAG_SELECT, RETRIEVE_RESULTS,
    DELETE_OTP,
    TAG_MANAGE, TAG_MANAGE_CREATE, TAG_MANAGE_RENAME,
) = range(14)

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            email TEXT,
            display_name TEXT,
            verified INTEGER DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS otps (
            chat_id INTEGER PRIMARY KEY,
            email TEXT,
            otp_code TEXT,
            expires_at TEXT,
            purpose TEXT DEFAULT 'login'   -- 'login' or 'delete', keeps the two kinds of OTP from crossing over
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            item_type TEXT,        -- 'file' or 'link'
            original_name TEXT,
            stored_path TEXT,      -- NULL for links
            link_url TEXT,         -- NULL for files
            category TEXT,
            subject TEXT,
            level TEXT,
            chapter TEXT,
            file_size_bytes INTEGER,  -- NULL for links
            uploaded_at TEXT,
            is_deleted INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            email TEXT,
            action TEXT,           -- login/register/upload/retrieve/delete_request/delete_confirm/stats_view/tag_*
            detail TEXT,
            file_size_bytes INTEGER,
            created_at TEXT
        );

        -- Each student owns their own tag list -- not shared, not a fixed taxonomy.
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            name TEXT,
            created_at TEXT
        );

        -- Many-to-many: a file can carry several tags (capped at MAX_TAGS_PER_FILE
        -- by the app, not the schema), a tag can label many files.
        CREATE TABLE IF NOT EXISTS file_tags (
            file_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (file_id, tag_id)
        );
        """
    )
    conn.commit()

    # --- lightweight migrations for a DB created before these columns existed ---
    file_cols = {row[1] for row in conn.execute("PRAGMA table_info(files)")}
    if "file_size_bytes" not in file_cols:
        conn.execute("ALTER TABLE files ADD COLUMN file_size_bytes INTEGER")

    otp_cols = {row[1] for row in conn.execute("PRAGMA table_info(otps)")}
    if "purpose" not in otp_cols:
        conn.execute("ALTER TABLE otps ADD COLUMN purpose TEXT DEFAULT 'login'")

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# TAGS (student-owned, free-form -- create/rename/delete anytime)
# ---------------------------------------------------------------------------
def list_tags(chat_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name FROM tags WHERE chat_id = ? ORDER BY name COLLATE NOCASE", (chat_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_or_create_tag(chat_id, name):
    """Case-insensitive dedupe per student -- 'Accounts' and 'accounts' are the same tag."""
    name = name.strip()
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM tags WHERE chat_id = ? AND name = ? COLLATE NOCASE", (chat_id, name)
    ).fetchone()
    if existing:
        conn.close()
        return existing["id"]
    cur = conn.execute(
        "INSERT INTO tags (chat_id, name, created_at) VALUES (?, ?, ?)",
        (chat_id, name, datetime.now().isoformat()),
    )
    conn.commit()
    tag_id = cur.lastrowid
    conn.close()
    return tag_id


def rename_tag(chat_id, tag_id, new_name):
    new_name = new_name.strip()
    conn = get_db()
    clash = conn.execute(
        "SELECT id FROM tags WHERE chat_id = ? AND name = ? COLLATE NOCASE AND id != ?",
        (chat_id, new_name, tag_id),
    ).fetchone()
    if clash:
        conn.close()
        return False  # a different tag with that name already exists
    conn.execute("UPDATE tags SET name = ? WHERE id = ? AND chat_id = ?", (new_name, tag_id, chat_id))
    conn.commit()
    conn.close()
    return True


def delete_tag(chat_id, tag_id):
    """Removes the tag and un-tags any files that had it -- the files themselves
    are never touched."""
    conn = get_db()
    conn.execute("DELETE FROM file_tags WHERE tag_id = ? AND tag_id IN (SELECT id FROM tags WHERE chat_id = ?)",
                 (tag_id, chat_id))
    conn.execute("DELETE FROM tags WHERE id = ? AND chat_id = ?", (tag_id, chat_id))
    conn.commit()
    conn.close()


def get_file_tags(file_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT t.id, t.name FROM tags t JOIN file_tags ft ON ft.tag_id = t.id WHERE ft.file_id = ? "
        "ORDER BY t.name COLLATE NOCASE",
        (file_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def seed_starter_tags(chat_id):
    for name in STARTER_TAGS:
        get_or_create_tag(chat_id, name)


def render_tag_picker(tags, selected_ids, toggle_prefix, done_callback, done_label=None, extra_rows=None):
    """Shared multi-select keyboard builder for both the upload tag-picker and
    the retrieval tag-picker -- one row per tag with a checkbox glyph."""
    keyboard = []
    for t in tags:
        mark = "☑️" if t["id"] in selected_ids else "⬜"
        keyboard.append([InlineKeyboardButton(f"{mark} {t['name']}", callback_data=f"{toggle_prefix}{t['id']}")])
    if extra_rows:
        keyboard.extend(extra_rows)
    label = done_label or f"✅ Done ({len(selected_ids)} selected)"
    keyboard.append([InlineKeyboardButton(label, callback_data=done_callback)])
    return InlineKeyboardMarkup(keyboard)


def user_folder(chat_id):
    folder = os.path.join(BASE_STORAGE_PATH, str(chat_id))
    os.makedirs(folder, exist_ok=True)
    return folder


def log_activity(chat_id, action, detail="", file_size_bytes=None, email=None):
    """Best-effort activity record -- never let a logging failure break the bot."""
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO activity_log (chat_id, email, action, detail, file_size_bytes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (chat_id, email, action, detail, file_size_bytes, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception:
        logger.exception("Failed to write activity_log row (chat_id=%s, action=%s)", chat_id, action)


# ---------------------------------------------------------------------------
# OTP / EMAIL
# ---------------------------------------------------------------------------
def send_otp_email(to_email: str, otp_code: str):
    subject = "Your 1Lavya MyFiles Hub verification code"
    body = f"Your OTP is: {otp_code}\nThis code is valid for {OTP_VALID_MINUTES} minutes."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [to_email], msg.as_string())


def send_delete_otp_email(to_email: str, otp_code: str, file_count: int):
    subject = "1Lavya MyFiles Hub -- confirm removing files from your account"
    body = (
        f"You requested to remove {file_count} file(s) from your MyFiles Hub account.\n\n"
        f"Confirmation code: {otp_code}\n"
        f"This code is valid for {OTP_VALID_MINUTES} minutes.\n\n"
        f"What this does: the {file_count} file(s) will be removed from your account -- "
        f"hidden from 'My Files' and search, and no longer retrievable by you through the "
        f"bot. It does not instantly and irreversibly erase the underlying file from storage.\n\n"
        f"If you did not request this, you can safely ignore this email -- nothing will be "
        f"removed without this code."
    )
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [to_email], msg.as_string())


def generate_and_send_otp(chat_id: int, email: str, purpose: str = "login", file_count: int = 0):
    otp_code = f"{secrets.randbelow(1000000):06d}"
    expires_at = (datetime.now() + timedelta(minutes=OTP_VALID_MINUTES)).isoformat()

    conn = get_db()
    conn.execute("DELETE FROM otps WHERE chat_id = ?", (chat_id,))
    conn.execute(
        "INSERT INTO otps (chat_id, email, otp_code, expires_at, purpose) VALUES (?, ?, ?, ?, ?)",
        (chat_id, email, otp_code, expires_at, purpose),
    )
    conn.commit()
    conn.close()

    if purpose == "delete":
        send_delete_otp_email(email, otp_code, file_count)
    else:
        send_otp_email(email, otp_code)


def verify_otp(chat_id: int, entered_code: str, purpose: str = "login") -> bool:
    conn = get_db()
    row = conn.execute("SELECT * FROM otps WHERE chat_id = ?", (chat_id,)).fetchone()
    if not row:
        conn.close()
        return False
    row_purpose = row["purpose"] if "purpose" in row.keys() and row["purpose"] else "login"
    valid = (
        row["otp_code"] == entered_code.strip()
        and datetime.now() < datetime.fromisoformat(row["expires_at"])
        and row_purpose == purpose
    )
    if valid:
        conn.execute("DELETE FROM otps WHERE chat_id = ?", (chat_id,))
        conn.commit()
    conn.close()
    return valid


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
URL_RE = re.compile(r"^https?://\S+$")

# Casual openers that should wake the bot the same as /start, for a chat that
# hasn't started a conversation yet. Only ever checked as an entry_point (i.e.
# no active conversation) -- can't misfire on ordinary replies mid-flow, such as
# someone typing "hi" as a chapter name.
GREETING_RE = re.compile(r"^\s*(hi+|hey+|hello+|hiya|yo|namaste)\s*[!.]*\s*$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# AUTH HANDLERS
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
    conn.close()

    if user and user["verified"]:
        return await show_main_menu(update, context)

    keyboard = [
        [InlineKeyboardButton("I'm an existing user", callback_data="auth:existing")],
        [InlineKeyboardButton("I'm a new user", callback_data="auth:new")],
    ]
    await update.message.reply_text(
        "*Welcome to 1Lavya MyFiles Hub* \U0001F4C1\n\nAre you an existing user or a new user?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return AUTH_MENU


async def auth_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["is_new_user"] = query.data == "auth:new"
    await query.edit_message_text("Please enter your email address to receive a verification code:")
    return AUTH_EMAIL


async def auth_email_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if not EMAIL_RE.match(email):
        await update.message.reply_text("That doesn't look like a valid email. Please try again:")
        return AUTH_EMAIL

    # TODO: validate against enrolled student list here, if you maintain one.

    chat_id = update.effective_chat.id
    context.user_data["pending_email"] = email
    try:
        generate_and_send_otp(chat_id, email)
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        await update.message.reply_text(
            "Sorry, we couldn't send the verification email right now. Please try again in a moment."
        )
        return AUTH_EMAIL

    await update.message.reply_text(f"A 6-digit code was sent to {email}. Please enter it here:")
    return AUTH_OTP


async def auth_otp_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    code = update.message.text.strip()

    if not verify_otp(chat_id, code, purpose="login"):
        await update.message.reply_text("That code is incorrect or expired. Please try again, or /start over.")
        return AUTH_OTP

    email = context.user_data["pending_email"]
    conn = get_db()
    existing = conn.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE users SET email = ?, verified = 1 WHERE chat_id = ?", (email, chat_id)
        )
        conn.commit()
        conn.close()
        log_activity(chat_id, "login", email=email)
        await update.message.reply_text("\u2705 Verified! Welcome back.")
        return await show_main_menu(update, context)
    else:
        conn.execute(
            "INSERT INTO users (chat_id, email, verified, created_at) VALUES (?, ?, 1, ?)",
            (chat_id, email, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        log_activity(chat_id, "register", email=email)
        await update.message.reply_text("\u2705 Verified! What name should we save for your profile?")
        return PROFILE_NAME


async def profile_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    chat_id = update.effective_chat.id
    conn = get_db()
    conn.execute("UPDATE users SET display_name = ? WHERE chat_id = ?", (name, chat_id))
    conn.commit()
    conn.close()
    seed_starter_tags(chat_id)
    await update.message.reply_text(
        f"Thanks, {name}! You're all set. I've given you a starter set of tags "
        f"({', '.join(STARTER_TAGS)}) -- rename, delete, or add to them anytime from "
        f"\U0001F3F7️ My Tags."
    )
    return await show_main_menu(update, context)


# ---------------------------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------------------------
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("\U0001F4E4 Upload a file/link", callback_data="menu:upload")],
        [InlineKeyboardButton("\U0001F4E5 My Files", callback_data="menu:myfiles")],
        [InlineKeyboardButton("\U0001F3F7️ My Tags", callback_data="menu:tags")],
        [InlineKeyboardButton("\U0001F4CA My Stats", callback_data="menu:stats")],
        [InlineKeyboardButton("\U0001F5D1 Delete My Files", callback_data="menu:delete")],
    ]
    target = update.message or update.callback_query.message
    await target.reply_text("What would you like to do?", reply_markup=InlineKeyboardMarkup(keyboard))
    return MAIN_MENU


async def main_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "menu:upload":
        await query.edit_message_text(
            "Send me the file/photo (as a document or a photo) OR paste a link now.\n"
            "You can send several at once -- I'll ask about tagging once they're all in."
        )
        return UPLOAD_WAIT_ITEM
    elif query.data == "menu:myfiles":
        context.user_data["retrieve_mode"] = "browse"
        return await retrieve_start(update, context)
    elif query.data == "menu:delete":
        context.user_data["retrieve_mode"] = "delete"
        return await retrieve_start(update, context)
    elif query.data == "menu:stats":
        return await show_my_stats(update, context)
    elif query.data == "menu:tags":
        return await show_tag_manager(update, context)
    elif query.data == "menu:done":
        await query.edit_message_text(
            "\U0001F44D All set! Send /start anytime to come back to the menu."
        )
        return MAIN_MENU


async def show_my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = update.callback_query

    conn = get_db()
    total_row = conn.execute(
        "SELECT COUNT(*) AS c, COALESCE(SUM(file_size_bytes), 0) AS s "
        "FROM files WHERE chat_id = ? AND is_deleted = 0",
        (chat_id,),
    ).fetchone()
    untagged_row = conn.execute(
        "SELECT COUNT(*) AS c FROM files f "
        "WHERE f.chat_id = ? AND f.is_deleted = 0 "
        "AND NOT EXISTS (SELECT 1 FROM file_tags ft WHERE ft.file_id = f.id)",
        (chat_id,),
    ).fetchone()
    by_tag = conn.execute(
        "SELECT t.name, COUNT(*) AS c, COALESCE(SUM(f.file_size_bytes), 0) AS s "
        "FROM tags t JOIN file_tags ft ON ft.tag_id = t.id "
        "JOIN files f ON f.id = ft.file_id AND f.is_deleted = 0 "
        "WHERE t.chat_id = ? GROUP BY t.id ORDER BY c DESC",
        (chat_id,),
    ).fetchall()
    conn.close()

    def fmt_size(n):
        n = n or 0
        if n >= 1024 * 1024:
            return f"{n / (1024 * 1024):.1f} MB"
        if n >= 1024:
            return f"{n / 1024:.1f} KB"
        return f"{n} bytes"

    lines = [
        "\U0001F4CA *Your MyFiles Hub stats*",
        f"Total files/links: {total_row['c']}",
        f"Total size: {fmt_size(total_row['s'])}",
        "",
        "*By tag* (a file with several tags counts under each):",
    ]
    if by_tag:
        for r in by_tag:
            lines.append(f"\u2022 {r['name']}: {r['c']} file(s), {fmt_size(r['s'])}")
    else:
        lines.append("No tagged files yet.")
    if untagged_row["c"]:
        lines.append(f"\u2022 (untagged): {untagged_row['c']} file(s)")

    log_activity(chat_id, "stats_view")

    text = "\n".join(lines)
    if query:
        await query.answer()
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return await show_main_menu(update, context)




# ---------------------------------------------------------------------------
# TAG MANAGEMENT (create / rename / delete -- students own their tag list)
# ---------------------------------------------------------------------------
async def show_tag_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tags = list_tags(chat_id)

    keyboard = [[InlineKeyboardButton("➕ Create New Tag", callback_data="tagmgr_new")]]
    for t in tags:
        keyboard.append([
            InlineKeyboardButton(f"✏️ {t['name']}", callback_data=f"tagmgr_rename:{t['id']}"),
            InlineKeyboardButton("🗑️", callback_data=f"tagmgr_delete:{t['id']}"),
        ])
    keyboard.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="menu:done")])

    text = "\U0001F3F7️ *Your Tags*\n" + (
        "Tap ✏️ to rename or 🗑️ to delete a tag. Deleting a tag never deletes the "
        "files that had it -- they just lose that tag."
        if tags else "You don't have any tags yet -- create your first one below."
    )

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    return TAG_MANAGE


async def tag_manager_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "tagmgr_new":
        await query.answer()
        await query.edit_message_text("Type the name for the new tag:")
        return TAG_MANAGE_CREATE

    if data.startswith("tagmgr_rename:"):
        await query.answer()
        tag_id = int(data.split(":", 1)[1])
        context.user_data["tagmgr_rename_id"] = tag_id
        await query.edit_message_text("Type the new name for this tag:")
        return TAG_MANAGE_RENAME

    if data.startswith("tagmgr_delete:"):
        tag_id = int(data.split(":", 1)[1])
        chat_id = update.effective_chat.id
        conn = get_db()
        tag = conn.execute("SELECT name FROM tags WHERE id = ? AND chat_id = ?", (tag_id, chat_id)).fetchone()
        file_count = conn.execute("SELECT COUNT(*) AS c FROM file_tags WHERE tag_id = ?", (tag_id,)).fetchone()["c"]
        conn.close()
        if not tag:
            await query.answer("That tag no longer exists.", show_alert=True)
            return await show_tag_manager(update, context)
        await query.answer()
        keyboard = [
            [InlineKeyboardButton("✅ Yes, delete it", callback_data=f"tagmgr_delconfirm:{tag_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="tagmgr_delcancel")],
        ]
        await query.edit_message_text(
            f"Delete tag '{tag['name']}'? It's on {file_count} file(s) -- they'll keep "
            f"their other tags, just lose this one. The files themselves are never touched.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return TAG_MANAGE

    if data.startswith("tagmgr_delconfirm:"):
        tag_id = int(data.split(":", 1)[1])
        chat_id = update.effective_chat.id
        delete_tag(chat_id, tag_id)
        log_activity(chat_id, "tag_delete", detail=str(tag_id))
        await query.answer("Tag deleted.")
        return await show_tag_manager(update, context)

    if data == "tagmgr_delcancel":
        await query.answer("Cancelled.")
        return await show_tag_manager(update, context)

    await query.answer()
    return await show_tag_manager(update, context)


async def tag_manager_create_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    chat_id = update.effective_chat.id
    if not name or len(name) > 40:
        await update.message.reply_text("Please send a short tag name (1-40 characters).")
        return TAG_MANAGE_CREATE
    get_or_create_tag(chat_id, name)
    log_activity(chat_id, "tag_create", detail=name)
    await update.message.reply_text(f"✅ Tag '{name}' created.")
    return await show_tag_manager(update, context)


async def tag_manager_rename_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text.strip()
    chat_id = update.effective_chat.id
    tag_id = context.user_data.pop("tagmgr_rename_id", None)
    if not new_name or len(new_name) > 40:
        context.user_data["tagmgr_rename_id"] = tag_id
        await update.message.reply_text("Please send a short tag name (1-40 characters).")
        return TAG_MANAGE_RENAME
    if tag_id is None:
        await update.message.reply_text("Something went wrong -- let's start over.")
        return await show_tag_manager(update, context)

    ok = rename_tag(chat_id, tag_id, new_name)
    if not ok:
        await update.message.reply_text(f"You already have a tag named '{new_name}'. Try a different name.")
        context.user_data["tagmgr_rename_id"] = tag_id
        return TAG_MANAGE_RENAME

    log_activity(chat_id, "tag_rename", detail=new_name)
    await update.message.reply_text(f"✅ Renamed to '{new_name}'.")
    return await show_tag_manager(update, context)

# ---------------------------------------------------------------------------
# UPLOAD + TAGGING
# ---------------------------------------------------------------------------
async def _parse_incoming_item(update: Update, chat_id: int):
    """Turn one incoming message (document, photo, or link) into an item dict,
    or return None if the message isn't a recognised upload."""
    message = update.message

    if message.document:
        doc = message.document
        # SECURITY.md §3.A.6 -- validate BEFORE downloading, so a rejected
        # upload (too large, or a blocked executable/script extension)
        # never touches disk at all.
        ok, reason = input_guard.validate_upload(doc.file_name, doc.file_size)
        if not ok:
            return {"rejected": True, "reason": reason}
        folder = user_folder(chat_id)
        stored_path = os.path.join(folder, doc.file_name)
        file_obj = await doc.get_file()
        await file_obj.download_to_drive(stored_path)
        size = doc.file_size or (os.path.getsize(stored_path) if os.path.exists(stored_path) else None)
        return {
            "item_type": "file",
            "original_name": doc.file_name,
            "stored_path": stored_path,
            "link_url": None,
            "file_size_bytes": size,
        }

    if message.photo:
        photo = message.photo[-1]  # highest-resolution size Telegram sent
        # No extension check here (Telegram always sends a real .jpg for a
        # photo message) -- just the size ceiling, same reasoning as
        # documents above.
        ok, reason = input_guard.validate_upload(None, photo.file_size)
        if not ok:
            return {"rejected": True, "reason": reason}
        folder = user_folder(chat_id)
        filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        stored_path = os.path.join(folder, filename)
        file_obj = await photo.get_file()
        await file_obj.download_to_drive(stored_path)
        size = photo.file_size or (os.path.getsize(stored_path) if os.path.exists(stored_path) else None)
        return {
            "item_type": "file",
            "original_name": filename,
            "stored_path": stored_path,
            "link_url": None,
            "file_size_bytes": size,
        }

    if message.text and URL_RE.match(message.text.strip()):
        url = message.text.strip()
        return {
            "item_type": "link",
            "original_name": url,
            "stored_path": None,
            "link_url": url,
            "file_size_bytes": None,
        }

    return None


async def upload_item_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fires once per incoming file/photo/link/text while in UPLOAD_WAIT_ITEM.
    Doesn't ask about tags itself -- buffers the item and (re)schedules
    _finalize_batch, so a group of files sent together get collected before we
    ask how to tag them.

    Also doubles as the fallback text handler for 'type a tag name' when that
    prompt was sent by the background finalize task -- a background task can't
    move the formal conversation state, so we're still nominally in
    UPLOAD_WAIT_ITEM at that point and must recognise + delegate here."""
    if context.user_data.get("upload_tag_create_mode") and update.message.text:
        return await upload_tag_create_received(update, context)

    # SECURITY.md §3.A.2 -- a dedicated limit on uploads specifically
    # (each one downloads a real file to disk), checked before doing any
    # work at all.
    if not await rate_limiter.check_and_notify(update, context, MYFILES_BOT_ID, "upload"):
        return UPLOAD_WAIT_ITEM

    chat_id = update.effective_chat.id
    item = await _parse_incoming_item(update, chat_id)
    if item is None:
        await update.message.reply_text("Please send a document file, a photo, or a valid http(s) link.")
        return UPLOAD_WAIT_ITEM
    if item.get("rejected"):
        await update.message.reply_text(f"⚠️ {item['reason']}")
        return UPLOAD_WAIT_ITEM

    batch = context.user_data.setdefault("pending_batch", [])
    batch.append(item)

    old_task = context.user_data.get("batch_finalize_task")
    if old_task and not old_task.done():
        old_task.cancel()
    context.user_data["batch_finalize_task"] = asyncio.create_task(
        _finalize_batch(context, chat_id)
    )
    return UPLOAD_WAIT_ITEM


async def _finalize_batch(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Runs BATCH_DEBOUNCE_SECONDS after the most recent item arrived. If a newer
    item superseded this task in the meantime, asyncio.sleep raises CancelledError
    and we just exit -- the newer task will run instead."""
    try:
        await asyncio.sleep(BATCH_DEBOUNCE_SECONDS)
        batch = context.user_data.get("pending_batch") or []
        if not batch:
            return

        if len(batch) == 1:
            await enter_tag_selection(context, chat_id, context.user_data)
        else:
            keyboard = [
                [InlineKeyboardButton("✅ Yes, same tags for all", callback_data="batch_same:yes")],
                [InlineKeyboardButton("❌ No, they're different", callback_data="batch_same:no")],
            ]
            await context.bot.send_message(
                chat_id,
                f"You sent {len(batch)} files. Do they all pertain to the same tags?",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("Error finalizing upload batch for chat_id=%s", chat_id)


async def batch_same_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    batch = context.user_data.get("pending_batch") or []

    if query.data == "batch_same:no":
        for item in batch:
            path = item.get("stored_path")
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    logger.warning("Could not remove discarded batch file: %s", path)
        context.user_data.pop("pending_batch", None)
        await query.edit_message_text(
            "Okay -- please send only files that share the same tags together, "
            "or send them one at a time."
        )
        return await show_main_menu(update, context)

    await query.edit_message_text(f"Great -- tag all {len(batch)} files:")
    return await enter_tag_selection(context, chat_id, context.user_data)


async def enter_tag_selection(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_data: dict):
    """Shows the multi-select tag picker for whatever's sitting in pending_batch
    (1 or more items, always tagged identically as a set). If the student has no
    tags at all yet, walks them through creating a first one before any picker
    can be shown."""
    user_data["upload_selected_tag_ids"] = set()
    tags = list_tags(chat_id)

    if not tags:
        user_data["upload_tag_create_mode"] = "first"
        await context.bot.send_message(
            chat_id,
            "You don't have any tags yet. Let's create your first one -- "
            "type a short name (e.g. 'Accounting' or 'Chapter 5'):",
        )
        return UPLOAD_TAG_CREATE

    keyboard = render_tag_picker(
        tags, user_data["upload_selected_tag_ids"], "utag:", "utag_done",
        extra_rows=[[InlineKeyboardButton("➕ New Tag", callback_data="utag_new")]],
    )
    await context.bot.send_message(
        chat_id, f"Pick up to {MAX_TAGS_PER_FILE} tags for this upload:", reply_markup=keyboard
    )
    return UPLOAD_TAG_SELECT


async def upload_tag_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    tag_id = int(query.data.split(":", 1)[1])
    selected = context.user_data.setdefault("upload_selected_tag_ids", set())

    if tag_id in selected:
        selected.remove(tag_id)
    elif len(selected) >= MAX_TAGS_PER_FILE:
        await query.answer(f"You can pick at most {MAX_TAGS_PER_FILE} tags per file.", show_alert=True)
        return UPLOAD_TAG_SELECT
    else:
        selected.add(tag_id)
    await query.answer()

    tags = list_tags(chat_id)
    keyboard = render_tag_picker(
        tags, selected, "utag:", "utag_done",
        extra_rows=[[InlineKeyboardButton("➕ New Tag", callback_data="utag_new")]],
    )
    await query.edit_message_reply_markup(reply_markup=keyboard)
    return UPLOAD_TAG_SELECT


async def upload_tag_new_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["upload_tag_create_mode"] = "additional"
    await query.message.reply_text("Type the name for the new tag:")
    return UPLOAD_TAG_CREATE


async def upload_tag_create_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    chat_id = update.effective_chat.id
    if not name or len(name) > 40:
        await update.message.reply_text("Please send a short tag name (1-40 characters).")
        return UPLOAD_TAG_CREATE

    tag_id = get_or_create_tag(chat_id, name)
    context.user_data.pop("upload_tag_create_mode", None)
    selected = context.user_data.setdefault("upload_selected_tag_ids", set())
    if len(selected) < MAX_TAGS_PER_FILE:
        selected.add(tag_id)

    tags = list_tags(chat_id)
    keyboard = render_tag_picker(
        tags, selected, "utag:", "utag_done",
        extra_rows=[[InlineKeyboardButton("➕ New Tag", callback_data="utag_new")]],
    )
    await update.message.reply_text(
        f"Tag '{name}' created and selected. Pick up to {MAX_TAGS_PER_FILE} tags total:",
        reply_markup=keyboard,
    )
    return UPLOAD_TAG_SELECT


def _insert_file_row(conn, chat_id, item):
    cur = conn.execute(
        """INSERT INTO files
           (chat_id, item_type, original_name, stored_path, link_url,
            file_size_bytes, uploaded_at, is_deleted)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
        (
            chat_id, item["item_type"], item["original_name"], item["stored_path"], item["link_url"],
            item.get("file_size_bytes"), datetime.now().isoformat(),
        ),
    )
    return cur.lastrowid


async def upload_tag_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    selected = context.user_data.get("upload_selected_tag_ids") or set()
    if not selected:
        await query.answer("Select at least 1 tag first.", show_alert=True)
        return UPLOAD_TAG_SELECT
    await query.answer()

    batch = context.user_data.get("pending_batch") or []
    conn = get_db()
    for item in batch:
        file_id = _insert_file_row(conn, chat_id, item)
        for tag_id in selected:
            conn.execute("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)", (file_id, tag_id))
        log_activity(chat_id, "upload", detail=item["original_name"], file_size_bytes=item.get("file_size_bytes"))
    conn.commit()
    conn.close()

    tag_names = [t["name"] for t in list_tags(chat_id) if t["id"] in selected]
    await query.edit_message_text(f"✅ Saved and tagged {len(batch)} file(s) with: {', '.join(tag_names)}")
    for key in ("pending_batch", "upload_selected_tag_ids", "upload_tag_create_mode"):
        context.user_data.pop(key, None)

    return await show_post_upload_menu(update, context)


async def show_post_upload_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shown right after a save completes -- a focused two-choice prompt instead
    of dumping the full main menu, so 'what happens now' is never left unclear."""
    keyboard = [
        [InlineKeyboardButton("\U0001F4E4 Upload more files", callback_data="menu:upload")],
        [InlineKeyboardButton("✅ Done for now", callback_data="menu:done")],
    ]
    target = update.message or update.callback_query.message
    await target.reply_text(
        "What would you like to do next?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MAIN_MENU

# ---------------------------------------------------------------------------
# RETRIEVAL (menu-driven, options built from the user's own tagged files)
# ---------------------------------------------------------------------------
def search_files_by_tags(chat_id, tag_ids, match_mode="OR"):
    """match_mode='AND' -> file must carry every selected tag.
    match_mode='OR' -> file must carry at least one selected tag."""
    if not tag_ids:
        return []
    placeholders = ",".join("?" * len(tag_ids))
    conn = get_db()
    if match_mode == "AND":
        rows = conn.execute(
            f"""SELECT f.* FROM files f
                JOIN file_tags ft ON ft.file_id = f.id
                WHERE f.chat_id = ? AND f.is_deleted = 0 AND ft.tag_id IN ({placeholders})
                GROUP BY f.id
                HAVING COUNT(DISTINCT ft.tag_id) = ?
                ORDER BY f.uploaded_at DESC""",
            [chat_id, *tag_ids, len(tag_ids)],
        ).fetchall()
    else:
        rows = conn.execute(
            f"""SELECT DISTINCT f.* FROM files f
                JOIN file_tags ft ON ft.file_id = f.id
                WHERE f.chat_id = ? AND f.is_deleted = 0 AND ft.tag_id IN ({placeholders})
                ORDER BY f.uploaded_at DESC""",
            [chat_id, *tag_ids],
        ).fetchall()
    conn.close()
    return rows


def _retrieve_mode_label(mode):
    return ("\U0001F517 Match: ANY selected (OR) -- tap for ALL" if mode == "OR"
            else "\U0001F517 Match: ALL selected (AND) -- tap for ANY")


async def retrieve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for both 'My Files' (browse) and 'Delete My Files' -- which
    one is controlled by context.user_data['retrieve_mode'], set by the caller
    before this runs. Both share the same tag-picker + AND/OR search below."""
    chat_id = update.effective_chat.id
    tags = list_tags(chat_id)

    if not tags:
        target = update.callback_query.message if update.callback_query else update.message
        await target.reply_text("You don't have any tags yet -- upload something first to create one.")
        return await show_main_menu(update, context)

    context.user_data["retrieve_selected_tag_ids"] = set()
    context.user_data["retrieve_match_mode"] = "OR"
    return await show_retrieve_tag_picker(update, context, edit=False)


async def show_retrieve_tag_picker(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    chat_id = update.effective_chat.id
    tags = list_tags(chat_id)
    selected = context.user_data.get("retrieve_selected_tag_ids", set())
    mode = context.user_data.get("retrieve_match_mode", "OR")

    keyboard = render_tag_picker(
        tags, selected, "rtag:", "rtag_search",
        done_label=f"\U0001F50D Show results ({len(selected)} tag(s))",
        extra_rows=[[InlineKeyboardButton(_retrieve_mode_label(mode), callback_data="rtag_mode")]],
    )
    text = "Pick one or more tags to filter by:"
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        target = update.callback_query.message if update.callback_query else update.message
        await target.reply_text(text, reply_markup=keyboard)
    return RETRIEVE_TAG_SELECT


async def retrieve_tag_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tag_id = int(query.data.split(":", 1)[1])
    selected = context.user_data.setdefault("retrieve_selected_tag_ids", set())
    if tag_id in selected:
        selected.remove(tag_id)
    else:
        selected.add(tag_id)
    return await show_retrieve_tag_picker(update, context, edit=True)


async def retrieve_mode_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current = context.user_data.get("retrieve_match_mode", "OR")
    context.user_data["retrieve_match_mode"] = "AND" if current == "OR" else "OR"
    return await show_retrieve_tag_picker(update, context, edit=True)


async def retrieve_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    selected = context.user_data.get("retrieve_selected_tag_ids") or set()
    if not selected:
        await query.answer("Pick at least 1 tag first.", show_alert=True)
        return RETRIEVE_TAG_SELECT
    await query.answer()

    mode = context.user_data.get("retrieve_match_mode", "OR")
    rows = search_files_by_tags(chat_id, list(selected), mode)
    retrieve_mode = context.user_data.get("retrieve_mode", "browse")

    if not rows:
        await query.edit_message_text("No files match that tag selection.")
        return await show_main_menu(update, context)

    context.user_data["retrieve_results"] = [dict(r) for r in rows]

    if retrieve_mode == "delete":
        # Deletion is a deliberate, separate action -- never bundled into the normal
        # browse screen. Show what would be removed, require an explicit tap, then
        # gate the actual removal behind an emailed OTP (see delete_otp_received).
        preview_lines = []
        for r in rows[:20]:
            names = ", ".join(t["name"] for t in get_file_tags(r["id"]))
            preview_lines.append(f"• {r['original_name']} [{names}]")
        preview = "\n".join(preview_lines)
        if len(rows) > 20:
            preview += f"\n...and {len(rows) - 20} more"
        keyboard = [
            [InlineKeyboardButton(f"\U0001F5D1 Request removal of these {len(rows)} file(s)", callback_data="delete_request")],
        ]
        await query.edit_message_text(
            f"Found {len(rows)} file(s) matching your tags ({mode}):\n{preview}\n\n"
            f"These will be removed from your account view (hidden from My Files and "
            f"search) -- not instantly erased from storage. Tap below to get a "
            f"confirmation code by email.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return RETRIEVE_RESULTS

    keyboard = []
    for r in rows:
        names = ", ".join(t["name"] for t in get_file_tags(r["id"]))
        label = f"{r['original_name']} [{names}]" if names else r["original_name"]
        keyboard.append([InlineKeyboardButton(label[:64], callback_data=f"send_one:{r['id']}")])
    keyboard.append([InlineKeyboardButton(f"\U0001F4E6 Send all {len(rows)} files", callback_data="send_all")])

    await query.edit_message_text(
        f"Found {len(rows)} file(s) ({mode} match). Pick one, or send all:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    log_activity(chat_id, "retrieve", detail=f"{len(rows)} file(s) matched tags ({mode})")
    return RETRIEVE_RESULTS



async def retrieve_results_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    results = context.user_data.get("retrieve_results", [])

    if query.data.startswith("send_one:"):
        file_id = int(query.data.split(":", 1)[1])
        row = next((r for r in results if r["id"] == file_id), None)
        if row:
            await send_single_item(context, chat_id, row)
        return await show_main_menu(update, context)

    if query.data == "send_all":
        await send_bulk(context, chat_id, results)
        return await show_main_menu(update, context)

    if query.data == "delete_request":
        conn = get_db()
        user = conn.execute("SELECT email FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
        conn.close()
        if not user or not user["email"]:
            await query.message.reply_text("Couldn't find your registered email. Please /start again.")
            return await show_main_menu(update, context)

        context.user_data["delete_pending_ids"] = [r["id"] for r in results]
        try:
            generate_and_send_otp(chat_id, user["email"], purpose="delete", file_count=len(results))
        except Exception as e:
            logger.error(f"Failed to send delete-confirmation OTP: {e}")
            await query.message.reply_text(
                "Sorry, couldn't send the confirmation email right now. Please try again shortly."
            )
            return await show_main_menu(update, context)

        log_activity(chat_id, "delete_request", detail=f"{len(results)} file(s)", email=user["email"])
        await query.message.reply_text(
            f"A confirmation code was emailed to {user['email']}. Enter it here to remove "
            f"{len(results)} file(s) from your account, or /cancel to back out."
        )
        return DELETE_OTP

    return await show_main_menu(update, context)


async def delete_otp_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    code = update.message.text.strip()

    if not verify_otp(chat_id, code, purpose="delete"):
        await update.message.reply_text("That code is incorrect or expired. Please try again, or /cancel.")
        return DELETE_OTP

    ids = context.user_data.pop("delete_pending_ids", [])
    if ids:
        conn = get_db()
        conn.executemany("UPDATE files SET is_deleted = 1 WHERE id = ?", [(i,) for i in ids])
        conn.commit()
        conn.close()
        log_activity(chat_id, "delete_confirm", detail=f"{len(ids)} file(s)")

    await update.message.reply_text(
        f"✅ Removed {len(ids)} file(s) from your account. "
        f"They're hidden from My Files and search from now on."
    )
    return await show_main_menu(update, context)


async def send_single_item(context, chat_id, row):
    if row["item_type"] == "link":
        await context.bot.send_message(chat_id=chat_id, text=f"\U0001F517 {row['link_url']}")
    else:
        path = row["stored_path"]
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                await context.bot.send_document(chat_id=chat_id, document=f, filename=row["original_name"])
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"File missing on disk: {row['original_name']}")


async def send_bulk(context, chat_id, rows):
    links = [r for r in rows if r["item_type"] == "link"]
    files = [r for r in rows if r["item_type"] == "file" and r["stored_path"] and os.path.exists(r["stored_path"])]

    for r in links:
        await send_single_item(context, chat_id, r)

    if not files:
        return

    # Zip files into ~45MB parts
    limit_bytes = TELEGRAM_SAFE_LIMIT_MB * 1024 * 1024
    parts = []
    current_part = []
    current_size = 0
    for r in files:
        size = os.path.getsize(r["stored_path"])
        if current_size + size > limit_bytes and current_part:
            parts.append(current_part)
            current_part = []
            current_size = 0
        current_part.append(r)
        current_size += size
    if current_part:
        parts.append(current_part)

    folder = user_folder(chat_id)
    for i, part in enumerate(parts, start=1):
        zip_path = os.path.join(folder, f"_bulk_export_part{i}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in part:
                zf.write(r["stored_path"], arcname=r["original_name"])
        with open(zip_path, "rb") as f:
            await context.bot.send_document(
                chat_id=chat_id, document=f, filename=f"MyFiles_part{i}_of_{len(parts)}.zip"
            )
        os.remove(zip_path)


# ---------------------------------------------------------------------------
# FALLBACK / CANCEL
# ---------------------------------------------------------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Send /start to begin again.")
    return ConversationHandler.END


def main():
    if not BOT_TOKEN:
        raise SystemExit("Set BOT_TOKEN first (edit the file or set TELEGRAM_BOT_TOKEN env var).")

    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    platform_db.schedule_heartbeat(app, MYFILES_BOT_ID)

    # 2026-08-17: every handler function below wrapped with
    # activity_logger.log_activity() at registration time only -- see
    # telegram/LOGGING-ARCHITECTURE.md §3. Every pattern/filter/state key
    # is UNCHANGED from before -- only the callback reference passed to
    # each Handler constructor is wrapped, nothing about this
    # ConversationHandler's own structure or routing logic is touched.
    # UPLOAD_WAIT_ITEM's combined (Document|PHOTO|TEXT) handler is tagged
    # "text" (not "photo") -- it's the closest of the 4 valid handler_kind
    # values for a genuinely mixed filter, and activity_logger's own text
    # extraction already handles a photo/document update safely (no
    # .text attribute -> falls back to empty, never crashes), just labels
    # it a little less precisely than a dedicated "mixed" kind would.
    # 2026-08-24: rate_limiter.rate_limited() wraps OUTERMOST (see that
    # module's own docstring for why) -- a "general" flood cap on every
    # handler, SECURITY.md §4.1.
    def _la(kind, func):
        return rate_limiter.rate_limited("general", MYFILES_BOT_ID)(activity_logger.log_activity(kind, MYFILES_BOT_ID)(func))

    # AUTH_EMAIL/AUTH_OTP/DELETE_OTP get the tighter "otp_attempt" bucket
    # instead of "general" -- these are OTP request/guess attempts
    # specifically (real login/account-security surface, distinct from
    # ordinary menu navigation), see rate_limiter.BUCKETS' own comment.
    def _la_otp(func):
        return rate_limiter.rate_limited("otp_attempt", MYFILES_BOT_ID)(
            activity_logger.log_activity("text", MYFILES_BOT_ID, always_redact=True)(func)
        )

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", _la("command", start)),
            MessageHandler(filters.Regex(GREETING_RE) & filters.TEXT & ~filters.COMMAND, _la("text", start)),
        ],
        states={
            AUTH_MENU: [CallbackQueryHandler(_la("callback", auth_menu_choice), pattern=r"^auth:")],
            # always_redact=True: these two collect an email address and an
            # OTP code via PTB's OWN ConversationHandler state, which
            # activity_logger's context.user_data-based redaction detection
            # cannot see at all -- see activity_logger.py's own REDACTION
            # comment block for the full reasoning (a real gap found and
            # fixed before this wiring went in, not a theoretical one).
            AUTH_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, _la_otp(auth_email_received))],
            AUTH_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, _la_otp(auth_otp_received))],
            PROFILE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, _la("text", profile_name_received))],
            MAIN_MENU: [CallbackQueryHandler(_la("callback", main_menu_choice), pattern=r"^menu:")],
            UPLOAD_WAIT_ITEM: [
                MessageHandler((filters.Document.ALL | filters.PHOTO | filters.TEXT) & ~filters.COMMAND, _la("text", upload_item_received)),
                CallbackQueryHandler(_la("callback", batch_same_choice), pattern=r"^batch_same:"),
                # Also registered here (not just under UPLOAD_TAG_SELECT/UPLOAD_TAG_CREATE):
                # a single-item upload's tag prompt is sent by a background task
                # (_finalize_batch), which can't move the conversation state, so the
                # very first tag interaction still arrives while formally in this state.
                CallbackQueryHandler(_la("callback", upload_tag_toggle), pattern=r"^utag:"),
                CallbackQueryHandler(_la("callback", upload_tag_new_prompt), pattern=r"^utag_new$"),
                CallbackQueryHandler(_la("callback", upload_tag_done), pattern=r"^utag_done$"),
            ],
            UPLOAD_TAG_SELECT: [
                CallbackQueryHandler(_la("callback", upload_tag_toggle), pattern=r"^utag:"),
                CallbackQueryHandler(_la("callback", upload_tag_new_prompt), pattern=r"^utag_new$"),
                CallbackQueryHandler(_la("callback", upload_tag_done), pattern=r"^utag_done$"),
            ],
            UPLOAD_TAG_CREATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, _la("text", upload_tag_create_received))],
            RETRIEVE_TAG_SELECT: [
                CallbackQueryHandler(_la("callback", retrieve_tag_toggle), pattern=r"^rtag:"),
                CallbackQueryHandler(_la("callback", retrieve_mode_toggle), pattern=r"^rtag_mode$"),
                CallbackQueryHandler(_la("callback", retrieve_search), pattern=r"^rtag_search$"),
            ],
            RETRIEVE_RESULTS: [CallbackQueryHandler(_la("callback", retrieve_results_action), pattern=r"^(send_one:|send_all|delete_request)")],
            DELETE_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, _la_otp(delete_otp_received))],  # always_redact=True -- an OTP code, same reasoning as AUTH_EMAIL/AUTH_OTP above
            TAG_MANAGE: [CallbackQueryHandler(_la("callback", tag_manager_action), pattern=r"^tagmgr_")],
            TAG_MANAGE_CREATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, _la("text", tag_manager_create_received))],
            TAG_MANAGE_RENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, _la("text", tag_manager_rename_received))],
        },
        # "start" here too (not just in entry_points) so /start also works as a reset
        # from *inside* an active conversation, not just as the very first message.
        fallbacks=[CommandHandler("cancel", _la("command", cancel)), CommandHandler("start", _la("command", start))],
    )

    app.add_handler(conv)

    logger.info("1Lavya MyFiles Hub Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
