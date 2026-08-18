#!/usr/bin/env python3
"""
telegram/tools/send_mcq_progress_broadcast.py -- "keep going" progress
nudge broadcast (2026-08-18)
--------------------------------------------------------------------------------
Pranav's ask: the third tier in the same day's series of 3 MCQ-activity
broadcasts (0 MCQs -> send_mcq_nudge_broadcast.py; 10+ MCQs ->
send_mcq_congrats_broadcast.py; now the middle: 1-10 MCQs answered).
Nudge them to reach 15 total answered MCQs (framed as "unlocks your
personalised chapter-wise report" -- motivational framing only, the real
report_flow.py on-demand trigger already works at any count; 15 is not a
new technical gate), mention their real credit balance, and give 3
buttons: Continue Practicing, Show Chapter List (NEW, 2026-08-18 --see
below), Not Interested.

ELIGIBILITY: real students (same admin/smoke-test exclusions as every
broadcast this session) with 1-10 MCQs answered all-time, rolled up by
1LAVYA username. Confirmed via AskUserQuestion, 2026-08-18: the exactly-10
boundary case (outside both "< 10" here and "> 10" in the earlier congrats
campaign) is explicitly INCLUDED here, closing the gap between the two
campaigns cleanly -- every student who's answered 1+ MCQ now falls into
exactly one of the two campaigns, never zero.

SHOW CHAPTER LIST (new, 2026-08-18): Pranav's ask -- tapping it should
"directly open up name of Chapter and All chapters at last and on
clicking a particular chapter, it should directly start MCQ for all Exam
Type and All Years Mixed." Built entirely from ALREADY-EXISTING plumbing
in exam_hub_bot.py -- the "MIX (All)" sentinel both McqBank/QuestionBank
already support for exam_type/year, and _build_chapter_screen()'s own
"All Chapters" trailing button -- no new aggregation logic was needed,
just a new cold-safe entry point (exam_hub_bot.py's button_router()
"restart" branch, extended for callback_data "restart:bcastchapters:
<campaign_id>") that resolves the student's OWN most-practiced subject
from their real attempt history (_students_own_mcq_subject(), new) and
jumps straight to that chapter screen, skipping Course/Level/Subject/
Type/Year entirely.

PERSISTENCE: same telegram/database/broadcast.py tables as the other two
2026-08-18 campaigns.

SAFETY: same --dry-run (default) / --preview (Pranav's own chat, no
campaign row) / --live discipline as every broadcast script this session.

USAGE:
    python telegram/tools/send_mcq_progress_broadcast.py            # dry-run (default)
    python telegram/tools/send_mcq_progress_broadcast.py --preview  # send to Pranav's own chat only
    python telegram/tools/send_mcq_progress_broadcast.py --live     # the real thing
"""

import sys
import time
import argparse
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_ROOT = REPO_ROOT / "telegram"

sys.path.insert(0, str(TELEGRAM_ROOT / "database"))
sys.path.insert(0, str(TELEGRAM_ROOT / "tools"))

import db  # noqa: E402
import wallet  # noqa: E402
import broadcast  # noqa: E402
import broadcast_sender  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(TELEGRAM_ROOT / ".env")

MIN_ANSWERED, MAX_ANSWERED = 1, 10   # inclusive both ends -- confirmed via AskUserQuestion (exactly-10 included)
TARGET_ANSWERED = 15                  # motivational framing only, not a real technical gate

SMOKE_TEST_IDS = {900777001, 900999001}
ADMIN_TELEGRAM_IDS = {5777734732, 6357621862}

PREVIEW_CHAT_ID = 5777734732
PREVIEW_BOT_ID = "capranav-exam"

CATEGORY = "mcq_progress_nudge"
SEND_DELAY_SECONDS = 0.35

MESSAGE_TEMPLATE_HTML = (
    "\U0001F4C8 <b>You're on a roll, {first_name}!</b>\n\n"
    "You've completed <b>{n} MCQ{plural}</b> so far — just <b>{remaining} more</b> to reach "
    f"{TARGET_ANSWERED} and unlock your personalised, chapter-wise performance report!\n\n"
    "\U0001F4B3 You currently have <b>{credit_left} credits</b> available for MCQ practice.\n\n"
    "Keep going — tap below to continue practicing. For any help, reach out to us at support@1lavya.com."
)


def _strip_html(html: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html)


