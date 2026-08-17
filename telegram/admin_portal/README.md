# 1LAVYA Admin Portal

**Phase 4** of the platform roadmap: Branding Kit → Report Pipeline →
Leaderboard → **Admin Portal**. Built in tiers, each smoke-tested and
handed off for Pranav's confirmation before the next — this file tracks
what's actually live vs. still coming.

**Live at:** `http://127.0.0.1:8788/` (runs as the `1lavya-admin-portal`
managed process — `python telegram/tools/manage_bots.py status` shows it
alongside every bot). Login credentials are in `telegram/.env`'s
`ADMIN_PORTAL_*` vars — rotate any time with `set_password.py`.

## Why it runs alongside the old dashboard, not replacing it

`telegram/tools/dashboard_server.py` (port 8787, stdlib `http.server`)
keeps running exactly as before. Its Analytics content (Student Master,
Faculty Report, Content Health, Bot-wise Usage, Message Volume) is the
**working, live source** for that data until this app's own Analytics tab
is built and can absorb it. The two will run side by side through the
whole Phase 4 build — nothing Pranav currently relies on breaks
mid-transition. Once every module here has a home, the old dashboard
retires.

## Foundation tier — built 2026-08-11, this is what's live

Pranav's confirmed build order: *"Flask migration + sidebar shell + login
+ Bot Status/Restart + Bot-wise Logs first... then Analytics tabs... then
Masters... then Leaderboard/Catalog edits last."* This is that first
tier.

- **Flask app** (`app.py`) with a proper sidebar shell (`templates/base.html`,
  `static/style.css`) — sections for every module on Pranav's full list
  (Analytics, Masters, Content, Leaderboards, Users & Access), with
  not-yet-built ones rendering as grayed "Soon" items rather than being
  invisible — communicates the full intended shape of the portal even
  before every module exists.
- **Single-admin login** (`auth.py`) — Pranav's confirmed choice over
  no-auth-for-now, specifically so RBAC (his own "later on" ask: module-wise
  access for students/faculty/managers) extends this same session system
  later rather than replacing a no-auth system under time pressure. Every
  route is wrapped in `role_required("admin")`, not a bare login check —
  adding a second role later is a decorator-argument change per route, not
  a redesign.
- **Bot Status & Restart** (`/bots`) — live process state (real OS process
  + heartbeat freshness, the same signal `manage_bots.py status` uses),
  with a Restart button per bot. Restart calls `manage_bots.py`'s own
  `restart_bot()` function **directly** (imported, not subprocessed) — the
  exact same code path `python manage_bots.py restart <id>` already uses
  from a terminal, so the button can never drift from that script's real
  behavior.
- **Explicit confirm on every destructive action** (Pranav's confirmed
  choice) — a shared JS modal (`base.html`) used by Restart today, reused
  by every future destructive action (Masters edits, Faculty/Bot addition,
  Leaderboard edits) without rebuilding the pattern each time.
- **Bot-wise Logs** (`/bots/<id>/logs`) — tails the real log file
  `manage_bots.py` itself writes to, no new logging path.
- **Audit trail** (`admin_actions` table, `audit.py`) — every real action
  (bot restart today; masters edits/faculty addition/etc. in later phases)
  logs who did what, when. Same "complete trail" discipline already
  established for `report_flow_events`/`leaderboard_broadcast_log`.

## Verified (2026-08-11)

- All new Python files parse clean; `bots.json`/`leaderboards.json` valid JSON.
- `admin_actions` table confirmed created via the real schema migration.
- **Real restart tested manually** against a real bot (`1lavya-platform-watcher`):
  confirmed actual PID change, actual stop→start sequence through
  `manage_bots.py`'s real code, a correct audit-log row, and — separately —
  confirmed an **unauthenticated** restart attempt is blocked (302 redirect
  to login, no process touched, no audit row created).
- **A real bug found and fixed during this verification**: `dict.items` in
  the `NAV_SECTIONS` structure collided with Python's own built-in
  `dict.items()` method — Jinja2's `section.items` attribute lookup found
  the *method*, not the dict key, causing a 500 on every page. Renamed the
  key to `links`. A second, unrelated issue (two stale dev-server processes
  left listening on the same port from an earlier manual test, `pkill`
  silently failing to find them on Windows) was found and cleared by PID
  directly via PowerShell — not a code bug, a leftover-process artifact of
  manual testing, but worth knowing `pkill -f` isn't reliable in this
  environment for future debugging.
