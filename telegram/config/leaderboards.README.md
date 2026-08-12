# `leaderboards.json` — leaderboard registry

Added 2026-08-11, Phase 3 of the branding-kit → report-pipeline → leaderboard
→ admin-portal roadmap. Same pattern as `bots.json`/`tenants.json`/
`alerts.json`: a hand-edited JSON file is the single source of truth for
what a leaderboard IS — no admin UI yet (Phase 4), a bot/broadcaster restart
picks up an edit.

## Why "fully manual" (Pranav's explicit choice, 2026-08-11)

Each leaderboard's `eligibility` is hand-specified, **not** auto-derived
from `bots.json`/`tenants.json`. This is deliberate: it lets one course+level
(e.g. CMA Intermediate) have zero, one, or several leaderboards with no code
change — Pranav's own example is two boards under **one** faculty bot
(CS Arun Chouhan's unified bot serves both CMA Foundation and CMA
Intermediate Law, but each level gets its **own** leaderboard, never pooled
together).

## Field reference (per leaderboard entry)

| Field | Meaning |
|---|---|
| `leaderboard_id` | Free-text, stable identifier — referenced by `leaderboard_participants.leaderboard_id` in the DB and by `profile_flow.py`'s join/leave buttons. Never reuse an id for a different leaderboard once students have joined the old one. |
| `display_name` | Shown to students in the profile menu and at the top of the nightly broadcast. |
| `eligibility` | `{"course": ..., "level": ...}` — a student's `student_profiles.course`/`.level` must match **exactly** for the leaderboard to appear as joinable in their profile menu. (Extensible to add `"subject"` later if a course+level ever needs finer splitting — not needed by any leaderboard today.) |
| `metrics` | List of metric keys from the registry in `telegram/database/leaderboard_metrics.py` (`accuracy_pct`, `questions_attempted`, `time_spent_minutes` today). Each metric gets its **own** mini-ranking section in the nightly broadcast (Pranav's choice, 2026-08-11 — not a blended weighted score). |
| `min_attempts_floor` | A student must have at least this many **answered** MCQs within this leaderboard's `eligibility` scope to appear on **any** of its metric rankings — a blanket gate across every metric (Pranav's choice), not just accuracy, so a single lucky/fast answer can't top a "Time Spent" or "Questions Attempted" board on day one. Falls back to `defaults.min_attempts_floor` if omitted. |
| `top_n` | How many students to show per metric section in the broadcast. Falls back to `defaults.top_n`. |
| `broadcast_bot_token_env` | Which bot's token (an env var name, resolved from `telegram/.env`) actually posts the nightly message. Must be a bot that has been added as an **admin with post permission** in every channel listed below — a Telegram-side step only Pranav can do; this script cannot create channels or grant admin rights. |
| `broadcast_channels` | List of `{"chat_id": ..., "label": ...}` — one leaderboard can broadcast to **multiple** channels (Pranav's "one to one or one to many" spec). `chat_id` is a Telegram channel's numeric id (negative, like a group — get it the same way documented in `alerts.json`'s own comment, or via `@userinfobot`/forwarding a channel post to a bot that echoes chat info). |
| `status` | `"active"` or `"inactive"`. An `"inactive"` leaderboard never appears in a student's profile menu and is skipped by the nightly broadcaster — this is how a leaderboard is safely staged (metrics/channels filled in, still `chat_id: null` placeholders) before it's real. |

## How a student joins

`profile_flow.py`'s profile menu shows every `"active"` leaderboard whose
`eligibility` matches the student's own `course`/`level` (only available once
they have a username set — see `telegram/PROFILE-SYSTEM.md`). A student may
join **at most 5** leaderboards at once (Pranav's explicit cap) — enforced in
Python, not a SQL constraint (see `schema.sql`'s own note on why).

## How the nightly broadcast works

`telegram/bots/leaderboard_broadcaster.py`, a standalone managed process
(see `bots.json`'s `1lavya-leaderboard-broadcaster` entry) — same
`--once`-for-testing / continuous-loop shape as `watcher_bot.py`. Wakes at
`defaults.broadcast_time_ist` (IST, fixed UTC+5:30 offset — India has no DST,
so no timezone-database dependency is needed) once every calendar day, or
run manually with `--once` any time. For every `"active"` leaderboard: query
`leaderboard_metrics.py` for each of its `metrics`, filter to students who
meet `min_attempts_floor`, render one message with one section per metric,
POST to every configured channel, and log the attempt in
`leaderboard_broadcast_log`.

## Metrics registry

See `telegram/database/leaderboard_metrics.py`'s own `METRICS` dict —
the canonical list of what a leaderboard can rank students by. Adding a new
metric is one new registry entry + one computation function there, then
referencing its key from any leaderboard's `metrics` list here — no schema
change needed.

**Identity note**: every metric is computed **per `username`**, aggregating
activity across **every** `telegram_user_id` (phone) linked to that
username — consistent with the profile system's "one identity, several
phones" design. A student with no username yet cannot be ranked on any
leaderboard (they also can't join one — see above).
