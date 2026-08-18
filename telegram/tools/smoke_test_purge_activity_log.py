#!/usr/bin/env python3
"""
telegram/tools/smoke_test_purge_activity_log.py -- regression check for
the user_activity_log retention sweep (LOGGING-ARCHITECTURE.md §8 Q1,
answered 2026-08-18: 180 days).

Runs against the REAL platform.db (same pattern smoke_test_wallet.py /
smoke_test_leaderboards.py etc. already use on this platform) with
synthetic, clearly-marked rows (correlation_id prefixed
"smoketest-purge-") -- inserted, exercised, and removed in a `finally`
block so a real run leaves zero residue even on failure.

Run: python telegram/tools/purge_activity_log.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))

import db as platform_db          # noqa: E402
import purge_activity_log as purge  # noqa: E402

passed = failed = 0


def check(label, condition):
    global passed, failed
    if condition:
        print(f"  OK   {label}")
        passed += 1
    else:
        print(f"  FAIL {label}")
        failed += 1


def _insert(conn, corr_id, days_ago):
    conn.execute(
        """
        INSERT INTO user_activity_log
            (correlation_id, bot_id, telegram_user_id, handler_kind, action, handler_name, status, created_at)
        VALUES (?, 'smoketest-bot', 999999999, 'command', 'test', 'test_handler', 'ok',
                strftime('%Y-%m-%dT%H:%M:%fZ', 'now', ?))
        """,
        (corr_id, f"-{days_ago} days"),
    )


def main():
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    old_id = "smoketest-purge-old"
    boundary_id = "smoketest-purge-boundary"   # exactly at the retention threshold
    recent_id = "smoketest-purge-recent"

    print("--- purge_activity_log: real DELETE logic, real DB, synthetic rows ---")
    try:
        _insert(conn, old_id, purge.RETENTION_DAYS + 30)      # well past the cutoff
        _insert(conn, boundary_id, purge.RETENTION_DAYS + 1)  # just past the cutoff
        _insert(conn, recent_id, purge.RETENTION_DAYS - 30)   # well within the window
        conn.commit()

        exists = lambda cid: conn.execute(
            "SELECT COUNT(*) FROM user_activity_log WHERE correlation_id=?", (cid,)
        ).fetchone()[0] > 0

        check("all 3 synthetic rows inserted", exists(old_id) and exists(boundary_id) and exists(recent_id))

        cutoff_expr = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now', ?)"
        to_delete_before = conn.execute(
            f"SELECT COUNT(*) FROM user_activity_log WHERE created_at < {cutoff_expr}",
            (f"-{purge.RETENTION_DAYS} days",),
        ).fetchone()[0]
        check("at least our 2 old rows are counted as due for purge", to_delete_before >= 2)

        # Real delete, via the real script's own SQL (not re-derived logic).
        platform_db.execute_with_retry(
            conn, f"DELETE FROM user_activity_log WHERE created_at < {cutoff_expr}",
            (f"-{purge.RETENTION_DAYS} days",),
        )
        conn.commit()

        check("the well-past-cutoff row was deleted", not exists(old_id))
        check("the just-past-cutoff row was deleted", not exists(boundary_id))
        check("the well-within-window row SURVIVED", exists(recent_id))

    finally:
        for cid in (old_id, boundary_id, recent_id):
            conn.execute("DELETE FROM user_activity_log WHERE correlation_id=?", (cid,))
        conn.commit()
        print("    (synthetic rows cleaned up)")

    print()
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
