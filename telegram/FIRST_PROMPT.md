# FIRST_PROMPT.md — Telegram Bot Platform orientation

**Give this file to any agent picking up work in `telegram/`.** It's a map, not a
manual — one line per thing, pointing at the real doc/file for depth. Keep it short;
if you're about to explain *how* something works here, that explanation belongs in
the linked doc, not in this file. **Update this file whenever you build/move/rename
something under `telegram/`** — a stale map is worse than no map.

Repo-wide rules (git root, pillars, non-negotiables) live in `/CLAUDE.md` — read that
first if you haven't. This file starts where CLAUDE.md §11 (Telegram) leaves off, as
a structured index instead of a chronological log.

**Before adding more features here**, read `/CLAUDE.md`'s "Telegram platform: known
scale-readiness gaps" callout (right after §2, added 2026-08-12) — a PM+CTO-level
review found the infra layer (single local-PC deployment, no backups, untested
SQLite concurrency, unenforced billing, long-polling, manual faculty onboarding)
still sized for ~100 students, not Pranav's 100k+ target. Fix priority matters more
than feature count until that list is worked through.

---

## Running this folder standalone (moved into a different repo)

`telegram/` is designed to be dropped into any other repo/computer as a whole folder and
just work, with zero code changes. This depends on a discipline audited repeatedly
(2026-08-12 through 2026-08-18): every script locates itself via
`Path(__file__).resolve().parents[N]`, never a hardcoded machine path, and nothing under
`telegram/` reads a file outside `telegram/` — the one historical exception,
`tools/build_exam_bot_mcq_export.py`, now prefers the live `first_run/` source when present
and falls back to a bundled snapshot (`reference-data/questions_index_snapshot.json`)
otherwise, see that script's own docstring.

**First-time setup in a new location:**
1. Create a Python 3.11+ venv and `pip install -r telegram/requirements.txt` — this file
   lives INSIDE `telegram/` (separate from the cap-online repo's own root-level
   `requirements.txt`, which also covers other pillars) specifically so it travels with
   the folder.
2. `cp telegram/.env.example telegram/.env` and fill in every real secret listed there
   (bot tokens, SMTP, Cloudflare Email + backup infra, Razorpay, Admin Portal login).
   That file is the audited, complete checklist of every env var the code actually reads
   (as of 2026-08-18) — if you add a new `os.environ.get(...)` anywhere under `telegram/`,
   add it there too in the same pass, or it silently won't travel next time.
3. `python telegram/tools/manage_bots.py start` (or `ensure-running`) to bring up every
   `active` bot in `config/bots.json`.

**What does NOT travel with a plain folder copy — redo by hand on the new machine:**
- The `.venv` itself (step 1 above recreates it).
- `telegram/database/platform.db`, `telegram/assets/myfiles_bot/`, `telegram/database/run/`
  — gitignored runtime state (real student data, live PIDs/logs). Copy manually if you
  want existing data to carry over; otherwise the platform just starts fresh.
- Windows Task Scheduler jobs + the Startup-folder autostart entry (see `CRONJOBS.md`) —
  OS-level config on the OLD machine, not part of this folder. Re-register them on the
  new machine for the same self-healing/backup/broadcast automation there.
- `tools/restart_all_bots.bat`/`tools/ensure_bots_running.bat` hardcode an absolute
  `REPO_ROOT` line BY NECESSITY — they're meant to be copied into the Startup folder,
  physically outside this repo. Update that one line after copying either script over.

---

## Read order

1. This file (map + read order).
2. `/CLAUDE.md` §11 — the full dated build history and *why* behind every decision
   below. Skim headers, read the sections relevant to your task.
3. The one feature doc that matches your task (table below).
4. The actual code, once you know which files matter.

## What exists, one line each

