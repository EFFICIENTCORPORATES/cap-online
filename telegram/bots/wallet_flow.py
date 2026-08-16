"""
telegram/bots/wallet_flow.py -- wallet status display + recharge flow
(2026-08-16)
--------------------------------------------------------------------------------
Two related, always-together features, per Pranav's ask: typing "wallet"
shows balance status (same "profile" trigger convention profile_flow.py
already established) with a "Recharge Wallet" button; typing "recharge" (or
tapping that button) starts the actual top-up conversation -- Razorpay
Payment Link creation, sent to the student, polled for confirmation, wallet
credited on payment. See telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md
§9.5/§0.2 for the original design this implements.

FIRST LIVE RAZORPAY USE ON THIS PLATFORM. Live keys, no test-mode fallback
(Pranav's explicit call, 2026-08-15 -- "amount is small... please go ahead
with the live keys only"). Every create_payment_link() call here is a real,
payable link. Idempotency lives at the DB layer (payments.gateway_txn_id
UNIQUE, wallet.credit_for_recharge()'s idempotency_key) -- this module never
retries a create call on its own.

SAME MODULE SHAPE / host-injection pattern as test_flow.py -- see that
module's own docstring for the full reasoning (avoids a circular import,
reuses exam_hub_bot.py's HTML/message helpers without duplicating them).

CALLBACK NAMESPACING: `walletrc:<action>` for the recharge amount picker
(amount buttons + custom-amount text entry), separate from test_flow.py's
`t*`/`testflow:` prefixes and every other flow's own prefix, same explicit-
pattern-per-module discipline this platform enforces everywhere.
"""

import sys
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402
import wallet  # noqa: E402
import identity  # noqa: E402
import razorpay_client  # noqa: E402

logger = logging.getLogger(__name__)

WALLET_TRIGGER_PHRASES = {"wallet", "my wallet", "balance", "my balance", "check balance"}
RECHARGE_TRIGGER_PHRASES = {"recharge", "top up", "topup", "add money", "add credits"}

AMOUNT_PRESETS_INR = [20, 50, 100]
POLL_INTERVAL_SECONDS = 20
LINK_VALIDITY_MINUTES = 30

UD_AWAITING_CUSTOM_AMOUNT = "walletrc_awaiting_custom_amount"


def matches_wallet_trigger(text: str) -> bool:
    return text.strip().lower() in WALLET_TRIGGER_PHRASES


def matches_recharge_trigger(text: str) -> bool:
    return text.strip().lower() in RECHARGE_TRIGGER_PHRASES


def is_awaiting_custom_amount(context) -> bool:
    return bool(context.user_data.get(UD_AWAITING_CUSTOM_AMOUNT))


# ---------------------------------------------------------------------------
# WALLET STATUS ("wallet" trigger)
# ---------------------------------------------------------------------------

def _nearest_expiry(conn, username: str):
    """The soonest un-swept grant expiry for this username, or None if the
    student has no grant-sourced credits left to expire (already clawed
    back, or never had one)."""
    row = conn.execute(
        "SELECT expires_at, amount_credits FROM wallet_grants "
        "WHERE username=? AND swept_at IS NULL ORDER BY expires_at LIMIT 1",
        (username,),
    ).fetchone()
    return row  # (expires_at, amount_credits) or None


def _status_text_and_markup(conn, username: str) -> tuple:
    balance = wallet.get_balance(conn, username)
    mcq_equiv = balance // wallet.RATE_MCQ_CREDIT
    desc_equiv = balance // wallet.RATE_DESCRIPTIVE_CREDIT
    test_marks_equiv = balance // wallet.RATE_TEST_CREDIT_PER_MARK

    lines = [
        "\U0001F4B0 <b>Your Balance</b>",
        "",
        f"Enough for about <b>{mcq_equiv} MCQs</b>, or <b>{desc_equiv} Descriptive Questions</b>, "
        f"or <b>{test_marks_equiv} marks worth of Tests</b> (any mix — one shared balance).",
    ]

    expiry = _nearest_expiry(conn, username)
    if expiry:
        expires_at, grant_amount = expiry
        days_left = (datetime.fromisoformat(expires_at) - datetime.now(timezone.utc)).days
        if days_left >= 0:
            lines.append("")
            lines.append(f"⏳ Part of your balance (from a free grant) expires in <b>{days_left} day(s)</b> if unused.")

    lines.append("")
    lines.append("Type <code>recharge</code> anytime to add more, or tap below.")

    markup = InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F4B3 Recharge Wallet", callback_data="walletrc:start")]])
    return "\n".join(lines), markup


async def show_wallet_status(update, context, host):
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    user = update.effective_user
    username, _ = identity.ensure_wallet_identity(conn, user)
    text, markup = _status_text_and_markup(conn, username)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


