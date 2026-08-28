# BROADCASTING.md — plan for a safe, automated, daily student-engagement broadcast

**Status: PLAN ONLY, not yet built or scheduled.** Nothing in this document has been
registered as a Windows Task Scheduler job. Broadcasting to real students unattended,
every day, with no human in the loop per-send, is exactly the kind of outward-facing,
hard-to-reverse action `/CLAUDE.md` §11's own standing rule calls out for a
confirming question before proceeding — so this file is the proposal to review, not
a fait accompli. See §7 for exactly what happens once you approve it.

This extends, and is meant to eventually REPLACE running-by-hand, the one-off scripts
already built 2026-08-18 (`send_mcq_nudge_broadcast.py` / `_progress_` / `_congrats_`)
and 2026-08-26 (`send_streak_engagement_broadcast.py`) — see `/CLAUDE.md` §11 and
those scripts' own docstrings for that history. Nothing about those 4 scripts breaks;
this plan folds their logic into one governed daily process instead of 4 separate
manually-triggered ones.

---

## 1. Why a single daily ORCHESTRATOR, not 4+ separate cron jobs

The single biggest spam risk isn't any one script — it's **multiple independent
scripts each deciding a student is "theirs" on the same day**. `send_mcq_progress_
broadcast.py` and `send_streak_engagement_broadcast.py`, for example, could BOTH
legitimately want to message the same student (1-10 MCQs answered AND on a 2-day
streak) if run as separate, uncoordinated cron entries.

**Plan: one script, `send_daily_engagement_broadcast.py` (new, not yet built), runs
once a day, computes every segment in ONE pass per student, and picks exactly one
message per student via a single priority order (§3).** This is the only way to
structurally guarantee "no overlap, no more than one message per chat_id" for an
unattended daily job — a promise that's easy to keep by hand for one manual run, and
easy to accidentally break the moment more than one script runs on its own timer.

---

## 2. Proposed schedule

**Daily at 7:30 PM IST (19:30).**

| Existing job | Time | Gap to 19:30 |
|---|---|---|
| 1LAVYA Bots - Health Check | every 30 min | N/A (harmless, always-on) |
| 1LAVYA Platform Backup | 03:30 IST | 16h clear |
| 1LAVYA Log Rotation | hourly | N/A (cheap no-op most runs) |
| 1LAVYA Activity Log Purge | 04:00 IST | 15.5h clear |
| Leaderboard broadcaster | 23:11 IST | 3.5h clear |
| Day End Faculty Reports | 23:50 IST | 4.3h clear |

**Reasoning**: 7:30 PM is after typical school/college/coaching hours for CA/CS/CMA
students, while there's still real evening study time left that day to act on the
nudge — a message that lands at 3:30 AM or during class hours gets ignored by
construction, which itself would look like "no interaction" and could wrongly trip
the stale-suppression rule in §4. Comfortably clear of every write-heavy job above
(backup/log rotation/purge), so no DB-contention or backup-consistency risk. A single
constant in the script (`SEND_HOUR_IST`), trivial to change if you'd rather test a
different time.

---

## 3. Segment taxonomy — one priority-ordered decision per student, per day

Computed fresh every run from `exam_hub_mcq_attempts` + `students` (same "roll up in
Python by 1LAVYA username, real students only, admin/smoke-test excluded" pattern
every broadcast script already uses) — **first match wins, so every real student
lands in exactly one bucket or none at all.**

