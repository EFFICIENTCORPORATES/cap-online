"""
telegram/database/cf_email.py -- Cloudflare Email Service sender (2026-08-11)
--------------------------------------------------------------------------------
Send-only transactional email via Cloudflare's Email Service (public beta,
launched 2026-04-16 -- https://developers.cloudflare.com/email-service/).
No inbox is configured or needed here -- this repo never reads incoming
mail, only sends. Confirmed prerequisites (Pranav, 2026-08-11): 1lavya.com
is already onboarded for Email Sending in the Cloudflare dashboard (SPF/
DKIM/DMARC set up there, out of scope for this repo), and support@1lavya.com
/ admin@1lavya.com are real, monitored mailboxes.

REST endpoint: POST https://api.cloudflare.com/client/v4/accounts/{account_id}/email/sending/send
Auth: `Authorization: Bearer <CF_EMAIL_API_TOKEN>` (needs "Email Sending:
Edit" permission). CF_EMAIL_ACCOUNT_ID/CF_EMAIL_API_TOKEN both come from
telegram/.env (gitignored) -- see .env.example for the real names.

ADDRESS SCHEME (Pranav, 2026-08-11, confirmed "one domain, different local
parts" over literal per-bot subdomains -- Cloudflare's onboarding/
verification is per-DOMAIN, not automatically per-subdomain, so a single
verified 1lavya.com covers every bot's address with no extra setup):
each bot in telegram/config/bots.json carries its own `from_email` (e.g.
studyhub@1lavya.com, csarunchouhan@1lavya.com) -- see
report_delivery.py's resolve_from_address(). Every address is unmonitored
by design (Pranav's explicit call) -- replies aren't read; the branded
footer (telegram/branding/brand_kit.py's render_email_footer_html())
always points real questions to support@1lavya.com / admin@1lavya.com
instead.

Raw urllib, not requests -- no new dependency, same technique
watcher_bot.py/leaderboard_broadcaster.py already use for their own
outbound HTTP calls.
"""

import os
import json
import base64
import urllib.request
import urllib.error
from email.utils import formataddr

CF_SEND_URL_TMPL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/email/sending/send"


class CloudflareEmailError(Exception):
    """Raised on any failure to send -- missing config, HTTP error, or a
    200 response whose body itself reports success=false. Callers are
    responsible for catching this, logging it, and telling the student
    honestly rather than pretending the email went out."""


def _account_id() -> str:
    return os.environ.get("CF_EMAIL_ACCOUNT_ID", "")


def _api_token() -> str:
    return os.environ.get("CF_EMAIL_API_TOKEN", "")


def is_configured() -> bool:
    return bool(_account_id() and _api_token())


def build_from_header(from_name: str, from_email: str) -> str:
    """Split out of send_email() purely so a test can verify the exact
    quoting behavior without a network call -- see send_email()'s own
    inline comment for the real 2026-08-11 incident this guards against
    (an unquoted display name containing a comma/parentheses broke
    Cloudflare's From-header parser in production)."""
    return formataddr((from_name, from_email)) if from_name else from_email


def send_email(from_email: str, from_name: str, to_email: str, subject: str,
                html_body: str, text_body: str = None, attachments: list = None) -> dict:
    """attachments: list of {"filename": str, "content_bytes": bytes,
    "content_type": str} -- base64-encoded here, callers never handle that
    encoding themselves. Raises CloudflareEmailError on any failure; never
    returns a falsely-successful result."""
    account_id, token = _account_id(), _api_token()
    if not account_id or not token:
        raise CloudflareEmailError(
            "CF_EMAIL_ACCOUNT_ID / CF_EMAIL_API_TOKEN not configured in telegram/.env -- see .env.example."
        )

    # REAL BUG, found + fixed 2026-08-11 (live incident on the csarunchouhan
    # bot -- Cloudflare rejected the send with HTTP 400
    # "email.sending.error.email.invalid"): a hand-rolled f"{name} <{email}>"
    # is only valid RFC 5322 syntax when `name` has no special characters.
    # csarunchouhan's own bots.json display_name -- "CS Arun Chouhan (Study +
    # Exam Practice, one bot)" -- contains both a comma and parentheses,
    # which Cloudflare's From-header parser rejected outright. Reproduced
    # exactly (isolated from/to independently before finding the real
    # culprit was the UNQUOTED display name specifically), confirmed fixed
    # by quoting. `email.utils.formataddr` is the stdlib's own correct
    # RFC 5322 quoting/escaping -- only wraps in quotes when actually
    # needed, never guessed by hand again.
    payload = {
        "from": build_from_header(from_name, from_email),
        "to": to_email,
        "subject": subject,
        "html": html_body,
    }
    if text_body:
        payload["text"] = text_body
    if attachments:
        payload["attachments"] = [
            {
                "filename": a["filename"],
                "type": a.get("content_type", "application/octet-stream"),
                "content": base64.b64encode(a["content_bytes"]).decode("ascii"),
                "disposition": "attachment",
            }
            for a in attachments
        ]

    url = CF_SEND_URL_TMPL.format(account_id=account_id)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise CloudflareEmailError(f"HTTP {e.code} from Cloudflare Email Service: {detail}") from e
    except Exception as e:
        raise CloudflareEmailError(f"Request to Cloudflare Email Service failed: {e}") from e

    if not result.get("success"):
        raise CloudflareEmailError(f"Cloudflare Email Service reported failure: {result}")
    return result
