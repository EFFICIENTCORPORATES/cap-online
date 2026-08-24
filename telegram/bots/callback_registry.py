"""
telegram/bots/callback_registry.py -- central callback_data route registry
(2026-08-24, SECURITY.md §3.A.5/§4.5)
--------------------------------------------------------------------------------
Not a new bug -- promoting an already-documented, already-recurred-3+-times
bug class (see /CLAUDE.md's own "known scale-readiness gaps" callout:
"regex pattern collisions swallowing another handler's buttons", plus a
real 64-byte callback_data overflow found 2026-08-12 in exam_hub_bot.py's
chapter picker that silently broke an entire keyboard) to "fix the class,
not the next instance." SECURITY.md frames this as security-adjacent
because an attacker who understands this bug class could deliberately
craft input to trigger it, turning a correctness bug into a targeted
denial-of-service against one specific menu.

WHAT THIS DOES: every bot's main() already registers each
CallbackQueryHandler with an explicit `pattern=` restricting which
callback_data prefixes it claims (the fix already applied 2026-08-10/
2026-08-11 after the first two incidents of this bug class). What was
still missing: nothing verified, AT STARTUP, that two different handlers'
patterns don't actually claim the SAME prefix -- a collision would mean
python-telegram-bot always calls whichever handler was registered first
for a matching update, and the second handler's buttons never fire at
all. CallbackRegistry.validate() below makes that an explicit, loud,
fail-fast startup check instead of something a human has to notice by
reading every pattern by eye.

SCOPE, STATED HONESTLY: this platform's callback_data convention is
already narrow and consistent -- every real pattern in every bot's main()
is one of:
  - a bare literal prefix:      r"^fuzzytrigger:"
  - an alternation of literals: r"^(course|level|mode|...)(:|$)"
  - None (matches everything -- valid ONLY if it's the sole handler
    registered; a collision is certain otherwise)
_parse_prefixes() below recognises exactly these three shapes and nothing
more -- this is deliberately NOT a general regex-intersection solver (that
problem is undecidable for arbitrary regexes). A pattern written some
other way is flagged UNPARSEABLE (a loud WARNING, not silently assumed
safe) rather than either crashing startup or giving a false sense of
security -- a human still has to eyeball that one specifically.

USAGE, at registration time in each bot's main() (a drop-in replacement
for constructing CallbackQueryHandler directly):

    registry = CallbackRegistry(BOT_ID)
    app.add_handler(registry.callback_handler(handler_func, pattern=r"^(a|b)(:|$)", label="button_router"))
    ...
    registry.validate()   # once, after every registration, BEFORE app.run_polling()

LENGTH CHECKING: assert_callback_data_length() is a separate, reusable
helper for a flow module BUILDING a callback_data string from dynamic data
(a chapter slug, a filename) to call defensively at construction time --
this registry has no way to enumerate every string a flow might build at
RUNTIME, so it cannot catch the 64-byte class of bug the way it catches
pattern collisions at STARTUP. Existing call sites already work around
this (a small integer index instead of the raw dynamic string, per the
2026-08-07/2026-08-12 fixes) -- this helper is for any NEW callback_data
construction to self-check against, not a retrofit of already-fixed sites.

NOT applied to myfiles_hub_bot.py: its routing is a python-telegram-bot
ConversationHandler, a structurally different (and inherently collision-
safe) mechanism -- each conversation STATE has its own explicit, small
handler list, so two handlers can never silently compete for the same
callback_data the way a flat, bot-wide handler list can. This registry
exists for the flat-list shape study_hub_bot.py/exam_hub_bot.py/
faculty_bot.py actually use.
"""

import re
import logging

logger = logging.getLogger(__name__)

MAX_CALLBACK_DATA_BYTES = 64  # Telegram's own hard limit on callback_data


def assert_callback_data_length(value: str, *, context: str = ""):
    """Raises ValueError if `value`, encoded as UTF-8 (what Telegram
    actually counts), exceeds Telegram's 64-byte callback_data limit. Call
    this at the point a flow module BUILDS a dynamic callback_data string,
    before handing it to an InlineKeyboardButton -- catches the exact bug
    class found 2026-08-07 (Study Hub's file picker) and 2026-08-12 (Exam
    Hub's chapter picker) at construction time, instead of only surfacing
    when a real student's tap silently does nothing."""
    n = len(value.encode("utf-8"))
    if n > MAX_CALLBACK_DATA_BYTES:
        raise ValueError(
            f"callback_data exceeds Telegram's {MAX_CALLBACK_DATA_BYTES}-byte limit "
            f"({n} bytes): {value!r}" + (f" ({context})" if context else "")
        )


