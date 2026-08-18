#!/usr/bin/env python3
"""
telegram/bots/leaderboard_broadcaster.py -- nightly leaderboard broadcast
(2026-08-11, Phase 3 of the branding-kit -> report-pipeline -> leaderboard
-> admin-portal roadmap)
--------------------------------------------------------------------------------
A background process, not a Telegram-facing bot (it never calls
run_polling()/receives updates) -- same shape as telegram/bots/watcher_bot.py:
wakes on a schedule, does its work, sends its own heartbeat, sleeps again.
Lives under telegram/bots/ (not telegram/tools/) so manage_bots.py's
existing start/stop/status plumbing manages it exactly like every real bot,
zero changes to that script -- see bots.json's
"1lavya-leaderboard-broadcaster" entry.

WHAT IT DOES: for every "active" leaderboard in telegram/config/
leaderboards.json, computes each configured metric's ranking (via
telegram/database/leaderboard_metrics.py -- SEPARATE mini-rankings per
metric, Pranav's choice, 2026-08-11, not one blended score), renders one
message with one section per metric, and posts it to every configured
broadcast channel. Every attempt (success or failure) is logged to
leaderboard_broadcast_log for a complete audit trail.

SCHEDULE: leaderboards.json's defaults.broadcast_time_ist (23:11 by
default -- Pranav's literal "11:11 pm each day"). Computed against a FIXED
UTC+5:30 offset, not a timezone database lookup -- India Standard Time has
no DST, so this is exact with zero dependency on IANA tzdata being
installed (which Windows Python distributions sometimes lack -- a real
gotcha avoided here, not just a simplification).

WON'T DOUBLE-SEND: before running the scheduled broadcast, checks
leaderboard_broadcast_log for a 'sent' row for that leaderboard_id already
today (UTC date -- 23:11 IST always falls on the same UTC calendar day it's
scheduled for, so this is safe) -- a restart shortly after the nightly run
fired does not re-send. --once (below) deliberately bypasses this guard,
since testing wants a broadcast to actually happen on demand.

USAGE:
    python telegram/bots/leaderboard_broadcaster.py            # runs forever
    python telegram/bots/leaderboard_broadcaster.py --once      # broadcast
                                                                  # every active
                                                                  # leaderboard
                                                                  # right now,
                                                                  # bypassing the
                                                                  # already-sent-
                                                                  # today guard
                                                                  # (testing)

CONFIG: telegram/config/leaderboards.json -- see that file's own
leaderboards.README.md. Every leaderboard entry currently ships
'status': 'inactive' with 'chat_id': null placeholders -- nothing actually
broadcasts until Pranav creates the real channels, adds the posting bot as
an admin with post permission in each, fills in the real chat_ids, and
flips status to 'active'.
"""

import os
import sys
import time
import json
import logging
import argparse
import urllib.request
import urllib.error
import html as html_escape_module
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import log_rotation  # noqa: E402 -- telegram/database/log_rotation.py, Layer 1 of the log-rotation policy (2026-08-18)
import leaderboard_metrics  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
BOTS_PATH = REPO_ROOT / "telegram" / "config" / "bots.json"

BROADCASTER_BOT_ID = "1lavya-leaderboard-broadcaster"   # must match bots.json's own entry
IST_OFFSET = timedelta(hours=5, minutes=30)

load_dotenv(REPO_ROOT / "telegram" / ".env")

# 2026-08-18: handlers=[...] explicit now -- see LOGGING-ARCHITECTURE.md §6/§10.
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO,
    handlers=log_rotation.build_handlers(BROADCASTER_BOT_ID),
)
logger = logging.getLogger("leaderboard_broadcaster")


def resolve_token(env_name: str):
    return os.environ.get(env_name) if env_name else None


