"""
telegram/admin_portal/auth.py -- login/session/RBAC-ready auth (2026-08-11,
extended 2026-08-17 for the bot_admin role)
--------------------------------------------------------------------------------
Single-SUPER-admin login was this build's original scope (Pranav's
confirmed choice, 2026-08-11: "single admin login now, RBAC layered on
later" -- not a no-auth system that gets ripped out under time pressure
once real RBAC arrives). That account (role "admin", telegram/.env's
ADMIN_PORTAL_USERNAME/PASSWORD_HASH, rotated via set_password.py) is
COMPLETELY UNCHANGED here -- it still sees every route unconditionally,
exactly as before this file was touched.

2026-08-17 (part of the Phase 1 logging build, see
telegram/LOGGING-ARCHITECTURE.md): added a genuinely SECOND role,
"bot_admin" -- a faculty-scoped account that can log in via a row in the
admin_accounts DB table (see manage_bot_admin.py) and see ONLY the
Activity Log page, ONLY for the bot_id(s) listed for their username in
telegram/config/admin_access.json (see that file's own README for the
full two-step activation process). Every OTHER existing route still
requires role_required("admin") exactly as it did before -- a bot_admin
account is structurally incapable of reaching them, without a single
line of those routes changing, because "admin" and "bot_admin" are
different strings and role_required() only checks membership.

Credentials, two places on purpose (see LOGGING-ARCHITECTURE.md §... /
admin_access.README.md for the full "why two places" reasoning):
telegram/.env for the one super-admin account (gitignored, hand-edited);
the admin_accounts DB table for every bot_admin account (created via
manage_bot_admin.py, never touches .env -- this platform can have more
than one bot_admin, .env only ever held ONE set of credentials).
"""

import os
import sys
import json
import functools
from pathlib import Path

from flask import session, redirect, url_for, request
from werkzeug.security import check_password_hash, generate_password_hash  # noqa: F401 -- generate_password_hash re-exported for manage_bot_admin.py's convenience, kept here so both password-hashing call sites use the exact same werkzeug import path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402

ADMIN_ACCESS_JSON = REPO_ROOT / "telegram" / "config" / "admin_access.json"


def _admin_username() -> str:
    return os.environ.get("ADMIN_PORTAL_USERNAME", "")


def _admin_password_hash() -> str:
    return os.environ.get("ADMIN_PORTAL_PASSWORD_HASH", "")


def verify_credentials(username: str, password: str) -> bool:
    """The one super-admin account. Unchanged behavior."""
    real_username = _admin_username()
    real_hash = _admin_password_hash()
    if not real_username or not real_hash:
        return False
    if username != real_username:
        return False
    return check_password_hash(real_hash, password)


def _bot_admin_scope_map() -> dict:
    """username (lowercased) -> bot_ids, for every ACTIVE entry in
    admin_access.json. Re-read on every call (not cached) -- deliberately,
    so editing the JSON and restarting the portal is the only step needed,
    same "config file is the live source of truth" behavior every other
    JSON config on this platform already has."""
    if not ADMIN_ACCESS_JSON.exists():
        return {}
    try:
        data = json.loads(ADMIN_ACCESS_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        e["username"].lower(): e.get("bot_ids", [])
        for e in data.get("bot_admins", [])
        if e.get("status") == "active" and e.get("username")
    }


def verify_bot_admin_credentials(username: str, password: str) -> bool:
    """A bot_admin account (admin_accounts DB table). Returns True only if
    BOTH the login is valid AND admin_access.json currently grants this
    username real, active scope -- a DB account with no active JSON entry
    (yet, or anymore) cannot log in at all, not "logs in but sees
    nothing," so a revoked bot_admin is fully locked out the moment their
    admin_access.json entry is deactivated, without needing to also touch
    admin_accounts."""
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    row = conn.execute(
        "SELECT password_hash FROM admin_accounts WHERE username=?", (username,)
    ).fetchone()
    if not row or not check_password_hash(row[0], password):
        return False
    return username.lower() in _bot_admin_scope_map()


def bot_admin_allowed_bot_ids(username: str) -> list:
    return _bot_admin_scope_map().get(username.lower(), [])


# ---------------------------------------------------------------------------
# LOGIN ATTEMPT LOGGING + LOCKOUT (2026-08-18) -- LOGGING-ARCHITECTURE.md
# sec7's "security logs" item, the cheap slice built now rather than fully
# deferred: this portal controls live bot restarts and (with Test Mode
# billing live) touches real money, and had ZERO record of anyone trying
# to brute-force the login before this. Covers BOTH the super-admin and
# every bot_admin account -- one shared table, one shared check, since
# they share one login route.
# ---------------------------------------------------------------------------
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15   # both the window failures are counted over AND the effective lockout length -- a rolling window, no separate "unlock" step needed; it just ages out


def log_login_attempt(username: str, success: bool, remote_addr: str | None):
    """Best-effort, never blocks the actual login outcome -- a logging
    failure here must not turn a correct login into a rejected one, same
    "logging must never break the product" principle activity_logger.py
    already established."""
    try:
        conn = platform_db.get_connection()
        platform_db.init_schema(conn)
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO admin_login_attempts (username, success, remote_addr) VALUES (?, ?, ?)",
            (username, 1 if success else 0, remote_addr),
        )
    except Exception:
        pass


def is_locked_out(username: str) -> bool:
    """True if this username has MAX_FAILED_ATTEMPTS or more failed
    attempts within the last LOCKOUT_WINDOW_MINUTES. Checked BEFORE
    verifying a submitted password, so a locked-out account is refused
    even with the CORRECT password -- the whole point of a lockout.
    Best-effort: a DB read failure here fails OPEN (returns False, i.e.
    "not locked out") rather than permanently locking every admin out of
    their own portal because of an unrelated DB hiccup -- a lockout
    false-negative is recoverable (the attempt just gets logged and
    counted next time); a false-positive that can never be checked again
    is not."""
    try:
        conn = platform_db.get_connection()
        platform_db.init_schema(conn)
        row = conn.execute(
            "SELECT COUNT(*) FROM admin_login_attempts "
            "WHERE username = ? AND success = 0 "
            "AND created_at >= strftime('%Y-%m-%dT%H:%M:%fZ', 'now', ?)",
            (username, f"-{LOCKOUT_WINDOW_MINUTES} minutes"),
        ).fetchone()
        return bool(row and row[0] >= MAX_FAILED_ATTEMPTS)
    except Exception:
        return False


def current_user():
    return session.get("username")


def current_role():
    return session.get("role")


def current_allowed_bot_ids():
    """None for a super-admin (unrestricted -- sees every bot); a list
    (possibly empty) for a bot_admin. Routes that show per-bot data should
    always check this, not just the role, before deciding what to show."""
    return session.get("allowed_bot_ids")  # None if absent -- see login()'s own comment on why super-admin sessions never set this key at all


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    """Every real page/action route in this app wraps with this, even
    though only 'admin' exists today -- see module docstring. Returns a
    plain 403 (not a redirect) for a logged-in user lacking the role,
    since that's a real "you can't do this" state, distinct from "you're
    not logged in at all" (which login_required's redirect already
    covers, always checked first)."""
    def decorator(view):
        @functools.wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_role() not in roles:
                return "Forbidden -- your role does not have access to this page.", 403
            return view(*args, **kwargs)
        return wrapped
    return decorator
