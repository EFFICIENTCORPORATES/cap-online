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
| Logging/observability architecture (fine-grained activity log + correlation IDs) | `LOGGING-ARCHITECTURE.md` | **Design doc only, 2026-08-17 — not yet implemented.** Read before building any of it; has the evaluation, the decorator design, and the phased roadmap |
| Admin Portal (Flask, :8788) | `admin_portal/README.md` | `admin_portal/app.py` (Analytics > "MCQ Issue Reports" is the newest tab, 2026-08-13) |
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
| `*.env`, `*.env.example`, `creds.txt` | Secrets — gitignored, never commit |

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

As of 2026-08-13: all 9 real bot/service processes running
(`1lavya-studyhub`, `1lavya-examhub`, `1lavya-myfileshub`, `csarunchouhan`,
`capranav-study`, `capranav-exam`, `1lavya-dashboard`, `1lavya-platform-watcher`,
`1lavya-admin-portal`). Content validator: 0 errors/0 warnings platform-wide.
`course_catalog`: 975 rows, all CA/CS/CMA subjects with real content covered.
Leaderboards: 3 configured, all `status: "inactive"` pending real Telegram
channel IDs. Admin Portal: Foundation + Analytics tiers built (6 Analytics
views as of 2026-08-13, incl. MCQ Issue Reports); Masters editing, Faculty/Bot
addition, Leaderboard edits, Question Catalog content editing, and RBAC not
yet built.

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
