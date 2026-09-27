# capranav.com: handoff for the next agent

Written 2026-09-26 by the previous Claude Code session, for another AI agent to read and then continue the work.
This file is self-contained. It says what the site is, the rules you must follow, what is finished, and what is
pending, in priority order, with the exact files, commands and tests for each task.

**Path:** `D:\EffCorp_Projects\cap-online\capranav_com_revamped\AGENT-HANDOFF.md` (git root `D:\EffCorp_Projects\cap-online`,
remote `EFFICIENTCORPORATES/cap-online`, branch `main`).

## 0. Read first (in this order)

1. `D:\EffCorp_Projects\cap-online\CLAUDE.md`: repo-wide rules. Sections 2 (working rules) and 4-5 matter most. The long
   history from section 6 onward is mostly about other pillars (books, Telegram); this site is the `capranav_com_revamped/` folder.
2. This file.
3. `PROJECT-LOG.md` (newest entry first; read the top five entries), then `PENDING.md` (the older, shorter list this file supersedes).
4. Only when the task needs it: `SEO.md`, `BOT-PROTECTION.md`, `BACKUPS.md`, `SECURITY.md`, `TOPICS-EXPLORER.md`, `VIDEOS.md`,
   `ANATOMY.md`, `DATABASE-BACKUP.md`.

**Owner:** CA Pranav Pratik Tulshyan (faculty). He decides scope and wording. When unsure about anything about his profile, career,
claims or money, **ask him; do not guess.** He has said this several times.

## 1. What the site is

capranav.com is the live site of a CA Inter Advanced Accounting faculty: courses and books for sale, free exam analysis
(which topics ICAI asks most), must-practice questions, videos and Shorts, and a student dashboard. It runs entirely on Cloudflare.

| Piece | Detail |
|---|---|
| Code | Worker `capranav` (`worker/index.js`, `worker/lib/*.js`) plus static files in `public/` (Worker Assets) |
| Database | D1 `capranav-platform` (id `03830ea8-b539-480b-b106-0743aeda1b1f`): students, sessions, orders, entitlements, contact messages, admin users, and the 27-table anatomy set (`aa_*`) |
| Files | R2 `capranav-vault` (2 book PDFs + 98 published study PDFs), R2 `capranav-backups` (backups, see `BACKUPS.md`) |
| Email | Cloudflare Email Service (login codes, receipts, backup-failure alert) |
| Payments | Razorpay (secrets are Worker secrets, never in git) |
| Deploy | `cd capranav_com_revamped && npx wrangler@4.137.0 deploy` (pin the version, see section 6) |
| Live version at handoff | `527f91c0-7b64-46c9-9452-54ea29a045fa` |
| Public pages | `/`, `/about-us`, `/faq/`, `/topics/`, `/practice-with-pranav-bhaiya/`, `.../must-practice/`, `/videos/`, `/anatomy/`, `/pricing-details`, `/contact-us`, policies, three slide pages; private: `/admin`, `/dashboard`, `/reader` |

Everything the site publishes about analysis is computed from data in `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/`
(`descriptive_topic_priority.json`, the `mcq-library/`, and the workbook `ca_inter_descriptive_topic_priority_v1.xlsx`, which is gitignored)
by the scripts in `tools/`. **Pages are generated; edit the generators, not the output**, or the next run overwrites your change.

### Generators (all idempotent; run from `capranav_com_revamped/`)

| Script | Writes | Run when |
|---|---|---|
| `tools/build_topics_explorer_data.py` | `public/topics/data/*.json` | topic ranking or workbook data changes |
| `tools/build_must_practice_data.py` | `public/practice-with-pranav-bhaiya/must-practice/data/*.json` | a unit's list, weights or hand exclusions change |
| `tools/build_seo_static.py` | crawler-readable HTML blocks in Topics, Videos, Must Practice | after either data build |
| `tools/build_faq.py` | `public/faq/index.html` | data or profile facts change |
| `tools/apply_seo_meta.py` | `<head>` blocks (title, description, canonical, share tags, JSON-LD) on every page and `sitemap.xml` | any page added or retitled: edit its `PAGES` table |
| `tools/build_discovery_files.py` | `sitemap.txt`, `llms-full.txt`, `humans.txt`, IndexNow key file | after the three above |
| `tools/apply_legal_notice.py` | copyright and data-source notices in footers and the Terms clause | wording change in `tools/site_notices.py` |
| `tools/indexnow_ping.py` | tells Bing about every public URL | after each content deploy |
| `tools/qa_smoke.py` | nothing (tests) | after **every** deploy, see section 5 |