- `smoke_test_admin_portal.py`: **26/26 passed** via Flask's `test_client()`
  (no real network socket) — unauthenticated access blocked on every
  protected route, wrong-password rejection, session correctness after
  login/logout, real bot_ids rendered on the Bots page, unknown-bot_id
  restart handled without crashing, a **mocked** real-bot restart (proves
  the route→audit-log wiring without touching a real process on every
  test run — the real path was already proven by the manual test above),
  and the logs route for both a real and unknown bot_id.
- **Visually verified** via headless-Edge screenshots (login page, Overview,
  Bot Status table with all 9 other bots' real live data) — this repo's
  own established discipline of never trusting a layout by reading code
  alone.

## Analytics tier — built 2026-08-11, same day as the foundation tier

Pranav's follow-up ask, same day: universal table export (any DB table to
JSON/CSV/XLSX), admin-triggered performance-report emails to one or many
students, full Student Master visibility, and pagination/filtering/export
on every tabular view including CSV/HTML/PDF snapshots of any analytics
dashboard. Asked 4 clarifying questions before building (report-sending
scope, recipient-email source, table-export scoping, build pace) — all
answered with the recommended option.

**Shared infrastructure** (`exporters.py`) every analytics view and the
generic table-export page both build on:
- `filter_rows()` / `paginate()` — in-memory free-text filter + pagination
  over a list of dicts (deliberate: every `analytics.py` function already
  returns its full result set cheaply at this platform's real data
  volumes — reusing those already-tested functions unchanged is
  lower-risk than rewriting each as a paginated SQL query).
- `csv_response()` / `xlsx_response()` / `json_response()` — tabular export,
  reused by both the generic Data Export page and every curated Analytics
  view (which exports exactly what's currently filtered, not the raw table).
- `render_printable_table()` / `html_export_response()` /
  `pdf_export_response()` — ONE branded HTML snapshot source reused for
  both the "download as HTML" button (served as-is) and "download as PDF"
  (the same HTML through `xhtml2pdf`) — never two content copies that
  could drift apart.
- `page_url()` / `clear_filter_url()` (Jinja globals in `app.py`) —
  preserve every other query arg (filter text, bot_id selection, etc.)
  across a page change or filter clear.

**Data Export** (`/export`) — every real table in `platform.db`, JSON/CSV/
Excel, no scoping (Pranav's confirmed choice — single-admin login is the
only gate today; RBAC later can scope this per-role without a redesign).

**Analytics** (6 views, all paginated/filterable/exportable):
- **Student Master** (`/analytics/students`) — full visibility into every
  known student (contact info, faculty, courses, from real activity).
  Checkbox-select one or many students + **Send Report to Selected** —
  emails each their own existing performance report, but **only** to a
  student's already echo-confirmed email on file (Pranav's confirmed
  choice — never guessed/typed in for them); students with none show
  clearly and are skipped, never silently dropped. Sent from the admin
  portal's own dedicated address (`reports@1lavya.com`) — an honest label,
  not impersonating whichever bot the student happens to use, since this
  send is admin-triggered.
- **Bot-wise Usage** (`/analytics/bots`) — all-time totals per bot.
- **Faculty Report** (`/analytics/faculty-report`) — student-wise MCQ
  engagement for one bot, with a per-student **chapter drill-down**
  sub-page (a real page, not an inline JS-expand row, so it reuses the
  same pagination/export primitives as everything else).
- **Content Health** (`/analytics/content-health`) — every content-JSON
  issue, flattened to one row per issue.
- **Email Analytics** (`/analytics/email`) — the full `report_deliveries`
  trail, bot-triggered and admin-triggered sends together in one view.

## MCQ Issue Reports — added 2026-08-13

**`/analytics/issue-reports`** — every "Report Issue in MCQ" submission
(`telegram/bots/mcq_issue_flow.py`) across every bot, joined to `students`
for a display name: category, the student's own free-text description,
and the exact question by its `human_id`. Same paginated/filterable/
exportable shape as every other Analytics view above, built on the same
`exporters.py` primitives. **Read-only** — no status-editing UI (marking
a report resolved/dismissed) — not asked for; the generic "Data Export"
page and direct SQL against `mcq_issue_reports` already cover that if
needed before a dedicated triage view is built. Verified with a synthetic
row through Flask's real `test_client()` (login, render, all 4 export
formats, confirmed cleanup), then added as a permanent step in
`smoke_test_admin_portal.py` — full suite re-run clean, **110 checks,
0 failures**.