def eligible_students(conn) -> list:
    """Real students with MIN_ANSWERED..MAX_ANSWERED (inclusive) MCQs
    answered all-time, rolled up by 1LAVYA username (every linked phone
    merged). Each linked chat_id gets its own message, same per-chat_id
    delivery precedent as every earlier broadcast script."""
    rows = conn.execute(
        "SELECT a.telegram_user_id, s.lavya_username, s.first_name "
        "FROM exam_hub_mcq_attempts a "
        "JOIN students s ON s.telegram_user_id = a.telegram_user_id "
        "WHERE a.answered_at IS NOT NULL"
    ).fetchall()

    by_identity = {}
    for uid, lavya_username, first_name in rows:
        if uid in SMOKE_TEST_IDS or uid in ADMIN_TELEGRAM_IDS:
            continue
        key = lavya_username or f"__unlinked_{uid}"
        rec = by_identity.setdefault(key, {"count": 0, "chat_ids": set(), "first_name": first_name or "there"})
        rec["count"] += 1
        rec["chat_ids"].add(uid)

    out = []
    for key, rec in by_identity.items():
        if MIN_ANSWERED <= rec["count"] <= MAX_ANSWERED:
            for chat_id in rec["chat_ids"]:
                out.append({"telegram_user_id": chat_id, "username": key, "n": rec["count"], "first_name": rec["first_name"]})
    out.sort(key=lambda r: -r["n"])
    return out


def build_message_for(conn, username: str, first_name: str, n: int) -> str:
    remaining = max(TARGET_ANSWERED - n, 1)
    balance = wallet.get_balance(conn, username) if username and not username.startswith("__unlinked_") else 0
    return MESSAGE_TEMPLATE_HTML.format(
        first_name=first_name, n=n, plural="" if n == 1 else "s", remaining=remaining, credit_left=balance,
    )


def run(mode: str):
    conn = db.get_connection()
    db.init_schema(conn)
    tokens = broadcast_sender.load_bot_tokens()

    if mode == "preview":
        token = tokens.get(PREVIEW_BOT_ID)
        if not token:
            print(f"ERROR: no live token resolved for bot_id={PREVIEW_BOT_ID!r} -- check telegram/.env")
            return
        text = build_message_for(conn, "CAPRANAV", "Pranav", n=7)   # realistic sample n, not a placeholder oddity
        markup = broadcast_sender.get_continue_practicing_button_markup(campaign_id=0)
        ok, err = broadcast_sender.send_telegram_message(token, PREVIEW_CHAT_ID, text, parse_mode="HTML", reply_markup=markup)
        status = "OK" if ok else f"FAILED: {err}"
        print(f"Preview send to chat_id={PREVIEW_CHAT_ID} via {PREVIEW_BOT_ID}: {status}")
        print(f"\nNo campaign row created, nobody else touched. n=7 is a realistic SAMPLE (your own real answered "
              f"count is higher, outside this campaign's 1-10 range) -- credit balance shown IS your real balance:\n")
        print(_strip_html(text))
        return

    students = eligible_students(conn)
    print(f"Eligible students ({MIN_ANSWERED}-{MAX_ANSWERED} MCQs answered inclusive, all-time, real): {len(students)}")

    if mode == "dry-run":
        for s in students:
            bot_id = broadcast_sender.resolve_primary_bot(conn, s["telegram_user_id"])
            token = tokens.get(bot_id) if bot_id else None
            note = "" if (bot_id and token) else " -- NO DELIVERY BOT/TOKEN RESOLVED"
            print(f"  [{s['telegram_user_id']}] {s['first_name']!r} n={s['n']} -> bot={bot_id or '?'}{note}")
        print(f"\nDRY-RUN: no campaign created, nothing sent. Re-run with --live to actually broadcast.")
        return

    # --- live -----------------------------------------------------------
    campaign_id = broadcast.create_campaign(
        conn, category=CATEGORY,
        message_text=_strip_html(MESSAGE_TEMPLATE_HTML.format(first_name="{first_name}", n="{n}", plural="", remaining="{remaining}", credit_left="{credit_left}")),
        message_html=MESSAGE_TEMPLATE_HTML,
        criteria_description=f"MCQs answered {MIN_ANSWERED}-{MAX_ANSWERED} inclusive, all-time, platform-wide, "
                              f"rolled up by 1LAVYA username, excluding admin/smoke-test accounts",
        created_by="send_mcq_progress_broadcast.py",
    )
    print(f"Created campaign_id={campaign_id}")

    sent, failed = 0, 0
    for s in students:
        telegram_user_id = s["telegram_user_id"]
        bot_id = broadcast_sender.resolve_primary_bot(conn, telegram_user_id)
        token = tokens.get(bot_id) if bot_id else None

        if not bot_id or not token:
            err = "no bot_interactions row found" if not bot_id else f"no live token for bot_id={bot_id!r}"
            broadcast.log_delivery(conn, campaign_id, telegram_user_id, bot_id or "unknown", "", status="failed", error_detail=err)
            print(f"[{telegram_user_id}] SKIPPED -- {err}")
            failed += 1
            continue

        text = build_message_for(conn, s["username"], s["first_name"], s["n"])
        markup = broadcast_sender.get_continue_practicing_button_markup(campaign_id)
        ok, err = broadcast_sender.send_telegram_message(token, telegram_user_id, text, parse_mode="HTML", reply_markup=markup)
        broadcast.log_delivery(conn, campaign_id, telegram_user_id, bot_id, text,
                                status="sent" if ok else "failed", error_detail=None if ok else err)
        print(f"[{telegram_user_id}] via {bot_id}: n={s['n']} sent={ok}" + (f" ERROR={err}" if not ok else ""))
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
