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
per-tenant `Exam_Bot.db`), `bot_alert_state` (added 2026-08-10,
`telegram/bots/watcher_bot.py`'s down/up transition tracking — see below),
and `mcq_issue_reports` (added 2026-08-13, `telegram/bots/mcq_issue_flow.py`'s
"Report Issue in MCQ" flow — has its own Admin Portal page, see that
folder's README). `exam_hub_mcq_attempts`/`exam_hub_descriptive_events`
each also gained `content_owner` and `human_id` columns that same day (see
"content_owner tagging" below). `content_ingestion_log` (added 2026-08-13,
for the Admin Portal Overview rebuild's "New Questions Added" trend) is
written to via `analytics.log_content_ingestion()` whenever a new content
batch is wired into a tenant's `exam_content` — **tracks forward only**,
there is no historical ingestion-date data before this table existed
(content files never carried an "added on" timestamp, and file mtimes
would misdate an old file's later typo-fix as "new content" — deliberately
not used as a proxy). See `telegram/admin_portal/README.md`'s "Overview
rebuild" section for the full picture.
**Reshaped 2026-08-15** for the Test Mode billing rollout (see
`telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md` §9 for the full
decision trail): `wallet_ledger` now keys on `username`
(`student_profiles.username`), not `telegram_user_id` — a student's balance
follows them across every linked phone, consistent with the leaderboard/
profile identity model, rather than fragmenting per chat_id. `payments`
gained a `username` column alongside its existing `telegram_user_id` (which
chat_id/phone actually initiated a given recharge vs. whose balance it
credits). Both tables were verified empty before this reshape and migrated
via `db.py`'s `_migrate_wallet_ledger_shape()` (a one-time drop+recreate,
since SQLite can't `ALTER` a column's identity or widen a `CHECK`
constraint) — see that function's docstring for the full reasoning and its
guard against ever doing this again once real rows exist.

**Primitives now exist** (`telegram/database/wallet.py` — balance/credit/
debit with idempotency-key protection against double-charging on a
retry/restart) **and a Razorpay Payment Links client**
(`telegram/database/razorpay_client.py` — live keys, `RAZORPAY_1LAVYA_key_id`/
`_key_secret` in `telegram/.env`), both smoke-tested
(`telegram/database/smoke_test_wallet.py`, DB logic only, makes no network
call). **Still not wired into any bot's actual flow** — no conversational
recharge flow, no gating on MCQ/Descriptive practice or Test Mode yet, no
Cloudflare Tunnel/webhook (a polling-based confirmation is the planned v1
instead — see roadmap §9.5). MyFiles Hub's own `users`/`otps`/`files`/
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

## Self-healing autostart: Windows Startup + Task Scheduler (added 2026-08-15)

Found the ENTIRE platform down (every bot's heartbeat stale by ~4.7
hours) after a routine check — this machine has no auto-restart-on-crash,
per the known scale-readiness gap already flagged right after CLAUDE.md
§2. Pranav asked for two things to guard against this going forward:

1. **A script that auto-runs at Windows startup** and restarts whatever
   isn't running.
2. **A Task Scheduler job, every 30 minutes, as a safer-side recurring
   check** — restarts anything found down.

**`manage_bots.py` gained a new `ensure-running` action** (alongside its
existing `start`/`stop`/`restart`/`status`) — the self-healing check both
mechanisms below call. For every `active` bot: if its process isn't
running at all, start it (same idempotent check `start` already does). If
it IS running but its heartbeat has gone stale past
`HEARTBEAT_STALE_AFTER_SECONDS` — a hung process still holding its PID
but no longer doing real work — it gets a full restart, not just left
alone. A healthy bot is untouched. One command covers both "wasn't
running" and "is running but stuck," so there's only one thing to
schedule.

**`telegram/tools/ensure_bots_running.bat`** (new) is the actual
unattended entry point both mechanisms below call — explicitly uses the
repo's own `.venv\Scripts\python.exe` (never bare `python` off PATH,
which a Startup-folder/Task-Scheduler process doesn't reliably have set
up the way an interactive terminal does), logs every run to
`telegram/database/run/logs/ensure_bots_running.log`, and opens with a
20-second `ping`-based delay (NOT `timeout.exe`, which hard-refuses to
run — "Input redirection is not supported" — with no real interactive
console attached, exactly the case for both triggers below; confirmed by
testing, not assumed) so Windows networking has a moment to be ready
right after boot/logon.

**Wired into two places**, per Pranav's explicit ask for both:
1. A shortcut in the current user's Startup folder (`shell:startup`,
   `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\1LAVYA Bots -
   Ensure Running.lnk`) — points at the canonical repo `.bat` (not a
   copy), so any future edit to the script is picked up automatically,
   no re-placing needed. Runs once at this user's logon.
2. A Task Scheduler job, **"1LAVYA Bots - Health Check"**, `schtasks /sc
   minute /mo 30` — runs indefinitely, every 30 minutes, no end date.