## Overview rebuild — 2026-08-13

Pranav asked for the Overview page (previously a 3-tile placeholder — see
the "Foundation tier" section above) to become a real executive dashboard:
student onboarding trends, new-content growth, top performers, time
spent, questions attempted, and a faculty roster, all date-ranged,
filterable, and exportable (CSV/Excel/HTML/PDF, charts included),
sub-tab organized. Confirmed 4 clarifying decisions via AskUserQuestion
before building (all his recommended options): **Overview is a summary
layer** — charts + top-line tables per sub-tab, linking into the
already-built detailed Analytics pages (Student Master, Course Catalog,
Faculty Report) for full row-level drill-down, not a duplicate of those
pages; **"New Questions Added" tracks forward from today only** — no
historical ingestion-date data exists anywhere in the platform (content
files never carried an "added on" timestamp), so a new
`content_ingestion_log` DB table (`schema.sql`) starts the trail
2026-08-13 rather than attempting an approximate git-history backfill;
**charts are self-built inline SVG**, no new JS charting dependency,
consistent with this repo's "self-contained, no CDN" practice; **"Top
Performing Students" reuses the exact leaderboard definition** already
live for students (accuracy % with a minimum-attempts floor,
`leaderboard_metrics.py`), not a new ranking invented for this view.

**4 sub-tabs** (`/?tab=students|content|performance|faculty`), a shared
date-range picker (7d/30d/90d/all-time presets + an explicit from/to,
`_date_range_from_args()` in `app.py`) reused across every date-ranged
tab:

- **Students** — new-signup count + trend chart (`students.first_seen_at`),
  daily breakdown table, links to the full Student Master.
- **Content** — total/new questions, subjects-with-content and
  chapters-covered counts (`document_catalog.platform_question_totals()`),
  a daily new-questions chart, an MCQ-vs-Descriptive donut, a subject-wise
  summary table, and the raw `content_ingestion_log` rows for the range —
  with an explicit on-page note that tracking only starts 2026-08-13, not
  hidden as if the number were complete history.
- **Performance** — questions-attempted trend + accuracy, a by-course
  breakdown, **time spent today platform-wide and per-bot**
  (`analytics.fetch_time_spent_today()`, reusing
  `student_analytics`'s existing capped shown→answered gap metric rather
  than inventing a third "time on bot" definition), and the Top
  Performing Students table (course/level/min-attempts filters).
- **Faculty** — onboarding-fee status, content scope, linked bot(s), and
  **questions genuinely contributed** by each faculty
  (`analytics.fetch_faculty_roster()`) — counted ONLY from files under
  that faculty's own `faculty/<tenant_id>/` path (same convention
  `exam_hub_bot.py`'s `_infer_content_owner()` uses), never from a
  shared/flagship file a faculty's tenant entry also references. Verified
  against real data before trusting it: `capranav`'s own `exam_content`
  still points at the flagship's shared Advanced Accounting bank, and
  correctly shows **0 contributed** (matches `own_content.status ==
  "not_ingested"`), while `csarunchouhan` correctly shows his real
  1,025 MCQ + 47 descriptive.

**Charts**: `telegram/admin_portal/charts.py` (inline SVG bar/donut,
on-screen + "download as HTML") and `telegram/admin_portal/charts_pdf.py`
(a **separate** code path using reportlab's own native chart flowables —
`VerticalBarChart`/`Pie` — for PDF export). Found and worked around before
shipping, not after: `xhtml2pdf` (the HTML→PDF engine every table export
already uses) has no reliable inline-`<svg>` support, so routing the SVG
charts through it would have silently produced a blank/broken PDF chart.
reportlab is already a hard dependency of this project (`xhtml2pdf` is
built on it; also used directly by `generate_base_formats.py`), so this
added no new dependency. Verified visually, not just structurally — both
a bar and a pie PDF chart were rendered and read directly via Claude's own
PDF-viewing capability before being trusted.