# ---------------------------------------------------------------------------
# RECHARGE FLOW ("recharge" trigger, or the "Recharge Wallet" button)
# ---------------------------------------------------------------------------

def _amount_picker_markup():
    rows = [[InlineKeyboardButton(f"₹{amt}", callback_data=f"walletrc:amount:{amt}")] for amt in AMOUNT_PRESETS_INR]
    rows.append([InlineKeyboardButton("Custom amount", callback_data="walletrc:custom")])
    return InlineKeyboardMarkup(rows)


async def start_recharge_flow(update_or_query, context, host, is_callback=False):
    text = (
        f"\U0001F4B3 How much would you like to add? (minimum ₹{wallet.RECHARGE_MINIMUM_INR})\n\n"
        f"₹1 = {int(1/wallet.CREDIT_TO_INR)} credits."
    )
    markup = _amount_picker_markup()
    if is_callback:
        await update_or_query.edit_message_text(text, reply_markup=markup)
    else:
        await update_or_query.message.reply_text(text, reply_markup=markup)


async def _handle_custom_amount_prompt(query, context):
    context.user_data[UD_AWAITING_CUSTOM_AMOUNT] = True
    await query.edit_message_text(f"Type the amount in rupees (minimum ₹{wallet.RECHARGE_MINIMUM_INR}), e.g. 30")


async def handle_custom_amount_text(update, context, host) -> bool:
    if not is_awaiting_custom_amount(context):
        return False
    context.user_data[UD_AWAITING_CUSTOM_AMOUNT] = False
    text = (update.message.text or "").strip()
    try:
        amount = int(float(text))
    except ValueError:
        await update.message.reply_text(f"That doesn't look like a number — type just the amount, e.g. 30. Or type <code>recharge</code> to start over.", parse_mode=ParseMode.HTML)
        return True
    if amount < wallet.RECHARGE_MINIMUM_INR:
        await update.message.reply_text(f"Minimum recharge is ₹{wallet.RECHARGE_MINIMUM_INR}. Type <code>recharge</code> to try again.", parse_mode=ParseMode.HTML)
        return True
    await _create_and_send_link(update, context, host, amount, is_callback=False)
    return True


async def _create_and_send_link(update_or_query, context, host, amount_inr: int, is_callback: bool):
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    user = update_or_query.from_user if is_callback else update_or_query.effective_user
    username, _ = identity.ensure_wallet_identity(conn, user)
    chat_id = update_or_query.message.chat_id

    if not razorpay_client.is_configured():
        text = "⚠️ Recharging isn't available right now — please try again later or contact support@1lavya.com."
        if is_callback:
            await update_or_query.edit_message_text(text)
        else:
            await update_or_query.message.reply_text(text)
        return

    reference_id = f"recharge:{username}:{int(datetime.now(timezone.utc).timestamp())}"
    credits_for_amount = wallet.inr_to_credits(amount_inr)
    try:
        link = razorpay_client.create_payment_link(
            amount_inr=amount_inr,
            reference_id=reference_id,
            description=f"1LAVYA wallet recharge — {credits_for_amount} credits",
            customer_contact=None,
            notes={"username": username, "bot_id": getattr(host, "BOT_ID", "")},
            expire_after_minutes=LINK_VALIDITY_MINUTES,
        )
    except razorpay_client.RazorpayError as e:
        logger.error(f"wallet_flow: Razorpay Payment Link creation failed for {username}: {e}")
        text = "⚠️ Couldn't start your recharge right now — please try again in a bit."
        if is_callback:
            await update_or_query.edit_message_text(text)
        else:
            await update_or_query.message.reply_text(text)
        return

    now = platform_db.now()
    platform_db.execute_with_retry(
        conn,
        "INSERT INTO payments (kind, tenant_id, telegram_user_id, username, amount_inr, credits_granted, "
        "gateway, gateway_txn_id, status, created_at) VALUES ('student_credit_recharge',?,?,?,?,?,'razorpay',?,'pending',?)",
        (getattr(host, "TENANT_ID", ""), user.id, username, amount_inr, credits_for_amount, link["id"], now),
    )

    text = (
        f"\U0001F4B3 Tap to pay ₹{amount_inr} ({credits_for_amount} credits):\n{link['short_url']}\n\n"
        f"This link is valid for {LINK_VALIDITY_MINUTES} minutes. Your wallet will be credited automatically "
        f"the moment payment is confirmed — no need to do anything else here."
    )
    if is_callback:
        await update_or_query.edit_message_text(text)
    else:
        await update_or_query.message.reply_text(text)

    _schedule_poll_job(context, link["id"], chat_id, username, getattr(host, "TENANT_ID", ""))


