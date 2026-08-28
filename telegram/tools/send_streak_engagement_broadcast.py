#!/usr/bin/env python3
"""
telegram/tools/send_streak_engagement_broadcast.py -- streak-based
engagement broadcast, 3 mutually-exclusive segments in one script
(2026-08-26)
--------------------------------------------------------------------------------
Pranav's ask: extend the 2026-08-18 MCQ-activity broadcast series (0 MCQs /
1-10 MCQs / >10 MCQs, see send_mcq_nudge_broadcast.py / send_mcq_progress_
broadcast.py / send_mcq_congrats_broadcast.py) with a streak-aware angle:
students who didn't practice in the last 24h but WERE regular; students
currently maintaining a streak; students not maintaining one. Explicit
requirement: no overlap, no more than one message per chat_id.

SEGMENTATION -- one pass, priority-ordered, first-match-wins, so every
identity (rolled up by 1LAVYA username, same as every prior broadcast
script) lands in EXACTLY one of the 3 segments below. Students with ZERO
MCQ attempts ever are excluded entirely -- that's send_mcq_nudge_broadcast
.py's territory, not this script's, so the two scripts never double-message
the same student.

  1. STREAK_ACTIVE   -- current consecutive-day streak >= 2 AND last
                        practiced within the last 24h (today or yesterday
                        by calendar date). "Currently maintaining a streak."
  2. STREAK_LAPSED   -- NOT in segment 1, AND has practiced on >= 2 distinct
                        calendar days ever ("were regular"), AND last
                        practiced 1-3 days ago (caught early, before fully
                        cold). "Did not practice in the last 24 hours, but
                        were regular."
  3. NO_STREAK       -- everyone else with >= 1 MCQ attempt (mostly one-off
                        triers, or long-dormant 4+ days, or never built a
                        multi-day streak). "Not maintaining a streak."

Streak/last-active/lifetime-active-days are computed in Python from
exam_hub_mcq_attempts.shown_at dates (SQLite has no clean recursive-gaps-
and-islands window function for this) -- same "roll up in Python, not SQL"
precedent send_mcq_progress_broadcast.py/send_mcq_congrats_broadcast.py
already use for identity aggregation.

CREDITS LINE: deliberately does NOT claim practicing refills credits --
verified against wallet.py first (2026-08-26): the signup grant is
ONE-TIME with a 365-day unused-expiry, and MCQ practice isn't even wired to
debit credits yet. Instead: mentions the real 365-day validity + that
topping up is quick/inexpensive if ever needed -- reassuring without
inventing a mechanic that doesn't exist. Confirmed with Pranav via
AskUserQuestion before writing this.

DEDUPE ACROSS CAMPAIGNS: deliberately NOT applied (confirmed via
AskUserQuestion, 2026-08-26) -- only ~62 real students have any MCQ
history at all, and the last campaigns were 8 days ago on a different
topic (milestone/onboarding, not streaks). Revisit if broadcast cadence
increases.

PERSISTENCE: 3 separate broadcast_campaigns rows (one per category, since
each has its own criteria/message template), sharing the same
broadcast_deliveries mechanics as every prior campaign. A chat_id appears
in at most one campaign's deliveries by construction (segment assignment
above), not by a post-hoc dedupe step.

BUTTONS: reuses broadcast_sender.get_continue_practicing_button_markup()
as-is for all 3 segments (Continue Practicing / Show Chapter List / Not
Interested) -- the exact same already-registered callback_data prefixes
the 2026-08-18 progress campaign uses. No new CallbackQueryHandler
registration needed anywhere, avoiding this platform's own documented
callback-collision bug class.

SAFETY: same --dry-run (default) / --preview (Pranav's own chat, sends all
3 sample messages, no campaign rows) / --live discipline as every
broadcast script on this platform.

USAGE:
    python telegram/tools/send_streak_engagement_broadcast.py            # dry-run (default)
    python telegram/tools/send_streak_engagement_broadcast.py --preview  # send all 3 samples to Pranav's own chat only
    python telegram/tools/send_streak_engagement_broadcast.py --live     # the real thing
"""

import sys
import time
import argparse
import datetime
from collections import defaultdict
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

SMOKE_TEST_IDS = {900777001, 900999001}
ADMIN_TELEGRAM_IDS = {5777734732, 6357621862}

