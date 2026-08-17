"""
telegram/bots/fuzzy_trigger.py -- "did you mean X?" confirmation for a
near-miss on a known trigger word (2026-08-16)
--------------------------------------------------------------------------------
Built after independent code review found that ANY typo of a control word
("dne" for "done", "tst" for "test") on a Study-Hub-connected bot fell
straight through into a silent PDF/content search -- no acknowledgment, no
"did you mean X?", just an unrelated result handed back with no chance to
say "actually I meant something else." This module detects a close-but-
not-exact match against every known trigger phrase on the platform and
hands the caller a confirmation screen instead of silently guessing either
way (running the matched action, OR treating it as a real search).

USAGE (per bot's own text_router, right at the fallback point before
"nothing matched -> search/ignore"): call maybe_confirm() with a `dispatch`
dict mapping each canonical trigger phrase THIS bot actually supports to
the async callable that starts it -- each bot already has this exact
routing in its own text_router; this only asks it to name that routing
once, up front, rather than duplicating it here. If a close match against
a phrase this bot supports is found, sends the confirmation and returns
True (caller stops processing this message). Returns False otherwise (no
close match -- caller falls through to its own normal handling).

Every bot registers ONE CallbackQueryHandler for the `fuzzytrigger:` prefix
pointed at a small per-bot wrapper that calls handle_confirm_callback()
below with that SAME dispatch dict (and, on Study-Hub-connected bots, an
`on_decline` callable -- typically the bot's own free-text search -- run
when the student says "No, search instead").
"""

import difflib

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Every known control/trigger phrase across every flow this platform has --
# gathered in one place so a near-miss on ANY of them gets a confirmation,
# not just whichever flow happens to be active right now. Plain strings
# (not imported from each flow module's own TRIGGER_PHRASES/etc) --
# deliberately dependency-free, and this list is short/stable enough that
# hand-maintaining it here is simpler than five separate imports.
KNOWN_TRIGGERS = sorted({
    "profile", "report", "wallet", "recharge", "test", "upload", "done", "pass",
    "cancel", "exit", "stop",
})

# difflib similarity ratio, tuned so "dne"~"done" (0.86) and "tst"~"test"
# (0.86) match, while two genuinely different short words mostly don't.
_CLOSE_MATCH_CUTOFF = 0.75

UD_PENDING_ORIGINAL_TEXT = "fuzzytrigger_pending_original_text"
UD_MATCHED_PHRASE = "fuzzytrigger_matched_phrase"


def _closest_known_trigger(text: str):
    normalized = (text or "").strip().lower()
    if not normalized or len(normalized) > 24 or normalized in KNOWN_TRIGGERS:
        return None  # empty, a real sentence-length query, or already an exact match -- none of those are "typos" to confirm
    matches = difflib.get_close_matches(normalized, KNOWN_TRIGGERS, n=1, cutoff=_CLOSE_MATCH_CUTOFF)
    return matches[0] if matches else None


async def maybe_confirm(update, context, dispatch: dict) -> bool:
    """Returns True (and sends the confirmation) if the message looks like
    a typo of a trigger phrase this bot supports; False otherwise."""
    text = (update.message.text or "").strip()
    matched = _closest_known_trigger(text)
    if not matched or matched not in dispatch:
        return False

    context.user_data[UD_PENDING_ORIGINAL_TEXT] = text
    context.user_data[UD_MATCHED_PHRASE] = matched
    keyboard = [[
        InlineKeyboardButton(f"Yes, {matched}", callback_data="fuzzytrigger:yes"),
        InlineKeyboardButton(f"No, search for “{text}”", callback_data="fuzzytrigger:no"),
    ]]
    await update.message.reply_text(
        f"Did you mean <b>“{matched}”</b>?", parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return True


async def handle_confirm_callback(update, context, dispatch: dict, on_decline=None):
    """`on_decline(update, context, original_text)` -- run when the student
    picks "No, search instead"; typically the bot's own free-text search.
    Bots with no real search of their own (exam_hub_bot.py) can pass None
    -- the decline path then just confirms the typo wasn't meant as a
    command and stops, rather than guessing at a search that doesn't
    exist here."""
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]
    original_text = context.user_data.pop(UD_PENDING_ORIGINAL_TEXT, "")
    matched = context.user_data.pop(UD_MATCHED_PHRASE, None)

    if action == "yes" and matched and matched in dispatch:
        await query.edit_message_text(f"Got it — “{matched}” it is.")
        await dispatch[matched](update, context)
        return

    if on_decline:
        await query.edit_message_text(f"Searching for “{original_text}”…")
        await on_decline(update, context, original_text)
    else:
        await query.edit_message_text("No problem — type a command anytime (e.g. \"profile\", \"report\").")
