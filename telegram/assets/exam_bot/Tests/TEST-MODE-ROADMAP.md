# Test Mode — Roadmap (planning + in-progress build)

> **This file is now supplementary.** The primary, canonical reference for
> the whole Test Mode + wallet/billing system — architecture, every locked
> decision and why, full data model, file map, build chronology, and open
> points with their plans — is **`/TELEGRAM-TEST-MODE-SYSTEM.md`** (repo
> root), written 2026-08-16. Read that file first. This document is kept
> for its original granular edge-case planning and decision-by-decision
> trail, useful as backing detail, but no longer the first thing to read.

**Status: PLANNING, WITH REAL IMPLEMENTATION STARTED 2026-08-15.** This began
as a pure thinking-through-edge-cases pass (Pranav, 2026-08-15) before any code
was written — most of this document is still that planning material and should
be read as such. **Section 0 below is the current, load-bearing status** —
read it first, every session, before touching anything here; it tells you
exactly what's real (built, tested, on disk) vs. still just designed on paper.
Read `telegram/FIRST_PROMPT.md` first if you're new to this platform overall —
this doc assumes that context (bot roster, `tenants.json`/`bots.json`
convention, shared `platform.db`, the Mode-first Exam Hub flow, `human_id`/
`course_catalog`, the 64-byte `callback_data` bug class, the "known scale-
readiness gaps" callout in `/CLAUDE.md` right after §2).

**Where this lives:** this file sits in `telegram/assets/exam_bot/Tests/` per
Pranav's explicit instruction. Note this is *not* where the actual bot code will
end up — real code follows this repo's existing convention (`telegram/bots/` for
bot logic, `telegram/database/` for schema/queries, `telegram/tools/` for one-off
generator scripts) — this folder is planning + (later) generated test-catalog
artifacts + the local answer-sheet upload storage tree. Called out explicitly
rather than silently deviating from where code actually belongs. **The wallet/
billing code that already exists lives in `telegram/database/`** (see §0), not
in this folder — this folder holds the plan, not the implementation.

---

## 0. Current status (as of 2026-08-15/16 — read this first, every session)

This section exists so a fresh AI agent (or Pranav, or Future You) can pick
this up cold and know exactly what's real without re-deriving it from the rest
of this document or from chat history. Update it whenever the implementation
state changes — treat it like `FIRST_PROMPT.md`'s own "Status snapshot," not a
historical log.

### 0.1 What actually exists on disk right now, file by file

