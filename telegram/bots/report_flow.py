"""
telegram/bots/report_flow.py -- the 20-question milestone report flow
(2026-08-11, Phase 2 of the branding-kit -> report-pipeline -> leaderboard
-> admin-portal roadmap)
--------------------------------------------------------------------------------
Imported by exam_hub_bot.py, study_hub_bot.py (and, through both, faculty_bot.py's
unified bot). Four things: (1) after every MCQ answer, check whether this
student has just crossed the PLATFORM-WIDE 20-answered-MCQs threshold
(Pranav's explicit 2026-08-10 call -- counts across every bot the student
has ever used, not per-bot) and, if so and not already prompted, offer a
report; (2) an ON-DEMAND trigger (added 2026-08-11) -- typing "report",
"analysis", "email", or "mail" (exact phrase, case-insensitive -- same
TRIGGER_PHRASES/matches_trigger() shape as profile_flow.py) asks the
student to confirm, then funnels into the SAME channel-picker and delivery
pipeline as the milestone prompt, regardless of whether that milestone has
ever fired for them; (3) the echo-and-confirm contact-collection dialog
for mobile/email -- deliberately NO OTP anywhere (Pranav's explicit,
repeated call) -- the bot just repeats back what it heard and asks the
student to confirm or re-type, which catches the common typo class
without OTP's friction; (4) once contact info is collected, actually
generate and send the report.

CALLBACK_DATA NAMESPACING: `report:<choice>` for the channel-preference
buttons (`telegram`/`email`/`both`/`skip`, then post-delivery
`addemail`/`addtelegram`/`upsell_no`/`done`), `reportconfirm:<yes|retry>`
for the echo-confirm step. Both are NEW prefixes -- registered as their own
CallbackQueryHandler in exam_hub_bot.py's main(), and MUST also be added
wherever a bot composes exam_hub_bot's handlers under a pattern-restricted
CallbackQueryHandler (faculty_bot.py) -- see that exact class of bug (a
restrictive regex silently swallowing a whole button) already found and
fixed once this session on 2026-08-10 for "next"/"restart". Don't repeat
it here. "Continue Practicing" is the one exception -- it deliberately
reuses the bare `restart` callback_data (no `report:` prefix at all) so it
falls through to button_router's own already-registered handler instead of
this module needing to reimplement "reset and show the entry screen."

BROADCAST INTERACTION TRACKING (added 2026-08-18): `report:bcast:
<campaign_id>:<bot_id>` is a THIRD `report:` sub-value, deliberately
reusing the exact same already-registered `report:` CallbackQueryHandler
pattern in every bot -- no bot script needed a new handler registration
for this to work (see telegram/tools/broadcast_sender.py's
get_report_button_markup(), which builds this exact callback_data). A tap
logs a real interaction (telegram/database/broadcast.py's
log_interaction()) against that recipient's specific broadcast_deliveries
row, then drops straight into the SAME channel-picker + delivery pipeline
every other report request uses -- a broadcast's "Get My Report" button IS
the on-demand trigger, not a separate feature. `bot_id` is embedded
directly in the callback_data (not read from context.user_data) because a
student tapping this button may never have used the report flow before,
so context.user_data["report_flow_bot_id"] can't be assumed to exist yet.

POST-DELIVERY FLOW (added 2026-08-11, Pranav's ask after live-testing:
"it should have asked me whether I need report in email as well" when he'd
only chosen Telegram): after delivering through whichever channel(s) the
student originally picked, if they picked exactly ONE (not "both"), offer
the other one before ending (`_offer_upsell_or_wrapup`) -- accepting routes
through the SAME echo-confirm contact collection as the original flow, but
`context.user_data["report_flow_upsell"]` tells the confirm-step to send
through ONLY the newly-added channel (`_deliver_report` with a one-element
set), never re-send the channel(s) already delivered. Either way, the
conversation always ends with an explicit "Continue Practicing" / "I'm
Done" question -- it never just stops silently after the report.

STATE: tracked in context.user_data["report_flow_state"] -- one of
AWAITING_MOBILE, CONFIRMING_MOBILE, AWAITING_EMAIL, CONFIRMING_EMAIL, or
absent (not in this flow). is_awaiting_text_input() is what
exam_hub_bot.py's MessageHandler checks before delegating a free-text
message here -- outside this flow, exam_hub_bot.py has no general free-text
handling yet (that's separate, not-yet-scheduled roadmap scope, not part
of this phase).
"""

