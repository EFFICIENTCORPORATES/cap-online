# `bots.json` — the master bot mapping

Added 2026-08-10, alongside a full backend build (unified DB, process
manager, deterministic content pipeline, analytics dashboard) prompted by a
concrete need: CS Arun Chouhan wanted ONE bot combining Study Hub + Exam
Practice Hub, but CA Pranav wanted **TWO separate bots** (a Study bot and an
Exam bot). `tenants.json` (see `tenants.README.md`) used to conflate
"tenant" with "bot identity" (one `bot_token_env` per tenant entry) — that
broke the moment one faculty needed more than one bot. This file fixes that
by answering a different question entirely.

**`tenants.json` answers "what does this faculty teach"** (content_scope,
exam_content — content, not process). **`bots.json` answers "what bot
processes exist, and which token/script runs each one."** One tenant can
map to many bots here (Pranav: `capranav-study` + `capranav-exam`, both
`tenant_id: "capranav"`) or exactly one (Arun: `csarunchouhan`, one row).
Onboarding a new bot for an already-onboarded faculty is a pure `bots.json`
edit — no code, no `tenants.json` change.

## Field contract

| Field | Meaning |
|---|---|
| `bot_id` | Stable slug, one per **bot process**. Equals `tenant_id` when a tenant has exactly one bot (keeps the older `TENANT_ID` env var working as a fallback — see below); gets a `-study`/`-exam` suffix when a tenant has more than one. |
| `tenant_id` | FK into `tenants.json`. `null` for `1lavya-myfileshub` — MyFiles Hub is account-scoped, not content-scoped, so it has no tenant relationship at all. |
| `kind` | `"study"` (runs `study_hub_bot.py`) \| `"exam"` (runs `exam_hub_bot.py`) \| `"unified"` (runs `faculty_bot.py`, composes both) \| `"myfiles"` \| `"dashboard"` (added 2026-08-10, `dashboard_server.py` — not a Telegram bot, see below) \| `"watcher"` (added 2026-08-10, `watcher_bot.py` — also not a Telegram bot). |
| `display_name` | Human name for logs/dashboard. |
| `bot_username` | The registered `@...Bot` handle once known, else `null`. `null` for `"dashboard"`/`"watcher"` kinds — neither ever registers with BotFather or receives Telegram updates. |
| `bot_token_env` | Env var name holding the real token — never the token itself. Real value lives in `telegram/.env` (gitignored). `null` for `"dashboard"` (doesn't talk to Telegram at all) and for `"watcher"` (it sends via a DIFFERENT bot's token, hardcoded in `watcher_bot.py` to look up `1lavya-myfileshub`'s entry — see that script's own docstring for why it's not just another `bot_token_env` here). |
| `script` | Which file this bot_id runs, resolved from `script_dir` (below). |
| `script_dir` | Added 2026-08-10, optional, defaults to `"bots"` — the folder under `telegram/` that `script` resolves against. Only `1lavya-dashboard` uses a non-default value (`"tools"`, since `dashboard_server.py` isn't a Telegram bot script) — see `manage_bots.py`'s `resolve_script_path()` for why this exists as a real field instead of a relative `"../tools/..."` path (that was tried first and silently broke "already running" detection — see that function's own docstring). |
| `status` | `"active"` \| `"pending_bot_registration"` (config exists, no real token yet) \| `"inactive"`. `manage_bots.py` only starts `"active"` bots when run with no specific bot_id. `1lavya-platform-watcher` is `"inactive"` until `telegram/config/alerts.json`'s `admin_chat_ids` is filled in — see `database/README.md`. |
| `from_email` | Added 2026-08-11 for the student report pipeline's Cloudflare Email Service integration (`telegram/database/cf_email.py`/`report_delivery.py`) — this bot's own dedicated, unmonitored sending address (e.g. `studyhub@1lavya.com`). One shared domain, different local parts per bot (Pranav's confirmed choice, 2026-08-11 — Cloudflare's onboarding/verification is per-DOMAIN, so this needed no extra Cloudflare setup per bot). `null`/absent for any bot that never sends a report email (dashboard/watcher/broadcaster/myfiles) — `report_delivery.py`'s `resolve_from_address()` falls back to a generic `reports@1lavya.com` rather than crashing if one's ever missing. |

## How a bot process resolves its own identity

Every bot script (`study_hub_bot.py`, `exam_hub_bot.py`, `faculty_bot.py`)
reads a `BOT_ID` environment variable at startup (default `"1lavya-studyhub"`
/ `"1lavya-examhub"` respectively — today's original single-tenant
behavior), looks up that `bot_id` here, then uses the row's `tenant_id` to
load the actual content config from `tenants.json`. **`TENANT_ID` still
works as a fallback** for any bot whose `bot_id` equals its `tenant_id` —
true for every single-bot tenant — so existing launch commands written
before this file existed didn't break. Only a multi-bot tenant (Pranav)
actually needs the newer `BOT_ID` name, since `TENANT_ID=capranav` alone
would be ambiguous (which of his two bots?).

```powershell
# single-bot tenant -- both of these resolve identically:
$env:BOT_ID = "csarunchouhan"; python telegram\bots\faculty_bot.py
$env:TENANT_ID = "csarunchouhan"; python telegram\bots\faculty_bot.py

# multi-bot tenant -- BOT_ID is required, TENANT_ID=capranav alone is ambiguous:
$env:BOT_ID = "capranav-study"; python telegram\bots\study_hub_bot.py
$env:BOT_ID = "capranav-exam";  python telegram\bots\exam_hub_bot.py
```

Or start every `active` bot at once: `python telegram\tools\manage_bots.py start`
— see that script's own docstring for start/stop/restart/status and exactly
what "graceful stop" means on Windows.

## `myfiles_hub_bot.py` is listed here but not migrated

It keeps its own token/DB resolution entirely (untouched, still
self-contained, still reads `TELEGRAM_MYFILES_BOT_TOKEN` directly) — it's
listed in `bots.json` purely so `manage_bots.py` and the analytics
dashboard can start/stop/see it alongside every other bot. It does write a
heartbeat to the shared platform DB (a small, additive change — see its own
`MYFILES_BOT_ID` constant) but does not use `BOT_ID`/`bots.json` for
anything else. A full migration is possible later but wasn't needed to
solve the actual problem this file was built for.

## Current roster (as of 2026-08-10)

| bot_id | tenant_id | kind | status |
|---|---|---|---|
| `1lavya-studyhub` | `1lavya-studyhub` | study | active |
| `1lavya-examhub` | `1lavya-examhub` | exam | active |
| `1lavya-myfileshub` | *(none)* | myfiles | active |
| `csarunchouhan` | `csarunchouhan` | unified | active |
| `capranav-study` | `capranav` | study | active |
| `capranav-exam` | `capranav` | exam | active |
| `1lavya-dashboard` | *(none)* | dashboard | active |
| `1lavya-platform-watcher` | *(none)* | watcher | inactive (needs `alerts.json` filled in first) |

All 6 real bots were confirmed running by Pranav himself as of 2026-08-10
(`status: "active"` here now genuinely means "currently running," not just
"configured and ready" — this note previously said the opposite for
Pranav's two bots specifically, which was true when first written and is
no longer true; see `manage_bots.py status` or the dashboard's heartbeat
column for the current, authoritative answer rather than trusting either
version of this sentence).

## Known gap, honestly

Pranav's original ask included serving his own Revision Material (2
handwritten-notes PDFs, AS 2 and AS 10 — see
`telegram/assets/faculty/capranav-ca-inter-advacc/`). Those files are **not
yet ingested** into the Study Hub catalog — his `capranav-study` bot is
live and correctly scoped to CA Inter Advanced Accounting, but its
Revision Material category is still empty for everyone, him included (see
`tenants.json`'s `own_content.status: "not_ingested"` for his entry).
Wiring this in properly needs the `content_owner` tagging convention
(`schema.sql`'s own note) actually applied to `build_master_catalog.py`
first, so his 2 PDFs are attributed to him rather than silently merged into
the anonymous shared pool — deliberately not done in this pass, flagged
rather than rushed.
