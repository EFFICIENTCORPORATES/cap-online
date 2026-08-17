"""
telegram/admin_portal/smoke_test_sql_query_tool.py -- verifies the
read-only guarantee is REAL, not just documented (2026-08-17)
--------------------------------------------------------------------------------
This is the one module on this whole platform where "structurally passes"
isn't enough -- the entire point of sql_query_tool.py is that it CANNOT
write to platform.db no matter what text is submitted. So this suite
doesn't just check the validator rejects bad text; it also tries to
actually write through the tool's own real connection-opening code and
confirms sqlite3 itself refuses, proving the guarantee at the layer that
actually matters.

Run directly: python smoke_test_sql_query_tool.py
"""

import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sql_query_tool as sqt

passed = 0
failed = 0


def check(label, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  OK   {label}")
    else:
        failed += 1
        print(f"  FAIL {label}")


print("=== validate_readonly_select() -- text-level rejection ===")

for bad_sql, why in [
    ("", "empty"),
    ("   ", "whitespace only"),
    ("UPDATE students SET email='x'", "UPDATE"),
    ("DELETE FROM wallet_ledger", "DELETE"),
    ("DROP TABLE students", "DROP"),
    ("ATTACH DATABASE 'x.db' AS x", "ATTACH"),
    ("PRAGMA table_info(students)", "PRAGMA"),
    ("SELECT 1; DELETE FROM students", "multi-statement (write hidden after semicolon)"),
    ("SELECT 1; SELECT 2", "multi-statement (both harmless, still rejected -- one at a time)"),
    ("-- DELETE FROM students\nUPDATE students SET email='x'", "write disguised behind a comment"),
]:
    try:
        sqt.validate_readonly_select(bad_sql)
        check(f"rejects {why}", False)
    except sqt.QueryRejected:
        check(f"rejects {why}", True)
    except Exception as e:
        check(f"rejects {why} (wrong exception type: {type(e).__name__})", False)

for good_sql, why in [
    ("SELECT 1", "plain SELECT"),
    ("select 1", "lowercase select"),
    ("  SELECT 1  ", "SELECT with surrounding whitespace"),
    ("SELECT 1;", "SELECT with one harmless trailing semicolon"),
    ("WITH x AS (SELECT 1) SELECT * FROM x", "WITH / CTE"),
    ("-- a comment\nSELECT 1", "SELECT preceded by a comment"),
]:
    try:
        sqt.validate_readonly_select(good_sql)
        check(f"accepts {why}", True)
    except Exception as e:
        check(f"accepts {why} (raised {type(e).__name__}: {e})", False)

print()
print("=== run_query() -- real execution against the real DB, read-only ===")

# A real, representative query matching Pranav's own stated example: a
# student ID + credit balance + a calculated "used in last N days" column.
result = sqt.run_query("""
    SELECT username,
           SUM(amount) AS balance,
           SUM(CASE WHEN amount < 0 AND created_at >= datetime('now', '-10 days') THEN -amount ELSE 0 END) AS used_last_10_days
    FROM wallet_ledger
    GROUP BY username
    ORDER BY balance ASC
""")
check("returns real columns", result["columns"] == ["username", "balance", "used_last_10_days"])
check("returns at least one real row (platform has real students)", result["row_count"] > 0)
check("not truncated for a small real result", result["truncated"] is False)
check("elapsed_ms is a real, non-negative measurement", result["elapsed_ms"] >= 0)
print(f"    -> {result['row_count']} rows, {result['elapsed_ms']:.1f}ms, e.g. {result['rows'][0] if result['rows'] else None}")

# Row-cap / truncation behavior, using a cheap generated series so this
# doesn't depend on platform.db actually having >5 rows in any one table.
capped = sqt.run_query("WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt WHERE x<20) SELECT x FROM cnt", row_limit=5)
check("row cap actually caps the returned rows", capped["row_count"] == 5)
check("truncated=True when more rows existed than the cap", capped["truncated"] is True)

uncapped = sqt.run_query("WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt WHERE x<3) SELECT x FROM cnt", row_limit=500)
check("truncated=False when fewer rows than the cap", uncapped["truncated"] is False)
check("all rows returned when under the cap", uncapped["row_count"] == 3)

# Query-level error (bad SQL that IS a SELECT, so passes text validation,
# but sqlite3 itself rejects it) -- must surface as QueryFailed, not crash
# the caller with a raw traceback.
try:
    sqt.run_query("SELECT * FROM this_table_does_not_exist")
    check("a genuine SQL error (unknown table) raises QueryFailed", False)
except sqt.QueryFailed:
    check("a genuine SQL error (unknown table) raises QueryFailed", True)
except Exception as e:
    check(f"a genuine SQL error raises the WRONG exception type ({type(e).__name__})", False)

print()
print("=== THE guarantee: a write attempt against the tool's OWN connection-opening code physically fails ===")

# This is the test that actually matters most in this file: open a
# connection the SAME way run_query() does (not mocked, not assumed) and
# try to write through it directly. If this ever stops raising, the core
# safety property of this whole module is broken.
conn = sqt._readonly_connection()
try:
    conn.execute("UPDATE students SET email='pwned' WHERE telegram_user_id=1")
    conn.commit()
    check("a raw write attempt on the tool's read-only connection is physically refused by SQLite", False)
except sqlite3.OperationalError as e:
    check(f"a raw write attempt on the tool's read-only connection is physically refused by SQLite ({e})", "readonly" in str(e).lower())
finally:
    conn.close()

# And confirm the SAME connection can still genuinely read -- the
# guarantee is "no writes," never "nothing works."
conn2 = sqt._readonly_connection()
try:
    row = conn2.execute("SELECT COUNT(*) FROM students").fetchone()
    check("the same read-only connection can still read real data", row[0] >= 0)
finally:
    conn2.close()

print()
print("=== Confirm this test made ZERO real changes to platform.db ===")
# Re-check the exact student row the write attempt above targeted --
# must be untouched.
conn3 = sqt._readonly_connection()
try:
    row = conn3.execute("SELECT email FROM students WHERE telegram_user_id=1").fetchone()
    check("students.telegram_user_id=1's email was NOT changed by the write-attempt test above", (row is None) or (row[0] != "pwned"))
finally:
    conn3.close()

print()
print("=== rows_as_dicts() / filter_rows_by_column() / sort_rows() -- the filter/sort/paginate feature (2026-08-17) ===")

sample = sqt.run_query("""
    WITH data(name, credits) AS (
        VALUES ('Karan', 1000), ('Anmol', 250), ('Piyush', 1000), ('Harsh', NULL), ('taslim', 78)
    )
    SELECT name, credits FROM data
""")
dict_rows = sqt.rows_as_dicts(sample)
check("rows_as_dicts() produces one dict per row, keyed by real column names",
      dict_rows == [
          {"name": "Karan", "credits": 1000}, {"name": "Anmol", "credits": 250},
          {"name": "Piyush", "credits": 1000}, {"name": "Harsh", "credits": None},
          {"name": "taslim", "credits": 78},
      ])

# Per-column filter -- case-insensitive substring, AND across multiple columns.
only_karan = sqt.filter_rows_by_column(dict_rows, {"name": "kar"})
check("filter_rows_by_column() matches case-insensitively", [r["name"] for r in only_karan] == ["Karan"])
none_filter = sqt.filter_rows_by_column(dict_rows, {})
check("filter_rows_by_column() with no filters is a no-op", none_filter == dict_rows)
both_cols = sqt.filter_rows_by_column(dict_rows, {"name": "a", "credits": "1000"})
# Karan AND Piyush both have credits=1000, but only Karan's name contains
# "a" (Piyush doesn't) -- so the AND of both filters must exclude Piyush.
check("filter_rows_by_column() ANDs multiple column filters together (not OR)",
      [r["name"] for r in both_cols] == ["Karan"])

# Numeric-aware sort -- 78 must come before 250 and 1000 (a plain string
# sort would put "1000" before "250" before "78", which is wrong).
asc = sqt.sort_rows(dict_rows, "credits", reverse=False)
check("sort_rows() ascending is numeric, not lexicographic",
      [r["credits"] for r in asc if r["credits"] is not None] == [78, 250, 1000, 1000])
check("sort_rows() puts NULLs at the end (ascending)", asc[-1]["name"] == "Harsh")
desc = sqt.sort_rows(dict_rows, "credits", reverse=True)
check("sort_rows() descending is also numeric", [r["credits"] for r in desc if r["credits"] is not None] == [1000, 1000, 250, 78])
check("sort_rows() still puts NULLs at the end when descending (not the start)", desc[-1]["name"] == "Harsh")

# Text-column sort (no numeric fallback needed) -- alphabetical, case-insensitive
# (real column has a deliberately lowercase 'taslim' among capitalized names).
name_sorted = sqt.sort_rows(dict_rows, "name", reverse=False)
check("sort_rows() on a text column is case-insensitive alphabetical",
      [r["name"] for r in name_sorted] == ["Anmol", "Harsh", "Karan", "Piyush", "taslim"])

print()
print(f"{passed} passed, {failed} failed")
if failed:
    sys.exit(1)
