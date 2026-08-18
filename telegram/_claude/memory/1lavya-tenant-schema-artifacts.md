---
name: 1lavya-tenant-schema-artifacts
description: "Where the 1LAVYA platform's tenant/wallet/DB schema design actually lives on disk — tenants.json, schema.sql, and their READMEs, built 2026-08-09"
metadata: 
  node_type: memory
  type: project
  originSessionId: eff70d38-31a6-4cc7-baf2-a93b1aa25479
  modified: 2026-08-09T13:32:50.500Z
---

Built 2026-08-09 in response to [[1lavya-centralized-account-model]] and
[[1lavya-faculty-onboarding-model]] — the concrete schema/config artifacts, not yet
wired into any bot:

- **`telegram/config/tenants.json`** + **`tenants.README.md`** — the plug-and-play
  faculty registry Pranav asked for: one JSON entry per faculty (`tenant_id`,
  `bot_token_env` pointing at `telegram/.env`, `content_scope` as the filter against
  the shared 1LAVYA catalog, `onboarding_fee`, `own_content.status`). Real entries
  already populated for `1lavya-studyhub`, `1lavya-examhub`, `capranav`,
  `csarunchouhan`, matching the facts in [[1lavya-faculty-onboarding-model]]. The
  core design rule: **adding/editing `content_scope` is the entire "instant shared-
  content access" mechanic — zero code changes**; a faculty's own content is
  deliberately separate, gated by `own_content.status` ("not_ingested" until a real
  extraction pipeline runs), never conflated with the instant path.
- **`telegram/database/schema.sql`** + **`database/README.md`** — the central,
  cross-tenant DB: `students` (shared identity, Telegram user ID keyed),
  `wallet_ledger` (append-only, balance always derived via `SUM(amount)`, never
  stored — the anti-corruption rule from the 2026-08-09 feedback round), `payments`
  (idempotent via `gateway_txn_id UNIQUE`, covers both the faculty ₹5,000 onboarding
  fee and student credit-pack recharges). Also documents the live-DB (WAL mode) +
  5-second-delay snapshot-DB mechanic via SQLite's online backup API, satisfying
  [[1lavya-bot-infra-plan]]'s locked requirement, plus the `content_owner` tagging
  convention (`"1lavya"` vs `"<tenant_id>"`) to be applied to the existing catalog
  scripts later.
- **`telegram/.env` / `.env.example`** gained `FACULTY_CAPRANAV_BOT_TOKEN` /
  `FACULTY_CSARUNCHOUHAN_BOT_TOKEN` placeholders — real values go in `.env` only once
  BotFather actually issues each faculty's token (neither exists yet).

**Explicitly not done yet** (see `tenants.README.md`'s own "what still has to be
built" section): no bot reads `tenants.json` or `schema.sql` at runtime — the 3
existing bots are still single-tenant hardcoded scripts. Making them tenant-aware is
the next real build step, not this pass.
