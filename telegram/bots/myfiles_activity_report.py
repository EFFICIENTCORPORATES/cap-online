"""
MyFiles Hub -- activity report
-------------------------------
Reads the activity_log and files tables from the MyFiles Hub SQLite database
and prints a human-readable summary: per-student file counts + storage used,
activity counts by action type, and the most recent N events. Optionally
exports the full activity log to CSV.

This is a read-only reporting script -- it never writes to the bot's database.

Usage:
    python myfiles_activity_report.py
    python myfiles_activity_report.py --recent 50
    python myfiles_activity_report.py --csv activity_export.csv
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]   # telegram/bots/myfiles_activity_report.py -> repo root

# Derived from REPO_ROOT, same pattern as myfiles_hub_bot.py's own DB_PATH --
# was hardcoded to a D:\EffCorp_Projects\cap-online\... path until 2026-08-12;
# fixed as part of the telegram/ portability pass -- see FIRST_PROMPT.md.
DB_PATH = str(REPO_ROOT / "telegram" / "assets" / "myfiles_bot" / "myfiles_hub.db")


def get_conn():
    if not Path(DB_PATH).exists():
        sys.exit(f"Database not found at {DB_PATH} -- edit DB_PATH at the top of this script if it moved.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fmt_size(n):
    n = n or 0
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} bytes"


def print_per_student_summary(conn):
    print("=== Per-student summary (active, non-deleted files) ===")
    rows = conn.execute(
        """
        SELECT u.chat_id, u.email, u.display_name,
               COUNT(DISTINCT CASE WHEN f.is_deleted = 0 THEN f.id END) AS active_files,
               COALESCE(SUM(CASE WHEN f.is_deleted = 0 THEN f.file_size_bytes END), 0) AS total_bytes
        FROM users u
        LEFT JOIN files f ON f.chat_id = u.chat_id
        GROUP BY u.chat_id
        ORDER BY active_files DESC
        """
    ).fetchall()
    if not rows:
        print("  (no students registered yet)")
        return
    for r in rows:
        name = r["display_name"] or "(no name)"
        email = r["email"] or "(no email)"
        print(f"  {name:<22} {email:<32} files={r['active_files']:<4} size={fmt_size(r['total_bytes'])}")


def print_action_counts(conn):
    print("\n=== Activity counts by action ===")
    rows = conn.execute(
        "SELECT action, COUNT(*) AS c FROM activity_log GROUP BY action ORDER BY c DESC"
    ).fetchall()
    if not rows:
        print("  (no activity recorded yet)")
        return
    for r in rows:
        print(f"  {r['action']:<18} {r['c']}")


def print_recent(conn, n):
    print(f"\n=== Last {n} activity events ===")
    rows = conn.execute(
        "SELECT created_at, chat_id, email, action, detail, file_size_bytes "
        "FROM activity_log ORDER BY id DESC LIMIT ?",
        (n,),
    ).fetchall()
    if not rows:
        print("  (no activity recorded yet)")
        return
    for r in rows:
        size = f" ({fmt_size(r['file_size_bytes'])})" if r["file_size_bytes"] else ""
        print(f"  {r['created_at']}  chat={r['chat_id']:<12} {r['action']:<16} "
              f"{r['email'] or '':<28} {r['detail'] or ''}{size}")


def export_csv(conn, path):
    rows = conn.execute(
        "SELECT id, chat_id, email, action, detail, file_size_bytes, created_at "
        "FROM activity_log ORDER BY id"
    ).fetchall()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "chat_id", "email", "action", "detail", "file_size_bytes", "created_at"])
        for r in rows:
            writer.writerow(list(r))
    print(f"\nExported {len(rows)} activity rows to {path}")


def main():
    parser = argparse.ArgumentParser(description="MyFiles Hub activity report")
    parser.add_argument("--recent", type=int, default=20, help="Show the N most recent activity events (default 20)")
    parser.add_argument("--csv", type=str, default=None, help="Export the full activity log to this CSV path")
    args = parser.parse_args()

    conn = get_conn()
    print_per_student_summary(conn)
    print_action_counts(conn)
    print_recent(conn, args.recent)
    if args.csv:
        export_csv(conn, args.csv)
    conn.close()


if __name__ == "__main__":
    main()
