---
name: 1lavya-branding-report-leaderboard-portal-roadmap
description: "Locked build order and decisions for 1LAVYA's big 2026-08-11 roadmap (branding kit, student report PDFs, global-username leaderboard, Flask admin portal) — Phase 1 (branding kit) is done and smoke-tested"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82fc4833-12f2-45d0-bf8f-7222e49b86bc
  modified: 2026-08-11T09:42:13.516Z
---

Pranav laid out a large roadmap on 2026-08-11: conversational upgrades
(greetings, free-text intent routing scoped to a bot's tenant content_scope,
faculty bots stating their scope limits), deeper per-student analytics,
a 20-question report pipeline (collect email/mobile, no OTP — his repeated,
explicit call — generate a branded HTML→PDF, send by chosen channels), a
30-question leaderboard built on a NEW globally-unique "1LAVYA username"
identity (Instagram-handle-style, separate from a public display name, one
username can span multiple chat_ids/phones, leaderboard shows consolidated
scores, unique-chat-ID-count-per-username as an abuse signal, concurrent
cross-chat-ID activity logged not blocked), and turning the admin dashboard
into a full sidebar application (Masters, Settings, downloadable schema
templates, tabbed analytics) — all under consistent 1LAVYA branding, never
on faculty-branded bot output. See [[1lavya-platform-backend-built]] and
[[1lavya-reporting-roadmap-decisions]] for the infrastructure this builds on.

**Locked decisions, don't re-litigate without asking:**
1. Free-text search is scoped to the bot's tenant `content_scope` FIRST
   (never suggests out-of-scope content) — narrows via a Course+Level
   picker, then Subject if still ambiguous, THEN queries both Study Hub and
   Exam Hub content within that narrowed scope. Not "whichever hub the UI
   happens to be in" — that was my first offered option, Pranav corrected it.
2. The 20/30-question milestones are counted **platform-wide** (matches the
   centralized-account model), not per-bot.
3. The admin portal moves to **Flask** — Settings/Masters need writes, the
   current stdlib `http.server` dashboard was fine read-only, not for this.
4. **Build order is strict and process-bound**: Branding Kit → Report
   Pipeline → Leaderboard → Admin Portal. For EACH phase: build it,
   smoke-test it with a real re-runnable `.py` script (not ad hoc checks),
   document it, THEN hand off for Pranav's manual test. Only move to the
   next phase once he's confirmed the current one. **Do not skip ahead.**

**Phase 1 (Branding Kit) — DONE, smoke-tested, awaiting Pranav's manual
confirmation as of 2026-08-11.** `telegram/branding/` — see that folder's
own README.md for full depth. Key facts for continuity:
- Source: `telegram/1LAVYA_LOGO.jpeg`. Derived: transparent-bg PNG (feathered
  alpha), 3 pre-sized thumbnails, `brand_colors.json` (navy `#09284b`, gold
  `#d0942c`, both sampled from real logo pixels, not guessed).
- `brand_kit.py`: `colors()`, `logo_data_uri(variant)`, `render_header_html()`,
  `render_footer_html()`, `brand_css_vars()`.