def send_telegram_message(token: str, chat_id, text: str) -> tuple:
    """Raw HTTP POST to Bot API sendMessage -- same technique as
    watcher_bot.py's send_telegram_dm(), generalized to any chat_id
    (a channel's chat_id works identically to a user's, provided the
    posting bot has been added as an admin with post permission -- a
    Telegram-side prerequisite this script cannot verify or set up).
    Returns (ok: bool, error_detail: str|None)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        detail = f"HTTP {e.code} -- {body}"
        logger.error(f"sendMessage to chat_id={chat_id} failed: {detail}")
        return False, detail
    except Exception as e:
        logger.error(f"sendMessage to chat_id={chat_id} failed: {e}")
        return False, str(e)


MEDALS = {0: "\U0001F947", 1: "\U0001F948", 2: "\U0001F949"}   # 🥇🥈🥉


def render_broadcast_message(leaderboard: dict, rankings: dict) -> str:
    """One message, one section per metric in `leaderboard['metrics']`
    order -- separate mini-rankings, never a blended score (see this
    module's + leaderboard_metrics.py's docstrings for why)."""
    lines = [f"\U0001F3C6 <b>{html_escape_module.escape(leaderboard['display_name'])}</b> \U0001F3C6",
             "Tonight's Top Performers\n"]

    any_section = False
    for metric_key in leaderboard.get("metrics", []):
        meta = leaderboard_metrics.METRICS.get(metric_key)
        rows = rankings.get(metric_key, [])
        if not meta:
            continue
        lines.append(f"<b>{html_escape_module.escape(meta['label'])}</b>")
        if not rows:
            lines.append("<i>Not enough qualifying activity yet.</i>")
        else:
            any_section = True
            for i, (_username, display_name, value) in enumerate(rows):
                prefix = MEDALS.get(i, f"{i + 1}.")
                safe_name = html_escape_module.escape(display_name)
                lines.append(f"{prefix} {safe_name} — {value}{meta['suffix']}")
        lines.append("")

    if not any_section:
        lines.append("<i>No students have met the minimum-activity requirement yet -- keep practicing!</i>\n")

    lines.append("Keep practicing — updated every night. \U0001F4AA")
    return "\n".join(lines)


def _already_broadcast_today(conn, leaderboard_id: str) -> bool:
    today = datetime.now(timezone.utc).date().isoformat()
    row = conn.execute(
        "SELECT 1 FROM leaderboard_broadcast_log WHERE leaderboard_id=? AND status='sent' "
        "AND substr(sent_at,1,10)=? LIMIT 1",
        (leaderboard_id, today),
    ).fetchone()
    return row is not None


def broadcast_one_leaderboard(conn, leaderboard: dict, config: dict, force: bool):
    leaderboard_id = leaderboard["leaderboard_id"]

    if not force and _already_broadcast_today(conn, leaderboard_id):
        logger.info(f"[{leaderboard_id}] already broadcast today -- skipping.")
        return

    token_env = leaderboard.get("broadcast_bot_token_env")
    token = resolve_token(token_env)
    channels = leaderboard.get("broadcast_channels", [])
    now_str = platform_db.now()

    if not token:
        logger.warning(f"[{leaderboard_id}] no resolvable token ({token_env}) -- cannot broadcast.")
        for ch in channels:
            platform_db.execute_with_retry(
                conn,
                "INSERT INTO leaderboard_broadcast_log "
                "(leaderboard_id, channel_chat_id, metrics_included, participant_count, status, error_detail, sent_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (leaderboard_id, str(ch.get("chat_id")), ",".join(leaderboard.get("metrics", [])), None,
                 "failed", f"unresolved token env {token_env}", now_str),
            )
        return

    rankings = leaderboard_metrics.compute_rankings(conn, leaderboard, config)
    participant_count = len({u for rows in rankings.values() for (u, _, _) in rows})
    message = render_broadcast_message(leaderboard, rankings)

    if not channels:
        logger.warning(f"[{leaderboard_id}] has no broadcast_channels configured -- nothing to send to.")
        return

    for ch in channels:
        chat_id = ch.get("chat_id")
        label = ch.get("label", str(chat_id))
        if chat_id is None:
            logger.warning(f"[{leaderboard_id}] channel '{label}' has no chat_id yet -- skipping (placeholder).")
            platform_db.execute_with_retry(
                conn,
                "INSERT INTO leaderboard_broadcast_log "
                "(leaderboard_id, channel_chat_id, metrics_included, participant_count, status, error_detail, sent_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (leaderboard_id, "null", ",".join(leaderboard.get("metrics", [])), participant_count,
                 "failed", f"channel '{label}' has no chat_id configured", now_str),
            )
            continue

        ok, error_detail = send_telegram_message(token, chat_id, message)
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO leaderboard_broadcast_log "
            "(leaderboard_id, channel_chat_id, metrics_included, participant_count, status, error_detail, sent_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (leaderboard_id, str(chat_id), ",".join(leaderboard.get("metrics", [])), participant_count,
             "sent" if ok else "failed", error_detail, now_str),
        )
        logger.info(f"[{leaderboard_id}] -> channel '{label}' ({chat_id}): "
                    f"{'sent' if ok else 'FAILED'} ({participant_count} qualifying students)")


def run_all_broadcasts(force: bool = False):
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    config = leaderboard_metrics.load_leaderboards_config()
    active = leaderboard_metrics.active_leaderboards(config)

    if not active:
        logger.info("No active leaderboards configured -- nothing to broadcast.")
    for lb in active:
        try:
            broadcast_one_leaderboard(conn, lb, config, force)
        except Exception:
            logger.exception(f"[{lb.get('leaderboard_id')}] broadcast failed unexpectedly.")

    platform_db.send_heartbeat(conn, BROADCASTER_BOT_ID, os.getpid(), platform_db.now())


def _past_broadcast_time_today(hhmm: str) -> bool:
    """True from the configured IST time until midnight IST -- a direct
    "is it currently on-or-after the target clock time" check, not an
    inferred one. Deliberately simple: run_all_broadcasts() is itself
    idempotent per leaderboard per UTC day (see _already_broadcast_today
    above), so calling it on every wake tick once this returns True is
    always safe -- it just becomes a no-op for the rest of the day after
    the real send has already gone out."""
    hour, minute = map(int, hhmm.split(":"))
    now_ist = datetime.now(timezone.utc) + IST_OFFSET
    return (now_ist.hour, now_ist.minute) >= (hour, minute)


CHECK_INTERVAL_SECONDS = 300   # 5 minutes -- fine-grained enough to land close to the target time without excess polling


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true",
                         help="Broadcast every active leaderboard right now, bypassing the "
                              "already-sent-today guard (for testing).")
    args = parser.parse_args()

    if args.once:
        run_all_broadcasts(force=True)
        return

    logger.info(f"Leaderboard broadcaster starting -- checking every {CHECK_INTERVAL_SECONDS}s, firing at "
                f"leaderboards.json's defaults.broadcast_time_ist. Ctrl+C to stop.")
    while True:
        try:
            config = leaderboard_metrics.load_leaderboards_config()
            hhmm = config.get("defaults", {}).get("broadcast_time_ist", "23:11")
            if _past_broadcast_time_today(hhmm):
                run_all_broadcasts(force=False)
            else:
                # Not yet time -- just send a heartbeat so liveness stays visible.
                conn = platform_db.get_connection()
                platform_db.init_schema(conn)
                platform_db.send_heartbeat(conn, BROADCASTER_BOT_ID, os.getpid(), platform_db.now())
        except Exception:
            logger.exception("Broadcaster loop iteration failed -- will retry next wake.")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
