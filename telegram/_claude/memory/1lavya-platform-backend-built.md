---
name: 1lavya-platform-backend-built
description: "The full 1LAVYA bot backend (master bot mapping, unified DB, process manager, deterministic content pipeline, analytics dashboard) was built 2026-08-10, prompted by CA Pranav needing 2 separate bots instead of one unified bot like Arun's"
metadata: 
  node_type: memory
  type: project
  originSessionId: eff70d38-31a6-4cc7-baf2-a93b1aa25479
  modified: 2026-08-10T13:02:00.493Z
---

Built 2026-08-10 in one pass, per Pranav's explicit choice: "design/build the full
backend first" before onboarding his 2 bots (see [[1lavya-menu-autoskip-and-next-step-ux]]
and earlier entries for what existed before this). Every piece below was verified by
test (simulated flow / synthetic docx / headless-Chrome screenshot), not just written.

**1. Master bot mapping — `telegram/config/bots.json` + `bots.README.md`.** Split
"what does this faculty teach" (stays in `tenants.json`) from "what bot processes
exist, which token/script" (new file). Forced by Pranav wanting **two separate bots**
(Study + Exam) rather than Arun's one unified bot — the old tenants.json shape
(one `bot_token_env` per tenant) couldn't express that. `bot_id` equals `tenant_id`
for single-bot tenants (keeps old `TENANT_ID` launch commands working as a fallback);
multi-bot tenants get suffixed ids (`capranav-study`, `capranav-exam`). Real tokens
for both of Pranav's bots are now in `telegram/.env`
(`FACULTY_CAPRANAVSTUDY_BOT_TOKEN`, `FACULTY_CAPRANAVEXAM_BOT_TOKEN` — no underscore
between the name and study/exam, matches what was actually typed there) and both
resolve correctly, verified. **Not started/launched yet** — tokens exist, bots.json
says `status: "active"`, but nobody has run them.

**2. Unified database — `telegram/database/schema.sql` + `db.py`.** One shared
SQLite file (`platform.db`) instead of each bot's own separate `.db`. Tables shared
**per bot KIND** with a `bot_id` column (Pranav's explicit choice over one-table-per-
bot-instance) — `bot_heartbeats`, generic `bot_interactions` log, `study_hub_events`,
`exam_hub_sessions`/`exam_hub_descriptive_events`/`exam_hub_mcq_attempts` (migrated
off Exam Hub's old separate per-tenant `Exam_Bot.db`), plus the central `students`
table every bot now writes to (finishing the [[1lavya-centralized-account-model]]
decision). `wallet_ledger`/`payments` exist in the schema but are **still unwired** —
no bot gates or bills anything yet. Multi-process safety: WAL mode + 30s busy_timeout
+ an application-level retry-with-backoff wrapper — deliberately NOT the originally-
planned separate 5-second-snapshot file (see [[1lavya-bot-infra-plan]]); the
dashboard reads `platform.db` directly since it's an on-demand static-HTML generator,
not a live poller, so that contention risk doesn't really exist yet. Revisit if it
ever becomes a live page. A real bug was caught by testing: `last_insert_rowid()` is
connection-global, not table-specific — calling it AFTER a second, unrelated insert
(the generic interaction logger) returned the wrong row's id. Fixed by capturing the
id immediately after the intended insert, before any other write on that connection.

**3. Process manager — `telegram/tools/manage_bots.py` (+ `.bat` wrapper).**
`start`/`stop`/`restart`/`status` for every `active` bot in `bots.json` at once or by
`bot_id`. PID-tracked (with a cmdline check so a recycled PID is never mistaken for
the bot still running). Graceful stop on Windows via `CTRL_BREAK_EVENT` — **actually
verified working**, not assumed: python-telegram-bot's `run_polling()` does NOT
register signal handlers by default on Windows (confirmed by reading its source), but
`CTRL_BREAK_EVENT` still correctly unwound a test process through its shutdown path,
observed directly (a dummy script printed "exiting cleanly" before exiting, well
under the grace period). Falls back to a bounded force-terminate — an honest tradeoff
given this codebase's writes all commit immediately (see `manage_bots.py`'s own
docstring for why that makes the fallback low-risk, not a compromise).

**4. Deterministic content-conversion pipeline — `telegram/config/
FACULTY-MCQ-TEMPLATE.md` + `telegram/tools/convert_faculty_mcq_docx.py`.** Pranav's
explicit ask: "more deterministic, less AI driven." Canonical template locked in
(matches CS Arun Chouhan's own Foundation-file shape, which already proved fully
parseable) — the KEY rule is the correct answer NEVER lives inline on the question
(no more "✓ CORRECT ANSWER" marker), only in one separate Answer Key table at the
end, since an inline marker is exactly what caused 5 real defects when his other file
was hand-extracted (see [[1lavya-csarunchouhan-demo-content]]). The converter is pure
regex + `python-docx` table parsing, zero AI calls — verified against two synthetic
test docs covering both real answer-key table shapes seen in practice, and every
anomaly class (missing answer-key entry, orphan answer-key entry, bad option count,
missing explanation, numeric-figure-worth-double-checking) — all correctly caught and
reported, never silently guessed. **Not yet applied retroactively** to Arun's
existing 20 MCQs (those predate this tool) — new faculty content should go through it
going forward.

