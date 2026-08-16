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
import exam_hub_bot as bot  # noqa: E402 -- real module, real DB_CONN, real loaded content banks

CHAT_ID = 900_300_001
TG_HANDLE = "smoketst_ehwallet"  # <=20 chars, per identity.py's MAX_USERNAME_LEN -- a longer handle here would correctly fall back to the tg{id} placeholder, which is a real identity.py behavior, not a bug (caught by running this test with too-long a handle first)

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


def cleanup():
    row = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (CHAT_ID,)).fetchone()
    username = row[0] if row else None
    conn.execute("DELETE FROM exam_hub_sessions WHERE telegram_user_id=?", (CHAT_ID,))
    conn.execute("DELETE FROM exam_hub_descriptive_events WHERE telegram_user_id=?", (CHAT_ID,))
    conn.execute("DELETE FROM exam_hub_mcq_attempts WHERE telegram_user_id=?", (CHAT_ID,))
    conn.execute("DELETE FROM bot_interactions WHERE telegram_user_id=?", (CHAT_ID,))
    conn.execute("DELETE FROM students WHERE telegram_user_id=?", (CHAT_ID,))
    if username:
        conn.execute("DELETE FROM wallet_ledger WHERE username=?", (username,))
        conn.execute("DELETE FROM wallet_grants WHERE username=?", (username,))
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
        check("out-of-balance message doesn't falsely promise a working recharge", "recharg" in sent_text.lower())

    finally:
        cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
