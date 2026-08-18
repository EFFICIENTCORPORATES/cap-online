#!/usr/bin/env python3
"""
telegram/tools/send_mcq_congrats_broadcast.py -- "10+ MCQs" congrats
broadcast (2026-08-18)
--------------------------------------------------------------------------------
Pranav's ask: congratulate every student who has answered more than 10
MCQs (all-time, platform-wide), tell them their real MCQ count, and invite
them to get their performance report -- via the exact existing on-demand
report flow (typing "report", or now also a trackable "Get My Report"
button -- see telegram/bots/report_flow.py's "bcast:" branch and
telegram/database/broadcast.py, both added alongside this script). NOT a
proactive send of the report itself (confirmed via AskUserQuestion,
2026-08-18: "it should nudge them... we don't have contact details so
that's also a reason why we can't send these" -- Study/Exam bots don't
have a confirmed email/mobile for most students yet, so an unprompted
push would mean guessing or using stale/unconfirmed data).

ELIGIBILITY: MCQs ANSWERED (not just shown) > 10, all-time, no date range
("till date" -- Pranav's own wording), rolled up by the student's
permanent 1LAVYA username (every linked phone's activity merged before the
threshold is applied) -- matches this platform's own identity model
(telegram/database/leaderboard_metrics.py, and the 2026-08-17 Faculty
Report revision). Excludes the 2 synthetic smoke-test accounts and the 2
admin/faculty test accounts (CAPRANAV, Official1lavya) -- same exclusions
as telegram/tools/welcome_bonus_broadcast.py's precedent, confirmed
implicitly by not being challenged when stated in that script's own
docstring/output.

MESSAGE: personalized per recipient with their REAL answered-MCQ count
(Pranav's explicit correction: "instead of typing 'completed over 10', can
we get a tentative number, or exact number" -- using the exact number).
Sent with parse_mode=HTML for light emphasis + a "📊 Get My Report" inline
button (telegram/tools/broadcast_sender.py's get_report_button_markup()).

PERSISTENCE: every send goes through telegram/database/broadcast.py --
one broadcast_campaigns row (the template), one broadcast_deliveries row
per recipient (their real personalized text, send outcome, and -- once
tapped -- their interaction timestamp). This is the FIRST campaign to use
that new persistent system; see this script's own --backfill-welcome-bonus
mode for retroactively recording the 2026-08-17 welcome-bonus broadcast
(sent before this system existed) into the same tables, so "all these
broadcast messages" (Pranav's own phrase) really does mean all of them,
not just the ones sent after 2026-08-18.

SAFETY: same discipline as welcome_bonus_broadcast.py -- default is
--dry-run (prints the plan, touches nothing). --preview sends ONLY to
Pranav's own chat (CAPRANAV) as a live rendering/button check, creates no
campaign row for the real audience. --live is the real thing: creates one
campaign row and messages every eligible student, respecting a short
per-send delay to stay comfortably under Telegram's rate limits.

USAGE:
    python telegram/tools/send_mcq_congrats_broadcast.py                 # dry-run (default)
    python telegram/tools/send_mcq_congrats_broadcast.py --preview       # send to Pranav's own chat only
    python telegram/tools/send_mcq_congrats_broadcast.py --live          # the real thing
    python telegram/tools/send_mcq_congrats_broadcast.py --backfill-welcome-bonus <csv_path>   # one-time: record the 2026-08-17 broadcast into the new tables
"""

import os
import sys
import csv
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_ROOT = REPO_ROOT / "telegram"

sys.path.insert(0, str(TELEGRAM_ROOT / "database"))
sys.path.insert(0, str(TELEGRAM_ROOT / "tools"))

import db  # noqa: E402
import broadcast  # noqa: E402
import broadcast_sender  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(TELEGRAM_ROOT / ".env")

MCQ_ANSWERED_THRESHOLD = 10   # "more than 10" -- confirmed via AskUserQuestion, MCQs ANSWERED not just shown

SMOKE_TEST_IDS = {900777001, 900999001}
ADMIN_TELEGRAM_IDS = {5777734732, 6357621862}   # CAPRANAV (Pranav), Official1lavya -- same exclusions as welcome_bonus_broadcast.py

PREVIEW_CHAT_ID = 5777734732
PREVIEW_BOT_ID = "capranav-exam"

CATEGORY = "mcq_milestone_congrats"
SEND_DELAY_SECONDS = 0.35

MESSAGE_TEMPLATE_HTML = (
    "\U0001F389 <b>Congratulations from 1LAVYA!</b>\n\n"
    "You've answered <b>{count} MCQs</b> on your Study &amp; Exam Bots so far "
    "— that's real, consistent practice paying off.\n\n"
    "Want to see exactly how you're doing? Tap the button below (or type "
    "<b>report</b> any time) to get your personalised performance report "
    "— sent by Telegram, Email, or both, your choice.\n\n"
    "Keep up the great work! For any queries, reach out to us at support@1lavya.com."
)