**5. Analytics dashboard — `telegram/tools/generate_dashboard.py`.** Local, static
HTML (`telegram/database/dashboard.html`), regenerate on demand. Bot online/offline
via heartbeat freshness (360s staleness threshold = 3x the 120s heartbeat interval),
a stacked bar chart of message volume with date-range presets (today/7d/30d/month/
custom), true distinct-visitor counts per range (a real set union across days,
computed client-side — not a sum of daily uniques, which would double-count a
returning student). Used the `dataviz` skill's validated categorical palette; top-7
bots get their own series, rest fold into "Other" per that skill's own rule.
Rendered and screenshotted via headless Chrome to visually confirm before calling it
done — looked correct on the first real render.

**6. `myfiles_hub_bot.py`** got a heartbeat-only addition (hardcoded
`MYFILES_BOT_ID = "1lavya-myfileshub"`) — deliberately NOT migrated onto BOT_ID/the
shared DB for anything else; its own `users`/`otps`/`files`/`tags`/`activity_log`
stay exactly where they are (primary application data, not logs).

**Known gap, not addressed this pass**: `capranav`'s own Revision Material (2 PDFs,
AS 2 & AS 10) is still `not_ingested` — his Study bot is live-ready and correctly
scoped, but doesn't yet serve his own content, only the shared pool. Needs the
`content_owner` catalog-tagging convention actually applied to
`build_master_catalog.py` first (still just a documented convention in `schema.sql`,
not implemented) so his PDFs are attributed to him rather than silently merged into
the anonymous shared pool.

**Update 2026-08-10, same day**: Pranav asked directly whether all of this was
documented anywhere and where — the honest answer was no, CLAUDE.md (the repo's own
"read this first" master doc) hadn't been touched since 2026-08-08/09, well before any
of the above existed. Fixed by adding **CLAUDE.md §11** ("Telegram Bot Platform —
multi-tenant backend + first white-label faculty bots"), a proper end-to-end synthesis
of everything in this memory entry, matching the repo's own established style
(§6/§8/§9/§10). Also discovered while answering a related question: a NEW file,
`telegram/assets/faculty/csarunchouhan-cma-found-law/cma_foundation_law_faculty_mcqs.json`
(375 questions — Arun's full Foundation corpus, `publication_status: "draft"`,
different schema than `convert_faculty_mcq_docx.py` produces, no explanations yet) —
not converted or wired into his live bot as of this writing, flagged in CLAUDE.md §11
too. **CLAUDE.md §11 is now the correct starting point for any future session touching
`telegram/`** — read it before this memory file for the narrative; this file is for
session-continuity depth CLAUDE.md doesn't need to carry.

**Update 2026-08-10, later same day**: all 6 real bots (including Pranav's own
`capranav-study`/`capranav-exam`) confirmed started by Pranav himself — the "not yet
started by anyone" line above and in CLAUDE.md was accurate when written, no longer
true. A real user-reported bug was found and fixed live on `csarunchouhan`: "Next
Question"/"I'm Done" gave no response after an MCQ answer, root-caused to
`faculty_bot.py`'s `CallbackQueryHandler` pattern requiring a trailing colon
(`...|next|restart):`) that bare `callback_data="next"`/`"restart"` (no colon, by
design in `exam_hub_bot.py`) never matched — so no handler fired at all, not even
`query.answer()`. Fixed (`(:|$)` instead of literal `:`), deployed by restarting the
live process. Standalone `exam_hub_bot.py` was never affected.

Pranav then asked for "a robust architecture and a perfect reporting tool," specified
as: (1) DM alerts to admin chat ID(s) when a bot goes down, sent via the MyFiles Hub
bot's token (his choice), (2) a dashboard with a Refresh button that live-queries
instead of a static regenerate-the-file snapshot, (3) an on-demand bot-wise usage
summary, delivered as a dashboard view (his choice over a Telegram command). All three
built same session: `telegram/bots/watcher_bot.py` (edge-triggered down/up detection
off heartbeat freshness, state in a new `bot_alert_state` table, both transition
directions verified against the real live DB by temporarily perturbing one real bot's
state and watching it self-correct through the real code path — not mocked);
`telegram/tools/dashboard_server.py` (live version of the dashboard, runs as a managed
`bots.json` process); `telegram/database/analytics.py` + `dashboard_html.py` (the old
static `generate_dashboard.py` and the new live server were refactored onto these two
shared modules so they can't drift into disagreeing about a number).

**Still genuinely open**: `telegram/config/alerts.json`'s `admin_chat_ids` is empty —
the watcher cannot send anything until Pranav provides real Telegram chat ID(s) (see
that file's own comment for how to get one: message @Official1LavyaMyFilesBot once,
then @userinfobot). Its `bots.json` entry is `status: "inactive"` until then.

**Also flagged, not fixed**: this session's own sandboxed shell hit `WinError 87` on
`manage_bots.py`'s `CTRL_BREAK_EVENT` graceful-stop every single time (fell through to
force-terminate harmlessly) — contradicts this memory's own earlier "actually verified
working" claim above. Most likely that shell lacking a real attached Windows console,
not a regression in the code — but that's a guess, not confirmed. Worth Pranav testing
`manage_bots.py stop <bot_id>` from his own real terminal before trusting either claim.
