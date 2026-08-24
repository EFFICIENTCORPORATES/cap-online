"""
1LAVYA Faculty Bot -- unified Study Hub + Exam Practice Hub (added 2026-08-10)
--------------------------------------------------------------------------
1LAVYA's flagship product is 3 SEPARATE Telegram bots (Study Hub, Exam Hub,
MyFiles Hub -- each its own registered token). A white-label FACULTY only
gets ONE registered bot token, so their single bot has to do everything --
this script composes study_hub_bot.py + exam_hub_bot.py's already-tenant-
aware logic (see both files' own 2026-08-09/10 tenant-aware rewrites) under
one /start, rather than duplicating either bot's logic.

Flow:
    /start (or "reset" / a standalone "Hi"/"Hey"/...) -> top-level picker:
        "Study Hub" -> study_hub_bot.py's own entry screen (Browse / free-
                        text search), completely unchanged
        "Exam Practice Hub" -> exam_hub_bot.py's own Mode -> Course ->
                        Level -> Subject -> Exam Type -> Year -> Chapter ->
                        question flow (Mode-first as of the 2026-08-12
                        rewrite -- see that file's resolve_entry()),
                        completely unchanged here
    From INSIDE Study Hub, the existing "Main Menu" button (added to
    study_hub_bot.py's post-download prompt) and any reset trigger now land
    back on THIS bot's top-level picker, not Study Hub's own screen -- see
    the monkeypatch note below for exactly how, with zero duplicated logic.

Nothing in study_hub_bot.py or exam_hub_bot.py's own callback_data schemes
collides (verified: sh uses browse/cat/crs/lvl/subj/pt/file/mainmenu; eh
uses course/level/mode/subject/type/year/chapter/answer/pdf/next/mcqopt/
restart -- "subj" vs "subject" are different literal tokens, regex-checked,
not just eyeballed) -- both modules' existing handlers are registered
directly on ONE Application, unmodified.

SETUP (do this before running):
1. Both study_hub_bot.py's and exam_hub_bot.py's own dependencies:
   pip install python-telegram-bot rapidfuzz openpyxl pandas beautifulsoup4
   xhtml2pdf python-dotenv
2. This script only makes sense for a bot that has BOTH Study content
   (content_scope) AND Exam content (exam_content) configured for its
   tenant in telegram/config/tenants.json -- e.g. "csarunchouhan". A
   Study-Hub-only or Exam-Hub-only faculty should just run
   study_hub_bot.py or exam_hub_bot.py directly instead, not this script.
3. Set BOT_ID before launching, same as the other two bots (also accepts
   the older TENANT_ID name as a fallback -- see bots.json's own note on
   when that still works):
       $env:BOT_ID = "csarunchouhan"; python telegram/bots/faculty_bot.py
4. Run and keep the terminal open, same as any other bot here.
"""

import os
import sys
import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import study_hub_bot as sh
import exam_hub_bot as eh
from telegram_safety import safe_edit_message_text  # noqa: E402 -- 2026-08-18, see that module's own docstring
import cancel_utils  # noqa: E402 -- telegram/bots/cancel_utils.py, universal "get me out of this" escape hatch (2026-08-16)
import fuzzy_trigger  # noqa: E402 -- telegram/bots/fuzzy_trigger.py, "did you mean X?" typo confirmation (2026-08-16)
import activity_logger  # noqa: E402 -- telegram/bots/activity_logger.py, the fine-grained activity log + correlation IDs (2026-08-17)
import rate_limiter  # noqa: E402 -- telegram/bots/rate_limiter.py, per-user flood/abuse controls (2026-08-24, SECURITY.md Phase 1)
import callback_registry  # noqa: E402 -- telegram/bots/callback_registry.py, central callback_data route registry (2026-08-24, SECURITY.md Phase 2)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402 -- must follow the sys.path.insert() above

