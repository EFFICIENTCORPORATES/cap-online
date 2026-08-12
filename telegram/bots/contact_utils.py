"""
telegram/bots/contact_utils.py -- shared mobile/email validation
(2026-08-11)
--------------------------------------------------------------------------------
Extracted out of report_flow.py when profile_flow.py needed the exact same
mobile/email validation for its own email/mobile edit steps -- one
definition, not two copies that could drift (same "single source of
truth" discipline this repo already applies everywhere else, e.g.
CLAUDE.md section 7 for print CSS, telegram/database/analytics.py for
dashboard queries).
"""

import re

# Deliberately loose but not accept-anything: catches the obviously-wrong
# cases (no @ at all, not 10 digits) before even offering an echo-confirm
# step on something that couldn't possibly be right -- not a claim of full
# RFC-5322/E.164 validation.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOBILE_RE = re.compile(r"^(?:\+?91|0)?([6-9]\d{9})$")


def normalize_mobile(text: str) -> str | None:
    # Strip spaces/hyphens FIRST -- real users type "98765 43210" or
    # "+91-98765-43210" (common 5+5 Indian grouping), not always one
    # contiguous digit run. A regex trying to encode every separator
    # position directly missed exactly this case in testing before this
    # fix (2026-08-11, report_flow.py) -- normalize away formatting, then
    # match a clean pattern.
    cleaned = re.sub(r"[\s\-]", "", text.strip())
    m = MOBILE_RE.match(cleaned)
    return m.group(1) if m else None


def valid_email(text: str) -> bool:
    return bool(EMAIL_RE.match(text.strip()))
