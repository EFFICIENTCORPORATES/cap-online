#!/usr/bin/env python3
"""
telegram/admin_portal/set_password.py -- generate/rotate Admin Portal
login credentials (2026-08-11)
--------------------------------------------------------------------------------
Never writes telegram/.env directly (this repo's convention -- .env is
gitignored, hand-edited, never machine-written by a routine script) --
prints the three lines to paste in yourself, same as the values already
there were generated. The plaintext password is shown ONCE, here, and
never stored anywhere -- only its hash goes in .env.

USAGE:
    python telegram/admin_portal/set_password.py <username>
        Generates a new random password for <username>, prints it once.

    python telegram/admin_portal/set_password.py <username> <password>
        Hashes the password YOU chose instead of generating one.
"""

import sys
import secrets
from werkzeug.security import generate_password_hash


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python set_password.py <username> [password]")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) == 3 else secrets.token_urlsafe(12)
    password_hash = generate_password_hash(password)
    secret_key = secrets.token_hex(32)

    print("\nPaste these into telegram/.env (replacing any existing ADMIN_PORTAL_* lines):\n")
    print(f"ADMIN_PORTAL_USERNAME={username}")
    print(f"ADMIN_PORTAL_PASSWORD_HASH={password_hash}")
    print(f"ADMIN_PORTAL_SECRET_KEY={secret_key}")
    print(f"\nYour password (shown once, not recoverable from .env): {password}")
    print("\nRestart the 1lavya-admin-portal process for this to take effect:")
    print("    python telegram/tools/manage_bots.py restart 1lavya-admin-portal")


if __name__ == "__main__":
    main()
