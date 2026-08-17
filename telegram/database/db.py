"""
telegram/database/db.py -- the shared platform database helper (2026-08-10)
-----------------------------------------------------------------------------
Every bot process (study/exam/unified -- see telegram/config/bots.json)
imports this module instead of opening its own SQLite file. All of them now
write to the SAME file, telegram/database/platform.db, running
telegram/database/schema.sql's tables -- see that file's own comments for
the full schema and the "shared table per bot kind + bot_id column" design
decision this implements.

Because this file is now written to by MULTIPLE OS PROCESSES concurrently
(not just multiple threads in one process, which SQLite's `check_same_thread
=False` alone would cover) -- every connection here is opened in WAL mode
with a real busy_timeout, and every write goes through execute_with_retry()
as a second line of defense against a transient "database is locked" under
real contention. This is the single most important correctness concern this
module exists to centralize -- don't open a raw sqlite3.connect() to this
file anywhere else in the codebase; go through get_connection() here so
every writer gets the same protection.

MyFiles Hub is the one exception: its own users/otps/files/tags/
file_tags/activity_log tables intentionally stay in their own separate
myfiles_hub.db (primary application data, not "logs" -- see schema.sql's
own note on this). It still calls send_heartbeat() from here so the
dashboard can show it alongside every other bot.
"""

import os
import sqlite3
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]   # telegram/database/db.py -> repo root
PLATFORM_DB_PATH = REPO_ROOT / "telegram" / "database" / "platform.db"
SCHEMA_PATH = REPO_ROOT / "telegram" / "database" / "schema.sql"

_BUSY_TIMEOUT_MS = 30_000   # how long SQLite itself will wait for a lock before raising
_RETRY_ATTEMPTS = 5
_RETRY_BACKOFF_SECONDS = 0.25


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    """One connection per call -- bot scripts should open one at startup
    and reuse it (same pattern exam_hub_bot.py already used for its own
    per-tenant DB), not reconnect per query. WAL mode lets readers and
    writers coexist without blocking each other; busy_timeout makes SQLite
    itself retry internally for up to _BUSY_TIMEOUT_MS before raising
    "database is locked" -- execute_with_retry() below is the outer,
    application-level retry on top of that inner one."""
    os.makedirs(PLATFORM_DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=_BUSY_TIMEOUT_MS / 1000, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS};")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_schema(conn: sqlite3.Connection):
    """Idempotent -- every CREATE TABLE/INDEX in schema.sql is IF NOT
    EXISTS, so calling this from every bot's startup is safe and expected
    (whichever bot starts first actually creates the tables; every bot
    after that is a no-op)."""
    _migrate_wallet_ledger_shape(conn)
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
    _run_column_migrations(conn)
    _migrate_legacy_single_academic_profile(conn)


