#!/usr/bin/env python3
"""
telegram/tools/welcome_bonus_broadcast.py -- one-time welcome-bonus credit
+ broadcast (2026-08-17)
--------------------------------------------------------------------------------
Pranav's ask: give every real student whose wallet balance is currently 0
the existing 1000-credit signup bonus (wallet.grant_signup_bonus() -- see
that module's docstring; this script does NOT invent a new credit
mechanism, it just runs the already-audited one proactively instead of
waiting for the student's next wallet-gated interaction), and DM them a
short welcome-bonus announcement pointing them at Study & Exam Hub and
support@1lavya.com.

SCOPE, confirmed with Pranav 2026-08-17 (AskUserQuestion, all 3 answered
with the recommended option):
  - Students only -- excludes the 2 admin/faculty accounts that also sit in
    `students` (CAPRANAV = Pranav's own chat, Official1lavya = the
    platform/Arun admin chat), both already have real, non-zero balances.
  - "Everyone" = every real student whose CURRENT balance is exactly 0
    (checked live, before granting) -- this is both the credit eligibility
    AND the broadcast eligibility. A student who already received the
    grant earlier (13 of 105 in this DB, via natural bot usage since
    2026-08-16) is skipped entirely: not re-credited (grant_signup_bonus()
    is one-time-per-username-ever regardless), and not re-sent a "we've
    credited you" message that would be inaccurate for them.
  - 2 synthetic smoke-test accounts (telegram_user_id 900777001/900999001,
    first_name "Smoke", residue from smoke_test_wallet*.py runs) are
    excluded from both credit and message -- not real people.
  - Message text is the exact draft Pranav approved as-is.
  - A `--preview` mode sends ONLY to Pranav's own chat (CAPRANAV) as a
    live rendering check, credits nothing, touches no other student --
    run this first and confirm formatting before `--live`.

DELIVERY: a student can only be DM'd by a bot they've actually started a
conversation with (Telegram platform rule, same constraint watcher_bot.py
documents for its own admin alerts). Every real student's ACTUAL bot is
resolved from bot_interactions (COUNT-based, picks whichever bot they've
interacted with most) -- never a fixed/guessed bot. Confirmed via the live
DB before writing this: every one of the 105 real rows has at least one
bot_interactions row, so this always resolves to a real bot for a real
student.

SAFETY:
  - Default is `--dry-run` (prints the full plan -- who, which bot, old/new
    balance, message go/no-go -- without touching the DB or calling
    Telegram). Nothing is credited or sent unless `--live` or `--preview`
    is passed explicitly.
  - Every DB write goes through wallet.py/identity.py's own idempotent
    functions -- safe to re-run this script; anyone already credited (by
    an earlier run of this exact script, or by any other path) is skipped,
    never double-credited, never double-messaged (the eligibility check --
    balance == 0 -- re-evaluates live on every run, so a student granted by
    an earlier partial run no longer shows balance 0 and is naturally
    excluded the second time).
  - A short sleep between sends (SEND_DELAY_SECONDS) stays well under
    Telegram's per-bot send-rate limits -- this is a one-off ~100-message
    run, not a hot loop.
  - Full per-student outcome is written to a timestamped CSV next to this
    script's own output for a durable audit trail (Pranav asked for a
    "complete trail" discipline consistently elsewhere on this platform --
    matches that, no new pattern invented).

USAGE:
    python telegram/tools/welcome_bonus_broadcast.py               # dry-run (default)
    python telegram/tools/welcome_bonus_broadcast.py --preview     # send to Pranav's own chat only, credit nobody
    python telegram/tools/welcome_bonus_broadcast.py --live        # the real thing: credit + message every eligible student
"""

import os
import sys
import csv
import json
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

