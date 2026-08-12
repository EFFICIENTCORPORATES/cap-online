# `tenants.json` — the faculty content registry

**The rule this file exists to enforce**: onboarding a faculty for shared-1LAVYA-
content access is **one JSON entry, zero code changes**. Onboarding their own
content is a **separate, real pipeline** that takes real work. Never let the two
blur together — a faculty entry can go live for shared content today and still
show "own content: not yet available" for weeks while their material gets
processed, and that's the correct, expected state, not a bug.

**This file answers "what does this faculty teach" — nothing about bot
identity/tokens.** That split happened 2026-08-10: `bot_username`,
`bot_token_env`, and bot-level `status` used to live on the tenant entry
here, until CA Pranav's ask for **two separate bots** (Study + Exam, not
one unified bot like CS Arun Chouhan's) proved that "tenant" and "bot"
aren't the same thing. Those fields now live in
**`telegram/config/bots.json`** (see `bots.README.md`) — a tenant can map
to one bot or several there; this file no longer knows or cares how many.

## Field contract

| Field | Meaning |
|---|---|
| `tenant_id` | Stable slug, one per **faculty** (not per subject, not per bot — a faculty teaching 2 subjects across 2 bots is still 1 tenant here, 1 `tenants.json` entry, 2 `content_scope` entries, 2 rows in `bots.json`). Matches the prefix used in `telegram/assets/faculty/{tenant_id}-...` folder names. |
| `kind` | `"platform"` (the flagship 1LAVYA-branded bots, unrestricted) or `"faculty"` (a white-label bot). |
| `display_name` | Human name, shown in bot branding/messages. |
| `welcome_message` | Optional. The opening line(s) of `/start`'s reply, in Telegram Markdown. Falls back to the generic "Welcome to 1Lavya Study Hub" text if absent — every faculty tenant should get one written for their actual branding/tone (see `capranav`, still missing one) rather than silently inheriting 1LAVYA's own greeting. |
| `onboarding_fee` | `{amount_inr, paid, paid_at}` — tracks the flat ₹5,000 faculty fee. `paid: null` until confirmed; flip to `true`/`false` explicitly, never leave ambiguous. |
| `content_scope` | **`"ALL"`** for platform tenants, or a list of `{course, level, subject}` objects for faculty tenants — this is the filter a bot applies against the shared 1LAVYA master catalog (`StudyHub_Master_Catalog.xlsx`, `questions_index.json`, etc.) at query time. **Adding a scope entry here is the entire "instant access" mechanic** — no catalog rows need touching, no code needs editing, because the filter is generic (course/level/subject match), not hardcoded per faculty. |
| `own_content.status` | `"not_ingested"` \| `"ingested_demo_batch"` \| `"ingested"` — whether this faculty's own material has been through the extraction/catalog pipeline yet and is servable, and how completely. A bot should show "not yet available" for this part, never silently show nothing with no explanation. |
| `own_content.asset_paths` | Where their raw source files live (`telegram/assets/faculty/...`) — informational pointer for whoever runs the ingestion tooling (see `convert_faculty_mcq_docx.py`), not read by the bot directly. |
| `own_content.shape` | Free-text note on what they actually supplied — kept because it's been proven to differ wildly per faculty (Pranav: 2 revision PDFs, no exam content of his own; Arun: zero study materials, MCQ docx + one descriptive PDF) and drives what extraction tooling is even needed. |
| `exam_content` | `{mcq_json, descriptive_json}` — Exam Hub's content, sibling to `content_scope`. Each value is a repo-relative path, **or a list of them** (added 2026-08-11) — a list means "load and merge all of these at bot startup," used when a tenant's content comes from more than one independently-owned, independently-regenerated source (e.g. `1lavya-examhub`'s `mcq_json`: the CA-Inter auto-generated bank + a separately-built CA-Foundation-Quantitative-Aptitude batch) so neither source's own regeneration script ever clobbers the other. **Every reader of this field must handle both shapes** — `exam_hub_bot.py`'s `_resolve_content_paths()` and `validate_content_json.py`'s `discover_content_files()` both do; a single-string-only reader will crash with a `WindowsPath / list` TypeError the moment it hits a list-valued tenant (this happened once, 2026-08-11, to the live `:8787` dashboard — fixed same day). No `db_path` here anymore (2026-08-10) — every bot now writes to the one shared `telegram/database/platform.db`, resolved by code (`telegram/database/db.py`), not per-tenant config. |

## Why `content_scope` is the whole trick

A bot process, at startup, does roughly:

```python
bot = load_bot(bot_id, bots_path)          # telegram/config/bots.json -- which bot am I
tenant = load_tenant(bot["tenant_id"])     # this file -- what does that tenant teach
shared_rows = master_catalog.filter(scope=tenant["content_scope"])   # "ALL" or a course/level/subject list
own_rows    = faculty_catalog.filter(tenant_id=tenant["tenant_id"]) if tenant["own_content"]["status"] != "not_ingested" else []
serve(shared_rows + own_rows)
```

Nothing here is faculty-specific code — the *same* bot script runs for every
bot, parameterized only by which `BOT_ID` it was started with (see
`bots.README.md`) and what that bot's tenant config says here. That's what
makes adding a faculty's *shared*-content access "plug and play": their
`tenants.json` entry already exists, `content_scope` is already filled in —
the only missing piece is a `bots.json` row and a real BotFather token.

## The bots are actually wired up now (2026-08-09 → 2026-08-10)

- **`study_hub_bot.py`** (2026-08-09, moved onto `BOT_ID`/`bots.json`
  2026-08-10): scopes its catalog by `content_scope` at startup, appends a
  `_Powered by 1LAVYA_` footer **only on an actual file/PDF delivery** (not
  menus/questions — see `send_file()`'s own comment; this was tightened
  2026-08-10 after first shipping it on every response), auto-skips any
  Course/Level/Subject picker step that collapses to one real option for a
  narrowly-scoped faculty, and resets on `/start`, "reset", or a standalone
  greeting. Logs to the shared platform DB (see `telegram/database/`).
- **`exam_hub_bot.py`** (2026-08-10): same `BOT_ID` contract, resolving
  `JSON_PATH`/`MCQ_JSON_PATH`/`BOT_TOKEN` from `tenant_id`/`bots.json`.
  `COURSES` is scoped from `content_scope`; `AVAILABLE_DATA` is **computed
  from the loaded question banks**, never hand-maintained. Both
  `QuestionBank`/`McqBank` gained course+level-aware filtering so a tenant
  spanning more than one level (e.g. `csarunchouhan`, Foundation +
  Intermediate) never bleeds one level's questions into the other. Answers
  now offer Next/Back-to-Chapter-List/I'm-Done instead of just Next. Now
  migrated onto the shared platform DB (`exam_hub_sessions`/
  `exam_hub_descriptive_events`/`exam_hub_mcq_attempts`), replacing its old
  separate per-tenant `Exam_Bot.db` file.
- **`telegram/bots/faculty_bot.py`** (2026-08-10): composes both under one
  `/start` picker, for any tenant needing BOTH hubs in one Telegram identity
  (see that file's own docstring for the one deliberate monkeypatch this
  needs). Used by `csarunchouhan` (one bot). **Not** used by `capranav` —
  he asked for two *separate* bots (Study + Exam), which is exactly the
  case that led to splitting bot identity out into `bots.json` — see
  `bots.README.md`.
- `myfiles_hub_bot.py` does **not** follow this BOT_ID pattern (its own
  token/DB resolution is untouched) — see `bots.README.md`'s own note.

## Known follow-up, not fixed yet

- `content_scope`'s course/level/subject match assumes those three fields
  are enough to uniquely scope a faculty's access. If "limited, not
  exclusive" ever needs to mean *less than a whole subject* (e.g. a
  preview of specific chapters) — a real, still-open ambiguity — entries
  will need an optional chapter/topic-level restriction added. Don't build
  that speculatively; add it only once a concrete case actually exists.
- **The `.docx` MCQ extractor is now a real, deterministic tool**
  (`telegram/tools/convert_faculty_mcq_docx.py`, see
  `FACULTY-MCQ-TEMPLATE.md` for the format it expects) — but
  `csarunchouhan`'s existing 20 MCQs were hand-extracted *before* that tool
  existed, not (yet) re-run through it. `own_content.status:
  "ingested_demo_batch"` still honestly reflects that only ~20 of his
  ~375 total MCQs are usable. New faculty content going forward should go
  through the deterministic tool, not be hand-extracted the way his was.
- Wiring `own_content.status` to flip automatically once a faculty's
  catalog is built, rather than hand-edited.
- `capranav`'s own Revision Material (2 PDFs) is still `not_ingested` —
  see `bots.README.md`'s own "known gap" note.

See `telegram/database/README.md` for the shared DB/dashboard, and
`telegram/tools/manage_bots.py` for starting/stopping every bot at once —
neither existed when this file was first written; both are done now.
