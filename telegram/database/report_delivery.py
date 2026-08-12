"""
telegram/database/report_delivery.py -- email delivery + delivery logging
for the student report pipeline (2026-08-11, Phase 2; email backend
switched from Gmail SMTP to Cloudflare Email Service 2026-08-11 same day)
--------------------------------------------------------------------------------
Sends via telegram/database/cf_email.py (Cloudflare Email Service's REST
API) -- replaces this module's original Gmail-SMTP-reuse approach
(myfiles_hub_bot.py's OTP-email credentials) now that Pranav has real
Cloudflare Email Service credentials configured (telegram/.env's
CF_EMAIL_API_TOKEN/CF_EMAIL_ACCOUNT_ID) and confirmed 1lavya.com is
already onboarded for Email Sending in the Cloudflare dashboard.
myfiles_hub_bot.py's own OTP email is UNCHANGED -- still Gmail SMTP, not
migrated in this pass (not asked, not touched).

EACH BOT SENDS AS ITSELF: `bot_id` (now a required argument to
send_report_email()) resolves this bot's own dedicated, unmonitored
sending address via resolve_from_address() below, reading
telegram/config/bots.json's `from_email` field (Pranav's explicit ask,
2026-08-11 -- "each bot will have a dedicated email account... this will
be an unmonitored email id"). The EMAIL BODY, however, always carries full
1LAVYA branding regardless of which bot (including a faculty's own bot)
triggered it -- consistent with the precedent already set for the PDF
delivery captions in exam_hub_bot.py/study_hub_bot.py ("Powered by
1LAVYA" appears on every platform-generated FILE/report artifact
regardless of tenant, since 1LAVYA -- not the faculty -- built and
operates the report feature itself; only MENU/welcome/question text stays
strictly unbranded on faculty bots). See telegram/branding/brand_kit.py's
render_email_footer_html() for the support@/admin@ contact footer this
implies on every report email.

Telegram delivery (attaching the PDF via context.bot.send_document) is NOT
here -- it needs a live Bot instance from inside a running bot process, so
that logic lives directly in telegram/bots/report_flow.py instead. This
module only holds the pieces that don't need one: email (stateless HTTP)
and the report_deliveries audit-log writer, which callers on both delivery
paths share.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "branding"))
import cf_email  # noqa: E402
import brand_kit  # noqa: E402

BOTS_PATH = Path(__file__).resolve().parents[1] / "config" / "bots.json"
FALLBACK_FROM_EMAIL = "reports@1lavya.com"
FALLBACK_FROM_NAME = "1LAVYA"


def resolve_from_address(bot_id: str) -> tuple:
    """(from_email, from_display_name) for this bot_id, read from
    bots.json's own from_email/display_name fields. Falls back to a
    generic reports@1lavya.com / "1LAVYA" rather than raising if a bot_id
    is unknown or has no from_email configured -- report delivery should
    never hard-fail over a missing config field on a non-critical
    display detail."""
    try:
        data = json.loads(BOTS_PATH.read_text(encoding="utf-8"))
        for b in data.get("bots", []):
            if b.get("bot_id") == bot_id:
                return b.get("from_email") or FALLBACK_FROM_EMAIL, b.get("display_name") or FALLBACK_FROM_NAME
    except Exception:
        pass
    return FALLBACK_FROM_EMAIL, FALLBACK_FROM_NAME


def build_report_email_html(student_display_name: str, criteria_label: str, sender_bot_label: str) -> str:
    """Full branded HTML body -- table/inline-style markup (email clients,
    Outlook especially, have even less reliable CSS support than
    xhtml2pdf; matches the same constraint brand_kit.py's own module
    docstring already documents for that reason). Split out from
    send_report_email() so the smoke test can verify the rendered HTML
    (brand colors, footer, support/admin addresses all present) WITHOUT
    needing real Cloudflare credentials or a network call."""
    c = brand_kit.colors()
    return f"""
<div style="font-family:Arial,Helvetica,sans-serif; max-width:560px; margin:0 auto; padding:24px; color:{c['ink']};">
  <div style="font-size:20px; font-weight:bold; color:{c['navy']}; font-family:Georgia,'Times New Roman',serif;">{brand_kit.BRAND_NAME}</div>
  <div style="font-size:10px; color:{c['gold']}; text-transform:uppercase; margin-bottom:20px;">{brand_kit.TAGLINE}</div>

  <p style="font-size:14px; line-height:1.6;">Hi {student_display_name},</p>
  <p style="font-size:14px; line-height:1.6;">
    Attached is your {brand_kit.BRAND_NAME} performance report (<b>{criteria_label}</b>) --
    your accuracy, chapter-wise breakdown, and time spent practicing.
  </p>
  <p style="font-size:14px; line-height:1.6;">Keep practicing -- {brand_kit.TAGLINE}</p>

  {brand_kit.render_email_footer_html(sender_bot_label)}
</div>
""".strip()


def send_report_email(bot_id: str, to_email: str, pdf_bytes: bytes, student_display_name: str, criteria_label: str):
    """Raises on failure -- callers (report_flow.py, generate_student_report.py's
    CLI) are responsible for catching, logging to report_deliveries, and
    telling the student it failed rather than silently pretending it sent."""
    from_email, from_name = resolve_from_address(bot_id)
    html_body = build_report_email_html(student_display_name, criteria_label, from_name)
    cf_email.send_email(
        from_email=from_email,
        from_name=from_name,
        to_email=to_email,
        subject=f"Your {brand_kit.BRAND_NAME} Performance Report",
        html_body=html_body,
        attachments=[{
            "filename": "1LAVYA_Performance_Report.pdf",
            "content_bytes": pdf_bytes,
            "content_type": "application/pdf",
        }],
    )


def log_report_delivery(conn, telegram_user_id: int, criteria_label: str, channels_requested: str,
                         email_status: str = None, telegram_status: str = None, error_detail: str = None):
    """email_status/telegram_status: 'sent' | 'failed' | None (that channel
    wasn't requested this time). See schema.sql's report_deliveries CHECK
    constraints for the exact allowed values."""
    import db as platform_db

    platform_db.execute_with_retry(
        conn,
        """INSERT INTO report_deliveries
           (telegram_user_id, generated_at, criteria, channels_requested, email_status, telegram_status, error_detail)
           VALUES (?,?,?,?,?,?,?)""",
        (telegram_user_id, platform_db.now(), criteria_label, channels_requested, email_status, telegram_status, error_detail),
    )
