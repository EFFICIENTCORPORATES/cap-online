# SECURITY.md — the 1LAVYA Telegram platform's security checklist

**Status as of 2026-08-24.** Written directly off the lessons in
`comparator/sales-agent/coceducation/SCRAPING-INCIDENT-CASE-STUDY.md` — a same-day
exercise that mirrored an entire competitor website (pages, scripts, and media) in
under 20 minutes with a free tool and zero resistance from their servers. This
document translates those lessons into **this platform's actual architecture**,
verified against the real code (not assumed), and separates "every check we could
reasonably want" from "what to actually implement first." Pairs with
`BACKUP-STRATEGY.md` (data-survival — a different risk, already solved) and
`/CLAUDE.md`'s "known scale-readiness gaps" callout (gap #8 is this document's direct
ancestor).

**Implementation status (updated 2026-08-24, same day): §4 Phases 1–3 built,
verified, and deployed live** — per-user rate limiting + input validation
(`telegram/bots/rate_limiter.py` + `input_guard.py`), the central
callback-data route registry (`telegram/bots/callback_registry.py`), and
traffic-anomaly alerting (extended into `watcher_bot.py`). Full detail:
`_claude/memory/project_log.md`'s 2026-08-24 entry. **§4 items 3, 4, and 7
(Admin Portal: never expose the raw port / CSRF / a second factor) and §6's
Cloudflare Tunnel + Access path are still open** — each needs an explicit
decision or action from Pranav first (a new, narrowly-scoped Cloudflare
token; a hostname; who gets Access; TOTP enrollment) — see the phase-wise
plan already given; not started without that.

---

## 1. Why this platform's attack surface is different from a normal website

The case study's target was a conventional marketing website: one public domain,
every page and asset reachable by any anonymous HTTP request, no login anywhere. This
platform is architecturally different in one important way, verified directly in the
code, not assumed:

- **Every bot (`study_hub_bot.py`, `exam_hub_bot.py`, `faculty_bot.py`,
  `myfiles_hub_bot.py`, `watcher_bot.py`, `leaderboard_broadcaster.py`) calls
  `run_polling()`, not `set_webhook()`.** That means each bot process reaches *out* to
  Telegram's servers to fetch updates — there is **no inbound public HTTP endpoint for
  bot logic to attack directly**, unlike the target site in the case study, which had
  to serve every request to anyone who asked. This is a genuine, already-existing
  structural advantage — worth knowing so we don't over-correct by adding webhook-style
  defenses (e.g. request-signature verification) that this architecture doesn't need
  yet.
- **The Admin Portal (`admin_portal/app.py`) binds to `127.0.0.1` only** (confirmed at
  `app.run(host="127.0.0.1", ...)`), not `0.0.0.0` — it is not reachable from the
  internet today. This matters enormously for how urgently each Admin Portal item
  below needs to happen: **most are "before you ever expose this," not "right now."**

**So the real, live public attack surface today is not "our website" — it's the
Telegram Bot API itself.** Any of the ~9 bots on `bots.json` can be messaged by any
Telegram user, anonymous and unauthenticated by us (Telegram authenticates *them* to
*us*, cryptographically, at the platform level — see §4 — but we place no limits of
our own on what a verified-real Telegram user can then do to our bot). That is where
this document's highest-priority findings live.

---

## 2. What's already good — verified, not assumed

Worth stating plainly, because a security document that only lists gaps reads as if
nothing was ever done right. All of the below were confirmed by reading the actual
code during this review, not taken on faith:

| Control | Where | Status |
|---|---|---|
| Admin Portal bound to localhost only | `admin_portal/app.py` | ✅ Not internet-reachable today |
| Login lockout after repeated failures | `admin_portal/auth.py` — `LOCKOUT_WINDOW_MINUTES = 15`, a rolling window | ✅ Real brute-force throttling exists |
| Passwords hashed, never stored plain | `auth.py` via `werkzeug.security.check_password_hash` | ✅ |
| SQL Query tab is genuinely read-only | `admin_portal/sql_query_tool.py` — enforced inside the tool itself, not just by convention | ✅ |
| Cloudflare API tokens are purpose-scoped, not one all-powerful token | `.env` — the backup token is scoped to *only* `Workers R2 Storage: Edit` + `D1: Edit`; the email token is separate and scoped to Email Service only | ✅ Real least-privilege already in practice |
| Secrets never committed | `.gitignore` — `.env`, `creds.txt`, `**/creds.txt` all excluded; encrypted nightly in nightly backups | ✅ |
| Every bot has its own separate token | `bots.json` `bot_token_env` per bot | ✅ One leaked token doesn't compromise every bot |
| Admin actions are audit-logged | `admin_actions` table, `audit.py` | ✅ |
| Bots poll, don't accept inbound webhooks | confirmed via `run_polling()` in every bot script | ✅ No exposed HTTP endpoint to attack |