**New DB table**: `content_ingestion_log` (`schema.sql`) — one row per
content batch wired into a tenant's `exam_content`, not one per question.
Backfilled with 7 real rows for the same-day Cost & Management Accounting
wiring (700 MCQs, Ch3–Ch9) as its first real data, honestly labeled as a
backfill in the row's own `note`, not invented history.

**Verified**: `smoke_test_admin_portal.py` grew from 110 to **182
checks** — every tab renders with no unrendered Jinja, every preset/filter
combination, all 16 table-export format×tab combinations (content-type
checked, not just status code), all 10 chart-export combinations (5
charts × html/pdf) with a non-trivial byte-size check, an unknown
chart_id and an unsupported format both 404 instead of crashing, a
data-correctness spot check (the Content tab's on-page total matches
`fetch_content_growth()`'s own return value, not a second hand-typed
number), and full auth-gating coverage for every new route. **Visually
verified** via headless-Edge screenshots of all 4 tabs against real live
data (a throwaway auth-bypassed diagnostic instance on a different port,
never the real deployed process) before deploying. `smoke_test_course_
catalog.py` and `validate_content_json.py` both re-run clean afterward —
no regression. All other bot processes' PIDs confirmed unchanged;
`1lavya-admin-portal` restarted once, clean startup, 0 tracebacks.

**Known limitation, named honestly**: `fetch_faculty_roster()`'s
`unique_users_approx` column is a naive per-bot sum across a faculty's
linked bots, not a cross-bot deduplication (same distinction
`fetch_unique_mcq_attempters()`'s own docstring already documents for the
platform-wide number) — a student using both of a faculty's bots would be
counted twice there. Not fixed in this pass; the column name says
"approx" rather than silently implying precision.

## Verified (2026-08-11, Analytics tier)

- `smoke_test_admin_portal.py`: grew from 26 to **68 checks**, all
  passing — every new route's auth gating, the generic table-export
  endpoint (including a rejected unsupported format and an unknown-table
  404), Student Master's filter/pagination/all-4-export-formats, the bulk
  report-send (mocked `send_report_email()`, verified called exactly
  once — only for the student WITH a confirmed email, with the correct
  admin-portal `bot_id` and the correct real email address, correctly
  skipping the student without one, correct flash message, correct audit
  row), Bot-wise Usage, Faculty Report + its bot-selector + chapter
  drill-down (including a 400 when `bot_id` is missing from an export
  call and a 404 for an unknown student), and Content Health/Email
  Analytics.
- Every test-inserted `report_deliveries`/`admin_actions` row is
  precisely identified (by `delivery_id` captured before/after, not a
  guessed string match) and removed in a `finally` block — confirmed zero
  residue after a real run.
- **Visually verified** via headless-Edge screenshots of Student Master
  (real 65-row live data, disabled checkboxes for emailless students,
  filter/export toolbar) and Data Export (every real table with its real
  row count).
- `health_check.py`: same 16 pre-existing failures, nothing new.

## Faculty Comprehensive Report — added 2026-08-14

Pranav's ask: a faculty who's onboarded should get one comprehensive, any-
date-range report — which subjects/levels are live for them and how many
MCQ/Descriptive questions exist, which chapters are most accessed/
practiced (attempts, correct, time spent), student-wise performance, a
fixed last-7-days student-wise trend, which chapters each student
practices most, and a question-wise difficulty analysis (which MCQs are
most often answered wrong, and what students chose instead of the right
answer) — downloadable as PDF/XLSX/HTML and emailable straight to the
faculty. **Fully deterministic, no commentary** — every section is a
plain table of raw counts read from the platform activity logs, exactly
as asked.

