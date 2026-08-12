"""
telegram/bots/smoke_test_profile_flow.py -- smoke test for profile_flow.py
(2026-08-11)
--------------------------------------------------------------------------------
Same discipline as smoke_test_report_flow.py: synthetic telegram_user_ids
(way out of real range), no mocking of the actual DB layer or profile_flow
module -- exercises the REAL functions against the REAL shared
platform.db, then cleans up every row it touched in a `finally` block so a
run leaves no trace. Run directly: `python smoke_test_profile_flow.py`.

Covers:
  1. New username creation (validation, uniqueness, echo-confirm, lock)
  2. Duplicate username rejected (case-insensitive)
  3. A second chat_id linking to an EXISTING username (multi-phone scenario)
  4. Course/level/exam-attempt/display-name edits persist and are SHARED
     across both chat_ids linked to the same username
  5. Email/mobile edits are PER-CHAT-ID, not shared
  6. is_awaiting_text_input() / matches_trigger() correctness
  7. Once a username is set, the menu never offers to change it again
"""

import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import profile_flow  # noqa: E402

# Synthetic IDs, far outside any real Telegram user id range.
CHAT_A = 900_000_001   # "phone 1" of a student
CHAT_B = 900_000_002   # "phone 2" of the SAME student -- links to A's username
CHAT_C = 900_000_003   # a second, unrelated student
TEST_USERNAME = "smoketest_user_2026"

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


def mock_message(user_id, text):
    m = SimpleNamespace()
    m.text = text
    m.reply_text = AsyncMock()
    return SimpleNamespace(
        message=m, effective_user=SimpleNamespace(id=user_id), effective_chat=SimpleNamespace(id=user_id),
    )


def seed_student(chat_id):
    """profile_flow assumes a `students` row already exists (every bot
    upserts one on /start before any of this runs) -- mirror that here."""
    now = platform_db.now()
    conn.execute("DELETE FROM students WHERE telegram_user_id=?", (chat_id,))
    conn.execute(
        "INSERT INTO students (telegram_user_id, username, first_name, last_name, first_seen_at, last_seen_at) "
        "VALUES (?,?,?,?,?,?)",
        (chat_id, f"tg_{chat_id}", "Smoke", "Test", now, now),
    )
    conn.commit()


def cleanup():
    conn.execute("DELETE FROM students WHERE telegram_user_id IN (?,?,?)", (CHAT_A, CHAT_B, CHAT_C))
    conn.execute("DELETE FROM student_profiles WHERE username=?", (TEST_USERNAME,))
    conn.commit()


