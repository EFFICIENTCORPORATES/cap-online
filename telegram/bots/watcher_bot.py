#!/usr/bin/env python3
"""
telegram/bots/watcher_bot.py -- platform down/up alert watcher (2026-08-10)
--------------------------------------------------------------------------------
Pranav's ask, verbatim: "a fresh DM to be sent to mentioned CHATIDS (may be
more than 1), regarding the Bot being down for any reason." This is that --
a background process, not a Telegram-facing bot (it never calls
run_polling()/receives updates), that periodically checks every OTHER
active bot's heartbeat freshness and DMs a configured list of admin chat
IDs the moment one goes from up to down (and again when it recovers).

Lives under telegram/bots/ (not telegram/tools/) purely so
telegram/tools/manage_bots.py's existing start/stop/status/BOTS_DIR
plumbing manages it exactly like every real bot, with zero changes to that
script -- see telegram/config/bots.json's "1lavya-platform-watcher" entry.

HOW IT DETECTS "DOWN": heartbeat freshness (telegram/database/analytics.py's
fetch_heartbeats(), the SAME function the dashboard uses for its
Online/Offline column) -- not raw OS-level PID existence. This is
deliberate: a hung-but-still-running process is exactly the case a PID
check would miss and a stale heartbeat catches (see schema.sql's own note
on bot_heartbeats). It means "down" here always means the same thing the
dashboard already shows you, never a second, disagreeing definition.

EDGE-TRIGGERED, NOT LEVEL-TRIGGERED: alerts fire only on a state
TRANSITION (up->down or down->up), tracked in the bot_alert_state table
(schema.sql) so a watcher restart doesn't forget where it was and re-fire.
A bot that's been down for 3 hours does not get you 180 identical DMs at a
60s check interval -- exactly one down-alert, then silence until it
recovers (or the watcher restarts and independently re-observes "still
down", which also does not re-alert, since bot_alert_state already says
'down').

KNOWN, HONEST LIMITATION: if a bot is ALREADY down when admin_chat_ids
(telegram/config/alerts.json) is still empty, no alert fires for that
specific ongoing outage -- state tracking still correctly flips to 'down'
internally, there's just nobody configured to tell. The NEXT real
transition (its eventual recovery, or a later flap) alerts normally. This
is a deliberate simplicity tradeoff, not an oversight -- see alerts.json's
own comment.

CANNOT ALERT ON ITS OWN DEATH: if this process itself crashes or is
stopped, nothing here notices -- by definition, nothing is left running to
notice. `manage_bots.py status` (or the dashboard) still shows this
process's own heartbeat going stale like any other bot; there's no
meta-watcher watching the watcher. Flagged honestly rather than silently
assumed away.

SENDS VIA: the 1LAVYA MyFiles Hub bot's token (TELEGRAM_MYFILES_BOT_TOKEN)
-- Pranav's explicit choice, 2026-08-10, over registering a dedicated new
BotFather bot. This only works if every admin_chat_id has actually started
a conversation with @Official1LavyaMyFilesBot at least once (a Telegram
platform requirement for any bot sending a first message to a user, not
something this script can work around) -- the sendMessage failure for a
chat that's never messaged the bot is a clear, logged error, never silent.

USAGE:
    python telegram/bots/watcher_bot.py            # runs forever, checks
                                                     # every check_interval_seconds
    python telegram/bots/watcher_bot.py --once      # one check pass, then exit
                                                     # (used for testing / cron)

CONFIG: telegram/config/alerts.json -- admin_chat_ids (fill this in before
expecting real DMs -- empty by default, see that file's own comment),
check_interval_seconds, heartbeat_stale_after_seconds.
"""

import os
import sys
import json
import time
import logging
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import log_rotation  # noqa: E402 -- telegram/database/log_rotation.py, Layer 1 of the log-rotation policy (2026-08-18)
import analytics  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
BOTS_PATH = REPO_ROOT / "telegram" / "config" / "bots.json"
ALERTS_PATH = REPO_ROOT / "telegram" / "config" / "alerts.json"

WATCHER_BOT_ID = "1lavya-platform-watcher"   # must match bots.json's own entry

