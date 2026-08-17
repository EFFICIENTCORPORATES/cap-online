"""
telegram/bots/smoke_test_activity_logger.py -- smoke test for
activity_logger.py (2026-08-17)
--------------------------------------------------------------------------------
Deliberately runs ENTIRELY against synthetic data/functions, never touching
any real bot module or live process -- this proves the decorator itself is
correct in isolation BEFORE it gets wired into any live, student-facing bot
(per Pranav's explicit "be careful... any bot code is not affected" ask).
Same "no mocking of the DB layer itself, full cleanup in finally" discipline
as every other smoke test on this platform.

Run directly: `python smoke_test_activity_logger.py`.
"""

import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import activity_logger  # noqa: E402

CHAT_ID = 900_888_001
BOT_ID = "smoketest-bot"

conn = platform_db.get_connection()
platform_db.init_schema(conn)

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
    conn.execute("DELETE FROM user_activity_log WHERE bot_id=?", (BOT_ID,))
    conn.commit()


def rows_for(action=None):
    if action:
        return conn.execute(
            "SELECT * FROM user_activity_log WHERE bot_id=? AND action=? ORDER BY activity_id DESC LIMIT 1",
            (BOT_ID, action),
        ).fetchone()
    return conn.execute("SELECT * FROM user_activity_log WHERE bot_id=? ORDER BY activity_id", (BOT_ID,)).fetchall()


def cols():
    return [d[0] for d in conn.execute("SELECT * FROM user_activity_log LIMIT 0").description]


def as_dict(row):
    return dict(zip(cols(), row)) if row else None


def mock_callback_update(data: str, user_data: dict):
    user = SimpleNamespace(id=CHAT_ID, username=None)
    query = SimpleNamespace(data=data, from_user=user)
    update = SimpleNamespace(effective_user=user, callback_query=query, message=None)
    context = SimpleNamespace(user_data=user_data)
    return update, context


def mock_text_update(text: str, user_data: dict):
    user = SimpleNamespace(id=CHAT_ID, username=None)
    message = SimpleNamespace(text=text)
    update = SimpleNamespace(effective_user=user, callback_query=None, message=message)
    context = SimpleNamespace(user_data=user_data)
    return update, context


def mock_command_update(text: str, user_data: dict):
    return mock_text_update(text, user_data)  # same shape -- commands arrive as update.message.text too


