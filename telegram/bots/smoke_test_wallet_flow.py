"""
telegram/bots/smoke_test_wallet_flow.py -- smoke test for wallet_flow.py
(2026-08-16)
--------------------------------------------------------------------------------
CRITICAL SAFETY NOTE, read before touching this file: live Razorpay keys are
loaded into this process's environment (via exam_hub_bot.py's own
load_dotenv() at import time), so any UN-MOCKED call to
razorpay_client.create_payment_link() from this test would create a REAL,
live, payable Razorpay link. Every test below that reaches the
payment-creation or confirmation path mocks razorpay_client.create_payment_link
/fetch_payment_link explicitly via unittest.mock.patch -- never calls the
real API. Same discipline smoke_test_report_flow.py already established for
cf_email.py (deliberately unconfigured during automated runs there; here the
credentials ARE configured, so the mock is what keeps this safe instead).

Same cleanup/no-DB-mocking discipline as every other smoke test on this
platform otherwise. Run directly: `python smoke_test_wallet_flow.py`.
"""

import os
import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BOT_ID", "1lavya-examhub")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import wallet  # noqa: E402
import identity  # noqa: E402
import razorpay_client  # noqa: E402
import wallet_flow  # noqa: E402
import exam_hub_bot as bot  # noqa: E402

CHAT_ID = 900_500_001
TG_HANDLE = "smoketst_walletfl"

conn = bot.DB_CONN
host = sys.modules["exam_hub_bot"]

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
    # Deletion order matters (same lesson as smoke_test_wallet.py's own
    # earlier fix): payments.telegram_user_id ALSO references students, on
    # top of wallet_ledger's/wallet_grants'/students.lavya_username's own
    # FKs -- payments must go before students, not after.
    row = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (CHAT_ID,)).fetchone()
    username = row[0] if row else None
    conn.execute("DELETE FROM payments WHERE telegram_user_id=?", (CHAT_ID,))
    conn.execute("DELETE FROM students WHERE telegram_user_id=?", (CHAT_ID,))
    if username:
        conn.execute("DELETE FROM wallet_ledger WHERE username=?", (username,))
        conn.execute("DELETE FROM wallet_grants WHERE username=?", (username,))
        conn.execute("DELETE FROM student_profiles WHERE username=?", (username,))
        conn.execute("DELETE FROM payments WHERE username=?", (username,))
    conn.commit()


def mock_update(text=""):
    user = SimpleNamespace(id=CHAT_ID, username=TG_HANDLE, first_name="Smoke", last_name="Test")
    message = SimpleNamespace(chat_id=CHAT_ID, text=text, reply_text=AsyncMock())
    # effective_message=message mirrors real telegram.Update's own property --
    # needed since 2026-08-17's update.message -> update.effective_message
    # fix in wallet_flow.py (show_wallet_status/start_recharge_flow).
    return SimpleNamespace(effective_user=user, message=message, effective_message=message), user, message


def mock_context():
    return SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock()), job_queue=SimpleNamespace(run_repeating=lambda *a, **k: None))


def mock_query(user):
    q = SimpleNamespace()
    q.from_user = user
    q.message = SimpleNamespace(chat_id=CHAT_ID)
    q.edit_message_text = AsyncMock()
    return q


def last_text(mock_fn):
    call = mock_fn.await_args
    if call is None:
        return ""
    return call.args[0] if call.args else call.kwargs.get("text", "")


