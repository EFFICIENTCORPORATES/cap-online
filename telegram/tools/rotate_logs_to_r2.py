#!/usr/bin/env python3
"""
telegram/tools/rotate_logs_to_r2.py -- Layer 2 of the two-layer log
rotation policy (LOGGING-ARCHITECTURE.md §6/§10, built 2026-08-18)
--------------------------------------------------------------------------------
Layer 1 (telegram/database/log_rotation.py) keeps each PROCESS's own log
bounded (20MB active + 2 rotated backups, in-process, via
logging.handlers.RotatingFileHandler) -- but with ~9 processes, that alone
can still add up to several hundred MB, and it says nothing about a
GLOBAL ceiling across the whole telegram/database/run/logs/ folder. This
script is that global ceiling: run on its own schedule (Task Scheduler,
hourly -- see CRONJOBS.md), it checks the TOTAL size of everything under
that folder, and once it crosses WATERMARK_BYTES, ships the oldest
already-rotated chunks off to Cloudflare R2 (gzipped, timestamped) and
deletes them locally, oldest-first, until back under budget.

SAFETY -- NEVER touches a file a live process might still be writing to:
  - The ACTIVE `{bot_id}.log` files are open for the entire lifetime of
    their owning bot process (Layer 1's RotatingFileHandler) -- this
    script only ever touches files ALREADY rotated out by Layer 1
    (`{bot_id}.log.1`, `{bot_id}.log.2`, ...), which Python's logging
    module closes before renaming, so nothing holds them open once they
    exist under that name.
  - The `{bot_id}.crash.log` files ARE held open for the bot's entire
    lifetime too (inherited as its OS-level stdout via manage_bots.py's
    subprocess.Popen) -- also never touched directly here. They should
    stay tiny by design (see manage_bots.py's own comment at the change
    site) since routine output no longer lands there at all.
  - A small allowlist of NON-rotating, non-Python batch-script logs
    (currently just ensure_bots_running.log) get shipped+truncated
    directly instead, since nothing holds THOSE open between the brief
    windows a .bat script appends to them -- wrapped in try/except so a
    genuine mid-write collision is skipped and retried next run, never a
    hard failure.

REUSES telegram/tools/backup_to_cloudflare.py's own R2 client/bucket/
credential resolution directly (imported, not duplicated) -- same bucket,
same account, just a different key prefix (logs/ instead of
db-snapshots/ or assets/) and a genuinely different schedule (hourly, not
nightly -- log growth can burst within a single day at real scale, a
once-a-day check risks blowing past WATERMARK_BYTES before the next run).

R2 KEY SHAPE: logs/{bot_id}/{bot_id}_{UTC_timestamp}.log.gz -- one object
per shipped chunk, grouped by bot_id, named so the newest is always
lexically last within its folder.

USAGE:
    python telegram/tools/rotate_logs_to_r2.py            # real run
    python telegram/tools/rotate_logs_to_r2.py --dry-run  # report what WOULD ship, touch nothing
    python telegram/tools/rotate_logs_to_r2.py --force    # ship regardless of current total (testing)

CONFIG: reuses backup_to_cloudflare.py's telegram/.env CF_BACKUP_* vars --
no separate credential path. R2_KEY_PREFIX/retention below are the only
new settings, both this script's own.
"""

import argparse
import gzip
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_DIR = REPO_ROOT / "telegram"

sys.path.insert(0, str(TELEGRAM_DIR / "database"))
import log_rotation  # noqa: E402

LOG_DIR = log_rotation.LOG_DIR
SELF_BOT_ID = "rotate-logs-to-r2"   # this script's OWN log -- also Layer-1-bounded, for consistency

# BUG FIXED 2026-08-18, same day, caught by checking WHICH FILE a real
# Task-Scheduler-triggered run actually wrote to (it was backup.log, not
# rotate-logs-to-r2.log) -- this basicConfig() call MUST run BEFORE
# `import backup_to_cloudflare` below, because THAT module calls its own
# logging.basicConfig() at ITS OWN import time. Python's basicConfig() is
# a no-op once the root logger already has handlers -- whichever import
# happens first wins that race. Getting the order backwards here meant
# every line this script logged silently landed in backup_to_cloudflare's
# own rotated file instead of this script's, even though a correct-
# looking basicConfig() call was sitting right here.
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=log_rotation.build_handlers(SELF_BOT_ID),
)

