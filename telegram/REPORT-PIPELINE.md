# Student Report Pipeline — Phase 2 of the platform roadmap

**Phase 2** of: Branding Kit → **Report Pipeline** → Leaderboard → Admin
Portal. Built, smoke-tested, documented — ready for Pranav's manual test.

> **Update, same day**: Pranav's own manual test (35+, later confirmed 67,
> answered questions on his real account) found the milestone never fired
> at all. Real bug — see "The milestone trigger bug" section below — now
> fixed, plus a full audit-trail table and a dashboard student-breakdown
> view were added in response. All still Phase 2, all deployed.
>
> **Update, same day, later still**: after actually receiving a report,
> Pranav found the conversation just stopped — no offer of the other
> delivery channel, no "continue or done" question, and the email-sent
> message didn't mention checking Spam. All fixed — see "Post-delivery
> flow" below. Also added, per his ask: a Student Master dashboard view,
> and a real explanation (not a bug) for a dashboard number that looked
> inconsistent — see "The Unique Visitors 'discrepancy'" below.

## What it does

Platform-wide (every bot, not per-bot — Pranav's explicit call), once a
student answers their **20th MCQ**, the bot offers a performance report —
accuracy, chapter-wise breakdown, time spent practicing — delivered by
Telegram, email, or both, per the student's choice. **No OTP anywhere**
(Pranav's explicit, repeated call) — contact info is collected via
**echo-and-confirm** instead: the bot repeats back what it heard and asks
Confirm/Re-type, catching the common typo class without OTP's friction.

## The milestone trigger bug (found by Pranav's own live test, same day)

`maybe_trigger_report_milestone()` originally required
`count == MILESTONE_THRESHOLD` exactly (`== 20`). That's only safe if a
student's count is guaranteed to pass through exactly 20 at some checked
moment — it silently breaks for anyone whose count was **already past 20**
at the moment this feature was deployed. Exactly what happened: Pranav's
own test account had 27 answered questions before Phase 2 even went live;
every answer after that only pushed the count further past 20, so the
prompt could never fire, no matter how many more questions he answered (67
by the time this was caught). Fixed to `count < MILESTONE_THRESHOLD:
return` (i.e. fires the first time the count reaches *or passes* the
threshold) — the "only once" guarantee was always handled separately by
the milestone-row-existence check right after, so this is strictly
correct, not a looser version of the old check. A permanent regression
test (`smoke_test_report_flow.py`'s `step7b`) now simulates exactly this
scenario — a synthetic student already at 25 with no milestone row —
before trusting any future change to this function again.

## Complete audit trail

Added the same day, per Pranav's ask after debugging the bug above:
"there should be a log maintained of the message sent and user name
collected... a complete trail." New `report_flow_events` table — one row
per conversational step (`milestone_prompt_sent`, `channel_chosen`,
`mobile_rejected`/`mobile_collected_pending_confirm`/`mobile_confirmed`,
the same three for email, `mobile_retry`/`email_retry`, `declined`,
`report_generated`/`report_generation_failed`,
`report_delivery_attempted`) with a `detail` field that can hold real
collected values. Exactly the data that would have made the milestone bug
above obvious immediately (a student with 30+ answers and zero
`milestone_prompt_sent` rows) rather than needing a live debugging pass.

## Student-breakdown dashboard

Also added the same day, per Pranav's ask: a new "Student Breakdown" card
on the existing admin dashboard (`http://127.0.0.1:8787/`) — a dropdown of
every exam/unified-kind bot, driving a chat-ID-wise table (attempted,
answered, correct, wrong, accuracy). New
`analytics.fetch_student_breakdown_by_bot()`, wired into the same
`fetch_all()` both the live and static dashboard already share — no new
endpoint, no new page. Verified two ways: a direct query against real data,
and a headless-Edge screenshot with the dropdown programmatically switched
to a real bot, confirming the table actually re-renders on selection
change, not just that the default option happens to look right.

## Post-delivery flow (added after Pranav's own report-flow test)

Testing with his real account (Telegram-only, mobile number given) surfaced
a real gap: after the PDF arrived, the conversation just stopped. Fixed,
all in `report_flow.py`:

- **If the student picked exactly one channel** (not "both"), the bot now
  offers the other one before ending: "Would you also like this report by
  email?" / "...on Telegram?" Accepting routes through the SAME
  echo-and-confirm contact collection as the original flow — a new
  `context.user_data["report_flow_upsell"]` flag tells the confirm-step to
  send through **only the newly-added channel** (`_deliver_report()` with a
  one-element set), never re-send what was already delivered. Declining, or
  having picked "both" originally (nothing left to offer), skips straight
  to the next step.
- **The conversation always ends with an explicit question** — "▶️ Continue
  Practicing" or "✅ I'm Done" — never just stops silently. "Continue
  Practicing" deliberately reuses the bare `restart` callback_data (no
  `report:` prefix) so it falls through to `button_router`'s own
  already-registered, already-tested "reset and show the entry screen"
  handler, rather than reimplementing it here.
- **The email-sent message now explicitly asks the student to check
  Spam/Junk** and mark it "Not Spam" — a first email from a new sender
  routinely lands there, and without this nudge a student who only checks
  Inbox would conclude nothing was ever sent.

`report_deliveries.channels_requested` changed meaning slightly as a
result: it now logs the exact channel(s) attempted **in that specific
delivery call** (`"email,telegram"`, or just `"email"`/`"telegram"` for a
later upsell delivery), not the student's original choice label — a
student who chose Telegram, then accepted the email upsell, now has TWO
rows: one `"telegram"`, one `"email"`. More accurate, and necessary once a
single milestone can produce more than one delivery event.

New smoke-test coverage (`step7c_upsell_and_wrapup_flow`): choose
Telegram-only → confirm mobile → verify exactly one `send_document` call →
verify the upsell offer mentions email → accept → provide+confirm email →
verify `send_document` is NOT called again (only the new channel, email,
gets sent) → verify two separate `report_deliveries` rows exist, correctly
labeled → verify the continue/done question appears → choose "I'm Done".

## Student Master dashboard

Also added per Pranav's ask: a new "Student Master" card on the dashboard —
one row per known student (Chat ID, Name, Mobile, Email, Faculty, Courses,
Last Seen), with a live text filter. New `analytics.fetch_student_master()`.
"Faculty"/"Courses" are derived from **real recorded activity** (which
bot(s) they've actually used, joined against `bots.json`→`tenants.json` to
resolve a faculty bot vs. a platform bot), not a bot's full possible
content scope — a student who's only ever touched a platform bot
(`1lavya-studyhub`/`1lavya-examhub`) shows as "Self Study (1LAVYA Shared
Pool)". A real, one-line data-quality fix landed here too: the same
course+level was showing up twice (once with a subject, once without,
since the exam-hub tables don't carry a `subject` column but
`study_hub_events` does) — now deduped, preferring the more specific,
subject-bearing version.

## The Unique Visitors "discrepancy" — investigated, not a bug

Pranav noticed Student Breakdown showed 14+2=16 students while the
dashboard's "Unique Visitors" stat showed 32, and asked why. Checked
against real data rather than assumed — **two genuinely different
populations, both numbers correct for what they measure**:

1. **Summing Student Breakdown's per-bot counts double-counts anyone
   active on more than one bot.** At the time of investigation, 2 students
   had MCQ activity on both `capranav-exam` and `csarunchouhan` — the true
   unique count across bots (15) was smaller than the naive sum (17).
2. **"Unique Visitors" counts a much broader population**: every distinct
   chat_id with *any* interaction (menu taps, searches, file downloads,
   not just MCQ attempts) across *all 8 bots* — including Study Hub and
   MyFiles Hub, which Student Breakdown never touches at all. Confirmed
   directly: 18 of the 33 total visitors at investigation time had never
   attempted a single MCQ.

Rather than leave this as an explanation buried in a chat log, added a
third, unambiguous stat tile — **"Unique MCQ-Attempters (all-time)"**
(`analytics.fetch_unique_mcq_attempters()`) — plus hover tooltips on both
visitor-related tiles, and a note directly on the Student Breakdown card
pointing at the new stat and at Student Master for the true per-student
view. The goal is that this specific confusion can't recur silently next
time either.

## Files

| File | What it is |
|---|---|
| `database/schema.sql` + `database/db.py`'s `_run_column_migrations()` | New `students` columns (`mobile_number`, `email_verification_method`, `mobile_verification_method`, `report_channel_preference`) and three new tables (`student_report_milestones`, `report_deliveries`, `report_flow_events`). SQLite has no `ALTER TABLE ADD COLUMN IF NOT EXISTS` (confirmed by testing — a real gap in an earlier draft of this work) — migrations are idempotent Python, not raw SQL. |
| `database/student_analytics.py` | `fetch_student_report_data()` — accuracy, time-per-question, chapter-wise breakdown, time-on-bot, all platform-wide for one `telegram_user_id`. `platform_wide_mcq_answered_count()` — the milestone-trigger's own count. |
| `database/analytics.py`'s `fetch_student_breakdown_by_bot()` | The dashboard's chat-ID-wise breakdown query, one bot at a time. |
| `tools/generate_student_report.py` | Renders the branded (via `branding/brand_kit.py`) HTML→PDF report. Both an importable `build_report_pdf()` and a standalone CLI: `python telegram/tools/generate_student_report.py <chat_id> [--since DATE \| --last-n N] [--out path.pdf]`. |
| `database/report_delivery.py` | Email sending (reuses MyFiles Hub's existing SMTP account/pattern) + the `report_deliveries` audit-log writer. |
| `bots/report_flow.py` | The conversational flow: milestone trigger, echo-confirm contact collection, final generate+send. Imported by `exam_hub_bot.py` (and, through it, `faculty_bot.py`'s unified bot). |
| `bots/smoke_test_report_flow.py` | Re-run any time this pipeline changes. See below. |

## Why "time on bot" isn't a simple session-end timestamp

First draft closed a session (`ended_at`) the moment the next one started —
**rejected before shipping**: the gap between sessions can be days, and
that design would count the entire idle gap as active practice time.
Instead, each session's real span is computed at query time as
`MAX(activity timestamp) − started_at`, from the actual
`mcq_attempts`/`descriptive_events` rows tied to that `session_id` — never
wider than what real recorded activity actually spans. See
`schema.sql`'s own comment on `exam_hub_sessions` for the full reasoning.

## A real bug already caught by testing, not just written correctly

The mobile-number regex's first draft anchored the country-code separator
in one spot (`+91 9876543210`) but real users often type the 5+5 Indian
grouping with an internal space too (`+91 98765 43210`) — the first
version rejected that. Fixed by stripping spaces/hyphens *before* matching
a clean 10-digit pattern, rather than trying to encode every separator
position into the regex. Caught by testing a realistic range of formats,
not by inspection — the smoke test now covers this range permanently.

## The exact bug class from 2026-08-10, checked for deliberately this time

`exam_hub_bot.py`'s `button_router` was registered with **no pattern at
all** (matched every callback) — harmless only because nothing else
claimed any `callback_data`. Adding `report_flow`'s own callbacks
(`report:`/`reportconfirm:`) would have been **silently swallowed** by
that unscoped handler running first, finding no matching branch, and doing
nothing — exactly the "next"/"restart" bug found and fixed once already
this session (2026-08-10, `faculty_bot.py`). Fixed *before* shipping this
time: `button_router` now has an explicit pattern, `report_flow`'s handler
is registered separately, and `smoke_test_report_flow.py`'s Step 6 checks
every real callback string matches exactly one handler pattern —
permanently, not just today.

## Running the smoke test

```
python telegram/bots/smoke_test_report_flow.py
```

Seven steps: schema migration idempotency; `student_analytics` sanity
against a real student; real PDF generation through the actual `xhtml2pdf`
engine; email message structure (subject, PDF attachment — **not** a live
send, real SMTP credentials aren't configured in this dev environment,
verify a real send manually once they are); mobile/email validation
against realistic and invalid inputs; callback-pattern non-collision; and
a **full conversational-flow simulation** against a synthetic test student
(a `telegram_user_id` far outside any real range) — reaching exactly 20
answered questions, choosing "Both", typing/confirming a mobile number,
typing/confirming an email, and verifying the milestone record, the
student's stored contact fields, and a `report_deliveries` row all end up
correct. Synthetic rows are always cleaned up afterward, even on failure.

The one thing this environment genuinely cannot test: a real email
actually arriving (SMTP creds aren't configured here) — the smoke test
proved the message is *built* correctly and that a real SMTP failure is
*handled* gracefully (caught, logged, doesn't crash the bot — verified for
real when the mock credentials predictably failed auth during Step 7),
but an actual successful delivery needs verifying against Pranav's real
`telegram/.env` credentials.

## What's deliberately not built yet

- The 30-question leaderboard prompt (Phase 3 concept — note the actual
  Phase 3 leaderboard system, built 2026-08-11, ended up scoped as
  join-up-to-5-boards rather than a single 30-question prompt; see
  `telegram/LEADERBOARD-SYSTEM.md`).
- Admin-triggered/scheduled reports beyond the CLI (`generate_student_report.py`
  already supports being run by hand for any chat_id — a scheduled or
  admin-portal-triggered version is Phase 4 scope).
- The `--since`/`--last-n` report criteria are fully built and tested at
  the query/PDF layer, but the automatic 20-question milestone flow always
  sends an all-time report — a "give me last 100 questions" self-service
  option isn't wired into the conversational flow itself yet, only the CLI.

## Email backend switched to Cloudflare Email Service + on-demand trigger added (2026-08-11)

Two more of Pranav's asks, same day:

**1. On-demand trigger.** Just like `profile_flow.py`'s "profile"/"change
profile" trigger, a student can now type **"report", "analysis", "email",
or "mail"** (exact phrase, case-insensitive) to any bot — Study Hub, Exam
Hub, or a unified faculty bot — at any time, not just at the 20-question
milestone. The bot asks for confirmation, then funnels into the exact same
channel-picker/contact-collection/delivery pipeline the milestone already
used (`report_flow.start_report_flow_on_demand()`, sharing
`_send_channel_picker()`/`_handle_channel_choice()`/`_finalize()`/
`_deliver_report()` with the milestone path — no duplicated logic). Works
even for a student who's never hit 20 questions — `_finalize()` already
tolerated a missing milestone row (a `WHERE` clause matching zero rows is
a harmless no-op), so no separate code path was needed. Wired into
`study_hub_bot.py` for the first time in this pass (it never imported
`report_flow.py` before — Study Hub previously had no report-related
logic at all).

**2. Cloudflare Email Service replaces Gmail SMTP for report emails.**
Pranav provided real `CF_EMAIL_API_TOKEN`/`CF_EMAIL_ACCOUNT_ID` credentials
(`telegram/.env`) and confirmed via AskUserQuestion: 1lavya.com is already
onboarded for Email Sending in the Cloudflare dashboard; each bot gets its
own dedicated **unmonitored** sending address on **one shared domain**
(`studyhub@1lavya.com`, `examhub@1lavya.com`, `csarunchouhan@1lavya.com`,
`capranav-study@1lavya.com`, `capranav-exam@1lavya.com` — Cloudflare's
onboarding/verification is per-domain, so this needed zero extra
Cloudflare setup per bot, unlike literal per-bot subdomains); `support@`/
`admin@1lavya.com` are real, already-monitored mailboxes.

New `telegram/database/cf_email.py` — raw REST client for
`POST /accounts/{account_id}/email/sending/send`. `report_delivery.py`
rewritten: `send_report_email()` now takes a `bot_id` (threaded through
`report_flow.py`'s entry points via `context.user_data["report_flow_bot_id"]`,
set once when the milestone/on-demand flow starts and read back inside
`_deliver_report()`), resolves that bot's own `from_email` from
`bots.json` (`resolve_from_address()`, graceful fallback to
`reports@1lavya.com` for any bot with none configured), and sends a fully
1LAVYA-branded HTML email (`build_report_email_html()`) — **not** the
faculty's own branding, even when sent via a faculty's bot, matching the
existing precedent that platform-generated artifacts (the PDF's own
"Powered by 1LAVYA" caption) always carry 1LAVYA branding regardless of
tenant, since 1LAVYA built and operates the report feature itself. New
`telegram/branding/brand_kit.py`'s `render_email_footer_html()` — every
report email's footer states the mailbox is unmonitored and gives the two
real contact addresses Pranav specified: **support@1lavya.com** for any
issues, **admin@1lavya.com** for "getting your own Exam or Custom Bot
created" (his exact wording). Deliberately **text-based, not the logo
`<img>`** the dashboard/PDF header use — email clients (Outlook
especially) have much less reliable `data:`-URI image support than a
browser or `xhtml2pdf`, so the email template never depends on an image
rendering at all.

`myfiles_hub_bot.py`'s own OTP email is **unchanged** — still Gmail SMTP,
not migrated in this pass (not asked, out of scope).

**Verified for real, not just structurally**: after the smoke test's
purely-structural HTML/address checks passed, ran one live send through
the *actual* production code path (`report_delivery.build_report_email_html()`
+ `resolve_from_address()` + `cf_email.send_email()`, no separate ad hoc
script) to Pranav's own email — confirmed delivered
(`cf_email`'s response: `"delivered": ["pranavaiversion@gmail.com"]`,
real `message_id`). `smoke_test_report_flow.py` itself never fires a real
network call (no `load_dotenv()` in that script, by design, so
`cf_email.is_configured()` is deliberately `False` during automated runs —
confirmed the email-delivery-failure path inside `_deliver_report()` is
caught and logged gracefully rather than crashing, exactly as intended)
— gained a new Step 7d covering the full on-demand conversational flow
end-to-end (trigger-phrase matching, confirm, channel picker, delivery
with **zero** prior MCQ activity, and the "declined" branch). All 5 bots
that import `report_flow.py` restarted, confirmed clean startup logs.

## Real live bug found + fixed same day: unquoted From-header display name

Pranav reported a real failure minutes after this went live: "report has
been generated but delivery to one or more channels failed" on the
`csarunchouhan` bot. Investigated via the actual data, not guessed --
`report_deliveries` (delivery_id 40) had the exact Cloudflare error
logged: `HTTP 400 ... "email.sending.error.email.invalid"`, **and** a
`telegram.error.TimedOut` on the same delivery (two independent failures
at once -- see the second section below).

**Root-caused by isolation, not assumption**: reproduced the exact
failure through the real production code path first, then tested `from`
and `to` addresses independently (both individually succeeded) before
finding the actual culprit -- csarunchouhan's own `bots.json`
`display_name`, `"CS Arun Chouhan (Study + Exam Practice, one bot)"`,
contains a comma and parentheses. `cf_email.py`'s original
`f"{from_name} <{from_email}>"` is only valid RFC 5322 syntax for a
display name with no special characters -- Cloudflare's From-header parser
rejected the unquoted version outright. Every other bot's display name
(`"1Lavya Exam Hub"`, `"CA Pranav -- Study Bot"`, etc.) is plain enough
that this never surfaced anywhere else -- a latent bug specific to one
bot's own metadata, not something the original structural smoke test
(which never exercised `csarunchouhan`'s real display name) could have
caught.

**Fixed** with Python's own `email.utils.formataddr` (the stdlib's
correct RFC 5322 quoting/escaping -- only quotes when actually needed,
never hand-guessed again) via a new `cf_email.build_from_header()`
helper. **Verified with a real send** through the exact failing
from/to combination -- confirmed delivered. **Permanent regression test**
added to `smoke_test_report_flow.py`'s Step 4: asserts csarunchouhan's
display name still has the comma/parens that caused this, and that
`build_from_header()` correctly quotes it (and correctly does NOT quote a
plain name, since over-quoting isn't the goal either).

**Second, independent issue on the same delivery**: `send_document`
(Telegram) hit a genuine `httpx.ReadTimeout` on a ~32KB file -- a one-off
network blip, not a code bug (the file is small; nothing points at a
systemic cause). Added a bounded retry (one retry, 2s backoff) in
`_deliver_report()`'s Telegram branch, but **only** for the transient
`TimedOut`/`NetworkError` exception classes -- any other exception (bad
chat_id, etc.) still fails immediately rather than wasting time retrying
a non-transient error.

All 5 bots restarted with both fixes; `smoke_test_report_flow.py` re-run
clean.

## Real UX bug found + fixed same day: re-asking for contact info already on file

Pranav reported: "even after sharing the mobile number and email id once,
if I again ask for report than it again asks for my number/email... does
not the bot check with existing database whether the mobile and email id
are present and not ask and directly send." Confirmed -- it didn't.
`_handle_channel_choice()` unconditionally asked for mobile/email on
EVERY report request, ignoring whatever was already confirmed and stored
on `students` from a previous request.

**Fixed** in three places, all in `report_flow.py`: a new
`_existing_contact()` helper checks `students.mobile_number`/`.email`
before ever entering an `AWAITING_*` state.
- `_handle_channel_choice()`: if everything the chosen channel(s) need is
  already on file, skip straight to `_finalize()` -- zero prompts, exactly
  Pranav's ask ("directly send and then confirm its went").
- The "both" path's mobile→email handoff (inside `_handle_confirm_choice()`):
  previously always asked for email next after confirming mobile, even if
  email was already on file too -- now checks first.
- The post-delivery upsell (`_handle_upsell_choice()`, "would you also
  like this by email/Telegram too?"): now also checks first, since a
  student could have set the other channel's contact info via the
  "profile" menu since the original choice.

A student who wants to CHANGE a stored value still can, any time, via
"profile" → Email/Mobile (`profile_flow.py`) -- this flow only ever asks
when something is genuinely missing, never re-verifies something already
confirmed.

New smoke-test coverage (`step7e_reuses_existing_contact_info`): a
synthetic student with BOTH mobile and email already on file requests a
report via "both" -- asserts zero `AWAITING_*` state is ever entered, the
confirmation message says "saved" (not asking for input), a
`report_deliveries` row is created, no `mobile_collected`/`email_collected`
events appear in the audit trail, and a new `used_existing_contact_info`
event is logged instead. Also covers the "email"-only choice with email
already on file. All 5 bots restarted; full smoke test re-run clean.
