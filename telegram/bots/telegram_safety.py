"""
telegram/bots/telegram_safety.py -- small, dependency-free helpers that
absorb EXPECTED Telegram API quirks that aren't real application bugs.
Same shape as cancel_utils.py/contact_utils.py: a leaf module any bot can
import with zero circular-import risk.

BUILT 2026-08-18, prompted by a real activity-log review: 3 of the
platform's first 6 logged errors were plain `BadRequest: Message is not
modified` -- Telegram's own response when a bot calls edit_message_text()
with text/markup byte-identical to what's already on screen (the common
case is a student double-tapping the same button, or a network retry
re-delivering an update). This is NOT a bug in the handler's logic and
carries no useful debugging signal -- but a grep across the whole `bots/`
folder confirmed ZERO call sites anywhere caught it, so every double-tap
surfaced as a hard, logged error AND a dead tap for the student (nothing
visibly happens, since query.answer() had already cleared the loading
spinner before the edit call failed).

Deliberately narrow: this module swallows exactly ONE specific, textually
-matched BadRequest message and re-raises everything else unchanged --
it must never become a general-purpose "catch all Telegram errors" shim,
which would hide real bugs instead of just this one benign, expected one.
"""

import logging

from telegram.error import BadRequest

logger = logging.getLogger(__name__)

_NOT_MODIFIED_NEEDLE = "message is not modified"


async def safe_edit_message_text(query, *args, **kwargs):
    """Drop-in replacement for `await query.edit_message_text(...)` --
    same args/kwargs, same return value on success. The ONE difference:
    if Telegram rejects the edit because the new content is identical to
    what's already displayed, this returns None instead of raising --
    exactly a safe no-op, since the screen already shows what the caller
    wanted it to show. Any OTHER BadRequest (a real one -- bad entities,
    message too old to edit, etc.) is re-raised unchanged, never masked."""
    try:
        return await query.edit_message_text(*args, **kwargs)
    except BadRequest as e:
        if _NOT_MODIFIED_NEEDLE in str(e).lower():
            logger.info("safe_edit_message_text: ignored a benign 'message is not modified' (likely a double-tap).")
            return None
        raise
