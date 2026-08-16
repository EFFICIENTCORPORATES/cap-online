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
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402

logger = logging.getLogger(__name__)

CREDIT_TO_INR = 0.01  # 1 credit = ₹0.01 -- see module docstring; recommendation, not yet re-confirmed literally

RATE_MCQ_CREDIT = 1              # credits per MCQ shown
RATE_DESCRIPTIVE_CREDIT = 10     # credits per descriptive question shown
RATE_TEST_CREDIT_PER_MARK = 10   # credits per mark of an assembled Test Mode session

RECHARGE_MINIMUM_INR = 20  # locked 2026-08-15, third round

# --- Signup grant (locked 2026-08-16) -------------------------------------
# ONE-TIME per student, ever -- no renewal, no monthly recurrence (confirmed
# explicitly: "NO further grant is given, once exhausted they need to
# recharge the wallet"). Framed to students only in question/mark terms,
# NEVER in rupees -- see build_signup_grant_message() below. Expires 365
# days after grant if unused -- see wallet_grants (schema.sql) and
# sweep_expired_grants() below for the mechanics.
SIGNUP_GRANT_CREDITS = 1000        # = ₹10 at the CREDIT_TO_INR rate above
SIGNUP_GRANT_VALIDITY_DAYS = 365


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


def grant_signup_bonus(conn, username: str, tenant_id: str):
    """Grants SIGNUP_GRANT_CREDITS exactly ONCE per username, ever -- call
    this on a student's first-ever interaction with any 1LAVYA bot (after
    identity.ensure_wallet_identity() has resolved their username). Safe to
    call more than once for the same username (e.g. a student's first
    message arrives on two different bots in quick succession) -- the
    ledger idempotency_key AND a direct wallet_grants existence check both
    guard against a double-grant.

    Returns (new_balance, already_granted: bool). Posts BOTH a
    wallet_ledger credit (moves the balance) and a wallet_grants row
    (tracks the 365-day expiry lifecycle -- see that table's own schema.sql
    comment for why these are separate)."""
    existing = conn.execute(
        "SELECT grant_id FROM wallet_grants WHERE username=? AND grant_type='signup_bonus'",
        (username,),
    ).fetchone()
    if existing:
        return get_balance(conn, username), True

    now_dt = datetime.now(timezone.utc)
    granted_at = now_dt.isoformat(timespec="seconds")
    expires_at = (now_dt + timedelta(days=SIGNUP_GRANT_VALIDITY_DAYS)).isoformat(timespec="seconds")
    idem_key = f"signup_grant:{username}"

    new_balance, already_applied = credit(
        conn, username, tenant_id, "signup_grant", SIGNUP_GRANT_CREDITS,
        reference="signup_bonus", idempotency_key=idem_key,
    )
    if already_applied:
        # Ledger already had this grant (a race with another call) but
        # wallet_grants somehow didn't -- back-fill the tracking row so
        # the expiry sweep still knows about it, rather than silently
        # leaving an ungoverned credit with no expiry.
        pass

    db.execute_with_retry(
        conn,
        "INSERT INTO wallet_grants (username, grant_type, amount_credits, ledger_reference, granted_at, expires_at) "
        "VALUES (?, 'signup_bonus', ?, ?, ?, ?)",
        (username, SIGNUP_GRANT_CREDITS, idem_key, granted_at, expires_at),
    )
    return new_balance, False


def sweep_expired_grants(conn, tenant_id: str = "platform"):
    """Finds every wallet_grants row past its expires_at that hasn't been
    swept yet, and claws back whatever's left of it (capped at the grant's
    own original size AND the student's current balance -- see the
    wallet_grants schema.sql comment for why this never touches money
    beyond what this specific grant originally gave). Posts a
    'grant_expired' ledger debit for the clawed-back amount (skipped
    entirely if the remaining amount is 0 -- a fully-spent grant needs no
    ledger row, just marking swept).

    Meant to be run periodically (a scheduled tool script or a low-frequency
    job_queue task in one bot) -- NOT on every bot startup like
    init_schema(), since 365-day expiries are inherently a slow-moving
    concern, not something that needs checking every process restart.
    Idempotent and safe to re-run at any cadence -- only ever acts on rows
    with swept_at IS NULL.

    Returns the number of grants swept (for a caller to log/report)."""
    now_iso = db.now()
    due = conn.execute(
        "SELECT grant_id, username, amount_credits, ledger_reference "
        "FROM wallet_grants WHERE expires_at <= ? AND swept_at IS NULL",
        (now_iso,),
    ).fetchall()

    swept_count = 0
    for grant_id, username, amount_credits, ledger_reference in due:
        balance = get_balance(conn, username)
        expired_amount = max(0, min(amount_credits, balance))
        if expired_amount > 0:
            debit(
                conn, username, tenant_id, "grant_expired", expired_amount,
                reference=f"wallet_grants:{grant_id}",
                idempotency_key=f"grant_expired:{grant_id}",
                allow_negative=True,  # this IS the clawback -- must be allowed to zero out even the last credit
            )
        db.execute_with_retry(
            conn, "UPDATE wallet_grants SET expired_amount=?, swept_at=? WHERE grant_id=?",
            (expired_amount, now_iso, grant_id),
        )
        swept_count += 1
        logger.info(f"wallet: swept expired grant_id={grant_id} username={username!r}, clawed back {expired_amount} credits")
    return swept_count


def build_signup_grant_message() -> str:
    """The exact framing Pranav asked for: illustrative equivalences of ONE
    shared credit pool (never three separate allowances -- a student who
    mixes MCQs/Descriptive/Tests draws down the SAME balance, not three
    independent buckets), and NEVER a rupee figure. Centralized here so
    every bot's welcome message uses identical wording rather than each
    hand-rolling its own version."""
    mcq_equiv = SIGNUP_GRANT_CREDITS // RATE_MCQ_CREDIT
    desc_equiv = SIGNUP_GRANT_CREDITS // RATE_DESCRIPTIVE_CREDIT
    test_marks_equiv = SIGNUP_GRANT_CREDITS // RATE_TEST_CREDIT_PER_MARK
    return (
        f"\U0001F381 You've got free access to get started — enough for about "
        f"<b>{mcq_equiv} MCQs</b>, or <b>{desc_equiv} Descriptive Questions</b>, or "
        f"<b>{test_marks_equiv} marks worth of Tests</b> (use any mix — it's one shared "
        f"balance, not three separate ones). Valid for {SIGNUP_GRANT_VALIDITY_DAYS} days. "
        f"Go ahead and try!"
    )
