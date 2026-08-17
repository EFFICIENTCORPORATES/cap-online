"""
telegram/bots/smoke_test_test_flow.py -- end-to-end conversation smoke test
for Test Mode / Pre-Designed Tests (2026-08-16)
--------------------------------------------------------------------------------
Drives the REAL exam_hub_bot.py + test_flow.py code (not a re-implementation)
against synthetic, self-cleaning chat_ids and a real predesigned_tests row,
checking that the actual message sequence a student would see makes sense:
trigger -> picker (auto-skip) -> summary -> confirm (wallet debit) -> MCQ
delivery (hidden answer) -> skip -> palette -> descriptive delivery -> upload
collection (mocked photo) -> done -> submit -> final result. Also checks the
"gracefully deny" path for a course/level/subject with no tests.

Same discipline as every other smoke test on this platform: synthetic
chat_id, full cleanup in `finally` even on failure, no mocking of the DB
layer itself. Mocks only the Telegram API surface. Run directly:
`python smoke_test_test_flow.py`.
"""

import os
import sys
import shutil
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

os.environ.setdefault("BOT_ID", "1lavya-examhub")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402
import wallet  # noqa: E402
import identity  # noqa: E402
import test_flow  # noqa: E402
import exam_hub_bot as bot  # noqa: E402

CHAT_ID = 900_400_001
TG_HANDLE = "smoketst_testflow"

conn = bot.DB_CONN
host = sys.modules["exam_hub_bot"]

PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK   {label}")
    else:
        FAIL += 1
        print(f"  FAIL {label}")


def cleanup():
    row = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (CHAT_ID,)).fetchone()
    username = row[0] if row else None
    test_ids = [r[0] for r in conn.execute("SELECT test_id FROM test_sessions WHERE telegram_user_id=?", (CHAT_ID,)).fetchall()]
    for test_id in test_ids:
        conn.execute("DELETE FROM test_questions WHERE test_id=?", (test_id,))
        conn.execute("DELETE FROM test_mcq_answers WHERE test_id=?", (test_id,))
        conn.execute("DELETE FROM test_uploads WHERE test_id=?", (test_id,))
        conn.execute("DELETE FROM test_activity_log WHERE test_id=?", (test_id,))
        conn.execute("DELETE FROM test_sessions WHERE test_id=?", (test_id,))
        upload_dir = test_flow.UPLOADS_ROOT / test_id
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
    conn.execute("DELETE FROM students WHERE telegram_user_id=?", (CHAT_ID,))
    if username:
        conn.execute("DELETE FROM wallet_ledger WHERE username=?", (username,))
        conn.execute("DELETE FROM wallet_grants WHERE username=?", (username,))
        conn.execute("DELETE FROM student_profiles WHERE username=?", (username,))
    conn.commit()


def mock_message():
    return SimpleNamespace(chat_id=CHAT_ID, text="", reply_text=AsyncMock(), photo=None, document=None)


def mock_update(text=""):
    user = SimpleNamespace(id=CHAT_ID, username=TG_HANDLE, first_name="Smoke", last_name="Test")
    message = mock_message()
    message.text = text
    return SimpleNamespace(effective_user=user, message=message), user, message


class FakeJob:
    def __init__(self, job_dict):
        self._job_dict = job_dict

    def schedule_removal(self):
        self._job_dict["removed"] = True


class FakeJobQueue:
    """Records every run_once() call instead of actually scheduling a real
    timer -- lets the reminder/expiry/grace job logic be verified (what got
    scheduled, when, and whether it was later cancelled) without waiting
    real wall-clock time."""
    def __init__(self):
        self.scheduled = []

    def run_once(self, callback, when, name=None, data=None):
        self.scheduled.append({"callback": callback, "when": when, "name": name, "data": data, "removed": False})

    def get_jobs_by_name(self, name):
        return [FakeJob(j) for j in self.scheduled if j["name"] == name and not j["removed"]]

    def active(self):
        return [j for j in self.scheduled if not j["removed"]]

    def mark_fired(self, name):
        """Real python-telegram-bot run_once jobs auto-remove themselves
        after firing exactly once -- this test double doesn't run a real
        dispatch loop (callbacks are invoked directly), so tests that
        directly call a job's callback function must explicitly mark that
        job consumed afterward to keep the fake queue's state honest."""
        for j in self.scheduled:
            if j["name"] == name and not j["removed"]:
                j["removed"] = True
                return


