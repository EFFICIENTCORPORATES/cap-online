"""
telegram/bots/smoke_test_leaderboards.py -- smoke test for the leaderboard
system (2026-08-11): telegram/database/leaderboard_metrics.py,
telegram/bots/leaderboard_broadcaster.py, and profile_flow.py's
join/leave/max-5 handling.

Same discipline as smoke_test_report_flow.py / smoke_test_profile_flow.py:
synthetic usernames/chat_ids, real shared platform.db, no mocking of the
DB layer itself, full cleanup in `finally` even on failure. Run directly:
`python smoke_test_leaderboards.py`.

Uses a TEMPORARY leaderboards.json config (via monkeypatching
leaderboard_metrics.LEADERBOARDS_PATH's effect through an explicit `config`
argument, never touching the real file on disk) so this test never
depends on -- or risks corrupting -- Pranav's real leaderboard config.
"""

import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import leaderboard_metrics  # noqa: E402
import leaderboard_broadcaster  # noqa: E402
import profile_flow  # noqa: E402

CHAT_X1 = 900_100_001   # student X, phone 1
CHAT_X2 = 900_100_002   # student X, phone 2 (same username, linked)
CHAT_Y = 900_100_003    # student Y
CHAT_Z = 900_100_004    # student Z -- wrong course/level, should never qualify
USERNAME_X = "smoketest_lb_x"
USERNAME_Y = "smoketest_lb_y"
USERNAME_Z = "smoketest_lb_z"
LEADERBOARD_ID = "smoketest-cma-inter-law"

TEST_CONFIG = {
    "schema_version": 1,
    "defaults": {"min_attempts_floor": 3, "top_n": 10, "broadcast_time_ist": "23:11"},
    "leaderboards": [
        {
            "leaderboard_id": LEADERBOARD_ID,
            "display_name": "Smoketest CMA Inter Law Leaderboard",
            "eligibility": {"course": "CMA", "level": "Intermediate"},
            "metrics": ["accuracy_pct", "questions_attempted"],
            "min_attempts_floor": 3,
            "top_n": 10,
            "broadcast_bot_token_env": "SMOKETEST_NONEXISTENT_TOKEN_ENV",
            "broadcast_channels": [{"chat_id": -1009999, "label": "Smoketest Channel"}],
            "status": "active",
        }
    ],
}

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


def mock_context():
    return SimpleNamespace(user_data={})


def mock_query(user_id, data):
    q = SimpleNamespace()
    q.data = data
    q.from_user = SimpleNamespace(id=user_id)
    q.message = SimpleNamespace(chat_id=user_id, reply_text=AsyncMock())
    q.answer = AsyncMock()
    q.edit_message_text = AsyncMock()
    return q