# Traffic-anomaly alerting (SECURITY.md Phase 3, 2026-08-24) -- reuses this
# script's own already-proven admin-DM pipe (see module docstring's
# "SENDS VIA" note) rather than building a second alerting mechanism. Two
# independent signals, checked over the same rolling window:
#   - 'high_volume': one telegram_user_id logged an unusual number of
#     ANY actions (user_activity_log -- see LOGGING-ARCHITECTURE.md §4)
#     in the window, regardless of whether rate_limiter.py ever blocked
#     any of them -- catches sustained near-threshold use across multiple
#     bots that no single bot's own general limiter would individually flag.
#   - 'repeated_rate_limit_hits': one telegram_user_id was ACTIVELY
#     blocked by rate_limiter.py (rate_limit_hits -- see that module) many
#     times in the window -- a stronger, more specific signal of
#     deliberate abuse (already being throttled, not just fast).
# Thresholds are deliberately generous (a real flood, not a fast-tapping
# student) -- tune here, in one place, same discipline as
# rate_limiter.BUCKETS.
TRAFFIC_ANOMALY_WINDOW_MINUTES = 5
TRAFFIC_ANOMALY_VOLUME_THRESHOLD = 150            # user_activity_log rows from one telegram_user_id within the window
TRAFFIC_ANOMALY_RATE_LIMIT_HIT_THRESHOLD = 10     # rate_limit_hits rows from one telegram_user_id within the window
TRAFFIC_ANOMALY_ALERT_COOLDOWN_MINUTES = 30       # don't re-DM about the same (user, signal) more often than this

load_dotenv(REPO_ROOT / "telegram" / ".env")

# 2026-08-18: handlers=[...] explicit now -- see LOGGING-ARCHITECTURE.md §6/§10.
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO,
    handlers=log_rotation.build_handlers(WATCHER_BOT_ID),
)
logger = logging.getLogger("watcher_bot")


def load_bots() -> list:
    return json.loads(BOTS_PATH.read_text(encoding="utf-8"))["bots"]


def load_alerts_config() -> dict:
    """Reloaded every check pass (not cached at startup) so editing
    admin_chat_ids takes effect without restarting the watcher -- same
    "no code change, no restart needed" ethos as tenants.json/bots.json."""
    if not ALERTS_PATH.exists():
        return {"admin_chat_ids": [], "check_interval_seconds": 60,
                "heartbeat_stale_after_seconds": analytics.HEARTBEAT_STALE_AFTER_SECONDS}
    return json.loads(ALERTS_PATH.read_text(encoding="utf-8"))


def resolve_sender_token() -> str | None:
    bots = load_bots()
    sender = next((b for b in bots if b["bot_id"] == "1lavya-myfileshub"), None)
    if not sender:
        return None
    return os.environ.get(sender.get("bot_token_env"))


