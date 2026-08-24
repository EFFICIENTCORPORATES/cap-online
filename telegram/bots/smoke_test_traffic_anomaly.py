"""
telegram/bots/smoke_test_traffic_anomaly.py -- smoke test for
watcher_bot.py's check_traffic_anomalies() (2026-08-24, SECURITY.md
Phase 3)
--------------------------------------------------------------------------------
Runs against the REAL shared DB (same pattern smoke_test_report_flow.py/
smoke_test_leaderboards.py already use) with synthetic, clearly-marked
telegram_user_ids -- inserts real rows into user_activity_log/
rate_limit_hits, runs the real check_traffic_anomalies(), and asserts on
what actually landed in traffic_anomaly_alerts. Never sends a real
Telegram DM (no sender_token/admin_chat_ids passed in) -- exercises the
"no admin_chat_ids configured" logged-not-sent branch, same as every other
alert-DM smoke test on this platform. Full cleanup in a finally block.

Run directly: `python smoke_test_traffic_anomaly.py`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import watcher_bot  # noqa: E402

USER_FLOOD = 900_666_001    # will exceed the volume threshold
USER_BLOCKED = 900_666_002  # will exceed the rate-limit-hit threshold
USER_QUIET = 900_666_003    # stays well under both thresholds -- negative control
BOT_ID = "smoketest-bot"

conn = platform_db.get_connection()
platform_db.init_schema(conn)

PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK   {label}")
    else:
        FAIL += 1
        print(f"  FAIL {label}")


def cleanup():
    for uid in (USER_FLOOD, USER_BLOCKED, USER_QUIET):
        conn.execute("DELETE FROM user_activity_log WHERE telegram_user_id=?", (uid,))
        conn.execute("DELETE FROM rate_limit_hits WHERE telegram_user_id=?", (uid,))
        conn.execute("DELETE FROM traffic_anomaly_alerts WHERE telegram_user_id=?", (uid,))
    conn.commit()


def seed_activity_rows(telegram_user_id: int, count: int):
    now = platform_db.now()
    for i in range(count):
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO user_activity_log (correlation_id, bot_id, telegram_user_id, handler_kind, action, "
            "handler_name, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (f"smoketest-{i}", BOT_ID, telegram_user_id, "callback", "test_action", "test_handler", "ok", now),
        )


def seed_rate_limit_hits(telegram_user_id: int, count: int):
    for _ in range(count):
        platform_db.log_rate_limit_hit(conn, BOT_ID, telegram_user_id, "general", "test_handler")


def alerts_for(telegram_user_id: int):
    return conn.execute(
        "SELECT signal, observed_count FROM traffic_anomaly_alerts WHERE telegram_user_id=? ORDER BY alert_id",
        (telegram_user_id,),
    ).fetchall()


def main():
    print("=== smoke_test_traffic_anomaly ===")
    cleanup()

    try:
        # --- [1] High-volume signal -----------------------------------------
        print("\n[1] High-volume signal")
        seed_activity_rows(USER_FLOOD, watcher_bot.TRAFFIC_ANOMALY_VOLUME_THRESHOLD + 5)
        seed_activity_rows(USER_QUIET, 3)  # negative control -- nowhere near the threshold

        watcher_bot.check_traffic_anomalies(conn, sender_token=None, admin_chat_ids=[])

        flood_alerts = alerts_for(USER_FLOOD)
        check("the flooding user gets exactly one 'high_volume' alert row", len(flood_alerts) == 1 and flood_alerts[0][0] == "high_volume")
        check("the recorded observed_count matches what was actually seeded", flood_alerts[0][1] == watcher_bot.TRAFFIC_ANOMALY_VOLUME_THRESHOLD + 5)
        check("the quiet (negative-control) user gets NO alert", len(alerts_for(USER_QUIET)) == 0)

        # --- [2] Cooldown -- a second check pass does NOT re-alert ----------
        print("\n[2] Cooldown suppresses immediate re-alerting")
        watcher_bot.check_traffic_anomalies(conn, sender_token=None, admin_chat_ids=[])
        check("a second check pass within the cooldown window does not add a duplicate alert row", len(alerts_for(USER_FLOOD)) == 1)

        # --- [3] Repeated rate_limit_hits signal ------------------------------
        print("\n[3] Repeated rate_limit_hits signal")
        seed_rate_limit_hits(USER_BLOCKED, watcher_bot.TRAFFIC_ANOMALY_RATE_LIMIT_HIT_THRESHOLD + 2)
        watcher_bot.check_traffic_anomalies(conn, sender_token=None, admin_chat_ids=[])
        blocked_alerts = alerts_for(USER_BLOCKED)
        check("the repeatedly-blocked user gets exactly one 'repeated_rate_limit_hits' alert", len(blocked_alerts) == 1 and blocked_alerts[0][0] == "repeated_rate_limit_hits")

        # --- [4] Below-threshold activity never alerts ------------------------
        print("\n[4] Below-threshold activity never alerts")
        cleanup()
        seed_activity_rows(USER_QUIET, watcher_bot.TRAFFIC_ANOMALY_VOLUME_THRESHOLD - 1)  # exactly one under
        watcher_bot.check_traffic_anomalies(conn, sender_token=None, admin_chat_ids=[])
        check("one row under the threshold never triggers an alert", len(alerts_for(USER_QUIET)) == 0)

        # --- [5] The window boundary format matches platform_db.now() ---------
        print("\n[5] Window boundary format")
        boundary = watcher_bot._minutes_ago_str(5)
        check("the boundary string is directly comparable to a real created_at value (same format)", boundary < platform_db.now())

    finally:
        cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