import sys
import asyncio
import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut, NetworkError

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
sys.path.insert(0, str(REPO_ROOT / "telegram" / "tools"))
import db as platform_db  # noqa: E402
import student_analytics  # noqa: E402
import report_delivery  # noqa: E402
import generate_student_report  # noqa: E402
import contact_utils  # noqa: E402 -- shared with profile_flow.py, same directory (telegram/bots/)
import broadcast  # noqa: E402 -- telegram/database/broadcast.py (2026-08-18), for the "report:bcast:<id>:<bot_id>" branch below

logger = logging.getLogger(__name__)

MILESTONE_20Q = "20_questions_report_prompt"
MILESTONE_THRESHOLD = 20

# On-demand trigger (added 2026-08-11, Pranav's ask: "just like by typing
# profile, student can edit or view their profile... same way, by typing
# report, analysis, or email or mail, Bot will ask whether you need your
# analysis report"). Exact-phrase, case-insensitive match -- same
# discipline as profile_flow.py's TRIGGER_PHRASES, and the SAME accepted
# tradeoff: a student typing the single bare word "report" to mean
# something else (e.g. searching Study Hub for "Auditor's Report", a real
# CA topic) would be caught by this instead -- low-probability (an exact
# one-word message, not "audit report" or "report on X"), same risk class
# already accepted for "profile" colliding with nothing real in practice.
TRIGGER_PHRASES = {"report", "analysis", "email", "mail"}

AWAITING_MOBILE = "awaiting_mobile"
CONFIRMING_MOBILE = "confirming_mobile"
AWAITING_EMAIL = "awaiting_email"
CONFIRMING_EMAIL = "confirming_email"

# 2026-08-11: moved to contact_utils.py (shared with profile_flow.py's own
# email/mobile edit steps) -- these names kept as thin aliases so nothing
# else in this module (or smoke_test_report_flow.py, which references them
# directly) needs to change.
_normalize_mobile = contact_utils.normalize_mobile
_valid_email = contact_utils.valid_email


def is_awaiting_text_input(context) -> bool:
    return context.user_data.get("report_flow_state") in (AWAITING_MOBILE, AWAITING_EMAIL)


def matches_trigger(text: str) -> bool:
    return text.strip().lower() in TRIGGER_PHRASES


def _log_event(conn, telegram_user_id: int, event_type: str, detail: str = None):
    """The complete conversational trail Pranav asked for after debugging
    the missed-milestone bug ("a log maintained of the message sent and
    user name collected... all such messages sent... a complete trail") --
    every prompt shown, every value collected/confirmed/rejected, every
    send outcome. See schema.sql's own comment on report_flow_events for
    why `detail` can hold real contact values. Never raises -- logging
    must never break the actual conversation (same principle db.py's
    log_interaction() already follows)."""
    try:
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO report_flow_events (telegram_user_id, event_type, detail, created_at) VALUES (?,?,?,?)",
            (telegram_user_id, event_type, detail, platform_db.now()),
        )
    except Exception:
        logger.exception(f"_log_event failed (telegram_user_id={telegram_user_id}, event_type={event_type})")


