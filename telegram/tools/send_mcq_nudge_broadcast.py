#!/usr/bin/env python3
"""
telegram/tools/send_mcq_nudge_broadcast.py -- "haven't practiced yet"
nudge broadcast (2026-08-18)
--------------------------------------------------------------------------------
Pranav's ask: nudge every student who's started an exam-capable bot but
never practiced a single MCQ -- tell them the real MCQ counts available to
THEM (by their own bot's subject/level scope), remind them content is
organised chapter-wise (pick any chapter), tell them their real current
credit balance, and give tappable buttons. Confirmed via AskUserQuestion,
2026-08-18: eligibility = zero MCQ attempts anywhere, platform-wide
(rolled up by identity, not just on one bot); a small, carefully-tested
addition to exam_hub_bot.py's existing "restart" handler for a tracked
"Start Practicing" button (reusing its already-safe cold-reinitialization
path, not the less-safe "mode:mcq" shortcut); message direction approved
as drafted; preview-first before the real send.

ELIGIBILITY: real students (excludes 2 smoke-test rows, 2 admin/faculty
test accounts, and -- found while building this -- several ORPHANED
bot_interactions rows with no matching `students` row at all, likely
residue from other smoke test suites; requiring a real `students` row via
INNER JOIN excludes these cleanly) who have interacted with at least one
exam-capable bot (kind in ('exam','unified') in bots.json) AND have zero
rows in exam_hub_mcq_attempts anywhere, for any telegram_user_id linked to
their 1LAVYA username (not just this one chat_id) -- 60 real students as
of 2026-08-18.

CONTENT BREAKDOWN: personalized per recipient, using THEIR OWN bot's
tenant content_scope -- reuses telegram/admin_portal/faculty_report.py's
content_availability() directly (same 100%-accurate-by-construction
human_id-derived counter the Course Catalog/Faculty Report pages already
use, not a second counting method), filtered to entries with mcq_count > 0
only (a subject with zero MCQs isn't something to nudge anyone toward,
even if it's technically in their content_scope -- e.g. several CA
Final/CS subjects exist in the flagship's "ALL" scope with 0 MCQs so far).

BUTTONS: telegram/tools/broadcast_sender.py's
get_start_practicing_button_markup() -- "▶️ Start Practicing Now"
(exam_hub_bot.py's tracked `restart:bcast:<campaign_id>` branch) and
"🔕 Not Interested" (report_flow.py's tracked `report:bcastdismiss:
<campaign_id>` branch). Both reuse already-registered callback prefixes --
no bot script needed a new CallbackQueryHandler registration.

PERSISTENCE: same telegram/database/broadcast.py tables as
send_mcq_congrats_broadcast.py (2026-08-18's earlier campaign) --
campaign_id + one delivery row per recipient with their own real
personalized text, send outcome, and (once tapped) interaction timestamp.

SAFETY: same --dry-run (default) / --preview (Pranav's own chat only,
no campaign row) / --live discipline as every broadcast script on this
platform.

USAGE:
    python telegram/tools/send_mcq_nudge_broadcast.py            # dry-run (default)
    python telegram/tools/send_mcq_nudge_broadcast.py --preview  # send to Pranav's own chat only
    python telegram/tools/send_mcq_nudge_broadcast.py --live     # the real thing
"""

import sys
import time
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_ROOT = REPO_ROOT / "telegram"

sys.path.insert(0, str(TELEGRAM_ROOT / "database"))
sys.path.insert(0, str(TELEGRAM_ROOT / "tools"))
sys.path.insert(0, str(TELEGRAM_ROOT / "branding"))
sys.path.insert(0, str(TELEGRAM_ROOT / "admin_portal"))

import db  # noqa: E402
import wallet  # noqa: E402
import identity  # noqa: E402
import broadcast  # noqa: E402
import broadcast_sender  # noqa: E402
import faculty_report  # noqa: E402 -- telegram/admin_portal/faculty_report.py, for content_availability() reuse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(TELEGRAM_ROOT / ".env")

BOTS_PATH = TELEGRAM_ROOT / "config" / "bots.json"

SMOKE_TEST_IDS = {900777001, 900999001}
ADMIN_TELEGRAM_IDS = {5777734732, 6357621862}

PREVIEW_CHAT_ID = 5777734732
PREVIEW_BOT_ID = "capranav-exam"

CATEGORY = "mcq_not_started_nudge"
SEND_DELAY_SECONDS = 0.35

MESSAGE_TEMPLATE_HTML = (
    "\U0001F3AF <b>Time to Start Practicing, {first_name}!</b>\n\n"
    "We noticed you've joined but haven't tried any MCQs yet — here's what's "
    "ready and waiting for you:\n\n"
    "{breakdown}\n"
    "All questions are organised <b>chapter-wise</b> — pick literally any "
    "chapter you like and start at your own pace, in any order.\n\n"
    "\U0001F4B3 You currently have <b>{credit_left} credits</b> available for "
    "MCQ practice.\n\n"
    "Ready when you are — tap below to begin!"
)


