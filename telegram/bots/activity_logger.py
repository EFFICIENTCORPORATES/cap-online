"""
telegram/bots/activity_logger.py -- the fine-grained "who did what, when"
activity trail + correlation IDs (2026-08-17, Phase 1 of
telegram/LOGGING-ARCHITECTURE.md)
--------------------------------------------------------------------------------
Read telegram/LOGGING-ARCHITECTURE.md §3-5 FIRST -- this module is the
implementation of the design decided there; this docstring is deliberately
short and doesn't re-derive the reasoning.

ONE decorator, applied ONLY at handler-registration time in each bot's
main() -- NEVER inside profile_flow.py/wallet_flow.py/test_flow.py/any flow
module. This captures the GENERIC envelope (who, what action, how long,
success/failure) for every handler on the platform for free, because every
callback_data on this platform is already `action:value` and every text
trigger is already a known short phrase -- see _extract_action() below.
It does NOT and must NOT try to capture domain meaning (a wallet amount, an
MCQ's correctness, a chapter name) -- that stays exactly where it already
lives, in wallet_ledger/exam_hub_mcq_attempts/etc., written explicitly by
the code that actually knows it.

SAFETY, non-negotiable (real students practice on these bots right now):
logging is ALWAYS best-effort. A failure anywhere in this module (a DB
write hiccup, an unexpected update shape) is caught, logged as a WARNING,
and never allowed to block, delay, or break the actual handler it's
wrapping -- same "logging must never break the product" principle
db.py's own log_interaction() already established for bot_interactions.
The one exception: a real exception RAISED BY THE WRAPPED HANDLER ITSELF is
re-raised after being logged, never swallowed -- this module observes,
it never changes what the bot actually does.
"""

import sys
import time
import uuid
import logging
import functools
import contextvars
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CORRELATION ID -- shared between this module's own activity_log rows and
# every text-log line written anywhere during the same handler call, via a
# contextvar + a logging.Filter every bot installs once at startup. See
# LOGGING-ARCHITECTURE.md §5.
# ---------------------------------------------------------------------------
_correlation_id_var = contextvars.ContextVar("correlation_id", default="-")

# Every bot's logging.basicConfig() should use this exact format string --
# one shared constant so no bot drifts to a slightly different field name.
LOG_FORMAT_WITH_CORRELATION = "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s"


class CorrelationIdFilter(logging.Filter):
    """Stamps the CURRENT correlation_id (or '-' outside any decorated
    handler, e.g. at import time or from a background job) onto every
    LogRecord. Install ONCE per process, on the root logger, so it applies
    to our own loggers AND third-party ones (httpx, telegram.ext, ...)."""

    def filter(self, record):
        record.correlation_id = _correlation_id_var.get()
        return True


def install_correlation_filter():
    """Call once, near the top of each bot's main module (right after its
    own logging.basicConfig() call which MUST already use
    LOG_FORMAT_WITH_CORRELATION above, or every log line will KeyError on
    the missing %(correlation_id)s field).

    BUG FOUND AND FIXED before any live bot was touched (caught by this
    platform's own "import every bot with a real BOT_ID and check for
    tracebacks" discipline, run BEFORE any restart): a Filter attached to
    the ROOT LOGGER via logging.getLogger().addFilter() only runs for
    records logged DIRECTLY through that logger object -- Python's logging
    module applies a logger's own filters once, at the ORIGINATING logger,
    not again at each ancestor a record propagates through on its way to
    the shared handlers. A record from any NAMED logger (httpx,
    apscheduler, telegram.ext, or this bot's own `logger = logging.
    getLogger(__name__)`) never re-runs the root logger's filter, so
    correlation_id was never set on it -> a hard KeyError the moment
    anything tried to format %(correlation_id)s. The correct attachment
    point is the HANDLER(S) -- Handler.handle() calls its own filters for
    EVERY record that reaches it, regardless of which logger it
    originated from, which is what "one filter, every log line in the
    process" actually requires.

    Idempotent -- installing twice on the same handler is harmless (a
    duplicate filter just runs twice, same correlation_id both times), but
    bots should still only call this once."""
    root = logging.getLogger()
    for handler in root.handlers:
        handler.addFilter(CorrelationIdFilter())