| Topic | Read this doc | Code lives in |
|---|---|---|
| Who owns this platform, faculty model | `/CLAUDE.md` §11 opening + `_claude/memory/1lavya-*` | — |
| Which bot processes exist, tokens, ports | `config/bots.README.md` | `config/bots.json` |
| What each faculty teaches / content scope | `config/tenants.README.md` | `config/tenants.json` |
| Shared platform DB (schema, tables, retry logic) | `database/README.md` | `database/schema.sql`, `database/db.py` |
| Study Hub bot (browse/search PDFs) | `bots/README_Bot1_StudyHub.md` | `bots/study_hub_bot.py` |
| Exam Hub bot (MCQ/descriptive practice) | `bots/README_Bot2_ExamHub.md` | `bots/exam_hub_bot.py` |
| MCQ Issue Report flow ("Report Issue in MCQ") | `bots/README_Bot2_ExamHub.md` (2026-08-13 entry) | `bots/mcq_issue_flow.py`, `mcq_issue_reports` table in `database/schema.sql` |
| MyFiles Hub bot (personal file storage, separate DB) | `bots/README_Bot3_MyFilesHub.md` | `bots/myfiles_hub_bot.py` |
| Faculty bot (single-token, composes both hubs) | `/CLAUDE.md` §11 | `bots/faculty_bot.py` |
| Student profile system (username, linked chat_ids) | `PROFILE-SYSTEM.md` | `bots/profile_flow.py` |
| 20-question report pipeline (email/PDF) | `REPORT-PIPELINE.md` | `bots/report_flow.py`, `database/report_delivery.py`, `database/cf_email.py` |
| Leaderboard system (join, nightly broadcast) | `LEADERBOARD-SYSTEM.md` | `bots/leaderboard_broadcaster.py`, `database/leaderboard_metrics.py`, `config/leaderboards.json` |
| Course/chapter/unit taxonomy + human-readable question IDs + Study/Exam/Revision/Question-Bank catalogues | `COURSE-CATALOG.md` | `tools/populate_course_catalog.py`, `tools/generate_mcq_human_ids.py`, `admin_portal/document_catalog.py` |
| Logging/observability: fine-grained activity log, correlation IDs, `bot_admin` RBAC + Activity Log viewer, log ROTATION (1GB local budget, overflow → R2), `user_activity_log` retention (180 days), failed-admin-login lockout | `LOGGING-ARCHITECTURE.md` (§9 = activity log/correlation/RBAC build, §10 = rotation, §11 = retention + login lockout) | `bots/activity_logger.py`, `admin_portal/auth.py` + `/logs/activity`, `config/admin_access.json`, `admin_portal/manage_bot_admin.py`, `database/log_rotation.py` (Layer 1), `tools/rotate_logs_to_r2.py` (Layer 2, hourly), `tools/purge_activity_log.py` (daily) — see `CRONJOBS.md` for all 3 schedules |
| Every scheduled/unattended job on this platform (Windows Task Scheduler + Startup) — the single "what runs on a timer" list | `CRONJOBS.md` | `tools/ensure_bots_running.bat`, `tools/backup_to_cloudflare.py`, `tools/rotate_logs_to_r2.py`, `tools/generate_day_end_faculty_reports.py` |
| Admin Portal (Flask, :8788) | `admin_portal/README.md` | `admin_portal/app.py` (Overview's 5th "SQL Query" tab, added 2026-08-17, is the newest addition — see next row) |
| Writing SQL against `platform.db` (schema map, verified join recipes, SQLite gotchas) + the read-only ad hoc SQL Query tab (Overview → SQL Query, filter/sort/paginate) | `_claude/skills/SKILL-telegram-sql-query.md` | `admin_portal/sql_query_tool.py` |
| Ready-to-run SQL reports for non-technical use (active students, MCQ-practice counts, top performers, contact-info coverage) — each with one clearly marked number to edit for the time window/threshold | `SQL-QUERY-COOKBOOK.md` | `admin_portal/sql_query_tool.py` |
| Down/up alerting | `/CLAUDE.md` §11 (2026-08-10 entry) | `bots/watcher_bot.py`, `config/alerts.json` |
| Live dashboard (:8787, pre-Admin-Portal) | `/CLAUDE.md` §11 | `tools/dashboard_server.py`, `database/analytics.py`, `database/dashboard_html.py` |
| 1LAVYA branding kit (colors, logo, PDF/email header-footer) | `branding/README.md` | `branding/brand_kit.py` |
| Content field-consistency validator | `/CLAUDE.md` §11 (2026-08-10 Content Health entry) | `tools/validate_content_json.py` |
| Process management (start/stop/restart/status) | `/CLAUDE.md` §11 | `tools/manage_bots.py` (+ `.bat`) |
| CA Study Hub catalog build (flat-folder PDFs → Excel) | `_claude/skills/SKILL-study-bot-catalog-pipeline.md` | `tools/scan_study_bot_source.py`, `tools/build_study_bot_catalog.py` |
| CS/CMA chapter ToC extraction + PDF splitting | `_claude/skills/SKILL-cs-cma-toc-pipeline.md` | `tools/scan_cs_cma_toc.py`, `tools/build_cs_cma_catalog.py`, `tools/split_cs_cma_pdfs.py` |
| Faculty MCQ docx → JSON conversion (deterministic, zero-AI) | `config/FACULTY-MCQ-TEMPLATE.md` | `tools/convert_faculty_mcq_docx.py`, `tools/merge_faculty_mcq_sources.py` |
| MCQ JSON creation prompt for external AI models (PDF → MCQ JSON) | `base_formats/MCQ_PROMPT.md` | `base_formats/generate_base_formats.py` (field-contract source), `tools/ingest_ca_foundation_accounting_economics_mcqs.py` (the ingestion pattern any resulting batch still needs) |
| Question Bank Book (PYQ/MTP/RTP → chapter books, separate from this bot platform) | `_claude/skills/SKILL-question-bank-pipeline-overview.md` | `first_run/` (repo root, not under `telegram/`) |
| Test Mode (paid, timed mock tests) + wallet/billing (identity, credits, Razorpay recharge) | `/TELEGRAM-TEST-MODE-SYSTEM.md` (repo root — canonical; `assets/exam_bot/Tests/TEST-MODE-ROADMAP.md` is supplementary) | `bots/test_flow.py`, `bots/wallet_flow.py`, `database/wallet.py`, `database/identity.py`, `database/razorpay_client.py` |

## Folder map

| Folder | Contents |
|---|---|
| `bots/` | All bot process scripts + their READMEs, shared flow modules (`profile_flow.py`, `report_flow.py`, `contact_utils.py`), and their smoke tests |
| `database/` | Shared `platform.db` schema/access layer, analytics queries, email client, report/leaderboard logic. `database/run/` = live PID files + `logs/` (gitignored) |
| `admin_portal/` | Flask app — the ops/analytics UI at `:8788` |
| `branding/` | Logo assets + derived brand kit (colors, PNG cutout, thumbnails) used by PDFs/emails/dashboards |
| `config/` | The JSON "source of truth" files (`tenants.json`, `bots.json`, `leaderboards.json`, `alerts.json`) + a README per file |
| `tools/` | One-off/batch scripts: catalog builders, converters, the validator, process manager, dashboard generator. Not long-running processes (those are in `bots/`) |
| `assets/study_bot/{Study Materials,Exam Materials,Revision Material}/` | The actual PDFs Study Hub serves — flat, generated, course-agnostic |
| `assets/exam_bot/` | MCQ/descriptive JSON content the Exam Hub bot reads (1LAVYA shared pool + `faculty/` subfolder per tenant) |
| `assets/faculty/` | Per-faculty raw MCQ/descriptive content, one subfolder per `bot_id`-ish tenant slug |
| `assets/myfiles_bot/` | MyFiles Hub's own storage area |
| `assets/backup pdfs/` | Pre-restructuring backup, not read by anything live |
| `source-docs/` | Generated Excel catalogs (`StudyHub_Master_Catalog.xlsx` is what Study Hub actually loads) |
| `reference-data/` | Bundled snapshots of canonical data owned by OTHER cap-online pillars (e.g. the CA Inter Adv Acc topic index, the Question Bank Book's `questions_index.json`) — exist purely so scripts under `telegram/` still run once this folder is detached from the rest of cap-online. See each file's own `.README.md`/`_snapshot_note` for provenance and how to refresh it; these go stale on their own, never auto-update |
| `requirements.txt` | This folder's OWN pinned dependency list (added 2026-08-18) — separate from the cap-online repo's root-level one, specifically so it travels with `telegram/` on its own |
| `.gitignore` | This folder's OWN ignore rules (added 2026-08-18, mirrors the cap-online root `.gitignore`'s telegram-relevant entries) — so `telegram/` is safe to `git add .` inside any repo it's copied into, not just this one |
| `*.env`, `*.env.example`, `creds.txt` | Secrets — gitignored, never commit. `.env.example` is the audited checklist of every real env var the code reads |

## How to inform your own working memory (i.e. don't re-derive what's already known)

- **Don't re-investigate settled architecture.** Every JSON-is-source-of-truth
  decision (`tenants.json`, `bots.json`, `leaderboards.json`, `course_catalog` DB
  table) was deliberate — read the linked README before proposing a different shape.
- **Don't re-litigate locked scope decisions** without asking Pranav: OP/PP duplicate
  detection is out of scope for this edition; Question Catalog editing is
  metadata-only; billing/wallet is schema-only, not wired into any bot flow.
  Full list of open/deferred items: `/CLAUDE.md` §11, each doc's own "not built yet"
  section.
- **Verify structurally AND visually before trusting a fix.** This session's repeated
  lesson: 0 structural errors ≠ correct output. Screenshot dashboards/PDFs, don't
  just parse-check them. See `/CLAUDE.md` §7 and the branding/course-catalog entries
  in §11 for real examples of bugs that only a rendered check caught.
- **Never assume one data source shares one structural convention** (e.g. "every
  StudyHub subject is single-unit") — test against every real row first. The
  course-catalog duplicate-key check exists specifically to catch this class of bug.
- **Ask before assuming on high-stakes/foundational changes** (per Pranav's standing
  instruction) — anything touching live bot behavior, question identity, or
  outward-facing broadcasts (leaderboard channels, emails) warrants a clarifying
  question if genuinely ambiguous, not a guess.

## Status snapshot (update this, don't let it rot)

As of 2026-08-13 (bot-process list/counts stale beyond this date -- see
`/CLAUDE.md` §11's own dated entries for everything since, incl. wallet/
Test Mode billing, multi-course profiles, and the 2026-08-17 logging build
below, for the current real picture): all 9 real bot/service processes
running (`1lavya-studyhub`, `1lavya-examhub`, `1lavya-myfileshub`,
`csarunchouhan`, `capranav-study`, `capranav-exam`, `1lavya-dashboard`,
`1lavya-platform-watcher`, `1lavya-admin-portal`). Content validator: 0
errors/0 warnings platform-wide. `course_catalog`: 975 rows, all CA/CS/CMA
subjects with real content covered. Leaderboards: 3 configured, all
`status: "inactive"` pending real Telegram channel IDs. Admin Portal:
Foundation + Analytics tiers built (6 Analytics views as of 2026-08-13,
incl. MCQ Issue Reports); Masters editing, Faculty/Bot addition, Leaderboard
edits, and Question Catalog content editing still not built. **RBAC
correction (2026-08-17): a real second role, `bot_admin`, now exists** --
scoped to `/logs/activity` only, for exactly one `bot_id` at a time, see
`LOGGING-ARCHITECTURE.md` §9. Full portal-wide RBAC (per-module roles
beyond this one page) is still not built.

**Exam Hub (`bots/exam_hub_bot.py`) flow, current as of 2026-08-13**: Mode →
Course → Level → Subject → Exam Type → Year → Chapter → question, every step
auto-skipped when only one real option exists, every option list derived
live from real loaded content (never a hand-maintained list). Every
question shows its `human_id` (globally unique, student-facing — see
COURSE-CATALOG.md) on-screen. A **standing rule** governs content going
forward: every question on the platform — MCQ or descriptive, 1LAVYA-
authored or faculty-sourced — joins the flagship `1lavya-examhub` bot's
pool; a faculty's own bot stays separately scoped via `content_scope`;
provenance is tracked via `_content_owner` (inferred from each source
file's path), never via withholding content. MCQ answer screens have a
4th "Report Issue in MCQ" button (`bots/mcq_issue_flow.py`,
`mcq_issue_reports` table, its own Admin Portal page) and "I'm Done" shows
a real today's-summary before offering the existing report-email flow.

**Read `/CLAUDE.md` §11's last 4 dated entries (2026-08-12/13) for the full
narrative** behind all of the above — two real production bugs found via
live logs and fixed (`Button_data_invalid` from an over-long
`callback_data`, a silent `KeyError` from a stale post-restart session),
the Mode-first rewrite and why, the chapter-label duplication bug and fix,
and the standing content-ownership rule. This file intentionally does not
duplicate that narrative — see the "Read order" note at the top of this
file for why, and keep this snapshot itself short on every future update
rather than letting it grow back into a log.