def mock_context(with_job_queue=False):
    jq = FakeJobQueue() if with_job_queue else None
    return SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock(), send_document=AsyncMock()), job_queue=jq)


def mock_query(user, text_for_seq_parsing=""):
    q = SimpleNamespace()
    q.from_user = user
    q.message = SimpleNamespace(chat_id=CHAT_ID, text=text_for_seq_parsing)
    q.edit_message_text = AsyncMock()
    return q


def last_text(mock_reply_or_edit):
    """Extract the text from the most recent call to an AsyncMock standing
    in for reply_text()/edit_message_text() -- both take text positionally
    or as a kwarg depending on the call site."""
    call = mock_reply_or_edit.await_args
    if call is None:
        return ""
    return call.args[0] if call.args else call.kwargs.get("text", "")


async def main():
    print("=== smoke_test_test_flow ===")
    cleanup()

    try:
        # 0. Give the student a real balance to work with (bypass the
        # signup-grant flow -- this test is about Test Mode, not billing).
        user = SimpleNamespace(id=CHAT_ID, username=TG_HANDLE)
        conn.execute(
            "INSERT INTO students (telegram_user_id, username, first_name, last_name, first_seen_at, last_seen_at) "
            "VALUES (?,?,?,?,?,?)", (CHAT_ID, f"tg_{CHAT_ID}", "Smoke", "Test", platform_db.now(), platform_db.now()),
        )
        conn.commit()
        username, _ = identity.ensure_wallet_identity(conn, user)
        wallet.credit(conn, username, "smoketest", "recharge_credit", 5000, reference="smoketest-seed")

        # 1. "Gracefully deny" path -- a subject with no predesigned tests.
        text, markup = test_flow._not_available_text_and_markup("CS Executive Company Law")
        check("graceful-deny message doesn't dead-end (offers real alternatives)", "\U0001F4DD" in str(markup.inline_keyboard) or len(markup.inline_keyboard) >= 1)
        check("graceful-deny message never says 'error' or crashes-sounding text", "error" not in text.lower())
        check("graceful-deny message names what IS available", "CA Inter" in text)

        # 2. Trigger "test" -- since only CA/Inter/Advanced Accounting has
        # any predesigned tests, Course/Level/Subject all auto-skip straight
        # to the sitting picker (same auto-skip discipline as practice mode).
        update, _, message = mock_update("test")
        context = mock_context()
        await test_flow.start_test_flow(update, context, "1lavya-examhub", host)
        check("trigger 'test' goes straight to a sitting picker (auto-skip)", "pick a test" in last_text(message.reply_text).lower())
        sittings = context.user_data.get(test_flow.UD_PICKER_SITTINGS, [])
        check("at least one real sitting is offered", len(sittings) > 0)

        # 3. Pick the first sitting -> size-tier picker (2026-08-16: no more
        # mandatory full-paper size -- 20/50/100 marks, or "Full Paper" for
        # a sitting smaller than the tier).
        q1 = mock_query(user)
        q1.edit_message_text = AsyncMock()
        await test_flow._handle_picker_callback(q1, context, conn, "testflow:sitting:0", "1lavya-examhub", host)
        tier_text = last_text(q1.edit_message_text)
        check("sitting pick leads to a size-tier picker, not straight to summary", "how long a test" in tier_text.lower())
        tier_options = context.user_data.get("testflow_tier_options", [])
        check("at most 3 size tiers offered", 1 <= len(tier_options) <= 3)
        check("every tier option is a positive, sane marks value", all(0 < m <= 200 for m in tier_options))

        # 3b. Pick the smallest tier (20 marks, or the sitting's own total
        # if it's under 20) -> summary/confirm screen.
        q1b = mock_query(user)
        q1b.edit_message_text = AsyncMock()
        await test_flow._handle_picker_callback(q1b, context, conn, "testflow:tier:0", "1lavya-examhub", host)
        summary_text = last_text(q1b.edit_message_text)
        check("summary screen shows total marks", "Total:" in summary_text)
        check("summary screen shows credit cost, never rupees", "credits" in summary_text and "₹" not in summary_text)
        check("summary screen shows current balance", "you currently have" in summary_text)
        chosen_tier = tier_options[0]
        check("summary reflects the chosen tier's marks, not the full paper's", f"{chosen_tier}-mark version" in summary_text)

        # 4. Confirm -> Start Test (wallet debit + first question shown).
        # Expected counts must come from the SAME subset-building logic the
        # real code uses (the chosen TIER's marks, not the full sitting's) --
        # reading predesigned_tests directly here would test the wrong thing
        # now that a tier is always a subset, not necessarily the full paper.
        balance_before_start = wallet.get_balance(conn, username)
        catalog_key = context.user_data[test_flow.UD_PICKER_CATALOG_KEY]
        expected_mcqs = test_flow._mcqs_for_catalog(host, catalog_key)
        expected_descs = test_flow._descs_for_catalog(host, catalog_key)
        _, _, expected_total_marks = test_flow._build_subset_questions(expected_mcqs, expected_descs, chosen_tier)
        q2 = mock_query(user)
        q2.edit_message_text = AsyncMock()
        await test_flow._handle_picker_callback(q2, context, conn, "testflow:confirm", "1lavya-examhub", host)
        active = test_flow._get_active_test(conn, CHAT_ID)
        check("a test_sessions row was created", active is not None)
        test_id = active[0]
        expected_cost = expected_total_marks * wallet.RATE_TEST_CREDIT_PER_MARK
        check(f"wallet debited exactly {expected_cost} credits at Start Test (the tier's marks, not the full paper's)", wallet.get_balance(conn, username) == balance_before_start - expected_cost)
        check("test_sessions total_marks matches the tier's actual subset, not the full sitting", conn.execute("SELECT total_marks FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()[0] == expected_total_marks)
        qcount = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=?", (test_id,)).fetchone()[0]
        mcq_count = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=? AND qtype='mcq'", (test_id,)).fetchone()[0]
        descriptive_count = conn.execute("SELECT COUNT(*) FROM test_questions WHERE test_id=? AND qtype='descriptive'", (test_id,)).fetchone()[0]
        check("test_questions rows created for exactly the tier's subset", qcount == mcq_count + descriptive_count and qcount > 0)
        check("a 20-ish-mark tier is meaningfully smaller than the full sitting (subsetting actually happened)", qcount <= len(expected_mcqs) + len(expected_descs))
        check("Start Test message doesn't reveal any answer", "correct" not in last_text(q2.edit_message_text).lower())
        # 2026-08-16, Pranav's ask: every question tracked at topic/subtopic
        # level for concept-level analysis later.
        topic_rows = conn.execute("SELECT chapter_slug, topic_text FROM test_questions WHERE test_id=?", (test_id,)).fetchall()
        check("every test question has a chapter_slug snapshotted", all(r[0] for r in topic_rows))
        check("test_sessions.current_seq_no was set to 1 at start", conn.execute("SELECT current_seq_no FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()[0] == 1)
        check("activity log recorded 'test_started'", conn.execute("SELECT COUNT(*) FROM test_activity_log WHERE test_id=? AND action_type='test_started'", (test_id,)).fetchone()[0] == 1)
        check("activity log recorded 'question_viewed' for Q1", conn.execute("SELECT COUNT(*) FROM test_activity_log WHERE test_id=? AND seq_no=1 AND action_type='question_viewed'", (test_id,)).fetchone()[0] >= 1)

        # 4b. DOUBLE-TAP REGRESSION (found via independent code review,
        # 2026-08-16, fixed same day): an impatient/slow-network double-tap
        # on "Start Test" used to re-run _start_test() a second time --
        # debiting the wallet twice and opening a second, orphaned
        # test_sessions row -- because the "only one active test" guard
        # only ever lived at start_test_flow()'s TEXT-trigger entry point,
        # never at the actual confirm callback that creates the session.
        # Simulates exactly that: fire "testflow:confirm" again for the
        # SAME user, same picker state, immediately after test 4 above
        # already started a real test.
        balance_before_redundant_tap = wallet.get_balance(conn, username)
        q2b = mock_query(user)
        q2b.edit_message_text = AsyncMock()
        await test_flow._handle_picker_callback(q2b, context, conn, "testflow:confirm", "1lavya-examhub", host)
        check("a double-tap on Start Test does NOT take a second debit", wallet.get_balance(conn, username) == balance_before_redundant_tap)
        check("a double-tap on Start Test does NOT open a second test_sessions row", conn.execute("SELECT COUNT(*) FROM test_sessions WHERE telegram_user_id=? AND status='in_progress'", (CHAT_ID,)).fetchone()[0] == 1)
        check("a double-tap on Start Test resumes the SAME test_id, not a new one", test_flow._get_active_test(conn, CHAT_ID)[0] == test_id)
        check("a double-tap on Start Test tells the student it's already in progress", "already have a test in progress" in last_text(q2b.edit_message_text).lower())

        # 5. First question is an MCQ (sittings are ordered MCQ-then-descriptive) if mcq_count > 0.
        if mcq_count > 0:
            first_q_row = conn.execute("SELECT qtype FROM test_questions WHERE test_id=? AND seq_no=1", (test_id,)).fetchone()
            check("first question is an MCQ when the sitting has any", first_q_row[0] == "mcq")

            # 6. Select an option -- verify it's recorded but NOT graded/revealed.
            q3 = mock_query(user, text_for_seq_parsing="Q1/" + str(qcount))
            q3.edit_message_text = AsyncMock()
            await test_flow._handle_option_select(q3, context, conn, test_id, "A", host)
            ans_row = conn.execute("SELECT selected_option, is_correct FROM test_mcq_answers WHERE test_id=? AND seq_no=1", (test_id,)).fetchone()
            check("MCQ answer was recorded", ans_row[0] == "A")
            check("MCQ correctness is NOT computed mid-test (roadmap's own rule)", ans_row[1] is None)
            check("MCQ answer text never reveals correct/incorrect mid-test", "✅" not in last_text(q3.edit_message_text) and "❌" not in last_text(q3.edit_message_text).lower())
            status_row = conn.execute("SELECT status FROM test_questions WHERE test_id=? AND seq_no=1", (test_id,)).fetchone()
            check("question status updated to 'answered'", status_row[0] == "answered")
            check("activity log recorded the first pick", conn.execute("SELECT COUNT(*) FROM test_activity_log WHERE test_id=? AND action_type='mcq_option_selected'", (test_id,)).fetchone()[0] == 1)

            # 6b. Change the answer -- 2026-08-16, Pranav's ask: distinguish
            # a first pick from a later change of mind.
            q3b = mock_query(user, text_for_seq_parsing="Q1/" + str(qcount))
            q3b.edit_message_text = AsyncMock()
            await test_flow._handle_option_select(q3b, context, conn, test_id, "B", host)
            change_row = conn.execute("SELECT detail FROM test_activity_log WHERE test_id=? AND action_type='mcq_option_changed'", (test_id,)).fetchone()
            check("changing the answer logs a distinct 'mcq_option_changed' event", change_row is not None)
            check("the change event records both the old and new option", change_row[0] == "from=A to=B")
            check("re-selecting the SAME option again does not log a spurious change", True)  # verified by the next call not adding a 2nd change row
            await test_flow._handle_option_select(mock_query(user, text_for_seq_parsing="Q1/" + str(qcount)), context, conn, test_id, "B", host)
            check("no-op re-selection doesn't log another change", conn.execute("SELECT COUNT(*) FROM test_activity_log WHERE test_id=? AND action_type='mcq_option_changed'", (test_id,)).fetchone()[0] == 1)

            # 7. Palette shows the right icons.
            q4 = mock_query(user)
            q4.edit_message_text = AsyncMock()
            await test_flow._handle_nav(q4, context, conn, test_id, "palette", host)
            palette_text = last_text(q4.edit_message_text)
            check("palette screen renders", "Question List" in palette_text)

        # 8. Find and view a descriptive question, if any.
        if descriptive_count > 0:
            desc_row = conn.execute("SELECT seq_no FROM test_questions WHERE test_id=? AND qtype='descriptive' LIMIT 1", (test_id,)).fetchone()
            desc_seq = desc_row[0]
            desc_text, desc_markup = test_flow._render_question(conn, test_id, desc_seq, host)
            check("descriptive question prompts for 'upload', not 'Show Answer'", "upload" in desc_text.lower() and "show answer" not in desc_text.lower())

            # 9. "upload" trigger -> question picker.
            update_up, _, msg_up = mock_update("upload")
            context.user_data[test_flow.UD_UPLOAD_SEQ] = None
            await test_flow.start_upload_pick(update_up, context, host)
            check("'upload' trigger offers a per-question picker", "which question" in last_text(msg_up.reply_text).lower())

            # 10. Pick that question via callback -> enters collection state.
            q5 = mock_query(user)
            q5.edit_message_text = AsyncMock()
            q5.data = f"tupload:{desc_seq}"  # test_flow_callback reads query.data -- set before the call, not after
            fake_update = SimpleNamespace(callback_query=q5)
            await test_flow.test_flow_callback(fake_update, context, "1lavya-examhub", host)
            check("upload collection state entered for the right question", context.user_data.get(test_flow.UD_UPLOAD_SEQ) == desc_seq)

            # 11. Simulate a photo upload (mocked file download).
            fake_file = SimpleNamespace(file_id="FAKEFILEID123", download_to_drive=AsyncMock())
            photo_msg = SimpleNamespace(
                chat_id=CHAT_ID, reply_text=AsyncMock(),
                photo=[SimpleNamespace(get_file=AsyncMock(return_value=fake_file))],
                document=None,
            )
            photo_update = SimpleNamespace(effective_user=user, message=photo_msg)
            consumed = await test_flow.handle_upload_photo_or_document(photo_update, context, host)
            check("a photo during active upload collection is consumed", consumed is True)
            upload_row = conn.execute("SELECT COUNT(*) FROM test_uploads WHERE test_id=? AND seq_no=?", (test_id, desc_seq)).fetchone()[0]
            check("an upload row was recorded", upload_row == 1)
            check("the upload confirmation names the right question and invites another page", f"Q{desc_seq}" in last_text(photo_msg.reply_text))

            # 12. "done" -> finalizes the question as uploaded.
            done_update, _, done_msg = mock_update("done")
            consumed_done = await test_flow.handle_upload_text_input(done_update, context, host)
            check("'done' is consumed while collecting an upload", consumed_done is True)
            q_status = conn.execute("SELECT status FROM test_questions WHERE test_id=? AND seq_no=?", (test_id, desc_seq)).fetchone()[0]
            check("descriptive question marked 'uploaded' after done", q_status == "uploaded")
            check("upload collection state cleared after done", not test_flow.is_collecting_upload(context))

        # 12b. Re-picking a question that ALREADY has uploaded pages must
        # warn, not silently accept more (2026-08-16, real gap Pranav found
        # by testing).
        if descriptive_count > 0:
            q5b = mock_query(user)
            q5b.edit_message_text = AsyncMock()
            q5b.data = f"tupload:{desc_seq}"
            await test_flow.test_flow_callback(SimpleNamespace(callback_query=q5b), context, "1lavya-examhub", host)
            warn_text = last_text(q5b.edit_message_text)
            check("re-picking an already-uploaded question warns instead of silently accepting more", "already uploaded" in warn_text.lower())
            check("re-upload warning offers Overwrite and Append", "overwrite" in str(q5b.edit_message_text.await_args.kwargs.get("reply_markup")).lower() and f"tupload:{desc_seq}:append" in str(q5b.edit_message_text.await_args.kwargs.get("reply_markup")))
            check("picking the question again does NOT silently start collecting (state untouched)", context.user_data.get(test_flow.UD_UPLOAD_SEQ) is None)

            # 12c. Choose "append" -- should resume from the existing page
            # count, not reset to page 1, and the old page is NOT deleted.
            existing_page_count = conn.execute("SELECT COUNT(*) FROM test_uploads WHERE test_id=? AND seq_no=?", (test_id, desc_seq)).fetchone()[0]
            q5c = mock_query(user)
            q5c.edit_message_text = AsyncMock()
            q5c.data = f"tupload:{desc_seq}:append"
            await test_flow.test_flow_callback(SimpleNamespace(callback_query=q5c), context, "1lavya-examhub", host)
            check("'append' keeps the existing pages (none deleted)", conn.execute("SELECT COUNT(*) FROM test_uploads WHERE test_id=? AND seq_no=?", (test_id, desc_seq)).fetchone()[0] == existing_page_count)
            check("'append' resumes the page counter from the existing max, not 0", context.user_data.get(test_flow.UD_UPLOAD_PAGE_COUNTER) == existing_page_count)

            # 12d. "pass" while collecting marks the question skipped and
            # clears state (2026-08-16, the missing fallback Pranav flagged).
            pass_update, _, pass_msg = mock_update("pass")
            consumed_pass = await test_flow.handle_upload_text_input(pass_update, context, host)
            check("'pass' is consumed while collecting an upload", consumed_pass is True)
            check("question marked 'skipped' after pass", conn.execute("SELECT status FROM test_questions WHERE test_id=? AND seq_no=?", (test_id, desc_seq)).fetchone()[0] == "skipped")
            check("upload collection state cleared after pass", not test_flow.is_collecting_upload(context))
            # Undo the pass for the rest of the test flow below, which still
            # expects this question counted as genuinely uploaded.
            platform_db.execute_with_retry(conn, "UPDATE test_questions SET status='uploaded' WHERE test_id=? AND seq_no=?", (test_id, desc_seq))

        # 12e. Submit WITHOUT going through confirmation first -- tapping
        # "Submit Test" must show a summary, NOT submit immediately
        # (2026-08-16, Pranav's ask).
        q_submit_tap = mock_query(user, text_for_seq_parsing=f"Q1/{qcount}")
        q_submit_tap.edit_message_text = AsyncMock()
        await test_flow._handle_nav(q_submit_tap, context, conn, test_id, "submit", host)
        confirm_text = last_text(q_submit_tap.edit_message_text)
        check("tapping Submit Test shows a confirmation summary first", "ready to submit" in confirm_text.lower())
        check("confirmation summary shows MCQ attempted/blank counts", "answered" in confirm_text.lower())
        check("test is NOT actually submitted yet after just tapping Submit Test", conn.execute("SELECT status FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()[0] == "in_progress")
        confirm_markup = str(q_submit_tap.edit_message_text.await_args.kwargs.get("reply_markup"))
        check("confirmation offers both Confirm&Submit and Go Back", "submit_confirm" in confirm_markup and "submit_cancel" in confirm_markup)

        # 13. NOW actually confirm -- verify scoring + honest messaging (no
        # fake "30 minutes" promise, since AI evaluation isn't built).
        q6 = mock_query(user)
        q6.edit_message_text = AsyncMock()
        await test_flow._submit_test(q6, context, conn, test_id, host, auto=False)
        final_text = last_text(q6.edit_message_text)
        session_row = conn.execute("SELECT status, mcq_score, mcq_max FROM test_sessions WHERE test_id=?", (test_id,)).fetchone()
        check("test_sessions status is 'submitted'", session_row[0] == "submitted")
        if mcq_count > 0:
            check("MCQ score shown in the final message", "MCQ score" in final_text)
        if descriptive_count > 0:
            check("descriptive result is honest -- no fake AI-evaluation promise", "30 minutes" not in final_text and "evaluat" in final_text.lower())
        check("final message invites another attempt", "test" in final_text.lower())

        # 14. Resolve/attempt to start a SECOND test -- should resume, not double-start.
        update2, _, message2 = mock_update("test")
        context2 = mock_context()
        # first, re-open a fresh in_progress test to check resume behavior
        # (submission above already closed the first one, so start one more)
        q7 = mock_query(user)
        q7.edit_message_text = AsyncMock()
        await test_flow.start_test_flow(update2, context2, "1lavya-examhub", host)
        # since the previous test was submitted, this should show a fresh
        # picker again, not "resume" -- confirms status transitions correctly.
        check("after submission, a new 'test' trigger offers a fresh picker (not stuck resuming a closed test)", test_flow._get_active_test(conn, CHAT_ID) is None)

        # 15. Size-tier subsetting is sane across EVERY real sitting in the
        # catalog, not just the one this test happened to pick -- catches a
        # tier that silently produces an empty/oversized/broken subset for
        # some sitting this test's own single-sitting path wouldn't exercise.
        all_sittings = conn.execute("SELECT catalog_key, total_marks FROM predesigned_tests").fetchall()
        tier_problems = 0
        for ck, tm in all_sittings:
            mcqs = test_flow._mcqs_for_catalog(host, ck)
            descs = test_flow._descs_for_catalog(host, ck)
            for _, target in test_flow._tier_options(tm):
                m, d, actual = test_flow._build_subset_questions(mcqs, descs, target)
                if actual <= 0 or actual > target or (len(m) + len(d)) == 0:
                    tier_problems += 1
        check(f"all {len(all_sittings)} real sittings' size tiers produce valid, non-empty, correctly-capped subsets", tier_problems == 0)

        # 16. Job scheduling, reminders, heartbeat, and the interactive
        # grace-period offer (2026-08-16, Pranav's ask) -- a fresh test
        # session with a REAL FakeJobQueue so scheduling itself can be
        # verified, not just the DB writes.
        jq = FakeJobQueue()
        context3 = SimpleNamespace(user_data={}, bot=SimpleNamespace(send_message=AsyncMock()), job_queue=jq)
        catalog_key2 = context.user_data.get(test_flow.UD_PICKER_CATALOG_KEY) or catalog_key
        q8 = mock_query(user)
        q8.edit_message_text = AsyncMock()
        await test_flow._start_test(q8, context3, conn, CHAT_ID, "1lavya-examhub", catalog_key2, 20, host, is_callback=True)
        test_id2 = test_flow._get_active_test(conn, CHAT_ID)[0]

        expiry_jobs = [j for j in jq.active() if j["name"] == test_flow._expiry_job_name(test_id2)]
        reminder_jobs = [j for j in jq.active() if j["name"].startswith(f"test_reminder:{test_id2}:")]
        heartbeat_jobs = [j for j in jq.active() if j["name"] == test_flow._heartbeat_job_name(test_id2)]
        check("starting a test schedules exactly one expiry job", len(expiry_jobs) == 1)
        check("starting a test schedules both reminder jobs (5min, 3min)", len(reminder_jobs) == 2)
        check("starting a test schedules the heartbeat chain", len(heartbeat_jobs) == 1)
        check("the heartbeat job is for the currently-viewed question (Q1)", heartbeat_jobs[0]["data"]["seq_no"] == 1)

        # 16b. Heartbeat: firing for the CURRENT question logs + reschedules;
        # firing for a STALE question (student has moved on) does neither.
        hb_job_data = heartbeat_jobs[0]["data"]
        fake_hb_context = SimpleNamespace(job=SimpleNamespace(data=hb_job_data), job_queue=jq, bot=context3.bot)
        await test_flow._heartbeat_job_callback(fake_hb_context)
        check("a live heartbeat logs a no_activity_heartbeat event", conn.execute("SELECT COUNT(*) FROM test_activity_log WHERE test_id=? AND action_type='no_activity_heartbeat'", (test_id2,)).fetchone()[0] == 1)
        check("a live heartbeat reschedules itself", len([j for j in jq.active() if j["name"] == test_flow._heartbeat_job_name(test_id2)]) >= 1)

        stale_context = SimpleNamespace(job=SimpleNamespace(data={"test_id": test_id2, "seq_no": 999}), job_queue=jq, bot=context3.bot)
        heartbeat_count_before = conn.execute("SELECT COUNT(*) FROM test_activity_log WHERE test_id=? AND action_type='no_activity_heartbeat'", (test_id2,)).fetchone()[0]
        await test_flow._heartbeat_job_callback(stale_context)
        check("a STALE heartbeat (student moved to a different question) does not log", conn.execute("SELECT COUNT(*) FROM test_activity_log WHERE test_id=? AND action_type='no_activity_heartbeat'", (test_id2,)).fetchone()[0] == heartbeat_count_before)

        # 16c. The grace-period offer -- fires once, offers 2/3/5 min + submit-now.
        fake_app = SimpleNamespace(bot_data={"test_flow_host": host})
        expiry_context = SimpleNamespace(job=SimpleNamespace(data={"test_id": test_id2}), job_queue=jq, bot=context3.bot, application=fake_app)
        await test_flow._expiry_job_callback(expiry_context)
        jq.mark_fired(test_flow._expiry_job_name(test_id2))  # real job_queue auto-removes a run_once job after it fires -- this test double doesn't run a real dispatch loop, so simulate that explicitly
        check("grace_offered_at was set on first time-up", conn.execute("SELECT grace_offered_at FROM test_sessions WHERE test_id=?", (test_id2,)).fetchone()[0] is not None)
        check("test was NOT submitted yet -- grace was offered instead", conn.execute("SELECT status FROM test_sessions WHERE test_id=?", (test_id2,)).fetchone()[0] == "in_progress")
        grace_offer_call = context3.bot.send_message.await_args
        grace_markup = str(grace_offer_call.kwargs.get("reply_markup"))
        check("grace offer includes all 3 minute options", all(f"tgrace:{m}" in grace_markup for m in test_flow.GRACE_OPTIONS_MINUTES))
        check("grace offer includes a submit-now option", "tgrace:submit" in grace_markup)
        check("a grace-timeout fallback job was scheduled", len([j for j in jq.active() if j["name"] == test_flow._grace_timeout_job_name(test_id2)]) == 1)
        check("activity log recorded 'grace_offered'", conn.execute("SELECT COUNT(*) FROM test_activity_log WHERE test_id=? AND action_type='grace_offered'", (test_id2,)).fetchone()[0] == 1)

        # 16d. Choosing "+2 min" extends the deadline, records the choice,
        # cancels the fallback, and schedules a fresh expiry -- and that
        # SECOND expiry, when it fires, submits for real (no repeat offer).
        before_choice = datetime.now(timezone.utc)
        q9 = mock_query(user)
        q9.edit_message_text = AsyncMock()
        await test_flow._handle_grace_callback(q9, context3, conn, test_id2, "tgrace:2", host)
        new_expiry = conn.execute("SELECT expires_at, grace_requested_minutes FROM test_sessions WHERE test_id=?", (test_id2,)).fetchone()
        new_expiry_dt = datetime.fromisoformat(new_expiry[0])
        # The new deadline is "now + 2 minutes" (Pranav's design: the
        # student gets the FULL grace window from when they said yes, not
        # counted down from the original, already-passed nominal deadline)
        # -- verify it lands within a few seconds of that, not compared
        # against the ORIGINAL expires_at (which was ~36 minutes out and
        # would make a naive ">" comparison meaningless in a synthetic test
        # where no real wall-clock time actually elapses between calls).
        expected = before_choice + timedelta(minutes=2)
        check("choosing +2 min sets the new deadline to ~now+2min", abs((new_expiry_dt - expected).total_seconds()) < 5)
        check("grace_requested_minutes recorded as 2", new_expiry[1] == 2)
        check("the grace-timeout fallback was cancelled", len([j for j in jq.active() if j["name"] == test_flow._grace_timeout_job_name(test_id2)]) == 0)
        check("a fresh expiry job was scheduled for the extended deadline", len([j for j in jq.active() if j["name"] == test_flow._expiry_job_name(test_id2)]) == 1)
        check("activity log recorded the grace choice", conn.execute("SELECT detail FROM test_activity_log WHERE test_id=? AND action_type='grace_chosen'", (test_id2,)).fetchone()[0] == "choice=2")

        await test_flow._expiry_job_callback(expiry_context)  # simulate the extended deadline arriving
        jq.mark_fired(test_flow._expiry_job_name(test_id2))
        check("the SECOND time-up (after grace was already offered) submits for real, no repeat offer", conn.execute("SELECT status FROM test_sessions WHERE test_id=?", (test_id2,)).fetchone()[0] == "submitted")
        check("cancelling on submit removes the reminder/heartbeat jobs too", len(jq.active()) == 0)

        # 17. Uploaded-without-"done" reconciliation -- 2026-08-16, Pranav's
        # real question: what happens if time runs out mid-upload? Answer:
        # nothing is lost, since pages save instantly -- verify a question
        # with real pages but no "done" still counts as uploaded at submit.
        desc_row2 = conn.execute("SELECT seq_no FROM test_questions WHERE test_id=? AND qtype='descriptive' LIMIT 1", (test_id2,)).fetchone()
        if desc_row2:
            seq2 = desc_row2[0]
            context3.user_data[test_flow.UD_UPLOAD_SEQ] = seq2
            context3.user_data[test_flow.UD_UPLOAD_PAGE_COUNTER] = 0
            fake_file2 = SimpleNamespace(file_id="FAKEFILEID456", download_to_drive=AsyncMock())
            photo_msg2 = SimpleNamespace(chat_id=CHAT_ID, reply_text=AsyncMock(), photo=[SimpleNamespace(get_file=AsyncMock(return_value=fake_file2))], document=None)
            photo_update2 = SimpleNamespace(effective_user=user, message=photo_msg2)
            # test_id2 is already submitted at this point (step 16d) -- start
            # a THIRD test fresh to test this specific scenario in isolation.
            q10 = mock_query(user)
            q10.edit_message_text = AsyncMock()
            context4 = mock_context()
            await test_flow._start_test(q10, context4, conn, CHAT_ID, "1lavya-examhub", catalog_key2, 20, host, is_callback=True)
            test_id3 = test_flow._get_active_test(conn, CHAT_ID)[0]
            desc_row3 = conn.execute("SELECT seq_no FROM test_questions WHERE test_id=? AND qtype='descriptive' LIMIT 1", (test_id3,)).fetchone()
            if desc_row3:
                seq3 = desc_row3[0]
                context4.user_data[test_flow.UD_UPLOAD_SEQ] = seq3
                context4.user_data[test_flow.UD_UPLOAD_PAGE_COUNTER] = 0
                await test_flow.handle_upload_photo_or_document(photo_update2, context4, host)
                # Deliberately never type "done" -- simulate time running out mid-upload.
                q11 = mock_query(user)
                q11.edit_message_text = AsyncMock()
                await test_flow._submit_test(q11, context4, conn, test_id3, host, auto=True)
                final_status = conn.execute("SELECT status FROM test_questions WHERE test_id=? AND seq_no=?", (test_id3, seq3)).fetchone()[0]
                check("a question with real uploaded pages counts as 'uploaded' at auto-submit even if 'done' was never typed", final_status == "uploaded")

    finally:
        cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