def _strip_html(html_text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html_text)


def _esc(text: str) -> str:
    """HTML-escape free text before interpolating into an HTML parse_mode
    message -- see send_mcq_progress_broadcast.py's own _esc() docstring
    for the real live bug this guards against (a Telegram first_name
    containing '</>' broke the HTML parser for exactly that recipient).
    Applied here defensively too, for any future re-run of this script."""
    import html as html_module
    return html_module.escape(text or "", quote=False)


def load_bots() -> list:
    return json.loads(BOTS_PATH.read_text(encoding="utf-8"))["bots"]


def _exam_capable_bot_ids(bots: list) -> list:
    return [b["bot_id"] for b in bots if b.get("kind") in ("exam", "unified")]


def eligible_students(conn, bots: list) -> list:
    """Real students who've interacted with an exam-capable bot AND have
    zero MCQ attempts anywhere, rolled up by 1LAVYA username. Returns a
    list of dicts (one per chat_id -- each linked device gets its own
    message, same precedent as the two earlier broadcast scripts)."""
    exam_bot_ids = _exam_capable_bot_ids(bots)
    placeholders = ",".join("?" * len(exam_bot_ids))

    started_rows = conn.execute(
        f"""SELECT DISTINCT bi.telegram_user_id, s.lavya_username, s.first_name
            FROM bot_interactions bi
            JOIN students s ON s.telegram_user_id = bi.telegram_user_id
            WHERE bi.bot_id IN ({placeholders}) AND bi.telegram_user_id > 0""",
        exam_bot_ids,
    ).fetchall()

    practiced_ids = {r[0] for r in conn.execute("SELECT DISTINCT telegram_user_id FROM exam_hub_mcq_attempts").fetchall()}
    practiced_usernames = set()
    for uid in practiced_ids:
        row = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (uid,)).fetchone()
        if row and row[0]:
            practiced_usernames.add(row[0])

    out = []
    for uid, lavya_username, first_name in started_rows:
        if uid in SMOKE_TEST_IDS or uid in ADMIN_TELEGRAM_IDS:
            continue
        if uid in practiced_ids:
            continue
        if lavya_username and lavya_username in practiced_usernames:
            continue
        out.append({"telegram_user_id": uid, "lavya_username": lavya_username, "first_name": first_name or "there"})
    out.sort(key=lambda r: r["telegram_user_id"])
    return out


def resolve_recipient_bot(conn, telegram_user_id: int, exam_bot_ids: list) -> str | None:
    """Whichever EXAM-CAPABLE bot this student has interacted with the
    most -- deliberately narrower than broadcast_sender.resolve_primary_bot()
    (which would happily pick a non-exam bot like Study Hub if they've used
    it more), since the nudge and its "Start Practicing" button both need
    a bot that actually has MCQ practice."""
    placeholders = ",".join("?" * len(exam_bot_ids))
    row = conn.execute(
        f"SELECT bot_id, COUNT(*) n FROM bot_interactions WHERE telegram_user_id=? AND bot_id IN ({placeholders}) "
        f"GROUP BY bot_id ORDER BY n DESC LIMIT 1",
        [telegram_user_id] + exam_bot_ids,
    ).fetchone()
    return row[0] if row else None


def _tenant_for_bot(bots: list, bot_id: str) -> tuple:
    """(tenant_id, tenant_dict) for a bot_id, or (None, None)."""
    bot = next((b for b in bots if b["bot_id"] == bot_id), None)
    if not bot or not bot.get("tenant_id"):
        return None, None
    tenants = faculty_report._load_tenants()
    return bot["tenant_id"], tenants.get(bot["tenant_id"])


def build_breakdown(conn, tenant: dict) -> str:
    """Bullet list of '{subject} ({course} {level}): {N} MCQs' -- only
    entries with real content (mcq_count > 0), reusing
    faculty_report.content_availability() directly."""
    rows = faculty_report.content_availability(conn, tenant)
    rows = [r for r in rows if r["mcq_count"] > 0]
    if not rows:
        return "• New content is being added soon — check back shortly!\n"
    lines = [f"• <b>{r['subject']}</b> ({r['course']} {r['level']}): {r['mcq_count']} MCQs" for r in rows]
    return "\n".join(lines) + "\n"


def build_message_for(conn, telegram_user_id: int, first_name: str, lavya_username: str, tenant: dict) -> str:
    username = lavya_username
    if not username:
        stub_user = type("StubUser", (), {"id": telegram_user_id, "username": None})()
        username, _ = identity.ensure_wallet_identity(conn, stub_user)
        wallet.grant_signup_bonus(conn, username, "platform")
    balance = wallet.get_balance(conn, username)
    breakdown = build_breakdown(conn, tenant)
    return MESSAGE_TEMPLATE_HTML.format(first_name=_esc(first_name), breakdown=breakdown, credit_left=balance)


