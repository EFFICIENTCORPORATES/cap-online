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
        "Exam Practice Hub" -> exam_hub_bot.py's own Course -> Level ->
                        Mode -> Exam Type -> Year -> Chapter -> question
                        flow, completely unchanged
    From INSIDE Study Hub, the existing "Main Menu" button (added to
    study_hub_bot.py's post-download prompt) and any reset trigger now land
    back on THIS bot's top-level picker, not Study Hub's own screen -- see
    the monkeypatch note below for exactly how, with zero duplicated logic.

Nothing in study_hub_bot.py or exam_hub_bot.py's own callback_data schemes
collides (verified: sh uses browse/cat/crs/lvl/subj/pt/file/mainmenu; eh
uses course/level/mode/type/year/chapter/answer/pdf/next/mcqopt/restart) --
both modules' existing handlers are registered directly on ONE Application,
unmodified.

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402 -- must follow the sys.path.insert() above

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
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
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    elif choice == "exam":
        context.user_data.clear()
        user = query.from_user
        eh.db_upsert_student(user)
        context.user_data["session_id"] = eh.db_start_session(user.id)
        # entry_screen_and_updates() auto-skips the Course/Level picker when
        # this tenant's content_scope leaves only one real option -- see
        # its own docstring in exam_hub_bot.py.
        text, markup, updates = eh.entry_screen_and_updates()
        if updates:
            context.user_data.update(updates)
            eh.db_update_session(context.user_data["session_id"], **updates)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Free text in this unified bot normally means Study Hub's own
    fuzzy-search (sh.free_text_search) -- but if the report flow is mid-
    dialog waiting for a mobile number or email (eh.report_flow's own
    state), that has to be checked FIRST, or Study Hub's search would
    swallow "9876543210" as a garbled catalog query instead of the report
    flow ever seeing it. Same "check the more specific state first" rule as
    exam_hub_bot.py's own text_router, just composed with Study Hub's
    handler here since this bot has one."""
    if eh.profile_flow.is_awaiting_text_input(context):
        if await eh.profile_flow.handle_profile_text_input(update, context):
            return
    if eh.profile_flow.matches_trigger((update.message.text or "").strip()):
        await eh.profile_flow.start_profile_flow(update, context)
        return
    if eh.report_flow.is_awaiting_text_input(context):
        await eh.report_flow.handle_contact_text_input(update, context)
        return
    await sh.free_text_search(update, context)


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

    # sh.start is patched (see above) to show the top-level picker, not
    # Study Hub's own screen -- exactly the desired /start and /reset
    # behavior for this unified bot.
    app.add_handler(CommandHandler("start", sh.start))
    app.add_handler(CommandHandler("reset", sh.start))
    app.add_handler(CallbackQueryHandler(hub_callback, pattern=r"^hub:"))
    app.add_handler(CallbackQueryHandler(sh.browse_callback, pattern=r"^(browse|cat|crs|lvl|subj|pt|file|mainmenu):"))
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
    app.add_handler(CallbackQueryHandler(eh.button_router, pattern=r"^(course|level|mode|type|year|chapter|answer|pdf|next|mcqopt|restart)(:|$)"))
    # 2026-08-11: report_flow's callbacks, same as exam_hub_bot.py's own
    # standalone registration -- eh.report_flow is exam_hub_bot.py's own
    # already-imported module reference, not a fresh import here.
    app.add_handler(CallbackQueryHandler(eh.report_flow.report_flow_callback, pattern=r"^(report|reportconfirm):"))
    # eh.profile_flow is exam_hub_bot.py's own already-imported module
    # reference, same reuse pattern as eh.report_flow directly above.
    app.add_handler(CallbackQueryHandler(eh.profile_flow.profile_flow_callback, pattern=r"^(profile|profileconfirm):"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    logger.info(f"Faculty Bot starting for bot_id '{BOT_ID}' (tenant '{TENANT_ID}', {TENANT['display_name']})...")
    app.run_polling()


if __name__ == "__main__":
    main()
