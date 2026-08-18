---
name: 1lavya-admin-portal-foundation
description: "Phase 4 Admin Portal foundation tier — Flask app at :8788, single-admin login (RBAC-ready), sidebar shell with 12 planned modules, live Bot Status/Restart, Bot Logs, audit trail"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82fc4833-12f2-45d0-bf8f-7222e49b86bc
  modified: 2026-08-11T16:44:25.489Z
---

Built 2026-08-11. Phase 4 of the roadmap (Branding Kit → Report Pipeline → Leaderboard → **Admin Portal**). Pranav's ask was large — analytics, masters CRUD, bot restart, question catalog edits, faculty/bot addition, leaderboard edits, email analytics, bot logs, and later module-wise RBAC for students/faculty/managers — with an explicit "don't assume, ask me" instruction.

Asked 4 clarifying questions before building (all answered "Recommended"): **single-admin login now, RBAC layers on later** (not no-auth); **metadata-only Question Catalog editor first** (not full content editing); **foundation-tier-first build sequencing** across the ~12 modules (Flask+login+sidebar+Bot Status/Restart/Logs → Analytics → Masters → Content/Leaderboards/RBAC last); **explicit confirm dialog on every destructive action**.

New `telegram/admin_portal/` — `app.py` (Flask, port 8788, runs alongside the existing `:8787` dashboard until Analytics migrates over), `auth.py` (session-based single-admin login, every route wrapped in `role_required()` not bare login_required, so RBAC later is a decorator-argument change not a redesign), `audit.py` + new `admin_actions` DB table (who/what/when for every real action), `set_password.py` (credential rotation), branded sidebar template with "Soon" badges for the ~10 not-yet-built modules. Registered in `bots.json` as `1lavya-admin-portal`.

Bot Status & Restart calls `manage_bots.py`'s own `restart_bot()` directly (imported, not subprocessed). Verified for real: manual restart of `1lavya-platform-watcher` (real PID change, real audit row), confirmed unauthenticated restart attempts are blocked. `smoke_test_admin_portal.py`: 26/26 via Flask test_client. Visually verified via headless-Edge screenshots. One real bug found+fixed: a `NAV_SECTIONS` dict key named `"items"` collided with Python's `dict.items()` method under Jinja2 attribute lookup — renamed to `"links"`.

Also same session: 3rd leaderboard added to `leaderboards.json` for CA Pranav (CA Inter Advanced Accounts, posted via capranav-exam) — all 3 leaderboards (his + CS Arun Chouhan's CMA Inter/Foundation Law) now use the same 3-metric set (accuracy/attempted/time-spent), still `status: "inactive"` pending real Telegram channel IDs from Pranav.

See [[1lavya-leaderboard-system-built]], [[1lavya-branding-report-leaderboard-portal-roadmap]]. Full detail: `telegram/admin_portal/README.md`.

**Why:** the platform now has enough moving parts (9+ bots, leaderboards, reports, content) that hand-editing JSON files and SSHing in for restarts doesn't scale — this is the ops/admin control plane, built as the RBAC foundation for eventually giving faculty/managers scoped access too.
**How to apply:** any NEW admin-portal route must be wrapped in `auth.role_required("admin")` (or a future specific role) — never a bare function. Any NEW destructive action should call `audit.log_action()` and use the shared `confirmAction()` JS modal in `base.html` rather than building its own confirm UI.

**Update, same day — Analytics tier built**: universal "export any DB table" (JSON/CSV/XLSX, no scoping), 5 paginated/filterable/exportable Analytics views (Student Master, Bot-wise Usage, Faculty Report + chapter drill-down, Content Health, Email Analytics), and Student Master's bulk "Send Report to Selected" (emails each selected student their own existing report, only to an already-confirmed email on file, sent from `reports@1lavya.com`). New `exporters.py` — shared filter/paginate/CSV/XLSX/JSON/HTML/PDF-snapshot primitives every current AND future tabular view reuses. `smoke_test_admin_portal.py`: 68/68 passing. See `telegram/admin_portal/README.md`'s "Analytics tier" section.
**How to apply (cross-cutting export/pagination)**: any NEW tabular view should reuse `exporters.filter_rows()`/`paginate()`/the `_export_toolbar.html`+`_pagination.html` partials, not rebuild filtering/pagination/export from scratch.
