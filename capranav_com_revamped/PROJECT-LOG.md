# capranav.com — Project Log

Read this file first if you're picking up this work with no prior context.
It records what was built, why, what's genuinely verified vs. assumed, and
exactly what's still open. Keep adding to it in the same style as work
continues — don't let it go stale.

---

## Open TODO list (added 2026-09-24 — keep this current)

1. **YouTube player + Shorts viewer** (`/videos/`). Official `youtube-nocookie.com`
   embed, IFrame Player API. Data in one `videos.json` for now (long videos +
   Shorts: id, title, type, group, order); **document the later move to a D1
   `videos` table + admin page**. Shorts viewer: custom vertical scroll-snap feed,
   auto-advance on end (toggle), loop, mute, speed, group chips, deep links.
   Public, no login (may change later). Groups decided from the *nature* of the
   videos once Pranav sends the links (check each link: `/shorts/` = Short; title
   via YouTube oEmbed). Autoplay starts muted (browser rule). Not deployed yet.
2. **Downloadable Excel tables.** Buttons such as "Top 100 topic list" that download
   sheets of `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/
   ca_inter_descriptive_topic_priority_v1.xlsx`: Top 100 PYQ, Chapter Priority,
   Topic Attempts (has PYQ/MTP/RTP marks + sittings), Question Topic Map,
   A-B-C-D Questions, Study Topics. Most data is already in D1 (`aa_*` tables) —
   confirm per sheet what is missing, then generate .xlsx server-side per request
   (or pre-generate per sheet into R2 and serve via `aa_documents`). No
   "MTP-wise topic list" sheet exists by that name — Topic Attempts carries MTP
   marks/sittings; a dedicated MTP view would need building. Decide with Pranav.
3. **Security hardening vs `Main1lavyaAIAgents/SECURITY-LEVEL3-RECOMMENDATIONS.md`**
   — see the audit below/in chat: Turnstile on OTP/contact/admin login, per-IP
   OTP limit, Cloudflare rate-limiting rule + Bot Fight Mode, Cloudflare Access on
   `/admin`, security headers (HSTS/CSP/X-Frame-Options).

---

### Must Practice surfaced on the homepage — 2026-09-24

Checked how a student actually reaches the Must Practice page and found they
effectively could not: the homepage had no link to it, or to the practice hub at
all. The only route was capranav.com → `/anatomy/` → the practice hub → the card,
three clicks deep behind a link titled "The Anatomy of Advanced Accounts", which
gives no hint that practice questions sit behind it.

The near-miss worth recording: the homepage already had a section headed
**"Practice"** containing only the Telegram MCQ bot and the Anatomy explorer — a
practice section that did not mention the practice questions.

Added a card to that existing section, placed first, and reworded the heading
from "Free MCQ practice." to "Practice, free." — the old heading would have
misdescribed the section the moment a descriptive-question card sat under it.
Deployed version `8f622617-0465-4a1c-8165-d00f2285093c`, verified live: the
homepage carries the link, the heading changed, and the target returns 200.

One self-inflicted thing caught and fixed in the same pass: a temporary `__p.html`
iframe harness used to screenshot the section was deployed to production to take
the shot. Removed and redeployed; confirmed it now 404s. Screenshot harnesses
belong on the local dev server, not on the live site.

---

### Must Practice selection rules written down and encoded; AS 10 built locally — 2026-09-24

The AS 2 shortlist was published on 2026-09-23 as a hand-typed list of ten ids:
the reasoning existed, the formula behind it did not. `build_must_practice_data.py`
only rendered what a session had picked, so a second unit would have been a fresh
judgement call with nothing to hold it to.

New `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/MUST-PRACTICE-RULES.md`
states the rule and the reasoning behind each weight — including the two a reader
would argue with: why Study-Material match is weighted so heavily, and why a PYQ
scores *lower* than an MTP/RTP (an MTP/RTP signals the paper ahead; a PYQ in that
exact form has just been used). `SCORING` in the build script is now the single
place the weights live, and the script computes the shortlist and prints every
question's score.

**Encoding the formula changed AS 2 by one question.** It reproduced nine of the
ten; it ranks `M2C5U1-009` above `M2C5U1-013`, where the hand pick had kept -013
as the most recent question actually set in a real exam. Pranav's call: the
formula stands, and AS 2 was republished to match. Deployed version
`34e43885-87cd-4822-91a2-cfa8b43d573f`.

A limitation is stated in the rules rather than hidden: the coverage pass
guarantees no Top-100 topic is missed but does not cap duplication, so AS 2's
computed ten include six on exclusions from cost of inventories. The fix, if
wanted, is a per-topic cap in the coverage pass — not a hand edit.

**AS 10 (`M2-C5-U2`) built locally**, `published: false`, so the live picker still
shows only AS 2. Ten questions from a library of 16, all five Top-100 topics of
the chapter covered, pages 65–78.