Distinct from the existing **Analytics → Faculty Report** page
(`analytics_faculty_report`, one bot at a time, student list + a chapter
drill-down sub-page) — that page is unchanged. This is the new, bigger
**Analytics → Faculty Comprehensive Report** (`/reports/faculty`),
scoped to a whole **tenant** (a faculty can have more than one bot — e.g.
CA Pranav's `capranav-study` + `capranav-exam` — this report pools
activity across every bot linked to that tenant, not one bot's slice).

**New module, `telegram/admin_portal/faculty_report.py`** — the query +
render + email layer, six sections:

1. `content_availability()` — per (course, level, subject) in the
   tenant's `content_scope`: chapters with content vs. total, MCQ count,
   Descriptive count. A **static** snapshot (not date-ranged — "how many
   questions exist" isn't a time-boxed fact) — reuses
   `document_catalog.question_bank_rows()`, the same human_id-derived,
   100%-accurate-by-construction counter the Course Catalog page already
   uses, not a second counting method.
2. `chapter_stats()` — per chapter, across every subject/course the
   tenant's exam-hub bot(s) serve: unique students, MCQ shown/answered/
   correct/accuracy, time spent (minutes, capped per-question at the same
   30-minute ceiling `student_analytics.py` already uses so one abandoned
   question can't blow up the total), Descriptive views. Sorted most-
   practiced first.
3. `student_performance()` — the same metrics, per student (chat ID),
   sorted most-active first, with a last-active timestamp.
4. `student_last7days()` — per (student, day) for the real last 7 UTC
   calendar days — a **fixed** window, deliberately independent of
   whatever custom date range the report itself is set to (this section
   answers "how are things going right now," not a slice of an arbitrary
   range).
5. `student_chapter_matrix()` — one row per (student, chapter) they've
   touched, ranked **within that student's own activity** (rank 1 = their
   own most-practiced chapter) — "which student is doing which chapters
   the most."
6. `question_difficulty()` — per MCQ: times answered, times wrong, wrong
   %, the correct option, and the single **most commonly chosen wrong
   option** (not just "wrong" in general) with its count. Filtered to
   questions with ≥2 real recorded answers so one fluke wrong guess can't
   show as "100% wrong."

`build_report()` assembles all six into one dict; `render_full_report_
html()` renders it as one branded, table-based document (same
`brand_kit.py` header/footer, same xhtml2pdf-safe inline-style markup
every other export in this portal uses); `build_report_pdf()` (xhtml2pdf)
and `build_report_xlsx()` (one `openpyxl` sheet per section) both build on
that same section list, so the three formats can't drift apart.
`send_report_email()` sends the PDF via the same Cloudflare Email Service
backend `report_delivery.py` already uses, from the Admin Portal's own
dedicated address (`1lavya-admin-portal`'s `from_email`, an honest label
since this is an admin-triggered send, not a bot-triggered one). New
`faculty_report_deliveries` table (`schema.sql`) logs every download and
email attempt — same audit-trail discipline as `report_deliveries`.

**New `contact_email` field** on faculty tenants in `tenants.json` (null
today — no real address on file for either Pranav or Arun yet) — the
report page's email box pre-fills from it when set, but the admin can
always type a different address in at send time; it's a convenience
default, never a requirement.

**Routes** (`app.py`): `GET /reports/faculty` (tenant picker + date-range
picker + all 6 sections on-screen), `GET /reports/faculty/<tenant_id>.
{pdf,xlsx,html}` (the same downloadable formats), `POST /reports/faculty/
<tenant_id>/email`. New sidebar entry, **Analytics → Faculty
Comprehensive Report**.

**Real bug found and fixed before this shipped** (not by inspection —
running the real query layer against the real DB straight after writing
it): `student_performance()`'s "last active" tracker started every
student at `None` and tried `max()` across a mix of `None` and real ISO
timestamp strings — Python can't compare `str` and `NoneType`, so the
very first real call crashed. Fixed by filtering `None` out before
`max()`, then re-verified against all 4 real tenants (`capranav`,
`csarunchouhan`, `1lavya-examhub`, `1lavya-studyhub`) with real data —
every section returns real, non-crashing rows (`1lavya-studyhub`
correctly returns all-empty activity sections, since it's a study-only
bot with no exam-hub data — an honest empty state, not a bug).

**Verified**: `smoke_test_admin_portal.py` grew from 182 to **205
checks**, all passing — the report page and all 3 downloadable formats for a real
tenant, an unsupported format 400s, an unknown `tenant_id` 404s, invalid-
email rejection, a successful (mocked `send_report_email()`) send logging
a `'sent'` row with the exact typed address, a failed (mocked, forced
exception) send logging a `'failed'` row with the error detail and
flashing without crashing, and full auth-gating on every new route.
`health_check.py`: same 16 pre-existing failures, nothing new.
`1lavya-admin-portal` restarted, confirmed live on port 8788 with a clean
startup log (0 tracebacks) immediately after.

**Known limitation, named honestly**: `chapter_stats()`/`student_
performance()`/etc. group by `chapter_slug`/`telegram_user_id` directly
from `exam_hub_mcq_attempts`/`exam_hub_descriptive_events` — they don't
separately break activity out by *subject* the way `content_availability()`
does, since those tables don't carry a subject column per row (only
`course`/`level`/`chapter_slug`/`chapter_label`). For every tenant live
today this is unambiguous in practice (each tenant's chapters map to
exactly one subject), but a future faculty teaching two subjects that
happen to share a chapter label could see them merged in sections 2–6.
Not fixed speculatively — flagged for whenever that first becomes a real
case, same "don't build for a case that doesn't exist yet" discipline
this repo already follows elsewhere.

## Faculty Master DB table + Masters > Faculty Details — added 2026-08-14

Pranav asked directly: "maintain a faculty table where we can store the
details of the faculty... should we have this in a JSON file or should we
keep this inside a table in db?" — confirmed via AskUserQuestion: **DB
table**, not JSON.

**New `faculty_master` table** (`schema.sql`) — administrative/contact
details only: `contact_email`, `contact_phone`, free-text `notes`.
Deliberately does NOT duplicate anything `tenants.json` already owns —
`content_scope`/`own_content`/`exam_content`/`kind` stay there
unchanged (the bot scripts read that file directly at process startup,
moving them would mean rewriting every bot's content-loading code for no
benefit here), and `onboarding_fee` (amount/paid/paid_at) also stays
there unchanged (already read by `fetch_faculty_roster()` — a second copy
here would just be a dual-source-of-truth risk). This table is purely the
*new* administrative layer, one row per `tenant_id` (matched by
convention against `tenants.json`'s own `tenant_id`, not a real SQL
foreign key), upserted (never duplicated) on every save.

**New module** `telegram/admin_portal/faculty_master.py` —
`list_faculty_master()` (every tenant from `tenants.json`, left-joined to
its `faculty_master` row if any, plus `onboarding_fee` shown read-only
alongside for one coherent view), `get_faculty_master()`,
`upsert_faculty_master()`.

**New page**: **Masters → Faculty Details** (`/masters/faculty`, list +
per-tenant edit form at `/masters/faculty/<tenant_id>`) — every save is
audit-logged (`admin_actions`) like every other write in this portal. The
existing stub **Faculty / New Bot** nav item stays disabled — that's the
bigger, still-unbuilt "generate a new tenant/bot's config" scope, a
different thing from editing an existing faculty's contact details.

**Faculty Comprehensive Report's email box now pre-fills from this
table** (`faculty_report.list_reportable_tenants()`/`build_report()`
both updated to read `contact_email` from `faculty_master`, not
`tenants.json`) — save a faculty's email once here, and it's pre-filled
on the report page every time after.

**Verified**: `smoke_test_admin_portal.py` grew from 205 to **220
checks** — the list/edit pages, create-then-update (proves the upsert
never duplicates a row, `tenant_id` being the primary key), an unknown
`tenant_id` 404s, an empty field on save correctly clears that column,
the report page's email box reflects a freshly-saved address, and full
auth-gating. **The test carefully preserves and restores whatever real
row already exists for the tenant it exercises** (captured before, written
back after) rather than blindly overwriting-then-deleting — this route
can hold real admin-entered data by the time the test runs again, and a
naive test would have silently destroyed it. `health_check.py`: same 16
pre-existing failures, nothing new. `1lavya-admin-portal` restarted,
confirmed live with a clean startup log.

**Real mid-build issue caught and fixed**: because the live Admin Portal
process re-runs `init_schema()` (a `CREATE TABLE IF NOT EXISTS ...`
`executescript()`) on every single request, a request against the live
process landed *between* this table's first draft (with two now-removed
fee-status columns) and the trimmed final version — creating the real
`faculty_master` table with the wrong (draft) columns before the schema
file had settled. `CREATE TABLE IF NOT EXISTS` doesn't retroactively fix
an already-created table's columns, so the live DB briefly disagreed with
the (correct) file on disk. Caught by inspecting `PRAGMA table_info`
before trusting it, confirmed zero rows existed yet (nothing real to
lose), fixed with a `DROP TABLE` + re-`init_schema()` — worth remembering
for any future same-session schema edit while `1lavya-admin-portal` (or
any bot) is left running: a table's *shape* isn't safely re-editable
after its very first creation without an explicit migration, only new
tables/rows are "free."