PREVIEW_CHAT_ID = 5777734732
PREVIEW_BOT_ID = "capranav-exam"

STREAK_ACTIVE_MIN = 2       # consecutive days, currently unbroken
STREAK_ACTIVE_MAX_LAG = 1   # last practiced today (0) or yesterday (1)
LAPSED_MIN_ACTIVE_DAYS = 2  # lifetime distinct practice days, to count as "were regular"
LAPSED_LAG_RANGE = (1, 3)   # 1-3 days since last practice, inclusive

SEND_DELAY_SECONDS = 0.35

CREDITS_LINE = (
    "\U0001F4B3 You {have_word} <b>{credit_left} credits</b> {avail_word} — valid for a full year, "
    "and topping up is quick and inexpensive if you ever need more. Practice as much as you want!"
)

TEMPLATES = {
    "streak_active_celebrate": (
        "\U0001F525 <b>{streak}-Day Streak, {first_name}!</b>\n\n"
        "You've practiced MCQs {streak} days in a row — that's exactly the kind of "
        "consistency that gets real results in the exam.\n\n"
        "{credits_line}\n\n"
        "Don't break the chain — tap below to keep your streak alive today! "
        "For any help, reach out to us at support@1lavya.com."
    ),
    "streak_lapsed_winback": (
        "\U0001F44B <b>We miss you already, {first_name}!</b>\n\n"
        "You've been a regular — {active_days} different day{active_plural} of practice so far — "
        "but it's been {lag} day{lag_plural} since your last MCQ. A short gap is easy to close "
        "before it turns into a habit of skipping.\n\n"
        "{credits_line}\n\n"
        "Jump back in — even 5 questions today keeps you on track! "
        "For any help, reach out to us at support@1lavya.com."
    ),
    "no_streak_habit_nudge": (
        "\U0001F4DA <b>Let's build a study habit, {first_name}!</b>\n\n"
        "You've tried MCQ practice with us before — {active_days} day{active_plural} so far. "
        "Little and often beats one big push: even 5–10 questions a day adds up fast "
        "before your exam.\n\n"
        "{credits_line}\n\n"
        "Pick any chapter and start today — tap below! "
        "For any help, reach out to us at support@1lavya.com."
    ),
}

CRITERIA_DESCRIPTIONS = {
    "streak_active_celebrate": f"Current consecutive-day MCQ-practice streak >= {STREAK_ACTIVE_MIN}, last practiced "
                                f"within the last 24h (today or yesterday), rolled up by 1LAVYA username, real "
                                f"students only.",
    "streak_lapsed_winback": f"Practiced on >= {LAPSED_MIN_ACTIVE_DAYS} distinct days ever (were regular) but last "
                              f"practiced {LAPSED_LAG_RANGE[0]}-{LAPSED_LAG_RANGE[1]} days ago (not in segment "
                              f"'streak_active_celebrate'), rolled up by 1LAVYA username, real students only.",
    "no_streak_habit_nudge": "Every real student with >= 1 MCQ attempt ever, not already in "
                              "'streak_active_celebrate' or 'streak_lapsed_winback' (mostly one-off triers or "
                              "long-dormant 4+ days), rolled up by 1LAVYA username.",
}


def _esc(text: str) -> str:
    """HTML-escape free text before interpolating into an HTML parse_mode
    message -- see send_mcq_progress_broadcast.py's own _esc() docstring
    for the real live bug this guards against (an un-escaped Telegram
    first_name broke the HTML parser for exactly one student)."""
    import html as html_module
    return html_module.escape(text or "", quote=False)


def _strip_html(html_text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html_text)


def _plural(n: int) -> str:
    return "" if n == 1 else "s"


def _current_streak(dateset: set) -> tuple:
    """(streak_length, most_recent_date_str) -- consecutive calendar days
    ending at the most recent active day. dateset holds 'YYYY-MM-DD'
    strings."""
    last = max(dateset)
    y, m, d = map(int, last.split("-"))
    cur_d = datetime.date(y, m, d)
    streak = 1
    while (cur_d - datetime.timedelta(days=1)).isoformat() in dateset:
        cur_d -= datetime.timedelta(days=1)
        streak += 1
    return streak, last


def _days_ago(date_str: str, today: datetime.date) -> int:
    y, m, d = map(int, date_str.split("-"))
    return (today - datetime.date(y, m, d)).days


