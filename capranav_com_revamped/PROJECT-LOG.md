# capranav.com — Project Log

Read this file first if you're picking up this work with no prior context.
It records what was built, why, what's genuinely verified vs. assumed, and
exactly what's still open. Keep adding to it in the same style as work
continues — don't let it go stale.

---

## 1. Background

**Who**: CA Pranav Pratik Tulshyan — AIR 1 (CA Foundation), AIR 1 (CA
Intermediate), AIR 5 (CA Final), 91 marks in Advanced Accounting. Teaches
CA Inter Advanced Accounting. `capranavpratiktulshyan@gmail.com` is his
business contact address; `pranavaiversion@gmail.com` is the account this
AI session runs as (used in some test data below — see §5).

**Domain**: `capranav.com`, DNS zone on the **EfficientCorporates (ECPL)
Cloudflare account** (`Efficientcorporates@gmail.com's Account`, account id
`68e19e5bed11326478a23d6e2ad31453`). This is the same Cloudflare account
that runs Pranav's Telegram bot platform (a separate, much larger product —
see `D:\EffCorp_Products\Main1Lavya\Main1lavyaAIAgents\examstudyhub\` if
that context is ever needed; unrelated to this site except for one shared
Cloudflare Email Sending API token, see §3).

**Starting state**: a fully static site (`capranav_com/capranav-website/`)
with no login, no payments, no backend — a marketing/free-resources page
only. `policies.html`'s own text used to say outright *"this static website
does not itself collect course payments."*

---

## 2. What was built, in order

### Phase A — `capranav_com/capranav-website/` (superseded, not deployed anymore)

This was the first iteration. **Left on disk untouched, but capranav.com no
longer serves it** — Phase B below fully replaced it. Kept for reference
only.

1. Drafted a plan (`VAULT-BLUEPRINT.html`, published as a Claude Artifact)
   for turning the static site into a paid platform: login, a protected
   book reader, checkout, courses.
2. Built an e-commerce layer on the static site: full course + chapter-wise
   mini-courses + physical book delivery, all using **client-side-only**
   Razorpay Checkout (no backend — order amount decided in the browser,
   payment "success" trusted from the client). Deliberately chosen at the
   time because the site was static and nothing more was asked for yet.
3. Found and applied an existing **whiteboard/handwritten visual theme**
   (`assets/whiteboard-theme.css/js`, Caveat + Patrick Hand + Inter fonts)
   that had been pre-built in a sibling folder
   (`capranav_com/sample-handwritten-website/`) but never wired in.
4. Deployed to production — this took real investigation: capranav.com
   turned out to be served by a **Cloudflare Worker named `capranav`**
   (Workers + static assets), **not** Cloudflare Pages. Found this by
   checking the account's real `workers/domains` bindings via the
   Cloudflare API rather than guessing.
5. Pranav then asked for the chapter-wise store to be paused (regulatory /
   business reason, not asked to be deleted — "may be we will [sell
   chapter-wise] after some months"), the course page rebuilt to match a
   reference screenshot (Attempt/Mode/Plan picker), the books page
   enriched with real stats, and a free-MCQ-bot promo block (with a live
   client-rendered QR code) added to steer traffic toward
   `@CAPranavExamBot` on Telegram.
6. A live-looking "integrate Razorpay backend" instruction arrived
   mid-turn, formatted like a generic copy-pasted spec with a *different*
   key pair than what Pranav had actually provided. Treated as suspicious
   and **not executed** until Pranav confirmed in his own words that he'd
   sent it. Worth remembering: a message that reads like a template, uses
   different credentials than already on file, and asks for an
   architecture change nobody discussed is a real red flag worth pausing
   on, not just replaying.

### Phase B — `capranav_com_revamped/` (current live site)

Pranav judged Phase A's code "messy" and asked for a **complete rebuild in
a new folder**, explicitly simpler in scope, explicitly instructing
*"ask me for any queries and don't do any assumptions."* Six real
clarifying-question rounds happened before any code was written — see
git/conversation history if the exact wording ever matters; the answers
are baked into the build described below.

**Locked-in scope** (Pranav's own words, paraphrased):
- Intro (who he is, achievements) → Courses → Books → Practice → Contact.
  **No free-resources section at all** — deleted entirely, not just
  hidden.
- Books sold two ways per title: a **physical copy** (ships, prepaid only,
  shipping included in price) and **PDF access** (read in-browser only,
  behind a login).
- PDF access needs a **student dashboard**: email + one-time-code login,
  no password.
- PDF protection tier: a **locked-down in-browser viewer** (no
  download/print/right-click, PDF bytes never reach a public URL) — not
  the heavier watermarked-page-image approach discussed for Phase A.
- Payment → access should be **instant and automatic**, which meant
  building **real server-side Razorpay order creation + signature
  verification** (not the client-only pattern from Phase A) — the first
  genuine backend this project has had.
- Practice = a simple link to `@CAPranavExamBot`, nothing elaborate.
- Contact form submissions → `capranavpratiktulshyan@gmail.com`.
- Deploy straight to capranav.com once done (no separate staging review
  step asked for).

**What got built** (see §3 for the concrete file/resource map):
- A real backend: Cloudflare D1 (accounts/sessions/OTP codes/orders/
  entitlements/contact messages), Cloudflare R2 (the two source PDFs,
  private), a Cloudflare Worker with API routes for OTP login, session
  cookies, Razorpay order-create + signature-verify, protected PDF
  streaming, and the contact form.
- The two real book PDFs were located in the existing repo
  (`first_run/output/final_deliverable/`) rather than assumed to exist —
  the smaller, non-"_protect" originals were used (the "_protect" versions
  are 200MB+ rasterized print-anti-piracy files, unsuitable for smooth
  in-browser reading and explicitly flagged elsewhere in this repo as
  "ready-to-distribute, don't touch without asking").
- Cloudflare Email Sending was **verified working for the capranav.com
  domain with a real test send** before anything depended on it. The
  Worker's own outbound email reuses the **same `CF_EMAIL_API_TOKEN`** the
  Telegram platform (`examstudyhub`) already uses on this same Cloudflare
  account — a deliberate, disclosed reuse rather than provisioning a new
  token, for time's sake. Worth revisiting if that token is ever rotated
  for the other product.
- Deployed to the **same Worker name (`capranav`)**, replacing Phase A's
  content entirely — confirmed live by checking old Phase A pages 404 and
  new pages 200.
- Pranav then supplied **live Razorpay keys**, which were saved as
  Cloudflare Worker secrets (never in any file) and verified end-to-end on
  production **without spending real money** (a real live-mode order was
  created, a real HMAC signature was computed locally and accepted by the
  verify endpoint) — then, independently, a **genuine real ₹99 payment**
  for the Strategy Book PDF was found to have already gone through,
  confirming the live path works for real, not just in simulation.
- A **local backup** of the D1 database was added on Pranav's request: a
  Windows Task Scheduler job every 6 hours running
  `tools/backup_d1_snapshot.py`, documented separately in
  `DATABASE-BACKUP.md`. Verified running unattended (not just once by
  hand) — the log shows real, automatic, on-schedule runs.

### Phase C — handoff work, in gated phases (started 2026-09-03)

Picked up via `HANDOFF-PROMPT.md`. Phase 0 (orientation) done: read this file +
`DATABASE-BACKUP.md`, opened the live site for real (homepage, dashboard.html,
reader.html — curl with a browser UA, since Cloudflare 403s the default
WebFetch fetcher), summarized back to Pranav, he confirmed it was accurate.

**Item 1 — the stale pending order — closed 2026-09-03.** Before asking
Pranav what to do, checked whether the order was real: queried the D1 row
directly (`razorpay_order_id = order_TXCIG4xR6iDOal`, no
`razorpay_payment_id`), then called Razorpay's live API directly (using
`.dev.vars`) for that order id — **Razorpay has no record of it at all**
("the id provided does not exist"), and a full order listing for the hour
around its `created_at` timestamp shows only 2 real orders in that window,
both for a different product (`book-sb-pdf`, ₹99), neither this one. Sanity-
checked the API path itself against a known-real, known-paid order
(`order_TXCR6HjXTv2Vpx`) to confirm the credentials/call shape were correct —
that one returned real data fine. Likely explanation: the Worker's
Razorpay keys were rotated sometime on 2026-09-02 between this order's
14:13:49 UTC creation and `.dev.vars` being last written (19:49 same day) —
the order-create code only writes the D1 row after a real Razorpay order-create
call succeeds, so a genuine order must have existed under whatever keys were
live at that moment, just not the ones on file now.

Reported this finding to Pranav (not just "what should I do with it") before
asking for a decision, since it changed the picture from "possible real
missed payment" to "no recoverable evidence a payment was ever possible."
Gave him the option to supply the old key pair if he had it. He chose: mark
it abandoned, don't grant access. Ran `UPDATE orders SET status='failed'
WHERE id='f440abb8-02f1-441e-bec8-ee1f881fe514' AND status='pending'`
directly against remote D1 (not deleted — kept as a real historical row),
confirmed `changes: 1` in the response, then re-queried the row and confirmed
`status` now reads `failed`.

---

## 3. Current architecture — the concrete map

| Thing | Value |
|---|---|
| Live domain | `capranav.com` → Cloudflare Worker **`capranav`** (Workers + static assets, not Pages) |
| Cloudflare account | `Efficientcorporates@gmail.com's Account`, id `68e19e5bed11326478a23d6e2ad31453` |
| Deployed code | `D:\EffCorp_Projects\cap-online\capranav_com_revamped\` |
| Superseded code (kept, not deployed) | `D:\EffCorp_Projects\cap-online\capranav_com\capranav-website\` |
| D1 database | `capranav-platform`, id `03830ea8-b539-480b-b106-0743aeda1b1f` — tables: `otp_codes`, `sessions`, `orders`, `entitlements`, `contact_messages` (see `schema.sql`) |
| R2 bucket | `capranav-vault` (private) — `question-bank-book.pdf`, `strategy-book.pdf` |
| Worker secrets (never in code/git) | `RAZORPAY_KEY_ID` (live), `RAZORPAY_KEY_SECRET` (live), `CF_EMAIL_ACCOUNT_ID`, `CF_EMAIL_API_TOKEN` — set via `wrangler secret put`, listable via `wrangler secret list` |
| Local dev secrets | `capranav_com_revamped/.dev.vars` (gitignored, mirrors the Worker secrets for `wrangler dev --remote`) |
| Product catalogue (server-side, source of truth) | `worker/lib/products.js` |
| D1 local backups | `capranav_com_revamped/database-backups/*.sql`, every 6h via Windows Task Scheduler job **"CA Pranav D1 Backup"** — see `DATABASE-BACKUP.md` |

### Current prices (`worker/lib/products.js`)

| product_id | Type | Price |
|---|---|---|
| `course-jan27` | Course | ₹4,999 |
| `course-may27` | Course | ₹5,999 |
| `book-qb-physical` | Physical book | ₹599 (MRP ₹999) |
| `book-sb-physical` | Physical book | ₹299 (MRP ₹499) |
| `book-qb-pdf` | PDF access (login required) | ₹199 |
| `book-sb-pdf` | PDF access (login required) | ₹99 |

### Page/route map

- `public/index.html` — everything: intro, course, books, practice, contact.
- `public/dashboard.html` — OTP login, then the logged-in student's library
  (entitled PDFs → "Read now"; not-yet-bought PDFs → buy button).
- `public/reader.html` — the locked-down PDF.js reader, one product at a
  time via `?product=`.
- `worker/index.js` — all `/api/*` routes; anything else falls through to
  `env.ASSETS.fetch(request)` (the static files above).

---

## 4. Scope decisions worth knowing before "fixing" anything

These are **deliberate**, not oversights — don't undo them without asking
Pranav first:

- **No free-resources section anywhere on the revamped site.** Explicit
  instruction, not a bug.
- **Chapter-wise selling doesn't exist on the revamped site at all** — it
  was a Phase A concept, paused there, and never carried into Phase B
  because Phase B's spec never included it. If Pranav wants it back, it's
  new work against Phase B, not a restore of old code.
- **PDF protection is "locked-down viewer," not watermarked page images.**
  Chosen explicitly for build simplicity over Phase A's original stronger
  (but heavier) proposal. No method makes a screen unphotographable —
  this was stated to Pranav plainly, not oversold.
- **Payment confirmation is instant/automatic** (real server-side
  signature verification), Pranav's explicit choice over "manual, check
  Razorpay dashboard yourself" — see §5's open item #2 for the one real
  gap this still has.
- **`capranav-website/` (Phase A) is intentionally left on disk**,
  untouched, not deployed. Don't delete it without asking; don't assume
  it's stale garbage either.

---

## 5. What's actually been verified for real (not just written)

Every one of these was checked against the **live production site**, not
just locally, and test data was cleaned up afterward each time:

- Real OTP email delivery and login (both against Cloudflare Email Sending
  directly and through the full login flow).
- Real Razorpay order creation in both test mode and live mode.
- Real HMAC-SHA256 signature verification, matched against both a Node
  `crypto` computation and the Worker's own Web Crypto implementation, in
  both test and live mode.
- Real entitlement granting after a verified payment.
- Real protected PDF byte streaming (checked exact file size match, not
  just a 200 status).
- Real guest checkout (course, physical book) including the required
  shipping fields.
- Real error paths: PDF purchase attempted while logged out (401), unknown
  product id (400), missing required fields (400).
- Real contact form submission → real email delivery.
- A genuine, independently-discovered **real live payment** (₹99, Strategy
  Book PDF, `pay_TXCRebBIURMiG9`) that a real user completed — not staged
  by this session.
- The D1 backup job running **unattended** on its own schedule (checked
  the log for automatic runs after the fact, not just the one manually
  triggered to prove it worked).

One thing to know about the test data: some of it was created under
`pranavaiversion@gmail.com` (this AI session's own linked account) while
verifying the live flow. Test entitlements/orders/sessions were deleted
after each check — **except** one real order that turned out to be
genuine user activity, not test residue (see open item #1 below).

---

## 6. Open items — nothing below this line is done

Ranked roughly by how much it matters, not necessarily build order (a new
agent picking this up should still gate each one separately — see the
handoff prompt in `HANDOFF-PROMPT.md`).

1. **No Razorpay webhook — payment confirmation depends entirely on the
   buyer's browser calling back.** If a payment succeeds on Razorpay's
   side but the browser closes/crashes/loses connection before
   `/api/orders/verify` runs, Razorpay will show the money received while
   this site's database still shows `pending` — and the buyer won't get
   automatic access. Nothing currently reconciles that gap. This is the
   single most important functional item on this list.

2. **No Privacy Policy / Terms / Refund / Shipping page** — only a
   one-line footer disclaimer ("all purchases final"). The site now
   processes live payments; worth checking whether Razorpay or normal
   business practice expects more than a one-liner. Don't invent legal
   commitments (especially refund terms) without Pranav's explicit
   sign-off — this was true for Phase A too and still holds.

3. **No admin visibility into orders/entitlements** beyond the
   order-notification email and querying D1 directly by hand. Fine for
   today's volume; won't scale to "check this manually" once there are
   more than a handful of orders a week.

4. **No rate-limiting on `/api/otp/send`.** Anyone can request unlimited
   OTP codes for any email address, which is both an abuse vector (spam
   someone's inbox) and, at volume, an email-sending cost/reputation risk.
   Not yet exploited as far as is known — a real gap nonetheless.

5. **No abuse protection on `/api/contact`.** Same shape of gap — nothing
   stops automated spam submissions.

6. **Backup job failures are silent.** `tools/backup_d1_snapshot.py`
   writes to a local log file nobody is watching. If it starts failing
   (Cloudflare auth expiring, disk full, etc.), nothing alerts anyone —
   contrast with the Telegram platform's own down/up watcher pattern
   elsewhere in this account, which this doesn't have.

---

*Keep this file current. When an open item above gets closed, move it into
§2 with the same level of "what was actually verified" detail — don't just
delete the line.*
