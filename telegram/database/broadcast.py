"""
telegram/database/broadcast.py -- persistent, trackable broadcast messages
(2026-08-18)
--------------------------------------------------------------------------------
Pranav's explicit ask (after the 2026-08-17 welcome-bonus broadcast, which
was a one-off script with no persistence beyond a CSV on disk): "all these
broadcast message which are being done...should get stored in a persistent
table inside of a database..with all relevant details like timestamp,
category, chat id, bot id, message content html.. and also if we can track
their interactions on these message then the same should also get tracked
and stored so that we know how many students interacted with the message."

Two tables (schema.sql): `broadcast_campaigns` (one row per message, sent
once, to many people) and `broadcast_deliveries` (one row per recipient's
actual copy -- send outcome, and whether/how they interacted). Every
future broadcast should go through this module rather than being another
unlogged one-off script -- see create_campaign()/log_delivery()/
log_interaction() below.

INTERACTION TRACKING: real, not inferred. A broadcast that wants trackable
interaction embeds an inline button whose callback_data encodes the
campaign_id (see telegram/bots/report_flow.py's `report:bcast:<campaign_id
>:<bot_id>` branch, added alongside this module -- reuses the ALREADY-
REGISTERED `report:` CallbackQueryHandler pattern in every bot, so no bot
script needed a new handler registration at all, avoiding this codebase's
own documented callback-collision bug class). A tap calls log_interaction()
here, which stamps interacted_at on that exact recipient's delivery row --
never a guess from unrelated free-text activity.

Pure DB-layer module (no Telegram HTTP calls) -- same "testable without a
running bot" discipline wallet.py/identity.py/leaderboard_metrics.py
already follow. Telegram send mechanics (resolving which bot a recipient
can be DM'd through, the raw HTTP POST) live in
telegram/tools/broadcast_sender.py instead -- a campaign script imports
both.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402


def create_campaign(conn, category: str, message_text: str, message_html: str = None,
                     criteria_description: str = None, created_by: str = None) -> int:
    """One row per broadcast message (the template/definition, not any one
    recipient's copy). Returns the new campaign_id."""
    db.execute_with_retry(
        conn,
        "INSERT INTO broadcast_campaigns (category, message_text, message_html, criteria_description, created_by, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (category, message_text, message_html, criteria_description, created_by, db.now()),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def log_delivery(conn, campaign_id: int, telegram_user_id: int, bot_id: str, message_text: str,
                  status: str, error_detail: str = None) -> int:
    """One row per recipient's actual copy. `message_text` is the REAL text
    sent to THIS recipient (may be personalized, e.g. their own MCQ count)
    -- always stored per-row, never assumed identical to the campaign's own
    template. `status` must be 'sent' or 'failed' (schema CHECK). Returns
    the new delivery_id."""
    db.execute_with_retry(
        conn,
        "INSERT INTO broadcast_deliveries (campaign_id, telegram_user_id, bot_id, message_text, sent_at, status, error_detail) "
        "VALUES (?,?,?,?,?,?,?)",
        (campaign_id, telegram_user_id, bot_id, message_text, db.now(), status, error_detail),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def log_interaction(conn, campaign_id: int, telegram_user_id: int, interaction_type: str) -> bool:
    """Stamps interacted_at on this recipient's delivery row for this
    campaign -- the FIRST interaction only (a second tap doesn't overwrite
    the original timestamp, matching "when did they first respond" being
    the more useful fact than "when did they last click"). Returns True if
    a matching delivery row was found and updated, False otherwise (e.g. a
    stale/replayed callback_data referencing a campaign_id that was never
    actually sent to this chat_id -- logged as a no-op, never crashes the
    caller). Safe to call more than once per recipient (idempotent on the
    already-interacted case)."""
    row = conn.execute(
        "SELECT delivery_id, interacted_at FROM broadcast_deliveries WHERE campaign_id=? AND telegram_user_id=? "
        "ORDER BY delivery_id DESC LIMIT 1",
        (campaign_id, telegram_user_id),
    ).fetchone()
    if not row:
        return False
    delivery_id, already_interacted = row
    if already_interacted:
        return True
    db.execute_with_retry(
        conn, "UPDATE broadcast_deliveries SET interacted_at=?, interaction_type=? WHERE delivery_id=?",
        (db.now(), interaction_type, delivery_id),
    )
    return True


def campaign_summary(conn, campaign_id: int) -> dict:
    """Plain counts for reporting back after a send -- sent/failed/
    interacted, used by campaign scripts' own final printout and available
    for a future Admin Portal view of the same data."""
    row = conn.execute(
        "SELECT COUNT(*), "
        "SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN interacted_at IS NOT NULL THEN 1 ELSE 0 END) "
        "FROM broadcast_deliveries WHERE campaign_id=?",
        (campaign_id,),
    ).fetchone()
    total, sent, failed, interacted = row
    return {
        "campaign_id": campaign_id,
        "total_recipients": total or 0,
        "sent": sent or 0,
        "failed": failed or 0,
        "interacted": interacted or 0,
    }
