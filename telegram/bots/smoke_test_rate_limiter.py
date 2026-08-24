"""
telegram/bots/smoke_test_rate_limiter.py -- smoke test for rate_limiter.py
and input_guard.py (2026-08-24, SECURITY.md Phase 1)
--------------------------------------------------------------------------------
Deliberately runs ENTIRELY against synthetic bot_id/user_id and a temporary
BUCKETS override -- never touches any real bot module or live process, same
"proves the mechanism correct in isolation BEFORE it's wired into any live,
student-facing bot" discipline as smoke_test_activity_logger.py.

Run directly: `python smoke_test_rate_limiter.py`.
"""

import sys
import time
import asyncio
from pathlib import Path
from types import SimpleNamespace
from collections import namedtuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import rate_limiter  # noqa: E402
import input_guard  # noqa: E402

BOT_ID = "smoketest-bot"
USER_A = 900_777_001
USER_B = 900_777_002

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
    conn.execute("DELETE FROM rate_limit_hits WHERE bot_id=?", (BOT_ID,))
    conn.commit()
    rate_limiter._windows.clear()
    rate_limiter._last_notified.clear()


def hits_for(user_id=None):
    if user_id is not None:
        return conn.execute(
            "SELECT * FROM rate_limit_hits WHERE bot_id=? AND telegram_user_id=?", (BOT_ID, user_id)
        ).fetchall()
    return conn.execute("SELECT * FROM rate_limit_hits WHERE bot_id=?", (BOT_ID,)).fetchall()


def mock_callback_update(user_id: int, data: str = "x:1"):
    user = SimpleNamespace(id=user_id, username=None)
    query = SimpleNamespace(data=data, from_user=user, answered_with=None)

    async def _answer(text=None, show_alert=False):
        query.answered_with = text

    query.answer = _answer
    update = SimpleNamespace(effective_user=user, callback_query=query, effective_message=None, message=None)
    return update, query


def mock_text_update(user_id: int, text: str = "hi"):
    user = SimpleNamespace(id=user_id, username=None)
    message = SimpleNamespace(text=text, replied_with=None)

    async def _reply_text(t):
        message.replied_with = t

    message.reply_text = _reply_text
    update = SimpleNamespace(effective_user=user, callback_query=None, effective_message=message, message=message)
    return update, message