def build_identity_map(conn) -> dict:
    """1LAVYA username (or a per-chat_id fallback for unlinked students) ->
    {chat_ids, dates (set of 'YYYY-MM-DD' strings), first_name}. Excludes
    smoke-test/admin rows, same as every prior broadcast script."""
    rows = conn.execute(
        "SELECT a.telegram_user_id, s.lavya_username, s.first_name, date(a.shown_at) d "
        "FROM exam_hub_mcq_attempts a JOIN students s ON s.telegram_user_id = a.telegram_user_id"
    ).fetchall()

    by_identity = defaultdict(lambda: {"chat_ids": set(), "dates": set(), "first_name": "there"})
    for uid, lavya_username, first_name, d in rows:
        if uid in SMOKE_TEST_IDS or uid in ADMIN_TELEGRAM_IDS:
            continue
        key = lavya_username or f"__unlinked_{uid}"
        rec = by_identity[key]
        rec["chat_ids"].add(uid)
        rec["dates"].add(d)
        rec["first_name"] = first_name or "there"
    return by_identity


def segment_identities(by_identity: dict, today: datetime.date) -> dict:
    """Returns {"streak_active_celebrate": [...], "streak_lapsed_winback": [...],
    "no_streak_habit_nudge": [...]} -- each list item is (username_key, rec, streak, lag, active_days).
    Priority-ordered, first-match-wins -- an identity appears in exactly one list."""
    out = {"streak_active_celebrate": [], "streak_lapsed_winback": [], "no_streak_habit_nudge": []}
    for key, rec in by_identity.items():
        streak, last_date = _current_streak(rec["dates"])
        lag = _days_ago(last_date, today)
        active_days = len(rec["dates"])

        if lag <= STREAK_ACTIVE_MAX_LAG and streak >= STREAK_ACTIVE_MIN:
            out["streak_active_celebrate"].append((key, rec, streak, lag, active_days))
        elif LAPSED_LAG_RANGE[0] <= lag <= LAPSED_LAG_RANGE[1] and active_days >= LAPSED_MIN_ACTIVE_DAYS:
            out["streak_lapsed_winback"].append((key, rec, streak, lag, active_days))
        else:
            out["no_streak_habit_nudge"].append((key, rec, streak, lag, active_days))
    return out


def build_message(conn, category: str, username_key: str, first_name: str, streak: int, lag: int, active_days: int) -> str:
    balance = wallet.get_balance(conn, username_key) if username_key and not username_key.startswith("__unlinked_") else 0
    credits_line = CREDITS_LINE.format(
        have_word="have" if balance != 1 else "have",
        credit_left=balance,
        avail_word="available",
    )
    return TEMPLATES[category].format(
        first_name=_esc(first_name),
        streak=streak,
        active_days=active_days,
        active_plural=_plural(active_days),
        lag=lag,
        lag_plural=_plural(lag),
        credits_line=credits_line,
    )


def run_preview(conn, tokens: dict):
    token = tokens.get(PREVIEW_BOT_ID)
    if not token:
        print(f"ERROR: no live token resolved for bot_id={PREVIEW_BOT_ID!r} -- check telegram/.env")
        return
    samples = [
        ("streak_active_celebrate", "Pranav", 4, 0, 8),
        ("streak_lapsed_winback", "Pranav", 1, 2, 5),
        ("no_streak_habit_nudge", "Pranav", 1, 9, 1),
    ]
    print("PREVIEW -- sending all 3 sample messages to your own chat. No campaign rows created, nobody else touched.\n")
    for category, first_name, streak, lag, active_days in samples:
        text = build_message(conn, category, "CAPRANAV", first_name, streak, lag, active_days)
        markup = broadcast_sender.get_continue_practicing_button_markup(campaign_id=0)
        ok, err = broadcast_sender.send_telegram_message(token, PREVIEW_CHAT_ID, text, parse_mode="HTML", reply_markup=markup)
        status = "OK" if ok else f"FAILED: {err}"
        print(f"=== {category} === (sample streak={streak} lag={lag} active_days={active_days}) -- send: {status}")
        print(_strip_html(text))
        print()


