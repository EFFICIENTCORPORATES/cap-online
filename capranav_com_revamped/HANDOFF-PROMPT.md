You are picking up work on capranav.com from a previous AI session. Real
money, real student accounts, and a real live payment gateway are already
running on this site — treat it accordingly.

## Before you touch anything

1. Read `capranav_com_revamped/PROJECT-LOG.md` in full. It's the complete
   history of what was built, why, what's genuinely verified vs. assumed,
   and the exact architecture (Cloudflare account, D1 database id, R2
   bucket, Worker name, secret names, product catalogue, prices). Do not
   re-derive any of this from scratch or guess at it — it's already
   written down accurately.
2. Read `capranav_com_revamped/DATABASE-BACKUP.md` too — there's a backup
   job already running every 6 hours; don't duplicate it.
3. Open the live site yourself (capranav.com) and click through it before
   writing any code, so you're working against what's actually there, not
   what you imagine is there.
4. Section 4 of PROJECT-LOG.md lists deliberate scope decisions. Don't
   "fix" any of those — they're intentional, not oversights.

## Ground rules for this whole session

- **Never fabricate or assume a decision that's genuinely Pranav's to
  make** — pricing, legal wording (especially refund terms), what happens
  to the stale pending order, how much admin tooling he actually wants.
  Ask him directly. This exact instruction from him ("ask me for any
  queries and don't do any assumptions") is why the current site looks
  the way it does — keep honoring it.
- **Verify everything for real, against the live site, not just
  structurally.** "The code compiles" and "the endpoint returns 200" are
  not verification. Create a real test order, compute a real signature,
  confirm a real row changed in D1, then clean up the test data
  afterward — this is the standard the existing code was held to
  throughout PROJECT-LOG.md §5, and every phase below should match it.
- **Secrets never go in a file that gets committed, ever.** Use
  `wrangler secret put` for anything the deployed Worker needs, and
  `.dev.vars` (already gitignored) for local `wrangler dev --remote`
  testing. Never print a secret value into a commit message, a log file
  a human will read, or this repo's own memory/documentation files.
- **Cloudflare resources already exist — don't recreate them.** The D1
  database, R2 bucket, and Worker are already provisioned (see the table
  in PROJECT-LOG.md §3). Extend them; don't create parallel ones.
- **Don't touch `capranav_com/capranav-website/`** (the old, superseded
  site). It's kept for reference only and isn't deployed.
- **Keep the site's actual scope simple**, matching Pranav's repeated
  instruction — resist adding features nobody asked for while fixing the
  items below.
- Update `PROJECT-LOG.md` as you go, in the same style — move each closed
  item from §6 into §2 with real verification detail, don't just delete
  the line.

## The work, in gated phases

**Do not start a phase until the previous one has been confirmed working
by Pranav.** Each phase ends with an explicit stop: report what you did,
how you verified it for real, and wait for his go-ahead before continuing.
This mirrors how every phase of the existing build was actually done —
don't skip the gate because it feels slow.

---

### Phase 0 — Orientation (no code)

Read everything in "Before you touch anything" above. Then summarize back
to Pranav, in your own words, what's currently live and what the six open
items are — not to prove you read it, but so any misunderstanding surfaces
before you write a line of code.

**Gate**: Pranav confirms your summary is accurate.

---

### Phase 1 — The stale pending order

Query the `orders` table for the row described in PROJECT-LOG.md §6 item
1 (`book-qb-pdf`, ₹199, `pranavaiversion@gmail.com`, `2026-09-02
14:13:49`). Ask Pranav directly what happened with this — did he mean to
buy it and abandon the checkout, or is it safe to delete? Do exactly what
he says. Do not delete or modify it on your own judgment.

**Gate**: Pranav has told you what to do with this specific row, and
you've done it.

---

### Phase 2 — Razorpay webhook (the most important item)

Build a real webhook endpoint (`POST /api/razorpay/webhook`) so payment
confirmation no longer depends solely on the buyer's browser calling back.

