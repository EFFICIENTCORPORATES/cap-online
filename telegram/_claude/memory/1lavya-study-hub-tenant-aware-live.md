---
name: 1lavya-study-hub-tenant-aware-live
description: "study_hub_bot.py is now tenant-aware and CS Arun Chouhan's Study Hub bot is live-ready — how it works, and that Exam Hub/MyFiles Hub don't have this yet"
metadata: 
  node_type: memory
  type: project
  originSessionId: eff70d38-31a6-4cc7-baf2-a93b1aa25479
  modified: 2026-08-09T16:10:46.059Z
---

Built 2026-08-09, follows [[1lavya-tenant-schema-artifacts]]. `telegram/bots/study_hub_bot.py`
now reads a `TENANT_ID` env var at launch (default `"1lavya-studyhub"`, i.e. today's
original unrestricted behavior) and self-configures from
`telegram/config/tenants.json`:
- Filters its catalog DataFrame once at startup to the tenant's `content_scope` —
  every existing browse/search method inherits the restriction automatically, no
  per-method changes needed.
- Faculty tenants (`kind: "faculty"`) get a `_Powered by 1LAVYA_` line appended to
  **every** response (all `edit_message_text`/`reply_text`/`send_document` caption
  call sites go through a `with_brand()` helper); the flagship 1LAVYA tenants don't.
- A tenant can carry its own `welcome_message` (Markdown) for `/start`.
- A standalone greeting (hi/hey/hello/hiya/yo/namaste) or the word "reset" resets the
  conversation the same way `/start` does (regex `RESET_TRIGGER_RE`, same word list
  `myfiles_hub_bot.py` already used for its own greeting handling).
- Token resolves via the tenant's `bot_token_env` (from `telegram/.env`), falling
  back to `telegram/creds.txt` only for the `1lavya-studyhub` tenant (backward
  compat).

**CS Arun Chouhan's Study Hub bot is ready to run**: verified by smoke-test (module
import with `TENANT_ID=csarunchouhan`, no live polling) — catalog correctly scopes to
18 rows (5 CMA Foundation + 13 CMA Intermediate "Business Laws..." chapters, real
subject strings pulled from the actual catalog, not guessed), Exam/Revision
categories correctly empty (existing "not available yet" UX handles this), footer/
greeting/token resolution all confirmed working with the real
`FACULTY_CSARUNCHOUHAN_BOT_TOKEN` now in `telegram/.env`. Launch command: see
`telegram/bots/README_Bot1_StudyHub.md`'s setup checklist (`$env:TENANT_ID =
"csarunchouhan"; python telegram/bots/study_hub_bot.py`, separate terminal from the
flagship bot).

**Not done yet — only Study Hub (Bot 1) got this treatment.** `exam_hub_bot.py`
(MCQ/Descriptive practice) and `myfiles_hub_bot.py` are still single-tenant, not
tenant-aware. Arun's Exam Hub bot additionally needs the `.docx` MCQ extractor
(doesn't exist) before it can go live at all — his Study Hub bot has no such
content blocker since it serves the already-existing shared CMA catalog.