def run(mode: str):
    conn = db.get_connection()
    db.init_schema(conn)
    bots = load_bots()
    exam_bot_ids = _exam_capable_bot_ids(bots)
    tokens = broadcast_sender.load_bot_tokens()

    if mode == "preview":
        token = tokens.get(PREVIEW_BOT_ID)
        if not token:
            print(f"ERROR: no live token resolved for bot_id={PREVIEW_BOT_ID!r} -- check telegram/.env")
            return
        _, tenant = _tenant_for_bot(bots, PREVIEW_BOT_ID)
        text = build_message_for(conn, PREVIEW_CHAT_ID, "Pranav", "CAPRANAV", tenant)
        markup = broadcast_sender.get_start_practicing_button_markup(campaign_id=0)
        ok, err = broadcast_sender.send_telegram_message(token, PREVIEW_CHAT_ID, text, parse_mode="HTML", reply_markup=markup)
        status = "OK" if ok else f"FAILED: {err}"
        print(f"Preview send to chat_id={PREVIEW_CHAT_ID} via {PREVIEW_BOT_ID}: {status}")
        print(f"\nNo campaign row created, nobody else touched. Content breakdown/credits are YOUR real "
              f"capranav-exam tenant scope + real balance (not a placeholder). Message sent:\n")
        print(_strip_html(text))
        return

    students = eligible_students(conn, bots)
    print(f"Eligible students (started an exam-capable bot, zero MCQs practiced anywhere, real): {len(students)}")

    if mode == "dry-run":
        for s in students:
            bot_id = resolve_recipient_bot(conn, s["telegram_user_id"], exam_bot_ids)
            token = tokens.get(bot_id) if bot_id else None
            note = "" if (bot_id and token) else " -- NO DELIVERY BOT/TOKEN RESOLVED"
            print(f"  [{s['telegram_user_id']}] {s['first_name']!r} -> bot={bot_id or '?'}{note}")
        print(f"\nDRY-RUN: no campaign created, nothing sent. Re-run with --live to actually broadcast.")
        return

    # --- live -----------------------------------------------------------
    campaign_id = broadcast.create_campaign(
        conn, category=CATEGORY,
        message_text=_strip_html(MESSAGE_TEMPLATE_HTML.format(first_name="{first_name}", breakdown="{breakdown}", credit_left="{credit_left}")),
        message_html=MESSAGE_TEMPLATE_HTML,
        criteria_description="Real students who've interacted with an exam-capable bot but have zero MCQ attempts "
                              "anywhere, platform-wide, rolled up by 1LAVYA username, excluding admin/smoke-test accounts",
        created_by="send_mcq_nudge_broadcast.py",
    )
    print(f"Created campaign_id={campaign_id}")

    sent, failed = 0, 0
    for s in students:
        telegram_user_id = s["telegram_user_id"]
        bot_id = resolve_recipient_bot(conn, telegram_user_id, exam_bot_ids)
        token = tokens.get(bot_id) if bot_id else None

        if not bot_id or not token:
            err = "no bot_interactions row found for an exam-capable bot" if not bot_id else f"no live token for bot_id={bot_id!r}"
            broadcast.log_delivery(conn, campaign_id, telegram_user_id, bot_id or "unknown", "", status="failed", error_detail=err)
            print(f"[{telegram_user_id}] SKIPPED -- {err}")
            failed += 1
            continue

        _, tenant = _tenant_for_bot(bots, bot_id)
        if not tenant:
            broadcast.log_delivery(conn, campaign_id, telegram_user_id, bot_id, "", status="failed", error_detail=f"no tenant resolved for bot_id={bot_id!r}")
            print(f"[{telegram_user_id}] SKIPPED -- no tenant for bot_id={bot_id!r}")
            failed += 1
            continue

        text = build_message_for(conn, telegram_user_id, s["first_name"], s["lavya_username"], tenant)
        markup = broadcast_sender.get_start_practicing_button_markup(campaign_id)
        ok, err = broadcast_sender.send_telegram_message(token, telegram_user_id, text, parse_mode="HTML", reply_markup=markup)
        broadcast.log_delivery(conn, campaign_id, telegram_user_id, bot_id, text,
                                status="sent" if ok else "failed", error_detail=None if ok else err)
        print(f"[{telegram_user_id}] via {bot_id}: sent={ok}" + (f" ERROR={err}" if not ok else ""))
        if ok:
            sent += 1
        else:
            failed += 1
        time.sleep(SEND_DELAY_SECONDS)

    summary = broadcast.campaign_summary(conn, campaign_id)
    print(f"\nSummary: campaign_id={campaign_id}, {summary['total_recipients']} recipients, "
          f"{summary['sent']} sent, {summary['failed']} failed. "
          f"(Interaction counts will grow as students tap a button.)")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview", action="store_true", help="Send to Pranav's own chat only. Creates no campaign row.")
    group.add_argument("--live", action="store_true", help="The real thing: create a campaign and message every eligible student.")
    args = parser.parse_args()

    if args.preview:
        run("preview")
    elif args.live:
        run("live")
    else:
        run("dry-run")


if __name__ == "__main__":
    main()