- Register the webhook URL in the Razorpay Dashboard yourself is not
  possible for you to do — **ask Pranav to add the webhook URL and copy
  the webhook secret from his Razorpay Dashboard**, then store that secret
  the same way the existing Razorpay keys are stored (`wrangler secret
  put RAZORPAY_WEBHOOK_SECRET` or similar — match the existing naming
  convention in `worker/lib/razorpay.js`).
- Verify Razorpay's webhook signature (different mechanism than the
  payment signature already implemented — read Razorpay's own webhook
  docs, don't assume it's the same HMAC construction).
- Make the handler **idempotent** — a webhook can legitimately fire more
  than once for the same event. Getting this wrong could double-grant
  something or double-send a notification email; both are real bugs to
  design against up front, not patch later.
- Decide (and confirm with Pranav) how this interacts with the existing
  client-side `/api/orders/verify` path — most likely both can mark an
  order paid, whichever happens first, with the second becoming a no-op.
- **Verify for real**: Razorpay's Dashboard has a way to send a test
  webhook event — use it, don't just unit-test your signature-checking
  code in isolation. Confirm a real webhook delivery actually flips an
  order from `pending` to `paid` and grants the entitlement, end to end,
  on the live site.

**Gate**: a real Razorpay test webhook delivery has been shown to update
the live database correctly, and Pranav has confirmed the webhook URL +
secret are correctly set in his Razorpay Dashboard.

---

### Phase 3 — Privacy / Terms / Refund / Shipping content

Ask Pranav directly:
- Does he want a dedicated policies page, or is the current one-line
  footer disclaimer enough for now?
- If a page is wanted: what should the actual refund policy say? (Do not
  write a refund policy yourself and treat it as final — this is a real
  legal/business commitment, same rule that held for Phase A's policy
  page.)
- Any specific privacy commitments he wants stated (what data is
  collected, that OTP codes/orders live in Cloudflare D1, etc.)?

Only build the page once he's given you actual content to work from, not
before.

**Gate**: Pranav has reviewed and approved the actual wording before it's
published live.

---

### Phase 4 — Admin visibility into orders

Ask Pranav how much he actually wants here before building anything — the
range is wide, from "just make the order-notification email nicer" to "a
real login-gated admin page listing orders/entitlements." Don't assume
the bigger option is better; confirm the scope first.

If a page is wanted, it needs its own authentication (don't reuse student
OTP login for this — an admin page needs a separate, harder-to-guess
credential) and should be read-only to start.

**Gate**: scope confirmed with Pranav *before* writing code; working
result verified against real order data afterward.

---

### Phase 5 — Rate-limiting / abuse protection

Two independent gaps, both in `worker/index.js`:
- `/api/otp/send` has no limit on how many codes can be requested for one
  email address.
- `/api/contact` has no protection against automated spam.

Build reasonable limits (e.g., a small number of OTP sends per email per
hour, tracked in D1 or Cloudflare's rate-limiting primitives if
available). **Verify the limit doesn't lock out a real legitimate user**
in normal use — test the exact boundary, not just that a limit exists.

**Gate**: demonstrated a legitimate user can still log in normally, and a
rapid-repeat abuse pattern is genuinely blocked — both tested for real
against the live site.

---

### Phase 6 — Backup failure monitoring

`tools/backup_d1_snapshot.py` (see DATABASE-BACKUP.md) only logs to a
local file today. Add a real alert on failure — reuse whatever alerting
mechanism Pranav already has for the Telegram platform's bot-down
watcher if it's reasonable to reach from here, or propose a simpler
alternative (e.g., an email on failure, reusing the existing
`CF_EMAIL_API_TOKEN` pattern already in `worker/lib/email.js`) and confirm
with Pranav before building.

**Verify by actually causing a failure** (e.g., temporarily point the
export at a nonexistent database name) and confirming the alert fires,
then revert and confirm a normal run stays silent.

**Gate**: a real, deliberately-caused failure produced a real alert;
normal operation produces none.

---

## When you're done with all six phases

Update `PROJECT-LOG.md`: move every closed item from §6 into §2 with the
same "what was actually verified" rigor already used throughout that
file, and add any new open items you found along the way rather than
quietly fixing them without a mention.
