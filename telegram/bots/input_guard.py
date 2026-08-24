"""
telegram/bots/input_guard.py -- shared free-text sanitization + upload
validation (2026-08-24, SECURITY.md §3.A.4 / §3.A.6, Phase 1)
--------------------------------------------------------------------------------
Same shape as contact_utils.py/telegram_safety.py: a dependency-free leaf
module any bot can import with zero circular-import risk.

TWO separate concerns bundled here because SECURITY.md itself groups them
under one "input validation" heading, not because they share implementation:

1. sanitize_free_text() -- a standing rule for any free-text field this
   platform collects (a search query, a profile display name, an MCQ-issue
   description, ...). contact_utils.py already validates mobile/email
   FORMAT; this is the complementary, more basic guard every OTHER
   free-text field should apply: bound the length (nothing on this
   platform legitimately needs megabytes of text) and strip control
   characters -- Telegram will happily forward whatever a client sends,
   with no guarantee "text" is free of null bytes, ANSI escape sequences,
   or other junk that could corrupt a log line, a generated PDF, or a
   stored filename downstream. This is a HYGIENE pass, not a correctness
   check -- it never rejects input outright, it just bounds/cleans
   whatever gets logged, stored, or echoed back.

2. validate_upload() -- MyFiles Hub-specific (telegram/bots/
   myfiles_hub_bot.py is the only bot that stores arbitrary
   student-uploaded files long-term). Telegram's own Bot API already
   refuses to hand a bot any file over 20MB (a real, already-existing
   backstop -- SECURITY.md §1/§3.A.6), so MAX_UPLOAD_BYTES below is stated
   explicitly rather than only relied on implicitly (so a future change to
   Telegram's own ceiling doesn't silently raise ours too). The part
   Telegram's limit does NOT cover is file TYPE -- this adds a DENY-list of
   executable/script extensions so MyFiles Hub (a personal file locker,
   not a narrowly-typed feature) can't quietly become a redistribution
   point for a .exe/.apk/.ps1 a student uploads and later retrieves/shares
   via "send to me"/"send all". Deliberately a deny-list, not an
   allow-list -- a student's own PDFs/photos/docs/zips are all legitimate
   personal-storage content; guessing every legitimate extension up front
   would be both incomplete and a worse student experience than blocking
   the specific, genuinely dangerous handful.
"""

import re

MAX_FREE_TEXT_LEN = 500  # generous for a search query or an issue description; nothing on this platform legitimately needs more

# Keep \t \n \r (0x09/0x0a/0x0d) -- real multi-line student input. Strip the
# rest of the C0 control range plus DEL (0x7f).
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_free_text(text: str | None, max_len: int = MAX_FREE_TEXT_LEN) -> str:
    """Never raises -- a None/non-string input returns ''."""
    if not isinstance(text, str):
        return ""
    cleaned = _CONTROL_CHARS_RE.sub("", text)
    return cleaned.strip()[:max_len]


# ---------------------------------------------------------------------------
# MyFiles Hub upload validation
# ---------------------------------------------------------------------------
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # matches Telegram's own bot-download ceiling -- see module docstring

BLOCKED_UPLOAD_EXTENSIONS = {
    ".exe", ".msi", ".bat", ".cmd", ".com", ".scr", ".ps1", ".psm1",
    ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".hta", ".jar",
    ".apk", ".dll", ".sh", ".bin", ".reg", ".lnk", ".cpl", ".gadget",
}


def validate_upload(filename: str | None, file_size: int | None) -> tuple[bool, str | None]:
    """Returns (ok, reason). `reason` is a short, student-facing
    explanation when ok is False -- never an internal detail. Called
    BEFORE downloading the file, so a rejected upload never touches disk."""
    if file_size is not None and file_size > MAX_UPLOAD_BYTES:
        return False, (
            f"That file is too large ({file_size // (1024 * 1024)}MB) -- "
            f"MyFiles Hub can only store files up to {MAX_UPLOAD_BYTES // (1024 * 1024)}MB."
        )
    name = (filename or "").strip().lower()
    for ext in BLOCKED_UPLOAD_EXTENSIONS:
        if name.endswith(ext):
            return False, (
                "That file type isn't allowed here -- MyFiles Hub is for documents, "
                "photos, and study material, not executable/script files."
            )
    return True, None
