# 1LAVYA Faculty Search — sales-agent bots (sample build, 2026-08-24)

## What this is

1LAVYA is building a **Telegram sales-agent bot for each client institute**, on the
same model as the faculty study/exam bots elsewhere in `telegram/`: one bot process +
one BotFather token + one content source per client, all running the same code.

**Client context (confirmed by Pranav, 2026-08-24):** every website listed in
`website_links.txt` — `coceducation.com`, `vcgurukul.com`, `bbvirtuals.com`,
`vsmartacademy.com` — is a **paying 1LAVYA client** for this product, not a competitor
being profiled. Since these institutes couldn't hand over structured course data
directly, 1LAVYA mirrored each client's own public website with `wget`/`wget2` (see
each client's own `wget-log.txt`/`mirror-status.json`) as a stand-in for that intake
call. Per Pranav: **1LAVYA is entering into an agreement with each institute** under
which their public site content becomes the source for their own bot (and,
prospectively, a cross-institute comparator bot students can use to compare faculties
— not built yet, see "Not built yet" below). `coceducation/SCRAPING-INCIDENT-CASE-STUDY.md`
is a security write-up 1LAVYA prepared to hand back to each site owner, using this same
mirroring exercise as evidence for why they should harden their own sites.

**Only `coceducation` has a real, built catalog so far** — the other three clients'
mirrors are thinner (see their own folders) and haven't been run through an extraction
pipeline yet.

## Architecture

```
telegram/comparator/sales-agent/
  website_links.txt              -- the 4 client sites
  <client>/
    site-mirror/                 -- raw wget mirror (gitignored, local only)
    mirror-status.json           -- how/when it was pulled
    client_config.json           -- display name, token env var, file paths
    catalog.json                 -- ★ the bot's actual knowledge base (committed)
    sales_agent.db               -- this client's OWN sqlite log (gitignored)
    extract_catalog.py           -- site-mirror/ -> catalog.json (coceducation only, so far)

telegram/bots/
  sales_agent_bot.py             -- ONE script, reused for every client
  smoke_test_sales_agent_bot.py  -- permanent regression checks (run after any change)
```

**Why `catalog.json`, not the raw HTML mirror, is what the bot reads:** the mirrored
pages are ~900KB each (inlined CSS/JS, a repeated "related products" carousel) — no
bot could search or answer from 421 of those directly. `extract_catalog.py` parses out
just the real per-course facts (title, faculty, price/MRP/discount, purchase options,
the highlights table, and the real `coceducation.com/course_details/<slug>` URL) into
one small JSON file. **`catalog.json` is generated — never hand-edit it.** Re-run the
extractor after a fresh site mirror instead.

**Why each client gets its own `sales_agent.db`, not the shared platform `platform.db`:**
Pranav's explicit instruction (2026-08-24) — each institute's bot interaction data
(searches, course views, buy-link clicks) stays in its own file, not pooled with
1LAVYA's own flagship-bot data or another client's.

## Running the sample bot (coceducation)

```bash
# 1. Rebuild the catalog if the site mirror has changed:
.venv/Scripts/python telegram/comparator/sales-agent/coceducation/extract_catalog.py

# 2. Set a REAL BotFather token (get one from @BotFather on Telegram):
export SALES_AGENT_COCEDUCATION_BOT_TOKEN="123456:ABC-real-token-here"

# 3. Run it:
.venv/Scripts/python telegram/bots/sales_agent_bot.py
```

Without a real token in that env var, the bot loads its catalog and logs a clear
warning, then refuses to call Telegram — it will not silently crash with a cryptic
auth error. `client_config.json`'s `bot_token_placeholder` value
(`REPLACE_WITH_COCEDUCATION_BOT_TOKEN`) is a placeholder only, exactly as asked; there
is no real token anywhere in this repo.

**Smoke test** (no real Telegram connection needed):
```bash
.venv/Scripts/python telegram/bots/smoke_test_sales_agent_bot.py
```

## What the bot actually does

- `/start` → main menu: 🔍 Search a course · 📚 Browse by exam (CA/CMA/CFM/Other) ·
  ℹ️ About · 📞 Contact.
- Free-text questions ("Santosh Kumar accounting", "strategic financial management")
  are fuzzy-matched (`rapidfuzz`) against every course's title+faculty; top matches
  shown as buttons.
- Tapping a course shows a card: faculty, price with MRP/discount if any, lecture
  count/duration/language, doubt-solving mode, and the real purchase options (mode of
  distribution, attempt) scraped straight from that course's own page.
- **"🛒 Buy Now / View Full Details"** is a real Telegram URL button pointing at that
  exact course's real page on `coceducation.com` — this bot never takes a payment
  itself; buying always means "go complete it on the client's own site," per how this
  was scoped.
- Every search, browse, and course view is logged to `sales_agent.db` (student's
  Telegram user id + what they looked at) — nothing beyond that is collected.

## Adding another client (vcgurukul / bbvirtuals / vsmartacademy)

1. Confirm/refresh that client's `site-mirror/`.
2. Write (or adapt `coceducation/extract_catalog.py` into) an extractor for that
   site's own HTML structure — **it will very likely differ** from coceducation's
   theme (different CMS, different markup), so don't assume the same selectors apply.
3. Add `<client>/client_config.json` (copy coceducation's, change the slug/token-env/
   display name).
4. Run `SALES_AGENT_CLIENT=<client> .venv/Scripts/python telegram/bots/sales_agent_bot.py`
   with that client's own real token in its own env var.

No change to `sales_agent_bot.py` itself should be needed for a same-shaped catalog.

## Not built yet, named honestly

- **vcgurukul / bbvirtuals / vsmartacademy catalogs + bots** — only coceducation has
  been built end-to-end so far (it had the fullest mirror).
- **The cross-institute "comparator" bot** Pranav described (where a student compares
  faculties across multiple institutes in one place) — a materially different product
  from "one bot per client answering about that client only," not started.
- **Process management / `bots.json` registration** — every other live bot on this
  platform is managed via `telegram/tools/manage_bots.py` + `bots.json`
  (start/stop/restart, heartbeats, the down/up alert watcher). This sample bot is
  standalone and isn't wired into that yet — worth doing before any of these go live,
  so they get the same crash-recovery/monitoring as the rest of the platform.
- **Formal legal agreement text with each institute** — Pranav says this is "already
  entering into agreement"; this repo has no signed-agreement artifact for any of the
  4 clients. Confirm the coceducation agreement is actually finalized before this
  sample bot (or its data) goes anywhere client-facing or public.
