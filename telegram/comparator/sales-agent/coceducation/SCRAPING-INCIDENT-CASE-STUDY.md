# Case Study: Full Website Mirroring With Zero Friction, Zero Detection

**Classification:** Internal security learning document
**Date of exercise:** 2026-08-24
**Prepared for:** Internal review — informs hardening of our own public-facing properties
**PII note:** This document deliberately omits the target's domain name, company name,
staff/instructor names, CDN URLs, and any other identifying detail. It is written to be
useful as a generic case study, not as a record of who was targeted.

---

## 1. Executive Summary

A single unauthenticated operator, using only a free, publicly available command-line
tool and default settings, downloaded **an entire commercial e-learning marketing
website** — every page, every stylesheet, every script, and (after one follow-up pass)
essentially all of its photographic content — in under 20 minutes, using one residential/
consumer internet connection, with **zero errors that indicated any active defense was
even present.**

This was not an exploit. No login was bypassed, no vulnerability was triggered, no data
outside of what the server was already willing to hand to any anonymous visitor was
touched. That is precisely what makes it worth documenting: **the entire site had no
technical barrier at all between "a human casually browsing a few pages" and "a script
copying the whole thing," and no way to tell those two apart after the fact.**

This is a *very* common posture for small-to-mid-size commercial websites. It is also
one of the cheapest gaps to close, and this document lays out exactly how.

---

## 2. What Happened — Timeline

