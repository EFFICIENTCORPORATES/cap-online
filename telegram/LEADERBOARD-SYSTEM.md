# Leaderboard System (built 2026-08-11)

Phase 3 of the branding-kit → report-pipeline → leaderboard → admin-portal
roadmap (Phases 1–2 done same week — see `telegram/branding/README.md`,
`telegram/REPORT-PIPELINE.md`). Built on top of the student profile/identity
system (`telegram/PROFILE-SYSTEM.md`) — a student needs a permanent
1LAVYA username before they can join any leaderboard.

## What it does

A student can join **up to 5** live leaderboards from their profile menu
(text "profile" → 🏆 Leaderboards). Only leaderboards matching their
**exact** Course + Level appear — a CA Inter student never sees a CA
Final/CMA Inter/CS Inter board, per Pranav's explicit spec. Each night at
**11:11 PM IST**, every active leaderboard's standings are posted to its
configured Telegram channel(s).

## Locked design decisions (all confirmed via AskUserQuestion, 2026-08-11)

1. **Leaderboard scope is fully manual per leaderboard** — each entry in
   `telegram/config/leaderboards.json` hand-specifies its own
   `eligibility` (course + level), not auto-derived from `bots.json`/
   `tenants.json`. This is what lets CS Arun Chouhan's **one** unified bot
   host **two separate** leaderboards (CMA Intermediate Law, CMA
   Foundation Law) — Pranav's own example.
2. **Leaderboards are managed via a JSON config file**, same pattern as
   `bots.json`/`tenants.json`/`alerts.json` — no admin UI yet (that's
   Phase 4). A leaderboard is staged with `status: "inactive"` and
   `chat_id: null` placeholders until Pranav creates the real channel,
   adds the posting bot as an admin with post rights, and fills in the
   real chat_id.
3. **One leaderboard can rank by multiple metrics** (accuracy %, questions
   attempted, time spent) — from an extensible **metrics master**
   (`telegram/database/leaderboard_metrics.py`'s `METRICS` registry).
   Each metric gets its **own separate mini-ranking section** in the
   nightly broadcast — never a blended weighted score.
4. **A blanket minimum-attempts floor gates every metric**, not just
   accuracy — a student needs `min_attempts_floor` (default 10) answered
   MCQs in that leaderboard's course+level scope before appearing on
   *any* of its rankings, so one lucky fast answer can't top a "Time
   Spent" board on day one.
5. **The faculty report is built now**, as a new dashboard card at
   `:8787` (not deferred to Phase 4) — see below.

## Identity: one username, every linked phone counted together

Every metric is computed **per username**, aggregating MCQ activity across
**every** `telegram_user_id` (phone) linked to that username — consistent
with the profile system's "one identity, several phones" design. A
student practicing from 2 phones gets combined credit, not split into two
weaker entries.

## Files

| File | Role |
|---|---|
| `telegram/config/leaderboards.json` + `.README.md` | The leaderboard registry — eligibility, metrics, channels, min-attempts floor, per-leaderboard broadcast bot token. Two example (inactive) entries seeded for CS Arun Chouhan's CMA Inter/Foundation Law boards. |
| `telegram/database/schema.sql` | New `leaderboard_participants` (who joined what) + `leaderboard_broadcast_log` (full audit trail of every nightly send attempt) tables. |
| `telegram/database/leaderboard_metrics.py` | Config loading, eligibility matching, the metrics registry, and ranking computation (`compute_rankings()`). |
| `telegram/bots/profile_flow.py` | New "🏆 Leaderboards" menu — shows eligible active boards, join/leave toggle, enforces the 5-board cap. |
| `telegram/bots/leaderboard_broadcaster.py` | Standalone managed process (like `watcher_bot.py`) — wakes near 23:11 IST daily (fixed UTC+5:30 offset, no tzdata dependency), renders and posts each active leaderboard's message, logs every attempt. `--once` bypasses the already-sent-today guard for testing. |
| `telegram/database/analytics.py` / `dashboard_html.py` | New `fetch_faculty_report()` + the "Faculty Report — Student-wise & Chapter-wise" dashboard card (click a row to expand that student's chapter breakdown). |
| `telegram/bots/smoke_test_leaderboards.py` | 28 checks against the real DB with synthetic, self-cleaning data. |

## Verification performed (2026-08-11)

- All new/edited files parse clean via `ast.parse()`; `bots.json`/
  `leaderboards.json` both valid JSON.
- Schema migration re-run against the real `platform.db` — confirmed both
  new tables exist with the expected columns.
- `smoke_test_leaderboards.py`: **28/28 passed** — eligibility matching,
  join/leave, the 5-board cap (including the rejected 6th join showing an
  alert), multi-phone metric aggregation (verified against real seeded
  MCQ attempts across two chat_ids), the minimum-attempts floor gate
  (including the exact-at-floor boundary case), full ranking sort order
  per metric, broadcast message rendering, and the broadcast-log audit
  trail (including a real logged failure when no token resolves).
- `smoke_test_profile_flow.py` re-run clean (43/43) — the new Leaderboards
  button didn't disturb any existing profile flow behavior.
- Faculty Report verified against **real production data**: queried
  through the actual `analytics.fetch_all()` / rendered through the real
  `dashboard_html.render_page()`, confirmed correct chapter-wise rows for
  `csarunchouhan` (15 students) and `capranav-exam` (3 students). Static
  dashboard regenerated; live `:8787` server restarted and confirmed
  serving `faculty_report` in its `/api/data` response and rendering the
  new card.
- All 5 bots that import `profile_flow.py`
  (`1lavya-studyhub`, `1lavya-examhub`, `csarunchouhan`, `capranav-study`,
  `capranav-exam`) restarted, confirmed clean startup logs, no import
  errors.

## What's NOT live yet (by design, not oversight)

- **No leaderboard is actually broadcasting.** Every entry in
  `leaderboards.json` ships `status: "inactive"` with `chat_id: null` —
  Pranav needs to (1) create the real Telegram channel(s), (2) add the
  posting bot as an **admin with post permission** in each (a
  Telegram-side step this script cannot do), (3) fill in the real
  `chat_id`, (4) flip `status` to `"active"`.
- **`1lavya-leaderboard-broadcaster` is `status: "inactive"` in
  `bots.json`** — starting it before any leaderboard is active is
  harmless (it just finds nothing to send every check) but pointless.
  Flip both once the first real leaderboard is ready.
- **The exam-attempt picker is now Year → Month** (two guided steps,
  replacing the earlier free-text quick-picks), per Pranav's ask this same
  session — covered by the same `smoke_test_profile_flow.py` run.

## Also updated this session

**Target Attempt in the profile menu** is now a two-step guided picker
(tap a Year, then tap a Month) instead of a hand-picked quick-list —
Pranav's ask, so students aren't stuck with sitting labels that go stale.
Years are computed relative to "today" at render time, never hardcoded.