None of this is undone by anything below — the point of this document is to close the
*remaining* gaps, on top of what's already solid.

---

## 3. The full checklist — every category of check worth having

Organized by layer. This is the "everything we could reasonably want" answer to your
question; §4 picks the priority subset.

### A. Telegram-interaction layer (the actual live public surface)

1. **Per-user rate limiting / flood control on bot handlers.** Verified absent —
   grepping every file in `bots/` for flood/throttle/cooldown/rate-limit logic returns
   nothing. Nothing today stops one chat_id from firing messages or button taps as
   fast as Telegram will accept them.
2. **Abuse limits on expensive or side-effecting actions specifically**: free-text
   search (`study_hub_bot.py`), the report/email trigger (`report_flow.py` — confirmed
   no cooldown logic exists there either), leaderboard join/leave, MCQ-issue reports,
   PDF/report generation.
3. **A cooldown on the email-sending flow in particular.** `report_flow.py` sends a
   real email via Cloudflare Email Service on request, with no minimum interval between
   requests from the same chat_id — today this mostly just wastes send quota/cost if
   spammed, but it's the one flow that reaches outside our own infrastructure (a real
   inbox), so it deserves its own explicit limit rather than relying on the general
   rate-limit fix to happen to cover it.
4. **Input validation on every free-text field**, especially anything that reaches a
   DB query or gets echoed back to the user (profile fields, search terms). Already
   partially covered — `contact_utils.py` validates mobile/email formats — but this
   should be a standing rule for any *new* free-text field, not just the two already
   covered.
5. **A central callback-data route registry.** Not a new idea — `/CLAUDE.md` already
   documents this exact bug class recurring 3+ times (regex pattern collisions
   swallowing another handler's buttons, and a real 64-byte `callback_data` overflow
   silently breaking an entire keyboard). Framed as security-adjacent here because an
   attacker who understands this bug class could deliberately craft input to trigger
   it, turning a correctness bug into a denial-of-service against a specific menu.
6. **File upload validation on MyFiles Hub** — size ceiling (Telegram's own Bot API
   already caps bot-downloadable files at 20MB, a natural backstop), and a check that
   accepted file types match what the feature actually expects, rather than accepting
   anything Telegram will forward.
7. **Anomalous-volume detection per chat_id**, reusing infrastructure we already have:
   `watcher_bot.py` already DMs admins on bot up/down transitions — extending it (or a
   sibling script) to flag "one chat_id generated N interactions in the last minute" is
   a small addition on top of an existing, proven alerting path, not a new system.

### B. Admin Portal — the highest-value target *if and when* it's ever exposed

Everything here matters far more the day this portal becomes reachable from outside
`127.0.0.1` than it does today — but building it in now costs little and removes the
temptation to rush it later under time pressure.

1. **Never port-forward the raw Flask port (8788) to the internet.** If remote access
   is ever needed, put **Cloudflare Tunnel + Cloudflare Access** in front of it instead
   — see §6 for exactly what that needs from our Cloudflare account.
2. **CSRF protection on every state-changing route.** Verified absent — no CSRF token
   generation/validation anywhere in `admin_portal/`. Today the impact is limited by
   the portal being localhost-only, but a route like bot-restart or bulk-report-send
   should never be one unguarded `POST` away from a forged form on an unrelated page,
   regardless of network exposure.
3. **Explicit session cookie hardening** — `SESSION_COOKIE_SAMESITE`,
   `SESSION_COOKIE_SECURE` (once served over HTTPS via a Tunnel), and a defined session
   lifetime. Currently relies entirely on Flask's own defaults.
4. **Basic security response headers** (`X-Frame-Options`, `X-Content-Type-Options`,
   a Content-Security-Policy) — cheap, standard, currently absent. Low urgency alone,
   but trivial to add alongside item 3.
5. **A second factor (TOTP) on the admin login**, on top of the existing
   password + lockout. Single-factor is an acceptable risk for a localhost-only tool
   used by one person; it stops being acceptable the moment §6's Tunnel makes this
   portal reachable from anywhere Pranav has his phone.
6. **RBAC** — already on the platform's own roadmap (`admin_portal/README.md`), not
   yet built. Its priority should rise directly in proportion to how exposed the
   portal becomes.
