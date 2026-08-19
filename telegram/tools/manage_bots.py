#!/usr/bin/env python3
"""
telegram/tools/manage_bots.py -- start/stop/restart/status for every bot
in telegram/config/bots.json, at once or one at a time (added 2026-08-10).
--------------------------------------------------------------------------
Reads the master mapping (bots.json), and for every `status: "active"` bot
(or just one, if you pass its bot_id), launches/stops/restarts its own OS
process: `python telegram/bots/{script}` with BOT_ID set in that process's
environment -- exactly the same thing you'd do by hand in N terminals, just
scripted, with PID tracking so "stop" and "status" actually know what's
running.

USAGE (from the repo root):
    python telegram/tools/manage_bots.py start            # every active bot
    python telegram/tools/manage_bots.py start csarunchouhan
    python telegram/tools/manage_bots.py stop              # every active bot
    python telegram/tools/manage_bots.py stop 1lavya-examhub
    python telegram/tools/manage_bots.py restart
    python telegram/tools/manage_bots.py status            # PID + heartbeat freshness for every bot
    python telegram/tools/manage_bots.py ensure-running    # self-healing check, see below

A thin manage_bots.bat wrapper in the same folder does `python
manage_bots.py %*` for anyone who wants a literal double-clickable /
`manage_bots.bat status`-from-cmd entry point.

ENSURE-RUNNING (added 2026-08-15, for unattended/scheduled use -- Windows
Startup folder + Task Scheduler, see telegram/tools/ensure_bots_running.bat
and telegram/tools/WINDOWS-AUTOSTART.md): a self-healing check, safe to run
repeatedly/concurrently. For every `active` bot in bots.json: if its
process isn't running at all, start it (same as `start`'s own already-
idempotent "skip if already running" check). If the process IS running
but its heartbeat has gone STALE past HEARTBEAT_STALE_AFTER_SECONDS (the
exact same "online" definition status()/the dashboard/the watcher already
use) -- a hung process still holding its PID but no longer doing real
work -- it gets a full `restart` (graceful-stop-then-start), not just left
alone. A healthy bot is untouched. This is deliberately a superset of
`start`, not a separate concept -- unattended contexts (a machine reboot,
a scheduled health check) need both "wasn't running" and "is running but
stuck" covered by the one command, so there's only one thing to schedule.

WHAT "GRACEFUL STOP" ACTUALLY MEANS HERE (read this before trusting it
blindly): each bot is started with CREATE_NEW_PROCESS_GROUP so `stop` can
target it individually with a CTRL_BREAK_EVENT, which (via Python's default
Windows signal plumbing) unwinds into python-telegram-bot's own
`finally:`-block shutdown path (closes the Telegram connection cleanly,
etc.) *if* the bot process handles it in time. This repo's actual SQLite
write pattern (see telegram/database/db.py -- every write commits
immediately, nothing is ever batched or held open across requests) means
there is no meaningfully-sized "in-flight, uncommitted" window to protect
in the first place -- so the bounded grace period + force-terminate
fallback below is a deliberate, honest tradeoff, not a compromise: waiting
forever for an uncooperative process would be worse than a bounded wait
followed by a clean kill, given how little there actually is to lose.

Requires: pip install psutil
"""

import os
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path

import psutil

REPO_ROOT = Path(__file__).resolve().parents[2]   # telegram/tools/manage_bots.py -> repo root
BOTS_PATH = REPO_ROOT / "telegram" / "config" / "bots.json"
BOTS_DIR = REPO_ROOT / "telegram" / "bots"
RUN_DIR = REPO_ROOT / "telegram" / "database" / "run"
LOG_DIR = RUN_DIR / "logs"

DEFAULT_SCRIPT_DIR = "bots"   # every real Telegram bot script lives here


