"""
telegram/bots/smoke_test_exam_hub_wallet.py -- integration test for the
2026-08-16 wallet/billing wiring inside exam_hub_bot.py
--------------------------------------------------------------------------------
This is DELIBERATELY separate from telegram/database/smoke_test_wallet.py:
that one proves wallet.py/identity.py's own logic is correct in isolation;
THIS one proves the actual WIRING inside exam_hub_bot.py (db_ensure_wallet(),
the debit calls in send_question()/send_mcq(), the out-of-balance path) is
correct -- a wiring bug (wrong variable name, wrong function signature,
debit called in the wrong place) would NOT be caught by the isolated module
test, only by actually driving the real bot code.

Imports exam_hub_bot.py directly (with BOT_ID=1lavya-examhub) and calls its
real start()/send_question()/send_mcq() against synthetic, self-cleaning
chat_ids and real (but harmless) question records already loaded in the
bot's own bank/mcq_bank -- same "no mocking of the DB layer itself, full
cleanup in finally" discipline as every other smoke test on this platform.
Mocks only the Telegram API surface (query/message/context), same pattern
smoke_test_leaderboards.py's mock_query() already established.

Run directly: `python smoke_test_exam_hub_wallet.py` (from telegram/bots/,
or anywhere -- it sets BOT_ID itself before importing).
"""

import os
import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

os.environ.setdefault("BOT_ID", "1lavya-examhub")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import wallet  # noqa: E402
import identity  # noqa: E402
import broadcast  # noqa: E402 -- telegram/database/broadcast.py (2026-08-18), for step 7 below
import exam_hub_bot as bot  # noqa: E402 -- real module, real DB_CONN, real loaded content banks

CHAT_ID = 900_300_001
TG_HANDLE = "smoketst_ehwallet"  # <=20 chars, per identity.py's MAX_USERNAME_LEN -- a longer handle here would correctly fall back to the tg{id} placeholder, which is a real identity.py behavior, not a bug (caught by running this test with too-long a handle first)
BCAST_CHAT_ID = 900_300_003  # step 7's broadcast "restart:bcast:<id>" tracked-tap test -- synthetic, never a real student's
BCAST_CHAPTERS_CHAT_ID = 900_300_004  # step 7's "restart:bcastchapters:<id>" (Show Chapter List, WITH prior MCQ history) test
BCAST_NOHISTORY_CHAT_ID = 900_300_005  # step 7's "restart:bcastchapters:<id>" fallback test (NO prior MCQ history)

conn = bot.DB_CONN  # the SAME connection the bot module itself uses -- not a separate one

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


REGRESSION_CHAT_ID = 900_300_002  # step 6's session-expired-loop regression check -- synthetic, never a real student's


def cleanup():
    for chat_id in (CHAT_ID, REGRESSION_CHAT_ID, BCAST_CHAT_ID, BCAST_CHAPTERS_CHAT_ID, BCAST_NOHISTORY_CHAT_ID):
        row = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (chat_id,)).fetchone()
        username = row[0] if row else None
        # BUG FIXED 2026-08-17: exam_hub_mcq_attempts/exam_hub_descriptive_events
        # both FK-reference exam_hub_sessions(session_id) -- deleting
        # exam_hub_sessions FIRST (the original order here) only ever
        # worked by accident, because steps 3-5 above construct their mock
        # context with session_id=None, so nothing they logged carried a
        # real FK to clean up in the first place. Step 6's regression check
        # calls the REAL bot.start() (real session_id throughout), which
        # immediately surfaced this as a real IntegrityError -- children
        # must be deleted before the parent they reference.
        conn.execute("DELETE FROM exam_hub_descriptive_events WHERE telegram_user_id=?", (chat_id,))
        conn.execute("DELETE FROM exam_hub_mcq_attempts WHERE telegram_user_id=?", (chat_id,))
        conn.execute("DELETE FROM exam_hub_sessions WHERE telegram_user_id=?", (chat_id,))
        conn.execute("DELETE FROM bot_interactions WHERE telegram_user_id=?", (chat_id,))
        conn.execute("DELETE FROM students WHERE telegram_user_id=?", (chat_id,))
        if username:
            conn.execute("DELETE FROM wallet_ledger WHERE username=?", (username,))
            conn.execute("DELETE FROM wallet_grants WHERE username=?", (username,))
            conn.execute("DELETE FROM access_requests WHERE username=?", (username,))
            conn.execute("DELETE FROM student_academic_profiles WHERE username=?", (username,))
            conn.execute("DELETE FROM student_profiles WHERE username=?", (username,))
    conn.commit()


