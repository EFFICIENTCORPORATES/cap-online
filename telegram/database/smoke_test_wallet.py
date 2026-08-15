"""
telegram/database/smoke_test_wallet.py -- smoke test for wallet.py (2026-08-15)
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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db as platform_db  # noqa: E402
import wallet  # noqa: E402

USERNAME = "smoketest_wallet_x"
TENANT = "smoketest"

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


def cleanup():
    conn.execute("DELETE FROM wallet_ledger WHERE username=?", (USERNAME,))
    conn.execute("DELETE FROM student_profiles WHERE username=?", (USERNAME,))
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

    finally:
        cleanup()

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
