# `telegram/database/` — the shared platform database

`schema.sql` is the central, cross-bot DB — **wired in and live as of
2026-08-10** (was schema-only/unwired when this doc was first written).
Every bot process (`study_hub_bot.py`, `exam_hub_bot.py`, `faculty_bot.py`,
and `myfiles_hub_bot.py` for its heartbeat only) now writes to the ONE file
`telegram/database/platform.db` via `db.py`, instead of each bot keeping
its own separate `.db` file. See `telegram/config/bots.README.md` for the
`bot_id` every row is tagged with, and `tenants.README.md` for the content
registry this joins against.

**What's actually wired in**: student identity (`students`), the generic
`bot_interactions` log, `bot_heartbeats`, Study Hub's `study_hub_events`,
Exam Hub's `exam_hub_sessions`/`exam_hub_descriptive_events`/
`exam_hub_mcq_attempts` (migrated 2026-08-10 from Exam Hub's old separate
per-tenant `Exam_Bot.db`), and `bot_alert_state` (added 2026-08-10,
`telegram/bots/watcher_bot.py`'s down/up transition tracking — see below).
**Still schema-only, not wired into any bot**: `wallet_ledger` and
`payments` — those were designed for the ₹5,000 faculty-fee / MCQ-credit
billing model, which hasn't been built into any bot's actual flow yet (no
gating, no payment webhook). MyFiles Hub's own `users`/`otps`/`files`/
`tags`/`file_tags`/`activity_log` deliberately stay in their own separate
`myfiles_hub.db` — primary application data, not logs, out of scope for
this migration (see `schema.sql`'s own note).

## Multi-process writes: WAL mode + retry, not a separate snapshot file

The original design here called for a **live DB** plus a **separate
snapshot file refreshed every ~5 seconds**, so analytics reads would never
contend with live bot writes. **That's not what got built.** Instead,
`db.py`'s `get_connection()` opens `platform.db` in **WAL mode** with a
30-second `busy_timeout`, and every write goes through
`execute_with_retry()` (a real retry-with-backoff loop) on top of that —
this is enough for multiple bot *processes* (not just threads) to write to
the same file safely, verified by test with two separate connections
writing concurrently. The dashboard (`generate_dashboard.py`) reads
`platform.db` directly too, but **on demand, not continuously** — it's a
static-HTML-snapshot generator you re-run when you want fresh numbers, not
a live-polling page, so the contention the original 5-second-snapshot
design was protecting against barely exists at the read pattern this
actually has. If the dashboard ever becomes a live, continuously-refreshing
page, or write volume grows enough that WAL-mode readers start seeing real
contention, the original snapshot-copy design (SQLite's `backup()` API,
same idea as before) is still the right upgrade — just not needed yet.
Revisit if either of those actually happens; don't build it speculatively.

If/when the engine moves to PostgreSQL, the equivalent is a logical
replication slot or a scheduled `pg_dump`/read-replica.

## Why `mcq_debit` fires on "shown", not "answered"

A student who is shown a question and never answers it has still consumed
the platform's resource (the question was selected, rendered, sent) —
charging on `answered_at` would let someone "browse" unlimited questions
without ever tapping an option. `descriptive_question_events`/`mcq_attempts`
(Exam Hub's existing per-bot tables) already timestamp `shown_at` separately
from `answered_at`, so this lines up with instrumentation that already
exists — debiting on shown is a small addition there, not a new concept.

## Running the tools

- **Start/stop/restart every bot**: `python telegram/tools/manage_bots.py
  start` (or `stop`/`restart`/`status`, optionally with a specific `bot_id`)
  — reads `telegram/config/bots.json`'s `active` bots, one OS process each,
  with PID tracking and a real graceful-shutdown attempt via
  `CTRL_BREAK_EVENT` before a bounded force-terminate fallback. **Caveat
  added 2026-08-10**: the original "verified working on Windows" claim
  didn't hold up in this session's own sandboxed shell — every `stop`/
  `restart` call there hit `WinError 87: The parameter is incorrect` on
  the signal itself and fell through to the force-terminate fallback
  (harmlessly — the bot still stopped, just after the full grace period
  instead of immediately). Most likely cause is that shell having no real
  attached Windows console for `GenerateConsoleCtrlEvent` to target, not a
  code defect — but this is flagged, not confirmed either way; worth
  Pranav checking `manage_bots.py stop <bot_id>` from an actual PowerShell/
  cmd window on his own machine before trusting "graceful" at face value.
  See that script's own docstring for exactly what "graceful" means here.
- **Live dashboard (recommended)**: `python
  telegram/tools/dashboard_server.py`, then open `http://127.0.0.1:8787/`
  — a Refresh button re-queries `platform.db` on click and re-renders in
  place, no page reload, no re-running a script by hand (Pranav's ask,
  2026-08-10: "refresh button which will make the necessary query and get
  the latest"). Local only (binds `127.0.0.1`), matching the platform's
  existing local-server-for-now stance. Can run as a managed, always-on
  process like every bot — see `telegram/config/bots.json`'s
  `1lavya-dashboard` entry and `python telegram/tools/manage_bots.py start
  1lavya-dashboard`.
- **Static dashboard snapshot** (for a one-off file you can email/share):
  `python telegram/tools/generate_dashboard.py`, then open
  `telegram/database/dashboard.html`. No Refresh button — re-run the
  script to refresh. Both this and the live server render the exact same
  page from the exact same query layer (`telegram/database/analytics.py` +
  `dashboard_html.py`, added 2026-08-10 specifically so the two surfaces
  can't drift into disagreeing about a number — see those modules' own
  docstrings) — the only difference is where the data comes from (baked in
  vs. fetched live).
- Both dashboards show: bot online/offline (via `bot_heartbeats`), a
  **bot-wise usage summary** (interactions, unique users, Study Hub
  downloads/searches, Exam Hub sessions/MCQ accuracy/descriptive views —
  added 2026-08-10 as the "on demand summary of usage metrics, bot-wise"
  Pranav asked for, delivered as a dashboard view per his choice over a
  Telegram command), and message volume stacked by bot with date-range
  presets plus true distinct-visitor counts per range (computed
  client-side as a set union across days, not a sum of daily uniques).
- **Down/up DM alerts**: `python telegram/bots/watcher_bot.py` (runs
  forever, checking every `check_interval_seconds`) or `--once` for a
  single check pass — added 2026-08-10 per Pranav's ask for "a fresh DM to
  be sent to mentioned CHATIDS ... regarding the Bot being down for any
  reason." Detects down/up via the same heartbeat-freshness signal the
  dashboard uses (never disagrees with what the dashboard shows), fires
  exactly once per real state transition (tracked in the new
  `bot_alert_state` table, survives a watcher restart), and sends via the
  1LAVYA MyFiles Hub bot's token (Pranav's choice). **Needs
  `telegram/config/alerts.json`'s `admin_chat_ids` filled in with real
  Telegram chat ID(s) before it can actually DM anyone** — ships empty by
  design; the watcher runs fine either way, it just logs a warning and
  skips sending until that's done (see that file's own comment for how to
  get a chat ID). Its `bots.json` entry is deliberately `status: "inactive"`
  until then, so `manage_bots.py start` (no bot_id) doesn't silently run a
  watcher that can't alert anyone yet — flip it to `"active"` once
  `alerts.json` is filled in. Full detail, including honest limitations
  (can't alert on its own death; a bot already down when `alerts.json` is
  first configured doesn't get a retroactive alert for that outage), in
  `watcher_bot.py`'s own module docstring.
- **Content Health**: `python telegram/tools/validate_content_json.py` (or
  the "Content Health" card on either dashboard, which runs the exact same
  check live via `analytics.fetch_content_health()`) — added 2026-08-10,
  Pranav's ask: as more faculty bring their own JSON, each potentially
  adding their own extra display fields, how do we guarantee the fields
  the BOT CODE actually depends on are always present and correctly
  shaped, so a malformed file fails loudly here instead of silently
  breaking mid-conversation for a real student? Checks every tenant's
  MCQ/descriptive JSON (auto-discovered from `tenants.json`'s
  `exam_content`) against a field contract derived directly from what
  `exam_hub_bot.py`'s `QuestionBank`/`McqBank` actually read — ERROR for
  anything that would crash or silently corrupt an answer (a bad
  `correct_option`, too few `options`, a duplicate `mcq_id`/`book_id`
  silently shadowing an earlier record), WARNING for anything with a safe
  fallback but degraded content (a missing `chapter_label`, no
  `answer_html`). **Extra faculty-specific fields never trigger a flag,
  only missing/malformed core ones do** — this is deliberately not a
  content-quality/fact-checking tool (that's a separate, deeper concern —
  see `first_run/`'s `extract_book_questions.py`/`diff_book_vs_index.py`
  for that kind of QA on the Question Bank Book pipeline specifically).
  Verified against all 4 real live content files (clean) and a synthetic
  negative-control file covering all 4 defect classes above (all correctly
  caught) before being trusted.

## Example analytics queries (against `platform.db`)

For anything the dashboard already shows (heartbeats, daily activity, the
bot-wise summary), prefer calling `telegram/database/analytics.py`'s
functions directly over hand-writing the SQL again — see that module's own
docstring. The raw SQL below is for ad hoc questions neither dashboard view
answers.

```sql
-- Unique students, platform-wide
SELECT COUNT(*) FROM students;

-- Messages by bot, last 30 days (what generate_dashboard.py's chart shows)
SELECT bot_id, COUNT(*) FROM bot_interactions
WHERE created_at >= datetime('now', '-30 days') GROUP BY bot_id;

-- MCQs actually attempted (not just shown) per bot
SELECT bot_id, COUNT(*) FROM exam_hub_mcq_attempts
WHERE answered_at IS NOT NULL GROUP BY bot_id;

-- The wallet/payments queries below are for once that system is actually
-- built (see the "still schema-only" note above) -- not usable yet.

-- Total MCQs served (debited), all-time and this month
SELECT COUNT(*) FROM wallet_ledger WHERE event_type = 'mcq_debit';
SELECT COUNT(*) FROM wallet_ledger
WHERE event_type = 'mcq_debit' AND created_at >= strftime('%Y-%m-01', 'now');

-- Wallet recharge activity (money in) by tenant
SELECT tenant_id, COUNT(*) AS recharges, SUM(amount_inr) AS total_inr
FROM payments WHERE kind = 'student_credit_recharge' AND status = 'completed'
GROUP BY tenant_id;

-- A specific student's current credit balance (always derived, never stored)
SELECT COALESCE(SUM(amount), 0) AS balance
FROM wallet_ledger WHERE telegram_user_id = ?;
```

The "1LAVYA-exclusive vs. faculty content" count isn't in this DB — it comes
from the catalog artifacts once the `content_owner` tagging convention
(bottom of `schema.sql`) is applied there.
