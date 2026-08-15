"""
telegram/database/razorpay_client.py -- Razorpay Payment Links client (2026-08-15)
--------------------------------------------------------------------------------
Built for the wallet recharge flow (see telegram/database/wallet.py and
telegram/bots/wallet_flow.py) -- see
telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md §9.5 for the full
decision trail behind every choice below.

WHY PAYMENT LINKS, NOT A WEBSITE CHECKOUT: 1LAVYA has no website product to
embed a checkout into -- students transact entirely inside Telegram. Razorpay
Payment Links is the first-class, Razorpay-documented product for exactly
this "sell via a chat interface, no website" shape (they sell an equivalent
WhatsApp Payment Links Bot for the identical use case) -- the bot creates a
link via this module, sends the URL to the student, the student pays in
their own UPI app.

WHY POLLING, NOT A WEBHOOK, FOR V1: webhooks need a public HTTPS endpoint,
which needs Cloudflare Tunnel set up first (blocked on Pranav's own
interactive `cloudflared login` step -- can't be done on his behalf). Razorpay's
GET /v1/payment_links/{id} endpoint gives a live status (issued / paid /
partially_paid / cancelled / expired) via the same API-key auth, no webhook
required -- good enough for a correct v1. fetch_payment_link() below is what
a job_queue polling loop in wallet_flow.py calls periodically after creating
a link. The webhook (with mandatory X-Razorpay-Signature verification) is a
planned LATER optimization for faster confirmation + a reconciliation
safety net, not a launch blocker -- see roadmap §9.5's own note on this.

LIVE KEYS: Pranav's explicit call (2026-08-15, "amount is small... please
go ahead with the live keys only"), given per-transaction amounts are ₹1-20.
There is no test-mode safety net here -- every call this module makes is
real money. Consequences taken deliberately in this module's design:
  - Every state-changing call (create_payment_link) requires an idempotency
    key from the caller (reference_id) and should be called at most once per
    logical recharge attempt -- callers own retry-safety at the DB layer
    (see wallet.py's idempotency_key handling), this module does not retry
    create calls internally, since a naive retry of a POST could create two
    real, separate payment links for one student action.
  - fetch_payment_link() (a GET, safe to retry/poll) has no such restriction.

Env vars (telegram/.env, gitignored -- confirmed 2026-08-15, never tracked
in git history): RAZORPAY_1LAVYA_key_id / RAZORPAY_1LAVYA_key_secret.

Raw urllib, not requests or the official `razorpay` SDK -- matches this
codebase's own established pattern for outbound HTTP to a third-party API
(see cf_email.py, watcher_bot.py, leaderboard_broadcaster.py) rather than
adding a new dependency for what's a small, well-documented REST surface.
"""

import os
import json
import base64
import time
import urllib.request
import urllib.error

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


class RazorpayError(Exception):
    """Raised on any failure to create/fetch a Payment Link -- missing
    config or an HTTP error. Callers are responsible for catching this,
    logging it, and telling the student honestly (e.g. "couldn't start
    your recharge, try again in a bit") rather than pretending it worked."""


def _key_id() -> str:
    return os.environ.get("RAZORPAY_1LAVYA_key_id", "")


def _key_secret() -> str:
    return os.environ.get("RAZORPAY_1LAVYA_key_secret", "")


def is_configured() -> bool:
    return bool(_key_id() and _key_secret())


def _auth_header() -> str:
    raw = f"{_key_id()}:{_key_secret()}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _request(method: str, path: str, payload: dict = None) -> dict:
    if not is_configured():
        raise RazorpayError(
            "RAZORPAY_1LAVYA_key_id / RAZORPAY_1LAVYA_key_secret not configured "
            "in telegram/.env."
        )
    url = f"{RAZORPAY_API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": _auth_header(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RazorpayError(f"HTTP {e.code} from Razorpay ({method} {path}): {detail}") from e
    except Exception as e:
        raise RazorpayError(f"Request to Razorpay failed ({method} {path}): {e}") from e


def create_payment_link(*, amount_inr: float, reference_id: str, description: str,
                         customer_name: str = None, customer_contact: str = None,
                         notes: dict = None, expire_after_minutes: int = 30) -> dict:
    """Creates a real, live Payment Link -- every call is a real
    outward-facing action (Razorpay will actually issue a payable link).
    `reference_id` should be unique per logical recharge attempt (e.g.
    "recharge:{username}:{unix_ts}") -- Razorpay itself doesn't dedupe on
    this, so callers must not call this twice for one student action; see
    module docstring's note on idempotency living at the DB layer, not here.

    amount_inr is rupees (e.g. 20.0 for a ₹20 recharge) -- converted to
    paise (the API's required unit) here so no caller has to remember that
    conversion or risk an off-by-100 bug.

    expire_after_minutes: how long the link stays payable -- short by
    design (30 min default) so an abandoned recharge attempt doesn't sit
    payable indefinitely; the polling loop in wallet_flow.py should stop
    waiting once this window passes and treat the attempt as expired.

    Returns the raw Razorpay response dict -- callers read `id` (the
    Payment Link id, e.g. "plink_..." -- store this as payments
    .gateway_txn_id immediately) and `short_url` (what to send the
    student)."""
    payload = {
        "amount": round(amount_inr * 100),
        "currency": "INR",
        "reference_id": reference_id,
        "description": description,
        "expire_by": int(time.time()) + expire_after_minutes * 60,
        "notify": {"sms": False, "email": False},  # the bot sends the link itself, in-chat
        "reminder_enable": False,
    }
    if customer_name or customer_contact:
        payload["customer"] = {}
        if customer_name:
            payload["customer"]["name"] = customer_name
        if customer_contact:
            payload["customer"]["contact"] = customer_contact
    if notes:
        payload["notes"] = notes
    return _request("POST", "/payment_links", payload)


def fetch_payment_link(payment_link_id: str) -> dict:
    """Safe to call repeatedly (a GET) -- this is what a polling loop uses
    to check whether a link has been paid. Returns the raw Razorpay
    response; callers read `status` (issued / paid / partially_paid /
    cancelled / expired) and `amount_paid`."""
    return _request("GET", f"/payment_links/{payment_link_id}")