def _migrate_wallet_ledger_shape(conn: sqlite3.Connection):
    """One-time reshape for wallet_ledger (telegram_user_id -> username,
    widened event_type CHECK to add test_debit/descriptive_debit) and
    payments (added a `username` column) -- 2026-08-15, Test Mode billing
    rollout (see telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md §9 for
    the full decision trail: wallet balance now follows a student's shared
    1LAVYA username, not one phone/chat_id).

    SQLite's ALTER TABLE can't rename/retype a column or widen a CHECK
    constraint (confirmed by this codebase's own established convention --
    see _COLUMN_MIGRATIONS' docstring above for the same limitation on
    plain ADD COLUMN cases), so the only option is DROP + let
    executescript() below recreate both tables fresh from schema.sql's new
    CREATE TABLE text. This is safe ONLY because both tables were verified
    empty (0 rows each) directly against the live platform.db before this
    function was written -- not assumed. Guards the same way going forward:
    refuses to drop either table if it ever finds a real row, rather than
    silently destroying data, so a future re-run after real rows exist
    fails loudly instead of quietly eating them.

    Must run BEFORE executescript() in init_schema() -- CREATE TABLE IF NOT
    EXISTS is a no-op against an already-existing old-shape table, so the
    drop has to happen first or the new shape never takes effect."""
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('wallet_ledger','payments')"
    ).fetchall()
    existing_tables = {row[0] for row in tables}

    if "wallet_ledger" in existing_tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(wallet_ledger)").fetchall()}
        current_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='wallet_ledger'"
        ).fetchone()
        current_sql = current_sql[0] if current_sql else ""
        # Stale if EITHER the pre-2026-08-15 shape (telegram_user_id, no
        # username) OR the pre-2026-08-16 event_type enum (missing the new
        # 'grant_expired' CHECK value) -- both require a reshape SQLite's
        # ALTER TABLE can't express in place. Deliberately checks for the
        # PRESENCE of the new marker ('grant_expired'), not the absence of
        # the old name ('free_monthly_grant') -- a real bug caught while
        # building this: schema.sql's own explanatory comment on the rename
        # mentions the old name in prose, which would make an
        # absence-of-old-name check permanently misfire as "still stale"
        # even after the reshape actually happened, re-dropping the table
        # (harmless while empty, but would hard-crash via the row-count
        # guard below on every restart once real rows exist).
        is_stale = ("telegram_user_id" in cols and "username" not in cols) or ("grant_expired" not in current_sql)
        if is_stale:
            count = conn.execute("SELECT COUNT(*) FROM wallet_ledger").fetchone()[0]
            if count > 0:
                raise RuntimeError(
                    f"wallet_ledger has {count} real row(s) under a stale shape -- refusing "
                    "to auto-drop. This migration was only ever verified safe against an "
                    "empty table; a real data-preserving migration is needed instead."
                )
            conn.execute("DROP TABLE wallet_ledger")
            logger.info("Migrated: dropped stale-shape wallet_ledger (verified empty) for reshape")

    if "payments" in existing_tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(payments)").fetchall()}
        if "username" not in cols:
            count = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
            if count > 0:
                raise RuntimeError(
                    f"payments has {count} real row(s) without a username column -- "
                    "refusing to auto-drop. This migration was only ever verified safe "
                    "against an empty table; a real data-preserving migration is needed instead."
                )
            conn.execute("DROP TABLE payments")
            logger.info("Migrated: dropped old-shape payments (verified empty) to add username column")

    conn.commit()


# New columns added to EXISTING tables since this repo went live (both
# `students` and `exam_hub_sessions` already had real rows) -- SQLite has
# no `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (confirmed by testing
# directly, 2026-08-11: it's a syntax error, unlike `CREATE TABLE`/
# `CREATE INDEX IF NOT EXISTS`, which SQLite does support). schema.sql's
# own CREATE TABLE statements only describe a table's shape for a brand-new
# database; a column added after go-live has to be migrated in here
# instead, checking `PRAGMA table_info` first so re-running this on every
# bot startup (like every other part of init_schema()) is safe. Add new
# entries here, never as a plain `ALTER TABLE` in schema.sql directly.
_COLUMN_MIGRATIONS = {
    "students": [
        ("mobile_number", "TEXT"),
        ("email_verification_method", "TEXT CHECK (email_verification_method IN ('otp', 'echo_confirm') OR email_verification_method IS NULL)"),
        ("mobile_verification_method", "TEXT CHECK (mobile_verification_method IN ('echo_confirm') OR mobile_verification_method IS NULL)"),
        ("report_channel_preference", "TEXT CHECK (report_channel_preference IN ('telegram', 'email', 'both') OR report_channel_preference IS NULL)"),
        # References student_profiles(username) -- safe because schema.sql's
        # executescript() (which creates student_profiles) always runs
        # BEFORE this migration function, in init_schema() below.
        ("lavya_username", "TEXT REFERENCES student_profiles(username)"),
    ],
    "exam_hub_sessions": [
        # Added 2026-08-12 for exam_hub_bot.py's Mode-first flow rewrite
        # (Mode -> Course -> Level -> Subject -> Exam Type) -- Subject is a
        # new funnel step, so it's tracked here the same way course/level/
        # mode already were, for the same "see where students drop off"
        # analytics reasoning schema.sql's own comment on this table gives.
        ("subject", "TEXT"),
    ],
    "exam_hub_mcq_attempts": [
        # Added 2026-08-13 -- provenance tagging (see exam_hub_bot.py's
        # _infer_content_owner()): which tenant's content this question was
        # sourced/generated by ("1lavya" or a faculty tenant_id), so usage/
        # accuracy can be broken down by content source later, not just by
        # bot_id (a faculty's OWN bot only ever logs bot_id=that faculty,
        # but the flagship bot now serves everyone's content merged
        # together -- this is the only column that tells them apart there).
        ("content_owner", "TEXT"),
        ("human_id", "TEXT"),
    ],
    "exam_hub_descriptive_events": [
        ("content_owner", "TEXT"),
        ("human_id", "TEXT"),
    ],
    "mcq_issue_reports": [
        # mcq_issue_reports was created (via schema.sql's CREATE TABLE)
        # earlier the same day this column was added, so it needs the
        # same ALTER-via-migration treatment as every other post-go-live
        # column in this dict -- adding `human_id` directly to schema.sql's
        # CREATE TABLE text would be a silent no-op against an already-
        # created table (CREATE TABLE IF NOT EXISTS doesn't ALTER).
        ("human_id", "TEXT"),
    ],
    "test_sessions": [
        # Added 2026-08-16 for the interactive grace-period offer (Pranav:
        # ask the student if they need 2/3/5 extra minutes when time runs
        # out, offered exactly once, tracked) -- test_sessions was created
        # (via schema.sql's CREATE TABLE) earlier the same session, so this
        # needs the same ALTER-via-migration treatment as every other
        # post-go-live column in this dict.
        ("grace_offered_at", "TEXT"),
        ("grace_requested_minutes", "INTEGER"),
        # Added same day, same reasoning -- exact-point resume + what the
        # no-activity heartbeat checks against (see test_activity_log).
        ("current_seq_no", "INTEGER"),
    ],
    "test_questions": [
        # Added 2026-08-16 -- topic/subtopic snapshot per question, for
        # concept-level analysis (Pranav's ask). test_questions was created
        # earlier the same session, needs the same migration treatment.
        ("chapter_slug", "TEXT"),
        ("topic_text", "TEXT"),
    ],
}


