"""
telegram/bots/smoke_test_callback_registry.py -- smoke test for
callback_registry.py (2026-08-24, SECURITY.md Phase 2)
--------------------------------------------------------------------------------
Deliberately runs ENTIRELY against synthetic patterns/handlers, never
touching any real bot module -- proves the collision detector itself is
correct in isolation, then separately confirms it validates cleanly
against every real bot's actual registrations (each bot's own main()
already calls registry.validate() at startup -- see study_hub_bot.py/
exam_hub_bot.py/faculty_bot.py -- so a real collision there is caught by
just running the bot; this file adds the synthetic positive/negative
controls those startup runs alone can't prove).

Run directly: `python smoke_test_callback_registry.py`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import callback_registry as cr  # noqa: E402

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


def check_raises(label, fn, exc_type=RuntimeError):
    try:
        fn()
        check(label, False)
    except exc_type:
        check(label, True)
    except Exception as e:
        check(f"{label} (raised {type(e).__name__}, expected {exc_type.__name__})", False)


async def _noop(update, context):
    return None


def main():
    print("=== smoke_test_callback_registry ===")

    # --- [1] _parse_prefixes() against every real pattern shape on this platform ---
    print("\n[1] _parse_prefixes() against real pattern shapes")
    real_patterns = {
        r"^(browse|cat|crs|lvl|subj|ed|pt|file|mainmenu):": {"browse", "cat", "crs", "lvl", "subj", "ed", "pt", "file", "mainmenu"},
        r"^(profile|profileconfirm):": {"profile", "profileconfirm"},
        r"^fuzzytrigger:": {"fuzzytrigger"},
        r"^(course|level|mode|subject|type|year|chapter|answer|pdf|next|mcqopt|restart|reportissue|imdone|sessprofile)(:|$)": {
            "course", "level", "mode", "subject", "type", "year", "chapter", "answer",
            "pdf", "next", "mcqopt", "restart", "reportissue", "imdone", "sessprofile",
        },
        r"^walletrc(:|$)": {"walletrc"},
        r"^hub:": {"hub"},
    }
    for pattern, expected in real_patterns.items():
        prefixes, parseable = cr._parse_prefixes(pattern)
        check(f"parses {pattern!r} correctly", parseable and prefixes == expected)
    prefixes_none, parseable_none = cr._parse_prefixes(None)
    check("None pattern parses as 'matches everything' (prefixes=None, parseable=True)", prefixes_none is None and parseable_none is True)

    # --- [2] Unparseable pattern -- logged, not raised ------------------------------
    print("\n[2] Unparseable pattern")
    weird_prefixes, weird_parseable = cr._parse_prefixes(r"^foo.*bar$")
    check("a pattern outside the known shapes is flagged unparseable", weird_parseable is False)

    reg = cr.CallbackRegistry("_smoketest")
    reg.callback_handler(_noop, pattern=r"^foo.*bar$", label="weird_handler")
    reg.callback_handler(_noop, pattern=r"^(a|b):", label="normal_handler")
    try:
        reg.validate()
        check("validate() does NOT raise just because one pattern is unparseable", True)
    except Exception:
        check("validate() does NOT raise just because one pattern is unparseable", False)

    # --- [3] No collision -- real, non-overlapping patterns ------------------------
    print("\n[3] No collision (real shape)")
    reg2 = cr.CallbackRegistry("_smoketest")
    reg2.callback_handler(_noop, pattern=r"^(a|b|c):", label="handler1")
    reg2.callback_handler(_noop, pattern=r"^(d|e):", label="handler2")
    reg2.callback_handler(_noop, pattern=r"^single:", label="handler3")
    try:
        reg2.validate()
        check("validate() passes for genuinely non-overlapping patterns", True)
    except Exception as e:
        check(f"validate() passes for genuinely non-overlapping patterns (raised: {e})", False)

    # --- [4] Real collision -- two handlers claim the same prefix -------------------
    print("\n[4] Real collision detected")
    reg3 = cr.CallbackRegistry("_smoketest")
    reg3.callback_handler(_noop, pattern=r"^(a|b|report):", label="handler_x")
    reg3.callback_handler(_noop, pattern=r"^(report|reportconfirm):", label="handler_y")
    check_raises("validate() raises when two handlers both claim 'report'", reg3.validate)

    # --- [5] Unrestricted (None) pattern alongside another handler -----------------
    print("\n[5] Unrestricted pattern alongside another handler")
    reg4 = cr.CallbackRegistry("_smoketest")
    reg4.callback_handler(_noop, pattern=None, label="catch_all_handler")
    reg4.callback_handler(_noop, pattern=r"^report:", label="report_handler")
    check_raises("validate() raises when an unrestricted handler coexists with another", reg4.validate)

    # --- [6] A SOLE unrestricted handler is fine ------------------------------------
    print("\n[6] A sole unrestricted handler is fine")
    reg5 = cr.CallbackRegistry("_smoketest")
    reg5.callback_handler(_noop, pattern=None, label="only_handler")
    try:
        reg5.validate()
        check("validate() passes when the unrestricted handler is the ONLY one registered", True)
    except Exception as e:
        check(f"validate() passes when the unrestricted handler is the ONLY one registered (raised: {e})", False)

    # --- [7] assert_callback_data_length() ------------------------------------------
    print("\n[7] assert_callback_data_length()")
    try:
        cr.assert_callback_data_length("chapter:3")
        check("a short callback_data string passes", True)
    except ValueError:
        check("a short callback_data string passes", False)
    check_raises("a callback_data string over 64 bytes raises ValueError", lambda: cr.assert_callback_data_length("chapter:" + "x" * 80), ValueError)
    # UTF-8 byte length, not character count -- a multi-byte character
    # could pass a naive len() check while still exceeding Telegram's real
    # (byte-based) limit.
    check_raises(
        "byte length (not character count) is what's checked",
        lambda: cr.assert_callback_data_length("x:" + ("₹" * 40)),  # rupee sign, 3 bytes each in UTF-8
        ValueError,
    )

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