7. **A cadence for actually reading the audit log** — `admin_actions` already records
   everything; a log nobody looks at is a control that exists on paper only.

### C. Cloudflare / API token hygiene

1. **Keep tokens purpose-scoped** — already true today (§2); the discipline to
   preserve is *never* widening an existing token's scope for convenience when a new
   feature needs a new permission. Create a new token instead (see §6).
2. **Set a rotation reminder.** Cloudflare API tokens don't expire on their own — put a
   calendar reminder (6–12 months, or immediately on any suspected exposure) to
   regenerate each one.
3. **Check Cloudflare's own Account → Audit Log periodically.** It's free, already
   available, and shows every API call made with every token on the account — the
   simplest way to notice a token being used somewhere it shouldn't be.
4. **Confirm the R2 backup bucket is not public-read.** It should already be
   private-by-default (R2 buckets aren't public unless explicitly configured with a
   custom domain or public access enabled) — worth a one-time explicit check in the
   dashboard rather than assuming.

### D. Database & backup security

Mostly already solved by `BACKUP-STRATEGY.md` — cross-referenced here, not duplicated:

1. Encrypted secrets backup — done (`BACKUP-STRATEGY.md` §3d).
2. Backup-passphrase custody — **still needs Pranav to save
   `CF_BACKUP_ENCRYPTION_PASSPHRASE` in a password manager**, per that document's own
   §6.1 — repeating it here because it's a security dependency, not just an
   operational one: if this machine dies *and* that passphrase only ever lived on it,
   every encrypted secret backup becomes permanently unreadable.
3. Physical/OS-level protection of the one machine holding `platform.db` — a strong
   Windows account password, automatic OS updates, and disk encryption (BitLocker)
   matter more now that this PC is the sole custodian of both live data *and* every
   credential on the platform.
