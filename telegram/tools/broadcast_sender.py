"""
telegram/tools/broadcast_sender.py -- shared Telegram send mechanics for
broadcast campaign scripts (2026-08-18)
--------------------------------------------------------------------------------
Extracted from telegram/tools/welcome_bonus_broadcast.py (2026-08-17, the
first broadcast this platform ever sent) so the second one doesn't
re-derive the same logic: which bot a specific recipient can actually be
DM'd through (Telegram only allows a bot to message a chat_id that has
already started a conversation with THAT bot -- resolved from
bot_interactions, never guessed), and the raw HTTP POST to sendMessage
(same urllib technique watcher_bot.py/leaderboard_broadcaster.py already
use -- no need for a full telegram.Bot/Application for a one-off script).

Pure send-mechanics only -- no DB persistence of the broadcast itself
(see telegram/database/broadcast.py for that; a campaign script imports
both).
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_ROOT = REPO_ROOT / "telegram"
BOTS_PATH = TELEGRAM_ROOT / "config" / "bots.json"


def load_bot_tokens() -> dict:
    """bot_id -> resolved token, for every bot with a real (non-placeholder)
    bot_token_env set in telegram/.env."""
    bots = json.loads(BOTS_PATH.read_text(encoding="utf-8"))["bots"]
    tokens = {}
    for b in bots:
        env_var = b.get("bot_token_env")
        if not env_var:
            continue
        token = os.environ.get(env_var)
        if token and "PASTE_YOUR" not in token:
            tokens[b["bot_id"]] = token
    return tokens


def resolve_primary_bot(conn, telegram_user_id: int) -> str | None:
    """Whichever bot this telegram_user_id has interacted with the most --
    the one they've actually started a conversation with (a Telegram
    platform requirement for any bot's first message to a user). Ties are
    broken by COUNT DESC, arbitrary but harmless (only matters for the rare
    student/admin who's used more than one bot)."""
    row = conn.execute(
        "SELECT bot_id, COUNT(*) n FROM bot_interactions WHERE telegram_user_id=? "
        "GROUP BY bot_id ORDER BY n DESC LIMIT 1",
        (telegram_user_id,),
    ).fetchone()
    return row[0] if row else None


def send_telegram_message(token: str, chat_id: int, text: str, parse_mode: str = None,
                           reply_markup: dict = None) -> tuple:
    """Raw HTTP POST to Bot API sendMessage. `reply_markup`, if given, is a
    plain dict matching Telegram's InlineKeyboardMarkup JSON shape (e.g.
    {"inline_keyboard": [[{"text": "...", "callback_data": "..."}]]}) --
    the caller builds it, this function just forwards it. Returns
    (ok: bool, error_detail: str)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True, ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return False, f"HTTP {e.code} -- {body}"
    except Exception as e:
        return False, str(e)


def get_report_button_markup(campaign_id: int, bot_id: str) -> dict:
    """The '📊 Get My Report' inline button -- callback_data
    'report:bcast:<campaign_id>:<bot_id>', reusing the ALREADY-REGISTERED
    `report:` CallbackQueryHandler pattern every bot already has (see
    telegram/bots/report_flow.py's own module docstring for the exact
    branch this routes to) -- no bot script needs a new handler
    registration for this button to work. bot_id is embedded directly
    (rather than relying on any in-memory context.user_data state, which
    may not exist yet for a student who's never used the report flow
    before) since it's the one thing the callback handler can't otherwise
    know for certain at tap time."""
    return {"inline_keyboard": [[
        {"text": "\U0001F4CA Get My Report", "callback_data": f"report:bcast:{campaign_id}:{bot_id}"},
    ]]}