async def main():
    print("=== smoke_test_wallet_flow ===")
    print("(SAFETY: every Razorpay call below is mocked -- no real API calls, no real payment links created)")
    cleanup()

    try:
        # 0. Set up a student with a known balance + a real grant.
        user = SimpleNamespace(id=CHAT_ID, username=TG_HANDLE)
        conn.execute(
            "INSERT INTO students (telegram_user_id, username, first_name, last_name, first_seen_at, last_seen_at) "
            "VALUES (?,?,?,?,?,?)", (CHAT_ID, f"tg_{CHAT_ID}", "Smoke", "Test", platform_db.now(), platform_db.now()),
        )
        conn.commit()
        username, _ = identity.ensure_wallet_identity(conn, user)
        wallet.grant_signup_bonus(conn, username, "smoketest")
        wallet.debit(conn, username, "smoketest", "mcq_debit", 200, reference="smoketest-usage")

        # 1. "wallet" trigger shows balance in question/mark terms, an
        # expiry notice, and a real Recharge Wallet button -- never rupees.
        update, _, message = mock_update("wallet")
        context = mock_context()
        await wallet_flow.show_wallet_status(update, context, host)
        wallet_text = last_text(message.reply_text)
        check("wallet screen shows MCQ-equivalent balance", "MCQs" in wallet_text)
        check("wallet screen shows Descriptive-equivalent balance", "Descriptive Questions" in wallet_text)
        check("wallet screen shows Test-marks-equivalent balance", "marks worth of Tests" in wallet_text)
        check("wallet screen never mentions rupees", "₹" not in wallet_text)
        check("wallet screen shows an expiry notice for the grant", "expires in" in wallet_text)
        call_kwargs = message.reply_text.await_args.kwargs
        check("wallet screen includes a real Recharge Wallet button", "walletrc:start" in str(call_kwargs.get("reply_markup")))

        # 2. "recharge" trigger shows the amount picker (₹20/₹50/₹100 + custom).
        update2, _, message2 = mock_update("recharge")
        context2 = mock_context()
        await wallet_flow.start_recharge_flow(update2, context2, host)
        picker_markup = str(message2.reply_text.await_args.kwargs.get("reply_markup"))
        check("recharge picker offers all 3 presets", all(f"walletrc:amount:{a}" in picker_markup for a in wallet_flow.AMOUNT_PRESETS_INR))
        check("recharge picker offers a custom-amount option", "walletrc:custom" in picker_markup)

        # 3. Selecting a preset amount -- MOCKED Razorpay call, verifies the
        # DB write (payments row, pending) and the message sent to the
        # student, without ever hitting the real API.
        fake_link_response = {"id": "plink_SMOKETEST_FAKE_123", "short_url": "https://rzp.io/l/smoketestfake"}
        with patch.object(razorpay_client, "create_payment_link", return_value=fake_link_response) as mock_create:
            q3 = mock_query(user)
            context3 = mock_context()
            await wallet_flow._create_and_send_link(q3, context3, host, 50, is_callback=True)
            check("create_payment_link was called exactly once (mocked, not real)", mock_create.call_count == 1)
            call_kwargs3 = mock_create.call_args.kwargs
            check("the mocked call used the correct amount", call_kwargs3["amount_inr"] == 50)
        sent_text3 = last_text(q3.edit_message_text)
        check("the payable link is shown to the student", "smoketestfake" in sent_text3)
        payment_row = conn.execute("SELECT status, amount_inr, credits_granted, gateway_txn_id FROM payments WHERE username=?", (username,)).fetchone()
        check("a payments row was created as 'pending'", payment_row is not None and payment_row[0] == "pending")
        check("the payments row has the correct amount/credits", payment_row[1] == 50 and payment_row[2] == wallet.inr_to_credits(50))
        check("the payments row's gateway_txn_id matches the (mocked) link id", payment_row[3] == "plink_SMOKETEST_FAKE_123")

        # 4. Simulate the poll job firing and finding the payment 'paid' --
        # MOCKED fetch_payment_link, verifies the wallet actually gets
        # credited and the payments row moves to 'completed'.
        balance_before = wallet.get_balance(conn, username)
        fake_job = SimpleNamespace(data={"payment_link_id": "plink_SMOKETEST_FAKE_123", "chat_id": CHAT_ID, "username": username, "tenant_id": "smoketest"}, schedule_removal=lambda: None)
        fake_context = SimpleNamespace(job=fake_job, bot=SimpleNamespace(send_message=AsyncMock()))
        with patch.object(razorpay_client, "fetch_payment_link", return_value={"status": "paid"}) as mock_fetch:
            await wallet_flow._poll_job_callback(fake_context)
            check("fetch_payment_link was called exactly once (mocked, not real)", mock_fetch.call_count == 1)
        new_balance = wallet.get_balance(conn, username)
        check("wallet was credited the correct amount on confirmed payment", new_balance == balance_before + wallet.inr_to_credits(50))
        payment_row2 = conn.execute("SELECT status FROM payments WHERE gateway_txn_id=?", ("plink_SMOKETEST_FAKE_123",)).fetchone()
        check("payments row moved to 'completed'", payment_row2[0] == "completed")
        check("student was notified of the successful recharge", fake_context.bot.send_message.await_count == 1)

        # 5. Re-firing the poll job (already completed) must NOT double-credit.
        with patch.object(razorpay_client, "fetch_payment_link", return_value={"status": "paid"}):
            await wallet_flow._poll_job_callback(fake_context)
        check("re-polling an already-completed payment does not double-credit", wallet.get_balance(conn, username) == new_balance)

        # 6. Custom-amount text flow, below-minimum rejected without any Razorpay call.
        context6 = mock_context()
        context6.user_data[wallet_flow.UD_AWAITING_CUSTOM_AMOUNT] = True
        update6, _, message6 = mock_update("5")
        with patch.object(razorpay_client, "create_payment_link") as mock_create6:
            consumed = await wallet_flow.handle_custom_amount_text(update6, context6, host)
            check("below-minimum custom amount is rejected", consumed is True and "minimum" in last_text(message6.reply_text).lower())
            check("no Razorpay call made for a rejected amount", mock_create6.call_count == 0)

    finally:
        cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
