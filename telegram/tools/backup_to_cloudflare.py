#!/usr/bin/env python3
"""
telegram/tools/backup_to_cloudflare.py -- off-machine backup pipeline (2026-08-16)
--------------------------------------------------------------------------------
Everything under telegram/ that ISN'T already safe via `git push` -- see
CLAUDE.md's "Telegram platform: known scale-readiness gaps" callout, gap #1
("no real off-machine backup") -- gets a nightly copy pushed to Cloudflare
R2 (+ a queryable D1 mirror of platform.db), on Pranav's own Cloudflare
account (same account CF_EMAIL_* already uses -- confirmed 2026-08-14,
staying there rather than the separate 1LAVYA account until the domain
itself migrates, see memory 1lavya-cloudflare-account).

Deliberately NOT registered in telegram/config/bots.json / managed by
manage_bots.py -- this is a run-to-completion batch job (driven by Windows
Task Scheduler), not a long-running process with a heartbeat; forcing it
into the bot-management model would make it show as permanently "offline"
between runs for no benefit.

WHAT GETS BACKED UP (see CLAUDE.md's telegram/ backup-planning conversation,
2026-08-13/14, for the full reasoning on what's in/out of scope):
  1. SQLite-CONSISTENT snapshots of platform.db + myfiles_hub.db (via
     sqlite3's own .backup() API, never a raw file copy -- safe even while
     WAL-mode writers are live) -- gzipped, timestamped, 60-day retention.
  2. A full D1 mirror of platform.db, refreshed (wipe + reinsert) every
     run -- a QUERYABLE off-site copy, not just a blob backup. Modest data
     volume today (a few thousand rows total) makes a full refresh simpler
     and more robust than incremental sync logic. Schema replay re-inserts
     "IF NOT EXISTS" itself (see _ensure_if_not_exists) -- sqlite_master.sql
     silently drops that clause from the stored DDL text even when the
     original CREATE TABLE had one, a real bug caught by re-running this
     against an already-populated D1 database, not by reading the code.
  3. .env + creds.txt -- Fernet-encrypted (PBKDF2-derived key from
     CF_BACKUP_ENCRYPTION_PASSPHRASE) before upload, NEVER plaintext.
     Losing the passphrase makes only this backup copy unrecoverable -- the
     live files on this PC are untouched either way. Pranav was told to
     also save this passphrase in a password manager (NOT just .env),
     since if this machine's disk dies, .env dies with it too.
  4. Live-served asset folders (study_bot/faculty/exam_bot PDFs+JSON,
     myfiles_bot/uploads -- real student-uploaded files) -- MD5-vs-ETag
     compared against what's already in R2 so a re-run only uploads
     new/changed files, never deletes a remote object based on local state
     (a backup that can delete backed-up content because a local file
     moved/vanished is a liability, not a safety net).

DELIBERATELY EXCLUDED: assets/backup pdfs/ (1.5GB, documented in CLAUDE.md
as pre-restructuring leftover, "not read by anything" -- Pranav's explicit
call, 2026-08-13) and database/run/logs/ (diagnostic, regenerates itself --
see telegram/tools/rotate_logs_to_r2.py instead, 2026-08-18, its own
SEPARATE hourly job that ships only the overflow once the local log
budget is exceeded -- see LOGGING-ARCHITECTURE.md §6/§10 for why this
stays a different script on a different schedule rather than a 5th phase
bolted onto this one).
Python code + question-bank JSON + config JSON are already safe via git.

USAGE:
    python telegram/tools/backup_to_cloudflare.py                # full run
    python telegram/tools/backup_to_cloudflare.py --skip-assets  # DB + secrets + D1 only (fast)
    python telegram/tools/backup_to_cloudflare.py --skip-d1      # skip the D1 mirror refresh
    python telegram/tools/backup_to_cloudflare.py --decrypt-secret path/to/secrets/env/env_20260816_030000.enc
        # writes the decrypted plaintext to stdout -- the actual disaster-recovery path.

CONFIG: telegram/.env's CF_BACKUP_* vars (account id, API token, R2 access
key/secret -- see that file's own comment for how these were derived/
verified, and _claude/memory's 1lavya-cloudflare-account for the full
provenance) plus CF_BACKUP_ENCRYPTION_PASSPHRASE (secrets backup is SKIPPED,
loudly, if this is unset -- never silently sends .env/creds.txt unencrypted).

ON FAILURE: sends a DM via the same watcher_bot.py plumbing (MyFiles Hub
bot token + telegram/config/alerts.json's admin_chat_ids) already used for
bot down/up alerts -- reused directly, not reimplemented. Silent on
success (no nightly noise), same edge-triggered philosophy as the watcher.
"""