async def main():
    print("=== profile_flow.py smoke test ===")
    cleanup()  # in case a previous crashed run left rows behind
    seed_student(CHAT_A)
    seed_student(CHAT_B)
    seed_student(CHAT_C)

    # --- 1. trigger phrase matching -----------------------------------
    print("\n[1] Trigger phrase matching")
    check("'profile' matches", profile_flow.matches_trigger("profile"))
    check("'Change Profile' matches (case-insensitive)", profile_flow.matches_trigger("Change Profile"))
    check("'my profile please' does NOT match (not exact)", not profile_flow.matches_trigger("my profile please"))
    check("'randomtext' does not match", not profile_flow.matches_trigger("randomtext"))

    # --- 2. new username: validation ------------------------------------
    print("\n[2] New username validation")
    check("'ab' (too short) rejected", profile_flow._valid_username("ab") is None)
    check("'this_is_way_too_long_12345' (too long) rejected", profile_flow._valid_username("this_is_way_too_long_12345") is None)
    check("'bad name!' (invalid chars) rejected", profile_flow._valid_username("bad name!") is None)
    check("'good_name_1' accepted", profile_flow._valid_username("good_name_1") == "good_name_1")

    # --- 3. full new-username creation flow, CHAT_A ---------------------
    print("\n[3] New username creation flow (chat A)")
    ctx_a = mock_context()
    q = mock_query(CHAT_A, "profile:has_username_no")
    await profile_flow._handle_profile_action(q, ctx_a, "has_username_no")
    check("state -> AWAITING_NEW_USERNAME", ctx_a.user_data.get("profile_flow_state") == profile_flow.AWAITING_NEW_USERNAME)

    consumed = await profile_flow.handle_profile_text_input(mock_message(CHAT_A, TEST_USERNAME), ctx_a)
    check("username text input consumed", consumed is True)
    check("state -> CONFIRMING_NEW_USERNAME", ctx_a.user_data.get("profile_flow_state") == profile_flow.CONFIRMING_NEW_USERNAME)
    check("pending username staged", ctx_a.user_data.get("profile_flow_pending_username") == TEST_USERNAME)

    q_confirm = mock_query(CHAT_A, "profileconfirm:yes")
    await profile_flow._handle_profile_confirm(q_confirm, ctx_a, "yes")
    row = conn.execute("SELECT username FROM student_profiles WHERE username=?", (TEST_USERNAME,)).fetchone()
    check("student_profiles row created", row is not None)
    link = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (CHAT_A,)).fetchone()
    check("students.lavya_username linked for chat A", link and link[0] == TEST_USERNAME)
    check("state cleared after confirm", ctx_a.user_data.get("profile_flow_state") is None)

    # --- 4. duplicate username rejected, case-insensitive ---------------
    print("\n[4] Duplicate username rejection (case-insensitive)")
    ctx_c = mock_context()
    ctx_c.user_data["profile_flow_state"] = profile_flow.AWAITING_NEW_USERNAME
    reply = mock_message(CHAT_C, TEST_USERNAME.upper())  # different case, same username
    await profile_flow.handle_profile_text_input(reply, ctx_c)
    reply.message.reply_text.assert_called_once()
    reply_text = reply.message.reply_text.call_args[0][0]
    check("rejected as already taken", "already taken" in reply_text.lower())
    check("state stays AWAITING_NEW_USERNAME (not advanced)", ctx_c.user_data.get("profile_flow_state") == profile_flow.AWAITING_NEW_USERNAME)

    # --- 5. second chat_id links to the SAME existing username -----------
    print("\n[5] Linking a second chat_id (CHAT_B) to the existing username")
    ctx_b = mock_context()
    ctx_b.user_data["profile_flow_state"] = profile_flow.AWAITING_EXISTING_USERNAME
    consumed = await profile_flow.handle_profile_text_input(mock_message(CHAT_B, TEST_USERNAME), ctx_b)
    check("existing-username text input consumed", consumed is True)
    link_b = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (CHAT_B,)).fetchone()
    check("students.lavya_username linked for chat B", link_b and link_b[0] == TEST_USERNAME)
    check("state cleared after link", ctx_b.user_data.get("profile_flow_state") is None)

    # linking to a NON-existent username must fail cleanly
    ctx_c2 = mock_context()
    ctx_c2.user_data["profile_flow_state"] = profile_flow.AWAITING_EXISTING_USERNAME
    consumed2 = await profile_flow.handle_profile_text_input(mock_message(CHAT_C, "no_such_username_xyz"), ctx_c2)
    check("nonexistent-username link consumed (handled, not fell through)", consumed2 is True)
    link_c = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (CHAT_C,)).fetchone()
    check("chat C still has no lavya_username (link correctly rejected)", link_c and link_c[0] is None)

    # --- 6. shared fields (course/level/exam_attempt/display_name) -------
    print("\n[6] Shared fields (course/level/exam_attempt/display_name)")
    ctx_a2 = mock_context()
    q_course = mock_query(CHAT_A, "profile:pick_course:CA")
    await profile_flow._handle_profile_action(q_course, ctx_a2, "pick_course:CA")
    check("pending course staged", ctx_a2.user_data.get("profile_flow_pending_course") == "CA")
    q_level = mock_query(CHAT_A, "profile:pick_level:Inter")
    await profile_flow._handle_profile_action(q_level, ctx_a2, "pick_level:Inter")
    row = conn.execute("SELECT course, level FROM student_profiles WHERE username=?", (TEST_USERNAME,)).fetchone()
    check("course/level saved", row == ("CA", "Inter"))

    ctx_a3 = mock_context()
    q_year = mock_query(CHAT_A, "profile:pick_attempt_year:2027")
    await profile_flow._handle_profile_action(q_year, ctx_a3, "pick_attempt_year:2027")
    check("pending attempt year staged", ctx_a3.user_data.get("profile_flow_pending_attempt_year") == "2027")
    q_month = mock_query(CHAT_A, "profile:pick_attempt_month:November")
    await profile_flow._handle_profile_action(q_month, ctx_a3, "pick_attempt_month:November")
    row = conn.execute("SELECT exam_attempt FROM student_profiles WHERE username=?", (TEST_USERNAME,)).fetchone()
    check("exam_attempt saved as 'Month Year'", row[0] == "November 2027")
    check("pending attempt year cleared after save", "profile_flow_pending_attempt_year" not in ctx_a3.user_data)

    ctx_b2 = mock_context()
    ctx_b2.user_data["profile_flow_state"] = profile_flow.AWAITING_DISPLAY_NAME
    await profile_flow.handle_profile_text_input(mock_message(CHAT_B, "Rahul K"), ctx_b2)
    row = conn.execute("SELECT display_name FROM student_profiles WHERE username=?", (TEST_USERNAME,)).fetchone()
    check("display_name saved (set via chat B)", row[0] == "Rahul K")

    profile_via_a = profile_flow._get_profile_for_chat(conn, CHAT_A)
    check("chat A sees display_name set via chat B (shared)", profile_via_a["display_name"] == "Rahul K")
    check("chat A sees course/level/attempt too (shared)",
          profile_via_a["course"] == "CA" and profile_via_a["level"] == "Inter"
          and profile_via_a["exam_attempt"] == "November 2027")

    # --- 7. per-chat-id fields (email/mobile) NOT shared ------------------
    print("\n[7] Per-chat-id fields (email/mobile) stay separate")
    ctx_a4 = mock_context()
    ctx_a4.user_data["profile_flow_state"] = profile_flow.AWAITING_EMAIL
    await profile_flow.handle_profile_text_input(mock_message(CHAT_A, "student.a@example.com"), ctx_a4)
    check("state -> CONFIRMING_EMAIL", ctx_a4.user_data.get("profile_flow_state") == profile_flow.CONFIRMING_EMAIL)
    q_ec = mock_query(CHAT_A, "profileconfirm:yes")
    await profile_flow._handle_profile_confirm(q_ec, ctx_a4, "yes")
    row_a = conn.execute("SELECT email FROM students WHERE telegram_user_id=?", (CHAT_A,)).fetchone()
    check("chat A email saved", row_a[0] == "student.a@example.com")
    row_b = conn.execute("SELECT email FROM students WHERE telegram_user_id=?", (CHAT_B,)).fetchone()
    check("chat B email NOT affected (per-chat-id, not shared)", row_b[0] is None)

    ctx_a5 = mock_context()
    ctx_a5.user_data["profile_flow_state"] = profile_flow.AWAITING_MOBILE
    await profile_flow.handle_profile_text_input(mock_message(CHAT_A, "9876543210"), ctx_a5)
    check("state -> CONFIRMING_MOBILE", ctx_a5.user_data.get("profile_flow_state") == profile_flow.CONFIRMING_MOBILE)
    check("mobile normalized correctly", ctx_a5.user_data.get("profile_flow_pending_mobile") == "9876543210")

    # invalid mobile stays in AWAITING_MOBILE
    ctx_a6 = mock_context()
    ctx_a6.user_data["profile_flow_state"] = profile_flow.AWAITING_MOBILE
    await profile_flow.handle_profile_text_input(mock_message(CHAT_A, "12345"), ctx_a6)
    check("invalid mobile rejected, state unchanged", ctx_a6.user_data.get("profile_flow_state") == profile_flow.AWAITING_MOBILE)

    # --- 8. menu never re-offers username setup once one is set ----------
    print("\n[8] Menu never re-offers username setup once locked")
    profile = profile_flow._get_profile_for_chat(conn, CHAT_A)
    markup = profile_flow._menu_keyboard(profile)
    all_cb = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    check("no 'start_username' button once username exists", "profile:start_username" not in all_cb)
    check("summary shows username as permanent",
          "permanent" in profile_flow._profile_summary_text(profile, CHAT_A, conn).lower())

    profile_none = profile_flow._get_profile_for_chat(conn, CHAT_C)
    check("chat C (no username yet) has no profile", profile_none is None)
    markup_none = profile_flow._menu_keyboard(profile_none)
    all_cb_none = [btn.callback_data for row in markup_none.inline_keyboard for btn in row]
    check("'start_username' IS offered when no username exists", "profile:start_username" in all_cb_none)

    # --- 9. is_awaiting_text_input() correctness --------------------------
    print("\n[9] is_awaiting_text_input()")
    ctx_none = mock_context()
    check("False when state is unset", profile_flow.is_awaiting_text_input(ctx_none) is False)
    ctx_menu = mock_context()
    ctx_menu.user_data["profile_flow_state"] = profile_flow.CONFIRMING_START
    check("False for CONFIRMING_START (button-driven, not text)", profile_flow.is_awaiting_text_input(ctx_menu) is False)
    ctx_text = mock_context()
    ctx_text.user_data["profile_flow_state"] = profile_flow.AWAITING_DISPLAY_NAME
    check("True for AWAITING_DISPLAY_NAME", profile_flow.is_awaiting_text_input(ctx_text) is True)

    print(f"\n=== {PASS} passed, {FAIL} failed ===")
    return FAIL == 0


if __name__ == "__main__":
    try:
        ok = asyncio.run(main())
    finally:
        cleanup()
        print("(cleanup done -- all synthetic rows removed)")
    sys.exit(0 if ok else 1)