| # | Segment | Condition | Message theme | Cadence-appropriate for daily? |
|---|---|---|---|---|
| 0 | **Suppressed** | Stale-response rule tripped (§4) OR explicit "Not Interested" tap | *(no message sent)* | — |
| 1 | **Not started** | Interacted with an exam-capable bot, zero MCQ attempts ever | "Here's what's ready for you" (reuses `send_mcq_nudge_broadcast.py`'s template) | Yes, but see §4 — this is the segment most likely to go stale fastest |
| 2 | **Streak active** | Current streak ≥ 2 days, last practiced today/yesterday | Celebrate + protect the streak | Yes — status changes daily by nature |
| 3 | **Lapsed regular** | Practiced on ≥ 2 distinct days ever, last practiced 1-3 days ago | Win-back, "you were regular" | Yes |
| 4 | **General / no streak** | Any other student with ≥ 1 MCQ attempt | "Build a study habit" | Yes, but lowest urgency — see §6 on whether this needs a lighter touch (e.g. every 2nd day instead of daily) |

**Deliberately NOT part of the daily loop**: the `>10 MCQs` milestone congrats
(`send_mcq_congrats_broadcast.py`) and the `welcome_bonus` grant announcement. Both
are **one-time, threshold-crossing events**, not a daily state — sending "you've
crossed 10 MCQs!" every day forever is exactly the spam pattern you're trying to
avoid. Recommendation: keep these as **event-triggered** (fire once, the moment a
student's count crosses a round number — 10, 25, 50, 100 — tracked by checking
whether that student already has a `mcq_milestone_congrats` delivery row referencing
that specific milestone before sending another), run on the SAME daily cron but as a
separate, low-volume pass, exempt from the "one message per day" cap since it's
rare and additive news, not routine engagement pressure. Flagged as a **§8 open
question** — happy to fold it in if you'd rather.

---

## 4. Anti-spam: the stale-attempt cutoff you asked for

**Rule: after `STALE_THRESHOLD` (default 4, your requested 3-5 range midpoint)
consecutive daily broadcasts to a student with ZERO real engagement, stop sending —
automatically, no manual list-pruning required.**

"Zero real engagement" on a given delivery means BOTH of these are true:
- `broadcast_deliveries.interacted_at IS NULL` for that delivery (no button tap), **AND**
- No `exam_hub_mcq_attempts` row exists for that student with `shown_at` after that
  delivery's `sent_at` (didn't quietly go practice anyway without tapping the button —
  a real, generous check: a student who ignores the button but opens the bot and
  practices on their own is correctly NOT counted as unresponsive).

**Computed live, every run, from the existing `broadcast_deliveries` +
`exam_hub_mcq_attempts` tables — never a stored "suppressed" flag.** This matches
this platform's own established discipline (wallet balance is `SUM(ledger)`, never a
mutable column; `human_id` idempotency is re-verified, never assumed) — a live
computation can't drift out of sync with reality the way a cached flag can. Concretely:
look at each candidate student's last `STALE_THRESHOLD` daily-broadcast deliveries
(any segment/category, `status='sent'`, most recent first); if every single one is
"zero real engagement" as defined above, skip them this run.

**Explicit opt-out is separate and stronger**: the "🔕 Not Interested" button
(`report:bcastdismiss:<campaign_id>`, already wired and already logs
`interaction_type='dismissed'`) marks suppression **immediately**, not after
`STALE_THRESHOLD` misses — a student who actively says no shouldn't get 3 more
nudges first. The daily script's eligibility query excludes anyone whose most recent
broadcast delivery (any category) has `interaction_type='dismissed'`.

**Automatic re-activation, no admin action needed**: because suppression is computed
live, not stored, the moment a suppressed student answers a real MCQ or taps a button
on ANY message (including a future non-broadcast interaction), their delivery-history
window naturally changes and they become eligible again on the next run. Nothing to
reset by hand. (A student who explicitly dismissed can still re-enter once they
generate a fresh, non-dismissed interaction — e.g. they come back and practice on
their own, or interact with the bot in some other tracked way.)

**New, small, append-only audit table** (proposed addition to `schema.sql`, mirrors
the ledger/audit-trail pattern this platform already uses everywhere — `wallet_
ledger`, `admin_actions`, `report_flow_events`):

```sql
CREATE TABLE IF NOT EXISTS broadcast_suppression_events (
    event_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id     INTEGER NOT NULL,
    reason                 TEXT NOT NULL,   -- 'stale_streak' | 'explicit_dismiss'
    detail                   TEXT,          -- e.g. 'last 4 deliveries, campaign_ids 41,44,47,52'
    created_at                 TEXT NOT NULL
);
```

Purely a visibility/audit log for the Admin Portal (so you can SEE who's being
skipped and why, without it ever being the thing the skip decision itself trusts) —
matches the "compute live, log for humans" split this platform already uses for
wallet grant sweeps.

---

## 5. Other safety rails

- **One message per identity per calendar day, hard guarantee.** The orchestrator
  assigns each 1LAVYA-username identity to at most one segment (§3), then sends to
  every linked `chat_id` under that identity — never more than one segment's worth
  of messages, ever, in one run. As a second, independent safety net (in case of an
  accidental manual re-run the same day), the send loop also skips any `chat_id`
  that already has a `broadcast_deliveries` row with today's date before sending —
  belt AND suspenders, not just one check.
