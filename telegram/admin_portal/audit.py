"""
telegram/admin_portal/audit.py -- admin_actions audit trail (2026-08-11)
--------------------------------------------------------------------------------
One function every route that performs a real, production-affecting action
(bot restart today; master edits/faculty addition/leaderboard edits in
later phases) calls exactly once, after the action completes (successfully
or not) -- see schema.sql's own comment on admin_actions for why this
exists. Never raises -- logging an action must never be the reason the
action itself appears to fail to the person who just did it.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402

logger = logging.getLogger(__name__)


def log_action(conn, username: str, action_type: str, target: str = None, detail: str = None):
    try:
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO admin_actions (username, action_type, target, detail, created_at) VALUES (?,?,?,?,?)",
            (username, action_type, target, detail, platform_db.now()),
        )
    except Exception:
        logger.exception(f"log_action failed (username={username}, action_type={action_type}, target={target})")