def send_telegram_dm(token: str, chat_id, text: str) -> bool:
    """Raw HTTP POST to Bot API sendMessage -- no need for a full
    telegram.Bot/Application just to send one-off admin DMs. Returns True/
    False, logs the real error either way (a bad chat_id or a chat that's
    never started the sender bot is the expected failure mode -- see module
    docstring)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error(f"sendMessage to chat_id={chat_id} failed: HTTP {e.code} -- {body}")
        return False
    except Exception as e:
        logger.error(f"sendMessage to chat_id={chat_id} failed: {e}")
        return False


def get_alert_state(conn, bot_id: str):
    row = conn.execute(
        "SELECT last_status, since_at, last_alert_sent_at FROM bot_alert_state WHERE bot_id=?", (bot_id,)
    ).fetchone()
    if not row:
        return None
    return {"last_status": row[0], "since_at": row[1], "last_alert_sent_at": row[2]}


def set_alert_state(conn, bot_id: str, status: str, since_at: str, alert_sent: bool):
    now = platform_db.now()
    existing = get_alert_state(conn, bot_id)
    last_alert_sent_at = now if alert_sent else (existing["last_alert_sent_at"] if existing else None)
    if existing:
        platform_db.execute_with_retry(
            conn,
            "UPDATE bot_alert_state SET last_status=?, since_at=?, last_alert_sent_at=? WHERE bot_id=?",
            (status, since_at, last_alert_sent_at, bot_id),
        )
    else:
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO bot_alert_state (bot_id, last_status, since_at, last_alert_sent_at) VALUES (?,?,?,?)",
            (bot_id, status, since_at, last_alert_sent_at),
        )


def _minutes_ago_str(minutes: int) -> str:
    # SAME format platform_db.now() produces (isoformat(timespec="seconds"),
    # timezone-aware UTC) -- both user_activity_log.created_at and
    # rate_limit_hits.created_at are written via platform_db.now(), NOT the
    # SQL-side strftime() DEFAULT (that default is only used when a column
    # is omitted from the INSERT, and both writers always supply it
    # explicitly) -- so a lexical "created_at >= ?" comparison is only
    # correct if the boundary string is in that SAME format. Confirmed
    # against analytics.py's own established "plain string comparison
    # against an ISO boundary" pattern for this exact reason.
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat(timespec="seconds")


def _last_alert_at(conn, telegram_user_id: int, signal: str):
    row = conn.execute(
        "SELECT created_at FROM traffic_anomaly_alerts WHERE telegram_user_id=? AND signal=? "
        "ORDER BY alert_id DESC LIMIT 1",
        (telegram_user_id, signal),
    ).fetchone()
    return row[0] if row else None


def _record_traffic_anomaly_alert(conn, telegram_user_id: int, signal: str, window_minutes: int, observed_count: int):
    platform_db.execute_with_retry(
        conn,
        "INSERT INTO traffic_anomaly_alerts (telegram_user_id, signal, window_minutes, observed_count, created_at) "
        "VALUES (?,?,?,?,?)",
        (telegram_user_id, signal, window_minutes, observed_count, platform_db.now()),
    )


def check_traffic_anomalies(conn, sender_token, admin_chat_ids):
    """SECURITY.md §4.6/§3.A.7 -- see the module-level constants' own
    comment for the two signals checked. Cooldown-gated (not edge-
    triggered like bot up/down above) -- a flood is a sustained condition,
    not a discrete state transition, so "don't re-DM about the same user
    within the cooldown" is the right shape here, checked directly against
    this table's own most recent row rather than a separate state table."""
    window_start = _minutes_ago_str(TRAFFIC_ANOMALY_WINDOW_MINUTES)
    cooldown_boundary = _minutes_ago_str(TRAFFIC_ANOMALY_ALERT_COOLDOWN_MINUTES)

    volume_rows = conn.execute(
        "SELECT telegram_user_id, COUNT(*) AS c FROM user_activity_log "
        "WHERE created_at >= ? AND telegram_user_id IS NOT NULL "
        "GROUP BY telegram_user_id HAVING c >= ?",
        (window_start, TRAFFIC_ANOMALY_VOLUME_THRESHOLD),
    ).fetchall()
    hit_rows = conn.execute(
        "SELECT telegram_user_id, COUNT(*) AS c FROM rate_limit_hits "
        "WHERE created_at >= ? "
        "GROUP BY telegram_user_id HAVING c >= ?",
        (window_start, TRAFFIC_ANOMALY_RATE_LIMIT_HIT_THRESHOLD),
    ).fetchall()

    flagged = [(uid, "high_volume", count) for uid, count in volume_rows]
    flagged += [(uid, "repeated_rate_limit_hits", count) for uid, count in hit_rows]

    for telegram_user_id, signal, count in flagged:
        last_alert = _last_alert_at(conn, telegram_user_id, signal)
        if last_alert is not None and last_alert >= cooldown_boundary:
            continue  # already alerted about this user+signal recently -- don't re-DM every check pass

        label = "unusually HIGH ACTIVITY" if signal == "high_volume" else "REPEATEDLY hitting rate limits"
        text = (
            f"\U0001F6A8 Traffic anomaly: telegram_user_id={telegram_user_id} is {label}\n"
            f"Signal: {signal} -- {count} in the last {TRAFFIC_ANOMALY_WINDOW_MINUTES} minute(s)\n"
            f"Checked: {platform_db.now()}\n\n"
            f"Query this user's own trail: SELECT * FROM user_activity_log WHERE telegram_user_id={telegram_user_id} "
            f"ORDER BY created_at DESC LIMIT 50;"
        )
        alert_sent = False
        if sender_token and admin_chat_ids:
            results = [send_telegram_dm(sender_token, cid, text) for cid in admin_chat_ids]
            alert_sent = any(results)
        else:
            logger.warning(f"[traffic-anomaly] telegram_user_id={telegram_user_id} flagged ({signal}, count={count}) "
                            f"but no admin_chat_ids configured -- alert NOT sent:\n{text}")

        # Recorded regardless of whether the DM actually sent -- this row
        # is also the cooldown gate (see _last_alert_at() above), and an
        # unsent-but-unrecorded flag would just re-attempt (and re-fail)
        # every single check pass instead of respecting the same cooldown
        # a successfully-sent alert gets.
        _record_traffic_anomaly_alert(conn, telegram_user_id, signal, TRAFFIC_ANOMALY_WINDOW_MINUTES, count)
        logger.info(f"[traffic-anomaly] telegram_user_id={telegram_user_id} flagged ({signal}, count={count}, "
                    f"alert_sent={alert_sent})")