- **Circuit breaker on the eligible count.** If the total number of students to
  message in one run is wildly outside the historical range (e.g. jumps from ~60 to
  500+ overnight — likely a query bug, not real growth), the script aborts BEFORE
  sending and DMs an alert via the existing `watcher_bot.py` plumbing, the same
  "alert on any phase failure" pattern the backup job already uses. Threshold
  configurable, defaults conservative given the platform's real current ~65-student
  scale.
- **Per-send delay** (0.35s, same as every existing broadcast script) to stay
  comfortably under Telegram's rate limits.
- **Dry-run-first, always.** The script always computes and logs the full plan
  (who, which segment, which bot) before touching the network — `--live` is required
  explicitly, exactly like every broadcast script today. For the SCHEDULED run
  specifically, propose: the Task Scheduler job always calls `--live`, but the script
  itself writes its full per-run plan to `database/run/logs/daily_broadcast.log`
  BEFORE sending anything, so there's always a paper trail to review the next
  morning even though no human approved that specific night's list in the moment.
- **Fails loud, not silent.** Any crash, 0-sends-when-N-expected, or an unusually
  high failure rate triggers the same admin DM alert as every other scheduled job on
  this platform (`CRONJOBS.md` §1's pattern) — logged, not swallowed.
- **Buttons unchanged**: every message keeps the already-proven `Continue Practicing
  / Show Chapter List / Not Interested` markup (`broadcast_sender.
  get_continue_practicing_button_markup()`) — no new callback registrations, so this
  can't introduce the callback-collision bug class this platform has hit 3+ times.

---

## 6. What still needs building (not done yet)

1. `telegram/tools/send_daily_engagement_broadcast.py` — the consolidated
   orchestrator (§3's priority order + §4's suppression check), built by combining
   the already-proven logic in `send_mcq_nudge_broadcast.py` and
   `send_streak_engagement_broadcast.py` rather than rewritten from scratch.
2. The `broadcast_suppression_events` table (§4) — one `CREATE TABLE IF NOT EXISTS`
   addition to `schema.sql`, applied idempotently like every other table here.
3. A smoke test (`smoke_test_daily_broadcast.py`, following this platform's own
   "every feature ships with a re-runnable smoke test" rule) — covering: the
   priority order never double-assigns a student, the stale-suppression rule
   correctly excludes a synthetic 4-miss student and correctly re-includes one who
   engaged on their 3rd, the explicit-dismiss exclusion, and the circuit breaker.
4. Registering the actual Windows Task Scheduler job (§7) — the one step this
   session should NOT do without your explicit go-ahead, per this file's own opening
   note.

---

## 7. Rollout sequence (same discipline as every other phase on this platform)

1. Build the orchestrator + suppression table + smoke test (items 1-3 above).
2. `--dry-run` against real `platform.db` — review the exact plan (who, which
   segment, why) with you before anything is sent.
3. `--preview` — sample of each segment's message sent to your own chat only, no
   campaign rows, no real students touched.
4. **You confirm** the schedule, thresholds, and wording are right (§8 has the open
   parameters to confirm).
5. Only then: register the actual Task Scheduler job, add it to `CRONJOBS.md`'s
   table (§1 of that file) the same day, verified the same way every other job in
   that file was (`Get-ScheduledTaskInfo`, a real triggered run, `LastTaskResult: 0`).
6. First few live nights: manually check the log + Admin Portal the next morning
   before trusting it to run fully unattended long-term.

---

## 8. Open questions to confirm before I build this

- **Send time**: 19:30 IST as proposed, or a different hour?
- **Stale threshold**: 4 consecutive non-engaged sends (your 3-5 range midpoint), or
  a specific number within that range?
- **Milestone congrats (>10 MCQs, future round numbers)**: fold into this daily
  script as a rare event-triggered exception (§3), or keep it fully separate/manual
  as it is today?
- **Explicit dismiss duration**: permanent-until-they-re-engage-organically (as
  designed in §4), or should a "Not Interested" tap only suppress for a fixed
  cooldown (e.g. 30 days) and then be eligible again automatically?
- **"General / no streak" segment (§3, #4)**: send it daily like the others, or at a
  lighter cadence (e.g. every 2nd or 3rd day) since it's the lowest-urgency,
  highest-volume bucket (53 of 62 real students today) and most likely to feel
  repetitive fastest?
