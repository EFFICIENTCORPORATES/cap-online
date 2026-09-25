# Bot protection, throttling and rate limits (capranav.com)

Written 2026-09-25. Goal, in Pranav's words: search and AI crawlers should read the site freely and show it to
their users; people who want to **steal the content** (mirror the site, scrape the data, build a copy) should find
it slow, noisy and not worth it.

The honest limit first: whatever a browser can display, a determined person can save. Nothing on a public site
makes that impossible. The controls below make **bulk** copying slow and detectable, keep the valuable data out of
easy reach, and keep paid content behind login. They do not touch what crawlers need: the HTML pages.

## What is in place (built 2026-09-25 unless noted)

| Layer | Control | Where |
|---|---|---|
| Edge | Cloudflare proxy, DDoS mitigation, TLS, caching (on since the site launched) | Cloudflare |
| Edge | Browser integrity check: some scripted user-agents (for example Python-urllib) get 403 | Cloudflare setting |
| Worker | **Bulk data files** (topic data, the Excel sheets, Must Practice questions) are served through the Worker. A request must come from a capranav.com page (`Sec-Fetch-Site: same-origin`, or a Referer from the site). A bare wget, curl or script gets **403** | `worker/lib/guard.js`, `run_worker_first` in `wrangler.toml` |
| Worker | **Per-IP rate limit** on those files: 40 requests per minute (`RL_DATA`) | `wrangler.toml` `[[ratelimits]]` |
| Worker | `/api/anatomy/*` JSON: same-site required and 120 requests per minute per IP (`RL_API`) | `worker/index.js` |
| Worker | `/api/anatomy/document` (PDF downloads): 12 per minute per IP (`RL_DOC`) | `worker/index.js` |
| Worker | Data files carry `X-Robots-Tag: noindex` so search engines do not index raw JSON | `worker/index.js` |
| Worker | Login codes: 5 per hour per email and 10 per hour per IP; contact form 5 per hour per IP plus a honeypot; admin login failed-attempt limit per IP; book PDFs only after login and purchase (added earlier) | `worker/index.js`, `worker/lib/admin.js` |
| Site | robots.txt allows named search and AI crawlers and disallows `/admin`, `/api/`, `/dashboard`, `/reader` for everyone | `public/robots.txt` |
| Site | Crawler-readable HTML for the JavaScript-built pages, so crawlers never need the data files | `tools/build_seo_static.py` |

### Verified

* Bare `curl` to `/topics/data/topics.json`: 403. With `Sec-Fetch-Site: same-origin`: 200.
* A burst of 60 same-origin requests: 40 succeed, the rest get 429 with `Retry-After: 60` (tested locally).
* The topics, Must Practice, Anatomy and Videos pages, and the Excel downloads, still work in a real browser
  (headless Edge) with the guards on.
* Bare `curl` to `/api/anatomy/topics`: 403 (live).
* Real search and AI crawlers are not affected: they read the HTML, which is not guarded. Each crawler user-agent
  returns 200 for the pages.

### What this does and does not stop

* Stops: `wget --mirror`, `curl`, `python-requests` and similar scripts that do not send browser headers; a scraper
  hammering the data files or the anatomy API; PDF harvesting at speed.
* Does **not** stop: a script that sends `Sec-Fetch-Site: same-origin` itself; a headless browser; a slow patient
  crawl of the public HTML pages (which are public on purpose, for crawlers). Rate limits are per Cloudflare
  location, not global.
* The public HTML pages still contain the ranked topics and the must-practice questions (not the answers). That is
  the deliberate public layer that earns search and AI visibility.

## Still to do in the Cloudflare dashboard (cannot be done from the repo)

Do these in the dashboard for the capranav.com zone. Free-plan features first.

1. **Security > Bots > Bot Fight Mode: ON.** Challenges known scraper signatures. Verified crawlers (Googlebot,
   Bingbot, the OpenAI and Anthropic crawlers and so on) are not challenged.
2. **Security > Settings > "Always Use HTTPS": ON** (SSL/TLS > Edge Certificates). Redirects plain HTTP.
3. **A site-wide rate-limiting rule** (Security > WAF > Rate limiting rules): when the request rate from one IP
   exceeds **120 requests per minute**, block for 10 minutes, but never for verified bots. Free-plan rules can only
   count per IP; use the expression:

   ```
   not cf.client.bot
   ```
   Characteristics: IP. Period: 1 minute. Requests: 120. Action: Block (or Managed Challenge). Duration: 10 minutes.
4. **A custom WAF rule that challenges spoofed crawlers**: a request that claims to be a big crawler but is not
   verified. Expression (custom rule, action Managed Challenge):

   ```
   (http.user_agent contains "GPTBot" or http.user_agent contains "ClaudeBot" or http.user_agent contains "Googlebot"
    or http.user_agent contains "bingbot" or http.user_agent contains "PerplexityBot")
   and not cf.client.bot
   ```
   Real crawlers (verified by Cloudflare through their IP ranges) pass; impostors get challenged. Check that
   `cf.client.bot` is available on your plan; otherwise use Security > Bots > "Verified bots" settings.
5. **AI Crawl Control** (formerly AI Audit): keep the AI crawlers you want set to **Allow** (search and answer
   crawlers: OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot; and, by your choice,
   GPTBot and ClaudeBot). Decide separately about CCBot, Bytespider and Amazonbot, which mainly feed copy sites.
   Use its metrics to see which crawlers actually visit.
6. **Cloudflare Access on `/admin*` and `/api/admin/*`** (Zero Trust > Access > Applications, self-hosted, free under
   50 users, policy: your email). Takes the admin login off the public internet.
7. **Turnstile** on the login-code form, the contact form and the admin login. Create a widget (Turnstile > Add
   site, managed mode) and give the site key and secret; the Worker check is a small addition. Not built yet
   because it needs the keys.
8. **Confirm the plan** (Workers Free vs Paid). On the free plan a flood of requests can use up the daily request
   allowance (100,000) and take the site down even when every request is harmless.

## Ideas that need a decision

* Move answers, bulk downloads and the full datasets behind a free login (passkeys, no personal data): planned.
* Canary entries (fake topics or questions) and per-account invisible watermarks in downloads, so a copy can be
  traced and proven.
* A stricter Content-Security-Policy that also restricts scripts (needs work: the site uses inline scripts, Razorpay
  and one CDN import); ship it as `Content-Security-Policy-Report-Only` first.

## Tuning

The three limits are in `wrangler.toml` (`RL_DATA` 40/min, `RL_API` 120/min, `RL_DOC` 12/min). They are per IP: a
college or office where many students share one address will share the limit, so keep them generous. If a real
user reports "Too many requests", raise the number and redeploy. The same-site rule and the path list live in
`worker/lib/guard.js` (`DATA_PATHS`).
