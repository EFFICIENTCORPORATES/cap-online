"""
telegram/database/smoke_test_wallet.py -- smoke test for wallet.py + identity.py
(2026-08-15, extended 2026-08-16 for auto-identity + signup grant/expiry)
--------------------------------------------------------------------------------
Same discipline as smoke_test_leaderboards.py / smoke_test_profile_flow.py:
synthetic usernames, the real shared platform.db, no mocking of the DB layer
itself, full cleanup in `finally` even on failure. Run directly:
`python smoke_test_wallet.py`.

Deliberately does NOT touch razorpay_client.py or make any network call --
this only proves the ledger arithmetic/idempotency logic, which is fully
testable without live Razorpay credentials (and must never spend real money
just by being run). A separate, manual, opt-in check is needed before
trusting the actual Razorpay integration end to end -- see wallet_flow.py's
own module docstring once that's built.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db as platform_db  # noqa: E402
import wallet  # noqa: E402
import identity  # noqa: E402

USERNAME = "smoketest_wallet_x"
USERNAME_GRANTS = "smoketest_wallet_grants"  # separate from USERNAME on purpose -- tests 1-10 deliberately drive USERNAME's balance deeply negative (test 9's allow_negative admin adjustment), which would silently invalidate the grant/expiry tests' own assumptions if they shared a username
TENANT = "smoketest"

# Synthetic chat_ids for identity.py's tests -- well out of any real
# Telegram ID range this platform would ever see.
CHAT_WITH_TG_USERNAME = 900_200_001
CHAT_NO_TG_USERNAME = 900_200_002
CHAT_COLLISION = 900_200_003
TG_USERNAME_CANDIDATE = "smoketest_tg_handle"

conn = platform_db.get_connection()
platform_db.init_schema(conn)

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


def seed_profile(username):
    now = platform_db.now()
    conn.execute("DELETE FROM student_profiles WHERE username=?", (username,))
    conn.execute(
        "INSERT INTO student_profiles (username, display_name, course, level, exam_attempt, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (username, f"Display {username}", "CA", "Inter", "Nov 2026", now, now),
    )
    conn.commit()


def seed_bare_student(chat_id):
    """A students row with NO lavya_username -- the state identity.py's
    functions are meant to operate on. Mirrors db.upsert_student()'s own
    shape minimally (only the columns identity.py actually reads/writes)."""
    now = platform_db.now()
    conn.execute("DELETE FROM students WHERE telegram_user_id=?", (chat_id,))
    conn.execute(
        "INSERT INTO students (telegram_user_id, username, first_name, last_name, first_seen_at, last_seen_at) "
        "VALUES (?,?,?,?,?,?)",
        (chat_id, f"tg_{chat_id}", "Smoke", "Test", now, now),
    )
    conn.commit()


def cleanup():
    # Deletion order matters: students.lavya_username ALSO carries a FK to
    # student_profiles(username) (db.py's _COLUMN_MIGRATIONS), on top of
    # wallet_ledger's/wallet_grants' own FKs -- a real bug caught by
    # actually running this cleanup, not assumed: `students` must be
    # deleted (or unlinked) BEFORE `student_profiles`, not after.
    for chat_id in (CHAT_WITH_TG_USERNAME, CHAT_NO_TG_USERNAME, CHAT_COLLISION):
        row = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (chat_id,)).fetchone()
        username = row[0] if row else None
        conn.execute("DELETE FROM students WHERE telegram_user_id=?", (chat_id,))
        if username:
            conn.execute("DELETE FROM wallet_ledger WHERE username=?", (username,))
            conn.execute("DELETE FROM wallet_grants WHERE username=?", (username,))
            # student_academic_profiles/access_requests also FK to
            # student_profiles(username) since 2026-08-16 -- defensively
            # cleared here too, same reasoning smoke_test_leaderboards.py's
            # own cleanup() comment gives (any init_schema() re-run, even
            # from a module this test doesn't call directly, would migrate
            # a course/level-bearing student_profiles row into the new
            # table and FK-block the delete two lines down otherwise).
            conn.execute("DELETE FROM access_requests WHERE username=?", (username,))
            conn.execute("DELETE FROM student_academic_profiles WHERE username=?", (username,))
            conn.execute("DELETE FROM student_profiles WHERE username=?", (username,))
    conn.execute("DELETE FROM student_profiles WHERE username=?", (TG_USERNAME_CANDIDATE,))
    for uname in (USERNAME, USERNAME_GRANTS):
        conn.execute("DELETE FROM wallet_ledger WHERE username=?", (uname,))
        conn.execute("DELETE FROM wallet_grants WHERE username=?", (uname,))
        conn.execute("DELETE FROM access_requests WHERE username=?", (uname,))
        conn.execute("DELETE FROM student_academic_profiles WHERE username=?", (uname,))
        conn.execute("DELETE FROM student_profiles WHERE username=?", (uname,))
    conn.commit()


def main():
    print("=== smoke_test_wallet ===")
    cleanup()  # in case a prior failed run left residue
    seed_profile(USERNAME)

    try:
        # 1. Fresh username has a zero balance, not an error.
        check("fresh username balance is 0", wallet.get_balance(conn, USERNAME) == 0)

        # 2. credit() increases balance by exactly the amount given.
        new_balance, already = wallet.credit(conn, USERNAME, TENANT, "recharge_credit", 2000)
        check("credit(2000) -> balance 2000", new_balance == 2000)
        check("credit() first call is not already_applied", already is False)

        # 3. debit() with sufficient balance succeeds and decreases correctly.
        ok, bal, already = wallet.debit(conn, USERNAME, TENANT, "test_debit", 400, reference="smoketest-test-1")
        check("debit(400) succeeds", ok is True)
        check("debit(400) -> balance 1600", bal == 1600)

        # 4. debit() with insufficient balance fails cleanly, balance unchanged.
        ok, bal, already = wallet.debit(conn, USERNAME, TENANT, "test_debit", 999_999, reference="smoketest-toolarge")
        check("debit(too large) fails", ok is False)
        check("debit(too large) leaves balance unchanged at 1600", bal == 1600)
        check("balance really is still 1600 in the ledger", wallet.get_balance(conn, USERNAME) == 1600)

        # 5. Idempotent debit: the same idempotency_key applied twice only charges once.
        key = "test_debit:smoketest-test-2"
        ok1, bal1, already1 = wallet.debit(conn, USERNAME, TENANT, "test_debit", 300, reference="smoketest-test-2", idempotency_key=key)
        ok2, bal2, already2 = wallet.debit(conn, USERNAME, TENANT, "test_debit", 300, reference="smoketest-test-2", idempotency_key=key)
        check("idempotent debit: first call succeeds, not already_applied", ok1 is True and already1 is False)
        check("idempotent debit: second call reports already_applied", already2 is True)
        check("idempotent debit: balance only dropped once (1300, not 1000)", bal1 == 1300 and bal2 == 1300)

        # 6. Idempotent credit: same story for a recharge confirmation polled more than once.
        rkey = "recharge:plink_smoketest_1"
        bal1, already1 = wallet.credit(conn, USERNAME, TENANT, "recharge_credit", 500, reference="plink_smoketest_1", idempotency_key=rkey)
        bal2, already2 = wallet.credit(conn, USERNAME, TENANT, "recharge_credit", 500, reference="plink_smoketest_1", idempotency_key=rkey)
        check("idempotent credit: first call is fresh", already1 is False)
        check("idempotent credit: second call is a no-op", already2 is True)
        check("idempotent credit: balance only rose once (1800, not 2300)", bal1 == 1800 and bal2 == 1800)

        # 7. debit_for_test() applies the locked rate (10 credits/mark) and is
        #    keyed to test_id, so a retried "Start Test" tap can't double-charge.
        current = wallet.get_balance(conn, USERNAME)
        ok, bal, already = wallet.debit_for_test(conn, USERNAME, TENANT, "smoketest-test-abc", total_marks=40)
        check("debit_for_test(40 marks) charges 400 credits (10/mark)", ok is True and bal == current - 400)
        ok2, bal2, already2 = wallet.debit_for_test(conn, USERNAME, TENANT, "smoketest-test-abc", total_marks=40)
        check("debit_for_test() retried for the same test_id is a no-op", already2 is True and bal2 == bal)

        # 8. credit_for_recharge() applies the given pack size and is keyed to
        #    the payment_link_id, so a polling loop can't double-credit.
        current = wallet.get_balance(conn, USERNAME)
        bal, already = wallet.credit_for_recharge(conn, USERNAME, TENANT, "plink_smoketest_2", credits_granted=2000)
        check("credit_for_recharge(2000) credits correctly", bal == current + 2000)
        bal2, already2 = wallet.credit_for_recharge(conn, USERNAME, TENANT, "plink_smoketest_2", credits_granted=2000)
        check("credit_for_recharge() retried for the same link_id is a no-op", already2 is True and bal2 == bal)

        # 9. allow_negative is opt-in only -- a plain debit never goes negative,
        #    but an explicit admin adjustment can (schema comment's own intent).
        ok, bal, _ = wallet.debit(conn, USERNAME, TENANT, "manual_adjustment", 999_999,
                                   reference="smoketest-admin-correction", allow_negative=True)
        check("allow_negative=True permits a balance-driving-negative debit", ok is True and bal < 0)

        # 10. Currency conversion sanity (1 credit = ₹0.01).
        check("credits_to_inr(2000) == 20.0", wallet.credits_to_inr(2000) == 20.0)
        check("inr_to_credits(20) == 2000", wallet.inr_to_credits(20) == 2000)

        # 11. identity.ensure_wallet_identity: a student WITH a valid,
        #     unclaimed Telegram @username gets that as their permanent
        #     1LAVYA username, silently, no prompt.
        seed_bare_student(CHAT_WITH_TG_USERNAME)
        tg_user = SimpleNamespace(id=CHAT_WITH_TG_USERNAME, username=TG_USERNAME_CANDIDATE)
        uname, was_created = identity.ensure_wallet_identity(conn, tg_user)
        check("auto-identity uses the real Telegram @username", uname == TG_USERNAME_CANDIDATE)
        check("auto-identity reports was_auto_created=True on first call", was_created is True)
        row = conn.execute("SELECT lavya_username FROM students WHERE telegram_user_id=?", (CHAT_WITH_TG_USERNAME,)).fetchone()
        check("students.lavya_username actually got linked", row[0] == TG_USERNAME_CANDIDATE)

        # 12. Idempotent: calling again for the same chat_id returns the
        #     same username, was_auto_created=False, no duplicate row.
        uname2, was_created2 = identity.ensure_wallet_identity(conn, tg_user)
        check("auto-identity is idempotent (same username)", uname2 == TG_USERNAME_CANDIDATE)
        check("auto-identity second call reports was_auto_created=False", was_created2 is False)

        # 13. A student with NO Telegram @username at all falls back to the
        #     deterministic tg{id} placeholder.
        seed_bare_student(CHAT_NO_TG_USERNAME)
        no_handle_user = SimpleNamespace(id=CHAT_NO_TG_USERNAME, username=None)
        uname3, _ = identity.ensure_wallet_identity(conn, no_handle_user)
        check("no Telegram @username -> falls back to tg{id} placeholder", uname3 == f"tg{CHAT_NO_TG_USERNAME}")

        # 14. A student whose Telegram @username collides with an ALREADY
        #     CLAIMED different profile also falls back to the placeholder
        #     -- never silently takes over someone else's identity.
        seed_bare_student(CHAT_COLLISION)
        colliding_user = SimpleNamespace(id=CHAT_COLLISION, username=TG_USERNAME_CANDIDATE)  # already claimed by CHAT_WITH_TG_USERNAME above
        uname4, _ = identity.ensure_wallet_identity(conn, colliding_user)
        check("colliding Telegram @username -> falls back to placeholder, not a takeover", uname4 == f"tg{CHAT_COLLISION}")
        check("the original claimant's link is untouched by the collision", uname == TG_USERNAME_CANDIDATE)

        # 15. grant_signup_bonus: grants the locked amount exactly once.
        # Uses a DEDICATED username (USERNAME_GRANTS), isolated from
        # USERNAME's own tests above -- test 9 deliberately drives USERNAME
        # deeply negative (allow_negative admin adjustment), which would
        # silently break the expiry-clawback assumptions below if reused.
        seed_profile(USERNAME_GRANTS)
        bal, already = wallet.grant_signup_bonus(conn, USERNAME_GRANTS, TENANT)
        check(f"grant_signup_bonus credits {wallet.SIGNUP_GRANT_CREDITS} credits", bal == wallet.SIGNUP_GRANT_CREDITS)
        check("grant_signup_bonus first call is fresh", already is False)
        grant_row = conn.execute(
            "SELECT amount_credits, expires_at FROM wallet_grants WHERE username=? AND grant_type='signup_bonus'",
            (USERNAME_GRANTS,),
        ).fetchone()
        check("wallet_grants row created with the right amount", grant_row[0] == wallet.SIGNUP_GRANT_CREDITS)
        expires_dt = datetime.fromisoformat(grant_row[1])
        days_out = (expires_dt - datetime.now(timezone.utc)).days
        check("expiry is ~365 days out", 363 <= days_out <= 365)

        # 16. Idempotent: a second grant attempt for the same username is a no-op.
        bal2, already2 = wallet.grant_signup_bonus(conn, USERNAME_GRANTS, TENANT)
        check("grant_signup_bonus second call reports already_granted", already2 is True)
        check("grant_signup_bonus second call does not change the balance", bal2 == bal)
        count = conn.execute(
            "SELECT COUNT(*) FROM wallet_grants WHERE username=? AND grant_type='signup_bonus'", (USERNAME_GRANTS,)
        ).fetchone()[0]
        check("exactly one wallet_grants row exists, not two", count == 1)

        # 17. sweep_expired_grants: a grant whose expiry is in the FUTURE is untouched.
        swept = wallet.sweep_expired_grants(conn, TENANT)
        check("sweep does nothing to a not-yet-expired grant", swept == 0)
        check("balance unaffected by a no-op sweep", wallet.get_balance(conn, USERNAME_GRANTS) == wallet.SIGNUP_GRANT_CREDITS)

        # 18. Backdate the grant's expiry into the past, spend PART of it,
        #     then sweep -- should claw back only what's left (capped at
        #     the original grant size and the current balance), never more.
        wallet.debit(conn, USERNAME_GRANTS, TENANT, "mcq_debit", 300, reference="smoketest-spend-before-expiry")
        balance_before_sweep = wallet.get_balance(conn, USERNAME_GRANTS)
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
        conn.execute("UPDATE wallet_grants SET expires_at=? WHERE username=? AND grant_type='signup_bonus'", (past, USERNAME_GRANTS))
        conn.commit()
        swept2 = wallet.sweep_expired_grants(conn, TENANT)
        check("sweep processes exactly the one due grant", swept2 == 1)
        check("balance after sweep is 0 (the whole remaining grant was clawed back)", wallet.get_balance(conn, USERNAME_GRANTS) == 0)
        swept_row = conn.execute(
            "SELECT expired_amount, swept_at FROM wallet_grants WHERE username=? AND grant_type='signup_bonus'", (USERNAME_GRANTS,)
        ).fetchone()
        check("expired_amount recorded correctly (balance_before_sweep, not the full original grant)", swept_row[0] == balance_before_sweep)
        check("swept_at is now set", swept_row[1] is not None)

        # 19. Re-running the sweep is a safe no-op (swept_at already set).
        swept3 = wallet.sweep_expired_grants(conn, TENANT)
        check("re-running the sweep touches nothing already swept", swept3 == 0)

        # 20. Separately, confirm the clawback cap really does protect a
        #     student who has since recharged -- the expiry must NEVER
        #     touch more than the grant's own original size, even if their
        #     balance (including real paid recharge money) is much larger.
        seed_profile(USERNAME_GRANTS + "_funded")
        wallet.grant_signup_bonus(conn, USERNAME_GRANTS + "_funded", TENANT)
        wallet.credit(conn, USERNAME_GRANTS + "_funded", TENANT, "recharge_credit", 5000, reference="smoketest-real-recharge")
        balance_with_recharge = wallet.get_balance(conn, USERNAME_GRANTS + "_funded")
        conn.execute(
            "UPDATE wallet_grants SET expires_at=? WHERE username=? AND grant_type='signup_bonus'",
            (past, USERNAME_GRANTS + "_funded"),
        )
        conn.commit()
        wallet.sweep_expired_grants(conn, TENANT)
        after = wallet.get_balance(conn, USERNAME_GRANTS + "_funded")
        check(
            "expiry never claws back more than the grant's own size, even with a real recharge sitting in the wallet",
            after == balance_with_recharge - wallet.SIGNUP_GRANT_CREDITS,
        )
        conn.execute("DELETE FROM wallet_ledger WHERE username=?", (USERNAME_GRANTS + "_funded",))
        conn.execute("DELETE FROM wallet_grants WHERE username=?", (USERNAME_GRANTS + "_funded",))
        conn.execute("DELETE FROM student_profiles WHERE username=?", (USERNAME_GRANTS + "_funded",))
        conn.commit()

        # 20. The welcome-message builder uses question/mark language only,
        #     never rupees, and the numbers match the locked rates exactly.
        msg = wallet.build_signup_grant_message()
        check("grant message mentions 1000 MCQs", "1000 MCQs" in msg)
        check("grant message mentions 100 Descriptive Questions", "100 Descriptive Questions" in msg)
        check("grant message mentions 100 marks worth of Tests", "100 marks worth of Tests" in msg)
        check("grant message mentions the 365-day validity", "365 days" in msg)
        check("grant message never mentions rupees/money", "₹" not in msg and "rupee" not in msg.lower() and "inr" not in msg.lower())

    finally:
        cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