Standard content deploy: build scripts, then `npx wrangler@4.137.0 deploy`, `python tools/qa_smoke.py --browser`, `python tools/indexnow_ping.py`,
then commit and push.

## 2. Rules and locked decisions (do not revisit without asking Pranav)

From `CLAUDE.md`: Markdown by default; **no binary files in git** (images, office files, PDFs are gitignored); UTF-8 only, never NUL bytes; after any
structural change (files or folders added, moved, deleted) run `python tools/health_check.py` then `python tools/file_index.py` at the repo root
and fix what they flag; end every session with a short dated entry at the top of `_claude/memory/project_log.md`; ask at the first real blocker; other
AI sessions work in this repo concurrently, so check `git status` and `git log` before assuming a file is stale. Commit messages end with the
`Co-Authored-By` line your harness specifies. The user wants work **pushed to git** (`git push origin main` works from this machine).

Decisions Pranav has made:

* **Public layer vs gated layer.** Public and crawlable (this earns search and AI visibility): topic names, ranks, marks, question text, source,
  "why practise", FAQs, video titles. Gated behind a free login (planned): full model answers, bulk downloads, full datasets, study PDFs. The static
  crawler-readable blocks deliberately **omit answers**. Everyone (crawlers and users) sees the same page; never show full content to "verified bots" only
  (cloaking risk, and spoofable).
* **AI search and answer bots are welcome** to read and show excerpts with attribution. Copying, scraping, mirroring or republishing is **not permitted**.
  The exact wording is in `tools/site_notices.py` and is on the Terms page, footers, FAQ, `llms.txt`, `llms-full.txt`, `robots.txt` and the Excel export.
* **"Powered by 1LAVYA"** on every analytical page (Topics, Anatomy, practice hub, Must Practice, FAQ) and in the Excel export, linking to `1lavya.com` with UTM
  parameters. **The Videos page says "Powered by MERA BRAND" as plain text, no link.**