def _strip_html(html: str) -> str:
    """A crude plain-text rendition for broadcast_campaigns.message_text
    (the searchable/readable field) -- broadcast_campaigns.message_html
    keeps the exact markup actually sent."""
    import re
    return re.sub(r"<[^>]+>", "", html)


def eligible_students(conn) -> list:
    """Every real student (excludes smoke-test + admin rows) whose all-time
    ANSWERED MCQ count, rolled up by 1LAVYA username (every linked phone
    merged), exceeds MCQ_ANSWERED_THRESHOLD. Returns a list of dicts sorted
    by count descending. `chat_ids` is every telegram_user_id that
    contributed to this username's count -- each gets its own message
    (matching welcome_bonus_broadcast.py's per-chat_id delivery precedent),
    since a message is something a specific device receives."""
    rows = conn.execute(
        "SELECT a.telegram_user_id, s.lavya_username, COUNT(*) n "
        "FROM exam_hub_mcq_attempts a "
        "JOIN students s ON s.telegram_user_id = a.telegram_user_id "
        "WHERE a.answered_at IS NOT NULL "
        "GROUP BY a.telegram_user_id"
    ).fetchall()

    by_identity = {}   # identity key (lavya_username, or a per-chat_id fallback) -> {"count": int, "chat_ids": set}
    for uid, lavya_username, n in rows:
        if uid in SMOKE_TEST_IDS or uid in ADMIN_TELEGRAM_IDS:
            continue
        key = lavya_username or f"__unlinked_{uid}"
        rec = by_identity.setdefault(key, {"count": 0, "chat_ids": set()})
        rec["count"] += n
        rec["chat_ids"].add(uid)

    out = []
    for key, rec in by_identity.items():
        if rec["count"] > MCQ_ANSWERED_THRESHOLD:
            for chat_id in rec["chat_ids"]:
                out.append({"telegram_user_id": chat_id, "username": key, "mcq_answered_count": rec["count"]})
    out.sort(key=lambda r: r["mcq_answered_count"], reverse=True)
    return out


def run(mode: str):
    conn = db.get_connection()
    db.init_schema(conn)
    tokens = broadcast_sender.load_bot_tokens()

    if mode == "preview":
        token = tokens.get(PREVIEW_BOT_ID)
        if not token:
            print(f"ERROR: no live token resolved for bot_id={PREVIEW_BOT_ID!r} -- check telegram/.env")
            return
        # Real count for the preview recipient's OWN chat_id -- NOT a
        # placeholder (2026-08-18: an earlier version hardcoded 999 here,
        # which Pranav correctly flagged as confusing/looked wrong -- every
        # number shown anywhere in this flow, including the preview, is now
        # a real live query result, never invented).
        real_count = conn.execute(
            "SELECT COUNT(*) FROM exam_hub_mcq_attempts WHERE telegram_user_id=? AND answered_at IS NOT NULL",
            (PREVIEW_CHAT_ID,),
        ).fetchone()[0]
        # Preview uses a fake campaign_id (0) -- the button is real/tappable
        # for rendering purposes, but log_interaction() will correctly
        # no-op (no matching delivery row) if actually tapped in preview.
        text = MESSAGE_TEMPLATE_HTML.format(count=real_count)
        markup = broadcast_sender.get_report_button_markup(campaign_id=0, bot_id=PREVIEW_BOT_ID)
        ok, err = broadcast_sender.send_telegram_message(token, PREVIEW_CHAT_ID, text, parse_mode="HTML", reply_markup=markup)
        status = "OK" if ok else f"FAILED: {err}"
        print(f"Preview send to chat_id={PREVIEW_CHAT_ID} via {PREVIEW_BOT_ID}: {status}")
        print(f"\nNo campaign row created, nobody else touched. Message sent (count={real_count}, "
              f"your own real answered-MCQ count, queried live -- NOT a placeholder):\n")
        print(_strip_html(text))
        return

    students = eligible_students(conn)
    print(f"Eligible students (MCQs answered > {MCQ_ANSWERED_THRESHOLD}, all-time, real, non-admin): {len(students)}")

    if mode == "dry-run":
        for s in students:
            bot_id = broadcast_sender.resolve_primary_bot(conn, s["telegram_user_id"])
            token = tokens.get(bot_id) if bot_id else None
            note = "" if (bot_id and token) else " -- NO DELIVERY BOT/TOKEN RESOLVED"
            print(f"  [{s['telegram_user_id']}] username={s['username']} answered={s['mcq_answered_count']} "
                  f"-> bot={bot_id or '?'}{note}")
        print(f"\nDRY-RUN: no campaign created, nothing sent. Re-run with --live to actually broadcast.")
        return

    # --- live -----------------------------------------------------------
    campaign_id = broadcast.create_campaign(
        conn, category=CATEGORY,
        message_text=_strip_html(MESSAGE_TEMPLATE_HTML.format(count="{count}")),
        message_html=MESSAGE_TEMPLATE_HTML,
        criteria_description=f"MCQs answered > {MCQ_ANSWERED_THRESHOLD}, all-time, platform-wide, rolled up by "
                              f"1LAVYA username, excluding admin/smoke-test accounts",
        created_by="send_mcq_congrats_broadcast.py",
    )
    print(f"Created campaign_id={campaign_id}")

    sent, failed = 0, 0
    for s in students:
        telegram_user_id = s["telegram_user_id"]
        bot_id = broadcast_sender.resolve_primary_bot(conn, telegram_user_id)
        token = tokens.get(bot_id) if bot_id else None
        text = MESSAGE_TEMPLATE_HTML.format(count=s["mcq_answered_count"])

        if not bot_id or not token:
            err = "no bot_interactions row found" if not bot_id else f"no live token for bot_id={bot_id!r}"
            broadcast.log_delivery(conn, campaign_id, telegram_user_id, bot_id or "unknown", text, status="failed", error_detail=err)
            print(f"[{telegram_user_id}] SKIPPED -- {err}")
            failed += 1
            continue

        markup = broadcast_sender.get_report_button_markup(campaign_id, bot_id)
        ok, err = broadcast_sender.send_telegram_message(token, telegram_user_id, text, parse_mode="HTML", reply_markup=markup)
        broadcast.log_delivery(conn, campaign_id, telegram_user_id, bot_id, text,
                                status="sent" if ok else "failed", error_detail=None if ok else err)
        print(f"[{telegram_user_id}] via {bot_id}: answered={s['mcq_answered_count']} sent={ok}" + (f" ERROR={err}" if not ok else ""))
        if ok:
            sent += 1
        else:
            failed += 1
        time.sleep(SEND_DELAY_SECONDS)

    summary = broadcast.campaign_summary(conn, campaign_id)
    print(f"\nSummary: campaign_id={campaign_id}, {summary['total_recipients']} recipients, "
          f"{summary['sent']} sent, {summary['failed']} failed. "
          f"(Interaction counts will grow as students tap 'Get My Report'.)")