# ---------------------------------------------------------------------------
# MILESTONE TRIGGER
# ---------------------------------------------------------------------------
async def maybe_trigger_report_milestone(query, context, telegram_user_id: int, bot_id: str):
    """Call this right after logging an MCQ answer. `bot_id` is stored in
    context.user_data so _deliver_report() (below, called much later in
    the conversation, possibly after several button taps) knows which
    bot's own dedicated sending address (telegram/config/bots.json's
    from_email) to send the report email as -- see report_delivery.py's
    resolve_from_address(), added 2026-08-11 alongside Pranav's "each bot
    has a dedicated unmonitored email account" ask. Fires the first time
    the student's count reaches OR PASSES the threshold, and never again --
    "never again" is guaranteed entirely by the milestone-row-existence
    check below, not by this count comparison.

    BUG FIXED 2026-08-11 (found via a live user report: a real account with
    35+, later confirmed 67, answered questions never got prompted, ever):
    this used to require count == MILESTONE_THRESHOLD exactly. That's only
    safe if every single answer is guaranteed to be checked and the count
    always increases by exactly 1 between checks -- true in principle here,
    but it silently breaks for any student whose count was ALREADY past 20
    at the moment this feature was deployed (exactly what happened: this
    account was already at 27 when Phase 2 went live, having tested before
    the restart) -- every later answer only pushes the count further past
    20, so an exact-equality check can never become true again. `>=` is
    correct and was always sufficient on its own."""
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    count = student_analytics.platform_wide_mcq_answered_count(conn, telegram_user_id)
    if count < MILESTONE_THRESHOLD:
        return

    existing = conn.execute(
        "SELECT status FROM student_report_milestones WHERE telegram_user_id=? AND milestone_type=?",
        (telegram_user_id, MILESTONE_20Q),
    ).fetchone()
    if existing:
        return  # already prompted (or declined/fulfilled) -- never re-nag for this milestone

    platform_db.execute_with_retry(
        conn,
        "INSERT INTO student_report_milestones (telegram_user_id, milestone_type, status, triggered_at) VALUES (?,?,?,?)",
        (telegram_user_id, MILESTONE_20Q, "prompted", platform_db.now()),
    )
    context.user_data["report_flow_bot_id"] = bot_id

    await _send_channel_picker(
        context, query.message.chat_id,
        "\U0001F389 <b>You've answered 20 questions!</b>\n\n"
        "Want a performance report -- your accuracy, chapter-wise breakdown, "
        "and time spent practicing? We'll send it wherever you like.",
    )
    _log_event(conn, telegram_user_id, "milestone_prompt_sent", detail=f"answered_count={count}")