async def wallet_flow_callback(update, context, bot_id: str, host):
    query = update.callback_query
    data = query.data
    action = data.split(":")[1] if ":" in data else ""

    if action == "start":
        await start_recharge_flow(query, context, host, is_callback=True)
    elif action == "amount":
        amount = int(data.split(":")[2])
        await _create_and_send_link(query, context, host, amount, is_callback=True)
    elif action == "custom":
        await _handle_custom_amount_prompt(query, context)


# ---------------------------------------------------------------------------
# PAYMENT CONFIRMATION POLLING -- no webhook yet (Cloudflare Tunnel still
# blocked on Pranav's own interactive login, see roadmap §9.5); polling
# GET /v1/payment_links/{id} is a complete, correct v1.
# ---------------------------------------------------------------------------

def _poll_job_name(payment_link_id: str) -> str:
    return f"recharge_poll:{payment_link_id}"


def _schedule_poll_job(context, payment_link_id: str, chat_id: int, username: str, tenant_id: str):
    if not context.job_queue:
        return
    context.job_queue.run_repeating(
        _poll_job_callback, interval=POLL_INTERVAL_SECONDS, first=POLL_INTERVAL_SECONDS,
        name=_poll_job_name(payment_link_id),
        data={"payment_link_id": payment_link_id, "chat_id": chat_id, "username": username, "tenant_id": tenant_id},
    )


async def _poll_job_callback(context):
    job_data = context.job.data
    payment_link_id = job_data["payment_link_id"]
    conn = platform_db.get_connection()
    row = conn.execute("SELECT status, amount_inr, credits_granted, created_at FROM payments WHERE gateway_txn_id=?", (payment_link_id,)).fetchone()
    if not row or row[0] != "pending":
        context.job.schedule_removal()
        return
    _, amount_inr, credits_granted, created_at = row

    created_dt = datetime.fromisoformat(created_at)
    if datetime.now(timezone.utc) - created_dt > timedelta(minutes=LINK_VALIDITY_MINUTES + 2):
        platform_db.execute_with_retry(conn, "UPDATE payments SET status='failed' WHERE gateway_txn_id=?", (payment_link_id,))
        context.job.schedule_removal()
        await context.bot.send_message(chat_id=job_data["chat_id"], text="⏰ That recharge link expired unused. Type <code>recharge</code> to try again.", parse_mode=ParseMode.HTML)
        return

    try:
        link = razorpay_client.fetch_payment_link(payment_link_id)
    except razorpay_client.RazorpayError as e:
        logger.warning(f"wallet_flow: poll failed for {payment_link_id}: {e}")
        return  # transient -- try again next interval, don't give up on one failed poll

    status = link.get("status")
    if status == "paid":
        now = platform_db.now()
        platform_db.execute_with_retry(conn, "UPDATE payments SET status='completed', completed_at=? WHERE gateway_txn_id=?", (now, payment_link_id))
        new_balance, already = wallet.credit_for_recharge(conn, job_data["username"], job_data["tenant_id"], payment_link_id, credits_granted)
        context.job.schedule_removal()
        if not already:
            await context.bot.send_message(
                chat_id=job_data["chat_id"],
                text=f"✅ Payment received! {credits_granted} credits added — your new balance is {new_balance}.",
            )
    elif status in ("cancelled", "expired"):
        platform_db.execute_with_retry(conn, "UPDATE payments SET status='failed' WHERE gateway_txn_id=?", (payment_link_id,))
        context.job.schedule_removal()
        await context.bot.send_message(chat_id=job_data["chat_id"], text="That recharge link was cancelled or expired. Type <code>recharge</code> to try again.", parse_mode=ParseMode.HTML)
    # else ("issued"/"partially_paid"): keep polling


def rearm_pending_recharge_jobs(application, host):
    """Same reasoning as test_flow.rearm_pending_test_jobs() -- job_queue
    jobs don't survive a process restart. Sweeps pending payments and
    re-arms their poll job (or fails them out if their link has already
    aged past validity while the bot was down)."""
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    rows = conn.execute(
        "SELECT gateway_txn_id, telegram_user_id, username, tenant_id, created_at FROM payments "
        "WHERE status='pending' AND gateway='razorpay'"
    ).fetchall()
    rearmed = 0
    for payment_link_id, telegram_user_id, username, tenant_id, created_at in rows:
        application.job_queue.run_repeating(
            _poll_job_callback, interval=POLL_INTERVAL_SECONDS, first=5,
            name=_poll_job_name(payment_link_id),
            data={"payment_link_id": payment_link_id, "chat_id": telegram_user_id, "username": username, "tenant_id": tenant_id},
        )
        rearmed += 1
    if rearmed:
        logger.info(f"wallet_flow: startup sweep -- re-armed {rearmed} pending recharge poll job(s).")