- Markup is deliberately table/inline-style only (no flexbox/grid/gradients/
  em-units) because it must render correctly in BOTH a real browser AND
  `xhtml2pdf`/`reportlab` (Phase 2's future PDF engine, already proven in
  `exam_hub_bot.py`'s `html_to_pdf_bytes()`).
- Real bug the smoke test caught: `letter-spacing: 0.02em` silently dropped
  by reportlab (can't parse `em`), `pisa` still reported 0 errors — only
  caught by actually rendering through both engines and inspecting pixels/
  PDF content, not by a "did it crash" check. Fixed; smoke test now guards
  this regression class permanently.
- Wired into the real dashboard already (not left untested in isolation).

**Phase 2 (Report Pipeline) — DONE, deployed, 2026-08-11.** Pranav confirmed
Phase 1 and said proceed. Full detail: `telegram/REPORT-PIPELINE.md`. Key
facts for continuity:
- New: `database/student_analytics.py` (accuracy/time-per-question/chapter-
  wise/time-on-bot, platform-wide), `tools/generate_student_report.py`
  (branded HTML→PDF, importable + CLI), `database/report_delivery.py`
  (email via MyFiles Hub's SMTP), `bots/report_flow.py` (the conversational
  flow: 20-question trigger, echo-confirm contact collection, no OTP).
- Schema migrations for EXISTING tables (`students` gained 4 columns) are
  idempotent Python in `db.py`'s `_run_column_migrations()`, NOT raw SQL —
  SQLite has no `ADD COLUMN IF NOT EXISTS` (confirmed by testing, a wrong
  assumption in the first draft).
- Two real bugs caught by testing before shipping: (1) a session-end design
  that would have counted multi-day idle gaps as active "time on bot" —
  reverted, now computed as `MAX(activity) - started_at` per session at
  query time; (2) mobile regex rejected realistic Indian 5+5-grouped input
  ("+91 98765 43210") — fixed by stripping separators before matching.
- Re-guarded against the EXACT callback-pattern-collision bug class found
  twice already (2026-08-10's "next"/"restart" bug in faculty_bot.py):
  `exam_hub_bot.py`'s `button_router` had no pattern at all before this
  change — fixed with an explicit pattern before `report_flow`'s own
  callbacks were added, in both `exam_hub_bot.py` and `faculty_bot.py`.
- `smoke_test_report_flow.py`: 7 steps, ~40 checks, full conversational-flow
  simulation against a synthetic test student. Real SMTP creds aren't
  configured in this dev environment — message-building and graceful-
  failure-handling are verified for real, actual delivery is not; Pranav
  needs to verify a real send once real creds are in `telegram/.env`.
- Deployed: restarted `1lavya-examhub`, `capranav-exam`, `csarunchouhan`.

**Update, same day — a real bug found by Pranav's own manual test.** His
account had 35+ (later confirmed 67) answered questions, prompt never
fired. Root cause: the milestone check required `count == 20` exactly —
broke for anyone (like his account) already past 20 when Phase 2 deployed,
since every later answer only pushes further past 20. Fixed to `>=`. Added
a permanent regression test for this exact scenario. Also built, same
session: `report_flow_events` (a complete audit trail of every
conversational step — prompt shown, value collected/confirmed/rejected,
delivery attempted) and a new "Student Breakdown" card on the `:8787`
dashboard (bot dropdown → chat-ID-wise attempted/answered/correct/wrong).
Redeployed (restarted `1lavya-examhub`, `capranav-exam`, `csarunchouhan`,
`1lavya-dashboard`); confirmed the real account will fire on its next
answer. Full detail: `telegram/REPORT-PIPELINE.md`.

**Not started**: Phase 3 (Leaderboard). Do not begin it until Pranav
explicitly confirms Phase 2 works on his end — that confirmation gate is
part of the locked process above, not optional.

**Update 2026-08-11, minutes later — a real deploy gap + a real DB bug,
both found and fixed via Pranav's own manual check.** He reported no
branding visible at all on the real `:8787` page. Cause: the live
`1lavya-dashboard` process predated the `dashboard_html.py` edit (Python
doesn't hot-reload), and the smoke test had only ever checked the *static*
`dashboard.html` file, never the actually-running server — a real gap in
what "smoke tested" meant. Restarted, confirmed live via a real screenshot
of the URL. **Operational rule now written into `telegram/branding/
README.md`'s top callout: always restart `1lavya-dashboard` after editing
`dashboard_html.py`/`brand_kit.py`.**

Fixed the smoke test itself: Step 7 now fetches the live `:8787` server
directly and compares its recorded process-start time against both source
files' mtimes — a stale process is now a loud, automatic failure. That new
check immediately caught a second, separate, pre-existing bug: `db.py`'s
`send_heartbeat()` only ever wrote `started_at` on a bot_id's first-ever
heartbeat INSERT, never on later UPDATEs (i.e. every restart) — so the
column silently kept showing the very first process's start time forever.
Fixed (confirmed nothing else in the codebase reads `started_at` today, so
safe with no other blast radius). Restarted only `1lavya-dashboard` to pick
it up — left the other 6 bots running since they share the same fix but it
has no current user-facing effect for them; they'll get it on their next
natural restart.

Smoke test is now 7/7 green, including both new checks. This is the same
"trust the actual rendered/deployed thing, not a structural pass" lesson
this session has now hit four separate times (three on csarunchouhan's
content pipeline, once here on the branding kit's own deployment) — worth
treating as a standing discipline for every future phase, not a one-off.
