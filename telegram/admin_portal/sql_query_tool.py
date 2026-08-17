"""
telegram/admin_portal/sql_query_tool.py -- ad hoc, read-only SQL query
runner for the Admin Portal's Overview page (2026-08-17)
--------------------------------------------------------------------------------
Pranav's ask: a 5th Overview tab, after Students/Content/Performance/
Faculty -- a free-text SQL box + Run button, so he (or an AI model he's
fed the schema to) can build ANY custom cross-table view ("student ID +
current credits + a calculated 'credits used in last 10 days' column")
without needing a developer to write a bespoke query every time, same
flexibility the existing "Data Export" page already gives for whole
tables, one level more powerful.

SAFETY -- this is the one thing worth reading carefully before touching
this file. `platform.db` is being written to right now by 9+ live bot
processes handling real students' wallets. An arbitrary-SQL box on a
production OLTP database is genuinely dangerous if it can write: a single
AI-hallucinated or hand-typed mistake (an UPDATE/DELETE/DROP, or even a
runaway unindexed JOIN with no LIMIT) could corrupt real data or hang the
shared DB file for every live bot. Given that, this tool is deliberately
NOT "run any SQL" -- it's READ-ONLY, enforced two independent ways so a
single bug in either one can't turn into a real incident:

1. TEXT VALIDATION (validate_readonly_select) -- the submitted text must
   be exactly one statement, and that statement must start with SELECT or
   WITH (a CTE). Rejects everything else outright (INSERT/UPDATE/DELETE/
   DROP/ALTER/ATTACH/PRAGMA/...) before ever touching the database.
2. A GENUINELY READ-ONLY CONNECTION (`sqlite3.connect(..., uri=True)`
   against a `file:...?mode=ro` URI) -- SQLite itself refuses any write
   attempt on this connection with `OperationalError: attempt to write a
   readonly database`. This is the connection every query in this module
   runs on, always -- so even if #1 had a bug (or missed some exotic
   syntax), the write would still physically fail at the SQLite layer.
   (mode=ro only affects the MAIN database file -- ATTACH could still open
   a SEPARATE writable file, which is exactly why #1 rejects ATTACH as a
   non-SELECT statement rather than relying on mode=ro alone.)

On top of the write-safety guarantee: a row cap (so a huge result set
never gets pulled fully into memory) and a wall-clock query timeout (via
sqlite3's own progress_handler -- so one expensive query can't hang this
request indefinitely), so this also can't become a live-bot-facing
performance incident even though it can only ever READ.

Every query run through here is audit-logged by the caller (app.py), same
discipline as every other action-performing route on this portal.
"""

import re
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "platform.db"

# Applies to the on-screen preview table (kept small -- this platform's own
# real data volumes are "dozens to low hundreds of rows" per exporters.py's
# own docstring, so this will essentially never bind in normal use).
PREVIEW_ROW_LIMIT = 500
# Applies to CSV/XLSX/JSON export -- generous, but still a real backstop
# against a query that's technically valid SELECT but returns something
# enormous (e.g. a careless cross join).
EXPORT_ROW_LIMIT = 20_000

PREVIEW_TIMEOUT_SECONDS = 5.0
EXPORT_TIMEOUT_SECONDS = 15.0

_ALLOWED_LEADING_KEYWORDS = ("select", "with")


class QueryRejected(Exception):
    """The submitted text failed validation -- never reached the database
    at all. Distinct from QueryFailed (below) so the UI can say "not
    allowed" vs. "ran, but errored/timed out" with different framing."""


class QueryFailed(Exception):
    """The query was valid SELECT/WITH and reached the (read-only)
    database, but sqlite3 itself raised -- a genuine SQL error, or the
    timeout guard tripping."""


