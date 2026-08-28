# Payments & Wallet System — How It Works

**Status:** authoritative, describes the live system as of 2026-08-24.
**Read this if:** you're a student support person explaining the wallet to
a student, or an AI/developer touching `telegram/database/wallet.py`,
`identity.py`, `telegram/bots/wallet_flow.py`, or `test_flow.py`.

---

## 1. The one-sentence version

Every student has **one shared credit balance**, auto-created silently on
their first-ever interaction with any 1LAVYA bot, pre-loaded with **1,000
free credits** (worth roughly 1,000 MCQs, or 100 Descriptive questions, or
100 marks of Test Mode — one pool, not three separate ones), topped up via
Razorpay when it runs out.

## 2. Currency and rates

1 credit = ₹0.01 internally (never shown to students — see §5). Locked
rates:

| Activity | Cost | Rupee equivalent |
|---|---|---|
| MCQ practice | 1 credit per question shown | ₹1 / 100 MCQs |
| Descriptive practice | 10 credits per question shown | ₹1 / 10 questions (flat, regardless of marks) |
| Test Mode | 10 credits per mark of the assembled test | ₹1 / 10 marks — question delivery + PDF assembly only; evaluation is billed separately and not yet priced |

Debiting happens **at the moment a question is shown**, not when it's
answered — a shown-but-abandoned question is still charged (matches how
the platform already logs "shown" events for analytics elsewhere).

## 3. Identity: the thing that makes this frictionless

The wallet is keyed by a **1LAVYA username** (`student_profiles.username`),
not a Telegram chat ID — this is what lets one balance follow a student
across every phone/bot they use. Students never see a signup step for this:

- `telegram/database/identity.py`'s `ensure_wallet_identity()` runs
  silently on every relevant interaction. If the student already has a
  linked username (auto-created earlier, or set up by hand via "profile"),
  it's reused. Otherwise:
  - their real Telegram `@username` is used, if they have one and it isn't
    already claimed by someone else;
  - otherwise a deterministic `tg{telegram_user_id}` placeholder is used
    (always valid, always unique).
- This username is **permanent** — changing your Telegram handle later
  never changes your 1LAVYA identity. A student can still type "profile"
  any time to view/fill in the rest (display name, course, level, etc.).
- **As of 2026-08-24, the exact moment a username is first created is also
  the exact moment the 1,000-credit signup bonus is granted** — see §7 for
  why this had to be true and what broke before it was.

## 4. The signup bonus

- **1,000 credits, one time, ever.** No renewal, no monthly top-up. Once
  spent (or expired), the only way to get more is a real recharge.
- **Expires 365 days after grant if unused** — a background sweep
  (`wallet.sweep_expired_grants()`) claws back whatever's left of it,
  capped at the grant's own original size and the student's current
  balance (it can never touch money from a real recharge sitting in the
  same wallet).
- **Never framed in rupees.** The welcome message
  (`wallet.build_signup_grant_message()`) always speaks in
  questions/marks: *"enough for about 1000 MCQs, or 100 Descriptive
  Questions, or 100 marks worth of Tests (use any mix — it's one shared
  balance)"* — deliberate, so the free tier never feels like "you get
  ₹10," just "you get to start."
- Shown once, as its own message, ahead of whatever menu comes next — so
  it's never buried inside a Markdown-formatted screen.

## 5. Recharging

Triggered by typing **"recharge" / "top up" / "add money" / "add
credits"** to any bot, or tapping "💳 Recharge Wallet" from the
out-of-balance screen (§6). Flow:

1. Bot offers presets **₹20 / ₹50 / ₹100**, or a typed custom amount
   (minimum **₹20**).
2. A real Razorpay Payment Link is created (`razorpay_client.py`) and sent
   to the student.
3. On confirmed payment, `wallet.credit_for_recharge()` adds the credits
   (1 credit per ₹0.01, so ₹20 → 2,000 credits) and the student is
   notified with their new balance.
