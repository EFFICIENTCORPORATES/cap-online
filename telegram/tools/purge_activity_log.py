#!/usr/bin/env python3
"""
telegram/tools/purge_activity_log.py -- retention sweep for
user_activity_log (LOGGING-ARCHITECTURE.md §8 Q1, answered 2026-08-18:
Pranav chose 180 days)
--------------------------------------------------------------------------------
`user_activity_log` (the fine-grained per-tap activity trail, §3-4 of
LOGGING-ARCHITECTURE.md) had NO retention policy at all before this --
the one DB table on this whole platform with genuinely unbounded growth
and no sweep precedent to copy (wallet_ledger/payments/admin_actions etc.
are all permanent-by-design audit trails; this is the one table that
isn't). At 419 rows after ~1.5 days of real Phase-1 traffic this was a
non-issue in practice, but "no policy" isn't the same as "the right
policy," so this closes that gap rather than leaving it open indefinitely.

WHY A SEPARATE SCRIPT, NOT FOLDED INTO backup_to_cloudflare.py OR
rotate_logs_to_r2.py: different concern entirely (deleting old DB rows,
not shipping files), different natural cadence (this only needs to run
occasionally -- daily is already generous for a 180-day retention window)
-- matches this platform's own "one script, one job" precedent
(backup_to_cloudflare.py / rotate_logs_to_r2.py / generate_day_end_
faculty_reports.py are all separate scripts on separate schedules for the
same reason).

RETENTION_DAYS = 180 is Pranav's own explicit choice (2026-08-18,
AskUserQuestion) -- never silently change this number without asking
again, same "explicit number, not an assumption" discipline this exact
policy already required once.

USAGE:
    python telegram/tools/purge_activity_log.py            # real run
    python telegram/tools/purge_activity_log.py --dry-run  # report the row count that WOULD be deleted, touch nothing

SCHEDULING: Windows Task Scheduler, "1LAVYA Activity Log Purge", daily --
see CRONJOBS.md.
"""

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_DIR = REPO_ROOT / "telegram"

sys.path.insert(0, str(TELEGRAM_DIR / "database"))
import log_rotation  # noqa: E402 -- basicConfig() must run before any other import that might call its own (see rotate_logs_to_r2.py's bug #3 for exactly why this ordering matters)

SELF_BOT_ID = "purge-activity-log"
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=log_rotation.build_handlers(SELF_BOT_ID),
)
logger = logging.getLogger("purge_activity_log")

import db as platform_db  # noqa: E402

RETENTION_DAYS = 180   # Pranav's explicit choice, 2026-08-18 -- see module docstring


def main():
    parser = argparse.ArgumentParser(description="Delete user_activity_log rows older than RETENTION_DAYS.")
    parser.add_argument("--dry-run", action="store_true", help="Report the row count that WOULD be deleted, touch nothing.")
    args = parser.parse_args()

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    cutoff_expr = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now', ?)"
    offset = f"-{RETENTION_DAYS} days"

    total_before = conn.execute("SELECT COUNT(*) FROM user_activity_log").fetchone()[0]
    to_delete = conn.execute(
        f"SELECT COUNT(*) FROM user_activity_log WHERE created_at < {cutoff_expr}", (offset,)
    ).fetchone()[0]

    logger.info(f"user_activity_log: {total_before} total rows, {to_delete} older than {RETENTION_DAYS} days.")

    if args.dry_run:
        logger.info(f"[DRY RUN] would delete {to_delete} row(s), touching nothing.")
        return

    if to_delete == 0:
        logger.info("Nothing to purge this run.")
        return

    platform_db.execute_with_retry(
        conn, f"DELETE FROM user_activity_log WHERE created_at < {cutoff_expr}", (offset,)
    )
    conn.commit()
    total_after = conn.execute("SELECT COUNT(*) FROM user_activity_log").fetchone()[0]
    logger.info(f"Purged {total_before - total_after} row(s). {total_after} rows remain.")


if __name__ == "__main__":
    main()