sys.path.insert(0, str(TELEGRAM_DIR / "tools"))
import backup_to_cloudflare as backup_mod  # noqa: E402 -- reuses its R2 client/bucket/creds, see module docstring
logger = logging.getLogger("rotate_logs_to_r2")

# The 1GB "as a whole" budget: trigger BEFORE the hard ceiling (a
# watermark, not the limit itself) so an hourly check has real headroom
# against bursty growth between runs, and never actually hits 1GB live.
TOTAL_BUDGET_BYTES = 1 * 1024 * 1024 * 1024       # 1GB, the hard ceiling
WATERMARK_BYTES = int(TOTAL_BUDGET_BYTES * 0.8)   # 800MB -- act once crossed

R2_KEY_PREFIX = "logs"
R2_RETENTION_DAYS = 90   # matches LOGGING-ARCHITECTURE.md §8's suggested default; text compresses well, cheap to keep

# Batch-script logs with no owning long-running process holding them open
# between writes -- safe to ship-then-truncate directly (not through
# Layer 1's rotation, they're not Python). Each gets its own, much
# smaller threshold, independent of the global watermark -- these should
# never legitimately grow large; if one does, ship it regardless.
DIRECT_MANAGE_FILES = {
    "ensure_bots_running.log": 5 * 1024 * 1024,   # 5MB
}


def _current_total_bytes() -> int:
    return sum(p.stat().st_size for p in LOG_DIR.glob("*") if p.is_file())


def _rotated_chunks() -> list:
    """Every file Layer 1's RotatingFileHandler has already rotated OUT --
    matches "{name}.log.{n}" for any n, e.g. "1lavya-studyhub.log.1" --
    NEVER the bare "{name}.log" (still open, still being written to)."""
    return [p for p in LOG_DIR.glob("*.log.*") if p.is_file()]


def _bot_id_from_rotated_name(path: Path) -> str:
    # "1lavya-studyhub.log.1" -> "1lavya-studyhub"
    return path.name.split(".log.")[0]


def _ship_and_delete(s3, path: Path, *, dry_run: bool) -> int:
    """Gzips + uploads `path` to R2 under logs/{bot_id}/{bot_id}_{ts}.log.gz,
    then deletes the local copy ONLY after a verified successful upload.
    Returns the number of bytes freed (0 on dry-run or any failure)."""
    bot_id = _bot_id_from_rotated_name(path)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    key = f"{R2_KEY_PREFIX}/{bot_id}/{bot_id}_{ts}.log.gz"
    size = path.stat().st_size

    if dry_run:
        logger.info(f"[DRY RUN] would ship {path.name} ({size / 1024:.1f} KB) -> {key}, then delete locally")
        return 0

    try:
        compressed = gzip.compress(path.read_bytes())
    except OSError as e:
        logger.warning(f"Could not read {path} (likely a transient write in progress) -- skipping this run: {e}")
        return 0

    try:
        s3.put_object(Bucket=backup_mod.BUCKET_NAME, Key=key, Body=compressed)
    except Exception as e:
        logger.error(f"Upload FAILED for {path.name} -> {key}: {e} -- leaving the local file in place.")
        return 0

    try:
        path.unlink()
    except OSError as e:
        # Uploaded successfully but couldn't delete locally -- not a data-loss
        # risk (R2 has it), just means this run's freed-space count is off
        # and the next run will try to re-ship the same content. Log and move on.
        logger.warning(f"Uploaded {key} OK but could not delete local {path}: {e}")
        return 0

    logger.info(f"Shipped + removed: {path.name} ({size / 1024:.1f} KB) -> {key}")
    return size


def _ship_direct_managed_files(s3, *, dry_run: bool) -> int:
    """The small allowlist of non-Python batch-script logs -- shipped
    whole + TRUNCATED (never deleted -- the owning .bat script's next
    `>>` append assumes the file still exists) once they cross their own
    threshold."""
    freed = 0
    for name, threshold in DIRECT_MANAGE_FILES.items():
        path = LOG_DIR / name
        if not path.exists() or path.stat().st_size < threshold:
            continue
        bot_id = path.stem
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        key = f"{R2_KEY_PREFIX}/{bot_id}/{bot_id}_{ts}.log.gz"
        size = path.stat().st_size
        if dry_run:
            logger.info(f"[DRY RUN] would ship+truncate {name} ({size / 1024:.1f} KB) -> {key}")
            continue
        try:
            compressed = gzip.compress(path.read_bytes())
            s3.put_object(Bucket=backup_mod.BUCKET_NAME, Key=key, Body=compressed)
            path.write_text("", encoding="utf-8")   # truncate in place, don't delete
            logger.info(f"Shipped + truncated: {name} ({size / 1024:.1f} KB) -> {key}")
            freed += size
        except OSError as e:
            logger.warning(f"Could not ship/truncate {name} (likely a transient write in progress): {e}")
    return freed