def mock_update():
    user = SimpleNamespace(id=CHAT_ID, username=TG_HANDLE, first_name="Smoke", last_name="Test")
    message = SimpleNamespace(chat_id=CHAT_ID, reply_text=AsyncMock())
    update = SimpleNamespace(effective_user=user, message=message)
    context = SimpleNamespace(user_data={})
    return update, context, user, message


def mock_query(context, user):
    q = SimpleNamespace()
    q.from_user = user
    q.message = SimpleNamespace(chat_id=CHAT_ID, reply_text=AsyncMock())
    q.answer = AsyncMock()
    q.edit_message_text = AsyncMock()
    context.bot = SimpleNamespace(send_message=AsyncMock(), send_document=AsyncMock())
    return q


async def main():
    print("=== smoke_test_exam_hub_wallet ===")
    cleanup()

    try:
        # 1. First /start ever -> grants the signup bonus, sends a welcome message.
        update, context, user, message = mock_update()
        await bot.start(update, context)
        row = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (CHAT_ID,)).fetchone()
        check("start() auto-provisioned a username", row is not None and row[0] == TG_HANDLE)
        username = row[0]
        check("start() actually granted the signup bonus in the ledger", wallet.get_balance(conn, username) == wallet.SIGNUP_GRANT_CREDITS)
        # 2 calls to reply_text: the welcome-bonus message, then the menu.
        check("start() sent a welcome-bonus message (2 replies: bonus + menu)", message.reply_text.await_count == 2)
        first_call_text = message.reply_text.await_args_list[0].args[0]
        check("the welcome message uses question/mark language, not rupees", "1000 MCQs" in first_call_text and "₹" not in first_call_text)

        # 2. A second /start (e.g. "Start Over") does NOT re-grant.
        update2, context2, user2, message2 = mock_update()
        await bot.start(update2, context2)
        check("second start() does not re-grant", wallet.get_balance(conn, username) == wallet.SIGNUP_GRANT_CREDITS)
        check("second start() sends only the menu, no bonus message", message2.reply_text.await_count == 1)

        # 3. send_question() actually debits RATE_DESCRIPTIVE_CREDIT (10) via
        #    the real wired-in call, not just wallet.py in isolation.
        balance_before = wallet.get_balance(conn, username)
        real_book_id = bot.bank.questions[0]["book_id"]
        ctx3 = SimpleNamespace(user_data={"queue": [real_book_id], "queue_pos": 0, "session_id": None}, bot=SimpleNamespace(send_message=AsyncMock()))
        q3 = mock_query(ctx3, user)
        await bot.send_question(q3, ctx3)
        check(
            f"send_question() debited exactly {wallet.RATE_DESCRIPTIVE_CREDIT} credits",
            wallet.get_balance(conn, username) == balance_before - wallet.RATE_DESCRIPTIVE_CREDIT,
        )

        # 4. send_mcq() actually debits RATE_MCQ_CREDIT (1) via the real wired-in call.
        balance_before = wallet.get_balance(conn, username)
        real_mcq_id = bot.mcq_bank.questions[0]["mcq_id"]
        ctx4 = SimpleNamespace(user_data={"queue": [real_mcq_id], "queue_pos": 0, "session_id": None}, bot=SimpleNamespace(send_message=AsyncMock()))
        q4 = mock_query(ctx4, user)
        await bot.send_mcq(q4, ctx4)
        check(
            f"send_mcq() debited exactly {wallet.RATE_MCQ_CREDIT} credit",
            wallet.get_balance(conn, username) == balance_before - wallet.RATE_MCQ_CREDIT,
        )

        # 5. Drain the balance to (just under) zero, then confirm the NEXT
        #    question is blocked with the out-of-balance message, and no
        #    further debit happens (balance doesn't go negative).
        remaining = wallet.get_balance(conn, username)
        wallet.debit(conn, username, "smoketest", "manual_adjustment", remaining, reference="smoketest-drain")
        check("balance drained to exactly 0 for the next check", wallet.get_balance(conn, username) == 0)

        ctx5 = SimpleNamespace(user_data={"queue": [real_mcq_id], "queue_pos": 0, "session_id": None}, bot=SimpleNamespace(send_message=AsyncMock()))
        q5 = mock_query(ctx5, user)
        await bot.send_mcq(q5, ctx5)
        check("out-of-balance: no negative debit happened", wallet.get_balance(conn, username) == 0)
        check("out-of-balance: bot.send_message was called with the out-of-balance text", ctx5.bot.send_message.await_count == 1)
        sent_text = ctx5.bot.send_message.await_args.kwargs.get("text", "")
        check("out-of-balance message never mentions rupees", "₹" not in sent_text)
        # 2026-08-16: now carries a REAL Recharge Wallet button (walletrc:start)
        # rather than just promising text -- checked via the actual markup,
        # not string-matching the message body.
        sent_markup = ctx5.bot.send_message.await_args.kwargs.get("reply_markup")
        check("out-of-balance message includes a real Recharge Wallet button", sent_markup is not None and "walletrc:start" in str(sent_markup))

        # 6. REGRESSION (live bug report, 2026-08-17): "session expired"
        # looping right after picking a Subject/Mode, for any subject whose
        # Exam Type and/or Year auto-skip (2026-08-16's Mix-All fix).
        # Root cause was two-fold: (a) the "subject" action discarded
        # resolve_entry()'s `updates` entirely, so an auto-picked exam_type/
        # year never reached context.user_data, and the very next tap
        # (Chapter) always found them missing via _require_state() ->
        # "session expired"; (b) once fixed naively, db_update_session()
        # turned out to accept ANY kwarg as a literal SQL column with zero
        # validation, crashing on exam_type/year (exam_hub_sessions only
        # tracks mode/course/level/subject, by design). Both fixed --
        # this walks the REAL button_router end to end across every real
        # (course, level, subject) combo that has an auto-skip on Type or
        # Year, on a synthetic chat_id (never a real student's), and
        # asserts neither failure mode can recur.
        reg_chat = 900_300_002
        reg_user = SimpleNamespace(id=reg_chat, username=None, first_name="Smoke", last_name="Regression")

        async def tap_as(ctx, user, chat_id, data):
            qq = SimpleNamespace(data=data, from_user=user, message=SimpleNamespace(chat_id=chat_id),
                                  edit_message_text=AsyncMock(), answer=AsyncMock())
            await bot.button_router(SimpleNamespace(callback_query=qq), ctx)
            return qq

        async def tap(ctx, data):
            return await tap_as(ctx, reg_user, reg_chat, data)

        checked_a_real_autoskip_case = False
        for mode in ("mcq", "descriptive"):
            bank_obj = bot._mode_bank(mode)
            for course in bank_obj.courses():
                for level in bank_obj.levels(course):
                    for i, subject in enumerate(bank_obj.subjects(course, level)):
                        ets = bank_obj.exam_types(course, level, subject)
                        if len(ets) > 1:
                            continue  # only care about a subject whose Type step auto-skips
                        ctx6 = SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock()))
                        upd6 = SimpleNamespace(effective_user=reg_user, message=SimpleNamespace(reply_text=AsyncMock(), chat_id=reg_chat))
                        await bot.start(upd6, ctx6)
                        await tap(ctx6, f"mode:{mode}")
                        # Drive Course/Level explicitly (bypasses Pranav's own
                        # saved-profile auto-fill so this test exercises every
                        # real combo, not just his one saved CA Inter profile).
                        ctx6.user_data.update({"course": course, "level": level, "mode": mode})
                        subjects = bank_obj.subjects(course, level)
                        ctx6.user_data["subject_options"] = subjects
                        q6 = await tap(ctx6, f"subject:{i}")
                        crashed_or_expired = (
                            q6.edit_message_text.call_args is None
                            or "session has expired" in q6.edit_message_text.call_args[0][0].lower()
                        )
                        check(f"picking Subject '{subject}' ({course} {level}, {mode}, auto-skip Type) never itself shows session-expired", not crashed_or_expired)
                        check(f"  -> exam_type WAS saved to user_data for '{subject}'", "exam_type" in ctx6.user_data)
                        if "chapter_slugs" in ctx6.user_data:
                            q7 = await tap(ctx6, "chapter:0")
                            still_expired = (
                                q7.edit_message_text.call_args is not None
                                and "session has expired" in q7.edit_message_text.call_args[0][0].lower()
                            )
                            check(f"  -> the FOLLOW-UP Chapter tap for '{subject}' does not loop back to session-expired", not still_expired)
                            checked_a_real_autoskip_case = True
        check("at least one real (course, level, subject) combo with an auto-skipping Type step was actually exercised", checked_a_real_autoskip_case)

        # 7. Broadcast "Start Practicing Now" button (2026-08-18) --
        # callback_data "restart:bcast:<campaign_id>". Real checks: (a) a
        # bare "restart" tap (the overwhelming majority of real traffic,
        # e.g. every "Continue Practicing" button) is COMPLETELY unaffected
        # -- still resets to the entry screen, no broadcast code path
        # touched at all; (b) a genuine "restart:bcast:<id>" tap does the
        # SAME full reinitialization (proving the extension didn't change
        # existing behavior) AND logs a real interaction against the exact
        # matching broadcast_deliveries row; (c) a stale/unmatched
        # campaign_id doesn't crash the tap -- the menu still renders.
        bcast_user = SimpleNamespace(id=BCAST_CHAT_ID, username=None, first_name="Smoke", last_name="Broadcast")
        campaign_id = broadcast.create_campaign(
            conn, category="smoketest_category", message_text="smoketest", message_html="<b>smoketest</b>",
            criteria_description="smoketest", created_by="smoke_test_exam_hub_wallet.py",
        )
        broadcast.log_delivery(conn, campaign_id, BCAST_CHAT_ID, bot.BOT_ID, "smoketest (personalized)", status="sent")
        try:
            # (a) bare "restart" -- provably unaffected
            ctx7a = SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock()))
            q7a = await tap(ctx7a, "restart")
            check("a bare 'restart' tap still resets to the entry screen (unaffected by the extension)",
                  q7a.edit_message_text.await_count == 1)
            no_interaction_row = conn.execute(
                "SELECT interacted_at FROM broadcast_deliveries WHERE campaign_id=? AND telegram_user_id=?",
                (campaign_id, reg_chat),
            ).fetchone()
            check("a bare 'restart' tap never touches broadcast tracking (no row for an unrelated chat_id)",
                  no_interaction_row is None)

            # (b) the real tracked tap
            ctx7b = SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock()))
            q7b = await tap_as(ctx7b, bcast_user, BCAST_CHAT_ID, f"restart:bcast:{campaign_id}")
            check("a tracked 'restart:bcast:<id>' tap still shows the real entry screen", q7b.edit_message_text.await_count == 1)
            row = conn.execute(
                "SELECT interacted_at, interaction_type FROM broadcast_deliveries WHERE campaign_id=? AND telegram_user_id=?",
                (campaign_id, BCAST_CHAT_ID),
            ).fetchone()
            check("a real interaction was logged against the matching delivery row", row is not None and row[0] is not None)
            check("interaction_type is 'start_practicing_tap'", row is not None and row[1] == "start_practicing_tap")

            # (c) stale/unmatched campaign_id -- must not crash
            ctx7c = SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock()))
            q7c = await tap_as(ctx7c, bcast_user, BCAST_CHAT_ID, "restart:bcast:999999999")
            check("a stale/unmatched campaign_id does not crash the tap", q7c.edit_message_text.await_count == 1)

            # (d) "Show Chapter List" -- restart:bcastchapters:<id>, WITH
            # real prior MCQ history: jumps straight to a chapter picker
            # for the student's own most-practiced subject, MIX exam
            # type/year, no Course/Level/Subject picker shown at all.
            chapters_user = SimpleNamespace(id=BCAST_CHAPTERS_CHAT_ID, username=None, first_name="Smoke", last_name="Chapters")
            real_mcq_id = bot.mcq_bank.questions[0]["mcq_id"]
            real_q = bot.mcq_bank.get_by_id(real_mcq_id)
            platform_db.upsert_student(conn, chapters_user)
            platform_db.execute_with_retry(
                conn,
                "INSERT INTO exam_hub_mcq_attempts (bot_id, telegram_user_id, mcq_id, course, level, shown_at, correct_option) "
                "VALUES (?,?,?,?,?,?,?)",
                (bot.BOT_ID, BCAST_CHAPTERS_CHAT_ID, real_mcq_id, real_q.get("_course"), real_q.get("_level"),
                 platform_db.now(), real_q.get("correct_option", "A")),
            )
            broadcast.log_delivery(conn, campaign_id, BCAST_CHAPTERS_CHAT_ID, bot.BOT_ID, "smoketest (personalized)", status="sent")

            resolved = bot._students_own_mcq_subject(BCAST_CHAPTERS_CHAT_ID)
            check("_students_own_mcq_subject() resolves a real (course, level, subject) from the seeded attempt",
                  resolved is not None and resolved == (real_q.get("_course"), real_q.get("_level"), real_q.get("_subject")))

            ctx7d = SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock()))
            q7d = await tap_as(ctx7d, chapters_user, BCAST_CHAPTERS_CHAT_ID, f"restart:bcastchapters:{campaign_id}")
            check("'Show Chapter List' tap renders a real screen", q7d.edit_message_text.await_count == 1)
            shown_text = q7d.edit_message_text.call_args[0][0]
            check("the shown screen is the CHAPTER picker, not the generic Mode/entry screen",
                  "Select *Chapter*" in shown_text)
            check("Course/Level/Subject/mode were set directly (no picker shown for them)",
                  ctx7d.user_data.get("mode") == "mcq" and ctx7d.user_data.get("course") == real_q.get("_course")
                  and ctx7d.user_data.get("level") == real_q.get("_level") and ctx7d.user_data.get("subject") == real_q.get("_subject"))
            check("exam_type/year were pre-set (MIX or the sole real value, never left unset)",
                  ctx7d.user_data.get("exam_type") and ctx7d.user_data.get("year"))
            row_d = conn.execute(
                "SELECT interacted_at, interaction_type FROM broadcast_deliveries WHERE campaign_id=? AND telegram_user_id=?",
                (campaign_id, BCAST_CHAPTERS_CHAT_ID),
            ).fetchone()
            check("interaction_type is 'show_chapters_tap'", row_d is not None and row_d[1] == "show_chapters_tap")

            # (e) "Show Chapter List" with NO prior MCQ history -- must fall
            # back gracefully to the normal entry screen, never crash or
            # show a broken/empty chapter list.
            nohistory_user = SimpleNamespace(id=BCAST_NOHISTORY_CHAT_ID, username=None, first_name="Smoke", last_name="NoHistory")
            broadcast.log_delivery(conn, campaign_id, BCAST_NOHISTORY_CHAT_ID, bot.BOT_ID, "smoketest (personalized)", status="sent")
            ctx7e = SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock()))
            q7e = await tap_as(ctx7e, nohistory_user, BCAST_NOHISTORY_CHAT_ID, f"restart:bcastchapters:{campaign_id}")
            check("'Show Chapter List' with zero prior history falls back without crashing",
                  q7e.edit_message_text.await_count == 1)
            fallback_text = q7e.edit_message_text.call_args[0][0]
            check("the fallback is NOT a chapter screen (no history to show chapters for)",
                  "Select *Chapter*" not in fallback_text)
        finally:
            conn.execute("DELETE FROM broadcast_deliveries WHERE campaign_id=?", (campaign_id,))
            conn.execute("DELETE FROM broadcast_campaigns WHERE campaign_id=?", (campaign_id,))
            conn.commit()

    finally:
        cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
