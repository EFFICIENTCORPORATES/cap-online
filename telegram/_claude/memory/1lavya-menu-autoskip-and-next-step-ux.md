---
name: 1lavya-menu-autoskip-and-next-step-ux
description: "Faculty bots now auto-skip Course/Level/Subject pickers that have only one real option (derived from tenants.json, no new storage needed), and MCQ/descriptive results offer Next/Back/Done instead of just Next"
metadata: 
  node_type: memory
  type: project
  originSessionId: eff70d38-31a6-4cc7-baf2-a93b1aa25479
  modified: 2026-08-09T18:44:43.700Z
---

Built 2026-08-10, on top of [[1lavya-study-hub-tenant-aware-live]] and
[[1lavya-csarunchouhan-demo-content]].

**Auto-skip single-option menu steps** (Pranav's ask: a faculty bot should never make
a student pick a Course/Subject the faculty's own scope has already fixed). Implemented
by deriving it fresh from `content_scope` in `telegram/config/tenants.json` every time
— **no new per-student/session storage was needed**, since `tenants.json` is already
the persistent, disk-backed source of truth; the fix was making the menu code actually
check "how many options are there?" before rendering a picker.
- `study_hub_bot.py`: `route_browse()` (renamed from the old `browse_callback` body)
  recurses with a synthetic callback-data string whenever Course/Level/Subject
  collapses to exactly one option, reusing every existing branch unchanged. Back
  buttons use new `effective_course_back()`/`effective_level_back()`/
  `effective_subject_back()` helpers that always point to the last screen that was
  genuinely shown — verified by test that the full Back chain (Chapter → Level →
  Category) never dead-ends or loops even when multiple steps were auto-skipped.
- `exam_hub_bot.py`: new `entry_screen_and_updates()` computes the same cascade for
  Course→Level→Mode, used by `start()`, the `restart` action, and the `course` action
  (if a chosen course's Level list is itself a singleton). `faculty_bot.py`'s
  "Exam Practice Hub" entry point uses it too.
- Verified: Arun's bot (1 course, CMA) skips the Course step entirely in both hubs;
  the flagship bots (3 courses) are provably unaffected (`entry_screen_and_updates()`
  returns no auto-selected fields when there's real choice).

**3-way next-step options** (Pranav's ask: after an MCQ, offer more than just "Next
Question"). New `exam_hub_bot.py` helper `next_step_rows()` renders **Next Question /
Back to Chapter List / I'm Done** — applied to `handle_mcq_answer`'s result,
`send_answer`'s descriptive result (kept alongside the existing "Get as PDF" button),
and both "you've gone through everything" exhausted-queue messages (which previously
had zero buttons — a dead end). "Back to Chapter List" reuses the existing `year:`
action unchanged (context.user_data already has exam_type/year set), "I'm Done" reuses
`restart`.

**Real bug found and fixed in the same pass**: the descriptive JSON
(`book_questions_extracted.json`) never actually got the explicit `exam_type`/`year`
fields planned back in [[1lavya-csarunchouhan-demo-content]] — it was silently falling
back to pattern-detecting a year from `src_text`, which has no digits in it, producing
a "Select Year: **Unknown**" button instead of "2026". Fixed by adding the fields
directly to all 5 records. Caught by simulated end-to-end testing, not by inspection —
worth remembering that this fallback-detection path can silently produce ugly-but-
technically-functional output rather than an obvious error.