def run(mode: str):
    conn = db.get_connection()
    db.init_schema(conn)
    tokens = broadcast_sender.load_bot_tokens()

    if mode == "preview":
        run_preview(conn, tokens)
        return

    today = datetime.date.today()
    by_identity = build_identity_map(conn)
    segments = segment_identities(by_identity, today)

    total = sum(len(v) for v in segments.values())
    print(f"Real students with >=1 MCQ attempt ever: {total}")
    for category in ("streak_active_celebrate", "streak_lapsed_winback", "no_streak_habit_nudge"):
        print(f"  {category}: {len(segments[category])}")

    if mode == "dry-run":
        print()
        for category in ("streak_active_celebrate", "streak_lapsed_winback", "no_streak_habit_nudge"):
            print(f"--- {category} ---")
            for key, rec, streak, lag, active_days in segments[category]:
                for chat_id in rec["chat_ids"]:
                    bot_id = broadcast_sender.resolve_primary_bot(conn, chat_id)
                    token = tokens.get(bot_id) if bot_id else None
                    note = "" if (bot_id and token) else " -- NO DELIVERY BOT/TOKEN RESOLVED"
                    print(f"  [{chat_id}] {rec['first_name']!r} streak={streak} lag={lag} active_days={active_days} "
                          f"-> bot={bot_id or '?'}{note}")
        print(f"\nDRY-RUN: no campaign created, nothing sent. Re-run with --live to actually broadcast.")
        return

    # --- live -----------------------------------------------------------
    campaign_ids = {}
    for category in ("streak_active_celebrate", "streak_lapsed_winback", "no_streak_habit_nudge"):
        campaign_ids[category] = broadcast.create_campaign(
            conn, category=category,
            message_text=_strip_html(TEMPLATES[category]),
            message_html=TEMPLATES[category],
            criteria_description=CRITERIA_DESCRIPTIONS[category],
            created_by="send_streak_engagement_broadcast.py",
        )
        print(f"Created campaign_id={campaign_ids[category]} for category={category}")

    sent, failed = 0, 0
    for category in ("streak_active_celebrate", "streak_lapsed_winback", "no_streak_habit_nudge"):
        campaign_id = campaign_ids[category]
        for key, rec, streak, lag, active_days in segments[category]:
            for chat_id in rec["chat_ids"]:
                bot_id = broadcast_sender.resolve_primary_bot(conn, chat_id)
                token = tokens.get(bot_id) if bot_id else None

                if not bot_id or not token:
                    err = "no bot_interactions row found" if not bot_id else f"no live token for bot_id={bot_id!r}"
                    broadcast.log_delivery(conn, campaign_id, chat_id, bot_id or "unknown", "", status="failed", error_detail=err)
                    print(f"[{chat_id}] SKIPPED ({category}) -- {err}")
                    failed += 1
                    continue

                text = build_message(conn, category, key, rec["first_name"], streak, lag, active_days)
                markup = broadcast_sender.get_continue_practicing_button_markup(campaign_id)
                ok, err = broadcast_sender.send_telegram_message(token, chat_id, text, parse_mode="HTML", reply_markup=markup)
                broadcast.log_delivery(conn, campaign_id, chat_id, bot_id, text,
                                        status="sent" if ok else "failed", error_detail=None if ok else err)
                print(f"[{chat_id}] via {bot_id} ({category}): sent={ok}" + (f" ERROR={err}" if not ok else ""))
                if ok:
                    sent += 1
                else:
                    failed += 1
                time.sleep(SEND_DELAY_SECONDS)

    print(f"\nOverall: {sent} sent, {failed} failed, across 3 campaigns.")
    for category in ("streak_active_celebrate", "streak_lapsed_winback", "no_streak_habit_nudge"):
        summary = broadcast.campaign_summary(conn, campaign_ids[category])
        print(f"  {category} (campaign_id={campaign_ids[category]}): {summary['total_recipients']} recipients, "
              f"{summary['sent']} sent, {summary['failed']} failed.")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preview", action="store_true", help="Send all 3 sample messages to Pranav's own chat only. Creates no campaign rows.")
    group.add_argument("--live", action="store_true", help="The real thing: create 3 campaigns and message every eligible student, each exactly once.")
    args = parser.parse_args()

    if args.preview:
        run("preview")
    elif args.live:
        run("live")
    else:
        run("dry-run")


if __name__ == "__main__":
    main()