| File | Status | What it does |
|---|---|---|
| `telegram/database/schema.sql` | **Modified, live** | `wallet_ledger` reshaped to key on `username` (not `telegram_user_id`); `event_type` CHECK widened with `test_debit`/`descriptive_debit`; new `idempotency_key` column. `payments` gained a `username` column. See §9 below for the full "why." |
| `telegram/database/db.py` | **Modified, live** | New `_migrate_wallet_ledger_shape()`, called at the top of `init_schema()` — a one-time `DROP TABLE`+recreate for `wallet_ledger`/`payments` (SQLite can't `ALTER` a column's identity or widen a `CHECK`). Guarded: refuses to drop either table if it ever finds a real row. **Already run against the live `platform.db`** — both tables were verified empty first, migration executed, reshaped tables confirmed. |
| `telegram/database/wallet.py` | **New, complete for its scope** | The ledger primitives every other piece should call: `get_balance()`, `debit()`, `credit()` (both idempotency-key protected against double-charge/double-credit on a retry or restart), plus `debit_for_test()` and `credit_for_recharge()` at the locked rates. `CREDIT_TO_INR = 0.01` is the recommended (not yet Pranav-reconfirmed) exchange rate. |
| `telegram/database/razorpay_client.py` | **New, complete for its scope, UNEXERCISED against the live API** | Raw REST client (matches `cf_email.py`'s style, no new dependency): `create_payment_link()`, `fetch_payment_link()`. Reads live keys from `RAZORPAY_1LAVYA_key_id`/`RAZORPAY_1LAVYA_key_secret` in `telegram/.env` (confirmed gitignored, confirmed never tracked in git history). No call has been made against Razorpay's real API by any session yet — every call this module makes is real money, deliberately left for a human-verified first use, not an AI-initiated test call. |
| `telegram/database/smoke_test_wallet.py` | **New, passing 21/21** | Pure DB-logic test for `wallet.py` (balance/credit/debit/idempotency/rate-helpers/currency conversion). Makes zero network calls by design — safe to re-run any time. Does NOT test `razorpay_client.py` at all (nothing to test without spending real money). |
| `telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md` | This file | The plan. Sections 1–8 are the original Test Mode feature design (mostly still just planning); §9 is the billing/wallet design + decision trail; §0 (this section) is the living status. |

### 0.1a Update, 2026-08-16 — platform-wide identity + signup grant + live MCQ/Descriptive billing

Scope grew significantly beyond Test Mode itself this round (Pranav's
explicit direction) — building the wallet foundation turned into turning on
real billing for ordinary practice across the exam-hub bots, immediately.
**Built, tested, and DEPLOYED LIVE** (per Pranav's explicit "wire in and
restart yourself, no check-in needed"):

- **`telegram/database/identity.py`** (new) — `ensure_wallet_identity()`
  auto-provisions a student's permanent 1LAVYA username from their Telegram
  `@username` (falling back to a `tg{id}` placeholder if they have none, or
  it's invalid/already claimed) — no manual profile-setup step required.
  Confirmed necessary: 96 real students existed at build time, only 1 had
  ever set up a username manually. Reuses `profile_flow.py`'s exact
  validation/insert pattern — an auto-provisioned username is
  indistinguishable in the DB from a manually-set one, and is bound by the
  same **permanent, never-editable** rule already shown to students via
  "profile" (a real tension with Pranav's ask for one-time editability,
  resolved by NOT promising editability rather than contradicting existing
  on-screen text — see §9.6).
- **`wallet_ledger`/`payments` reshaped a second time**: `event_type`
  renamed `free_monthly_grant`→`signup_grant`, added `descriptive_debit`/
  `grant_expired`. New **`wallet_grants`** table tracks each grant's own
  365-day expiry lifecycle separately from the ledger (see schema.sql's own
  comment for the clawback-cap math: never expires more than the grant's
  own original size or the student's current balance, so a real recharge is
  never wrongly touched by an old grant's expiry).
- **`wallet.py` gained**: `grant_signup_bonus()` (1000 credits, ₹10-
  equivalent, ONE-TIME ever, idempotent), `sweep_expired_grants()` (365-day
  clawback, capped and safe, meant to run periodically — not wired to a
  schedule yet, see §0.2), `build_signup_grant_message()` (the exact
  question/marks-only framing Pranav specified, one shared pool not three
  separate ones, no rupee figures ever).
- **`exam_hub_bot.py` wired in** (the shared script behind `1lavya-examhub`,
  `capranav-exam`, and — via `faculty_bot.py`'s import — `csarunchouhan`):
  `db_ensure_wallet()` runs on every `/start`/restart, granting the
  one-time bonus and showing the welcome message on a student's genuine
  first-ever touch (platform-wide, keyed by username — whichever exam-hub
  bot they touch first). `send_question()`/`send_mcq()` now debit
  (`descriptive_debit`=10 credits, `mcq_debit`=1 credit) **before** showing
  content; an out-of-balance student sees an honest message (no rupees, no
  false promise of a working recharge yet) instead of the question.
- **Two integration test suites, both passing**: `telegram/database/
  smoke_test_wallet.py` (49/49 — ledger/identity/grant/expiry logic in
  isolation, including a real bug caught and fixed mid-build: the FK from
  `students.lavya_username` to `student_profiles.username`, on top of
  `wallet_ledger`'s own FK, meant cleanup order mattered and the first
  version got it backwards) and `telegram/bots/
  smoke_test_exam_hub_wallet.py` (13/13, new — drives the REAL
  `exam_hub_bot.py` functions, not just `wallet.py` in isolation, catching
  what a module-only test can't: wiring bugs. One real test-setup bug
  caught here too — a synthetic Telegram handle exceeding the 20-char limit
  correctly triggered the placeholder fallback, which was `identity.py`
  working as designed, not a bug).
- **Deployed**: all three bots restarted via `manage_bots.py`, confirmed
  fresh PIDs and clean startup logs (no tracebacks) via `manage_bots.py
  status`.

**Known gap, stated honestly**: this round's identity/grant wiring only
touches the exam-hub-kind bots. Study Hub and MyFiles Hub bots do NOT call
`db_ensure_wallet()` on their own `/start` — a student whose actual first-
ever platform touch is Study Hub won't see the welcome-bonus message at
that moment (they still get the grant automatically, just later, the first
time they hit a wallet-gated exam-hub flow — a UX gap, not a financial or
correctness one). Extending this to Study Hub/MyFiles Hub is straightforward
(same `identity.ensure_wallet_identity()` + `wallet.grant_signup_bonus()`
calls, different bot script) but wasn't done this round given the size of
what was already in flight.

**Incident, not swept under the rug**: while restarting `1lavya-examhub`,
a `tail` of its log to check for a clean startup was displayed unfiltered
and briefly showed the bot's live Telegram token in plaintext (standard
`httpx` request-logging behavior, not something this session's code
introduced — but displaying it without filtering was this session's own
mistake). Practical exposure is low (a bot token controls that bot's
messages, not money), but rotating it via BotFather is worth considering
since it's now sat in a conversation transcript.

### 0.1b Update, 2026-08-16 (same day, later) — Test Mode itself: BUILT and DEPLOYED

**Pre-Designed Tests, the actual feature, is now live** on `1lavya-examhub`
and `capranav-exam` (Pranav's confirmed scope: CA Inter Advanced Accounting
only, the sole subject with real "sitting" data). Full engine, not a demo:

- **`telegram/tools/generate_predesigned_tests.py`** (new) — groups the
  REAL, already-loaded MCQ + descriptive banks by real sitting (verified
  matching key: both sides encode exam_type/year/month/set consistently —
  confirmed by inspecting real `mcq_id`s and `src_text`s directly, not
  assumed). **RTP is excluded** — every real RTP record, MCQ and
  descriptive alike, was confirmed to carry no reliable stated marks, so a
  ₹-based test fee and a "total marks" summary would both be meaningless.
  **27 real sittings generated** (18 MTP, 9 PYQ) into the new
  `predesigned_tests` table, ranging 62–125 marks. A cross-check ran
  after the fact: `test_flow.py`'s own (separately implemented) question-
  matching logic was checked against all 27 catalog rows and agreed
  exactly on every one — 0 mismatches, meaning a student is never shown a
  summary promising different content than what they actually receive.
- **`telegram/bots/test_flow.py`** (new, ~600 lines) — the full engine:
  Course→Level→Subject→sitting picker (auto-skips when only one real
  option, same discipline as practice mode; a subject with no tests gets
  an honest "not available yet, here's what you can do instead" message,
  never a dead end); a summary/confirm screen showing cost in credits
  (never rupees) against the student's real balance; `Start Test` debits
  the wallet upfront via the already-built `debit_for_test()`; MCQ
  delivery with the answer genuinely hidden until submission (a real,
  separate render path from practice mode, not a flag on it); skip-and-
  revisit navigation; a question-list "palette" (✅/⚪/🟡/📝 status icons);
  descriptive delivery with an `upload`-triggered, question-scoped photo/
  document collection flow (`Page N saved... type done`); submission that
  grades MCQs immediately and honestly reports descriptive answers as
  "saved, evaluation coming in a future update" (no false 30-minute
  promise, since AI evaluation — a separate, differently-priced feature —
  isn't built); a scheduled auto-submit at time-up that **survives a bot
  restart** (`rearm_pending_test_jobs()`, swept at every startup, same
  discipline this platform already established for every other scheduled
  job). Uses a "host module" dependency-injection pattern (passes
  `exam_hub_bot` itself into `test_flow.py`'s functions) specifically to
  reuse `exam_hub_bot.py`'s existing HTML-rendering/message-splitting
  helpers without a circular import or duplicating that logic.
- **Wired into `exam_hub_bot.py`**: new callback prefixes
  (`testflow:`/`tnav:`/`topt:`/`tgo:`/`tupload:`, same explicit-pattern-
  per-module discipline as every existing flow, guarding against the
  callback-collision bug class this platform has hit 3+ times), a new
  photo/document `MessageHandler` (this bot never needed one before Test
  Mode), and the `"test"`/`"upload"` text triggers checked in the same
  "most specific active state first" order as every other trigger.
- **`telegram/assets/exam_bot/Tests/uploads/`** added to `.gitignore` —
  binary + personal student data, before any real file could land there.
- **Three new DB tables** (`test_sessions`, `test_questions`,
  `test_mcq_answers`, `test_uploads` — 4, really) plus `predesigned_tests`,
  all created cleanly (brand new tables, no reshape needed).
- **Three test suites, all passing, run for real**:
  `smoke_test_test_flow.py` (new, 32/32 — drives the ACTUAL conversation
  sequence end to end: trigger → picker → summary → paid start → MCQ
  answer with correctness hidden → palette → descriptive view → upload
  trigger → question pick → mocked photo → `done` → submit → honest
  result — this is the specific "smoke test the conversation/message
  sequence" check Pranav asked for), plus the two wallet suites from
  §0.1a re-verified still passing (49 + 13). **Two real test-script bugs
  were caught and fixed while building this** (both in the test script
  itself, not the product): a premature callback-handler call before its
  mock `.data` attribute was set, and stray empty upload directories left
  behind by a mocked file download — both fixed, cleanup verified leaves
  zero residue.
- **Deployed**: `1lavya-examhub` and `capranav-exam` restarted (per
  Pranav's explicit scope — `csarunchouhan` was NOT included this round,
  since he doesn't teach CA Inter Advanced Accounting), confirmed fresh
  PIDs and clean startup logs.

**Explicitly NOT built this round, by deliberate choice, not oversight**:
- **The 3-PDF delivery bundle** (§10 — Suggested Answer / Question Paper /
  Student Answer Sheet PDFs). Uploaded files are safely stored on disk and
  in `test_uploads` regardless — nothing is lost by deferring this: it can
  be built later as a pure addition, without touching the core flow above.
- **AI evaluation (Phase 2)** — still correctly blocked on evaluation
  pricing, per Pranav's own "we'll discuss separately."
- **Student Customised Test** — out of scope for this round per Pranav's
  own confirmed choice (Pre-Designed only).
- **Reminder messages at 50%/75%/90%/T-5min** — the roadmap's §7 flagged
  these as a "nice to have"; only the essential mechanics shipped (a live
  "time remaining" line on every question, freshly computed, plus the
  hard auto-submit at expiry). No milestone reminder pings.
- **A live end-to-end test with real Telegram** (an actual person tapping
  through a real test in the real app) — everything above is verified by
  driving the real code programmatically, which is real and meaningful
  verification, but is not the same as a human clicking through the real
  UI. Worth Pranav doing once, the same "human-verified first real
  transaction" caveat already flagged for the wallet/Razorpay work.

### 0.1c Update, 2026-08-16 (same day, later still) — wallet status screen, real recharge flow, Test size tiers

Three more pieces, all built, tested, and deployed:

1. **`telegram/bots/wallet_flow.py`** (new) — typing `wallet` (mirrors
   `profile`'s exact trigger convention) shows current balance in question/
   mark terms (never rupees), the nearest grant-expiry date if one is
   pending, and a real "💳 Recharge Wallet" button. Typing `recharge` (or
   tapping that button) opens an amount picker (₹20/₹50/₹100 + custom,
   ₹20 minimum) that creates a REAL Razorpay Payment Link — **the first
   live Razorpay API call this platform has ever made** — sends the
   payable URL in-chat, and polls for confirmation every 20s
   (`context.job_queue`, re-armed on restart the same way Test Mode's own
   expiry jobs are) crediting the wallet the instant payment clears. The
   two `_out_of_balance_text()` call sites in `exam_hub_bot.py`, and both
   of `test_flow.py`'s insufficient-balance messages, now carry this same
   real Recharge Wallet button instead of the old "coming very soon" text.
2. **Test Mode size tiers** (`test_flow.py`) — Pranav's explicit
   correction: no more mandatory full-paper test. Every sitting now offers
   **up to 3 size options — 20 / 50 / 100 marks** (a tier at or above the
   sitting's own total collapses to one "Full Paper (N marks)" option
   instead of a phantom oversized choice). A tier's actual question subset
   is built deterministically — the same 20-mark version of a given
   sitting is always the same questions, not randomized — using a 30:70
   MCQ:Descriptive split (the same ratio Pranav already confirmed for the
   still-unbuilt Custom Test's own assembly, reused rather than inventing
   a second competing ratio), taking the largest in-order prefix of each
   pool that fits its sub-target, with any leftover reallocated to
   whichever pool still has room. The wallet charge and test duration are
   both computed from the tier's REAL resulting marks (often slightly
   under the nominal target — can't split one question to hit an exact
   number), never the nominal tier value.
3. **Verified for real**: `smoke_test_wallet_flow.py` (new, 21/21) —
   **every Razorpay call in this test is explicitly mocked**
   (`unittest.mock.patch.object`), a real safety requirement discovered
   while writing it: this platform's actual live Razorpay keys are loaded
   into any process that imports `exam_hub_bot.py`, so an unmocked call
   here would have created real, live, payable Razorpay links on every
   test run. `smoke_test_test_flow.py` grew to 39 checks (was 32) covering
   the new tier-picker step and a full 27-sitting × tier cross-check
   (every real sitting's every tier produces a valid, non-empty,
   correctly-capped subset — 0 problems). Two more real test-cleanup bugs
   were caught and fixed (same FK-ordering lesson recurring a third time:
   `payments.telegram_user_id` also references `students`, on top of
   every other FK already known about — worth remembering as a durable
   pattern, not just a one-off). All 4 suites together: 122 checks passing
   (49 + 13 + 39 + 21).
4. **Deployed**: `1lavya-examhub` and `capranav-exam` restarted, confirmed
   clean.

**Still true**: no human has completed a real live payment through this
flow yet. Everything above is verified by driving the real code (including
the real DB writes and real message construction) with the Razorpay layer
mocked — genuine, meaningful verification, but not the same as an actual
UPI payment clearing. This remains the one gap only a human can close.

### 0.1d Update, 2026-08-16 (same day, later still) — real bugs from Pranav's manual test, plus full activity logging

Pranav manually tested a real run and reported 6 concrete issues/gaps. All
fixed/built, all tested (81 + 49 + 13 + 21 = 164 checks across 4 suites):

1. **Re-uploading over an already-uploaded question now warns first**
   ("You've already uploaded N page(s) — Overwrite / Add more pages")
   instead of silently accepting more on top. Overwrite deletes the old
   pages/files and resets; Append resumes the page counter from the real
   existing max, never resets to page 1.
2. **The literal `<code>` tags showing in the "no pages uploaded" message
   were a real bug** — `parse_mode=ParseMode.HTML` was missing on that one
   call while every sibling call had it. Fixed, and simplified the wording
   per Pranav's ask (plain quotes, not code-styled).
3. **`"pass"` is now a real, first-class way to decline a descriptive
   question** while in upload-collection state — marks it `skipped`
   (reusing the same status value MCQ skip already used), distinct from
   "forgot," clears the collection state, and is mentioned in the "no
   pages" message as the honest alternative to trying again.
4. **Submit Test now shows a confirmation summary first** (MCQs
   answered/blank, descriptive uploaded/passed/missing) with Confirm &
   Submit / Go Back — tapping the button no longer submits immediately.
5. **Timer reminders (5-min, 3-min) now exist** — genuinely didn't before.
   **The interactive grace-period offer, per Pranav's real design call**:
   at nominal time-up, the student is offered 2/3/5 extra minutes (or
   submit now) — **exactly once**, tracked (`test_sessions.grace_offered_at`/
   `grace_requested_minutes`), with a 60-second fallback that submits
   automatically if there's no response. Confirmed and fixed the real
   underlying concern: no data is actually at risk mid-upload either way,
   since every photo saves to disk/DB the instant it's sent — a question
   with real pages but no "done" now correctly counts as uploaded at
   submission (auto or manual), reconciled explicitly rather than relying
   on the student remembering to type "done" before time runs out.
6. **Comprehensive activity/analytics logging, built from scratch** — a
   new `test_activity_log` append-only event table (Pranav's own proposed
   "action + timestamp" shape, same architectural pattern this schema
   already uses for `wallet_ledger`/`report_flow_events`) capturing every
   question view, MCQ pick AND later change (with old→new value), upload
   page/done/pass/overwrite/append, reminders, the grace offer/choice, and
   submission — all timestamped. A **60-second no-activity heartbeat**
   (self-terminating design: each firing re-checks whether the student is
   still on that exact question before logging and rescheduling itself,
   so it naturally stops the instant they navigate away, no separate
   cancellation needed) guarantees at most 60 seconds of "what was the
   student doing" is ever unaccounted for, even if the phone dies mid-test.
   **Exact-point resume**: `test_sessions.current_seq_no` now tracks the
   literal question last shown, and resuming an in-progress test returns
   there specifically (not just "the first unanswered question"), restored
   correctly across a bot restart too. **Topic/subtopic tracking**:
   `test_questions.chapter_slug`/`topic_text` are snapshotted from the
   real content bank at test-build time, so every question is analyzable
   at concept level later, not just chapter level. The student-facing
   "activity" dashboard view Pranav described is NOT built — this is the
   data-capture layer only, a UI to browse it is a separate future piece.

**Two real bugs caught by the tests themselves while building this**, both
fixed: `_cancel_test_timers()` never cancelled the heartbeat chain (harmless
in practice — the heartbeat self-checks status and would have quietly
stopped on its next fire — but fixed properly rather than left relying on
that); `_new_test_id()` used second-precision timestamps, a real (if
unlikely) collision risk for two Start-Test calls within the same second,
now millisecond-precision.

**Deployed**: `1lavya-examhub` and `capranav-exam` restarted.

**Explicitly not built this round**: the 2-PDF result bundle (MCQ
Evaluation + Descriptive Evaluation, per Pranav's detailed spec) — a
separate, substantial piece (image-to-PDF conversion, precise page-break
merging) intentionally not rushed at the tail end of this already-large
round. That's the clear next deliverable.

### 0.2 What is NOT built yet — the actual next steps, in order

1. **A human-verified first real transaction** — the recharge flow exists,
   is deployed, and is verified with every Razorpay call mocked. No one has
   completed a real live payment through it yet. This is the single most
   important remaining gap, given there's no test-mode safety net (§9.5's
   "live keys, no test mode" decision) — a real recharge should be run and
   watched end-to-end by a person before trusting the pipeline generally.
2. **Cloudflare Tunnel + webhook** (optional upgrade, not a blocker —
   polling alone is a complete, correct v1) — still blocked on Pranav's own
   interactive `cloudflared login`; see §9.5.
3. **Extend identity/grant/wallet display to Study Hub + MyFiles Hub bots**
   — a student whose genuine first-ever platform touch is Study Hub doesn't
   see the welcome-bonus message at that moment today, and can't type
   `wallet` there either (see §0.1a's "known gap"). Same functions,
   different bot scripts — small, not done this round.
4. **Schedule `wallet.sweep_expired_grants()`** — built and tested, but not
   wired to any recurring job yet (no urgency: the earliest possible real
   expiry is 365 days out). A low-frequency `job_queue` task in one bot, or
   a standalone scheduled tool script, either is fine.
5. **The 3-PDF delivery bundle, AI evaluation (Phase 2), Student Customised
   Test, and milestone timer reminders** — see §0.1b's own "explicitly not
   built" list; all still true, nothing changed here.

### 0.3 Verification trail (so "done" isn't taken on faith)

- Both `wallet_ledger`/`payments` were queried directly against the live
  `platform.db` and confirmed to have **0 rows** before the schema reshape —
  not assumed safe, checked.
- The migration was run for real (`db.init_schema()` against the live
  `platform.db`, not a scratch copy) and the resulting table shapes were
  read back via `PRAGMA table_info` and confirmed correct.
- `smoke_test_wallet.py`: 21/21 checks passing, including the specific
  double-charge/double-credit idempotency cases, run and captured directly
  (not just written and assumed to pass).
- `health_check.py` and `file_index.py` were re-run after every structural
  change in this work, per `/CLAUDE.md`'s non-negotiable rule — same 16
  pre-existing, already-documented failures both times, nothing new.
- **Not yet verified**: the actual live Razorpay API itself (every call in
  every automated test is deliberately mocked, per §0.1c's safety note — no
  real payment has ever been completed through this pipeline).

### 0.4 A note on concurrent work in this exact area

While this session was working, **another concurrent session/process
modified `telegram/database/schema.sql` and `telegram/database/README.md`
in parallel** — adding `faculty_master`/`content_ingestion_log` table
definitions and a "Self-healing autostart" (Windows Task Scheduler) section,
both unrelated to Test Mode/billing. This is exactly the scenario
`/CLAUDE.md` §2's multi-agent warning describes. Handled by staging only
this session's own hunks/edits into git (verified via `git diff --cached`
before committing) and leaving the other session's uncommitted work
untouched in the working tree for it to commit separately. If you're a
future agent reading this and `schema.sql`/`database/README.md` look
different from what's described here, **check git log and read the current
file directly rather than trusting this section blindly** — same "don't
assume you're the only author" discipline `/CLAUDE.md` already asks for.

---

## 1. What's being built (as given by Pranav, 2026-08-15)

A new **Test Mode** inside the existing `1lavya-examhub` bot (`bots/exam_hub_bot.py`),
alongside its existing Descriptive/MCQ **practice** mode. Two kinds of test:

1. **Student Customised Test** — student picks one or more chapters and a target
   total marks; the bot assembles a real test (MCQ + descriptive) from the
   platform's existing tagged question pool and runs it as a timed exam inside
   the chat: MCQs answered by button tap (skip-and-revisit allowed, answers
   withheld until the test ends), descriptive answers submitted by photo/document
   upload against a specific question number, saved to a dedicated per-test
   folder on this PC.
2. **Pre-Designed Tests** — ready-made tests the student picks off a menu instead
   of building one.

**Phase 1** (this document's main focus) = the whole test-taking experience:
setup, timer, MCQ delivery, answer upload, submission, immediate MCQ scoring.
**Phase 2** = AI evaluation of the uploaded descriptive answer sheets, delivered
back to the student within ~30 minutes.

---

## 2. Locked decisions (confirmed with Pranav, 2026-08-15)

These three were genuine architecture forks — asked before writing anything
further, per this repo's standing practice for foundational decisions.

1. **Marks targeting = approximate matching.** A student picks a target total
   marks; the bot best-effort assembles a mix of MCQ + descriptive questions
   that lands close to it (tolerance band, e.g. ±10–15%), using a cleaned-up
   numeric marks field extracted at build time. The actual total is never
   promised exact — shown plainly on the Test Summary screen before the student
   confirms.
2. **Pre-Designed Tests = reuse of real sittings.** Every already-tagged real
   paper (MTP/RTP/PYQ, an `exam_type`+`year`+`set` grouping that came out of the
   `first_run/` pipeline) becomes a ready-made timed test as-is — real,
   ICAI-authentic, zero new curation. **Scope note, important:** this only
   applies where a "sitting" concept genuinely exists in the source data. Today
   that's **CA Inter Advanced Accounting only** (the content the `first_run/`
   pipeline built, Part I MCQ + Part II Descriptive per real paper). CA
   Foundation Quant/Accounting/Economics, CMA Law, and CA Inter Costing are all
   standalone per-chapter/per-topic MCQ banks with no real "one paper" grouping
   — they simply won't have Pre-Designed Tests until/unless equivalent
   full-sitting data exists for them. Don't force a fake grouping onto content
   that was never a real paper.
3. **AI grading = fully automated, no human gate, for v1.** Matches the "within
   30 minutes" ask literally — AI grades and the result reaches the student
   directly every time, with no faculty checkpoint in the loop. Quality control
   leans on the existing "Report Issue" mechanism after the fact (same posture
   the platform already takes with MCQs). A faculty audit *queue* (not a
   release gate) is worth adding later, same shape as the hybrid option that
   was raised — deferred, not rejected outright.

### 2.1 Billing (added 2026-08-15, second round — see §9 for full detail)

4. **Test Mode is paid, via the same wallet mechanism the schema has always
   intended** (`wallet_ledger`, first real wiring of it platform-wide).
   Confirmed pricing: **₹1 per 10 marks of assembled test content** (i.e. ₹10
   for a 100-mark test), charged **upfront when the student taps "Start Test"**
   (not at submission), applied **uniformly** to every test regardless of
   MCQ/descriptive mix or Custom/Pre-Designed.
5. **This charge covers the test-taking *facility* only — question delivery,
   upload collection, and converting the student's uploaded images into a
   properly ordered PDF. It explicitly does NOT include AI evaluation.**
   Evaluation pricing is a **separate, not-yet-decided charge** ("we will
   discuss separately" — Pranav, 2026-08-15) — never invent a number for it;
   Milestone 4 (Phase 2) cannot start until this is settled (§9.3).
6. **This also turns on billing for ordinary practice mode**, not just tests
   — the first time `wallet_ledger` goes from schema-only to actually wired
   in anywhere: **MCQ practice = ₹1 per 100 MCQs shown; Descriptive practice
   = ₹1 per 10 questions shown, flat regardless of marks.** This is a bigger
   scope increase than originally scoped for "Test Mode" alone — see §9.

---

## 3. Open decisions still needing Pranav's input (not blocking, but real)

Each of these has a recommended default in this document so the roadmap isn't
stuck, but none should be treated as locked the way §2 is.

| # | Question | Default assumed in this doc |
|---|---|---|
| 1 | Negative marking on Test-mode MCQs? | No — matches how practice-mode MCQs already work platform-wide |
| 2 | Can a student retake the same Pre-Designed Test? | Yes, unlimited, but each attempt is stored as its own row (Attempt 2, 3...) and **is charged again in full each time** (no discount for a repeat) — no blocking logic built for v1 |
| 3 | Is answer language restricted to English? | No restriction assumed; AI evaluation must handle Hindi/English-mixed handwriting — flagged as a real quality risk in §7 |
| 4 | Should uploaded answer-sheet images leaving this PC to an external AI vision API need explicit student consent/disclosure text? | Yes, a one-line notice shown before first upload — see §7's privacy note |
| 5 | ~~Is Test Mode free?~~ | **RESOLVED 2026-08-15 (round 2) — it's paid, see §2.1 and §9.** |
| 6 | Which AI provider/model for Phase 2 vision grading? | Not chosen in this doc — no AI integration exists anywhere in this codebase today (verified: zero references to any LLM API). This is greenfield, needs its own decision + API key + cost model before Phase 2 starts. |
| 7 | ~~Wallet balance scope~~ | **RESOLVED 2026-08-15 (third round) — `student_profiles.username`-scoped, see §9.4 #2 and §9.5.** |
| 8 | Does the existing "100 free MCQs/month" grant concept extend to Descriptive practice and/or Test Mode, or is a fresh test/descriptive question always pay-as-you-go from ₹0? | Still not decided — assumed pay-as-you-go with no free allowance for Descriptive/Test in this doc, since Pranav's pricing description didn't mention a free tier for either; flag for confirmation before M0.5 |
| 9 | ~~How does a student put money into their wallet?~~ | **RESOLVED 2026-08-15 (third round) — Razorpay, live keys, Payment Links via the bot. See §9.5 for the full mechanics, and note it's still blocked on the KYC website content (real business facts needed from Pranav).** |
| 10 | Recharge minimum? | **RESOLVED 2026-08-15 (third round) — ₹20.** |
| 11 | What happens to a student who tries to recharge before they have a 1LAVYA username? | Default assumed in this doc: the bot requires a username first (routes into `profile_flow.py`'s existing username-creation step), same precondition leaderboard-joining already has — no separate "pending credit" design needed. Not yet confirmed with Pranav as a locked decision, just the sensible default given §9.4 #2. |

---

## 4. High-level architecture

### 4.1 Where it lives in the bot
A new top-level fork at the very first `/start` question, ahead of today's
Mode picker:

```
/start
 ├─ 🎯 Practice Questions   → existing Mode → Course → Level → ... flow, unchanged
 └─ 📝 Take a Test          → NEW
      ├─ Student Customised Test
      │    Course → Level → Subject → Chapter multi-select → Target Marks
      │    → Test Summary → Confirm → (timed test runs)
      └─ Pre-Designed Tests
           Course → Level → Subject → pick a real sitting from a list
           → Test Summary → Confirm → (timed test runs)
```
Both branches converge on the same test-running engine once a question set is
assembled — the *only* difference between Custom and Pre-Designed is how the
question set gets built, never how it's delivered, timed, or graded. Build the
engine once.

### 4.2 New DB tables (proposed, `telegram/database/schema.sql`)

Same conventions already established platform-wide: append-only where it
matters, a complete audit trail (mirroring `report_flow_events`), `bot_id` on
every row since faculty-scoped bots run this too, nothing here duplicates
`course_catalog`/`human_id` — it references them.

```
test_sessions
  test_id            TEXT PRIMARY KEY   -- e.g. "T-{telegram_user_id}-{unix_ts}"
  bot_id             TEXT NOT NULL
  telegram_user_id   INTEGER NOT NULL
  test_kind          TEXT CHECK (test_kind IN ('custom','predesigned'))
  predesigned_ref    TEXT               -- NULL for custom; else a predesigned_tests.catalog key
  course, level, subject   TEXT
  chapters_json      TEXT               -- JSON list of chapter_slugs (custom only)
  target_marks       INTEGER            -- NULL for predesigned (marks are whatever the real sitting is)
  actual_total_marks INTEGER NOT NULL
  mcq_count, descriptive_count  INTEGER
  duration_minutes   INTEGER NOT NULL
  started_at         TEXT NOT NULL
  expires_at         TEXT NOT NULL
  status             TEXT CHECK (status IN (
                        'setup','in_progress','submitted',
                        'evaluating','evaluated','abandoned','expired'))
  submitted_at       TEXT
  mcq_score          INTEGER
  mcq_max            INTEGER
  descriptive_score  INTEGER            -- NULL until Phase 2 evaluation completes
  descriptive_max    INTEGER
  evaluated_at       TEXT

test_questions
  test_id            TEXT NOT NULL REFERENCES test_sessions(test_id)
  seq_no             INTEGER NOT NULL   -- 1..N, the question's number WITHIN this test, never the source paper's own qno
  qtype              TEXT CHECK (qtype IN ('mcq','descriptive'))
  source_id          TEXT NOT NULL      -- mcq_id or book_id
  human_id           TEXT
  chapter_slug        TEXT
  marks                INTEGER
  case_ref              TEXT            -- non-NULL if this MCQ shares a case scenario with other seq_nos in the same test
  status                 TEXT CHECK (status IN (
                            'pending','answered','skipped','flagged',
                            'not_uploaded','uploaded'))
  PRIMARY KEY (test_id, seq_no)

test_mcq_answers
  test_id, seq_no    -- FK into test_questions
  selected_option    TEXT
  is_correct         INTEGER            -- computed at grading time, never shown to student mid-test
  answered_at        TEXT

test_uploads
  upload_id          INTEGER PRIMARY KEY AUTOINCREMENT
  test_id, seq_no    -- FK into test_questions
  page_no            INTEGER NOT NULL   -- order within this question's answer
  file_path          TEXT NOT NULL      -- telegram/assets/exam_bot/Tests/uploads/{test_id}/{seq_no}/...
  telegram_file_id   TEXT
  mime_type          TEXT
  uploaded_at        TEXT NOT NULL

test_evaluations                        -- Phase 2
  test_id, seq_no
  ai_marks_awarded   REAL
  max_marks          INTEGER
  ai_feedback_text   TEXT
  confidence         TEXT               -- e.g. 'high'/'low'/'unreadable' -- see §7
  model_used         TEXT
  evaluated_at       TEXT

test_flow_events                        -- same "complete trail" discipline as report_flow_events
  event_id           INTEGER PRIMARY KEY AUTOINCREMENT
  test_id            TEXT
  telegram_user_id   INTEGER NOT NULL
  event_type         TEXT NOT NULL
  detail             TEXT
  created_at         TEXT NOT NULL

predesigned_tests                       -- catalog of which real sittings are offered as tests
  catalog_key        TEXT PRIMARY KEY   -- e.g. "CA-Inter-AdvAcc-MTP-May2026-Set1"
  course, level, subject   TEXT
  exam_type, year, set_no   TEXT
  title                TEXT NOT NULL
  total_marks           INTEGER NOT NULL
  duration_minutes        INTEGER NOT NULL
  mcq_count, descriptive_count  INTEGER
  active                          INTEGER NOT NULL DEFAULT 1
  generated_at                      TEXT NOT NULL
```

`predesigned_tests` is **generated by a script**, never hand-typed — same
discipline as `course_catalog`/every other catalog in this platform. The
generator groups `mcq_questions_extracted.json` + `book_questions_extracted.json`
records by (`course`,`level`,`subject`,`exam_type`,`year`,`set`), and only
emits a row where the grouping looks like a genuinely complete real paper
(see §7's "incomplete sitting" edge case) — anything that fails that check is
logged, not silently included.

### 4.3 Local storage

```
telegram/assets/exam_bot/Tests/uploads/{test_id}/{seq_no}/{page_no}_{unix_ts}.jpg
```
Gitignored in full (`telegram/assets/exam_bot/Tests/uploads/`) — this is both
binary content (repo rule: no binaries in git) and student personal data.
Never committed under any circumstance.

---

## 5. Flow design, step by step

### 5.1 Custom Test setup
1. Course → Level → Subject (auto-skip when the tenant only has one real
   option, same as practice mode today).
2. **Chapter multi-select** — checkbox-toggle inline keyboard + a "✅ Done"
   button, reusing the exact toggle pattern already proven in this codebase
   (`profile_flow.py`'s leaderboard join menu, MyFiles Hub's tag picker). Must
   require ≥1 chapter selected before "Done" is accepted. Chapters carrying a
   `LEGACY-*` `final_chapter` tag or genuinely unindexed topics are never
   offered here (see §7).
3. **Target marks** — a row of common presets (20 / 40 / 60 / 100) plus a
   "Custom amount" free-text option.
4. Bot assembles the question set (see §6 for the algorithm), then shows a
   **Test Summary** screen: chapters covered, MCQ count, descriptive count,
   actual assembled marks (vs. the requested target), estimated duration.
   Buttons: **Start Test** / **🔁 Regenerate** (fresh random subset, same
   parameters) / **Cancel**.

### 5.2 Pre-Designed Test setup
1. Course → Level → Subject.
2. A list of active `predesigned_tests` rows for that scope (title, marks,
   duration) — pick one.
3. Same Test Summary → Start Test / Cancel (no "Regenerate" — it's a fixed
   real paper).

### 5.3 Running the test
- On **Start**: insert `test_sessions` (`status='in_progress'`), insert every
  `test_questions` row, `started_at=now`, `expires_at = now + duration`.
  Send a rules message: timer behavior, "MCQs can be skipped and revisited,
  answers are hidden until the test ends," upload instructions for descriptive
  questions, and (if descriptive questions exist) the privacy notice from §7.
- Schedule `job_queue` reminders tied to `test_id` (50%/75%/90% elapsed, T-5min,
  and the expiry auto-submit) — same `run_repeating`/`run_once` mechanism
  `db.py`'s `schedule_heartbeat()` already establishes. **Critical:** these
  jobs must be re-armed from the DB on every bot startup (a sweep over
  `test_sessions WHERE status='in_progress'`), never assumed to survive a
  restart — `context.user_data` and in-memory `JobQueue` state are both wiped
  on restart, and this bot *will* restart (deploys, crashes, the known
  scale-readiness gap of no auto-restart-on-crash).
- **MCQ delivery:** one at a time by default, with **◀ Previous / ▶ Next / 📋
  Question Palette / 🏁 Submit Test** navigation. Tapping an option **stores**
  the answer but does **not** reveal correct/incorrect or the explanation
  (this is the one deliberate divergence from practice mode's instant-feedback
  rendering — needs its own render path, not a flag on the existing one, so
  the two behaviors can never leak into each other by a shared-code mistake).
  An answer can be changed any number of times before final submission.
- **Question Palette:** a grid of `1..N` buttons colored/labelled by status
  (✅ answered / ⚪ skipped / 🚩 flagged for review), tapping jumps directly to
  that question. Uses an index into `test_questions.seq_no`, never a literal
  payload, keeping `callback_data` short regardless of test size — the exact
  discipline this platform has already had to retrofit twice (Study Hub,
  Exam Hub chapter picker).
- **Descriptive questions inside a test:** shown read-only (question text,
  marks, topic) — **no "Show Answer" button** (unlike practice mode; the
  answer must stay hidden until evaluated). Instruction line: *"Type
  `upload` when you're ready to submit your written answer for this
  question."*
- **Upload flow:** student texts `upload` (a bot-wide trigger, same pattern as
  the existing `profile`/`report` triggers) → bot lists this test's
  descriptive question numbers (index-based buttons) → student picks one →
  bot enters an upload-collection state scoped to that `(test_id, seq_no)` →
  accepts one or more photos/documents, confirming each with "Page N saved —
  send another page, or type `done` to finish this question" → `done` (or
  picking a different question) closes collection, sets
  `test_questions.status='uploaded'`.
- **Submission** (manual "🏁 Submit Test" or automatic at `expires_at`):
  MCQs are graded immediately (`selected_option` vs. the real `correct_option`,
  never previously exposed). If the test has no descriptive component, the
  full result (score, right/wrong per question, explanations now revealed)
  is delivered instantly — reuse the same rendering the existing "I'm Done"
  summary and PDF report already establish. If it does have descriptive
  content: show the MCQ score now, mark `status='evaluating'`, tell the
  student *"Your descriptive answers are being evaluated — expect your full
  report within about 30 minutes"* and hand off to Phase 2.
- **Auto-submit at expiry:** the scheduled expiry job force-closes the test
  exactly like manual submission — any open upload-collection state for that
  test is also closed at that instant, no grace period (see §7's "late
  upload" edge case for why this is a hard cutover, not soft).

---

## 6. Marks-approximate assembly algorithm (Custom Test)

1. Filter the merged question pool to: `chapter_slug` in the selected set,
   `_content_owner`/`content_scope` matching this bot's tenant, **excluding**
   any `LEGACY-*`/unindexed-topic records (§7), excluding records already
   flagged `status='resolved'`... no — `mcq_issue_reports` triage isn't built
   yet, so this is a v2 refinement, not v1 (noting so it isn't forgotten).
2. Split into MCQ pool (clean numeric `marks`) and descriptive pool (numeric
   marks extracted from `marks_text` where parseable; RTP-style "no stated
   marks" records get a fallback estimate, e.g. the chapter's median marks
   among its own sittings — never treated as 0, never silently dropped).
3. Decide an MCQ:descriptive marks split ratio (needs Pranav's input — not
   decided in this doc; a reasonable default to propose is roughly matching
   ICAI's own real paper ratios, but flag this explicitly as a genuine open
   question, not a silent assumption).
4. Randomly sample from each pool toward the sub-targets, **keeping any MCQ's
   full `case_ref` group together as one atomic unit** — a case-scenario MCQ
   can never be pulled into a test without its sibling case-linked questions,
   since the narrative would otherwise reference facts nowhere in the test.
5. Stop once within tolerance (±10–15%) of the requested total, or once the
   filtered pool is exhausted — whichever comes first. **If the pool is
   exhausted before reaching even a reasonable fraction of the target** (a
   thin chapter, e.g. AS 1/AS 27), don't silently under-deliver: the Test
   Summary screen must say so plainly ("Only ~18 marks worth of content
   exists for these chapters") and let the student adjust chapters or accept
   the smaller total, mirroring how the Question Bank Book handles thin
   chapters honestly rather than padding or erroring.
6. "🔁 Regenerate" re-runs the sample with a fresh random seed, not the same
   subset — otherwise Regenerate would be a no-op.

---

## 7. Edge cases and risks (the actual point of this document)

### Content/assembly integrity
- **Case-scenario MCQs must never be split from their narrative** during
  marks-approximate sampling — see §6 step 4. This is the single most
  test-specific reuse of an already-known platform hazard (§ README's own
  "Case Scenario MCQs" note).
- **`LEGACY-*` and unindexed-topic questions must never enter a test** — they
  were deliberately excluded from the Question Bank Book for the same reason
  (no chapter exists in the current syllabus for them); a test built against
  the current syllabus taxonomy must apply the identical filter.
- **OP/PP duplicate detection still doesn't exist.** A Custom Test could
  unknowingly serve two near-identical questions (same underlying problem,
  renamed figures, across two sittings) as if they were independent — a known,
  named, still-open platform gap (see `/CLAUDE.md`'s Question Bank Book
  section). Not a blocker for v1, but worth stating rather than pretending
  it's solved.
- **Thin content pools** (§6 step 5) — some chapters simply don't have enough
  tagged marks to hit a student's requested total. Handle honestly, never pad.
- **"Sitting" grouping is not universal** — a Pre-Designed Test generator that
  assumes every `exam_type`+`year`+`set` grouping is a complete, real paper
  will be wrong for content that was never authored as a full sitting (CA
  Foundation Quant/Accounting/Economics, CMA Law, CA Inter Costing — all
  standalone chapter-wise banks). The generator needs an explicit
  completeness check (e.g. "does Part I + Part II sum to something close to
  a real paper's 100 marks, and does it actually originate from the
  `first_run/` sitting pipeline") before emitting a `predesigned_tests` row —
  never infer a fake "paper" from unrelated per-chapter content.
- **Tenant/content_scope isolation** — Test Mode on a narrowly-scoped bot
  (`capranav-exam`, `csarunchouhan`) must only ever draw from that tenant's
  `content_scope`, exactly like practice mode already enforces. A shared
  assembly function that forgets this filter would leak the full flagship
  pool onto a scoped bot — an easy, high-consequence mistake to make when
  building the shared engine described in §4.1.

### Session/timer/resilience
- **Only one active test per student at a time.** Starting a new test while
  one is already `in_progress` should offer Resume or Abandon-and-start-new,
  never silently create a second concurrent session.
- **Bot restarts mid-test are a certainty, not an edge case** — this platform
  has no auto-restart-on-crash guarantee and content changes require a full
  restart (both named in `/CLAUDE.md`'s scale-readiness callout). All test
  state must be resumable purely from `test_sessions`/`test_questions`/
  `test_mcq_answers` in the DB; `context.user_data` can never be the source
  of truth for anything that must survive a restart. On startup, sweep
  `in_progress` tests and re-arm their expiry/reminder jobs.
- **Abandoned tests need an explicit sweep**, not just a job that may or may
  not have survived — a periodic pass (same shape as `watcher_bot.py`'s
  polling loop) that finds any `test_sessions` row past `expires_at` and still
  `in_progress`, and force-finalizes it. Without this, a test whose expiry
  job was lost to a restart sits open forever.
- **"Timer" needs an honest UX framing.** Telegram bots cannot push a live
  ticking countdown into one chat bubble without constant message edits (rate
  limits, visual noise). The realistic version is: a freshly-computed "⏱ Time
  Remaining" line on every question render, plus milestone reminder messages
  (50%/75%/90%/T-5min) and a hard auto-submit at expiry. Set this expectation
  with the student up front rather than implying a literal live clock.
- **Duration for Pre-Designed Tests should be derived from the actually
  assembled marks** (the same `ceil(marks × 1.8)` minutes convention the
  Question Bank Book pipeline already uses per question), not blindly copied
  from "ICAI's real paper is 3 hours" — if our tagged corpus doesn't fully
  cover that sitting, 3 hours would be a misleading number for a shorter
  effective paper.

### Upload handling
- **Wrong-question mapping** — never infer which question an upload is for;
  always require the explicit picker before accepting files, exactly as
  designed in §5.3.
- **File validation** — reject non-image/non-PDF uploads with a clear message;
  Telegram's own bot-API download size ceiling (20MB) needs a graceful
  message, not a silent failure; a corrupted/unreadable image must be caught
  before Phase 2 ever treats it as gradeable input.
- **Multi-page ordering** — pages must be uploaded in order (or explicitly
  numbered); an out-of-order answer sheet risks the AI misreading a
  multi-page solution. Simplest v1 mitigation: pages are graded in upload
  order, and the "Page N saved" confirmation after each upload gives the
  student a chance to notice and restart that question if they uploaded out
  of sequence.
- **Late upload after expiry** — hard cutover, no grace window (§5.3). Any
  upload attempt after a test's `expires_at` should get a clear "this test has
  ended" message, not silently accepted or silently dropped without
  explanation.
- **Re-upload before submission** — allow replacing/adding pages for a
  question any time before the test is submitted, same "can change your mind"
  principle already applied to MCQ answers.

### Phase 2 (AI evaluation) specific
- **No AI integration exists anywhere in this codebase today** — confirmed by
  search. This is a from-scratch build: provider/model choice, API key
  management (`.env`, same pattern as `CF_EMAIL_API_TOKEN`), request/response
  handling, none of it reusable from elsewhere in the platform.
- **Marking rubric quality is the real risk, not the AI call itself.** Today's
  `answer_html` is a single model answer, not a structured rubric ("2 marks
  for X, 3 marks for Y..."). Grading quality against a free-hand answer will
  be meaningfully better with an actual rubric than with a bare model-answer
  comparison — this may need its own authoring pass per question, or an
  accepted-as-coarser holistic AI grade for v1. Flag honestly to Pranav before
  Phase 2 starts, don't discover it mid-build.
- **Illegible handwriting is a certainty at scale.** The pipeline needs an
  explicit "could not confidently read this answer" outcome (stored as
  `confidence='unreadable'` in `test_evaluations`) rather than ever silently
  guessing a low mark for something the AI couldn't actually read.
- **Per-question failure isolation.** One API failure/timeout must never fail
  an entire test's evaluation — retry that question, and if it still fails,
  deliver the rest of the report with an honest "this question's evaluation
  is delayed" note, never a guessed mark standing in for a real failure.
- **Cost, at real scale, is unbounded today.** Every descriptive question in
  every test is a paid vision-LLM call, and this platform has **zero working
  billing/quota enforcement anywhere** (the `wallet_ledger`/`payments` schema
  exists, nothing calls it) — this is already flagged as gap #3 in
  `/CLAUDE.md`'s scale-readiness callout, and Test Mode is the single most
  AI-cost-exposed feature this platform will have shipped. Worth an explicit
  conversation with Pranav about either a usage cap or accepting the exposure
  consciously before this goes out to more than a handful of students.
- **Data leaves the local machine for the first time.** Every prior feature
  on this platform keeps content and student data on the local PC (or sends
  branded emails via Cloudflare) — sending a student's handwritten answer
  sheet to an external AI vision API is a new category of data flow. Needs an
  explicit, visible disclosure to the student before their first upload (open
  decision #4 in §3), and Pranav should be comfortable with whichever
  provider's data-retention terms apply.
- **Rate-limiting/abuse is still unaddressed platform-wide** (gap #8 in
  `/CLAUDE.md`'s callout) — nothing stops a student from generating many
  tests back to back today, and Test Mode multiplies the consequence of that
  gap (AI cost, disk usage for uploads) far more than any prior feature has.
  With real billing now involved (§9), a paid test at least imposes its own
  natural throttle (a student needs wallet balance to spam tests) — worth
  noting as a side-benefit, not a substitute for real rate-limiting.

### Billing-specific (see §9 for the full mechanics)
- **No payment gateway exists anywhere in this codebase.** `payments` is
  schema-only; nothing has ever actually processed a UPI/card/gateway
  transaction on this platform. This is now a hard blocking dependency for
  Test Mode shipping at all, not a nice-to-have — see §9.4.
- **Insufficient balance at "Start Test"** must be caught *before* the test
  is created (never assemble-then-fail-to-charge) — a clear "top up ₹X to
  start this test" message, which today has nowhere to send the student
  (circular on the gateway gap above).
- **The charge is non-refundable on abandonment** per the locked timing
  decision (§2.1) — an assembled-and-started test is paid for whether or not
  the student finishes it. This should be stated to the student plainly
  before they tap "Start Test," not discovered afterward.
- **Exactly-once debit, never a double-charge.** A retry, a duplicate button
  tap, or a bot restart mid-charge must never debit the wallet twice for one
  test — needs an idempotency key on the `wallet_ledger` insert (e.g. keyed
  to `test_id`, same idea as `payments.gateway_txn_id`'s uniqueness
  constraint already in the schema for exactly this reason).
- **The balance is always `SUM(amount)` over `wallet_ledger`, never a stored
  mutable field** — this rule already exists in the schema's own comments for
  exactly the reason it matters here: a crash mid-debit must never corrupt a
  balance the way a mutable column could.

### Reporting/ops
- **Test attempts need Admin Portal visibility eventually** — a new Analytics
  tab mirroring the existing Faculty Comprehensive Report pattern. Not
  required for v1, but the schema above is written so it doesn't need
  reshaping later (every table already carries `bot_id`, `telegram_user_id`,
  timestamps).
- **Audit trail** — `test_flow_events` mirrors `report_flow_events`'s
  "complete trail" discipline (every prompt shown, choice made, retry) so a
  "the bot never gave me my score" support conversation is diagnosable from
  data alone.

---

## 9. Billing & Wallet Integration (added 2026-08-15, second round)

### 9.1 Confirmed pricing

| What | Rate | Charged when | Covers |
|---|---|---|---|
| MCQ practice | ₹1 per 100 MCQs shown | Per MCQ, as shown (existing `mcq_debit` event type, never actually wired in until now) | Just showing the question |
| Descriptive practice | ₹1 per 10 questions shown, **flat regardless of marks** | Per question, as shown (new `descriptive_debit` event type) | Just showing the question |
| Test Mode (Custom or Pre-Designed, MCQ or descriptive) | **₹1 per 10 marks of the assembled test** | Once, upfront, at "Start Test" (new `test_debit` event type) | Question delivery + upload collection + image→PDF assembly (§10) — **not** evaluation |
| Test evaluation (Phase 2) | **Not yet decided** | N/A | AI grading — separate conversation per Pranav, don't build M4 pricing until this lands |

### 9.2 Proposed currency mechanism (recommendation, not yet confirmed)

The schema's existing comment says `wallet_ledger.amount` is denominated in
"MCQ-credits, never rupees directly," and the 100-free-MCQs/month grant has
always implied **1 credit = 1 MCQ = ₹0.01**. All three of today's confirmed
rates reduce cleanly to that same exchange rate:

- MCQ practice: ₹1/100 MCQs = **1 credit per MCQ shown**
- Descriptive practice: ₹1/10 questions = **10 credits per question shown**
- Test facility: ₹1/10 marks = **10 credits per mark of assembled test**

Recommend locking **1 credit = ₹0.01** as the platform-wide exchange rate so
every debit type (existing and new) shares one currency and one `wallet_ledger`
table — no per-feature sub-ledgers. This is inferred from Pranav's three
numbers, not something he stated explicitly as an exchange rate — flag for a
one-line confirmation before building, since it's easy to get backwards.

### 9.3 Schema changes needed

- `wallet_ledger.event_type` CHECK constraint needs at least `'test_debit'`
  added (and `'descriptive_debit'` if MCQ/descriptive get distinct event
  types rather than sharing one). **Do not add an evaluation event type yet**
  — that pricing doesn't exist (§9.1's last row); adding the column/enum
  value early risks a real charge going out at an invented rate before
  Pranav has actually set one.
- `reference` on a `test_debit` row should be the `test_id`, giving a direct,
  auditable link from a wallet debit to the exact test it paid for — same
  discipline `mcq_id`-as-reference already establishes for `mcq_debit`.

### 9.4 What's actually blocking this from shipping

1. **No payment gateway integration exists anywhere in this codebase.**
   `payments` is schema-only (`gateway`, `gateway_txn_id`, `status` columns
   exist, nothing calls them). A student cannot put money into their wallet
   today by any means. **RESOLVED 2026-08-15 (third round): Razorpay,
   live keys** (see §9.5 for the full mechanics — Payment Links product,
   KYC website requirement, webhook/Cloudflare Tunnel plan).
2. **Wallet identity scope.** **RESOLVED 2026-08-15 (third round): scoped to
   `student_profiles.username`**, not `telegram_user_id` — one balance across
   every phone a student links, consistent with the leaderboard/profile
   identity model. Resolution for the "no username yet" edge case: **a
   recharge requires a username to already exist** (same precondition
   leaderboard-joining already has) — the bot prompts the student through
   `profile_flow.py`'s existing username-creation flow first, rather than
   inventing a pending-credit holding state for an identity that doesn't
   exist yet. `wallet_ledger` needs a schema change from `telegram_user_id`
   to `username` as its subject column (a real, non-trivial migration since
   the column is currently `NOT NULL REFERENCES students(telegram_user_id)`
   — needs its own careful pass, not a quick rename).
3. **No wallet balance UI exists yet** — a student needs to see their balance
   somewhere before "insufficient balance" messages make sense (a `/wallet`
   or "💰 My Balance" entry point, probably alongside the existing "profile"
   text-trigger convention).
4. **Recharge minimum. RESOLVED 2026-08-15 (third round): ₹20.**

### 9.5 Payment collection mechanics (locked 2026-08-15, third round)

Researched and decided across several rounds of discussion — captured here so
it isn't scattered across chat history.

**Gateway: Razorpay, live keys, kept in `telegram/.env`** (confirmed
gitignored via `*.env`/`.env` rules, never tracked in git history — verified
directly, not assumed). Pranav's explicit call, given per-transaction amounts
are small (₹1–2 for practice, ₹20 minimum for a recharge) — accepted the
tradeoff of no test-mode safety net in exchange for simplicity. Given that,
the build must compensate with **idempotent debit logic from day one** (a
retry/restart must never double-charge — same discipline `payments
.gateway_txn_id`'s uniqueness constraint already exists for), **manual
verification of the first several real transactions** rather than looping
automated test calls against the live endpoint, and no bulk/automated testing
against live Razorpay.

**Collection method: Razorpay Payment Links, shared via the Telegram bot** —
not a traditional website checkout. This is a first-class, Razorpay-
documented use case (they sell an equivalent WhatsApp Payment Links product
for exactly this "sell via a chat interface, no website checkout" shape) —
the bot generates a Payment Link via Razorpay's API for the recharge amount
and sends it to the student in-chat.

**A live website at `1lavya.com` is still required regardless of collection
method** — this is a separate RBI/Razorpay KYC requirement, not a technical
integration choice. Before Razorpay activates live payments, the domain must
show, live: Terms & Conditions, Privacy Policy, Refund & Cancellation Policy
(with a real timeline, e.g. "5–7 business days"), and real contact details
(phone/email/registered address). **Blocked on real business facts from
Pranav** (registered entity name/address, support phone, refund policy
terms, GST number if applicable) — this content must never be invented/
templated with placeholder facts, since it gates a live payment-collecting
business. Not yet built as of this writing.

**Payment confirmation: webhook via Cloudflare Tunnel.** Razorpay webhooks
cannot be delivered to `localhost` — only a public URL — and this platform
has no internet-facing server today (everything runs on Pranav's local PC).
Plan: Cloudflare Tunnel exposes a small local receiver under a subdomain
(e.g. `pay.1lavya.com`), separate from the `1lavya.com`/`www.` KYC page.
Two safety requirements once built: (1) **verify every webhook's
`X-Razorpay-Signature`** against the webhook secret before trusting it —
`pay.1lavya.com` is a genuinely public endpoint the moment it exists, so
skipping signature verification means anyone could POST a fake "payment
succeeded" event; (2) **don't rely on the webhook alone** — add a periodic
reconciliation sweep (poll Razorpay's API for recent successful payments,
cross-check against `wallet_ledger`) as a safety net against this PC's known
fragility (no auto-restart, the tunnel or bot could be down exactly when
Razorpay tries to deliver) — same "sweep" pattern already used elsewhere on
this platform (the down/up watcher, the test-expiry sweep in §7).
`cloudflared tunnel login`'s initial browser-based authorization is
inherently a Pranav-in-the-loop step (real OAuth consent, can't be
delegated) — everything after that (tunnel creation, the DNS CNAME record)
can be automated once that first login happens, either by hand (a 2-minute
dashboard step) or via a narrowly-scoped Cloudflare API token (Zone → DNS →
Edit, restricted to just the `1lavya.com` zone — never the account-wide
Global API Key) if automation is wanted later. Not yet built as of this
writing — no credential has been requested or issued for this.

**Sequencing, in order**: ~~KYC website~~ (resolved 2026-08-15 — Pranav
confirmed `1lavya.com` is already Razorpay-approved, no page build needed)
→ **build the Payment Links + wallet-credit flow against live keys with
careful manual verification** (in progress) → Cloudflare Tunnel + webhook
receiver → register the webhook in Razorpay's dashboard (generates the
webhook secret) → reconciliation sweep job.

**Built so far (2026-08-15, same round)**:
- `wallet_ledger`'s `username`-scoping migration (§9.4 #2) — done, verified
  against the live `platform.db` (both tables confirmed empty before the
  reshape, migration re-run and re-checked afterward — see
  `db.py`'s `_migrate_wallet_ledger_shape()`).
- `telegram/database/wallet.py` — balance/credit/debit primitives plus
  `debit_for_test()`/`credit_for_recharge()` helpers, all idempotency-key
  protected against double-charging on a retry/restart. Smoke-tested
  (`smoke_test_wallet.py`, 21/21 passing, DB logic only — no network call).
- `telegram/database/razorpay_client.py` — raw REST client (matches this
  codebase's `cf_email.py` style, no new dependency), `create_payment_link()`
  and `fetch_payment_link()`. **Deliberately not exercised against the live
  API by this session** — every call it makes is real money with live keys
  and no test-mode fallback, so it's built and reviewable but not yet
  triggered live.

**Not yet built**: the actual conversational recharge flow
(`telegram/bots/wallet_flow.py` — "recharge"/"top up" trigger, the
username-required precondition, sending the Payment Link, the polling loop
for confirmation), wiring it into any live bot's handler registration, and
the Cloudflare Tunnel/webhook (still blocked on Pranav's own interactive
`cloudflared login`). None of the live bot processes have been touched or
restarted by this work.

### 9.6 Auto-provisioned identity vs. the permanent-username promise (flagged 2026-08-16)

Pranav asked (2026-08-16) for a student's wallet identity to be silently
auto-set from their Telegram `@username`, with "he can anytime edit it once."
`profile_flow.py`'s existing username system is explicitly **permanent,
locked forever once claimed** — and says so directly to the student: typing
"profile" renders `Username: xxxxx (permanent, cannot be changed)` verbatim
(`profile_flow.py`'s `_profile_summary_text()`). Auto-setting a username and
then allowing one edit would make that on-screen text false the moment a
student who got auto-provisioned checks their profile.

**Resolution taken**: `identity.py` auto-provisions silently, exactly as
asked, but does **not** offer a one-time edit — the auto-set username is
bound by the exact same permanent rule as a manually-chosen one, no
exception carved out. This is the safer default (never promise something
untrue to a student) but is a real, deliberate deviation from Pranav's
literal ask, flagged here rather than silently decided. If a one-time-edit
exception for auto-provisioned usernames specifically is actually wanted,
that's a `profile_flow.py` change (a new "was this auto-assigned and never
confirmed?" flag, checked before permanently locking) — not built.

## 10. Answer-Sheet PDF Assembly & Delivery Bundle (added 2026-08-15, second round)

Per Pranav: the Test Mode facility charge (§9.1) explicitly covers converting
a student's question-wise uploaded images into **one properly ordered PDF**,
and the student receives **three separate PDFs** at the end — the Suggested
Answer PDF, the Question Paper PDF, and their own Answer Sheet PDF — via
email and/or Telegram, whichever they choose.

### 10.1 Technical approach (using libraries already proven elsewhere in this repo)

- **Image → PDF pages**: Pillow (`PIL.Image`) already used in
  `branding/build_brand_kit.py` — `Image.save(..., format="PDF",
  save_all=True, append_images=[...])` turns a sequence of photos into one
  multi-page PDF directly, no extra dependency.
- **Merging with native PDF uploads**: a student might upload an actual PDF
  (a scanned answer sheet) instead of photos for some questions — `pypdf`
  (already used elsewhere in this repo, e.g. the Question Bank Book's PDF
  conversion work) can merge that page-for-page with the Pillow-built image
  pages into one final document.
- **Ordering**: pages assembled strictly by `test_questions.seq_no` (the
  test's own question order, §4.2), then `test_uploads.page_no` within each
  question — never by upload timestamp alone, since a student might revisit
  and add a page to an earlier question after starting a later one.
- **A visible page header per question** (e.g. "Q{seq_no} — {human_id} —
  {marks} marks") stamped onto the assembled PDF, so the final document reads
  like a real, organized answer booklet, not a raw dump of photos — this is
  most of what the student is actually paying for.
- **Suggested Answer PDF** and **Question Paper PDF**: both are extensions of
  the existing single-question `send_pdf()` (`xhtml2pdf`/`pisa`, already
  proven in `exam_hub_bot.py`) — bundling every question's HTML (or every
  question+answer HTML) into one document instead of one PDF per question.

### 10.2 Delivery

Reuse the existing **channel-picker + confirm** pattern from `report_flow.py`
(Telegram / Email / Both) rather than building a new one, and
`database/cf_email.py`'s **already-existing attachment support**
(`send_email(..., attachments=[...])` takes `filename`/`content_bytes`
directly — confirmed while researching this doc, no new email capability
needed) for the email path. For Telegram delivery, three separate
`send_document()` calls (same pattern `myfiles_hub_bot.py`'s `send_single_item()`
already uses). All three PDFs delivered together as one bundle, not
dribbled out as each becomes ready.

### 10.3 Edge cases this adds

- **A test with zero descriptive questions** has no Answer Sheet PDF to
  build — only 2 of the 3 PDFs apply; don't send an empty/placeholder third
  file.
- **A question the student never uploaded anything for** — the Answer Sheet
  PDF should show that question's slot honestly (e.g. "No answer submitted
  for this question"), never silently skip the page and shift numbering.
- **File size** — a 100-mark test with many multi-page photo answers could
  produce a large merged PDF; both Telegram's document-send limit and
  Cloudflare Email's attachment size limit need checking against a realistic
  worst case before this ships, not assumed fine.
- **Corrupted/unreadable uploaded image** (§7) surfaces here concretely too —
  if a page can't be decoded into a PDF page at assembly time, the assembly
  step must degrade gracefully (skip that page with a visible placeholder
  note) rather than fail the entire bundle for one bad file.
- **This is a separate concern from Phase 2 AI evaluation**, worth stating
  explicitly since they're easy to conflate: the Answer Sheet PDF is built
  and delivered **before/independent of** any AI grading — it's part of the
  Phase 1 facility the student already paid for, and would ship even if
  Phase 2 evaluation didn't exist yet.

---

## 11. Phased build plan

Respecting Pranav's own Phase 1 / Phase 2 split, broken into buildable,
independently-smoke-testable milestones — each gets a real synthetic-data
smoke test + a full click-journey simulation before being trusted, matching
this platform's established discipline everywhere else.

| Milestone | Scope | Why this order |
|---|---|---|
| **M0** | DB tables (§4.2 + §9.3's wallet additions) + `uploads/` folder + `.gitignore` entry + `predesigned_tests` generator script | Pure scaffolding, testable in isolation, nothing bot-facing yet |
| **M0.5** | Wallet wiring — payment gateway/recharge mechanism (§9.4 #1), balance UI (§9.4 #3), identity-scope decision (§9.4 #2), MCQ/Descriptive practice debit wired in for real | **Genuinely blocking**, not optional groundwork — Test Mode cannot charge a ₹0 wallet with no way to add funds. This is now a bigger, separate piece of work triggered by "Test Mode," not a small side task. |
| **M1** | Pre-Designed Tests, **MCQ portion only** — timer, palette, auto-grading, instant result, **upfront wallet debit at Start Test** | Lowest-risk slice: proves session persistence, job re-arming after restart, the withheld-answer MCQ render path, and the real-money debit flow, before descriptive complexity is layered on |
| **M2** | Add descriptive delivery + upload collection to Pre-Designed Tests, **plus the image→PDF assembly + 3-PDF delivery bundle (§10)** — still Phase 1, no AI grading yet | Proves the upload flow, PDF assembly, and delivery pipeline against real content before Custom Test's harder assembly problem is added |
| **M3** | Custom Test builder — chapter multi-select + marks-approximate assembly (§6) | Reuses all session/timer/upload/billing/PDF machinery M1–M2 already proved; isolates the one genuinely new problem (assembly) to its own milestone |
| **M4 (Phase 2)** | AI evaluation pipeline — rubric strategy decision, provider integration, per-question failure isolation, 30-min SLA, auto-release (§2 decision 3), **evaluation pricing (§9.1's open row)** | Deliberately last — the highest-uncertainty, highest-cost, most-irreversible-if-wrong piece. **Cannot start until evaluation pricing is decided** — Pranav's own words, "will discuss separately." |
| **M5** | Reporting polish — Admin Portal Tests analytics tab, wallet/spend visibility in the Faculty/Admin reports | Polish once the core loop works end to end |

**Before M1 starts**, the open questions in §3 (especially #6 the AI provider,
#7 wallet identity scope, #8 free-allowance policy, #9 payment gateway) and
the MCQ:descriptive split ratio in §6 step 3 need actual answers from Pranav
— not because M1 touches AI, but because the schema, billing math, and UX
text written in M1 will already be shaped by some of those answers.
