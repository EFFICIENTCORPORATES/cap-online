# Project Log — cap-online

A running status note. Newest entries at the top. One short block per session.

## 2026-09-23 — Telegram platform migration confirmed; duplicate content audited for removal

Verified the migration rather than assuming it. The platform repo holds 6,228 files against this
repo's 2,351, and is well ahead (CA Final AFM MCQs, faculty OTP login, live question bank, wallet
work). Checked every file here by content hash against it.

Found six files that existed ONLY in cap-online and copied them into the platform repo first,
hash-verified: `bots/myfiles_hub_bot.py` (the MyFiles Hub bot itself), `myfiles_activity_report.py`,
`README_Bot3_MyFilesHub.md`, the archived sales-agent note, a CMA Final Law MCQ set and
csarunchouhan's `mcq_questions_extracted.json`. Worth knowing: that repo's `bots.json` still lists
`1lavya-myfileshub` as active and carries its data and PID file, but its source was missing there
until this copy — whether that bot is still in service needs confirming.

The 1.22 GB `Study Materials.zip` looked unique until checked properly: all 1,091 entries exist in
the platform repo by content, renamed to the `CA_L3_P02_C1_U0_…` human-id convention, so a filename
comparison had made them look absent.

Built `tools/prune_migrated_telegram.py` (dry-run default, `--execute` to apply, full manifest,
per-file twin re-verified at the moment of deletion) and `telegram/MIGRATED.md`. Accounts papers for
CA/CMA/CS are preserved here — scope taken from the platform's own `course_catalog` subject names,
accounting papers only, Cost/FM excluded. Old runtime logs are kept too, since by nature they have
no twin. Dry run: 2,183 files / 4.09 GB removable, 298 accounts files and 38 runtime files kept.
**Not executed** — the bulk delete needs Pranav to run it, since most of that tree is untracked and
deletion is permanent. CLAUDE.md's Pillar 6 row and sections 8–11 are now marked historical.


## 2026-09-23 — Repo hygiene cleared, and QB e-book checkout moved to VC Gurukul

Cleared all three standing repo-hygiene issues; `health_check.py` now reports
**0 problems, down from 26**. (1) Nine `books/ca-inter/bridge-course/base-studymaterials/*.md`
files were UTF-16 LE, not corrupt — converted to UTF-8 with a round-trip check and
verified character-identical against git HEAD. (2) `health_check.py`'s `EXPECTED_DIRS`
still pointed at pre-move book paths and the deleted `question-bank/{pyq,mtp,rtp,solutions}`
v1 layout — repointed at the real `books/ca-inter/...` locations; 46/46 now resolve.
(3) CLAUDE.md's folder map was corrected to the post-move paths, five undocumented
folders were added (`books/ca-foundation/`, `books/ca-inter/smat-may-27-edition/`,
`capranav_com_revamped/`, `capranav_com/`, `mentorship/`), and a dated path note warns
that sections 6+ are a historical log still quoting old paths.

Separately, moved the ₹199 Question Bank e-book off this site's Razorpay checkout to
VC Gurukul's product page, following the 2026-09-06 course-redirect precedent (guarded
and commented, not deleted). Guarded server-side too, so no hand-crafted request can
create the order. Existing entitlement holders are unaffected. Deployed and verified
live. Full detail: `capranav_com_revamped/PROJECT-LOG.md`.

CORRECTION (same session): an earlier version of this entry said the Telegram platform was
"offline". That was wrong. Pranav confirmed the platform was MIGRATED on 2026-09-03 to its own
repo (`EFFICIENTCORPORATES/Main1lavyaAIAgents`, folder `examstudyhub/`) and now runs on a Contabo
server. The stale heartbeats, the disabled scheduled tasks and the renamed startup shortcut on
this PC are the correct end state of that migration, not an outage. See `telegram/MIGRATED.md`.


## 2026-09-23 — AS 2 Must Practice question page published on capranav.com

Identified the 10 must-practice AS 2 descriptive questions for the Jan/May 2027 attempt from `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/`, ranked on Top-100 topic weight, ICAI Study Material match percentage, paper type/recency and marks, then adjusted for coverage so all six Top-100 AS 2 topics appear rather than five near-identical exclusions-from-cost questions. Noted for the class pitch: AS 2 has scored zero marks in the last three PYQs after a 5/7/4/5 run.

Built and deployed a new public page at `/practice-with-pranav-bhaiya/must-practice/` — Module → Chapter → Unit picker across all 36 units, ranked question table, row expands to the verbatim question, answer behind a Show answer button, with the Author's Note/Examiner's Comment carried through. `capranav_com_revamped/tools/build_must_practice_data.py` generates the static JSON; Question Bank page numbers are resolved by matching each question's own printed header line against the distributed V1 PDF's text layer (all 10 resolved to exactly one page, 46–61; an ambiguous header would render "not traced", never a guess). The unit tree is derived from the canonical topic ranking so the picker cannot drift from the syllabus.

Confirmed this session that wrangler is authenticated on this machine (OAuth, efficientcorporates@gmail.com, workers/d1/pages write scopes) so deploys can be run directly from here. Verified with local and live headless-Edge screenshots, `wrangler deploy --dry-run`, and post-deploy 200s on the page, both JSON files, both assets and the untouched `/`, `/anatomy/` and practice hub. Deployed version `6d9bf497-f03f-47ac-9c0a-589e6e8d8363`. Only AS 2 is published; adding a unit is one entry in the script's `UNITS` table plus a re-run.

## 2026-09-22 — Anatomy sortable explorer and R2 PDF library published

Enhanced the live `/anatomy/` syllabus explorer with Overall Rank and Priority Band columns, click-to-sort direction arrows on every data column, Top 50/Next 50/Beyond Top 100 filtering, universal search across topic ID/name/page/unit/chapter, and a reset control. Added foreign-keyed document tables to the existing D1 database and uploaded 98 PDFs to the existing R2 bucket under `anatomy/`: 36 unit study-material PDFs and 62 available exam question/answer/comment documents. Added secure Worker-mediated inline Open PDF and attachment Download actions without exposing bucket listing. A fresh production D1 snapshot was taken before migration; local/remote counts and foreign keys passed; live topic-ID/page searches, 50-row priority result, PDF Range delivery, download disposition, login API and dashboard were smoke-tested after deployment.

## 2026-09-22 — Practice with Pranav Bhaiya interactive decks published

Published only the three confirmed Day 1 decks from `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/slides/`: Opening, Syllabus Flow, and Marks Split. Added a dedicated live hub at `/practice-with-pranav-bhaiya/` and linked it from the Anatomy page. Preserved the canonical decks unchanged and added `capranav_com_revamped/tools/sync_practice_slides.py` to refresh their Worker Assets copies after future edits. Hash checks confirmed all three published copies were byte-for-byte identical to their sources. Wrangler dry-run passed; deployed to the existing `capranav` Worker. Live smoke tests returned 200 for the hub and all decks and confirmed each deck contains Enter, Right Arrow, mouse-click, and on-screen navigation handlers. Existing `/api/me` still returned 200.

## 2026-09-22 — The Anatomy of Advanced Accounts first release deployed

Extended the existing `capranav` Worker, `capranav-platform` D1 database, and `capranav-vault` binding without creating parallel Cloudflare resources. Added an additive normalized `aa_*` schema covering 3 modules, 15 chapters, 36 units, 400 topics, 35 PYQ/MTP/RTP sittings, 509 descriptive questions through September 2026, 649 question-topic links, 62 study-material items, and 133 PYQ match rows. Added a deterministic importer merging the flat May dataset with reviewed current-syllabus overrides and all 13 September 2026 PYQ questions. The validator distinguishes the current 84-mark descriptive Part II from the older paper scheme, reports three historical source-total anomalies for review, confirms zero missing PYQ/MTP marks, and passes `PRAGMA foreign_key_check`. Took a fresh live D1 export before migration, applied only additive tables/views, deployed the read-only `/anatomy/` explorer and four `/api/anatomy/*` endpoints, and smoke-tested the new page plus the existing login, dashboard, and protected-reader boundary. Charts remain outside this first database release. The three confirmed Day 1 interactive slide decks were published in the follow-up release recorded above.

## 2026-09-22 — Descriptive Top 50/100 topic ranking and A/B/C/D question map

Built a reproducible descriptive-question analysis covering 509 PYQ/MTP/RTP records through September 2026 and 400 current Study Material topic rows. Added detailed topic IDs for all 13 September 2026 questions and completed 18 previously blank post-2023 mappings. Classified each question A (>=90% Study Material question match), B (50–<90%), C (topic present without a >=50% question match), or D (no current topic); manual PYQ reviews override deterministic normalized-text matches. The remaining 51 D records are confined to May/November 2023 legacy-syllabus material. Ranked topics on allocated descriptive PYQ marks across the ten available attempts (May 2023–September 2026), retaining both OR alternatives as concept exposure and dividing multi-topic question marks to prevent double-counting. Created `ca_inter_descriptive_topic_priority_v1.xlsx` with Guide, Top 100 PYQ, Chapter Priority, Topic Attempts, Question Topic Map, A-B-C-D Questions, and Study Topics sheets. The workbook is filterable and pivot-ready, with separate full, allocated, and OR-adjusted marks fields.

## 2026-09-22 — Last-six-PYQ marks split and Day 1 transition to AS 2

Calculated the January 2025 to September 2026 PYQ footprint across 15 teaching chapters, separating MCQ and descriptive marks and allocating internal OR marks equally across alternatives. Saved the reusable calculation in `data/last-six-pyq-marks-split.json`. Created `slides/day-01-marks-split.html`, a five-step interactive continuation to the syllabus-flow presentation: six-paper method, Part A-D split, 15-chapter stacked chart, preparation implications, and the transition to AS 2. The presentation labels the figures as normalized historical question presence rather than promised ICAI weightage. January 2025 currently has 28 of 30 MCQ marks mapped in the available MCQ library, so that two-mark mapping remains a documented follow-up.


## 2026-09-21 — Practice workbook v2: source correction, PYQ matching, summary checks

Implemented Pranav's approved workbook changes. Corrected May 2026 PYQ Q5(b) to 4 marks from the photographed printed question paper, recorded its conflict with the Suggested Answers PDF, and made Q5(a) a flagged provisional 10-mark inference so Q5 reconciles to 14. Regenerated the 831-row question index and both sheet-ready JSON files. Added `build_pyq_study_matches.py`: it extracts 223 study-material illustrations independently of the preceding/final topic plus 72 TYK questions, normalizes away names/dates/amounts, and ranks candidates for 120 descriptive PYQs. Manually reviewed and recorded 19 same-concept matches at 100% plus 4 partial-concept matches at 75%; all other candidates explicitly withhold a percentage pending concept review. Expanded question JSON with match provenance/status/score and OR/marks-check fields. Created `ca_inter_practice_index_v2.xlsx` with Summary, Questions and Study topics sheets; Summary shows per-attempt theory/practical marks, OR-deduped offered totals, answerable totals, missing/source issues, and chapter-wise counts. Tables are filterable, headers frozen, and columns fitted/wrapped for readability. Verified source row counts (496/400), May 2026 total (30+84=114 offered; 100 answerable), Q5(b)=4/source-conflict, no formula errors, and visually reviewed all three sheets.

## 2026-09-21 — Practice with Pranav Bhaiya workbook review inventory (no workbook edits)

Pranav is reviewing the CA Inter practice workbook and asked to collect changes before editing. Earlier points: end-of-standard illustrations must not automatically map only to the last topic (often Disclosures); PYQs should be traced to exact/near-replica study-material questions or concept sources with evidence. New points: audit May 2026 PYQ Q5(b) marks (Pranav sees 4, workbook says 10), add per-attempt marks reconciliation, theory/practical split, and chapter-wise question counts in a future summary sheet. Read-only trace found 10 in flat JSON, question index, parsed HTML, and printed page 34 of the local ICAI Suggested Answers PDF; Q5(a) was inferred as 4 in the parsed record. The question-only paper Pranav consulted has not been examined, so the discrepancy remains open. For this indexed May 2026 PYQ, 30 MCQ marks + 84 descriptive marks offered (one Q6 OR counted once) = 114 printed-choice marks; mandatory answer selection totals 100. No workbook or source data changed.

## 2026-09-21 — CA Inter practice-session source indexes converted to Excel

Reviewed `first_run/scripts/build_sheet_jsons.py` and its two sheet-ready JSON outputs. Created a two-tab Excel workbook from all 496 descriptive question records and 400 study-material topic records, preserving source columns and list fields, with filters and frozen headers. Verified row counts and rendered both sheets. The question index covers 2023–2026 MTP/RTP/PYQ and contains metadata rather than full question or answer text; flagged that distinction for live YouTube practice-session planning.

## 2026-09-11 — CA Foundation Offline Retrieval Engine restored and launched

Inspected `books/ca-foundation/CA_Foundation_Offline_Retrieval_Engine_SMAT`
for Pranav and found that the supplied copy could not start because
`ca_retrieval/engine.py` was missing, although the entry points, supporting
modules, compiled cache, validation artifacts, and regression tests all expected
it. Restored the engine module using those existing interfaces, preserving the
Corrected V2 source-verified Example registry behavior. Validation now passes
with 37 documents, 2,757 effective blocks, and zero errors/warnings; all 12
regression tests pass. Completed a real Chapter 3 Example retrieval (8 source
items), added computer-specific verified GUI instructions to `QUICK_START.md`,
and launched the GUI successfully on this computer.

## 2026-08-24 — SECURITY.md Phases 1-3 built, verified, and deployed live

Pranav asked to review `telegram/SECURITY.md` (written the same day, off the
scraping-incident case study) and proceed with a phase-wise plan; then asked
to build and complete Phases 1-3 (of the plan's own §4 priority ordering).
All three built, smoke-tested, dry-run/import-checked against every real
tenant, then deployed to all affected live bots one at a time with fresh-PID/
fresh-heartbeat/clean-log verification after each restart -- same discipline
this repo's own history already established for every prior fix.

**Phase 1 -- per-user abuse controls** (SECURITY.md §4.1/§4.2/§3.A.2/§3.A.6):
new `telegram/bots/rate_limiter.py` (in-memory per-process sliding-window
limiter, `rate_limited()` decorator applied OUTERMOST at every handler
registration across `study_hub_bot.py`/`exam_hub_bot.py`/`faculty_bot.py`/
`myfiles_hub_bot.py`, plus an inline `check_and_notify()`/`check()` pair for
narrower per-action buckets at specific chokepoints: `study_hub_bot.py`'s
catalog search, `report_flow.py`'s email-send channel specifically (a
cooldown, not a block on Telegram delivery), `profile_flow.py`'s leaderboard
join/leave, `mcq_issue_flow.py`'s issue-report submit, `exam_hub_bot.py`'s
`send_pdf()`, and `myfiles_hub_bot.py`'s upload + OTP-attempt handlers) and
new `telegram/bots/input_guard.py` (free-text sanitization, applied to
Study Hub search/profile display-name/MCQ-issue description; a MyFiles Hub
upload validator -- size ceiling + an executable/script extension deny-list,
checked BEFORE download). New `rate_limit_hits` DB table (audit trail, also
feeds Phase 3). 36-check `smoke_test_rate_limiter.py`, all passing.

**Phase 2 -- central callback-data route registry** (SECURITY.md §4.5/§3.A.5):
new `telegram/bots/callback_registry.py` -- `CallbackRegistry.validate()`,
called once per bot right before `run_polling()`, parses every registered
pattern's literal callback_data prefixes and raises a loud `RuntimeError` at
STARTUP on a real collision or an unrestricted pattern coexisting with
another handler (exactly the bug class that recurred 3+ times per
`/CLAUDE.md`'s own callout) -- an unparseable pattern (outside this
platform's own established `^(a|b)(:|$)`/`^literal:` shapes) logs a loud
WARNING instead of either crashing or a false sense of safety. Wired into
`study_hub_bot.py`/`exam_hub_bot.py`/`faculty_bot.py` (not
`myfiles_hub_bot.py` -- its `ConversationHandler`-based routing is
structurally collision-safe already, explained in the module's own
docstring). Validated 0 collisions against every real bot's actual
registrations (4/4, 7/7, 9/9 patterns). 16-check
`smoke_test_callback_registry.py`, including a synthetic positive collision
control that genuinely raises.

**Phase 3 -- traffic-anomaly alerting** (SECURITY.md §4.6/§3.A.7): extended
`watcher_bot.py` (reusing its already-proven admin-DM pipe, not a new
system) with `check_traffic_anomalies()` -- two signals, cooldown-gated (not
edge-triggered, since a flood is a sustained condition) via a new
`traffic_anomaly_alerts` table that doubles as the audit trail: `high_volume`
(>150 `user_activity_log` rows from one `telegram_user_id` in 5 minutes,
across ANY bot) and `repeated_rate_limit_hits` (>10 `rate_limit_hits` rows in
5 minutes -- a stronger, more specific abuse signal). Verified against the
real live DB via `--once` (silent success, nothing to report) and a 7-check
`smoke_test_traffic_anomaly.py` (positive/negative controls, cooldown
suppression, real DB writes, cleaned up).

**Deployed live**: `1lavya-studyhub`, `1lavya-examhub`, `1lavya-myfileshub`,
`csarunchouhan`, `capranav-study`, `capranav-exam`, `1lavya-platform-watcher`
restarted one at a time -- each confirmed via fresh PID, fresh heartbeat,
`callback_registry` logging "0 collisions" in its own startup line, and a
clean `.crash.log` (the one pre-existing crash.log traceback found during
verification, an SSL "certificate has expired" error, is the SAME
machine-clock-reads-2030 issue already flagged in the 2026-08-22 entry
below -- confirmed stale by its file mtime, not from this restart). Full
regression suite (13 smoke-test files) re-run clean; `health_check.py`: 17
pre-existing issues, all pre-dating this session and unrelated to
`telegram/` (stale `question-bank`/`syllabus-engine` EXPECTED_DIRS, NUL
bytes in `books/bridge-course/`, two undocumented top-level folders) --
zero new issues from this work.

**Not done, deliberately** -- the remaining SECURITY.md §4 items (Admin
Portal CSRF/session hardening/MFA, the Cloudflare Tunnel + Access path) were
scoped by Pranav as Phases 4-7, not asked for yet; §4.7 (Admin Portal MFA)
and the Tunnel work both need a decision/action from Pranav first (a new
Cloudflare token, a hostname, TOTP enrollment) per the phase-wise plan
already given.

## 2026-08-22 — Backup pipeline audit: 3 real bugs found across 6 nights of production drift, all fixed; BACKUP-STRATEGY.md written

Pranav asked to (1) verify the backup pipeline (built 2026-08-16) is actually
working, (2) get a full strategy doc, (3) make sure there's no real data-loss
risk. Checked real state rather than re-asserting the build-time verification —
queried `backup_runs`' full history (10 rows) and Windows Task Scheduler's
actual run history, not just "is the task registered."

**Found the pipeline had been silently degraded for days**: Task Scheduler
triggered every single night without fail (0 missed runs) but the D1 mirror
phase had failed 4 of the last 5 nights. Root cause: another session's
unrelated feature work added a `session` column to `course_catalog` via
`ALTER TABLE` — the D1 replay's `CREATE TABLE IF NOT EXISTS` is a no-op
against a table D1 already has, so that column never reached D1, and every
insert referencing it failed. **Real disaster-recovery data was never at
risk** (DB snapshots + assets kept succeeding every night regardless, since
phases are deliberately isolated) — only the D1 convenience-mirror layer went
stale. Fixed structurally: D1 tables are now DROP + recreated from the
current authoritative schema every run (data was already being fully wiped
and reinserted regardless, so this costs nothing extra and makes the whole
bug class impossible, not just this instance). Verified against the real
4-nights-stale database: 37 tables, 12,834 rows, 0 errors.

**Two more real, independent bugs found the same pass**: every asset object
had been stored under a doubled `assets/assets/...` prefix since the very
first run (content always correct, just a wrong/undocumented path — fixed,
existing ~2,500 objects re-synced onto the correct prefix); and the
failure-alert DM function only logged on its own failure, never on success,
making "did Pranav actually get notified about those 4 bad nights"
genuinely unanswerable from the log alone — fixed to always log the outcome.
Also found (not a bug in this system) one run that failed with an SSL
"certificate expired" error traced to the machine's clock briefly reading
the year 2030 — flagged to Pranav as a clock-reliability concern, not fixed
in code since there's nothing in this pipeline to fix.

**Fixing the asset-prefix bug surfaced something bigger, investigated properly
before touching anything**: comparing old-vs-new prefix objects found 1,131
files (1.57GB) that existed under the old prefix with NO counterpart in the
freshly-corrected sync. Rather than assume either "just stale duplicates" or
"real data loss," checked directly: confirmed the old filenames genuinely don't
exist locally anymore, THEN confirmed the same content DOES exist locally under
a new naming convention (`CA_L3_P01_C0_U1-1_...` etc., matching the platform's
existing human-readable-ID scheme) -- a real, undocumented content-reorganization
pass happened locally between 08-16 and 08-20/22, apparently by someone else's
work this session hasn't seen logged. Confirmed benign (164 CA Final files alone
verified present under new names, in some cases split MORE granularly than
before) before deleting the 2,494 stale old-prefix objects -- byte-for-byte
ETag-verified first that nothing about the still-current 1,363 files was lost.
Also found and flagged (not deleted, not this session's file): a 1.25GB
`Study Materials.zip` sitting directly in the live-served `study_bot/` folder,
undated pre-rename safety copy, harmlessly-but-redundantly swept into the
backup by the same sync.

**New `telegram/BACKUP-STRATEGY.md`** — the full strategy doc Pranav asked
for: what's backed up and why, every alternative considered and rejected
per data type (full vs incremental vs continuous replication for the DB;
R2 vs S3/GCS/a second local drive; D1 mirror vs R2-only vs Postgres;
full-reupload vs delta sync for assets), the real 6-night track record
table, all bugs found with dates (including the rename discovery above),
the restore procedure, and honest RPO/RTO limitations (~24h RPO, manual RTO
-- this system makes data survivable, not the service self-healing). Final
clean end-to-end run confirmed after all fixes: D1 37 tables/12,836 rows,
assets 0 uploaded/1,363 unchanged/0 failed. Full detail there; this log
entry is the pointer.

## 2026-08-18 (cont'd, 2) — "1-10 MCQs" progress broadcast, new "Show Chapter List" button, live HTML-escaping bug found+fixed

Third and final tier of the day's MCQ-activity broadcast series: students
with 1-10 MCQs answered (the gap between the 0-MCQ nudge and the >10
congrats campaigns). Confirmed via AskUserQuestion: include the exactly-
10 boundary case (closes the gap between the two earlier campaigns
cleanly), message direction, and a genuinely new interactive feature --
"Show Chapter List" jumping straight to the student's own most-practiced
chapter list, all exam types/years mixed, per Pranav's explicit spec.

Investigated before building: confirmed the platform ALREADY has
everything needed for "all exam type/years mixed" -- both McqBank/
QuestionBank already support a "MIX (All)" sentinel for exam_type/year,
and `_build_chapter_screen()` already appends an "All Chapters" trailing
button. No new aggregation logic was needed -- built new
`_students_own_mcq_subject()` (resolves a student's own most-practiced
(course, level, subject) from their real attempt history via the live
mcq_bank, never guessed) and extended `exam_hub_bot.py`'s "restart" branch
a second time (already extended once earlier today) for a third variant,
`restart:bcastchapters:<campaign_id>` -- proven behaviorally identical to
bare "restart" for the 99.9% real-traffic case via new regression checks,
with a defensive fallback if the resolved subject has zero content on
that specific bot (cross-bot mismatch protection, unneeded but present
for the real 23 recipients -- verified none had one).

**Real bug caught live, not in testing**: one student's real Telegram
first_name is literally `⏤͟͞𝘿𝙞𝙖𝙣𝙖™ </>` — the unescaped `</>` broke
Telegram's HTML parser (400 "can't parse entities"), silently failing
delivery to exactly that one recipient during the live broadcast. Root-
caused immediately (not guessed), fixed with proper `html.escape()` on
all Telegram-supplied free text before HTML interpolation (applied to
both this script and the earlier same-day nudge script, which had the
identical latent vulnerability), then retried delivery to just that one
student (not a full resend) — succeeded, preserved as a second row in
`broadcast_deliveries` alongside the original failed attempt, an honest
history rather than overwriting it.

8 new regression checks in `smoke_test_exam_hub_wallet.py` (Show Chapter
List: happy path with real MCQ history resolving the correct subject/
exam_type/year and rendering the real chapter screen; graceful fallback
with zero history; bare-restart unaffected). All 5 bots restarted, 0
tracebacks since. **Live result: 23/23 recipients delivered** (22 on the
first pass + 1 retry after the escaping fix) — `campaign_id=11`. This
closes the loop on MCQ-activity segmentation for today: every real
student who's answered 1+ MCQ now falls into exactly one of the two
activity-based campaigns (1-10 or >10), and everyone who's started but
never practiced got the third (0-MCQ) campaign earlier today.

## 2026-08-18 (cont'd) — "Haven't practiced yet" nudge broadcast, 2 new tracked buttons

Pranav asked for a second broadcast: students who've started an exam-
capable bot but never practiced a single MCQ, nudged with their own bot's
real MCQ counts by subject/level (chapter-wise, pick any), their real
credit balance, and interactive buttons — all logged in the same
persistent tables built earlier today.

Confirmed 4 things via AskUserQuestion first: eligibility = zero MCQ
attempts anywhere platform-wide (rolled up by identity), not just on one
bot; go ahead with a small, carefully-tested addition to exam_hub_bot.py's
existing "restart" handler (the live "Continue Practicing" hot path) for a
tracked button rather than the less-safe "mode:mcq" shortcut; message
direction approved; preview-first.

**Real bug caught before writing any code**: the naive eligibility query
included 4 phantom telegram_user_ids with no matching `students` row at
all — orphaned `bot_interactions` residue from other smoke test suites'
incomplete cleanup, not real people. Fixed by requiring an INNER JOIN to
`students` — 64 candidates → 60 genuinely real eligible students.

Built: `exam_hub_bot.py`'s "restart" branch extended (not replaced) to
recognize `restart:bcast:<campaign_id>` alongside the existing bare
`restart` — proven behaviorally identical for the 99.9% bare-restart case
via a new regression check, only the new 3-part value triggers tracking.
`report_flow.py` gained a second generic `report:bcastdismiss:<campaign_id>`
branch (a "🔕 Not Interested" button, not report-specific, reusing that
already-registered prefix). `broadcast_sender.py` gained
`get_start_practicing_button_markup()`. Content breakdown reuses
`faculty_report.content_availability()` directly, filtered to
mcq_count > 0 only, personalized per recipient's own bot/tenant scope.

10 new regression checks added across `smoke_test_exam_hub_wallet.py` (the
restart extension) and `smoke_test_report_flow.py` (the dismiss button) —
both suites fully passing. All 5 bots restarted, 0 tracebacks since.
**Live result: 60 recipients, 58 sent, 2 failed** (same 2 permanent
Telegram-side cases as the earlier campaign — one blocked, one
deactivated). campaign_id=7 in `broadcast_campaigns`/`broadcast_deliveries`.

## 2026-08-18 — "10+ MCQs" congrats broadcast + persistent, trackable broadcast infrastructure

Pranav asked to broadcast a congratulations message to every student who's
answered more than 10 MCQs, nudging them to get their report via the
existing report flow (Telegram/Email/Both, their choice) — explicitly NOT
a proactive send (no confirmed contact details for most students). Asked
several clarifying questions first per his explicit "don't assume": MCQs
answered (not shown), nudge not proactive-send, exact per-student count
(not "10+"), preview-first. Mid-conversation he added a real
infrastructure requirement: every broadcast should be persisted (category,
timestamp, chat_id, bot_id, message content, interaction tracking), not
another one-off unlogged script like 2026-08-17's welcome-bonus broadcast.

Built: `broadcast_campaigns`/`broadcast_deliveries` tables (schema.sql);
`telegram/database/broadcast.py` (create_campaign/log_delivery/
log_interaction/campaign_summary); `telegram/tools/broadcast_sender.py`
(reusable bot-resolution + raw HTTP send, extracted from the 2026-08-17
script). Real interaction tracking via a "📊 Get My Report" inline button
whose callback_data encodes the campaign_id — wired into
`report_flow.py`'s ALREADY-REGISTERED `report:` callback prefix (a new
`bcast:` sub-value), so **no bot script needed any new handler
registration** — deliberately avoiding this codebase's own documented
callback-collision bug class. A tap logs a real interaction against that
exact delivery row, then drops straight into the existing channel-picker
flow (the button IS the on-demand trigger).

`telegram/tools/send_mcq_congrats_broadcast.py`: eligibility = MCQs
answered > 10, all-time, rolled up by 1LAVYA username (multi-device
merged), excluding admin/smoke-test accounts — 12 real students (11–148
answered). Real bug caught by Pranav's own preview check: the first
preview used a hardcoded placeholder count (999) instead of a real
number — fixed to query the preview recipient's own real answered-MCQ
count live (103), re-previewed, confirmed, then broadcast for real.

6 new regression checks added to `smoke_test_report_flow.py` (the "bcast:"
branch: real interaction logged, bot_id read from callback_data not
context.user_data, a second tap doesn't overwrite the first timestamp, a
stale/unmatched campaign_id doesn't crash) — full suite passing. All 5
bots importing `report_flow.py` restarted (0 tracebacks since). Backfilled
2026-08-17's welcome-bonus broadcast CSV into the new tables too, so the
persistent record covers both real broadcasts sent so far, not just future
ones. **Live result: 12/12 sent, 0 failed** — and a real student tapped
"Get My Report" 20 seconds after receiving it, confirming the whole
tracked pipeline end-to-end in production before this was even reported
back as done.

## 2026-08-17 — Faculty Comprehensive Report: level-wise segmentation, username-rollup identity, Day End Report, colorful PDF

Pranav asked whether a faculty-level bot-usage report already existed
(one did — `telegram/admin_portal/faculty_report.py`, built 2026-08-14),
then asked for it to break out **by level** (CS Arun Chouhan has 3 live:
CMA Foundation/Intermediate/Final Law), be obtainable as a **"Day End
Report"** every day from the Admin Portal, additionally auto-save a PDF
to a folder while the platform is new, and be **colorful and easy to
understand** — while staying 100% deterministic, Python + SQL only, no
AI/manual content. Presented a plan first (per his ask), confirmed 2
design forks via AskUserQuestion (username-rollup identity vs. raw
chat_id; one combined document vs. separate files per level — both
answered with the recommended option), then built.

`faculty_report.build_report()` restructured: one level-block per
(course, level) the tenant serves (resolved from `content_scope`, no new
config), each with all 6 sections + a scorecard (unique students/MCQs
shown/avg accuracy/time spent). Sections 3–5 now key on the student's
permanent 1LAVYA username (every linked phone's activity merged),
matching `leaderboard_metrics.py`'s own identity model, with a new "Chat
ID(s)" column so a faculty can still identify/message a specific device.
New `telegram/tools/generate_day_end_faculty_reports.py` — a
run-to-completion batch script (same shape as `backup_to_cloudflare.py`,
not a `bots.json` process), scheduled via a new Windows Task Scheduler
job **"1LAVYA Day End Faculty Reports"** (daily 23:50 local), saves each
real faculty's day-end PDF to `telegram/reports/day_end/{tenant_id}/`.
Real bug caught by the script's own first run: `faculty_report_deliveries
.status` is CHECK-constrained to `('sent','failed','downloaded')`, no
`'saved'` value — fixed to log `"downloaded"`. A "Day End (Today)" button
was added to `/reports/faculty` itself for on-demand use.

PDF made colorful: navy section-header bars, a per-level banner + 4-tile
scorecard, green/amber/red accuracy badges by threshold, alternating row
bands — all inline styles (xhtml2pdf's weak CSS support, CLAUDE.md §7).
One real regression caught by testing: `letter-spacing:.03em` triggered
xhtml2pdf/reportlab's known `em`-unit parsing failure (same bug class
already documented in `branding/README.md`'s Phase-1 gotcha) — caught via
a stray warning on PDF build, removed. Visually verified via a
headless-Edge screenshot of the rendered HTML against real production
data before trusting the layout (this repo's own standing discipline).

`smoke_test_admin_portal.py` gained 7 new checks, full suite **280/280
passing**. Both real faculties' reports (capranav: 1 level, csarunchouhan:
3 levels) regenerated end-to-end against live data with no errors.
`1lavya-admin-portal` restarted and confirmed live. Full detail:
`telegram/admin_portal/README.md`'s "Revised 2026-08-17" section.

## 2026-08-17 — One-time welcome-bonus credit + broadcast sent to 92 real students

Pranav asked for a 1000-credit welcome bonus for every student whose
wallet balance shows 0, plus a broadcast DM telling them about it (from
1LAVYA, pointing at Study & Exam Bots, support@1lavya.com). Read
`telegram/FIRST_PROMPT.md` + `/TELEGRAM-TEST-MODE-SYSTEM.md` first — this
reuses the already-existing, audited `wallet.grant_signup_bonus()`
mechanism (1000 credits, one-time-per-username-ever, idempotent), not a
new credit type.

Given this touches real production wallets and DMs ~100 real people
(outward-facing, irreversible), confirmed 3 things via AskUserQuestion
before writing anything: exclude the 2 admin/faculty accounts sitting in
`students` (CAPRANAV = Pranav's own chat, Official1lavya), use the drafted
message text as-is, and send a live preview to Pranav's own chat first
before the real broadcast.

Built `telegram/tools/welcome_bonus_broadcast.py` (dry-run by default,
`--preview` sends only to Pranav, `--live` is the real thing). Eligibility
= real student (excludes 2 synthetic smoke-test rows + the 2 admin
accounts) with a CURRENT balance of exactly 0, checked live — this
doubles as "hasn't already received the bonus," since the 13 students who
already had it (via natural usage since 2026-08-16) all showed non-zero
balances. Delivery bot per student resolved from `bot_interactions`
(whichever bot they've actually started a conversation with — Telegram
requires this) — never a fixed bot.

Dry run: 92 eligible, 0 errors. Preview: sent to Pranav's chat via
`capranav-exam`, accidentally sent twice (this session re-ran `--preview`
to verify an unrelated stdout-encoding fix, not a script bug — the mass
loop only sends once per student per run). Pranav approved the wording.
**Live run: 92/92 credited (1000 each), 90/92 messages delivered** — 2
failed for permanent Telegram-side reasons (one blocked the bot, one
account deactivated); both were still credited per the agreed scope (only
delivery failed, not eligibility). Split: 82 via `csarunchouhan`, 7 via
`capranav-exam`, 3 via `1lavya-examhub`. Full per-student audit trail:
`telegram/database/run/welcome_bonus_broadcast_live_20260817T135227Z.csv`.

Not scheduled/repeating — this was a one-time proactive run of an
already-live mechanism, not a new automated flow. Re-running the script
later is safe (idempotent) but would only pick up students who are new or
have never been granted since, matching its own eligibility check.

## 2026-08-17 — Test Mode tenant-scoping bug fixed (CS Arun Chouhan's bot was showing CA content)

Pranav reported: typing "test" on CS Arun Chouhan's bot (CMA Law
`content_scope`, no CA content at all) showed the CA Inter Advanced
Accounting test catalog. Confirmed real, root-caused directly (not
guessed): `test_flow.py`'s picker (`_available_courses`/`_levels`/
`_subjects`) queried `predesigned_tests` globally with no tenant filter
at all — unlike `exam_hub_bot.py`'s own MCQ/Descriptive picker, which has
filtered every list through `SCOPE_TRIPLES` since 2026-08-12. Test Mode
was simply never wired into that existing mechanism when built
2026-08-16; invisible until `csarunchouhan` (via `faculty_bot.py`) became
the first genuinely scope-mismatched tenant to exercise it.

Fixed by threading `host` through the whole picker chain and filtering
every course/level/subject list through the same `host._scope_allows_*()`
predicates `exam_hub_bot.py` already exposes — no new scoping mechanism
invented. Added a second, independent defense-in-depth guard directly in
`_start_test()` (the actual wallet-debiting, session-creating action every
path funnels through) so a stale callback or future picker bug can never
again bill/start a test outside a bot's own tenant scope. The "jump to CA"
shortcut on the graceful-deny screen is now scope-gated too. A tenant with
zero real overlap (csarunchouhan today — no CMA content exists in
`predesigned_tests`) now gets an honest "not for your subjects yet"
message instead of either the wrong catalog or a platform-appears-empty
one.

14 new regression checks in `smoke_test_test_flow.py` (§18), simulating a
CMA-scoped host by wrapping the real `exam_hub_bot` module and overriding
only the 3 scope predicates — exercises the real picker/guard code, not a
reimplementation. Full suite 94/94 passing; `smoke_test_exam_hub_wallet.py`
re-run clean (41/41). Deployed: `1lavya-examhub`, `capranav-exam`,
`csarunchouhan` all restarted, confirmed clean startup logs, confirmed
`csarunchouhan` resolves to `mcq`/`descriptive` courses = `['CMA']` only.

Also updated `/TELEGRAM-TEST-MODE-SYSTEM.md` (new §5.8, plus updated §9/
§11/§12) with the full writeup, and answered Pranav's follow-up question
("what's the roadmap for Test Mode on other subjects") by actually
inspecting the real content for every other live subject
(`csarunchouhan`'s CMA Law, CA Inter Costing, CA Foundation Accounting/
Economics/Quant): all of it is flat `exam_type: "PRACTICE"` chapter-tagged
content, not real MTP/RTP/PYQ sittings — so Pre-Designed Tests can never
extend to these subjects no matter how much more content is added; the
already-designed-but-deferred Student Customised Test (chapter picker +
marks-target assembly) is the only viable path, and is now flagged in
§12 item 7 as such rather than just "a nicer alternative." Also surfaced
a real, separate gap while confirming this: descriptive content outside
CA Inter Advanced Accounting doesn't reliably carry a real marks value
(e.g. csarunchouhan's Companies Act bank: `"Marks: Not stated in
source"` on every record) — needed before a marks-target assembly could
work for that content, Pranav's call on how to resolve.

## 2026-08-16 (cont'd) — Backup Snapshot Summary added to Admin Portal; real D1-mirror idempotency bug found + fixed

Pranav asked for the backup pipeline (built earlier this same session --
see the entry below) to show its status under the Admin Portal's
`/bots` page, plus asked what kind of backup this actually is and why
that approach was chosen over the alternatives.

Built: new `backup_runs` DB table (schema.sql) -- one row per invocation
of `backup_to_cloudflare.py`, inserted as `'running'` at start, finalized
with real per-phase metrics at the end, same "one fast local query, no
live external call" audit-trail pattern every other table in this schema
already follows. New `telegram/admin_portal/backup_status.py` +
a "Backup Snapshot Summary" card wired into the existing `/bots` template
-- last-run status, DB snapshot sizes, D1 tables/rows mirrored, assets
uploaded/unchanged/failed, secrets backed up, and a recent-runs history
table. Honestly renders `--` (not `0`) for any phase a run skipped.

**Real bug found by actually re-running the backup a second time**: the
D1 mirror's schema replay assumed `sqlite_master.sql`'s stored CREATE
TABLE/INDEX text would carry the "IF NOT EXISTS" clause schema.sql's own
DDL always uses -- it doesn't; SQLite silently strips that clause from
the canonical stored text. The first-ever run (empty D1 database) worked
by coincidence; the second run (against the now-populated database) hit a
real `SQLITE_ERROR: table students already exists`. Fixed by re-inserting
the clause before replay (`_ensure_if_not_exists()`), verified by actually
re-running against the already-populated database (32 tables, 4,104 rows,
0 errors) rather than trusting the fix by inspection. Both the original
failure and the fixed success are visible in `backup_runs`' own history.

Verified further: a real full run with asset sync confirmed the
incremental design works as intended -- 0 uploaded, 1,244 unchanged, 35s
total (vs. ~22 minutes on the very first full upload). Page rendering
checked via Flask's `test_client()` (same technique
`smoke_test_admin_portal.py` uses for auth-gated routes) plus a real
headless-Edge screenshot of the output. `1lavya-admin-portal` restarted,
confirmed clean. Full detail: `telegram/admin_portal/README.md`'s new
"Backup Snapshot Summary" section.

## 2026-08-16 — Test Mode + wallet/billing: comprehensive root-level reference doc written

Closing out the multi-round Test Mode + wallet/billing build (Pre-Designed
Tests, wallet identity/credits/Razorpay recharge, size tiers, the 6-issue
manual-QA fix round, and full activity logging — see prior sessions'
history), Pranav asked for the whole system documented end-to-end in a new
root-level MD file "so that any new AI model can also refer this MD file
and understand and build the things exactly from the point we left off."

Wrote **`/TELEGRAM-TEST-MODE-SYSTEM.md`** (repo root, per his explicit
instruction — a deliberate exception to this platform's usual convention
of keeping feature docs like `PROFILE-SYSTEM.md`/`LEADERBOARD-SYSTEM.md`
inside `telegram/`) — architecture, the full wallet/credit/identity model
and why each rate/decision was chosen, the Test Mode engine end-to-end
(sitting catalog generation, size tiers, timers/grace period, activity
logging/topic tracking/exact-point resume), the complete data model, a
file-by-file map, testing discipline, a dated build chronology, the
recurring concurrent-session git-entanglement lesson (§10, worth any
future session reading before committing to `schema.sql`), and every open
point named honestly with its actual plan (no real live Razorpay payment
completed yet; the 2-PDF evaluation bundle is the clear next build; AI
evaluation blocked on pricing; Study Hub/MyFiles Hub wallet extension;
`sweep_expired_grants()` unscheduled; Custom Test out of scope; no
student-facing activity-log UI yet).

Added a pointer at the top of the original planning doc
(`telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md`) marking it
supplementary now that the root file is canonical, and a new row in
`telegram/FIRST_PROMPT.md`'s index table pointing to both. Ran
`tools/health_check.py` (16 pre-existing, unrelated failures only — stale
`EXPECTED_DIRS`, 9 pre-existing NUL-byte files elsewhere, undocumented
`capranav_com/` — nothing new from this change) and `tools/file_index.py`
to regenerate the index. No code changed this round — documentation only.

## 2026-08-16 — All 9 bots restarted after a ~9.7h outage; Cloudflare R2+D1 off-machine backup pipeline built and deployed

Asked to check/restart all bots — found all 9 down (heartbeats stale ~9.7h,
same class of gap as 2026-08-15's entry below). Restarted via
`manage_bots.py restart`, confirmed clean startup logs, fresh heartbeats.

Separately, walked `telegram/` for a real inventory of what's genuinely
local-only and irreplaceable: `database/platform.db` (880KB then, 83
students/395 MCQ attempts/etc.), `assets/myfiles_bot/myfiles_hub.db` +
its `uploads/` (real student-uploaded files), and ~1.4GB of live-served
PDFs/JSON — all gitignored by design, zero off-machine copy. Presented a
backup plan (R2 for blobs, D1 for a queryable mirror); Pranav confirmed
the direction, then separately created a Custom Cloudflare API Token
(`Workers R2 Storage: Edit` + `D1: Edit`) and asked where to get R2's
Access Key ID/Secret — derived both **without any extra dashboard step**
per Cloudflare's own documented mechanism (Access Key ID = the token's
own `id`, Secret = SHA-256 of the token value), verified with a real
signed S3 `ListBuckets` call before trusting it. Confirmed staying on the
existing EfficientCorporates (ECPL) Cloudflare account (not a separate
1LAVYA account Pranav also created) since `1lavya.com`'s domain currently
lives there.

Built and deployed `telegram/tools/backup_to_cloudflare.py`: SQLite-
consistent DB snapshots (via `.backup()` API, WAL-safe), a full D1 mirror
of `platform.db` (table order derived at runtime from
`PRAGMA foreign_key_list`, never hand-maintained), Fernet-encrypted
`.env`/`creds.txt` with a real `--decrypt-secret` restore path, and an
MD5-vs-R2-ETag asset sync that only uploads new/changed files and never
deletes remote objects based on local state. Registered as a new Windows
Task Scheduler job, "1LAVYA Platform Backup," nightly at 3:30 AM
(deliberately not a `bots.json` entry — batch job, not a heartbeat
process). Bucket + D1 database both auto-created on first run.

**Verified for real, not just trusted**: D1 mirror cross-checked against
live `platform.db` query results (29 tables, 3,981 rows; `course_catalog`
matched exactly at 975 rows on two checks minutes apart, confirming the
mirror reflects genuine current state, not a stale copy); the encrypted-
secrets path proven with an actual download→decrypt→read round trip.
First full asset sync (the one-time 1.4GB upload) completed clean before
session end: **1,244 files uploaded, 0 failed**, full run (DB snapshots +
secrets + asset sync) in ~1,298s. Every future nightly run only touches
changed files, so this cost is paid once. `health_check.py`: same 16
pre-existing failures, nothing new introduced.
Full detail: `telegram/database/README.md`'s new "Off-machine backup"
section, CLAUDE.md's 2026-08-16 dated entry under §11, and memory
`1lavya-cloudflare-account`.

## 2026-08-15 — Whole platform found down; Windows autostart + 30-min health-check automation built

Asked to check if the bots were working. Found ALL 9 down — heartbeats
stale ~4.7 hours, matching the known "no auto-restart-on-crash, single
machine" gap flagged in CLAUDE.md right after §2. Restarted everything
via `manage_bots.py start`, confirmed all real content loading /
Telegram API calls succeeding, no tracebacks.

Pranav then asked for two standing safeguards: an auto-run-at-Windows-
startup script, and a Task Scheduler job every 30 minutes to restart
anything found down. Built:
- `manage_bots.py` gained a new `ensure-running` action — starts a bot
  that isn't running, RESTARTS one that's running but heartbeat-stale
  (a hung process, not just a dead one).
- `telegram/tools/ensure_bots_running.bat` (new) — the unattended entry
  point, explicit `.venv` python (not bare `python` off PATH), logs to
  its own file, `ping`-based startup delay (not `timeout.exe`, which
  refuses to run without a real console — found by testing).
- A Startup-folder shortcut (`shell:startup`) pointing at the canonical
  `.bat`, and a new Task Scheduler job "1LAVYA Bots - Health Check"
  (every 30 min, indefinite). A true pre-login "at boot" trigger needed
  admin rights this shell doesn't have — documented as a known gap with
  the exact command Pranav can run himself if he wants it too; the two
  mechanisms built already bound any outage to ≤30 min regardless.

**Real bug found and fixed**: my own earlier manual test (verifying the
new stale-heartbeat-restart path) left a timezone-naive timestamp in
`bot_heartbeats` for one bot. `analytics.fetch_heartbeats()`'s existing
try/except only guarded the parse step, not the later naive-minus-aware
subtraction one line down — so it crashed, uncaught, aborting the WHOLE
function and silently dropping every other bot's heartbeat too. This was
live and real: it put `1lavya-platform-watcher` into an actual 60s crash
loop. Fixed the bad DB value and hardened `fetch_heartbeats()`/
`_parse_iso()` (treat naive as UTC, catch `TypeError` too) so one bad row
can never do this again. Restarted all 9 bots to pick up the fix (Python
doesn't hot-reload).

**Also chased and ruled out**: every restarted bot briefly appeared as
TWO OS processes (a `.venv` one and a global-Python child of it) —
looked exactly like a duplicate-instance/Telegram-polling-conflict risk,
investigated seriously (including a live-monitored kill-and-watch test)
before `.venv\pyvenv.cfg` confirmed it: normal Python 3.11+ Windows
venv-launcher stub+worker behavior, not a bug. Noted in
`telegram/database/README.md` so a future session doesn't re-chase it.

`health_check.py`: same 16 pre-existing failures, nothing new.
`file_index.py` re-run. Full detail: `telegram/database/README.md`'s
"Self-healing autostart" section, `CLAUDE.md` section 11's matching entry.

## 2026-08-14 (cont'd) — Faculty Master DB table + Masters > Faculty Details

Same day, right after the Faculty Comprehensive Report entry below:
Pranav asked to "maintain a faculty table where we can store the details
of the faculty," and directly asked JSON file vs. DB table — confirmed
via AskUserQuestion: **DB table**. Separately reported not being able to
find the new report/email box anywhere — confirmed it's the Admin Portal
at **port 8788** (not the old dashboard at 8787), sidebar **Analytics →
Faculty Comprehensive Report**; the running process's PID/heartbeat was
checked live to confirm it was serving the just-built code, not a stale
process.

Built `faculty_master` (`schema.sql`) — `contact_email`/`contact_phone`/
`notes`, one row per `tenant_id`, upserted. Deliberately does NOT
duplicate `tenants.json`'s `content_scope`/`kind`/`onboarding_fee` (those
stay there, read directly by the bot scripts at startup) — this is
purely the new administrative layer. New
`telegram/admin_portal/faculty_master.py` (list/get/upsert) and a new
**Masters → Faculty Details** page (list + per-tenant edit form),
audit-logged like every other portal write. Removed the `contact_email`
field I'd added to `tenants.json` earlier the same day (nothing depended
on it yet) and repointed the Faculty Comprehensive Report's email
pre-fill at the new table instead.

**Real mid-build issue, caught and fixed**: the live `1lavya-admin-portal`
process re-runs `init_schema()` on every request, so a live request
landed between this table's first draft (had 2 fee-status columns I
later decided to drop, to avoid duplicating `tenants.json`'s existing
`onboarding_fee`) and the trimmed final version — the real DB table got
created with the wrong (draft) shape before the file settled.
`CREATE TABLE IF NOT EXISTS` doesn't retroactively fix that. Caught by
checking `PRAGMA table_info` before trusting it (not by inspection
alone), confirmed 0 rows existed yet (nothing real to lose), fixed with a
`DROP TABLE` + re-`init_schema()`.

**Verified**: `smoke_test_admin_portal.py` grew from 205 to **220
checks** — list/edit pages, create-then-update via the same `tenant_id`
primary key (proves no duplicate row), unknown-tenant 404, empty-field-
clears-column, the report page's email box reflecting a freshly-saved
address, and full auth-gating. One check specifically **captures and
restores** whatever real row already exists for the tenant it exercises
(rather than overwriting-then-deleting), since this route can hold real
admin-entered data by the time the test runs again. `health_check.py`:
same 16 pre-existing failures, nothing new. `1lavya-admin-portal`
restarted twice this session (once after the report build, again after
this table), confirmed live both times with clean startup logs. Full
detail: `telegram/admin_portal/README.md`'s "Faculty Master DB table"
section, `CLAUDE.md` section 11's matching dated entry.

## 2026-08-14 — Faculty Comprehensive Report built (Admin Portal)

Pranav asked for a full, deterministic per-faculty report, for any date
range: subjects/levels live for that faculty + how many MCQ/Descriptive
questions exist; chapter-wise practice (most accessed, MCQ attempted/
correct/time spent) across every subject/course that faculty serves;
student-wise performance; a fixed last-7-days student-wise trend; which
chapters each student practices most; and a question-wise difficulty
analysis (which MCQs are most often wrong, and what students chose
instead of the right answer) — all downloadable as PDF/XLSX/HTML by
button and emailable straight to the faculty, with no commentary, just
raw facts in properly-headed tables (his explicit wording).

Explored the existing Admin Portal stack first (`app.py`, `analytics.py`,
`exporters.py`, `document_catalog.py`, `student_analytics.py`,
`report_delivery.py`/`cf_email.py`, `brand_kit.py`, `schema.sql`) rather
than inventing new patterns, then built:

- **`telegram/admin_portal/faculty_report.py`** (new) — the query/render/
  email layer. Six sections: `content_availability()` (static, reuses
  `document_catalog.question_bank_rows()`'s human_id-derived counts),
  `chapter_stats()`, `student_performance()`, `student_last7days()` (a
  fixed real-last-7-UTC-days window, independent of the report's own date
  range), `student_chapter_matrix()` (ranked within each student's own
  activity), `question_difficulty()` (≥2-attempt filtered, surfaces the
  single most commonly chosen WRONG option per question, not just "wrong"
  in general). `build_report()` assembles all six; `render_full_report_
  html()`/`build_report_pdf()`/`build_report_xlsx()` share one section
  list so the 3 formats can't drift; `send_report_email()` reuses the
  same Cloudflare Email Service backend `report_delivery.py` already
  uses, sent from the Admin Portal's own dedicated address.
- **`faculty_report_deliveries`** table (`schema.sql`) — audit trail of
  every download/email attempt, same discipline as `report_deliveries`.
- **`contact_email`** field added to faculty tenants in `tenants.json`
  (null today — pre-fills the send box when set, always overridable by
  typing a different address).
- **3 new routes** in `app.py` (`GET /reports/faculty`, `GET /reports/
  faculty/<tenant_id>.{pdf,xlsx,html}`, `POST /reports/faculty/
  <tenant_id>/email`) + a new template `faculty_full_report.html` + a new
  sidebar entry, **Analytics → Faculty Comprehensive Report** — distinct
  from and alongside the existing per-bot "Faculty Report" page (kept
  unchanged). Scoped to a whole tenant, not one bot, since a faculty can
  have more than one bot (e.g. Pranav's `capranav-study` +
  `capranav-exam`) — this report pools activity across all of them.

**Real bug found and fixed by actually running the code against the live
DB** (not by inspection): `student_performance()`'s "last active"
tracker started every student at `None` and called `max()` across a mix
of `None` and real ISO timestamp strings on their first row — Python
can't compare `str`/`NoneType`, so every real call crashed immediately.
Fixed by filtering `None`s out before `max()`, then re-verified clean
against all 4 real tenants (`capranav`, `csarunchouhan`, `1lavya-examhub`,
`1lavya-studyhub`) with real data — every section returns correct,
non-crashing rows (`1lavya-studyhub` correctly shows all-empty activity
sections, since it's a study-only bot with no exam-hub data — an honest
empty state, not a bug).

**Verified**: `smoke_test_admin_portal.py` grew from 182 to **205
checks**, all passing — the report page, all 3 downloadable formats
against a real tenant, an unsupported-format 400, an unknown-tenant 404,
invalid-email rejection, a mocked successful email logging a `'sent'`
row with the exact address, a mocked forced-failure email logging a
`'failed'` row with the error detail and flashing without crashing, and
full auth-gating on every new route. `health_check.py`: same 16
pre-existing failures, nothing new. `tools/file_index.py` re-run.
`1lavya-admin-portal` restarted to deploy; confirmed live on port 8788
with a clean startup log (0 tracebacks) and the new route correctly
redirecting when unauthenticated. Full detail: `telegram/admin_portal/
README.md`'s "Faculty Comprehensive Report" section, and CLAUDE.md
section 11's matching dated entry.

## 2026-08-13 (cont'd, 3) — Admin Portal Overview rebuilt into a real analytics dashboard

Pranav asked for the Admin Portal's Overview page (`:8788/`, previously a
3-tile placeholder) to become a full executive dashboard: new-student
onboarding trends over any date range, new questions added (MCQ/
Descriptive split, which subjects), top performing students, total
platform time-spent today (+ bot-wise), questions attempted, subject/
chapter drill-down, and a faculty roster — all filterable, exportable
(CSV/Excel/HTML/PDF, including the charts themselves), sub-tab organized,
"top industry level." Told explicitly not to assume anything and to ask
first.

Asked 4 clarifying questions via AskUserQuestion before writing any code
(all answered with the recommended option): Overview becomes a **summary
dashboard** (charts + top-line tables per sub-tab) that links into the
already-built detailed Analytics pages (Student Master, Course Catalog,
Faculty Report) for full drill-down, rather than duplicating them;
**"New Questions Added" tracks forward from today only** — confirmed no
historical ingestion-date data exists anywhere (content JSON files never
carried an "added on" field), so a new `content_ingestion_log` DB table
starts the real trail today rather than an approximate git-history
backfill; **charts are self-built inline SVG**, no new JS charting
library, matching this repo's existing no-CDN/self-contained practice;
**"Top Performing Students" reuses the exact accuracy-%-with-minimum-
attempts-floor definition** already live on the student-facing Telegram
leaderboards, not a new ranking invented for this view.

**Built**: `schema.sql`'s new `content_ingestion_log` table, backfilled
honestly with 7 real rows for the same-day Cost & Management Accounting
wiring (see the entry below) as its first real data. 8 new query
functions in `telegram/database/analytics.py` (`fetch_student_
onboarding`, `log_content_ingestion`, `fetch_content_growth`,
`fetch_time_spent_today`, `fetch_questions_attempted`,
`fetch_top_performers`, `fetch_faculty_roster`) plus `document_catalog.
platform_question_totals()` — every one individually tested against the
real live DB before being wired into any route. `telegram/admin_portal/
charts.py` (dependency-free inline SVG bar/donut charts) and a
**separate** `charts_pdf.py` (reportlab-native `VerticalBarChart`/`Pie`
flowables) for PDF chart export — found before shipping, not after, that
`xhtml2pdf` (the engine every table export already uses) has no reliable
inline-`<svg>` support, so PDF chart export needed its own code path;
reportlab is already a hard dependency here (via `xhtml2pdf` and
`generate_base_formats.py`), so this added nothing new to install. Both
chart types verified visually (a rendered bar and pie PDF read directly
via Claude's own PDF-viewing capability) before trusting them, not just
structurally.

Rebuilt `overview.html` with 4 sub-tabs (Students / Content / Performance
/ Faculty) sharing one date-range picker (`_date_range_from_args()`,
7d/30d/90d/all-time presets + explicit from/to). `fetch_faculty_roster()`
correctly counts "questions contributed" ONLY from a faculty's own
`faculty/<tenant_id>/` content files — verified against real data before
trusting it: `capranav`'s own `exam_content` still points at the
flagship's shared Advanced Accounting bank, and the roster correctly
shows 0 questions contributed for him (matches his real
`own_content.status == "not_ingested"`), while `csarunchouhan` shows his
real 1,025 MCQ + 47 descriptive.

**Verified, multiple layers**: every new analytics function unit-tested
against the real live DB directly before wiring into any route (caught
nothing wrong — all returned sensible real numbers first try).
`smoke_test_admin_portal.py` grew from 110 to **182 checks, 0 failures**
— every tab render, every preset/filter combination, all 16 table ×
format export combinations (content-type checked, not just status), all
10 chart × format export combinations with a non-trivial size check, an
unknown chart_id and an unsupported format both 404 cleanly, a
data-correctness spot check (the Content tab's on-page total matches
`fetch_content_growth()`'s own return value verbatim), and full auth
gating on every new route. **Visually verified** via headless-Edge
screenshots of all 4 tabs against real live data — on a **throwaway**
diagnostic Flask instance with auth monkeypatched to a no-op (never the
real deployed process, never a change to `auth.py` itself), on a
different port, killed immediately after. One real mistake made and
caught in the same pass: cleaning up leftover diagnostic processes
afterward, a PID-matching command accidentally killed the REAL production
`1lavya-admin-portal` process instead of only the throwaway ones —
caught immediately via `manage_bots.py status` showing it "not running,"
fixed with a normal `restart` (which was needed anyway to deploy the new
code), verified back online with a fresh PID and a clean startup log, and
every OTHER bot process's PID confirmed unchanged throughout. Re-ran
`smoke_test_course_catalog.py` and `validate_content_json.py` afterward
— both still clean, no regression. `health_check.py`: same pre-existing
failures, nothing new from this change (structural: only new files in
already-existing folders, no new top-level folder).

Documented in `telegram/admin_portal/README.md`'s new "Overview rebuild"
section, `telegram/database/README.md`'s `content_ingestion_log` note,
and `CLAUDE.md` section 11.

## 2026-08-13 (cont'd, 2) — CA Inter Cost & Management Accounting MCQs (700 questions, 7 chapters) reviewed and wired live

An external contributor (govinjee@gmail.com) submitted MCQ batches for CA
Inter Cost & Management Accounting into a new
`telegram/assets/exam_bot/ca-inter-cost-accounting/` folder, in 3 rounds:
(1) an initial Ch2 Material Cost file (75 MCQs) reviewed and found to be
missing `human_id`/`subject`, using `"Intermediate"` instead of the
catalog's `"Inter"`, and inventing a `"Unit 1"` where the real syllabus
chapter has no sub-units — flagged back via a drafted (unsent) email;
(2) a corrected Ch4/Ch5 resubmission (200 MCQs) that fixed every one of
those gaps — reviewed clean, including independently re-deriving every
"Hard"-difficulty numeric question's arithmetic, and a second draft email
sent reporting no issues; (3) 5 more chapters (Ch3, Ch6, Ch7, Ch8, Ch9 —
500 more MCQs, 700 total across the folder) submitted the same way.

All 700 questions passed the full validation pass: structurally clean
(`telegram/tools/validate_content_json.py --file`, 0 errors on every
file), `human_id` correctly formatted and matching `course_catalog`
exactly (course=CA, level=Inter, paper=04, chapter/unit correct per
chapter), zero `mcq_id`/`human_id` collisions either within the 7 files
or against any of the ~4,500 questions already live on the platform.

**Wired into `telegram/config/tenants.json`**: all 7 files added to
`1lavya-examhub`'s `exam_content.mcq_json` list (entries 6–12), per the
2026-08-13 standing rule that every question on the platform joins the
flagship bot's pool — the notes field's own running history was updated
to document this addition the same way every prior one is documented.
Verified end-to-end **before** touching the live process: imported
`exam_hub_bot` in an isolated interpreter with `BOT_ID=1lavya-examhub`
and confirmed all 700 questions resolve correctly to
`CA → Inter → Cost and Management Accounting` with all 7 chapters
showing in the right order — no "Unknown" bucket, no exceptions. Only
then restarted the `1lavya-examhub` process (the only bot that reads this
tenant's `mcq_json`); confirmed via its log that all 12 files (5 prior +
7 new) loaded cleanly with 0 tracebacks since restart, and via
`manage_bots.py status` that every other bot's PID was untouched. Full
platform-wide `validate_content_json.py` re-run clean (14 files, 0
errors/0 warnings) and `smoke_test_course_catalog.py` /
`smoke_test_admin_portal.py` both re-run clean afterward.

Total platform MCQ pool: 4,497 → 5,197. Two draft emails sit unsent in
Gmail for Pranav to review/send at his discretion (the flagged-issues one
for the superseded Ch2 file, and the clean-review one for Ch4/Ch5) — no
email was sent for this final 5-chapter/700-question batch since it was
wired in directly per Pranav's own instruction, not flagged for revision.

## 2026-08-13 (cont'd) — Standing "everything joins the flagship" rule, human_id made live, Issue Reports in Admin Portal

Pranav clarified and extended the earlier CMA-merge decision: it's not a
one-off, it's a standing rule — **every question on the platform becomes
part of the flagship `1lavya-examhub` bot's pool**, MCQ and descriptive
alike, with provenance tracked via tagging, never via withholding content.
Also asked for issue reports to have a real place in the Admin Portal, and
flagged that the human-readable MCQ ID work from 2026-08-11
(`generate_mcq_human_ids.py`) never actually went live.

**Merged csarunchouhan's descriptive bank into the flagship** (47 Companies
Act questions) — `tenants.json`'s `descriptive_json` became a list (same
pattern `mcq_json` already used). Investigating first (never assumed)
found a real data-sync bug: the bot-facing file had been copied from its
raw, already-human-id'd source *before* the ID retrofit ran, so all 47
records were silently missing it (confirmed via full field-diff: every
OTHER field was byte-identical between raw and bot-facing — human_id was
the only gap). Patched from the raw source directly, verified 47/47 now
correct, 0 NUL bytes, valid UTF-8/JSON.

**`_content_owner` provenance tagging built** (`exam_hub_bot.py`) —
inferred purely from each source file's own path (`.../faculty/<tenant_id>/`
→ that tenant; everything else → `"1lavya"`), no per-record field or
schema change needed on any content file. Persisted into
`exam_hub_mcq_attempts`/`exam_hub_descriptive_events` via 2 new DB columns
(`content_owner`, `human_id`) so usage can eventually be broken down by
source, not just by which bot logged it. Verified: 3,472 "1lavya" + 1,025
"csarunchouhan" MCQs, 455 + 47 descriptive, exactly matching expected
counts, 0 missing human_id anywhere in the merged pool.

**human_id made genuinely live** — it was already 100%-covered and
globally unique across every merged content file (verified by direct
audit before touching anything), but was never actually shown to a
student or used anywhere, which is what Pranav meant by "not yet made
live." Added as the first line (🆔) of every question's meta text, both
Descriptive and MCQ. Threaded through the "Report Issue in MCQ" flow too
— `mcq_issue_reports` gained a `human_id` column (via `db.py`'s migration
list, since that table was created earlier the same day and CREATE TABLE
IF NOT EXISTS doesn't retroactively ALTER it), shown on the category-
picker screen and in the thank-you confirmation, so a filed report is
always traceable to one exact, citable question.

**"MCQ Issue Reports" — new Admin Portal Analytics page**
(`/analytics/issue-reports`), same paginated/filterable/exportable (CSV/
Excel/HTML/PDF) shape as every other Analytics view, joined to `students`
for a display name. Read-only — no status-editing UI, not asked for.
Verified with a synthetic DB row through Flask's real test_client (login,
render, all 4 export formats, cleanup confirmed), then added as a
permanent new step in `smoke_test_admin_portal.py` (own the same
insert-verify-cleanup discipline the rest of that suite already uses) —
full suite re-run clean.

All 3 changes verified end-to-end against real data/DB before deploying.
Restarted `1lavya-examhub`, `capranav-exam`, `csarunchouhan`,
`1lavya-admin-portal`; confirmed 0 tracebacks since restart in every log
(checked from each process's actual restart marker line, not a naive
timestamp string comparison — the first attempt at that check gave a
false positive). `README_Bot2_ExamHub.md` and `telegram/FIRST_PROMPT.md`
updated to match.

## 2026-08-13 — Chapter-label fix, CMA Law merged into flagship, MCQ issue reports, real "I'm Done" summary

Pranav flagged 4 things after using the rebuilt Exam Hub: (1) chapter
names showing without Unit distinction, so many chapters looked
repeated; (2) CMA Foundation/Intermediate Law MCQs (Arun's content, but
Pranav's stated position: these are 1LAVYA assets Arun was given access
to, not his exclusively) missing from the flagship `1lavya-examhub` bot;
(3) wanted a "Report Issue in MCQ" 4th button (category picker + free
text, stored for later resolution); (4) wanted "I'm Done" to show a
quick today's-summary before offering the existing report pipeline.

**Chapter duplication root-caused, not just noticed**: confirmed via
data audit that 2 files (CA Foundation Accounting, Business Economics)
were ingested with a bare "Chapt N"/"Chapt. N" `chapter_label` with no
Unit differentiation — e.g. "Chapt 1" literally shared by 7 different
real units, "Chapt 7" by 4. The underlying grouping (`chapter_slug`) was
always correct; only the DISPLAYED label collided. Fixed with
`_disambiguate_chapter_labels()` in `exam_hub_bot.py`: detects colliding
labels within each (course, level, subject) scope and appends the real
unit/chapter name via a `course_catalog` join (same human_id mechanism
built the day before for course/level/subject resolution) — falls back
to a title-cased slug if even that lookup fails, so nothing is ever left
silently ambiguous. Verified: 0 duplicate labels remaining in both
affected subjects; the flagship's already-good "AS 11: ..." style labels
confirmed byte-for-byte unchanged (only colliding groups are touched).

**CMA Law merged into the flagship**: added
`telegram/assets/exam_bot/faculty/csarunchouhan/mcq_questions_extracted.json`
(1,025 MCQs, both CMA Foundation and Intermediate) as a 5th `mcq_json`
entry in `tenants.json`'s `1lavya-examhub` tenant, per Pranav's explicit
ownership call. MCQ only, not descriptive, per his literal ask. Verified
live: `1lavya-examhub`'s McqBank now reports `courses = ['CA', 'CMA']`,
4,497 total MCQs, no id collisions.

**"Report Issue in MCQ" built**: new `bots/mcq_issue_flow.py` (same shape
as `profile_flow.py`/`report_flow.py` — host script owns the callback
registration and text_router priority-check, this module never imports
`exam_hub_bot.py`/`McqBank`, every field it needs is passed in by the
caller at call time). New `mcq_issue_reports` DB table (bot_id,
telegram_user_id, mcq_id, course/level/subject/chapter, category
[wrong_question/wrong_answer/typo_error/wrong_mapping/other],
description, status, created_at) — visible today via the Admin Portal's
existing generic "Data Export" page, no dedicated triage UI built yet
(not asked for). New 4th button on the MCQ answer screen; category →
free-text → stored → "Thanks for your report... you may also mail us at
support@1lavya.com" confirmation, restoring the same Next/Chapter-List/
I'm-Done keyboard the student was already looking at. Cancel path
verified too.

**"I'm Done" real bug found while building this**: it was wired to the
exact SAME bare `restart` callback_data as "Start Over" — tapping it
silently reset straight to the Mode picker with zero summary, ever. Not
a design choice, a real bug. Fixed: new `imdone` action, new
`student_analytics.fetch_today_summary()` (UTC-day, platform-wide MCQs
attempted/answered/correct + descriptive viewed + a lightweight
"time spent today" metric — deliberately simpler than the full report's
all-time session-span number, documented as such), shown before offering
the SAME existing on-demand report flow (`report_flow.py`'s
`report:ondemand_yes`/`_no` buttons, called directly — zero new
report-delivery code, just setting `report_flow_bot_id` the same way
that flow's other two entry points already do).

Everything verified against the real database and real content before
deploying (full click-journey simulations: category-report round-trip
confirmed stored correctly with all fields, cancel path, I'm Done summary
reading real today's-DB-rows) — not just structurally. Deployed to
`1lavya-examhub`, `capranav-exam`, `csarunchouhan`; confirmed clean
restart, no new tracebacks. `README_Bot2_ExamHub.md` and
`telegram/FIRST_PROMPT.md` updated to match.

## 2026-08-12 (cont'd, 2) — Exam Hub rebuilt Mode-first; real Subject-picker gap closed

Following the bug fix and scale review below, Pranav confirmed a real gap
he'd suspected: Exam Hub never had a Subject-level picker at all
(Course→Level→Mode→ExamType→Year→Chapter, nothing narrowed by Subject) --
at CA Foundation this merged 3 subjects (Accounting/Business Economics/
Quantitative Aptitude) into one undifferentiated Chapter list. Asked which
flow order he wanted (Subject-before-Mode vs. Mode-first with Course/
Level/Subject restricted to real content); he chose Mode-first.

Rebuilt `exam_hub_bot.py`'s flow as Mode -> Course -> Level -> Subject ->
Exam Type -> Year -> Chapter -> question, every step auto-skipped when
only one real option exists, every list derived live from actual loaded
content (dropped the old hand-maintained `COURSES`/`AVAILABLE_DATA`
"show everything, gate later" globals -- a student never taps a dead
end now). This surfaced and fixed a real correctness gap along the way:
2 of 3 CA Foundation content files had no `subject` field at all, and
the flagship's descriptive bank had no `course`/`level` field on ANY
record (a "matches everything" hack only ever correct because exactly
one course/level/subject was in scope when it was written). Fixed by
deriving (course, level, subject) from each record's `human_id` via a
join against the platform's own `course_catalog` DB table (the same
mechanism already used for chapter/unit naming) -- validated against
every real record across every tenant before shipping: 0 unresolved.
Subject buttons use index-based `callback_data` from the start (learned
from the chapter bug fixed minutes earlier the same day).

Updated `faculty_bot.py` to match (calls the renamed `resolve_entry()`,
callback pattern gained `subject`), added an `exam_hub_sessions.subject`
DB column via `db.py`'s migration list, and verified with 3 full
simulated click-journeys against real data (multi-subject CA Foundation
MCQ with actual chapter/queue build, full-auto-skip CA Inter Descriptive
matching the pre-rewrite zero-extra-taps behavior, csarunchouhan's CMA
Foundation/Intermediate subject differentiation) before deploying.
Deployed to `1lavya-examhub`, `capranav-exam`, `csarunchouhan`; confirmed
clean restart, no new tracebacks. `README_Bot2_ExamHub.md` and
`telegram/FIRST_PROMPT.md` updated to match. Full detail in both docs'
2026-08-12 entries.

## 2026-08-12 (cont'd) — Telegram platform scale review + real exam_hub_bot.py bug fixed

Pranav asked for an independent PM+CTO-level review of the Telegram bot
platform against a 100k-student target (currently ~100). Findings (not
code-quality issues — the feature layer is solid): single local-Windows-PC
deployment with no auto-restart/backups, untested SQLite single-connection
concurrency under python-telegram-bot's asyncio loop, no working
billing/quota enforcement despite a well-designed schema, long-polling
(no horizontal scale path), content requiring a full bot restart to
reload, dev/prod sharing one DB file, a recurring callback_data bug
class, no rate-limiting, and fully-manual faculty onboarding. Logged as a
brief, durable callout in `/CLAUDE.md` (right after §2) and pointed to
from `telegram/FIRST_PROMPT.md`, so any future session sees it before
adding more features on top.

Also fixed a real, live bug Pranav reported: MCQ practice silently did
nothing after selecting Year. Root cause, confirmed via the actual
`1lavya-examhub.log` traceback: `exam_hub_bot.py`'s Chapter-picker built
`callback_data=f"chapter:{chapter_slug}"` using the raw slug — some
content (newly-ingested CA Foundation Accounting/Business Economics, 150
records across both) slugifies full chapter/unit names, well past
Telegram's 64-byte callback_data limit, so `edit_message_text` failed
outright (`Button_data_invalid`) for the WHOLE chapter list the moment
even one slug was too long (3 of 71 chapters for CA Foundation MCQs).
Fixed by carrying a small integer index in callback_data instead,
resolved back via `context.user_data` (same fix pattern already used for
Study Hub's buttons). Also hardened the `year`/`chapter` handlers against
a second bug found in the same logs (`KeyError: 'exam_type'`, from
reading prior-step state via raw dict indexing instead of a checked
lookup — a stale keyboard tapped after a bot restart crashed silently)
with a `_require_state()` helper that shows "session expired, start
over" instead of crashing. Verified against the real offending data
before and after the fix (not just structurally), then restarted and
confirmed clean on all 3 affected processes (`1lavya-examhub`,
`capranav-exam`, `csarunchouhan`).

Separately confirmed a real, related gap Pranav suspected: Exam Hub has
no Subject-level picker at all (Course→Level→Mode→ExamType→Year→Chapter,
nothing narrows by Subject) — at CA+Foundation this already merges 3
subjects' chapters into one undifferentiated list, and 2 of the 3
source files don't even carry a `subject` field yet. Not built — needs
Pranav's decision on ordering (Subject before Mode, vs. Mode-first) since
it changes the flow for every course/level combo. Full detail:
`telegram/FIRST_PROMPT.md`'s 2026-08-12 status entries.

## 2026-08-12 — MCQ_PROMPT.md: AI-model prompt for generating MCQ JSON correctly

Pranav asked for a "Skill plus prompt" file to give AI models generating
MCQ JSON from PDFs, so future batches don't need the repair/normalize
pass the CA Foundation Accounting/Economics batches just needed. Built
`telegram/base_formats/MCQ_PROMPT.md` -- a paste-ready system prompt,
directly encoding every real defect found and fixed this session:
invalid JSON escaping (raw LaTeX leaking into strings), inconsistent
answer-key formats (letter vs text vs list index) across chapters
within one file, field-name typos, and — confirmed by finding the exact
source — a chapter_slug ("intro-to-as") copy-pasted from
`base_formats/mcq_input_example.json`'s own AS-1 example record into an
unrelated Economics chapter and never updated. Built on top of the
already-existing (concurrent-session-built) `generate_base_formats.py`'s
authoritative field contract (MCQ_FIELDS/PROVENANCE_FIELDS) rather than
re-deriving field names from scratch. Includes a worked example, a JSON
validity checklist, content-fidelity rules (never silently "correct" a
source figure, flag "Needs Review" instead), and an 8-point mandatory
self-check before the AI returns output. Documents that any resulting
batch still needs ingestion-script preflight (duplicate IDs,
correct_option validity, course_catalog cross-check) — the prompt
reduces defects, doesn't replace verification. health_check.py: same 16
pre-existing issues, nothing new.

## 2026-08-12 — CA Foundation Accounting + Business Economics MCQs fixed, normalized, made live

Finished the ingestion of the 2 new MCQ content sets. Built
`telegram/tools/ingest_ca_foundation_accounting_economics_mcqs.py`:
repaired the 3 invalid-JSON files (found a real `":="` typo along the
way), merged both subjects' scattered chapter/unit files into 2 clean
per-subject files (1,595 Accounting + 918 Economics MCQs), resolved
every question's chapter/unit via one regex against the source's own
(inconsistently formatted) unit fields -- no fuzzy matching needed.
4 more real bugs found via preflight checks: a Python falsy-zero
bug that dropped a valid `correct_answer: 0`, 3 different per-chapter
answer formats needing separate handling, a `mc_id`/`mcq_id` typo, an
`Options`/`options` capitalization typo. Corrected the source's own
inaccurate `exam_type: "MTP"` label to `"PRACTICE"` (self-authored, not
a real ICAI paper) matching existing convention. Extended
`generate_mcq_human_ids.py` with a new resolver; all 2,513 records got
human_ids, idempotent. Wired into `1lavya-examhub` via `tenants.json`,
restarted, confirmed loading both files clean. Admin Portal Question
Bank tab shows correct live counts (verified + screenshot). Content
validator 0/0, both smoke suites passing, health_check.py: same 16
pre-existing issues. Still open: faculty attribution (null), duplicate
detection, student tags. Full detail: `telegram/COURSE-CATALOG.md`.

## 2026-08-12 — CA Foundation Accounting: 4 missing chapters (8-11) found + real ICAI PDFs sourced

Pranav asked whether a new CA Foundation Accounting MCQ set's chapter
names matched our master syllabus. Checked chapter-by-chapter: Ch.1-7
matched exactly, but the new content also had Ch.8-11 (NPO Financial
Statements/Incomplete Records/Partnership & LLP Accounts/Company
Accounts) that didn't exist anywhere in course_catalog or our Study
Materials — asked Pranav for the official syllabus rather than guess; he
gave https://www.icai.org/post/19138. Confirmed all 11 chapters
(including the exact 6-unit splits for Ch.10/11) are real and match
ICAI's own syllabus exactly — our data was incomplete, the new content
wasn't wrong. Found the real PDF download links on that same ICAI page,
downloaded and verified all 15, added using the existing naming
convention, updated the source Excel, re-ran the full downstream chain
(build_master_catalog -> populate_course_catalog -> build_knowledge_base_
catalog). course_catalog grew 960->975 rows, no collision. 3 new
regression checks added, full suite passing, content validator 0/0,
1lavya-studyhub + 1lavya-admin-portal restarted and confirmed loading all
1102 catalog rows live. health_check.py: same 16 pre-existing issues.
Still open: the new MCQ content itself (3 invalid-JSON files, schema
inconsistencies, wrong subject name on Economics) hasn't been
fixed/ingested yet — only the taxonomy gap is closed. Full detail:
`telegram/COURSE-CATALOG.md`.

## 2026-08-12 — 4 document/question catalogues added to Admin Portal Course Catalog

Pranav asked the existing Course Catalog page to become a live Study
Materials catalogue (reading `knowledge_base_documents.json`), plus 3
more: Exam Materials, Revision Material, and a Question Bank catalogue
(chapter-level MCQ+Descriptive counts). Also asked whether 3 PDFs he'd
just added to Study Materials (CA Inter Law's "Other Laws" — General
Clauses Act, Interpretation of Statutes, FEMA 1999) were showing up —
they weren't, since `knowledge_base_documents.json` derives from
`1Lavya_Study_Hub_File_Mapping.xlsx`, not a live folder scan, and those 3
files had never been added there. Fixed at the root (verified real
chapter titles from the PDFs themselves, added 3 Excel rows, re-ran the
whole downstream chain). Found and fixed a second real bug via the
catalog's own duplicate-key check: CA Inter Corporate and Other Laws'
printed chapter numbering restarts at Module 4 (Ch.1/2/3, "Other Laws"),
colliding with Module 1's own Ch.1/2/3 — verified this is the only CA
subject with that pattern, added a small documented offset
(`CHAPTER_NO_MODULE_OFFSET`) so Module 4 continues as 13/14/15.
`course_catalog` grew 957→960 rows.

Built `admin_portal/document_catalog.py` (Study/Revision Material =
course_catalog chapters joined to real documents; Exam Materials = flat
paper listing; Question Bank = MCQ/Descriptive counts from every
question's own human_id). Wired as a 5-tab strip on
`/content/course-catalog` (4 new tabs + the original Chapter Taxonomy,
kept not replaced), sharing one Course→Level→Subject picker, full
export support on every tab. CS/CMA Exam Materials sourcing from ICAI/
ICSI/ICMAI's own websites was raised and explicitly deferred as its own
task (asked via AskUserQuestion) — today's Exam Materials only covers CA
Inter Advanced Accounting (58 files); every other subject shows an
honest "not sourced yet" row. Found and fixed a third bug testing
Pranav's own example URL (subject=Accounting, when the real CA Inter
subject is Advanced Accounting): an invalid subject now falls back to a
real one instead of silently rendering an empty table.

Verified: course-catalog smoke tests +2 checks (41 total), admin portal
smoke tests 72→87, content validator still 0/0, visually confirmed via
headless-Edge screenshots, `1lavya-admin-portal` + `1lavya-studyhub`
restarted and confirmed loading the new catalog live, health_check.py
same 16 pre-existing issues. Full detail: `telegram/COURSE-CATALOG.md`.

## 2026-08-12 — New telegram/FIRST_PROMPT.md orientation doc

Pranav asked for a lean map file any agent can be handed to get oriented in
`telegram/` fast — folder-by-folder purpose, which doc to read for which
topic, read order, and a "how to inform your own working memory" section
(don't re-derive settled architecture, don't re-litigate locked scope,
verify visually not just structurally, ask before assuming on high-stakes
changes). Scoped to Telegram only (not the whole repo) and built to sit
*alongside* CLAUDE.md §11, not replace it — §11 stays the detailed dated
history/reasoning log; FIRST_PROMPT.md is the short index that points into
it. Explicit instruction: keep this updated going forward whenever
`telegram/` changes structurally — treat it like a living map, not a
one-time snapshot.

## 2026-08-12 — Real Course Catalog gap found + fixed; confirmed year-warning fix still holds

Pranav checked the live Admin Portal himself: "I saw many subjects and
chapters missing" for CA — correct. The first course_catalog build only
covered 2 of CA's 17 real subjects (Adv Accounting + Quant Aptitude); CA
Final had zero. CS/CMA were always complete. Root cause:
`rows_from_studyhub_catalog()` was hand-scoped to one subject instead of
importing `build_study_bot_catalog.py`'s own already-verified
`COURSE_META` (all 17 CA subjects, real paper numbers) directly.

Fixing this surfaced two MORE real bugs, both caught by the catalog's own
duplicate-key collision check doing its job: (1) CA Final Advanced
Auditing chapter 14 is genuinely 2 units (Banks/NBFCs) — fixed by parsing
the real unit number from each file's own filename (verified against all
314 real CA filenames first, 0 unmatched); (2) CA Inter Financial
Management chapter 9 has 6 real named units but EVERY filename says U0 —
fixed by checking each row's own Label text for an explicit "Unit N"
prefix (roman/arabic) as authoritative over the filename, and correctly
excluding 3 genuine chapter-level review files ("Comprehensive
Illustrations," "Test Your Knowledge," "Appendix") that aren't real
syllabus units at all.

Result: 957 catalog rows (up from 701), all 17 CA subjects present, CA
Final populated for the first time. human_id generator re-confirmed fully
idempotent against the larger catalog (0 new IDs — no new question
content, only catalog coverage). 5 new permanent regression checks added.
Visually re-verified: CA Final Financial Reporting (previously empty) now
shows its real 46-row structure. Also re-confirmed the "year" warning fix
from the day before is still clean everywhere (raw validator, both
dashboards, bot logs) — Pranav's separate ask to double-check this held.
Full detail: `telegram/COURSE-CATALOG.md`'s new section.

## 2026-08-11 — Course Catalog DB table + human-readable MCQ IDs + year-warning fix

Pranav asked for a Course/Level/Subject-wise Course Catalog view, that
this catalog become the single DB source of truth for every MCQ/
descriptive question's chapter/unit tagging (not independently typed),
and a new additive human-readable ID per question
(`CA_L2_P01_C3_U4_00876`), retrofitted onto ALL existing questions,
deterministically, via a catalog-driven script. Also asked to fix a
"Recommended field 'year' is missing" Content Health warning.

Investigated before building anything: found 4 different, mutually
inconsistent MCQ ID schemes already in production across the 4 existing
content files, but also found real, ALREADY-VERIFIED raw material to
build from (file 1's canonical CA Inter Adv Accounting index,
CS_CMA_Chapter_Catalog.xlsx's 647 real chapters w/ PaperNo,
StudyHub_Master_Catalog.xlsx's CA Foundation Quant Aptitude chapters —
none needed fresh research). Asked 4 clarifying questions before writing
code (CMA vs CO course code — every existing platform reference uses CMA,
not CO; CS level-number mapping; whether to re-verify paper numbers
against real sources; retrofit-now vs new-content-only pace) — confirmed:
CMA not CO, CSEET=L1/Executive=L2/Professional=L3, re-verify (all 4
paper numbers cross-checked against already-verified sources, confirmed
correct), and retrofit all ~2,500 existing questions now via deterministic
script.

Built: new `course_catalog` DB table (701 rows, 3 sources) via
`populate_course_catalog.py`; `generate_mcq_human_ids.py` — catalog-is-
authoritative retrofit (a real mismatch found+correctly resolved: CA
Foundation Quant Aptitude's MCQs all self-tag U1, but the real ICAI
material has no sub-unit structure there — catalog's U0 used instead,
loudly reported not silently patched), idempotent (verified via an actual
second real run assigning exactly 0 new ids). 2,486 questions across 6
files now carry a human_id alongside their existing internal ID. New
Admin Portal → Content → Course Catalog page (Course/Level/Subject
dropdowns, filterable/paginated/exportable). `smoke_test_course_catalog.py`
(new, 39 checks) + `smoke_test_admin_portal.py` (grew to 72). Content
validator: 0 errors/warnings platform-wide.

Also fixed the year warning: root cause was `--year` never passed when
converting Arun's CMA Foundation Law docx (375 records got `year: null`
while the sibling Intermediate file correctly had `"2026"`) — fixed at
the source, re-merged, re-validated. All affected bots restarted;
`health_check.py` shows no new issues. Full detail:
`telegram/COURSE-CATALOG.md`.

## 2026-08-11 — Admin Portal: Analytics tier built (universal table export, bulk report emails, full Student Master)

Same day as the Foundation tier, Pranav asked for: (1) download any DB
table as JSON/CSV/XLSX; (2) send the performance report by email to one
or many students, from the portal itself; (3) full Student Master
visibility; (4) pagination + filtering + Excel export on every tabular
view; (5) every analytics dashboard downloadable as CSV, and as HTML or
PDF on demand. Asked 4 clarifying questions first (report-sending scope,
recipient-email source, table-export scoping, build pace) — all answered
with the recommended option.

Built shared infrastructure (`exporters.py`): in-memory filter/paginate
helpers (reusing `analytics.py`'s already-tested functions unchanged,
deliberate given real data volumes), CSV/XLSX/JSON response builders, and
ONE shared branded-HTML-snapshot source reused for both "download as
HTML" and "download as PDF" (via `xhtml2pdf`) so the two never drift
apart. New Jinja globals `page_url()`/`clear_filter_url()` preserve
filter state across pagination.

Built 5 Analytics views (Student Master, Bot-wise Usage, Faculty Report +
chapter drill-down, Content Health, Email Analytics) + the generic Data
Export page (every real table, no scoping — Pranav's confirmed choice).
Student Master's bulk "Send Report to Selected" only emails students with
an already-confirmed email on file (never guessed/typed for them), sent
from the admin portal's own dedicated `reports@1lavya.com` address.
`smoke_test_admin_portal.py` grew from 26 to **68 checks**, all passing —
including a mocked bulk-send verified to skip the emailless student and
send to exactly the right address for the other, with precise (delivery-
id-based) cleanup of every test-inserted row. Visually verified via
headless-Edge screenshots (Student Master's real 65-row data, Data
Export's real table list). `health_check.py`: same 16 pre-existing
failures, nothing new. Full detail: `telegram/admin_portal/README.md`.

Still not built, by design: Masters display/editing, Faculty/New Bot
addition, Question Catalog metadata editor, Leaderboard edits, Users &
Access (RBAC) — each its own build → smoke test → confirmation cycle.

## 2026-08-11 — Admin Portal (Phase 4) foundation tier built + 3rd leaderboard added

Pranav asked to (1) build the 3 leaderboards (CS Arun Chouhan: CMA Inter +
Foundation Law; CA Pranav: CA Inter Advanced Accounts), all ranked by Top
10 Most Attempted / Most Accurate / Most Time Spent, and (2) start the
full Admin Portal — Flask, sidebar+sub-tabs, and an extensive module list
(analytics, masters, bot restart, question catalog edits, faculty/bot
addition, leaderboard edits, email analytics, bot logs), plus later
module-wise RBAC. Explicitly asked to be asked, not assumed.

Added the 3rd leaderboard entry to `leaderboards.json` (capranav-exam
posting, course=CA/level=Inter, same 3-metric set as the other two — all
still `status: "inactive"`, waiting on real channel IDs). For the Admin
Portal, asked 4 clarifying questions before writing code (auth approach
given RBAC is coming later; Question Catalog edit depth; build
sequencing across ~12 modules; confirmation-safeguard requirement for
destructive actions) — all answered with the recommended option: single-
admin login now (RBAC layers on later), metadata-only catalog editor
first, foundation-tier-first build order, explicit confirm dialogs on
destructive actions.

Built the Foundation tier: `telegram/admin_portal/` — Flask app
(`app.py`), single-admin session auth (`auth.py`, structured for RBAC
later via `role_required()`), an `admin_actions` audit-log table + writer
(`audit.py`), a branded sidebar shell (navy/gold, "Soon" badges for every
not-yet-built module so the full intended shape is visible), single-admin
login (credentials generated + given to Pranav once, only the hash
stored), Bot Status & Restart (calls `manage_bots.py`'s own `restart_bot()`
directly, not subprocessed), and Bot-wise Logs. Runs on port 8788,
alongside the existing `:8787` dashboard (not replacing it until
Analytics is migrated in a later tier). Registered as `1lavya-admin-portal`
in `bots.json` so `manage_bots.py` manages it like every other process.

Found and fixed one real bug during verification: `NAV_SECTIONS`' dict key
`"items"` collided with Python's own `dict.items()` method — Jinja2's
`section.items` attribute lookup silently grabbed the method instead of
the key, 500-erroring every page. Renamed to `"links"`. Also hit (and
resolved, not a code bug) two stale dev-server processes left listening
on port 8788 from manual testing that `pkill -f` couldn't find on Windows
— cleared by PID via PowerShell directly.

`smoke_test_admin_portal.py`: 26/26 passed via Flask's `test_client()`
(auth gating, audit logging, unknown-bot handling, a mocked real-bot
restart). **Manually verified against a real bot** (`1lavya-platform-watcher`):
actual restart, actual audit row, and a correctly-blocked unauthenticated
attempt. Visually verified via headless-Edge screenshots (login, Overview,
Bot Status table with all 9 other bots' real live data). `health_check.py`:
same 16 pre-existing failures, nothing new. Full detail:
`telegram/admin_portal/README.md`.

**Not built yet, by design** (confirmed sequencing): Analytics tabs,
Masters display/editing, Faculty/New Bot addition (clarified: can only
ever generate config — BotFather registration has no API, stays a manual
human step), Question Catalog metadata editor, Leaderboard edits, Users &
Access (RBAC). Each gets its own build → smoke test → confirmation cycle.

## 2026-08-11 — Real UX bug: report flow re-asked for contact info already on file

Pranav: "even after sharing the mobile number and email id once, if I
again ask for report than it again asks for my number/email... does not
the bot check with existing database." Confirmed real —
`_handle_channel_choice()` never checked `students.mobile_number`/`.email`
before asking, on every single report request. Fixed in three places in
`report_flow.py` (initial channel choice, the "both" mobile→email handoff,
and the post-delivery upsell) via a new `_existing_contact()` helper —
each now skips straight to delivery when the needed value(s) are already
on file, matching Pranav's exact ask ("directly send and then confirm its
went"). A student who wants to change a stored value still can via the
"profile" menu. New smoke-test coverage
(`step7e_reuses_existing_contact_info`): asserts zero prompts, a real
delivery, and the correct audit-trail event. All 5 bots restarted, full
smoke test re-run clean.

## 2026-08-11 — Real live email-delivery bug found + fixed (unquoted From header)

Minutes after the Cloudflare Email Service integration went live, Pranav
reported a real failure on the csarunchouhan bot: "report has been
generated but delivery to one or more channels failed." Investigated via
the actual `report_deliveries`/`report_flow_events` rows (not guessed) —
found the exact Cloudflare error: HTTP 400
`"email.sending.error.email.invalid"`. Reproduced the exact failure
through the real production code path, then isolated `from`/`to`
independently (both worked alone) before finding the real culprit:
csarunchouhan's own `bots.json` `display_name` — `"CS Arun Chouhan (Study
+ Exam Practice, one bot)"` — contains a comma and parentheses, and
`cf_email.py`'s hand-rolled `f"{name} <{email}>"` From-header wasn't
RFC-5322-quoted for that case. Every other bot's display name is plain
enough that this never surfaced elsewhere. Fixed with Python's own
`email.utils.formataddr` via a new `cf_email.build_from_header()` helper;
verified with a real send through the exact failing combination —
delivered. Added a permanent regression check to
`smoke_test_report_flow.py`. Also found and fixed, same delivery: a
`telegram.error.TimedOut` on `send_document` (a one-off ~32KB-file network
blip) — added one bounded retry (2s backoff) for the transient
TimedOut/NetworkError classes only, real errors still fail immediately.
All 5 bots restarted with both fixes; smoke test re-run clean.

## 2026-08-11 — Cloudflare Email Service wired in + on-demand report trigger

Pranav added real `CF_EMAIL_API_TOKEN` to `telegram/.env` and asked to wire
up Cloudflare's Email Service (send-only, no inbox) for the student report
pipeline: one dedicated unmonitored email per bot, all on one domain;
support@1lavya.com / admin@1lavya.com referenced for real issues / new-bot
requests; good 1LAVYA branding; plus a new "report"/"analysis"/"email"/
"mail" on-demand trigger (parallel to "profile") so a student can request
their report anytime, not just at the 20-question milestone.

Researched the actual product first (WebSearch/WebFetch — Cloudflare Email
Service, public beta since 2026-04-16, real REST API contract) rather than
guessing, then asked 4 clarifying questions before touching anything real
(domain onboarding status, Account ID, subdomain-vs-single-domain
addressing, support/admin mailbox reality) since this touches live DNS/
domain config I can't verify or set up myself. All confirmed: domain
already onboarded, Account ID provided, single-domain/different-local-
parts addressing (my recommendation, accepted), support@/admin@ already
real mailboxes.

Built: `telegram/database/cf_email.py` (raw REST client), rewrote
`report_delivery.py` (per-bot `from_email` resolved from `bots.json`,
fully 1LAVYA-branded HTML body via new `brand_kit.render_email_footer_html()`),
threaded `bot_id` through `report_flow.py`'s entry points, added the
on-demand trigger (`report_flow.start_report_flow_on_demand()`, reusing
the milestone flow's entire pipeline) and wired it into all 3 bot
scripts — `study_hub_bot.py` for the first time (never had report_flow
wired in before). Verified with a REAL send through the actual production
code path to Pranav's own email — confirmed delivered. Smoke test
extended (Step 4 rewritten for the new backend, new Step 7d for the
on-demand flow) — all passing, deliberately network-free by design (no
`load_dotenv()` in the test script). All 5 affected bots restarted clean.
Full detail: `telegram/REPORT-PIPELINE.md`'s new section.

## 2026-08-11 — Leaderboard system built (Phase 3) + exam-attempt picker redesigned

Pranav asked for: (1) the profile's Target Attempt field to be a guided
Year-then-Month picker instead of free-text quick-picks; (2) a full
leaderboard system inside the profile — students join up to 5 live
leaderboards, scoped strictly to their own Course+Level, each mapped to
one-or-more Telegram channels broadcasting nightly at 11:11 PM, with
multiple ranking metrics (accuracy/questions attempted/time spent) driven
by a metrics master; (3) a faculty-facing student-wise/chapter-wise report.

Given the real architectural forks (leaderboard scope granularity, config
vs. admin-UI management, single-vs-multi-metric display, minimum-attempts
floor scope, faculty-report timing), asked 6 clarifying questions via
AskUserQuestion before building — all confirmed: eligibility is fully
manual per leaderboard (JSON config, same pattern as bots.json/
tenants.json), multiple metrics render as SEPARATE mini-rankings per
leaderboard (never a blended score), the minimum-attempts floor gates ALL
metrics blanket-style, and the faculty report is built now as a dashboard
card (not deferred to Phase 4).

Built: `telegram/config/leaderboards.json` + README (2 example CMA Inter/
Foundation Law boards, both inactive pending real channel IDs);
`telegram/database/schema.sql`'s new `leaderboard_participants` +
`leaderboard_broadcast_log` tables; `telegram/database/leaderboard_metrics.py`
(config loading, eligibility matching, 3-metric registry, ranking
computation aggregated per-username across every linked phone);
`profile_flow.py`'s new 🏆 Leaderboards menu (join/leave, 5-board cap) and
Year→Month exam-attempt picker; `telegram/bots/leaderboard_broadcaster.py`
(standalone nightly job, fixed UTC+5:30 IST offset, `--once` test mode,
full broadcast-log audit trail); `analytics.py`'s new
`fetch_faculty_report()` + a new expandable "Faculty Report" dashboard
card at `:8787`. New `smoke_test_leaderboards.py`: 28/28 passed against
the real DB (multi-phone metric aggregation, exact-at-floor boundary,
6th-join rejection, broadcast logging). Faculty Report verified against
real production data through the actual dashboard pipeline; static
dashboard regenerated, live `:8787` server restarted and confirmed
serving the new data. All 5 profile-flow bots restarted clean. Full
detail: `telegram/LEADERBOARD-SYSTEM.md`.

Nothing is broadcasting live yet by design — every leaderboard ships
`status: "inactive"` until Pranav creates real Telegram channels, adds the
posting bot as channel admin, and fills in real chat_ids (a Telegram-side
step this session cannot do).

## 2026-08-11 — Student profile system built (identity foundation for Phase 3 Leaderboard)

Pranav asked for students to be able to set up/edit a profile (username,
display name, avatar, email, phone, course & level, exam attempt) by
texting "profile"/"change profile" to any bot, with confirmation before
editing and username permanently locked once set. Confirmed via
AskUserQuestion: build this now as the Phase 3 (Leaderboard) identity
foundation, avatar pulled live from Telegram (never stored), course/level
via guided picker, username Instagram-style (3-20 chars, letters/numbers/
underscore, case-insensitive).

Built: `telegram/database/schema.sql`'s new `student_profiles` table
(username PK, shared fields: display_name/course/level/exam_attempt) +
`students.lavya_username` link column (via `db.py`'s column-migration
mechanism, since SQLite has no `ALTER TABLE ADD COLUMN IF NOT EXISTS`).
Extracted `telegram/bots/contact_utils.py` out of `report_flow.py` for
shared mobile/email validation. New `telegram/bots/profile_flow.py` — full
trigger/state-machine/menu flow, supporting one username linked across
multiple chat_ids (a student's several phones) with shared vs. per-chat-id
fields correctly separated (email/mobile stay per-chat-id; Pranav's own
reasoning — different phones might use different emails). Wired into
`exam_hub_bot.py`, `study_hub_bot.py`, `faculty_bot.py` with an explicitly
scoped new `profile:`/`profileconfirm:` callback prefix (guarding against
the callback-pattern-collision bug class already found 3x this session)
and text-router priority ordering so a profile edit in progress is never
swallowed by search/report-flow. New `smoke_test_profile_flow.py`: 41/41
passed against the real DB with synthetic, self-cleaning chat_ids. All 5
affected bot processes restarted, verified via `bot_heartbeats.started_at`
(not log-grepping) and clean startup logs. Full detail:
`telegram/PROFILE-SYSTEM.md`.

Also this session: filled in the real admin chat IDs for the down/up
watcher (see the entry directly below, same day, done first).

## 2026-08-11 — Platform watcher activated with real admin chat IDs

Pranav provided his own and Arun's real Telegram chat IDs. Filled into
`telegram/config/alerts.json`'s `admin_chat_ids`, flipped
`1lavya-platform-watcher`'s `bots.json` status to `active`, started it as a
managed process. Verified real end-to-end delivery, not just configuration:
safely perturbed one low-stakes bot's (`1lavya-dashboard`) alert state to a
fake "down" via direct DB update (no real process touched), ran a real check
pass, confirmed a genuine down→up transition alert — then sent an explicit,
clearly-labeled one-time test DM to each admin chat ID individually and
confirmed both delivered successfully via the Telegram API's own response.
Platform down/up alerting is now genuinely live, not just theoretically
configured.

## 2026-08-11 — Post-delivery CTAs, Student Master dashboard, Unique Visitors explained

Pranav's next round of live-test feedback, all addressed:

1. **No CTA after report delivery.** Chose Telegram-only, got the PDF, conversation
   just stopped — should have offered email too, then asked continue/done.
   Restructured `report_flow.py`: extracted `_deliver_report()` (sends through a
   given channel set, reusable) out of the old `_finalize()`; after delivering
   through exactly ONE originally-chosen channel, now offers the other one
   (`_offer_upsell_or_wrapup`) via the same echo-confirm collection, with a new
   `report_flow_upsell` flag telling the confirm-step to send only the NEW
   channel, never re-send what's already gone out. Either way, the conversation
   now always ends with an explicit "Continue Practicing" / "I'm Done" question —
   "Continue" deliberately reuses bare `restart` callback_data to fall through to
   `button_router`'s already-tested reset handler, no new logic needed for it.
   Email-sent message now explicitly says to check Spam and mark "Not Spam".
   `report_deliveries.channels_requested` now logs the actual channels attempted
   per call (not the original label) since one milestone can now produce two
   delivery rows. New smoke-test step (`step7c`) covers the whole upsell/wrap-up
   path — all green, ~13 new checks.
2. **Student Master dashboard section.** New card: Chat ID, Name, Mobile, Email,
   Faculty, Courses (derived from real activity, not a bot's full scope — a
   platform-only user shows "Self Study"), Last Seen, with a live text filter.
   New `analytics.fetch_student_master()`. Caught and fixed a real display
   redundancy along the way: the same course+level showed up twice (with and
   without subject, since exam-hub tables don't carry `subject` but
   `study_hub_events` does) — deduped, preferring the more specific version.
3. **"14+2=16 vs 32 Unique Visitors" investigated with real queries, not assumed
   — confirmed not a bug, two different populations.** Summing Student
   Breakdown's per-bot counts double-counts students active on multiple bots (2
   such students at the time, true unique = 15, not the naive sum 17). "Unique
   Visitors" counts ANY interaction across ALL 8 bots including Study Hub/MyFiles
   Hub, not just MCQ attempts — 18 of 33 total visitors had never attempted a
   single MCQ. Added a third, unambiguous stat tile ("Unique MCQ-Attempters,
   all-time") plus tooltips and a cross-reference note on Student Breakdown, so
   this can't cause the same confusion again.

All three verified: smoke test full pass, direct queries against real data, and
headless-Edge screenshots with real interactions simulated (dropdown switch,
text-filter input) to confirm the UI actually responds, not just that the
default view looks right. Restarted `1lavya-examhub`, `capranav-exam`,
`csarunchouhan`, `1lavya-dashboard`; confirmed all four running code newer than
every relevant source edit (via `bot_heartbeats.started_at` vs. file mtimes).
Full detail: `telegram/REPORT-PIPELINE.md`.

## 2026-08-11 — Real milestone bug found via live testing; fixed + audit trail + dashboard added

Pranav manually tested Phase 2 with his own account (35+, later confirmed 67,
answered MCQs) and the report prompt never fired. Confirmed against real data:
67 answered, zero milestone rows. Root cause: `maybe_trigger_report_milestone()`
required `count == 20` exactly. This account already had 27 answered questions
at 08:49 UTC, *before* Phase 2 was even deployed (~09:00 UTC) — every answer
since only pushed the count further past 20, so the exact-equality check could
never become true again. The "only fire once" guarantee was already handled
separately by the milestone-row-existence check right after it — the equality
check was both redundant and the actual bug. Fixed: `count < MILESTONE_THRESHOLD:
return` (i.e. `>=` fires it), confirmed correct for the real account
(`will fire on next answer: True`). Added a permanent regression test
(`step7b`) simulating a synthetic student already at 25 answered with no
milestone row — must still fire on the very next check.

Built the two things Pranav asked for alongside the fix:
- **Complete audit trail**: new `report_flow_events` table, logged at every
  step of the conversation (prompt shown, channel chosen, a value rejected,
  collected-pending-confirm, confirmed, retried, report generated, delivery
  attempted) — exactly the trail that would have made this bug obvious
  immediately instead of needing a live debugging session. `detail` can hold
  real contact values (same PII sensitivity as `students`, same DB, nothing
  new exposed). Smoke-tested: the full synthetic-flow simulation now asserts
  the exact expected event sequence, in order.
- **Student-breakdown dashboard**: new "Student Breakdown" card on the
  existing `:8787` dashboard — a bot-name dropdown (exam/unified kind bots
  only) driving a chat-ID-wise table (attempted/answered/correct/wrong/
  accuracy). New `analytics.fetch_student_breakdown_by_bot()`, wired into the
  same `fetch_all()` both dashboard surfaces already share. Verified two ways:
  a direct query test against real data, and a headless-Edge screenshot with
  the dropdown programmatically switched to a bot with real data, confirming
  the table actually re-renders correctly (not just that the default option
  looks right).

All changes re-ran through `smoke_test_report_flow.py` (still all green,
including the new regression test and event-trail check) before deploying.
Restarted `1lavya-examhub`, `capranav-exam`, `csarunchouhan`, and
`1lavya-dashboard`; confirmed clean since restart on all four.
`health_check.py`: same 16 pre-existing failures.

## 2026-08-11 — Phase 2 (Report Pipeline) built, smoke-tested, deployed

Pranav confirmed Phase 1 (branding) looked right and said to proceed. Built the
full 20-question milestone report pipeline: `database/schema.sql` +
`db.py`'s `_run_column_migrations()` (new `students` contact columns + 2 new
tables — SQLite has no `ADD COLUMN IF NOT EXISTS`, confirmed by testing, so
migrations are idempotent Python checking `PRAGMA table_info`, not raw SQL);
`database/student_analytics.py` (accuracy, time-per-question, chapter-wise,
time-on-bot, all platform-wide); `tools/generate_student_report.py` (branded
HTML→PDF via the Phase 1 brand kit, both importable and a CLI);
`database/report_delivery.py` (email, reusing MyFiles Hub's SMTP account);
`bots/report_flow.py` (the conversational flow — milestone trigger,
echo-and-confirm contact collection, no OTP anywhere per Pranav's repeated
call, final generate+send).

Caught and fixed one real design flaw before it shipped: first draft closed a
session's `ended_at` when the next one started, which would have counted
multi-day idle gaps between sessions as active practice time. Reverted;
"time on bot" is now computed at query time as
`MAX(activity timestamp) - started_at` per session, from real recorded
activity only. Also caught a real regex bug via testing (not written
correctly on the first pass): "+91 98765 43210" — real Indian 5+5 grouping
with an internal space — failed the mobile validator; fixed by stripping
separators before matching instead of encoding every separator position.

Deliberately re-guarded against the EXACT bug class found twice already this
session: `exam_hub_bot.py`'s `button_router` had no callback pattern at all
(harmless only because nothing else claimed any callback_data) — adding
`report_flow`'s own `report:`/`reportconfirm:` callbacks would have been
silently swallowed by it. Fixed before shipping (explicit pattern on
`button_router`, `report_flow` registered separately, same fix mirrored in
`faculty_bot.py`) and added a permanent smoke-test check verifying every real
callback string matches exactly one handler pattern.

Built `bots/smoke_test_report_flow.py` — 7 steps, ~40 checks, including a
full conversational-flow simulation against a synthetic test student (a
telegram_user_id far outside any real range, always cleaned up after) that
exercises the entire path: 19 answers (no prompt) → 20th (prompt fires once)
→ 21st (no re-prompt) → choose "Both" → invalid mobile rejected → valid
mobile (realistic format) → confirm → email → confirm → verifies DB state,
milestone status, and a report_deliveries row. Real SMTP creds aren't
configured in this dev environment — the test proved the email message
builds correctly and that a genuine SMTP auth failure is caught and logged
gracefully (verified for real, not simulated — the mock credentials
predictably failed auth mid-test), not that a real email actually sends;
flagged honestly for Pranav to verify once real creds are in `.env`.

All checks passed. Restarted `1lavya-examhub`, `capranav-exam`, and
`csarunchouhan` to deploy; confirmed clean (no new errors since restart,
checked by timestamp against each log, since old pre-restart tracebacks are
still visible in the same append-only log file). `health_check.py`: same 16
pre-existing failures. Full detail: `telegram/REPORT-PIPELINE.md`.

## 2026-08-11 — Phase 1 branding invisible on live :8787 (stale process); found + fixed, smoke test hardened

Pranav reported no header/footer visible at `http://127.0.0.1:8787/`. Root cause:
the live `1lavya-dashboard` process had been running since before
`dashboard_html.py` was edited to add branding -- Python doesn't hot-reload
changed source, so it kept serving the old unbranded page. My own smoke test's
Step 5 only regenerated and checked the *static* `dashboard.html` file, never
actually hit the live server, so this gap sailed through "all checks passed."
Restarted the process; branding confirmed live via curl + a real headless-Edge
screenshot of the actual `:8787` URL.

Fixed the smoke test itself, not just the immediate symptom: added a new step
that (1) fetches the live `:8787` endpoint directly and checks the branding is
actually there, and (2) compares the live process's own recorded start time
against `dashboard_html.py`/`brand_kit.py`'s mtimes -- a process older than the
source is now a real, automatic "restart this" failure, not something that has
to be remembered by hand.

That staleness check immediately caught a second, separate real bug while
being built: `db.py`'s `send_heartbeat()` only ever wrote `started_at` on the
very first INSERT for a bot_id -- every subsequent UPDATE (i.e. every restart)
left it untouched, so the column silently kept showing the first time that
bot_id was ever seen, across every past process, not the current one. Every
caller already computed the correct value per-process; the UPDATE statement
just never wrote it. Fixed in `db.py` (now writes `started_at` on both branches
-- idempotent within one process's life, correctly picks up the new value on
restart). Confirmed nothing else in the codebase reads `started_at` today
(only `last_heartbeat_at` is displayed anywhere), so this was safe to fix with
no other blast radius. Restarted `1lavya-dashboard` to pick it up; left the
other 6 bots running (same shared `db.py` fix, but no current user-facing
impact for them, so no urgency to force a restart -- they'll pick it up
naturally next time they restart for something else).

Full smoke test re-run clean, 7/7 steps, including the new live-server and
staleness checks. `health_check.py`: same 16 pre-existing failures.

## 2026-08-11 — Big roadmap locked in; Phase 1 (Branding Kit) built + smoke-tested

Pranav laid out a large roadmap in one message: conversational upgrades
(greetings, free-text intent routing, faculty scope-limiting), deeper
per-student analytics, a 20-question report pipeline (email/mobile,
branded HTML→PDF, no OTP), a 30-question leaderboard built on a new
globally-unique "1LAVYA username" identity system, and a full admin-portal
buildout — all under consistent 1LAVYA branding. Reflected back a structured
understanding (six subsystems, what already exists vs. genuinely new) and
asked 4 decision-critical questions before writing any code: free-text
search is scoped to the bot's tenant content_scope first (narrow via
Course+Level then Subject if ambiguous, then query both hubs); the 20/30
milestones are platform-wide; the admin portal moves to Flask (writes are
coming, stdlib http.server won't scale to that safely); build order is
strictly Branding Kit → Report Pipeline → Leaderboard → Admin Portal, each
phase built + smoke-tested + documented before the next starts.

**Phase 1 (Branding Kit) — built, smoke-tested, documented.**
`telegram/branding/`: `build_brand_kit.py` derives a transparent-background
PNG (feathered alpha, verified by compositing onto navy before trusting
it), pre-sized thumbnails, and `brand_colors.json` (navy `#09284b`/gold
`#d0942c`, sampled from the logo's actual pixels via hue-bucketing) from
`telegram/1LAVYA_LOGO.jpeg`. `brand_kit.py` is the reusable module other
code imports. Wired into the real dashboard (not left untested in
isolation) via the shared `dashboard_html.py` template.

Real bug caught by the smoke test, not by inspection: `letter-spacing:
0.02em` rendered fine in a browser but `xhtml2pdf`/`reportlab` (Phase 2's
future PDF engine) silently dropped it — `em` units aren't parseable there,
and `pisa`'s own error count stayed 0 even though a real rule was lost.
Caught by actually rendering through both engines and inspecting output
(headless-Edge screenshot for the browser; a real PDF read directly via
Claude's own PDF-viewing for xhtml2pdf) rather than trusting a "0 errors"
result — the same lesson already relearned twice today on the
csarunchouhan content pipeline, now relearned a third time here and fixed
before it could repeat (the smoke test has a permanent step guarding this
exact regression class going forward).

`health_check.py`: same 16 pre-existing failures, nothing new. Phase 1
awaiting Pranav's manual confirmation before Phase 2 (Report Pipeline)
starts, per the locked build-order process.

## 2026-08-11 — Exam Hub base-format package

Created `telegram/base_formats/` for sharing the required faculty input
contract. It contains a three-page PDF guide, an Excel workbook with MCQ,
descriptive, provenance and validation sheets, and compact valid JSON examples
for both live bot schemas. The examples are generated from the current
`mcq_questions_extracted.json` and `book_questions_extracted.json` shapes; the
large production banks are not duplicated. Added a README and generator script.
Artifact validation passed: JSON arrays load, workbook sheets exist, and the PDF
opens successfully. `file_index.py` passed; health check retains the same 16
pre-existing repository failures.

## 2026-08-10 — csarunchouhan: correct answer was leaked inline in 50 MCQ options

Pranav reported: the bot shows a checkmark against the right option inside the
question itself, before the student answers. Scanned the live merged JSON
directly for checkmark characters in `options` -- found exactly **50 records**,
all from one file (`Factories_Act_50_MCQs_June2026 (1).docx`).

Root cause: `convert_inter_law_mcqs.py` already had logic to detect and strip an
inline "✓ CORRECT ANSWER" marker (this docx set doesn't follow
FACULTY-MCQ-TEMPLATE.md's answer-key-table-only convention) -- but the regex
required the literal word "ANSWER" after "CORRECT". Scanned all 14 source docx
files for every distinct marker phrase actually used (not guessed): exactly two
exist -- `"✓ CORRECT ANSWER"` (13 files, correctly stripped) and `"✓ CORRECT"`
with no "ANSWER" (this one file, 50 questions) -- so every one of those 50 kept
the checkmark AND the word "CORRECT" visible in the option text shown to
students before they answered. Checked Foundation content independently for the
same defect class: clean, 0/375.

Fixed the regex to make "ANSWER" optional (`✓\s*CORRECT(?:\s*ANSWER)?`) rather
than special-casing the one file. Re-ran the converter: 0 remaining checkmarks
across all 650 Intermediate records, and the converter's own answer-key
cross-check found no mismatches (the inline marker agreed with the answer-key
table on all 50, so `correct_option` itself didn't change -- only the leaked
text). Re-ran the merge, re-validated, restarted, and verified by directly
simulating rendering against all 50 previously-affected records plus a broader
random sample of 20 across the full 1,025-record bank -- 0 leaks either way.

**Hardened `validate_content_json.py`** with a new check: any checkmark
character (✓✔✅) in an MCQ's `options` or `question_html` is now an ERROR --
scoped to those two fields only (never `answer_html`, which is supposed to
reveal the answer after the student responds), and to the checkmark glyph
specifically (not the bare word "correct," which shows up legitimately in
normal question phrasing like "which of the following is CORRECT" and
shouldn't be flagged). Verified the new check actually fires against a
synthetic reproduction of the real bug before trusting it.

This is the third real content bug found in this tenant's pipeline today (after
the null-vs-missing-field crash and the blank-question paragraph-parsing bug).
All three were things a validator or converter's own "0 issues" report said were
fine. The recurring lesson, now written into
[[1lavya-csarunchouhan-demo-content]]: a structural "0 errors" result is not the
same as "students will see the right thing" -- worth an actual rendering
spot-check on any new faculty content batch before calling it done, not just
after a live bug report.

## 2026-08-10 — csarunchouhan: all 650 Intermediate MCQs had a blank question (converter bug, not the merge)

Pranav reported: MCQs now render with visible A/B/C/D options but a completely
blank question. Checked the actual JSON directly: **all 650/650 Intermediate
records** had `question_html: "<p></p>"` — genuinely empty, present in the file
before today's merge, not something the merge introduced.

Root-caused by reading the real source docx
(`AcceptanceDeposits_50MCQs_June2026.docx`) paragraph-by-paragraph: these
particular files put `"Q1.  [Section 2(31) — Definition of Deposit]"` on its own
paragraph with nothing after the bracket, then the ACTUAL question text
("Under Section 2(31)... 'deposit' means:") on a separate, following paragraph,
before any options. `convert_inter_law_mcqs.py`'s parsing loop only ever set
`question_text` once, at the moment it matched `"Q<n>."`, from whatever text sat
on that same line (empty here) — any paragraph that came after and matched
neither the question pattern, an option pattern, nor "Explanation:" fell through
every branch and was silently dropped. Exactly the class of "silently ignored
error" Pranav suspected.

Fixed the parser: any paragraph appearing after a `"Q<n>."` match but before the
first matched option is now appended to `question_text` instead of discarded
(gated on "no options captured yet for this question," so it never fires once
options have started, and correctly handles a genuine multi-paragraph stem too,
not just this one document shape). Re-ran the converter: 0/650 blank afterward.
Re-ran `merge_faculty_mcq_sources.py` (the converter writes straight to the
shared tenant file again, wiping the Foundation merge — exactly the documented
operational rule). Restarted the bot; **this time verified by directly simulating
`send_mcq()`'s own rendering logic against a random sample of 12 real records
spanning both levels** (not just checking the JSON in isolation, which is what
let this slip through originally) — 0/12 blank, real readable question text.

**Also strengthened `validate_content_json.py`** so this exact bug class can
never pass silently again: `_is_present()` now strips HTML tags before checking
for blank content, so `"<p></p>"` correctly counts as empty everywhere, not just
as a literal empty string. Verified against a synthetic reproduction of the
original bug (correctly flagged as ERROR).

**Honest note on my own process**: I declared the earlier merge "validated
clean" based on the converter's own report (0 issues) plus my validator (0
errors) — neither actually checked whether `question_html` contained real text,
only whether the field was present as a non-empty string. Two real bugs in two
consecutive checks now (the null-vs-missing crash, and this one) both came from
trusting a structural "0 errors" result without exercising the actual rendered
output first. Fixed the validator gap this time; the broader lesson — spot-check
real rendering before calling faculty content "done," not just the JSON shape —
is now written into memory ([[1lavya-csarunchouhan-demo-content]]).

## 2026-08-10 — csarunchouhan: real crash bug found + fixed (null-value fields, not just missing ones)

Pranav reported a live bug: tapping "FACULTY_PRACTICE" (an Exam Type) gave no
response at all. Logs (`telegram/database/run/logs/csarunchouhan.log`) showed the
real cause: `telegram.error.BadRequest: Can't parse inlinekeyboardbutton: can't
find field "text"`, from `exam_hub_bot.py:752` (the Year-selection screen), plus a
follow-on `KeyError: 'exam_type'` once the student's session state and the
(never-updated, because the edit failed) displayed menu diverged.

Root cause: `McqBank.years()` used `q.get("year", "Unknown")` — but `dict.get(key,
default)` only substitutes the default when the KEY IS ABSENT, not when it's
present with an explicit `null`. All 375 Foundation records merged in earlier today
have `"year": null` (key present, value None) — so `years()` returned `None` for
that bucket, and `InlineKeyboardButton(None, ...)` builds fine in Python but gets
rejected by Telegram's API at send time. This is the exact same class of mistake
this session already fixed once today in `faculty_bot.py`'s callback regex (a
"missing" case handled, an adjacent "differently-shaped" case wasn't) — should
have anticipated this specific failure mode when the Foundation merge produced 375
"missing year" warnings earlier, not just filed it as a cosmetic gap.

Fixed properly, not just at the one crash site: every `.get(field, default)` in
both `McqBank` and `QuestionBank` that could face an explicit `null` (not just an
absent key) was changed to `q.get(field) or default` — `exam_types()`, `years()`,
`chapters()` (both classes), `_filter()`'s equality comparisons (had to match the
same normalization or a synthesized "Unknown"/"unknown" bucket would silently
match zero records instead of crashing — same root cause, quieter failure mode),
and the MCQ meta line (was about to render the literal word "None" to students for
`year`/`difficulty`). Verified the exact reproduction path directly (no live
Telegram needed): `years('FACULTY_PRACTICE', 'CMA', 'Foundation')` now returns
`['Unknown']` (a real button-safe string) instead of `[None]`, and
`filter_questions(...)` correctly finds all 375 records under that bucket.
Restarted csarunchouhan again to deploy; startup log clean, no errors.
`validate_content_json.py` re-run: still 0 errors (the 375 "missing year"
warnings are now honestly true to what the code does, not a broken promise).

## 2026-08-10 — csarunchouhan: stale-content drift found + fixed; Foundation MCQs merged in

Pranav asked to confirm the bot loads from JSON not DB (yes, re-verified). Found a
real, live issue while checking: another concurrent session's new
`convert_inter_law_mcqs.py` (see the entry directly below — 650 CMA Intermediate
Law MCQs across 6 modules) had already overwritten the tenant's live-configured
`mcq_questions_extracted.json` at 19:10, but the running bot process (last started
18:16) had no way to know — it was still serving its stale 20-question in-memory
snapshot. Same for the descriptive file (47 records on disk, bot still serving 5).
This repo's multi-agent-concurrency note (CLAUDE.md section 2) applied literally
here, one file layer down: not a git-history divergence this time, but a bot
process silently diverging from a file another session had already rewritten.
Validated the new content two ways before deploying — the converter's own report
(650/650 expected, 0 issues) and an independent run of `validate_content_json.py`
(0 errors) — then restarted to deploy both.

Also found: all 650 new MCQs were `(CMA, Intermediate)` only — the previously-known
375-question Foundation file was still sitting unmerged, so `AVAILABLE_DATA` for
this tenant showed Intermediate only, meaning a CMA Foundation student got zero MCQs
despite Study Hub happily serving them Foundation study materials. Pranav confirmed:
merge Foundation in too. Inspected first — all 375 Foundation records are
self-labeled `publication_status: "draft"` with **zero real explanations** (every
`answer_html` is a bare `"(B)"`, unlike Intermediate's real explanations) — flagged
this explicitly before merging; Pranav confirmed merge as-is, explanations to follow
later without needing a re-merge.

Built `telegram/tools/merge_faculty_mcq_sources.py` rather than hand-editing the
JSON — the actual root cause here is architectural: two independent per-level
converters both writing toward the same shared tenant-facing file with no merge
step between them, so whichever runs last silently clobbers the other. The new
script reads a tenant's configured source list, fails loudly on any `mcq_id`
collision (none found — Foundation uses `CMAF-P1-...`, Intermediate `CMAI-P5-...`),
writes the combined 1025-record file, and re-runs `validate_content_json.py`
against its own output before declaring success. Restarted csarunchouhan again;
`AVAILABLE_DATA` now correctly shows `{('CMA','Foundation'), ('CMA','Intermediate')}`.
Documented the operational rule (re-run the merge after any future re-run of
`convert_inter_law_mcqs.py`, since it writes directly to the shared file) in the
merge script's own docstring.

## 2026-08-10 — Arun Chouhan Intermediate Law MCQ bank

Built `telegram/assets/faculty/csarunchouhan-cma-inter-law/
convert_inter_law_mcqs.py` for the 14 actual MCQ DOCX papers in the faculty
folder. The deterministic converter preserves the Exam Hub MCQ list schema,
cross-checks inline marked answers against each answer-key table, maps records
to exact CMA catalog modules M7–M12, and retains every explicit DOCX topic label.
Final result: 650/650 records, 650 unique IDs, valid A-D options, zero answer
mismatches, zero exclusions, and no missing topics. Published the bot input at
`telegram/assets/exam_bot/faculty/csarunchouhan/mcq_questions_extracted.json`;
source JSON and a separate validation report remain beside the faculty source.
The three non-MCQ reference sheets were deliberately excluded. The RAG master
spec was updated with the implementation decision and the current limitation:
the catalog is exact at module level, while CMA topic IDs are not yet governed
by a separate master taxonomy.

## 2026-08-10 — Reporting roadmap discussed; Content Health validator built

Pranav laid out a bigger roadmap (content-schema consistency, a full admin portal
at :8787, student-wise analytics, a faculty leaderboard, PDF reports emailed to
students) and asked for feedback before committing. Pushed back on three points:
"no email verification needed" doesn't hold (people mistype emails regardless of
intent; risk is a real student's performance data reaching a stranger) — agreed
on echo-and-confirm instead of OTP or send-immediately. Leaderboard scoring
wasn't decided — Pranav chose accuracy with a minimum-attempts floor. The
existing `watermark_for_print.py` (rasterizes every page for print/anti-piracy)
is the wrong tool for an emailed report — `exam_hub_bot.py` already has a
working `xhtml2pdf`/`pisa` PDF pipeline to reuse instead; no 1LAVYA logo asset
exists yet in this repo (still open).

Pranav chose to build the smallest piece first: `telegram/tools/
validate_content_json.py`. Its core-field contract was derived by grepping every
real field access in `exam_hub_bot.py`'s `QuestionBank`/`McqBank`, not guessed —
ERROR for anything that crashes or silently corrupts an answer (bad
`correct_option`, <2 options, duplicate `mcq_id`/`book_id` shadowing an earlier
record), WARNING for safe-fallback-but-degraded fields, and extra
faculty-specific fields never flagged at all. Verified against all 4 real
content files (clean) and a synthetic negative-control file covering all 4
defect classes (all caught). Wired into both dashboards as a live "Content
Health" card via `analytics.fetch_content_health()` (added to the same shared
`fetch_all()` both dashboards already call, so no extra wiring needed there).
`health_check.py`: same 16 pre-existing failures, nothing new.

Still open, by choice: student-wise analytics, leaderboard, PDF report/email —
next in the build order once picked up again.

## 2026-08-10 — csarunchouhan Next/I'm-Done bug fixed live; dashboard + down-alert watcher built

Pranav reported that on the live `csarunchouhan` bot, "Back to Chapter List" worked
after an MCQ answer but "Next Question" and "I'm Done" gave no response. Verified
independently by reading the code: `faculty_bot.py`'s exam-hub `CallbackQueryHandler`
pattern required a trailing colon (`...|next|mcqopt|restart):`), but `exam_hub_bot.py`'s
Next/I'm-Done buttons use bare `callback_data` ("next"/"restart", no colon, by design) —
so in the unified bot specifically, no handler ever matched and Telegram never even got
`query.answer()` back. Standalone `exam_hub_bot.py` was unaffected. Fixed the regex to
`(:|$)`, verified against every real callback shape, and deployed live (restarted
`csarunchouhan` — confirmed via the DB it was only Pranav's own test session at the
time). Discovered in passing that all 6 real bots, including `capranav-study`/
`capranav-exam`, were already running — Pranav confirmed he'd started them himself.

Pranav then asked for "a robust architecture and a perfect reporting tool." Built,
same day:
- `telegram/bots/watcher_bot.py` — down/up DM alerts via the MyFiles Hub bot's token to
  `telegram/config/alerts.json`'s `admin_chat_ids` (empty by design until Pranav fills
  in real chat IDs). Edge-triggered off heartbeat freshness, state tracked in a new
  `bot_alert_state` table so a restart doesn't re-fire. Both transition directions
  verified against the real live DB (not mocked) by temporarily perturbing one real
  bot's state at a time and confirming detection, then letting it self-correct.
- `telegram/tools/dashboard_server.py` — live dashboard (127.0.0.1:8787) with a Refresh
  button that re-queries `platform.db` in place, no page reload. Runs as a managed
  process (`bots.json`'s `1lavya-dashboard` entry).
- Bot-wise usage summary (interactions, unique users, downloads/searches, MCQ accuracy,
  descriptive views) added as a dashboard view, per Pranav's choice over a Telegram
  command.
- Refactored the pre-existing static `generate_dashboard.py` onto a shared query layer
  (`telegram/database/analytics.py`) and page template (`dashboard_html.py`) so the live
  and static dashboards can't drift into disagreeing about a number.

Self-caught bug before shipping: the dashboard's first `bots.json` entry used a relative
`"../tools/..."` script path, which would have silently broken `manage_bots.py`'s
"already running" detection (forward-slash string never matches the backslash-separated
string Windows actually launches with). Fixed properly — `manage_bots.py` gained
`resolve_script_path()` + an optional `script_dir` field, verified via a real start/
status/duplicate-start cycle.

Flagged, not fixed: `manage_bots.py stop`/`restart` hit `WinError 87` on the
`CTRL_BREAK_EVENT` graceful-stop signal every time in this session's shell (fell through
to force-terminate harmlessly) — likely that shell having no attached Windows console,
not a code defect, but the "verified working on Windows" claim in the docs no longer
holds unconditionally. Worth Pranav checking from his own terminal.

Full detail in CLAUDE.md section 11's new dated entry. `health_check.py`: same 16
pre-existing, unrelated failures as before, nothing new. Still open: `alerts.json`'s
`admin_chat_ids` needs Pranav's real chat ID(s) before the watcher can send anything.

## 2026-08-10 — Arun Chouhan Companies Act descriptive bank

Built `telegram/assets/faculty/csarunchouhan-cma-inter-law/
faculty_descriptive_pdf_to_json.py` to extract the faculty's Companies Act PDF
into the shared descriptive-question shape. It generated 47 CMA Intermediate
Law descriptive records with source hash, page ranges, faculty provenance and
draft/review status, and published the bot input to
`telegram/assets/exam_bot/faculty/csarunchouhan/book_questions_extracted.json`,
the path already configured for Arun's Exam Hub tenant. The source PDF has 47
detected prompts but only 46 literal `Ans.` markers because of its irregular
column/page layout; this discrepancy is reported for review, while all 47
prompt-answer segments are retained. Existing CA question files were untouched.

## 2026-08-10 — RAG master specification amended

Expanded `telegram/assets/CA_CS_CMA_Knowledge_Base_RAG_Master_Spec.md` with
the project-specific handoff architecture: current 1,084-document corpus,
unified JSON catalog contract, native CA/CS/CMA structures, separate syllabus
taxonomy, typed content blocks, complete implementation phases, Question Bank
Engine integration, white-label permissions, source-integrity rules, update
protocol and decision log. The document is now the living specification for
future bots and AI agents joining the RAG build. Markdown diagnostics passed;
the repository health check retains the same 16 pre-existing failures.

## 2026-08-09 — Unified knowledge-base document catalog

Built `telegram/tools/build_knowledge_base_catalog.py`, which reads the CA and
CS/CMA source catalogs plus the existing Exam Materials catalog and generates
`telegram/source-docs/knowledge_base_documents.json`. The manifest preserves
native course metadata, adds physical-file-specific document IDs, SHA-256 hashes,
PDF page counts, processing status, and review flags, and validates both catalog
directions against the 1,084 PDFs on disk. Validation passed: 1,026 Study
Materials and 58 Exam Materials. The known ICSI merged Lesson 6 with no physical
PDF is excluded consistently with the existing master-catalog pipeline. `file_index.py`
completed; `health_check.py` retains the same 16 pre-existing repository failures.

---

## 2026-08-08/09 — Study Hub Bot unified for CA + CS + CMA across 3 material categories

Continuing from the CS/CMA catalog work: Pranav asked for a PDF-splitting script next
(explicitly staged as its own step, reviewed before running). Built
`telegram/tools/split_cs_cma_pdfs.py` — reads `CS_CMA_Chapter_Catalog.xlsx`'s page
ranges, writes one PDF per chapter. Per his instruction, delivered the code without
running it myself (only a syntax check); safe-by-default design: dry run unless
`--execute` is passed, wipes-and-rebuilds its output folder idempotently, every row
validated independently so one bad row can't crash the batch. Pranav ran it himself —
confirmed later, output matched exactly (646 files, byte-identical naming to what the
script predicted).

He then restructured `telegram/assets/` entirely: replaced the separate per-course flat
folders with `telegram/assets/study_bot/{Study Materials, Exam Materials, Revision
Material}/`, merged in his split-script output + the existing CA flat folder (1,026
Study Materials files total: 380 CA + 646 CS/CMA), and added a new **Exam Materials**
category — 58 CA Inter Advanced Accounting MTP/PYQ/RTP papers with already
self-describing filenames (`{CourseLevel}-{Subject}-{PaperType}-{Session}[-SetN]-
{Q|Ans}.pdf`). Asked for `study_hub_bot.py` to be rewritten to match, serving all three
courses (CA/CS/CMA) instead of just CA.

**Built `telegram/tools/build_master_catalog.py`**: the one catalog the bot now reads
(`StudyHub_Master_Catalog.xlsx`) — merges the CA and CS/CMA study catalogs into one
unified schema, plus parses Exam Materials filenames directly (a small 9-entry table
splits `CAInter`-style prefixes into Course+Level; Subject full names resolve by
matching filename prefixes against the already-loaded Study Materials rows — no
separate table to maintain). Self-cross-checks against disk every run, both directions.
First run: 1,084 rows, zero mismatches (1,026 Study + 58 Exam + 0 Revision, the last
category being genuinely empty so far and handled as such, not an error).

**Rewrote `study_hub_bot.py`**: new browse tree Category → Course → Level → Subject →
(Chapter, or Paper Type → file for Exam Materials), every level computed dynamically
from the catalog — no hardcoded course/level lists, so new content just appears once
catalogued. An empty category (Revision Material) shows "not available yet" instead of
a broken empty menu. Extended the 64-byte `callback_data` lesson from the 2026-08-07
incident one level deeper (Category and Paper-Type both index-based, never literal
strings). Verified for real: every possible `callback_data` string across the entire
1,172-node current browse tree — max 25 bytes. Smoke-tested against the real catalog and
real files: full tree traversal, free-text search across all 3 courses + Exam Materials,
and a 15-row random sample of file-path resolution — all correct.

Documented in a new `_claude/skills/SKILL-study-hub-bot-architecture.md` (the
unification layer above the existing CA and CS/CMA pipeline skills), `CLAUDE.md` §10,
and updated `README_Bot1_StudyHub.md` for the new architecture.

**Still genuinely open**: Exam Materials covers exactly one subject so far; Revision
Material has no content or agreed naming convention yet (bot/catalog both handle the
empty state gracefully in the meantime); `telegram/assets/backup pdfs/` (the
pre-restructuring backup) hasn't been reviewed for whether it's safe to delete — that's
Pranav's call.

---

## 2026-08-08 — Question Bank Book marketing one-pager built

Pranav asked Claude to independently review the finished `QUESTION-BANK-BOOK.html`
and identify genuinely marketable features/problems solved (not generic flattery —
read `AS10_Question_Book.html`, `book_stats.json`, `front-matter.html`, and
`How-to-Read-this-Book.md` directly first). Pranav then drafted his own feature pitch
from the student's actual study journey (Study Material → MTP/RTP/PYQ, topic-wise) and
asked for a review — gaps flagged: MCQ-exclusion needed explicit framing (real
expectation-setting risk, not just a nice-to-have), "important chapters" and
"important topics" are actually two separate real features (coverage matrix +
topic-wise marks mapping), the Examiner's-Comment-vs-Author's-Note distinction and
Pranav's own AIR-1 credibility were both missing from the draft, and hard numbers beat
vague claims.

Pranav then asked for an HTML one-pager, with an exact hero line ("Most Friendly
Question Bank for Self Study Students"), MCQ mention placed last and low-key (book
promoted first), and `1Lavya.com` named only as one neutral non-endorsed example
("or any other MCQ practice platform") per his explicit instruction not to be seen as
associated with it. Built with real design investment (`artifact-design` skill) —
fetched and embedded Fraunces + IBM Plex Sans + IBM Plex Mono as base64 @font-face
data URIs (no external font requests), deliberately reused the book's own established
CSS colour language (tan/pink/green note coding, the `Marks · Approx Time · Topic`
meta line, the dotted-line Error Register) so the page reads as a page out of the book
itself, and used two genuine excerpts from the actual book (the AS 10 Preet Ltd. PPE
question + its real Author's Note) as facsimile exhibits rather than invented
examples. Published as a Claude Artifact, then saved into the repo as the persistent
copy at `content/productions/question-bank-launch/deck/question-bank-onepager.html`
(new production folder, per `content/productions/`'s existing one-folder-per-video
convention) with its own `README.md` documenting design intent and origin.

**Not yet done, left as visible placeholders rather than invented**: no purchase
link, price, or contact address wired into the page yet — needs Pranav's input.

`tools/health_check.py` and `tools/file_index.py` re-run after adding the new
`content/productions/question-bank-launch/` folder — same 16 pre-existing failures as
every prior run (`syllabus-engine`/`question-bank` stale `EXPECTED_DIRS`, unrelated
bridge-course NUL bytes, `capranav_com/` staleness), nothing new introduced.

---

## 2026-08-08 — Exam Hub Bot (Bot 2): added MCQ mode + Course/Level menu + SQLite activity logging

Pranav asked for `telegram/bots/exam_hub_bot.py` (previously descriptive-only,
reading `book_questions_extracted.json`) to also serve **MCQ practice** —
Course → Level → Descriptive/MCQ → (MCQ path) Exam Type → Year → Chapter →
one MCQ at a time with 4 (occasionally 3) option buttons, instant
correct/incorrect + explanation on tap — and to log every interaction to a
SQLite DB for analytics ("which student checked which question, what was
his response, correct or wrong").

**Found the MCQ source data already exists**, just never exposed to this
bot: `first_run/output/generated-from-script/questions_index.json` (the
Question Bank Book pipeline's Layer 2, see CLAUDE.md §6's 2026-07-26 entry
on why MCQs were pulled from the *printed* chapter books but always stayed
in this JSON) — 335 of its 831 rows are Part I/MCQ, each already carrying
parsed options, the correct letter, and a Claude-authored explanation.

**New script, `telegram/tools/build_exam_bot_mcq_export.py`**: filters to
Part I, drops the 1 row with no reliable answer key
(`CAI-P1-PYQ-2025-01-PI-Q4`), regex-parses `<li data-opt="X">` option markup
into a plain `{letter: text}` dict (confirmed NOT always 4 options — one
real MCQ, `CAI-P1-MTP-2026-01-S1-PI-Q11`, is genuinely 3-option — never
assume A–D), and maps each row's `final_chapter` unitcode to the same
`chapter_slug`/`chapter_label` the descriptive bank already uses (read
straight off `book_questions_extracted.json` rather than re-deriving a
second slugging scheme — confirmed all 28 MCQ unitcodes are a subset of the
descriptive bank's 34). Output: `telegram/assets/exam_bot/
mcq_questions_extracted.json`, 334 usable records, self-contained and
regenerable, same "generated, never hand-edited" pattern as the descriptive
file.

**Course/Level menu**: Pranav's explicit call — show the full CA / CS / CMA
× their levels structure up front even though only CA→Inter has any
question data today, and just tell the student plainly ("no questions for
this Level yet") for every other combination rather than hiding them. Gated
by one `AVAILABLE_DATA = {("CA", "Inter")}` set in the script — extend it
as more course/level question banks get built.

**SQLite activity log** at `telegram/assets/exam_bot/Exam_Bot.db` (new
`**/*.db` gitignore rule added — binary, stays local, same "no binary files
in git" principle as everything else). Four tables: `students` (upserted
per Telegram user), `bot_sessions` (one per `/start`, tracks the
course/level/mode funnel for drop-off analysis), `descriptive_question_events`
(one row per question shown, updated in place when the answer is revealed
/ PDF requested), `mcq_attempts` (one row per MCQ shown, updated in place
with the selected option + correct/incorrect once answered). Rows are
inserted at "shown" time and updated as the student acts, so
shown-but-abandoned questions are visible too (nullable columns stay NULL).

Rewrote `exam_hub_bot.py` end to end on this design — added a parallel
`McqBank` class (mirrors `QuestionBank`, but `exam_type`/`year` are already
explicit fields in the MCQ export, no pattern-detection needed like the
descriptive bank's `src_text` scanning), all the new menu/callback
branches (`course:`, `level:`, `mode:`, `mcqopt:`, `restart`), and the DB
helper functions. Smoke-tested directly (bs4/xhtml2pdf/python-telegram-bot
are all installed in this sandbox) rather than just `py_compile`: loaded
both banks for real, rendered a real case-mcq's HTML through
`html_to_telegram_text`, ran the DB init + a full write/read cycle across
all 4 tables with a fake user, confirmed the 3-option MCQ record parses
without assuming 4 options, and confirmed `html_to_pdf_bytes` still
produces real PDF bytes for a descriptive record — all correct on the
first real run. `tools/health_check.py` still shows only its pre-existing,
already-documented failures (stale `EXPECTED_DIRS`, `bridge-course` NUL
bytes, `capranav_com/` staleness — see CLAUDE.md §5) — nothing new from
this change. `tools/file_index.py` re-run clean.

**Not committed yet** — left for Pranav to review (new bot logic + a new
gitignore rule + a new generated data file, not pushed per "commit/push
only when asked"). README (`README_Bot2_ExamHub.md`) fully rewritten to
document the new flow, the DB schema (with a sample analytics query), and
the re-run instruction for the export script whenever
`questions_index.json` changes upstream.

---

## 2026-08-08 — CS/CMA Chapter Catalog (ToC extraction pipeline), Stage 1+2 built

Pranav added CS and CMA study material — 50 consolidated PDFs (one per subject, all
chapters in one file — no per-chapter split like ICAI's CA material, and no usable
embedded bookmarks) across `telegram/assets/{CS Exce, CS Prof, CS EET, CMA Final, CMA
Found Study mat, CMA Inter Study Mat}/`. Asked for a script-generated Excel catalog
bifurcating each subject into chapter-wise page ranges via each PDF's own printed Table
of Contents, capturing both the printed page range and the actual PDF page range (since
downstream Python code needs the latter, not the former), plus full + abbreviated
chapter names and a planned final split-PDF filename — explicitly staged as "the Excel
catalog first," before any actual PDF splitting.

**Built `telegram/tools/cs_cma_common.py`**: per-file Course/Level/Subject/PaperNo
metadata read from each PDF's own cover page (not guessed) — 50 entries. Caught that CMA
Intermediate's "Paper 7" (Taxation) is one syllabus paper split by ICMAI into two study-
note volumes (Direct/Indirect) — kept as `7A`/`7B`, mirroring CA Inter's existing
GST/Income-tax Paper 3A/3B split.

**Built `telegram/tools/scan_cs_cma_toc.py`** (Stage 1): two ToC parsers, auto-selected
per publisher. ICMAI's "Contents as per Syllabus" page gives explicit printed page
*ranges* per Module/Section directly (no end-page inference needed); ICSI's "CONTENTS"
section gives each Lesson's start page only (end = next lesson's start - 1). Found and
fixed several real parsing bugs along the way: a too-permissive embedded-whitespace
number regex that once swallowed an adjacent citation year into a page number; ICSI
sub-heading lines ("SECTION I: ...CODE, 2020") whose trailing citation-year looked like a
page number; a `Module N **:** Title` colon-separator variant my regex only handled for
periods; and — the significant one — `^`/`$` regex anchors applied to a whole multi-line
page string instead of per-line, which silently broke ToC-window-size detection *and*
let a lesson's own later body-chapter heading (which restates "LESSON N" + title) bleed
into the parsed ToC as corrupted duplicate entries. Also found 7 of the 23 ICMAI files
render their ToC table column-by-column (all headings, then all page ranges dumped
together) rather than row-by-row — built a positional-zip fallback parser for those,
only invoked when the primary parser finds zero modules.

Every computed PDF page range is verified by fuzzy-content-matching the chapter title
against its own computed opening page (same discipline as the CA pipeline), not trusted
from arithmetic alone. Result: 647 chapters across 50 files. Two rows needed an explicit,
documented correction: two genuine typos in ICMAI's own printed ToC ("Operatinal Audit"
/ "Diefferent Service Organisations" — confirmed by reading the real chapter page, which
spells both correctly), and one ICSI lesson (ESG book, Lesson 6) whose own ToC states it
was merged into an earlier lesson and has no standalone content. Both handled via
explicit override tables in Stage 2, with a Notes column explaining each — never
silently applied or silently dropped.

**Built `telegram/tools/build_cs_cma_catalog.py`** (Stage 2): generates
`telegram/source-docs/CS_CMA_Chapter_Catalog.xlsx` — `PrintedPageStart/End` (as printed
in the book) alongside `PDFPageStart/End_1indexed` (1-indexed, as any viewer shows it —
subtract 1 for pypdf), full `ChapterName` + `ShortChapterName` (≤35 char, Telegram-
button-width, same abbreviation scheme as the CA catalog), `SourceFile` (which
consolidated PDF these pages still live inside), and `FinalPDFFileName` (the planned name
once a chapter *is* split out — not yet built).

**Independent verification**: a random 12-row spot-check (re-reading the actual PDF
pages fresh, not trusting the pipeline's self-reported scores) confirmed every one
correct, including cross-checking the printed page number visible in each page's own
running header against the catalog's `PrintedPageStart`.

Full pipeline documented in `_claude/skills/SKILL-cs-cma-toc-pipeline.md`; summarized in
`CLAUDE.md` §9. `health_check.py` clean (same pre-existing unrelated failures only).

**Explicitly not built yet** (scope locked to "Excel catalog first," don't build without
asking): actually splitting the 50 consolidated PDFs into per-chapter files using this
catalog's page ranges, and wiring the result into `study_hub_bot.py` (which currently
only serves CA content).

---

## 2026-08-07 (cont'd) — Telegram Study Hub Bot: catalog pipeline built, bot wired to real data

Reviewed `telegram/bots/study_hub_bot.py` at Pranav's request and found it couldn't
actually serve this repo's own content: `EXCEL_PATH`/`FILES_FOLDER` pointed outside the
repo (`D:\Eklavvia\...`), the mapping Excel was still the blank 3-row template, the real
380 ICAI PDFs (CA Foundation ×4, CA Inter ×8, CA Final ×5 — Pranav had just added CA
Final) sat in a *nested* course/Module tree the bot's flat-folder code can't read, and a
live bot token was hardcoded in the script plus sitting in an ungitignored
`telegram/creds.txt`. Flagged all of this; Pranav asked for it to be fixed end to end,
via script (not manual), with the flat filenames self-identifying by Course/Level/
Subject, kept short, and — critically — verified against real PDF content before trusting
any filename, "as this will be the last time we will be checking it."

**Built `telegram/tools/scan_study_bot_source.py`** (read-only): extracted real first-page
text from all 380 PDFs via `pypdf`, fuzzy-scored it against each filename's stated title.
380/380 had extractable text; every low score was structurally expected (front-matter
files like "Initial Pages"). Manually followed up on the genuine outliers and found three
real defects: a corrigendum file with no parseable name at all; two CA Final Advanced
Auditing chapters literally named "Untitled" (real content, confirmed by reading page 1:
Chapter 14 Units 1–2, Special Features of Audit of Banks / NBFCs); two CA Foundation
Quants files filed under chapter 0 that are actually real Chapters 13 and 14 (confirmed
via the printed chapter number on each page). Also read every subject's own "Initial
Pages" cover to get exact, ICAI-verified paper names/numbers rather than guess them.

**Built `telegram/tools/build_study_bot_catalog.py`**: copies all 380 PDFs into a new
flat folder (`telegram/assets/study_bot_flat/`) under a self-identifying name —
`{Course}{Level}-{SubjectShort}-{Session}_M{n}-C{n}-U{n}_{ShortTitle}.pdf`, e.g.
`CAInter-AdvAcc-May26_M1-C4-U2_AS3CashFlowStatement.pdf` — and generates
`telegram/source-docs/1Lavya_Study_Hub_File_Mapping.xlsx` from scratch (was the blank
template before). Both outputs regenerate wholesale on every run; the three filename
corrections above live in a documented `TITLE_OVERRIDES` table, not silently applied.
Result: 380 source PDFs → 380 flat PDFs → 380 Excel rows, zero collisions.

Per Pranav's explicit choice, once the flat copy was verified complete, **deleted the
nested source tree** (380 original PDFs + their 216 `.md` conversion siblings) — "delete
the older version to avoid duplication."

**Also fixed**: `study_hub_bot.py` no longer hardcodes a live token (was both in the
script and in plaintext `telegram/creds.txt`, neither gitignored) — it now parses its
token from `creds.txt` at runtime or `TELEGRAM_STUDY_BOT_TOKEN`. Added a "Secrets /
credentials" section to `.gitignore` (`telegram/creds.txt`, `**/creds.txt`, `*.env`) plus
a blanket `desktop.ini` rule. `EXCEL_PATH`/`FILES_FOLDER` are now resolved repo-relative
via `Path(__file__)` instead of a hardcoded outside-the-repo path. Smoke-tested the whole
bot end to end (catalog load, browse flow, free-text search, on-disk file resolution) —
all working against the real data for the first time.

Wrote up the full pipeline in `_claude/skills/SKILL-study-bot-catalog-pipeline.md` and
`CLAUDE.md` §8 (new), updated `README_Bot1_StudyHub.md`, deleted the now-superseded blank
Excel template. `health_check.py` and `file_index.py` both re-run clean — the only
failures left are pre-existing ones unrelated to this work (stale `EXPECTED_DIRS` list,
`books/bridge-course` NUL-byte files, undocumented `capranav_com/`), all already flagged
elsewhere.

One expected (non-bug) finding from testing free-text search: "cash flow statement"
correctly returns two results, because ICAI's own material repeats the topic under two
real chapter codes (`M1-C4-U2` and `M3-C11-U2`) — the same duplicate-chapter situation
already documented for the Question Bank pipeline below, independently hit again here.

**Same-day follow-up**: Pranav actually ran the live bot and searching "Inventories"
threw `telegram.error.BadRequest: Button_data_invalid`. Root cause: Telegram's inline
button `callback_data` has its own 64-byte cap, separate from any filesystem limit — the
bot was putting the raw `FileName` (up to 82 chars) straight into `callback_data`,
overflowing for 192/380 files, plus the same bug independently existed on the Subject
picker via long subject names (23/380 rows, e.g. "Advanced Auditing, Assurance &
Professional Ethics"). Fixed in `study_hub_bot.py` by carrying a small integer
row-id/list-index in every callback instead of the literal string, resolved back through
the catalog. Verified by generating and byte-checking every possible callback string
across the entire browse tree (401) plus several free-text queries — max is now 23 bytes.
Documented in `SKILL-study-bot-catalog-pipeline.md` §6 and `CLAUDE.md` §8.

**Third bug, same incident**: after that fix, Pranav noticed "Inventories" still didn't
surface CA Inter Advanced Accounting's "Valuation of Inventory" chapter. Not a
callback_data issue this time — 21 chapters genuinely score ≥60 against "Inventories"
(the topic recurs across Foundation/Inter/Final), but `TOP_N_SUGGESTIONS = 3` was
silently dropping everything past the top 3; two exact-title matches (score 100, one
each in Foundation and Final) filled 2 slots, and the AdvAcc chapter lost a 5-way tie at
72.7 for the last one purely by sort-order luck. Fixed by raising `TOP_N_SUGGESTIONS` to
8 and adding Level to each search-result button's label (previously only Subject was
shown, so same-titled chapters at different levels were indistinguishable). Documented
in `SKILL-study-bot-catalog-pipeline.md` §6.

---

## 2026-08-07 — Book-vs-data QA tooling built; real Cash Flow Statement taxonomy bug found and fixed

Pranav asked for a script converting the final `QUESTION-BANK-BOOK.html` back into JSON.
Clarified purpose first (AskUserQuestion): scope = questions only, purpose = QA/
round-trip verification against `questions_index.json`, not a new data source.

**Built two new scripts in `first_run/scripts/`:**
- `extract_book_questions.py` — parses the real merged book (all 34 `.qb-section`
  chapters, `.qblock` by `.qblock`) into JSON. Exports `parse_qblock()` and
  `extract_book()` for reuse.
- `diff_book_vs_index.py` — for every `questions_index.json` row that
  `generate_chapter_book.select_chapter_rows()` (new — factored out of `build_book()`,
  behavior-preserving, verified byte-identical AS02 output before/after) says belongs in
  the book, regenerates that row's exact qblock HTML via the real `render_qblock()`,
  parses it with the same `parse_qblock()`, and diffs field-by-field against what's
  actually in the book. No label/selection logic re-derived on either side — both paths
  call the real pipeline functions — so a diff here is real drift, not two independent
  parsers disagreeing. Validated with a positive control (real row, byte-identical) and
  a negative control (corrupted fields, correctly flagged) before trusting a clean run.
  Output: `first_run/output/qa/{book_questions_extracted.json, book-vs-index-diff.json,
  book-vs-index-diff.md}`.

**First real run found a genuine bug, not noise:** 27 of 455 questions came back
"orphan" (found in the book, no matching expected row) — all 27, no exceptions, were
the Cash Flow Statement chapter. Root cause: `qb_merge.py`'s `CHAPTERS` tuple listed
`study_ref = "M1-C4-U2"` for that chapter, but every one of its 27 tagged questions in
`questions_index.json` (and `generate_all_chapter_books.py`'s own
`NON_AS_SLUGS`/`TITLE_OVERRIDES` table, which is what actually pulls the chapter's
content) uses `"M3-C11-U2"` instead. Both codes are real, distinct entries in
`1-ca-inter-adv-accounts-topic-page-index.json` (`M1-C4-U2` = the standalone AS 3
chapter under Module 1, 11 topics; `M3-C11-U2` = the Cash Flow unit inside Module 3's
"Financial Statements of Companies" chapter, 7 topics) — a genuine duplicate-chapter
situation, not a typo, and one already flagged and deliberately resolved toward
`M3-C11-U2` elsewhere in the repo (`books/question-bank/mcq_bank/tag_batch01.py`'s
tagging notes, `topic-index.json`'s `lastUpdated` note) — this was the one place that
decision never propagated to.

Consequence in the *published* book, confirmed before the fix: the "Study Material
Reference" banner atop the chapter, its Table of Contents cross-reference, **and** its
row in the Chapter-wise Sitting Summary (coverage matrix) all pointed at `M1-C4-U2` —
the coverage-matrix row showed **zero marks in every single sitting** for Cash Flow
Statement as a result (real questions existed, just tagged under the code the matrix
was reading numbers *from*).

Pranav confirmed: point everything at `M3-C11-U2`. Fixed the one `CHAPTERS` tuple entry
in `qb_merge.py` (comment explains the history), then re-ran exactly what the runbook's
"what needs re-running" table calls for on a `CHAPTERS`-tuple change: Step 2.5
(`generate_qb_coverage_matrix.py`) → Step 5 (`generate_qb_toc.py`) → Step 6
(`qb_merge.py`) → Step 7 (`resolve_qb_toc_pages.py --remerge`, real headless-Chrome
pagination). Result: still 688 pages, Cash Flow Statement still lands on page 393
(content length unchanged, only the reference code and matrix numbers changed). All of
`HOW-TO-BUILD-THE-BOOK.md`'s Step 7 validation assertions pass (0 blank ToC pages, 0
build-info/extraction-note leftovers, 0 duplicate student-notes strips). Re-ran the new
QA diff tool: **455/455 matched, 0 missing, 0 drifted, 0 orphan** — confirmed clean.

**Grepped the whole repo for every `M1-C4-U2` occurrence to check for other drift**
(Pranav explicitly asked for full consistency, not just the banner): confirmed
`generate_qb_toc.py` and `generate_qb_coverage_matrix.py` both import `CHAPTERS`
directly from `qb_merge.py` (single source of truth, no separate copy to fix). All
other `M1-C4-U2` occurrences in the repo are legitimate — the real Module 1 AS 3
chapter entry in files 0/1, and the `books/question-bank/mcq_bank/` pipeline's own
(separate, already-correct) tagging notes about the same duplicate.

**Left untouched, flagged instead of silently fixed:** `first_run/output/
final_deliverable/` holds already-built, named "V1" / "_protect" (watermarked,
encrypted) PDFs of the Question Bank Book, generated 2026-07-28/30 — before this fix,
so they still carry the wrong Cash Flow Statement reference. This looks like a
already-distributed or ready-to-distribute deliverable folder, not pipeline scratch
output, so it was not regenerated or overwritten without asking. If a corrected PDF
release is wanted, that's a separate explicit step (open the fixed
`QUESTION-BANK-BOOK.html` in Chrome, Ctrl+P → Save as PDF, then re-run whatever
watermark/protect script produced the "_protect" version).

---

## 2026-07-28 (cont'd, 4) — Question Bank Book: full print-cost reduction pass implemented, 819 → 688 pages

Pranav gave the go-ahead to implement the punch list from the previous entry, plus new
points: a new `topic_name_abbvtd` field he added to
`books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`,
a redesigned Error Register (one shared 6-page/3-double-sided-sheet appendix instead of
34 per-chapter pages), and dropping the redundant chapter-name repeat on every
question's topic line. Explicitly asked to skip visual (screenshot) verification for
now and just document + hand over the final path.

**All implemented, pipeline rebuilt and re-validated after every change:**

1. **Topic-wise Marks Mapping bug, root cause confirmed and fixed.**
   `extract_questions.py`'s `extract_topics()` now also captures `data-subtopictitle`
   (was already present on the source tags, just never read). New
   `qb_common.abbreviated_topic_label()` prefers file 1's `topic_name_abbvtd` (matched
   via `topic_no` for the plain-integer tagging convention, e.g. Framework's "7",
   "7/9/11") and falls back to `subtopictitle` otherwise. Spot-checked on the Framework
   chapter: rows now read "6 — Fundamental Accounting Assumptions",
   "7/9/11 — Qual. Char. Fin Stmts / Elements of Financial Statements / Capital
   Maintenance", etc. — no longer the same chapter title repeated on every row.
2. **Per-question topic line no longer repeats the chapter name** — same
   `abbreviated_topic_label()`, used in `topic_full_label()` too. Shows just
   `Topic {ref}: {name}`.
3. **Empty Descriptive/Integrated sections omitted entirely** — no heading, no "no
   questions" placeholder, when a section has zero rows (`render_section()`).
4. **Repeated per-box provenance sentence removed** (~500+ Author's
   Note/Examiner's Comment boxes) — the explanation now lives once in front matter's
   How to Read This Book colour key.
5. **3-line student-fields block collapsed to 1 line**, renamed "My Notebook Ref No" →
   "My NB Page No"; the My Tag suggestion examples moved into front matter (stated
   once, not per question). "Student Self Notes" (the 2-line writing box) was
   correctly kept — a first draft of this edit accidentally deleted it entirely,
   caught and fixed in the same pass before it reached the pipeline.
6. **Error Register redesigned**: `generate_chapter_book.py` no longer emits any
   `.error-register` content per chapter (was 34 full pages). New
   `generate_qb_front_back_matter.build_error_register_pages()` builds ONE shared
   6-page appendix (3 double-sided sheets, alternating "Concepts I Forgot"/"Mistakes I
   Repeated More Than Twice") with a "Chapter/Topic" column so one register serves the
   whole book, appended at the very end of back matter.
7. **Coverage-matrix chapter column** now uses file 1's existing `chapter_name_short`
   field (via a new `qb_common.chapter_name_short_lookup()`) instead of an ad hoc
   string-split, plus CSS wrapping (`max-width`/`overflow-wrap`, `white-space: nowrap`
   removed) as a fallback for names still long after abbreviation (Framework's short
   name barely shortens the full one) — both fixes applied together as Pranav asked.
8. **Page-break blank-space bug fixed**: `table` and `.answer-block` removed from
   `qb_common.print_layer_css()`'s `break-inside: avoid` list — the exact same
   "large container jumps whole, leaves the rest of the page blank" failure the
   `.qblock` fix (2026-07-26) already solved once, rediscovered one container level
   deeper after Pranav sent real screenshots. A table with proper thead/tbody already
   only splits between whole rows, so this is safe, not a new risk.
9. **Margins checked, left unchanged** — already at a documented 6mm floor (cut from
   20mm previously), flagged as near the physical print-safety limit; explained to
   Pranav rather than reduced further.

**Two real mistakes caught and fixed within this same pass, before they reached the
pipeline**: (a) the student-fields collapse first draft deleted the separate "Student
Self Notes" writing box entirely, not just the 3 metadata lines — restored; (b) the
new CSS comment explaining fix #8 used markdown-style backtick-quoting
(`` `table` ``/`` `.answer-block` ``), which tripped this pipeline's own hard
"0 backticks anywhere" validation rule — reworded without backticks.

**Result**: full pipeline re-run (extract → chapter books → coverage matrix → stats →
front/back matter → ToC → merge → resolve) end-to-end. **688 pages**, down from 819
(131 pages / ~16%, all from removing genuine repetition and fixing real bugs, no
content cut). Validated: 0 unclosed tags (full `html.parser` pass), 0 duplicate ids,
0 NUL bytes, 0 backticks, 0 blank ToC pages.

**Not done this pass, by Pranav's explicit request**: visual/screenshot verification of
the page-break fix and the coverage-matrix wrapping. A PDF was generated via headless
Chrome (proving pagination completes and is stable at 688 pages) but not visually
reviewed page-by-page. If blank-space complaints continue after this fix, that
verification is the first real next step, not re-guessing the CSS further.

Final book: `first_run/output/QUESTION-BANK-BOOK.html`. Full detail in
`first_run/HOW-TO-BUILD-THE-BOOK.md`'s "Print-cost reduction pass" section and its two
new gotchas, and `CLAUDE.md` §6.

---

## 2026-07-28 (cont'd, 3) — Question Bank Book: Pranav's print-review punch list (recorded, NOT yet actioned — he's still reviewing)

Pranav is reviewing the 819-page merged book and sent a first batch of review points,
explicitly asking to record them and hold off implementing until he says go (he's
still reviewing, more points likely to follow). Recorded here verbatim/summarized so
nothing is lost; **none of these are implemented yet**.

1. **Empty sections should be omitted entirely, not printed as "No questions..."** —
   e.g. an empty "II. Integrated Questions" section currently still prints its heading
   + intro sentence + the honest-finding note. Only render a section when it has rows.
2. **Remove the per-box "Written by the author, not ICAI..." provenance line** — stated
   once already in front matter (How to Read This Book / Book Coverage), repeating it
   under every single Author's Note box is redundant. Drop the repeated line, keep the
   once-stated explanation in front matter.
3. **Collapse the 3-line student-fields block into 1 line**, and rename "My Notebook
   Ref No" → "My NB Page No": `My NB Page No ______  My Tag ______  Revision Phase 1 2 3`
   — currently 3 separate `<div>` lines per question. Also move the "e.g. Last-day
   Revision, Not Important..." explainer for My Tag into front matter (state once, not
   per question).
4. **Chapter-Wise Sitting Summary table: chapter-name column too wide** — long names
   like "Framework for Preparation and Presentation of Financial Statements" push the
   table past the page margin. Needs a smaller font and/or wrapping for the chapter
   column.
5. **Real print flow problem: wasted blank space after each question, answer restarts
   on a fresh page** — needs investigation into why content isn't flowing continuously
   (likely `break-inside: avoid` on `.answer-block`/`table` forcing a jump to the next
   page when the remaining space on the current page is too short, rather than letting
   a long table split across the break). Needs actual visual verification (screenshot),
   not just CSS reasoning — same lesson CLAUDE.md §7 already states.
6. **Real bug, root cause confirmed this session (see above)**: the new Topic-wise
   Marks Mapping table shows the same chapter-level title repeated on every row
   instead of each row's actual topic name. Cause: `extract_questions.py`'s
   `extract_topics()` (line 53) only captures `data-title` (chapter-level, same for
   every question in that chapter) from each sitting HTML's `topic-tag` span — it never
   captures `data-subtopictitle`, which already exists on the source tags with correct,
   specific per-topic text (confirmed present and accurate via direct grep against
   `MTP_May2023_Set1.html`). Fix: capture `data-subtopictitle` in `extract_topics()`,
   re-run `extract_questions.py`, and use it (not `title`) for the table's row label in
   `generate_chapter_book.py`'s `subtopic_key()`. Not a data-quality problem — the
   sitting HTML tagging itself is fine; only the extraction script drops a field that
   was always there.

**Also asked for**: genuine page-count-reduction ideas (separate from the fixes above,
which are also page-saving as a side effect). Ideas given in-conversation, not yet
written up as a durable doc — revisit and formalize once Pranav finishes this review
pass and gives the go-ahead to implement.

---

## 2026-07-28 (cont'd, 2) — Question Bank Book: Chapter-wise Sitting Summary + per-chapter Topic-wise Summary built (819 pages)

Pranav's request, once the 34-sitting corpus was complete: a whole-book "which chapter
matters most" marks-coverage table near the front, and a per-chapter "which topic
within this chapter matters most" table at the start of each chapter. OP/PP explicitly
confirmed out of scope for this edition (not deferred-but-maybe — a firm decision, see
the previous entry).

**Built:**
- Three new shared helpers in `qb_common.py` (`session_label()`, `dedup_marks_sum()`,
  `dedup_count()`, `sessions_for()`) so both new features and any future one share
  identical marks-aggregation logic — no risk of two tables disagreeing on a number.
- `generate_qb_coverage_matrix.py` (new script) → `output/chapter-coverage-matrix.html`:
  3 pages (MTP/RTP/PYQ), each a chapter × exam-session marks matrix, one column per
  session (an MTP session's Set 1 + Set 2 combine into one column), Total column at the
  end. RTP pages show question **count**, not marks — ICAI's RTP documents carry no
  per-question marks key, confirmed already known from `book_stats.json`. Wired into
  `qb_merge.py`'s `BOOK_ORDER`, right after the ToC.
- `generate_chapter_book.py`: a Topic-wise Marks Mapping table added to every chapter,
  right after the intro notes. **Real finding, fixed same session**: the first combined
  draft (one table, all paper types together) produced 22 columns for AS 2 — the exact
  print-width problem the whole-book matrix exists to avoid, rediscovered one level
  deeper than expected (a "single chapter" isn't automatically narrow if it's tested in
  nearly every sitting). Fixed by splitting into up to 3 mini-tables per chapter
  (MTP/PYQ marks, RTP count), same pattern as the whole-book version.

**Validated**: all 34 regenerated chapter books + the new coverage-matrix page pass a
full `html.parser` structural pass (0 errors) and a duplicate-id check (corrected to
properly anchor the regex after an earlier false-positive from `data-target-id=`
matching a naive `id="..."` pattern). Full pipeline re-run end-to-end (stats → coverage
matrix → front/back matter → ToC → merge → resolve): **819 pages** (up from 796),
38 merged sections (was 37).

Both features and the OP/PP-out-of-scope decision are documented in
`first_run/HOW-TO-BUILD-THE-BOOK.md` §5/§6 and `CLAUDE.md` §6.

---

## 2026-07-28 (cont'd) — Question Bank Book: all 34 sittings built, full pipeline rebuilt (796 pages)

Completed the scaling work the previous entry left in progress: all 24 remaining
sittings are now built and independently validated (structural checks re-run by the
orchestrating session on every file, not just trusted from each agent's self-report —
two real defects were caught this way: a stray backtick in `PYQ_Nov2023.html`'s
extraction-note, fixed directly; and my own validation script's false-positive
duplicate-id count, caused by an unanchored regex matching `data-target-id="..."`
as if it were `id="..."` — the actual merged book has 0 real duplicate ids, confirmed
with a corrected regex plus a full `html.parser` structural pass, 0 errors).

**Blocker resolved mid-session**: the account's monthly Claude spend limit that paused
the previous entry's batch reset partway through — confirmed by a live retry, not
assumed. Two further spend-limit hits occurred later in the same session; in every
case, the agent's `Write` call had already completed before the process was killed,
so the file survived regardless — this pattern (write to disk as early as possible,
refine in place) is now baked into every sitting-build agent's instructions going
forward, per Pranav's explicit request.

**Real finding, confirmed at scale**: 47 question records across 13 distinct
pre-syllabus-change topics (Hire Purchase, Departmental Accounts, Incomplete Records,
Insurance Claims for Loss of Stock, Redemption of Debentures/Preference Shares, Profit
Prior to Incorporation, Bonus Shares, Managerial Remuneration, Issue of Debentures,
Rights Issue) were tagged `LEGACY-*` across the older 2023 sittings. Fixed
`generate_all_chapter_books.py` and `generate_book_stats.py` to explicitly skip/report
these rather than silently including them or crashing — confirmed working: pipeline
run shows "Skipped 47 LEGACY records across 13 topics" and generates exactly 34
legitimate chapter books, no stray `LEGACY_Question_Book.html` file.

**Full pipeline rebuilt end-to-end** with all 34 sittings:
`extract_questions.py` (831 total question records, 897 counting case-scenario nodes)
→ `generate_all_chapter_books.py` (34 chapter books, incl. AS 1 and AS 27 now finally
covered — both previously the only two genuinely untouched chapters) →
`generate_book_stats.py` → `generate_qb_front_back_matter.py` → `generate_qb_toc.py`
→ `qb_merge.py` → `resolve_qb_toc_pages.py --remerge`. Final `QUESTION-BANK-BOOK.html`:
**796 pages** (up from 308 with the 10-sitting pilot), all 34 chapters' ToC page
numbers correctly resolved. Corpus totals: 437 distinct question numbers as originally
printed, 3,096 total marks covered, 68 real ICAI Examiner's Comments matched (up from
24) + 763 synthesized Author's Notes.

**Next**: build the two summary-table features locked in earlier this session
(Chapter-wise Sitting Summary, per-chapter Topic-wise Summary — see the previous
entry and `CLAUDE.md` §6) now that the full 34-sitting corpus finally exists, which
was the explicit precondition for starting that work.

---

## 2026-07-28 — Question Bank Book: scaling to all 34 sittings (in progress, paused on account spend limit); OP/PP scoped out of edition 1; two new summary-table features locked in

Pranav asked to build all 24 remaining in-scope sittings (from `first_run/pending/`
PDFs + `first_run/output/pending-pdf-parsed-clean/` MD aids), using the same
parallel-background-agent-per-sitting pattern this session established, batched ~5 at
a time with independent re-validation after each batch (both the agent's own
self-check and a second structural check run by the orchestrating session before
trusting the result).

**Progress at pause: 14 of 24 built and independently validated** — MTP Jan2025
Set1/Set2, PYQ Jan2025, RTP Jan2025, PYQ May2023, MTP May2023 Set1/Set2, MTP May2024
Set1/Set2, PYQ May2024, RTP May2024, MTP May2025 Set2, PYQ May2025, RTP May2025. **1
never written** (MTP May2025 Set1 — its agent died before the Write call ran). **9 not
yet started**: MTP Nov2023 Set1/Set2, PYQ Nov2023, MTP Sep2024 Set1/Set2, PYQ Sep2024,
RTP Sep2024, MTP Sep2025 Set1/Set2.

**Real finding, now a locked rule**: several 2023-vintage sittings test topics from
before a syllabus change, absent from the current 36-chapter taxonomy entirely (Hire
Purchase, Departmental Accounts, Incomplete Records, Insurance Claims for Loss of
Stock, Redemption of Debentures/Preference Shares, Profit Prior to Incorporation,
Bonus Shares, Managerial Remuneration). Tagged `LEGACY-{SLUG}` + `data-issue="topic-
legacy-not-in-current-syllabus"`; Pranav's call: keep them in the sitting record for
completeness, exclude from generated chapter books entirely (no appendix this
edition). Full detail: `CLAUDE.md` §6.

**Blocker (paused here, not a pipeline bug)**: batch 3's remaining agents all failed
mid-work on the account's **monthly Claude spend limit**. 4 of those 5 agents'
`Write` calls had already completed before the API error killed them, so their files
survived and were independently validated anyway — confirms the per-sitting
save-as-you-go approach is robust to a mid-batch failure. Resume once the daily/
monthly usage allowance is confirmed available again.

**Two scope decisions, both Pranav's call, both documented in full in `CLAUDE.md` §6**:
1. **OP/PP recurring-question detection is explicitly OUT of this edition's scope**
   (not just "still not built") — deferred to a dedicated post-launch effort once the
   full 34-sitting corpus exists, since the ≥90%-similarity comparison is O(n²) over
   the whole corpus and running it against a partial corpus now would mean redoing it
   later for nothing.
2. **Two new locked-in features, not yet built**: a whole-book **Chapter-wise Sitting
   Summary** (marks-coverage matrix, one column per exam session not per individual
   paper/set, split into 3 pages — MTP/RTP/PYQ — for print width, each with a
   row-summed Total column) near the front matter, and a narrower **per-chapter
   Topic-wise Summary** at the start of each chapter book (formalizing the exact
   pattern Pranav already hand-built for the AS10 pilot in
   `AS10_Question_Reference.html`). Both are pure `questions_index.json` derivations,
   no new tagging needed — build both only after all 34 sittings are in, for the same
   reason as the OP/PP deferral.

---

## 2026-07-27 (cont'd, 4) — Question Bank Book: wired book_stats.json into the actual front matter as a "Book Coverage at a Glance" page

Pranav's ask, after reviewing what `generate_book_stats.py` computes: don't leave it
sitting unused in `book_stats.json` — bake it into the book itself. Also asked to
confirm (not just recall) that color-coding, headers/footers, and student-notes boxes
are genuinely script-generated, not manually patched — verified directly by grepping
`generate_chapter_book.py`/`qb_common.py` before answering (they are: `.mistakes
icai`/`.mistakes synth` per-question, static `.brand-header`/`.brand-footer` plus a
separate print running-header/footer via `position: running()`, and
`.self-notes`/`.notebook-ref`/`.revision-phase` all rendered inline in
`render_qblock()`).

**Implemented:**
- `generate_qb_front_back_matter.py` now reads `output/generated-from-script/
  book_stats.json` (hard error if missing/stale — never silently builds a front matter
  without it) and renders a new "Book Coverage at a Glance" front-matter page: 6 stat
  tiles (sittings covered, distinct questions, question records incl. split parts,
  chapters touched of 36, total marks, real ICAI examiner's comments), the full sittings
  list, and 3 honest caveat notes (why MTP/PYQ sittings sum to 114 not 100, why RTP
  shows 0 marks, how many mistake notes are synthesized vs real). Every number is read
  live at generation time, never hand-typed.
- New CSS (`.qb-stats-grid`/`.qb-stat-tile`/`.qb-stats-sittings`) added to
  `qb_common.front_back_css()` so `qb_merge.py` picks it up automatically for the merged
  book too — one shared definition, not duplicated.
- `generate_book_stats.py` is now a **required** upstream step (Step 3), not an
  optional/informational one — `HOW-TO-BUILD-THE-BOOK.md` updated throughout (step
  descriptions, the "what needs re-running" table, the architecture note, the
  copy-paste command block) to reflect the new Step 3 → Step 4 dependency.

**Ran the full pipeline end-to-end to confirm it actually works**: `generate_book_stats.py`
→ `generate_qb_front_back_matter.py` → `generate_qb_toc.py` → `qb_merge.py` →
`resolve_qb_toc_pages.py --remerge`. Book grew from 307 to **308 pages** (exactly the one
new front-matter page, as expected). Validated: all prior checks still pass (0 blank ToC
pages, 0 build-info/extraction-note leftovers, 0 duplicate student-notes strips), plus new
checks confirming the stats page and its 6 tiles are present in the final merged
`QUESTION-BANK-BOOK.html`.

---

## 2026-07-27 (cont'd, 3) — CLAUDE.md reconciled: fixed stale/contradictory statements, documented the multi-agent reality, added Claude_V2.md to the read order

Pranav's ask: "document all of your skills, understanding into the claude.md file... make
sure even a fresh git repo pull will give all the context to that new AI after reading
claude.md and claude_v2.md... don't repeat things and ensure things are not contradictory."

Read `Claude_V2.md` in full (690 lines) first — confirmed it's entirely Strategy-Book
(Pillar 1) specific, zero overlap with Question Bank content, so nothing there needed
touching. All the actual staleness was in `CLAUDE.md` §6, left behind by today's rapid
pace of work:
- Two "still not built" statements about the whole-book merge script were now flatly
  false (it's built and proven — see the previous entry). Annotated both in place as
  historical rather than deleting them, and added the real current-state entry at the
  end of §6.
- The "unconfirmed origin" note about `QUESTION-BANK-BOOK.html`/`front-matter.html`/
  `back-matter.html`/`vendor/` was stale — their origin (the Codex session) is now
  confirmed and documented.
- §3's `first_run/` folder-table row hadn't been updated since the merge/ToC/stats
  scripts were added — now lists all of them and points to the new
  `HOW-TO-BUILD-THE-BOOK.md`.
- Added an explicit "this repo has multiple concurrent AI sessions" callout to §2
  (working rules) — this has caused real confusion and even a git-history divergence
  requiring a manual merge (see the 2026-07-27 entry further down) — worth stating
  plainly rather than leaving future sessions to piece it together from scattered
  mentions.
- Added `Claude_V2.md` to §1's mandatory read order (conditional on the task touching
  the Strategy Book, same pattern as the existing `content/README.md` conditional entry)
  — it was previously only cited deep in §7, easy to miss on a fresh clone.

Ran `tools/health_check.py` and `tools/file_index.py` afterward — same 16 pre-existing,
unrelated failures as before this session started (stale `EXPECTED_DIRS`, bridge-course
NUL bytes, undocumented `capranav_com/`), nothing new introduced.

---

## 2026-07-27 (cont'd, 2) — Question Bank Book: took full ownership of the whole-book pipeline, audited every file, ran it end-to-end, wrote the master runbook

Pranav's ask: "take full control of the entire book and entire flow," go through every
file the parallel agent had built, fix small bugs directly, only pause on major issues,
and produce one final MD file documenting the whole build end-to-end.

**Audit findings:**
- The student-notes duplication risk flagged in the previous session (my per-question
  fields in `generate_chapter_book.py` vs. `qb_common.py`'s `inject_student_notes()`)
  had **already been found and fixed** by the parallel agent — `page_shell()` no longer
  calls that function, confirmed by grepping the merged book (0 occurrences of the old
  strip's text, all of my new fields present and correct, `build-info`/`Extraction note`
  both at 0). No action needed there, just verified.
- **Real gap found and fixed**: `qb_common.front_back_css()` already defined `.qb-howto`
  and `.qb-legend-*` CSS classes, but no page anywhere in the actual HTML used them — a
  "How to Read This Book" legend page was designed (CSS existed) but never actually
  written into `front-matter.html`. Added the page (condensed from the existing
  `first_run/output/How-to-Read-this-Book.md`), plus 3 more legend swatches
  (`qb-legend-answer`/`qb-legend-case`/`qb-legend-flagged`) alongside the 2 that already
  existed (`qb-legend-examiner`/`qb-legend-author`) so all five colour-coded box types
  get a swatch, not just two.
- **Real bug found and fixed**: `resolve_qb_toc_pages.py` builds a `file://` URL and
  passes it unencoded into an HTTP request to Chrome's DevTools endpoint — a raw space
  in the repo's path (this clone sits under `.../Other computers/...`) makes
  `http.client` reject the request outright. Fixed with `urllib.parse.quote(file_url,
  safe=":/")` before use; safe regardless of whether a given path has a space in it.

**Ran the full pipeline end-to-end** for the first time in one continuous pass:
`generate_all_chapter_books.py` → `generate_book_stats.py` →
`generate_qb_front_back_matter.py` → `generate_qb_toc.py` → `qb_merge.py` →
`resolve_qb_toc_pages.py --remerge` (had to `pip install websocket-client` first, not
previously installed in this environment). Final `QUESTION-BANK-BOOK.html`: **307 pages**,
all 34 ToC page numbers correctly resolved and baked in, validated clean (0 unclosed
tags, 0 duplicate ids, 0 NUL bytes, 0 backticks, 0 placeholders, 0 leftover build-info/
extraction-note text, 0 duplicate student-notes strips).

**New file**: `first_run/HOW-TO-BUILD-THE-BOOK.md` — the master end-to-end runbook
Pranav asked for: architecture diagram, folder map, prerequisites, the exact 7-step
command sequence (extract → chapter books → stats → front/back matter → ToC → merge →
resolve-and-remerge → manual PDF export), a "what needs re-running after X changes"
table, every fixed-incident gotcha in one place, and the still-open items (OP/PP tags,
short chapter names). `SKILL-question-bank-pipeline-overview.md` updated to point to it
and to describe the now-complete merge/ToC/front-back-matter stages instead of
describing them as future work.

---

## 2026-07-27 (cont'd) — Question Bank Book: Dedication added, How-to-Use removed (superseded by How-to-Read-this-Book.md), ToC split into its own file

Pranav's follow-up after reviewing the front matter and the stats script:

1. **Dedication page added.** Reused the Strategy Book's exact dedication (same real people: parents, sister, CA Deepak Pandey, CA Mukul Bhatt, CA Praveen Sharma, CA Gurpreet Singh & Rahul Bhutani) rather than inventing a different one, since Pranav didn't ask for a different dedication when given the choice. New `.qb-dedication-block`/`.qb-ded-*` CSS in `qb_common.front_back_css()`, ported from the Strategy Book's own rules onto this book's CSS variable names.
2. **"How to Use This Book" removed from front matter.** The other session's `How-to-Read-this-Book.md` is more comprehensive and already describes the current (post-redesign) book shape accurately — mine was still describing the old 3-section MCQ/Descriptive/Integrated structure, now stale anyway. Removed rather than kept as a second, competing copy.
3. **Table of Contents split into its own file**, `first_run/output/table-of-contents.html`, generated by a rewritten `generate_qb_toc.py` -- confirmed directly for Pranav: **the ToC is 100% script-derived, not hand-typed.** Every row's chapter order, label, and study-material code comes straight from `qb_merge.py`'s `CHAPTERS` tuple; the only thing not computed at generation time is the page number, which can't be known until the book is actually paginated -- `resolve_qb_toc_pages.py` fills that in afterward from a real headless-Chrome pass. Rewriting this as a fully-owned, always-regenerated-from-scratch file also permanently closes the class of bug from the previous "patch an existing div" approach (the ToC-duplication bug fixed earlier this week) -- there's no longer any existing content for a bad patch to leave behind.
4. Moved `wrap_page()` (the shared standalone-HTML-file shell) into `qb_common.py` so all three front-matter-shaped files (front-matter.html, back-matter.html, table-of-contents.html) share one copy instead of two independently hand-kept ones.
5. **Disabled the merge-time `inject_student_notes()` overlay** in `qb_common.page_shell()` -- the 34 chapter files (redesigned outside this session, see the 2026-07-27 entry above) now have their own richer, built-in self-notes/notebook-ref/tag/revision-phase block per question. Calling both would have printed the exact kind of duplication Pranav asked to avoid elsewhere this same conversation. Function left defined, not deleted, in case a future chapter-book redesign drops its own version again.

Re-merged and verified clean: 305 pages (down from 368, mostly because the redesigned chapter files no longer include MCQs), 0 duplicate ids, dedication renders correctly on its own page, ToC starts immediately after with all 34 real page numbers resolved.

**Still not reconciled (flagged, not fixed this pass)**: the chapter-print CSS overrides (`print_layer_css()`'s `chapter_print_*` font-size rules) don't yet cover the new chapter classes (`.self-notes`, `.brand-header`, `.brand-footer`, `.error-register`), so those render at their original (larger) size; and the redesigned per-question content is tall enough with its own new fields that some pages show the same kind of trailing whitespace the earlier page-break fix addressed for the old shape -- would need the same break-inside review applied to the new elements.

---

## 2026-07-27 — Book stats script built; discovered the 34 chapter files were substantially redesigned outside this session

Two things this session, in order:

**1. Discovered `generate_chapter_book.py` and all 34 chapter files were regenerated/redesigned outside this conversation** (files dated 2026-07-26 ~20:2x-20:3x, after this session's earlier merge work that day). Real, confirmed changes: MCQs are now deliberately excluded from the printed chapter books (they're described as living on "the dedicated MCQ platform" instead -- only Descriptive + Integrated sections remain); the old `id="AS02-NNN"` bug is fixed at the source now (ids are correctly per-chapter, e.g. `M2C5U2-001`); a richer built-in self-notes/notebook-ref/tag-placeholder/revision-phase block was added per question (overlapping with, and now superseding, the simpler one-line strip this session had injected at merge time); a per-chapter brand-header/footer and a back-of-chapter "Sanjeevani Booti 2: Error Register" section were added. **Not yet reconciled with the merge pipeline** (`qb_merge.py`/`qb_common.py` still assume the old shape in places -- e.g. the now-redundant `inject_student_notes()` merge-time overlay, and the chapter_print_* font overrides don't yet cover the new `.self-notes`/`.brand-header`/`.error-register` classes) -- flagged to Pranav directly rather than guessed at; the previously-delivered `QUESTION-BANK-BOOK.html` is stale against this and needs a full re-merge once the reconciliation approach is agreed.

**2. Built `first_run/scripts/generate_book_stats.py`** (Pranav's request: a script-driven book-coverage summary — attempts covered, question counts including parts/sub-parts, total marks). Reads `questions_index.json` (Layer 2) directly rather than the 34 chapter files, deliberately: chapter-book rendering policy (MCQs in/out) can keep changing, but the underlying question corpus is stable, so the stats describe the corpus with the current rendering policy called out as a separate, explicit fact rather than baked into the numbers.

Ran it and checked every surprising number against the raw data before trusting it, rather than reporting them as-is:
- **275 total question records** (already parts/sub-parts-inclusive, since independent splitting happens at extraction) across the 10 known sittings; **165 distinct question numbers as originally printed** (collapsing split sub-parts and OR-alternative pairs back to their real printed number).
- **"Easy" for all 275 rows on the difficulty field** — checked topic_count distribution directly (272 rows touch exactly 1 topic, 3 touch 2), confirmed this is a real consequence of the splitting design, not a computation bug; the difficulty label currently carries near-zero signal.
- **RTP sittings show 0 marks** — confirmed by grepping the raw sitting HTML: RTP files genuinely have zero `data-marks` attributes anywhere (ICAI's RTP documents don't publish a marks-weighted answer key), matching an already-documented, expected behavior from 2026-07-26's log, not new data loss.
- **Each MTP/PYQ sitting sums to 114 marks, not the nominal 100** — traced to Part II's "answer any N of the remaining M" choice structure: the book deliberately includes every optional question shown (Q1-Q6, 84 marks) rather than only the subset (Q1-Q5, 70 marks) one specific sitting required, so a student can practice all of them. Verified consistent (30 + 84 = 114) across all 7 MTP/PYQ sittings, confirming it's structural, not a one-off tagging error.

Every one of those four "this looks wrong" moments turned out to be either already-documented expected behavior or a real, traceable structural fact -- none were left unexplained in the script's own output (each has an inline NOTE in both the console summary and the written `book_stats.json`).

**Not yet done**: wiring these stats into an actual front-matter page (Pranav asked to confirm the script works first, before deciding where in the book's flow to place it) -- `book_stats.json` is written to `first_run/output/generated-from-script/` for now, nothing reads it yet.

---

## 2026-07-26 (cont'd, 8) — Question Bank Book: chapter-book reader-experience overhaul (MCQs removed, Integrated-topic bug fixed, several new student-facing fields)

Pranav sent a 16-point review of the rendered chapter books; asked for feedback/plan first (delivered), then to implement all "straightforward" items and report what's left.

**Implemented in `generate_chapter_book.py`, all 34 books regenerated and re-validated clean (0 unclosed tags/NUL/backticks/placeholders/duplicate IDs):**
- MCQs removed from the book entirely (still in sitting HTML + `questions_index.json`, just not rendered) — sections renumbered to I. Descriptive, II. Integrated.
- Fixed a real bug: `topic_label()` used to show only the current chapter's tag on an Integrated-section row, hiding the question's other tested standard (found via `AS16_Question_Book.html`'s MTP_May2026_Set2 Q8 — showed "AS 16" only despite also testing AS 10). Now shows every tagged topic.
- Topic tags now render in full (`M1_C2_U0 : Framework for Preparation and Presentation of Financial Statements / ICAI Study Mat Topic No : 7/9/11`) instead of the old compressed `Framework (7/9/11)`.
- Examiner's Comment (tan/orange) vs Author's Note (pale pink) now actually colour-differ, matching `book-style.json` — previously both rendered in one flat colour despite the front-matter legend promising a distinction.
- New "Approx Time" field (`ceil(marks × 1.8)` minutes, computed at generation time; RTP with no stated marks shows a "10–20 minutes" range).
- Removed from rendered output (data still in JSON): per-question Extraction Note, file-level Build Info footer.
- New per-question fields: blank Student Self Notes box, My Notebook Ref No, freeform My Tag, Revision Phase 1/2/3 tick-boxes.
- New chapter-end blank page: "Sanjeevani Booti 2: Error Register" (dotted lines, 40% opacity, two sections).
- New static header/footer branding (Pranav Bhaiya / Newton of Accounts / AIR 1-1-5 / Kahaan-Koncept-Karma) on each standalone chapter file — **not** the same as a print running-header-on-every-physical-page, which belongs to the other agent's merge/pagination scripts (`qb_merge.py`/`qb_common.py`) and isn't wired up there yet.
- Title simplified to `{Standard} — {Chapter}`, no "Question Book" suffix.
- New `first_run/output/How-to-Read-this-Book.md` — student-facing guide to every colour/field and why it exists; each chapter book's "how this is organised" note now points here.

**Explicitly parked (need more design or Pranav's input, not built this pass):** OP/PP recurring-question tags (duplicate-detection design exists, never built) and a short-chapter-name field for the topic-index taxonomy (needs Pranav to help draft ~36 short names). Both named honestly as "coming in a future edition" in the new guide.

**Flag for the parallel agent running the whole-book merge**: this pass changed the DOM/CSS inside each chapter book — removed `.extraction-note` and `.build-info` divs, added `.self-notes`/`.notebook-ref`/`.tag-placeholder`/`.revision-phase`/`.error-register` (the last has `page-break-before:always`), changed `.mistakes` to need an `.icai`/`.synth` subclass for colour. If `qb_merge.py`/`qb_common.py` has any CSS or structural assumptions keyed to the old markup (e.g. selectors targeting `.extraction-note`/`.build-info`, or page-count math from the earlier print-cost pass), it should be re-checked against the regenerated files before the next merged-book build.

---

## 2026-07-26 (cont'd, 7) — Question Bank Book: ToC-duplication bug fixed, study-material cross-reference added, page-break waste cut, student-notes strip added

Pranav's review of the merged book (388 pages, from the print-cost pass) surfaced four things in one message. All four addressed:

1. **Real bug: Table of Contents was duplicating on re-runs.** Root cause: `generate_qb_toc.py`'s patch regex used a non-greedy `(.*?)(</div>)` to find the ToC list div's closing tag -- correct only while that div was still empty. Once it held 34 nested `<div class="qb-toc-entry">` rows, the lazy match stopped at row 1's own `</div>` instead of the list's real closing tag, so every re-run replaced only row 1 and left the old rows sitting there, growing by ~33 stale rows each time (confirmed: 67 entries in the file Pranav flagged, exactly 34 fresh + 33 leftover). Fixed with balanced-`<div>`-tag counting instead of regex (`_find_matching_close()`), verified idempotent by running it 3 times in a row and confirming the count stays at 34.

2. **Chapter <-> study-material cross-reference, added.** Each of the 34 `CHAPTERS` entries in `qb_merge.py` now carries a 4th field, `study_material_ref` (e.g. `"M2-C5-U1"`), sourced from `1-ca-inter-adv-accounts-topic-page-index.json`'s `unique_chapter_id` -- deliberately NOT `metadata-index/topic-index.json` (which already correctly drives each *question's* own subtopic tag like "AS 2 (1.4)", untouched) since that file only covers 32/36 chapters and documents itself as secondary to file 1 for chapter-level IDs. Shows as a small chip next to every ToC entry and as a one-line "Study Material Reference: M2-C5-U1" banner at the top of each chapter.

3. **Page-break waste, measured and fixed.** Pranav's instinct that "each question starting from a new page" was wasteful was checked against real data, not assumed: 312 of 334 content pages (93%) held exactly 1 qblock, averaging 282px of ~960px (29%) unused per page. Cause: `break-inside: avoid` was set on the whole `.qblock` container, so any question too tall for the remaining space on a page jumped ENTIRELY to the next page rather than just the part that didn't fit. Fixed by moving `break-inside: avoid` down to the smaller indivisible pieces inside a qblock (`.question`, `.answer-block`, `.mistakes`, `.extraction-note`, `table`, `.note`, `.case-facts`, `.empty-section` -- confirmed these are real sibling `<div>`s, not guessed) and removing it from `.qblock` itself, so a page break can now fall between a question's own Question/Answer/Notes sections instead of only between different questions. Cut 388 -> 361 pages on its own.

4. **Student self-notes + notebook-page-reference strip, added to every question.** A compact one-line strip ("Your Notes: ______ Practiced in Notebook — Page No.: ____") injected after each qblock's content via `qb_common.inject_student_notes()`, using the same balanced-div-counting technique as the ToC fix (a qblock's real closing tag is not the first `</div>` inside it either). Applied only at merge time -- the 34 source chapter files (screen-review copies) are untouched, this only exists in the print-ready merged book, which is the only place a student would actually write in it. Kept deliberately compact (single line, not a ruled box) given the same-day cost-cutting effort: added only ~7 pages across all 278 questions.

**Net page count after all four fixes: 368** (was 388 before this round; 707 before the whole print-cost pass started). Re-verified structurally clean each time (0 duplicate ids, 0 NUL, 0 backticks, single `<style>`/script) and visually via headless-Chrome screenshots of the ToC and an AS 2 chapter page.

**Not yet done, flagged for a decision, not executed:** nothing outstanding from this round -- all four of Pranav's points were addressed. Still open from earlier: whether to extend the em-dash humanization pass to the 34 chapter files' own content (their own `<h1>`s still have em-dashes), and OP/PP duplicate detection.

---

## 2026-07-26 (cont'd, 6) — Question Bank Book: print-cost reduction (margins + font size), 707 → 388 pages

Pranav asked to shrink margins to "nearly zero" and reduce font size, explicitly for printing cost (page count is the direct cost driver). Both changes went into `first_run/schema/book-style.json` (the single source of truth) and are consumed additively by `qb_common.py`'s `print_layer_css()` — the 34 chapter files' own embedded style is still never touched, this is a merge-time-only override layered on top, same discipline as everything else in this pipeline.

- **Margins**: `page_geometry_for_future_print_stage` cut from 20mm to 6mm on every side — near the practical floor for a home/office printer (many can't guarantee edge printing below ~4-5mm without clipping; true 0mm was avoided for that reason, flagged in a code comment so it's an easy one-line change if Pranav confirms his actual print method can go tighter).
- **Font size**: new `chapter_print_*` fields added to `book-style.json` (body 9pt, h1 15pt, h2 12pt, table 7.5pt, small text 7pt) plus tightened `.qblock` margin/padding — applied only inside `.qb-book-content` (higher specificity than the chapter files' own bare-tag rules, no `!important` needed).
- **Result**: 707 → **388 pages** (~45% cut). Re-verified structurally clean (0 duplicate ids — a first check falsely flagged 34 "duplicates" that turned out to be a regex matching `data-target-id="..."` as if it were `id="..."`, not real; a boundary-safe regex confirmed the true count is 0) and visually via headless-Chrome screenshots (title page and an AS 2 chapter page both still legible at the smaller size).

**Also discovered and adapted to, mid-task, not caused by this session's own work**: sometime between this morning's working merge and this afternoon, the 34 chapter files were moved from `first_run/output/` directly into a new `first_run/output/generated-from-script/` subfolder and regenerated fresh (confirmed by mtimes — content shape/style unchanged, same known `id="AS02-NNN"` bug still present), and the 10 sitting-level files similarly moved into `first_run/output/parsed-from-pdf/`. `qb_merge.py`'s file-existence check caught this immediately (all 34 chapters suddenly "missing") rather than silently merging stale content. Fixed `qb_common.load_chapter_html()` and `qb_merge.py`'s validation to check both the old flat location and the new subfolder, so the pipeline keeps working regardless of which layout is current — worth telling Pranav this reorganization happened, since it wasn't this session's doing and it's unclear if it was intentional or another concurrent process.

**Output** (unchanged path): `first_run/output/QUESTION-BANK-BOOK.html` — 388 pages, same Chrome → Save as PDF workflow.

---

## 2026-07-26 (cont'd, 5) — Question Bank Book: front/back matter, whole-book merge, ToC with real page numbers — full pipeline working end-to-end

Pranav assigned a new deliverable on top of the 34 already-generated chapter files ("the main content is done"): front/back matter, a chapter merge order, and one final single HTML mergeable into a print-ready PDF via Chrome — same "Save as PDF" workflow already proven on the Strategy Book.

**Built, all in `first_run/scripts/`:**
- `qb_common.py` — shared helpers: fixes the real `id="AS02-NNN"` bug (every chapter file hardcodes this id prefix regardless of its actual chapter — confirmed directly, fixed at merge time via slug-prefix rewriting, chapter source files never touched); the print/pagination CSS layer (page geometry literally templated from `book-style.json`, since `@page` doesn't resolve `var()`); front/back-matter-only CSS (title page, copyright page, ToC, author bio).
- `generate_qb_front_back_matter.py` — writes `front-matter.html` (title page, copyright & disclaimers, How to Use This Book, ToC placeholder) and `back-matter.html` (About the Author, closing note) as standalone reviewable files.
- `qb_merge.py` — the whole-book assembler. `CHAPTERS` tuple = 34 chapters in teaching sequence (cross-referenced against `1-ca-inter-adv-accounts-topic-page-index.json`'s `teaching_sequence`; confirmed the 34-vs-36 gap is two deliberate syllabus-pair collapses, not missing content — Financial Statements' two units share one file, and pre-Ind-AS "AS 14" **is** "Amalgamation of Companies" so that pairing shares one file too, confirmed straight from that file's own `<title>`).
- `generate_qb_toc.py` + `resolve_qb_toc_pages.py` — same two-pass pattern as the Strategy Book's ToC (`target-counter()` is confirmed broken in this vendored paged.js; real page numbers come from polling `data-page-number` via a headless-Chrome CDP pass after a first blank-ToC merge, then re-merging).

**Two real bugs found and fixed, both invisible without headless-Chrome verification (reading the code/output alone would have missed both):**
1. Pagination silently never started (0 `.pagedjs_page` elements, no console dialog, no crash) — root cause was `<link rel="stylesheet" href="vendor/gfonts-local.css">` in the merged file's `<head>`: paged.js internally re-fetches every linked stylesheet via XHR to analyze it, and Chrome blocks that XHR under `file://` origin (CORS: "Access to XMLHttpRequest ... blocked by CORS policy"), throwing an uncaught promise rejection that halted initialization before any page ever rendered. Fixed by inlining the font CSS text directly into the merged `<style>` block instead of linking it (with its `url(fonts/...)` paths rewritten to `url(vendor/fonts/...)`, since inlined relative URLs resolve against the *document's* location, not the original CSS file's).
2. The title page's author-name/credential line was rendering on a *different, much later physical page* than the rest of the title page — traced via `getBoundingClientRect()` (not visible from a DOM-only check) to `.qb-title-page`'s `min-height: 220mm` exceeding the actual per-page content-box height (`254mm - 20mm - 20mm = 214mm`, from `book-style.json`): a `display:flex; justify-content:space-between` container that overflows a page boundary doesn't fragment predictably, so its children scattered across pages instead of visibly overflowing where the bug would have been obvious. Fixed: `min-height: 190mm` (safely under the 214mm ceiling) plus `break-inside: avoid` as a second line of defence.

**Verified clean after both fixes** (headless Chrome, real-time `.pagedjs_page`-count polling until stable — no `--dump-dom`/timed-capture shortcuts, per the Strategy Book's established discipline): **707 pages**, 0 duplicate `id` attributes (319 total, verified with a boundary-safe regex after an initial loose regex falsely flagged 34 — those were `data-target-id="..."` substring matches, not real duplicates), exactly one `<style>` block and one `paged.polyfill.js` reference, 0 NUL bytes, 0 backticks, 0 leftover placeholder markers, all 34 ToC entries resolved to real ascending page numbers (7 through 674). Screenshotted the title page, ToC, and an AS 2 chapter-opening page directly (not just DOM-checked) to confirm the visual fix.

**Flagged, not changed:** the 34 chapter files' own content (headings, question text) still contains em-dashes in places — e.g. `AS02_Question_Book.html`'s own `<h1>` reads "AS 2 — Valuation of Inventories: Question Book." Left untouched deliberately, since Pranav said this content is done and out of scope for this task; new content this session (book title, chapter labels in the running header/ToC, all front/back-matter prose) was written without em-dashes from the start, matching the Strategy Book's cleanup discipline. Worth a decision from Pranav on whether the same humanization pass should eventually extend to the 34 chapter files.

**Output:** `first_run/output/QUESTION-BANK-BOOK.html` — open in Chrome, wait for pagination to finish (a 707-page document takes noticeably longer to settle than any single chapter), then Ctrl+P → Save as PDF with Background graphics enabled.

---

## 2026-07-26 (cont'd, 4) — Phase 2 complete: 5 more sittings built, full 34-chapter Question Bank Book generated

Built the 5 sittings Pranav named (completing the Jan 2026 exam cycle + starting Sep 2025): `MTP_Jan2026_Set1.html`, `MTP_Jan2026_Set2.html`, `RTP_Jan2026.html`, `PYQ_Sep2025.html`, `RTP_Sep2025.html` — all read from raw source PDFs, tagged, split, and validated against the same schema as the original 5, at the Phase 2 relaxed accuracy bar (§0 of the Phase 1 skill: correct transcription and topic tagging, MCQ letters verified against source, but not the exhaustive re-derivation depth Phase 1's audit applied). PYQ_Sep2025 has a real ICAI Examiner's Comments document — folded in 13 verbatim real comments (labelled "Examiner's Comment") alongside synthesized ones (labelled "Author's Note"), the first sitting since PYQ_Jan2026 to exercise that distinction.

**Two accuracy-relevant things surfaced and fixed along the way:**
- Resolved a genuinely unresolved flag from Phase 1: `MTP_Jan2026_Set1.html` Q15's lease-rent MCQ (dealer/operating lease, 20% margin on cost) had been left flagged `unverified-arithmetic` because the simple pro-rata computation didn't reproduce the answer key. Building `RTP_Jan2026.html` turned up the *identical* question with one extra detail in its narrative ("3-year **operating** lease") that the MTP version's shorter restatement omitted — this revealed the actual mechanism (recover cost+margin in proportion to output consumed during the lease, out of the machine's full economic-life output, not a flat 3-year spread). Went back and fixed the MTP file's explanation with the same resolved logic.
- Found and fixed a real `unitCode` inconsistency: Branch Accounting was tagged `M3-C15-U0` in some files and `M3-C15-U1` in others; Framework similarly `M1-C2-U0` vs `M1-C2-U1`. Per CLAUDE.md's locked U0/U1 migration, both are single-unit chapters that must always use U0 — left un-caught, this would have silently split each into two separate "chapters" at book-generation time. Fixed across all affected files before generating books.

**Also caught mid-build:** `extract_questions.py`'s file-discovery briefly re-ingested a previously generated chapter book as if it were an 11th sitting (same bug pattern as before, from a stray filename not matching the `_Question_Book.html` exclusion at the time it was written) — already covered by the existing exclusion filter from the last fix, no recurrence.

**Built `first_run/scripts/generate_all_chapter_books.py`** — a batch driver that reads every unique `final_chapter` out of `questions_index.json` and calls the existing `generate_chapter_book.build_book()` for each, with a naming scheme matching the AS10 reference sample's style (`AS02_Question_Book.html`, `AS16_Question_Book.html`, ... `CashFlowStatement_Question_Book.html`, `Buyback_Question_Book.html`, etc. for the non-AS-numbered chapters).

**Result:** 275 rows extracted across all 10 sittings (30 Part I marks + 88 raw/84 deduped Part II marks per marked paper, consistently — RTPs correctly show 0/0/0 since they print no marks). **34 chapters touched — essentially the entire 36-chapter syllabus** (only 2 chapters, AS 1 and AS 27, remain thin at 2 questions each; genuinely zero-coverage chapters from the original per-question audit are now gone). All 34 generated chapter books validated structurally clean (0 unclosed tags, 0 NUL, 0 backticks, 0 duplicate IDs). Two chapters (AS 10, AS 16) now have real, non-empty Section III "Integrated" content for the first time in this pilot, from genuinely connected multi-topic questions found across the 10 sittings.

**Not done in this phase** (per Pranav's explicit "keep parked" instruction from earlier): the whole-book merge/"sewing" script, OP/PP duplicate-detection implementation, and any of the parked UX items (answer-hide toggle, mobile/print CSS, filter bar, etc.). Several likely-recurring (OP/PP) questions were spotted and noted in extraction-notes during this build (the P/Q/R Ltd. AS 18 scenario across 3 sittings; the Anshul manufacturers AS 2 scenario across 2; the Alfa/Jay Ltd. reconstruction scenario within the same MTP series; the Mansi Ltd./Akash Ltd. AS 19 sale-leaseback across 2 RTPs) but not formally merged, since duplicate detection remains a separate, not-yet-built workstream.

---

## 2026-07-26 (cont'd, 3) — Phase 1 closed out; accuracy bar relaxed for descriptives; moving to Phase 2 (scale to more sittings)

After the MCQ audit found 6 real errors, Pranav deliberately relaxed the remaining bar rather than asking for the same depth on all 69 descriptive rows: "we need not be 100% accurate... first edition... just skim through and let's close this." Ran a fast automated red-flag skim (hedge phrases, placeholder text, suspiciously short answers) across all 69 descriptive rows — zero automated flags, one manual catch during spot-reading: `MTP_May2026_Set1.html`'s Q6(a) alt-2 (amalgamation purchase consideration) had literal leftover placeholder text ("see working note...", a stray "...") sitting inside a real answer table, previously flagged `needs-visual-check`/`ocr-garbled`. Recomputed the missing share-count derivation from the given exchange ratios, confirmed it reconciles exactly to the already-stated rupee totals, and marked the row `verified`.

**Also implemented, per Pranav's instructions**: renamed the rendered Mistakes box from generic wording to **"Examiner's Comment"** (real ICAI sittings) vs. **"Author's Note"** (synthesized, with an explicit "may not apply in every case" caveat) — a display-layer change in `generate_chapter_book.py`, not a change to the underlying `data-comment-source` enum. Added a reader-facing disclaimer (top and bottom of every chapter book) acknowledging first-edition status and inviting error reports by email — **placeholder email address in the script (`ERROR_REPORT_EMAIL`), needs Pranav's real address before any real distribution**. Rewrote the book's front-matter to be student-facing (moved script/JSON/folder-path references into a small "Build info" footer, per the already-accepted Phase 1 §4 item). Documented the bar relaxation in `SKILL-question-bank-phase1-definition-of-done.md` §0 (new) so it isn't lost/re-litigated on the next sitting.

`AS02_Question_Book.html` regenerated against the new template and re-validated clean.

**Next**: Pranav asked to move to "Phase 2" — build 5 more sitting HTML files through the full pipeline (source PDF → tagged sitting HTML → extraction → chapter books) and produce the complete chapter-wise Question Bank across all resulting chapters, not just AS 2. This is a substantially larger undertaking than anything done so far (roughly re-doing the full sitting-authoring effort 5 more times, then generating N chapter books instead of 1) — scope/sitting-selection to be confirmed before starting.

---

## 2026-07-26 (cont'd, 2) — Full MCQ accuracy audit (Phase 1 §1) completed for all 5 pilot sittings

Executed the accuracy-audit gate from `SKILL-question-bank-phase1-definition-of-done.md` §1 against all 67 MCQ rows across the 5 sitting files (the other 69 descriptive rows are not yet done — see below). Independently re-derived the arithmetic for every MCQ carrying a Claude-authored explanation (50 of 67; the other 17 are genuinely bare-letter with no explanation, matching source, no risk). Consulted `books/concept-book/raw_icai_study_materials/` (Pranav's explicit authorization) to resolve conceptual doubts against three different standards' actual rule text (AS 18 related-party aggregation through a controlled subsidiary; AS 23 equity-method dividend treatment; AS 25 interim-period cost/gain/estimate-change treatment, cross-checked against a near-identical worked illustration in the AS 25 study material itself).

**Found and fixed, beyond the original 2 (AS02-005/006):**
- `MTP_May2026_Set2.html` Q7 (AS 16 borrowing-cost suspension): the case narrative's stated "3 months" standstill doesn't reconcile to the official answer letter — only a 4-month reading does. Flagged as a source-wording ambiguity (`data-issue="source-inconsistency"`) rather than silently picking one reading, per the verbatim-extraction skill's "flag, don't fix" doctrine.
- `MTP_May2026_Set2.html` Q15 (AS 18 related party): final letter was already right, but the stated method (diluting an indirect holding through a subsidiary as 60%×20%=12%) is not how AS 18 aggregates control-based holdings — verified against the AS 18 study material and corrected to the proper full (non-diluted) aggregation.
- `PYQ_Jan2026.html` Q7 (AS 23 equity method): explanation was self-contradictory (called the same dividend "pre-acquisition" then "post-acquisition" in one sentence) and never showed real numbers; the attached Mistakes note claimed the dividend "should be added, not deducted" — backward. Rewrote with the full verified calculation (₹26,00,000).
- `PYQ_Jan2026.html` Q12 (cash flow): the written formula literally computed to ₹20,30,000 while claiming to justify ₹23,00,000, hedged with "= per source figure" — a real tell that the reconciliation was never actually completed. Re-derived properly (interest reclassified to financing, added back before removing) and cross-checked against Q13/Q14's dependent figures.
- `PYQ_May2026.html` Q10 (AS 25 interim reporting): previously bare answer-letter only, no explanation at all, on a question where three plausible sign conventions are easy to get wrong (confirmed by getting it wrong myself twice before checking source) — added a fully verified explanation after cross-referencing the AS 25 study material's own near-identical worked illustration.
- `RTP_May2026.html` Q2 (AS 19 lease PV computation): could **not** be independently re-derived — the discount/implicit rate needed for the calculation is not present anywhere in the extracted source text. Flagged honestly (`data-issue="unverified-arithmetic"`) rather than assumed correct just because the letter matches the source answer key.

**Confirmed correct (no change needed) after independent re-derivation:** the remaining ~44 authored MCQ explanations, including several cross-checked against the AS 18/AS 23/Amalgamation study materials for genuinely tricky theory points (G Limited associate-via-board-representation despite only 12% holding; External Reconstruction vs. Absorption vs. Amalgamation terminology; Amalgamation Adjustment Reserve = statutory reserves only).

Also caught and fixed 2 stray literal backticks introduced by this session's own edits (violates the repo's no-backtick/UTF-8 discipline) — from markdown-style code spans in extraction-note prose, switched to `<code>` tags.

**Not yet done, and substantially larger in scope per row:** the 69 descriptive-answer rows (full worked solutions — journals, balance sheets, ledger accounts) have not been arithmetic-audited yet. Flagged to Pranav as the next chunk of Phase 1 §1; pacing/priority to be confirmed before continuing.

---

## 2026-07-26 (cont'd) — Phase 1 scope finalized and locked

After the accuracy incident below, Pranav cut off further open-ended review discussion and finalized scope: "whatever is parked for later, keep it parked... I just want that this book HTML should have accuracy at all cost... genuinely high value [improvements] are only to be considered." Wrote the locked checklist to `_claude/skills/SKILL-question-bank-phase1-definition-of-done.md` — the reusable Definition of Done for scaling past the AS 2 pilot to the remaining ~35 chapters and ~12+ sittings. Locked scope:

1. **Accuracy audit (top priority, gate before anything else)** — re-derive every AI-authored explanation's arithmetic across all 5 sittings against source figures; consult `books/concept-book/raw_icai_study_materials/` (per-unit ICAI study material MD, Pranav explicitly authorized this as the reference to resolve conceptual doubt) whenever the correct rule itself, not just the arithmetic, is uncertain.
2. **Cross-chapter cluster classification, finalized design** — one home chapter per case-scenario cluster/connected question (latest-taught touched standard), shown there under a new "(b) Integrated with Other Standards" sub-heading; every other touched chapter gets a cross-reference pointer only, never duplicated full content. This one rule resolves the earlier-logged case-scenario-duplication issue, the cross-chapter-cluster-homing issue, and the Single-AS/Integrated sub-bucket issue together. Design locked; `extract_questions.py`/`generate_chapter_book.py` implementation not yet built.
3. **Theory/practical** — folded into the accuracy-audit pass (already tagged at Layer 1, just needs a sanity check + surfacing), not a separate workstream.
4. **Two external-review suggestions accepted as genuinely high value**: strip build/engineering plumbing from student-facing text; fix the Mistakes-box voice so MTP/RTP synthesized comments don't falsely claim "many examinees" behavior on papers that never had real candidates (reframed as a correctness fix, not a tone preference). Bonus near-free item: render the topic tag's existing `data-subtopictitle`.
5. **Everything else explicitly parked**: answer-hide toggle, concept recap, revision scaffolding, mobile/print CSS, filter bar, OP/PP badge, Q11/Q12 cross-pointer.

Execution order locked: full accuracy audit first, then the combined cluster/sub-bucket/theory-practical/voice-fix regeneration, then re-validate AS 2 as the Phase 1 proof before scaling.

---

## 2026-07-26 — Real accuracy incident: two backward AS 2 explanations found via external AI review of AS02_Question_Book.html

Pranav ran the AS02 book past another AI for review and relayed its findings rather than accepting them at face value: "Dont accept everyting blindly... evaluate all against our Main goal... main is to make life of student easier and to ensure 100% accuracy at all cost." Independently re-verified every claim from source before acting.

**Confirmed, fixed:** `PYQ_Jan2026.html` Q4 and `PYQ_May2026.html` Q6 (both AS 2 MCQs) had explanations where the arithmetic actually computed to the *distractor* option, not the letter the qblock claimed — and the attached synthesized "Common Student Mistakes" note branded the *correct* method as the student error, exactly backward. Traced root cause by reading the actual source PDFs: both ICAI "Suggested Answers" documents give only a bare letter (`4. (B)`, `6. (B)`) with zero working — meaning the explanations were never transcribed, they were authored by Claude while building these files directly (2026-07-24 session), and the `extraction-note` on both falsely claimed "Verbatim... Confidence: high" for reasoning that was never in the source. Fixed both explanations with correct AS 2 reasoning (fixed-overhead absorption at the *actual* production rate when actual exceeds normal capacity; raw-material write-down to replacement cost when the finished goods it feeds are expected to sell below cost), corrected the mistakes-notes, and rewrote the extraction-notes to honestly distinguish source-verbatim (letter/options) from Claude-authored (explanation).

**Also fixed for consistency, not correctness:** the 4 sibling AS 2 MCQs in `MTP_May2026_Set2.html` (Q10–13) had the same "verbatim... high confidence" mislabeling on Claude-authored explanations, even though re-deriving their arithmetic independently confirmed all 4 were already correct. Relabeled honestly rather than left as-is, since the metadata claim was still false regardless of whether the content happened to be right.

**Bug also caught mid-fix:** `extract_questions.py`'s file-discovery (`os.listdir(OUTPUT_DIR) if f.endswith(".html")`) was sweeping up generated chapter-book outputs (`AS02_Question_Book.html`) as if they were a 6th sitting, double-counting those 7 rows (136 → 143). Fixed by excluding `*_Question_Book.html` from the glob — will matter more once more chapter books accumulate in the same folder.

**Flagged as a systemic risk, not fully resolved:** found on 2 of ~13 AS 2 MCQs checked so far — since ICAI MCQ answer keys are routinely bare-letter-only, most authored explanations across all 5 sittings carry the same unverified-arithmetic risk. Recommended a full audit pass (re-derive every MCQ explanation's arithmetic against its own source figures) before scaling past the pilot; not yet scheduled. New skill section added: `SKILL-question-bank-verbatim-extraction.md` §6, plus a new `data-issue="answer-key-letter-only"` vocabulary value in the html-schema skill.

**Evaluated, not blindly accepted, the same reviewer's 12 UX/structure suggestions** (case-scenario dedup — already tracked as our own issue 1; subtopic-title surfacing — cheap, data already exists via `data-subtopictitle`; engineering-plumbing-in-student-view removal; mobile CSS; print CSS tied to CLAUDE.md §7's existing page-break architecture; MTP/RTP "examinees" voice being factually wrong since those papers never had real candidates; etc.) — see chat for the full per-item verdict, not duplicated here since most are pending design decisions, not facts to persist.

---

## 2026-07-25 — Pipeline proven end-to-end: extraction script + first real chapter book (AS 2)

Pranav asked to prove the whole pipeline actually works: "For all the extracted HTML File, I want you to complete the entire pending actions... I want to see from you being able to give me a 'Proper well formatted HTML file for the AS02 Chapter'." Built and ran both remaining scripts against the 5 real pilot sitting files (no synthetic test data).

**`first_run/scripts/extract_questions.py`** (Layer 1 → Layer 2, BeautifulSoup, mechanical only — no AI re-judgment): walks every sitting HTML in `first_run/output/`, emits one row per qblock into `first_run/output/questions_index.json`. Ran clean: **136 rows from 5 files** (MTP Set1: 28, MTP Set2: 27, PYQ Jan2026: 27, PYQ May2026: 28, RTP: 26). Built-in marks sanity check (Part I total 30, Part II raw vs alt-group-deduped total 84, across the 4 files that carry marks; RTP correctly shows 0/0/0 since it prints none).

**Caught before extraction, via a pre-flight `grep -o 'data-part="[^"]*"' | sort -u` across all 5 files**: `MTP_May2026_Set1.html` (the oldest file, built before the `"I"`/`"II"` data-part convention was settled) still had free-text values (`"Part I - Case Scenario I"`, `"Part I - MCQs"`, `"Part II"`). Fixed with a targeted regex pass (18 lines), re-validated 0 errors. This is exactly the cross-session schema drift the extraction script's Part-I/Part-II bucketing logic depends on being clean — worth re-running that same grep sanity check before extracting after any future file is added or edited.

**`first_run/scripts/generate_chapter_book.py`** (Layer 2 → Layer 3, plain Python/f-strings, no AI): takes a unitcode + labels, queries `questions_index.json`, partitions into Section I (MCQ/case-mcq), II (descriptive, single-topic = the norm post-splitting), III (integrated — `topic_count > 1` and the target unit is a secondary tag), renders inline-CSS HTML matching the `AS10_Question_Book.html` quality bar (qmeta line, case-facts embedded inline, answer block, Common-Student-Mistakes box **with an explicit real-ICAI-vs-synthesized provenance line per entry** — a discipline the AS10 hand-built sample predates and doesn't have, added here since our schema already tracks it losslessly in `examiner_comment.comment_source`).

Ran it for AS 2 (Valuation of Inventories, `M2-C5-U1`) → `first_run/output/AS02_Question_Book.html`: **6 MCQs + 1 descriptive + 0 integrated = 7 questions**, matching the record set already hand-confirmed by ad-hoc query. Validated: 0 unclosed tags (the 2 "errors" HTMLParser reported were a validator artifact from self-closing `<br/>` synthetic end-tag events, not real defects — confirmed by grep, no `</br>` exists anywhere), 0 NUL bytes, 0 backticks, correct `&#8377;` rupee entities, 0 placeholder phrases, 0 duplicate IDs. Read the full rendered output — case scenarios correctly embedded per-MCQ (the exact bug Pranav flagged earlier in this project as the "major issue" with the original external-AI output), verbatim accounting tables intact, synthesized-mistakes provenance correctly labelled throughout (no real ICAI comment exists for any of these 7 — all synthesized per `examiner-comments-writing-skill.md`).

**Honest finding surfaced by the run itself, documented in the book's own scope note**: Section III (Integrated) is genuinely empty for AS 2 across this 5-file pilot — 0 records exist where AS2 is a secondary tag on a connected multi-topic question. This is the expected shape of the independent-vs-connected splitting design (most multi-topic-looking questions get split into single-topic records at extraction time), not a pipeline gap — but it means the AS10 hand-built sample's 3-section structure won't always have content in all 3 sections for every chapter, which future chapter-book runs should expect and state plainly rather than treat as a bug to chase.

Also deleted `first_run/output/TODO.md` — confirmed stale (pre-build planning notes for RTP referencing an abandoned `M1-C4-U2`/`M3-C11-U2` unit-code confusion that was resolved differently in the final schema).

**Next**: this is the first chapter book against real data — scale the same `generate_chapter_book.py` call to the remaining 35 chapters once enough sittings are tagged (still only 5 of ~17+ sittings exist at all); OP/PP duplicate detection and a whole-book merge script are still designed-not-built.

---

## 2026-07-24 (cont'd, 3) — Remaining 3 pilot sittings built directly (MTP Set 2, PYQ May2026, PYQ Jan2026)

Pranav decided not to hand the revised prompts to the external AI for the remaining 3 sittings ("I dont know they will again create a mess") and asked Claude to build them directly instead, against the schema/skills already established from the MTP Set 1 and RTP rebuilds — "minimum token possible... best possible output." All 3 built end-to-end: source PDFs extracted via pypdf, read in full, classified question-by-question (independent-split vs connected vs OR-alternative), tagged against `topic-index.json` with `data-final-chapter`, and validated with the same Python script used for the first two files.

**MTP May 2026 Set 2** (13+14-page Q/Ans PDFs) — 27 qblocks + 3 case scenarios. One judgment call worth recording: Q6(a) bundles two Framework sub-questions ((i) qualitative characteristics, (ii) capital maintenance calc) under one 4-mark heading with no individual mark split shown in the source — kept as one record rather than inventing a split, since both map to the same syllabus unit anyway.

**PYQ May 2026** (44-page Ans PDF, both Q&A embedded per the PYQ sourcing decision) — 28 qblocks + 3 case scenarios. One genuine ambiguity flagged rather than guessed: Q5(a)'s mark value is not printed in the extracted source text (only Q5(b)'s "10 Marks" is) — inferred as 4 (14 total pattern minus 10) and marked `data-issue="marks-mismatch"` rather than stated as confirmed fact.

**PYQ Jan 2026** (45-page Ans PDF) — the pilot's one sitting with a real ICAI Examiner's Comments document (`Paper1-ExaminerComments-Jan2026.md`). Matched all 6 real comments to their corresponding Part II sub-questions (Q1a/b/c, Q2, Q3a/b, Q4, Q5, Q6a-alt1, Q6b, Q6c — 11 of 12 Part II records), leaving only Q6(a)'s AS 19 lease alternative synthesized since the real comment for Q6(a) discusses only the AS 24 disclosure alternative content, not the lease computation — confirmed by actually reading what the comment describes rather than assuming one comment covers both OR-branches.

**Caught and fixed a self-introduced schema bug during this build**: all 11 real-comment blocks in the Jan 2026 file were first written with the citation string stuffed into `data-comment-source` (e.g. `data-comment-source="ICAI Examiner's Comment — Jan 2026, paraphrased"`) and the `synthesized` CSS class left on by copy-paste, instead of the clean enum `data-comment-source="icai"` plus the citation in `data-source`, per the schema. Caught by grepping the output for the enum values immediately after the validation pass reported "0 errors" (structural validation doesn't check semantic correctness of attribute values) — a reminder that automated validation catches malformed HTML, not wrong values in well-formed attributes. Fixed with a targeted regex pass; re-validated: 11 `icai` + 16 `synthesized` = 27, matching the 27 qblocks exactly.

All three files validated identically to the first two: 0 unclosed tags, 0 backticks, 0 placeholder phrases, all IDs unique, all case-scenario references resolve, marks arithmetic consistent (Part I 30, Part II 84 after alt-group dedup across all three files).

**All 5 pilot sittings are now built and validated against the current schema**: MTP Set 1, MTP Set 2, RTP May2026, PYQ May2026, PYQ Jan2026. Next: the HTML→JSON extraction script, duplicate-detection (OP/PP) implementation, and difficulty-computation step, per the six `SKILL-question-bank-*.md` skills — none of these are built yet, only designed.

---

## 2026-07-24 (cont'd, 2) — RTP May 2026 rebuilt against the revised schema

Extended the same-day schema revision (previous entry below) to the second pilot file.
`first_run/output/RTP_May2026.html` had been generated under the *old* schema and, on
inspection, was far worse than the MTP file had been: nearly every Part II answer (16 of
20 questions) was placeholder/meta-descriptive text ("see source", "as printed in source",
"full data in source") with **zero real content**, zero topic tagging throughout, and the
document metadata claimed `"Total Marks: NA"` while individual questions carried invented
marks values (4, 6, 8, 14, etc.) that do not exist anywhere in the source PDF — the RTP
genuinely prints no marks per question at all, so those numbers were fabricated by the
earlier AI, not merely omitted.

Extracted the full 48-page source PDF and rebuilt the file end-to-end: real Case Scenario
node (the AS 16 borrowing-cost scenario behind Q1's four MCQ sub-parts), verbatim content
for every one of the 20 original questions, correct MCQ answers cross-checked against the
source answer key (**and one genuine error caught and fixed**: Q4's answer was recorded as
"(a)" in the old file; the source's own suggested-answer section plainly states "4. (b)"),
topic tags against `topic-index.json` for all 26 resulting records, and `data-marks`
omitted throughout rather than invented (documented in the Part II section header so this
isn't mistaken for an oversight). Applied the independent/connected sub-part rule from the
new question-splitting skill: Q9 (three unrelated post-balance-sheet events bundled under
one number) and Q17 (two unrelated AS 29 fact patterns) split into independent records;
Q15 (three progressively-building sub-parts, the third explicitly referencing "the above")
and Q20 (Euro-denominated branch accounts feeding a converted trial balance) correctly kept
as single connected records — a real worked example of both branches of the rule.

Also caught, independently of the splitting/tagging work: Q10 is printed in the source
under the heading "AS 7 Construction Contracts" but its actual content (Y Limited
constructing its own factory) is a self-constructed-PPE-plus-borrowing-cost problem, AS 10
+ AS 16, not AS 7 at all — exactly the header-mismatch failure mode already anticipated and
warned against in the RTP prompt's specific notes, now confirmed as a real, not just
theoretical, risk. Tagged from actual content, flagged the header mismatch in the
extraction-note rather than tagging blindly from the printed heading. One further source
typo was caught and corrected with a flagged note (an evident stray-zero OCR/typo artifact
in one journal-entry credit figure in Q19, internally inconsistent with the same entry's
debit side and with the same figure used correctly elsewhere in the same scheme).

Validated identically to the MTP file: 0 unclosed HTML tags, 0 backticks, 0 leftover
placeholder phrases, all 27 IDs (26 qblocks + 1 case scenario) unique, case-scenario
reference resolves.

**Both pilot sittings reviewed under the revised schema are now MTP May 2026 Set 1 and
RTP May 2026.** Remaining: MTP Set 2, PYQ May 2026, PYQ Jan 2026 still need first-time
generation via the revised prompts.

---

## 2026-07-24 (cont'd) — Question Bank schema revision: case scenarios, marks tagging, question splitting, Final Chapter, six new skill files

Continuing the same-day MTP Set 1 review (previous entry below), Pranav flagged two more
structural gaps by inspecting the rectified file directly: (1) Case Scenario MCQs'
shared narratives were captured nowhere at all — the questions referenced facts
("the Company", specific rupee figures, dates) that appeared in no visible node, an
extraction blunder neither the original AI nor Claude's first-pass fix had caught; (2)
marks, paper facets (MTP/RTP/PYQ, month, year, set), and difficulty needed to be
independently machine-queryable, not embedded in display strings like `"MTP May 2026 Set 1"`
or `"14 (7+7)"`.

Fixed the case-scenario gap immediately (added `.case-scenario` nodes + `data-case-ref`
for all three scenarios in the pilot file). For the rest, Pranav also forwarded an
external AI's independent schema-review document and asked for honest evaluation, not
blanket acceptance — most of it was sound (paper-level facets, structured MCQ options,
deterministic composite IDs, structured review-flag attributes) and was adopted; two
specific recommendations were rejected with reasoning (a parallel topic-ID namespace that
would recreate the U0/U1 ID-scheme fight already fixed once; diluting the synthesized
examiner-comment voice, which reverses `examiner-comments-writing-skill.md`'s explicit
design choice — voice fidelity + provenance metadata was always the intended
misattribution safeguard, not a diluted voice).

**New locked decision (Pranav):** multi-part descriptive questions get classified
independent (unrelated sub-parts, just bundled under one question number — the common
case, confirmed by checking every multi-part question in the pilot file) vs. connected
(one continuous fact pattern). Independent sub-parts split into separate Question Bank
records, each single-topic; connected questions stay one record. Paired with a new
`data-final-chapter` concept — every question/fragment's designated home chapter in the
assembled book, computed from `teaching_sequence` (pulled fresh from
`books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`).
Also confirmed: Easy/Medium/Hard difficulty (by count of distinct topics tagged: ≤2/3–5/
>5) will be computed in the Python `questions.json` step, never hand-authored in HTML —
Pranav's own call, for the same one-place-to-change-the-logic reason already governing
the rest of the pipeline's two-layer (HTML source / JSON computed) architecture.

Rebuilt `MTP_May2026_Set1.html` end-to-end against the new schema: split the four
multi-part Part II questions into 13 independent records (one, Q6's part (a), also needed
`data-alt-group` handling for its OR-alternative), added paper-level facets on `<body>`,
converted all 15 MCQs' options to structured `<ol><li data-opt>` lists, fixed 54 leftover
stray-backtick rupee signs the earlier review had missed, fixed an arrow-in-cell
(`1,50,000 → 8,50,000`) table anti-pattern into separate before/after columns, and added
`data-final-chapter`/`data-confidence`/`data-review-status`/`data-comment-source` across
all 28 resulting qblocks. Validated with a Python script: 0 unclosed HTML tags, 0
backticks, 0 leftover placeholder phrases, all 31 IDs (28 qblocks + 3 case scenarios)
unique, all case-scenario references resolve, marks arithmetic correct (Part I = 30, Part
II = 84 across 6 distinct questions after alt-group deduplication, i.e. 6×14 — matching
the paper's "compulsory Q1 + best 4 of remaining 5" structure).

Wrote six new skill files at `_claude/skills/SKILL-question-bank-*.md`
(`pipeline-overview`, `html-schema`, `topic-tagging`, `question-splitting`,
`examiner-comments`, `duplicate-detection`) plus `verbatim-extraction` (seven total),
per Pranav's explicit request that all of today's Question Bank learnings be captured as
durable, self-contained documentation usable "by anyone using a clone of git... with
whatever AI they want" — `pipeline-overview` is the front-matter index pointing to the
rest. Updated `first_run/schema/HTML-SCHEMA.md` (the operative generation spec) and
`first_run/prompts/GENERATE-SITTING-HTML-PROMPTS.md` (all 3 prompts) to match, including
switching the prompts' source-of-truth instruction from the `.md` conversions to the
original PDFs directly (per the new `verbatim-extraction` skill's #1 rule) and adding an
explicit "count questions against the paper's own stated structure" instruction, aimed
directly at the missing-Q6 failure mode from earlier today.

**Not yet done:** `RTP_May2026.html` (generated under the old schema) needs re-review/
rebuild against the new one. `MTP_May2026_Set2.html`, `PYQ_May2026.html`,
`PYQ_Jan2026.html` still need first-time generation with the revised prompts. The
HTML→JSON extraction script, the duplicate-detection (OP/PP) implementation, and the
difficulty-computation step are all still unbuilt — designed in the new skills, not yet
coded.

---

## 2026-07-24 — MTP May 2026 Set 1: reviewed and rectified the first pilot AI output against the source PDF

Pranav ran Prompt 1 through his external AI and got `first_run/output/MTP_May2026_Set1.html`. He asked for a review against the **PDF** (not the MD conversion), and rectification of anything wrong.

**Found it badly non-compliant with `HTML-SCHEMA.md` and the prompt's own rules**, extracted both source PDFs (`CAInter-AdvAcc-MTP-May2026-Set1-Q.pdf`, `-Ans.pdf`) via `pypdf` to verify line by line:
- **Zero chapter/topic tagging** on all 20 questions (`<span class="na">Not tagged yet</span>` everywhere) despite the prompt requiring it.
- **Part II (descriptive, 70 of 100 marks) was not verbatim** — placeholder/meta-descriptive text like "(full text as in source)" and "as in source answers (verbatim, OCR-normalized)" stood in for actual content.
- **Question 6 of the source paper (14 marks — AS 24/Amalgamation alternative + AS 1 + AS 17) was missing entirely** — the AI only produced Q1–Q5 of Part II's 6 printed questions, silently dropping one full question worth 14 marks.
- **Two mark totals were wrong**: Q2 shown as 12 (source: 7+7=14), Q5 shown as 16 (source: 10+4=14) — the overall 30+70=100 happened to still check out only by coincidental cancellation.
- Examiner comments were thin one-liners, not following `examiner-comments-writing-skill.md`'s required quantifier/failure-mode/citation/consequence structure.
- Positives that did hold up: all 15 Part I MCQ answers verified correct against the PDF; `.author-comment` placeholders correctly present/empty throughout.

**Rectified directly** rather than re-prompting the external AI: rebuilt all 21 question blocks (added the missing Q6 as `id="Q21"`) with genuine verbatim question/answer text transcribed from the PDF extraction, tagged every question against `topic-index.json`'s taxonomy (flagging the one AS 1 tag as pointing to a chapter/unit not yet individually indexed, rather than fabricating detail), fixed the two mark totals, rewrote every examiner comment in the skill's actual voice, and fixed the "Printed paper instructions" placeholder with the real verbatim instructions. Also flagged (not silently corrected) one internal inconsistency found in the source answer PDF itself — Falgun Ltd.'s Note 1 Share Capital block prints figures for a different company size than the trial balance — left in as printed with an extraction-note pointing it out for Pranav's judgment call. Verified the final file has zero unclosed HTML tags and correct marks arithmetic (Part I 30 + Part II compulsory Q1 14 + best 4-of-5 optional = 70 = 100 total; file now shows all 6 printed Part II questions summing to 84, matching how MTP answer keys conventionally print solutions for every optional question).

**Not yet done:** `RTP_May2026.html` (already generated, not yet reviewed) still pending; the stray empty `first_run/output/TODO.md` is still unexplained/uninvestigated.

---

## 2026-07-23 — Strategy book: em-dash pass across all student-visible content

Pranav flagged that heavy em-dash use across the book reads as an AI-writing tell, and asked for a pass to humanize it. Scoped to actual book content only (Bucket 0–6, AI Section, Emergency, Personal Pages, front matter's real prose, Author's Journey) — explicitly not MASTER.md's internal working-draft/status notes, which aren't student-visible.

**Real scope, checked before starting:** 529 em-dashes in MASTER.md, but only 417 were prose (the other 112 are `Strategy N — Title` / `BUCKET N — Name` structural heading separators the parser's regex depends on to detect section boundaries — confirmed via the renderer that these never even survive into the rendered HTML as literal dash characters, since the tokenizer splits them into separate number/title fields). Plus 25 in front-matter.html and 41 in authors-journey.html (both hand-authored, edited directly, never regenerated).

**Went through every instance by hand, not a blind find-replace** — a mechanical substitution would break grammar constantly (some dashes need a comma, some a period splitting into two sentences, some a colon, some parentheses, depending on what the sentence is actually doing). Worked bucket by bucket: Routing → Bucket 0 → ... → Personal Pages, then both hand-authored files. A few of the period-splits (e.g. "Don't overthink the sequence. This default beats a blank page every time.") land closer to the book's intended "older brother, blunt" voice than the original single long sentence did anyway.

Also fixed the `<title>` tag em-dash (shared across all generator output, one-line fix in `build_page()`) and the Table of Contents' own `Bucket N — Label` format in `generate_toc.py` (that one was my own code, no parser dependency, fixed for full consistency).

**Left alone, deliberately:**
- Heading separators (`Strategy N — Title`, `BUCKET N — Name`, `TRACK A — ...`) — structural convention, not a prose tell, and some are parser-regex-load-bearing.
- Two table-placeholder dashes in the backward-planning calendars (`Exams start  —  —  01-05-2027`) — these mean "no value," same as a spreadsheet blank cell, not a written dash.
- One literal quoted exam-answer example (`"Computation of Total Income — Mr. X"`) — showing exact text a student would write on their answer sheet; a real accounting convention, not prose style.

**Verified, not assumed:** re-ran the full merge + ToC-resolve pipeline afterward — stable at 92 pages, same page numbers as before the edit (confirms the punctuation changes didn't meaningfully shift line-wrapping), and grepped the final merged book's body content for `—` to confirm only the three intentional exemption categories above remain.

Also caught and fixed a newly-stale `component-index` health-check failure (MASTER.md's content changed enough to trip the checksum) by re-running `tools/generate_component_index.py`.

---

## 2026-07-23 — first_run/ pilot workspace built: schema, style JSON, 3 external-AI prompts

Pranav reviewed `Claude_V2.md`'s paged.js/single-source-of-truth learnings (from the concurrent Strategy Book session) and asked for the same discipline in the Question Bank pipeline: font-size/spacing/margins controlled from exactly one JSON, never hardcoded per file. Distilled those learnings into new **CLAUDE.md section 7** (7 numbered lessons: JSON-driven geometry, `@page` not resolving `var()`, `break-inside:avoid` for page-break safety, local font vendoring, `position:running()` for repeating headers, merge-script gotchas, screenshot-based verification).

Also reconsidered and simplified the pipeline: **Parsed MD is not a required gate** (tagging works fine from Raw MD directly; cleanup can happen once, per-question, at first-read time instead of upfront for whole sittings that might not even get used) and **sitting-level records should embed full question+answer content directly** rather than staying a lean pointer-only index (this reverses part of yesterday's `TAGGING-SCHEMA.md` decision — for good reason: the one careful AI read of messy OCR content should never be thrown away and redone later). Also: MTP_Jan2025.json bundling both Sets into one file is inconsistent with the one-Set-per-100-mark-file convention used everywhere since — needs splitting (not done this session, flagged).

Further refined (after Pranav pushed back and asked for independent evaluation rather than agreement): moved from "embed HTML directly as JSON string values" to **"AI writes a standalone HTML file per sitting; a script extracts JSON from it mechanically."** Concrete reason this is better, not just different: embedding dense HTML (nested tables, quoted attributes, rupee signs) as JSON string values asks a model to get two escaping disciplines right at once, and smaller models are exactly the kind of thing that gets this wrong — a single bad escape corrupts the *entire* file. Plain HTML has no such compounding failure mode.

**Built `first_run/` (new temporary top-level folder, documented in CLAUDE.md §3 and README.md, zero new health_check failures introduced):**
- `source/` — copies of the 5-sitting pilot's 7 raw MD files + `Paper1-ExaminerComments-Jan2026.md`.
- `schema/book-style.json` + `generate_style_css.py` + generated `book-style.css` — the single source of truth for every font-size/spacing/colour/margin value; every sitting HTML links to the one generated stylesheet rather than hardcoding anything.
- `schema/HTML-SCHEMA.md` — the exact per-question HTML structure (`.qblock`, `.qmeta`, `.question`, `.answer-block`, `.topics`/`.topic-tag`, `.examiner-comment` with a mandatory `data-source` provenance attribute, `.author-comment` — always present, always empty, always hidden, a placeholder for Pranav's own future notes — and `.extraction-note`).
- `prompts/GENERATE-SITTING-HTML-PROMPTS.md` — 3 full, self-contained prompts (MTP/RTP/PYQ) for an external AI to read the raw sources directly and write real HTML files into `first_run/output/` (never just display content) — PYQ's prompt explicitly handles the split (Jan 2026 has a real ICAI Examiner's Comments doc to match against; May 2026 doesn't and gets synthesized notes per `examiner-comments-writing-skill.md`, embedded in the prompt).

**Pilot scope confirmed by Pranav:** MTP May 2026 Set 1 + Set 2, RTP May 2026, PYQ May 2026, and PYQ Jan 2026 (deliberately included out-of-batch specifically to test the real-comment-matching path) — 5 sittings, run through to a full chapter-book proof before scaling to the remaining ~30+.

**Waiting on:** Pranav running the 3 prompts (5 times total) via his other AI model(s). Next session resumes with reviewing the 5 HTML outputs, then building the HTML→JSON extraction script against real data.

---

## 2026-07-23 — Question Bank: U0 migration completed (topic-index.json + 4 tagged sittings)

Follow-up to the canonical topic/page-index JSON built earlier today (see entry below). Pranav confirmed: migrate everything to `U0` for the 7 single-unit chapters (Intro to AS, Framework, Applicability, Buyback, Amalgamation, Internal Reconstruction, Branch Accounting), reversing yesterday's `U1` choice.

Migrated in one pass: `topic-index.json` (7 `unitCode` fields + their `"unit": 1`→`0` companions) and all 4 already-tagged sitting JSONs (`MTP_Jan2025.json`, `MTP_May2024_Set1.json`, `PYQ_Jan2026.json`, `RTP_May2026.json` — 28 `unitCode` occurrences total). Re-validated every file as parseable JSON afterward; grepped for stray `U1` references and confirmed zero remain for these 7 chapters anywhere in tagging data. Deliberately left `topic-index.json`'s `sourceFile` fields alone (e.g. `"M1_C1_U1_ Introduction....pdf"`) — those are real filenames on disk under `raw_icai_study_materials/`, not our tagging convention.

Updated `TAGGING-SCHEMA.md` and `CLAUDE.md` §6 to mark the migration done (was previously flagged "not yet done, waiting on Pranav").

**Everything is now consistent**: `U0` + hyphens, matching the master syllabus JSON, the new canonical topic/page index, `topic-index.json`, and all 4 tagged sittings. Clear to proceed with Phase 1 (parsing + tagging the remaining ~34 sittings) without a looming ID-scheme cleanup hanging over it.

---

## 2026-07-23 — Strategy book: Table of Contents built, real page numbers verified working

Pranav wanted a Python script to generate the Table of Contents as its own file, added to the merge order like any other section — good instinct, and exactly how it's built. The hard part was always going to be page numbers: nobody can know what page Bucket 3 starts on until paged.js has actually laid out the whole merged book.

**First approach (didn't work, confirmed properly rather than given up on early):** CSS `target-counter()` — the standards-based way to ask "what page did this element land on." Looked promising (paged.js's CSS parser accepted the syntax, `getComputedStyle` showed it rewritten into an internal counter reference) but never actually resolved to a rendered number, across several syntax variants tried. Confirmed via paged.js's own GitHub issues this is a known, still-open bug (#145, "TOC page number always zero") — not a mistake in usage. One variant (`url(#fragment)` as a literal target) crashed pagination entirely and is now flagged in the code to never retry.

**What actually works:** paged.js stamps a real `data-page-number` attribute on every physical page container it creates. Built `tools/resolve_toc_pages.py` — drives its own headless Chrome instance over the DevTools Protocol (`websocket-client`, pip-installed), polls for genuine real-time pagination stability (reusing the section-15 lesson from yesterday — a fixed timer is not a reliable completion signal for a document this size), looks up which page each section's anchor lands on, and bakes the real number into `toc.html` as plain static text. Two-pass build: merge once (blank numbers) → resolve → merge again (correct numbers). `--remerge` flag chains the last two steps automatically.

**Verified, not assumed:** ran the full 3-command pipeline, then independently re-checked all 12 baked-in numbers against a fresh real-time pagination pass of the final book — every one matched exactly (routing→11 ... authors-journey→89, out of 92 total pages).

**Supporting changes:** `strategy_book_parser.py`'s `_h1()` now writes `id="{slug}"` on every section heading (bucket banners and generic H1s) — these are what the ToC and resolver both anchor to; `tools/generate_toc.py` imports `BOOK_ORDER` directly from the merge script rather than keeping a second list (order changes propagate automatically) and reuses `SECTION_META`'s already-correct labels rather than re-deriving display names. Front-matter.html and authors-journey.html both needed small hand-patches (anchor id, and — for front-matter specifically, since it supplies the merge's shared stylesheet — the new `.toc-entry`/`.toc-page` CSS) added surgically, never through the generator, per the standing hazard logged yesterday.

Full investigation and the working pipeline documented in Claude_V2.md section 16. Ran `health_check.py`/`file_index.py` — same 16 pre-existing failures, nothing new.

---

## 2026-07-23 — Canonical topic/page-number JSON built, U0/U1 decision reversed

Pranav shared `books/concept-book/syllabus-engine/data/CA INTER ADV ACCOUNTS - For Adarsh.csv` (400 topics, all 36 chapters incl. AS 1 and AS 27, real ICAI page numbers) and asked whether to convert it to JSON. Validated first: 0 duplicate topic IDs, 0 blank fields, spot-checked AS 10 against existing hand-built data — matched exactly. Test-converted before committing to anything.

Built `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` — the new canonical topic-number + page-number source. Cross-joined 1:1 against the locked master syllabus JSON (file 0) by `unique_chapter_id` (zero unmatched either direction), pulling in `teaching_sequence`/`chapter_name_short`/`marks_distinct_attempt_count`; added `standard`/`standard_title` (parsed from unit name) and `is_single_unit_chapter`.

**Decision reversed:** the CSV (and file 0) both use `U0` for the 7 single-unit chapters; Pranav confirmed switching from the `U1` convention chosen in yesterday's `TAGGING-SCHEMA.md` to `U0` ("no further units" reads more sensibly), and to keep hyphens (not the CSV's underscores) for IDs. `topic-index.json` and the 4 already-tagged sitting JSONs still use `U1` — **not yet migrated**, flagged as pending.

Also reviewed 3 more AS10 sample files Pranav added (`AS10_Question_Bank.json`, `AS10_Question_Reference.html`, `MTP_Jan2026.json`) — confirmed the two-layer book architecture (lean per-sitting tagging vs. derived per-chapter book JSON with embedded content), and that `MTP_Jan2026.json` is new untagged content needing to be folded into Layer 1.

Updated `TAGGING-SCHEMA.md` and `CLAUDE.md` §6 with all of this.

---

## 2026-07-23 — authors-journey.html: caught a second content-loss mistake, rewrote in third person

Pranav asked to check whether `authors-journey.html` was complete. Reading it showed the plain `[STRUCTURE ONLY]` placeholder — but per `project_log.md`'s own entry from 2026-07-22 ("Author's Journey + front-matter Category B sections complete"), the parallel session had already fully written this section (5-phase first-person narrative, real facts from the author profile, 4 quotes, photo placeholders). **My own blanket regeneration loop the previous session (run twice, for the book-order change and the font fix) silently overwrote it back to placeholder** — I'd protected `front-matter.html` specifically because I already knew it carried hand-authored content, but didn't realize this file did too, and didn't check before regenerating.

**Checked for recovery, found none:** MASTER.md never had the content (same gap as front-matter), the merged `FULL-BOOK.html` had already been regenerated by the time I looked, and a stray backup copy noticed in an earlier file listing no longer existed. Unlike the front-matter incident, there was no diff sitting in conversation context to restore from — the actual prose was gone for good.

**Resolution:** Pranav asked for the section to be rewritten in third person ("About the Author" style) rather than the original first-person plan. Read `books/about-author/Pranav_Pratik_Tulshyan_Master_Profile_Journey.md` (the real source document — far more detailed than the summary in the old log entry) and wrote a full third-person narrative covering the same ground: the demo-class Socrates story setup, Foundation 2014–15 (the teacher's rank-vs-pass philosophy, the PCO booth call, the 19 Jan 2015 AIR 1 result), Intermediate 2015–16 (handwritten summary system, the 25 April 2015 earthquake and the AIR-1-to-85%-target reframe, the Nepal Blockade, the Auditing Pronouncements story, the 1 Feb 2016 AIR 1 result), a "Why He Teaches" bridge (EY, CA Final AIR 5, IOCL, the coding/Efficient Corporates detour, the decision to teach CA Inter Accounts specifically), and the Socrates-story loop close. ~1,673 words. Added the missing `.journey-close`/`.photo-ph`/`.ph-caption`/`.story-vignette` CSS locally in this file (kept self-contained, not dependent on merge order). Verified it actually paginates correctly (2 pages, no errors) before re-merging — did **not** re-run the generator on any file, only the merge script, to avoid repeating the exact same mistake a third time.

**Standing risk, now stated more broadly (see also Claude_V2.md §14.2):** at least two build/ files (front-matter, authors-journey) have carried hand-authored content invisible to MASTER.md and at risk from any blanket regeneration. There may be others not yet discovered. Until this is resolved by porting real content back into MASTER.md as the source of truth, **never run `strategy_book_parser.py --section all` without first diffing every affected file against a fresh regen** — not just the ones already known to be hand-edited.

---

## 2026-07-22 — Strategy book: FULL-BOOK.html finalized (87 pages, verified stable) + a major false-alarm debugging lesson

Pranav gave the exact book order to merge (front-matter, routing, bucket-0..6, ai-section, emergency, personal-pages, authors-journey — "cover" deliberately dropped) and asked for a final, properly print-ready `FULL-BOOK.html` with "no margin or page issues."

**Checked front-matter.html was in sync first** (it carries hand-authored content from a concurrent session, per the standing hazard logged this morning) — geometry, footer fix, and structure were all already correct; no changes needed there.

**Updated `BOOK_ORDER` in `tools/strategy_book_merge.py`** to match exactly, regenerated the other 13 sections individually (still deliberately not touching front-matter.html directly via the generator), hand-patched only front-matter.html's font-loading `<link>` tag, and re-merged.

**Then hit a serious-looking problem:** repeated headless-Chrome checks of the identical merged file gave wildly different page counts (4, 7, 10, 22, 262) — looked like real pagination corruption. Spent real effort chasing two plausible causes (an empty `.blank-page` div confusing paged.js's fragmentation; Google Fonts loading over the network racing against paged.js's layout pass) — vendored all fonts locally either way (`design/templates/vendor/fonts/*.woff2` + `gfonts-local.css`, replacing the `@import` from fonts.googleapis.com) since it's a legitimate improvement regardless, but **instability persisted through both fixes**.

**Root cause, confirmed properly rather than guessed:** `--dump-dom`/`--virtual-time-budget` simply capture Chrome's headless state at an arbitrary, non-deterministic point — for a small file this coincides closely enough with paged.js actually finishing, but for this ~200KB/13-section merged book, paged.js needs several real seconds of wall-clock CPU time to converge, and every prior capture in this session was catching it mid-render. Installed `websocket-client` via pip (flagged, same low-risk pattern as the other concurrent session's `pypdf` install today) and drove Chrome directly over the DevTools Protocol, polling `document.querySelectorAll('.pagedjs_page').length` every 3 **real** seconds with no virtual-time involved at all. Result: **87 pages, stable from the very first check through 120 continuous real seconds** — confirmed genuinely complete, not a snapshot. Separately confirmed the actual rendered text ends exactly at the book's true final line ("End of Master Draft...") — nothing silently truncated.

**Documented as Claude_V2.md §15** — a standing rule for future sessions: never trust a single `--dump-dom`/`--screenshot` capture's page count for the *full merged book* (only for small single-section files, where it's fine). Poll for real-time stability instead, or just do what the human workflow already does — open it in a foreground tab and wait until it visibly stops changing before printing.

**Final state delivered:** `books/strategy-book/design/templates/build/FULL-BOOK.html`, 87 pages, verified stable, front-matter in sync, fonts vendored locally, correct book order. Ran `health_check.py`/`file_index.py` — same 16 pre-existing failures, nothing new.

---

## 2026-07-22 — Question Bank Book: locked in the end-goal + two new content layers

Pranav showed the target deliverable: `books/question-bank/metadata-index/AS10_Question_Book.html`, a hand-built student-facing "go-to book for practice" for AS 10 (~58 questions, official answers, topic tags, Common Student Mistakes, confidence flags). This reframed the whole Question Bank effort — tagging isn't the end product, it's infrastructure for one HTML book per chapter.

**Two strategic decisions confirmed by Pranav (see CLAUDE.md §6 for full detail):** (1) tag every sitting comprehensively once for every chapter, never re-scan chapter-by-chapter; (2) render chapter books with a reusable generator script, not hand-assembled HTML.

**New work this session:**
- Pranav sourced 6 real ICAI "Examiners' Comments on the Performance of the Examinees" PDFs (Jan2025/May2024/Sep2024/May2025/Sep2025/Jan2026) — converted, sliced to Paper 1 section (`Raw_PDF_.../examiner-comments-paper1/`). Analysed all 6 and wrote `metadata-index/examiner-comments-writing-skill.md` — a style guide for writing ICAI-voiced "Common Student Mistakes" for every question outside those 6 sittings, with a strict real-vs-synthesized provenance tag.
- Added Pranav's OP/PP recurring-question rule (90%-similarity-on-numbers-stripped text; earliest sitting = OP, rest = PP) to `TAGGING-SCHEMA.md`, alongside the `commonMistakes` schema.
- Deliberately did NOT retrofit the 4 already-tagged sitting JSONs — new shape applies going forward only.

**Blocked on:** Pranav is going to share more `AS10_*` sample files (`AS10_Question_Reference.html`, `question-book-implementation-plan.md`, `AS10_Question_Bank.json`) to reconcile our schema before the generator script gets built and Phase 1 (parse+tag remaining ~34 sittings) resumes at scale.

---

## 2026-07-22 — Strategy book: Author's Journey + front-matter Category B sections complete

**`authors-journey.html`** — fully written (was a CSS-only shell):
- Added CSS for `.journey-close` (gold left-border close block) and `.photo-ph` (picture gallery placeholders with handwritten-style `.ph-caption` in Kalam font)
- Full first-person narrative in 5 phases: Foundation 2014–15, Intermediate 2015–16, February 1 2016 result, Why I'm Here, the Socrates close
- All key facts from the master profile used: PCO booth call (80 seconds, 3rd ranker), earthquake April 25 2015 (11:56 AM, Cost Accounting / Overhead chapter), 25–30 days lost, 85% mental reframe, Nepal Blockade, Auditing Pronouncements 5-mark question, dates (Jan 19 2015 CPT, Feb 1 2016 IPCC)
- Four key quotes placed as `blockquote.anon-bq`: "I am not guaranteeing the result. I am guaranteeing the work." / the rank feeling quote / "What you do not revise the day before the exam..." / "Be stubborn about your goals. Be flexible about your methods."
- Socrates loop closes the section in `.journey-close` block
- Four `.photo-ph` placeholders for picture gallery (real photos needed from Pranav)

**`front-matter.html`** — all Category B sections written:
- Added CSS for `.story-vignette` (left border, non-italic vignette block) and `.dedication-block` (centered, spacious)
- **Dedication:** left as `[AUTHOR TO CONFIRM]` — Pranav must write this personally
- **The Socrates Story:** written as a brief plain-prose vignette (7 short paragraphs), no moral stated, no explanation — sits alone as intended
- **About This Book:** full prose from the bullet outlines — what it is, what it isn't, the implementation-layer differentiator, the gyaan warning
- **About the Author:** two-paragraph credential block — AIR 1 CPT+IPCC, EY, IOCL, VC Gurukul; pointer to the journey at the back
- **How to Read This Book:** prose version — bucket navigation, Bucket 0 is daily, [ALL]/[RANK] markers, Emergency Section independence, groups note
- Table of Contents remains `[AUTO-GENERATED]`

**What's left in the book:**
- Cover: Pranav getting it built elsewhere
- Dedication: Pranav's personal text
- Picture Gallery photos: real CPT/IPCC notebooks etc.
- Table of Contents: auto-generated at final assembly

---

## 2026-07-22 — Strategy book front-matter: Blank Page, Title Page, Copyright done

Completed three of the four Category A sections in `books/strategy-book/design/templates/build/front-matter.html`. Emergency section was already fully written (6 steps + 10-day schedule + "what not to do") in a prior context window — confirmed complete, no further work needed.

**What changed in front-matter.html:**
- Removed the `<h1>FRONT MATTER</h1>` editorial heading and the three `<h3 class="subsection-heading">Page N</h3>` structural markers for pages 1–3.
- Added CSS for three new layout classes: `.blank-page`, `.title-page` (with sub-elements `.tp-series`, `.tp-title`, `.tp-rule`, `.tp-author`, `.tp-credential`, `.tp-publisher`), and `.copyright-page` (with `.copy-year`).
- **Page 1 — Blank Page:** genuinely empty `<div class="blank-page"></div>` with `break-after: page`.
- **Page 2 — Title Page:** flex column layout (top/center/bottom zones); title "The Comprehensive CA Intermediate Exam Preparation Guide"; author "CA Pranav Pratik Tulshyan"; credential "AIR 1 (Foundation) · AIR 1 (Intermediate)"; publisher "VC Gurukul · Noida". Gold rule between title and author block.
- **Page 3 — Copyright & Disclaimers:** copyright line + no-reproduction notice + ICAI-requirements disclaimer + strategy-results disclaimer + publication year. Padded from top 60mm (verso positioning convention).
- Pages 4 onwards (Dedication, Socrates Story, About This Book, About the Author, How to Read, ToC) left as `[STRUCTURE ONLY]` — Category B/C, need Pranav's input.

---

## 2026-07-22 — Strategy book: whole-book merge script (`strategy_book_merge.py`)

Continuation of the same-day paged.js work. Pranav wanted independent per-section HTML files (already true — `strategy_book_parser.py` outputs one per bucket) plus one Python script to stitch them into a single whole-book file for continuous pagination/page numbers, with an explicit tuple of paths/slugs controlling merge order rather than relying on filenames.

**Two things checked before building, both verified rather than assumed:**
- Diffed the embedded `<style>` block across 4 different generated files (`bucket-0`, `ai-section`, `cover`, `authors-journey`) — byte-identical. Confirms consolidating to one shared stylesheet in the merged file is lossless, since per-section color/label are always inline styles, never baked into the CSS.
- Found a real bug while checking mergeability: every strategy heading gets `id="s{number}"`, and the number restarts at 1 in every bucket (confirmed `bucket-0.html` and `bucket-1.html` both have `id="s1"`, `id="s2"`...) — would collide into duplicate/invalid ids the moment two sections share one document.

**Also fixed in passing:** `"THE AUTHOR'S JOURNEY — CPT & IPCC"` had no `SECTION_META` entry, so it fell through to a generic fallback — output filename `section.html` (meaningless, collision-prone) and a mangled running-header label ("The Author'S Journey — Cpt & Ipcc" from Python's naive `.title()`). Added a proper entry; now generates as `authors-journey.html` with the correct label.

**Built `tools/strategy_book_merge.py`:** takes `BOOK_ORDER` (an explicit tuple of section slugs, editable in one place, not derived from filenames) or a `--order` CLI override; extracts each section's body-only content (drops the per-file paged.js `<script>` tag, kept exactly once in the output); rewrites `id="sN"` → `id="{slug}-sN"`; wraps each section in a `.book-section` div with `break-before: right` (recto-start, added only at merge time — lone section files don't need it); writes into the same `build/` folder as `vendor/paged.polyfill.js` so the existing relative script path keeps working. Validates in both directions before merging: any listed slug with no file = hard error; any file in `build/` not listed = hard error (downgradeable to a warning via `--force`) — protects against a section silently vanishing from the final book. Also checks CSS is still byte-identical across all sections being merged (hard error if not, `--force` to override) and warns if `MASTER.md` is newer than the build files being merged (stale-build hint).

**Verified with headless Chrome, not just read from the code:** ran `--dump-dom` on the merged 14-section `FULL-BOOK.html` (193,698 chars) — confirmed running-header color switches correctly at each section boundary (all 10 distinct bucket/section colors found in the rendered DOM, in the right places), single `<style>`/`<script>` survived the merge, ids properly disambiguated (`bucket-0-s1` and `bucket-1-s1` both present, distinctly). Also tested the validation logic directly: missing-slug hard error, orphaned-file hard error, and `--force` correctly downgrading the orphan case to a warning.

Documented all of this as durable learnings in **Claude_V2.md §13** (paged.js running-element mechanism, why `@page` can't be trusted with `var()`, the print-media export gap, and the full list of merge-script gotchas) so a future session doesn't have to re-derive any of it.

Ran `tools/health_check.py` + `tools/file_index.py` after adding the new script and build artifact — same 16 pre-existing failures as this morning's entry, nothing new introduced.

---

## 2026-07-22 — Question Bank: PYQ pipeline simplified to Answers-only, coverage extended to 2021

Pranav noticed PYQ "Suggested Answers" PDFs already contain both question and answer text, and are printed (not scanned) — unlike the separate PYQ Question-only PDFs, which always convert blank. Decision: PYQ sourcing now targets only the Suggested Answers document per sitting (same single-document shape as RTP); Question-only PDFs are dead weight.

**Work done:**
- Moved the 4 existing PYQ Question-only PDF/MD pairs (Jan2025, Jan2026, May2024, May2026) to new `Raw_PDF_Question_Bank_CA_Inter_Accounts/deprecated-pyq-question-files/`.
- Converted 6 newly-sourced PYQ Answer PDFs to `.md`: May 2026 (fills a previously-missing sitting) plus 5 older sittings never in the repo before — Dec 2021, May 2022, Nov 2022, May 2023, Nov 2023 (last two were AES-encrypted, empty-password decrypt worked). Used `pypdf` directly (MarkItDown isn't installed in this sandbox) — same plain-text-extraction contract, logged as such.
- Updated `conversion_log.txt` and `question_bank_index.csv` to match current folder reality.
- Built `books/question-bank/question_bank_index_by_attempt.csv` (new) — one row per exam sitting (not per file) with PDF/MD/Parsed/JSON status columns; more useful than the per-file CSV for pipeline-status questions. Updated `CLAUDE.md` section 6 accordingly.

**Result:** PYQ coverage now spans **Dec 2021 – May 2026** (was May 2024 – May 2026) — real progress toward the README's 7–10 yr goal. MTP/RTP still only May 2023 – May 2026.

**Note:** installed `pypdf` + `cryptography` via pip into the sandbox Python (not into the repo/venv) to do the conversions — flagging since it's an environment change, though a low-risk, easily-redone one.

---

## 2026-07-22 — Strategy book: paged.js wired in, page geometry config-driven

Pranav asked how to write the strategy book's HTML so page size/margins can change anytime with no manual re-editing and no overflow risk. Diagnosed a real bug in the existing `tools/strategy_book_parser.py` output: each section was one giant `.page-shell` div with `position:absolute` header/edge-tab/footer — correct-looking for exactly one physical page, but silently broken the moment Chrome sliced a tall bucket into multiple PDF pages (header/footer/edge-tab would only appear once per bucket file, not repeated per page).

**Work done:**
- `books/strategy-book/design/page-geometry.json` (new) — single source of truth for trim/margins.
- `tools/strategy_book_parser.py` — `get_css()` now templates both the `:root` CSS vars and the literal `@page` rule from that one JSON (`@page` doesn't reliably resolve `var()`, so both are substituted from the same source at generation time, never hand-duplicated). Removed the `.page-shell` fixed-div-per-file pattern entirely; content is now one continuous flow. Header/edge-tab/journey-strip are defined once per section via `position: running(name)` + `@page { @top-center/@bottom-center/@right-middle { content: element(name); } }` (edge tab only on `@page :right`) — paged.js auto-repeats them on every generated physical page. Added `break-inside: avoid` on every component (was missing) and `print-color-adjust: exact` (was missing entirely — bucket colours would've printed white).
- Vendored `paged.js` locally at `design/templates/vendor/paged.polyfill.js` (downloaded, MIT license) rather than a CDN, consistent with the offline-safe pattern already used for fonts/images elsewhere in this repo.
- Regenerated all sections (`python tools/strategy_book_parser.py --section all`) — 14 files now, including `cover.html`, `bucket-1.html`, `bucket-2.html`, `bucket-6.html` which MASTER.md had content for but nothing had generated yet.
- Verified with headless Chrome `--dump-dom`: pagination and running-element repetition are confirmed genuinely working (running header found on 4+ generated pages, edge tab on 3+, journey strip on 4+ for `bucket-0.html`).
- **Found and documented a real gap:** the existing `chrome --print-to-pdf` CLI recipe (`_claude/skills/SKILL-html-to-pdf.md`) does NOT work on paged.js output — produces a near-empty ~1KB PDF, because paged.js's paginated view is hidden under print media unless the caller forces screen-media emulation first (which plain Chrome CLI flags cannot do; normally requires Puppeteer). Added a new §9 to that skill file documenting this, with the working manual fallback (open in Chrome → Ctrl+P → Save as PDF) and what a Node+Puppeteer automated path would need. **Node/npm are not installed on this machine** — flagged, not installed without asking first.
- Ran `tools/health_check.py` + `tools/file_index.py` per repo rule. Health check's 16 failures are all pre-existing, unrelated to this work (missing `syllabus-engine`/`question-bank` subfolders, NUL bytes in unrelated `bridge-course/base-studymaterials/*.md` files, `capranav_com/` undocumented in CLAUDE.md) — not touched this session, flagged for Pranav.

**Known trade-off, not yet solved:** `.bucket-banner` (bucket opener colour banner) no longer bleeds to the full trim edge — the old negative-margin trick escaped `.page-shell`'s padding, which no longer exists. True full-bleed under `@page`-margin pagination needs a dedicated zero-margin named page; open item.

**Next lever:** if Pranav wants one-command PDF regeneration back, that needs Node + Puppeteer installed — ask before adding. Otherwise the manual Ctrl+P → Save as PDF path works today with zero new tooling.

---

## 2026-07-22 — Question Bank Book: full-focus audit + tagging schema + 3 sittings tagged

Pranav asked to shift full focus to the Question Bank Book (`books/question-bank/`). Ran a 3-way audit (question-bank folder, concept-book/syllabus taxonomy, mcq-platform for competing schemes) and wrote it up in **CLAUDE.md section 6** (new) — corrected two stale path entries in section 3 (`syllabus-engine/` and `question-bank/` both actually live nested under `books/concept-book/` and `books/` respectively, not at repo root as previously documented).

**Key findings:** raw PDFs converted (54/55) but only 3 of ~55 files had gone through the clean HTML-table parse; only 1 of ~17 exam sittings (MTP Jan 2025) had questions tagged to syllabus topics; three overlapping chapter/topic ID schemes exist in the repo (concept-book bracket tags, the "locked" master syllabus JSON, and `topic-index.json`) with a `U0`-vs-`U1` mismatch for 7 single-unit chapters between the master JSON and everything else.

**Work done:**
- `books/question-bank/metadata-index/TAGGING-SCHEMA.md` (new) — locks in `topic-index.json`'s `unitCode`+`subtopicRef` scheme (not the master JSON's IDs) as the tagging target, documents the U0/U1 reconciliation table, and switches to a **lean index** going forward (question/answer content stays in `Parsed_PDF_.../`, tagging files only point at it via `mdAnchor` — no more full-HTML duplication like the `MTP_Jan2025.json` pilot did).
- Tagged all 3 already-parsed pilot sittings end-to-end: `MTP_May2024_Set1.json`, `PYQ_Jan2026.json`, `RTP_May2026.json` (new files in `metadata-index/`) — 4 of ~17 sittings now tagged, up from 1.
- Extended `topic-index.json` from 22 to **32 of 36** syllabus units — added stub entries (heading lists only, not full descriptions) for AS16, AS28, AS18, AS5, AS24, AS7, AS22, AS25, AS15, AS17 as they came up in the 3 sittings. Only AS 1 and AS 27 remain untouched by any tagged question.
- All new/edited JSON validated (`python -c "import json; json.load(...)"`).

**Explicitly NOT done (flagged, Pranav to decide):** `books/question-bank/README.md` still describes the abandoned `pyq/mtp/rtp/solutions/` layout; `tools/health_check.py`'s `EXPECTED_DIRS` still checks for a top-level `question-bank/` that doesn't exist (pre-existing false-flag, not touched this session).

**Next lever:** parsing the remaining ~52 raw conversions into the clean `Parsed_PDF_.../` format is now the bottleneck — tagging itself is fast once a sitting is parsed.

---

## 2026-07-20 (latest) — Phase 1 extraction fully delegated (MTP/RTP/PYQ/ICAI-Practice); Batch 1 book pivot

**Continuation of the same session — read the two entries below first if picking this up cold.**

**Pivot:** Pranav asked to finish the Batch 1 (10-unit) Question Bank Book first, before starting Batch 2/3 Phase 0. Since Phase 1 (question extraction) is naturally per-source-paper not per-chapter, decided (Pranav's call) to **extract every question from every source paper once now**, then tag against Batch 1's keyword index only — non-Batch-1 matches wait for Batch 2/3's indexes later. This avoids re-scanning the same source papers three times.

**Delegation across tools, per Pranav's request:**

- Wrote `phase1-mtp-prompts.md` (5 prompts, 18 MTP attempts/36 files), `phase1-rtp-prompts.md` (3 prompts, 7 RTP files), `phase1-pyq-prompts.md` (3 prompts, 7 PYQ attempts incl. the null-Q/null-Ans edge cases) — for Pranav to run through Gemini/Copilot/Blackbox. **Not yet run as of this entry.**
- ICAI-Practice compilation (scanned, 101+111 pages) was assigned to me directly since it needed OCR. Built and verified an OCR pipeline (PyMuPDF + pytesseract, see the entry below for the snippet) and OCR'd both PDFs successfully.
- **I hand-extracted Model Test Papers 1–4's questions myself** (reading the OCR text directly) — written to `books/question-bank/metadata-index/icai-practice-extraction/icai_practice_MTP{1,2,3,4}_Q_extracted.json`. Partway through MTP5, Pranav pointed out that once OCR is done, structuring plain OCR text into JSON is mechanically identical to what the other three tools are doing for MTP/RTP/PYQ — no longer needs a premium model. **Correct call — I agreed and stopped doing it by hand.**
- Copied `icai_practice_Q_ocr.txt` / `icai_practice_Ans_ocr.txt` (the full OCR dumps) into the repo at `books/question-bank/metadata-index/icai-practice-extraction/` so Tier 2 tools can actually read them (they'd been sitting in Claude's own scratchpad temp dir, inaccessible to VS Code extensions). Wrote `phase1-icai-practice-prompts.md` (2 prompts: extract MTP5-8, then match answers for all 8 papers against the Ans OCR text, using my MTP1-4 files as the format reference). **Not yet run.**

**Lesson for future sessions:** OCR (image→text) is genuinely Tier 1/mechanical and fine to do myself via Tesseract. But *structuring* OCR'd text into schema'd JSON is Tier 2 work like any other source file — don't keep doing that by hand past the first paper or two once the OCR output is confirmed clean; write the prompt and hand it off. Recognize this pivot point earlier next time instead of grinding through several papers first.

**Current state:** all four Phase 1 prompt sets (MTP, RTP, PYQ, ICAI-Practice) are written and ready. Nothing to do until Pranav runs them and brings back outputs. Next real work is reviewing/merging those 8 batches of JSON, then Phase 2 (tagging against Batch 1's `topic-keyword-index.json`), then Phases 3–8 to produce the finished Batch 1 book.

---

## 2026-07-20 (later) — Phase 0 Batch 1 complete: topic-keyword-index.json (10/36 units)

**Continuation of the AS2/AS10 audit session (see the entry below this one for full background — read that first if this is your first time picking up the Question Bank Book work).**

**What happened this session:**
- Rebatched Phase 0 to Chapters 1–4 / 5–9 / 10–15 (10/17/9 units, replacing the earlier 17/13/6 split) — AS 2 and AS 10 now sit in Batch 2, not Batch 1.
- Verified Tesseract 5.5.0 install and built a working OCR pipeline: **PyMuPDF (`fitz`) + `pytesseract`**, no Poppler needed — simpler than the originally-planned `pdf2image` route. Confirmed end-to-end against the ICAI-Practice compilation.
- Wrote `books/question-bank/metadata-index/phase0-batch1-prompts.md` — 10 fully-instantiated Phase 0 prompts (real file paths, real topic scaffolds pulled from the taxonomy JSON), one per Batch 1 unit, ready to paste into Gemini/Copilot/Blackbox.
- **Ran all 10 prompts and completed the full Tier 3 review + merge cycle.** `books/question-bank/metadata-index/topic-keyword-index.json` now has **10/36 units, 114 topics**: M1-C1-U0 (Intro to AS), M1-C2-U0 (Framework), M1-C3-U0 (Applicability), M1-C4-U1 (AS1), M1-C4-U2 (AS3 Cash Flow), M1-C4-U3 (AS17 Segment Reporting), M1-C4-U4 (AS18 Related Party), M1-C4-U5 (AS20 EPS), M1-C4-U6 (AS24 Discontinuing Ops), M1-C4-U7 (AS25 Interim Reporting).

**Batch 1 is fully done.** Every Tier 2 draft was checked line-by-line against its actual source `.md`, not rubber-stamped. Patterns worth knowing before doing Batch 2/3:
- **Almost every unit's Tier 2 draft omitted the unit's own "Illustrations + Test Your Knowledge" section** as a topic bucket — even though this is usually the single richest source of realistic exam-style numerical/scenario questions. Added as a `*`-suffixed unnumbered bucket (e.g. `M1-C4-U5-T5.13*`) in every case. **Expect this same gap in Batch 2/3 outputs — check for it every time, don't assume a Tier 2 tool will remember to include it.**
- Some tools explicitly stated they only read part of a long source file (AS 17's tool said "read lines 1 to 500" of a 1010-line file) — when that happens, the *numbered* topics it did cover are usually still accurate, but the unread tail (illustrations/TYK) needs a separate read-and-add pass.
- Dense definitional/threshold sections (AS 18's `T4.6`, the MSME/SMC thresholds in `M1-C3-U0-T2`) came back essentially error-free even under heavy scrutiny — the Tier 2 tools are reliable on this kind of content when given the exact file path + topic scaffold, per the prompt design in `phase0-batch1-prompts.md`. The failure mode is *omission* (missing sub-rules, missing whole sections), not *fabrication* — no hallucinated facts were found across all 10 units.
- One prompt output arrived as an exact duplicate of an earlier prompt's output (Prompt 9 first came back identical to Prompt 7) — flagged to Pranav, he re-ran it and got a valid distinct result. If this happens again, don't merge the duplicate; ask for a re-run.

**Immediate next steps:**
1. Batch 2 (Chapters 5–9, 17 units — includes AS 2 and AS 10, which already have deep familiarity from the original audits) is next. Per Pranav's decision, wait for **all 17** Batch 2 units' Phase 0 keyword drafts before starting Phase 1 (question extraction) on any of them, including AS 2/AS 10 — don't fast-track those two ahead of their batch-mates.
2. Need a new `phase0-batch2-prompts.md` analogous to the Batch 1 one, with real file paths + topic scaffolds for all 17 Batch 2 units.
3. The two flagged AS 10 audit gaps (PYQ May 2026, ICAI-Practice MTP 6–8) from the earlier session are still open and lower priority than the Question Bank Book pipeline work.

---

## 2026-07-20 — AS2/AS10 question-bank audits + Question Bank Book project kicked off

**Read this entry first if you're picking up the "Question Bank Book" work on a fresh clone/session — it explains exactly where things stand and what to do next.**

**What exists now:**
- `books/question-bank/metadata-index/AS2_Question_Reference.html` and `AS10_Question_Reference.html` — accuracy-audited, topic-tagged references of every genuine question found in the MTP/RTP/PYQ/ICAI-Practice question bank for AS 2 (Valuation of Inventories) and AS 10 (Property, Plant & Equipment) respectively. Each has a topic-wise marks-weightage summary plus MCQ/Descriptive/Integrated detail tables with page refs (Q and Ans located independently, never inferred from each other), marks, concepts tested, and "Common Student Mistakes." **AS10's audit has two known gaps, clearly flagged inside the file itself: PYQ May 2026 (scanned PDF, no Ans doc exists) and ICAI-Practice Model Test Papers 6–8 were never audited.**
- `books/question-bank/metadata-index/topic-index.json` — a reusable index of ICAI base-material unit structure (currently has full/accurate numbered sub-topic breakdowns only for AS 2 and AS 10, built by directly reading each unit's source `.md`/`.pdf` — not guessed). Superseded in spirit by the newer `topic-keyword-index.json` planned in Phase 0 below, but still useful as-is.
- `_claude/skills/SKILL-question-bank-summary-making.md` — the accuracy-first methodology for auditing a chapter's questions across the question bank (source-of-truth locations, false-positive traps like FIFO-for-investments-vs-inventory, independent Q/Ans page verification rule, speed-vs-accuracy tradeoff handling, marks-aggregation rules). Load this before doing any further chapter audits.
- `books/question-bank/metadata-index/question-book-implementation-plan.md` — the actual build plan for turning these audits into a full **"Question Bank Book"**: one flowing per-chapter document (Q.N → metadata → question → answer → rubric → common mistakes), topic-ordered, with OP/PP duplicate-question linking and per-question time estimates. Read this file in full before doing any Question Bank Book work — it has the phase breakdown, tier assignments (Python / cheap model / Claude), ready-to-paste prompts for Phase 0 and Phase 1, and the Tesseract OCR install steps.
- `books/concept-book/syllabus-engine/data/0-ca-inter-adv-accounts-subtopics-marks-weightage.json` — pre-existing, NOT built this session, but central to the plan: canonical `M{module}-C{chapter}-U{unit}-T{topic}` IDs for all 36 units across the syllabus's 15 ICAI chapters. Confirmed by cross-checking against a direct read of the AS2/AS10 source units that its numbering is accurate.

**Key decisions made with Pranav this session (don't re-litigate these):**
- The "Question Bank Book" per chapter will have: Q.N sequence → metadata (MCQ-Direct/MCQ-Scenario/Descriptive, attempt, Q.No in that attempt, marks, estimated time = marks×1.8 min, topic tags in the `M-C-U-T` format, comprehensive-question flag for ≥3 distinct topic tags) → question → official answer → "Important Computational Steps" (rubric, author-inferred since ICAI doesn't publish official step-marks — will later drive AI-based grading of student answers, so this stays Claude-only, never delegated to a cheap model) → "Common Student Mistakes."
- Missing marks: apply an ICAI-typical default (2 marks is near-universal for MCQs) but always label it `"Author Guessed"`, never silently presented as ICAI's own figure.
- Duplicate/near-identical questions across attempts get an **OP** (original, earliest attempt) / **PP** ("Practice Perfect", later near-duplicates ≥95% text-similar after stripping numbers) tagging system — PP entries carry a pointer back to their OP.
- Ordering within a chapter's book follows the ICAI syllabus's own topic sequence, not the order questions happened to appear across exam attempts.
- Cost-control architecture (Pranav's framing, agreed): **Tier 1 fully deterministic → Python** (written by GitHub Copilot/Gemini in VS Code, not Claude); **Tier 2, 40–90% deterministic → cheap/free model** (Blackbox/Copilot/Gemini in VS Code, but the *prompt* is always authored by Claude); **Tier 3, creative/high-stakes/review → Claude directly**. OCR for scanned PDFs uses Tesseract (a dedicated tool), not an LLM at all.
- Phase 0 (building one single master `topic-keyword-index.json` covering all 36 units, so cross-chapter tagging for integrated questions works cleanly) runs **before** any further chapter's question extraction, in 3 batches by ICAI chapter number: **Batch 1 = Chapters 1–5 (17 units)**, **Batch 2 = Chapters 6–10 (13 units)**, **Batch 3 = Chapters 11–15 (6 units)** — note this split is workload-uneven (Batch 1 is ~3x Batch 3), which was flagged to Pranav and accepted as-is.

**Immediate next steps (in order):**
1. Build `books/question-bank/metadata-index/topic-keyword-index.json` for Batch 1 (Chapters 1–5) — the Phase 0 prompt is in `question-book-implementation-plan.md`, run once per unit via Gemini/Copilot, Claude reviews the drafts before merging (AS2/AS10 already have deep source familiarity from the audits, so those two units should be fast).
2. Once Phase 0 Batch 1 is done, Phase 1 (question+answer extraction) can start for the Batch 1 chapters — or, per Pranav's earlier framing, interleave so the AS2/AS10 book doesn't wait on all 17 Batch-1 units' keyword indexes to finish first (this specific interleaving question was raised but not yet finally answered — ask Pranav to confirm before assuming).
3. Separately, and lower priority: finish the two flagged AS10 audit gaps (PYQ May 2026, ICAI-Practice MTP 6–8) if a complete AS10 reference is needed before the Question Bank Book work reaches AS10.

---

## 2026-06-22 — CA Foundation strategy slides + HTML-to-PDF skill

Created `books/strategy-book/working/exam-strategyFoundation.html` (7-slide interactive dark-background presentation with beat-wise JS animation engine for CA Foundation Sep 2026 batch). Generated `exam-strategyFoundation-print.html` (static print copy, mm/pt sizing, all content visible) and `exam-strategyFoundation.pdf` (7 pages, 150 KB, A4 landscape) via Chrome headless.

Converted `books/concept-book/chapters/seq04-as02-valuation-of-inventories.html` to PDF (16 pages, 595 KB, A4 portrait). Added `print-color-adjust: exact` to source `*` rule; used Edge + `--virtual-time-budget=15000` because Chrome headless failed silently on Google Fonts.

Created `_claude/skills/SKILL-html-to-pdf.md` — full 8-section skill with two worked examples (slides vs. chapter), documenting the Chrome-vs-Edge decision, `--virtual-time-budget` flag, `--no-margins` usage, and the "no separate print file needed when source already has @media print" pattern.

---

## 2026-06-22 - Parsed question-bank pilot created

Created ooks/question-bank/Parsed_PDF_Question_Bank_CA_Inter_Accounts/ with one parsed MTP, one parsed RTP, one parsed PYQ, and a README. Outputs remain .md files with HTML table blocks for ruled accounting layouts. Ran python tools/health_check.py (17 pre-existing failures remain) and python tools/file_index.py (417 files indexed).

---

## 2026-06-22 - Question-bank markdown parseability sampling

Inspected ooks/question-bank/README.md, question_bank_index.csv, and sampled MTP/RTP/PYQ markdown files under ooks/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/. Confirmed raw OCR markdown is parseable with a custom rule-based parser, but needs cleanup rules for page numbers, table fragments, front-matter announcements, and embedded suggested answers in RTP files.

---

## 2026-06-22 - Orientation read: CLAUDE.md + project context reviewed

Read AGENTS.md, README.md, CLAUDE.md, and the _claude/memory/ context to understand the cap-online ecosystem. Ran python tools/health_check.py; it reported existing missing expected folders, NUL-byte text files in bridge-course/question-bank sources, and undocumented top-level capranav_com/. No content files changed beyond this log note.

---

## 2026-06-19 — AS02.dc.html animation: 4 fixes applied + local React bundled

Applied all 4 agreed fixes to `books/concept-book/characters/animations/AS02.dc.html`:

1. **Narrator position**: `top:332` → `bottom:90` (subtitle band, no longer overlaps characters)
2. **Pranav walk animation**: Added `asEnter` keyframe (slide in from right); changed his Scene 4 beat pose from `'walk'` (bounce) to `'enter'`
3. **Jump-to-scene menu**: `≡` button top-left opens an overlay listing all 12 scenes; click to jump; ESC or click-away to close; click-to-advance blocked while menu is open
4. **Local React**: Downloaded React 18.3.1 UMD as `react.min.js` + `react-dom.min.js` into animations folder; added `<script>` tags before `support.js` in all 3 `.dc.html` files (AS02, universe-intro, Character Universe) — zero CDN dependency at runtime

All changes committed locally. Pranav to `git push origin main` from his machine.

---

## 2026-06-17 — AS 2 Concept Book chapter: HTML print version complete

Created `books/concept-book/chapters/seq04-as02-valuation-of-inventories.html` — print-ready A4 HTML for the AS 2 Concept Book chapter. Self-contained file (Google Fonts CDN, all CSS inline).

Design: 7 pages — (1) cover (navy gradient, watermark AS2, gold-orange accent bar, badges), (2) story "Godown Ka Hisaab", (3–5) Layer 2 concept notes [AS2-1.2] to [AS2-1.15], (6) Illustration Guide, (7) TYK Guide + Layer 3. Color system: Story = orange border on warm cream; Kaam Ki Baat = green border on mint; Story Reference = purple border on lavender; Exam Note = red border on light red; Layer 3 = dark navy background with orange numbered circles. Print: @page A4, position:fixed header/footer repeating on each printed page. Fonts: Poppins (headings/badges), Merriweather (story prose), Lato (body).

All 4 Kaam Ki Baat boxes, 3 Story References, and Exam Notes from the MD chapter are fully reproduced in the HTML.

---

## 2026-06-17 — final-deliverables: 02A and 03A light versions created

Continuation session (context exhausted in previous turn). Tasks from previous session pending were:

1. `final-deliverables/02A-batch-day-wise-planner-light.md` — lighter version of 02. Stripped Kahaani/Koncept/Karma narrative from Day Focus column; removed Notes column. Kept all 97 rows, 6 phase headers, chapter tests, ITD tests, holiday markers. Day Focus is now just topic/subtopic name (e.g. "Why AS exist; ASB formation; 8-step standard setting; benefits and limitations"). Phase summary table retained at bottom.

2. `final-deliverables/03A-bridge-course-skeleton-light.md` — lighter version of 03. Removed all Kahaani narration (story beats, dialogues, Arjun/bus scenes). Kept: time budget tables for both sessions, Kahaani slot with just the anchor concept (blood report metaphor / why rules exist), full Koncept topic list in sequence, all Karma items (MCQ topics + illustration details), Layer 3 one-liners, vision close content list. 1.5 hrs × 2 session format maintained.

3. `final-deliverables/` folder documented in CLAUDE.md section 3 and README.md (folder map + Where things are table). This was overdue from when the folder was created last session.

4. `file_index.py` run: 326 files. `generate_component_index.py` run (regenerated). `health_check.py`: 22 pre-existing failures — 12 missing gitignored/local folders, 9 NUL-byte OCR files from last session's base-studymaterials, 1 component-index CRLF/LF hash mismatch (systematic tooling bug — generator hashes text, health_check hashes raw bytes on Windows). No new failures from this session's work.

---

## 2026-06-15 — teaching_sequence.md: ALL 10 chapters complete

Multi-session task concluded. Built `books/bridge-course/teaching_sequence.md` — 7-column table (CA Level | Chapter No. | Unit No. + Unit Name | Topic/SubTopic ID | Topic Name | Page No. | One-Line Summary) from all 10 base-studymaterial OCR files.

This session (continuation): CA Inter Chapter 2 (24 rows) + CA Inter Chapter 3 (9 rows) appended.

- Ch3 sections: 1 (Status of AS), 2 (Applicability intro), 2.1 (MSME/Large criteria, effective 1 Apr 2024), 2.1-Illus (Example 1), 2.3 (Companies), 2.3.1 (20 AS in entirety), 2.3.2 (SMC exemptions), UNTSMRY, TYK (ranking: 2.1 \ 1)
- Full file: header + Foundation Units 1–7 + Inter Ch1 (16 rows) + Inter Ch2 (24 rows) + Inter Ch3 (9 rows)
- `file_index.py` run (116 files); `health_check.py` 15 pre-existing failures only (same as before — not caused by this work)

---

## 2026-06-15 — Bridge Course Topics to cover.md — full final rewrite completed

Continuation session (prior context was exhausted mid-task). Wrote the complete final version of `books/bridge-course/Topics to cover.md` covering ALL source chapters:
- Foundation Ch1 Units 1–7: every numbered sub-topic, all illustrations with concept-test note, Summary, TYK with sub-topic IDs
- Inter Ch1 (Intro to AS): all 14 sections including 8-step process, IFRS components, carve outs/ins, Ind AS roadmap for all 4 entity categories
- Inter Ch2 (Framework): all 11 sections — 8 elements of the Framework, 7 user groups, 3 fundamental assumptions, 4 qualitative characteristics + sub-qualities, 5 elements (formal definitions), 4 measurement bases, all 3 capital maintenance concepts; all illustrations/examples with concept-test notes
- Inter Ch3 (Applicability): Status, 3-question test, ICDS (10 standards), MSME vs Large entity revised criteria (Aug 2024), SMC vs Non-SMC exemptions; all MCQs with sub-topic IDs, case scenarios
- Ran `file_index.py` (116 files); `health_check.py` shows 15 pre-existing failures only (no new issues)

---

## 2026-06-15 — Bridge Course Layer 2 revision map written

Created `books/bridge-course/Topics to cover.md` — point-wise, topic-wise raw concept summary of all source chapters:

- **CA Foundation Ch1 Units 1, 2, 5, 6, 7:** 6-step accounting cycle, evolution (Egypt → Pacioli), objectives, functions, book-keeping vs accounting, sub-fields, users, disciplines; all 12 GAAPs with key pointer each; 3 Fundamental Assumptions; Accounting Policies (selection + change); 4 Valuation Bases + Accounting Estimates; AS objectives, benefits, limitations, ASB process (8 steps), 3 sets of standards, AS 1-29 full list, key Ind AS list
- **CA Inter Ch1:** GAAP at Inter depth, IFRS/IASB, Convergence vs Adoption, Ind AS, Carve-outs, Phase-wise Roadmap
- **CA Inter Ch2:** Framework (objectives, users, 4 qualitative characteristics with sub-qualities), 5 elements with formal definitions, 2 recognition criteria, 4 measurement bases, Financial vs Physical Capital Maintenance
- **CA Inter Ch3:** Status of AS, 3-question applicability test, Companies Act Sec 129/133/143, non-corporate applicability, CA's professional responsibility
- Purpose: "Layer 2 skeleton" — Pranav Sir will insert story anchors and concept teaching between these raw topics
- `file_index.py` run (116 files: 106 text, 10 local); `health_check.py` has 15 pre-existing failures (9 NUL-byte files in base-studymaterials, 5 missing gitignored folders, component-index stale) — none caused by today's work

---

## 2026-06-15 — Bridge Course master teaching document complete

Rewrote `books/bridge-course/bridge-story.md` into a full structured teaching guide:

- **3-class × 1-hour structure** with story, chapter maps, cliffhangers
- **Class 1 (Foundation):** Going Concern, Money Measurement, Matching, Consistency, Conservatism, Materiality, Accounting Policies, Valuation Bases, Why AS exist — all with blood-report / Byju's / Arjun story thread
- **Class 2 (Inter Ch 1):** GAAP, AS-setting process (ASB), IFRS/IASB, Convergence vs Adoption, Ind AS, Carve-outs, Roadmap
- **Class 3 (Inter Ch 2 + 3):** Framework (4 qualitative characteristics), Elements (formal definitions), Recognition criteria, Capital Maintenance, 3-Question Test, Companies Act Sec 129/133/143, CA's responsibility
- Every class ends with a story cliffhanger except Class 3 (which is a resolution)
- AI fear not resolved — one paragraph: focus on studies, conversation for later
- Ran `file_index.py` (updated); `generate_component_index.py` (regenerated)
- `health_check.py` has 13 pre-existing failures (NUL bytes in base-studymaterials files from cross-mount edit, 5 missing gitignored folders, component-index stale) — none caused by today's work

---

## 2026-06-14 — Bridge course story written

Created `books/bridge-course/bridge-story.md` — a Chapter 0-style Hinglish dialogue story bridging CA Foundation → CA Inter. Same characters (Arjun + Pranav Bhaiya), same narrative style. Covers:

- Foundation concept recap (Entity, Dual Aspect, Accrual, Matching, Going Concern, Consistency, Conservatism)
- Why Accounting Standards exist (the 5-accountants-5-profits problem)
- What Accounting Standards are and how ICAI formulates them
- AS vs Ind AS vs IFRS — India's convergence journey
- Framework for financial statements (Reliable, Relevant, Comparable, Understandable)

Setting: Arjun receives his Foundation result (passed), calls Pranav Bhaiya, conversation bridges him into the Inter level. Content is ICAI curriculum-accurate throughout.

---

## 2026-06-13 — Working tree cleanup: 4-block atomic commit plan completed

Resumed from previous context (session ran out). Committed remaining 2 blocks:

- **Block 3** (`a6b3e18`): CLAUDE.md + content/README.md — documented `productions/` folder in both files
- **Block 4** (this entry): file-index regeneration + project log

**Sep26-strategy relocation** (done in prior session, committed as Block 1):
All 14 old paths under `books/strategy-book/video-presentations/sep26-strategy/` moved to `content/productions/sep26-strategy/deck/`. Git detected renames correctly.

**Pending decision (Pranav):** `content/assets/green-screen/book-cover-image-base-64.txt` — 573KB base64-encoded PNG. Used by `book-promo.html` for self-containment. Per "no binary files in git" rule, recommend adding to `.gitignore`. If Pranav wants it committed, can do so explicitly.

**Pending tasks:**
- Add `--input` flag to `tools/strategy_book_parser.py` so it can process `CA-Inter-90-Days-Strategy.md` (currently defaults to MASTER.md only)
- Generate 90-day book HTML → PDF once `--input` flag added

---

## 2026-06-11 — AI section expanded + parser table support added

**MASTER.md — THE AI SECTION:** Added 3 new sub-sections after the existing 7 use-cases:
- **TOOL PICKER** — markdown table: 10 rows mapping task → best tool → why (NotebookLM, Claude, Perplexity, ChatGPT, Sarvam/Gemini, KIMI)
- **OUTPUT FORMAT** — HTML vs MD vs PDF guidance with ready-to-use prompts; explains token cost of scanned PDFs
- **TOKEN MINIMIZATION** — 6 numbered habits for free-plan users + PRANAV'S TIP (compact MD summary habit)

**Parser (`tools/strategy_book_parser.py`) — markdown table support added:**
- Tokenizer: detects `|`-prefixed lines, parses header/separator/data rows → `{'type': 'table'}` token
- Renderer: `_table()` method → `<table class="content-table">` with thead/tbody
- `_component_body()`: table token wired in (tables inside components work too)
- CSS: `.content-table` / `.table-wrap` — zebra-striped, uppercase headers, border-collapse

Verified: parser renders AI section cleanly; all 7 checks pass (content-table, NotebookLM, headings, HOW TO DO THIS, PRANAV'S TIP, handwritten class, file size 20KB). health_check green (47/47, MD5: 5805c527).

---

## 2026-06-11 — CA-Inter-90-Days-Strategy.md fully rewritten, HTML-synced

Complete rewrite of `books/strategy-book/working/CA-Inter-90-Days-Strategy.md`.
Now fully in sync with the sep26-strategy HTML slide deck and standalone as an
independent book.

**Structure:** FRONT MATTER (Title, Copyright, Dedication, Socrates Story, About
the Author, About This Book, How to Read) → ROUTING PAGE → BUCKET 3 (Phase 1:
Build Your Arsenal, 18 strategies) → BUCKET 4 (Phase 2: Delivery Mode, 10
strategies) → BUCKET 5 (The 15 Days, 17 strategies) → BUCKET 0 (Daily
Foundation, 13 strategies + Discipline Bridge) → PERSONAL PAGES → AUTHOR'S STORY.

**Sync gaps closed vs slides:**
- Booti 3: "Paste It Where You Live" → "The Visual Vault" (Flowcharts / Tables
  & Formats / Skeletons / Dates·Rates·Limits / Mnemonics); paste-it is now the
  usage rule, not the name
- Level 1 gate: 3-check system (Boundary written + Layer 1&2 documented + 3
  Bootis) → LEVEL 1 CLEARED → NO NEW MATERIAL
- Mock Analysis Protocol: routing decision tree (recall-fail → Visual Vault;
  didn't-know-in-Boundary → Golden Nuggets; outside Boundary → decide)
- Discipline Bridge: before Bucket 0 — "CA is game of PREPARATION not talent"
  + Atomic Habits framing
- Student Toolkit promise (20+ tools, comment guarantee)
- "ON GROUND Strategies" / "No Gyaan Baazi" language in About This Book
- North Star escalates to 3× per day in Bucket 4
- Layer 3 size: "10–40 pages per subject"
- Gamify frame: Level 1 / Final Boss (tied to Level 1 CLEARED milestone)

**Parser compliance:** Section headings map to existing SECTION_META keys
(BUCKET 3/4/5/0, FRONT MATTER, ROUTING PAGE, PERSONAL PAGES). 58 strategy
headings. 48 component markers. Health check clean.

**Stats:** ~1520 lines. Gallery skipped (per Pranav). About Author added.

---

## 2026-06-11 — Book-promo silent slide (book-promo.html) + CTA bug confirmed fixed

- **CTA stray `</div>` bug**: confirmed already fixed on disk (Pranav's edit); his local `node --check slides-part4.js` passes. Deck is now **29 slides** — Pranav added Mock Analysis Protocol (24B), Discipline Bridge (24C), and a Manifest line on the CTA; deck README still says 27 (update pending).
- **New: `books/strategy-book/video-presentations/sep26-strategy/book-promo.html`** — standalone silent promo slide for the Complete Strategy Book PDF (end of Sep-26 video, no voiceover). Floating 3D A4 book cover (dark, brand blue/green edge, gold accents, shine sweep, float + floor-shadow animation) with Pranav's photo **chroma-keyed from green-screen** (`content/assets/green-screen/Book-cover-green.png` → transparent cutout, embedded base64 — file ~386 KB, fully self-contained). Right panel: LAUNCHING SOON badge, facts (90+ strategies, **20+ frameworks** — actual count 23, Pranav chose the safe number, 30+ Pranav's Tips, 7 buckets, 3 Bootis, 17 exam-day strategies, fill-in pages), CTA "For **Jan 27 & May 27** attempts" (Pranav confirmed; original brief said Jan 26) + PRE-BOOK NOW / Early Bird / UP TO 30% OFF / link in description. 1920×1080 stage, auto-scales to window.
- **Note**: the base64-embedded image makes this HTML a ~386 KB blob in git — Pranav to decide: commit as-is or gitignore it.
- Sandbox health_check: known stale-mount false flags (slides.js, parser, video-brief) + **component-index STALE (MASTER.md changed: 86bb07d8 → efdc37ad)** — Pranav to run `python tools/generate_component_index.py` + health_check locally. file_index regenerated (200 files).

## 2026-06-09 — reconcile Pranav's edits + new spaces (Session: setup, cont.)

- Confirmed Pranav's build-out: strategy-book `sources/ design/ working/ video-presentations/`, new tools (`generate_component_index.py`, `strategy_book_parser.py`), component-index MD5 check in health_check, segment-library + standup material in `preparations/`, all motivation images moved to `obs-setup/assets/` (content/motivation now a daily-quote media library, kept).
- Fixed typo `sources/extermal` → `sources/external`; added `.txt` to Report 4 & 5 (external strategy research from YouTube etc.).
- New top-level **`student-toolkit/`** (separate from telegram bots) — moved `Exam Preparation date calculator.xlsx` there.
- Dedupe: removed 6 redundant strategy copies from `_claude/` (book is single source of truth); concept-book material stays in `_claude/` until it gets its own home.
- Placed syllabus master `CA-Inter-Adv-Accounts-Syllabus-TEACHER-COPY.xlsx` → `syllabus-engine/data/` (4 sheets: chapter categorize, topics+subtopics w/ unique topic IDs, combined syllabus, ICAI topics).
- Registered `student-toolkit` in CLAUDE.md + health_check EXPECTED_DIRS.
- health_check encoding guard flagged sandbox-corrupted reads of `strategy_book_parser.py` (NULs) and `slides.js` (truncated) — disk copies intact; commit from Pranav's machine. Component-index stale → run `generate_component_index.py`.

## 2026-06-11 — Deck: Mock Analysis Protocol + Discipline bridge slides (Pranav's 2nd pass)

- **New slide "Mock Analysis Protocol"** (after Mock Window): analysis TURANT mock ke baad (khud ya siblings/friend se checkwao) + routing — knew-but-no-recall → Visual Vault · didn't-know-but-in-Boundary → Golden Nuggets · chapter-not-in-Boundary → decide; if added → must also go in Layer 3 + revision material.
- **New slide "Discipline bridge"** (cushion before Bucket 0, was abrupt): "Tough? Impossible?" → "CA is a game of PREPARATION, not talent" → discipline ≠ quick motivation / week's josh / Monday flame → unwavering commitment → ATOMIC HABITS, 21 din = habit, "buffer aaj bhi hai. Go."
- Deck now 29 slides. Fixed stray `</div>` in CTA (from Pranav's manual edit; wording kept). Pranav's wording edits this pass retained: "This entire PPT discussion — FREE PDF", manifest line, "Exam ke 15 days ki strategy".
- Clarified for Pranav: "Error Register ka ek full pass" = one complete start-to-finish sweep of every logged error before exams.
- Commit still Pranav-side (sandbox stale-view issue).

---

## 2026-06-11 — Deck review tweaks (Pranav's pass) + commit deferred to Pranav

- Pranav reviewed full deck. Changes: visible **"↺ RESET" button** on Subject Slider Board (R key kept as backup); **Booti 3 renamed "The Visual Vault"** (Pranav picked from options) — contents now Flowcharts / Tables & Formats / Skeletons / Dates·Rates·Limits / Mnemonics, paste-it-where-you-live kept as the usage rule; AI slide synced ("printable visual sheets — Visual Vault ke liye"); **15 JULY slide now gates LEVEL 1 CLEARED on 3 checks** — Boundary written (har subject/chapter) + Anchor Material & Layer 1–2 ready/documented (physical ya digital) + 3 Bootis — then "Tab — aur sirf tab — LEVEL 1 CLEARED".
- Pranav edits this session: "ON GROUND Strategies" wording, Layer 3 "Around 10-40 pages", toolkit line "This is where I'll help".
- **OPEN: Booti 3 rename in `CA-Inter-90-Days-Strategy.md`** (book still says "Paste It Where You Live") — Pranav to decide.
- **Git: NOT committed from sandbox** — sandbox mount serves stale/truncated views of files edited this session; a sandbox commit would store corrupted blobs. Pranav commits from his machine (`git add -A && git commit`). His local health_check is the authoritative check this session.

## 2026-06-11 — Fixes: .handwritten class + 90-day book AUTHOR SAYS rename + MASTER trailing space

**Fix 1:** `tools/strategy_book_parser.py` PRANAV'S TIP renderer — `comp-body` → `comp-body handwritten` (`.handwritten` CSS was orphaned after AUTHOR SAYS removal; this wires it back in).
**Fix 2:** `CA-Inter-90-Days-Strategy.md` — all 10 `> **AUTHOR SAYS:**` → `> **PRANAV'S TIP:**` (90-day guide had not been updated in the earlier rename pass).
**Cleanup:** MASTER.md line 1 trailing space (test artifact from staleness-test) removed. Component index regenerated (clean MD5: `86bb07d8`). All health checks green (46/46, encodings OK, index in sync).

---

## 2026-06-11 — AUTHOR SAYS → PRANAV'S TIP rename + component index automation

**MASTER.md:** All 30 occurrences of `> **AUTHOR SAYS:**` renamed to `> **PRANAV'S TIP:**` (branding — student reads Pranav's name on every tip block). PT total now 33 (30 former AS + 3 original PT), IF = 22.

**Reference code system designed and implemented:**
- `ASG.B.S` = All Strategy, Bucket B, strategy S (e.g., `ASG.0.4` = Move Your Body)
- `RSG.B.S` = Rank Strategy (e.g., `RSG.3.11` = Rate Your Chapters; only 2 RANK strategies exist, both in B3)
- `IF.B.S` / `PT.B.S` = component inside that strategy
- Bucket 6 → `6A` (Track A, passed) and `6B` (Track B, failed/retaking)
- Emergency → `E`

**New tool: `tools/generate_component_index.py`** — auto-generates MASTER-component-index.md from MASTER.md. Writes MD5 of MASTER.md into index header. Run after any MASTER.md edit.

**health_check.py updated:** Check 5 added — compares stored MD5 in index to current MASTER.md; fails with regeneration instructions if stale.

**strategy_book_parser.py updated:** Removed `AUTHOR SAYS` from COMPONENT_MARKERS; `PRANAV'S TIP` handler (`.pran-tip` CSS class) already existed and handles all PT blocks.

All checks green (46/46 folders, encodings clean, component index in sync, MD5: `86bb07d8`).

---

## 2026-06-11 — Sep-26 video slide deck COMPLETE: all 27 slides (Phases 1–4)

- Major restructure per Pranav after first-3-slides review: **15th July** (not 25th) = B4 start/Level-Up/No-New-Material date (Pranav's buffer choice; exact 45-days-before-1-Sep is 18 Jul — flagged, he chose 15th; slides say "45+ days"). Exams 1–12 Sep. Bilingual headings everywhere (EN + Devanagari). Brand chrome = DISC blue/green; bucket colours from design-spec; gold = Bootis only.
- **Phase 1**: slide chrome in engine (bilingual header + live days chip, footer journey strip w/ proportional buckets + B0 band, watermark "CA Pranav P Tulshyan"), Gita Shlok opener (2.47), Reality Check title, Bucket Analysis proportional timeline (B1 8% / B2 34% / B3 22% / B4 16% / B5 7% / B6 13%; markers AAJ · 15 JULY pulsing · 1 SEP · 12 SEP; B0 band beneath). Approved by Pranav.
- **Phases 2–4** (new files, additive architecture): `js/slides-part2/3/4.js` (SLIDES.push), `js/engine-extras.js`, `css/parts.css`. Slides: interactive **Subject Slider Board** (6 draggable markers on bucket-gradient tracks, B4 goal line at 64%, LEVEL 1 CLEARED badge when all ≥ B4, R = reset, tap-to-jump), Mission (live days-to-15-July), Roadmap TOC, North Star (21 hours, 1×/day), Boundary + 3-question filter + NOTHING ELSE stamp, **Implementation Framework + STUDENT TOOLKIT badge** (20+ tools, comment promise), 3-Layer Architecture (fixes layers-before-explained hiccup), Drive setup, Physical vs Digital (red flash), Booti intro + 3 Booti slides (gold, field-by-field; footer booti-tracker slots fill ①②③), AI (violet, memory-machine framing), Group Decision (comfort-first formula), 15 JULY deadline (LEVEL 1 CLEARED + NO NEW MATERIAL flash), Bucket 4 rules (North Star 3×/day), Layer 3 A/B/C (60/30/10), Mock Window (min 1/max 2, deadline live-computed = exam−10 = 22 AUG), Bucket 0 tick-list, CTA ("No Gyaan Baazi. ON GROUND Strategies." — Pranav's wording).
- Verified: node --check all new JS, 27 slides, all step sequences sequential, mock date computes 22 AUG. **Known sandbox issue:** the Cowork sandbox mount pins stale sizes for re-written files (slides.js etc.) → health_check run in-sandbox false-flags UTF-8 on them; files verified complete/valid on Windows side and Pranav's local health_check runs green. New-file architecture (part files) chosen partly for this reason.
- README (deck) updated: full file map, R key, wording-edit guide. Commit locally; Pranav pushes.

---

## 2026-06-11 — Sep-26 video slide deck: engine + first 3 slides

- New folder `books/strategy-book/video-presentations/sep26-strategy/` — HTML/CSS/JS deck for the Sep-26 strategy video (per `working/video-brief-sep26-strategy.md`). Multi-file: `index.html`, `css/theme.css` (B3 #E8A13D / B4 #E07A2F tokens, dark/light themes, 1920×1080 scaled stage, reveal animations), `css/slides.css`, `js/engine.js` (vanilla-JS: →/Space/click step reveals, ←, F fullscreen, H HUD), `js/slides.js` (content-as-data, edit text without touching engine), `README.md`.
- Built slides 1–3 for Pranav's look-and-feel approval: Hook ("83 days" — **live-computed** from EXAM_DATE 2026-09-01), Pain Mirror (NEW slide approved by Pranav — 4 Hinglish pain lines + closer), Positioning ("Yeh video kya NAHI hai"). 15 slides remain (18 total).
- Decisions locked with Pranav: pain-mirror slide added; days counter auto-calculated; folder location under strategy-book. **Slide 4 redesigned per Pranav**: timeline Today → 25th July → 1st Sep; first half = fix boundary + finalize 3 Bootis, second half = pure revision & practice (to build next).
- `books/strategy-book/README.md` updated (video-presentations/ in layout + file table). Verified: node --check clean, 3 slides / 12 reveal steps, days calc = 83. health_check green (46/46); file_index 91 files. Commit locally; Pranav pushes.

---

## 2026-06-10 — Staleness check + component index corrected

Checked 6 files for staleness and contradictions: CLAUDE.md (current), README.md (current), content/README.md (current), project_log.md (current), MASTER-component-index.md (stale — fixed), CA-Inter-Book-Full-Structure.md (superseded — marked archived).

**MASTER-component-index.md corrections:**
- Added `IF = IMPLEMENTATION FRAMEWORK` to key + IF column to per-section table (B0:3, B1:2, B2:6, B3:4, B4:3, B5:3, B6:1 = 22 content blocks)
- AS counts corrected: B0 6→7, B2 9→10, B3 5→6, B4 0→2, B5 2→3 (total 20→30)
- WA counts corrected: B1 2→1, B2 1→0 (total 1 WARNING at B1 S10)
- B3 tag notation corrected: "10×[ALL], 1×[RANK], 1×[ALL], 1×[RANK]" → "11×[ALL], 2×[RANK]"
- PRANAV'S TIP corrected: 4→3 (B1 S6, B1 S10, B4 S1)
- Total strategies corrected: 94→91; [ALL] 90→89; [RANK] 4→2 (B3 S11, B3 S13)

**CA-Inter-Book-Full-Structure.md:** Added ARCHIVED DRAFT header — this file diverged from MASTER.md before the 2026-06-10 normalization pass. It is reference-only; all active work is in MASTER.md.

---

## 2026-06-10 — New file: CA-Inter-90-Days-Strategy.md (website PDF mini-book)

Created `books/strategy-book/working/CA-Inter-90-Days-Strategy.md` — complete standalone 90-day strategy book for the website PDF. Parser-compatible with `tools/strategy_book_parser.py`.

Structure: Socrates Story (STRUCTURE ONLY) → About This Book (STRUCTURE ONLY) → Routing Page → First 45 Days (Strategies 1–17: boundary, Physical vs Digital, 3 Layers, 3 Sanjeevani Bootis, revision strategies) → Next 45 Days (Strategies 1–10: Layer 3 build, No New Material, mocks, error register) → Exam: The 15 Days (Strategies 1–17: kit/logistics, reading time, hall mechanics, between-papers) → Bucket 0 — The Daily Foundation (all 13 strategies, at end) → Personal Pages (Why I Am Doing CA, Dream Marksheet, Vision Board, My Boundary, My Notes) → Author's Journey + Gallery (STRUCTURE ONLY).

Key: "21 Hours Before Exam" throughout · PRANAV'S TIP components included in Physical vs Digital and Layer 2/Layer 3 strategies · cross-refs to MASTER.md noted via [REF: …] tags · parser note at end flagging new SECTION_META slugs required (FIRST 45 DAYS, NEXT 45 DAYS, EXAM: THE 15 DAYS, THE SOCRATES STORY).

health_check green (46/46); file_index 85 files.

---

## 2026-06-10 — MASTER.md: 23 Implementation Frameworks added across all 7 Buckets

Major session — comprehensive framework layer added to the Strategy Book:

- **New parser tag `IMPLEMENTATION FRAMEWORK`** added to file header (front-cover countable element).
- **About This Book** updated: added differentiator line about implementation plans for each strategy.
- **Bucket 0**: Wake Anchor Rule (sleep), 2-Minute Park Protocol (emotions + "scientifically proven" note without names), 4-Part Target Rule (daily targets).
- **Bucket 1**: Full 2-Role Rule rewrite in Pranav's plain-language style (Understanding vs Boundary); A/B/C Classification Formula (W = avg marks, ≥5=A, ≥2=B, else C) with VC Gurukul channel reference; 3-Condition Removal Rule for boundary.
- **Bucket 2**: Layer Lock Rule (zero Layer 2 during classes); 3-Question Class Filter (what to write); 25-5 Rhythm (active recall — no scientist names); 3-Item Buddy Agenda (study buddy calls); full Sanjeevani Booti 2 Error Register format (3 entry types + 5-field error format); MCQ Quota by Category (30/15/8 with VC Gurukul platform reference).
- **Bucket 3**: Compression Time Test (Layer 2 quality check); 3-Gate Revision Standard (Notes + Test + Error); Author Says on 7-subject IPCC spacing; 3-Day Triage Protocol (recovery); Action Matrix (chapter rating → action trigger).
- **Bucket 4**: 4-Type Layer 3 Filter (only 4 content types allowed); Author Says on mnemonic pairing (Audit disaster story); Layer 3 reading time updated to 30–40 min; Decision Tree (new material vs boundary gap); Mock Sequence Rule + Author Says (sister checking immediately).
- **Bucket 5**: 4-Step Reading Time Protocol (15-min sequence); MCQ-first rationale rewritten in Pranav's style + Author Says (watch on desk); Every-5 OMR cross-check; 4-Line Fallback Protocol (never leave blank); CA Inter Time Budget (1.8 min/mark table).
- **Between Papers**: COMPLETELY REWRITTEN — Pranav's 20–22 hr study approach: 2 hrs same day + 16 hrs next day + 4 hrs exam morning. Remove completed subject materials immediately after exam.
- **Bucket 6**: 3-Column Look-Back Table (honest review after exams).
- Memory saved: `project_ca_inter_basics.md` + `feedback_ca_inter_book_rules.md`.
- Total: 23 IMPLEMENTATION FRAMEWORK blocks, 30 AUTHOR SAYS blocks, 91 strategies.
- health_check green (46/46); file_index 84 files.

---

## 2026-06-10 — MASTER.md: 7 new concepts added + PRANAV'S TIP parser component

- Added **Strategy 13 — Make It a Game** to Bucket 0 (gamify concept: learning as levels, exam as Final Boss, Princess ko bachana hai).
- Added **PRANAV'S TIP for Google Drive subfolder structure** to B1 S6 (Layer 1 / Layer 2 / Layer 3 subfolders per subject).
- Added **Strategy 10 — Physical vs Digital** to Bucket 1: what must be physical (Layer 3 always physical), what is digital, WARNING for never-digital-as-primary, PRANAV'S TIP for cloud backup + YouTube Unlisted for heavy files.
- Enhanced **Error Register format** in B2 S15 with new PRANAV'S TIP block (5 specific fields: where is Q, where is solution, what was asked, where messed up, why messed up).
- Added **Strategy 18 — The Golden Nuggets Register** to Bucket 2 (distinct from Error Register; collects per-chapter: important concepts + exam tips + examiner tricks while watching revision videos).
- Added **North Star Question framing** ("21 Hours Before Exam") to Bucket 4 intro, before Strategy 1.
- Added **Layer 3 default A→B→C sequence** as PRANAV'S TIP inside B4 Strategy 1 Build Layer 3.
- Added **PRANAV'S TIP** to `COMPONENT_MARKERS` in `tools/strategy_book_parser.py` + renderer + CSS class `.pran-tip`.
- Updated `MASTER-component-index.md`: new key PT, updated strategy counts (B0:13, B1:10, B2:18), added new strategy rows.
- health_check green (46/46); file_index 83 files.

---

## 2026-06-10 — Video planning: Sep 2026 strategy video brief

- Planning discussion for a YouTube video targeting CA Inter Sep 2026 students ("exactly what to do in the next 40 days").
- Decided format: face-to-camera primary, slides only for data-heavy blocks (timelines, templates, checklists).
- Content scope: Bucket 3-to-4 transition. Core: Boundary fixation, 3-Layer material framework, three "Sanjeevani Bootis" (Golden Nuggets register, Error Register, Paste-It-Where-You-Live), AI usage for memory, post-25th-July phase. Bucket 0 compressed to 90 seconds at end. Bucket 5 deferred to separate video.
- Positioning: "Big Brother, not topper, not faculty" — no planners, no motivation, raw strategies only.
- Created `books/strategy-book/working/video-brief-sep26-strategy.md` — full run-of-show + 6 critical flags + open decisions table for Pranav.
- health_check green (46/46); file_index 83 files.

---

## 2026-06-10 — Strategy Book: md_to_html.py converter + Bucket 0 HTML output

- Built `books/strategy-book/design/templates/md_to_html.py` — state-machine line-by-line parser that converts MASTER.md → print-ready B5 HTML implementing design-spec.md visual system. Self-contained CSS (Archivo/Source Sans 3/Kalam, Google Fonts), embedded in output HTML.
- Handles all 10 component types (AUTHOR SAYS, HOW TO DO THIS, RANK ONLY, END GOAL, STARTING LATE? BARE MINIMUM, WARNING, DIAGRAM, FILL-IN, CHECKLIST — END OF BUCKET, EXAMPLE), strategy headings (number circle + title + ALL/RANK badge), non-strategy H3s, code/template blocks, checklists (`- [ ]` + ★), anonymous blockquotes, inline REF/STRUCTURE ONLY/AUTHOR TO CONFIRM tags.
- Generated `books/strategy-book/design/templates/build/bucket-0.html` (B5 Slate theme, 26KB, 564 lines). Component counts verified against MASTER-component-index: 5 Author Says, 3 HOW TO, 1 RANK ONLY, 1 DIAGRAM, 12 strategy headings. `build/` is gitignored per existing .gitignore rule.
- Known limitation: indented continuation lines of list items (e.g., `>   move on...` below a `> - list item`) are rendered as a separate `<p>` rather than joined to the list item. Text content is preserved; only visual grouping differs.
- CLI flags: `--section "BUCKET 0"`, `--section all`, `--list-sections`, `--output <path>`.
- health_check green (46/46); file_index regenerated (76 files). Commit locally; Pranav pushes.

---

## 2026-06-10 — Strategy Book MASTER: formatting normalization pass + component index

- **Normalization pass** on `books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md` (FORMATTING ONLY — zero content/wording changed). Objective: make every recurring component machine-parseable for the HTML build pipeline.
- Key changes made (counts): 20 AUTHOR SAYS → blockquotes · 12 HOW TO DO THIS → blockquotes (inline variants had text moved below marker) · 4 STARTING LATE? BARE MINIMUM → convention-compliant blockquotes · 6 END GOAL → blockquotes with `- [ ]` checkbox items (replacing □ in code blocks) · 8 RANK ONLY → blockquotes (inline ★ [RANK] within [ALL] strategies) · 2 DIAGRAM markers added (Routing Flowchart, Posture & Eye Exercise) · 5 FILL-IN markers added in Personal Pages section.
- **Heading fixes:** `# ROUTING PAGE — WHERE ARE YOU...` split into H1 + H2 · `### Priorities from today...` and `### Your Bucket 0 Daily Tick` and `### Understand this before any class strategy.` all converted to ALL-CAPS non-strategy H3 (no tag) · All Bucket 5 and Bucket 6 `**Strategy N — ...**` bold headings promoted to `### Strategy N — ...` with `---` after each · Added missing `---` after Bucket 2 Strategies 6, 7, 8.
- **Created** `books/strategy-book/working/MASTER-component-index.md` — per-section table, global summary (88 strategies total: 84 × [ALL], 4 × [RANK]), FILL-IN inventory, DIAGRAM inventory, 10 NEEDS HUMAN DECISION items, 3 UNTAGGED recurring patterns (code-fenced structured content, inline REF tags, STRUCTURE ONLY blocks).
- health_check green (46/46); file_index regenerated (74 files). Commit locally; Pranav pushes.

---

## 2026-06-10 — Strategy Book: subject-wise routing, repeat-attempt check, tick-list end-goals

- MASTER edits (`working/CA-Inter-Strategy-Book-MASTER.md`): Routing page now leads with the **subject-by-subject** principle (run buckets per subject, even for both-groups students) + a **repeat/multiple-attempt self-check** (per subject: 70%+ → Bucket 3, 50–70% → Bucket 2, <50% → fresh start Bucket 1/0).
- **All bucket "End Goals" converted to tick-lists** (□/★); folded the old separate end-of-bucket checklists in (one checklist per bucket). **Bucket 0** got a **Daily Tick** habit-tracker instead. Bucket 1 list includes a **FIXED (not new) single Gmail + phone number** for all study/digital activity.
- Bucket 0 also: "better late than never" line + Indian pure-veg budget diet examples. Voice kept to the Raj-Shamani/older-brother spec throughout.
- **Consistency pass:** reconciled `sources/summary-strategy-book-memory.md` — fixed the two stale lines (separate-closing-checklist format; "feedback-collection / no further changes" status) and appended a dated **UPDATE — current state (2026-06-10)** section cataloguing everything added across recent sessions. README is a file-manifest, still accurate (design/ entry already present). No contradictions found across the doc set.
- health_check green; file_index regenerated. Commit locally; Pranav pushes. (Sandbox git index keeps corrupting on this mount — rebuild with `git reset` before committing; one Cowork session at a time.)

## 2026-06-10 — Strategy Book design system: spec v1 locked

- Created `books/strategy-book/design/design-spec.md` — the visual design source of truth. Decisions locked by Pranav: **full-colour interior, B5 (7"×10") trim, diagram ownership decided per-diagram later, spec-only for now (no sample chapter yet)**.
- Spec covers: bucket colour system (B0 slate → B5 maroon, B6 sky, AI violet, Emergency signal-red with full red edge strip; gold reserved for RANK); **stepped right-edge bleed tabs** (9 slots → closed-book fore-edge index, Pranav's idea); footer **journey strip** ("you are here" mini-timeline on every page, B0 segment always half-filled); 2-page bucket-opener spread (End Goal + ranker line + grey Bare-Minimum box + mini-TOC); fixed component library (How to Do This checklist box = signature, Author Says in Kalam handwritten font with avatar, RANK gold border, warning strips, fill-in workbook forms); typography (Archivo/Source Sans 3/Kalam/Noto Serif Devanagari); **11-diagram Excalidraw inventory** prioritised (routing flowchart #1, 3-layer funnel #2…) — .excalidraw JSON committed, PNG exports local-only; production = HTML + paged.js → B5+bleed PDF.
- `books/strategy-book/README.md` updated (design/ in folder map + file table). health_check green (46/46, encodings clean, CLAUDE.md current); file_index 73 files. Commit locally; Pranav pushes.
- Next step when Pranav triggers build: CSS tokens + one sample section (Bucket 5 recommended) → print review → roll out.

## 2026-06-09 — Verification pass + git recovery

- Ran `tools/health_check.py` (green: 46/46 dirs, README links resolve, UTF-8/NUL clean, CLAUDE.md current) and `tools/file_index.py` (regenerated `_claude/artifacts/file-index.md`, 72 files). No structural fixes needed.
- Strategy Book confirmed fully committed on Pranav's machine (MASTER, Full-Structure, README, all sources — verified against HEAD).
- **Git incident logged for future-proofing:** two concurrent Cowork sessions/app hitting `.git` at once corrupted the index (stale `.git/index.lock`, "bad signature/index corrupt", and a sandbox view that showed the whole repo staged as deleted). No data lost — fixed by removing the lock + `git reset` to rebuild the index from HEAD. **Rule going forward: one Cowork session at a time on this repo.**

## 2026-06-09 — Strategy Book MASTER: harvested from 5 external ranker/faculty reports

- Reviewed the 5 `books/strategy-book/sources/extermal/` reports (YouTube ranker + faculty compilations). ~70% was CA Final (articleship/IBS/CFA/placement) — filtered as out-of-scope; deduped heavy repetition. Harvested 5 Inter-relevant items into `working/CA-Inter-Strategy-Book-MASTER.md`:
  - **Bucket 5 — new Strategy 1 "Your Exam Kit & Logistics"** (scout centre; TWO identical calculators; 3–4 same-brand black pens; 3–4 hall-ticket copies; stapler/scale/pencils; night-before pack; reach 1hr early; loose clothing; light meal + nimbu-paani/glucose). Renumbered Bucket 5 → 1–17. Folded submission mechanics (tick attempted-question boxes, OMR domino alignment, "1+2" supplement count, pen-cap-off, last-10-min review) into "Presentation & Submission" (Strat 11).
  - **Bucket 2** — Pause-and-Solve (Undivided-Attention, esp. recorded lectures); study-buddy fixed-call + Author Says (Teach-a-Friend → "and Keep a Study Buddy"); own-the-technical-keywords (theory mnemonics strat).
  - **Bucket 3** — Hinglish/Hindi revision notes (Build Layer 2); exam answer stays English.
- **Resolved morning-theory-vs-practical conflict** per Pranav: flipped Bucket 3 "Match Subject to Your Energy" → theory in your most productive window (morning OR night), practical sums when low/sleepy.
- **Excluded:** all CA-Final content; "lucky break" chapter-gambling; "reject notes/master from source"; rigid 12–14h & Pomodoro mandates; pure motivation/anecdote.
- health_check green; file_index 72. NOTE: project_log + summary-memory show signs of a **concurrent session/app** (a "Batch Operations" entry appeared that this session didn't write; summary-memory locked EPERM). Layer-3 fix still pending in canonical summary-memory. Commit locally; Pranav pushes.

## 2026-06-09 — Batch Operations system rebuilt + Standup Teaching philosophy doc

- Created `preparations/standup-teaching.md` — working philosophy doc for "Standup Teaching" (Pranav's named teaching style blending deep concept teaching with clean, anchored comedy). Not in books yet; flagged for future `books/about-author/` entry.
- Rebuilt `preparations/cainter-batch-operations.html` (replacing old `cainter-batch_operations_daily.html` which had a fixed daily quote+verse+insta routine). Key changes:
  - **Segment Library** (19 types): 6 Opening segments (Motivational Quote, Gita Shlok, Mahabharata/Epic Story, Personal IPCC Story, Standup Moment, Exam War Story) + 13 Mid-class segments (Insta Comedy Feed, Insta Motivation, Spiritual Reels, AI Tool Update, ICAI Updates, Financial News Brief, Mental Side of CA, CV & Career Reality, Famous CA/Finance Stories, Accounting in the News, Myth vs Reality in CA, YT Shorts Comment React, Student Doubt Discussion). Replaces the previous fixed daily routine.
  - **Week Planner tab**: Sun planning — pick Opening + Mid-class segment per day for 6 days. Saved to localStorage.
  - **Daily Ops tab**: Simplified checklist (fewer items, segment-aware). localStorage persistence per date — resets daily, survives refresh.
  - **Quote/Verse banks**: Added "Mark used" toggle per item, saved to localStorage — prevents repetition.
  - **Class structure**: Updated to 2.5 hr / 150 min flow, batch stats card (100 classes, 240 hrs, 4 months).
  - Removed: Sunday prep load for 6 separate daily items (now weekly Segment Library planning instead).
- README.md updated: preparations/ folder map expanded, "Where things are" table updated.
- Commit locally; Pranav pushes.

## 2026-06-09 — Strategy Book MASTER: harvested missing strategies + reverse-planning

- Compared MASTER vs Full-Structure vs original General-Exam-Systems; harvested everything missing into **MASTER** (the canonical working draft). All edits in `books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md`.
- **Bucket 1 restructured:** new Strategy 3 *Pick Your Anchor Book*; new Strategy 4 *Plan Backward From Exam Day* (industry hours + reverse-planning calendar for RANK and a separate PASS/exemption chart + one-group-or-two decision merged in); 3-Question Filter + Golden Rule box added to *Fix Your Boundary*. Renumbered to 1–9 (old standalone Both-Groups removed, folded into Strat 4).
- **Reverse-planning dates:** kept Pranav's round-number durations (4/21/45; 185/231/308/461) but **recomputed the calendar dates** — his table didn't tie out (second-rev start is 24-02-2027 not 17-03; Scenario A start 23-08-2026 not 28-10). PASS chart: exam-anchored back end fixed, second revision 45→39 days, classes+first-rev −30% (≈1295h) → starts 23-10-2026/21-09/29-07/12-04. **Flagged to Pranav** in case his dates used a different assumption (e.g. study-days only).
- **Other harvests:** Chapter Rating [RANK] (Exam-Relevant A/B/C + Recall + Simulation, Hinglish, Bucket 3); Paste-It-Where-You-Live (Bucket 3, GST-in-hallway Author Says); Amalgamation 5-times rule [RANK] (Bucket 3, exception only); 15-min Reading-Time strategy (Bucket 5 Strat 6, anecdote softened — dropped the 'not allowed' claim); Revision Marathons (Bucket 4); Dual-coding tip + Write-by-hand 'worse to worst' Author Says (Bucket 2); target-driven-not-hours + Pain Choice + diet (Bucket 0); AI teacher-first caution (AI Section); 'no motivation, gamified journey, warna time chala jayega' positioning (About This Book).
- **Dropped per Pranav:** Five-Year Rule, Articleship Discipline.
- **Layer 3 corrected** to one thin BOUND notebook per subject (spiral-bound A4 ok) — u
