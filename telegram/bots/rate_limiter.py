"""
telegram/bots/rate_limiter.py -- per-user abuse/flood controls (2026-08-24,
SECURITY.md §4.1/§4.2, the Phase 1 fix for §3.A.1-3)
--------------------------------------------------------------------------------
Same shape as activity_logger.py: a leaf module every bot imports, applied
ONLY at handler-registration time in each bot's main() (the general "every
handler gets this" limiter) -- NEVER inside profile_flow.py/report_flow.py/
wallet_flow.py/any flow module for the general case. A SECOND, narrower
mechanism (check_and_notify(), below) is deliberately provided for the
handful of specific expensive/side-effecting actions SECURITY.md §3.A.2
calls out by name (free-text search, the email/report send, leaderboard
join/leave, MCQ-issue reports, PDF generation) -- those chokepoints sit deep
inside an already-registered, already-wrapped handler (e.g. report_flow.py's
_deliver_report(), not report_flow_callback() itself), so a second decorator
around the whole handler would either rate-limit unrelated taps in the same
flow or need its own bespoke wrapping. check_and_notify() is the inline
equivalent, called at the exact point that actually matters.

WHY IN-MEMORY, NOT A DB TABLE (the limiter's own state, not its audit
trail -- see rate_limit_hits in schema.sql for the audit side): every bot on
this platform is already its own single OS process with its own single
asyncio event loop (see /CLAUDE.md's scale-readiness gap #2) -- a DB
round-trip on EVERY tap/message just to decide whether to allow it would add
real latency to every single interaction and load onto platform.db for a
purely per-process, ephemeral concern. An in-memory sliding window, scoped
to the one process that's actually receiving that bot's updates, is the
right-sized answer at this platform's real scale (LOGGING-ARCHITECTURE.md
§0's own "right-sized, not over-engineered" principle) -- it resets on a bot
restart, which is fine: a restarted process starting with a clean slate is
never a security regression, just a rare, brief window where a very recent
flood is forgotten.

FAIL-OPEN, DELIBERATELY: any unexpected error inside this module (a bad
bucket name, a DB write failure for the audit row, a malformed update this
module doesn't recognise) is caught and logged, and the wrapped handler
still runs. A rate limiter that can itself take the platform down on a bug
would be a worse outcome than the abuse it exists to prevent -- same
"logging must never break the product" principle activity_logger.py already
established, applied here to "limiting must never break the product."
"""

import sys
import time
import logging
import functools
from pathlib import Path
from collections import namedtuple, deque

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402

logger = logging.getLogger(__name__)

_Bucket = namedtuple("_Bucket", ["max_calls", "window_seconds"])

# Tune here, in one place -- same "one named constant, not a magic number
# per call site" discipline this codebase already uses for
# LOCKOUT_WINDOW_MINUTES/MAX_BYTES/RETENTION_DAYS elsewhere. Deliberately
# generous on "general" (this exists to stop a flood, not to throttle a
# normal fast-tapping student) and deliberately tighter on the handful of
# expensive/external-facing actions SECURITY.md §3.A.2 names specifically.
BUCKETS = {
    "general":             _Bucket(max_calls=25, window_seconds=10),    # every handler, registration-time wrap
    "search":              _Bucket(max_calls=8,  window_seconds=20),   # study_hub_bot.py free_text_search()
    "email_report":        _Bucket(max_calls=3,  window_seconds=1800), # report_flow.py _deliver_report()'s email channel specifically -- real Cloudflare Email send quota/cost per hit
    "leaderboard_toggle":  _Bucket(max_calls=10, window_seconds=60),   # profile_flow.py join/leave
    "mcq_issue_report":    _Bucket(max_calls=5,  window_seconds=600),  # mcq_issue_flow.py submit
    "pdf_generation":      _Bucket(max_calls=10, window_seconds=60),   # exam_hub_bot.py send_pdf()
    "upload":              _Bucket(max_calls=15, window_seconds=60),   # myfiles_hub_bot.py upload_item_received()
    "otp_attempt":         _Bucket(max_calls=8,  window_seconds=600),  # myfiles_hub_bot.py's AUTH_EMAIL/AUTH_OTP/DELETE_OTP -- OTP request/guess attempts specifically
}

DEFAULT_BLOCK_MESSAGE = "⏳ You're doing that a lot -- please wait a bit and try again."