# Matches r"^(a|b|c)(:|$)" or r"^(a|b|c):" -- an alternation of bare
# word-characters at the very start of the pattern.
_ALTERNATION_RE = re.compile(r"^\^\(([a-zA-Z0-9_|]+)\)(?:\(:\|\$\)|:)?$")
# Matches r"^literal:" or r"^literal(:|$)" -- a single bare literal prefix.
_LITERAL_RE = re.compile(r"^\^([a-zA-Z0-9_]+)(?:\(:\|\$\)|:)?$")


def _parse_prefixes(pattern):
    """Returns (prefixes, parseable). prefixes is a set[str] of the
    literal callback_data prefixes this pattern claims, or None if the
    pattern matches EVERYTHING (pattern is None/""). parseable is False
    when this pattern doesn't match any of the three shapes this registry
    understands -- see module docstring's SCOPE note."""
    if pattern is None or pattern == "":
        return None, True
    m = _ALTERNATION_RE.match(pattern)
    if m:
        return set(m.group(1).split("|")), True
    m = _LITERAL_RE.match(pattern)
    if m:
        return {m.group(1)}, True
    return None, False


class CallbackRegistry:
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self._registrations = []  # [(pattern, label), ...]

    def callback_handler(self, func, pattern=None, label=None):
        """Returns a real telegram.ext.CallbackQueryHandler, exactly as
        `CallbackQueryHandler(func, pattern=pattern)` would -- a drop-in
        replacement for that constructor call that also records the
        registration for validate() to check. `telegram.ext` is imported
        lazily so this module has no hard python-telegram-bot dependency
        for a caller that only wants assert_callback_data_length()."""
        from telegram.ext import CallbackQueryHandler
        self._registrations.append((pattern, label or getattr(func, "__name__", "?")))
        return CallbackQueryHandler(func, pattern=pattern)

    def validate(self):
        """Call once, after every handler for this bot has been
        registered, BEFORE app.run_polling(). Raises RuntimeError on a
        real prefix collision or on an unrestricted (None) pattern
        coexisting with any other handler -- both are exactly the bug
        class this module exists to catch, and both are cheap/certain to
        fix once caught, so failing the whole startup loudly is the right
        call (same "fail fast at startup" discipline this platform's own
        wallet_ledger/course_catalog migrations already use for a
        detected data-shape problem). An UNPARSEABLE pattern only logs a
        WARNING -- see module docstring's SCOPE note; this registry can't
        prove that one safe OR unsafe, so it doesn't pretend to."""
        parsed = []
        for pattern, label in self._registrations:
            prefixes, parseable = _parse_prefixes(pattern)
            if not parseable:
                logger.warning(
                    f"callback_registry[{self.bot_id}]: pattern for '{label}' ({pattern!r}) "
                    f"doesn't match this registry's known shapes -- NOT collision-checked. "
                    f"Verify manually that it can't swallow another handler's callback_data."
                )
                continue
            parsed.append((label, pattern, prefixes))

        catch_alls = [label for label, _pattern, prefixes in parsed if prefixes is None]
        if catch_alls and len(parsed) > 1:
            raise RuntimeError(
                f"callback_registry[{self.bot_id}]: handler(s) {catch_alls} have an "
                f"UNRESTRICTED pattern (matches every callback_data) registered "
                f"alongside {len(parsed) - len(catch_alls)} other handler(s) -- this "
                f"WILL silently swallow their buttons. Give it an explicit `pattern=`."
            )

        for i in range(len(parsed)):
            label_i, pattern_i, prefixes_i = parsed[i]
            if prefixes_i is None:
                continue
            for j in range(i + 1, len(parsed)):
                label_j, pattern_j, prefixes_j = parsed[j]
                if prefixes_j is None:
                    continue
                overlap = prefixes_i & prefixes_j
                if overlap:
                    raise RuntimeError(
                        f"callback_registry[{self.bot_id}]: handlers '{label_i}' ({pattern_i!r}) "
                        f"and '{label_j}' ({pattern_j!r}) both claim callback_data prefix(es) "
                        f"{sorted(overlap)} -- one will silently swallow the other's buttons. "
                        f"Scope the patterns so they don't overlap."
                    )

        logger.info(
            f"callback_registry[{self.bot_id}]: validated {len(parsed)}/{len(self._registrations)} "
            f"handler pattern(s), 0 collisions."
        )
