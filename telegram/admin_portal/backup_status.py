"""
telegram/admin_portal/backup_status.py -- Backup Snapshot Summary (2026-08-16)
--------------------------------------------------------------------------------
Reads the `backup_runs` table (schema.sql) that telegram/tools/
backup_to_cloudflare.py writes to on every invocation -- one fast local
query, no live call to R2/D1 on page load and no log-file parsing. See
that script's own docstring and telegram/database/README.md's
"Off-machine backup" section for the full pipeline this reports on.

Wired into the Admin Portal's existing Bot Status page (/bots) as a
"Backup Snapshot Summary" card, per Pranav's ask (2026-08-16) -- backup
status lives alongside bot process status since both answer the same
underlying question ("is the platform actually safe right now").
"""

from __future__ import annotations

HISTORY_LIMIT = 10

_COLUMNS = (
    "run_id, started_at, finished_at, status, duration_seconds, "
    "platform_db_snapshot_kb, myfiles_db_snapshot_kb, secrets_backed_up, "
    "d1_tables_mirrored, d1_rows_mirrored, assets_uploaded, assets_unchanged, "
    "assets_failed, failed_phases, error_detail"
)


def _row_to_dict(row) -> dict:
    (run_id, started_at, finished_at, status, duration_seconds,
     platform_db_snapshot_kb, myfiles_db_snapshot_kb, secrets_backed_up,
     d1_tables_mirrored, d1_rows_mirrored, assets_uploaded, assets_unchanged,
     assets_failed, failed_phases, error_detail) = row
    return {
        "run_id": run_id, "started_at": started_at, "finished_at": finished_at, "status": status,
        "duration_seconds": duration_seconds,
        "platform_db_snapshot_kb": platform_db_snapshot_kb, "myfiles_db_snapshot_kb": myfiles_db_snapshot_kb,
        "secrets_backed_up": secrets_backed_up,
        "d1_tables_mirrored": d1_tables_mirrored, "d1_rows_mirrored": d1_rows_mirrored,
        "assets_uploaded": assets_uploaded, "assets_unchanged": assets_unchanged, "assets_failed": assets_failed,
        "failed_phases": failed_phases, "error_detail": error_detail,
    }


def fetch_backup_summary(conn) -> dict:
    """Returns {"latest": {...} | None, "history": [...]} -- `latest` is the
    single most recent run (shown as the headline card), `history` is the
    last HISTORY_LIMIT runs (newest first, including `latest`) for a small
    trend table. Both None/empty if backup_to_cloudflare.py has never run
    on this machine yet -- an honest "no backup has ever run" state, not a
    silently empty-looking card."""
    rows = conn.execute(
        f"SELECT {_COLUMNS} FROM backup_runs ORDER BY run_id DESC LIMIT {HISTORY_LIMIT}"
    ).fetchall()
    history = [_row_to_dict(r) for r in rows]
    return {"latest": history[0] if history else None, "history": history}
