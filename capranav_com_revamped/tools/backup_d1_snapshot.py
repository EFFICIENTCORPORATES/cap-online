"""
backup_d1_snapshot.py — export a local copy of the live Cloudflare D1
database ("capranav-platform") to database-backups/, timestamped.

Run manually:
    python tools/backup_d1_snapshot.py

Scheduled: Windows Task Scheduler job "CA Pranav D1 Backup", every 6 hours.
See DATABASE-BACKUP.md (this folder) for what this does, why, the retention
policy, and how to restore from a snapshot.

Contains real student PII (emails, phone numbers, order/shipping details) —
database-backups/ is gitignored and must never be committed.
"""

import subprocess
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "database-backups"
LOG_FILE = BACKUP_DIR / "backup.log"
DATABASE_NAME = "capranav-platform"
RETENTION_DAYS = 30  # older snapshots are pruned automatically


def log(message: str) -> None:
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] {message}"
    print(line)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_export() -> bool:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = BACKUP_DIR / f"{DATABASE_NAME}_{stamp}.sql"

    cmd = f'npx --yes wrangler d1 export {DATABASE_NAME} --remote --output="{out_file}"'
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # wrangler prints emoji/box-drawing chars the default Windows codepage can't decode
            timeout=300,
        )
    except Exception as e:
        log(f"FAILED to run wrangler export: {e}")
        return False

    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip()[-500:]
        log(f"FAILED (exit {result.returncode}): {tail}")
        return False

    if not out_file.exists() or out_file.stat().st_size == 0:
        log("FAILED: export command reported success but the output file is missing or empty.")
        return False

    log(f"OK: snapshot written to {out_file.name} ({out_file.stat().st_size:,} bytes)")
    return True


def prune_old_snapshots() -> None:
    cutoff = datetime.datetime.now() - datetime.timedelta(days=RETENTION_DAYS)
    removed = 0
    for f in BACKUP_DIR.glob(f"{DATABASE_NAME}_*.sql"):
        try:
            mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                removed += 1
        except OSError:
            continue
    if removed:
        log(f"Pruned {removed} snapshot(s) older than {RETENTION_DAYS} days.")


def main() -> int:
    ok = run_export()
    prune_old_snapshots()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