def resolve_script_path(bot: dict) -> Path:
    """Added 2026-08-10 for the "1lavya-dashboard" entry (dashboard_server.py
    lives in telegram/tools/, not telegram/bots/ -- it's not a Telegram bot).
    An optional bots.json `script_dir` field overrides the telegram/bots/
    default. Resolving through ONE function (not "BOTS_DIR / script" typed
    out at each call site) matters here specifically: is_running()'s cmdline
    match and start_bot()'s actual subprocess.Popen() argv must produce the
    IDENTICAL string, or "already running" detection silently breaks (a
    literal "../tools/..." string once tried here, and failed exactly this
    way -- str(Path(...)) normalizes separators, a hand-written ".." string
    doesn't match it)."""
    script_dir = bot.get("script_dir", DEFAULT_SCRIPT_DIR)
    return REPO_ROOT / "telegram" / script_dir / bot["script"]

GRACE_PERIOD_SECONDS = 12   # how long "stop" waits for a graceful exit before force-terminating
HEARTBEAT_STALE_AFTER_SECONDS = 360   # 3x the 120s heartbeat interval in db.py's schedule_heartbeat()

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("manage_bots")


TENANTS_PATH = REPO_ROOT / "telegram" / "config" / "tenants.json"


def load_bots():
    import json
    data = json.loads(BOTS_PATH.read_text(encoding="utf-8"))
    return data["bots"]


def _content_paths_for_bot(bot: dict) -> list:
    """Every JSON file this bot's tenant loads at startup (mcq_json +
    descriptive_json from tenants.json, string-or-list both handled) --
    used by ensure_running()'s freshness check below. Non-exam-hub bots
    (dashboard/watcher/admin-portal/myfiles) have no tenant_id or no
    exam_content and simply return []."""
    import json
    tenant_id = bot.get("tenant_id")
    if not tenant_id:
        return []
    tenants = json.loads(TENANTS_PATH.read_text(encoding="utf-8"))["tenants"]
    tenant = next((t for t in tenants if t["tenant_id"] == tenant_id), None)
    if not tenant:
        return []
    ec = tenant.get("exam_content") or {}
    paths = []
    for key in ("mcq_json", "descriptive_json"):
        v = ec.get(key)
        if not v:
            continue
        paths.extend(v if isinstance(v, list) else [v])
    return [REPO_ROOT / p for p in paths]


def _stale_content_reason(proc: psutil.Process, bot: dict):
    """None if this bot's wired content is no newer than when its process
    started; otherwise a short string naming the newest-changed file, for
    the log line. Compares against the OS process's own create_time() --
    not a DB heartbeat field -- so this check has no dependency on the
    bot's own code ever having run correctly."""
    paths = _content_paths_for_bot(bot)
    if not paths:
        return None
    started_at = proc.create_time()
    newest_path, newest_mtime = None, started_at
    for p in paths:
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if m > newest_mtime:
            newest_path, newest_mtime = p, m
    if newest_path is None:
        return None
    return f"{newest_path.name} changed {int(newest_mtime - started_at)}s after process start"


def pidfile_path(bot_id: str) -> Path:
    return RUN_DIR / f"{bot_id}.pid"


def read_pid(bot_id: str):
    p = pidfile_path(bot_id)
    if not p.exists():
        return None
    try:
        return int(p.read_text().strip())
    except (ValueError, OSError):
        return None


def write_pid(bot_id: str, pid: int):
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    pidfile_path(bot_id).write_text(str(pid), encoding="utf-8")


def clear_pid(bot_id: str):
    p = pidfile_path(bot_id)
    if p.exists():
        p.unlink()