def seed_student(chat_id, username, course, level):
    # student_profiles row must exist BEFORE any students row references it
    # via lavya_username -- foreign_keys=ON (db.py's get_connection()) rejects
    # the insert order the other way around.
    now = platform_db.now()
    conn.execute("DELETE FROM students WHERE telegram_user_id=?", (chat_id,))
    existing = conn.execute("SELECT 1 FROM student_profiles WHERE username=?", (username,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO student_profiles (username, display_name, course, level, exam_attempt, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (username, f"Display {username}", course, level, "Nov 2026", now, now),
        )
    conn.execute(
        "INSERT INTO students (telegram_user_id, username, first_name, last_name, first_seen_at, last_seen_at, lavya_username) "
        "VALUES (?,?,?,?,?,?,?)",
        (chat_id, f"tg_{chat_id}", "Smoke", "Test", now, now, username),
    )
    conn.commit()


def seed_mcq_attempts(chat_id, course, level, n_answered, n_correct):
    """Writes n_answered rows (n_correct of them marked correct) into
    exam_hub_mcq_attempts for this chat_id/course/level, plus one session
    with a real time span so time_spent_minutes has something to compute."""
    now = platform_db.now()
    conn.execute(
        "INSERT INTO exam_hub_sessions (bot_id, telegram_user_id, started_at, course, level) VALUES (?,?,?,?,?)",
        ("smoketest-bot", chat_id, now, course, level),
    )
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for i in range(n_answered):
        is_correct = 1 if i < n_correct else 0
        conn.execute(
            "INSERT INTO exam_hub_mcq_attempts (bot_id, telegram_user_id, session_id, mcq_id, course, level, "
            "correct_option, selected_option, is_correct, shown_at, answered_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("smoketest-bot", chat_id, session_id, f"mcq-{chat_id}-{i}", course, level,
             "A", "A" if is_correct else "B", is_correct, now, now),
        )
    conn.commit()
    return session_id


def cleanup():
    # FK order matters: leaderboard_participants/student_academic_profiles/
    # access_requests all reference student_profiles (must go first),
    # students also references student_profiles (must go before
    # student_profiles too) -- student_profiles itself goes last.
    # student_academic_profiles included since 2026-08-16: this test seeds
    # course/level directly on the legacy student_profiles columns, and any
    # profile_flow.py call in this test re-runs init_schema() (every
    # profile_flow function does), which idempotently migrates that row
    # into student_academic_profiles too -- leaving it un-cleaned would
    # FK-block the student_profiles delete below.
    conn.execute("DELETE FROM leaderboard_participants WHERE leaderboard_id LIKE 'smoketest%'")
    conn.execute("DELETE FROM leaderboard_broadcast_log WHERE leaderboard_id LIKE 'smoketest%'")
    conn.execute("DELETE FROM exam_hub_mcq_attempts WHERE bot_id='smoketest-bot'")
    conn.execute("DELETE FROM exam_hub_sessions WHERE bot_id='smoketest-bot'")
    conn.execute("DELETE FROM students WHERE telegram_user_id IN (?,?,?,?)", (CHAT_X1, CHAT_X2, CHAT_Y, CHAT_Z))
    conn.execute("DELETE FROM access_requests WHERE username IN (?,?,?)", (USERNAME_X, USERNAME_Y, USERNAME_Z))
    conn.execute("DELETE FROM student_academic_profiles WHERE username IN (?,?,?)", (USERNAME_X, USERNAME_Y, USERNAME_Z))
    conn.execute("DELETE FROM student_profiles WHERE username IN (?,?,?)", (USERNAME_X, USERNAME_Y, USERNAME_Z))
    conn.commit()


async def main():
    print("=== leaderboard system smoke test ===")
    cleanup()
    seed_student(CHAT_X1, USERNAME_X, "CMA", "Intermediate")
    seed_student(CHAT_X2, USERNAME_X, "CMA", "Intermediate")   # same username as X1 -- linked second phone
    seed_student(CHAT_Y, USERNAME_Y, "CMA", "Intermediate")
    seed_student(CHAT_Z, USERNAME_Z, "CA", "Inter")             # wrong course/level -- must never qualify

    # --- 1. config loading + eligibility matching ------------------------
    print("\n[1] Config loading + eligibility matching")
    eligible = leaderboard_metrics.eligible_leaderboards_for("CMA", "Intermediate", TEST_CONFIG)
    check("smoketest leaderboard is eligible for CMA Intermediate", any(lb["leaderboard_id"] == LEADERBOARD_ID for lb in eligible))
    not_eligible = leaderboard_metrics.eligible_leaderboards_for("CA", "Inter", TEST_CONFIG)
    check("smoketest leaderboard is NOT eligible for CA Inter", not any(lb["leaderboard_id"] == LEADERBOARD_ID for lb in not_eligible))
    check("get_leaderboard() finds it by id", leaderboard_metrics.get_leaderboard(LEADERBOARD_ID, TEST_CONFIG) is not None)
    check("get_leaderboard() returns None for unknown id", leaderboard_metrics.get_leaderboard("no-such-id", TEST_CONFIG) is None)

    # --- 2. profile_flow join/leave + max cap -----------------------------
    print("\n[2] profile_flow.py join/leave + max-5 cap")
    ctx_x = mock_context()
    q_join = mock_query(CHAT_X1, f"profile:toggle_lb:{LEADERBOARD_ID}")
    await profile_flow._handle_profile_action(q_join, ctx_x, f"toggle_lb:{LEADERBOARD_ID}")
    joined = conn.execute(
        "SELECT 1 FROM leaderboard_participants WHERE username=? AND leaderboard_id=?", (USERNAME_X, LEADERBOARD_ID)
    ).fetchone()
    check("chat X1 joining links to username X's participation row", joined is not None)

    # joining again (toggle) should LEAVE
    q_leave = mock_query(CHAT_X1, f"profile:toggle_lb:{LEADERBOARD_ID}")
    await profile_flow._handle_profile_action(q_leave, ctx_x, f"toggle_lb:{LEADERBOARD_ID}")
    left = conn.execute(
        "SELECT 1 FROM leaderboard_participants WHERE username=? AND leaderboard_id=?", (USERNAME_X, LEADERBOARD_ID)
    ).fetchone()
    check("toggling again leaves the leaderboard", left is None)

    # re-join for the rest of the test
    q_join2 = mock_query(CHAT_X1, f"profile:toggle_lb:{LEADERBOARD_ID}")
    await profile_flow._handle_profile_action(q_join2, ctx_x, f"toggle_lb:{LEADERBOARD_ID}")

    # max-5 cap: fill username X up to 5 with fake leaderboard_ids, then a 6th must be rejected
    for i in range(4):   # already has 1 (the real one above) -> add 4 more = 5 total
        conn.execute(
            "INSERT INTO leaderboard_participants (username, leaderboard_id, joined_at) VALUES (?,?,?)",
            (USERNAME_X, f"smoketest-filler-{i}", platform_db.now()),
        )
    conn.commit()
    count_before = conn.execute("SELECT COUNT(*) FROM leaderboard_participants WHERE username=?", (USERNAME_X,)).fetchone()[0]
    check("username X now has exactly 5 leaderboards", count_before == 5)

    ctx_x2 = mock_context()
    q_sixth = mock_query(CHAT_X1, "profile:toggle_lb:smoketest-sixth-board")
    await profile_flow._handle_profile_action(q_sixth, ctx_x2, "toggle_lb:smoketest-sixth-board")
    count_after = conn.execute("SELECT COUNT(*) FROM leaderboard_participants WHERE username=?", (USERNAME_X,)).fetchone()[0]
    check("6th join attempt rejected -- still exactly 5", count_after == 5)
    q_sixth.answer.assert_called()
    alert_call = [c for c in q_sixth.answer.call_args_list if c.kwargs.get("show_alert")]
    check("6th join attempt shows an alert to the student", len(alert_call) > 0)

    # clean up filler rows, keep only the real leaderboard for the rest of the test
    conn.execute("DELETE FROM leaderboard_participants WHERE leaderboard_id LIKE 'smoketest-filler%' OR leaderboard_id='smoketest-sixth-board'")
    conn.commit()

    # Y also joins, Z (wrong course/level) does NOT
    conn.execute(
        "INSERT INTO leaderboard_participants (username, leaderboard_id, joined_at) VALUES (?,?,?)",
        (USERNAME_Y, LEADERBOARD_ID, platform_db.now()),
    )
    conn.commit()

    # --- 3. metric computation, aggregated across linked chat_ids ---------
    print("\n[3] Metric computation (username X aggregated across chat X1 + X2)")
    seed_mcq_attempts(CHAT_X1, "CMA", "Intermediate", n_answered=4, n_correct=3)   # 75% on phone 1
    seed_mcq_attempts(CHAT_X2, "CMA", "Intermediate", n_answered=2, n_correct=2)   # 100% on phone 2
    # combined: 6 answered, 5 correct -> 83.3%
    seed_mcq_attempts(CHAT_Y, "CMA", "Intermediate", n_answered=3, n_correct=1)     # 33.3%, exactly at the floor (3)
    seed_mcq_attempts(CHAT_Z, "CA", "Inter", n_answered=10, n_correct=10)           # would dominate if scope leaked

    chat_ids_x = leaderboard_metrics._linked_chat_ids(conn, USERNAME_X)
    check("username X resolves to both linked chat_ids", set(chat_ids_x) == {CHAT_X1, CHAT_X2})

    attempted_x = leaderboard_metrics.compute_questions_attempted(conn, chat_ids_x, "CMA", "Intermediate")
    check("questions_attempted aggregates across both phones (4+2=6)", attempted_x == 6)

    accuracy_x = leaderboard_metrics.compute_accuracy_pct(conn, chat_ids_x, "CMA", "Intermediate")
    check("accuracy_pct aggregates correctly (5/6 = 83.3%)", accuracy_x == 83.3)

    time_x = leaderboard_metrics.compute_time_spent_minutes(conn, chat_ids_x, "CMA", "Intermediate")
    check("time_spent_minutes returns a non-negative number", time_x is not None and time_x >= 0)

    # --- 4. min-attempts floor gate (blanket across all metrics) ----------
    print("\n[4] Minimum-attempts floor (3), blanket across metrics")
    qualifying = leaderboard_metrics.qualifying_participants(conn, LEADERBOARD_ID, {"course": "CMA", "level": "Intermediate"}, 3)
    check("username X qualifies (6 >= 3)", USERNAME_X in qualifying)
    check("username Y qualifies (3 >= 3, exactly at floor)", USERNAME_Y in qualifying)
    check("username Z never appears (wrong course/level, never joined)", USERNAME_Z not in qualifying)

    qualifying_high_floor = leaderboard_metrics.qualifying_participants(conn, LEADERBOARD_ID, {"course": "CMA", "level": "Intermediate"}, 7)
    check("raising the floor above everyone's attempts excludes both", len(qualifying_high_floor) == 0)

    # --- 5. full ranking computation ---------------------------------------
    print("\n[5] compute_rankings() -- separate mini-ranking per metric")
    leaderboard_cfg = leaderboard_metrics.get_leaderboard(LEADERBOARD_ID, TEST_CONFIG)
    rankings = leaderboard_metrics.compute_rankings(conn, leaderboard_cfg, TEST_CONFIG)
    check("rankings has one section per configured metric", set(rankings.keys()) == {"accuracy_pct", "questions_attempted"})
    acc_rows = rankings["accuracy_pct"]
    check("accuracy ranking sorted descending (X's 83.3% above Y's 33.3%)",
          len(acc_rows) == 2 and acc_rows[0][0] == USERNAME_X and acc_rows[1][0] == USERNAME_Y)
    attempted_rows = rankings["questions_attempted"]
    check("questions_attempted ranking sorted descending (X's 6 above Y's 3)",
          len(attempted_rows) == 2 and attempted_rows[0][0] == USERNAME_X and attempted_rows[1][0] == USERNAME_Y)

    # --- 6. broadcaster: message rendering + already-sent-today guard -----
    print("\n[6] leaderboard_broadcaster.py rendering + logging")
    message = leaderboard_broadcaster.render_broadcast_message(leaderboard_cfg, rankings)
    check("rendered message includes the leaderboard display name", leaderboard_cfg["display_name"] in message)
    check("rendered message includes both students' display names", f"Display {USERNAME_X}" in message and f"Display {USERNAME_Y}" in message)
    check("rendered message includes a medal for rank 1", "\U0001F947" in message)

    check("not yet marked as broadcast today", not leaderboard_broadcaster._already_broadcast_today(conn, LEADERBOARD_ID))
    leaderboard_broadcaster.broadcast_one_leaderboard(conn, leaderboard_cfg, TEST_CONFIG, force=True)
    log_row = conn.execute(
        "SELECT status, error_detail FROM leaderboard_broadcast_log WHERE leaderboard_id=? ORDER BY broadcast_id DESC LIMIT 1",
        (LEADERBOARD_ID,),
    ).fetchone()
    check("broadcast attempt logged", log_row is not None)
    check("logged as failed (no real token configured for this test env var)", log_row[0] == "failed")
    check("error_detail mentions the unresolved token", "token" in (log_row[1] or "").lower())

    # --- 7. is_awaiting_text_input unaffected by leaderboard menu ---------
    print("\n[7] Leaderboard menu doesn't interfere with text-awaiting state")
    ctx_menu = mock_context()
    check("no text-awaiting state after a leaderboards: action", profile_flow.is_awaiting_text_input(ctx_menu) is False)

    print(f"\n=== {PASS} passed, {FAIL} failed ===")
    return FAIL == 0


if __name__ == "__main__":
    try:
        ok = asyncio.run(main())
    finally:
        cleanup()
        print("(cleanup done -- all synthetic rows removed)")
    sys.exit(0 if ok else 1)