# A blocked tap still gets exactly one reply per this cooldown, never one
# per blocked attempt -- otherwise the "you're going too fast" message
# itself becomes the flood. Keyed the same way the limiter windows are.
_NOTIFY_COOLDOWN_SECONDS = 30

_windows: dict[tuple, deque] = {}
_last_notified: dict[tuple, float] = {}

# Opportunistic memory hygiene -- see module docstring's "right-sized" note.
# At this platform's real scale (hundreds to low thousands of distinct
# users) this is a trivial amount of memory even unpruned for weeks, but a
# cheap periodic sweep costs nothing and keeps that true indefinitely.
_call_counter = 0
_PURGE_EVERY = 2000
_STALE_AFTER_SECONDS = 3600


def _extract_user_id(update):
    # Same technique activity_logger.py's own _extract_user_id() uses --
    # getattr(..., None) throughout, never a bare attribute access, so an
    # update-like object missing an attribute falls through cleanly instead
    # of raising before the fail-open path below ever gets a chance to run.
    effective_user = getattr(update, "effective_user", None)
    if effective_user:
        return effective_user.id
    callback_query = getattr(update, "callback_query", None)
    if callback_query and getattr(callback_query, "from_user", None):
        return callback_query.from_user.id
    # check_and_notify() is also called from a few chokepoints that only
    # have a bare CallbackQuery in hand, not the full Update (e.g.
    # exam_hub_bot.py's send_pdf(query, context, book_id)) -- duck-typed via
    # its own .from_user, distinct from the update.callback_query branch
    # above.
    from_user = getattr(update, "from_user", None)
    if from_user:
        return from_user.id
    return None


def _resolve_callback_query(update):
    """Returns a real CallbackQuery whether `update` is a full Update or a
    bare CallbackQuery itself -- see _extract_user_id()'s own note."""
    callback_query = getattr(update, "callback_query", None)
    if callback_query:
        return callback_query
    if getattr(update, "from_user", None) is not None and hasattr(update, "answer"):
        return update  # `update` IS already a CallbackQuery
    return None


def _maybe_purge():
    global _call_counter
    _call_counter += 1
    if _call_counter % _PURGE_EVERY != 0:
        return
    now = time.monotonic()
    for store in (_windows,):
        stale = [k for k, dq in store.items() if not dq or (now - dq[-1]) > _STALE_AFTER_SECONDS]
        for k in stale:
            store.pop(k, None)
    stale_notify = [k for k, t in _last_notified.items() if (now - t) > _STALE_AFTER_SECONDS]
    for k in stale_notify:
        _last_notified.pop(k, None)


def _check(bot_id: str, telegram_user_id: int, bucket: str) -> bool:
    """True = allowed (and this call now counts against the window). False =
    blocked -- a blocked attempt is deliberately NOT counted as a new call,
    so a burst of blocked taps can't itself extend the block past the real
    window."""
    spec = BUCKETS.get(bucket)
    if spec is None:
        logger.error(f"rate_limiter: unknown bucket '{bucket}' -- failing open (allowing).")
        return True

    _maybe_purge()
    key = (bot_id, telegram_user_id, bucket)
    now = time.monotonic()
    window = _windows.setdefault(key, deque())
    cutoff = now - spec.window_seconds
    while window and window[0] < cutoff:
        window.popleft()
    if len(window) >= spec.max_calls:
        return False
    window.append(now)
    return True


def _log_hit_best_effort(bot_id: str, telegram_user_id: int, bucket: str, handler_name: str):
    try:
        conn = platform_db.get_connection()
        platform_db.init_schema(conn)
        platform_db.log_rate_limit_hit(conn, bot_id, telegram_user_id, bucket, handler_name)
    except Exception as e:
        logger.warning(f"rate_limiter: failed to write rate_limit_hits row (non-fatal): {e}")


async def _notify_blocked(update, bot_id: str, telegram_user_id: int, bucket: str, message: str | None):
    """Best-effort, throttled to one reply per _NOTIFY_COOLDOWN_SECONDS per
    (bot_id, telegram_user_id, bucket) -- see module docstring. A
    callback_query is ALWAYS answered even when the text is suppressed by
    the cooldown (Telegram leaves the tap's loading spinner up forever
    otherwise -- a real UX bug distinct from whether we say anything)."""
    key = (bot_id, telegram_user_id, bucket)
    now = time.monotonic()
    say_something = (now - _last_notified.get(key, 0)) >= _NOTIFY_COOLDOWN_SECONDS
    if say_something:
        _last_notified[key] = now
    text = message or DEFAULT_BLOCK_MESSAGE
    try:
        callback_query = _resolve_callback_query(update)
        if callback_query:
            await callback_query.answer(text if say_something else None, show_alert=False)
            return
        if say_something:
            effective_message = getattr(update, "effective_message", None) or getattr(update, "message", None)
            if effective_message:
                await effective_message.reply_text(text)
    except Exception as e:
        logger.warning(f"rate_limiter: failed to notify blocked user (non-fatal): {e}")


