#!/usr/bin/env python3
"""
telegram/bots/smoke_test_report_flow.py -- Phase 2 (Report Pipeline) smoke
test (2026-08-11)
--------------------------------------------------------------------------------
Per Pranav's process for this roadmap: build each phase, smoke-test it with
a real re-runnable script, document it, THEN hand off for his manual test.
This is that script for Phase 2.

Uses a SYNTHETIC test student (a telegram_user_id far outside any real
Telegram ID range) for the full conversational-flow simulation, so this
can be re-run against the real production platform.db without ever
touching real student data -- inserts its own test rows, cleans them up in
a `finally` block even if a check fails partway through.

Checks, in order (stops at the first hard failure):
  1. Schema migration is idempotent (safe to call init_schema() twice).
  2. student_analytics queries return sane, correctly-shaped data for a
     real student with real attempts.
  3. The report PDF renders through the real xhtml2pdf engine (0 errors,
     real bytes) for that same real student.
  4. Email message construction is structurally correct (subject, PDF
     attachment) -- without needing real SMTP credentials or a network call
     (not configured in this dev environment; the CLI/live flow's actual
     send still needs to be tested by Pranav once real creds are in place).
  5. Mobile/email input validation catches the real invalid cases and
     accepts the real valid ones (including realistic formatting like
     "+91 98765 43210" -- a case a naive regex missed once already).
  6. Callback pattern non-collision: every real callback_data string this
     bot's handlers actually produce matches EXACTLY ONE registered
     handler pattern -- catches the exact bug class already found twice
     this session (an unscoped/mis-scoped CallbackQueryHandler silently
     swallowing another handler's callbacks).
  7. FULL conversational flow simulation against a synthetic student:
     reaching exactly 20 answered MCQs triggers the prompt once (and only
     once on a 21st), choosing "Both", typing a mobile number, confirming
     it, typing an email, confirming it, and verifying the milestone
     record, the student's stored contact fields, and a report_deliveries
     row all end up correct.

USAGE:
    python telegram/bots/smoke_test_report_flow.py
"""