import argparse
import base64
import gzip
import hashlib
import json
import logging
import logging.handlers
import os
import re
import sqlite3
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_DIR = REPO_ROOT / "telegram"

sys.path.insert(0, str(TELEGRAM_DIR / "database"))
import db as platform_db  # noqa: E402 -- for the backup_runs audit-trail row (see schema.sql)

load_dotenv(TELEGRAM_DIR / ".env")

LOG_PATH = TELEGRAM_DIR / "database" / "run" / "logs" / "backup.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
# 2026-08-18: RotatingFileHandler instead of a plain FileHandler -- see
# LOGGING-ARCHITECTURE.md §6/§10. Low-risk here specifically: this is a
# run-to-completion batch job (Task Scheduler, nightly), not a persistent
# process, so there's no cross-restart file-lock concern at all -- unlike
# the long-running bots, this one didn't NEED telegram/database/log_rotation.py's
# shared handler, but uses the same numbers for consistency.
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=20 * 1024 * 1024, backupCount=2, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("backup_to_cloudflare")

# --- config, all from telegram/.env ---
ACCOUNT_ID = os.environ.get("CF_BACKUP_ACCOUNT_ID", "")
API_TOKEN = os.environ.get("CF_BACKUP_API_TOKEN", "")
R2_ACCESS_KEY = os.environ.get("CF_BACKUP_R2_ACCESS_KEY_ID", "")
R2_SECRET_KEY = os.environ.get("CF_BACKUP_R2_SECRET_ACCESS_KEY", "")
R2_ENDPOINT = os.environ.get("CF_BACKUP_R2_ENDPOINT") or f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
BUCKET_NAME = os.environ.get("CF_BACKUP_R2_BUCKET", "1lavya-platform-backups")
D1_DB_NAME = os.environ.get("CF_BACKUP_D1_DB_NAME", "1lavya_platform_mirror")
ENCRYPTION_PASSPHRASE = os.environ.get("CF_BACKUP_ENCRYPTION_PASSPHRASE", "")

CF_API_BASE = "https://api.cloudflare.com/client/v4"
DB_SNAPSHOT_RETENTION_DAYS = 60
SECRETS_RETENTION_COUNT = 10
# Keeps every real object under a few hundred MB as a single-part PUT, so its
# R2 ETag stays a plain MD5 (multipart ETags are NOT a plain MD5, which would
# silently break the MD5-vs-ETag change-detection sync_assets() relies on).
LARGE_FILE_TRANSFER_CONFIG = TransferConfig(multipart_threshold=4 * 1024**3)

ASSET_SYNC_DIRS = [
    TELEGRAM_DIR / "assets" / "study_bot",
    TELEGRAM_DIR / "assets" / "faculty",
    TELEGRAM_DIR / "assets" / "exam_bot",
    TELEGRAM_DIR / "assets" / "myfiles_bot" / "uploads",
]
SKIP_FILENAMES = {"desktop.ini", "Thumbs.db"}


# ---------------------------------------------------------------------------
# Cloudflare REST API (D1 admin) -- separate from the R2 object operations
# below, which go through the S3-compatible client instead (R2 file-level
# reads/writes use SigV4 signing, not this Bearer-token REST API).
# ---------------------------------------------------------------------------

