"""
telegram/database/wallet.py -- the shared credit-wallet ledger (2026-08-15)
--------------------------------------------------------------------------------
Built for Test Mode billing (see
telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md §9 for the full decision
trail). Every bot/flow that needs to check or move a student's balance
imports this instead of touching wallet_ledger directly -- keeps the
"balance is always SUM(amount), never a stored mutable field" rule
(schema.sql's own comment on wallet_ledger) enforced in exactly one place,
same reasoning db.py centralizes every write for the same table.

IDENTITY: every function here takes a `username` (student_profiles.username),
never a telegram_user_id -- wallet balance follows a student across every
linked phone (locked 2026-08-15, third round of the billing discussion).
Calling code is responsible for resolving telegram_user_id -> username first,
and for routing a student with no username yet into profile_flow.py's
username-creation step BEFORE ever reaching a function here -- this module
intentionally has no Telegram-specific knowledge, so it stays testable
without a running bot.

CURRENCY: 1 credit = ₹0.01 -- a RECOMMENDATION inferred from Pranav's three
confirmed rates (it's the only exchange rate that makes all three come out
to clean whole-credit numbers), not yet re-confirmed by him as a literal
number -- see roadmap §9.2. Every rate below reduces cleanly under it:
  - MCQ practice:          1 credit  per MCQ shown        (₹1 / 100 MCQs)
  - Descriptive practice:  10 credits per question shown   (₹1 / 10 questions, flat, regardless of marks)
  - Test Mode facility:    10 credits per mark of the test  (₹1 / 10 marks -- question delivery + upload/PDF assembly ONLY, evaluation billed separately, not yet priced)

NOT WIRED INTO ANY LIVE PRACTICE FLOW YET. This module provides the
primitives (balance, debit, credit) and the recharge-specific helper this
session's Razorpay work needs. Actually debiting real students for ordinary
MCQ/Descriptive practice (exam_hub_bot.py's send_question/send_mcq) is a
separate, much higher-blast-radius change -- it would start blocking
existing free usage for every current student the moment it's wired in --
and needs its own explicit go-ahead before touching those live code paths,
per this platform's own established "build -> confirm -> deploy" discipline.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402

logger = logging.getLogger(__name__)

CREDIT_TO_INR = 0.01  # 1 credit = ₹0.01 -- see module docstring; recommendation, not yet re-confirmed literally

RATE_MCQ_CREDIT = 1              # credits per MCQ shown
RATE_DESCRIPTIVE_CREDIT = 10     # credits per descriptive question shown
RATE_TEST_CREDIT_PER_MARK = 10   # credits per mark of an assembled Test Mode session

RECHARGE_MINIMUM_INR = 20  # locked 2026-08-15, third round


def credits_to_inr(credits: int) -> float:
    return round(credits * CREDIT_TO_INR, 2)


def inr_to_credits(rupees: float) -> int:
    return round(rupees / CREDIT_TO_INR)


def get_balance(conn, username: str) -> int:
    """The ONLY correct way to read a balance -- SUM(amount) over
    wallet_ledger, never a stored column (schema.sql's own rule, repeated
    here because it matters). Returns 0 for a username with no ledger rows
    yet, not an error -- a brand-new profile with nothing granted or spent
    is a completely normal state."""
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM wallet_ledger WHERE username = ?",
        (username,),
    ).fetchone()
    return row[0]


def _insert_ledger_row(conn, username, tenant_id, event_type, amount, reference, idempotency_key):
    """Internal. `amount` here is already signed (negative for a debit,
    positive for a credit) -- public functions below own translating a
    plain positive quantity into the right sign so callers never have to
    remember the convention."""
    if idempotency_key:
        existing = conn.execute(
            "SELECT ledger_id FROM wallet_ledger WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if existing:
            logger.info(f"wallet: idempotent no-op for {idempotency_key!r} (already applied as ledger_id={existing[0]})")
            return existing[0], False
    db.execute_with_retry(
        conn,
        "INSERT INTO wallet_ledger (username, tenant_id, event_type, amount, reference, idempotency_key, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, tenant_id, event_type, amount, reference, idempotency_key, db.now()),
    )
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return new_id, True


def debit(conn, username: str, tenant_id: str, event_type: str, amount_credits: int,
          reference: str = None, idempotency_key: str = None, allow_negative: bool = False):
    """amount_credits is a POSITIVE quantity (the amount to remove) --
    negated internally so callers never touch the ledger's sign convention
    directly. Refuses to take a balance negative unless allow_negative=True
    (reserved for a deliberate admin manual_adjustment, never a student-
    facing debit). If idempotency_key is given and already applied, this is
    a safe no-op that reports the PRE-EXISTING outcome, not a fresh charge
    -- exactly what protects a retried "Start Test" tap from double-billing.

    Returns (success: bool, new_balance: int, already_applied: bool)."""
    if idempotency_key:
        existing = conn.execute(
            "SELECT ledger_id FROM wallet_ledger WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if existing:
            return True, get_balance(conn, username), True

    if not allow_negative:
        current = get_balance(conn, username)
        if current < amount_credits:
            return False, current, False

    _insert_ledger_row(conn, username, tenant_id, event_type, -abs(amount_credits), reference, idempotency_key)
    return True, get_balance(conn, username), False


def credit(conn, username: str, tenant_id: str, event_type: str, amount_credits: int,
           reference: str = None, idempotency_key: str = None):
    """amount_credits is a POSITIVE quantity. Returns (new_balance,
    already_applied) -- idempotent the same way debit() is, so a retried
    payment-confirmation poll can never double-credit a recharge."""
    _, applied = _insert_ledger_row(conn, username, tenant_id, event_type, abs(amount_credits), reference, idempotency_key)
    return get_balance(conn, username), not applied


# ---------------------------------------------------------------------------
# Higher-level helpers -- the specific debit/credit shapes this platform's
# locked pricing (§9.1) actually needs. Prefer these over calling debit()/
# credit() directly so the credit-rate math lives in exactly one place.
# ---------------------------------------------------------------------------

def debit_for_test(conn, username: str, tenant_id: str, test_id: str, total_marks: int):
    """Charged once, upfront, at 'Start Test' (locked 2026-08-15 -- see
    roadmap §2.1). idempotency_key is the test_id itself, so a retried/
    duplicate 'Start Test' tap for the same test can never double-charge."""
    amount = total_marks * RATE_TEST_CREDIT_PER_MARK
    return debit(
        conn, username, tenant_id, "test_debit", amount,
        reference=test_id, idempotency_key=f"test_debit:{test_id}",
    )


def credit_for_recharge(conn, username: str, tenant_id: str, payment_link_id: str, credits_granted: int):
    """Called once a Razorpay Payment Link is confirmed `paid` (see
    razorpay_client.fetch_payment_link()). idempotency_key is the payment
    link id, so a polling loop that checks status more than once after
    payment (which it will -- polling doesn't stop the instant it sees
    'paid' in every possible race) can never double-credit the same
    recharge."""
    return credit(
        conn, username, tenant_id, "recharge_credit", credits_granted,
        reference=payment_link_id, idempotency_key=f"recharge:{payment_link_id}",
    )