4. A full cold-restore rehearsal — flagged as never yet done in
   `BACKUP-STRATEGY.md` §10, repeated here because an unrehearsed restore is a security
   gap as much as an operational one (you don't actually know recovery works under
   pressure until you've tried it once, deliberately).

### E. Bot token & credential hygiene

1. Telegram bot tokens are all-or-nothing (Telegram has no scoped-token concept) — the
   mitigation is procedural: **know the BotFather `/revoke` step before you need it**,
   and rotate immediately on any suspected leak.
2. Already-separate tokens per bot (`bots.json`) correctly limits blast radius — keep
   this pattern for every future bot, never share one token across two bot identities.
3. Never let a token reach a log file — worth a one-time grep across `database/run/`
   logs to confirm no token has ever been accidentally printed by an exception
   traceback.

### F. General web hygiene (carried over from the case study, for whenever it applies)

Not urgent today (no public marketing site or student-facing web view currently
exists on this platform), but worth keeping on file for the day one does:

1. Edge-layer rate limiting / bot management (Cloudflare) in front of any public page.
2. Signed, expiring URLs instead of permanent public links for any served file.
3. No human-readable internal folder taxonomy in public-facing paths.
4. Terms of Use + monitoring, exactly as detailed in the case study's §5.

---

## 4. The major checks — implement these first

Out of everything in §3, these are the ones worth doing **now**, ranked by a
combination of (a) how real and demonstrated the risk already is, (b) how cheap the
fix is relative to the exposure it closes, and (c) how much of the fix reuses
infrastructure we already have rather than requiring something new.

1. **Per-user rate limiting on every bot handler.** This is the single most exposed,
   most trivially triggerable gap on the entire platform — it needs zero
   sophistication to hit (exactly the case study's core lesson), it's live on every
   bot today, and a basic per-chat_id sliding-window limiter is a small, self-contained
   addition, not an architecture change.
2. **A cooldown specifically on the email/report-send flow.** Narrower than #1, but
   worth calling out on its own because it's the one flow that spends real external
   quota/cost per trigger and reaches an actual inbox.
3. **Never expose the Admin Portal's raw port to the internet — plan the Cloudflare
   Tunnel + Access path now**, even before remote access is actually needed, so it's
   ready the moment it is (see §6). Today's protection (localhost-only binding) is a
   network-topology default, not a designed control — it would take one careless
   port-forward to remove it entirely.
4. **CSRF protection on Admin Portal state-changing routes.** Cheap, standard, and
   currently fully absent — this is the kind of fix that's nearly free today and
   meaningfully more urgent (and more annoying to retrofit under pressure) the moment
   §6's Tunnel is in place.
5. **A central callback-data route registry.** This isn't a new recommendation — it's
   promoting an already-documented, already-recurred-3+-times bug class to "fix the
   class, not the next instance," per `/CLAUDE.md`'s own framing.
6. **Traffic-anomaly alerting reusing `watcher_bot.py`.** This directly closes the
   "how would we even know this happened" gap the case study exposed — we already
   have the DM-to-admin pipe built and proven (bot up/down alerts); extending its
   triggering conditions is far cheaper than building a new alerting system.
7. **A second factor on the Admin Portal login.** Lowest urgency of this list *today*
   (localhost-only), but cheap enough to do now rather than treat as a "before Tunnel
   goes live" blocker later.

---

## 5. Deliberately not on the priority list right now, and why

- **RBAC** — real, valuable, already on the roadmap, but its priority is explicitly
  tied to Admin Portal exposure (§3.B.6) — doing it before the Tunnel work in §6 would
  be solving tomorrow's problem before today's.
- **Full dependency/vulnerability scanning of the Python codebase** — a legitimate
  general-hygiene item, but not something this incident specifically demonstrated as
  exploitable; worth a separate, dedicated pass rather than folding into this
  incident-driven list.
- **Migrating bots to webhooks** — not a security recommendation at all here; polling
  is currently the *safer* posture (§1) precisely because it has no inbound surface.
  Don't change this for security reasons; it's already tracked separately as a
  scaling decision (`/CLAUDE.md` gap #4).

---

## 6. Your Cloudflare / token question, answered directly

**Short answer: don't widen either of the two existing tokens. If you build the Admin
Portal Tunnel (item 3 above), create a third, brand-new, narrowly-scoped token for it
— keep the one-token-per-purpose discipline that's already in place.**

What actually exists today, verified in `.env` (values not reproduced here):

| Token | Scope | Purpose |
|---|---|---|
| `CF_BACKUP_API_TOKEN` | `Account > Workers R2 Storage: Edit`, `Account > D1: Edit` | Nightly backup snapshots + D1 mirror |
| `CF_EMAIL_API_TOKEN` | Email Service sending | Student/faculty report emails |

Note there is **no Wrangler CLI configuration anywhere in this repo** (`wrangler.toml`
doesn't exist, no `wrangler` invocation anywhere in `telegram/`) — everything
Cloudflare-facing today is done via direct REST API calls (`cf_email.py`,
`backup_to_cloudflare.py`, both using `urllib`, not the SDK or CLI). That's fine and
already working; just worth naming precisely, since "we have Wrangler" and "we have
two REST API tokens" imply different things when planning new work.

For each recommendation above that actually touches Cloudflare:

- **Cloudflare Tunnel + Access for the Admin Portal (§4.3)** — needs a **new** token
  scoped to `Account > Cloudflare Tunnel: Edit` + `Account > Access: Apps and
  Policies: Edit`. Do not add this scope to `CF_BACKUP_API_TOKEN` or
  `CF_EMAIL_API_TOKEN` — if either of those ever leaked, you'd want the blast radius
  limited to "our backups" or "our email," not "and also remote access to the admin
  portal."
- **WAF / Bot Management / Rate Limiting rules on the `1lavya.com` zone (§3.F, for
  whenever a public web surface exists)** — this is normally a one-time manual
  dashboard configuration (Zone → Security → WAF), not something that needs an API
  token at all unless you specifically want to automate rule deployment via script,
  in which case that would be a fourth, separately-scoped token
  (`Zone > Firewall Services: Edit`) — not needed today, since no public web surface
  exists yet on this platform.
- **Everything else in this document** (rate limiting on bot handlers, CSRF, callback
  registry, MFA, cooldowns) is pure application code — none of it touches Cloudflare
  or needs any token change at all.

---

## 7. Honest limitations

- This document is scoped to what the case study specifically demonstrated (scraping/
  abuse-of-openness) plus what code review turned up while investigating it. It is not
  a full penetration test or a dependency/CVE audit — those are different, separately
  worthwhile exercises this document doesn't replace.
- Every "verified absent" claim above was checked by grepping the actual code during
  this review (2026-08-24); if new handlers or flows are added later without the
  corresponding rate-limit/cooldown/CSRF pattern, this document will silently go stale
  exactly the way `/CLAUDE.md` itself warns can happen — worth a periodic re-check,
  not a one-time read.
- Fixing everything in §4 does not make this platform's Admin Portal safe to expose
  carelessly — it makes the *planned* exposure path (Tunnel + Access) safe. Any
  shortcut around that path (a raw port-forward "just for a day") re-opens exactly the
  risk this document exists to close.