def cf_api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{CF_API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare API {method} {path} failed: HTTP {e.code} -- {body_text}")


def ensure_d1_database() -> str:
    resp = cf_api("GET", f"/accounts/{ACCOUNT_ID}/d1/database?name={D1_DB_NAME}")
    existing = next((d for d in resp.get("result", []) if d["name"] == D1_DB_NAME), None)
    if existing:
        return existing["uuid"]
    logger.info(f"Creating D1 database '{D1_DB_NAME}'...")
    resp = cf_api("POST", f"/accounts/{ACCOUNT_ID}/d1/database", {"name": D1_DB_NAME})
    return resp["result"]["uuid"]


def d1_query(database_id: str, sql: str, params: list | None = None) -> dict:
    body = {"sql": sql}
    if params is not None:
        body["params"] = params
    resp = cf_api("POST", f"/accounts/{ACCOUNT_ID}/d1/database/{database_id}/query", body)
    if not resp.get("success"):
        raise RuntimeError(f"D1 query failed: {resp.get('errors')} -- sql={sql[:200]}")
    return resp["result"][0]


# ---------------------------------------------------------------------------
# R2 (S3-compatible) client
# ---------------------------------------------------------------------------

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket(s3):
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        logger.info(f"R2 bucket '{BUCKET_NAME}' already exists.")
    except ClientError:
        logger.info(f"Creating R2 bucket '{BUCKET_NAME}'...")
        s3.create_bucket(Bucket=BUCKET_NAME)


def prune_by_age(s3, prefix: str, retention_days: int):
    cutoff = time.time() - retention_days * 86400
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"].timestamp() < cutoff:
                s3.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])
                logger.info(f"Pruned (age > {retention_days}d): {obj['Key']}")


def prune_by_count(s3, prefix: str, keep: int):
    paginator = s3.get_paginator("list_objects_v2")
    objs = []
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        objs.extend(page.get("Contents", []))
    objs.sort(key=lambda o: o["LastModified"], reverse=True)
    for obj in objs[keep:]:
        s3.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])
        logger.info(f"Pruned (beyond newest {keep}): {obj['Key']}")


# ---------------------------------------------------------------------------
# Phase 1: SQLite-consistent DB snapshots -> R2
# ---------------------------------------------------------------------------

