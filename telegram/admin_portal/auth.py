"""
telegram/admin_portal/auth.py -- login/session/RBAC-ready auth (2026-08-11)
--------------------------------------------------------------------------------
Single-admin login for this build (Pranav's confirmed choice, 2026-08-11:
"single admin login now, RBAC layered on later" -- not a no-auth system
that gets ripped out under time pressure once real RBAC arrives). Every
protected route already goes through role_required(), not a bare
login_required() -- today only "admin" exists and every route requires it,
but adding a second role later (student/faculty/manager -- per the
platform's own long-stated plan) is a decorator-argument change per route,
not a redesign of how routes are protected.

Credentials live in telegram/.env (gitignored): ADMIN_PORTAL_USERNAME,
ADMIN_PORTAL_PASSWORD_HASH (werkzeug's own scrypt-based hash -- the
plaintext is never stored anywhere after generation), ADMIN_PORTAL_SECRET_KEY
(Flask session-signing key). Rotate either via set_password.py.
"""

import os
import functools

from flask import session, redirect, url_for, request
from werkzeug.security import check_password_hash


def _admin_username() -> str:
    return os.environ.get("ADMIN_PORTAL_USERNAME", "")


def _admin_password_hash() -> str:
    return os.environ.get("ADMIN_PORTAL_PASSWORD_HASH", "")


def verify_credentials(username: str, password: str) -> bool:
    real_username = _admin_username()
    real_hash = _admin_password_hash()
    if not real_username or not real_hash:
        return False
    if username != real_username:
        return False
    return check_password_hash(real_hash, password)


def current_user():
    return session.get("username")


def current_role():
    return session.get("role")


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