def is_running(bot_id: str, script_path: Path) -> psutil.Process | None:
    """Not just "is this PID alive" -- also checks the process's own
    command line actually mentions the bot's resolved script path, so a PID
    the OS has since recycled for an unrelated process is never mistaken
    for this bot still running (a real, if rare, false-positive risk with
    bare PID tracking). Matches on str(script_path), the SAME string
    start_bot() passes to subprocess.Popen() -- see resolve_script_path()'s
    own docstring for why that identity matters."""
    pid = read_pid(bot_id)
    if pid is None:
        return None
    try:
        proc = psutil.Process(pid)
        if not proc.is_running():
            return None
        cmdline = " ".join(proc.cmdline())
        if str(script_path) not in cmdline:
            return None
        return proc
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def start_bot(bot: dict):
    bot_id = bot["bot_id"]
    script_path = resolve_script_path(bot)
    proc = is_running(bot_id, script_path)
    if proc:
        logger.info(f"[{bot_id}] already running (PID {proc.pid}) -- skipping.")
        return

    if not script_path.exists():
        logger.error(f"[{bot_id}] script not found: {script_path} -- skipping.")
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # BUG FIXED 2026-08-18: this used to redirect stdout/stderr straight
    # into f"{bot_id}.log" -- the SAME file every bot's own
    # logging.basicConfig() now writes to directly via a bounded
    # RotatingFileHandler (see telegram/database/log_rotation.py,
    # LOGGING-ARCHITECTURE.md §6/§10). Two independent writers holding the
    # same file open (one unbounded OS-level append, one in-process
    # rotating handler that occasionally renames/truncates it) would
    # fight each other -- so this redirect now goes to a SEPARATE,
    # small "{bot_id}.crash.log" instead. Its only real job is catching
    # something that happens BEFORE the bot's own logging.basicConfig()
    # runs (an import error at the very top of the script) -- routine
    # output no longer lands here at all, so it should stay tiny. The
    # Admin Portal's Bot-wise Logs viewer and every other existing
    # consumer of f"{bot_id}.log" needs ZERO changes -- that filename and
    # location are unchanged, only WHO writes it changed.
    crash_log_file = open(LOG_DIR / f"{bot_id}.crash.log", "a", encoding="utf-8")

    env = os.environ.copy()
    env["BOT_ID"] = bot_id
    # 2026-08-18: tells log_rotation.build_handlers() this process is
    # managed (its stdout/stderr already goes to crash_log_file below) --
    # see that function's own docstring for the duplication bug this
    # prevents. Never set for a manual `python study_hub_bot.py` run from
    # an interactive terminal, which still gets a live StreamHandler.
    env["BOT_MANAGED"] = "1"

    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    popen = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent),
        env=env,
        stdout=crash_log_file,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    write_pid(bot_id, popen.pid)
    logger.info(f"[{bot_id}] started (PID {popen.pid}) -- log: {LOG_DIR / f'{bot_id}.log'}")


def stop_bot(bot: dict):
    bot_id = bot["bot_id"]
    script_path = resolve_script_path(bot)
    proc = is_running(bot_id, script_path)
    if not proc:
        logger.info(f"[{bot_id}] not running.")
        clear_pid(bot_id)
        return

    pid = proc.pid
    logger.info(f"[{bot_id}] stopping (PID {pid}) -- sending CTRL_BREAK_EVENT, waiting up to {GRACE_PERIOD_SECONDS}s...")
    try:
        if os.name == "nt":
            os.kill(pid, signal.CTRL_BREAK_EVENT)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError as e:
        logger.warning(f"[{bot_id}] couldn't signal PID {pid} ({e}) -- will force-terminate instead.")

    deadline = time.time() + GRACE_PERIOD_SECONDS
    while time.time() < deadline:
        if not psutil.pid_exists(pid):
            logger.info(f"[{bot_id}] stopped cleanly.")
            clear_pid(bot_id)
            return
        time.sleep(0.5)

    logger.warning(f"[{bot_id}] did not exit within {GRACE_PERIOD_SECONDS}s -- force-terminating.")
    try:
        psutil.Process(pid).terminate()
        psutil.Process(pid).wait(timeout=5)
    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
        pass
    clear_pid(bot_id)
    logger.info(f"[{bot_id}] force-terminated.")


def restart_bot(bot: dict):
    stop_bot(bot)
    start_bot(bot)


def _get_conn():
    sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
    import db as platform_db

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    return conn


