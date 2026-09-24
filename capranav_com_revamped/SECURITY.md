# capranav.com — Security posture

Audited 2026-09-24 against `Main1lavyaAIAgents/SECURITY-LEVEL3-RECOMMENDATIONS.md`
(written for vcgurukul.com; applied here because the threat model — scraping,
bot abuse of forms, an exposed admin page — is the same).

Status legend: **FIXED** (in code, see "Deploy" below), **OPEN — dashboard**
(a Cloudflare zone setting, not something the repo can change), **OPEN — code**
(planned, not built).

## 1. What was wrong, and what changed

| # | Vulnerability found | Risk | Mitigation | Status |
|---|---|---|---|---|
| 1 | **OTP limit was per email only.** One bot could request codes for unlimited *different* addresses. | Email-bombing third parties; abuse of the Cloudflare Email quota and sender reputation. | New per-IP cap (10 codes/hour across all emails) in `handleOtpSend`, using a new `otp_codes.ip` column (`migrations/0003_otp_ip_rate_limit.sql`). The per-email cap of 5/hour stays. | FIXED |
| 2 | **No security headers** on pages (only `nosniff` on some API responses). | Clickjacking (site framed by another site), downgrade to HTTP after first visit, referrer leakage, unneeded browser features. | Worker adds HSTS (1 year), `X-Content-Type-Options`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy`, `Permissions-Policy` and a CSP limited to `frame-ancestors 'self'; base-uri 'self'; object-src 'none'; form-action 'self'` on every response it produces. `public/_headers` gives static files the same set. | FIXED |
| 3 | **No `robots.txt` / `security.txt`.** | Crawlers were told nothing about `/admin` and `/api/`; researchers had no contact route. | `public/robots.txt` disallows `/admin`, `/admin.html`, `/api/`. `public/.well-known/security.txt` gives a contact and expiry. (robots.txt is a courtesy for well-behaved crawlers, **not** protection.) | FIXED |
| 4 | **`http://` is served, not redirected to HTTPS.** | Anyone on the plain link (or a typed URL without `https`) gets an unencrypted page and session-cookie exposure on hostile networks. Cookies are `Secure`, so logins fail rather than leak, but pages/forms still load unencrypted. | HSTS (above) fixes it after a visitor's first HTTPS visit. The full fix is the zone setting **SSL/TLS → Edge Certificates → Always Use HTTPS**. | OPEN — dashboard |
| 5 | **`/admin` is public** (returns 200 to anyone). Protected only by password + a per-IP failed-login limit. | Password guessing from many IPs; admin page reachable by scanners. | Put `capranav.com/admin*` and `/api/admin/*` behind **Cloudflare Access** (free under 50 users). | OPEN — dashboard |
| 6 | **No Turnstile** on the OTP, contact and admin-login forms. The contact form has only a hidden honeypot. | Automated form abuse that passes a honeypot. | Add a Turnstile widget + server-side token check in `handleOtpSend`, `handleContact`, `handleAdminLogin`. Needs a Turnstile site key + secret (dashboard). | OPEN — needs key |
| 7 | **No site-wide rate limit, Bot Fight Mode, or WAF managed rules confirmed.** Plain scripted clients get the same 200 as browsers. | Cheap scraping of the whole site and its JSON endpoints (`/api/anatomy/*`). | Enable Bot Fight Mode; add one Cloudflare rate-limiting rule (e.g. >120 requests/min per IP); confirm WAF managed rules. | OPEN — dashboard |
| 8 | **No full script-src CSP.** | An injected script would run freely. | The site uses inline scripts/styles, Razorpay checkout and a pdf.js import from cdnjs, so an enforcing script CSP would break it. Plan: ship it as `Content-Security-Policy-Report-Only`, fix violations, then enforce (nonces/hashes). | OPEN — code |

## 2. What was already fine (verified in code)

- **Book PDFs** are served only through the Worker after login **and** a purchase
  check (`handleRead`), with `Cache-Control: no-store`. The R2 bucket is bound to
  the Worker, not exposed by a public domain in code.
- **Sessions/cookies**: `HttpOnly; Secure`, `SameSite=Strict` for admin and `Lax`
  for students; server-side expiry.
- **Admin login** is rate limited per IP and audited (`admin_login_attempts`,
  `deletion_log`).
- **Contact form** is limited to 5/hour per IP and has a honeypot.
- **All D1 queries** use bound parameters (`.bind(...)`).
- Traffic is proxied by Cloudflare (`Server: cloudflare`), so edge features apply.

## 3. How it is protected now (the layers)

1. **Edge (Cloudflare):** TLS, caching, DDoS protection. *Bot Fight Mode / WAF /
   rate-limit rules are not confirmed — see rows 4, 5, 7.*
2. **Worker:** security headers on every response; per-email + per-IP OTP limits;
   per-IP contact and admin-login limits; entitlement check on paid files.
3. **Data:** D1 with bound parameters; R2 private behind the Worker; nightly D1
   backup tooling (`DATABASE-BACKUP.md`).

## 4. Deploy order (code written and tested locally, NOT yet deployed)

1. `npx wrangler d1 execute capranav-platform --remote --file=migrations/0003_otp_ip_rate_limit.sql`
   — **first**. The new Worker reads/writes `otp_codes.ip`; without the column,
   OTP sending would error.
2. `npx wrangler deploy`
3. Verify live: `curl -sI https://capranav.com/` shows the headers;
   `/robots.txt` and `/.well-known/security.txt` return 200; log in with OTP once
   to confirm the flow still works.

## 5. Verification done locally (`wrangler dev --local`, local D1)

- Headers present on static pages, API responses and 404s.
- `/robots.txt` and `/.well-known/security.txt` return 200.
- OTP: from one IP, requests 1–10 pass the limiter and the 11th–12th return 429;
  a different IP is unaffected. (Email sending itself fails locally because no
  Cloudflare Email token is configured there — that is expected and unrelated.)
- **Not** tested: a real browser pass through Razorpay checkout and the PDF
  reader with the new headers. None of the headers block inline scripts, external
  scripts or Razorpay, but check the checkout once after deploy.

## 6. Re-audit

Re-run the checks in this file after any Cloudflare setting change, and
periodically re-run the scraping tests from the two incident case studies against
this site — a control that has never been exercised is a hope, not a verified fact.