* **Two contacts (confirmed 2026-09-27):** `me@capranav.com` for anything about the site, the CA Inter Advanced Accounting syllabus, courses and enquiries (incoming capranav.com mail forwards to Pranav's Gmail); `admin@1lavya.com` only for faculty or institutes wanting to white-label the important-question lists and syllabus mappings. Both live in `tools/site_notices.py`. Outgoing mail already uses capranav.com senders (`login@`, `orders@`, `contact@`, `alerts@`).
* **Never name clients** (audit clients). Describe them: "Fortune 500", "one of India's largest metals and mining groups".
* **No "best faculty" style claims.** Pranav now holds a Certificate of Practice (since June 2026), so ICAI advertising rules apply. State verifiable
  facts (ranks, dates, employers). No offers of services, prices for practice work, or solicitation.
* **No exact attempt names in descriptive text** ("upcoming attempts"). The only places that name batches are the real product names `Jan'27 batch` and
  `May'27 batch` in `worker/lib/products.js`, `public/pricing-details.html` and the homepage course picker (`public/assets/app.js`), because orders are tied to them.
* **Must Practice lists are always ten questions**, computed by rule, never hand-picked, with documented hand exclusions. Read
  `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/MUST-PRACTICE-RULES.md` before touching a list.
* Confirmed career facts (usable on the site): AIR 1 CA Foundation (CPT), AIR 1 CA Intermediate (IPC), AIR 5 CA Final (Nov 2018 attempt), all levels first attempt,
  91 marks in Advanced Accounting, AIR 3 B.Com (Hons.) DU-SOL; EY articleship Mar 2016 to Mar 2019; Indian Oil May 2019 to May 2024 (SAP accounting, quarterly closing,
  Ind AS 115 and 116); Ministry of Petroleum and Natural Gas May 2024 to May 2025 (Assistant Director, Finance, PPAC); virtual CFO for D2C startups and AI
  implementations since mid-2025; practising CA firm since June 2026; teaching through VC Gurukul, Noida and (accounting and GST for professionals) Newton of Accounts.
  His earlier bio said "5 years finance and accounts"; the dates give 5 + 1 (+ 3 articleship), so the site states dates, not a total. Do not publish a total without asking.

## 3. State at handoff (what is done)

Details are in `PROJECT-LOG.md`. In short: security headers and per-IP OTP limit; mobile layout fixed (a leaked global `table{min-width}` in `anatomy.css` was the root cause);
Must Practice for AS 2 and AS 10 (ten questions each, duplicate and diversity rules); `/videos/` (7 videos, 4 Shorts, auto-scroll feed, data in `public/videos/videos.json`);
`/topics/` explorer (filters, tick-many Module/Chapter/Unit, sort and reverse, Excel and CSV, ID decoder; ranks reproduce the workbook for all 104 PYQ-marked topics);
SEO (head blocks, JSON-LD, sitemap.xml and sitemap.txt, robots.txt naming crawlers, llms.txt, llms-full.txt, humans.txt, IndexNow, a 25-question `/faq/`);
the profile on `/about-us`; bot guards (bulk data files and anatomy API same-site only plus rate limits); backups (nightly Worker cron to `capranav-backups`, 6-hourly PC export
uploaded off-machine; first nightly run verified at 2026-09-25 21:30 UTC); copyright and data-source notices; internal links cleaned so crawlers see no 307 redirects.

## 4. Pending work

### 4A. Blocked on Pranav (you can prepare; you cannot finish alone)

| # | Item | What you can do meanwhile |
|---|---|---|
| A1 | **Done 2026-09-27 by API**: HTTPS, Bot Fight Mode, spoofed-crawler rule, rate limit (plan is Free: 100 req/10 s/IP; 20 blocked normal page loads). **Still open:** Cloudflare Access on `/admin*` and `/api/admin/*` (needs the email Pranav wants to allow); token `ectpl-capranav-prod-bot-protection` via `ectpl-creds --as 1lavya-agent` (load the key from the User env var) | See PROJECT-LOG 2026-09-27 |
| A3 | Submit `sitemap.xml` in **Google Search Console** and **Bing Webmaster Tools**; verify the domain | Needs his Google/Microsoft accounts. IndexNow (Bing) is already pinged |
| A4 | **Backlinks**: capranav.com from the VC Gurukul site, every YouTube video description and channel About, LinkedIn, Instagram, Telegram | Draft the exact link text and description lines for him to paste |
| A5 | Copy the Razorpay and email-token secrets to a password manager; download a DNS zone export (dashboard, DNS, Records, Export) and keep it | See `BACKUPS.md` |
| A6 | Decide which AI **training** crawlers stay allowed (GPTBot, ClaudeBot are allowed now) and whether to block CCBot, Bytespider, Amazonbot (all currently allowed) | Recommendation is in `BOT-PROTECTION.md` |
| A7 | **Login without personal data (passkeys)**: Pranav said he will describe the design in a separate message. Do not start B1 until he does | See B1 for the open questions |
| A8 | Review the 4 Shorts I chose from titles and hashtags (not watched): `0G3eN7OGzj8`, `jUzJAZrPCwE`, `BAnBpU0o4Nc`, `Q1AryOeDKw0`; send more links | `videos.json` schema is in `VIDEOS.md` |
| A9 | Question Bank **e-book checkout**: bring it back to this site or keep VC Gurukul's store (temporary since 2026-09-23) | The switch is described in a comment in `pricing-details.html` and `worker/lib/products.js` |
| A10 | Unanswered profile questions: what "1% at all levels" meant; whether to publish school marks (85.6, 82.0, 86.2 percent); a link to proof (rank certificates, LinkedIn); the public URL for Newton of Accounts | Leave them out until answered |
| A11 | Where the `1lavya.com` site's repo lives (for B9) | The Workers list shows `main1lavya-web` and `main1lavya-web-in`, which may be it; confirm before touching |
| A12 | Read the Terms clause once (it is a legal document) | Wording is in `tools/site_notices.py`; contacts settled 2026-09-27 |
| A13 | **Real-phone check** of Videos, Topics, Must Practice, FAQ (all testing so far used Edge emulation) | Give him a short checklist |
| A14 | **September batch**: when it opens, add the product and price | Edit `worker/lib/products.js`, `public/pricing-details.html`, the picker in `public/assets/app.js`. FAQ, llms files and meta text need no change |

### 4B. Buildable now, in priority order

**B1. Free login without personal data, then gate answers and bulk data** (start only after A7).
Goal: students get answers and downloads without giving an email or phone; scrapers cannot mass-harvest. Options already discussed with Pranav:
passkeys (WebAuthn; the account is a public key; best UX) with an authenticator-code (TOTP) fallback. Trade-offs to keep in the design: anonymous accounts are cheap
to create, so the protection must come from per-account and per-IP quotas, Turnstile at signup (needs A2), and per-account watermarks (B4). Existing paid accounts use
email codes (`worker/lib/session.js`); keep those separate. Data to gate: the `answer_html` fields in `public/practice-with-pranav-bhaiya/must-practice/data/*.json`
(today public behind the same-site guard only), the Excel sheets in `public/topics/data/sheets/`, and the A-B-C-D and question-topic-map sheets. Serve gated data from the
Worker after a session check (move files out of `public/` into R2 or the Worker; keep the URL contract the pages use, or update `must-practice.js` and `topics.js`).
Must not hurt AI ranking: the public teaser (question, topic, why, a three-line approach) stays visible to everyone. Acceptance: logged-out users see teasers only; a bare
script gets nothing useful; a logged-in browser gets answers; crawlers still get 200 with the teaser; `qa_smoke.py` still passes (update its data-file expectations).

**B2. One public page per topic (400) and per question (no answers), with their own titles, descriptions, JSON-LD and sitemap entries.**
This is the largest remaining search and AI visibility gain: today all topic information is on one page. Suggested URLs `/topics/<topic-id>` (for example
`/topics/M2-C5-U2-T2.6`) and `/questions/<book-id>`. Generate as static HTML from `topics.json` and the Must Practice libraries with a new script beside
`build_seo_static.py`; add every page to the sitemap (extend `apply_seo_meta.py`'s `sitemap_pages()` or add a second generated sitemap file and list both in `robots.txt`).
Each topic page: name, chapter and unit, marks and rank by paper type, which papers asked it (question numbers), the Study Material page, links to related questions and the
Must Practice list, breadcrumb markup. Keep the copyright and 1LAVYA footers. Watch the Worker Assets file-count limit (20,000 files free plan) and the `run_worker_first` list in `wrangler.toml`
(do not put these pages under the guarded data paths). Acceptance: `qa_smoke.py` crawl finds them all with no redirects; each has a unique title.

**B3. Publish more Must Practice units.** AS 13, AS 16, AS 19, AS 26, AS 28 first (all visible as "coming soon" in the picker), then the other chapters (36 units in `UNITS` of
`tools/build_must_practice_data.py`, only two published). Per unit: add the library file entry, run the build, **review the printed ranking for repeats** (the 90 percent text test,
the shared-figures test, the two-per-topic cap), look for parts of one question reissued alone and same-idea repeats under unrelated topic tags, add hand exclusions with a written reason in
`UNITS`, keep the list at ten, and document the exclusions in the table at the bottom of `MUST-PRACTICE-RULES.md`. Then `build_seo_static.py`, deploy, verify the picker and the rows in a browser.
Book page numbers are read from `first_run/output/final_deliverable/CA Inter Advanced Accounts_ The Complete Question Bank_V1.pdf` (a distributed, gitignored file; never regenerate or overwrite it).

**B4. Canary entries and per-account watermarks.** Add a few fake but plausible topics or questions that appear nowhere else, recorded in a private file (not in git), and invisible per-account marks
(zero-width or spacing patterns) in gated downloads, so a copy can be traced and proven. Depends on B1 for accounts.

**B5. Turnstile**: done 2026-09-27 (see PROJECT-LOG). Ask Pranav to send one real contact-form message and request one login code to confirm humans pass.

**B6. Videos: data in D1 and an admin form** (design and SQL are in `VIDEOS.md`); record an upload date per video so `VideoObject` markup is valid; add transcripts or summaries as visible text on `/videos/` (helps AI understanding).
The page reads `/videos/videos.json`; change that one fetch to `/api/videos` and keep `videos.json` as fallback for a release.

**B7. Content-Security-Policy for scripts**, shipped as `Content-Security-Policy-Report-Only` first, collect violations, then enforce (the site uses inline scripts and styles, Razorpay checkout, the pdf.js CDN import, the SheetJS CDN with an integrity hash, the YouTube iframe API). Baseline headers are in `worker/index.js` (`SECURITY_HEADERS`) and `public/_headers`.

**B8. Smaller items.** A purpose-made 1200 by 630 share image (today the portrait photo is used, `OG_IMAGE` in `apply_seo_meta.py`); Anatomy filters as tick-many (needs `handleAnatomyTopics` in `worker/index.js` to accept comma lists, then `public/assets/anatomy.js`);
Cloudflare Web Analytics; a "Newton of Accounts" link once A10 gives a URL; update the About page if Pranav answers A10.

**B9. The 1lavya.com landing.** Every link from capranav.com to 1lavya.com already carries `utm_source=capranav&utm_medium=referral&utm_campaign=powered_by&utm_content=<page>`. On 1lavya.com (a different codebase; needs A11) read those on landing, ask
"Did you like the content on capranav.com? Want more?" then "Are you a faculty who needs this for your own website, or a student who wants to study?", store the answer in the browser only (no personal data), and personalise the page. UTM values can be faked, so use them only to personalise, never for security or billing.

**B10. Backups, second pass.** (a) Exercise the failure-alert email path in `worker/index.js` `runScheduled` (force one failed run in a test and confirm the email arrives from `alerts@capranav.com`). (b) Add an independent copy outside Cloudflare (for example a weekly pull of `capranav-backups` to another location) so an account problem cannot take everything. (c) A quarterly restore drill on a calendar (procedure in `BACKUPS.md`). (d) Check `status.json` weekly; consider an admin-page tile. (e) If the plan is Free, confirm cron and CPU limits are respected (the last three runs were fine).

**B11. Tune and watch the guards.** Watch for real users hitting "Too many requests" (per-IP limits: `RL_DATA` 40/min, `RL_API` 120/min, `RL_DOC` 12/min in `wrangler.toml`; many students behind one college IP share a limit). Rate limits are per Cloudflare location. Every request to the guarded data paths also counts as a Worker invocation (Free plan: 100,000 a day); if traffic grows, reconsider.

## 5. Verification routine (every deploy)

```
cd D:\EffCorp_Projects\cap-online\capranav_com_revamped
python tools/qa_smoke.py --browser        # crawlers 200, data guard, sitemap, no redirects, no sideways scroll
```
Expect `ALL PASSED`. Also open the changed page in a real browser and read it. For layout work, screenshot with Playwright (`channel="msedge"`); code that only "reads right" has been wrong before.
Right after a deploy Cloudflare may serve a cached copy of a static URL for a few minutes: add `?x=<random>` when testing.

## 6. Environment gotchas (each cost time before)

* **Pin wrangler: `npx wrangler@4.137.0 ...`.** Unpinned `npx wrangler` tries to download the newest release and failed with EBUSY on a locked npx cache (it broke the D1 backup for a day). Do not "upgrade" without testing the backup job.
* **Bash heredocs with quotes broke repeatedly** ("unexpected EOF while looking for matching `'`"). Write Python patch scripts to a file with the Write tool and run them, instead of nested heredocs.
* Local dev: `npx wrangler@4.137.0 dev --local --port 8799` (uses a local D1; the anatomy seed was loaded locally earlier). Stop dev servers with PowerShell (`Get-NetTCPConnection -LocalPort 8799 ... Stop-Process`, and `Stop-Process -Name workerd`); `pkill` does not work in this shell.
* Cloudflare returns 403 to the `Python-urllib` user-agent; send a browser user-agent from scripts (`qa_smoke.py` does).
* Shared CSS is global: `public/assets/anatomy.css` is loaded by Anatomy, the practice hub, Must Practice, Topics, Videos and FAQ. A bare `table{min-width:...}` there once made every table on Must Practice 1180px wide. Scope selectors.
* `wrangler.toml` `run_worker_first` and `DATA_PATHS` in `worker/lib/guard.js` must list the same guarded paths.
* Ranking must match the workbook: marks are rounded to 2 places and ties use the workbook's own `officialRank` (see `TOPICS-EXPLORER.md`); RTP questions have no marks, so RTP views rank by times asked.
* The D1 backup job (`tools/backup_d1_snapshot.py`, Windows Task Scheduler "CA Pranav D1 Backup", every 6 hours) and its `database-backups/` folder contain student data: gitignored, never commit.
* Harmless: `warning: LF will be replaced by CRLF` and an occasional `.git/info/refs` message on commit.
* The `telegram/` folder is a migrated-out platform; its `.env` is not for this site.

## 6a. File map

| File | Contents |
|---|---|
| `PROJECT-LOG.md` | Dated history of everything built, newest first, with the reasoning |
| `PENDING.md` | Earlier owner-facing pending list (this file replaces it for agent work) |
| `SEO.md` | Discovery files, structured data, ranking notes, Cloudflare crawler findings |
| `BOT-PROTECTION.md` | Every bot and throttle control, dashboard rules still to apply |
| `BACKUPS.md` | Backup layers, schedules, checks, restore runbook, DNS snapshot, gaps |
| `SECURITY.md` | Findings against the Level 3 recommendations and how each was handled |
| `TOPICS-EXPLORER.md`, `VIDEOS.md`, `ANATOMY.md` | Design of those features |
| `worker/lib/guard.js`, `backup.js` | Bulk-data guard and nightly backup code |
| `tools/site_notices.py` | The copyright and data-source wording, single source |

## 7. Log your work

When you finish a task: add a dated entry at the top of `capranav_com_revamped/PROJECT-LOG.md` (what, why, how verified, what is left), a short one at the top of
`_claude/memory/project_log.md`, update this file's section 4 (remove what is done, add what you found), run the repo-root `health_check.py` and `file_index.py` if you added files, commit, and push.