# ---------------------------------------------------------------------------
# REDACTION -- states where the free-text a student just typed must NEVER
# be persisted verbatim into user_activity_log.action_detail (an email, a
# mobile number, an OTP code, a rupee amount) -- see
# LOGGING-ARCHITECTURE.md §4's own reasoning (a second, unprotected copy
# of PII is a real risk, not a theoretical one).
#
# TWO mechanisms, because this platform has TWO different ways a flow
# tracks "what is the student's next message expected to be":
#   1. context.user_data flags (profile_flow.py/report_flow.py/
#      wallet_flow.py's own pattern) -- detected automatically at runtime
#      via _REDACTED_TEXT_STATES/_REDACTED_FLAG_KEYS below, no per-handler
#      opt-in needed.
#   2. python-telegram-bot's OWN ConversationHandler state (myfiles_hub_bot.py's
#      pattern) -- that state lives inside PTB's own internal
#      ConversationHandler.conversations dict, NOT in context.user_data at
#      all, so mechanism 1 above literally cannot see it. Found and fixed
#      2026-08-17 BEFORE this was wired into that bot -- its AUTH_EMAIL/
#      AUTH_OTP/DELETE_OTP handlers would otherwise have logged real
#      emails and OTP codes verbatim. For this shape, the caller passes
#      log_activity(..., always_redact=True) explicitly at registration
#      time instead -- see myfiles_hub_bot.py's own main() for the real
#      usage.
# ---------------------------------------------------------------------------
_REDACTED_TEXT_STATES = {
    ("profile_flow_state", "profile_awaiting_email"),
    ("profile_flow_state", "profile_confirming_email"),
    ("profile_flow_state", "profile_awaiting_mobile"),
    ("profile_flow_state", "profile_confirming_mobile"),
    ("report_flow_state", "report_awaiting_email"),
    ("report_flow_state", "report_confirming_email"),
    ("report_flow_state", "report_awaiting_mobile"),
    ("report_flow_state", "report_confirming_mobile"),
}
_REDACTED_FLAG_KEYS = {"walletrc_awaiting_custom_amount"}  # any truthy value on these keys -- the value itself (a rupee amount) is what's sensitive here, not a specific state string

_MAX_ACTION_DETAIL_LEN = 200  # a truncated action_detail is still useful for search; an unbounded one just bloats the table for no benefit


def _is_redacted_turn(user_data: dict) -> bool:
    for key, sensitive_value in _REDACTED_TEXT_STATES:
        if user_data.get(key) == sensitive_value:
            return True
    return any(user_data.get(key) for key in _REDACTED_FLAG_KEYS)


# ---------------------------------------------------------------------------
# ACTION EXTRACTION -- derives a machine-readable action name from an
# update with ZERO knowledge of any specific flow's business logic. See
# module docstring for why this works for free on this platform's own
# already-consistent callback_data/trigger-phrase conventions.
# ---------------------------------------------------------------------------
def _extract_user_id(update):
    # getattr(..., None), not a bare attribute access -- real PTB Update
    # objects always expose effective_user as a computed property (never
    # raises), but this stays defensive against any update-like object
    # that doesn't define the attribute at all, so a missing attribute
    # falls through to the callback_query fallback below instead of
    # raising before ever reaching it.
    effective_user = getattr(update, "effective_user", None)
    if effective_user:
        return effective_user.id
    callback_query = getattr(update, "callback_query", None)
    if callback_query and getattr(callback_query, "from_user", None):
        return callback_query.from_user.id
    return None


def _extract_action(update, handler_kind: str, user_data: dict, always_redact: bool) -> tuple:
    """Returns (action, action_detail) -- action_detail already redacted
    per the rules above where it applies."""
    if handler_kind == "callback" and update.callback_query:
        data = update.callback_query.data or ""
        parts = data.split(":", 1)
        action = parts[0] or "unknown"
        detail = parts[1] if len(parts) > 1 else None
        return action, (detail[:_MAX_ACTION_DETAIL_LEN] if detail else None)

    if handler_kind == "command" and update.message:
        text = (update.message.text or "").strip()
        action = text.split()[0].lstrip("/") if text else "unknown"
        return action, None

    if handler_kind == "photo":
        return "photo_upload", None

    if handler_kind == "text" and update.message:
        text = (update.message.text or "").strip()
        if always_redact or _is_redacted_turn(user_data):
            return "text_input", "<redacted>"
        return "free_text", (text[:_MAX_ACTION_DETAIL_LEN] if text else None)

    return "unknown", None


# ---------------------------------------------------------------------------
# THE DECORATOR
# ---------------------------------------------------------------------------
def _write_activity_row(**fields):
    """Best-effort, never raises -- see module docstring's SAFETY note.
    A failure here is a warning in the log, never a broken bot response."""
    try:
        conn = platform_db.get_connection()
        platform_db.init_schema(conn)
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO user_activity_log "
            "(correlation_id, bot_id, telegram_user_id, conversation_id, handler_kind, action, "
            "action_detail, handler_name, duration_ms, status, error_summary, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                fields["correlation_id"], fields["bot_id"], fields["telegram_user_id"],
                fields.get("conversation_id"), fields["handler_kind"], fields["action"],
                fields.get("action_detail"), fields["handler_name"], fields.get("duration_ms"),
                fields["status"], fields.get("error_summary"), platform_db.now(),
            ),
        )
    except Exception as e:
        logger.warning(f"activity_logger: failed to write activity row (non-fatal): {e}")


