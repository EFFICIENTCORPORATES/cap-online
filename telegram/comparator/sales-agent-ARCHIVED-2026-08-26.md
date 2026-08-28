# `telegram/comparator/sales-agent/` — moved out of this repo, 2026-08-26

This folder used to live here (`telegram/comparator/sales-agent/`) and held the
coceducation sales-agent's site mirror, `catalog.json`, `client_config.json`,
`sales_agent.db`, and `extract_catalog.py`.

**It has been moved** to `D:\EffCorp_Products\Main1Lavya\ai-agents\sales-agent\` —
Pranav split this into its own separate 1LAVYA product (distinct from the
`ai-agents/faculty-search/` cross-institute comparator product) and moved its data
outside this repo entirely.

**What did NOT move**: `telegram/bots/sales_agent_bot.py` (the bot script) and
`telegram/bots/smoke_test_sales_agent_bot.py` are still here — they reuse this repo's
shared platform (heartbeats, `manage_bots.py` crash-recovery, rate limiting, the Admin
Portal, backups) rather than duplicating any of it in the product folder. The script
resolves the new external data location via the `SALES_AGENT_ROOT` env var in
`telegram/.env`.

**Known consequence, flagged not fixed**: `ai-agents/sales-agent/` is not currently
inside any git repository, so its data (including `catalog.json`, which used to be
version-controlled here) has no history/versioning and is outside this repo's existing
nightly Cloudflare backup coverage (`telegram/tools/backup_to_cloudflare.py` only
covers paths inside this repo/its known asset folders). Worth a decision from Pranav
on whether that data needs its own backup arrangement.

See `telegram/config/bots.json`'s `coceducation` entry and
`D:\EffCorp_Products\Main1Lavya\ai-agents\sales-agent\README.md` for the current,
correct picture.
