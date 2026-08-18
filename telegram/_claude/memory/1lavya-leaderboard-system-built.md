---
name: 1lavya-leaderboard-system-built
description: "Phase 3 leaderboard system — students join up to 5 course/level-scoped leaderboards, nightly 11:11pm IST Telegram channel broadcasts, multi-metric rankings, plus a faculty student/chapter report dashboard card"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82fc4833-12f2-45d0-bf8f-7222e49b86bc
  modified: 2026-08-11T13:12:00.793Z
---

Built 2026-08-11, on top of [[1lavya-profile-system-built]]. Students join up to 5 live leaderboards from their profile menu (🏆 Leaderboards) — only boards matching their exact Course+Level appear (a CA Inter student never sees CA Final/CMA Inter/CS Inter). Each night at 11:11 PM IST, active leaderboards broadcast standings to their configured Telegram channel(s).

**Key locked decisions** (all confirmed via AskUserQuestion before building, since this has real outward-facing/broadcast consequences):
- Leaderboard eligibility is **fully manual per leaderboard** in `telegram/config/leaderboards.json` (same pattern as bots.json/tenants.json) — lets ONE faculty bot (e.g. CS Arun Chouhan's unified bot) host multiple separate leaderboards (CMA Inter Law + CMA Foundation Law).
- Multiple metrics (accuracy %, questions attempted, time spent) on one leaderboard render as **separate mini-rankings**, never a blended score.
- A **blanket minimum-attempts floor** gates ALL metrics, not just accuracy.
- Metrics are computed **per username**, aggregating activity across every linked phone (consistent with the profile system's multi-device identity).
- Faculty student-wise/chapter-wise report built immediately as a new `:8787` dashboard card (`analytics.fetch_faculty_report()`), not deferred to Phase 4.

New files: `telegram/database/leaderboard_metrics.py`, `telegram/bots/leaderboard_broadcaster.py` (standalone nightly job, fixed UTC+5:30 IST offset — no tzdata dependency), `telegram/bots/smoke_test_leaderboards.py` (28/28 passing). Full writeup: `telegram/LEADERBOARD-SYSTEM.md`.

Also same session: the profile's Target Attempt field became a guided **Year → Month** picker (was free-text quick-picks).

**Not live yet, by design**: every leaderboard in `leaderboards.json` ships `status: "inactive"` with `chat_id: null` — needs Pranav to create real Telegram channels, add the posting bot as channel admin, fill in real chat_ids, then flip status to active (both the leaderboard entries AND the `1lavya-leaderboard-broadcaster` bots.json entry).

**Why:** gamification/engagement lever for students, plus faculty visibility into who's actually improving.
**How to apply:** when adding a new metric, it's one registry entry in `leaderboard_metrics.py`'s `METRICS` dict + one compute function — no schema change needed. When Pranav provides real channel IDs, just edit `leaderboards.json` directly (no code change) and flip status flags.
