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

**Analytics** (5 views, all paginated/filterable/exportable):
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

## What's NOT built yet (by design, per the confirmed build order)

1. **Masters display** — read-only views of `tenants.json`/`bots.json`/
   `leaderboards.json`.
2. **Masters editing + Faculty/New Bot addition** — writes real config.
   Note from Pranav's own ask, clarified before building anything here:
   "New Bot Addition" can only ever mean *generating the config entries* —
   registering a Telegram bot with BotFather is a human-in-Telegram action
   with no public API, this portal can't automate that step, only the
   config + a checklist for what's still manual.
3. **Question Catalog edits** — **metadata-only** for this build (chapter
   tags, marks, difficulty, flag/unflag) per Pranav's confirmed choice, not
   a full question/answer content editor (that's meaningfully bigger scope,
   parked for a later ask if wanted).
4. **Leaderboard edits + student-profile↔leaderboard mappings**.
5. **Users & Access (RBAC)** — the module this whole auth foundation was
   built to extend.

Each still gets its own build → smoke test → Pranav's confirmation before
the next, same as every phase of this roadmap so far.