def _strip_sql_comments(sql: str) -> str:
    """Removes `-- line comments` and `/* block comments */` before
    keyword-sniffing below, so e.g. "-- DROP everything\\nSELECT 1" isn't
    mistaken for starting with DROP, and (more to the point) so a
    real attempt to hide a second statement inside a comment doesn't
    accidentally confuse the single-statement check either."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def validate_readonly_select(sql: str) -> str:
    """Returns the cleaned (comment-stripped, trimmed) SQL text if it
    passes validation. Raises QueryRejected with a human-readable reason
    otherwise. This is defense-in-depth alongside the read-only connection
    in run_query() below -- never the ONLY thing standing between this box
    and a write, but it does give a much clearer error message than "the
    database is read-only" for the common case of someone pasting in an
    UPDATE by mistake."""
    if not sql or not sql.strip():
        raise QueryRejected("Type a SQL query first.")

    cleaned = _strip_sql_comments(sql).strip()
    if not cleaned:
        raise QueryRejected("That query is empty once comments are stripped out.")

    # Exactly one statement. A single harmless trailing semicolon (with only
    # whitespace after it) is fine and stripped; anything else after a
    # semicolon means a second statement was submitted.
    stripped_trailing = cleaned.rstrip()
    if stripped_trailing.endswith(";"):
        stripped_trailing = stripped_trailing[:-1].rstrip()
    if ";" in stripped_trailing:
        raise QueryRejected(
            "Only one statement at a time -- remove everything after the first semicolon "
            "(this tool refuses multiple statements, including ones hidden after a comment)."
        )
    cleaned = stripped_trailing

    first_word_match = re.match(r"[A-Za-z]+", cleaned)
    first_word = first_word_match.group(0).lower() if first_word_match else ""
    if first_word not in _ALLOWED_LEADING_KEYWORDS:
        raise QueryRejected(
            f"Only SELECT queries are allowed (this tool is read-only, enforced at the database "
            f"connection level too) -- \"{first_word or cleaned[:20]}\" isn't SELECT or WITH."
        )

    return cleaned


def _readonly_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise QueryFailed(f"Database file not found at {DB_PATH}.")
    # uri=True + mode=ro is what makes this a HARD guarantee, not just a
    # convention -- see module docstring point 2.
    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def _run_with_timeout(conn: sqlite3.Connection, sql: str, params: tuple, timeout_seconds: float):
    deadline = time.monotonic() + timeout_seconds

    def _progress_handler():
        return 1 if time.monotonic() > deadline else 0

    # n=1000 -- checked every 1000 SQLite VM instructions, frequent enough
    # to actually cap wall time closely, cheap enough not to slow a normal
    # small query down in any noticeable way.
    conn.set_progress_handler(_progress_handler, 1000)
    try:
        return conn.execute(sql, params)
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            raise QueryFailed(
                f"Query took longer than {timeout_seconds:.0f}s and was stopped -- "
                "try narrowing it (a WHERE clause, a smaller date range, fewer joined tables)."
            )
        raise QueryFailed(f"SQL error: {e}")
    except sqlite3.Error as e:
        raise QueryFailed(f"SQL error: {e}")
    finally:
        conn.set_progress_handler(None, 0)


def run_query(sql: str, row_limit: int = PREVIEW_ROW_LIMIT, timeout_seconds: float = PREVIEW_TIMEOUT_SECONDS) -> dict:
    """Validates, then executes, the given SQL against a read-only
    connection, capped at `row_limit` rows and `timeout_seconds` wall
    time. Returns {"columns": [...], "rows": [[...], ...], "row_count":
    int, "truncated": bool, "elapsed_ms": float}. Raises QueryRejected
    (never reached the DB) or QueryFailed (reached the DB, then errored or
    timed out) -- callers should catch both and show the message, they're
    always safe to display as-is (never leak a raw traceback)."""
    cleaned = validate_readonly_select(sql)

    # Wrapped as a subquery with a LIMIT of row_limit+1 -- lets us detect
    # "there were more rows than we're showing" (truncated=True) without
    # a separate COUNT(*) query (which could itself be expensive/slow for
    # the exact same reasons the row cap exists in the first place).
    # SQLite preserves the inner query's own row order here (no reordering
    # operation is added at the outer level) -- good enough for an ad hoc
    # admin tool, not a place to rely on undefined-order guarantees.
    wrapped = f"SELECT * FROM ({cleaned}) AS _sql_tool_q LIMIT ?"

    conn = _readonly_connection()
    try:
        start = time.monotonic()
        cursor = _run_with_timeout(conn, wrapped, (row_limit + 1,), timeout_seconds)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = [list(r) for r in cursor.fetchall()]
        elapsed_ms = (time.monotonic() - start) * 1000
    finally:
        conn.close()

    truncated = len(rows) > row_limit
    if truncated:
        rows = rows[:row_limit]

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "elapsed_ms": elapsed_ms,
    }


def run_query_for_export(sql: str) -> dict:
    """Same as run_query() but at the export ceiling/timeout instead of
    the on-screen preview's smaller ones -- used by the CSV/XLSX/JSON
    download routes, which re-run the exact same query text rather than
    caching the preview's result (keeps this stateless, same pattern
    every other export route on this portal already follows)."""
    return run_query(sql, row_limit=EXPORT_ROW_LIMIT, timeout_seconds=EXPORT_TIMEOUT_SECONDS)
