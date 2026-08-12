"""
telegram/bots/mcq_issue_flow.py -- "Report Issue in MCQ" flow (2026-08-13)
--------------------------------------------------------------------------
Lets a student flag a problem with an MCQ directly from the "Correct
Answer" screen: a 4th button alongside Next Question / Chapter List /
I'm Done -> pick a category (Wrong Question / Wrong Answer / Typo Error /
Wrong Mapping / Other) -> type a free-text description -> stored in
mcq_issue_reports (see database/schema.sql) -> a plain thank-you message
naming support@1lavya.com for anything more.

Imported by exam_hub_bot.py (and, through it, faculty_bot.py's unified
bot). Same shape as profile_flow.py/report_flow.py: the host script (1)
registers this module's callback handler, (2) checks
is_awaiting_text_input()/handle_issue_text_input() in its OWN text_router
BEFORE any other free-text handling -- same "most specific state first"
discipline those two flows already follow, and (3) calls
start_issue_report() itself once it knows which MCQ is being reported
(this module never looks a question up on its own -- see below).

CALLBACK_DATA NAMESPACING: `reportissue` (bare, no colon -- tapped from
the Correct-Answer screen, routed through the HOST's own button_router
since only the host has access to the current question's course/level/
subject/chapter) triggers the host to call start_issue_report(); this
module's own CallbackQueryHandler owns `issuecat:<index>` and
`issuecancel` (bare) -- register it with pattern
r"^(issuecat|issuecancel)(:|$)" and add it wherever a bot composes
exam_hub_bot's handlers under a pattern-restricted CallbackQueryHandler
(faculty_bot.py) -- the exact bug class (an unscoped/mis-scoped pattern
silently swallowing another handler's buttons) has already bitten this
platform 3+ times this session; don't repeat it here.

DELIBERATE NON-DEPENDENCY: this module never imports exam_hub_bot.py or
touches its McqBank/mcq_bank -- every field it needs (mcq_id, course,
level, subject, chapter_slug, chapter_label, a `return_markup` to restore
once the report flow ends) is passed into start_issue_report() by the
caller, which already has the current question in scope. Keeps this
module trivially reusable by any future bot that shows MCQs, with zero
risk of a circular import.
"""

import sys
import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402 -- must follow the sys.path.insert() above

logger = logging.getLogger(__name__)

# (category_code, button_label) -- category_code is what's stored in
# mcq_issue_reports.category (matches schema.sql's CHECK constraint
# exactly; keep the two in sync if this list ever changes).
CATEGORIES = [
    ("wrong_question", "❓ Wrong Question"),
    ("wrong_answer", "❌ Wrong Answer"),
    ("typo_error", "✏️ Typo Error"),
    ("wrong_mapping", "\U0001F500 Wrong Mapping"),
    ("other", "\U0001F4DD Other Issue"),
]

SUPPORT_EMAIL = "support@1lavya.com"


async def start_issue_report(query, context, bot_id: str, *, mcq_id: str, human_id, course, level, subject,
                              chapter_slug, chapter_label, return_markup: InlineKeyboardMarkup):
    """Called from the host's button_router when the student taps "Report
    Issue in MCQ" on the just-answered question's result screen.
    `return_markup` is whatever keyboard the host was already showing
    (typically next_step_rows()'s Next Question/Chapter List/I'm Done) --
    stashed here and restored on Cancel or after a successful submission,
    so the student is never left at a dead end. `human_id` (the platform's
    globally-unique, student-facing question ID -- see COURSE-CATALOG.md)
    is shown on-screen and stored alongside the internal `mcq_id`, added
    2026-08-13 so a filed report is unambiguously traceable to one exact
    question, the same ID the student can also quote directly to support."""
    context.user_data["issue_report"] = {
        "bot_id": bot_id, "mcq_id": mcq_id, "human_id": human_id, "course": course, "level": level, "subject": subject,
        "chapter_slug": chapter_slug, "chapter_label": chapter_label, "return_markup": return_markup,
        "awaiting_description": False,
    }
    id_line = f"ID: {human_id}\n\n" if human_id else ""
    keyboard = [[InlineKeyboardButton(label, callback_data=f"issuecat:{i}")] for i, (_code, label) in enumerate(CATEGORIES)]
    keyboard.append([InlineKeyboardButton("✖ Cancel", callback_data="issuecancel")])
    await query.edit_message_text(
        f"\U0001F6A9 *Report an Issue*\n\n{id_line}What's wrong with this question?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
    )


def is_awaiting_text_input(context) -> bool:
    state = context.user_data.get("issue_report")
    return bool(state and state.get("awaiting_description"))


async def handle_issue_text_input(update, context) -> bool:
    """Returns True if this message was consumed (the host's text_router
    should stop processing it further), False if this flow isn't active."""
    state = context.user_data.get("issue_report")
    if not state or not state.get("awaiting_description"):
        return False

    description = (update.message.text or "").strip()
    if not description:
        await update.message.reply_text("Please type a short description of the issue (or tap Cancel above).")
        return True

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    platform_db.log_mcq_issue_report(
        conn, bot_id=state["bot_id"], telegram_user_id=update.effective_user.id, mcq_id=state["mcq_id"],
        human_id=state.get("human_id"), course=state.get("course"), level=state.get("level"),
        subject=state.get("subject"), chapter_slug=state.get("chapter_slug"), chapter_label=state.get("chapter_label"),
        category=state["category"], description=description,
    )
    return_markup = state.get("return_markup")
    id_line = f" (ID: {state['human_id']})" if state.get("human_id") else ""
    context.user_data.pop("issue_report", None)
    await update.message.reply_text(
        f"✅ Thanks for your report{id_line} -- we'll check and resolve the issue.\n\n"
        f"You may also mail us at {SUPPORT_EMAIL} for further issues on this question.",
        reply_markup=return_markup,
    )
    return True


async def mcq_issue_flow_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "issuecancel":
        state = context.user_data.pop("issue_report", None)
        return_markup = state.get("return_markup") if state else None
        await query.edit_message_text("Cancelled.", reply_markup=return_markup)
        return

    if data.startswith("issuecat:"):
        state = context.user_data.get("issue_report")
        if not state:
            await query.edit_message_text("⚠️ Session expired -- please try again from the question.")
            return
        try:
            idx = int(data.split(":", 1)[1])
            category_code, category_label = CATEGORIES[idx]
        except (ValueError, IndexError):
            await query.edit_message_text("⚠️ Session expired -- please try again from the question.")
            return
        state["category"] = category_code
        state["awaiting_description"] = True
        await query.edit_message_text(
            f"Category: *{category_label}*\n\nPlease describe the issue in a message:",
            parse_mode=ParseMode.MARKDOWN,
        )