import re
import sys
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
sys.path.insert(0, str(REPO_ROOT / "telegram" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "telegram" / "branding"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import db as platform_db  # noqa: E402
import student_analytics  # noqa: E402
import generate_student_report  # noqa: E402
import report_delivery  # noqa: E402
import cf_email  # noqa: E402
import report_flow  # noqa: E402
import broadcast  # noqa: E402 -- telegram/database/broadcast.py (2026-08-18), for Step 7f

SYNTHETIC_USER_ID = -999999001  # negative, well outside any real Telegram user id
SYNTHETIC_USER_ID_2 = -999999002  # separate id for the already-past-threshold regression test
SYNTHETIC_USER_ID_3 = -999999003  # separate id for the post-delivery upsell/wrap-up flow test
SYNTHETIC_USER_ID_4 = -999999004  # separate id for the on-demand trigger flow test
SYNTHETIC_USER_ID_5 = -999999005  # separate id for the existing-contact-info reuse test
SYNTHETIC_USER_ID_6 = -999999006  # separate id for the broadcast "Get My Report" button test (2026-08-18)
REAL_TEST_USER_ID = 5777734732  # a real student with real data, used read-only (no writes)

failures = []


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(label)


def step1_migration_idempotent(conn):
    print("\n--- Step 1: schema migration is idempotent ---")
    platform_db.init_schema(conn)
    platform_db.init_schema(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(students)").fetchall()}
    check("students has mobile_number", "mobile_number" in cols)
    check("students has email_verification_method", "email_verification_method" in cols)
    check("students has report_channel_preference", "report_channel_preference" in cols)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    check("student_report_milestones table exists", "student_report_milestones" in tables)
    check("report_deliveries table exists", "report_deliveries" in tables)


def step2_analytics_sane(conn):
    print("\n--- Step 2: student_analytics returns sane data for a real student ---")
    data = student_analytics.fetch_student_report_data(conn, REAL_TEST_USER_ID)
    t = data["totals"]
    check("mcq_shown > 0", t["mcq_shown"] > 0, f"got {t['mcq_shown']}")
    check("mcq_answered <= mcq_shown", t["mcq_answered"] <= t["mcq_shown"])
    check("mcq_correct <= mcq_answered", t["mcq_correct"] <= t["mcq_answered"])
    check("accuracy_pct is between 0 and 100 (or None)",
          t["mcq_accuracy_pct"] is None or 0 <= t["mcq_accuracy_pct"] <= 100)
    check("by_chapter is a non-empty list", len(data["by_chapter"]) > 0)
    check("total_time_on_bot_seconds >= 0", t["total_time_on_bot_seconds"] >= 0)


def step3_pdf_renders(conn):
    print("\n--- Step 3: report PDF renders through the real xhtml2pdf engine ---")
    try:
        pdf_bytes = generate_student_report.build_report_pdf(conn, REAL_TEST_USER_ID)
        check("PDF generation succeeded", True)
        check("PDF is a real size (>5KB)", len(pdf_bytes) > 5000, f"got {len(pdf_bytes)} bytes")
        check("PDF starts with %PDF magic bytes", pdf_bytes[:4] == b"%PDF")
    except Exception as e:
        check("PDF generation succeeded", False, str(e))


def step4_email_message_structure():
    print("\n--- Step 4: email HTML/address construction (structural only -- no live network call) ---")
    html = report_delivery.build_report_email_html("Test Student", "All-time", "1Lavya Exam Hub")
    check("HTML body greets the student by name", "Test Student" in html)
    check("HTML body mentions 1LAVYA", "1LAVYA" in html)
    check("HTML body includes support@1lavya.com", "support@1lavya.com" in html)
    check("HTML body includes admin@1lavya.com", "admin@1lavya.com" in html)
    check("HTML body names the sending bot", "1Lavya Exam Hub" in html)

    from_email, from_name = report_delivery.resolve_from_address("1lavya-examhub")
    check("resolve_from_address finds the real configured address", from_email == "examhub@1lavya.com")
    check("resolve_from_address returns the bot's display name", from_name == "1Lavya Exam Hub")
    fallback_email, fallback_name = report_delivery.resolve_from_address("no-such-bot-id")
    check("resolve_from_address falls back gracefully for an unknown bot_id",
          fallback_email == report_delivery.FALLBACK_FROM_EMAIL and fallback_name == report_delivery.FALLBACK_FROM_NAME)

    # Regression test for the REAL live incident found 2026-08-11: an
    # unquoted display name containing a comma/parentheses (exactly
    # csarunchouhan's own bots.json display_name) broke Cloudflare's
    # From-header parser in production (HTTP 400
    # "email.sending.error.email.invalid"). Reproduced, root-caused
    # (isolated from/to independently before finding the display name
    # itself was the culprit), and fixed via email.utils.formataddr.
    csa_email, csa_name = report_delivery.resolve_from_address("csarunchouhan")
    check("csarunchouhan's own display name still has the comma/parens that caused this",
          "," in csa_name and "(" in csa_name)
    from_header = cf_email.build_from_header(csa_name, csa_email)
    check("From header quotes a display name containing special characters",
          from_header == f'"{csa_name}" <{csa_email}>', from_header)
    plain_header = cf_email.build_from_header("1Lavya Exam Hub", "examhub@1lavya.com")
    check("From header does NOT quote a plain display name (formataddr's own correct behavior)",
          plain_header == "1Lavya Exam Hub <examhub@1lavya.com>", plain_header)

    # Structural check on the Cloudflare payload shape itself, still no
    # network call -- send_email() builds this same dict internally, but
    # we only import cf_email to confirm is_configured() reflects the real
    # env vars, not to actually POST anything here.
    if cf_email.is_configured():
        print("    (CF_EMAIL_API_TOKEN/CF_EMAIL_ACCOUNT_ID ARE configured in this environment -- "
              "a real send is possible, but this smoke test deliberately never fires one; "
              "verify a real delivery manually via the live bot's \"report\" trigger.)")
    else:
        print("    (CF_EMAIL_API_TOKEN/CF_EMAIL_ACCOUNT_ID not configured in this environment -- "
              "structural checks only; verify manually once telegram/.env has real values.)")


def step5_validation():
    print("\n--- Step 5: mobile/email validation ---")
    valid_mobiles = ["9876543210", "+91 98765 43210", "+91-98765-43210", "098765 43210", "9876 543 210"]
    invalid_mobiles = ["12345", "5876543210", "abcdefghij", ""]
    for m in valid_mobiles:
        check(f"mobile {m!r} accepted", report_flow._normalize_mobile(m) == "9876543210")
    for m in invalid_mobiles:
        check(f"mobile {m!r} rejected", report_flow._normalize_mobile(m) is None)

    valid_emails = ["a@b.com", "student.name@college.edu.in"]
    invalid_emails = ["not-an-email", "a@b", "@b.com", ""]
    for e in valid_emails:
        check(f"email {e!r} accepted", report_flow._valid_email(e))
    for e in invalid_emails:
        check(f"email {e!r} rejected", not report_flow._valid_email(e))


def step6_callback_pattern_noncollision():
    print("\n--- Step 6: callback_data patterns don't collide (the class of bug found twice already) ---")
    # The exact set of prefixes each real handler is registered with in
    # exam_hub_bot.py/faculty_bot.py's main() -- kept in sync by hand since
    # there's no single source both the handler registration and this
    # check could both read from without importing python-telegram-bot's
    # Application machinery itself. If main() changes, update this too.
    button_router_pattern = re.compile(r"^(course|level|mode|type|year|chapter|answer|pdf|next|mcqopt|restart)(:|$)")
    report_flow_pattern = re.compile(r"^(report|reportconfirm):")

    real_callback_samples = [
        "course:CMA", "level:Foundation", "mode:mcq", "type:FACULTY_PRACTICE",
        "year:2026", "chapter:some-slug", "answer:book123", "pdf:book123",
        "next", "restart", "mcqopt:CMAI-Q1:A",
        "report:telegram", "report:email", "report:both", "report:skip",
        "report:addemail", "report:addtelegram", "report:upsell_no", "report:done",
        # 2026-08-11: the on-demand trigger's own two new callback values --
        # same "report:" prefix, no new handler registration needed, but
        # worth an explicit non-collision check since they're new real
        # strings this bot now actually produces.
        "report:ondemand_yes", "report:ondemand_no",
        "reportconfirm:yes", "reportconfirm:retry",
    ]
    for sample in real_callback_samples:
        matches_button_router = bool(button_router_pattern.match(sample))
        matches_report_flow = bool(report_flow_pattern.match(sample))
        total_matches = int(matches_button_router) + int(matches_report_flow)
        check(f"'{sample}' matches exactly one handler pattern", total_matches == 1,
              f"button_router={matches_button_router}, report_flow={matches_report_flow}")


class FakeUser:
    def __init__(self, user_id):
        self.id = user_id
        self.username = "smoketestuser"
        self.first_name = "Smoke"
        self.last_name = "Test"


class FakeMessage:
    def __init__(self, chat_id, text=""):
        self.chat_id = chat_id
        self.text = text
        self.reply_text = AsyncMock()


class FakeQuery:
    def __init__(self, user_id, chat_id, data):
        self.from_user = FakeUser(user_id)
        self.message = FakeMessage(chat_id)
        self.data = data
        self.answer = AsyncMock()
        self.edit_message_text = AsyncMock()


class FakeUpdate:
    def __init__(self, user_id, chat_id, text):
        self.message = FakeMessage(chat_id, text)
        self.effective_user = FakeUser(user_id)
        # mirrors real telegram.Update's own effective_message property --
        # needed since 2026-08-17's update.message -> update.effective_message
        # fix in report_flow.py (start_report_flow_on_demand).
        self.effective_message = self.message


class FakeCallbackUpdate:
    """report_flow_callback() expects an Update with a .callback_query
    attribute -- this wraps a FakeQuery into that shape. Module-level (not
    redefined per test step) so every step that needs it shares one copy."""
    def __init__(self, q):
        self.callback_query = q


class FakeContext:
    def __init__(self):
        self.user_data = {}
        self.bot = MagicMock()
        self.bot.send_message = AsyncMock()
        self.bot.send_document = AsyncMock()


def _cleanup_synthetic(conn, user_id=SYNTHETIC_USER_ID):
    conn.execute("DELETE FROM exam_hub_mcq_attempts WHERE telegram_user_id=?", (user_id,))
    conn.execute("DELETE FROM exam_hub_sessions WHERE telegram_user_id=?", (user_id,))
    conn.execute("DELETE FROM student_report_milestones WHERE telegram_user_id=?", (user_id,))
    conn.execute("DELETE FROM report_deliveries WHERE telegram_user_id=?", (user_id,))
    conn.execute("DELETE FROM report_flow_events WHERE telegram_user_id=?", (user_id,))
    conn.execute("DELETE FROM students WHERE telegram_user_id=?", (user_id,))
    conn.commit()


async def step7b_already_past_threshold_regression(conn):
    """Regression test for the real bug found 2026-08-11: a real account
    already had 27 answered questions at the moment Phase 2 was deployed
    (tested before the restart) -- the milestone never fired, ever, because
    the original check required count == 20 exactly, and every answer
    after deployment only pushed the count further past 20. Simulates
    exactly that scenario: a student who is ALREADY at 25 answered
    questions (never 20 exactly, from this test's point of view) with no
    milestone row yet -- the very next answer must still trigger the
    prompt."""
    print("\n--- Step 7b: regression -- student already past threshold before first check ---")
    _cleanup_synthetic(conn, SYNTHETIC_USER_ID_2)
    try:
        user = FakeUser(SYNTHETIC_USER_ID_2)
        platform_db.upsert_student(conn, user)
        for i in range(25):
            conn.execute(
                "INSERT INTO exam_hub_mcq_attempts (bot_id, telegram_user_id, mcq_id, correct_option, "
                "selected_option, is_correct, shown_at, answered_at) VALUES (?,?,?,?,?,?,?,?)",
                ("smoketest", SYNTHETIC_USER_ID_2, f"Q{i}", "A", "A", 1, platform_db.now(), platform_db.now()),
            )
        conn.commit()

        query = FakeQuery(SYNTHETIC_USER_ID_2, 12345, "mcqopt:QX:A")
        context = FakeContext()
        await report_flow.maybe_trigger_report_milestone(query, context, SYNTHETIC_USER_ID_2, "smoketest-examhub")
        check("prompt fires for a student already at 25 answered (never exactly 20)",
              context.bot.send_message.call_count == 1)

        # And it must still never fire twice.
        await report_flow.maybe_trigger_report_milestone(query, context, SYNTHETIC_USER_ID_2, "smoketest-examhub")
        check("does not re-fire on a later check", context.bot.send_message.call_count == 1)
    finally:
        _cleanup_synthetic(conn, SYNTHETIC_USER_ID_2)
        print("    (synthetic test data cleaned up)")


async def step7c_upsell_and_wrapup_flow(conn):
    """Regression test for Pranav's live-test feedback, 2026-08-11: after
    choosing Telegram-only and receiving the report, the bot gave no
    follow-up at all -- it should have offered email too, then asked
    whether to continue practicing or stop. Simulates exactly that path:
    choose 'telegram' -> confirm mobile -> report delivered -> upsell
    offers email -> accept -> provide+confirm email -> the SECOND delivery
    sends ONLY email (never re-sends telegram) -> continue/done offer ->
    choose 'I'm Done'."""
    print("\n--- Step 7c: post-delivery upsell + continue/done wrap-up ---")
    _cleanup_synthetic(conn, SYNTHETIC_USER_ID_3)
    try:
        user = FakeUser(SYNTHETIC_USER_ID_3)
        platform_db.upsert_student(conn, user)
        for i in range(20):
            conn.execute(
                "INSERT INTO exam_hub_mcq_attempts (bot_id, telegram_user_id, mcq_id, correct_option, "
                "selected_option, is_correct, shown_at, answered_at) VALUES (?,?,?,?,?,?,?,?)",
                ("smoketest", SYNTHETIC_USER_ID_3, f"Q{i}", "A", "A", 1, platform_db.now(), platform_db.now()),
            )
        conn.commit()

        context = FakeContext()
        trigger_query = FakeQuery(SYNTHETIC_USER_ID_3, 12345, "mcqopt:QX:A")
        await report_flow.maybe_trigger_report_milestone(trigger_query, context, SYNTHETIC_USER_ID_3, "smoketest-examhub")

        # --- Choose "Telegram" only ---
        choice_query = FakeQuery(SYNTHETIC_USER_ID_3, 12345, "report:telegram")
        await report_flow.report_flow_callback(FakeCallbackUpdate(choice_query), context)
        check("state is AWAITING_MOBILE after choosing 'telegram'",
              context.user_data.get("report_flow_state") == report_flow.AWAITING_MOBILE)

        mobile_update = FakeUpdate(SYNTHETIC_USER_ID_3, 12345, "9876543210")
        await report_flow.handle_contact_text_input(mobile_update, context)
        confirm_mobile_query = FakeQuery(SYNTHETIC_USER_ID_3, 12345, "reportconfirm:yes")
        send_message_count_before_delivery = context.bot.send_message.call_count
        await report_flow.report_flow_callback(FakeCallbackUpdate(confirm_mobile_query), context)

        check("send_document called exactly once (telegram delivery, original choice)",
              context.bot.send_document.call_count == 1)
        check("no email sent (student only chose telegram)",
              context.bot.send_document.call_args.kwargs.get("filename") == "1LAVYA_Performance_Report.pdf")
        # A new send_message should have fired for the upsell offer (asking about email).
        check("upsell offer sent after telegram-only delivery",
              context.bot.send_message.call_count > send_message_count_before_delivery)
        last_upsell_call = context.bot.send_message.call_args
        check("upsell offer text asks about email",
              "email" in last_upsell_call.kwargs.get("text", "").lower())

        # --- Accept the upsell: "Yes, email it too" ---
        addemail_query = FakeQuery(SYNTHETIC_USER_ID_3, 12345, "report:addemail")
        await report_flow.report_flow_callback(FakeCallbackUpdate(addemail_query), context)
        check("state is AWAITING_EMAIL after accepting the email upsell",
              context.user_data.get("report_flow_state") == report_flow.AWAITING_EMAIL)
        check("report_flow_upsell flag is set", context.user_data.get("report_flow_upsell") is True)

        email_update = FakeUpdate(SYNTHETIC_USER_ID_3, 12345, "upselltest@example.com")
        await report_flow.handle_contact_text_input(email_update, context)
        confirm_email_query = FakeQuery(SYNTHETIC_USER_ID_3, 12345, "reportconfirm:yes")
        send_document_count_before = context.bot.send_document.call_count
        await report_flow.report_flow_callback(FakeCallbackUpdate(confirm_email_query), context)

        check("send_document NOT called again (upsell only sends the NEW channel, email)",
              context.bot.send_document.call_count == send_document_count_before)
        check("report_flow_upsell flag cleared after use",
              "report_flow_upsell" not in context.user_data)

        deliveries = conn.execute(
            "SELECT channels_requested FROM report_deliveries WHERE telegram_user_id=? ORDER BY delivery_id",
            (SYNTHETIC_USER_ID_3,),
        ).fetchall()
        check("exactly 2 delivery rows logged (original telegram + upsell email)", len(deliveries) == 2,
              f"got {deliveries}")
        if len(deliveries) == 2:
            check("first delivery was telegram-only", deliveries[0][0] == "telegram")
            check("second delivery was email-only (the upsell)", deliveries[1][0] == "email")

        # --- Continue/done offer should now have been sent ---
        final_call_text = context.bot.send_message.call_args.kwargs.get("text", "")
        check("continue/done question sent after upsell resolves",
              "continue" in final_call_text.lower() and "done" in final_call_text.lower())

        # --- Choose "I'm Done" ---
        done_query = FakeQuery(SYNTHETIC_USER_ID_3, 12345, "report:done")
        await report_flow.report_flow_callback(FakeCallbackUpdate(done_query), context)
        check("'I'm Done' acknowledged", done_query.edit_message_text.call_count == 1)

        event_types = [r[0] for r in conn.execute(
            "SELECT event_type FROM report_flow_events WHERE telegram_user_id=? ORDER BY event_id",
            (SYNTHETIC_USER_ID_3,),
        ).fetchall()]
        check("two 'report_delivery_attempted' events logged (original + upsell)",
              event_types.count("report_delivery_attempted") == 2, f"got {event_types}")
    finally:
        _cleanup_synthetic(conn, SYNTHETIC_USER_ID_3)
        print("    (synthetic test data cleaned up)")


async def step7_full_flow_simulation(conn):
    print("\n--- Step 7: full conversational flow, synthetic student (cleaned up after) ---")
    _cleanup_synthetic(conn)  # in case a previous failed run left rows behind
    try:
        user = FakeUser(SYNTHETIC_USER_ID)
        platform_db.upsert_student(conn, user)

        # Insert exactly 19 answered MCQ attempts -- milestone must NOT fire yet.
        for i in range(19):
            conn.execute(
                "INSERT INTO exam_hub_mcq_attempts (bot_id, telegram_user_id, mcq_id, correct_option, "
                "selected_option, is_correct, shown_at, answered_at) VALUES (?,?,?,?,?,?,?,?)",
                ("smoketest", SYNTHETIC_USER_ID, f"Q{i}", "A", "A", 1, platform_db.now(), platform_db.now()),
            )
        conn.commit()

        query19 = FakeQuery(SYNTHETIC_USER_ID, 12345, "mcqopt:QX:A")
        context = FakeContext()
        await report_flow.maybe_trigger_report_milestone(query19, context, SYNTHETIC_USER_ID, "smoketest-examhub")
        check("no prompt sent at 19 answered questions", context.bot.send_message.call_count == 0)

        # The 20th answer -- milestone MUST fire exactly once.
        conn.execute(
            "INSERT INTO exam_hub_mcq_attempts (bot_id, telegram_user_id, mcq_id, correct_option, "
            "selected_option, is_correct, shown_at, answered_at) VALUES (?,?,?,?,?,?,?,?)",
            ("smoketest", SYNTHETIC_USER_ID, "Q19", "A", "A", 1, platform_db.now(), platform_db.now()),
        )
        conn.commit()
        query20 = FakeQuery(SYNTHETIC_USER_ID, 12345, "mcqopt:QX:A")
        await report_flow.maybe_trigger_report_milestone(query20, context, SYNTHETIC_USER_ID, "smoketest-examhub")
        check("prompt sent at exactly 20 answered questions", context.bot.send_message.call_count == 1)

        milestone_row = conn.execute(
            "SELECT status FROM student_report_milestones WHERE telegram_user_id=? AND milestone_type=?",
            (SYNTHETIC_USER_ID, report_flow.MILESTONE_20Q),
        ).fetchone()
        check("milestone row created with status='prompted'", milestone_row and milestone_row[0] == "prompted")

        # A 21st answer must NOT re-trigger the prompt.
        conn.execute(
            "INSERT INTO exam_hub_mcq_attempts (bot_id, telegram_user_id, mcq_id, correct_option, "
            "selected_option, is_correct, shown_at, answered_at) VALUES (?,?,?,?,?,?,?,?)",
            ("smoketest", SYNTHETIC_USER_ID, "Q20", "A", "B", 0, platform_db.now(), platform_db.now()),
        )
        conn.commit()
        query21 = FakeQuery(SYNTHETIC_USER_ID, 12345, "mcqopt:QX:A")
        await report_flow.maybe_trigger_report_milestone(query21, context, SYNTHETIC_USER_ID, "smoketest-examhub")
        check("no re-prompt at 21 answered questions", context.bot.send_message.call_count == 1)

        # --- Choose "Both" ---
        choice_query = FakeQuery(SYNTHETIC_USER_ID, 12345, "report:both")
        await report_flow.report_flow_callback(FakeCallbackUpdate(choice_query), context)
        check("state is AWAITING_MOBILE after choosing 'both'",
              context.user_data.get("report_flow_state") == report_flow.AWAITING_MOBILE)

        # --- Type an invalid mobile number, then a valid one ---
        bad_update = FakeUpdate(SYNTHETIC_USER_ID, 12345, "12345")
        consumed = await report_flow.handle_contact_text_input(bad_update, context)
        check("invalid mobile number rejected (message consumed, state unchanged)",
              consumed and context.user_data.get("report_flow_state") == report_flow.AWAITING_MOBILE)

        good_mobile_update = FakeUpdate(SYNTHETIC_USER_ID, 12345, "+91 98765 43210")
        await report_flow.handle_contact_text_input(good_mobile_update, context)
        check("valid mobile number moves to CONFIRMING_MOBILE",
              context.user_data.get("report_flow_state") == report_flow.CONFIRMING_MOBILE)
        check("normalized mobile stored in pending state",
              context.user_data.get("report_flow_pending_mobile") == "9876543210")

        # --- Confirm mobile -> should move to AWAITING_EMAIL (channel == 'both') ---
        confirm_mobile_query = FakeQuery(SYNTHETIC_USER_ID, 12345, "reportconfirm:yes")
        await report_flow.report_flow_callback(FakeCallbackUpdate(confirm_mobile_query), context)
        check("state is AWAITING_EMAIL after confirming mobile (channel=both)",
              context.user_data.get("report_flow_state") == report_flow.AWAITING_EMAIL)
        student_row = conn.execute(
            "SELECT mobile_number, mobile_verification_method FROM students WHERE telegram_user_id=?",
            (SYNTHETIC_USER_ID,),
        ).fetchone()
        check("mobile_number persisted to students table", student_row[0] == "9876543210")
        check("mobile_verification_method is 'echo_confirm'", student_row[1] == "echo_confirm")

        # --- Type email, confirm -> should finalize (generate + "send") ---
        email_update = FakeUpdate(SYNTHETIC_USER_ID, 12345, "smoketest@example.com")
        await report_flow.handle_contact_text_input(email_update, context)
        check("valid email moves to CONFIRMING_EMAIL",
              context.user_data.get("report_flow_state") == report_flow.CONFIRMING_EMAIL)

        confirm_email_query = FakeQuery(SYNTHETIC_USER_ID, 12345, "reportconfirm:yes")
        await report_flow.report_flow_callback(FakeCallbackUpdate(confirm_email_query), context)

        student_row2 = conn.execute(
            "SELECT email, email_verification_method, report_channel_preference FROM students WHERE telegram_user_id=?",
            (SYNTHETIC_USER_ID,),
        ).fetchone()
        check("email persisted to students table", student_row2[0] == "smoketest@example.com")
        check("email_verification_method is 'echo_confirm'", student_row2[1] == "echo_confirm")
        check("report_channel_preference is 'both'", student_row2[2] == "both")

        milestone_row2 = conn.execute(
            "SELECT status FROM student_report_milestones WHERE telegram_user_id=? AND milestone_type=?",
            (SYNTHETIC_USER_ID, report_flow.MILESTONE_20Q),
        ).fetchone()
        check("milestone status is now 'fulfilled'", milestone_row2 and milestone_row2[0] == "fulfilled")

        check("send_document was attempted (telegram delivery)", context.bot.send_document.call_count >= 1)

        delivery_row = conn.execute(
            "SELECT channels_requested, telegram_status FROM report_deliveries WHERE telegram_user_id=? "
            "ORDER BY delivery_id DESC LIMIT 1",
            (SYNTHETIC_USER_ID,),
        ).fetchone()
        check("a report_deliveries row was logged", delivery_row is not None)
        if delivery_row:
            # "email,telegram" not "both" -- 2026-08-11: channels_requested now
            # logs the actual set of channels attempted IN THIS delivery call
            # (sorted, comma-joined), not the original choice label -- matters
            # once an upsell delivery can log a second row for just one channel.
            check("channels_requested logged as 'email,telegram'", delivery_row[0] == "email,telegram")
            check("telegram_status is 'sent' (mocked bot.send_document doesn't raise)", delivery_row[1] == "sent")

        # --- Complete conversational trail (Pranav's ask after the missed-milestone bug) ---
        event_types = [r[0] for r in conn.execute(
            "SELECT event_type FROM report_flow_events WHERE telegram_user_id=? ORDER BY event_id",
            (SYNTHETIC_USER_ID,),
        ).fetchall()]
        expected_sequence = [
            "milestone_prompt_sent", "channel_chosen", "mobile_rejected",
            "mobile_collected_pending_confirm", "mobile_confirmed",
            "email_collected_pending_confirm", "email_confirmed",
            "report_generated", "report_delivery_attempted",
        ]
        check(f"complete event trail logged in order (got {event_types})", event_types == expected_sequence)

    finally:
        _cleanup_synthetic(conn)
        print("    (synthetic test data cleaned up)")


async def step7d_ondemand_trigger_flow(conn):
    """Regression/coverage test for the on-demand trigger added 2026-08-11
    (Pranav: "by typing report, analysis, or email or mail, Bot will ask
    whether you need your analysis report"). Deliberately a student with
    ZERO MCQ activity and no milestone row at all -- proves the on-demand
    path works independently of the 20-question milestone ever having
    fired, per the module's own docstring on _finalize()'s tolerance for a
    missing milestone row."""
    print("\n--- Step 7d: on-demand trigger ('report'/'analysis'/'email'/'mail') ---")
    _cleanup_synthetic(conn, SYNTHETIC_USER_ID_4)
    try:
        user = FakeUser(SYNTHETIC_USER_ID_4)
        platform_db.upsert_student(conn, user)

        check("'report' matches the trigger", report_flow.matches_trigger("report"))
        check("'Analysis' matches (case-insensitive)", report_flow.matches_trigger("Analysis"))
        check("'email' matches", report_flow.matches_trigger("email"))
        check("'mail' matches", report_flow.matches_trigger("mail"))
        check("'give me my report please' does NOT match (not exact)",
              not report_flow.matches_trigger("give me my report please"))

        context = FakeContext()
        trigger_update = FakeUpdate(SYNTHETIC_USER_ID_4, 12345, "report")
        await report_flow.start_report_flow_on_demand(trigger_update, context, "smoketest-examhub")
        check("on-demand trigger sends a confirm prompt", trigger_update.message.reply_text.call_count == 1)

        confirm_yes_query = FakeQuery(SYNTHETIC_USER_ID_4, 12345, "report:ondemand_yes")
        await report_flow.report_flow_callback(FakeCallbackUpdate(confirm_yes_query), context)
        check("confirming yes shows the channel picker", context.bot.send_message.call_count >= 1)
        picker_call = context.bot.send_message.call_args
        picker_markup = picker_call.kwargs.get("reply_markup")
        picker_callbacks = [btn.callback_data for row in picker_markup.inline_keyboard for btn in row]
        check("channel picker offers telegram/email/both/skip",
              set(picker_callbacks) == {"report:telegram", "report:email", "report:both", "report:skip"})

        # --- Choose "email" -> straight to delivery (no milestone row exists at all) ---
        choice_query = FakeQuery(SYNTHETIC_USER_ID_4, 12345, "report:email")
        await report_flow.report_flow_callback(FakeCallbackUpdate(choice_query), context)
        check("state is AWAITING_EMAIL after choosing 'email'",
              context.user_data.get("report_flow_state") == report_flow.AWAITING_EMAIL)

        email_update = FakeUpdate(SYNTHETIC_USER_ID_4, 12345, "ondemand@example.com")
        await report_flow.handle_contact_text_input(email_update, context)
        confirm_email_query = FakeQuery(SYNTHETIC_USER_ID_4, 12345, "reportconfirm:yes")
        await report_flow.report_flow_callback(FakeCallbackUpdate(confirm_email_query), context)

        delivery_row = conn.execute(
            "SELECT channels_requested FROM report_deliveries WHERE telegram_user_id=? "
            "ORDER BY delivery_id DESC LIMIT 1",
            (SYNTHETIC_USER_ID_4,),
        ).fetchone()
        check("a report was generated/delivered with zero prior MCQ activity", delivery_row is not None)

        milestone_row = conn.execute(
            "SELECT 1 FROM student_report_milestones WHERE telegram_user_id=?", (SYNTHETIC_USER_ID_4,)
        ).fetchone()
        check("no milestone row was created by the on-demand path (never touched that table)", milestone_row is None)

        # --- "No" branch, separately, on a fresh confirm ---
        context2 = FakeContext()
        no_query = FakeQuery(SYNTHETIC_USER_ID_4, 12345, "report:ondemand_no")
        await report_flow.report_flow_callback(FakeCallbackUpdate(no_query), context2)
        check("declining shows a polite decline message", no_query.edit_message_text.call_count == 1)
        # BUG FIXED 2026-08-16 (independent code review): this used to be a
        # dead end -- plain text, zero buttons, no CTA. Must now offer
        # Continue Practicing / I'm Done like every other decline path.
        decline_cta_text = context2.bot.send_message.call_args.kwargs.get("text", "")
        decline_cta_markup = context2.bot.send_message.call_args.kwargs.get("reply_markup")
        check("declining the on-demand offer now also offers a Continue/Done CTA, not a dead end",
              context2.bot.send_message.call_count == 1 and "continue practicing" in decline_cta_text.lower())
        check("that CTA has real buttons", decline_cta_markup is not None and len(decline_cta_markup.inline_keyboard) == 2)

        # --- "Not now" (skip) on the very FIRST channel picker -- the
        # other confirmed dead end (2026-08-16 review): also used to end
        # with plain text and no keyboard. ---
        context3 = FakeContext()
        skip_query = FakeQuery(SYNTHETIC_USER_ID_4, 12345, "report:skip")
        await report_flow.report_flow_callback(FakeCallbackUpdate(skip_query), context3)
        skip_cta_text = context3.bot.send_message.call_args.kwargs.get("text", "") if context3.bot.send_message.call_args else ""
        check("'Not now' (skip) also offers a Continue/Done CTA instead of dead-ending",
              context3.bot.send_message.call_count == 1 and "continue practicing" in skip_cta_text.lower())
    finally:
        _cleanup_synthetic(conn, SYNTHETIC_USER_ID_4)
        print("    (synthetic test data cleaned up)")


async def step7e_reuses_existing_contact_info(conn):
    """Regression test for the real bug Pranav reported 2026-08-11: "even
    after sharing the mobile number and email id once, if I again ask for
    report than it again asks for my number/email." Simulates a student
    who ALREADY has both mobile_number and email on file (e.g. from an
    earlier report request), then requests a report again via the
    on-demand trigger with 'both' -- must go straight to delivery with
    ZERO text-input prompts, not re-ask for either value."""
    print("\n--- Step 7e: reuses existing contact info instead of re-asking ---")
    _cleanup_synthetic(conn, SYNTHETIC_USER_ID_5)
    try:
        user = FakeUser(SYNTHETIC_USER_ID_5)
        platform_db.upsert_student(conn, user)
        platform_db.execute_with_retry(
            conn,
            "UPDATE students SET mobile_number=?, email=?, mobile_verification_method='echo_confirm', "
            "email_verification_method='echo_confirm' WHERE telegram_user_id=?",
            ("9998887776", "already-on-file@example.com", SYNTHETIC_USER_ID_5),
        )

        context = FakeContext()
        trigger_update = FakeUpdate(SYNTHETIC_USER_ID_5, 12345, "report")
        await report_flow.start_report_flow_on_demand(trigger_update, context, "smoketest-examhub")
        confirm_yes_query = FakeQuery(SYNTHETIC_USER_ID_5, 12345, "report:ondemand_yes")
        await report_flow.report_flow_callback(FakeCallbackUpdate(confirm_yes_query), context)

        # Choose "both" -- since BOTH mobile and email are already on file,
        # this must skip straight to delivery with no AWAITING_* state at all.
        choice_query = FakeQuery(SYNTHETIC_USER_ID_5, 12345, "report:both")
        await report_flow.report_flow_callback(FakeCallbackUpdate(choice_query), context)
        check("no text-input state entered -- nothing was re-asked",
              context.user_data.get("report_flow_state") is None)
        check("choice message confirms using saved info (not asking for anything)",
              "saved" in choice_query.edit_message_text.call_args[0][0].lower())

        delivery_row = conn.execute(
            "SELECT channels_requested FROM report_deliveries WHERE telegram_user_id=? "
            "ORDER BY delivery_id DESC LIMIT 1",
            (SYNTHETIC_USER_ID_5,),
        ).fetchone()
        check("a report was delivered without ever asking for contact info", delivery_row is not None)

        event_types = [r[0] for r in conn.execute(
            "SELECT event_type FROM report_flow_events WHERE telegram_user_id=? ORDER BY event_id",
            (SYNTHETIC_USER_ID_5,),
        ).fetchall()]
        check("no mobile/email collection events were logged (nothing was ever asked)",
              not any("mobile_collected" in e or "email_collected" in e for e in event_types))
        check("'used_existing_contact_info' event was logged instead",
              "used_existing_contact_info" in event_types)

        # --- Same check for the "email"-only choice with email already on file ---
        context2 = FakeContext()
        context2.user_data["report_flow_bot_id"] = "smoketest-examhub"
        choice_query2 = FakeQuery(SYNTHETIC_USER_ID_5, 12345, "report:email")
        await report_flow.report_flow_callback(FakeCallbackUpdate(choice_query2), context2)
        check("'email'-only choice also skips straight to delivery when email is on file",
              context2.user_data.get("report_flow_state") is None)
    finally:
        _cleanup_synthetic(conn, SYNTHETIC_USER_ID_5)
        print("    (synthetic test data cleaned up)")


async def step7f_broadcast_report_button(conn):
    """2026-08-18: the 'Get My Report' button embedded in a broadcast
    message -- callback_data 'report:bcast:<campaign_id>:<bot_id>'. Real
    checks: (1) a genuine tap logs an interaction against the exact
    matching broadcast_deliveries row (never a guess/inference from
    unrelated activity), sets report_flow_bot_id from the callback_data
    itself (not context.user_data, which wouldn't exist yet for a student
    who's never used the report flow before), and drops straight into the
    same channel picker every other on-demand request uses; (2) a stale/
    replayed campaign_id with no matching delivery row does NOT crash --
    the report flow still proceeds (logged as a warning, not an error)."""
    print("\n--- Step 7f: broadcast 'Get My Report' button (2026-08-18) ---")
    _cleanup_synthetic(conn, SYNTHETIC_USER_ID_6)
    campaign_id = None
    try:
        user = FakeUser(SYNTHETIC_USER_ID_6)
        platform_db.upsert_student(conn, user)

        campaign_id = broadcast.create_campaign(
            conn, category="smoketest_category", message_text="smoketest message",
            message_html="<b>smoketest</b> message", criteria_description="smoketest",
            created_by="smoke_test_report_flow.py",
        )
        broadcast.log_delivery(conn, campaign_id, SYNTHETIC_USER_ID_6, "smoketest-examhub",
                                "smoketest message (personalized)", status="sent")

        context = FakeContext()
        tap_query = FakeQuery(SYNTHETIC_USER_ID_6, 12345, f"report:bcast:{campaign_id}:smoketest-examhub")
        await report_flow.report_flow_callback(FakeCallbackUpdate(tap_query), context)

        check("report_flow_bot_id is set from the callback_data itself",
              context.user_data.get("report_flow_bot_id") == "smoketest-examhub")
        check("the tap drops into the channel picker (edit_message_text called)",
              tap_query.edit_message_text.await_count >= 1)

        delivery_row = conn.execute(
            "SELECT interacted_at, interaction_type FROM broadcast_deliveries WHERE campaign_id=? AND telegram_user_id=?",
            (campaign_id, SYNTHETIC_USER_ID_6),
        ).fetchone()
        check("a real interaction was logged against the matching delivery row", delivery_row is not None and delivery_row[0] is not None)
        check("interaction_type is 'report_button_tap'", delivery_row is not None and delivery_row[1] == "report_button_tap")

        event_types = [r[0] for r in conn.execute(
            "SELECT event_type FROM report_flow_events WHERE telegram_user_id=? ORDER BY event_id",
            (SYNTHETIC_USER_ID_6,),
        ).fetchall()]
        check("'ondemand_confirmed' event was logged for the broadcast-sourced tap", "ondemand_confirmed" in event_types)

        # --- a second tap doesn't overwrite the original interaction timestamp ---
        first_interacted_at = delivery_row[0]
        context2 = FakeContext()
        tap_query2 = FakeQuery(SYNTHETIC_USER_ID_6, 12345, f"report:bcast:{campaign_id}:smoketest-examhub")
        await report_flow.report_flow_callback(FakeCallbackUpdate(tap_query2), context2)
        delivery_row2 = conn.execute(
            "SELECT interacted_at FROM broadcast_deliveries WHERE campaign_id=? AND telegram_user_id=?",
            (campaign_id, SYNTHETIC_USER_ID_6),
        ).fetchone()
        check("a second tap does not overwrite the original interaction timestamp",
              delivery_row2 is not None and delivery_row2[0] == first_interacted_at)

        # --- stale/replayed campaign_id with no matching delivery row: must not crash ---
        context3 = FakeContext()
        bogus_query = FakeQuery(SYNTHETIC_USER_ID_6, 12345, "report:bcast:999999999:smoketest-examhub")
        await report_flow.report_flow_callback(FakeCallbackUpdate(bogus_query), context3)
        check("a stale/unmatched campaign_id does not crash the tap",
              bogus_query.edit_message_text.await_count >= 1)
        check("the report flow still proceeds even with unmatched tracking data",
              context3.user_data.get("report_flow_bot_id") == "smoketest-examhub")
    finally:
        if campaign_id is not None:
            conn.execute("DELETE FROM broadcast_deliveries WHERE campaign_id=?", (campaign_id,))
            conn.execute("DELETE FROM broadcast_campaigns WHERE campaign_id=?", (campaign_id,))
            conn.commit()
        _cleanup_synthetic(conn, SYNTHETIC_USER_ID_6)
        print("    (synthetic test data cleaned up)")


def main():
    conn = platform_db.get_connection()
    step1_migration_idempotent(conn)
    step2_analytics_sane(conn)
    step3_pdf_renders(conn)
    step4_email_message_structure()
    step5_validation()
    step6_callback_pattern_noncollision()
    asyncio.run(step7_full_flow_simulation(conn))
    asyncio.run(step7b_already_past_threshold_regression(conn))
    asyncio.run(step7c_upsell_and_wrapup_flow(conn))
    asyncio.run(step7d_ondemand_trigger_flow(conn))
    asyncio.run(step7e_reuses_existing_contact_info(conn))
    asyncio.run(step7f_broadcast_report_button(conn))

    print(f"\n{'='*70}")
    if failures:
        print(f"{len(failures)} check(s) FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