# NOTE: `import study_hub_bot as sh` above already ran ITS OWN
# logging.basicConfig() (correlation-formatted, httpx silenced) at import
# time -- Python's basicConfig() only configures the root logger the FIRST
# time it's called in a process, so this call is a harmless no-op today.
# Kept explicit anyway (not relying on import order staying exactly as-is)
# -- same reasoning install_correlation_filter() below is called again
# even though sh's own import already installed one on the root logger.
logging.basicConfig(format=activity_logger.LOG_FORMAT_WITH_CORRELATION, level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
activity_logger.install_correlation_filter()
logger = logging.getLogger(__name__)

if sh.BOT_ID != eh.BOT_ID:
    # Both modules independently resolve BOT_ID at their own import time --
    # they should always agree since it's one process, one environment. A
    # mismatch here would mean a real bug (e.g. one module cached an import
    # from a previous run), not a config problem -- fail loudly rather than
    # silently serve two different tenants' data.
    raise SystemExit(f"BOT_ID mismatch: study_hub_bot={sh.BOT_ID!r} vs exam_hub_bot={eh.BOT_ID!r}")

BOT_ID = sh.BOT_ID
TENANT_ID = sh.TENANT_ID
TENANT = sh.TENANT
BOT_CONFIG = sh.BOT_CONFIG
BOT_TOKEN = sh.BOT_TOKEN

# Capture Study Hub's OWN entry screen (welcome text + "Browse" button)
# before patching the module -- this is what "Study Hub" in the top-level
# picker below shows.
_study_hub_own_entry = sh.welcome_text_and_keyboard


def hub_picker_text_and_keyboard():
    """The top-level picker this script adds. No brand footer -- this is a
    welcome/menu screen, not an answer or a PDF (Pranav, 2026-08-10)."""
    opening = TENANT.get("welcome_message") or "*Welcome!* \U0001F44B"
    text = f"{opening}\n\nWhat would you like to do?"
    keyboard = [
        [InlineKeyboardButton("\U0001F4D8 Study Hub", callback_data="hub:study")],
        [InlineKeyboardButton("\U0001F4DD Exam Practice Hub", callback_data="hub:exam")],
    ]
    return text, InlineKeyboardMarkup(keyboard)


# Monkeypatch: study_hub_bot.start() and its "mainmenu" callback branch both
# call welcome_text_and_keyboard() BY NAME, resolved from sh's own module
# globals at call time -- reassigning the name here means every place
# inside study_hub_bot.py that already resets "to the top" (the /start
# command, a standalone greeting/"reset" via RESET_TRIGGER_RE, and the
# post-download "Main Menu" button) now correctly lands on THIS bot's
# top-level picker instead of Study Hub's own screen, with no changes to
# study_hub_bot.py itself. Tapping "Study Hub" from the picker (below)
# calls the captured _study_hub_own_entry() instead, so Study Hub's own
# screen is still reachable -- it's just no longer where a reset goes.
sh.welcome_text_and_keyboard = hub_picker_text_and_keyboard


async def hub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":", 1)[1]

    if choice == "study":
        context.user_data.clear()
        text, markup = _study_hub_own_entry()
        await safe_edit_message_text(query, text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    elif choice == "exam":
        context.user_data.clear()
        user = query.from_user
        eh.db_upsert_student(user)
        # BUG FIXED 2026-08-17 (real support tickets: students "asked for
        # payment" despite never having attempted any real questions).
        # eh.db_ensure_wallet() -- which BOTH provisions the wallet identity
        # AND grants the one-time 1000-credit signup bonus -- used to be
        # called only from exam_hub_bot.py's own start()/"restart" handlers.
        # This unified bot's "Exam Practice Hub" tap is a THIRD entry point
        # into the exact same wallet-gated flow, but only ever called
        # ensure_wallet_identity() (creates the username) -- never
        # grant_signup_bonus() -- so any student whose first-ever platform
        # touch was tapping this button got a real wallet identity with a
        # PERMANENT ZERO balance, and their very first MCQ/descriptive
        # question hit the "balance isn't enough" wall instantly. Confirmed
        # against the live DB: 5 real students on THIS bot (csarunchouhan --
        # the only tenant that runs faculty_bot.py) had a student_profiles
        # row with zero wallet_ledger rows at all, all with first_seen_at
        # after the 2026-08-16 billing rollout. db_ensure_wallet() is
        # idempotent (grant_signup_bonus() is a safe no-op if already
        # granted, e.g. via a plain /start on a bot that already grants),
        # so calling it here is always safe, never a double-grant.
        welcome_bonus_text = eh.db_ensure_wallet(user)
        # 2026-08-16: same stash exam_hub_bot.py's own start()/"restart" do,
        # needed by resolve_entry()'s profile-based Course/Level auto-fill.
        context.user_data["lavya_username"], _ = eh.identity.ensure_wallet_identity(eh.DB_CONN, user)
        context.user_data["session_id"] = eh.db_start_session(user.id)
        # resolve_entry() (renamed from entry_screen_and_updates() in the
        # 2026-08-12 Mode-first rewrite) auto-skips Course/Level/Subject
        # when this tenant's content leaves only one real option at that
        # step -- see its own docstring in exam_hub_bot.py.
        text, markup, updates = eh.resolve_entry(context)
        if updates:
            context.user_data.update(updates)
            eh.db_update_session(context.user_data["session_id"], **updates)
        if welcome_bonus_text:
            # Sent as its own message ahead of the menu, same as
            # exam_hub_bot.py's own start() -- never buried inside the
            # Markdown-formatted menu text.
            await context.bot.send_message(chat_id=query.message.chat_id, text=welcome_bonus_text, parse_mode=ParseMode.HTML)
        await safe_edit_message_text(query, text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


def _fuzzy_dispatch():
    """Shared by text_router() (detection) and _fuzzy_trigger_callback()
    (resolution) -- must be the SAME mapping both times, see
    fuzzy_trigger.py's own docstring."""
    return {
        "profile": lambda u, c: eh.profile_flow.start_profile_flow(u, c, BOT_ID),
        "wallet": lambda u, c: eh.wallet_flow.show_wallet_status(u, c, eh),
        "recharge": lambda u, c: eh.wallet_flow.start_recharge_flow(u, c, eh),
        "test": lambda u, c: eh.test_flow.start_test_flow(u, c, BOT_ID, eh),
        "upload": lambda u, c: eh.test_flow.start_upload_pick(u, c, eh),
        "report": lambda u, c: eh.report_flow.start_report_flow_on_demand(u, c, BOT_ID),
    }


async def _search_original_text(update, context, original_text):
    """fuzzy_trigger.py's on_decline callback for this bot -- "No, search
    instead" on the "did you mean X?" prompt means run Study Hub's own
    search on the ORIGINAL typed text, not the matched trigger phrase."""
    update.message.text = original_text
    await sh.free_text_search(update, context)


async def _fuzzy_trigger_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await fuzzy_trigger.handle_confirm_callback(update, context, _fuzzy_dispatch(), on_decline=_search_original_text)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Free text in this unified bot normally means Study Hub's own
    fuzzy-search (sh.free_text_search) -- but every awaiting-state check
    below has to run first, most-specific first, same "check the more
    specific state first" rule as exam_hub_bot.py's own text_router.

    BUG FIXED 2026-08-16 (independent code review): this router never
    checked test_flow's/wallet_flow's own awaiting-states or trigger
    phrases at all -- meaning Test Mode and wallet status/recharge were
    completely unreachable through this unified bot (the ONE Telegram bot
    a single-token faculty like CS Arun Chouhan actually runs: no "Start
    Test" flow, no "wallet"/"recharge" trigger, and typing "done"/"pass"
    mid-upload fell straight through to Study Hub's search instead of
    completing the upload). Mirrored here now, same ordering as
    exam_hub_bot.py's own text_router. Also added: a universal cancel
    phrase (cancel_utils.py) and a "did you mean X?" confirmation for a
    near-miss on any of the trigger words below (fuzzy_trigger.py) --
    both found missing by the same review."""
    text = (update.message.text or "").strip()

    if cancel_utils.matches_cancel(text):
        if cancel_utils.cancel_all_flows(context):
            await update.message.reply_text("❌ Cancelled — you can start fresh anytime.")
            return
        # nothing was active -- fall through to normal handling, same
        # reasoning cancel_utils.cancel_all_flows()'s own docstring gives.

    if eh.test_flow.is_collecting_upload(context):
        if await eh.test_flow.handle_upload_text_input(update, context, eh):
            return
    if eh.wallet_flow.is_awaiting_custom_amount(context):
        if await eh.wallet_flow.handle_custom_amount_text(update, context, eh):
            return
    if eh.mcq_issue_flow.is_awaiting_text_input(context):
        if await eh.mcq_issue_flow.handle_issue_text_input(update, context):
            return
    if eh.profile_flow.is_awaiting_text_input(context):
        if await eh.profile_flow.handle_profile_text_input(update, context):
            return
    if eh.profile_flow.matches_trigger(text):
        await eh.profile_flow.start_profile_flow(update, context, BOT_ID)
        return
    if eh.wallet_flow.matches_wallet_trigger(text):
        await eh.wallet_flow.show_wallet_status(update, context, eh)
        return
    if eh.wallet_flow.matches_recharge_trigger(text):
        await eh.wallet_flow.start_recharge_flow(update, context, eh)
        return
    if eh.test_flow.matches_trigger(text):
        await eh.test_flow.start_test_flow(update, context, BOT_ID, eh)
        return
    if eh.test_flow.matches_upload_trigger(text):
        await eh.test_flow.start_upload_pick(update, context, eh)
        return
    if eh.report_flow.matches_trigger(text) and not eh.report_flow.is_awaiting_text_input(context):
        await eh.report_flow.start_report_flow_on_demand(update, context, BOT_ID)
        return
    if eh.report_flow.is_awaiting_text_input(context):
        if await eh.report_flow.handle_contact_text_input(update, context):
            return

    # Nothing matched exactly -- check for a plausible TYPO of one of the
    # trigger phrases above before falling through to Study Hub's search
    # (see fuzzy_trigger.py's own docstring).
    if await fuzzy_trigger.maybe_confirm(update, context, _fuzzy_dispatch()):
        return

    await sh.free_text_search(update, context)


async def _test_flow_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await eh.test_flow.test_flow_callback(update, context, BOT_ID, eh)


async def _wallet_flow_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await eh.wallet_flow.wallet_flow_callback(update, context, BOT_ID, eh)


async def _upload_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await eh.test_flow.handle_upload_photo_or_document(update, context, eh)


def main():
    if not BOT_TOKEN:
        env_name = BOT_CONFIG.get("bot_token_env")
        raise SystemExit(
            f"No bot token found for bot_id '{BOT_ID}'. "
            f"Set the {env_name} variable in telegram/.env "
            f"(see telegram/config/bots.README.md)."
        )

    # study_hub_bot/exam_hub_bot each already opened + initialized their own
    # DB_CONN at import time (both point at the same shared platform.db --
    # see telegram/database/db.py); nothing extra to init here.

    app = Application.builder().token(BOT_TOKEN).build()
    platform_db.schedule_heartbeat(app, BOT_ID)

    # 2026-08-17: every handler below wrapped with activity_logger.
    # log_activity() at registration time only -- see
    # telegram/LOGGING-ARCHITECTURE.md §3. Deliberately passes THIS file's
    # own BOT_ID (e.g. "csarunchouhan"), never eh's/sh's own -- log_activity()
    # takes bot_id as an explicit argument for exactly this reason, so a
    # handler reused from exam_hub_bot.py/study_hub_bot.py still logs under
    # the bot that's actually running it.
    #
    # sh.start is patched (see above) to show the top-level picker, not
    # Study Hub's own screen -- exactly the desired /start and /reset
    # behavior for this unified bot.
    # 2026-08-24: rate_limiter.rate_limited() wraps OUTERMOST around every
    # handler below (see that module's own docstring for why) -- a
    # "general" flood cap, SECURITY.md §4.1.
    def _rl(kind, func):
        return rate_limiter.rate_limited("general", BOT_ID)(activity_logger.log_activity(kind, BOT_ID)(func))

    # 2026-08-24: callback_registry.CallbackRegistry -- a drop-in
    # replacement for constructing CallbackQueryHandler directly, so
    # registry.validate() (below, right before run_polling()) can catch
    # exactly the collision bug class the comment a few lines down
    # describes at STARTUP, not via a live user report.
    registry = callback_registry.CallbackRegistry(BOT_ID)

    app.add_handler(CommandHandler("start", _rl("command", sh.start)))
    app.add_handler(CommandHandler("reset", _rl("command", sh.start)))
    app.add_handler(registry.callback_handler(_rl("callback", hub_callback), pattern=r"^hub:", label="hub_callback"))
    app.add_handler(registry.callback_handler(_rl("callback", sh.browse_callback), pattern=r"^(browse|cat|crs|lvl|subj|pt|file|mainmenu):", label="sh.browse_callback"))
    # (:|$) not a literal trailing ":" -- "next" and "restart" are bare
    # callback_data values with NO colon (see exam_hub_bot.py's next_step_rows()
    # and its "Start Over" buttons), unlike every other action here which is
    # always "action:value". A literal ":" here silently dropped every tap on
    # "Next Question"/"I'm Done" in this unified bot specifically -- no handler
    # matched, so python-telegram-bot never even called query.answer(), and the
    # button just sat there with no response (query.answer() lives inside
    # button_router() itself, so a query that never reaches it is never
    # acknowledged at all). Standalone exam_hub_bot.py never had this bug --
    # its own CallbackQueryHandler(button_router) has no pattern restriction.
    # Found 2026-08-10 via a live user report on the csarunchouhan bot.
    app.add_handler(registry.callback_handler(_rl("callback", eh.button_router), pattern=r"^(course|level|mode|subject|type|year|chapter|answer|pdf|next|mcqopt|restart|reportissue|imdone|sessprofile)(:|$)", label="eh.button_router"))
    # 2026-08-11: report_flow's callbacks, same as exam_hub_bot.py's own
    # standalone registration -- eh.report_flow is exam_hub_bot.py's own
    # already-imported module reference, not a fresh import here.
    app.add_handler(registry.callback_handler(_rl("callback", eh.report_flow.report_flow_callback), pattern=r"^(report|reportconfirm):", label="eh.report_flow_callback"))
    # eh.profile_flow is exam_hub_bot.py's own already-imported module
    # reference, same reuse pattern as eh.report_flow directly above.
    app.add_handler(registry.callback_handler(_rl("callback", eh.profile_flow.profile_flow_callback), pattern=r"^(profile|profileconfirm):", label="eh.profile_flow_callback"))
    # eh.mcq_issue_flow, same reuse pattern, added 2026-08-13.
    app.add_handler(registry.callback_handler(_rl("callback", eh.mcq_issue_flow.mcq_issue_flow_callback), pattern=r"^(issuecat|issuecancel)(:|$)", label="eh.mcq_issue_flow_callback"))
    # 2026-08-16 (independent code review): Test Mode + wallet callbacks --
    # previously missing entirely from this bot, see text_router()'s own
    # docstring for the full bug.
    app.add_handler(registry.callback_handler(_rl("callback", _test_flow_callback_wrapper), pattern=r"^(testflow|tnav|topt|tgo|tupload|tgrace)(:|$)", label="_test_flow_callback_wrapper"))
    app.add_handler(registry.callback_handler(_rl("callback", _wallet_flow_callback_wrapper), pattern=r"^walletrc(:|$)", label="_wallet_flow_callback_wrapper"))
    app.add_handler(registry.callback_handler(_rl("callback", _fuzzy_trigger_callback), pattern=r"^fuzzytrigger:", label="_fuzzy_trigger_callback"))
    # Photo/document uploads -- only meaningful during Test Mode's upload
    # collection; handle_upload_photo_or_document() is a no-op (returns
    # False) when no upload is actively being collected, so this handler
    # is safe to register unconditionally, same as exam_hub_bot.py's own.
    app.add_handler(MessageHandler((filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND, _rl("photo", _upload_router)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _rl("text", text_router)))
    registry.validate()

    # Sweep any in-progress tests/pending recharges/pending access requests
    # from before this restart and re-arm their jobs -- job_queue jobs do
    # NOT survive a process restart. Must happen AFTER the Application (and
    # its job_queue) is built, before run_polling() starts serving real
    # traffic. Same calls exam_hub_bot.py's own main() already makes --
    # previously missing here entirely (another symptom of the same gap
    # text_router()'s docstring describes).
    eh.test_flow.rearm_pending_test_jobs(app, eh)
    eh.wallet_flow.rearm_pending_recharge_jobs(app, eh)
    eh.profile_flow.rearm_pending_access_requests(app, BOT_ID)

    logger.info(f"Faculty Bot starting for bot_id '{BOT_ID}' (tenant '{TENANT_ID}', {TENANT['display_name']})...")
    app.run_polling()


if __name__ == "__main__":
    main()