def rate_limited(bucket: str, bot_id: str, message: str | None = None):
    """Decorator, applied at handler-REGISTRATION time only (same discipline
    as activity_logger.log_activity()) -- wraps OUTERMOST, i.e. wrap the
    already-log_activity()-wrapped callable, not the other way around, so a
    blocked tap never generates a normal 'ok' activity-log row for a handler
    invocation that never actually happened:

        app.add_handler(CommandHandler("start",
            rate_limiter.rate_limited("general", BOT_ID)(
                activity_logger.log_activity("command", BOT_ID)(start))))

    Usage: `bucket` must be a key in BUCKETS above."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update, context):
            telegram_user_id = None
            try:
                telegram_user_id = _extract_user_id(update)
            except Exception as e:
                logger.warning(f"rate_limiter: user_id extraction failed (non-fatal, failing open): {e}")

            if telegram_user_id is None:
                # Can't key a per-user limiter without a user id -- fail
                # open rather than either blocking everyone or crashing.
                return await func(update, context)

            try:
                allowed = _check(bot_id, telegram_user_id, bucket)
            except Exception as e:
                logger.warning(f"rate_limiter: check failed (non-fatal, failing open): {e}")
                allowed = True

            if allowed:
                return await func(update, context)

            try:
                await _notify_blocked(update, bot_id, telegram_user_id, bucket, message)
            except Exception as e:
                logger.warning(f"rate_limiter: notify failed (non-fatal): {e}")
            _log_hit_best_effort(bot_id, telegram_user_id, bucket, func.__name__)
            return None
        return wrapper
    return decorator


def check(bot_id: str, telegram_user_id: int, bucket: str) -> bool:
    """Pure check -- no notification, no audit-row side effect -- for a
    caller that only has a bot_id/telegram_user_id in hand, not an
    Update/CallbackQuery (e.g. report_flow.py's _deliver_report(), called
    well after the tap that triggered it, deep inside a helper that never
    sees the original Update). Pair with log_hit() below to record a block.
    Never raises -- fails open."""
    try:
        return _check(bot_id, telegram_user_id, bucket)
    except Exception as e:
        logger.warning(f"rate_limiter.check: failed (non-fatal, failing open): {e}")
        return True


def log_hit(bot_id: str, telegram_user_id: int, bucket: str, handler_name: str = "inline"):
    """Public wrapper around the best-effort audit-row writer, for a caller
    using check() directly instead of check_and_notify()."""
    _log_hit_best_effort(bot_id, telegram_user_id, bucket, handler_name)


async def check_and_notify(update, context, bot_id: str, bucket: str, *, message: str | None = None) -> bool:
    """Inline use for ONE specific chokepoint deep inside an already-
    registered handler (see module docstring). Returns True if the caller
    should proceed, False if it was blocked -- the student has already been
    (best-effort, throttled) told either way by the time this returns, so
    the caller only needs to skip the expensive/external action itself, not
    send its own message too. Never raises."""
    telegram_user_id = None
    try:
        telegram_user_id = _extract_user_id(update)
    except Exception as e:
        logger.warning(f"rate_limiter.check_and_notify: user_id extraction failed (non-fatal, failing open): {e}")
    if telegram_user_id is None:
        return True

    try:
        allowed = _check(bot_id, telegram_user_id, bucket)
    except Exception as e:
        logger.warning(f"rate_limiter.check_and_notify: check failed (non-fatal, failing open): {e}")
        return True

    if allowed:
        return True

    try:
        await _notify_blocked(update, bot_id, telegram_user_id, bucket, message)
    except Exception as e:
        logger.warning(f"rate_limiter.check_and_notify: notify failed (non-fatal): {e}")
    _log_hit_best_effort(bot_id, telegram_user_id, bucket, "check_and_notify")
    return False
