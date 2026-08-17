#!/usr/bin/env python3
"""
telegram/admin_portal/manage_bot_admin.py -- create/rotate/remove a
bot_admin login (2026-08-17)
--------------------------------------------------------------------------------
Companion to set_password.py, but for the NEW bot_admin role (see
telegram/config/admin_access.README.md for the full two-step activation
process) instead of the single super-admin account set_password.py manages.

Same "shown once, never stored" discipline as set_password.py: the
plaintext password is printed here and nowhere else -- only its hash is
written, this time to the admin_accounts DB table (not telegram/.env,
since this platform can have more than one bot_admin and .env only ever
held ONE set of admin credentials).

Creating a row here is only HALF of activating a real bot_admin -- see
telegram/config/admin_access.README.md's two-step process. This script
never touches admin_access.json itself (that's a hand-edited policy file,
same "never machine-written" convention telegram/.env already follows).

USAGE:
    python manage_bot_admin.py create <username> [password]
        Creates a new bot_admin login. Generates a random password if none
        given. Fails loudly if the username already exists -- use `reset`
        to rotate an existing one instead.

    python manage_bot_admin.py reset <username> [password]
        Rotates an existing bot_admin's password.

    python manage_bot_admin.py remove <username>
        Deletes the login entirely (does NOT touch admin_access.json --
        remove/deactivate that entry separately if the account should also
        lose its scope, not just its ability to log in).

    python manage_bot_admin.py list
        Shows every existing bot_admin username (no hashes), and whether
        each one has a matching active entry in admin_access.json.
"""

import sys
import json
import secrets
from pathlib import Path
from werkzeug.security import generate_password_hash

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402

ADMIN_ACCESS_JSON = REPO_ROOT / "telegram" / "config" / "admin_access.json"


def _conn():
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    return conn


def _load_scope_map() -> dict:
    """username -> bot_ids, for every ACTIVE entry in admin_access.json --
    used only by `list` below, to show whether a DB account actually has a
    real, live scope or is still a dangling login with nothing to see."""
    if not ADMIN_ACCESS_JSON.exists():
        return {}
    data = json.loads(ADMIN_ACCESS_JSON.read_text(encoding="utf-8"))
    return {
        e["username"].lower(): e["bot_ids"]
        for e in data.get("bot_admins", [])
        if e.get("status") == "active"
    }


def cmd_create(username: str, password: str = None):
    conn = _conn()
    existing = conn.execute("SELECT 1 FROM admin_accounts WHERE username=?", (username,)).fetchone()
    if existing:
        print(f"'{username}' already exists -- use 'reset' to rotate its password instead.")
        sys.exit(1)
    password = password or secrets.token_urlsafe(12)
    now = platform_db.now()
    platform_db.execute_with_retry(
        conn,
        "INSERT INTO admin_accounts (username, password_hash, created_at, updated_at) VALUES (?,?,?,?)",
        (username, generate_password_hash(password), now, now),
    )
    print(f"\nCreated bot_admin '{username}'.")
    print(f"Password (shown once, not recoverable): {password}")
    print(
        f"\nThis account can log in now, but sees NOTHING until you add/activate an entry for "
        f"'{username}' in telegram/config/admin_access.json -- see that file's own README."
    )


def cmd_reset(username: str, password: str = None):
    conn = _conn()
    existing = conn.execute("SELECT admin_id FROM admin_accounts WHERE username=?", (username,)).fetchone()
    if not existing:
        print(f"No bot_admin account named '{username}' -- use 'create' instead.")
        sys.exit(1)
    password = password or secrets.token_urlsafe(12)
    platform_db.execute_with_retry(
        conn, "UPDATE admin_accounts SET password_hash=?, updated_at=? WHERE username=?",
        (generate_password_hash(password), platform_db.now(), username),
    )
    print(f"\nPassword rotated for '{username}'.")
    print(f"New password (shown once, not recoverable): {password}")


def cmd_remove(username: str):
    conn = _conn()
    existing = conn.execute("SELECT 1 FROM admin_accounts WHERE username=?", (username,)).fetchone()
    if not existing:
        print(f"No bot_admin account named '{username}'.")
        sys.exit(1)
    platform_db.execute_with_retry(conn, "DELETE FROM admin_accounts WHERE username=?", (username,))
    print(
        f"Removed login for '{username}'. Remember: admin_access.json's own entry (if any) still "
        f"lists this username -- deactivate/remove it there too if it should also lose its scope."
    )


def cmd_list():
    conn = _conn()
    rows = conn.execute("SELECT username, created_at, updated_at FROM admin_accounts ORDER BY username").fetchall()
    scope_map = _load_scope_map()
    if not rows:
        print("No bot_admin accounts exist yet.")
        return
    print(f"{'username':<24} {'created_at':<22} {'active scope (bot_ids)'}")
    for username, created_at, _updated_at in rows:
        scope = scope_map.get(username.lower())
        scope_text = ", ".join(scope) if scope else "(none -- add/activate an admin_access.json entry)"
        print(f"{username:<24} {created_at:<22} {scope_text}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    action = sys.argv[1]
    if action == "create" and len(sys.argv) in (3, 4):
        cmd_create(sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else None)
    elif action == "reset" and len(sys.argv) in (3, 4):
        cmd_reset(sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else None)
    elif action == "remove" and len(sys.argv) == 3:
        cmd_remove(sys.argv[2])
    elif action == "list" and len(sys.argv) == 2:
        cmd_list()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