**Known limitation, named honestly**: a true "at system boot, before any
user logs in" Task Scheduler trigger (`schtasks /sc onstart`) needs
elevated rights this session's shell doesn't have (`ERROR: Access is
denied`) — not created. In practice this doesn't leave a real gap: the
Startup-folder shortcut covers this user's own logon, and the 30-minute
recurring task independently guarantees recovery within, at most, 30
minutes of any outage regardless of *why* the bots went down (a crash,
not just a reboot). If Pranav wants true pre-login boot coverage too, he
can run `schtasks /create /tn "1LAVYA Bots - Startup Check" /tr
"D:\EffCorp_Projects\cap-online\telegram\tools\ensure_bots_running.bat"
/sc onstart /f` himself from an elevated (Run as Administrator) prompt.

**A real bug found and fixed while restarting everything**: an earlier
manual test (verifying `ensure-running`'s stale-heartbeat-restart path)
left a **timezone-naive** `last_heartbeat_at` value in `bot_heartbeats`
for one bot (written via raw SQLite `datetime('now', ...)`, which
produces a different shape than `db.py`'s own `now()`). `analytics.
fetch_heartbeats()`'s existing `try/except` only guarded the *parse* step
— the actual crash was one line later, subtracting a timezone-aware `now`
from that naive value (`TypeError: can't subtract offset-naive and
offset-aware datetimes`), **outside** the guarded block, which aborted
the whole function and therefore silently dropped *every other bot's*
heartbeat too, not just the bad row's. This wasn't a hypothetical — it
put `1lavya-platform-watcher` into a real crash loop ("Check pass failed
— will retry next interval," every 60s). Fixed in two places: the bad DB
value itself (rewritten via `db.py`'s own `now()`), and `_parse_iso()`/
`fetch_heartbeats()` hardened to (a) treat a naive timestamp as UTC
instead of crashing, and (b) catch `TypeError` alongside `ValueError`, so
one malformed row can never again take down every bot's heartbeat
display. All 9 active bots restarted afterward to pick up the fix
(Python doesn't hot-reload a running process's imports); verified clean
— confirmed the exact bad-shape row no longer crashes `fetch_heartbeats()`
and the watcher stopped erroring.

**Also investigated and ruled out, worth knowing so a future session
doesn't waste time re-diagnosing it**: every restarted bot briefly appears
as **two** OS processes — one at `.venv\Scripts\python.exe`, one at the
machine's global `Python312\python.exe`, the child of the first. This
looks exactly like a duplicate/conflicting second instance (and was
chased as one, including a live-monitored kill-and-watch test) before
`.venv\pyvenv.cfg` settled it: Python 3.11+'s Windows venv launcher makes
`.venv\Scripts\python.exe` a tiny redirector stub that spawns the real
base interpreter as a child and waits on it, relaying its exit code —
completely normal, intentional behavior, not a bug, not a second bot
instance, not a second Telegram poller. `manage_bots.py`'s own PID
tracking already correctly targets the stub (confirmed: killing it
correctly cascades to the child too).

## Off-machine backup: Cloudflare R2 + D1 (added 2026-08-16)

Closes the other half of scale-readiness gap #1 (the self-healing
autostart above only restarts a *crashed process* on the *same* machine —
it does nothing if the machine/disk itself is what's gone). Pranav asked
what to back up and how; a real inventory (not guesswork) confirmed
`database/platform.db`, the separate `assets/myfiles_bot/myfiles_hub.db` +
its `uploads/` folder (real student-uploaded files), and ~1.4GB of
live-served PDFs/JSON under `assets/study_bot/`, `assets/faculty/`,
`assets/exam_bot/` are **100% local-only** — all gitignored by design
(`**/*.db`, `**/*.pdf`, `*.env`, `creds.txt`). Python code + question-bank
JSON + config JSON are already safe via `git push` and are NOT part of
this pipeline.

**`telegram/tools/backup_to_cloudflare.py`** — run nightly at 3:30 AM via
a Windows Task Scheduler job, **"1LAVYA Platform Backup"** (deliberately
NOT a `bots.json` entry — this is a run-to-completion batch job, not a
long-running heartbeat process manage_bots.py knows how to model). Four
phases, each independently try/excepted so one failing doesn't block the
others:

1. **SQLite-consistent DB snapshots** — `platform.db` + `myfiles_hub.db`,
   via `sqlite3`'s own `.backup()` API (never a raw file copy — safe even
   while WAL-mode bot processes are actively writing), gzipped,
   timestamped, 60-day retention (pruned automatically each run).
2. **A full D1 mirror of `platform.db`** — a genuinely queryable off-site
   copy, not just a blob. Schema replayed verbatim from the source's own
   `sqlite_master` (every statement is `IF NOT EXISTS`, safe to repeat
   every run); table order for wipe/reinsert derived at RUNTIME from
   `PRAGMA foreign_key_list` (never a hand-maintained list that could
   silently drift from `schema.sql` as tables are added). Full refresh
   (`DELETE` then reinsert) every run rather than incremental sync — at
   today's data volume (a few thousand rows total) this is simpler and
   more robust than tracking deltas.
3. **Encrypted secrets backup** — `.env`/`creds.txt`, Fernet-encrypted
   with a PBKDF2-derived key from `CF_BACKUP_ENCRYPTION_PASSPHRASE`
   (`telegram/.env`). **Silently sending these unencrypted was never on
   the table** — the phase is skipped loudly (logged warning, not a
   crash) if that passphrase is unset. Real disaster-recovery path exists
   via `--decrypt-secret <downloaded-file>`, not just one-way upload —
   verified with an actual download-decrypt-read round trip before this
   was considered done. **The passphrase must also live somewhere other
   than this PC** (a password manager) — if only stored in `.env`, it
   protects nothing once this machine is the thing that's gone.
4. **Asset sync** — `study_bot/`, `faculty/`, `exam_bot/` (PDFs+JSON),
   `myfiles_bot/uploads/`. Compares each local file's MD5 against the
   object's R2 ETag (kept as a plain MD5 by forcing single-part uploads —
   multipart ETags aren't a plain MD5 and would silently break this
   comparison) and only uploads new/changed files. **Never deletes a
   remote object based on local state** — a backup that can destroy
   backed-up content because a local file moved/vanished is a liability,
   not a safety net. `assets/backup pdfs/` (1.5GB, already documented
   elsewhere in this repo as pre-restructuring/unused) is deliberately
   excluded from scope.

**On any phase failure**, sends a DM via `watcher_bot.py`'s existing
sender-token/`alerts.json` plumbing — reused directly (same function
calls), not reimplemented. Silent on success, same edge-triggered
philosophy as the down/up watcher (no nightly "it worked" noise).

**Cloudflare account**: the existing **EfficientCorporates (ECPL)**
account (same one `CF_EMAIL_*` already uses), not a separate 1LAVYA
account Pranav also has — his call, since `1lavya.com`'s domain currently
lives on ECPL; see `_claude/memory`'s `1lavya-cloudflare-account` for the
full history and the 1LAVYA account id kept on file for when the domain
migrates. The R2 Access Key ID/Secret Access Key in `telegram/.env`
(`CF_BACKUP_R2_*`) are **not separately generated** — they're
deterministically derived from `CF_BACKUP_API_TOKEN` per Cloudflare's own
documented mechanism (Access Key ID = the token's `id`, Secret = SHA-256
of the token value) and were verified with a real signed S3 `ListBuckets`
call before being trusted.

**First real run, verified**: bucket (`1lavya-platform-backups`) and D1
database (`1lavya_platform_mirror`) both auto-created on first run. D1
mirror: 29 tables, 3,981 rows, cross-checked against live query results
on `platform.db` directly (not just trusted from the script's own log
line) — `course_catalog` (static reference data) matched exactly at 975
rows both times; the live-activity tables had genuinely grown between two
checks minutes apart, confirming the mirror reflects real current state,
not a stale copy. DB snapshots + encrypted secrets + D1 mirror: ~200s.
Asset sync (the one-time full 1.4GB upload): materially longer — every
future nightly run only touches new/changed files, so this cost is paid
once, not nightly.

**Restore path**: `python telegram/tools/backup_to_cloudflare.py
--decrypt-secret <path>` for `.env`/`creds.txt`; a `db-snapshots/*.db.gz`
object is a real, complete SQLite file once gunzipped — copy it over
`platform.db`/`myfiles_hub.db` directly; the D1 mirror is queryable
as-is from the Cloudflare dashboard or API with zero extra steps, useful
even before a full machine restore. Asset files restore via a plain S3
`GetObject`/`sync` back into `telegram/assets/`.

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
-- keyed by their 1LAVYA username since 2026-08-15, not telegram_user_id --
-- see telegram/database/wallet.py's get_balance() for the real callable version.
SELECT COALESCE(SUM(amount), 0) AS balance
FROM wallet_ledger WHERE username = ?;
```

## content_owner tagging (wired in 2026-08-13)

`schema.sql` documented a "content-ownership tagging convention"
(`content_owner` = `"1lavya"` for shared content, or a tenant_id for
faculty-sourced content) back on 2026-08-09 but left it unwired. It's
live now: `exam_hub_bot.py`'s `_infer_content_owner()` derives it purely
from each content file's own path (`.../faculty/<tenant_id>/...` → that
tenant_id; everything else → `"1lavya"`) at load time — no per-record
field or content-file schema change needed anywhere — and it's persisted
into every `exam_hub_mcq_attempts`/`exam_hub_descriptive_events` row.
This is provenance only, never an access filter: **every question on the
platform joins the flagship `1lavya-examhub` bot's pool regardless of
`content_owner`** (a standing rule, see `/CLAUDE.md` §11's 2026-08-13
entries) — a faculty's own bot separately stays scoped via
`tenants.json`'s `content_scope`.

```sql
-- MCQs served, broken down by which tenant's content it actually was
SELECT content_owner, COUNT(*) FROM exam_hub_mcq_attempts GROUP BY content_owner;
```