def _heartbeat_age_seconds(conn, bot_id: str):
    """Seconds since bot_id's last recorded heartbeat, or None if it has
    never sent one. Single implementation shared by status() and
    ensure_running() so "how stale is too stale" is answered identically
    in both places (the same reasoning schema.sql/analytics.py already
    apply -- one definition, reused, never re-derived per caller)."""
    row = conn.execute("SELECT last_heartbeat_at FROM bot_heartbeats WHERE bot_id=?", (bot_id,)).fetchone()
    if not row:
        return None
    from datetime import datetime, timezone
    last = datetime.fromisoformat(row[0].replace("Z", "+00:00")) if row[0].endswith("Z") else datetime.fromisoformat(row[0])
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last).total_seconds()


def status():
    conn = _get_conn()
    bots = load_bots()
    print(f"{'BOT_ID':<24} {'KIND':<10} {'STATUS':<12} {'PROCESS':<18} {'HEARTBEAT':<20}")
    print("-" * 90)
    for bot in bots:
        bot_id, kind = bot["bot_id"], bot["kind"]
        cfg_status = bot.get("status", "unknown")
        proc = is_running(bot_id, resolve_script_path(bot))
        process_str = f"PID {proc.pid}" if proc else "not running"

        age = _heartbeat_age_seconds(conn, bot_id)
        if age is None:
            hb_str = "never"
        else:
            hb_str = f"{int(age)}s ago" + ("" if age < HEARTBEAT_STALE_AFTER_SECONDS else " (STALE)")

        print(f"{bot_id:<24} {kind:<10} {cfg_status:<12} {process_str:<18} {hb_str:<20}")


def ensure_running(bots: list):
    """The self-healing check -- see this module's own docstring
    ("ENSURE-RUNNING") for the full reasoning. Prints one line per bot so
    an unattended log (Task Scheduler/Startup-folder output redirected to
    a file) clearly shows what happened -- or that nothing needed to
    change -- on every single run, not just the runs that did something."""
    conn = _get_conn()
    for bot in bots:
        bot_id = bot["bot_id"]
        script_path = resolve_script_path(bot)
        proc = is_running(bot_id, script_path)

        if not proc:
            logger.info(f"[{bot_id}] not running -- starting.")
            start_bot(bot)
            continue

        age = _heartbeat_age_seconds(conn, bot_id)
        if age is None:
            logger.info(f"[{bot_id}] running (PID {proc.pid}), no heartbeat recorded yet -- leaving it (likely just started).")
            continue
        if age >= HEARTBEAT_STALE_AFTER_SECONDS:
            logger.warning(f"[{bot_id}] running (PID {proc.pid}) but heartbeat is STALE ({int(age)}s ago) -- restarting.")
            restart_bot(bot)
            continue

        # Added 2026-08-19: heartbeat alone only proves the process is
        # ALIVE, not that it's serving current content -- mcq_bank/bank
        # load once at startup and never re-read disk (see
        # exam_hub_bot.py's own docstring). A content edit after startup
        # would otherwise sit invisible to students until someone
        # remembers to restart by hand. Reusing this same 30-min
        # ensure-running cadence caps that staleness window instead of
        # requiring a new, separately-scheduled check.
        stale_reason = _stale_content_reason(proc, bot)
        if stale_reason:
            logger.warning(f"[{bot_id}] running (PID {proc.pid}) but content is stale ({stale_reason}) -- restarting.")
            restart_bot(bot)
            continue

        logger.info(f"[{bot_id}] healthy (PID {proc.pid}, heartbeat {int(age)}s ago).")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("start", "stop", "restart", "status", "ensure-running"):
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    target_bot_id = sys.argv[2] if len(sys.argv) > 2 else None

    if action == "status":
        status()
        return

    bots = load_bots()
    if target_bot_id:
        bots = [b for b in bots if b["bot_id"] == target_bot_id]
        if not bots:
            known = [b["bot_id"] for b in load_bots()]
            sys.exit(f"Unknown bot_id '{target_bot_id}'. Known bot_ids: {known}")
    else:
        bots = [b for b in bots if b.get("status") == "active"]
        if not bots:
            print("No `active` bots in bots.json.")
            return

    if action == "ensure-running":
        ensure_running(bots)
        return

    fn = {"start": start_bot, "stop": stop_bot, "restart": restart_bot}[action]
    for bot in bots:
        fn(bot)


if __name__ == "__main__":
    main()