4. **Idempotent by construction** — the ledger insert's `idempotency_key`
   is the Razorpay payment link ID itself, so a polling loop that checks
   payment status more than once (it will) can never double-credit the
   same payment.

A student can check their balance any time by typing **"wallet" /
"balance" / "my balance"**.

## 6. What happens at zero balance

A debit that can't be covered (`wallet.debit()`) never touches the
ledger — it's a clean refusal, not a failed transaction to clean up. The
student sees: *"🛑 You've used up your balance for now."* plus a Recharge
Wallet button. **Deliberately never mentions money/rupees here either.**

## 7. A real bug, found and fixed 2026-08-24 — worth knowing about

**Symptom (real support complaint):** newly-enrolled students got no
welcome-bonus message, and their very first question hit "recharge your
wallet" — with a genuine zero balance, not a display glitch.

**Root cause:** `identity.ensure_wallet_identity()` and
`wallet.grant_signup_bonus()` were always meant to be called together —
`db_ensure_wallet()` in `exam_hub_bot.py` does exactly that, and every
bot's `/start`/`restart` handler calls it correctly. But several *other*
call sites — `exam_hub_bot.py`'s own `send_question()`/`send_mcq()`, and
the newer `test_flow.py`/`wallet_flow.py` (built after Test Mode/Recharge
shipped) — each called `ensure_wallet_identity()` **directly**, only
because they needed a username to pass into `wallet.debit()`. Calling it
silently *creates* a wallet identity if one doesn't exist yet — with a
real, permanent **zero** balance, since only `db_ensure_wallet()` grants
the bonus. This exact bug had already been found and fixed once, 2026-08-17,
in one call site (`faculty_bot.py`'s "Exam Practice Hub" button) — but
recurred because it was patched at the call site, not at the source.

**The fix:** `ensure_wallet_identity()` itself now grants the signup bonus
the instant it auto-creates a username — before returning to whatever
caller needed the identity. This closes the bug class structurally: every
existing call site is now safe automatically, and so is any future one,
without needing to remember to pair the two calls by hand ever again.
`db_ensure_wallet()` was adjusted to use the identity call's own
`was_new` flag (rather than a second, now-always-redundant grant call) to
decide whether to show the welcome message — otherwise the message would
have silently stopped appearing for everyone.

**Verified**, not just reasoned about: simulated a brand-new student
hitting the MCQ-shown code path directly (bypassing `/start` entirely, the
exact failure mode) — confirmed 1,000 credits granted automatically and
the first debit succeeds. Re-ran all 236 relevant smoke-test checks across
`smoke_test_wallet.py`, `smoke_test_wallet_flow.py`,
`smoke_test_exam_hub_wallet.py`, `smoke_test_test_flow.py` — all green.
Restarted every affected bot (`1lavya-examhub`, `capranav-exam`,
`csarunchouhan`).

## 8. Data model

| Table | Purpose |
|---|---|
| `wallet_ledger` | The only source of truth for balance — `SUM(amount)` per username, never a stored mutable field. Every credit/debit is one signed row (`event_type`, `amount`, `reference`, `idempotency_key`). |
| `wallet_grants` | Tracks the signup bonus's 365-day expiry lifecycle separately from the ledger row that actually moved the balance. |
| `payments` | One row per recharge attempt (`pending` → `completed`), keyed to the Razorpay payment link ID. |
| `student_profiles.username` | The permanent 1LAVYA identity everything above is keyed on. |

## 9. Not yet built / known open items

- Test Mode's **evaluation** step is not priced yet (only question
  delivery + PDF assembly are billed today).
- No admin-facing UI yet to manually adjust a student's balance (the
  `allow_negative=True` manual-adjustment path exists in `wallet.debit()`
  but nothing in the Admin Portal calls it).
- The ₹0.01-per-credit exchange rate is a recommendation inferred from the
  three locked rates coming out to clean whole numbers — not yet
  re-confirmed by Pranav as a literal figure (see `wallet.py`'s own
  docstring).