async def main():
    print("=== smoke_test_rate_limiter ===")
    cleanup()
    # Isolated test buckets -- never touches the real BUCKETS entries other
    # modules import by name, so this file's timing assumptions can't drift
    # if a real bucket's thresholds are tuned later.
    _Bucket = namedtuple("_Bucket", ["max_calls", "window_seconds"])
    rate_limiter.BUCKETS["_test_tight"] = _Bucket(max_calls=3, window_seconds=1)
    rate_limiter.BUCKETS["_test_loose"] = _Bucket(max_calls=100, window_seconds=60)

    try:
        # --- [1] Core sliding-window check() ---------------------------------
        print("\n[1] Core sliding-window behavior")
        allowed = [rate_limiter._check(BOT_ID, USER_A, "_test_tight") for _ in range(3)]
        check("first 3 calls within the window are all allowed", all(allowed))
        blocked = rate_limiter._check(BOT_ID, USER_A, "_test_tight")
        check("the 4th call within the same window is blocked", blocked is False)
        # A blocked attempt must not itself count as a new call -- re-checking
        # immediately should still be blocked, not somehow "allowed" because
        # the deque grew past max_calls.
        still_blocked = rate_limiter._check(BOT_ID, USER_A, "_test_tight")
        check("a repeated blocked attempt stays blocked (doesn't extend the window)", still_blocked is False)
        check("a DIFFERENT user is unaffected by user A's block", rate_limiter._check(BOT_ID, USER_B, "_test_tight") is True)

        time.sleep(1.1)
        check("after the window elapses, user A is allowed again", rate_limiter._check(BOT_ID, USER_A, "_test_tight") is True)

        # --- [2] Unknown bucket fails open ------------------------------------
        print("\n[2] Fail-open behavior")
        check("an unknown bucket name fails OPEN (returns True)", rate_limiter._check(BOT_ID, USER_A, "_no_such_bucket") is True)
        check("check() (public) also fails open for an unknown bucket", rate_limiter.check(BOT_ID, USER_A, "_no_such_bucket") is True)

        # --- [3] Decorator: allowed path -------------------------------------
        print("\n[3] rate_limited() decorator -- allowed path")
        cleanup()
        calls = []

        @rate_limiter.rate_limited("_test_loose", BOT_ID)
        async def loose_handler(update, context):
            calls.append(1)
            return "handled"

        update, query = mock_callback_update(USER_A)
        result = await loose_handler(update, SimpleNamespace(user_data={}))
        check("an allowed call actually invokes the wrapped handler", calls == [1])
        check("an allowed call returns the wrapped handler's real return value", result == "handled")

        # --- [4] Decorator: blocked path (callback) ---------------------------
        print("\n[4] rate_limited() decorator -- blocked path (callback query)")
        cleanup()
        calls = []

        @rate_limiter.rate_limited("_test_tight", BOT_ID)
        async def tight_handler(update, context):
            calls.append(1)
            return "handled"

        ctx = SimpleNamespace(user_data={})
        for _ in range(3):
            update, query = mock_callback_update(USER_A)
            await tight_handler(update, ctx)
        check("3 allowed calls all reached the handler", calls == [1, 1, 1])

        update4, query4 = mock_callback_update(USER_A)
        result4 = await tight_handler(update4, ctx)
        check("the 4th (blocked) call does NOT reach the wrapped handler", calls == [1, 1, 1])
        check("a blocked call returns None (never the wrapped handler's value)", result4 is None)
        check("a blocked CALLBACK query is still answered (clears the loading spinner)", query4.answered_with is not None)

        rows = hits_for(USER_A)
        check("exactly one rate_limit_hits row was written for the block", len(rows) == 1)

        # --- [5] Decorator: blocked path (text message) ------------------------
        print("\n[5] rate_limited() decorator -- blocked path (text message)")
        cleanup()

        @rate_limiter.rate_limited("_test_tight", BOT_ID)
        async def tight_text_handler(update, context):
            return "handled"

        ctx2 = SimpleNamespace(user_data={})
        for _ in range(3):
            update, message = mock_text_update(USER_A)
            await tight_text_handler(update, ctx2)
        update4, message4 = mock_text_update(USER_A)
        await tight_text_handler(update4, ctx2)
        check("a blocked TEXT message gets a reply (not silently dropped)", message4.replied_with is not None)

        # --- [6] Notify throttling: one message per cooldown, not per block -----
        print("\n[6] Notify throttling")
        cleanup()

        @rate_limiter.rate_limited("_test_tight", BOT_ID)
        async def spam_handler(update, context):
            return "handled"

        ctx3 = SimpleNamespace(user_data={})
        for _ in range(3):
            update, _ = mock_callback_update(USER_A)
            await spam_handler(update, ctx3)
        first_blocked_update, first_blocked_query = mock_callback_update(USER_A)
        await spam_handler(first_blocked_update, ctx3)
        second_blocked_update, second_blocked_query = mock_callback_update(USER_A)
        await spam_handler(second_blocked_update, ctx3)
        check("the FIRST blocked tap gets a real message", first_blocked_query.answered_with is not None)
        check("a SECOND blocked tap within the cooldown gets a silent answer() (no repeated text)", second_blocked_query.answered_with is None)
        # Both blocks are still individually audited even though only one was announced.
        check("both blocked attempts are still individually logged to rate_limit_hits", len(hits_for(USER_A)) == 2)

        # --- [7] check_and_notify() with a bare CallbackQuery (no full Update) --
        print("\n[7] check_and_notify() -- bare CallbackQuery caller shape (e.g. send_pdf())")
        cleanup()
        _, bare_query = mock_callback_update(USER_A)
        ctx4 = SimpleNamespace(user_data={})
        allowed_results = [await rate_limiter.check_and_notify(bare_query, ctx4, BOT_ID, "_test_tight") for _ in range(3)]
        check("3 allowed calls via a bare CallbackQuery all return True", all(allowed_results))
        blocked_result = await rate_limiter.check_and_notify(bare_query, ctx4, BOT_ID, "_test_tight")
        check("the 4th call via a bare CallbackQuery returns False", blocked_result is False)
        check("the bare CallbackQuery was still answered on block", bare_query.answered_with is not None)

        # --- [8] check_and_notify() with no resolvable user id (fails open) -----
        print("\n[8] check_and_notify() -- unresolvable user id fails open")
        weird_update = SimpleNamespace()  # no effective_user, no callback_query, no from_user
        result_open = await rate_limiter.check_and_notify(weird_update, SimpleNamespace(user_data={}), BOT_ID, "_test_tight")
        check("an update with no extractable user id fails open (returns True)", result_open is True)

        # --- [9] input_guard.sanitize_free_text --------------------------------
        print("\n[9] input_guard.sanitize_free_text()")
        check("None input returns ''", input_guard.sanitize_free_text(None) == "")
        check("non-string input returns ''", input_guard.sanitize_free_text(12345) == "")
        check("plain text passes through unchanged", input_guard.sanitize_free_text("cash flow statement") == "cash flow statement")
        check("leading/trailing whitespace is trimmed", input_guard.sanitize_free_text("  hello  ") == "hello")
        dirty = "hi\x00there\x07\x1bworld"
        cleaned = input_guard.sanitize_free_text(dirty)
        check("control characters (NUL, BEL, ESC) are stripped", "\x00" not in cleaned and "\x07" not in cleaned and "\x1b" not in cleaned)
        check("real newline/tab characters are preserved (legitimate multi-line input)", input_guard.sanitize_free_text("line1\nline2\ttab") == "line1\nline2\ttab")
        long_text = "x" * 1000
        check("text longer than max_len is truncated", len(input_guard.sanitize_free_text(long_text, max_len=50)) == 50)

        # --- [10] input_guard.validate_upload -----------------------------------
        print("\n[10] input_guard.validate_upload()")
        ok, reason = input_guard.validate_upload("notes.pdf", 5 * 1024 * 1024)
        check("a normal PDF under the size cap is allowed", ok is True and reason is None)
        ok, reason = input_guard.validate_upload("huge.pdf", 25 * 1024 * 1024)
        check("a file over MAX_UPLOAD_BYTES is rejected", ok is False)
        check("the size-rejection reason is a plain student-facing string, not an internal detail", isinstance(reason, str) and "MB" in reason)
        ok, reason = input_guard.validate_upload("virus.exe", 1024)
        check("a .exe upload is rejected", ok is False)
        ok, reason = input_guard.validate_upload("script.PS1", 1024)  # case-insensitive
        check("extension matching is case-insensitive ('.PS1' also rejected)", ok is False)
        ok, reason = input_guard.validate_upload("homework.docx", 1024)
        check("a normal .docx is allowed (not on the deny-list)", ok is True)
        ok, reason = input_guard.validate_upload(None, 1024)  # e.g. a Telegram photo, no filename at all
        check("a None filename (e.g. a photo) with a safe size is allowed", ok is True)

    finally:
        cleanup()
        rate_limiter.BUCKETS.pop("_test_tight", None)
        rate_limiter.BUCKETS.pop("_test_loose", None)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