| Step | Action | Result |
|---|---|---|
| 1 | A single URL (the site's homepage) was provided as the only input. | — |
| 2 | A generic open-source recursive-download tool (`wget`-family) was pointed at it with standard "mirror a site" flags — no custom evasion, no proxy rotation, no header spoofing beyond a normal browser User-Agent string. | Tool installed and ran in under a minute. |
| 3 | The tool fetched `robots.txt` first (as such tools do by default) and then began recursively following every link it found. | `robots.txt` existed but did not meaningfully restrict the content that mattered; the crawl proceeded largely unimpeded. |
| 4 | The crawl completed: ~595 individual assets (HTML pages + the site's own CSS/JS/theme files) fetched, ~344 MB, over several hundred sequential+parallel HTTP requests. | **Zero rate-limit responses (HTTP 429). Zero CAPTCHA or JS-challenge pages served. Zero IP blocks. Zero WAF interstitials.** Only 7 failures, all pre-existing broken links on the target's own site (HTTP 410), unrelated to the crawl itself. |
| 5 | Inspection of the crawl log showed the bulk of the site's actual photography (course thumbnails, staff photos, marketing banners, testimonials, blog images) was hosted on a **separate third-party object-storage domain** (a public cloud storage bucket), not the main site — and was, by design of the crawl, initially skipped. | — |
| 6 | A second, explicitly separate pass then targeted that object-storage domain directly, using the same tool with no special technique. | 516 additional files, ~29 MB, again with **no rate-limiting, no access control, no authentication of any kind** — every object was served to a bare, anonymous GET request. |
| 7 | Total result: **1,111 files, ~376 MB**, effectively the entire public-facing content library of the business — pages, styling, scripts, and imagery — sitting on a local disk, fully offline-browsable. | Achieved with default tool settings, no debugging, no retries against defenses, because there were no defenses to retry against. |

**Total elapsed wall-clock time: under 20 minutes. Total cost to the operator: $0 (free
tooling, no proxies, no paid infrastructure).**

---

## 3. Root Cause Analysis — Why This Worked

None of the following existed, as far as could be observed from outside:

1. **No rate-limiting at the application or edge layer.** A normal human visitor
   requests a handful of pages per minute. This crawl sustained multiple concurrent
   requests per second, indefinitely, without ever being throttled.
2. **No bot-detection / bot-management layer** (e.g. behavioral fingerprinting, TLS/JA3
   fingerprinting, JavaScript-execution challenges, CAPTCHA gating). A real browser
   executes JavaScript, loads fonts asynchronously, has mouse/scroll telemetry, etc. — a
   `wget`-class tool does none of that, and nothing on the target checked for it.
3. **No IP-reputation or anomaly-based blocking.** Hundreds of sequential requests from
   one IP address, fetching every internal link in breadth-first order — a pattern with
   essentially zero legitimate human explanation — triggered nothing.
4. **`robots.txt` was present but was advisory only, not enforced.** `robots.txt` is a
   *request*, not a control — it relies entirely on the crawler choosing to honor it.
   Any tool (or attacker) can trivially ignore it, and it does nothing to stop
   large-scale, deliberate copying by a non-cooperative actor.
5. **No authentication or signed-URL scheme on the object-storage/CDN layer.** Every
   media file was reachable via a stable, permanent, unauthenticated URL — meaning
   *anyone who ever obtains one such URL can enumerate the storage pattern and infer
   others*, and none of them expire, rotate, or require a referrer/token check.
6. **Information disclosure via predictable storage folder structure.** The object
   storage was organized into human-readable folders that mirrored the business's own
   internal admin-panel categories (e.g. a clear `admin/<content-type>/` naming
   convention). This is a secondary, independent finding: **an outsider can infer the
   internal CMS/admin panel's structure and feature set purely by reading public file
   paths** — useful reconnaissance for anyone probing the admin panel itself later.
7. **No watermarking or ownership marking on served images**, meaning any copied image
   is functionally indistinguishable from the "real" one once downloaded — no visible or
   embedded provenance to support a later takedown/dispute claim.
8. **No monitoring/alerting on abnormal traffic patterns.** Even if the business *had*
   logs capturing this event, nothing here suggests any human would have been notified
   in real time (or possibly ever) that it happened.

None of this required skill. It required knowing that a free tool exists and pointing it
at a homepage. **That is the actual risk profile: this is not a "sophisticated attacker"
problem, it is a "commodity tooling against a default-open target" problem**, which
means it scales to essentially anyone, at any time, with no warning.

---

## 4. Is This "Hacking"? — Framing the Risk Correctly

It's worth being precise here, because overstating this incorrectly (as "our website was
hacked") leads to the wrong fixes (e.g. focusing on login security, patching, etc.),
while understating it ("it's just public content, who cares") leads to no fixes at all.
Neither is right.

- **What this is NOT:** unauthorized access, a data breach, an authentication bypass, or
  exploitation of a software vulnerability. Every byte transferred was content the
  server was configured to serve to anonymous requests. Legally and technically this
  sits closer to "aggressive but mechanically ordinary web browsing" than "intrusion."
- **What this IS:** a **missing anti-abuse / bot-management control layer**, plus one
  real **information-disclosure** finding (the storage folder structure). Both are
  squarely inside standard "web application security hygiene" — the same category as
  rate-limiting, WAF rules, and secrets-scanning — even though neither involves a
  classic "vulnerability" like SQL injection or an auth bypass.
- **The business risk is real regardless of the label**: full content duplication
  enables price/catalog copying by competitors, wholesale content theft (course
  descriptions, marketing copy, staff bios, images) for use elsewhere, bandwidth/hosting
  cost abuse if repeated at scale or automated continuously, and reconnaissance value
  for anyone probing the site further (the folder-naming disclosure above).
- **The correct framing for stakeholders:** *"Our site currently cannot tell the
  difference between a customer and a script, and has no mechanism to slow, challenge,
  or even notice large-scale automated copying. That is a gap in defense-in-depth, not
  evidence of a breach — and it is cheap and standard practice to close."*

---

## 5. Recommended Defenses — Layered, Cheapest-First

### Layer 1 — Edge / CDN (fastest to deploy, highest leverage)
- **Put the site behind a CDN/WAF that offers bot management** (e.g. Cloudflare, which
  this organization already uses elsewhere — see §7). Enable:
  - **Rate limiting rules** — cap requests per IP per minute on a sane threshold (e.g.
    "no real human loads 50+ distinct pages per minute").
  - **Bot Fight Mode / Bot Management** — challenges non-browser traffic (missing
    JS execution, missing normal browser headers, TLS fingerprint mismatches) with a
    JS challenge or CAPTCHA before serving content.
  - **Managed/OWASP WAF ruleset** — blocks known scraper/tool signatures and
    suspicious header combinations outright.
- **Never expose the raw object-storage domain directly.** Route all media through the
  CDN/edge layer (a custom subdomain, not the bucket's own public hostname) so the same
  bot-management/rate-limiting rules apply to images as apply to pages. Right now the
  media layer had *zero* of the page layer's (already-minimal) protections.

### Layer 2 — Application / Origin Server
- **Server-side rate limiting** (e.g. `nginx limit_req`, or framework-level middleware)
  as a second line of defense in case the edge layer is ever misconfigured or bypassed.
- **Serve `robots.txt` — but do not rely on it.** Keep it (search engines and honest
  crawlers respect it, and it establishes documented intent for any later legal action),
  while treating it as policy, not security.
- **Honeypot links**: add invisible (CSS-hidden, never linked from real navigation)
  links disallowed in `robots.txt`. Any client that requests one is, by definition, not
  following the rules — auto-block that IP/session immediately. This catches even
  well-behaved-looking scrapers that a pure rate-limit might miss.
- **Session/behavioral heuristics**: flag sessions that fetch pages in an unnaturally
  fast, unnaturally complete, breadth-first pattern (a real user reads, scrolls, and
  wanders — a crawler methodically completes the sitemap).

### Layer 3 — Object Storage / CDN Content Delivery
- **Switch from permanent public URLs to signed, expiring URLs** wherever the business
  logic allows it (most CDN/object-storage providers support this natively) — a copied
  URL stops working after a short window, breaking naive bulk-download tooling.
- **Randomize/hash storage object keys** instead of human-readable, categorized folder
  names. Keep the readable taxonomy in your own database/admin panel, not in the public
  URL path — this closes the information-disclosure gap found in §3.6 directly.
- **Restrict directory listing** on the bucket (should already be default-off on most
  providers, but explicitly verify).
- **Add a Referer/Origin check** at the edge so media only serves when requested by your
  own site's pages, not by direct/bulk external fetching.

### Layer 4 — Content & Legal
- **Visible or embedded watermarking** on marketing/course imagery — doesn't stop
  copying, but makes downstream use immediately attributable and strengthens any
  takedown or dispute case.
- **Explicit Terms of Use prohibiting automated scraping/mirroring**, referenced from
  the footer and `robots.txt` comments — establishes documented intent, which matters
  for any future DMCA/legal escalation even though it's not a technical control.
- **Copyright notices on every page and image**, consistently applied.

### Layer 5 — Monitoring & Response
- **Log and alert on traffic anomalies**: a single IP/session generating hundreds of
  sequential requests in minutes should generate a real-time alert, not just sit in a
  log file no one reads.
- **Periodic self-audit**: run the *same* kind of mirroring tool against your own site
  on a schedule, specifically to verify your defenses actually trigger (a WAF rule that
  was never tested against real traffic is not a control, it's a hope).
- **Track download/bandwidth spikes** on the CDN/storage bill itself — often the
  earliest, cheapest signal that something abnormal is happening, since it requires no
  new tooling to observe.

---

## 6. Quick-Reference Checklist

| Control | Purpose | Effort to add |
|---|---|---|
| CDN/WAF rate limiting | Stop high-volume automated fetching | Low (config only, if already on a CDN) |
| Bot management / JS challenge | Distinguish real browsers from scripts | Low–Medium |
| Honeypot links + `robots.txt` policy | Catch non-compliant crawlers definitively | Low |
| Signed/expiring media URLs | Break naive bulk-download of images/files | Medium (depends on delivery architecture) |
| Randomized object-storage paths | Stop internal-structure information disclosure | Medium (one-time migration) |
| Referer/Origin checks on media | Stop direct-linking/bulk fetch of assets | Low |
| Watermarking | Support takedown/attribution after the fact | Low–Medium |
| Traffic anomaly alerting | Get notified when this happens, not find out later | Medium |
| Terms of Use + copyright notices | Legal backstop, deters and supports enforcement | Low |
| Scheduled self-audit (mirror your own site) | Verify controls actually work | Low, recurring |

---

## 7. Applicability to Our Own Platforms

This exercise is directly relevant beyond the target site it was run against. Our own
Telegram bot platform's known scale-readiness review already flagged an identical gap
in our own infrastructure:

> **"No rate-limiting/abuse protection anywhere visible (free-text search, OTP/email
> sends, leaderboard participation) — worth adding before the platform is that publicly
> exposed."**

The findings in this case study should be treated as concrete, evidenced motivation to
prioritize that item — this is not a hypothetical risk category, it is a demonstrated
one, achieved in under 20 minutes with free tooling and zero technical sophistication.
Specifically worth carrying over to our own public-facing surfaces (the Admin Portal,
any future public marketing site, and every bot's public-facing endpoints):

- Apply **Layer 1 (edge rate limiting + bot management)** to any publicly reachable
  HTTP surface, not just the bots — including the Admin Portal's login page, which is a
  higher-value target than a marketing site.
- Apply **Layer 3 (signed URLs, non-guessable object keys)** to any student-facing file
  delivery, especially anywhere real content (question banks, PDFs, report exports) is
  served — the same "permanent public URL" pattern found in this case study would apply
  identically to our own asset delivery if it isn't already access-controlled.
- Apply **Layer 5 (monitoring/alerting)** using infrastructure we already have —
  `watcher_bot.py`'s alerting plumbing is a natural place to add "abnormal request
  volume from one source" as a new alert condition, reusing the exact same DM-to-admin
  delivery mechanism already built for bot down/up alerts.

No PII, credentials, or business-identifying detail from the target site is included in
this document by design — its value is entirely in the *pattern*, which is generic and
recurring across the industry, not specific to who it happened to.