def _prune_old_r2_logs(s3):
    backup_mod.prune_by_age(s3, f"{R2_KEY_PREFIX}/", R2_RETENTION_DAYS)


def _alert_failure(text: str):
    try:
        sys.path.insert(0, str(TELEGRAM_DIR / "bots"))
        import watcher_bot  # noqa: E402  (reuses resolve_sender_token/send_telegram_dm/load_alerts_config)
        token = watcher_bot.resolve_sender_token()
        cfg = watcher_bot.load_alerts_config()
        chat_ids = cfg.get("admin_chat_ids", [])
        if not token or not chat_ids:
            logger.warning("Could not send failure alert (no sender token / admin_chat_ids configured).")
            return
        full_text = f"\U0001F534 LOG ROTATION FAILED\n{text}\nLog: telegram/database/run/logs/{SELF_BOT_ID}.log"
        for cid in chat_ids:
            watcher_bot.send_telegram_dm(token, cid, full_text)
    except Exception:
        logger.exception("Failed to send the failure alert itself.")


def main():
    parser = argparse.ArgumentParser(
        description="Layer 2: ship overflow log chunks to Cloudflare R2, keep telegram/database/run/logs/ under its local budget."
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what WOULD be shipped/deleted, touch nothing.")
    parser.add_argument("--force", action="store_true", help="Act regardless of the current total (testing).")
    args = parser.parse_args()

    missing = [name for name in ("ACCOUNT_ID", "API_TOKEN", "R2_ACCESS_KEY", "R2_SECRET_KEY")
               if not getattr(backup_mod, name, None)]
    if missing:
        logger.error(f"Missing required telegram/.env CF_BACKUP_* vars (backup_to_cloudflare.py's {missing} resolved empty). Aborting.")
        sys.exit(1)

    s3 = backup_mod.get_s3_client()
    try:
        backup_mod.ensure_bucket(s3)
    except Exception as e:
        logger.exception("Bucket setup failed -- aborting, nothing else can proceed without it.")
        _alert_failure(f"Bucket setup failed: {e}")
        sys.exit(1)

    started = time.time()
    total_before = _current_total_bytes()
    logger.info(
        f"Current total under {LOG_DIR}: {total_before / (1024*1024):.1f} MB "
        f"(watermark {WATERMARK_BYTES / (1024*1024):.0f} MB, ceiling {TOTAL_BUDGET_BYTES / (1024*1024):.0f} MB)"
    )

    freed, shipped, failures = 0, 0, 0

    if args.force or total_before >= WATERMARK_BYTES:
        chunks = sorted(_rotated_chunks(), key=lambda p: p.stat().st_mtime)  # oldest first
        for chunk in chunks:
            if not args.force and (total_before - freed) < WATERMARK_BYTES:
                break
            result = _ship_and_delete(s3, chunk, dry_run=args.dry_run)
            if result:
                freed += result
                shipped += 1
            elif not args.dry_run:
                failures += 1
    else:
        logger.info("Under watermark -- nothing to ship this run.")

    freed += _ship_direct_managed_files(s3, dry_run=args.dry_run)

    if not args.dry_run:
        try:
            _prune_old_r2_logs(s3)
        except Exception:
            logger.exception("R2-side retention prune failed (non-fatal -- shipped objects are still safe, just not pruned this run).")

    elapsed = time.time() - started
    total_after = _current_total_bytes()
    logger.info(
        f"Done in {elapsed:.1f}s. Shipped {shipped} rotated chunk(s), freed ~{freed / (1024*1024):.1f} MB. "
        f"Total now: {total_after / (1024*1024):.1f} MB."
    )

    if failures:
        _alert_failure(f"{failures} chunk(s) failed to ship/delete this run -- see the log for detail.")
        sys.exit(1)


if __name__ == "__main__":
    main()
