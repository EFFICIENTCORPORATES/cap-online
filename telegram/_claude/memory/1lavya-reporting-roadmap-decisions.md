---
name: 1lavya-reporting-roadmap-decisions
description: "Locked decisions for 1LAVYA's planned leaderboard, PDF student reports, and content-schema validation — leaderboard scoring formula, email verification approach, and what's still open"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82fc4833-12f2-45d0-bf8f-7222e49b86bc
  modified: 2026-08-10T13:39:24.909Z
---

Pranav laid out a roadmap for the bot platform on 2026-08-10 (content-schema
consistency validation, growing the admin dashboard at `:8787` into a full
portal, student-wise analytics, a faculty-visible leaderboard with rewards,
and PDF performance reports emailed to students after 20 practiced
questions) and asked for feedback before committing. See
[[1lavya-platform-backend-built]] for the dashboard/DB/process-manager
infrastructure this roadmap builds on top of, and CLAUDE.md §11's own
2026-08-10 entries for full narrative detail.

**Locked decisions, don't re-litigate without asking:**

1. **Leaderboard scoring = accuracy with a minimum-attempts floor** (not raw
   accuracy alone — rewards never attempting hard questions — and not raw
   volume — rewards fast guessing). The exact floor number (e.g. ≥50
   attempts) is not yet chosen.
2. **Report emails use echo-and-confirm, not OTP, not send-immediately.**
   Pranav's original plan was "no verification needed, he wants the report
   so he won't give a wrong email" — pushed back on: people mistype emails
   regardless of intent (autocomplete, stale saved address), and the real
   risk is a named student's actual performance data reaching an unverified
   stranger, not just a lost email. Landed on the middle ground: the bot
   echoes the typed email back with a Confirm/Re-type button before
   sending — catches the common typo class with zero extra friction, no
   OTP round-trip.
3. **PDF reports reuse `exam_hub_bot.py`'s existing `xhtml2pdf`/`pisa`
   pipeline** (already proven — that's what generates the per-question PDF
   in `send_pdf()`), NOT `first_run/output/final_deliverable/
   watermark_for_print.py` — that script rasterizes every page to a
   high-DPI image for print/anti-piracy protection on the paid Question
   Bank Book, wrong tool (and would bloat file size) for a light emailed
   report.
4. **Report emailing can reuse existing SMTP infrastructure** —
   `schema.sql`'s `students.email` field was already designed to be
   populated once verified by *any* bot doing email OTP (MyFiles Hub
   already does this) — no need to build email-sending from scratch.

**Still genuinely open, not yet decided:**
- No 1LAVYA logo image exists anywhere in this repo — text wordmark vs. a
  real logo asset for report branding/watermark is Pranav's call, not made
  yet.
- The exact minimum-attempts floor for the leaderboard.
- Leaderboard visibility/consent (full name vs. first name + initial vs.
  alias; opt-in vs. opt-out) was flagged as needing a decision but not yet
  settled.
- Whether `:8787` ever needs to be reachable off the machine it runs on
  (currently binds `127.0.0.1` only, no auth) — flagged, not decided;
  matters a lot for how the portal should be built once student PII
  (reports, leaderboard) lives behind it.

**Build order Pranav chose** (smallest/most foundational first): (1) content
field-consistency validator — **built 2026-08-10**, see
[[1lavya-platform-backend-built]]'s own update for detail — then (2)
student-wise analytics dashboard view, (3) leaderboard, (4) PDF report/email
pipeline. Don't jump ahead to (3)/(4) without checking this hasn't changed.