def snapshot_sqlite_bytes(src_path: Path) -> bytes:
    """Uses sqlite3's own backup API, not a raw file copy -- safe even while
    WAL-mode writers are actively hitting the source (platform.db has
    multiple bot processes writing to it concurrently at any given time)."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(tmp_fd)
    try:
        src = sqlite3.connect(f"file:{src_path.as_posix()}?mode=ro", uri=True)
        dst = sqlite3.connect(tmp_path)
        src.backup(dst)
        dst.close()
        src.close()
        return Path(tmp_path).read_bytes()
    finally:
        os.unlink(tmp_path)


def backup_databases(s3) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    targets = {
        "platform_db": TELEGRAM_DIR / "database" / "platform.db",
        "myfiles_hub_db": TELEGRAM_DIR / "assets" / "myfiles_bot" / "myfiles_hub.db",
    }
    snapshot_kb = {}
    for label, path in targets.items():
        if not path.exists():
            logger.warning(f"[{label}] source not found at {path}, skipping.")
            continue
        raw = snapshot_sqlite_bytes(path)
        compressed = gzip.compress(raw)
        prefix = f"db-snapshots/{label}/"
        key = f"{prefix}{label}_{ts}.db.gz"
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=compressed)
        snapshot_kb[label] = len(compressed) / 1024
        logger.info(f"[{label}] snapshot uploaded: {key} ({len(compressed) / 1024:.1f} KB, "
                    f"raw {len(raw) / 1024:.1f} KB)")
        prune_by_age(s3, prefix, DB_SNAPSHOT_RETENTION_DAYS)
    return snapshot_kb


# ---------------------------------------------------------------------------
# Phase 2: encrypted secrets backup (.env, creds.txt) -> R2
# ---------------------------------------------------------------------------

def _derive_fernet_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390_000)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def encrypt_bytes(data: bytes, passphrase: str) -> bytes:
    salt = os.urandom(16)
    token = Fernet(_derive_fernet_key(passphrase, salt)).encrypt(data)
    return salt + token  # salt prepended so decryption can re-derive the same key


def decrypt_bytes(blob: bytes, passphrase: str) -> bytes:
    salt, token = blob[:16], blob[16:]
    return Fernet(_derive_fernet_key(passphrase, salt)).decrypt(token)


def backup_secrets(s3) -> int:
    if not ENCRYPTION_PASSPHRASE:
        logger.warning("CF_BACKUP_ENCRYPTION_PASSPHRASE not set in telegram/.env -- "
                        "SKIPPING .env/creds.txt backup (never sent unencrypted).")
        return 0
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backed_up = 0
    for label, path in {"env": TELEGRAM_DIR / ".env", "creds": TELEGRAM_DIR / "creds.txt"}.items():
        if not path.exists():
            logger.warning(f"[{label}] source not found at {path}, skipping.")
            continue
        blob = encrypt_bytes(path.read_bytes(), ENCRYPTION_PASSPHRASE)
        prefix = f"secrets/{label}/"
        key = f"{prefix}{label}_{ts}.enc"
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=blob)
        backed_up += 1
        logger.info(f"[{label}] encrypted + uploaded: {key}")
        prune_by_count(s3, prefix, SECRETS_RETENTION_COUNT)
    return backed_up


def decrypt_secret_file(path: Path):
    if not ENCRYPTION_PASSPHRASE:
        print("CF_BACKUP_ENCRYPTION_PASSPHRASE not set in telegram/.env -- cannot decrypt.", file=sys.stderr)
        sys.exit(1)
    plaintext = decrypt_bytes(path.read_bytes(), ENCRYPTION_PASSPHRASE)
    sys.stdout.buffer.write(plaintext)


# ---------------------------------------------------------------------------
# Phase 3: D1 mirror of platform.db (full refresh every run)
# ---------------------------------------------------------------------------

def _topological_table_order(conn: sqlite3.Connection) -> list:
    """Derived at runtime from the LIVE schema's own PRAGMA foreign_key_list
    -- never a hand-maintained table-order list, so this stays correct as
    schema.sql evolves without needing a matching edit here."""
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]
    deps = {}
    for t in tables:
        fks = conn.execute(f'PRAGMA foreign_key_list("{t}")').fetchall()
        deps[t] = {row[2] for row in fks if row[2] in tables and row[2] != t}
    ordered, remaining = [], set(tables)
    while remaining:
        ready = sorted(t for t in remaining if deps[t] <= set(ordered))
        if not ready:  # a real dependency cycle -- take what's left rather than loop forever
            ready = sorted(remaining)
        ordered.extend(ready)
        remaining -= set(ready)
    return ordered


_CREATE_STMT_RE = re.compile(
    r"^CREATE\s+(TABLE|(?:UNIQUE\s+)?INDEX)\s+(?!IF\s+NOT\s+EXISTS)", re.IGNORECASE
)


def _ensure_if_not_exists(sql: str) -> str:
    """sqlite_master.sql stores the CANONICAL create statement text -- it
    silently DROPS the original "IF NOT EXISTS" clause even when the source
    DDL had one (confirmed directly: schema.sql's `CREATE TABLE IF NOT
    EXISTS students (...)` is stored in sqlite_master as plain `CREATE TABLE
    students (...)`). Replaying that verbatim worked on a fresh D1 database
    (first-ever run) but broke on every run after, once the tables already
    existed -- a real bug caught by actually re-running this against a
    populated D1 database, not by reading the code. Re-inserted here so
    every replay is genuinely idempotent, matching what the comment always
    claimed schema.sql itself guaranteed."""
    return _CREATE_STMT_RE.sub(lambda m: f"CREATE {m.group(1)} IF NOT EXISTS ", sql, count=1)


def mirror_to_d1(database_id: str):
    conn = sqlite3.connect(f"file:{(TELEGRAM_DIR / 'database' / 'platform.db').as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # Pull every CREATE TABLE/INDEX statement from the live source's own
    # sqlite_master, keyed so tables and their indexes can be handled
    # separately below.
    table_ddls = {}
    index_ddls = []
    for kind, name, sql in conn.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE type IN ('table','index') "
        "AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
    ).fetchall():
        if kind == "table":
            table_ddls[name] = sql
        else:
            index_ddls.append(sql)

    order = [t for t in _topological_table_order(conn) if t in table_ddls]

    # DROP + recreate every table's SCHEMA every run (data was already being
    # fully wiped and reinserted every run regardless -- see the insert loop
    # below), rather than "CREATE TABLE IF NOT EXISTS" + DELETE FROM as this
    # originally worked. Real bug found live, 2026-08-19: IF-NOT-EXISTS is a
    # no-op against a table that already exists in D1, so a column added
    # locally via ALTER TABLE (course_catalog's `session` column, added by
    # unrelated feature work after D1 already had an older copy of that
    # table) never reached D1 -- silently, for FOUR consecutive nightly runs,
    # each one failing on "table course_catalog has no column named session"
    # the moment the insert loop tried to write it. Dropping and recreating
    # the table from the CURRENT authoritative DDL text every run makes this
    # class of drift structurally impossible, not just patched around.
    # Indexes are dropped along with their table (SQLite behavior) so they're
    # recreated fresh afterward too.
    for table in reversed(order):
        d1_query(database_id, f'DROP TABLE IF EXISTS "{table}"')
    for table in order:
        d1_query(database_id, _ensure_if_not_exists(table_ddls[table]))
    for idx_sql in index_ddls:
        d1_query(database_id, _ensure_if_not_exists(idx_sql))

    total_rows = 0
    for table in order:
        cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
        rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
        if not rows or not cols:
            continue
        col_list = ", ".join(f'"{c}"' for c in cols)
        # D1's bound-parameter ceiling is modest -- stay well under it
        # regardless of how wide any given table is.
        chunk_size = max(1, 90 // len(cols))
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i + chunk_size]
            placeholders = ",".join("(" + ",".join(["?"] * len(cols)) + ")" for _ in chunk)
            params = [row[c] for row in chunk for c in cols]
            d1_query(database_id, f'INSERT INTO "{table}" ({col_list}) VALUES {placeholders}', params)
        total_rows += len(rows)
    conn.close()
    logger.info(f"D1 mirror refreshed: {len(order)} tables, {total_rows} rows.")
    return len(order), total_rows


# ---------------------------------------------------------------------------
# Phase 4: asset sync (study/faculty/exam-bot PDFs+JSON, myfiles uploads)
# ---------------------------------------------------------------------------

def _local_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sync_assets(s3):
    """Object keys are `rel` AS-IS (e.g. "assets/study_bot/...") -- NOT
    "assets/" + rel. `rel` already starts with "assets/" on its own, since
    TELEGRAM_DIR (the relative-to base) is assets/'s own parent directory.
    A real bug, live in production since the very first run (2026-08-16):
    every uploaded key was actually "assets/assets/study_bot/...", a doubled
    prefix -- found 2026-08-22 by listing real bucket contents directly, not
    by reading the code. Content was never at risk (every file's bytes were
    always correct, just filed under a redundant path); see the one-time
    cleanup this fix's rollout ran to move the existing ~2,500 objects onto
    the correct prefix, documented in telegram/database/README.md."""
    uploaded = skipped = failed = 0
    for base_dir in ASSET_SYNC_DIRS:
        if not base_dir.exists():
            logger.warning(f"Asset dir not found, skipping: {base_dir}")
            continue
        prefix_root = base_dir.relative_to(TELEGRAM_DIR).as_posix()
        remote_etags = {}
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=f"{prefix_root}/"):
            for obj in page.get("Contents", []):
                remote_etags[obj["Key"]] = obj["ETag"].strip('"')

        for path in base_dir.rglob("*"):
            if path.is_dir() or path.name in SKIP_FILENAMES or path.name.startswith("."):
                continue
            key = path.relative_to(TELEGRAM_DIR).as_posix()
            try:
                digest = _local_md5(path)
            except OSError as e:
                logger.error(f"Could not read {path}: {e}")
                failed += 1
                continue
            if remote_etags.get(key) == digest:
                skipped += 1
                continue
            try:
                s3.upload_file(str(path), BUCKET_NAME, key, Config=LARGE_FILE_TRANSFER_CONFIG)
                uploaded += 1
            except Exception as e:
                logger.error(f"Upload failed for {key}: {e}")
                failed += 1
    logger.info(f"Asset sync complete: {uploaded} uploaded, {skipped} unchanged, {failed} failed.")
    return uploaded, skipped, failed


# ---------------------------------------------------------------------------
# Failure alerting -- reuses watcher_bot.py's sender/config plumbing rather
# than reimplementing Telegram DM sending + alerts.json loading a second time.
# ---------------------------------------------------------------------------

def alert_failure(text: str):
    try:
        sys.path.insert(0, str(TELEGRAM_DIR / "bots"))
        import watcher_bot  # noqa: E402  (reuses resolve_sender_token/send_telegram_dm/load_alerts_config)
        token = watcher_bot.resolve_sender_token()
        cfg = watcher_bot.load_alerts_config()
        chat_ids = cfg.get("admin_chat_ids", [])
        if not token or not chat_ids:
            logger.warning("Could not send failure alert (no sender token / admin_chat_ids configured).")
            return
        full_text = f"\U0001F534 BACKUP FAILED\n{text}\nLog: telegram/database/run/logs/backup.log"
        # send_telegram_dm() only logs on its OWN failure path (silent on
        # success) -- log the outcome here explicitly either way, so a
        # future "did the alert actually go out" question is answerable
        # from this log alone, not left ambiguous (a real gap found
        # 2026-08-22: 4 real failed nights left zero trace either way).
        results = [watcher_bot.send_telegram_dm(token, cid, full_text) for cid in chat_ids]
        if all(results):
            logger.info(f"Failure alert sent to {len(chat_ids)} admin chat_id(s).")
        else:
            sent = sum(results)
            logger.warning(f"Failure alert sent to only {sent}/{len(chat_ids)} admin chat_id(s) "
                            "-- see the sendMessage error(s) above.")
    except Exception:
        logger.exception("Failed to send the failure alert itself.")


# ---------------------------------------------------------------------------
# backup_runs audit trail (schema.sql) -- lets the Admin Portal's Bot Status
# page show a real "Backup Snapshot Summary" from one fast local query,
# rather than parsing this script's own log file or making a live R2/D1
# call on every page load. See telegram/admin_portal/backup_status.py.
# ---------------------------------------------------------------------------

def _start_backup_run(conn) -> int:
    now = platform_db.now()
    cur = conn.execute(
        "INSERT INTO backup_runs (started_at, status) VALUES (?, 'running')", (now,)
    )
    conn.commit()
    return cur.lastrowid


def _finish_backup_run(conn, run_id: int, *, status: str, duration_seconds: float,
                        snapshot_kb: dict, secrets_backed_up: int,
                        d1_tables: int | None, d1_rows: int | None,
                        assets_uploaded: int | None, assets_unchanged: int | None,
                        assets_failed: int | None, failed_phases: list, error_detail: str | None):
    platform_db.execute_with_retry(
        conn,
        "UPDATE backup_runs SET finished_at=?, status=?, duration_seconds=?, "
        "platform_db_snapshot_kb=?, myfiles_db_snapshot_kb=?, secrets_backed_up=?, "
        "d1_tables_mirrored=?, d1_rows_mirrored=?, assets_uploaded=?, assets_unchanged=?, "
        "assets_failed=?, failed_phases=?, error_detail=? WHERE run_id=?",
        (platform_db.now(), status, duration_seconds,
         snapshot_kb.get("platform_db"), snapshot_kb.get("myfiles_hub_db"), secrets_backed_up,
         d1_tables, d1_rows, assets_uploaded, assets_unchanged, assets_failed,
         ",".join(failed_phases) if failed_phases else None, error_detail, run_id),
    )


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="1LAVYA platform off-machine backup to Cloudflare R2 + D1.")
    parser.add_argument("--skip-assets", action="store_true", help="Skip the (slower) asset sync phase.")
    parser.add_argument("--skip-d1", action="store_true", help="Skip the D1 mirror refresh.")
    parser.add_argument("--decrypt-secret", metavar="FILE",
                         help="Decrypt a downloaded secrets/*.enc file to stdout, then exit.")
    args = parser.parse_args()

    if args.decrypt_secret:
        decrypt_secret_file(Path(args.decrypt_secret))
        return

    missing = [v for v in ("CF_BACKUP_ACCOUNT_ID", "CF_BACKUP_API_TOKEN",
                            "CF_BACKUP_R2_ACCESS_KEY_ID", "CF_BACKUP_R2_SECRET_ACCESS_KEY")
               if not os.environ.get(v)]
    if missing:
        logger.error(f"Missing required telegram/.env vars: {missing}. Aborting.")
        sys.exit(1)

    db_conn = platform_db.get_connection()
    platform_db.init_schema(db_conn)
    run_id = _start_backup_run(db_conn)

    started = time.time()
    s3 = get_s3_client()
    failures = []
    snapshot_kb, secrets_count = {}, 0
    d1_tables = d1_rows = assets_uploaded = assets_unchanged = assets_failed = None
    error_detail = None

    try:
        ensure_bucket(s3)
    except Exception as e:
        logger.exception("Bucket setup failed -- aborting, nothing else can proceed without it.")
        elapsed = time.time() - started
        _finish_backup_run(db_conn, run_id, status="failed", duration_seconds=elapsed,
                            snapshot_kb=snapshot_kb, secrets_backed_up=secrets_count,
                            d1_tables=None, d1_rows=None, assets_uploaded=None, assets_unchanged=None,
                            assets_failed=None, failed_phases=["bucket setup"], error_detail=str(e))
        alert_failure("Bucket setup failed -- entire run aborted.")
        sys.exit(1)

    try:
        snapshot_kb = backup_databases(s3)
    except Exception as e:
        logger.exception("[database snapshots] FAILED")
        failures.append("database snapshots")
        error_detail = str(e)

    try:
        secrets_count = backup_secrets(s3)
    except Exception as e:
        logger.exception("[secrets backup] FAILED")
        failures.append("secrets backup")
        error_detail = str(e)

    if not args.skip_d1:
        try:
            db_id = ensure_d1_database()
            d1_tables, d1_rows = mirror_to_d1(db_id)
        except Exception as e:
            logger.exception("[D1 mirror] FAILED")
            failures.append("D1 mirror")
            error_detail = str(e)

    if not args.skip_assets:
        try:
            assets_uploaded, assets_unchanged, assets_failed = sync_assets(s3)
            if assets_failed:
                failures.append("asset sync")
        except Exception as e:
            logger.exception("[asset sync] FAILED")
            failures.append("asset sync")
            error_detail = str(e)

    elapsed = time.time() - started
    status = "failed" if failures else "success"
    _finish_backup_run(db_conn, run_id, status=status, duration_seconds=elapsed,
                        snapshot_kb=snapshot_kb, secrets_backed_up=secrets_count,
                        d1_tables=d1_tables, d1_rows=d1_rows, assets_uploaded=assets_uploaded,
                        assets_unchanged=assets_unchanged, assets_failed=assets_failed,
                        failed_phases=failures, error_detail=error_detail)
    db_conn.close()

    if failures:
        msg = f"Backup run completed with FAILURES in: {', '.join(failures)} ({elapsed:.0f}s)"
        logger.error(msg)
        alert_failure(msg)
        sys.exit(1)
    logger.info(f"Backup run completed successfully in {elapsed:.0f}s.")


if __name__ == "__main__":
    main()