def check_once():
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    cfg = load_alerts_config()
    admin_chat_ids = cfg.get("admin_chat_ids", [])
    stale_after = cfg.get("heartbeat_stale_after_seconds", analytics.HEARTBEAT_STALE_AFTER_SECONDS)

    bots = load_bots()
    monitored = [b for b in bots if b.get("status") == "active" and b["bot_id"] != WATCHER_BOT_ID]
    heartbeats = analytics.fetch_heartbeats(conn, stale_after_seconds=stale_after)
    now_str = platform_db.now()

    sender_token = resolve_sender_token()
    if not sender_token:
        logger.warning("Sender bot token unresolved (1lavya-myfileshub's bot_token_env not set in telegram/.env) "
                        "-- alerts will be logged but cannot actually be sent.")

    for bot in monitored:
        bot_id, display_name = bot["bot_id"], bot["display_name"]
        hb = heartbeats.get(bot_id)
        current = "up" if (hb and hb["online"]) else "down"
        existing = get_alert_state(conn, bot_id)

        if existing is None:
            # First time we've ever seen this bot_id -- record a baseline
            # silently, don't alert (see module docstring: avoids a false
            # "down" alert for a bot that simply hasn't heartbeated yet in
            # its first interval after being added to bots.json).
            set_alert_state(conn, bot_id, current, now_str, alert_sent=False)
            logger.info(f"[{bot_id}] first observation: {current} (baseline, no alert)")
            continue

        if current == existing["last_status"]:
            continue   # no transition -- nothing to do

        # Real transition -- build and (attempt to) send the alert.
        if current == "down":
            age = int(hb["age_seconds"]) if hb else None
            age_text = f"{age}s ago" if age is not None else "never received"
            text = (
                f"\U0001F534 DOWN: {display_name} ({bot_id})\n"
                f"Last heartbeat: {age_text} (stale threshold {stale_after}s)\n"
                f"Checked: {now_str}\n\n"
                f"Restart: python telegram/tools/manage_bots.py restart {bot_id}"
            )
        else:
            text = (
                f"\U0001F7E2 BACK UP: {display_name} ({bot_id})\n"
                f"Was down since {existing['since_at']}\n"
                f"Checked: {now_str}"
            )

        alert_sent = False
        if sender_token and admin_chat_ids:
            results = [send_telegram_dm(sender_token, cid, text) for cid in admin_chat_ids]
            alert_sent = any(results)
        else:
            logger.warning(f"[{bot_id}] transitioned to {current} but no admin_chat_ids configured "
                            f"(telegram/config/alerts.json) -- alert NOT sent:\n{text}")

        set_alert_state(conn, bot_id, current, now_str, alert_sent=alert_sent)
        logger.info(f"[{bot_id}] transition {existing['last_status']} -> {current} "
                    f"(alert_sent={alert_sent})")

    # SECURITY.md Phase 3 -- reuses this same check pass/sender/admin list,
    # not a separate process or schedule.
    try:
        check_traffic_anomalies(conn, sender_token, admin_chat_ids)
    except Exception:
        logger.exception("check_traffic_anomalies() failed -- will retry next check pass (bot up/down checks above are unaffected).")

    # The watcher is itself a managed process -- send its own heartbeat so
    # it shows up in `manage_bots.py status` / the dashboard like every
    # other bot (see module docstring: nothing watches the watcher, but at
    # least its own liveness is visible the same way everything else's is).
    platform_db.send_heartbeat(conn, WATCHER_BOT_ID, os.getpid(), now_str)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single check pass and exit (for testing/cron).")
    args = parser.parse_args()

    if args.once:
        check_once()
        return

    cfg = load_alerts_config()
    interval = cfg.get("check_interval_seconds", 60)
    logger.info(f"Watcher starting -- checking every {interval}s. Ctrl+C to stop.")
    while True:
        try:
            check_once()
        except Exception:
            logger.exception("Check pass failed -- will retry next interval.")
        time.sleep(interval)


if __name__ == "__main__":
    main()