def log_activity(handler_kind: str, bot_id: str, always_redact: bool = False):
    """handler_kind: 'command' | 'callback' | 'text' | 'photo'. bot_id:
    passed explicitly (not read from a module global) so this decorator
    works identically whether it's wrapping exam_hub_bot.py's own handler
    or faculty_bot.py reusing eh's handler under a DIFFERENT bot_id.

    always_redact: set True when registering a handler you KNOW collects
    sensitive free text via a mechanism _is_redacted_turn() can't see at
    runtime (see the REDACTION comment block above -- PTB's own
    ConversationHandler state is the concrete example). Every OTHER flow
    on this platform tracks its own "awaiting sensitive input" state in
    context.user_data, which IS auto-detected -- this flag is the explicit
    escape hatch for the one architecture that doesn't.

    Usage, at registration time ONLY:
        app.add_handler(CommandHandler("start", log_activity("command", BOT_ID)(start)))
        app.add_handler(MessageHandler(filters.TEXT, log_activity("text", BOT_ID, always_redact=True)(collect_otp)))
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update, context):
            correlation_id = str(uuid.uuid4())
            token = _correlation_id_var.set(correlation_id)
            user_data = context.user_data if context.user_data is not None else {}

            # conversation_id: minted fresh the first time we see an empty
            # user_data (i.e. right after a clear()), then carried for as
            # long as that dict lives -- see LOGGING-ARCHITECTURE.md §4.
            conversation_id = user_data.get("_conversation_id")
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                user_data["_conversation_id"] = conversation_id
            user_data["_correlation_id"] = correlation_id

            # Extraction itself must never block the real handler -- each
            # piece falls back to a safe default independently, so a
            # failure in ONE never discards a value the OTHER already
            # computed successfully. BUG FIXED 2026-08-17 (caught by this
            # module's own end-to-end check against a real handler, before
            # any live bot went live with it): the original version wrapped
            # BOTH extractions in one try/except and reset BOTH to None on
            # any failure -- so a genuine telegram_user_id, successfully
            # extracted, was silently thrown away the moment action
            # extraction alone failed for any reason, which then failed
            # user_activity_log's own NOT NULL constraint on
            # telegram_user_id and dropped the row entirely (caught by
            # _write_activity_row()'s own try/except, but still a real,
            # avoidable loss of a row that should have recorded SOMETHING
            # real for that user).
            try:
                telegram_user_id = _extract_user_id(update)
            except Exception as e:
                logger.warning(f"activity_logger: user_id extraction failed (non-fatal): {e}")
                telegram_user_id = None
            try:
                action, action_detail = _extract_action(update, handler_kind, user_data, always_redact)
            except Exception as e:
                logger.warning(f"activity_logger: action extraction failed (non-fatal): {e}")
                action, action_detail = "unknown", None

            started = time.monotonic()
            status, error_summary = "ok", None
            try:
                return await func(update, context)
            except Exception as e:
                status = "error"
                error_summary = f"{type(e).__name__}: {e}"[:_MAX_ACTION_DETAIL_LEN]
                raise  # never swallow -- the real handler's own error path must still see this
            finally:
                # Defense in depth, deliberately redundant with
                # _write_activity_row()'s OWN internal try/except: this
                # whole block must NEVER be able to override/mask the real
                # handler's return value or exception, no matter what goes
                # wrong here -- caught a real gap in this exact spot via
                # this module's own smoke test (a monkeypatched
                # _write_activity_row with no internal guard propagated
                # straight through this finally block and clobbered the
                # wrapped handler's real result). Never trust a single
                # layer for a "logging must never break the product"
                # guarantee.
                try:
                    duration_ms = round((time.monotonic() - started) * 1000)
                    _write_activity_row(
                        correlation_id=correlation_id, bot_id=bot_id, telegram_user_id=telegram_user_id,
                        conversation_id=conversation_id, handler_kind=handler_kind, action=action,
                        action_detail=action_detail, handler_name=func.__name__, duration_ms=duration_ms,
                        status=status, error_summary=error_summary,
                    )
                except Exception as e:
                    logger.warning(f"activity_logger: logging itself failed (non-fatal, handler result unaffected): {e}")
                try:
                    _correlation_id_var.reset(token)
                except Exception:
                    pass
        return wrapper
    return decorator