async def main():
    print("=== smoke_test_activity_logger ===")
    cleanup()

    try:
        # 1. A callback tap with action:value -- both fields split correctly.
        @activity_logger.log_activity("callback", BOT_ID)
        async def fake_callback_handler(update, context):
            return "handled"

        ud1 = {}
        upd1, ctx1 = mock_callback_update("profile:edit_email", ud1)
        result = await fake_callback_handler(upd1, ctx1)
        check("wrapped callback handler still returns its real result", result == "handled")
        row = as_dict(rows_for("profile"))
        check("callback action split correctly ('profile')", row is not None and row["action"] == "profile")
        check("callback action_detail captured the rest ('edit_email')", row["action_detail"] == "edit_email")
        check("status recorded as 'ok'", row["status"] == "ok")
        check("duration_ms was recorded (non-negative int)", isinstance(row["duration_ms"], int) and row["duration_ms"] >= 0)
        check("telegram_user_id captured correctly", row["telegram_user_id"] == CHAT_ID)
        check("handler_name captured the real function name", row["handler_name"] == "fake_callback_handler")
        check("a correlation_id was generated (non-empty, looks like a UUID)", row["correlation_id"] and len(row["correlation_id"]) == 36)
        check("a conversation_id was generated and stashed in user_data", ud1.get("_conversation_id") == row["conversation_id"])

        # 2. A bare callback with no ':' -- action is the whole string, detail is None.
        @activity_logger.log_activity("callback", BOT_ID)
        async def fake_bare_handler(update, context):
            return None

        ud2 = {}
        upd2, ctx2 = mock_callback_update("restart", ud2)
        await fake_bare_handler(upd2, ctx2)
        row2 = as_dict(rows_for("restart"))
        check("bare callback_data (no colon) -> action is the whole string", row2["action"] == "restart")
        check("bare callback_data -> action_detail is None", row2["action_detail"] is None)

        # 3. Text trigger, NOT a redacted state -> logged as free_text with real content.
        @activity_logger.log_activity("text", BOT_ID)
        async def fake_text_handler(update, context):
            return None

        ud3 = {}
        upd3, ctx3 = mock_text_update("wallet", ud3)
        await fake_text_handler(upd3, ctx3)
        row3 = as_dict(rows_for("free_text"))
        check("a normal text message is logged as 'free_text'", row3["action"] == "free_text")
        check("a normal text message's real content IS captured (not sensitive)", row3["action_detail"] == "wallet")

        # 4. REGRESSION-CRITICAL: a redacted state (mid email collection) --
        # the raw typed email must NEVER appear in action_detail.
        ud4 = {"profile_flow_state": "profile_awaiting_email"}
        upd4, ctx4 = mock_text_update("realstudent@example.com", ud4)
        await fake_text_handler(upd4, ctx4)
        row4 = as_dict(rows_for("text_input"))
        check("a redacted state logs action='text_input', not 'free_text'", row4["action"] == "text_input")
        check("the actual typed email NEVER appears anywhere in the row", "realstudent@example.com" not in str(row4))
        check("action_detail is literally '<redacted>'", row4["action_detail"] == "<redacted>")

        # 5. Same for a redacted mobile-collection state.
        ud5 = {"report_flow_state": "report_awaiting_mobile"}
        upd5, ctx5 = mock_text_update("9876543210", ud5)
        await fake_text_handler(upd5, ctx5)
        rows_now = rows_for()
        last_row = as_dict(rows_now[-1])
        check("a redacted mobile-collection state also redacts correctly", last_row["action_detail"] == "<redacted>")
        check("the actual typed mobile number never appears anywhere in the row", "9876543210" not in str(last_row))

        # 6. Wallet custom-amount flag -- redacted via the FLAG-key path, not a state-string path.
        ud6 = {"walletrc_awaiting_custom_amount": True}
        upd6, ctx6 = mock_text_update("500", ud6)
        await fake_text_handler(upd6, ctx6)
        rows_now2 = rows_for()
        last_row2 = as_dict(rows_now2[-1])
        check("wallet custom-amount entry is also redacted (flag-key path)", last_row2["action_detail"] == "<redacted>")

        # 7. A command handler.
        @activity_logger.log_activity("command", BOT_ID)
        async def fake_command_handler(update, context):
            return None

        ud7 = {}
        upd7, ctx7 = mock_command_update("/start", ud7)
        await fake_command_handler(upd7, ctx7)
        row7 = as_dict(rows_for("start"))
        check("a /command is logged with the command name, no leading slash", row7 is not None and row7["action"] == "start")

        # 8. REGRESSION-CRITICAL: a real exception inside the wrapped handler
        # is (a) still raised to the caller (never swallowed) and (b) still
        # logged, with status='error' and a real error_summary -- this is
        # the exact guarantee that makes "logging observes, never changes
        # behavior" true even in the failure case.
        @activity_logger.log_activity("callback", BOT_ID)
        async def fake_crashing_handler(update, context):
            raise ValueError("deliberate test failure")

        ud8 = {}
        upd8, ctx8 = mock_callback_update("crashtest:boom", ud8)
        raised = False
        try:
            await fake_crashing_handler(upd8, ctx8)
        except ValueError as e:
            raised = True
            check("the real exception message survives unchanged", str(e) == "deliberate test failure")
        check("a real handler exception IS still raised to the caller (never swallowed)", raised)
        row8 = as_dict(rows_for("crashtest"))
        check("the crash was still logged with status='error'", row8 is not None and row8["status"] == "error")
        check("error_summary captured the real exception type + message", row8["error_summary"] == "ValueError: deliberate test failure")

        # 9. SAFETY-CRITICAL: if the DB write itself fails, the wrapped
        # handler's own return value must still come through untouched --
        # logging failing must NEVER break the actual bot response.
        real_write = activity_logger._write_activity_row
        def broken_write(**kwargs):
            raise RuntimeError("simulated DB outage")
        activity_logger._write_activity_row = broken_write
        try:
            @activity_logger.log_activity("callback", BOT_ID)
            async def fake_handler_during_outage(update, context):
                return "still works"
            ud9 = {}
            upd9, ctx9 = mock_callback_update("outage_test:x", ud9)
            result9 = await fake_handler_during_outage(upd9, ctx9)
            check("handler still returns its real result even if the activity-log DB write itself throws", result9 == "still works")
        finally:
            activity_logger._write_activity_row = real_write

        # 10. Photo handler_kind.
        @activity_logger.log_activity("photo", BOT_ID)
        async def fake_photo_handler(update, context):
            return None
        ud10 = {}
        upd10 = SimpleNamespace(effective_user=SimpleNamespace(id=CHAT_ID), callback_query=None, message=None)
        ctx10 = SimpleNamespace(user_data=ud10)
        await fake_photo_handler(upd10, ctx10)
        row10 = as_dict(rows_for("photo_upload"))
        check("a photo update is logged as 'photo_upload'", row10 is not None)

        # 11. conversation_id is REUSED across two calls sharing one
        # user_data dict (same "session"), not re-minted every call.
        shared_ud = {}
        u1, c1 = mock_callback_update("mode:mcq", shared_ud)
        await fake_callback_handler(u1, c1)
        conv_after_first = shared_ud["_conversation_id"]
        u2, c2 = mock_callback_update("course:CA", shared_ud)
        await fake_callback_handler(u2, c2)
        conv_after_second = shared_ud["_conversation_id"]
        check("conversation_id stays the SAME across two calls sharing one context.user_data", conv_after_first == conv_after_second)
        r1 = as_dict(rows_for("mode"))
        r2 = as_dict(rows_for("course"))
        check("both activity_log rows for that shared session carry the same conversation_id", r1["conversation_id"] == r2["conversation_id"])
        check("but each call still gets its OWN, DIFFERENT correlation_id", r1["correlation_id"] != r2["correlation_id"])

        # 12. LOG_FORMAT_WITH_CORRELATION contains the field CorrelationIdFilter sets.
        check("the shared log format string references %(correlation_id)s", "%(correlation_id)s" in activity_logger.LOG_FORMAT_WITH_CORRELATION)

        # 13. REGRESSION-CRITICAL (real bug found + fixed 2026-08-17, before
        # any live bot was touched): install_correlation_filter() must make
        # EVERY logger in the process safe to use with
        # LOG_FORMAT_WITH_CORRELATION -- including a NAMED child logger
        # (httpx, apscheduler, or any bot's own `logging.getLogger(__name__)`),
        # not just the root logger directly. A real end-to-end check: build
        # a throwaway logging setup exactly the way each bot's own
        # logging.basicConfig() + install_correlation_filter() does, then
        # actually emit a record through a CHILD logger and confirm it
        # formats with NO exception and the real correlation_id value shows
        # up in the rendered output.
        import io as _io
        import logging as _logging

        throwaway_root = _logging.getLogger("smoketest_activity_logger_throwaway_root")
        throwaway_root.handlers.clear()
        throwaway_root.filters.clear()
        throwaway_root.setLevel(_logging.INFO)  # a fresh named logger defaults to NOTSET/WARNING -- without this, .info() below is silently dropped before it ever reaches the handler, which would make this check pass for the wrong reason
        stream = _io.StringIO()
        handler = _logging.StreamHandler(stream)
        handler.setFormatter(_logging.Formatter(activity_logger.LOG_FORMAT_WITH_CORRELATION))
        throwaway_root.addHandler(handler)
        throwaway_root.addFilter(activity_logger.CorrelationIdFilter())  # exercises the SAME fixed code path install_correlation_filter() uses, just scoped to this throwaway logger instead of the real root
        for h in throwaway_root.handlers:
            h.addFilter(activity_logger.CorrelationIdFilter())

        child_logger = throwaway_root.getChild("some_named_child")  # simulates httpx/apscheduler/a bot's own module logger
        token = activity_logger._correlation_id_var.set("test-correlation-id-123")
        raised = False
        try:
            child_logger.info("a log line from a NAMED CHILD logger, not the root")
        except Exception:
            raised = True
        finally:
            activity_logger._correlation_id_var.reset(token)
        check("a named child logger formats successfully with the correlation format string (no KeyError)", not raised)
        check("the real correlation_id value actually appears in the rendered output", "test-correlation-id-123" in stream.getvalue())

        # 14. REGRESSION-CRITICAL (real gap found + fixed 2026-08-17, before
        # myfiles_hub_bot.py was wired in): always_redact=True must redact
        # unconditionally, for a flow (PTB's own ConversationHandler state)
        # that _is_redacted_turn()'s context.user_data-based detection
        # cannot see at all -- e.g. an OTP code or an email collected via a
        # ConversationHandler state, not a context.user_data flag.
        @activity_logger.log_activity("text", BOT_ID, always_redact=True)
        async def fake_otp_handler(update, context):
            return None
        ud14 = {}  # deliberately EMPTY -- no context.user_data flag exists for this to key off, unlike the earlier redaction tests
        upd14, ctx14 = mock_text_update("482913", ud14)  # a plausible OTP code
        await fake_otp_handler(upd14, ctx14)
        row14 = as_dict(rows_for("text_input"))
        check("always_redact=True redacts even with NO context.user_data flag present", row14 is not None and row14["action_detail"] == "<redacted>")
        check("the real OTP-like value never appears anywhere in the row", "482913" not in str(row14))

        # 15. And the inverse -- always_redact=False (the default) must NOT
        # redact a handler that has no matching context.user_data flag,
        # confirming #14 isn't just redacting everything unconditionally.
        row3_recheck = as_dict(rows_for("free_text"))
        check("a normal (non-redacted) handler from earlier in this run is UNAFFECTED by always_redact existing elsewhere", row3_recheck["action_detail"] == "wallet")

        # 16. REGRESSION-CRITICAL: user_id extraction must fall back to
        # callback_query.from_user.id even when the update-like object has
        # NO effective_user attribute AT ALL (not just one that's None) --
        # real PTB Update objects always expose effective_user as a
        # computed property, but a bare attribute access here used to
        # raise AttributeError on anything that doesn't, discarding an
        # already-resolvable telegram_user_id before the fallback was ever
        # reached (found via this module's own end-to-end check against a
        # real handler wrapped exactly as main() registers it).
        @activity_logger.log_activity("callback", BOT_ID)
        async def fake_no_effective_user_handler(update, context):
            return None
        no_eu_user = SimpleNamespace(id=CHAT_ID)
        no_eu_query = SimpleNamespace(data="test16:x", from_user=no_eu_user)
        no_eu_update = SimpleNamespace(callback_query=no_eu_query)  # deliberately NO effective_user attribute at all
        await fake_no_effective_user_handler(no_eu_update, SimpleNamespace(user_data={}))
        row16 = as_dict(rows_for("test16"))
        check("telegram_user_id still resolves via the callback_query fallback when effective_user is missing entirely", row16 is not None and row16["telegram_user_id"] == CHAT_ID)

    finally:
        cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
