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

A thin manage_bots.bat wrapper in the same folder does `python
manage_bots.py %*` for anyone who wants a literal double-clickable /
`manage_bots.bat status`-from-cmd entry point.

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


def load_bots():
    import json
    data = json.loads(BOTS_PATH.read_text(encoding="utf-8"))
    return data["bots"]


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
    log_file = open(LOG_DIR / f"{bot_id}.log", "a", encoding="utf-8")

    env = os.environ.copy()
    env["BOT_ID"] = bot_id

    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    popen = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent),
        env=env,
        stdout=log_file,
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


def status():
    sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
    import db as platform_db

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    bots = load_bots()
    print(f"{'BOT_ID':<24} {'KIND':<10} {'STATUS':<12} {'PROCESS':<18} {'HEARTBEAT':<20}")
    print("-" * 90)
    for bot in bots:
        bot_id, kind = bot["bot_id"], bot["kind"]
        cfg_status = bot.get("status", "unknown")
        proc = is_running(bot_id, resolve_script_path(bot))
        process_str = f"PID {proc.pid}" if proc else "not running"

        row = conn.execute(
            "SELECT last_heartbeat_at FROM bot_heartbeats WHERE bot_id=?", (bot_id,)
        ).fetchone()
        if not row:
            hb_str = "never"
        else:
            from datetime import datetime, timezone
            last = datetime.fromisoformat(row[0].replace("Z", "+00:00")) if row[0].endswith("Z") else datetime.fromisoformat(row[0])
            age = (datetime.now(timezone.utc) - last.replace(tzinfo=timezone.utc) if last.tzinfo is None else datetime.now(timezone.utc) - last).total_seconds()
            hb_str = f"{int(age)}s ago" + ("" if age < HEARTBEAT_STALE_AFTER_SECONDS else " (STALE)")

        print(f"{bot_id:<24} {kind:<10} {cfg_status:<12} {process_str:<18} {hb_str:<20}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("start", "stop", "restart", "status"):
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

    fn = {"start": start_bot, "stop": stop_bot, "restart": restart_bot}[action]
    for bot in bots:
        fn(bot)


if __name__ == "__main__":
    main()
