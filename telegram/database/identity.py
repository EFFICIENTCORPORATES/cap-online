"""
telegram/database/identity.py -- auto-provisioned 1LAVYA username (2026-08-16)
--------------------------------------------------------------------------------
Built so the wallet system (telegram/database/wallet.py) can debit ANY
student's balance without first forcing them through profile_flow.py's
manual username-setup UI -- Pranav's explicit call, 2026-08-16 (see
telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md §0/§9): "fetch their
Telegram @username... so we can silently use that in background without any
friction." Confirmed at the time of writing: 96 real students exist, only 1
has ever set up a 1LAVYA username manually -- gating the wallet on the
existing opt-in flow would have blocked 95 of them from free practice the
moment wallet-gating went live.

HOW: reuses profile_flow.py's EXACT username-creation pattern (INSERT
student_profiles, then UPDATE students.lavya_username) and its EXACT
validation rule (3-20 chars, alphanumeric + underscore, case-insensitive
uniqueness via student_profiles.username's own COLLATE NOCASE) -- an
auto-provisioned username is indistinguishable in the DB from one a student
typed in by hand, and is bound by the exact same rule profile_flow.py
already states to students: PERMANENT, never editable, once set (see that
module's own docstring and its `_profile_summary_text()`, which literally
renders "(permanent, cannot be changed)" the moment a student checks
"profile" -- auto-assigning a username and later claiming it can still be
edited would make that on-screen text a lie; this module does not do that).

PRECEDENCE: a student's Telegram @username, if they have one, is a valid
format, and isn't already claimed by a different student -- else a
deterministic `tg{telegram_user_id}` placeholder (always valid, always
unique, since telegram_user_id itself is unique). Telegram usernames are
NOT used as a live, ongoing key (a student can change their Telegram handle
any time in Telegram's own settings) -- this module only ever reads it ONCE,
at first-provision time, to seed the (thereafter-permanent) 1LAVYA username;
changing your Telegram handle later has no effect on your already-claimed
1LAVYA identity, by design.

NOT a competing identity system -- this IS the same student_profiles/
students.lavya_username system profile_flow.py already owns. A student who
was auto-provisioned can still type "profile" any time to view what got set
and fill in the rest (display name, course, level, etc.) -- they just never
get offered a *different* username, same as any other student.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402
import wallet  # noqa: E402

MIN_USERNAME_LEN, MAX_USERNAME_LEN = 3, 20  # mirrors profile_flow.py's own MIN/MAX exactly -- keep in sync if that ever changes


def _valid_username(text: str):
    """Mirrors profile_flow.py's _valid_username() exactly -- duplicated
    rather than imported to avoid a circular import (profile_flow.py is a
    bots/ module that itself may end up importing this one later; this
    module stays a pure database/ leaf with no bots/ dependency)."""
    text = (text or "").strip()
    if not (MIN_USERNAME_LEN <= len(text) <= MAX_USERNAME_LEN):
        return None
    if not all(c.isalnum() or c == "_" for c in text):
        return None
    return text


def ensure_wallet_identity(conn, telegram_user) -> tuple:
    """telegram_user: a telegram.User (or anything with .id and .username
    attributes). MUST be called after db.upsert_student() for this user in
    the same request -- this function only UPDATEs an existing students
    row, it does not create one.

    Returns (username: str, was_auto_created: bool). If this chat_id
    already has a linked username (auto-provisioned earlier, or set up
    manually via profile_flow.py), returns it immediately with
    was_auto_created=False -- idempotent, cheap to call on every message
    that might need a wallet operation, same spirit as upsert_student()
    itself."""
    telegram_user_id = telegram_user.id
    row = conn.execute(
        "SELECT lavya_username FROM students WHERE telegram_user_id=?", (telegram_user_id,)
    ).fetchone()
    if row and row[0]:
        return row[0], False

    candidate = _valid_username(getattr(telegram_user, "username", None))
    if candidate:
        taken = conn.execute("SELECT 1 FROM student_profiles WHERE username=?", (candidate,)).fetchone()
        if taken:
            candidate = None  # someone else already claimed this exact handle -- fall through to the placeholder

    username = candidate or f"tg{telegram_user_id}"
    now = db.now()

    existing_profile = conn.execute("SELECT 1 FROM student_profiles WHERE username=?", (username,)).fetchone()
    if not existing_profile:
        db.execute_with_retry(
            conn, "INSERT INTO student_profiles (username, created_at, updated_at) VALUES (?,?,?)",
            (username, now, now),
        )
    db.execute_with_retry(
        conn, "UPDATE students SET lavya_username=? WHERE telegram_user_id=?",
        (username, telegram_user_id),
    )

    # BUG FIXED 2026-08-24 (real complaint: newly-enrolled students hitting
    # "recharge your wallet" on their very first question, no welcome-bonus
    # message ever shown). Root cause: this exact same "identity provisioned,
    # bonus never granted" gap was already found and fixed once, 2026-08-17,
    # but only at ONE call site (faculty_bot.py's "Exam Practice Hub"
    # button) -- exam_hub_bot.py's own send_question()/send_mcq(), plus
    # test_flow.py and wallet_flow.py (all built after that fix), each call
    # ensure_wallet_identity() directly and independently, the same
    # unguarded way the fixed call site used to. Patching each call site
    # individually is exactly how it recurred -- fixing it HERE instead
    # means every existing AND future caller is safe by construction: the
    # instant a username is auto-created anywhere on the platform, the
    # one-time signup grant is applied in the same breath, before this
    # function ever returns to whichever flow needs the balance next.
    # grant_signup_bonus() is itself idempotent (checked by
    # wallet_grants + a ledger idempotency_key), so callers that ALSO
    # explicitly grant afterward (db_ensure_wallet(), for the welcome
    # message) never double-grant -- this call is always a safe no-op on
    # the (common) path where the bonus was already applied here first.
    wallet.grant_signup_bonus(conn, username, "platform")
    return username, True
