---
name: 1lavya-profile-system-built
description: "Student profile system (username/display name/course/level/exam attempt, echo-confirm email/mobile) built as the Phase 3 Leaderboard identity foundation"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82fc4833-12f2-45d0-bf8f-7222e49b86bc
  modified: 2026-08-11T12:24:10.436Z
---

Built 2026-08-11: any student can text "profile"/"change profile" to any 1LAVYA bot to view/edit a profile — permanent Instagram-style username (locked forever once set), display name, course & level (guided picker), target exam attempt, email/mobile (echo-confirm, reusing [[1lavya-reporting-roadmap-decisions]]'s pattern via new shared `telegram/bots/contact_utils.py`). Avatar is never stored — pulled live from Telegram's own profile photo.

**Key design**: one username can link multiple `telegram_user_id` chat_ids (a student's several phones) via `students.lavya_username` -> `student_profiles.username`. Shared fields (display_name/course/level/exam_attempt) live on `student_profiles` and update everywhere once linked; email/mobile stay per-chat-id on `students` (Pranav's own reasoning: different phones might use different emails).

Built explicitly as the identity foundation for the not-yet-built Phase 3 Leaderboard (see [[1lavya-reporting-roadmap-decisions]]) — Pranav confirmed via AskUserQuestion to build it now rather than re-derive it later.

New files: `telegram/bots/profile_flow.py` (full flow), `telegram/bots/contact_utils.py` (shared validation, extracted from report_flow.py), `telegram/bots/smoke_test_profile_flow.py` (41/41 passing). Wired into exam_hub_bot.py/study_hub_bot.py/faculty_bot.py with a new scoped `profile:`/`profileconfirm:` callback prefix — guards against the callback-pattern-collision bug class already hit 3x this session (see [[1lavya-platform-backend-built]]). Full writeup: `telegram/PROFILE-SYSTEM.md`.

**Why:** Pranav wants richer student data (contact info, course/level, exam attempt) to "serve better" and this doubles as the identity layer future features (leaderboard, cross-device progress) need.
**How to apply:** when touching any bot's text-message routing or callback_data registration, check profile_flow's awaiting-state FIRST (same discipline as report_flow) before any other free-text handling — it's a new, easy place to accidentally reintroduce the swallowed-callback bug class.