def _run_column_migrations(conn: sqlite3.Connection):
    for table, columns in _COLUMN_MIGRATIONS.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for col_name, col_def in columns:
            if col_name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
                logger.info(f"Migrated: added {table}.{col_name}")
    conn.commit()


def _migrate_legacy_single_academic_profile(conn: sqlite3.Connection):
    """One-time (per username), idempotent, additive data copy -- 2026-08-16
    multi-course profiles rollout (see schema.sql's own comment on
    student_academic_profiles for the full reasoning). Any existing
    student_profiles row that already has a course+level set gets copied
    into student_academic_profiles as that username's first academic
    profile -- the old columns are left untouched (never cleared, never
    dropped), this only ever ADDS a row, and only if one matching this
    username/course/level doesn't already exist (the UNIQUE constraint on
    student_academic_profiles would reject a duplicate anyway, but the
    explicit WHERE NOT EXISTS avoids even attempting the insert on every
    single bot startup once migrated once). Safe to run on every
    init_schema() call, same as every other migration in this file."""
    execute_with_retry(
        conn,
        """
        INSERT INTO student_academic_profiles (username, course, level, exam_attempt, created_at, updated_at)
        SELECT sp.username, sp.course, sp.level, sp.exam_attempt, sp.updated_at, sp.updated_at
        FROM student_profiles sp
        WHERE sp.course IS NOT NULL AND sp.level IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM student_academic_profiles sap
              WHERE sap.username = sp.username AND sap.course = sp.course AND sap.level = sp.level
          )
        """,
        (),
    )


def execute_with_retry(conn: sqlite3.Connection, sql: str, params=()):
    """Write helper with a real retry-with-backoff loop on top of SQLite's
    own busy_timeout, for the rare case even that isn't enough under real
    concurrent load from multiple bot processes. Commits on success.
    Raises the underlying exception if every attempt is exhausted -- never
    silently drops a write."""
    last_exc = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            conn.execute(sql, params)
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            last_exc = e
            if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                raise
            logger.warning(f"DB write contended (attempt {attempt + 1}/{_RETRY_ATTEMPTS}): {e}")
            time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise last_exc


# ---------------------------------------------------------------------------
# Shared writers -- every bot calls these instead of hand-rolling its own
# INSERT/UPDATE for these specific concerns.
# ---------------------------------------------------------------------------

def upsert_student(conn, user):
    """`user` is a telegram.User (or anything with .id/.username/.first_name/
    .last_name). Writes to the ONE shared `students` table -- see schema.sql's
    "centralized account model" note. Safe to call on every /start and every
    message; cheap upsert."""
    now_str = now()
    row = conn.execute(
        "SELECT telegram_user_id FROM students WHERE telegram_user_id=?", (user.id,)
    ).fetchone()
    if row:
        execute_with_retry(
            conn,
            "UPDATE students SET username=?, first_name=?, last_name=?, last_seen_at=? WHERE telegram_user_id=?",
            (user.username, user.first_name, user.last_name, now_str, user.id),
        )
    else:
        execute_with_retry(
            conn,
            "INSERT INTO students (telegram_user_id, username, first_name, last_name, first_seen_at, last_seen_at) "
            "VALUES (?,?,?,?,?,?)",
            (user.id, user.username, user.first_name, user.last_name, now_str, now_str),
        )