async def _send_channel_picker(context, chat_id: int, intro_text: str):
    """Shared by the 20-question milestone prompt above and the on-demand
    trigger below -- one place renders the Telegram/Email/Both/Not now
    choice, so the two entry points can never drift into showing different
    options for the same underlying flow."""
    keyboard = [
        [InlineKeyboardButton("\U0001F4F1 Telegram", callback_data="report:telegram")],
        [InlineKeyboardButton("\U0001F4E7 Email", callback_data="report:email")],
        [InlineKeyboardButton("\U0001F4F1\U0001F4E7 Both", callback_data="report:both")],
        [InlineKeyboardButton("Not now", callback_data="report:skip")],
    ]
    await context.bot.send_message(
        chat_id=chat_id, text=intro_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------------------------------------------------------------------
# ON-DEMAND TRIGGER ("report" / "analysis" / "email" / "mail")
# ---------------------------------------------------------------------------
async def start_report_flow_on_demand(update, context, bot_id: str):
    """Entry point when a student types one of TRIGGER_PHRASES, mirroring
    profile_flow.py's start_profile_flow() shape -- ask for confirmation
    first, THEN show the same channel picker the milestone prompt uses.
    Works regardless of whether the 20-question milestone has ever fired
    for this student (a student can ask for their report at any time,
    even with very few questions answered) -- _finalize() below already
    tolerates there being no milestone row to update (a WHERE clause that
    matches zero rows is a harmless no-op), so no separate code path is
    needed for "milestone never triggered" vs. "milestone already
    fulfilled" vs. "on-demand repeat request". `bot_id` is stored the same
    way maybe_trigger_report_milestone() does, for the same reason (which
    bot's own address sends the eventual report email)."""
    context.user_data["report_flow_bot_id"] = bot_id
    keyboard = [[
        InlineKeyboardButton("Yes", callback_data="report:ondemand_yes"),
        InlineKeyboardButton("No", callback_data="report:ondemand_no"),
    ]]
    # update.effective_message not update.message -- same fix/reasoning as
    # test_flow.start_test_flow()'s own 2026-08-17 fix: this is also
    # reachable via fuzzy_trigger.py's callback-based re-dispatch, where
    # update.message is None.
    await update.effective_message.reply_text(
        "Would you like your 1LAVYA performance report -- accuracy, chapter-wise breakdown, "
        "and time spent practicing?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------------------------------------------------------------------
# CHANNEL CHOICE -> CONTACT COLLECTION
# ---------------------------------------------------------------------------
async def report_flow_callback(update, context):
    query = update.callback_query
    await query.answer()
    action, _, value = query.data.partition(":")

    if action == "report":
        if value in ("telegram", "email", "both", "skip"):
            await _handle_channel_choice(query, context, value)
        elif value in ("addemail", "addtelegram", "upsell_no"):
            await _handle_upsell_choice(query, context, value)
        elif value == "done":
            await _handle_done_choice(query, context)
        elif value in ("ondemand_yes", "ondemand_no"):
            conn = platform_db.get_connection()
            platform_db.init_schema(conn)
            if value == "ondemand_yes":
                await query.edit_message_text("Great! Where would you like it sent?")
                await _send_channel_picker(context, query.message.chat_id, "Choose a delivery channel:")
                _log_event(conn, query.from_user.id, "ondemand_confirmed")
            else:
                await query.edit_message_text("No problem -- just type \"report\" anytime you'd like it.")
                _log_event(conn, query.from_user.id, "ondemand_declined")
                # BUG FIXED 2026-08-16 (independent code review): this used
                # to be a bare text reply with no keyboard at all -- a real
                # dead end, distinct from every other decline path in this
                # module (which all route through _offer_continue_or_done()
                # or a similar CTA). Give the same "what's next" choice.
                await _offer_continue_or_done(context, query.message.chat_id)
        elif value.startswith("bcast:"):
            # A broadcast's "Get My Report" button -- see this module's own
            # docstring ("BROADCAST INTERACTION TRACKING") and
            # telegram/database/broadcast.py. value shape:
            # "bcast:<campaign_id>:<bot_id>".
            _, campaign_id_str, bcast_bot_id = value.split(":", 2)
            conn = platform_db.get_connection()
            platform_db.init_schema(conn)
            try:
                campaign_id = int(campaign_id_str)
            except ValueError:
                campaign_id = None
            if campaign_id is not None:
                matched = broadcast.log_interaction(conn, campaign_id, query.from_user.id, "report_button_tap")
                if not matched:
                    # A stale/replayed callback_data referencing a
                    # campaign_id that was never actually sent to this
                    # chat_id -- logged, never crashes the tap. The report
                    # flow itself still proceeds either way (a student
                    # tapping a button that happens to reference bad
                    # tracking data should still get their report).
                    logger.warning(f"broadcast.log_interaction: no matching delivery row for "
                                    f"campaign_id={campaign_id} telegram_user_id={query.from_user.id}")
            context.user_data["report_flow_bot_id"] = bcast_bot_id
            await query.edit_message_text("Great! Where would you like it sent?")
            await _send_channel_picker(context, query.message.chat_id, "Choose a delivery channel:")
            _log_event(conn, query.from_user.id, "ondemand_confirmed", detail=f"via broadcast campaign {campaign_id_str}")
        # "restart" (Continue Practicing) is NOT handled here -- it's a bare
        # callback_data value that matches button_router's own pattern
        # (registered separately in exam_hub_bot.py's main()), reusing the
        # exact same "reset and show the entry screen" behavior every other
        # restart button already has. No new logic needed for it in this
        # module at all.
    elif action == "reportconfirm":
        await _handle_confirm_choice(query, context, value)


def _existing_contact(conn, telegram_user_id: int) -> tuple:
    """(mobile_number, email) already on file for this chat_id, or
    (None, None) if the student row doesn't exist yet. Checked before EVER
    asking for either -- added 2026-08-11 after a real report from Pranav:
    "even after sharing the mobile number and email id once, if I again
    ask for report than it again asks for my number/email... does not the
    bot check with existing database." It didn't -- every report request
    re-asked unconditionally, regardless of what was already confirmed on
    a previous request. A student who wants to change a stored value still
    can, any time, via the "profile" menu (profile_flow.py) -- this flow
    now only asks when something is genuinely missing."""
    row = conn.execute(
        "SELECT mobile_number, email FROM students WHERE telegram_user_id=?", (telegram_user_id,)
    ).fetchone()
    return (row[0], row[1]) if row else (None, None)


async def _handle_channel_choice(query, context, choice: str):
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    telegram_user_id = query.from_user.id

    if choice == "skip":
        platform_db.execute_with_retry(
            conn,
            "UPDATE student_report_milestones SET status='declined', resolved_at=? "
            "WHERE telegram_user_id=? AND milestone_type=?",
            (platform_db.now(), telegram_user_id, MILESTONE_20Q),
        )
        await query.edit_message_text("No problem -- you can always ask your faculty for this later. Keep practicing!")
        _log_event(conn, telegram_user_id, "declined")
        # BUG FIXED 2026-08-16 (independent code review): same dead-end
        # class as the "ondemand_no" branch above -- this used to end the
        # conversation with plain text and zero buttons.
        await _offer_continue_or_done(context, query.message.chat_id)
        return

    context.user_data["report_flow_channels"] = choice  # 'telegram' | 'email' | 'both'
    _log_event(conn, telegram_user_id, "channel_chosen", detail=choice)

    existing_mobile, existing_email = _existing_contact(conn, telegram_user_id)
    needs_mobile = choice in ("telegram", "both") and not existing_mobile
    needs_email = choice in ("email", "both") and not existing_email

    if not needs_mobile and not needs_email:
        # Everything this choice needs is already on file -- skip straight
        # to delivery, exactly Pranav's ask ("directly send and then
        # confirm its went").
        context.user_data["report_flow_state"] = None
        await query.edit_message_text("Using your saved contact info -- generating your report...")
        _log_event(conn, telegram_user_id, "used_existing_contact_info", detail=choice)
        await _finalize(query, context, telegram_user_id, choice)
        return

    if needs_mobile:
        context.user_data["report_flow_state"] = AWAITING_MOBILE
        await query.edit_message_text(
            "Please share the mobile number where you'd like to receive updates "
            "(just type it, e.g. 9876543210).\n\n"
            "<i>We use this only to identify you for reports -- no OTP, no calls.</i>",
            parse_mode="HTML",
        )
    else:
        # needs_email is the only thing left -- either choice=="email", or
        # choice=="both" and mobile was ALREADY on file (skipped above).
        context.user_data["report_flow_state"] = AWAITING_EMAIL
        await query.edit_message_text("Please type the email address where you'd like your report sent.")


async def handle_contact_text_input(update, context) -> bool:
    """Returns True if this message was consumed by the report flow (caller
    should not process it further), False if the flow isn't active."""
    state = context.user_data.get("report_flow_state")
    if state not in (AWAITING_MOBILE, AWAITING_EMAIL):
        return False

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    telegram_user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if state == AWAITING_MOBILE:
        normalized = _normalize_mobile(text)
        if not normalized:
            await update.message.reply_text(
                "That doesn't look like a valid 10-digit mobile number -- please try again (e.g. 9876543210)."
            )
            _log_event(conn, telegram_user_id, "mobile_rejected", detail=text)
            return True
        context.user_data["report_flow_pending_mobile"] = normalized
        context.user_data["report_flow_state"] = CONFIRMING_MOBILE
        keyboard = [[
            InlineKeyboardButton("✅ Confirm", callback_data="reportconfirm:yes"),
            InlineKeyboardButton("✏️ Re-type", callback_data="reportconfirm:retry"),
        ]]
        await update.message.reply_text(
            f"Is this correct? <b>{normalized}</b>", parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        _log_event(conn, telegram_user_id, "mobile_collected_pending_confirm", detail=normalized)
        return True

    if state == AWAITING_EMAIL:
        if not _valid_email(text):
            await update.message.reply_text("That doesn't look like a valid email address -- please try again.")
            _log_event(conn, telegram_user_id, "email_rejected", detail=text)
            return True
        context.user_data["report_flow_pending_email"] = text
        context.user_data["report_flow_state"] = CONFIRMING_EMAIL
        keyboard = [[
            InlineKeyboardButton("✅ Confirm", callback_data="reportconfirm:yes"),
            InlineKeyboardButton("✏️ Re-type", callback_data="reportconfirm:retry"),
        ]]
        await update.message.reply_text(
            f"Is this correct? <b>{text}</b>", parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        _log_event(conn, telegram_user_id, "email_collected_pending_confirm", detail=text)
        return True

    return False


async def _handle_confirm_choice(query, context, value: str):
    state = context.user_data.get("report_flow_state")
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    telegram_user_id = query.from_user.id

    if value == "retry":
        if state == CONFIRMING_MOBILE:
            context.user_data["report_flow_state"] = AWAITING_MOBILE
            await query.edit_message_text("No problem -- please type your mobile number again.")
            _log_event(conn, telegram_user_id, "mobile_retry")
        elif state == CONFIRMING_EMAIL:
            context.user_data["report_flow_state"] = AWAITING_EMAIL
            await query.edit_message_text("No problem -- please type your email address again.")
            _log_event(conn, telegram_user_id, "email_retry")
        return

    # value == "yes"
    channels = context.user_data.get("report_flow_channels")
    is_upsell = context.user_data.pop("report_flow_upsell", False)

    if state == CONFIRMING_MOBILE:
        mobile = context.user_data.pop("report_flow_pending_mobile", None)
        platform_db.execute_with_retry(
            conn, "UPDATE students SET mobile_number=?, mobile_verification_method='echo_confirm' WHERE telegram_user_id=?",
            (mobile, telegram_user_id),
        )
        _log_event(conn, telegram_user_id, "mobile_confirmed", detail=mobile)

        if is_upsell:
            # Post-delivery upsell ("addtelegram") -- send ONLY the newly-
            # added channel, never re-run the original delivery.
            context.user_data["report_flow_state"] = None
            await query.edit_message_text("Got it! Sending your report on Telegram now...")
            await _deliver_report(conn, context, query.message.chat_id, telegram_user_id, {"telegram"})
            await _offer_continue_or_done(context, query.message.chat_id)
            return

        if channels == "both":
            _, existing_email = _existing_contact(conn, telegram_user_id)
            if existing_email:
                # Email side of "both" is already on file too -- don't ask
                # for it a second time just because mobile needed a fresh
                # confirm this round.
                context.user_data["report_flow_state"] = None
                await query.edit_message_text("Got it! Using your saved email too -- generating your report...")
                await _finalize(query, context, telegram_user_id, channels)
                return
            context.user_data["report_flow_state"] = AWAITING_EMAIL
            await query.edit_message_text("Got it! Now please type the email address where you'd like your report sent.")
            return
        context.user_data["report_flow_state"] = None
        await query.edit_message_text("Got it! Generating your report...")
        await _finalize(query, context, telegram_user_id, channels)
        return

    if state == CONFIRMING_EMAIL:
        email = context.user_data.pop("report_flow_pending_email", None)
        platform_db.execute_with_retry(
            conn, "UPDATE students SET email=?, email_verification_method='echo_confirm' WHERE telegram_user_id=?",
            (email, telegram_user_id),
        )
        _log_event(conn, telegram_user_id, "email_confirmed", detail=email)

        if is_upsell:
            # Post-delivery upsell ("addemail") -- send ONLY the newly-
            # added channel, never re-run the original delivery.
            context.user_data["report_flow_state"] = None
            await query.edit_message_text("Got it! Sending your report by email now...")
            await _deliver_report(conn, context, query.message.chat_id, telegram_user_id, {"email"})
            await _offer_continue_or_done(context, query.message.chat_id)
            return

        context.user_data["report_flow_state"] = None
        await query.edit_message_text("Got it! Generating your report...")
        await _finalize(query, context, telegram_user_id, channels)
        return


async def _deliver_report(conn, context, chat_id: int, telegram_user_id: int, channels_to_send: set) -> tuple:
    """Generates the PDF once and sends it through exactly the channels in
    `channels_to_send` ({"email"}, {"telegram"}, or both) -- pulled out of
    the old _finalize() so the post-delivery upsell (below) can send
    through ONE additional channel later without re-sending the channel(s)
    already delivered. Returns (email_status, telegram_status, error_parts);
    never raises -- every failure is caught, logged, and reported back to
    the student honestly."""
    try:
        pdf_bytes = generate_student_report.build_report_pdf(conn, telegram_user_id)
        _log_event(conn, telegram_user_id, "report_generated", detail=f"{len(pdf_bytes)} bytes")
    except Exception as e:
        logger.exception(f"Report generation failed for telegram_user_id={telegram_user_id}")
        report_delivery.log_report_delivery(conn, telegram_user_id, "All-time", ",".join(sorted(channels_to_send)),
                                             error_detail=f"generation failed: {e}")
        _log_event(conn, telegram_user_id, "report_generation_failed", detail=str(e))
        await context.bot.send_message(chat_id=chat_id, text="Sorry, something went wrong generating your report. We'll look into it.")
        return None, None, [f"generation: {e}"]

    data_for_name = student_analytics.fetch_student_report_data(conn, telegram_user_id)
    display_name = generate_student_report.display_name_for_student(data_for_name)

    email_status, telegram_status, error_parts = None, None, []

    if "email" in channels_to_send:
        row = conn.execute("SELECT email FROM students WHERE telegram_user_id=?", (telegram_user_id,)).fetchone()
        bot_id = context.user_data.get("report_flow_bot_id")
        try:
            report_delivery.send_report_email(bot_id, row[0], pdf_bytes, display_name, "All-time")
            email_status = "sent"
            # Pranav's ask, 2026-08-11: tell the student explicitly to check
            # Spam/Junk and mark it "Not Spam" -- a first email from a new
            # sender routinely lands there, and without this nudge a student
            # who only checks Inbox would conclude nothing was ever sent.
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "\U0001F4E7 <b>Report sent to your email!</b>\n\n"
                    "If you don't see it in your Inbox within a few minutes, please check your "
                    "<b>Spam/Junk folder</b> too -- and mark it <b>\"Not Spam\"</b> there, so future "
                    "reports land directly in your Inbox."
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            email_status = "failed"
            error_parts.append(f"email: {e}")
            logger.exception(f"Report email failed for telegram_user_id={telegram_user_id}")

    if "telegram" in channels_to_send:
        # ONE retry, short backoff, ONLY for the transient network-error
        # class (TimedOut/NetworkError) -- found via a real live incident
        # 2026-08-11 (csarunchouhan bot: send_document hit a genuine
        # httpx.ReadTimeout on a ~32KB file, a one-off network blip, not a
        # code bug). Any other exception (bad chat_id, file too large,
        # etc.) is a real, non-transient failure -- retrying it would just
        # waste time before reporting the same failure, so those still
        # fail immediately on the first attempt.
        last_exc = None
        for attempt in range(2):
            try:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=pdf_bytes,
                    filename="1LAVYA_Performance_Report.pdf",
                    caption="\U0001F4CA Here's your performance report -- <i>Powered by 1LAVYA</i>",
                    parse_mode="HTML",
                )
                telegram_status = "sent"
                last_exc = None
                break
            except (TimedOut, NetworkError) as e:
                last_exc = e
                if attempt == 0:
                    logger.warning(f"Report Telegram delivery timed out (attempt 1/2) for "
                                    f"telegram_user_id={telegram_user_id} -- retrying once: {e}")
                    await asyncio.sleep(2)
            except Exception as e:
                last_exc = e
                break

        if last_exc is not None:
            telegram_status = "failed"
            error_parts.append(f"telegram: {last_exc}")
            # exc_info=last_exc (not logger.exception()) -- we're outside
            # the except block that actually caught it by this point (the
            # retry loop above), so sys.exc_info() would no longer point at
            # the real traceback; passing the caught exception object
            # explicitly is what actually attaches it correctly here.
            logger.error(f"Report Telegram delivery failed for telegram_user_id={telegram_user_id}", exc_info=last_exc)

    report_delivery.log_report_delivery(
        conn, telegram_user_id, "All-time", ",".join(sorted(channels_to_send)),
        email_status=email_status, telegram_status=telegram_status,
        error_detail="; ".join(error_parts) or None,
    )
    _log_event(conn, telegram_user_id, "report_delivery_attempted",
               detail=f"channels={sorted(channels_to_send)} email_status={email_status} telegram_status={telegram_status}")

    if error_parts:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Your report was generated, but delivery to one or more channels failed -- we'll follow up.",
        )

    return email_status, telegram_status, error_parts


async def _finalize(query, context, telegram_user_id: int, channels: str):
    """The ORIGINAL 20-question-milestone delivery -- marks the milestone
    fulfilled, delivers through every originally-chosen channel, then
    offers the post-delivery upsell (2026-08-11, Pranav's ask: "it should
    have asked me whether I need report in email as well" after choosing
    Telegram-only) -- never just ends silently."""
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    chat_id = query.message.chat_id

    platform_db.execute_with_retry(
        conn,
        "UPDATE students SET report_channel_preference=? WHERE telegram_user_id=?",
        (channels, telegram_user_id),
    )
    platform_db.execute_with_retry(
        conn,
        "UPDATE student_report_milestones SET status='fulfilled', resolved_at=? "
        "WHERE telegram_user_id=? AND milestone_type=?",
        (platform_db.now(), telegram_user_id, MILESTONE_20Q),
    )

    channels_to_send = {"email", "telegram"} if channels == "both" else {channels}
    _, _, error_parts = await _deliver_report(conn, context, chat_id, telegram_user_id, channels_to_send)
    if error_parts and error_parts[0].startswith("generation:"):
        return  # already told the student generation failed -- nothing to offer next

    await _offer_upsell_or_wrapup(context, chat_id, telegram_user_id, channels)


# ---------------------------------------------------------------------------
# POST-DELIVERY: offer the missing channel, then continue/done
# ---------------------------------------------------------------------------
async def _offer_upsell_or_wrapup(context, chat_id: int, telegram_user_id: int, channels: str):
    """channels is what was ORIGINALLY chosen at the milestone prompt. If
    it was "both", the student already has everything -- skip straight to
    the continue/done question. Otherwise offer the ONE channel they didn't
    pick (Pranav's ask, 2026-08-11) before that same final question."""
    if channels == "both":
        await _offer_continue_or_done(context, chat_id)
        return

    if channels == "telegram":
        keyboard = [
            [InlineKeyboardButton("\U0001F4E7 Yes, email it too", callback_data="report:addemail")],
            [InlineKeyboardButton("No thanks", callback_data="report:upsell_no")],
        ]
        text = "Would you also like this report by <b>email</b>?"
    else:  # "email"
        keyboard = [
            [InlineKeyboardButton("\U0001F4F1 Yes, Telegram too", callback_data="report:addtelegram")],
            [InlineKeyboardButton("No thanks", callback_data="report:upsell_no")],
        ]
        text = "Would you also like this report on <b>Telegram</b>?"

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def _handle_upsell_choice(query, context, value: str):
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    telegram_user_id = query.from_user.id

    if value == "upsell_no":
        await query.edit_message_text("No problem!")
        await _offer_continue_or_done(context, query.message.chat_id)
        return

    existing_mobile, existing_email = _existing_contact(conn, telegram_user_id)

    if value == "addemail" and existing_email:
        # Already have an email on file (e.g. set via the "profile" menu
        # since the original choice, or from an earlier report request) --
        # don't ask again, just send.
        await query.edit_message_text("Using your saved email -- sending your report now...")
        await _deliver_report(conn, context, query.message.chat_id, telegram_user_id, {"email"})
        await _offer_continue_or_done(context, query.message.chat_id)
        return
    if value == "addtelegram" and existing_mobile:
        await query.edit_message_text("Using your saved mobile number -- sending your report now...")
        await _deliver_report(conn, context, query.message.chat_id, telegram_user_id, {"telegram"})
        await _offer_continue_or_done(context, query.message.chat_id)
        return

    context.user_data["report_flow_upsell"] = True   # tells the confirm-step below to send ONE new channel, not re-run the full original delivery
    if value == "addemail":
        context.user_data["report_flow_state"] = AWAITING_EMAIL
        await query.edit_message_text("Great! Please type the email address where you'd like your report sent.")
    else:  # addtelegram
        context.user_data["report_flow_state"] = AWAITING_MOBILE
        await query.edit_message_text(
            "Great! Please share your mobile number as consent to receive this on Telegram "
            "(just type it, e.g. 9876543210).\n\n"
            "<i>Same rule as before -- no OTP, no calls, just your consent to send it here.</i>",
            parse_mode="HTML",
        )


async def _offer_continue_or_done(context, chat_id: int):
    keyboard = [
        # "restart" (bare, no colon) -- deliberately the SAME callback_data
        # button_router's own "Start Over"/entry-screen-reset buttons
        # already use, matched by its own registered pattern. Reuses the
        # existing, already-tested reset flow instead of reinventing it.
        [InlineKeyboardButton("▶️ Continue Practicing", callback_data="restart")],
        [InlineKeyboardButton("✅ I'm Done", callback_data="report:done")],
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text="Would you like to continue practicing, or are you done for now?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _handle_done_choice(query, context):
    await query.edit_message_text("Awesome work today! Come back anytime to keep practicing. \U0001F44B")