# Windows' default console codepage (cp1252) can't print the emoji in
# WELCOME_MESSAGE or in a stray non-ASCII first_name -- reconfigure stdout to
# UTF-8 with lossy fallback so a print() call never crashes the run partway
# through the real --live broadcast loop (the actual Telegram send is
# unaffected either way -- it already sends proper UTF-8 JSON over HTTP).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_ROOT = REPO_ROOT / "telegram"
BOTS_PATH = TELEGRAM_ROOT / "config" / "bots.json"

sys.path.insert(0, str(TELEGRAM_ROOT / "database"))
import db  # noqa: E402
import wallet  # noqa: E402
import identity  # noqa: E402

load_dotenv(TELEGRAM_ROOT / ".env")

# --- Exclusions, confirmed with Pranav 2026-08-17 --------------------------
SMOKE_TEST_IDS = {900777001, 900999001}         # synthetic smoke-test residue, not real people
ADMIN_TELEGRAM_IDS = {5777734732, 6357621862}   # CAPRANAV (Pranav), Official1lavya (platform/Arun admin chat) -- "students only"
PREVIEW_CHAT_ID = 5777734732                     # CAPRANAV -- where --preview sends its one test message
PREVIEW_BOT_ID = "capranav-exam"                 # the bot Pranav has interacted with most (68 interactions) -- any of his bots would work

TENANT_ID = "platform"
SEND_DELAY_SECONDS = 0.35   # ~3 messages/sec -- comfortably under Telegram's per-bot rate limits for a ~100-message one-off run

WELCOME_MESSAGE = (
    "\U0001F381 Welcome Bonus from 1LAVYA!\n\n"
    "We've credited 1000 credits to your account — completely free, as a welcome gift.\n\n"
    "Use them to practice MCQs, Descriptive Questions, or take Mock Tests on your "
    "Study & Exam Bots. Make the most of them!\n\n"
    "For any queries, reach out to us at support@1lavya.com."
)