The page resolver was upgraded along the way: two AS 10 questions are printed
twice in the book (home chapter plus another chapter's Integrated section), so
their header matched two pages and the old resolver returned None. It now
resolves the unambiguous questions first, uses their median page to locate the
chapter, and picks whichever hit sits nearest — still returning None, never a
guess, when nothing anchors the chapter. AS 2's page numbers are unchanged.

Open: two AS 10 questions (`-007`, `-008`) tie at exactly 0.487 with two others
from the same RTP, so which two make the cut is currently sort order rather than
a real distinction.

---

### Question Bank e-book moved to VC Gurukul checkout — published 2026-09-23

The ₹199 Question Bank e-book is no longer sold through this site's Razorpay
checkout. It now links to
`https://www.vcgurukul.com/product/advanced-accounting-question-bank-e-book-ca-pranav-p-tulshyan`,
the same arrangement already made for course enrolment on 2026-09-06, and
written the same way: the in-site path is commented/guarded rather than
deleted, so restoring it is a small, documented reversal.

Changed in four places, front and back: `worker/lib/products.js` gives
`book-qb-pdf` an `externalCheckoutUrl` and comments out `amountRupees`;
`worker/index.js`'s `handleOrderCreate` refuses to open a Razorpay order for
any product carrying that field; `public/assets/app.js` redirects that one
product's button; `public/assets/dashboard.js` renders a "Buy on VC Gurukul"
link instead of the buy modal and redirects the `?buy=book-qb-pdf` deep link.
The server-side guard is the part that matters — without it a hand-crafted
POST could still have created a ₹199 order.

**The product entry is deliberately kept, not deleted**: students who already
bought PDF access hold a `book-qb-pdf` entitlement and still need `fileKey` to
read via `/api/read`. Existing entitlements are untouched; only new in-site
purchases are refused, and the dashboard still shows "Read now" for owners.

Prices are no longer asserted for this product anywhere on the site (the home
card shows "Buy ↗", the pricing table links to "See price on VC Gurukul") —
VC Gurukul sets that price and this site cannot see it. The books section's
intro copy was also corrected: it promised "PDF access you can read right here
after logging in" for both books, which is no longer true for the Question Bank.

Verified against a local `wrangler dev` and then again live: `book-qb-pdf`
returns 409 with the external URL, `book-sb-pdf` still returns 401 (in-site
flow intact), `book-qb-physical` still returns its normal 400 address error.
Screenshots of the live home card and pricing table confirmed. Deployed
version `c857701b-63fb-46d3-b116-3098ccf57e9c`.

**Open for Pranav**: a VC Gurukul purchase does not create an entitlement on
capranav.com, so those buyers cannot read the book in the on-site reader —
VC Gurukul must deliver the file itself. If on-site reading is still wanted for
them, that needs a deliberate fulfilment step (manual entitlement grant, or an
integration) that does not exist today.

---

### Must Practice Questions page, AS 2 live — published 2026-09-23

New public page at `/practice-with-pranav-bhaiya/must-practice/`: a Module →
Chapter → Unit picker over all 36 units, a ranked table of the must-practice
descriptive questions for the chosen unit, each row expanding to the verbatim
question with the answer kept behind a Show answer button. AS 2 (Valuation of
Inventories) is the first unit published — 10 questions shortlisted from the
17 descriptive AS 2 questions in the corpus.

The shortlist is ranked on Top-100 topic weight, closeness to an ICAI Study
Material question (the strongest repeat signal), paper type and recency, and
marks, then adjusted so all six Top-100 AS 2 topics are covered rather than
five near-identical questions on exclusions from cost. Worth knowing for the
pitch: AS 2 has drawn zero marks across the last three PYQs (Jan 2026, May
2026, Sep 2026) after a 5/7/4/5 run, so it is overdue.

`tools/build_must_practice_data.py` generates everything served by the page.
It reads the reviewed question/answer HTML from the practice library under
`books/ca-inter/smat-may-27-edition/`, the topic ranks from
`descriptive_topic_priority.json`, and — the part worth calling out — resolves
each question's printed Question Bank page number by matching its own printed
header line (`MTP May 2024 Set 2 · Q1(b) · Marks: 5`) against the text layer of
the distributed `..._V1.pdf`. Every one of the 10 resolved to exactly one page,
in monotonic order (pages 46–61). A header that does not resolve to exactly one
page yields `null` and the page renders "not traced" rather than a guess. The
Module/Chapter/Unit tree is likewise derived from the canonical topic ranking
into `data/index.json`, so the picker cannot drift from the real syllabus.

Verified before and after deploying: local headless-Edge screenshots of the
table, an expanded question, the revealed answer with its accounting tables and
the Author's Note; `wrangler deploy --dry-run`; then on production, HTTP 200 on
the page, both JSON files, both assets and the unchanged `/`, `/anatomy/` and
practice hub, a live screenshot, and a check that the served JSON carries all
10 questions with their page numbers. Deployed version
`6d9bf497-f03f-47ac-9c0a-589e6e8d8363`.

Open: only AS 2 is published. Adding a unit means adding one entry to `UNITS`
in the build script and re-running it — no page or JS change. Every other unit
lists honestly as "coming soon".

---

### Anatomy rankings, explorer controls and R2 PDF library — published 2026-09-22

Added overall rank and priority band to all 400 syllabus topics (Top 50, Next
50, and Beyond Top 100). Expanded the live explorer with sortable columns,
direction arrows, a priority-band filter, universal topic-ID/page/name search,
and a full reset control. Uploaded 36 unit study-material PDFs plus 62 available
PYQ/MTP/RTP question, answer and examiner-comment documents to the existing R2
bucket under `anatomy/`; registered all 98 documents in D1 through foreign-keyed
unit/sitting junctions; and added separate Open PDF and Download actions. Took a
fresh D1 snapshot before migration, passed local and remote foreign-key checks,
deployed Worker version `5d8e5598-2163-4a5e-b76f-274613fa97f8`, and verified
topic-ID search, page search, the exact 50-row priority filter, Range/inline PDF
delivery, attachment download, `/api/me`, and the dashboard on production.

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

### Practice with Pranav Bhaiya Day 1 decks — published 2026-09-22

Published the three confirmed canonical HTML presentations at
`/practice-with-pranav-bhaiya/`: Day 1 Opening, Advanced Accounts Syllabus
Flow, and Marks Split/AS 2 Transition. The source files remain under the book
workspace. `tools/sync_practice_slides.py` copies them into Worker Assets so
future deck edits have one explicit release step and the sources do not drift.

Verified source and published-copy hashes match for all three files. Wrangler
dry-run passed. After deployment, the hub and each deck returned HTTP 200 on
`capranav.com`; all three live HTML files contain working Enter, Right Arrow,
Space, mouse-click, previous/next-button, and fullscreen handlers. The Anatomy
page links to the new hub, and the existing login API remained healthy.

### The Anatomy of Advanced Accounts — first release (2026-09-22)

Added a public, read-only syllabus and descriptive-question explorer at
`/anatomy/`, linked from the homepage Practice section. It uses the existing
Worker and existing `DB` binding only. The new additive `aa_*` schema contains
3 modules, 15 chapters, 36 units, 400 topics, 35 sittings, 509 descriptive
questions through the September 2026 PYQ, 649 many-to-many question-topic
links, 62 study-material items, and 133 PYQ-to-study-material match rows.

The import is reproducible through `tools/build_anatomy_seed.py`; generated SQL
is local-only. A fresh live D1 export was taken before applying the migration.
Remote counts were queried after import, `PRAGMA foreign_key_check` returned no
rows, and the September 2026 sitting reconciles to 84 offered descriptive
marks. Three older/source totals remain explicitly visible for review rather
than silently altered: PYQ September 2024 (86 vs 84), MTP November 2023 Set 1
(125 vs 120), and PYQ May 2023 (125 vs 120).

Wrangler dry-run passed. Production smoke tests confirmed `/anatomy/`, its
overview/hierarchy/topics/questions APIs, the homepage link, `/api/me`, the
dashboard, and the protected-reader unauthenticated 401 boundary. No charting
was included in this release; heatmaps and pivot-style analysis follow only
after the database review.

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
live at that moment, just not the ones on file now. **Confirmed by Pranav
2026-09-03**: yes, the live keys were rotated that day, deliberately, no
issue — matches this session's own reconstruction exactly.

Reported this finding to Pranav (not just "what should I do with it") before
asking for a decision, since it changed the picture from "possible real
missed payment" to "no recoverable evidence a payment was ever possible."
Gave him the option to supply the old key pair if he had it. He chose: mark
it abandoned, don't grant access. Ran `UPDATE orders SET status='failed'
WHERE id='f440abb8-02f1-441e-bec8-ee1f881fe514' AND status='pending'`
directly against remote D1 (not deleted — kept as a real historical row),
confirmed `changes: 1` in the response, then re-queried the row and confirmed
`status` now reads `failed`.

**Item 2 — Razorpay webhook (`POST /api/razorpay/webhook`) — built, deployed,
verified, and closed 2026-09-03.**

- Pranav registered the webhook in the Razorpay Dashboard himself (Live
  Mode) — URL `https://capranav.com/api/razorpay/webhook`, events
  `order.paid` and `payment.failed`, and supplied the secret he set there.
  Stored via `wrangler secret put RAZORPAY_WEBHOOK_SECRET` (confirmed via
  `wrangler secret list` output showing the new name — value never
  printed/logged/committed) and appended to `.dev.vars` (gitignored) for
  local `wrangler dev --remote` testing.
- Read Razorpay's actual webhook docs before writing any code, per the
  handoff's explicit instruction not to assume it's the same construction
  as the checkout signature: webhook signatures are HMAC-SHA256 of the
  **raw** request body (not `orderId|paymentId`), header
  `X-Razorpay-Signature`, keyed with the separate webhook secret — new
  `verifyWebhookSignature()` in `worker/lib/razorpay.js`, reusing the
  existing `hmacHex()` helper. Also confirmed via search that Razorpay
  sends a `X-Razorpay-Event-Id` header, unique per delivery, meant for
  dedup — used that for idempotency (see below).
- **Idempotency, two layers**, both real, both tested:
  1. New `webhook_events` table (`event_id` PRIMARY KEY) — a webhook
     delivery is recorded there on first receipt; a re-delivery of the
     same `X-Razorpay-Event-Id` hits a PK conflict and is acknowledged
     (`200 {"ok":true,"duplicate":true}`) without touching anything else.
  2. The actual order mutation itself is idempotent independent of the
     table above: `markOrderPaid()` (new shared helper, factored out of
     `handleOrderVerify` so both the webhook and the browser's own
     `/api/orders/verify` call run the exact same logic) does
     `UPDATE orders SET status='paid', ... WHERE id = ? AND status != 'paid'`
     and only grants the entitlement / sends the notification email if
     that UPDATE's own `changes` count is 1. This is what makes a genuine
     race between the webhook and the browser's verify call safe — the
     database's own atomic conditional write decides which of the two
     "wins," not a read-then-act check beforehand, closing exactly the
     double-grant/double-email risk the handoff flagged.
  3. `payment.failed` is acknowledged (event recorded, 200 returned) but
     deliberately makes no order-state change — a single failed attempt
     doesn't mean the order is dead, since Razorpay allows retrying
     payment against the same order, so leaving `status` alone means a
     later successful attempt on that same order still completes
     normally through the existing paths.
- **Verified for real against the live production database and the live
  Razorpay account** (not just structurally), before deploying:
  - Ran `wrangler dev --remote` (bound to the real `capranav-platform` D1,
    same as production) and created a genuine order via
    `POST /api/orders/create` (`book-sb-physical`, no login needed),
    getting back a real live-mode Razorpay order id.
  - Sent a hand-crafted `order.paid` webhook payload matching Razorpay's
    documented shape, signed with the real webhook secret exactly the way
    Razorpay signs it (Node `crypto.createHmac('sha256', secret)` over the
    raw JSON string) — confirmed the order flipped `pending → paid` in the
    real D1 row, `razorpay_payment_id` and `paid_at` were set correctly.
  - Confirmed a bad signature is rejected with 400 before touching the
    database at all.
  - Confirmed a **literal re-delivery of the same event id** is
    acknowledged but not reprocessed (`duplicate: true`), and separately
    confirmed the **race scenario** (a second, genuinely distinct event
    for an already-paid order — modeling the webhook and the browser's
    verify call both firing) leaves `paid_at`/`razorpay_payment_id`
    unchanged from the first transition, proving the entitlement/email
    side effects only ever run once.
  - Confirmed a `payment.failed` event for an unrelated/unknown order is
    acknowledged (200) and mutates nothing.
  - This test order was a physical book, so the real "new order"
    notification email genuinely fired to
    `capranavpratiktulshyan@gmail.com` as a side effect of proving the
    non-PDF branch works too — flagged to Pranav so a
    "New order — Webhook Test" email in that inbox isn't a surprise.
  - All test rows (the order, the 3 `webhook_events` test rows) deleted
    afterward; re-queried and confirmed 0 residue.
  - Deployed with `wrangler deploy`, then smoke-tested the real
    `https://capranav.com/api/razorpay/webhook` (not the workers.dev
    preview URL) with a garbage signature — got a real 400
    `"Invalid signature."` back, confirming the route is live on the real
    domain and actually verifying, not just returning success for
    anything.
  - **Razorpay does not actually offer a generic "send a sample event"
    button for a live-mode webhook** (checked their docs directly after
    initially assuming it did, and corrected that with Pranav rather than
    quietly dropping it) — their documented test path is a *separate*
    test-mode webhook + test-mode API keys + a test-card payment, which
    this project doesn't have configured and would be new parallel setup
    just to re-prove what was already proven above. Presented Pranav the
    honest choice — a real tiny live purchase for a Razorpay-initiated
    delivery, or accept the verification already done — and he confirmed
    the existing verification is sufficient. **Item closed 2026-09-03.**

**Item 3 — Privacy/Terms/Refund/Shipping page — built, deployed, and
reviewed. Closed 2026-09-04.** Wording drafted by this session at Pranav's
explicit request. Asked first whether he wanted a dedicated page at
all (per the handoff) — he said yes. Then asked for the actual
substance (refund terms, shipping specifics, privacy commitments) per the
handoff's "don't invent legal commitments yourself" instruction — he
explicitly told this session to invent it, asking for something neutral
and not biased. New `public/policies.html` (linked from the homepage
footer, replacing the old one-line-only disclaimer with a link to the
full page) covers four sections — Privacy Policy, Terms of Service,
Refund & Cancellation Policy, Shipping Policy — kept deliberately close to
what the site actually, technically does (no card data stored — Razorpay
handles that; data lives in Cloudflare D1; OTP-only login; the locked-down
PDF reader; no separate shipping charge since it's already folded into
the printed price) rather than promising anything not actually true of
the current build. Deployed with `wrangler deploy`; confirmed live at
`https://capranav.com/policies.html` (307-redirects to `/policies` —
confirmed this is pre-existing Workers Assets behavior, `dashboard.html`
does the same, not something new). Pranav reviewed the actual live page
and confirmed 2026-09-04 the wording is correct — gate satisfied.

**Item 4 — order-notification email made nicer — built, deployed, verified,
closed 2026-09-04.** Asked Pranav to pick a scope for admin visibility (per
the handoff's "ask before building" instruction); he chose the smallest
option — improve the existing notification email, no new admin page/login.
Two real gaps closed in the same change: the email previously fired only
for courses/physical books, meaning **every PDF purchase sent zero
notification at all** — now every paid order of every type emails
Pranav, with a clear "no action needed, access already granted"
vs. "action needed — ship/enrol" line so he can tell at a glance which
need his attention. New `orderNotificationEmailHtml()` in
`worker/lib/email.js` (order id, Razorpay payment id, amount, buyer
contact, shipping address if physical, paid-at timestamp, in a proper
table layout) replaces the old two-line HTML string. Along the way, fixed
a real latent bug in `markOrderPaid()`: it read `paid_at`/
`razorpay_payment_id` off the pre-UPDATE `order` snapshot for the email,
which would have shown blank/stale values — now both are computed once in
JS and passed into both the UPDATE and the email so they can never
diverge. Also added a `console.error` on email-send failure (previously
silently swallowed with no log at all), matching the pattern
`handleOtpSend` already used.
- **Verified for real**: created a genuine order via `wrangler dev
  --remote` (bound to production D1), sent it a real signed `order.paid`
  webhook, confirmed the order row updated with the JS-computed
  `paid_at`/payment id (not blank/stale), and confirmed no
  `order notification email failed` line appeared in the Worker log —
  i.e. the real Cloudflare Email API call succeeded. Test order and
  webhook-event row deleted afterward, confirmed gone. Also unit-tested
  `orderNotificationEmailHtml()` directly in Node for both the PDF
  (no-shipping) and physical-book (with-shipping) cases before touching
  the live path, to catch a template bug cheaply if there was one.
- Deployed with `wrangler deploy`.

**Item 5 — rate-limiting on `/api/otp/send` and `/api/contact` — built,
deployed, verified, closed 2026-09-04.** No scope question needed here
(the handoff doesn't gate this phase on a business decision, just asks for
"reasonable limits" — an engineering call). Both endpoints now cap at
**5 per hour** — OTP by email address (counted directly off the existing
`otp_codes` table, no new table needed), contact by submitter IP
(`CF-Connecting-IP`, new `ip` column on `contact_messages`). The counting
query for both is a windowed `COUNT(*) ... created_at > datetime('now',
'-60 minutes')` — no new infrastructure, reuses D1. Contact also got a
hidden honeypot field (`name="website"`, invisible to real visitors) — a
bot that fills every field gets a fake `{"ok":true}` with nothing saved or
emailed, no signal back that it was caught.
- **Verified for the exact boundary, not just "a limit exists"**: sent 6
  rapid OTP requests for one test email — the first 5 were correctly
  allowed through the rate gate (confirmed 5 real rows in `otp_codes`
  after), the 6th was rejected with 429 before touching the email-send
  path at all. Separately confirmed a real Cloudflare Email suppression on
  the `pranavaiversion@gmail.com` mailbox and every `+alias` of it
  (unrelated pre-existing condition, confirmed via a direct raw API call
  bypassing this session's code entirely — not a bug introduced here;
  worth Pranav knowing this test account can't currently receive
  Cloudflare-sent mail, likely from bounce/complaint volume during past
  testing) — then re-verified the OTP path really does send successfully
  end-to-end using a different, unsuppressed real address
  (`capranavpratiktulshyan@gmail.com`, one single request, confirmed 200).
  Did the same 6-rapid-requests boundary test for `/api/contact` (5
  allowed, 6th blocked with 429 — all 5 real notification emails clearly
  labeled "RATE LIMIT TEST (please delete)" in the subject/body so
  they're unambiguous in Pranav's inbox), and separately confirmed the
  honeypot path returns success but creates zero DB row. All test
  `otp_codes`/`contact_messages` rows deleted afterward, re-queried and
  confirmed 0 residue.
- Live D1 migration applied directly (`ALTER TABLE contact_messages ADD
  COLUMN ip TEXT` + a new index) — checked `PRAGMA table_info` first to
  confirm the column didn't already exist, since SQLite/D1 has no `ADD
  COLUMN IF NOT EXISTS`. `schema.sql` updated to match for any future
  fresh install.
- Deployed with `wrangler deploy`; smoke-tested the honeypot path on the
  real `capranav.com` domain post-deploy (200, no row created) to confirm
  the deploy actually took.

**Item 6 — backup-failure email alert — built, verified, closed
2026-09-04.** Per Pranav's choice, reused the existing
`CF_EMAIL_API_TOKEN`/`CF_EMAIL_ACCOUNT_ID` pattern rather than the
Telegram platform's watcher. `tools/backup_d1_snapshot.py` now sends a
failure-alert email (via a plain `urllib` call to the same Cloudflare
Email Sending API `worker/lib/email.js` uses — Python, so no access to the
Worker's own module, reads the same `.dev.vars` file directly instead) to
`capranavpratiktulshyan@gmail.com` whenever `run_export()` fails, with the
real error tail in the email body. New `--database` CLI flag (defaults to
the real `capranav-platform`) exists specifically so this could be tested
by deliberately pointing at a nonexistent name, per the handoff's own
instruction, without needing to hand-edit the script.
- **A real, pre-existing bug was found and fixed while testing this**:
  `log()`'s plain `print(line)` crashed with `UnicodeEncodeError` on
  Windows' default console codepage the moment wrangler's own error output
  contained an emoji — which is exactly what a real failure's error text
  contains. Uncaught, this would have crashed the script **before ever
  reaching the new alert code**, silently defeating the entire point of
  this phase on a genuine production failure. Fixed with a
  try/except fallback to an ASCII-safe console print (the UTF-8 log file
  write, unaffected either way, still keeps the undamaged original text).
- **Verified by actually causing a failure**, per the handoff's explicit
  instruction: ran `python tools/backup_d1_snapshot.py --database
  capranav-platform-DOES-NOT-EXIST-test` — confirmed it detected the
  export failure, logged it, and the failure-alert email API call
  returned `success: true` (real send, verified via the API's own
  response — same standard of verification used throughout this project
  when direct inbox access isn't available). Exit code 1, as expected.
  Then ran the script normally (real database) immediately after —
  confirmed a real, valid snapshot was written and the run stayed
  completely silent, no alert email attempted. That real snapshot file is
  legitimate backup data, not test residue, and was left in place.

### Reader upgrade: page-wise streaming, jump-to-page, Table of Contents; homepage photo re-cropped (2026-09-04)

Pranav asked for three reader improvements — real HTTP Range-based
streaming instead of downloading the whole PDF up front, a jump-to-page
control, and a Table of Contents — plus a homepage photo re-crop (bottom
20% removed, so nothing below the arms shows).

**Streaming**: `/api/read` now honors `Range` requests (new
`parseRangeHeader()`, R2's `bucket.get(key, { range })`, proper 206
responses with `Content-Range`/`Content-Length`, still auth/entitlement-
gated before touching R2 either way). `reader.js` switched from
`fetch().arrayBuffer()` (whole file into memory, then render) to
`pdfjsLib.getDocument({ url, withCredentials: true, rangeChunkSize: 512KB })`
— PDF.js now fetches only the byte ranges it actually needs per page.

**Verified for real, several independent ways, against the actual live
production D1/R2** (not just structurally):
- Byte-exact correctness: pulled a real range from the live endpoint and
  diffed it byte-for-byte against the same slice of the real 19,137,968-
  byte Question Bank Book PDF (`Buffer.compare` — exact match), for a
  normal range, an offset-only range, a suffix range (`bytes=-500`), and a
  range that overshoots EOF (correctly clamped, not an error).
- Auth still enforced on ranged requests: a `Range` request with no
  session cookie got 401 with zero PDF bytes leaked; an unknown product id
  got 404 before ever touching R2.
- Definitive proof the streaming savings are real, not just
  structurally-plausible: fetched the full file two ways over the same
  channel — reading it to completion took 3,572ms, while reading only the
  first chunk and then calling `reader.cancel()` returned in 373ms (~10×
  faster) — proving the server/R2 genuinely stops sending once the client
  stops reading, which is the actual mechanism PDF.js's per-page fetching
  depends on.
- Real browser verification: installed `puppeteer-core` temporarily
  (removed after, not committed), pointed it at the existing Edge install
  (`headless-Edge`, this repo's own established verification method — see
  §7 of `CLAUDE.md` in the parent repo), minted a real test session token
  + a temporary `book-qb-pdf` entitlement directly in D1 (OTP email login
  wasn't usable for this — see the suppression finding below), and drove
  the actual `reader.html` against the real 679-page book: initial render
  showed "Page 1 of 679" (matches the real PDF), jump-to-65 correctly
  showed "Page 65 of 679" with real rendered content, and the whole
  session (2 page navigations + opening the TOC) made only 3 total
  `/api/read` HTTP requests, the range ones a modest 524KB and 263,600
  bytes — not repeated full downloads. Screenshots confirmed correct
  visual rendering, including the TOC panel. Test session/entitlement
  deleted afterward, confirmed gone; the real `book-sb-pdf` entitlement
  for that account was left untouched.

**Jump-to-page**: a page-number input + "Go" button in the reader bar,
clamped to `[1, numPages]`, wired directly to the same `renderPage()` used
by Prev/Next/TOC clicks — verified above via the real jump-to-65 test.

**Table of Contents**: new `public/assets/book-toc.js`, one entry per
product. **Checked both real PDFs for an honest source before building
anything** — neither has a usable embedded PDF outline (Question Bank Book
has none at all; the Strategy Book's is auto-generated noise: fragments
like "2026", "1.", a repeated header line, not real chapters). The
Question Bank Book DOES have a real, printed Table of Contents on its own
pages 8–9 — extracted its full text directly (`pymupdf`) and transcribed
all **34 real chapters with their real page numbers** verbatim, not
invented. **The Strategy Book got no TOC entry, on purpose** — checked
every page's largest text across all 112 pages and found it's a visual
slide-deck with almost no chapter-title text at all (just page numbers and
a hashtag line, until a narrative section starting page 95) — there's
nothing honest to extract a chapter list from. The reader UI handles this
gracefully (Contents button disabled with a tooltip, panel shows "No table
of contents available for this book yet" instead of pretending one
exists). **Flagged to Pranav, not silently decided**: if he wants a Strategy
Book TOC, it needs either his own section breakdown or this session doing
a full manual page-by-page review for his sign-off — not something to
invent from the PDF alone.

**Homepage photo**: `public/assets/ca-pranav-professional.png` — confirmed
real dimensions first (1086×1448, RGBA, genuinely transparent background,
not opaque black), cropped to the top 80% (1086×1158, bottom 290px
removed) via Pillow, visually reviewed before deploying (ends right at the
crossed arms, no awkward cut). Verified live afterward by downloading the
actual production image and checking its real dimensions match
(1086×1158, not the old 1448).

**Housekeeping**: `puppeteer-core` (and the `package.json`/
`package-lock.json`/`node_modules` npm bootstrapped in passing) were
removed after testing — this project has never needed a `package.json`
(Wrangler bundles `worker/index.js` directly, no npm dependencies in the
Worker code), so nothing about this testing pass is left in the repo.

**One temporary diagnostic, since removed**: while chasing exact
byte-transfer proof, briefly added a byte-counting `TransformStream`
wrapper + `console.log` to `handleRead` — `wrangler dev --remote`'s
"remote preview" mode turned out not to stream Worker `console.log` back
to the local terminal (a real, if minor, tooling gap worth knowing for any
future session trying the same thing), so this avenue was abandoned in
favor of the early-cancel timing test above, and the diagnostic code was
fully removed before the final deploy — confirmed via `grep` for
"TEMP-DIAG"/"counted" returning nothing.

Deployed with `wrangler deploy`; live content on `capranav.com` confirmed
directly (not just trusting Wrangler's own "no updated asset files" message,
which turned out to be a reporting quirk — this deploy, like others this
session, silently did take effect; `reader.html`/`reader.js`/`book-toc.js`/
the cropped photo were all independently curled from the real domain and
matched the new local content exactly).

### Five named compliance pages + GSTIN/registered-address, and a real dashboard (profile + order history) (2026-09-04)

Pranav asked to confirm five specifically-named pages exist — **Terms and
Conditions, Privacy Policy, Cancellation and Refund, Shipping and Exchange,
Contact Us** (this exact five-item wording is Razorpay's own standard
website-policy checklist for live merchant accounts, not a coincidence) —
with GSTIN and registered-address details displayed properly, plus a real
student dashboard showing past orders/payments and letting a student
maintain a profile.

**Compliance pages**: the already-approved `policies.html` content (Pranav
signed off on this wording 2026-09-04, see above) was real and correct, but
lived only as anchored sections on one combined page — split it into five
genuinely standalone pages, same approved text verbatim, no new legal
wording invented: `public/privacy.html`, `terms.html`,
`cancellation-and-refund.html`, `shipping-and-exchange.html` (all reusing
the exact already-approved sentences), plus a new `contact-us.html` (email,
socials, the same contact form/`/api/contact` endpoint, wired with its own
small inline script rather than reusing `assets/app.js` wholesale — that
file assumes homepage-only elements like the course-attempt picker and
would throw before ever reaching the contact-form wiring on a page that
doesn't have them). `policies.html` itself kept live too (not deleted —
still a valid combined reference) and updated to cross-link to all five.

**GSTIN + registered address** — supplied directly by Pranav, used
verbatim, not reformatted or guessed at: **GSTIN 10AXBPT7695J1Z1**,
registered address "Ground Floor, Room No A102, Sikandarpur Road,
(Opposite Choudhary Store), Sikandarpur, Muzaffarpur, Bihar — 842001",
seller name "PRANAV PRATIK TULSHYAN". Shown two ways: a prominent
"Registered Seller Details" card on `contact-us.html` (and on
`policies.html`), and a compact line in the footer of **every** page on the
site (homepage + all five policy pages) so it's visible site-wide, not
just on one page a crawler might miss.

**Dashboard: order history + profile** — new `student_profiles` table
(`email` PK, `name`, `phone`, `updated_at`) — independent of any one order,
so "maintain your profile" is a real, persistent thing now, not just
whatever was typed at a past checkout. Three new endpoints:
`GET /api/profile` (returns the saved profile, or falls back to the most
recent order's buyer name/phone as a sensible default if nothing's been
saved yet — nothing is written until the student explicitly saves),
`POST /api/profile/update` (upsert via `ON CONFLICT(email) DO UPDATE`),
`GET /api/orders/mine` (every past order for the logged-in email, any
status, newest first — product title resolved through the same
`getProduct()` catalogue everything else uses, so it can never drift from
the real product list). `dashboard.js` rewritten to show three stacked
sections — Profile (editable name/phone), Your Library (unchanged), Order
History (status badges: green Paid / amber Pending / red Failed) — and the
PDF-purchase modal now pre-fills name/phone from the saved profile instead
of asking blank every time.

**Verified for real against live production D1** (not just structurally):
ran the whole flow through `wrangler dev --remote` with a real minted test
session — confirmed `/api/profile` correctly falls back to a genuine past
order's buyer details (`"AI PRANAV"` / a real phone number) before any
profile is saved; confirmed a save + a second save both work and land as
exactly **one row** (`SELECT COUNT(*)` = 1 — the upsert doesn't create
duplicates); confirmed `/api/orders/mine` returns this account's real order
history, including the exact stale order investigated and marked `failed`
in Phase 1 above, correctly labeled; confirmed both endpoints 401 without a
session. Visually verified via headless-Edge screenshot — profile form,
library, and order history (correct green/red status badges) all render
correctly — and separately screenshotted all five new policy pages plus
`contact-us.html`, confirming real title tags, real body content, and the
GSTIN string present on every one. All test session/profile rows deleted
afterward, confirmed zero residue.

Deployed with `wrangler deploy`; independently re-curled all five new pages
plus the homepage footer and the two new `/api/profile`/`/api/orders/mine`
routes directly from `capranav.com` post-deploy to confirm they're actually
live (this deploy, like the ones before it, showed Wrangler's "no updated
asset files" message despite genuinely taking effect).

---

## 3. Current architecture — the concrete map

| Thing | Value |
|---|---|
| Live domain | `capranav.com` → Cloudflare Worker **`capranav`** (Workers + static assets, not Pages) |
| Cloudflare account | `Efficientcorporates@gmail.com's Account`, id `68e19e5bed11326478a23d6e2ad31453` |
| Deployed code | `D:\EffCorp_Projects\cap-online\capranav_com_revamped\` |
| Superseded code (kept, not deployed) | `D:\EffCorp_Projects\cap-online\capranav_com\capranav-website\` |
| D1 database | `capranav-platform`, id `03830ea8-b539-480b-b106-0743aeda1b1f` — tables: `otp_codes`, `sessions`, `orders`, `entitlements`, `webhook_events`, `contact_messages`, `student_profiles`, `admin_users`, `admin_sessions`, `admin_login_attempts`, `deletion_log` (see `schema.sql`) |
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
- `public/dashboard.html` — OTP login, then three sections: Profile
  (editable name/phone, `student_profiles` table), Your Library (entitled
  PDFs → "Read now"; not-yet-bought PDFs → buy button), Order History
  (every past order, any status).
- `public/privacy.html`, `terms.html`, `cancellation-and-refund.html`,
  `shipping-and-exchange.html`, `contact-us.html`, `about-us.html`,
  `pricing-details.html` — the seven standalone compliance pages
  (Razorpay's real merchant-activation checklist, confirmed against their
  own docs), each carrying the GSTIN/registered-address block in its
  footer. `public/policies.html` — the older combined reference, kept
  live, cross-linking to all seven.
- `public/admin.html` — single-admin login (separate from student OTP
  login), gating one action: look up and delete/anonymize a student's
  data per the privacy policy's deletion promise. `noindex, nofollow`.
- `public/reader.html` — the locked-down PDF.js reader, one product at a
  time via `?product=`. Streams via HTTP Range requests (not a full
  download), with jump-to-page and a Table of Contents panel
  (`public/assets/book-toc.js` — real, per-book chapter/page data,
  currently only populated for `book-qb-pdf`; see §2's 2026-09-04 entry
  for why the Strategy Book has none).
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
after each check — **except** one order that sat unresolved for a day
(§2's "Phase C" — investigated and closed 2026-09-03, turned out to have
no real Razorpay-side record at all, marked `failed`).

### Buyer confirmation emails, a single-admin data-deletion tool, and two more Razorpay-checklist pages (2026-09-05)

Pranav asked for three more things: (1) buyer-facing order-confirmation
emails (previously only he got notified — the buyer saw just an
in-browser "Thank you" message with no record afterward); (2) a real,
working mechanism behind the privacy policy's data-deletion promise,
gated behind an admin login; (3) checked whether the site actually covers
Razorpay's full merchant-activation checklist, not just the five pages
built 2026-09-04.

**Razorpay checklist, verified against Razorpay's own docs (not
assumed)**: the real checklist is Terms & Conditions, Privacy Policy,
**About Us**, Contact Us, **Pricing Details**, Refunds/Cancellation,
Shipping — two items (About Us, Pricing Details) beyond what was built the
day before. Built both: `public/about-us.html` (reuses the same
already-public bio/credentials text from the homepage, plus the
GSTIN/address block) and `public/pricing-details.html` (every real price
from `worker/lib/products.js`, in one place — course batches, both books
both ways, the free Telegram bot). All seven pages now cross-link to each
other in both their nav strip and footer, and the homepage/`policies.html`
footers were updated to match.

**Buyer confirmation email**: new `buyerConfirmationEmailHtml()` in
`worker/lib/email.js`, sent from `markOrderPaid()` to `order.buyer_email`
(alongside the existing owner-facing notification, not instead of it) —
different next-step line per product type (PDF: link to the dashboard;
physical: dispatch timing; course: "we'll reach out within 24 hours",
matching the existing in-browser copy verbatim so the two never
contradict each other). Unit-tested all three variants directly in Node
before touching the live path, then verified via a real order + real
signed webhook against production D1/Cloudflare Email — confirmed no
`buyer confirmation email failed` line in the Worker log (the real
send succeeded). Used `capranavpratiktulshyan@gmail.com` as the test
buyer address rather than the usual `pranavaiversion@gmail.com` test
account, since that account (and its `+alias`es) is the one already known
to be Cloudflare-suppressed (§6 below) — didn't want a suppressed address
to produce a false negative.

**Admin login + data-deletion tool**: entirely separate from the student
OTP-login system (`worker/lib/admin.js`, new `cp_admin_session` cookie,
new `admin_users`/`admin_sessions` tables) and scoped to exactly one
action, per how narrowly Pranav asked for it — no broader admin panel.
New `public/admin.html` + `assets/admin.js`: log in, type a student email,
see a real preview of what deleting it would touch (order count, whether
a profile exists, entitlement/session/contact-message/OTP-code counts —
each pulled live from its own table, not guessed), then confirm. The
actual deletion **anonymizes order rows** (`buyer_name`/`buyer_email`/
`buyer_phone`/`shipping_json` replaced with `'[deleted]'`/`NULL`, but
`amount_rupees`/`product_id`/`status`/`created_at` kept) rather than
deleting them outright — Pranav's own explicit choice, matching what the
privacy policy already promises about accounting/GST record-keeping —
while `student_profiles`, `entitlements`, `sessions`, `contact_messages`,
and `otp_codes` rows for that email are deleted outright. Every deletion
writes to a new `deletion_log` table (student email, admin username,
exact counts, timestamp) — a real audit trail, not just a silent action.
A brute-force guard (new `admin_login_attempts` table, 5 failed attempts
per IP per 15 minutes) sits in front of the login itself.

**A real security tradeoff, flagged and consciously accepted, not silently
built**: Pranav asked for the admin password to be stored in **plain
text**. Before building it, this was flagged back to him plainly — a
hashed password costs nothing extra in his own day-to-day login
experience, and only changes what's readable if the database (or one of
its local `.sql` backups, which already get written to disk every 6
hours) is ever exposed — and he confirmed he wants plain text anyway.
Built exactly that (`admin_users.password` compared directly, no
hashing), with a code comment on the table pointing back to this decision
so a future session doesn't "fix" it without asking again first.

**Verified for real against production D1** (not just structurally),
using a temporary test admin account (`test_admin_temp`) and a fully
synthetic student (`admin-delete-test@example.com`) with a real row
seeded in **every** affected table:
- Confirmed a bad password gets 401, and — separately — 6 rapid bad
  attempts correctly got the 6th (really the 5th distinct failure,
  since one earlier bad-login test had already logged one) blocked with
  429; confirmed exactly 5 rows landed in `admin_login_attempts`, not more
  or fewer.
- Confirmed a correct login succeeds and sets a working session
  (`/api/admin/me` correctly flips to `loggedIn:true`).
- Confirmed the lookup step reports the exact real per-table counts (1
  across every table for the seeded synthetic student, then re-checked
  showing 0/1 correctly on a second synthetic student that only had 2 of
  the 6 tables populated — proving the counts are genuinely live, not
  hardcoded).
- Confirmed the actual deletion left the order row **anonymized but
  present** (`buyer_name`/`email`/`phone` = `'[deleted]'`, `amount_rupees`/
  `status`/`product_id` untouched) and every other table's row for that
  email **genuinely gone** (`SELECT COUNT(*)` = 0 across all five), and
  confirmed a `deletion_log` row was written with the correct admin
  username and exact per-table counts.
- Confirmed unauthenticated calls to `/api/admin/lookup` and
  `/api/admin/delete-student` both 401 before touching anything.
- Visually verified via headless-Edge screenshot: the login form, and the
  logged-in tool correctly rendering real per-table counts pulled from
  production D1.
- All test rows (order, profile, entitlement, session, contact message,
  OTP code, the temp admin account/session, the login-attempt rows, the
  deletion-log row) deleted afterward; re-queried and confirmed 0 residue
  across every one of the new tables.

Deployed with `wrangler deploy`; independently re-curled `about-us.html`,
`pricing-details.html`, `admin.html`, and `/api/admin/me` directly from
`capranav.com` post-deploy to confirm they're actually live.

**Not yet done**: no real admin account exists in production yet — the
test account above was deleted after verification, on purpose, since
Pranav hadn't given a real username/password to seed it with. Asked him
for the actual credentials to create the real one.

### Course enrolment temporarily redirects to VC Gurukul; books unchanged (2026-09-06)

Pranav asked for course "Enrol now" to redirect to VC Gurukul's own
product page instead of this site's Razorpay checkout — explicitly
temporary, explicitly not to delete the in-site Razorpay course flow.
Books (`data-buy-physical`/`data-buy-pdf`) are untouched — still buy
directly on this site exactly as before; `worker/lib/razorpay.js` and the
whole `/api/orders/*` backend are untouched too (courses could come back
to using them the moment the button's own handler is restored).

Changed only `public/assets/app.js`'s `enrol-button` click handler: it now
does `window.location.href = COURSE_EXTERNAL_CHECKOUT_URL` (the exact URL
Pranav gave). The original handler (`openGuestForm` → `window.buyProduct`
→ Razorpay) is left directly below it, commented out rather than deleted,
with a comment explaining it's the revert path — restoring in-site course
checkout later is delete-the-redirect-line-uncomment-the-block, not a
rebuild.

**Verified for real**: ran this through `wrangler dev --remote` and a
real headless-Edge session — clicking a physical book's buy button still
opens the guest-checkout modal (confirming books are genuinely
untouched), and clicking "Enrol now" was confirmed (via a request-
interception check, so the test didn't actually hit vcgurukul.com)
to navigate to exactly the URL Pranav gave, byte-for-byte. Deployed with
`wrangler deploy`; independently re-curled the live `app.js` from
`capranav.com` afterward and confirmed the URL is really there.

(Also hit a real, unrelated environment issue while testing this: 4 stale
`wrangler dev` processes from earlier in this session were still holding
port 8787, making new dev-server instances flakily unreachable. Killed
them by PID and switched to a fresh port — worth knowing if a future
session sees `wrangler dev` claim "Ready" but the port doesn't actually
respond.)

---

## 6. Open items

All six phases from `HANDOFF-PROMPT.md` are closed as of 2026-09-04 (see
§2 for each one's full detail and verification). Nothing on the original
gated list remains open. One new item was found along the way and is
recorded here rather than quietly worked around:

1. **`pranavaiversion@gmail.com` (and every `+alias` of it) appears to be
   on Cloudflare Email Sending's suppression list.** Found while testing
   Phase 5's OTP rate limit: a direct, raw call to the Cloudflare Email
   API (bypassing this project's code entirely) returned
   `email.sending.error.email.sending_disabled` for that address and a
   `+alias` variant, while the identical call to
   `capranavpratiktulshyan@gmail.com` succeeded normally — so this isn't
   an account-wide outage, just that one mailbox. Cloudflare auto-adds a
   recipient to this list after a hard bounce, repeated soft bounces, or a
   spam complaint — plausible given how much test OTP volume this address
   received across this project's history. Not fixed here (it's
   Cloudflare's own anti-abuse mechanism working as intended, and this
   session doesn't have a documented way to remove a specific address from
   it) — flagging so Pranav knows this specific test account can't
   currently receive Cloudflare-sent mail, in case it comes up again
   during future testing. Every real order/OTP/backup-alert email path
   itself was independently confirmed working, using other real addresses.

2. **The Strategy Book has no Table of Contents in the reader** (the
   Question Bank Book does — see §2's 2026-09-04 reader-upgrade entry).
   Checked every page of the real PDF first — it's a visual slide-deck with
   almost no chapter-title text to honestly extract, so nothing was
   invented. Needs either Pranav's own section breakdown, or his sign-off
   for this session to do a full manual page-by-page review and propose
   one — not something to build unprompted.

---

*Keep this file current. When an open item above gets closed, move it into
§2 with the same level of "what was actually verified" detail — don't just
delete the line.*
