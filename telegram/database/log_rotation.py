"""
telegram/database/log_rotation.py -- Layer 1 of the two-layer log rotation
policy (LOGGING-ARCHITECTURE.md §6/§10, built 2026-08-18)
--------------------------------------------------------------------------------
ONE place the actual numbers (max bytes per file, how many rotated backups
to keep locally) live -- every process's own logging.basicConfig() call
imports build_rotating_handler(bot_id) instead of hand-rolling its own
RotatingFileHandler, so a policy change is a one-line edit here, not N
edits scattered across every bot/dashboard/watcher script.

WHY THIS EXISTS: before this, every bot's logging.basicConfig() had no
`handlers=` argument, so it silently defaulted to writing to stderr --
telegram/tools/manage_bots.py then captured that at the OS-process level
via `subprocess.Popen(stdout=log_file)`, unbounded, no rotation (see
LOGGING-ARCHITECTURE.md's original §6 point 2, which named this exact gap
and deferred it). This module is that deferred fix, plus the reason it
was safe to defer no longer holds -- a real activity-log review
(2026-08-17/18) found the raw logs already at 59MB/day-and-a-half with no
ceiling in sight.

WRITES TO THE EXACT SAME PATH manage_bots.py's process manager and the
Admin Portal's Bot-wise Logs viewer already read
(telegram/database/run/logs/{bot_id}.log -- see manage_bots.py's own
LOG_DIR) -- zero changes needed in either of those two existing
consumers, this only changes WHO writes that file and HOW (bounded,
rotated, in-process) instead of an unbounded OS-level redirect.

manage_bots.py itself was changed alongside this module to redirect its
subprocess stdout/stderr to a SEPARATE, small `{bot_id}.crash.log`
instead of the main log -- catching genuinely pre-logging-setup crashes
(an import error before logging.basicConfig() ever runs) without the two
mechanisms fighting over the same file. See that script's own comment at
the change site.
"""

import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = REPO_ROOT / "telegram" / "database" / "run" / "logs"

# Layer 1's per-process local cap. Layer 2 (telegram/tools/rotate_logs_to_r2.py)
# enforces the GLOBAL ~1GB-across-everything ceiling by shipping the
# rotated chunks THIS handler produces off to Cloudflare R2 once the
# total (across every process) crosses its own watermark. These two
# numbers are deliberately conservative, not maxed out to "1GB / N
# processes" -- 20MB x (1 active + 2 backups) x ~9 processes tops out
# around 540MB, leaving Layer 2 real headroom to act well before the hard
# ceiling, not exactly at it.
MAX_BYTES = 20 * 1024 * 1024   # 20MB per active/rotated chunk
BACKUP_COUNT = 2               # + the active file = up to 60MB/process locally, worst case


def build_rotating_handler(bot_id: str) -> RotatingFileHandler:
    """The ONE handler every process's `logging.basicConfig(handlers=[...])`
    should use for its main structured log. `bot_id` must match its own
    telegram/config/bots.json entry -- that's what keeps the filename
    identical to what manage_bots.py / the Admin Portal's log viewer
    already expect. Safe to call more than once for the same bot_id
    (e.g. faculty_bot.py importing study_hub_bot.py, whose basicConfig()
    call wins the root-logger race) -- RotatingFileHandler's own file
    open is idempotent-safe, append mode."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return RotatingFileHandler(
        LOG_DIR / f"{bot_id}.log", maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8",
    )


def build_handlers(bot_id: str) -> list:
    """BUG FIXED 2026-08-18, same day it was introduced -- caught by
    actually inspecting the restarted processes' real log files, not by
    reading the code: the first version of this rotation policy had every
    process's logging.basicConfig() ALSO include a bare
    logging.StreamHandler() (for local/interactive-run visibility). That
    StreamHandler writes to stderr -- which manage_bots.py's own
    subprocess.Popen ALSO captures wholesale into f"{bot_id}.crash.log".
    Result: EVERY routine log line was being duplicated into TWO files,
    one bounded (the real .log) and one NOT (crash.log, plain append,
    no rotation) -- the exact "two full copies in two places" class of
    bug already found and fixed once this same day for
    myfiles_hub_bot.py's old separate log file, re-introduced by this
    fix's own first draft.

    Fix: manage_bots.py's start_bot() now sets env var BOT_MANAGED=1 on
    every process it launches. This function only adds the
    StreamHandler when that's NOT set -- i.e. a developer running
    `python study_hub_bot.py` directly from a terminal still sees live
    output, but a process launched by manage_bots.py (the normal,
    production path) does not duplicate its stderr into crash.log at
    all. crash.log still does its real job either way: Python's default
    unhandled-exception printer writes straight to the real OS-level
    stderr independent of the logging module entirely, so a genuine
    crash BEFORE logging.basicConfig() even runs is still caught by
    manage_bots.py's redirect regardless of this flag."""
    handlers = [build_rotating_handler(bot_id)]
    if not os.environ.get("BOT_MANAGED"):
        handlers.append(logging.StreamHandler())
    return handlers