## Backup Snapshot Summary (on Bot Status page) — added 2026-08-16

Pranav asked for the entire off-machine backup pipeline's status to be
visible under `/bots`, alongside bot process status — both answer the
same underlying question ("is the platform actually safe right now"). See
`telegram/tools/backup_to_cloudflare.py`'s own docstring and
`telegram/database/README.md`'s "Off-machine backup" section for the full
pipeline (nightly R2 + D1 backup, Windows Task Scheduler-driven).

**New `backup_runs` table** (`schema.sql`) — one row per backup run,
inserted as `'running'` when the script starts, finalized (`'success'`/
`'failed'`, every phase's real metrics, which phase(s) failed and why) at
the end. **Deliberately a DB table, not log-parsing or a live R2/D1 call
on every page load** — the same "one fast local query" pattern every
other audit table in this schema already follows (`admin_actions`,
`report_deliveries`, `leaderboard_broadcast_log`, ...), and the only way
to show a summary instantly rather than re-enumerating ~1,900 R2 objects
or making 30+ D1 API calls on every single page visit.

**New `telegram/admin_portal/backup_status.py`** — `fetch_backup_summary()`
returns the latest run (headline card) + last 10 runs (trend table).
Wired into the existing `/bots` route/template as a new "Backup Snapshot
Summary" card below the bots table: last-run status pill, DB snapshot
sizes, D1 tables/rows mirrored, assets uploaded/unchanged/failed, secrets
backed up, and a recent-runs history table. Honestly shows `--` (not `0`)
for any phase a given run skipped (e.g. `--skip-assets` during testing) —
never conflates "didn't run" with "ran and did nothing."

**A real bug found by actually re-running the backup a second time, not
by reading the code**: the D1 mirror's schema replay read each table's
`CREATE TABLE`/`CREATE INDEX` text from the source's own `sqlite_master`,
on the assumption (stated in a comment) that it would carry the `IF NOT
EXISTS` clause schema.sql's own DDL always uses. **It doesn't** —
`sqlite_master.sql` stores the canonical statement text with `IF NOT
EXISTS` silently stripped, confirmed by direct inspection
(`"CREATE TABLE students (..."`, no clause). The very first run (against
an empty, freshly-created D1 database) worked fine since nothing
collided — the SECOND run, against a database that already had all 29
tables, failed with a real `SQLITE_ERROR: table students already exists`.
Fixed with `_ensure_if_not_exists()` (a small regex re-insertion) and
verified by actually re-running against the already-populated database —
confirmed clean (32 tables now, real platform growth between runs, 0
errors) before trusting it. Both the original failure and the fixed
success are visible, honestly, in `backup_runs`' own history — the failed
row's `error_detail` captures the exact Cloudflare error text.

**Verified**: real backup runs (both a deliberately-reproduced failure and
the fixed success) recorded correctly in `backup_runs`; the rendered page
checked via Flask's own `test_client()` (same technique
`smoke_test_admin_portal.py` already uses for auth-gated routes) and a
real headless-Edge screenshot of the output — not just "the template has
no syntax errors." `1lavya-admin-portal` restarted, confirmed clean.

## What's NOT built yet (by design, per the confirmed build order)

1. **Masters display** — read-only views of `tenants.json`/`bots.json`/
   `leaderboards.json` in full (Faculty Details above covers the
   faculty-contact slice of this; the rest is still unbuilt).
2. **Masters editing + Faculty/New Bot addition** — writes real config
   (content_scope, bot tokens, etc. — distinct from the contact-details
   editing Faculty Details above already covers). Note from Pranav's own
   ask, clarified before building anything here: "New Bot Addition" can
   only ever mean *generating the config entries* — registering a
   Telegram bot with BotFather is a human-in-Telegram action with no
   public API, this portal can't automate that step, only the config + a
   checklist for what's still manual.
3. **Question Catalog edits** — **metadata-only** for this build (chapter
   tags, marks, difficulty, flag/unflag) per Pranav's confirmed choice, not
   a full question/answer content editor (that's meaningfully bigger scope,
   parked for a later ask if wanted).
4. **Leaderboard edits + student-profile↔leaderboard mappings**.
5. **Users & Access (RBAC)** — the module this whole auth foundation was
   built to extend.

Each still gets its own build → smoke test → Pranav's confirmation before
the next, same as every phase of this roadmap so far.
