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

FILTER/SORT/PAGINATE (2026-08-17, Pranav's ask): the global text filter,
per-column filters, and column sorting all have to see EVERY row the query
produced, not just whatever's on the currently-displayed page -- so
run_query() fetches up to FETCH_ROW_LIMIT rows (raised from the old 500-row
on-screen-only preview to the same generous ceiling exports already used),
and app.py does filter -> sort -> paginate in memory over that full
fetched set, same "already-tested small-data-volume in-memory" pattern
exporters.py's own docstring documents and every other analytics page on
this portal already uses -- not reinvented here, just applied to a
dynamic-columns result set instead of a fixed one. filter_rows_by_column()/
sort_rows() below are this module's own additions for the per-column
pieces exporters.filter_rows()/paginate() don't already cover.
"""

import re
import sqlite3
import time
from pathlib import Path

import exporters

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "platform.db"

# The one row-count safety ceiling, used for every fetch through this
# module (interactive tab display AND export alike, now that both need the
# full result set to filter/sort correctly, not just a small preview) --
# generous, but still a real backstop against a query that's technically
# valid SELECT but returns something enormous (e.g. a careless cross join).
# This platform's real data volumes are "dozens to low hundreds of rows"
# per exporters.py's own docstring, so this will essentially never bind.
FETCH_ROW_LIMIT = 20_000
FETCH_TIMEOUT_SECONDS = 15.0

PAGE_SIZE_CHOICES = (20, 100, 500)
DEFAULT_PAGE_SIZE = 100

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


def run_query(sql: str, row_limit: int = FETCH_ROW_LIMIT, timeout_seconds: float = FETCH_TIMEOUT_SECONDS) -> dict:
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


def rows_as_dicts(result: dict) -> list:
    """result is run_query()'s own return shape -- converts its
    columns/rows (list-of-lists, positional) into a list of dicts (keyed by
    column name), which is what filter_rows_by_column()/sort_rows()/
    exporters.filter_rows()/exporters.paginate() all expect. A query with a
    duplicate column NAME (e.g. `SELECT a.id, b.id FROM a JOIN b ...` with
    no alias) will collapse to one dict key, keeping only the last value --
    a real SQL-authoring footgun, not something this function can fix; the
    fix on the query-author's side is just to alias the columns
    (`SELECT a.id AS a_id, b.id AS b_id`)."""
    columns = result["columns"]
    return [dict(zip(columns, row)) for row in result["rows"]]


def filter_rows_by_column(rows: list, col_filters: dict) -> list:
    """col_filters: {column_name: filter_text}. ALL given filters must
    match (AND, not OR) for a row to survive -- case-insensitive substring,
    same matching rule exporters.filter_rows() (the global "any column"
    filter) already uses, so the two feel consistent to a user combining
    both. An empty/missing col_filters is a no-op, returns rows unchanged."""
    if not col_filters:
        return rows
    out = []
    for r in rows:
        matched_all = True
        for col, needle in col_filters.items():
            if not needle:
                continue
            v = r.get(col)
            haystack = "" if v is None else str(v)
            if needle.lower() not in haystack.lower():
                matched_all = False
                break
        if matched_all:
            out.append(r)
    return out


def sort_rows(rows: list, column: str, reverse: bool = False) -> list:
    """Sorts a list of dicts by one column. Numeric-aware where every
    non-null value in the column can be read as a number (so a credits
    column sorts 9 before 10, not lexicographically like a plain string
    sort would) -- falls back to a case-insensitive string sort for
    genuinely non-numeric columns. NULLs always sort to the end regardless
    of direction (a missing value is never meaningfully "smallest" or
    "largest" the way a real value is -- flipping direction shouldn't move
    them from one end to the other)."""
    present = [r for r in rows if r.get(column) is not None]
    missing = [r for r in rows if r.get(column) is None]
    try:
        present.sort(key=lambda r: float(r.get(column)), reverse=reverse)
    except (TypeError, ValueError):
        present.sort(key=lambda r: str(r.get(column)).lower(), reverse=reverse)
    return present + missing
