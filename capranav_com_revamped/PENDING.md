# Pending work: capranav.com

> **Superseded for agent work by `AGENT-HANDOFF.md`** (2026-09-26): self-contained, with rules, file paths, commands and acceptance tests. This file stays as the short owner-facing list.

Updated 2026-09-25. Grouped by who has to act. Finished work is in PROJECT-LOG.md; design detail is in the
per-topic documents named in each line.

## Needs Pranav (dashboard, keys or a decision)

| # | Item | Why it is waiting | Doc |
|---|---|---|---|
| 1 | Cloudflare dashboard: Bot Fight Mode, Always Use HTTPS, site-wide rate-limit rule, spoofed-crawler rule, Cloudflare Access on `/admin`, confirm the plan | Zone settings the repo cannot change | BOT-PROTECTION.md |
| 2 | Turnstile widget (site key and secret) | Needs your Cloudflare account | BOT-PROTECTION.md |
| 3 | Submit `sitemap.xml` in Google Search Console and Bing Webmaster Tools (verify the domain) | Needs your Google and Microsoft accounts. IndexNow has already been pinged for Bing (see SEO.md) | SEO.md |
| 4 | Off-site signals for ranking: link to capranav.com from the VC Gurukul site, from each YouTube video description and channel About, LinkedIn, Instagram, Telegram | Only you can edit those; search engines weigh outside links heavily | SEO.md |
| 5 | Keep a copy of the Razorpay and email-token secrets in a password manager | Cloudflare cannot show them back | BACKUPS.md |
| 6 | Download a DNS zone export from the dashboard (DNS > Records > Export) and store it | The repo has only a partial snapshot | BACKUPS.md |
| 7 | Decide: which AI training crawlers to keep allowing (GPTBot, ClaudeBot) and whether to block CCBot, Bytespider, Amazonbot | Business call | BOT-PROTECTION.md |
| 8 | Review the 4 Shorts I picked; send more video links | I chose them from titles and hashtags | VIDEOS.md |
| 9 | Question Bank e-book: bring checkout back to this site, or keep VC Gurukul's store | Business call | PROJECT-LOG.md |
| 10 | What you meant by "1% at all levels"; whether to publish school marks; a link to proof (rank certificates, LinkedIn) | Not answered yet | SEO.md |
| 11 | Where the 1lavya.com site's repo lives, so its "Did you like this? Student or faculty?" landing can be built | Not in this workspace | SEO.md |
| 12 | Real-phone check of Videos, Topics and Must Practice | I tested with browser emulation only | PROJECT-LOG.md |
| 13 | Confirm the data contact address: I published **admin@1lavya.com** (your message said "admin@1lavya.oc", which is not a valid domain) | Wording lives in `tools/site_notices.py`; change it there and re-run the builds | tools/site_notices.py |
| 14 | When the September batch opens: add the product to `worker/lib/products.js` and the pricing page, and the course picker on the homepage. The FAQ, llms files and search descriptions no longer name attempts, so they need no change | The two current batch names (Jan'27, May'27) are real product names tied to orders, so they stay in the course picker and pricing table | PROJECT-LOG.md |

## Next builds (I can do these once you say go)

| # | Item | Notes |
|---|---|---|
| 1 | **Login without personal data (passkeys)**, then move full answers, bulk downloads and the Excel sheets behind it | You said you would describe this next. The biggest remaining copy-protection step |
| 2 | Per-topic and per-question public pages (about 400 topic pages, plus question pages without answers), added to the sitemap | The strongest search and AI visibility gain still available |
| 3 | Remaining Must Practice units: AS 13, 19, 26, 28, then the other chapters (AS 16 is live but only formula-reviewed) | Each unit needs the same duplicate and diversity review |
| 4 | Canary entries and per-account watermarks | Lets a copy be proven |
| 5 | Turnstile wired into login, contact and admin forms | Needs item 2 above |
| 6 | Videos in D1 with an admin form; upload dates for video markup; transcripts | Design is in VIDEOS.md |
| 7 | Stricter Content-Security-Policy (report-only first) | BOT-PROTECTION.md |
| 8 | A 1200x630 social-share image; Anatomy filters as checkboxes; Cloudflare Web Analytics | Small |
| 9 | Off-site copy of backups beyond Cloudflare (for example a weekly pull to a second location) | BACKUPS.md |
| 10 | Test-restore drill on a calendar (quarterly) | BACKUPS.md |

## Known limits (not bugs)

* Nobody can guarantee a top search or AI ranking. The on-page, structured-data and discovery work is done; ranking
  also depends on outside links, time and competition (SEO.md).
* The same-site guard on data files stops naive scripts, not a determined scraper (BOT-PROTECTION.md).
* Rate limits are per IP and per Cloudflare location.
