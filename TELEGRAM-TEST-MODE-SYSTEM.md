# Telegram Platform — Test Mode & Wallet System: Complete Reference

**Status: primary, canonical reference for this whole system, as of 2026-08-16.**
If you are an AI agent (or a human) picking this up cold, read this file
start to finish before touching any code under `telegram/`. It explains not
just *what* exists but *why* every non-obvious decision was made, exactly
what's still open, and how each open item is planned to be closed — so you
can continue from precisely where this was left off, not re-derive it.

**Where this fits in the repo's doc hierarchy**: `/CLAUDE.md` §11 is the
platform's own dated build log (read it for everything that happened *before*
this system existed — wallet/billing didn't exist until this). This file
picks up the Test Mode + wallet/billing story in full depth, in one place,
rather than scattered across `/CLAUDE.md` §11's chronological entries and
`telegram/FIRST_PROMPT.md`'s index. `telegram/assets/exam_bot/Tests/
TEST-MODE-ROADMAP.md` is the **original planning document** this was built
from — it still holds some granular blow-by-blow detail (the original edge-
case brainstorm, the exact locked-decision trail with dates) and is kept as
supplementary reading, but **this file is now the primary reference** — the
roadmap file has a pointer at its own top saying so.

---

## 1. What this system is, in one paragraph

Students can now take real, timed, paid mock tests inside the `1lavya-examhub`
and `capranav-exam` Telegram bots — built from real CA Inter Advanced
Accounting exam papers (MTP/PYQ), with MCQ answers genuinely hidden until
submission, descriptive answers submitted via photo upload, a real Razorpay
payment wallet backing the whole thing, and a comprehensive activity log
capturing what the student did and when, down to the second. None of this —
the wallet, the identity system, or Test Mode itself — existed before
2026-08-15. All of it was built, tested, and deployed live across several
rounds on 2026-08-15/16.

---

## 2. Why this was built (the actual trigger, not a plan made in the abstract)

This did **not** start as "let's build a test feature." The literal sequence:

1. Pranav said he was creating a new Razorpay account and asked what to tell
   them about his collection method (no website exists — the whole platform
   is Telegram-native).
2. That led to researching UPI/payment-aggregator economics, then to
   Pranav pasting his live Razorpay keys into `telegram/.env` and saying
   "go ahead with the live keys only" (small transaction values, accepted
   the risk of no test-mode safety net).
3. **Only then** did he ask to actually build Test Mode — and specifically
   asked for the billing/wallet plumbing to exist first, since a paid test
   needs somewhere to charge from.
4. Once the wallet existed, he asked for it to be extended to gate ordinary
   MCQ/Descriptive **practice** too (not just Test Mode) — a real scope
   expansion, confirmed explicitly, not assumed.
5. Test Mode itself, wallet status/recharge UX, size tiers, and finally a
   full round of fixes from his own **manual testing** of the live system
   — each its own build-test-deploy-commit-merge cycle.

This ordering matters for anyone reading the git history: the wallet/
identity work is *chronologically and architecturally* the foundation, Test
Mode is built on top of it, not the other way around.

---

## 3. System architecture, top to bottom

```
┌─────────────────────────────────────────────────────────────┐
│ exam_hub_bot.py (the host process — 1lavya-examhub /         │
│ capranav-exam / csarunchouhan via faculty_bot.py's import)    │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────────┐ │
│  │ identity.py    │  │ wallet.py      │  │ razorpay_client.py │ │
│  │ (auto-username)│  │ (ledger, rates)│  │ (raw REST, live)   │ │
│  └───────────────┘  └───────────────┘  └────────────────────┘ │
│         used by            used by              used by         │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ wallet_flow.py -- "wallet"/"recharge" triggers,          │   │
│  │ balance display, Razorpay Payment Link creation + polling│   │
│  └────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ test_flow.py -- "test"/"upload" triggers, the entire     │   │
│  │ picker → summary → paid start → question delivery →      │   │
│  │ upload collection → timers/grace → submit engine          │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              telegram/database/platform.db
   (wallet_ledger, wallet_grants, payments, predesigned_tests,
    test_sessions, test_questions, test_mcq_answers, test_uploads,
    test_activity_log — all new, all described in §7)
```

**Design principle used throughout**: every new piece is its own module
(`identity.py`, `wallet.py`, `razorpay_client.py`, `wallet_flow.py`,
`test_flow.py`), following the exact same pattern this platform already
established for `profile_flow.py`/`report_flow.py`/`mcq_issue_flow.py` —
its own callback-data prefix, its own trigger phrases, imported into the
host bot script rather than the host script growing without bound. `test_flow.py`
and `wallet_flow.py` never import `exam_hub_bot.py` (would create a circular
import, since `exam_hub_bot.py` imports them) — instead the host bot passes
**itself** in as a `host` parameter at call time ("host-module injection"),
so `test_flow.py` can call `host.mcq_bank.get_by_id(...)`,
`host.html_to_telegram_text(...)`, etc. without duplicating that logic or
creating an import cycle.

---

## 4. The wallet & identity system

### 4.1 Why identity had to be auto-provisioned

The platform already had a username system (`profile_flow.py`, built
2026-08-11) — but it was opt-in, and when the wallet work started, **96 real
students existed and only 1 had ever set one up manually**. Gating a wallet
(which is keyed by username, for the multi-device-linking reasons the
original username system was built for) on that opt-in flow would have
silently locked out 95 of 96 students the moment billing went live.

**Decision**: `telegram/database/identity.py`'s `ensure_wallet_identity()`
silently claims a username from the student's own Telegram `@handle` the
first time they need a wallet operation — no prompt, no friction. If they
have no Telegram handle, or it's invalid (the same 3–20 char, alnum+
underscore rule `profile_flow.py` already enforces) or already claimed by
someone else, it falls back to a deterministic `tg{telegram_user_id}`
placeholder. This reuses the *exact same* `student_profiles`/
`students.lavya_username` tables `profile_flow.py` already owns — an
auto-provisioned username is indistinguishable in the database from one a
student typed in by hand.

**A real tension, flagged rather than silently resolved**: Pranav asked for
the student to be told their assigned username and be able to "edit it once."
The existing username system is explicitly *permanent, locked forever* —
`profile_flow.py`'s own profile screen literally renders `(permanent,
cannot be changed)`. Promising a one-time edit would make that on-screen
text false. **Resolution taken**: auto-provision silently as asked, but do
**not** offer the edit — the safer default (never promise something untrue)
over the literal ask. If a one-time-edit exception is actually wanted, it's
a `profile_flow.py` change (a new "was this auto-assigned and never
confirmed?" flag checked before permanently locking) — not built.

### 4.2 The credit system and why these specific rates

Everything is priced in **credits**, never shown to students as rupees
(Pranav's explicit, repeated rule — "never talk in terms of money, only
questions or marks"). The recommended (Pranav's own numbers imply this,
though never literally stated as an exchange rate) conversion is:

**1 credit = ₹0.01**

| Activity | Rate | Rupee equivalent |
|---|---|---|
| MCQ practice, per question shown | 1 credit | ₹1 per 100 MCQs |
| Descriptive practice, per question shown | 10 credits | ₹1 per 10 questions (flat, regardless of marks) |
| Test Mode facility, per mark of the assembled test | 10 credits | ₹1 per 10 marks |
| Signup grant (one-time, ever) | 1000 credits | ₹10-equivalent |
| Recharge minimum | — | ₹20 |

The Test Mode rate is confirmed to cover **only** question delivery, timing,
and upload collection — **not** AI evaluation of descriptive answers, which
Pranav has explicitly said is "a separate charge, we'll discuss separately."
No number has been invented for it. This is why `wallet.py` and the DB
schema have a clean seam between "facility" debits (`test_debit`) and
anything evaluation-related (nothing built yet).

### 4.3 The signup grant and its 365-day expiry

Every student gets **1000 credits, once, ever** — framed to them only as
"enough for about 1000 MCQs, or 100 Descriptive Questions, or 100 marks of
Tests (any mix, one shared balance)." This wording matters: it's explicitly
**not** three separate allowances, and `wallet.build_signup_grant_message()`
is the one place this framing lives so it's never re-worded inconsistently
elsewhere.

The grant expires 365 days after being granted, if unused. A dedicated
`wallet_grants` table (separate from the append-only `wallet_ledger`)
tracks each grant's own expiry lifecycle. The clawback math at expiry is
deliberately capped: `expired_amount = min(grant's own original size,
current balance)` — meaning an old, expired grant can **never** claw back
more than what it originally gave, so a student who has since made a real
paid recharge never has that money wrongly zeroed out by grant expiry. This
is an intentional approximation (not full FIFO lot-accounting of "which
credit was spent first") — correct for the common case (a grant-only
balance, which is every student's reality today, since recharges have never
actually been used by a real student yet) and safe even once recharges are
common.

`wallet.sweep_expired_grants()` implements this but **is not wired to any
scheduled job** — deliberately, since the earliest possible real expiry is
365 days out from whenever grants started being issued (2026-08-16). See
§12 for the plan.

### 4.4 Idempotency — the discipline that makes real money safe

Every debit/credit in `wallet.py` accepts an `idempotency_key`. A retry of
the same logical action (a double-tap, a bot restart mid-transaction, a
polling loop that checks payment status more than once after it's already
been credited) is a guaranteed no-op, not a double-charge. This was tested
explicitly and is the single most important correctness property of the
whole billing system — see `telegram/database/smoke_test_wallet.py`'s
"idempotent debit"/"idempotent credit" checks.

### 4.5 The recharge flow, and why polling instead of a webhook

`telegram/bots/wallet_flow.py`: typing `wallet` (same trigger convention as
`profile`) shows balance + nearest expiry + a "Recharge Wallet" button.
Typing `recharge` (or tapping that button) opens an amount picker
(₹20/₹50/₹100 + custom), creates a **real, live** Razorpay Payment Link via
`razorpay_client.py` (this platform's first-ever live Razorpay API call),
and sends the payable URL in chat.

**Confirmation is via polling, not a webhook**, because a webhook needs a
public HTTPS endpoint, and this whole platform runs on Pranav's local PC
with nothing internet-facing today. Setting that up needs Cloudflare
Tunnel, which needs Pranav's own interactive `cloudflared login` — a step
no AI session can do on his behalf. Polling `GET /v1/payment_links/{id}`
every 20 seconds via `context.job_queue` is a complete, correct v1 that
needed no infrastructure Pranav hadn't already set up. The webhook remains
a planned future upgrade for faster confirmation + a reconciliation safety
net, not a blocker.

**A real safety discovery while testing this**: the live Razorpay keys are
loaded into *any* process that imports `exam_hub_bot.py` — including
automated test runs. `telegram/bots/smoke_test_wallet_flow.py` therefore
mocks `razorpay_client.create_payment_link`/`fetch_payment_link` explicitly
via `unittest.mock.patch.object` on every single test path that would
otherwise touch them. Without this, running the test suite would have
created real, live, payable Razorpay links every time. **No human has yet
completed one real live payment through this pipeline** — everything is
verified with the Razorpay layer mocked, which is genuine and meaningful
verification of the surrounding logic, but is not the same as watching a
real UPI payment clear. This is the single most important open item — see
§12.

### 4.6 Turning on billing for ordinary practice (not just Test Mode)

`exam_hub_bot.py`'s `send_question()`/`send_mcq()` (the core practice-mode
functions, used by every student on every bot) now debit the wallet
*before* showing content, and show an honest "balance isn't enough" message
with a real Recharge Wallet button if the student can't afford it. This
was a deliberate, explicitly-confirmed scope expansion beyond Test Mode
(Pranav: "The wallet system should be extended across all the bots... a
single wallet for using everything"), not something assumed. Study Hub and
MyFiles Hub remain fully free — Pranav's own words: "we can any day have
some usage-based charge deducted" from them later, not decided yet.

---

## 5. Test Mode — Pre-Designed Tests

### 5.1 Scope, locked explicitly

**Pre-Designed Tests only** — no Student Customised Test (chapter-picker +
free-form marks target) was built. This was one of the very first
clarifying questions asked before any code was written, and Pranav picked
Pre-Designed specifically because it needs no new "which questions go into
this test" design decision — a real exam paper's own composition is used
as-is.

**CA Inter Advanced Accounting only** — the only subject with genuine
"one real paper" sitting data (built by an earlier, unrelated pipeline —
`first_run/`, see `/CLAUDE.md` §6 — that parsed real MTP/RTP/PYQ papers
into structured question banks). Any other course/level/subject a student
asks for is met with an honest "not available yet, here's what you can do
instead" (`test_flow.py`'s `_not_available_text_and_markup()`), never a
silent empty list or a dead end.

### 5.2 Why RTP sittings are excluded entirely

Before writing the catalog generator, every real RTP record (MCQ and
descriptive alike) was inspected directly. **None of them carry a reliable
stated marks value** — consistent with RTP being revision material, not a
scored real paper. A ₹-based test fee and a "total marks" summary are both
meaningless for a 0-marks test, so RTP sittings never become Predesigned
Tests. This is the concrete, real case the "gracefully deny" design
principle exists for.

### 5.3 How the sitting catalog is generated

`telegram/tools/generate_predesigned_tests.py` groups the real, already-
loaded MCQ and descriptive question banks (via `exam_hub_bot.py`'s own
`QuestionBank`/`McqBank` — reused directly, never re-parsed independently,
so the catalog can never drift from what the bot itself actually serves)
by real sitting. The matching key — confirmed by inspecting real data, not
assumed — is `(exam_type, year, month, set)`, extracted via regex from
both sides of the corpus:

- Descriptive `src_text`: `"MTP May 2024 Set 1"`, `"PYQ September 2025"`, etc.
- MCQ `mcq_id`: `"CAI-P1-MTP-2024-05-S1-PI-Q1-a"` — month **is** encoded in
  the id (confirmed: MTP 2024 has both `-05-` and `-09-` sittings with
  genuinely distinct real MCQs, i.e. May and September 2024 are different
  papers, not one combined group — a real finding from inspecting the data,
  not an assumption).

**Result: 27 real sittings** (18 MTP, 9 PYQ), 62–125 marks each, written
into a new `predesigned_tests` table. A cross-check was run: `test_flow.py`'s
own, separately-implemented question-matching logic was checked against all
27 catalog rows and **agreed exactly on every one** — 0 mismatches, meaning
a student is never shown a summary promising different content than what
they actually receive. This cross-check is now a permanent regression test
(`smoke_test_test_flow.py`).

### 5.4 Size tiers — 20/50/100 marks, not a mandatory full paper

Pranav's explicit correction after seeing the first version: "we should not
have the mandatory 100 marks test, instead we should have 3 options."
Every sitting now offers **up to 3 size tiers**:

- A tier at or above the sitting's own total collapses to one "Full Paper
  (N marks)" option instead of offering a phantom oversized choice a 62-mark
  paper can't actually provide.
- A tier's question subset is built **deterministically** — the same
  20-mark version of a given sitting is always the same questions, never
  randomized, so "the 20-mark version of MTP May 2026 Set 1" is a stable,
  well-defined thing a student could retake and compare.
- The split is **30% MCQ : 70% Descriptive** by marks — the same ratio
  Pranav confirmed for the (still unbuilt) Custom Test's own assembly,
  deliberately reused here rather than inventing a second, competing ratio
  decision. The algorithm takes the largest in-order prefix of each pool
  that fits its sub-target, with any leftover marks (a pool ran out before
  its sub-target) reallocated to whichever pool still has room.
- The wallet charge and test duration are both computed from the tier's
  **actual resulting marks** (often slightly under the nominal target —
  you can't split one question to hit an exact number), never the nominal
  tier value.

Validated across **all 27 sittings × every tier** — every combination
produces a valid, non-empty, correctly-capped subset. 0 problems, and this
is now a permanent regression check.

### 5.5 The full conversation flow

```
"test" (or resumes an in-progress test automatically)
  → Course → Level → Subject picker (auto-skips when only one real option
    exists, same discipline as practice mode's own Mode-first flow)
  → pick a real sitting
  → pick a size tier (20 / 50 / 100, or "Full Paper" if smaller)
  → summary screen: total marks, MCQ/Descriptive breakdown, credit cost
    against current balance (never rupees), rules explained
  → "Start Test" — debits the wallet upfront (idempotent, keyed to the
    test_id), creates the test session + every question row, schedules
    timers, shows Q1
  → MCQ delivery: answer genuinely hidden until submission (a real,
    separate render path from practice mode's instant-feedback rendering,
    not a flag on it) — can be changed any number of times before
    submitting; skip-and-revisit via Next/Prev/a question-list "palette"
    with status icons
  → Descriptive delivery: no "Show Answer" button (unlike practice mode) —
    prompts to type "upload" when ready
  → "upload" → picks which question (index-based, never a dead-end) →
    if that question already has pages, asks Overwrite vs. Append first →
    accepts photo(s)/document(s), one at a time, confirming each →
    "done" (finish, keep what's there) or "pass" (explicitly decline this
    question) end the collection
  → "Submit Test" → shows a confirmation summary (MCQs answered/blank,
    descriptive uploaded/passed/missing) → Confirm & Submit / Go Back
  → On confirm: MCQs graded instantly (deterministic, no AI needed);
    descriptive result reported honestly as "saved, evaluation coming in
    a future update" (no false 30-minute promise, since AI evaluation is
    a separate, differently-priced, unbuilt feature)
  → Auto-submits at time-up if never manually submitted (see §5.6)
```

### 5.6 Timers, reminders, and the interactive grace period

- **Reminders**: sent at 5 minutes and 3 minutes before the nominal time
  limit (Pranav's explicit numbers).
- **At nominal time-up**: the student is **not** immediately force-
  submitted. They're offered a **one-time** choice — +2, +3, or +5 minutes,
  or submit now — via `test_sessions.grace_offered_at` (set once, checked
  before ever offering again) and `grace_requested_minutes` (which choice,
  if any, was made). A 60-second fallback auto-submits if there's no
  response at all.
- **Nothing is actually lost by any of this timing**, and that's the real
  finding worth remembering: every uploaded photo is written to disk and
  logged in the database the instant it's sent, never batched behind
  typing "done." A question with real uploaded pages but no "done" still
  counts as `uploaded` at submission time (reconciled explicitly in
  `_submit_test()`), whether that submission is manual, auto-at-expiry, or
  after a grace extension. The grace period is a courtesy, not a data-
  safety mechanism — data safety was already solved by saving instantly.
- **All of this survives a bot restart.** `test_flow.rearm_pending_test_jobs()`
  runs at every bot startup, sweeping every `in_progress` test and
  re-arming whichever timers (expiry, reminders, the heartbeat — see §5.7)
  are still relevant, finalizing anything that's unambiguously overdue.
  `job_queue` jobs do not survive a process restart on their own — this
  platform has learned that lesson repeatedly (heartbeat scheduling,
  recharge polling, the platform watcher) and Test Mode follows the same
  discipline.

### 5.7 Activity logging, topic tracking, and exact-point resume

Built in direct response to Pranav's own detailed ask: capture *everything*,
so a student's understanding can eventually be analyzed at concept level,
and so at most 60 seconds of "what was the student doing" is ever lost even
if their phone dies mid-test.

**`test_activity_log`** — a new, lean, append-only event table (Pranav's
own proposed "action + timestamp" shape), the exact same architectural
pattern this schema already uses for `wallet_ledger`/`report_flow_events`:
a current-state table for fast queries ("what's the score"), an append-only
log underneath it for full history ("what actually happened, in order").
Logged events include: `test_started`, `question_viewed`,
`mcq_option_selected` **and** `mcq_option_changed` (with the old→new value,
so a change of mind is distinguishable from a first, confident pick),
`upload_page_added`/`upload_done`/`upload_overwrite_chosen`/
`upload_append_chosen`, `question_passed`, `no_activity_heartbeat`,
`reminder_sent`, `grace_offered`/`grace_chosen`, `submit_confirmation_shown`,
`test_submitted`.

**The 60-second no-activity heartbeat** is deliberately self-terminating:
each firing re-checks whether the student is *still* on that exact question
(`test_sessions.current_seq_no`) before logging anything or rescheduling
itself. The instant they navigate away, the next (possibly already
in-flight) firing simply finds a mismatch and stops — no separate
cancellation logic needed for the common case, though `_cancel_test_timers()`
also cancels it explicitly on test end for cleanliness.

**Exact-point resume**: `test_sessions.current_seq_no` tracks the literal
question last shown. Resuming an in-progress test (typing "test" again, or
recovering after a restart) returns to that *exact* question — not "the
first unanswered one," which could be materially different if the student
had navigated ahead to review something.

**Topic/subtopic tracking**: `test_questions.chapter_slug`/`topic_text` are
snapshotted from the real content bank at test-build time (never re-derived
later, so a test's own record stays stable even if content is re-tagged
afterward). This is what makes concept-level analysis possible later —
not built yet as an analysis *layer*, just as the raw capture.

**Explicitly not built**: the student-facing "activity" dashboard view
Pranav described ("visible to the student under an activity option under
his dashboard"). This document's system is the data-capture layer only —
a UI to browse it is a distinct, separate, future piece.

---

## 6. Data model — every new table, in one place

| Table | Purpose | Key columns worth knowing |
|---|---|---|
| `wallet_ledger` | The append-only credit/debit log. **The balance is always `SUM(amount)`, never a stored column.** | `username` (not `telegram_user_id` — see §4.1), `event_type`, `amount` (signed), `idempotency_key` (UNIQUE-guarded) |
| `wallet_grants` | Tracks each signup grant's own 365-day expiry lifecycle, separate from the ledger | `amount_credits`, `expires_at`, `expired_amount` (NULL until swept) |
| `payments` | One row per Razorpay recharge attempt | `gateway_txn_id` (the Payment Link id, UNIQUE — the idempotency key), `status` (`pending`/`completed`/`failed`) |
| `predesigned_tests` | The generated catalog of real sittings | `catalog_key`, `total_marks`, `mcq_count`/`descriptive_count`, `active` |
| `test_sessions` | One row per test a student has started | `test_id` (millisecond-precision, collision-safe), `username`, `status`, `expires_at`, `current_seq_no`, `grace_offered_at`/`grace_requested_minutes` |
| `test_questions` | One row per question *within* a test — its own `seq_no` numbering, never the source paper's own question number | `qtype`, `source_id` (mcq_id/book_id), `marks`, `status`, `chapter_slug`/`topic_text` (topic snapshot) |
| `test_mcq_answers` | Current selected option per MCQ (the event history of every pick/change lives in `test_activity_log` instead) | `selected_option`, `is_correct` (NULL until graded at submission) |
| `test_uploads` | One row per uploaded **page** (a question's answer can span several photos) | `page_no`, `file_path` (under `telegram/assets/exam_bot/Tests/uploads/`, gitignored) |
| `test_activity_log` | The full, append-only event history — see §5.7 | `seq_no` (nullable — NULL for test-level events), `action_type`, `detail`, `occurred_at` |

All of these were added via `schema.sql`'s `CREATE TABLE IF NOT EXISTS`
(brand new tables) or, for columns added to an already-live table mid-
session (a real recurring situation this session hit — see §9), via
`db.py`'s `_COLUMN_MIGRATIONS` dict (simple `ALTER TABLE ADD COLUMN`) or,
where a column's *identity* changed (not just an addition — e.g.
`wallet_ledger`'s `telegram_user_id`→`username` rename, or a widened
`CHECK` constraint), a one-time guarded `DROP TABLE` + recreate in
`db._migrate_wallet_ledger_shape()`, verified safe against the live
database (checked for zero real rows) before ever being written.

---

## 7. File map

| File | What it is |
|---|---|
| `telegram/database/identity.py` | Auto-provisions a student's permanent wallet identity from their Telegram handle |
| `telegram/database/wallet.py` | Ledger primitives (`get_balance`, `debit`, `credit`), locked rates, signup grant + expiry sweep, the grant message builder |
| `telegram/database/razorpay_client.py` | Raw REST client for Razorpay Payment Links (live keys) — matches this codebase's existing `cf_email.py` style, no new dependency |
| `telegram/bots/wallet_flow.py` | The `wallet`/`recharge` conversational flow |
| `telegram/tools/generate_predesigned_tests.py` | Generates the real-sitting catalog (run once; re-run only if the underlying content changes) |
| `telegram/bots/test_flow.py` | The entire Test Mode engine — picker, timers, question delivery, uploads, activity logging, submission |
| `telegram/bots/exam_hub_bot.py` | The host bot — wires all of the above in, plus the practice-mode wallet debits |
| `telegram/database/schema.sql` | All new tables (see §6) |
| `telegram/database/db.py` | Migration logic for the above |
| `telegram/database/smoke_test_wallet.py` | 49 checks — ledger/identity/grant/expiry logic in isolation |
| `telegram/bots/smoke_test_exam_hub_wallet.py` | 13 checks — the real wiring inside `exam_hub_bot.py` (not just `wallet.py` alone) |
| `telegram/bots/smoke_test_wallet_flow.py` | 21 checks — the recharge flow, **every Razorpay call mocked** |
| `telegram/bots/smoke_test_test_flow.py` | 81 checks — the full conversation sequence end to end, timers, grace period, activity logging |
| `telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md` | The original planning document — supplementary detail, superseded by this file as the primary reference |
| `telegram/assets/exam_bot/Tests/uploads/` | Where uploaded answer-sheet photos actually live — gitignored, binary + personal data |

---

## 8. Testing & verification discipline

**164 automated checks across 4 suites**, all passing, all re-verified after
every subsequent change in the same session. The discipline followed
throughout, consistent with how this whole platform has always been built:

- Every suite drives the **real code** (imports the actual bot modules,
  calls the actual functions) against synthetic, self-cleaning data in the
  real shared `platform.db` — never a reimplementation of the logic being
  tested, never a mocked DB layer.
- Full cleanup in a `finally` block, verified to leave zero residue, even
  on a failed run.
- Real bugs were caught **by the tests themselves**, not just written and
  assumed correct — worth listing explicitly since it's the clearest
  evidence this testing was genuine, not theater:
  - A foreign-key deletion-order bug, found **three separate times** across
    different test files (`students.lavya_username` and
    `payments.telegram_user_id` both reference `students`, on top of
    `wallet_ledger`'s own FK — a durable pattern now worth remembering,
    not just a one-off).
  - A self-inflicted false positive in the schema migration's staleness
    check (an explanatory comment mentioning the old enum value by name
    fooled a naive "does the old name still appear" check).
  - `_new_test_id()`'s second-precision timestamp collision risk — found
    because the test suite creates several test sessions in rapid
    succession, which a real student could plausibly also do.
  - `_cancel_test_timers()` never cancelled the heartbeat chain.
  - The `<code>`-tag rendering bug from Pranav's own manual test (§9.4).
- **The one thing automated testing cannot cover**: a real live Razorpay
  payment. Every test that touches `razorpay_client.py` mocks it
  explicitly. See §12.

---

## 9. Build chronology (dated, so the git history makes sense)

1. **2026-08-15 (payment collection research)** — Razorpay decision,
   UPI/aggregator economics researched, live keys added to `.env`.
2. **2026-08-15 (wallet foundation)** — `wallet_ledger`/`payments` reshaped
   (username-scoped), `wallet.py`, `razorpay_client.py` built.
   Deliberately not exercised against the live API. Deployed nowhere yet
   (no bot wiring).
3. **2026-08-16 (identity + signup grant + practice billing)** —
   `identity.py` built (96 students, 1 with a username, confirmed the real
   need). `wallet_grants` + 365-day expiry. `exam_hub_bot.py`'s
   `send_question()`/`send_mcq()` wired to debit for real. **Deployed** —
   the first time any of this touched real, live student traffic.
4. **2026-08-16 (Test Mode itself)** — `generate_predesigned_tests.py`
   (27 real sittings), `test_flow.py` (full engine, no size tiers yet, no
   wallet display), deployed.
5. **2026-08-16 (wallet display, real recharge, size tiers)** —
   `wallet_flow.py` built (the first live Razorpay call ever wired up, but
   never actually fired by this session), Test Mode's mandatory-full-paper
   design corrected to 3 size tiers per Pranav's explicit ask, deployed.
6. **2026-08-16 (Pranav's manual test → 6 fixes + full activity logging)**
   — re-upload confirmation, `pass`, submit confirmation summary, timer
   reminders + interactive grace period, and the entire `test_activity_log`
   system (topic tracking, heartbeat, exact-point resume) — all built in
   response to a real person actually using the live system and reporting
   back what was wrong or missing. Deployed.
7. **This document** — written after round 6, consolidating everything
   above into one canonical reference.

Every round in this list followed the same cycle: build → automated test →
deploy (restart the affected bot processes, confirm clean logs) → commit →
push the feature branch → fast-forward merge to `main` → push `main`. All
of it lives on branch `telegram/test-mode-wallet-billing`, merged into
`main` after each round (never a single giant commit).

---

## 10. A recurring operational lesson: concurrent-session git entanglement

**Worth knowing before you commit anything in this repo.** Across every
single round above, `telegram/database/schema.sql` (and once,
`telegram/database/README.md`) contained **unrelated, uncommitted work from
a different, concurrent AI session** — `faculty_master`/
`faculty_report_deliveries`/`content_ingestion_log` tables and a Windows
autostart section, none of it related to Test Mode/billing. This is exactly
the scenario `/CLAUDE.md` §2's multi-agent warning describes, and it
recurred, unprompted, in every round.

**The fix applied every time, and the one worth reusing**: never trust hunk
boundaries alone (`git diff`'s hunks can bundle adjacent, unrelated content
together when there's no separating context between them — this happened
more than once, including with content that had *never been committed by
anyone*, not just "committed by someone else"). Instead: identify the exact
line ranges of the foreign content by reading the file directly, build a
"HEAD + only this session's own known edits" reconstruction with Python
(never by hand-editing a raw diff), verify it with assertions (the foreign
section names must be absent, this session's own additions must be
present), verify the reconstruction is valid, loadable, self-contained SQL
on its own, stage *that*, then restore the working tree to its full state
(with the other session's work still sitting there, untouched, for them to
commit separately). `database/README.md` was ultimately excluded from every
commit in this whole build — every change to it, across all rounds, turned
out to belong to the other session, never this one.

If you're picking this up and `schema.sql`/`database/README.md` look
different from what's described here, **check git log and read the current
file directly** rather than trusting this section blindly.

---

## 11. Deployment status (as of 2026-08-16, end of round 6)

Live on `1lavya-examhub` and `capranav-exam` (both restarted after every
round, confirmed clean startup logs each time). **Not** deployed to
`csarunchouhan` — he doesn't teach CA Inter Advanced Accounting, so Test
Mode has nothing to offer his students; the practice-mode wallet debiting
*is* live for him too, though (via `faculty_bot.py`'s shared import of
`exam_hub_bot.py`'s functions).

---

## 12. Open points — and the actual plan for each, not just "not done"

1. **No human has completed a real live Razorpay payment yet.**
   *Plan*: Pranav (or another real person) needs to run one real ₹20 (or
   any amount) recharge through the live `wallet`/`recharge` flow and watch
   it clear end to end. Nothing else should be considered fully trustworthy
   about the payment side until this happens once, given there's no
   test-mode safety net (§4.5).

2. **The two evaluation PDFs (MCQ Evaluation + Descriptive Evaluation)** —
   Pranav's detailed spec: one PDF per test with every MCQ's question,
   student answer, correct answer, and explanation, marks shown per
   question; one PDF per test with every descriptive question's text,
   suggested answer, and the student's uploaded answer (images converted to
   PDF pages, embedded, no image ever cut across a page boundary, every new
   question starting on a fresh page), explicitly designed to be clean
   enough for a future AI model to grade from directly.
   *Plan*: this is the clear next build. Needs: HTML→PDF for the text
   portions (this codebase already does this via `xhtml2pdf`, just needs
   extending from "one question" to "every question in a test"), image→PDF
   for the uploaded photos (Pillow, already a dependency, straightforward
   per-image conversion), and a merge step (`pypdf`, already used elsewhere
   in this repo) stitching text-pages and image-pages together in the right
   order per question. Not started as of this document.

3. **AI evaluation of descriptive answers (Phase 2)** — blocked on
   Pranav's own explicit "we'll discuss separately" regarding pricing. No
   number has been invented. Blocked, not forgotten.
   *Plan*: once pricing is set, this becomes its own build — likely reading
   the Descriptive Evaluation PDF from item 2 above as its primary input,
   given Pranav's own framing of that PDF as something "any other AI bot"
   could grade from.

4. **Study Hub / MyFiles Hub don't have wallet identity/display yet** — a
   student whose genuine first-ever platform touch is Study Hub doesn't see
   the welcome-bonus message at that moment, and can't type `wallet` there.
   They still get the grant automatically the first time they touch a
   wallet-gated exam-hub flow — this is a UX gap, not a financial or
   correctness one.
   *Plan*: same `identity.ensure_wallet_identity()` + `wallet.
   grant_signup_bonus()` calls, wired into `study_hub_bot.py`/
   `myfiles_hub_bot.py`'s own `/start` handlers. Small, not started.

5. **`wallet.sweep_expired_grants()` isn't scheduled anywhere.**
   *Plan*: a low-frequency `job_queue` task in one bot, or a standalone
   scheduled tool script — either is fine. No urgency (earliest real
   expiry is 365 days from whenever a grant was actually issued, i.e. no
   earlier than 2027-08-16).

6. **Cloudflare Tunnel + webhook for faster/more robust payment
   confirmation** — an upgrade over polling, not a blocker. Needs Pranav's
   own interactive `cloudflared login`.
   *Plan*: once that happens, `wallet_flow.py` gains a webhook receiver
   alongside (not instead of) the existing polling, which becomes a
   reconciliation safety net rather than the primary confirmation path.

7. **Student Customised Test** (chapter picker + free-form marks target,
   as opposed to a Pre-Designed sitting) — explicitly out of scope for this
   edition, Pranav's own confirmed choice, not a gap.
   *Plan*: if/when revisited, the 30:70 MCQ:Descriptive ratio and the
   marks-approximate assembly approach are already designed (see
   `TEST-MODE-ROADMAP.md` §6) — this document's size-tier subsetting logic
   in `test_flow.py`'s `_build_subset_questions()` is directly reusable,
   since it already solves "assemble a target-marks subset with a fixed
   MCQ:Descriptive ratio," just currently scoped to one sitting rather than
   across the whole subject.

8. **The student-facing "activity" dashboard** (Pranav: "visible to the
   student under an activity option under his dashboard") — the data
   (`test_activity_log`) is fully captured; no UI exists to browse it.
   *Plan*: a new bot-facing view (likely alongside the existing `profile`/
   `wallet` text-trigger pattern) querying `test_activity_log` per student,
   or an Admin Portal analytics page (this platform already has a rich
   Admin Portal — see `/CLAUDE.md` §11 — with an established pattern for
   exactly this kind of paginated/filterable/exportable table view) for
   Pranav's own side. Not started.

---

## 13. Answering "why not just do X the simpler way" for the decisions most likely to be questioned later

- **Why not let Custom Test ship first, since it seems more flexible?**
  Because Pre-Designed needed zero new "which questions" design work (reuse
  a real paper as-is), while Custom Test's marks-approximate assembly is a
  genuinely harder, still-partially-designed problem (§12 item 7). Shipping
  the simpler, fully-specified thing first was the deliberate choice, not
  an oversight.
- **Why size tiers via a fixed 30:70 split instead of letting the student
  choose the MCQ:Descriptive mix?** Because that's a real, separate design
  decision (Custom Test's own open question) that Pranav had already
  weighed in on once (for Custom Test) — reusing it here avoids a second,
  possibly-inconsistent ratio decision for a feature (size tiers) that
  wasn't originally scoped to need one at all.
- **Why is the wallet keyed on `username` and not `telegram_user_id`,
  given that's a bigger schema change?** Because this platform already has
  a whole identity system (profile, leaderboards) built around "one
  student, several linked phones, one shared identity" — a wallet balance
  tied to a single device would contradict that model the moment a student
  switched phones. Confirmed explicitly with Pranav before building, not
  assumed.
- **Why is the wallet debit for Test Mode charged upfront, not
  incrementally as the student answers questions?** Confirmed explicitly
  (a locked decision from the original Test Mode design phase, see
  `TEST-MODE-ROADMAP.md` §2.1) — matches how a real exam fee works (pay to
  sit the paper, not per question you happen to finish), and makes the
  wallet math trivial to reason about (one debit, one `idempotency_key`,
  done) rather than needing per-question debit logic with its own
  idempotency surface.

---

## 14. Related documents

- `/CLAUDE.md` §11 — the platform's full dated history, everything that
  existed *before* this system (identity/leaderboard/report pipeline/
  Admin Portal), which this system was built on top of.
- `telegram/FIRST_PROMPT.md` — the platform-wide orientation index; update
  its table to point here once this file is read for the first time by a
  new session.
- `telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md` — the original
  planning document, kept for its granular decision-by-decision detail;
  superseded by this file as the primary reference (it says so at its own
  top now).
- `telegram/database/schema.sql` — the actual, current source of truth for
  every table described in §6; always more current than this document's
  prose if the two ever disagree — verify against it directly.