def backfill_welcome_bonus(csv_path: str):
    """One-time: record the 2026-08-17 welcome-bonus broadcast (sent
    before broadcast.py existed, tracked only in a CSV on disk) into the
    new persistent tables -- so "all these broadcast messages" (Pranav's
    own phrase) really covers all of them. No interaction tracking exists
    for that campaign (it had no button), so every delivery row's
    interacted_at stays NULL -- honest, not backfilled with a guess."""
    conn = db.get_connection()
    db.init_schema(conn)

    message_text = (
        "\U0001F381 Welcome Bonus from 1LAVYA!\n\n"
        "We've credited 1000 credits to your account — completely free, as a welcome gift.\n\n"
        "Use them to practice MCQs, Descriptive Questions, or take Mock Tests on your "
        "Study & Exam Bots. Make the most of them!\n\n"
        "For any queries, reach out to us at support@1lavya.com."
    )
    campaign_id = broadcast.create_campaign(
        conn, category="welcome_bonus", message_text=message_text, message_html=None,
        criteria_description="Real students with balance == 0 (never previously granted the signup bonus), "
                              "excluding admin/smoke-test accounts. Sent 2026-08-17.",
        created_by="backfill:welcome_bonus_broadcast.py",
    )

    rows_in, sent, failed = 0, 0, 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows_in += 1
            status = "sent" if row["message_sent"] == "True" else "failed"
            broadcast.log_delivery(
                conn, campaign_id, int(row["telegram_user_id"]), row["bot_id"] or "unknown",
                message_text, status=status, error_detail=row["error"] or None,
            )
            if status == "sent":
                sent += 1
            else:
                failed += 1

    print(f"Backfilled campaign_id={campaign_id} from {csv_path}: {rows_in} rows ({sent} sent, {failed} failed).")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview", action="store_true", help="Send to Pranav's own chat only. Creates no campaign row.")
    group.add_argument("--live", action="store_true", help="The real thing: create a campaign and message every eligible student.")
    group.add_argument("--backfill-welcome-bonus", metavar="CSV_PATH", help="One-time: record the 2026-08-17 welcome-bonus broadcast's CSV into the new tables.")
    args = parser.parse_args()

    if args.backfill_welcome_bonus:
        backfill_welcome_bonus(args.backfill_welcome_bonus)
    elif args.preview:
        run("preview")
    elif args.live:
        run("live")
    else:
        run("dry-run")


if __name__ == "__main__":
    main()