def log_interaction(conn, bot_id: str, telegram_user_id: int, event_type: str):
    """The generic, uniform log every bot writes to -- see bot_interactions'
    own comment in schema.sql for why this exists separately from the
    richer per-bot-kind tables. Never raises on a logging failure blocking
    the actual student-facing action -- catches and logs a warning instead,
    same "logging must never break the product" principle
    myfiles_hub_bot.py's activity_log already follows."""
    try:
        execute_with_retry(
            conn,
            "INSERT INTO bot_interactions (bot_id, telegram_user_id, event_type, created_at) VALUES (?,?,?,?)",
            (bot_id, telegram_user_id, event_type, now()),
        )
    except Exception as e:
        logger.warning(f"log_interaction failed (bot_id={bot_id}, event={event_type}): {e}")


def send_heartbeat(conn, bot_id: str, pid: int, started_at: str):
    """Upsert -- one row per bot_id, always. See bot_heartbeats' own
    comment in schema.sql for how the dashboard/process manager use this
    to tell "configured but not running" apart from "actually alive".

    BUG FIXED 2026-08-11 (found while building telegram/branding's smoke
    test, which added a real use for started_at -- detecting whether a live
    process predates a source-code change, i.e. needs a restart): the
    UPDATE branch below never wrote `started_at`, only `pid`/
    `last_heartbeat_at` -- so after any restart, this column kept showing
    the FIRST time this bot_id ever got a heartbeat row, across every past
    process, not the current process's actual start time. Every caller
    (schedule_heartbeat() below, dashboard_server.py's own heartbeat loop)
    already computes `started_at` correctly once at process startup and
    passes the SAME correct value on every tick -- the fix is just to
    actually write it on the UPDATE path too (idempotent on repeat ticks
    within one process's life; correctly picks up the new value the moment
    a new process's first heartbeat arrives after a restart)."""
    now_str = now()
    try:
        row = conn.execute("SELECT bot_id FROM bot_heartbeats WHERE bot_id=?", (bot_id,)).fetchone()
        if row:
            execute_with_retry(
                conn, "UPDATE bot_heartbeats SET pid=?, started_at=?, last_heartbeat_at=? WHERE bot_id=?",
                (pid, started_at, now_str, bot_id),
            )
        else:
            execute_with_retry(
                conn,
                "INSERT INTO bot_heartbeats (bot_id, pid, started_at, last_heartbeat_at) VALUES (?,?,?,?)",
                (bot_id, pid, started_at, now_str),
            )
    except Exception as e:
        logger.warning(f"send_heartbeat failed (bot_id={bot_id}): {e}")


def log_mcq_issue_report(conn, bot_id: str, telegram_user_id: int, mcq_id: str, human_id, course, level, subject,
                          chapter_slug, chapter_label, category: str, description: str) -> int:
    """See mcq_issue_reports' own comment in schema.sql -- one row per
    student-reported MCQ issue (telegram/bots/mcq_issue_flow.py)."""
    now_str = now()
    execute_with_retry(
        conn,
        """INSERT INTO mcq_issue_reports
           (bot_id, telegram_user_id, mcq_id, human_id, course, level, subject, chapter_slug,
            chapter_label, category, description, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (bot_id, telegram_user_id, mcq_id, human_id, course, level, subject, chapter_slug,
         chapter_label, category, description, "open", now_str),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def schedule_heartbeat(application, bot_id: str, interval_seconds: int = 120):
    """Call once from each bot's main(), after building the Application but
    before app.run_polling(). Uses python-telegram-bot's JobQueue (requires
    the `job-queue` extra -- pip install "python-telegram-bot[job-queue]",
    already added to every bot's own SETUP docstring) so the heartbeat runs
    on the bot's own event loop -- no extra thread, no separate process."""
    conn = get_connection()
    init_schema(conn)
    pid = os.getpid()
    started_at = now()

    async def _tick(context):
        send_heartbeat(conn, bot_id, pid, started_at)

    send_heartbeat(conn, bot_id, pid, started_at)  # write one immediately, don't wait for the first interval
    application.job_queue.run_repeating(_tick, interval=interval_seconds, first=interval_seconds)
