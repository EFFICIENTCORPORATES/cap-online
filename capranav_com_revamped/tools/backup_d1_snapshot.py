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

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "database-backups"
LOG_FILE = BACKUP_DIR / "backup.log"
DATABASE_NAME = "capranav-platform"
RETENTION_DAYS = 30  # older snapshots are pruned automatically

# Where failure alerts go — same inbox the Worker's own order-notification
# emails already use (see CONTACT_TO in worker/index.js).
ALERT_TO = "capranavpratiktulshyan@gmail.com"


def log(message: str) -> None:
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] {message}"
    try:
        print(line)
    except UnicodeEncodeError:
        # Windows' default console codepage (cp1252) can't display some
        # characters wrangler's own error output contains (emoji,
        # box-drawing) — found for real while testing the failure path
        # below, and it would otherwise crash the script before a real
        # failure ever reached send_failure_alert(). The log FILE (written
        # as UTF-8 just below) always keeps the full, undamaged text either
        # way — this is a console-display fallback only, not data loss.
        print(line.encode("ascii", errors="replace").decode("ascii"))
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_dev_vars() -> dict:
    """Read .dev.vars (gitignored) for the Cloudflare Email Sending credentials
    a failure alert needs — the same file the Worker's own local dev already
    uses, and the same product (worker/lib/email.js) already verified working
    for capranav.com's domain."""
    path = ROOT / ".dev.vars"
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def send_failure_alert(reason: str) -> None:
    creds = load_dev_vars()
    account_id = creds.get("CF_EMAIL_ACCOUNT_ID")
    api_token = creds.get("CF_EMAIL_API_TOKEN")
    if not account_id or not api_token:
        log("Could not send failure alert email: CF_EMAIL_ACCOUNT_ID/CF_EMAIL_API_TOKEN missing from .dev.vars.")
        return

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/sending/send"
    payload = json.dumps(
        {
            "from": "CA Pranav <backup-alerts@capranav.com>",
            "to": ALERT_TO,
            "subject": "capranav.com — D1 backup FAILED",
            "html": (
                "<p><strong>The scheduled D1 backup job (backup_d1_snapshot.py) failed.</strong></p>"
                f"<p>{reason}</p>"
                f"<p>See database-backups/backup.log on the machine this runs on for the full detail.</p>"
            ),
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("success"):
            log("Failure alert email sent.")
        else:
            log(f"Failure alert email API returned non-success: {body}")
    except urllib.error.URLError as e:
        log(f"Could not send failure alert email: {e}")
    except Exception as e:
        log(f"Could not send failure alert email (unexpected error): {e}")


def run_export(database_name: str) -> bool:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = BACKUP_DIR / f"{database_name}_{stamp}.sql"

    cmd = f'npx --yes wrangler d1 export {database_name} --remote --output="{out_file}"'
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        default=DATABASE_NAME,
        help=(
            "D1 database name to export (default: the real capranav-platform). "
            "Override only to deliberately test the failure-alert path against a "
            "nonexistent name — never for a real scheduled run."
        ),
    )
    args = parser.parse_args()

    ok = run_export(args.database)
    prune_old_snapshots()
    if not ok:
        send_failure_alert(
            f"wrangler d1 export failed for database '{args.database}'. "
            "See backup.log for the exact error."
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
