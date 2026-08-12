# Student Profile System (built 2026-08-11)

Built as the identity foundation for the Phase 3 (Leaderboard) roadmap item
(see `_claude/memory/1lavya-reporting-roadmap-decisions.md` and CLAUDE.md
§11's roadmap thread) — Pranav confirmed 2026-08-11: build the identity
layer now, as part of this feature, rather than re-deriving it later when
Phase 3 actually starts.

## What it does

Any student typing `profile`, `change profile`, `my profile`, or `edit
profile` (case-insensitive, exact phrase — not a fuzzy match) to **any**
1LAVYA bot (Study Hub, Exam Hub, or a unified faculty bot) is asked to
confirm, then shown a menu to set up or edit their profile:

- **Username** — permanent, Instagram-style (3–20 chars, letters/numbers/
  underscore, case-insensitive uniqueness). Set once, **never editable
  again** — the bot says so explicitly before the student confirms.
- **Display Name** — free text, editable anytime.
- **Course & Level** — guided picker (CA/CS/CMA → their real levels), not
  free text.
- **Target Exam Attempt** — a few quick-pick buttons (forward-looking, not
  hardcoded to a specific cycle that will go stale) plus a free-text
  "Other" option.
- **Email / Mobile Number** — reuses the exact echo-and-confirm collection
  pattern already built for `report_flow.py` (see `contact_utils.py`
  below), never OTP.
- **Avatar** — not collected or stored at all. Pulled live from the
  student's own Telegram profile photo whenever one is needed. No new
  storage, no moderation surface.

## Why one username can span multiple chat_ids

Pranav's own scenario: a student who practices from 3 different phones
should never lose their identity/progress just because they're texting
from a different number today. So:

- **Shared, once linked** (`student_profiles` table, keyed by `username`):
  display_name, course, level, exam_attempt. Editing any of these from
  *any* linked chat_id updates it for *all* of them.
- **Per-chat-id, never shared** (`students` table, one row per
  `telegram_user_id`): email, mobile_number. Pranav's explicit reasoning —
  "he might give different email ids as well" across phones.

The very first time a chat_id sets up a profile, it's asked: *"Do you
already have a 1LAVYA username (from another phone)?"* — Yes links this
chat_id to the existing `student_profiles` row (no new row created); No
walks through creating a brand-new one (with the permanent-lock warning
before the final confirm).

## Files

| File | Role |
|---|---|
| `telegram/bots/profile_flow.py` | The whole flow — trigger detection, state machine, menu, all field edits. Full design rationale in its own module docstring. |
| `telegram/bots/contact_utils.py` | Shared mobile/email validation, extracted out of `report_flow.py` when this module needed the exact same logic — one definition, not two that could drift. |
| `telegram/database/schema.sql` | `student_profiles` table (new) + `students.lavya_username` (new column, via `db.py`'s `_COLUMN_MIGRATIONS`, since SQLite has no `ALTER TABLE ADD COLUMN IF NOT EXISTS`). |
| `telegram/bots/smoke_test_profile_flow.py` | 41 checks, real DB, synthetic chat_ids, self-cleaning. Run: `python telegram/bots/smoke_test_profile_flow.py`. |

## Wired into

`exam_hub_bot.py`, `study_hub_bot.py`, and `faculty_bot.py` (which reuses
`exam_hub_bot.py`'s already-imported `profile_flow` reference — same
pattern it already uses for `report_flow`, not a fresh import). Each got:

1. A new `CallbackQueryHandler(profile_flow.profile_flow_callback,
   pattern=r"^(profile|profileconfirm):")` — a **new, explicitly scoped**
   prefix, guarding against the exact callback-pattern-collision bug class
   already found and fixed 3 times earlier this session (an unscoped or
   mis-scoped handler silently swallowing another handler's buttons).
2. Its text router checks `profile_flow.is_awaiting_text_input(context)`
   **first** (so a profile edit in progress is never swallowed by search/
   report-flow/other text handling), then `profile_flow.matches_trigger()`,
   before falling through to whatever that bot's own free-text handling
   was doing before.

`study_hub_bot.py` specifically: the profile check runs before both the
reset-greeting check (`RESET_TRIGGER_RE`) and the fuzzy catalog search, so
neither can ever misinterpret profile input.

## Verification performed (2026-08-11)

- All 5 touched files (`profile_flow.py`, `contact_utils.py`,
  `exam_hub_bot.py`, `study_hub_bot.py`, `faculty_bot.py`) parse clean via
  `ast.parse()`.
- Schema migration re-run against the real `platform.db` — confirmed
  `students.lavya_username` and the full `student_profiles` table exist.
- `smoke_test_profile_flow.py`: **41/41 passed**, covering new-username
  creation + lock, case-insensitive duplicate rejection, linking a second
  chat_id to an existing username, shared-field propagation across linked
  chat_ids, per-chat-id email/mobile isolation, invalid-input rejection,
  and menu correctness (no re-offering username setup once one exists).
- All 5 bot processes that import `profile_flow`
  (`1lavya-studyhub`, `1lavya-examhub`, `csarunchouhan`, `capranav-study`,
  `capranav-exam`) were restarted via `manage_bots.py restart <bot_id>`.
  Confirmed via `bot_heartbeats.started_at` (not log-grepping) that every
  one is running a process started *after* these edits, and each log shows
  a clean `Application started` / polling loop with no import errors.

## Known limitations (named, not hidden)

- **No profanity/reserved-word filter** on usernames — out of scope for
  this pass (no reliable offline wordlist to build this against
  correctly). A student could pick something inappropriate; not currently
  blocked.
- **Exam-attempt quick-picks are relative to today** (2026-08-11) and will
  read strangely a year or two out — deliberately not hardcoded to a
  specific cycle for this reason, but the labels themselves aren't
  auto-updating either. Revisit if this becomes a real complaint.
- **Course/Level picker is a fixed, hand-coded taxonomy** (CA
  Foundation/Inter/Final, CS Executive/Professional, CMA Foundation/
  Intermediate/Final) rather than derived from a live catalog file — this
  taxonomy changes rarely enough that the simplicity was judged worth it,
  but it means a real curriculum restructuring would need a code change
  here, not just new data.
- **Username reuse across bots is untested at true multi-process
  concurrency** beyond what the smoke test's sequential real-DB writes
  cover — the underlying `execute_with_retry()`/WAL protection is the same
  one every other write in this platform already relies on, not something
  new to this feature.