def load_bot_tokens() -> dict:
    """bot_id -> resolved token, for every bot with a real bot_token_env."""
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
    the one they've actually started a conversation with (see module
    docstring). Every real student has exactly one in practice; ties are
    broken by COUNT DESC, arbitrary but harmless since a tie only happens
    for the 2 excluded admin accounts."""
    row = conn.execute(
        "SELECT bot_id, COUNT(*) n FROM bot_interactions WHERE telegram_user_id=? "
        "GROUP BY bot_id ORDER BY n DESC LIMIT 1",
        (telegram_user_id,),
    ).fetchone()
    return row[0] if row else None


class _StubTelegramUser:
    """Minimal stand-in for a telegram.User -- identity.ensure_wallet_identity()
    only ever reads .id and .username (see that module's own docstring),
    so a live bot object is never needed for this bulk/offline run."""
    def __init__(self, telegram_user_id: int, username: str | None):
        self.id = telegram_user_id
        self.username = username


def send_telegram_dm(token: str, chat_id: int, text: str) -> tuple[bool, str]:
    """Raw HTTP POST to Bot API sendMessage -- same technique
    watcher_bot.py/cf_email.py already use elsewhere on this platform, no
    new dependency. Returns (ok, error_text)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True, ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return False, f"HTTP {e.code} -- {body}"
    except Exception as e:
        return False, str(e)


def eligible_students(conn):
    """Every real student (excludes smoke-test + admin rows) whose CURRENT
    balance is exactly 0, checked live. Returns a list of dicts. Balance for
    a student with no lavya_username yet is trivially 0 (no ledger rows can
    exist for a username that doesn't exist)."""
    rows = conn.execute(
        "SELECT telegram_user_id, username, lavya_username, first_name FROM students "
        "ORDER BY telegram_user_id"
    ).fetchall()

    out = []
    for telegram_user_id, tg_username, lavya_username, first_name in rows:
        if telegram_user_id in SMOKE_TEST_IDS or telegram_user_id in ADMIN_TELEGRAM_IDS:
            continue
        balance = wallet.get_balance(conn, lavya_username) if lavya_username else 0
        if balance != 0:
            continue
        out.append({
            "telegram_user_id": telegram_user_id,
            "tg_username": tg_username,
            "lavya_username": lavya_username,
            "first_name": first_name,
        })
    return out


def run(mode: str):
    conn = db.get_connection()
    db.init_schema(conn)
    tokens = load_bot_tokens()

    if mode == "preview":
        token = tokens.get(PREVIEW_BOT_ID)
        if not token:
            print(f"ERROR: no live token resolved for bot_id={PREVIEW_BOT_ID!r} -- check telegram/.env")
            return
        ok, err = send_telegram_dm(token, PREVIEW_CHAT_ID, WELCOME_MESSAGE)
        status = "OK" if ok else f"FAILED: {err}"
        print(f"Preview send to chat_id={PREVIEW_CHAT_ID} via {PREVIEW_BOT_ID}: {status}")
        print("\nNothing credited, no other student touched. Message sent:\n")
        print(WELCOME_MESSAGE)
        return

    students = eligible_students(conn)
    print(f"Eligible students (balance == 0, real, non-admin): {len(students)}")

    results = []
    for s in students:
        telegram_user_id = s["telegram_user_id"]
        bot_id = resolve_primary_bot(conn, telegram_user_id)
        token = tokens.get(bot_id) if bot_id else None

        row = {
            "telegram_user_id": telegram_user_id,
            "tg_username": s["tg_username"] or "",
            "first_name": s["first_name"] or "",
            "bot_id": bot_id or "",
            "credited": False,
            "new_balance": None,
            "message_sent": False,
            "error": "",
        }

        if mode == "dry-run":
            row["error"] = "dry-run -- no changes made" if not bot_id else ""
            if not bot_id:
                row["error"] = "no bot_interactions row found -- cannot resolve delivery bot"
            elif not token:
                row["error"] = f"no live token for resolved bot_id={bot_id!r}"
            results.append(row)
            continue

        if not bot_id:
            row["error"] = "no bot_interactions row found -- cannot resolve delivery bot"
            results.append(row)
            continue
        if not token:
            row["error"] = f"no live token for resolved bot_id={bot_id!r}"
            results.append(row)
            continue

        # --- credit -----------------------------------------------------
        stub_user = _StubTelegramUser(telegram_user_id, s["tg_username"])
        username, _ = identity.ensure_wallet_identity(conn, stub_user)
        new_balance, already_granted = wallet.grant_signup_bonus(conn, username, TENANT_ID)
        row["credited"] = not already_granted
        row["new_balance"] = new_balance

        # --- message ------------------------------------------------------
        ok, err = send_telegram_dm(token, telegram_user_id, WELCOME_MESSAGE)
        row["message_sent"] = ok
        if not ok:
            row["error"] = err

        results.append(row)
        print(f"[{telegram_user_id}] via {bot_id}: credited={row['credited']} "
              f"balance={new_balance} sent={ok}" + (f" ERROR={err}" if not ok else ""))
        time.sleep(SEND_DELAY_SECONDS)

    # --- audit trail CSV -----------------------------------------------------
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = TELEGRAM_ROOT / "database" / "run" / f"welcome_bonus_broadcast_{mode}_{ts}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "telegram_user_id", "tg_username", "first_name", "bot_id",
            "credited", "new_balance", "message_sent", "error",
        ])
        writer.writeheader()
        writer.writerows(results)

    sent = sum(1 for r in results if r["message_sent"])
    credited = sum(1 for r in results if r["credited"])
    failed = sum(1 for r in results if r["error"])
    print(f"\n{'DRY-RUN ' if mode == 'dry-run' else ''}Summary: {len(results)} eligible, "
          f"{credited} credited, {sent} messages sent, {failed} errors.")
    print(f"Full report: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview", action="store_true", help="Send the message to Pranav's own chat only. Credits nobody.")
    group.add_argument("--live", action="store_true", help="The real thing: credit + message every eligible student.")
    args = parser.parse_args()

    if args.preview:
        run("preview")
    elif args.live:
        run("live")
    else:
        run("dry-run")


if __name__ == "__main__":
    main()
